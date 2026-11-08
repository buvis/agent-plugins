"""Tests for guards.py: GuardDuty, GuardOutcome, run_guard and the nine duties.

custody_push_denied proves a CUSTODY_PUSH call relays the seam's denial.
missing_controller_seam_refused proves every stateful duty refuses with
seam=None. Pure duties decide from their own context keys alone, fail closed
when a key is missing, and never see a seam (per-duty rules live in
test_guards_pure_duties.py).
"""

from __future__ import annotations

import copy
import dataclasses
import enum
import importlib
import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

guards = importlib.import_module("guards")
jobs = importlib.import_module("jobs")

GuardDuty = guards.GuardDuty
GuardOutcome = guards.GuardOutcome

EXPECTED_DUTIES = {
    "DOCUMENT_LOCATION": "document_location",
    "CUSTODY_PUSH": "custody_push",
    "DELEGATION": "delegation",
    "POST_HANDOFF": "post_handoff",
    "DEPARTURE": "departure",
    "CONTEXT_REINJECTION": "context_reinjection",
    "STATE_INTEGRITY": "state_integrity",
    "REVIEW_COMPLETENESS": "review_completeness",
    "LIVE_JOB": "live_job",
}

STATEFUL = (
    GuardDuty.CUSTODY_PUSH,
    GuardDuty.STATE_INTEGRITY,
    GuardDuty.LIVE_JOB,
    GuardDuty.REVIEW_COMPLETENESS,
)

PURE = (
    GuardDuty.DOCUMENT_LOCATION,
    GuardDuty.DELEGATION,
    GuardDuty.POST_HANDOFF,
    GuardDuty.DEPARTURE,
    GuardDuty.CONTEXT_REINJECTION,
)

# One context per pure duty that satisfies its own required keys and passes.
PASSING = {
    GuardDuty.DOCUMENT_LOCATION: {
        "document_path": "docs/dev/project-management/prds/wip/00014-x.md"
    },
    GuardDuty.DELEGATION: {"dispatch_skill": "autopilot:use-codex"},
    GuardDuty.POST_HANDOFF: {"requested_skill": "autopilot:work", "leave_recorded": False},
    GuardDuty.DEPARTURE: {
        "leave_row_written": True,
        "last_store_write_at": 1,
        "leave_row_at": 2,
    },
    GuardDuty.CONTEXT_REINJECTION: {
        "contract_card_present": True,
        "contract_card_body": "card body",
    },
}

# One context per pure duty that supplies every key and fails the rule.
FAILING = {
    GuardDuty.DOCUMENT_LOCATION: {
        "document_path": "docs/dev/project-management/prds/00014-x.md"
    },
    GuardDuty.DELEGATION: {"dispatch_skill": "autopilot:work"},
    GuardDuty.POST_HANDOFF: {"requested_skill": "autopilot:work", "leave_recorded": True},
    GuardDuty.DEPARTURE: {
        "leave_row_written": True,
        "last_store_write_at": 3,
        "leave_row_at": 2,
    },
    GuardDuty.CONTEXT_REINJECTION: {
        "contract_card_present": True,
        "contract_card_body": "   ",
    },
}


class _RecordingFakeSeam(jobs.FakeSeam):
    """The real FakeSeam, plus a log of every evaluate_guard call it answers."""

    def __init__(self, *, guard_rules: dict) -> None:
        super().__init__(guard_rules=guard_rules)
        self.guard_calls: list = []

    def evaluate_guard(self, duty, context):
        self.guard_calls.append((duty, context))
        return super().evaluate_guard(duty, context)


class _TripwireSeam:
    """Records every call instead of raising, so a swallowed error cannot hide one."""

    def __init__(self) -> None:
        self.calls: list = []

    def submit_job(self, intent):
        self.calls.append(("submit_job", intent))

    def evaluate_guard(self, duty, context):
        self.calls.append(("evaluate_guard", duty, context))
        return {"allowed": False, "reason": "tripwire"}


def _pure_fn(duty):
    return getattr(guards, f"_guard_{duty.value}")


def _assert_outcome(test, outcome, expected) -> None:
    test.assertEqual(outcome, expected)
    test.assertIs(outcome.duty, expected.duty)
    test.assertIsInstance(outcome.duty, GuardDuty)


class GuardDutyTest(unittest.TestCase):
    def test_has_exactly_the_nine_named_duties(self) -> None:
        self.assertEqual({m.name: m.value for m in GuardDuty}, EXPECTED_DUTIES)
        self.assertEqual(len(list(GuardDuty)), 9)

    def test_is_a_str_enum(self) -> None:
        self.assertTrue(issubclass(GuardDuty, enum.StrEnum))
        self.assertEqual(GuardDuty.CUSTODY_PUSH, "custody_push")

    def test_stateful_and_pure_partition_every_duty(self) -> None:
        self.assertEqual(set(STATEFUL) | set(PURE), set(GuardDuty))
        self.assertEqual(set(STATEFUL) & set(PURE), set())


class GuardOutcomeTest(unittest.TestCase):
    def test_carries_exactly_four_fields_in_contract_order(self) -> None:
        names = tuple(f.name for f in dataclasses.fields(GuardOutcome))
        self.assertEqual(names, ("duty", "allowed", "reason", "stateful"))

    def test_is_frozen(self) -> None:
        outcome = GuardOutcome(
            duty=GuardDuty.CUSTODY_PUSH, allowed=False, reason="x", stateful=True
        )
        for field, value in (("allowed", True), ("reason", None), ("stateful", False)):
            with self.subTest(field=field):
                with self.assertRaises(dataclasses.FrozenInstanceError):
                    setattr(outcome, field, value)


class CustodyPushDeniedTest(unittest.TestCase):
    def test_custody_push_denied_relays_pending_critical(self) -> None:
        for reason in ("pending_critical", "unsigned_commit"):
            with self.subTest(reason=reason):
                seam = jobs.FakeSeam(guard_rules={"custody_push": (False, reason)})
                outcome = guards.run_guard(GuardDuty.CUSTODY_PUSH, {}, seam=seam)
                _assert_outcome(
                    self,
                    outcome,
                    GuardOutcome(
                        duty=GuardDuty.CUSTODY_PUSH, allowed=False, reason=reason, stateful=True
                    ),
                )

    def test_custody_push_allowed_with_empty_rules(self) -> None:
        outcome = guards.run_guard(
            GuardDuty.CUSTODY_PUSH, {}, seam=jobs.FakeSeam(guard_rules={})
        )
        _assert_outcome(
            self,
            outcome,
            GuardOutcome(duty=GuardDuty.CUSTODY_PUSH, allowed=True, reason=None, stateful=True),
        )

    def test_near_miss_rule_names_do_not_deny_custody_push(self) -> None:
        seam = jobs.FakeSeam(
            guard_rules={
                "custody": (False, "a"),
                "custody_push_extra": (False, "b"),
                "push": (False, "c"),
                "Custody_Push": (False, "d"),
            }
        )
        outcome = guards.run_guard(GuardDuty.CUSTODY_PUSH, {}, seam=seam)
        self.assertIs(outcome.allowed, True)
        self.assertIsNone(outcome.reason)

    def test_ok_key_in_context_does_not_override_seam_denial(self) -> None:
        seam = jobs.FakeSeam(guard_rules={"custody_push": (False, "pending_critical")})
        outcome = guards.run_guard(GuardDuty.CUSTODY_PUSH, {"ok": True}, seam=seam)
        self.assertIs(outcome.allowed, False)
        self.assertEqual(outcome.reason, "pending_critical")

    def test_ok_false_in_context_does_not_override_seam_allowance(self) -> None:
        for duty in STATEFUL:
            with self.subTest(duty=duty.value):
                outcome = guards.run_guard(
                    duty, {"ok": False}, seam=jobs.FakeSeam(guard_rules={})
                )
                _assert_outcome(
                    self,
                    outcome,
                    GuardOutcome(duty=duty, allowed=True, reason=None, stateful=True),
                )


class MissingControllerSeamRefusedTest(unittest.TestCase):
    def test_every_stateful_duty_refuses_without_seam(self) -> None:
        for duty in STATEFUL:
            for context in ({}, {"ok": True}, {"ok": True, "prd": "00014"}):
                with self.subTest(duty=duty.value, context=context):
                    _assert_outcome(
                        self,
                        guards.run_guard(duty, context, seam=None),
                        GuardOutcome(
                            duty=duty,
                            allowed=False,
                            reason="missing_controller_seam",
                            stateful=True,
                        ),
                    )

    def test_pure_duties_do_not_refuse_without_seam(self) -> None:
        for duty in PURE:
            with self.subTest(duty=duty.value):
                outcome = guards.run_guard(duty, dict(PASSING[duty]), seam=None)
                self.assertIs(outcome.allowed, True)
                self.assertIsNone(outcome.reason)
                self.assertNotEqual(outcome.reason, "missing_controller_seam")


class StatefulRelayTest(unittest.TestCase):
    RULES = {
        "custody_push": (False, "pending_critical"),
        "state_integrity": (False, "torn_state_file"),
        "live_job": (True, "job_still_running"),
        "review_completeness": (False, "missing_blind_lens"),
    }
    OTHER_RULES = {
        "custody_push": (False, "unsigned_commit"),
        "state_integrity": (False, "lease_expired"),
        "live_job": (False, "orphan_job"),
        "review_completeness": (False, "missing_doubt_lens"),
    }

    def test_each_stateful_duty_relays_its_own_rule_verbatim(self) -> None:
        for rules in (self.RULES, self.OTHER_RULES):
            seam = jobs.FakeSeam(guard_rules=dict(rules))
            for duty in STATEFUL:
                allowed, reason = rules[duty.value]
                with self.subTest(duty=duty.value, reason=reason):
                    _assert_outcome(
                        self,
                        guards.run_guard(duty, {}, seam=seam),
                        GuardOutcome(duty=duty, allowed=allowed, reason=reason, stateful=True),
                    )

    def test_a_rule_for_one_duty_does_not_leak_into_another(self) -> None:
        seam = jobs.FakeSeam(guard_rules={"state_integrity": (False, "torn_state_file")})
        denied = guards.run_guard(GuardDuty.STATE_INTEGRITY, {}, seam=seam)
        self.assertEqual((denied.allowed, denied.reason), (False, "torn_state_file"))
        for duty in (GuardDuty.CUSTODY_PUSH, GuardDuty.LIVE_JOB, GuardDuty.REVIEW_COMPLETENESS):
            with self.subTest(duty=duty.value):
                _assert_outcome(
                    self,
                    guards.run_guard(duty, {}, seam=seam),
                    GuardOutcome(duty=duty, allowed=True, reason=None, stateful=True),
                )

    def test_passes_duty_and_context_to_the_seam_once(self) -> None:
        contexts = (
            {},
            {"prd": "00014", "branch": "feat/x"},
            {"ok": True, "zz": 1, "nested": {"a": [1]}},
        )
        for duty in STATEFUL:
            for context in contexts:
                with self.subTest(duty=duty.value, context=context):
                    seam = _RecordingFakeSeam(guard_rules={})
                    passed = copy.deepcopy(context)
                    guards.run_guard(duty, passed, seam=seam)
                    self.assertEqual(passed, context)
                    self.assertEqual(len(seam.guard_calls), 1)
                    got_duty, got_context = seam.guard_calls[0]
                    self.assertEqual(got_duty, duty.value)
                    self.assertEqual(got_context, context)

    def test_never_mutates_the_callers_context(self) -> None:
        context = {"ok": True, "prd": "00014", "nested": {"a": [1]}}
        for duty in GuardDuty:
            for seam in (None, jobs.FakeSeam(guard_rules={duty.value: (False, "x")})):
                with self.subTest(duty=duty.value, seam=type(seam).__name__):
                    passed = copy.deepcopy(context)
                    guards.run_guard(duty, passed, seam=seam)
                    self.assertEqual(passed, context)

    def test_stateful_duty_never_submits_jobs(self) -> None:
        seam = _RecordingFakeSeam(guard_rules={})
        for duty in STATEFUL:
            guards.run_guard(duty, {}, seam=seam)
        self.assertEqual(seam.submitted_intents, [])
        self.assertEqual(len(seam.guard_calls), 4)


class PureGuardTest(unittest.TestCase):
    def test_ok_true_alone_denies_every_pure_duty(self) -> None:
        for duty in PURE:
            for context in ({"ok": True}, {}, {"ok": True, "path": "docs/x.md"}):
                with self.subTest(duty=duty.value, context=context):
                    outcome = guards.run_guard(duty, context, seam=None)
                    self.assertIs(outcome.allowed, False)
                    self.assertIs(outcome.stateful, False)
                    self.assertIsInstance(outcome.reason, str)
                    self.assertIn(duty.value, outcome.reason)

    def test_ok_flag_has_no_effect_on_a_real_verdict(self) -> None:
        for duty in PURE:
            for ok in (True, False):
                with self.subTest(duty=duty.value, ok=ok, kind="passing"):
                    context = {**PASSING[duty], "ok": ok}
                    self.assertIs(guards.run_guard(duty, context, seam=None).allowed, True)
                with self.subTest(duty=duty.value, ok=ok, kind="failing"):
                    context = {**FAILING[duty], "ok": ok}
                    self.assertIs(guards.run_guard(duty, context, seam=None).allowed, False)

    def test_never_consult_a_provided_seam(self) -> None:
        for duty in PURE:
            for contexts, expected in ((PASSING, True), (FAILING, False)):
                with self.subTest(duty=duty.value, expected=expected):
                    seam = _TripwireSeam()
                    outcome = guards.run_guard(duty, dict(contexts[duty]), seam=seam)
                    self.assertIs(outcome.allowed, expected)
                    self.assertIs(outcome.stateful, False)
                    self.assertEqual(seam.calls, [])

    def test_seam_rules_for_the_pure_duty_are_ignored(self) -> None:
        for duty in PURE:
            seam = _RecordingFakeSeam(guard_rules={duty.value: (False, "seam_says_no")})
            with self.subTest(duty=duty.value):
                outcome = guards.run_guard(duty, dict(PASSING[duty]), seam=seam)
                self.assertIs(outcome.allowed, True)
                self.assertEqual(seam.guard_calls, [])
                self.assertEqual(seam.submitted_intents, [])

    def test_pure_functions_take_only_a_context_parameter(self) -> None:
        for duty in PURE:
            with self.subTest(duty=duty.value):
                params = inspect.signature(_pure_fn(duty)).parameters
                self.assertNotIn("seam", params)
                self.assertEqual(list(params), ["context"])

    def test_pure_functions_decide_from_context_alone(self) -> None:
        for duty in PURE:
            fn = _pure_fn(duty)
            with self.subTest(duty=duty.value):
                _assert_outcome(
                    self,
                    fn(dict(PASSING[duty])),
                    GuardOutcome(duty=duty, allowed=True, reason=None, stateful=False),
                )
                denied = fn(dict(FAILING[duty]))
                self.assertEqual(
                    (denied.duty, denied.allowed, denied.stateful),
                    (duty, False, False),
                )
                self.assertIsInstance(denied.reason, str)


class RunGuardSignatureTest(unittest.TestCase):
    def test_seam_is_keyword_only(self) -> None:
        param = inspect.signature(guards.run_guard).parameters["seam"]
        self.assertIs(param.kind, inspect.Parameter.KEYWORD_ONLY)

    def test_positional_seam_raises_type_error(self) -> None:
        for duty in (GuardDuty.CUSTODY_PUSH, GuardDuty.DOCUMENT_LOCATION):
            with self.subTest(duty=duty.value):
                with self.assertRaises(TypeError):
                    guards.run_guard(duty, {}, jobs.FakeSeam(guard_rules={}))


class UnknownDutyTest(unittest.TestCase):
    def test_non_member_duty_raises(self) -> None:
        rejects = (
            "not_a_duty",
            "custody_push_extra",
            "custody",
            "",
            "Custody_Push",
            "CUSTODY_PUSH",
            "LIVE_JOB",
            "Document_Location",
            "DOCUMENT_LOCATION",
        )
        for duty in rejects:
            for seam in (None, jobs.FakeSeam(guard_rules={})):
                with self.subTest(duty=duty, seam=type(seam).__name__):
                    with self.assertRaises((ValueError, KeyError)):
                        guards.run_guard(duty, {}, seam=seam)


if __name__ == "__main__":
    unittest.main()
