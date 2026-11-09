"""Exported controller bundle, its pins, and the copy-only installed package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unittest
from pathlib import Path

from controller_cli_support import (
    ControllerCLITest,
    canonical,
    cli,
    fresh_request,
    private_path,
    strict_json,
    tree,
)

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "autopilot"
BUNDLE_RELATIVE = "plugins/autopilot/contracts/controller-v1.json"
BUNDLE = ROOT / BUNDLE_RELATIVE
README = PLUGIN / "README.md"
EXPORTER = ROOT / "tools" / "autopilot" / "export-controller-contract.py"
TARGET = Path("contracts") / "controller-v1.json"
SCHEMA = Path("contracts") / "controller" / "workflow-v1.json"
FIXTURES = Path("contracts") / "controller" / "fixtures-v1.json"
BUNDLE_KEYS = {
    "protocol_major",
    "package_version",
    "schema_digest",
    "fixture_digest",
    "operations",
    "capabilities",
}
OPERATIONS = {"workflow.open", "owner.acquire", "owner.release", "owner.recover"}
CAPABILITIES = {"workflow.core.v1"}
INSTALLED_ARGV = '["python3", "<installed-plugin-root>/controller/main.py"]'
LIMIT = 16777216
HEX = re.compile(r"[0-9a-f]{64}")
BUILD = r"[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*"
NEGATION = re.compile(r"\b(?:not|never|avoid)\b|n't", re.IGNORECASE)

# Runs a script with the stdlib only (-I -S), denying every read of the source
# checkout and the author home outside this test's sandbox and the interpreter.
GUARD = """
import os
import runpy
import sys

PRIVATE = {private!r}
ALLOWED = [os.path.realpath(path) for path in ({allowed!r}, sys.prefix,
           sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix)]


def inside(path, roots):
    return any(path == root or path.startswith(root.rstrip(os.sep) + os.sep)
               for root in roots)


def guard(event, args):
    if event not in ("open", "os.listdir", "os.scandir") or not args:
        return
    if args[0] is None or isinstance(args[0], int):
        return
    path = os.path.realpath(os.fsdecode(args[0]))
    if inside(path, PRIVATE) and not inside(path, ALLOWED):
        raise PermissionError("isolated test denies " + path)


sys.addaudithook(guard)
script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_tree(root: Path) -> dict:
    """tree() with directory link counts masked; APFS counts entries in them."""
    return {
        key: (kind, mode, None if stat.S_ISDIR(kind) else links, content)
        for key, (kind, mode, links, content) in tree(root).items()
    }


def heading_levels(lines: list[str]) -> list[int]:
    levels, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
        match = None if fenced else re.match(r"(#{1,6}) ", line)
        levels.append(len(match.group(1)) if match else 0)
    return levels


def heading_section(text: str, needle: str) -> list[str]:
    """Lines of the Markdown heading section that contains needle."""
    lines = text.splitlines()
    levels = heading_levels(lines)
    index = next(i for i, line in enumerate(lines) if needle in line)
    start = next((i for i in range(index, -1, -1) if levels[i]), 0)
    depth = levels[start] or 6
    end = next(
        (i for i in range(start + 1, len(lines)) if 0 < levels[i] <= depth),
        len(lines),
    )
    return lines[start:end]


def copy_plugin(destination: Path) -> Path:
    shutil.copytree(
        PLUGIN,
        destination,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return destination


class BundleAssertions(unittest.TestCase):
    def assert_runtime_matches(self, runtime: object, bundle: dict) -> None:
        self.assertIsInstance(runtime, dict)
        for key in ("protocol_major", "schema_digest", "fixture_digest"):
            self.assertEqual(runtime[key], bundle[key], key)
        self.assertIs(type(runtime["protocol_major"]), int)
        version = runtime["package_version"]
        self.assertIsInstance(version, str)
        if version != bundle["package_version"]:
            prefix = bundle["package_version"] + "+"
            self.assertTrue(version.startswith(prefix), version)
            self.assertRegex(version[len(prefix) :], "^" + BUILD + "$")
        for key in ("operations", "capabilities"):
            self.assertIsInstance(runtime[key], list)
            self.assertLessEqual(set(bundle[key]), set(runtime[key]), key)


class IsolatedCase(ControllerCLITest, BundleAssertions):
    def setUp(self) -> None:
        super().setUp()
        for name in ("home", "tmp"):
            (self.base / name).mkdir()
        self.cwd = self.base / "cwd"
        live = private_path(self.cwd)
        live.mkdir(parents=True)
        (live / "state.json").write_bytes(canonical({"revision": 7, "live": True}))
        # Live workflow state in the working directory is unreadable to every run.
        (self.cwd / ".autopilot").chmod(0o000)
        self.addCleanup((self.cwd / ".autopilot").chmod, 0o700)
        self.env = {
            "HOME": str(self.base / "home"),
            "TMPDIR": str(self.base / "tmp"),
            "PATH": "/usr/bin:/bin",
        }

    def run_isolated(
        self, script: Path, arguments: list[str]
    ) -> subprocess.CompletedProcess:
        code = GUARD.format(
            private=[str(ROOT), str(Path.home().resolve())], allowed=str(self.base)
        )
        return subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", code, str(script), *arguments],
            cwd=self.cwd,
            env=self.env,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def assert_exit(self, completed: subprocess.CompletedProcess, code: int) -> None:
        self.assertEqual(
            completed.returncode,
            code,
            completed.stderr.decode("utf-8", errors="replace"),
        )


class ControllerBundleReproducibleTest(IsolatedCase):
    def setUp(self) -> None:
        super().setUp()
        mirror = self.base / "checkout copy"
        self.plugin = copy_plugin(mirror / "plugins" / "autopilot")
        self.exporter = mirror / "tools" / "autopilot" / EXPORTER.name
        self.exporter.parent.mkdir(parents=True)
        shutil.copy2(EXPORTER, self.exporter)
        self.committed = BUNDLE.read_bytes()

    def export(self, *arguments: str) -> subprocess.CompletedProcess:
        return self.run_isolated(self.exporter, list(arguments))

    def test_controller_bundle_reproducible_default_export_writes_committed_bytes(
        self,
    ) -> None:
        target = self.plugin / TARGET
        target.unlink()
        before, cwd = stable_tree(self.plugin), tree(self.cwd)
        self.assert_exit(self.export(), 0)
        self.assertEqual(target.read_bytes(), self.committed)
        info = target.lstat()
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertEqual(info.st_nlink, 1)
        # No permission bit beyond the committed sibling contracts' bits.
        sibling = stat.S_IMODE((self.plugin / SCHEMA).lstat().st_mode)
        mode = stat.S_IMODE(info.st_mode)
        self.assertEqual(mode & ~sibling, 0, oct(mode))
        self.assertTrue(mode & stat.S_IRUSR, oct(mode))
        after = stable_tree(self.plugin)
        self.assertEqual(
            {key: value for key, value in after.items() if key != str(TARGET)}, before
        )
        self.assert_exit(self.export(), 0)
        self.assert_exit(self.export("--check"), 0)
        self.assertEqual(stable_tree(self.plugin), after)
        self.assertEqual(tree(self.cwd), cwd)

    def test_controller_bundle_reproducible_export_replaces_symlink_check_rejects_it(
        self,
    ) -> None:
        target = self.plugin / TARGET
        outside = self.base / "outside.json"
        victim = b'{"victim": true}\n'
        outside.write_bytes(victim)
        target.unlink()
        target.symlink_to(outside)
        self.assert_exit(self.export(), 0)
        self.assertEqual(outside.read_bytes(), victim)
        info = target.lstat()
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertEqual(info.st_nlink, 1)
        self.assertEqual(target.read_bytes(), self.committed)
        # A symlinked bundle is rejected even when its bytes match.
        outside.write_bytes(self.committed)
        target.unlink()
        target.symlink_to(outside)
        before = stable_tree(self.base)
        self.assert_exit(self.export("--check"), 1)
        self.assertEqual(stable_tree(self.base), before)

    def test_controller_bundle_reproducible_rejects_unknown_flags_without_writing(
        self,
    ) -> None:
        target = self.plugin / TARGET
        target.unlink()
        misuses = (
            ["--chek"],
            ["--check", "--plugin-root"],
            ["--plugin-root", str(self.plugin), "extra"],
        )
        for arguments in misuses:
            with self.subTest(arguments=arguments):
                before = stable_tree(self.base)
                self.assert_exit(self.export(*arguments), 2)
                self.assertEqual(stable_tree(self.base), before)
                self.assertFalse(os.path.lexists(target))

    def test_controller_bundle_reproducible_relocated_plugin_root_exports_same_bytes(
        self,
    ) -> None:
        other = copy_plugin(self.base / "elsewhere" / "plugin root" / "autopilot")
        (other / TARGET).unlink()
        # Covers the plugin root's parents, the other root, cwd, HOME and TMPDIR.
        before = stable_tree(self.base)
        self.assert_exit(self.export("--plugin-root", str(other)), 0)
        self.assertEqual((other / TARGET).read_bytes(), self.committed)
        after = stable_tree(self.base)
        written = str((other / TARGET).relative_to(self.base))
        self.assertEqual(
            {key: value for key, value in after.items() if key != written}, before
        )
        self.assert_exit(self.export("--check", "--plugin-root", str(other)), 0)
        self.assertEqual(stable_tree(self.base), after)
        self.assertEqual((self.plugin / TARGET).read_bytes(), self.committed)

    def test_controller_bundle_reproducible_export_reads_assets_of_given_plugin_root(
        self,
    ) -> None:
        other = copy_plugin(self.base / "relocated" / "autopilot")
        manifest = json.loads((other / "plugin.json").read_bytes())
        manifest["version"] = "9.8.7"
        (other / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (other / FIXTURES).write_bytes((other / FIXTURES).read_bytes() + b"\n")
        default_before = tree(self.plugin)
        self.assert_exit(self.export("--check", "--plugin-root", str(other)), 1)
        self.assertEqual((other / TARGET).read_bytes(), self.committed)
        self.assert_exit(self.export("--plugin-root", str(other)), 0)
        exported = strict_json((other / TARGET).read_bytes())
        committed = strict_json(self.committed)
        self.assertEqual(exported["package_version"], "9.8.7")
        self.assertEqual(exported["fixture_digest"], digest(other / FIXTURES))
        self.assertNotEqual(exported["fixture_digest"], committed["fixture_digest"])
        self.assertEqual(exported["schema_digest"], committed["schema_digest"])
        self.assertEqual(exported["schema_digest"], digest(other / SCHEMA))
        for key in ("protocol_major", "operations", "capabilities"):
            self.assertEqual(exported[key], committed[key], key)
        self.assert_exit(self.export("--check", "--plugin-root", str(other)), 0)
        self.assertEqual(tree(self.plugin), default_before)
        self.assert_exit(self.export("--check"), 0)
        (other / SCHEMA).write_bytes((other / SCHEMA).read_bytes() + b"\n")
        stale = (other / TARGET).read_bytes()
        self.assert_exit(self.export("--check", "--plugin-root", str(other)), 1)
        self.assertEqual((other / TARGET).read_bytes(), stale)
        self.assert_exit(self.export("--plugin-root", str(other)), 0)
        rewritten = strict_json((other / TARGET).read_bytes())
        self.assertEqual(rewritten["schema_digest"], digest(other / SCHEMA))
        self.assertNotEqual(rewritten["schema_digest"], committed["schema_digest"])
        self.assertEqual(rewritten["fixture_digest"], exported["fixture_digest"])
        self.assert_exit(self.export("--check", "--plugin-root", str(other)), 0)

    def test_controller_bundle_reproducible_export_rejects_non_string_or_empty_version(
        self,
    ) -> None:
        path = self.plugin / "plugin.json"
        manifest = json.loads(path.read_bytes())
        for version in (123, ""):
            with self.subTest(version=version):
                manifest_text = json.dumps(manifest | {"version": version}, indent=2)
                path.write_text(manifest_text + "\n")
                before = stable_tree(self.base)
                self.assertNotEqual(self.export().returncode, 0)
                self.assertEqual(stable_tree(self.base), before)
                self.assertEqual((self.plugin / TARGET).read_bytes(), self.committed)

    def test_controller_bundle_reproducible_check_fails_when_inputs_are_missing(
        self,
    ) -> None:
        for relative in (Path("plugin.json"), SCHEMA, FIXTURES):
            with self.subTest(missing=str(relative)):
                source = self.plugin / relative
                saved = source.read_bytes()
                source.unlink()
                before = stable_tree(self.base)
                self.assertNotEqual(self.export("--check").returncode, 0)
                self.assertEqual(stable_tree(self.base), before)
                self.assertEqual((self.plugin / TARGET).read_bytes(), self.committed)
                source.write_bytes(saved)
                self.assert_exit(self.export("--check"), 0)

    def test_controller_bundle_reproducible_check_rejects_missing_and_near_miss_bundles(
        self,
    ) -> None:
        target = self.plugin / TARGET
        bundle = strict_json(self.committed)
        schema_digest = bundle["schema_digest"].encode()
        fixture = bundle["fixture_digest"].encode()
        version = json.dumps(bundle["package_version"]).encode()
        same_length = {
            "flipped fixture digest": self.committed.replace(
                fixture, fixture[:-1] + (b"1" if fixture.endswith(b"0") else b"0")
            ),
            "renamed operation": self.committed.replace(
                b'"workflow.open"', b'"workflow.shut"'
            ),
            "drifted version": self.committed.replace(
                version,
                version[:-2] + (b"1" if version[-2:-1] == b"0" else b"0") + b'"',
                1,
            ),
        }
        variants = {
            "missing": None,
            "trailing newline": self.committed + b"\n",
            "truncated": self.committed[:-1],
            "stale digest": self.committed.replace(schema_digest, b"0" * 64),
        } | same_length
        for name, payload in variants.items():
            with self.subTest(variant=name):
                if payload is None:
                    target.unlink()
                else:
                    self.assertNotEqual(payload, self.committed)
                    target.write_bytes(payload)
                if name in same_length:
                    self.assertEqual(len(payload), len(self.committed))
                    self.assertNotEqual(strict_json(payload), bundle)
                before = tree(self.plugin)
                self.assert_exit(self.export("--check"), 1)
                self.assertEqual(tree(self.plugin), before)
                self.assertEqual(target.exists(), payload is not None)
                target.write_bytes(self.committed)
                self.assert_exit(self.export("--check"), 0)


class ControllerWithoutUpperLayersTest(IsolatedCase):
    def test_controller_without_upper_layers_guard_denies_checkout_and_author_home(
        self,
    ) -> None:
        probe = self.base / "probe" / "probe.py"
        probe.parent.mkdir()
        probe.write_text(
            "import json, sys\nfrom pathlib import Path\n"
            "print(json.dumps(sys.path))\nPath(sys.argv[1]).read_bytes()\n"
        )
        allowed = self.base / "inside.txt"
        allowed.write_bytes(b"sandbox")
        completed = self.run_isolated(probe, [str(allowed)])
        self.assert_exit(completed, 0)
        paths = json.loads(completed.stdout.splitlines()[0])
        self.assertEqual(Path(paths[0]), probe.parent)
        for entry in paths:
            self.assertFalse(Path(entry).resolve().is_relative_to(ROOT), entry)
            self.assertNotIn("site-packages", entry)
        for denied in (
            PLUGIN / "plugin.json",
            self.cwd / ".autopilot" / "controller" / "state.json",
            Path.home() / ".claude" / "settings.json",
        ):
            with self.subTest(denied=denied):
                completed = self.run_isolated(probe, [str(denied)])
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(b"PermissionError", completed.stderr)

    def exercise_install(self, install: Path) -> None:
        copy_plugin(install)
        before, cwd = tree(install), tree(self.cwd)
        main = install / "controller" / "main.py"
        bundle = strict_json((install / TARGET).read_bytes())
        plain = subprocess.run(
            [sys.executable, "-B", str(main), "--json", "contract"],
            cwd=self.cwd,
            env=self.env,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assert_exit(plain, 0)
        self.assert_runtime_matches(strict_json(plain.stdout), bundle)
        guarded = self.run_isolated(main, ["--json", "contract"])
        self.assert_exit(guarded, 0)
        self.assertEqual(strict_json(guarded.stdout), strict_json(plain.stdout))
        request = fresh_request(self.root)
        opened = self.run_isolated(
            main,
            [
                "--json",
                "apply",
                "--project-root",
                str(self.root),
                "--request",
                str(self.write_request(request)),
            ],
        )
        self.assert_open_consistent(request, self.response(opened, revision=0))
        self.assert_private()
        snapshot = self.run_isolated(
            main, ["--json", "snapshot", "--project-root", str(self.root)]
        )
        self.response(snapshot, revision=0)
        self.assertEqual(tree(install), before)
        self.assertEqual(tree(self.cwd), cwd)

    def test_controller_without_upper_layers_runs_end_to_end_from_two_install_roots(
        self,
    ) -> None:
        installs = (
            self.base / "install-a" / "autopilot",
            self.base / "plugin cache" / "buvis" / "autopilot-0.10.0",
        )
        for index, install in enumerate(installs):
            with self.subTest(install=install):
                self.root = self.base / f"project-{index}"
                self.root.mkdir()
                sibling = self.base / f"project-{index}-extra"
                sibling.mkdir()
                self.exercise_install(install)
                self.assertEqual(list(sibling.iterdir()), [])

    def test_controller_without_upper_layers_rejects_argument_misuse_without_state(
        self,
    ) -> None:
        install = copy_plugin(self.base / "install" / "autopilot")
        main = install / "controller" / "main.py"
        request = self.write_request(fresh_request(self.root))
        misuses = (
            ["--json", "apply", "--project-root", str(self.root)],
            ["--json", "snapshot"],
            ["--json", "apply", "--request", str(request)],
            ["--json", "export", "--project-root", str(self.root)],
        )
        for arguments in misuses:
            with self.subTest(arguments=arguments):
                self.assert_exit(self.run_isolated(main, arguments), 2)
                self.assertEqual(list(self.root.iterdir()), [])


class ContractBundlePinnableTest(BundleAssertions):
    def bundle(self) -> dict:
        value = strict_json(BUNDLE.read_bytes())
        self.assertIsInstance(value, dict)
        return value

    def test_contract_bundle_pinnable_regular_file_without_symlink_components(
        self,
    ) -> None:
        path = ROOT
        for part in Path(BUNDLE_RELATIVE).parts:
            path = path / part
            self.assertFalse(path.is_symlink(), path)
        info = BUNDLE.lstat()
        self.assertTrue(stat.S_ISREG(info.st_mode))
        self.assertGreater(info.st_size, 0)
        self.assertLess(info.st_size, LIMIT)

    def test_contract_bundle_pinnable_strict_object_with_exact_typed_keys(self) -> None:
        bundle = self.bundle()
        self.assertEqual(set(bundle), BUNDLE_KEYS)
        self.assertIs(type(bundle["protocol_major"]), int)
        self.assertEqual(bundle["protocol_major"], 1)
        manifest = json.loads((PLUGIN / "plugin.json").read_bytes())
        self.assertIs(type(bundle["package_version"]), str)
        self.assertEqual(bundle["package_version"], manifest["version"])
        self.assertNotEqual(bundle["package_version"], "")
        for key, source in (("schema_digest", SCHEMA), ("fixture_digest", FIXTURES)):
            self.assertIs(type(bundle[key]), str)
            self.assertRegex(bundle[key], "^[0-9a-f]{64}$")
            self.assertEqual(bundle[key], digest(PLUGIN / source))
        self.assertNotEqual(bundle["schema_digest"], bundle["fixture_digest"])
        for key, expected in (
            ("operations", OPERATIONS),
            ("capabilities", CAPABILITIES),
        ):
            self.assertIs(type(bundle[key]), list)
            self.assertTrue(all(type(item) is str for item in bundle[key]))
            self.assertEqual(len(bundle[key]), len(set(bundle[key])))
            self.assertEqual(set(bundle[key]), expected)

    def test_contract_bundle_pinnable_runtime_contract_matches_bundle(self) -> None:
        completed = cli(["--json", "contract"], cwd=ROOT / "tests")
        self.assertEqual(
            completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace")
        )
        self.assert_runtime_matches(strict_json(completed.stdout), self.bundle())

    def test_contract_bundle_pinnable_readme_documents_raw_digest_and_argv(
        self,
    ) -> None:
        raw = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
        text = README.read_text(encoding="utf-8")
        pin = f"{raw}  {BUNDLE_RELATIVE}"
        self.assertIn(pin, text)
        for line in text.splitlines():
            if "controller-v1.json" in line:
                for token in HEX.findall(line):
                    self.assertEqual(token, raw, line)
        # Every digest in the bundle pin's heading section is the raw digest.
        for line in heading_section(text, pin):
            for token in HEX.findall(line):
                self.assertEqual(token, raw, line)
        self.assertIn(INSTALLED_ARGV, text)
        # The argv is stated affirmatively, not only inside a prohibition.
        paragraphs = re.split(r"\n[ \t]*\n", text)
        affirmative = [
            block
            for block in paragraphs
            if INSTALLED_ARGV in block and not NEGATION.search(block)
        ]
        self.assertTrue(affirmative, "argv appears only beside a negation")


if __name__ == "__main__":
    unittest.main()
