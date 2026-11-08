"""Public local facade exports deterministic policy without runtime services."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

from test_contract import ROOT, load


PACKAGE = ROOT / "plugins" / "autopilot"
EXPORTER = ROOT / "tools" / "autopilot" / "export-policy.py"
POLICY = Path("contracts") / "review-policy-v1.json"
CAPABILITIES = b'["review-policy-v1","review-evidence-v1","review-fixtures-v1"]\n'
HELPER_OPERATIONS = [
    "stage-review-v1", "group-findings-v1", "check-evidence-v1", "prepare-close-v1",
    "catchup-probe-v1", "verification-artifact-v1", "controller-required-v1",
    "hosts-v1", "guards-v1", "diagnose-v1",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def sign(policy: dict) -> dict:
    payload = copy.deepcopy(policy)
    payload.pop("policy_digest", None)
    payload["policy_digest"] = hashlib.sha256(canonical(payload)).hexdigest()
    return payload


class LocalFacadeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.distribution = self.base / "portable distribution"
        self.package = self.distribution / "plugins" / "autopilot"
        shutil.copytree(PACKAGE, self.package)
        self.facade = self.package / "scripts" / "autopilot.py"
        self.exporter = self.distribution / "tools" / "autopilot" / "export-policy.py"
        self.exporter.parent.mkdir(parents=True)
        if EXPORTER.is_file():
            shutil.copyfile(EXPORTER, self.exporter)
        self.cwd = self.base / "unrelated cwd"
        self.home = self.base / "empty home"
        self.empty_path = self.base / "empty executable path"
        for directory in (self.cwd, self.home, self.empty_path):
            directory.mkdir()
        self.env = {
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.home),
            "XDG_CACHE_HOME": str(self.home), "XDG_STATE_HOME": str(self.home),
            "PATH": str(self.empty_path), "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1", "LANG": "C.UTF-8",
        }
        self.policy = load(PACKAGE / POLICY)
        self.original = (PACKAGE / POLICY).read_bytes()

    def run_cli(self, script: Path, *arguments: str, cwd: Path | None = None,
                home: Path | None = None) -> subprocess.CompletedProcess:
        self.assertTrue(script.is_file(), f"Public CLI executable is missing: {script}")
        env = dict(self.env)
        if home is not None:
            for key in ("HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
                env[key] = str(home)
        return subprocess.run(
            [sys.executable, str(script), *arguments], cwd=cwd or self.cwd,
            env=env, capture_output=True, timeout=60,
        )

    def assert_success(self, result: subprocess.CompletedProcess, expected: bytes) -> None:
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.stderr, b"")

    def assert_failure(self, result: subprocess.CompletedProcess) -> None:
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip(), "Failure must include a stderr diagnostic")
        self.assertEqual(result.stdout, b"")

    def write_policy(self, policy: object) -> bytes:
        content = canonical(policy) + b"\n"
        (self.package / POLICY).write_bytes(content)
        return content

    def test_capabilities_are_exact_contract_formats_without_runtime_side_effects(self) -> None:
        before = {p.relative_to(self.package): (p.stat().st_size, p.stat().st_mtime_ns)
                  for p in self.package.rglob("*") if p.is_file()}
        homes = (self.home, self.base / "clean config root", self.base / uuid.uuid4().hex)
        for home in homes:
            home.mkdir(exist_ok=True)
            for script in (PACKAGE / "scripts" / "autopilot.py", self.facade):
                with self.subTest(script=script, home=home):
                    result = self.run_cli(script, "--list-capabilities", home=home)
                    ids = json.loads(result.stdout)
                    self.assert_success(result, json.dumps(ids, separators=(",", ":")).encode() + b"\n")
                    self.assertEqual(ids, [*json.loads(CAPABILITIES), *HELPER_OPERATIONS])
            self.assertEqual(list(home.iterdir()), [])
        after = {p.relative_to(self.package): (p.stat().st_size, p.stat().st_mtime_ns)
                 for p in self.package.rglob("*") if p.is_file()}
        self.assertEqual(after, before)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.cwd.iterdir()), [])

    def test_policy_export_reproducible_across_relocation_and_unrelated_cwd(self) -> None:
        self.assertEqual(sign(self.policy), self.policy)
        expected = canonical(self.policy) + b"\n"
        working_dirs = (self.cwd, self.base / "another launch directory",
                        self.base / f"cwd-{uuid.uuid4().hex}")
        for directory in working_dirs:
            directory.mkdir(exist_ok=True)
        # Same-named data in cwd and HOME must not shadow packaged data.
        for directory in (*working_dirs, self.home):
            decoy = directory / POLICY
            decoy.parent.mkdir()
            decoy.write_text('{"policy_digest":"wrong"}', encoding="utf-8")
        decoy_package = self.package.with_name("autopilot-near-miss")
        (decoy_package / POLICY).parent.mkdir(parents=True)
        (decoy_package / POLICY).write_text("null", encoding="utf-8")
        before = {p.relative_to(self.distribution) for p in self.distribution.rglob("*")}
        for script in (PACKAGE / "scripts" / "autopilot.py", self.facade,
                       EXPORTER, self.exporter):
            for directory in working_dirs:
                for repeat in range(2):
                    with self.subTest(script=script, cwd=directory, repeat=repeat):
                        self.assert_success(self.run_cli(script, "--export-policy", cwd=directory)
                                            if script in (self.facade, PACKAGE / "scripts" / "autopilot.py")
                                            else self.run_cli(script, cwd=directory), expected)
        self.assertEqual({p.relative_to(self.distribution)
                          for p in self.distribution.rglob("*")}, before)
        self.assertEqual((PACKAGE / POLICY).read_bytes(), self.original)
        self.assertEqual((self.package / POLICY).read_bytes(), self.original)

    def test_export_out_writes_exact_bytes_to_each_passed_path_and_no_stdout(self) -> None:
        expected = canonical(self.policy) + b"\n"
        paths = (self.cwd / "policy.json", self.base / "other policy.json",
                 self.cwd / f"{uuid.uuid4().hex}.json",
                 self.base / f"export {uuid.uuid4().hex}.data")
        for script in (self.facade, self.exporter):
            prefix = ("--export-policy",) if script == self.facade else ()
            for output in paths:
                with self.subTest(script=script, output=output):
                    output.write_bytes(b"old content that must be replaced")
                    result = self.run_cli(script, *prefix, "--out", str(output))
                    self.assert_success(result, b"")
                    self.assertEqual(output.read_bytes(), expected)
                    output.unlink()
            relative = Path("relative-policy.json")
            result = self.run_cli(script, *prefix, "--out", str(relative))
            self.assert_success(result, b"")
            self.assertEqual((self.cwd / relative).read_bytes(), expected)
            (self.cwd / relative).unlink()
            generated_relative = Path(f"{uuid.uuid4().hex}.bin")
            self.assert_success(self.run_cli(script, *prefix, "--out", str(generated_relative)), b"")
            self.assertEqual((self.cwd / generated_relative).read_bytes(), expected)
            (self.cwd / generated_relative).unlink()
        self.assertEqual((self.package / POLICY).read_bytes(), self.original)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_resigned_policy_content_and_reference_digests_affect_export(self) -> None:
        digests = set()
        for section, reference_digest in (("reviewers \u017elu\u0165", "1" * 64),
                                           ("reviewers \u6771\u4eac", "2" * 64)):
            policy = copy.deepcopy(self.policy)
            policy["source_bindings"][0]["section"] = section
            policy["source_bindings"][-1]["section_sha256"] = reference_digest
            policy = sign(policy)
            digests.add(policy["policy_digest"])
            source = self.write_policy(policy)
            for script in (self.facade, self.exporter):
                with self.subTest(section=section, script=script):
                    arguments = ("--export-policy",) if script == self.facade else ()
                    self.assert_success(self.run_cli(script, *arguments), source)
            self.assertEqual((self.package / POLICY).read_bytes(), source)
        self.assertEqual(len(digests), 2)
        self.assertNotIn(self.policy["policy_digest"], digests)
        self.assertEqual((PACKAGE / POLICY).read_bytes(), self.original)

    def test_invalid_policy_never_creates_or_truncates_output(self) -> None:
        corruptions = [b"", b"{", b"null", b"[]", b"[{},{}]", b'"policy"']
        for digest in (None, "", "0" * 64, "0" * 63, "A" * 64, 123):
            policy = copy.deepcopy(self.policy)
            policy["policy_digest"] = digest
            corruptions.append(canonical(policy))
        missing = copy.deepcopy(self.policy)
        del missing["policy_digest"]
        corruptions.append(canonical(missing))
        changed = copy.deepcopy(self.policy)
        changed["source_bindings"][-1]["section_sha256"] = "3" * 64
        corruptions.append(canonical(changed))
        corruptions.append(canonical(sign({})))
        required_keys = (
            "schema_version", "procedure", "reviewer_jobs", "rubric_sets", "doubt_label_map",
            "execution_profiles", "artifact_kinds", "input_kinds", "source_bindings",
        )
        for key in required_keys:
            incomplete = copy.deepcopy(self.policy)
            del incomplete[key]
            corruptions.append(canonical(sign(incomplete)))
        for version in (0, 2, -1, "1", True, None, 1.0):
            unsupported = copy.deepcopy(self.policy)
            unsupported["schema_version"] = version
            corruptions.append(canonical(sign(unsupported)))
        extra = copy.deepcopy(self.policy)
        extra["unknown_root_field"] = "closed root"
        corruptions.append(canonical(sign(extra)))
        for content in corruptions:
            (self.package / POLICY).write_bytes(content)
            self.check_failed_exports_preserve_files(content)
        self.assertEqual((PACKAGE / POLICY).read_bytes(), self.original)

    def check_failed_exports_preserve_files(self, content: bytes) -> None:
        for script in (self.facade, self.exporter):
            prefix = ("--export-policy",) if script == self.facade else ()
            with self.subTest(script=script, content=content[:60]):
                self.assert_failure(self.run_cli(script, *prefix))
                for existing in (False, True):
                    output = self.cwd / ("existing.json" if existing else "absent.json")
                    if existing:
                        output.write_bytes(b"preserve this output")
                    self.assert_failure(self.run_cli(script, *prefix, "--out", str(output)))
                    if existing:
                        self.assertEqual(output.read_bytes(), b"preserve this output")
                    else:
                        self.assertFalse(output.exists())
                self.assertEqual((self.package / POLICY).read_bytes(), content)

    def test_nonfinite_and_fractional_numbers_are_rejected_recursively(self) -> None:
        # Re-sign invalid numeric values so a digest mismatch cannot mask this guard.
        locations = (
            ("procedure", "lanes", "full", "rework_policy", "cycle_cap_default"),
            ("source_bindings", -1, "section"),
            ("source_bindings", 0, "section"),
            ("source_bindings", len(self.policy["source_bindings"]) // 2, "section"),
            ("procedure", "lanes", "solo", "rework_policy", "reviewer_retry_limit"),
            ("procedure", "lanes", "full", "required_reviewer_jobs", 0),
            ("procedure", "lanes", "full", "required_reviewer_jobs", 1),
            ("procedure", "lanes", "full", "required_reviewer_jobs", -1),
            ("reviewer_jobs", 0, "lenses", 0),
            ("rubric_sets", "D", "rule_ids", 1),
        )
        for value in (float("nan"), float("inf"), float("-inf"), 0.5, -2.25, 1e-40):
            for location in locations:
                with self.subTest(value=value, location=location):
                    policy = copy.deepcopy(self.policy)
                    target = policy
                    for key in location[:-1]:
                        target = target[key]
                    target[location[-1]] = value
                    content = self.write_policy(sign(policy))
                    self.check_failed_exports_preserve_files(content)
        self.assertEqual((PACKAGE / POLICY).read_bytes(), self.original)

    def test_usage_errors_refuse_runtime_commands_and_ambiguous_modes(self) -> None:
        output = self.cwd / "untouched.json"
        output.write_bytes(b"keep")
        invalid_arguments = (
            (), ("--list-capabilities", "--export-policy"),
            ("--out", str(output)), ("--list-capabilities", "--out", str(output)),
            ("--export-policy", "--out"), ("--list-capabilities-extra",),
            ("--export-policy-extra",), ("--export-policy", "--fetch"),
            ("--run",), ("--state", str(output)), ("--supervisor",),
            ("--native-host",), ("run-autopilot",),
            ("--launch-runtime",), ("--export-policy", "--launch-runtime"),
            ("--list-capabilities", "--launch-runtime"),
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_failure(self.run_cli(self.facade, *arguments))
                self.assertEqual(output.read_bytes(), b"keep")
        exporter_invalid_arguments = (
            ("--out",), ("--launch-runtime",), ("--fetch",), ("--run",),
            ("--state", str(output)), ("--supervisor",), ("--native-host",),
            ("run-autopilot",), ("--export-policy-extra",),
            ("--out", str(output), "--launch-runtime"),
        )
        for arguments in exporter_invalid_arguments:
            with self.subTest(exporter_arguments=arguments):
                self.assert_failure(self.run_cli(self.exporter, *arguments))
                self.assertEqual(output.read_bytes(), b"keep")
        self.assertEqual((self.package / POLICY).read_bytes(), self.original)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(set(self.cwd.iterdir()), {output})

    def test_output_filesystem_failure_is_reported_without_policy_mutation(self) -> None:
        for script in (self.facade, self.exporter):
            prefix = ("--export-policy",) if script == self.facade else ()
            with self.subTest(script=script):
                result = self.run_cli(script, *prefix, "--out", str(self.cwd))
                self.assert_failure(result)
                self.assertEqual(list(self.cwd.iterdir()), [])
                self.assertEqual((self.package / POLICY).read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
