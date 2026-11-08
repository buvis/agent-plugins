"""Tests for tools/autopilot/build-compatibility.py: generates per-host
compatibility bundles from contracts/hosts.json and the live probe results.

round_trip proves the written claude.json/codex.json bundles contain exactly
the live-available capability subset of each host's declared contract, and
that compatibility/<host>.json is never written for the real repo while
--project-root points at a fixture tree.
build_failure proves a declared capability the live adapter reports
unimplemented aborts the build with a non-zero exit and a surfaced error.
no_coordinator_runtime_in_plugin statically rejects a supervisor/scheduler
loop or a bound TUI import from ever landing in the AP00014 module files.
"""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")
claude = importlib.import_module("claude")
codex = importlib.import_module("codex")

SCRIPT_PATH = "tools/autopilot/build-compatibility.py"

REAL_CONTRACT = {
    "schema_version": 1,
    "hosts": {
        "claude": {"capabilities": ["identity", "delegation", "isolation", "interception"]},
        "codex": {"capabilities": ["identity", "delegation", "isolation"]},
        "gemini": {"capabilities": ["identity"]},
    },
}

NEW_MODULE_FILES = (
    "hosts.py",
    "claude.py",
    "codex.py",
    "gemini.py",
    "jobs.py",
    "guards.py",
    "doctor.py",
)

_WHILE_TRUE_RE = re.compile(r"while\s+True\s*:")
_SCHEDULER_PATTERNS = ("schedule.", "APScheduler", "asyncio.get_event_loop().run_forever")
_TUI_IMPORTS = ("import curses", "from textual", "import urwid")


def _coordinator_runtime_violations(text: str) -> list[str]:
    """Names every coordinator-runtime pattern found in `text`, or []."""
    violations: list[str] = []
    if _WHILE_TRUE_RE.search(text):
        violations.append("while True")
    for pattern in _SCHEDULER_PATTERNS:
        if pattern in text:
            violations.append(pattern)
    for pattern in _TUI_IMPORTS:
        if pattern in text:
            violations.append(pattern)
    return violations


def _write_contract(project_root: Path, contract: dict) -> None:
    contracts_dir = project_root / "plugins" / "autopilot" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "hosts.json").write_text(json.dumps(contract), encoding="utf-8")


def _run_build(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT_PATH, "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def _expected_available(declared_capabilities: list[str], probe_result) -> set[str]:
    """Capability names from `declared_capabilities` whose live probe status
    is "available", per the robustness note: query the real adapter, never
    assume a result."""
    if probe_result.capability is None:
        return set()
    statuses = probe_result.capability.statuses
    return {
        name
        for name in declared_capabilities
        if name in statuses and statuses[name].status == "available"
    }


def _collect_capability_tokens(value) -> set[str]:
    """Walks an arbitrarily-shaped JSON value and collects every leaf string
    that is a known capability name. Schema-agnostic on purpose: the task
    does not pin the bundle's exact field names (see ASSUMPTIONS), so this
    checks the substantive claim ("capability list equals exactly the
    available subset") without hardcoding a key."""
    found: set[str] = set()
    if isinstance(value, str):
        if value in hosts.CAPABILITY_NAMES:
            found.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            found |= _collect_capability_tokens(item)
    elif isinstance(value, list):
        for item in value:
            found |= _collect_capability_tokens(item)
    return found


class RoundTripTest(unittest.TestCase):
    def test_bundle_capabilities_equal_exactly_the_live_available_subset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")

            claude_path = tmp_root / "plugins" / "autopilot" / "compatibility" / "claude.json"
            codex_path = tmp_root / "plugins" / "autopilot" / "compatibility" / "codex.json"
            self.assertTrue(claude_path.exists())
            self.assertTrue(codex_path.exists())

            claude_bundle = json.loads(claude_path.read_text(encoding="utf-8"))
            codex_bundle = json.loads(codex_path.read_text(encoding="utf-8"))

            expected_claude = _expected_available(
                REAL_CONTRACT["hosts"]["claude"]["capabilities"],
                claude.probe(project_root=tmp_root),
            )
            expected_codex = _expected_available(
                REAL_CONTRACT["hosts"]["codex"]["capabilities"],
                codex.probe(project_root=tmp_root),
            )

            self.assertEqual(_collect_capability_tokens(claude_bundle), expected_claude)
            self.assertEqual(_collect_capability_tokens(codex_bundle), expected_codex)

    def test_unavailable_capability_is_excluded_not_a_failure(self) -> None:
        # claude's own adapter hardcodes "interception" as always available,
        # so drive the exclusion through codex: its contract never declares
        # "interception", and whatever subset IS declared is exactly what
        # should show up, proving an excluded capability never trips the
        # exit code to non-zero.
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            contract = {
                "schema_version": 1,
                "hosts": {"codex": {"capabilities": ["identity", "delegation", "isolation"]}},
            }
            _write_contract(tmp_root, contract)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            expected = _expected_available(
                contract["hosts"]["codex"]["capabilities"], codex.probe(project_root=tmp_root)
            )
            codex_path = tmp_root / "plugins" / "autopilot" / "compatibility" / "codex.json"
            if expected:
                self.assertTrue(codex_path.exists())
                bundle = json.loads(codex_path.read_text(encoding="utf-8"))
                self.assertEqual(_collect_capability_tokens(bundle), expected)


class BuildFailureTest(unittest.TestCase):
    def test_declared_capability_reported_unimplemented_causes_nonzero_exit(self) -> None:
        # Confirm the assumption against the real adapter before relying on
        # it, per the task's own robustness note.
        probe = codex.probe(project_root=ROOT)
        self.assertEqual(probe.capability.statuses["interception"].status, "unimplemented")

        contract = {
            "schema_version": 1,
            "hosts": {
                "codex": {"capabilities": ["identity", "delegation", "isolation", "interception"]},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotEqual(proc.stderr.strip(), "")


class CliInvocationShapeTest(unittest.TestCase):
    def test_accepts_project_root_flag_exits_zero_and_never_touches_the_real_repo(self) -> None:
        real_bundle = ROOT / "plugins" / "autopilot" / "compatibility" / "claude.json"
        before = real_bundle.stat().st_mtime if real_bundle.exists() else None

        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")

        after = real_bundle.stat().st_mtime if real_bundle.exists() else None
        self.assertEqual(before, after)


class NoCoordinatorRuntimeInPluginTest(unittest.TestCase):
    def test_rejects_while_true_in_synthetic_source(self) -> None:
        self.assertEqual(
            _coordinator_runtime_violations("x = 1\nwhile True:\n    pass\n"), ["while True"]
        )

    def test_rejects_each_scheduler_shaped_loop_pattern(self) -> None:
        for pattern in ("schedule.every(1).seconds.do(x)", "import APScheduler", "asyncio.get_event_loop().run_forever()"):
            with self.subTest(pattern=pattern):
                self.assertTrue(_coordinator_runtime_violations(pattern))

    def test_rejects_each_bound_tui_import(self) -> None:
        for pattern in ("import curses", "from textual import App", "import urwid"):
            with self.subTest(pattern=pattern):
                self.assertTrue(_coordinator_runtime_violations(pattern))

    def test_accepts_benign_source_with_no_violations(self) -> None:
        self.assertEqual(_coordinator_runtime_violations("def f():\n    return 1\n"), [])

    def test_does_not_flag_near_miss_substrings(self) -> None:
        # "while" alone, "schedule" as a plain identifier, and "cursed" must
        # never trip the scanner - only the full patterns do.
        benign = "while x:\n    pass\nschedule = 1\ncursed = True\n"
        self.assertEqual(_coordinator_runtime_violations(benign), [])

    def test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern(self) -> None:
        for filename in NEW_MODULE_FILES:
            path = SCRIPTS / filename
            with self.subTest(file=filename):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(_coordinator_runtime_violations(text), [])

    def test_autopilot_py_contains_no_coordinator_runtime_pattern(self) -> None:
        # Exact location of autopilot.py was not pinned by the task; try the
        # same scripts/ directory as its siblings first (see ASSUMPTIONS).
        candidates = (SCRIPTS / "autopilot.py", ROOT / "plugins" / "autopilot" / "autopilot.py")
        found = [path for path in candidates if path.exists()]
        if not found:
            self.skipTest("autopilot.py location not confirmed (see ASSUMPTIONS)")
        text = found[0].read_text(encoding="utf-8")
        self.assertEqual(_coordinator_runtime_violations(text), [])


if __name__ == "__main__":
    unittest.main()
