"""Tests for tools/autopilot/build-compatibility.py: generates per-host
compatibility bundles from contracts/hosts.json and each adapter's own
declared-and-implemented capability set.

round_trip proves the written bundle of every declared host holds exactly
that host's declared capability set, that its bytes do not move when the
host binary and its auth disappear, and that compatibility/<host>.json is
never written for the real repo while --project-root points at a fixture
tree.
build_failure proves a declared capability the adapter does not implement
aborts the build with exit 1 and a surfaced error.
no_coordinator_runtime_in_plugin statically rejects a supervisor/scheduler
loop or a bound TUI import from ever landing in the AP00014 module files.
"""

from __future__ import annotations

import importlib
import json
import os
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

SCRIPT_PATH = "tools/autopilot/build-compatibility.py"

REAL_CONTRACT = {
    "schema_version": 1,
    "hosts": {
        "claude": {"capabilities": ["delegation", "identity", "interception", "isolation"]},
        "codex": {"capabilities": ["isolation"]},
        "gemini": {"capabilities": []},
    },
}

_AUTH_VARS = (
    "CODEX_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
)

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


def _run_build(
    project_root: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Runs the generator as a CHILD PROCESS, so `env` is the only way a test
    can change the binaries and auth the generator could observe: patching
    shutil.which or os.environ in this process never reaches it."""
    return subprocess.run(
        [sys.executable, SCRIPT_PATH, "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )


def _scrubbed_env(tmp_home: Path) -> dict[str, str]:
    """An environment where no host binary is reachable and no host auth
    exists: empty PATH, every auth variable removed, and HOME moved to a
    temp dir so codex's `~/.codex/auth.json` cannot leak the developer's
    real auth into the child."""
    env = {k: v for k, v in os.environ.items() if k not in _AUTH_VARS}
    env["PATH"] = ""
    env["HOME"] = str(tmp_home)
    return env


def _authenticated_env(tmp_home: Path) -> dict[str, str]:
    """The opposite extreme of `_scrubbed_env`: the real PATH plus a dummy
    value for every host auth variable, so the two runs genuinely differ in
    both binary and auth presence."""
    env = _scrubbed_env(tmp_home)
    env["PATH"] = os.environ.get("PATH", "")
    for name in _AUTH_VARS:
        env[name] = "dummy"
    return env


def _bundle_path(project_root: Path, host_id: str) -> Path:
    return project_root / "plugins" / "autopilot" / "compatibility" / f"{host_id}.json"


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


class EnvHelperControlTest(unittest.TestCase):
    """Control case for the machine-independence test: proves the scrubbed
    and authenticated environments really reach a child process, so that
    test is a guarantee and not a no-op."""

    PROBE = (
        "import json, os;"
        "print(json.dumps([os.environ['HOME'], os.environ['PATH'],"
        " os.environ.get('CODEX_API_KEY')]))"
    )

    def test_scrubbed_and_authenticated_envs_reach_the_child_process(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_home = Path(td)
            cases = (
                ("bare", _scrubbed_env(tmp_home), None),
                ("rich", _authenticated_env(tmp_home), "dummy"),
            )
            for label, env, expected_key in cases:
                with self.subTest(env=label):
                    proc = subprocess.run(
                        [sys.executable, "-c", self.PROBE],
                        capture_output=True,
                        text=True,
                        env=env,
                    )
                    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                    home, path, api_key = json.loads(proc.stdout)
                    self.assertEqual(home, str(tmp_home))
                    self.assertEqual(api_key, expected_key)
                    self.assertIs(path == "", label == "bare")


class RoundTripTest(unittest.TestCase):
    def test_bundle_capabilities_equal_exactly_the_declared_implemented_set(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")

            for host_id, declared in REAL_CONTRACT["hosts"].items():
                with self.subTest(host=host_id):
                    # gemini is the load-bearing case: it declares nothing and
                    # its binary may be absent, yet a bundle must still exist.
                    path = _bundle_path(tmp_root, host_id)
                    self.assertTrue(path.exists(), msg=f"no bundle for {host_id}")
                    bundle = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        _collect_capability_tokens(bundle), set(declared["capabilities"])
                    )
                    self.assertEqual(
                        bundle["capabilities"], sorted(declared["capabilities"])
                    )
                    self.assertEqual(bundle["host_id"], host_id)
                    self.assertEqual(bundle["probe_kind"], "static")

    def test_bundle_bytes_are_indent_two_json_with_a_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            contract = {
                "schema_version": 1,
                "hosts": {"codex": {"capabilities": ["isolation"]}},
            }
            _write_contract(tmp_root, contract)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            expected = {
                "host_id": "codex",
                "capabilities": ["isolation"],
                "probe_kind": "static",
            }
            text = _bundle_path(tmp_root, "codex").read_text(encoding="utf-8")
            self.assertEqual(text, json.dumps(expected, indent=2) + "\n")

    def test_bundle_capabilities_are_sorted_whatever_order_the_contract_used(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            contract = {
                "schema_version": 1,
                "hosts": {
                    "claude": {
                        "capabilities": [
                            "isolation",
                            "interception",
                            "identity",
                            "delegation",
                        ]
                    }
                },
            }
            _write_contract(tmp_root, contract)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            bundle = json.loads(
                _bundle_path(tmp_root, "claude").read_text(encoding="utf-8")
            )
            self.assertEqual(
                bundle["capabilities"],
                ["delegation", "identity", "interception", "isolation"],
            )

    def test_bundle_bytes_are_identical_with_no_binary_and_no_auth(self) -> None:
        """The headline property: the bundles are a code fact, not a fact
        about the builder's machine. Each run gets its OWN fresh root, so a
        generator that skips a host cannot pass by leaving the other run's
        file behind - the stale-bundle behaviour this test exists to kill."""
        bundles: dict[str, dict[str, bytes]] = {}
        for label, scrub in (("rich", False), ("bare", True)):
            with tempfile.TemporaryDirectory() as td:
                tmp_root = Path(td)
                tmp_home = tmp_root / "home"
                tmp_home.mkdir()
                _write_contract(tmp_root, REAL_CONTRACT)

                env = _scrubbed_env(tmp_home) if scrub else _authenticated_env(tmp_home)
                proc = _run_build(tmp_root, env=env)
                self.assertEqual(proc.returncode, 0, msg=f"{label}: {proc.stderr}")

                bundles[label] = {}
                for host_id in REAL_CONTRACT["hosts"]:
                    path = _bundle_path(tmp_root, host_id)
                    self.assertTrue(
                        path.exists(), msg=f"{label}: no bundle for {host_id}"
                    )
                    bundles[label][host_id] = path.read_bytes()

        for host_id in REAL_CONTRACT["hosts"]:
            with self.subTest(host=host_id):
                self.assertEqual(bundles["bare"][host_id], bundles["rich"][host_id])


class BuildFailureTest(unittest.TestCase):
    def test_declared_capability_the_adapter_does_not_implement_aborts_the_build(
        self,
    ) -> None:
        contract = {
            "schema_version": 1,
            "hosts": {"gemini": {"capabilities": ["identity"]}},
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn("is unimplemented", proc.stderr)
            self.assertIn(
                "host 'gemini': declared capability 'identity' is unimplemented",
                proc.stderr,
            )

    def test_abort_names_the_first_overclaimed_capability_in_sorted_order(self) -> None:
        contract = {
            "schema_version": 1,
            "hosts": {"codex": {"capabilities": ["isolation", "interception", "delegation"]}},
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn(
                "host 'codex': declared capability 'delegation' is unimplemented",
                proc.stderr,
            )
            self.assertNotIn("'interception' is unimplemented", proc.stderr)


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
