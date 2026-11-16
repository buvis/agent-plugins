"""Push-grammar, real-adapter and recorded-hook-equivalence tests (split from test_interception.py)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_interception import (
    CHARACTERIZATION,
    GuardDuty,
    INTERCEPTING,
    UNBOUND_CWD,
    _agent,
    _body,
    _cases,
    _child_env,
    _filler,
    _fresh,
    _push_commands,
    _random_skill,
    guards,
    host_fakes,
    interception,
)


class PushGrammarCharacterizationTest(unittest.TestCase):
    """Binds every push-* characterization fixture to the real
    guards.is_git_push grammar, not a test-local stand-in — closing the gap
    the module docstring above notes: these fixtures previously pinned only
    the duty-call shape, never the command-classification verdict itself."""

    def test_every_denied_push_fixture_is_a_grammar_match(self) -> None:
        """is_git_push is a conservative superset (§7): a false positive on
        an allowed command is tolerated, but every fixture the source denied
        for being a push must still be one, or custody_push is never
        consulted for it and the denial is unreachable."""
        document = json.loads(CHARACTERIZATION.read_text(encoding="utf-8"))
        cases = [case for case in document["cases"]
                 if case["case_id"].startswith("push-")
                 and (case["expected"] == "deny" or case["divergence"] is not None)
                 and case["payload"]["tool_name"] == "Bash"]
        self.assertTrue(cases, "expected at least one denied push-* fixture")
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                command = case["payload"]["tool_input"]["command"]
                self.assertTrue(guards.is_git_push(command), command)


# Every PreToolUse and Stop case runs through its own host's shipped adapter.
# effort_forwarding cases record model-effort translation, not a hook decision,
# so they never reach evaluate_hook; the count pins that no event drops silently.
HOOK_EVENTS = ("PreToolUse", "Stop")
NON_HOOK_EVENTS = frozenset({"effort_forwarding"})
NON_HOOK_CASE_COUNT = 5
# The recorded facts are SOURCE-shaped (`leave_marker`, `lanes`, `state`,
# `review_files`): the source hooks read the file system themselves. The target
# reads duty-keyed facts through the controller seam, so this harness has to
# translate them. Passing the recorded facts straight to FakeSeam makes every
# controller-keyed duty read `{}` and refuse with `malformed_controller_facts`,
# which both empties this test of meaning and reads as a contract divergence
# that does not exist.
LANE_AGE_CEILING_SECS = 3600  # stop-lane-past-the-age-ceiling-does-not-hold
LANE_BLOCK_CAP = 40  # stop-block-cap-gives-up vs stop-block-at-the-cap-still-denies


def _duty_facts(facts: dict) -> dict:
    """The recorded facts in the shape `interception._FACTS_SCHEMA` declares."""
    marker = facts.get("leave_marker")
    session = marker.get("session") if isinstance(marker, dict) else None
    recorded = isinstance(session, str)
    return {
        # A missing marker, and one the source could not parse, both mean
        # nothing shows a leave happened.
        "post_handoff": {
            "leave_recorded": recorded,
            "leave_session": session if recorded else "",
        },
        # These Stop fixtures characterize the live-lane and review-coverage
        # guards, not the departure guard: give departure a conforming,
        # non-blocking answer so it cannot mask what they do pin.
        "departure": {"leave_row_written": True, "last_store_write_at": 0, "leave_row_at": 0},
    }


def _guard_rules(facts: dict) -> dict:
    """Verdicts for the stateful duties the controller decides, derived from
    the same recorded facts the source hooks read off disk."""
    lanes = facts.get("lanes") or []
    holding = [
        lane for lane in lanes
        if lane.get("alive") and lane.get("age_secs", 0) <= LANE_AGE_CEILING_SECS
    ]
    gave_up = facts.get("lane_guard_blocks", 0) >= LANE_BLOCK_CAP
    state = facts.get("state") or {}
    converged = state.get("phase") == "done" and "review" in (state.get("phases_completed") or [])
    unreviewed = converged and not (facts.get("review_files") or [])
    return {
        GuardDuty.LIVE_JOB.value: (False, "live_lanes") if holding and not gave_up else (True, None),
        GuardDuty.REVIEW_COMPLETENESS.value: (
            (False, "review_file_missing") if unreviewed else (True, None)
        ),
    }


# Audit record: every recorded case whose expected decision differs from the
# source behaviour. A new divergence must be added here on purpose.
DIVERGENT_CASES = frozenset({
    "push-denies-direct-push-with-pending-custody",
    "push-denies-on-corrupt-custody-marker",
    "push-denies-hidden-push-when-cwd-has-custody",
    "push-grammar-denies-push-in-an-and-list",
    "push-grammar-denies-push-after-quoted-separators",
    "push-grammar-denies-wrapper-whose-option-hides-the-executable",
    "skill-allows-replaced-byte-session-id",
    "phase-denies-explicit-skill-name-fixture",
    "phase-lexicon-only-fixture-is-no-longer-denied",
    "stop-bound-session-without-controller-seam-is-denied",
    "effort-sonnet-wrapper-forwards-effort-with-a-prompt-file",
    "effort-sonnet-wrapper-forwards-effort-after-a-positional-prompt",
})


class HookBehaviorEquivalenceTest(unittest.TestCase):
    def _bound_root(self) -> str:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / ".autopilot" / "controller").mkdir(parents=True)
        return str(root)

    def _seam(self, case: dict):
        if not case["facts"].get("controller_seam"):
            return None
        return host_fakes.FakeSeam(
            guard_rules=_guard_rules(case["facts"]), facts=_duty_facts(case["facts"])
        )

    def _assert_stop_reply(self, case: dict, decision) -> None:
        module = dict(INTERCEPTING)[case["host"]]
        blocked = module.render_hook_reply("Stop", decision, stop_active=False)
        denies = case["expected"] == "deny"
        self.assertEqual(_body(blocked).get("decision") == "block", denies, msg=decision.outcomes)
        released = module.render_hook_reply("Stop", decision, stop_active=True)
        self.assertNotEqual(_body(released).get("decision"), "block")

    def test_hook_behavior_equivalence(self) -> None:
        document = json.loads(CHARACTERIZATION.read_text(encoding="utf-8"))
        cases = document["cases"]
        excluded = [case for case in cases if case["event"] not in HOOK_EVENTS]
        self.assertEqual({case["event"] for case in excluded}, NON_HOOK_EVENTS)
        self.assertEqual(len(excluded), NON_HOOK_CASE_COUNT)
        with _child_env(None):
            for case in cases:
                if case["event"] not in HOOK_EVENTS:
                    continue
                with self.subTest(case_id=case["case_id"]):
                    cwd = self._bound_root() if case["bound"] else UNBOUND_CWD
                    payload = {**case["payload"], "cwd": cwd}
                    decision = interception.evaluate_hook(
                        case["host"], case["event"], payload, env={}, seam=self._seam(case)
                    )
                    self.assertIs(decision.allowed, case["expected"] == "allow", msg=decision.outcomes)
                    if case["event"] == "Stop":
                        self._assert_stop_reply(case, decision)

    def test_divergences_are_written_down_and_pinned(self) -> None:
        document = json.loads(CHARACTERIZATION.read_text(encoding="utf-8"))
        divergent = {case["case_id"] for case in document["cases"] if case.get("divergence") is not None}
        for case in document["cases"]:
            if case.get("divergence") is not None:
                self.assertTrue(case["divergence"].strip(), case["case_id"])
        self.assertEqual(divergent, DIVERGENT_CASES)


class RealAdapterEvaluateHookTest(unittest.TestCase):
    def _bound_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / ".autopilot" / "controller").mkdir(parents=True)
        return root

    def test_unbound_push_skips_custody_push_only_for_git_pushes(self) -> None:
        for host_id, _ in INTERCEPTING:
            for command in _push_commands():
                with self.subTest(host=host_id, command=command):
                    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": UNBOUND_CWD}
                    decision = interception.evaluate_hook(host_id, "PreToolUse", payload, env={}, seam=None)
                    outcomes = {o.duty: o for o in decision.outcomes}
                    self.assertEqual(set(outcomes), {GuardDuty.DOCUMENT_LOCATION})
                    if guards.is_git_push(command):
                        self.assertEqual(decision.skipped, ((GuardDuty.CUSTODY_PUSH.value, "unbound"),))
                    else:
                        self.assertEqual(decision.skipped, ())
                    if outcomes[GuardDuty.DOCUMENT_LOCATION].allowed:
                        self.assertTrue(decision.allowed)

    def test_phase_fixtures_match_their_recorded_verdict(self) -> None:
        cases = _cases("phase-")
        with _child_env(None):
            for case in cases:
                with self.subTest(case_id=case["case_id"]):
                    payload = {**case["payload"], "cwd": UNBOUND_CWD}
                    decision = interception.evaluate_hook("claude", case["event"], payload, env={}, seam=None)
                    self.assertIs(decision.allowed, case["expected"] == "allow", msg=decision.outcomes)

    def test_dispatching_a_whole_phase_skill_in_the_prompt_is_denied(self) -> None:
        table = (("Call /autopilot:plan-tasks", False), ("Run autopilot:work", False),
                 ("Call /autopilot:plan-tasks-notes", True), ("Summarize the diff", True),
                 # per-run prompts, the phase skill at a random offset
                 (f"{_filler()} /autopilot:plan-tasks {_filler()}", False),
                 (f"{_filler()} autopilot:work {_filler()} {_random_skill()}", False),
                 (f"{_filler()} {_random_skill()} {_filler()} autopilot:work", True))
        with _child_env(None):
            for prompt, allowed in table:
                with self.subTest(prompt=prompt):
                    decision = interception.evaluate_hook("claude", "PreToolUse", _agent(prompt), env={}, seam=None)
                    self.assertIs(decision.allowed, allowed, msg=decision.outcomes)

    def test_a_child_session_dispatch_is_refused_for_depth(self) -> None:
        for extra, env_value, allowed in (({"agent_id": "agent-7"}, None, False), ({}, "child-3", False),
                                          ({}, None, True)):
            with self.subTest(extra=extra, env=env_value):
                with _child_env(env_value):
                    decision = interception.evaluate_hook(
                        "claude", "PreToolUse", _agent("Summarize", **extra), env={}, seam=None
                    )
                self.assertIs(decision.allowed, allowed)
                if not allowed:
                    self.assertIn("recursion_depth", decision.outcomes[0].reason)

    def test_a_skill_is_refused_only_after_this_sessions_own_leave(self) -> None:
        """skill-denies-autopilot-skill-after-own-leave and
        skill-allows-another-sessions-leave-marker: the decision needs the
        payload's session, so translate_hook must carry it."""
        root = self._bound_root()
        session_id = _fresh("s")
        for leave_session, allowed in ((session_id, False), (_fresh("s"), True)):
            with self.subTest(leave_session=leave_session):
                seam = host_fakes.FakeSeam(guard_rules={}, facts={"post_handoff": {
                    "leave_recorded": True, "leave_session": leave_session}})
                payload = {"tool_name": "Skill", "tool_input": {"skill": "autopilot:run-autopilot"},
                           "session_id": session_id, "cwd": str(root)}
                decision = interception.evaluate_hook("claude", "PreToolUse", payload, env={}, seam=seam)
                self.assertIs(decision.allowed, allowed, msg=decision.outcomes)

    def test_bound_stop_without_seam_blocks_then_releases(self) -> None:
        (case,) = [c for c in _cases("stop-bound-session-without-controller-seam-is-denied")]
        root = self._bound_root()
        for host_id, module in INTERCEPTING:
            with self.subTest(host=host_id):
                payload = {**case["payload"], "cwd": str(root)}
                decision = interception.evaluate_hook(host_id, "Stop", payload, env={}, seam=None)
                self.assertTrue(decision.bound)
                self.assertFalse(decision.allowed)
                self.assertEqual({o.reason for o in decision.outcomes}, {"missing_controller_seam"})
                blocked = module.render_hook_reply("Stop", decision, stop_active=False)
                self.assertEqual(_body(blocked)["decision"], "block")
                released = module.render_hook_reply("Stop", decision, stop_active=True)
                self.assertNotEqual(_body(released).get("decision"), "block")

    def test_session_start_reinjection_reaches_the_reply(self) -> None:
        root = self._bound_root()
        for host_id, module in INTERCEPTING:
            for body in ("card one", "card two"):
                with self.subTest(host=host_id, body=body):
                    seam = host_fakes.FakeSeam(guard_rules={}, facts={"context_reinjection": {
                        "contract_card_present": True, "contract_card_body": body}})
                    payload = {"session_id": "s1", "cwd": str(root), "source": "compact"}
                    decision = interception.evaluate_hook(host_id, "SessionStart", payload, env={}, seam=seam)
                    reply = module.render_hook_reply("SessionStart", decision, stop_active=False)
                    self.assertEqual(_body(reply)["hookSpecificOutput"]["additionalContext"], body)
                    self.assertEqual(seam.fact_reads[-1][2], str(root))


if __name__ == "__main__":
    unittest.main()
