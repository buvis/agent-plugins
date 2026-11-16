"""`delegation` is a reported capability: observed for a delegation-capable host
only when the bound runs traced both an allowed parent dispatch and a nested
dispatch refused with `recursion_depth`. prepare() validates the resources the
bundle declares before any launch, and run_live separates a containment
failure (`resource_escape`, check `failed`) from any other preparation failure
(`preparation_failed`, check `not_run`)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from probe_host_support import install_fake_hosts
from test_host_argv import OBSERVED, LiveProbeCase, _trace
from test_probe_host_resource_containment import (
    CAPABILITIES,
    _load_probe_host,
    _write_valid_hooks,
)

PARENT_ALLOWED = {"duty": "delegation", "allowed": True, "reason": None}
# guards._deny prefixes a stateless refusal's reason with its own duty name,
# which test_guards_pure_duties.py pins; the bare cause never reaches a trace.
NESTED_REFUSED = {"duty": "delegation", "allowed": False, "reason": "delegation: recursion_depth"}
TRACE_REL = Path("docs") / "dev" / "tmp" / "autopilot" / "hook-trace.jsonl"


def _not_observed(reason: str) -> dict:
    return {"status": "not_observed", "reason": reason}


def _delegation_outcomes(lines: list[dict]) -> list[dict]:
    return [o for line in lines for o in line.get("outcomes", []) if o.get("duty") == "delegation"]


class ProbeHostDelegationTest(LiveProbeCase):
    def test_claude_observes_delegation_from_an_allowed_parent_and_a_refused_nested_dispatch(self) -> None:
        run = self.probe("claude")
        self.assertEqual(run["record"]["observed"]["delegation"], OBSERVED)
        bound = _trace(run["run_dir"] / "project" / TRACE_REL)
        control = _trace(run["run_dir"] / "control" / TRACE_REL)
        outcomes = _delegation_outcomes(bound)
        self.assertEqual(outcomes.count(PARENT_ALLOWED), 2, outcomes)
        self.assertEqual(outcomes.count(NESTED_REFUSED), 2, outcomes)
        self.assertEqual(_delegation_outcomes(control), [])

    def test_delegation_reports_the_precise_gap_when_one_half_of_the_scenario_is_missing(self) -> None:
        cases = (
            ("no_nested", "nested_dispatch_not_refused"),
            ("no_parent", "parent_dispatch_not_allowed"),
            ("no_dispatch", "delegation_not_traced"),
            ("silent_refusal", "delegation_not_traced"),
        )
        for mode, reason in cases:
            with self.subTest(mode=mode):
                observed = self.probe("claude", mode)["record"]["observed"]
                self.assertEqual(observed["delegation"], _not_observed(reason))
                if mode != "silent_refusal":
                    for capability in ("identity", "isolation", "interception", "resources"):
                        self.assertEqual(observed[capability], OBSERVED, capability)

    def test_delegation_is_not_implemented_for_a_host_whose_adapter_omits_it(self) -> None:
        record = self.probe("codex")["record"]
        self.assertEqual(record["observed"]["delegation"], _not_observed("capability_not_implemented"))
        self.assertEqual(record["observed"]["interception"], OBSERVED)

    def test_only_the_delegation_capable_hosts_bound_prompts_carry_a_dispatch_scenario(self) -> None:
        claude = self.probe("claude")
        bound, control = claude["calls"][:2], claude["calls"][2]
        for call in bound:
            self.assertIn("dispatch", call["prompt"].lower())
            self.assertIn("nested", call["prompt"].lower())
        self.assertNotIn("dispatch", control["prompt"].lower())
        codex = self.probe("codex")
        for call in codex["calls"]:
            self.assertNotIn("dispatch", call["prompt"].lower())

    def test_a_failed_or_escaped_run_still_reports_delegation_with_the_failure_reason(self) -> None:
        cases = (("claude", "fail", "host_failed"), ("claude", "escape", "resource_escape"),
                 ("codex", "fail", "host_failed"))
        for host_id, mode, reason in cases:
            with self.subTest(host_id=host_id, mode=mode):
                record = self.probe(host_id, mode)["record"]
                self.assertEqual(record["observed"]["delegation"], _not_observed(reason))


class ProbeHostPreparationTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.module = _load_probe_host()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        install_fake_hosts(self.bin_dir)
        self.log = self.root / "launches.jsonl"
        patcher = mock.patch.dict(os.environ, {
            "PATH": f"{self.bin_dir}{os.pathsep}{os.environ['PATH']}",
            "FAKE_HOST_LOG": str(self.log), "FAKE_HOST_MODE": "honest",
            "FAKE_FOREIGN_ROOT": str(self.root),
        })
        patcher.start()
        self.addCleanup(patcher.stop)

    def _source(self, name: str, host_id: str = "claude", script: str = "scripts/autopilot.py") -> Path:
        source = self.root / f"source-{name}"
        _write_valid_hooks(source, host_id, script)
        self.module.SOURCE_PLUGIN = source
        return source

    def _live(self, host_id: str, run_dir: Path) -> dict:
        return self.module.run_live(host_id, run_dir, self.root, 5.0)

    def assert_failed_before_launch(self, result: dict, reason: str, resource_check: str) -> None:
        for capability in CAPABILITIES:
            self.assertEqual(result["observed"][capability], _not_observed(reason), capability)
        self.assertEqual(result["resource_check"], resource_check)
        self.assertEqual(result["invocations"], [])
        self.assertEqual(result["trace_lines"], 0)
        self.assertEqual(result["registration_surface"], "none")
        self.assertFalse(self.log.exists(), "a host was launched after a failed preparation")

    def test_a_missing_declared_hook_script_fails_preparation_and_launches_nothing(self) -> None:
        for host_id in ("claude", "codex"):
            with self.subTest(host_id=host_id):
                self._source(f"missing-script-{host_id}", host_id, "scripts/absent_hook.py")
                run_dir = self.root / f"run-missing-script-{host_id}"
                self.assert_failed_before_launch(
                    self._live(host_id, run_dir), "preparation_failed", "not_run")

    def test_a_missing_registration_asset_fails_preparation_and_launches_nothing(self) -> None:
        source = self._source("missing-asset")
        (source / "compatibility" / "claude" / "hooks.json").unlink()
        result = self._live("claude", self.root / "run-missing-asset")
        self.assert_failed_before_launch(result, "preparation_failed", "not_run")

    def test_a_declared_script_resolving_outside_the_copied_tree_is_a_resource_escape(self) -> None:
        self._source("escaping-script", script="../outside_hook.py")
        run_dir = self.root / "run-escaping-script"
        run_dir.mkdir()
        (run_dir / "outside_hook.py").write_text("print('outside')\n", encoding="utf-8")
        result = self._live("claude", run_dir)
        self.assert_failed_before_launch(result, "resource_escape", "failed")

    def test_a_source_symlink_escape_keeps_reason_resource_escape(self) -> None:
        source = self._source("escaping-symlink")
        outside = self.root / "outside-dir"
        outside.mkdir()
        (source / "linked").symlink_to(outside, target_is_directory=True)
        result = self._live("claude", self.root / "run-escaping-symlink")
        self.assert_failed_before_launch(result, "resource_escape", "failed")

    def test_a_git_failure_is_a_preparation_failure_not_a_resource_escape(self) -> None:
        self._source("git-failure")
        run_dir = self.root / "run-git-failure"
        run_dir.mkdir()
        (run_dir / "remote.git").write_text("a file where the bare repo must go", encoding="utf-8")
        self.assert_failed_before_launch(self._live("claude", run_dir), "preparation_failed", "not_run")

    def test_a_declared_script_that_stays_inside_the_copied_tree_is_accepted(self) -> None:
        cases = (("claude", "plugin-dir", "scripts/../scripts/autopilot.py"),
                 ("codex", "project-layer", "scripts/autopilot.py"))
        for host_id, surface, script in cases:
            with self.subTest(host_id=host_id):
                source = self._source(f"valid-{host_id}", host_id, script)
                run_dir = self.root / f"run-valid-{host_id}"
                run_dir.mkdir()
                self.assertEqual(self.module.prepare(run_dir, host_id), surface)
                asset = (source / "compatibility" / host_id / "hooks.json").read_bytes()
                if host_id == "codex":
                    for repo in ("project", "control"):
                        registered = run_dir / repo / ".codex" / "hooks.json"
                        self.assertEqual(registered.read_bytes(), asset)


if __name__ == "__main__":
    unittest.main()
