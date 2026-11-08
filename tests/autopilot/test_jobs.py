"""Tests for jobs.py: JobIntent, FakeSeam and request_cross_session_job.

recursive_child_denied proves an ancestry match on (host_id, job_id) raises
RecursionError before any argv is built or any seam is touched.
no_nested_driver_cli proves request_cross_session_job and every adapter's
build_job_argv never shell out. effort_forwarding proves JobIntent.effort is
carried in the intent but never forwarded into argv.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

claude = importlib.import_module("claude")
codex = importlib.import_module("codex")
gemini = importlib.import_module("gemini")
jobs = importlib.import_module("jobs")

INTENT_A = {
    "job_id": "alice",
    "role": "consensus-reviewer",
    "inputs": {"diff": {"path": "docs/dev/tmp/a.diff", "sha256": "aaa111"}},
    "isolation": "fresh-context",
    "tier": "opus",
    "effort": "high",
    "policy_constraints": {"blind": False, "allowed_inputs": ["diff"]},
}

INTENT_B = {
    "job_id": "blake",
    "role": "blind-reviewer",
    "inputs": {
        "prd": {"path": "docs/dev/project-management/prds/wip/p.md", "sha256": "bbb222"},
        "diff": {"path": "docs/dev/tmp/b.diff", "sha256": "ccc333"},
    },
    "isolation": "fresh-session",
    "tier": "sonnet",
    "effort": "low",
    "policy_constraints": {"blind": True, "allowed_inputs": ["prd"]},
}


def _intent(fields: dict):
    return jobs.build_job_intent(**fields)


def _fake_host(host_id: str, argv_prefix: list[str] | None = None, calls: list | None = None):
    """A host-adapter module double: HOST_ID plus build_job_argv returning a
    concrete list built from the intent's job_id and role (never effort).
    The module name never contains host_id, so only HOST_ID identifies it."""
    host = types.ModuleType("host_double")
    host.HOST_ID = host_id

    def build_job_argv(intent):
        if calls is not None:
            calls.append(intent)
        if argv_prefix is None:
            return None
        return [*argv_prefix, intent.job_id, intent.role]

    host.build_job_argv = build_job_argv
    return host


def _tripwire_host(host_id: str):
    host = types.ModuleType(f"tripwire_host_{host_id}")
    host.HOST_ID = host_id

    def build_job_argv(intent):
        raise AssertionError("build_job_argv reached despite recursive ancestry")

    host.build_job_argv = build_job_argv
    return host


class _TripwireSeam:
    def submit_job(self, intent):
        raise AssertionError("submit_job reached despite recursive ancestry")

    def evaluate_guard(self, duty, context):
        raise AssertionError("evaluate_guard reached despite recursive ancestry")


class _RecordingSeam:
    """ControllerSeam double returning a caller-chosen response, used to pin
    the exact {"mode": "controller", **submit_job(intent)} merge."""

    def __init__(self, response: dict) -> None:
        self.response = response
        self.received: list = []

    def submit_job(self, intent):
        self.received.append(intent)
        return dict(self.response)

    def evaluate_guard(self, duty, context):
        raise AssertionError("request_cross_session_job must not evaluate guards")


class HostIdConstantTest(unittest.TestCase):
    def test_every_adapter_exposes_its_own_host_id(self) -> None:
        self.assertEqual(claude.HOST_ID, "claude")
        self.assertEqual(codex.HOST_ID, "codex")
        self.assertEqual(gemini.HOST_ID, "gemini")


class BuildJobIntentTest(unittest.TestCase):
    def test_carries_every_field_verbatim_for_distinct_fixtures(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            with self.subTest(job_id=fields["job_id"]):
                intent = _intent(fields)
                self.assertIsInstance(intent, jobs.JobIntent)
                self.assertEqual(dataclasses.asdict(intent), fields)

    def test_intent_is_frozen(self) -> None:
        intent = _intent(INTENT_A)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            intent.effort = "low"

    def test_rejects_positional_arguments(self) -> None:
        with self.assertRaises(TypeError):
            jobs.build_job_intent(*INTENT_A.values())


class RecursiveChildDeniedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.alice = _intent(INTENT_A)

    def test_denies_when_ancestry_holds_same_host_and_job(self) -> None:
        for ancestry in (
            [{"host_id": "claude", "job_id": "alice"}],
            [{"host_id": "claude", "job_id": "alice"}, {"host_id": "codex", "job_id": "bob"}],
            [{"host_id": "codex", "job_id": "bob"}, {"host_id": "claude", "job_id": "alice"}],
            [
                {"host_id": "codex", "job_id": "bob"},
                {"host_id": "claude", "job_id": "alice"},
                {"host_id": "gemini", "job_id": "x"},
            ],
            [
                {"host_id": "codex", "job_id": "bob"},
                {"host_id": "gemini", "job_id": "x"},
                {"host_id": "claude", "job_id": "alice"},
                {"host_id": "codex", "job_id": "y"},
            ],
        ):
            with self.subTest(ancestry=ancestry):
                self.assertIs(
                    jobs.recursive_child_denied(self.alice, host=claude, ancestry=ancestry), True
                )

    def test_allows_when_job_or_host_differs(self) -> None:
        for ancestry in (
            [],
            [{"host_id": "claude", "job_id": "blake"}],
            [{"host_id": "codex", "job_id": "alice"}],
            [{"host_id": "claude", "job_id": "malice"}],
            [{"host_id": "claude", "job_id": "alice2"}],
            [{"host_id": "claude-code", "job_id": "alice"}],
            [{"host_id": "claud", "job_id": "alice"}],
            [{"host_id": "codex", "job_id": "alice"}, {"host_id": "claude", "job_id": "blake"}],
        ):
            with self.subTest(ancestry=ancestry):
                self.assertIs(
                    jobs.recursive_child_denied(self.alice, host=claude, ancestry=ancestry), False
                )

    def test_compares_against_the_passed_host_module_host_id(self) -> None:
        ancestry = [{"host_id": "zeta", "job_id": "alice"}]
        zeta = types.ModuleType("x")
        zeta.HOST_ID = "zeta"
        self.assertIs(jobs.recursive_child_denied(self.alice, host=zeta, ancestry=ancestry), True)
        name_only = [{"host_id": "x", "job_id": "alice"}]
        self.assertIs(jobs.recursive_child_denied(self.alice, host=zeta, ancestry=name_only), False)
        self.assertIs(jobs.recursive_child_denied(self.alice, host=claude, ancestry=ancestry), False)
        gemini_ancestry = [{"host_id": "gemini", "job_id": "alice"}]
        self.assertIs(
            jobs.recursive_child_denied(self.alice, host=gemini, ancestry=gemini_ancestry), True
        )
        self.assertIs(
            jobs.recursive_child_denied(self.alice, host=codex, ancestry=gemini_ancestry), False
        )

    def test_compares_against_the_intent_job_id(self) -> None:
        blake = _intent(INTENT_B)
        ancestry = [{"host_id": "claude", "job_id": "blake"}]
        self.assertIs(jobs.recursive_child_denied(blake, host=claude, ancestry=ancestry), True)
        self.assertIs(jobs.recursive_child_denied(self.alice, host=claude, ancestry=ancestry), False)


class RequestRecursionGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.alice = _intent(INTENT_A)
        self.recursive = [{"host_id": "claude", "job_id": "alice"}]

    def test_raises_recursion_error_in_standalone_mode(self) -> None:
        with self.assertRaises(RecursionError):
            jobs.request_cross_session_job(
                self.alice, seam=None, host=claude, ancestry=self.recursive
            )

    def test_raises_before_touching_the_seam(self) -> None:
        with self.assertRaises(RecursionError):
            jobs.request_cross_session_job(
                self.alice, seam=_TripwireSeam(), host=claude, ancestry=self.recursive
            )

    def test_raises_before_building_argv(self) -> None:
        for seam in (None, _TripwireSeam()):
            with self.subTest(seam=type(seam).__name__):
                with self.assertRaises(RecursionError):
                    jobs.request_cross_session_job(
                        self.alice,
                        seam=seam,
                        host=_tripwire_host("claude"),
                        ancestry=self.recursive,
                    )

    def test_distinct_job_or_host_in_ancestry_does_not_raise(self) -> None:
        for ancestry in (
            [{"host_id": "claude", "job_id": "blake"}],
            [{"host_id": "codex", "job_id": "alice"}],
        ):
            with self.subTest(ancestry=ancestry):
                result = jobs.request_cross_session_job(
                    self.alice, seam=None, host=claude, ancestry=ancestry
                )
                self.assertEqual(result["mode"], "standalone")
                seam = jobs.FakeSeam(guard_rules={})
                result = jobs.request_cross_session_job(
                    self.alice, seam=seam, host=claude, ancestry=ancestry
                )
                self.assertEqual(result["mode"], "controller")
                self.assertEqual(seam.submitted_intents, [self.alice])


class _ShellOutAttempt(Exception):
    pass


_SUBPROCESS_NAMES = ("run", "Popen", "call", "check_call", "check_output")
_OS_NAMES = (
    "execv", "execve", "execl", "execle", "execlp", "execlpe", "execvp", "execvpe",
    "system", "spawnv", "spawnve", "posix_spawn", "posix_spawnp", "fork",
)


class NoNestedDriverCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tripwires = {}
        for module, names in ((subprocess, _SUBPROCESS_NAMES), (os, _OS_NAMES)):
            for name in names:
                if not hasattr(module, name):
                    continue
                patcher = mock.patch.object(module, name, side_effect=_ShellOutAttempt(name))
                self.tripwires[f"{module.__name__}.{name}"] = patcher.start()
                self.addCleanup(patcher.stop)
        self.assertIn("subprocess.run", self.tripwires)
        self.assertIn("os.execv", self.tripwires)
        self.assertIn("os.execve", self.tripwires)

    def _assert_no_shell_out(self) -> None:
        called = [name for name, wire in self.tripwires.items() if wire.called]
        self.assertEqual(called, [])

    def test_request_never_shells_out_in_either_mode(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            for host in (claude, codex, gemini):
                with self.subTest(job_id=intent.job_id, host=host.HOST_ID):
                    standalone = jobs.request_cross_session_job(
                        intent, seam=None, host=host, ancestry=[]
                    )
                    self.assertEqual(
                        standalone,
                        {
                            "mode": "standalone",
                            "instruction": {"argv": host.build_job_argv(intent), "intent": fields},
                        },
                    )
                    controller = jobs.request_cross_session_job(
                        intent, seam=jobs.FakeSeam(guard_rules={}), host=host, ancestry=[]
                    )
                    self.assertEqual(controller["mode"], "controller")
        self._assert_no_shell_out()

    def test_adapter_build_job_argv_never_shells_out(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            for host in (claude, codex, gemini):
                with self.subTest(job_id=intent.job_id, host=host.HOST_ID):
                    argv = host.build_job_argv(intent)
                    self.assertTrue(argv is None or isinstance(argv, list))
        self._assert_no_shell_out()


class EffortForwardingTest(unittest.TestCase):
    def _assert_effort_absent(self, argv, effort: str) -> None:
        if argv is None:
            return
        for token in argv:
            self.assertNotIn(effort.lower(), token.lower())
            self.assertNotIn("--effort", token.lower())

    def test_effort_never_reaches_argv_from_real_adapters(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            for host in (claude, codex, gemini):
                with self.subTest(effort=intent.effort, host=host.HOST_ID):
                    result = jobs.request_cross_session_job(
                        intent, seam=None, host=host, ancestry=[]
                    )
                    argv = result["instruction"]["argv"]
                    self.assertEqual(argv, host.build_job_argv(intent))
                    self.assertEqual(result["instruction"]["intent"], fields)
                    self._assert_effort_absent(argv, intent.effort)

    def test_argv_is_exactly_what_the_host_built_with_no_effort_appended(self) -> None:
        host = _fake_host("zeta", argv_prefix=["zeta", "run"])
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            with self.subTest(effort=intent.effort):
                result = jobs.request_cross_session_job(intent, seam=None, host=host, ancestry=[])
                argv = result["instruction"]["argv"]
                self.assertEqual(argv, ["zeta", "run", intent.job_id, intent.role])
                self._assert_effort_absent(argv, intent.effort)

    def test_standalone_intent_still_carries_effort(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            with self.subTest(effort=intent.effort):
                result = jobs.request_cross_session_job(
                    intent, seam=None, host=claude, ancestry=[]
                )
                self.assertEqual(result["instruction"]["intent"]["effort"], fields["effort"])


class StandaloneModeTest(unittest.TestCase):
    def test_returns_host_argv_and_complete_intent(self) -> None:
        calls: list = []
        host = _fake_host("zeta", argv_prefix=["zeta", "run"], calls=calls)
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            with self.subTest(job_id=intent.job_id):
                result = jobs.request_cross_session_job(intent, seam=None, host=host, ancestry=[])
                self.assertEqual(
                    result,
                    {
                        "mode": "standalone",
                        "instruction": {
                            "argv": ["zeta", "run", intent.job_id, intent.role],
                            "intent": dataclasses.asdict(intent),
                        },
                    },
                )
                self.assertEqual(result["instruction"]["intent"], fields)
                self.assertIs(calls[-1], intent)
        self.assertEqual(len(calls), 2)

    def test_returned_intent_is_a_deep_copy_not_shared_with_the_intent(self) -> None:
        intent = _intent(copy.deepcopy(INTENT_A))
        result = jobs.request_cross_session_job(intent, seam=None, host=claude, ancestry=[])
        returned = result["instruction"]["intent"]
        self.assertIsNot(returned["inputs"], intent.inputs)
        self.assertIsNot(returned["policy_constraints"], intent.policy_constraints)
        returned["inputs"]["diff"]["sha256"] = "tampered"
        returned["inputs"]["extra"] = {}
        returned["policy_constraints"]["allowed_inputs"].append("prd")
        self.assertEqual(dataclasses.asdict(intent), INTENT_A)

    def test_none_argv_still_returns_complete_intent(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            for host in (claude, _fake_host("zeta", argv_prefix=None)):
                with self.subTest(job_id=intent.job_id, host=host.HOST_ID):
                    result = jobs.request_cross_session_job(
                        intent, seam=None, host=host, ancestry=[]
                    )
                    self.assertEqual(
                        result,
                        {
                            "mode": "standalone",
                            "instruction": {"argv": None, "intent": fields},
                        },
                    )

    def test_empty_inputs_and_constraints_are_kept_not_dropped(self) -> None:
        fields = {**INTENT_A, "inputs": {}, "policy_constraints": {}}
        intent = _intent(fields)
        result = jobs.request_cross_session_job(intent, seam=None, host=claude, ancestry=[])
        self.assertEqual(result["instruction"]["intent"], fields)


class ControllerModeTest(unittest.TestCase):
    def test_merges_seam_response_under_controller_mode(self) -> None:
        responses = (
            {"accepted": True, "job_ref": "job-001", "queue": "q1"},
            {"accepted": False, "job_ref": None, "reason": "duty_denied"},
        )
        for fields, response in zip((INTENT_A, INTENT_B), responses):
            intent = _intent(fields)
            seam = _RecordingSeam(response)
            with self.subTest(job_id=intent.job_id):
                result = jobs.request_cross_session_job(
                    intent, seam=seam, host=codex, ancestry=[]
                )
                self.assertEqual(result, {"mode": "controller", **response})
                self.assertEqual(seam.received, [intent])

    def test_fake_seam_response_matches_direct_submit(self) -> None:
        for fields in (INTENT_A, INTENT_B):
            intent = _intent(fields)
            with self.subTest(job_id=intent.job_id):
                direct = jobs.FakeSeam(guard_rules={}).submit_job(intent)
                self.assertIs(direct["accepted"], True)
                self.assertIsInstance(direct["job_ref"], str)
                self.assertNotEqual(direct["job_ref"], "")
                result = jobs.request_cross_session_job(
                    intent, seam=jobs.FakeSeam(guard_rules={}), host=gemini, ancestry=[]
                )
                self.assertEqual(result, {"mode": "controller", **direct})

    def test_fake_seam_issues_a_distinct_job_ref_per_submission(self) -> None:
        seam = jobs.FakeSeam(guard_rules={})
        first = seam.submit_job(_intent(INTENT_A))
        second = seam.submit_job(_intent(INTENT_B))
        self.assertIs(first["accepted"], True)
        self.assertIs(second["accepted"], True)
        self.assertNotEqual(first["job_ref"], second["job_ref"])

    def test_fake_seam_records_every_submitted_intent_in_order(self) -> None:
        seam = jobs.FakeSeam(guard_rules={})
        self.assertEqual(seam.submitted_intents, [])
        alice = _intent(INTENT_A)
        blake = _intent(INTENT_B)
        seam.submit_job(alice)
        jobs.request_cross_session_job(blake, seam=seam, host=claude, ancestry=[])
        self.assertEqual(len(seam.submitted_intents), 2)
        self.assertIs(seam.submitted_intents[0], alice)
        self.assertIs(seam.submitted_intents[1], blake)

    def test_fake_seam_instances_keep_separate_intent_logs(self) -> None:
        first = jobs.FakeSeam(guard_rules={})
        alice = _intent(INTENT_A)
        first.submit_job(alice)
        second = jobs.FakeSeam(guard_rules={})
        self.assertEqual(second.submitted_intents, [])
        self.assertEqual(first.submitted_intents, [alice])
        second.submit_job(_intent(INTENT_B))
        self.assertEqual(first.submitted_intents, [alice])


class FakeSeamGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.seam = jobs.FakeSeam(
            guard_rules={
                "custody_push": (False, "pending_critical"),
                "review_close": (True, "all_lenses_converged"),
            }
        )

    def test_answers_from_fixture_rules_verbatim(self) -> None:
        self.assertEqual(
            self.seam.evaluate_guard("custody_push", {}),
            {"allowed": False, "reason": "pending_critical"},
        )
        self.assertEqual(
            self.seam.evaluate_guard("review_close", {"prd": "00014"}),
            {"allowed": True, "reason": "all_lenses_converged"},
        )

    def test_duty_without_rule_is_allowed_with_no_reason(self) -> None:
        for duty in ("custody", "custody_push_extra", "Custody_Push", "unknown_duty"):
            with self.subTest(duty=duty):
                self.assertEqual(
                    self.seam.evaluate_guard(duty, {}), {"allowed": True, "reason": None}
                )

    def test_empty_rules_allow_every_duty(self) -> None:
        seam = jobs.FakeSeam(guard_rules={})
        self.assertEqual(seam.evaluate_guard("custody_push", {}), {"allowed": True, "reason": None})

    def test_evaluate_guard_does_not_record_intents(self) -> None:
        self.seam.evaluate_guard("custody_push", {})
        self.assertEqual(self.seam.submitted_intents, [])


if __name__ == "__main__":
    unittest.main()
