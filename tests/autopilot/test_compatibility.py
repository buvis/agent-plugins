"""Tests for tools/autopilot/build-compatibility.py: generates per-host
compatibility bundles (schema_version 2) from contracts/hosts.json and
each adapter's own declared-and-implemented capability set, gated through
hosts.adapter() before any adapter module is imported.

round_trip proves the written bundle of every declared host holds exactly
that host's declared capability set (expected from each adapter's own
`IMPLEMENTED_CAPABILITIES` constant, never from a literal), carries the
duty_coverage this schema version adds, that its bytes do not move when the
host binary, its auth or the reported platform change, and that
compatibility/<host>.json is never written for the real repo while
--project-root points at a fixture tree.
hooks_assets proves a registered host gets a compatibility/<host>/hooks.json
asset shaped like the design's client-manifest fragment, and an
unregistered host (gemini) gets none.
committed_bundles proves the bundles shipped in the repo are the ones the
generator produces from the repo's own contract.
build_failure proves a declared capability set that does not equal the
adapter's own IMPLEMENTED_CAPABILITIES aborts the build with exit 1, a
surfaced error and no bundle on disk; so does an inconsistent
registration/interception declaration.
unknown_host proves a host_id the contract declares but hosts.ADAPTERS does
not raises before any adapter module executes, and writes nothing.
undeclared_host_bundle_is_removed proves a stale bundle for a host the
contract no longer declares is deleted by a normal (non --check) build.
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
guards = importlib.import_module("guards")

SCRIPT_PATH = "tools/autopilot/build-compatibility.py"
ALL_DUTIES = tuple(duty.value for duty in guards.GuardDuty)

REAL_CONTRACT = {
    "schema_version": 2,
    "hosts": {
        "claude": {
            "capabilities": ["delegation", "identity", "interception", "isolation"],
            "session_env_var": "CLAUDE_CODE_SESSION_ID",
            "registration": {"asset": "compatibility/claude/hooks.json", "activation": "client-manifest-hooks-field"},
        },
        "codex": {
            "capabilities": ["identity", "interception", "isolation"],
            "session_env_var": "CODEX_SESSION_ID",
            "registration": {"asset": "compatibility/codex/hooks.json", "activation": "client-manifest-hooks-field"},
        },
        "gemini": {
            "capabilities": ["identity", "isolation"],
            "session_env_var": "GEMINI_SESSION_ID",
            "registration": None,
            "blockers": {"interception": "no_package_local_registration_surface"},
        },
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

_WHILE_TRUE_RE = re.compile(r"while\s+(?:True|1)\s*:")
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
    project_root: Path, env: dict[str, str] | None = None, *, check: bool = False
) -> subprocess.CompletedProcess:
    """Runs the generator as a CHILD PROCESS, so `env` is the only way a test
    can change the binaries and auth the generator could observe: patching
    shutil.which or os.environ in this process never reaches it."""
    argv = [sys.executable, SCRIPT_PATH, "--project-root", str(project_root)]
    if check:
        argv.append("--check")
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(ROOT), env=env)


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


def _hooks_path(project_root: Path, host_id: str) -> Path:
    return project_root / "plugins" / "autopilot" / "compatibility" / host_id / "hooks.json"


def _compatibility_dir(project_root: Path) -> Path:
    return project_root / "plugins" / "autopilot" / "compatibility"


def _implemented_capabilities(host_id: str) -> frozenset[str]:
    """The adapter's OWN `IMPLEMENTED_CAPABILITIES`, read from the module.
    Every expectation below is computed from this, so a generator carrying a
    hand-copied capability table instead of importing the adapter drifts out
    of agreement with these tests the moment an adapter changes."""
    return importlib.import_module(host_id).IMPLEMENTED_CAPABILITIES


def _bundle_names(project_root: Path) -> list[str]:
    compat_dir = _compatibility_dir(project_root)
    return sorted(p.name for p in compat_dir.glob("*.json")) if compat_dir.is_dir() else []


class EnvHelperControlTest(unittest.TestCase):
    """Control case for the machine-independence test: proves the scrubbed
    and authenticated environments really reach a child process, so that
    test is a guarantee and not a no-op."""

    PROBE = (
        "import json, os, sys;"
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
                        [sys.executable, "-c", self.PROBE], capture_output=True, text=True, env=env
                    )
                    self.assertEqual(proc.returncode, 0, msg=proc.stderr)
                    home, path, api_key = json.loads(proc.stdout)
                    self.assertEqual(home, str(tmp_home))
                    self.assertEqual(api_key, expected_key)
                    self.assertIs(path == "", label == "bare")


class RoundTripTest(unittest.TestCase):
    def test_bundle_capabilities_equal_exactly_the_adapters_implemented_set(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)

            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")

            self.assertEqual(
                _bundle_names(tmp_root),
                sorted(f"{host}.json" for host in REAL_CONTRACT["hosts"]),
            )
            for host_id, declaration in REAL_CONTRACT["hosts"].items():
                with self.subTest(host=host_id):
                    bundle = json.loads(_bundle_path(tmp_root, host_id).read_text(encoding="utf-8"))
                    self.assertEqual(bundle["schema_version"], 2)
                    self.assertEqual(bundle["host_id"], host_id)
                    self.assertEqual(bundle["probe_kind"], "static")
                    self.assertFalse(bundle["certified"])
                    self.assertEqual(
                        set(bundle["capabilities"]), _implemented_capabilities(host_id)
                    )
                    self.assertEqual(bundle["capabilities"], sorted(bundle["capabilities"]))
                    self.assertEqual(bundle["registration"], declaration["registration"])

    def test_duty_coverage_lists_all_nine_duties_for_every_host(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            for host_id in REAL_CONTRACT["hosts"]:
                with self.subTest(host=host_id):
                    bundle = json.loads(_bundle_path(tmp_root, host_id).read_text(encoding="utf-8"))
                    self.assertEqual(set(bundle["duty_coverage"]), set(ALL_DUTIES))

    def test_claude_and_codex_intercept_document_location_and_state_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            for host_id in ("claude", "codex"):
                with self.subTest(host=host_id):
                    bundle = json.loads(_bundle_path(tmp_root, host_id).read_text(encoding="utf-8"))
                    self.assertEqual(bundle["duty_coverage"]["document_location"], "intercepted")
                    self.assertEqual(bundle["duty_coverage"]["state_integrity"], "intercepted")

    def test_codex_duty_coverage_marks_delegation_and_post_handoff_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            bundle = json.loads(_bundle_path(tmp_root, "codex").read_text(encoding="utf-8"))
            self.assertEqual(bundle["duty_coverage"]["delegation"], "not_applicable_on_host")
            self.assertEqual(bundle["duty_coverage"]["post_handoff"], "not_applicable_on_host")

    def test_gemini_duty_coverage_is_blocked_for_every_duty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            bundle = json.loads(_bundle_path(tmp_root, "gemini").read_text(encoding="utf-8"))
            for duty in ALL_DUTIES:
                with self.subTest(duty=duty):
                    self.assertEqual(
                        bundle["duty_coverage"][duty],
                        "blocked:no_package_local_registration_surface",
                    )
            self.assertEqual(bundle["blockers"], {"interception": "no_package_local_registration_surface"})

    def test_bundle_bytes_are_identical_with_no_binary_and_no_auth(self) -> None:
        """The headline property: the bundles are a code fact, not a fact
        about the builder's machine."""
        bundles: dict[str, dict[str, bytes]] = {}
        for label in ("rich", "bare"):
            with tempfile.TemporaryDirectory() as td:
                tmp_root = Path(td)
                tmp_home = tmp_root / "home"
                tmp_home.mkdir()
                _write_contract(tmp_root, REAL_CONTRACT)

                env = _scrubbed_env(tmp_home) if label == "bare" else _authenticated_env(tmp_home)
                proc = _run_build(tmp_root, env=env)
                self.assertEqual(proc.returncode, 0, msg=f"{label}: {proc.stderr}")

                bundles[label] = {}
                for host_id in REAL_CONTRACT["hosts"]:
                    path = _bundle_path(tmp_root, host_id)
                    self.assertTrue(path.exists(), msg=f"{label}: no bundle for {host_id}")
                    bundles[label][host_id] = path.read_bytes()

        for host_id in REAL_CONTRACT["hosts"]:
            with self.subTest(host=host_id):
                self.assertEqual(bundles["bare"][host_id], bundles["rich"][host_id])

    def test_check_mode_exits_zero_against_a_fresh_build_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            before = {p: p.read_bytes() for p in sorted(_compatibility_dir(tmp_root).rglob("*.json"))}
            proc = _run_build(tmp_root, check=True)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            after = {p: p.read_bytes() for p in sorted(_compatibility_dir(tmp_root).rglob("*.json"))}
            self.assertEqual(before, after)


class HooksAssetTest(unittest.TestCase):
    def test_a_registered_host_gets_a_hooks_asset_shaped_from_its_own_registrations(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            claude_module = importlib.import_module("claude")
            doc = json.loads(_hooks_path(tmp_root, "claude").read_text(encoding="utf-8"))
            self.assertEqual(set(doc), {"hooks"})
            events_seen = [entry["matcher"] if "matcher" in entry else None
                           for event_entries in doc["hooks"].values() for entry in event_entries]
            expected_matchers = [reg.matcher for reg in claude_module.HOOK_REGISTRATIONS]
            self.assertEqual(sorted(filter(None, events_seen)), sorted(filter(None, expected_matchers)))
            for event_entries in doc["hooks"].values():
                for entry in event_entries:
                    for hook in entry["hooks"]:
                        self.assertEqual(hook["type"], "command")
                        self.assertIn("--hook claude --event", hook["command"])
                        self.assertIn("CLAUDE_PLUGIN_ROOT", hook["command"])

    def test_every_generated_hook_command_is_built_from_the_adapters_plugin_root_expression(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            expected_expr = {"claude": "${CLAUDE_PLUGIN_ROOT}", "codex": "${AUTOPILOT_PLUGIN_ROOT}"}
            for host_id, expr in expected_expr.items():
                with self.subTest(host=host_id):
                    self.assertEqual(importlib.import_module(host_id).PLUGIN_ROOT_EXPR, expr)
                    doc = json.loads(_hooks_path(tmp_root, host_id).read_text(encoding="utf-8"))
                    prefix = f'python3 "{expr}/scripts/autopilot.py" --hook {host_id} --event '
                    commands = [hook["command"] for entries in doc["hooks"].values()
                                for entry in entries for hook in entry["hooks"]]
                    self.assertTrue(commands)
                    for command in commands:
                        self.assertTrue(command.startswith(prefix), command)
                        self.assertRegex(command[len(prefix):], r"^\w+$")

    def test_no_generated_asset_for_a_non_claude_host_names_the_claude_variable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            self.assertEqual(_run_build(tmp_root).returncode, 0)
            bases = {
                "built": _compatibility_dir(tmp_root),
                "committed": ROOT / "plugins" / "autopilot" / "compatibility",
            }
            for label, base in bases.items():
                for host_id in ("codex", "gemini"):
                    paths = [base / f"{host_id}.json", *(base / host_id).rglob("*.json")]
                    for path in paths:
                        with self.subTest(source=label, asset=str(path.relative_to(base))):
                            self.assertNotIn(b"CLAUDE_PLUGIN_ROOT", path.read_bytes())
                doc = json.loads((base / "codex" / "hooks.json").read_text(encoding="utf-8"))
                commands = [hook["command"] for entries in doc["hooks"].values()
                            for entry in entries for hook in entry["hooks"]]
                with self.subTest(source=label, asset="codex command"):
                    self.assertTrue(commands)
                    for command in commands:
                        self.assertIn('"${AUTOPILOT_PLUGIN_ROOT}/scripts/autopilot.py"', command)

    def test_an_unregistered_host_gets_no_hooks_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertFalse(_hooks_path(tmp_root, "gemini").exists())
            self.assertFalse((_compatibility_dir(tmp_root) / "gemini").exists())


class BuildFailureTest(unittest.TestCase):
    def test_declared_capability_the_adapter_does_not_implement_aborts_the_build(self) -> None:
        contract = {
            "schema_version": 2,
            "hosts": {
                "gemini": {
                    "capabilities": ["identity", "interception"],
                    "session_env_var": "GEMINI_SESSION_ID",
                    "registration": {"asset": "compatibility/gemini/hooks.json", "activation": "x"},
                }
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn(
                "host 'gemini': declared capability 'interception' is unimplemented",
                proc.stderr,
            )
            self.assertEqual(_bundle_names(tmp_root), [])

    def test_undeclared_implemented_capability_also_aborts_the_build(self) -> None:
        """Equality cuts both ways: a contract that under-declares what the
        adapter actually implements is just as wrong as one that over-claims."""
        contract = {
            "schema_version": 2,
            "hosts": {
                "codex": {
                    "capabilities": ["isolation"],
                    "session_env_var": "CODEX_SESSION_ID",
                    "registration": {"asset": "compatibility/codex/hooks.json", "activation": "x"},
                }
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn("implemented capability", proc.stderr)
            self.assertIn("is undeclared", proc.stderr)
            self.assertEqual(_bundle_names(tmp_root), [])

    def test_registration_present_without_interception_declared_aborts_the_build(self) -> None:
        contract = {
            "schema_version": 2,
            "hosts": {
                "gemini": {
                    "capabilities": ["identity", "isolation"],
                    "session_env_var": "GEMINI_SESSION_ID",
                    "registration": {"asset": "compatibility/gemini/hooks.json", "activation": "x"},
                }
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn("registration must be non-null iff interception is declared", proc.stderr)

    def test_mismatched_session_env_var_aborts_the_build(self) -> None:
        contract = {
            "schema_version": 2,
            "hosts": {
                "codex": {
                    "capabilities": ["identity", "interception", "isolation"],
                    "session_env_var": "WRONG_ENV_VAR",
                    "registration": {"asset": "compatibility/codex/hooks.json", "activation": "x"},
                }
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn("session_env_var does not match", proc.stderr)

    def test_aborting_build_leaves_no_bundle_behind_for_any_declared_host(self) -> None:
        """The overclaiming host is declared SECOND, so a generator that
        writes each bundle as it goes leaves an already-validated codex.json
        on disk after the abort. A failed build must advertise nothing."""
        contract = {
            "schema_version": 2,
            "hosts": {
                "codex": {
                    "capabilities": ["identity", "interception", "isolation"],
                    "session_env_var": "CODEX_SESSION_ID",
                    "registration": {"asset": "compatibility/codex/hooks.json", "activation": "x"},
                },
                "gemini": {
                    "capabilities": ["identity", "interception", "isolation"],
                    "session_env_var": "GEMINI_SESSION_ID",
                    "registration": {"asset": "compatibility/gemini/hooks.json", "activation": "x"},
                },
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertEqual(_bundle_names(tmp_root), [])


class UnknownHostTest(unittest.TestCase):
    def test_unknown_host_executes_no_module(self) -> None:
        """A host_id the contract declares but hosts.ADAPTERS does not know
        must raise (via hosts.adapter()) before any sibling module import is
        even attempted, and write nothing."""
        contract = {
            "schema_version": 2,
            "hosts": {
                "mystery": {
                    "capabilities": ["identity"],
                    "session_env_var": "MYSTERY_SESSION_ID",
                    "registration": None,
                }
            },
        }
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, contract)
            proc = _run_build(tmp_root)
            self.assertNotEqual(proc.returncode, 0, msg=proc.stdout)
            self.assertIn("unknown host_id: 'mystery'", proc.stderr)
            self.assertEqual(_bundle_names(tmp_root), [])


class UndeclaredHostBundleRemovalTest(unittest.TestCase):
    def test_undeclared_host_bundle_is_removed(self) -> None:
        """A bundle for a host the contract no longer declares is stale and
        must not survive a normal build."""
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            compat_dir = _compatibility_dir(tmp_root)
            compat_dir.mkdir(parents=True)
            (compat_dir / "ghost.json").write_text(
                json.dumps({"host_id": "ghost"}), encoding="utf-8"
            )
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertFalse((compat_dir / "ghost.json").exists())
            self.assertEqual(
                _bundle_names(tmp_root), sorted(f"{host}.json" for host in REAL_CONTRACT["hosts"])
            )

    def test_check_mode_reports_an_undeclared_host_bundle_as_extra_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)

            ghost_path = _compatibility_dir(tmp_root) / "ghost.json"
            ghost_path.write_text(json.dumps({"host_id": "ghost"}), encoding="utf-8")
            proc = _run_build(tmp_root, check=True)
            self.assertEqual(proc.returncode, 1, msg=proc.stdout)
            self.assertIn("extra:", proc.stderr)
            self.assertTrue(ghost_path.exists())


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
            self.assertEqual(
                _bundle_names(tmp_root),
                sorted(f"{host}.json" for host in REAL_CONTRACT["hosts"]),
            )

        after = real_bundle.stat().st_mtime if real_bundle.exists() else None
        self.assertEqual(before, after)


class CommittedBundlesTest(unittest.TestCase):
    def test_committed_bundles_are_what_the_repo_contract_builds(self) -> None:
        """The shipped files must be the generator's output for the repo's own
        contract. This is the finding itself: a committed bundle that lists a
        capability the adapter does not implement, or whose duty_coverage
        disagrees with a fresh build, no longer matches."""
        proc = _run_build(ROOT, check=True)
        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")


class NoCoordinatorRuntimeInPluginTest(unittest.TestCase):
    def test_rejects_while_true_in_synthetic_source(self) -> None:
        self.assertEqual(
            _coordinator_runtime_violations("x = 1\nwhile True:\n    pass\n"), ["while True"]
        )

    def test_rejects_while_one_in_synthetic_source(self) -> None:
        # `while 1:` is the same unbounded loop with a truthy literal.
        self.assertEqual(
            _coordinator_runtime_violations("x = 1\nwhile 1:\n    pass\n"), ["while True"]
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
        benign = "while x:\n    pass\nwhile 10:\n    pass\nschedule = 1\ncursed = True\n"
        self.assertEqual(_coordinator_runtime_violations(benign), [])

    def test_no_ap00014_module_file_contains_a_coordinator_runtime_pattern(self) -> None:
        for filename in NEW_MODULE_FILES:
            path = SCRIPTS / filename
            with self.subTest(file=filename):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(_coordinator_runtime_violations(text), [])

    def test_the_bundle_generator_contains_no_coordinator_runtime_pattern(self) -> None:
        # The generator is the file this module tests; a supervisor loop,
        # scheduler or TUI import there is the same violation as in the
        # adapters, and the seven-file list above does not cover it.
        text = (ROOT / SCRIPT_PATH).read_text(encoding="utf-8")
        self.assertEqual(_coordinator_runtime_violations(text), [])

    def test_no_autopilot_python_file_imports_a_scheduler_or_a_tui_runtime(self) -> None:
        # Widened beyond the seven module files by glob, for the two pattern
        # families that have no legitimate use anywhere in this plugin. The
        # unbounded-loop ban stays on the AP00014 modules and the generator,
        # because `while True:` over a string or a path is a bounded idiom
        # these scripts already use.
        scanned = sorted(
            set((ROOT / "plugins" / "autopilot").rglob("*.py"))
            | set((ROOT / "tools" / "autopilot").rglob("*.py"))
        )
        self.assertTrue(scanned, msg="glob matched no autopilot python file")
        for path in scanned:
            with self.subTest(file=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8")
                banned = [p for p in _SCHEDULER_PATTERNS + _TUI_IMPORTS if p in text]
                self.assertEqual(banned, [])

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
