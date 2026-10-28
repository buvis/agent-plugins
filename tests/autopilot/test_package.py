"""Committed target packages remain complete and usable without their author."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
FORMATS = ["review-policy-v1", "review-evidence-v1", "review-fixtures-v1"]
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
GATE_SIZE = 742
GATE_SHA = "2ea4600b2ec6756640e2e23a8d761160afc889c0a3c6af0caa6fac6d0edaec75"

# External boundaries only: deny network, process launches, and author-home reads.
GUARD = '''
import os, pathlib, socket, sys
home = pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"]).resolve()
allowed = [pathlib.Path(p).resolve() for p in
           (sys.prefix, sys.base_prefix, os.environ["ISOLATED_TARGET"])]
for directory in sys.path:
    if pathlib.Path(directory).name == "site-packages" and pathlib.Path(directory).is_dir():
        allowed.extend(p.resolve() for p in pathlib.Path(directory).iterdir())
def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn"}:
        raise PermissionError("isolated target forbids process launch")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = pathlib.Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(home) and not any(path.is_relative_to(p) for p in allowed):
            raise PermissionError("isolated target forbids author/source reads")
def denied(*args, **kwargs):
    raise PermissionError("isolated target forbids network")
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
socket.getaddrinfo = denied
sys.addaudithook(audit)
'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TargetPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="autopilot-target-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.target = Path(cls.temp.name) / "target"
        cls.target.mkdir()
        archive = Path(cls.temp.name) / "target.tar"
        with archive.open("wb") as stream:
            subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"], cwd=ROOT,
                stdout=stream, stderr=subprocess.PIPE, check=True, timeout=60,
            )
        with tarfile.open(archive) as bundle:
            bundle.extractall(cls.target, filter="data")
        cls.package = cls.target / "plugins/autopilot"
        cls.mapping = json.loads((cls.target / "tools/autopilot/source-map.json").read_text())
        cls.inventory = json.loads(
            (cls.target / "tools/autopilot/source-inventory.json").read_text()
        )
        cls.guard = Path(cls.temp.name) / "guard"
        cls.guard.mkdir()
        (cls.guard / "sitecustomize.py").write_text(GUARD)
        cls.home = cls.target / "empty-home"
        cls.home.mkdir()
        cls.cwd = cls.target / "unrelated-cwd"
        cls.cwd.mkdir()
        cls.env = {
            "PATH": os.defpath, "HOME": str(cls.home), "USERPROFILE": str(cls.home),
            "PYTHONPATH": str(cls.guard), "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1", "FORBIDDEN_AUTHOR_HOME": str(Path.home()),
            "ISOLATED_TARGET": str(cls.target),
        }

    def child(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=self.cwd, env=self.env,
            text=True, capture_output=True, timeout=60,
        )

    def facade(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.child(self.package / "scripts/autopilot.py", *args)

    def validator(self) -> subprocess.CompletedProcess[str]:
        return self.child(self.target / "scripts/validate.py")

    def test_content_roster_matches_frozen_inventory_and_actual_package_bytes(self) -> None:
        mapping, inventory = self.mapping, self.inventory
        self.assertEqual(mapping["schema_version"], 1)
        inventory_bytes = (self.target / "tools/autopilot/source-inventory.json").read_bytes()
        self.assertEqual(mapping["source_inventory_sha256"], digest(inventory_bytes))
        source_rows = [a for a in mapping["assets"] if a["source_asset_id"] is not None]
        source_ids = [a["source_asset_id"] for a in source_rows]
        self.assertEqual(len(source_ids), 92)
        self.assertEqual(len(set(source_ids)), len(source_ids))
        self.assertEqual(set(source_ids), set(inventory["required_asset_ids"]))
        self.assertEqual(len(mapping["behaviors"]), 1381)
        self.assertEqual(len(mapping["regression_cases"]), 4950)
        expected = {a["destination_path"] for a in mapping["assets"]}
        actual = {p.relative_to(self.target).as_posix()
                  for p in self.package.rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)
        for row in mapping["assets"]:
            with self.subTest(asset=row["destination_path"]):
                path = self.target / row["destination_path"]
                self.assertTrue(path.resolve().is_relative_to(self.package.resolve()))
                self.assertEqual(digest(path.read_bytes()), row["destination_blob_sha256"])
                self.assertNotEqual(row["disposition"], "planned")
                if row["disposition"] == "preserved":
                    self.assertEqual(row["destination_blob_sha256"], row["source_blob_sha256"])

    def test_reference_tree_and_all_eleven_first_body_gates_preserve_source_bytes(self) -> None:
        rows = self.mapping["assets"]
        personas = [r for r in rows if "/references/personas/" in r["destination_path"]]
        skills = [r for r in rows if r["destination_path"].endswith("/SKILL.md")]
        self.assertEqual(len(personas), 18)
        self.assertEqual(len(skills), 11)
        self.assertTrue(all(r["disposition"] == "preserved" for r in rows
                            if "/references/" in r["destination_path"]))
        for row in skills:
            with self.subTest(skill=row["destination_path"]):
                data = (self.target / row["destination_path"]).read_bytes()
                frontmatter_end = data.index(b"\n---\n", 4) + len(b"\n---\n")
                self.assertEqual(digest(data[frontmatter_end:frontmatter_end + GATE_SIZE]), GATE_SHA)
                restored = data[:frontmatter_end] + data[frontmatter_end + GATE_SIZE:]
                self.assertEqual(digest(restored), row["source_blob_sha256"])

    def test_readme_retains_every_source_heading_with_completed_adaptation_receipts(self) -> None:
        source = next(a for a in self.inventory["assets"] if a["source_asset_id"] == "README.md")
        row = next(a for a in self.mapping["assets"] if a["source_asset_id"] == "README.md")
        text = (self.package / "README.md").read_text()
        headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE)
        self.assertEqual(row["disposition"], "adapted")
        self.assertEqual({s["source_anchor"] for s in row["section_plan"]},
                         {s["anchor"] for s in source["sections"]})
        for section in source["sections"]:
            with self.subTest(section=section["anchor"]):
                self.assertIn(section["heading"], headings)
                receipt = next(s for s in row["section_plan"]
                               if s["source_anchor"] == section["anchor"])
                self.assertEqual(receipt["source_sha256"], section["sha256"])
                self.assertTrue(receipt["reason"].strip())
                self.assertTrue(receipt["delivery_note"].strip())
        self.assertEqual(row["evidence"]["status"], "passed")
        self.assertTrue(all(c["status"] == "passed" for c in row["acceptance_cases"]))

    def test_resource_closure_declares_inside_resources_and_external_failure_rules(self) -> None:
        edges = self.mapping["resource_edges"]
        self.assertEqual({e["kind"] for e in edges}, {
            "packaged-resource", "external-capability", "informational-provenance",
        })
        for edge in edges:
            with self.subTest(edge=edge["reference"], source=edge.get("source_path", edge.get("source_behavior_id"))):
                if edge["kind"] == "packaged-resource":
                    path = self.target / edge["destination_path"]
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.resolve().is_relative_to(self.package.resolve()))
                    self.assertTrue(edge["failure_rule"].strip())
                elif edge["kind"] == "external-capability":
                    self.assertTrue(edge["capability"].strip())
                    self.assertTrue(edge["failure_rule"].strip())
                else:
                    self.assertRegex(edge["runtime_rule"], r"(?i)(must not|never).*(runtime|content)")

    def test_public_validator_accepts_contained_links_and_rejects_external_helpers(self) -> None:
        baseline = self.validator()
        self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
        for folder, name in (("scripts", "external-helper.py"),
                             ("references", "external-reference.md")):
            link = self.package / folder / name
            link.parent.mkdir(exist_ok=True)
            outside = self.target / ("autopilot-near-miss-" + name)
            outside.write_text("External content must never satisfy packaged resources.\n")
            try:
                link.symlink_to(self.package / "LICENSE")
                valid = self.validator()
                self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
                link.unlink()
                link.symlink_to(outside)
                invalid = self.validator()
                self.assertNotEqual(invalid.returncode, 0, invalid.stdout + invalid.stderr)
                self.assertTrue((invalid.stdout + invalid.stderr).strip())
            finally:
                link.unlink(missing_ok=True)
                outside.unlink(missing_ok=True)

    def test_target_only_checkout_denies_source_home_and_network_but_exports_policy(self) -> None:
        self.assertFalse((self.target / ".git").exists())
        self.assertEqual(list(self.home.iterdir()), [])
        probe = self.child("-c", '''
import os, pathlib, socket
assert pathlib.Path.home() == pathlib.Path(os.environ["HOME"])
for path in [pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"])/".claude/AGENTS.md",
             pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"])/"git/src/github.com/buvis/claude-autopilot/README.md"]:
    try: path.read_bytes()
    except PermissionError: pass
    else: raise AssertionError("author/source boundary escaped")
try: socket.create_connection(("127.0.0.1", 1), timeout=0.1)
except PermissionError: pass
else: raise AssertionError("network boundary escaped")
print("isolated")
''')
        self.assertEqual((probe.returncode, probe.stdout), (0, "isolated\n"), probe.stderr)
        capabilities = self.facade("--list-capabilities")
        self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
        self.assertEqual(capabilities.stdout, json.dumps(FORMATS, separators=(",", ":")) + "\n")
        expected = json.loads((self.package / "contracts/review-policy-v1.json").read_text())
        exported = self.facade("--export-policy")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        self.assertEqual(json.loads(exported.stdout), expected)
        for relative in ("policy-one.json", "nested/policy-two.json"):
            destination = self.cwd / relative
            destination.parent.mkdir(exist_ok=True)
            result = self.facade("--export-policy", "--out", relative)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(destination.read_bytes(), exported.stdout.encode())
        for args in ((), ("--list-capabilities-extra",), ("--export-policy", "--out", str(self.cwd))):
            result = self.facade(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((result.stdout + result.stderr).strip())

    def test_target_only_semantic_oracle_checks_every_committed_fixture_without_skip(self) -> None:
        result = self.child("-c", '''
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "tests/autopilot"))
from test_contract_semantics import validate_review
document = json.loads((root / "plugins/autopilot/contracts/review-fixtures-v1.json").read_text())
assert len(document["cases"]) == 55
outcomes = set()
for case in document["cases"]:
    actual = validate_review(document["policies"][case["policy"]], case["expected_context"], case["input"])
    assert actual == case["expect"], (case["name"], actual, case["expect"])
    outcomes.add(actual["outcome"])
assert outcomes == {"accepted", "rejected"}
print("55 fixtures validated")
''', self.target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "55 fixtures validated\n")

    def test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job(self) -> None:
        document = yaml.safe_load((self.target / ".github/workflows/validate.yml").read_text())
        jobs = document["jobs"]
        plugins = jobs["plugins"]
        self.assertEqual(plugins["runs-on"], "ubuntu-latest")
        self.assertEqual(plugins["env"], {"PYTHONDONTWRITEBYTECODE": "1"})
        steps = plugins["steps"]
        self.assertEqual([s.get("uses") for s in steps[:2]], [CHECKOUT, SETUP])
        self.assertEqual(steps[0]["with"], {"persist-credentials": False})
        self.assertEqual(steps[1]["with"], {"python-version": "3.10"})
        self.assertEqual([s["run"] for s in steps[2:]], [
            "python3 -m unittest discover -s scripts", "python3 scripts/validate.py",
            *[f"python3 -m unittest discover -s tests/specflow/{area}"
              for area in ("release", "contract", "rules", "review")],
            "python3 tools/specflow/check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER,RVC,RVR,RVD,RVX,CNV",
            "python3 tools/specflow/verify_release.py",
        ])
        steps = jobs["autopilot"]["steps"]
        self.assertTrue(any(s.get("uses") == CHECKOUT and
                            s.get("with", {}).get("persist-credentials") is False for s in steps))
        self.assertTrue(any(s.get("uses") == SETUP and
                            s.get("with", {}).get("python-version") == "3.12" for s in steps))
        commands = [s["run"] for s in steps if "run" in s]
        self.assertTrue(any(re.search(r"(?:^|\s)(?:-r|--requirement)\s+tools/autopilot/requirements-test\.txt(?:\s|$)", c)
                            and "pip install" in c for c in commands))
        self.assertTrue(any(shlex.split(c) == ["python", "-m", "pytest", "tests/autopilot", "-q"]
                            for c in commands))


if __name__ == "__main__":
    unittest.main()
