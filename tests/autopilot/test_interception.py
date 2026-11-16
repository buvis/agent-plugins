"""Tests for interception.py: find_binding, evaluate_hook and run_hook.

The real claude/codex translate_hook is driven below (ClaudeTranslateHookTest
onward): push-* fixtures pin the duty-call shape, skill-* and phase-* fixtures
pin post_handoff and delegation extraction. The render_hook_reply tests live in
test_interception_render_reply.py; the push-grammar, real-adapter and recorded
hook-equivalence tests live in test_interception_push_grammar.py.
"""

from __future__ import annotations

import importlib
import json
import os
import random
import string
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
TESTS_DIR = ROOT / "tests" / "autopilot"
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

interception = importlib.import_module("interception")
guards = importlib.import_module("guards")
hosts = importlib.import_module("hosts")
host_fakes = importlib.import_module("host_fakes")
claude_adapter = importlib.import_module("claude")
codex_adapter = importlib.import_module("codex")

GuardDuty = guards.GuardDuty
GuardOutcome = guards.GuardOutcome
DutyCall = interception.DutyCall
HookDecision = interception.HookDecision

CHARACTERIZATION = TESTS_DIR / "hook_characterization.json"
CHILD_ENV = "CLAUDE_CODE_CHILD_SESSION"
UNBOUND_CWD = "/does/not/exist"
INTERCEPTING = (("claude", claude_adapter), ("codex", codex_adapter))


class FindBindingTest(unittest.TestCase):
    def test_finds_a_binding_directory_at_cwd(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".autopilot" / "controller").mkdir(parents=True)
            self.assertEqual(interception.find_binding(root), root)

    def test_finds_a_binding_directory_in_an_ancestor(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".autopilot" / "controller").mkdir(parents=True)
            child = root / "a" / "b"
            child.mkdir(parents=True)
            self.assertEqual(interception.find_binding(child), root)

    def test_returns_none_when_no_binding_exists(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            self.assertIsNone(interception.find_binding(Path(raw)))

    def test_stops_at_the_first_git_toplevel(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as enclosing:
            enclosing_root = Path(enclosing)
            root = enclosing_root / "repo"
            root.mkdir()
            (root / ".git").mkdir()
            outer_binding = enclosing_root / ".autopilot" / "controller"
            outer_binding.mkdir(parents=True)
            self.assertIsNone(interception.find_binding(root))

    def test_a_binding_marker_that_is_a_file_not_a_directory_does_not_count(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".autopilot").mkdir()
            (root / ".autopilot" / "controller").write_text("not a dir")
            self.assertIsNone(interception.find_binding(root))


class EvaluateHookUnboundTest(unittest.TestCase):
    def test_unbound_controller_keyed_duties_are_skipped_not_refused(self) -> None:
        """custody_push and post_handoff are controller-keyed: with no
        `.autopilot/controller` found they are skipped, not refused, and do
        not appear in decision.outcomes. document_location needs no
        controller, so it still runs, is allowed, and the skip does not flip
        decision.allowed to False. custody_push is called twice here and
        must be skipped twice, in call order (no dedup, no reordering), and
        delegation (not controller-keyed) must be evaluated normally, never
        routed into the skip path alongside it."""
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.CUSTODY_PUSH, {}),
                DutyCall(GuardDuty.POST_HANDOFF, {"requested_skill": "autopilot:work", "session": "s1"}),
                DutyCall(GuardDuty.CUSTODY_PUSH, {}),
                DutyCall(GuardDuty.DOCUMENT_LOCATION, {"document_path": "src/app.py"}),
                DutyCall(
                    GuardDuty.DELEGATION,
                    {"dispatch_skill": "autopilot:plan-tasks-notes", "child_depth": 0},
                ),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(
            decision.skipped,
            (
                (GuardDuty.CUSTODY_PUSH.value, "unbound"),
                (GuardDuty.POST_HANDOFF.value, "unbound"),
                (GuardDuty.CUSTODY_PUSH.value, "unbound"),
            ),
        )
        for duty_value, reason in decision.skipped:
            self.assertIs(type(duty_value), str)
            self.assertNotIsInstance(duty_value, GuardDuty)
            self.assertIs(type(reason), str)
        outcomes = {outcome.duty: outcome for outcome in decision.outcomes}
        self.assertEqual(set(outcomes), {GuardDuty.DOCUMENT_LOCATION, GuardDuty.DELEGATION})
        self.assertTrue(outcomes[GuardDuty.DOCUMENT_LOCATION].allowed)
        self.assertTrue(outcomes[GuardDuty.DELEGATION].allowed)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.host_id, "claude")
        self.assertEqual(decision.event, "PreToolUse")
        self.assertEqual(decision.project_root, "/does/not/exist")

    def test_unbound_with_a_real_but_unbound_cwd_still_skips(self) -> None:
        """`bound` means "a `.autopilot/controller` marker was found
        searching upward", not "cwd exists as a directory": every other
        unbound test here uses the nonexistent path /does/not/exist, which a
        naive `cwd.is_dir()` check would also happen to classify as unbound.
        A real directory (with a `.git` marker, so find_binding stops there)
        that merely lacks `.autopilot/controller` must still be unbound."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            host_fakes.install_adapter(
                self,
                "claude",
                translate_hook=lambda event, payload: (DutyCall(GuardDuty.CUSTODY_PUSH, {}),),
                session_from_environment=lambda env: None,
            )
            decision = interception.evaluate_hook(
                "claude", "PreToolUse", {"cwd": str(root)}, env={}, seam=None
            )
            self.assertFalse(decision.bound)
            self.assertEqual(decision.skipped, ((GuardDuty.CUSTODY_PUSH.value, "unbound"),))
            self.assertTrue(decision.allowed)

    def test_unbound_document_location_refusal_survives_the_skip(self) -> None:
        """A pure duty's own refusal is never faked as allowed to make an
        unbound decision trivially pass, and skipping a controller-keyed
        duty never flips an otherwise-correct refusal from another duty back
        to decision.allowed = True."""
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.CUSTODY_PUSH, {"command": "git push"}),
                DutyCall(GuardDuty.DOCUMENT_LOCATION, {"document_path": "backlog/x.md"}),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(decision.skipped, ((GuardDuty.CUSTODY_PUSH.value, "unbound"),))
        outcomes = {outcome.duty: outcome for outcome in decision.outcomes}
        self.assertEqual(set(outcomes), {GuardDuty.DOCUMENT_LOCATION})
        self.assertFalse(outcomes[GuardDuty.DOCUMENT_LOCATION].allowed)
        self.assertFalse(decision.allowed)

    def test_unbound_other_controller_keyed_duties_are_also_skipped(self) -> None:
        """The remaining controller-keyed duties named by the finding:
        state_integrity, review_completeness, live_job, departure and
        context_reinjection are skipped, not refused, when unbound, and an
        all-skipped decision is allowed."""
        duties = (
            DutyCall(GuardDuty.STATE_INTEGRITY, {"path": "src/app.py"}),
            DutyCall(GuardDuty.REVIEW_COMPLETENESS, {}),
            DutyCall(GuardDuty.LIVE_JOB, {}),
            DutyCall(GuardDuty.DEPARTURE, {}),
            DutyCall(GuardDuty.CONTEXT_REINJECTION, {}),
        )
        host_fakes.install_adapter(
            self, "claude", translate_hook=lambda event, payload: duties,
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(
            decision.skipped,
            tuple((call.duty.value, "unbound") for call in duties),
        )
        self.assertEqual(decision.outcomes, ())
        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.additional_context)

    def test_unbound_with_no_duty_calls_allows_trivially(self) -> None:
        """Zero duty calls is not a crash and not a false refusal: skipped
        and outcomes are both empty, and decision.allowed is True."""
        host_fakes.install_adapter(
            self, "claude", translate_hook=lambda event, payload: (),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(decision.skipped, ())
        self.assertEqual(decision.outcomes, ())
        self.assertTrue(decision.allowed)

    def test_unbound_git_push_skips_custody_push_and_allows_overall(self) -> None:
        """The exact scenario from the finding: an unbound project running
        `git push` skips custody_push instead of refusing it, and overall
        decision.allowed is True because the only other duty
        (document_location) is allowed."""
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.CUSTODY_PUSH, {"command": "git push"}),
                DutyCall(GuardDuty.DOCUMENT_LOCATION, {"document_path": "src/app.py"}),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(decision.skipped, ((GuardDuty.CUSTODY_PUSH.value, "unbound"),))
        outcomes = {outcome.duty: outcome for outcome in decision.outcomes}
        self.assertEqual(set(outcomes), {GuardDuty.DOCUMENT_LOCATION})
        self.assertTrue(outcomes[GuardDuty.DOCUMENT_LOCATION].allowed)
        self.assertTrue(decision.allowed)


class EvaluateHookBoundTest(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / ".autopilot" / "controller").mkdir(parents=True)

    def test_bound_stateful_duties_refuse_without_seam(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (DutyCall(GuardDuty.CUSTODY_PUSH, {}),),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": str(self.root)}, env={}, seam=None
        )
        self.assertTrue(decision.bound)
        self.assertEqual(len(decision.outcomes), 1)
        self.assertFalse(decision.outcomes[0].allowed)
        self.assertEqual(decision.outcomes[0].reason, "missing_controller_seam")
        self.assertFalse(decision.allowed)

    def test_document_location_normalizes_against_the_binding_root_not_a_sub_cwd(self) -> None:
        """A bound session whose cwd is a subdirectory of the binding root
        must still normalize an absolute document_path against the binding
        root, even when the adapter's own DutyCall context copies cwd into
        project_root (the bug this finding fixes)."""
        sub = self.root / "sub"
        sub.mkdir()
        absolute_path = str(self.root / "backlog" / "x.md")
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.DOCUMENT_LOCATION,
                        {"document_path": absolute_path, "project_root": payload["cwd"]}),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": str(sub)}, env={}, seam=None
        )
        self.assertTrue(decision.bound)
        self.assertEqual(len(decision.outcomes), 1)
        # Normalized against self.root ("backlog/x.md" is a lifecycle dir at
        # the repo root, so it is denied); against the wrong sub root the
        # path falls outside the whole-path check and would be allowed.
        self.assertFalse(decision.outcomes[0].allowed)

    def test_env_argument_not_os_environ_resolves_session_identity(self) -> None:
        received: list = []
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (),
            session_from_environment=lambda env: received.append(dict(env)) or None,
        )
        with mock.patch.dict(os.environ, {"MARKER_NOT_PASSED_IN": "from-os-environ"}):
            interception.evaluate_hook(
                "claude", "PreToolUse", {"cwd": str(self.root)}, env={}, seam=None
            )
        self.assertEqual(received, [{}])

    def test_bound_controller_keyed_pure_duty_refuses_without_seam(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.POST_HANDOFF, {"requested_skill": "autopilot:work", "session": "s1"}),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": str(self.root)}, env={}, seam=None
        )
        self.assertFalse(decision.outcomes[0].allowed)
        self.assertEqual(decision.outcomes[0].reason, "missing_controller_seam")

    def test_session_start_reinjects_the_contract_card(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (DutyCall(GuardDuty.CONTEXT_REINJECTION, {}),),
            session_from_environment=lambda env: None,
        )
        seam = host_fakes.FakeSeam(
            guard_rules={},
            facts={
                "context_reinjection": {
                    "contract_card_present": True,
                    "contract_card_body": "step: build | next: review",
                }
            },
        )
        decision = interception.evaluate_hook(
            "claude", "SessionStart", {"cwd": str(self.root)}, env={}, seam=seam
        )
        self.assertTrue(decision.outcomes[0].allowed)
        self.assertEqual(decision.additional_context, "step: build | next: review")

    def test_malformed_controller_facts_refuse(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (DutyCall(GuardDuty.CONTEXT_REINJECTION, {}),),
            session_from_environment=lambda env: None,
        )
        for facts in ({"context_reinjection": {"contract_card_present": True}}, {}):
            with self.subTest(facts=facts):
                seam = host_fakes.FakeSeam(guard_rules={}, facts=facts)
                decision = interception.evaluate_hook(
                    "claude", "SessionStart", {"cwd": str(self.root)}, env={}, seam=seam
                )
                self.assertFalse(decision.outcomes[0].allowed)
                self.assertEqual(decision.outcomes[0].reason, "malformed_controller_facts")
                self.assertIsNone(decision.additional_context)


class RunHookTest(unittest.TestCase):
    def test_gemini_hook_is_a_usage_error(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            interception.run_hook("gemini", "PreToolUse", b'{"cwd": "/tmp"}', env={})
        self.assertEqual(caught.exception.code, 2)

    def test_oversized_input_is_invalid_for_a_registered_event(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            HOOK_REGISTRATIONS={"PreToolUse": object()},
            translate_hook=lambda event, payload: (),
            session_from_environment=lambda env: None,
            render_hook_reply=lambda event, decision, stop_active: interception.HookReply(
                stdout="{}", exit_code=0
            ),
        )
        oversized = b"x" * (interception.MAX_HOOK_INPUT_BYTES + 1)
        reply = interception.run_hook("claude", "PreToolUse", oversized, env={})
        self.assertEqual(reply.exit_code, 0)
        self.assertIn("hook_input_invalid", reply.stdout)

    def test_missing_cwd_is_invalid_input(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            HOOK_REGISTRATIONS={"PreToolUse": object()},
            translate_hook=lambda event, payload: (),
            session_from_environment=lambda env: None,
            render_hook_reply=lambda event, decision, stop_active: interception.HookReply(
                stdout="{}", exit_code=0
            ),
        )
        reply = interception.run_hook("claude", "PreToolUse", b'{"no_cwd": true}', env={})
        self.assertEqual(reply.exit_code, 0)
        self.assertIn("hook_input_invalid", reply.stdout)

    def test_non_pretooluse_invalid_input_is_a_system_message(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            HOOK_REGISTRATIONS={"Stop": object()},
            translate_hook=lambda event, payload: (),
            session_from_environment=lambda env: None,
            render_hook_reply=lambda event, decision, stop_active: interception.HookReply(
                stdout="{}", exit_code=0
            ),
        )
        reply = interception.run_hook("claude", "Stop", b"not json", env={})
        self.assertIn("systemMessage", reply.stdout)
        self.assertEqual(reply.exit_code, 0)

    def test_codex_malformed_apply_patch_tool_input_never_crashes(self) -> None:
        """tool_input: null, a non-dict tool_input, and a non-str patch field
        must each produce a structured reply, never an uncaught exception."""
        for tool_input in (None, "not-a-dict", {"patch": 123}):
            with self.subTest(tool_input=tool_input):
                payload = json.dumps(
                    {"tool_name": "apply_patch", "tool_input": tool_input, "cwd": "/tmp"}
                ).encode("utf-8")
                reply = interception.run_hook("codex", "PreToolUse", payload, env={})
                self.assertNotEqual(reply.exit_code, 1)
                self.assertIn("hook_input_invalid", reply.stdout)

    def test_claude_agent_malformed_tool_input_never_crashes(self) -> None:
        """tool_input: null, a non-dict tool_input, and a non-str prompt field
        must each render hook_input_invalid, never raise AttributeError/TypeError."""
        for tool_input in (
            None, "not-a-dict", {"description": "d", "prompt": 123, "subagent_type": "x"}
        ):
            with self.subTest(tool_input=tool_input):
                payload = json.dumps(
                    {"tool_name": "Agent", "tool_input": tool_input, "cwd": "/tmp"}
                ).encode("utf-8")
                reply = interception.run_hook("claude", "PreToolUse", payload, env={})
                self.assertNotEqual(reply.exit_code, 1)
                self.assertIn("hook_input_invalid", reply.stdout)


def _cases(prefix: str) -> list[dict]:
    document = json.loads(CHARACTERIZATION.read_text(encoding="utf-8"))
    return [case for case in document["cases"] if case["case_id"].startswith(prefix)]


def _push_commands() -> list[str]:
    return [
        case["payload"]["tool_input"]["command"]
        for case in _cases("push-")
        if case["payload"]["tool_name"] == "Bash"
    ]


def _child_env(value: str | None):
    """os.environ without CLAUDE_CODE_CHILD_SESSION, or with it set to value."""
    env = {key: item for key, item in os.environ.items() if key != CHILD_ENV}
    if value is not None:
        env[CHILD_ENV] = value
    return mock.patch.dict(os.environ, env, clear=True)


def _calls(calls: tuple) -> list[tuple]:
    return [(call.duty, dict(call.context)) for call in calls]


def _duties(calls: tuple) -> list[str]:
    return sorted(call.duty.value for call in calls)


def _mentions(calls: tuple, path: str) -> bool:
    for call in calls:
        for value in call.context.values():
            if value == path or (isinstance(value, (list, tuple)) and path in value):
                return True
    return False


def _random_skill() -> str:
    """A per-run autopilot skill name no implementation can have memorised."""
    left, right = ("".join(random.choices(string.ascii_lowercase, k=8)) for _ in range(2))
    return f"autopilot:{left}-{right}"


def _filler() -> str:
    """Zero to four random hex words: a random offset for an embedded skill."""
    return " ".join(uuid.uuid4().hex for _ in range(random.randint(0, 4)))


def _fresh(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _assert_payload_sourced(case: unittest.TestCase, calls: tuple, cwd: str, session_id: str, *subject) -> None:
    """Every context value is the call's subject (path, command, skill) or comes
    from this payload: project_root is cwd, session is the payload session_id."""
    for call in calls:
        context = dict(call.context)
        if "project_root" in context:
            case.assertEqual(context["project_root"], cwd)
        if "session" in context:
            case.assertEqual(context["session"], session_id)
        for key, value in context.items():
            for item in value if isinstance(value, (list, tuple)) else (value,):
                case.assertIn(item, {cwd, session_id, *subject}, key)


def _agent(prompt: str, **extra) -> dict:
    tool_input = {"description": "d", "prompt": prompt, "subagent_type": "general-purpose"}
    return {"tool_name": "Agent", "tool_input": tool_input, "cwd": UNBOUND_CWD, **extra}


def _allow(duty: GuardDuty) -> GuardOutcome:
    return GuardOutcome(duty=duty, allowed=True, reason=None, stateful=False)


def _deny(duty: GuardDuty, reason: str) -> GuardOutcome:
    return GuardOutcome(duty=duty, allowed=False, reason=reason, stateful=False)


def _decision(host_id: str, event: str, outcomes: list, context: str | None = None) -> HookDecision:
    return HookDecision(
        host_id=host_id, event=event, session=None, project_root="/r", bound=True,
        outcomes=tuple(outcomes), skipped=(), allowed=all(o.allowed for o in outcomes),
        additional_context=context,
    )


def _body(reply) -> dict:
    return json.loads(reply.stdout) if reply.stdout.strip() else {}


class ClaudeTranslateHookTest(unittest.TestCase):
    def test_file_edits_check_the_document_location_under_the_payload_cwd(self) -> None:
        for tool in ("Edit", "Write", "MultiEdit"):
            for path, cwd in (("/r1/docs/a.md", "/r1"), ("/r2/src/b.py", "/r2")):
                with self.subTest(tool=tool, path=path):
                    tool_input: dict[str, object] = {"file_path": path}
                    if tool == "MultiEdit":
                        tool_input["edits"] = [{"old_string": "a", "new_string": "b"},
                                               {"old_string": "c", "new_string": "d"}]
                    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd}
                    calls = claude_adapter.translate_hook("PreToolUse", payload)
                    self.assertEqual(
                        _calls(calls),
                        [(GuardDuty.DOCUMENT_LOCATION, {"document_path": path, "project_root": cwd})],
                    )

    def test_tools_outside_the_registrations_emit_no_duty(self) -> None:
        for tool, tool_input in (("Read", {"command": "git push"}), ("Task", {"prompt": "autopilot:work"})):
            with self.subTest(tool=tool):
                payload = {"tool_name": tool, "tool_input": tool_input, "cwd": UNBOUND_CWD}
                self.assertEqual(claude_adapter.translate_hook("PreToolUse", payload), ())

    def test_skill_requests_check_post_handoff_for_the_requested_skill(self) -> None:
        cases = _cases("skill-")
        skills = {case["payload"]["tool_input"]["skill"] for case in cases}
        self.assertGreater(len(skills), 1)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                cwd, session_id = _fresh("/w"), _fresh("s")
                payload = {**case["payload"], "cwd": cwd, "session_id": session_id}
                calls = claude_adapter.translate_hook(case["event"], payload)
                self.assertEqual(_duties(calls), ["post_handoff"])
                skill = case["payload"]["tool_input"]["skill"]
                self.assertEqual(calls[0].context["requested_skill"], skill)
                _assert_payload_sourced(self, calls, cwd, session_id, skill)

    def test_agent_dispatch_names_the_first_explicit_skill_in_its_prompt(self) -> None:
        table = (
            ("Run autopilot:work now", "autopilot:work"),
            ("Call /autopilot:plan-tasks please", "autopilot:plan-tasks"),
            ("autopilot:review-work-completion then autopilot:work", "autopilot:review-work-completion"),
            ("sync with git-ferry:catchup", "git-ferry:catchup"),
            ("", ""),
            ("plugin:autopilot:work", ""),
            ("xautopilot:work", ""),
            ("git-ferry:catchups", ""),
            ("Autopilot:Work", ""),
            ("see claude-autopilot/hooks and run-autopilot/cli", ""),
        )
        first, second = _random_skill(), _random_skill()
        built = (  # per-run prompts: no table of literal prompts can pass these
            (f"{_filler()} autopilot:work {_filler()}", "autopilot:work"),
            (f"{_filler()} /{first} {_filler()} {second}", first),
            (f"{_filler()} git-ferry:catchup {_filler()} {first}", "git-ferry:catchup"),
            (_filler(), ""),
        )
        with _child_env(None):
            for prompt, expected in table + built:
                with self.subTest(prompt=prompt):
                    calls = claude_adapter.translate_hook("PreToolUse", _agent(prompt))
                    self.assertEqual(_duties(calls), ["delegation"])
                    self.assertEqual(calls[0].context["dispatch_skill"], expected)
                    self.assertEqual(calls[0].context["child_depth"], 0)

    def test_agent_dispatch_depth_counts_an_agent_id_or_a_child_session(self) -> None:
        table = (
            ({}, None, 0), ({"agent_id": ""}, None, 0), ({"agent_id": "agent-7"}, None, 1),
            ({}, "", 0), ({}, "child-3", 1), ({"agent_id": "agent-7"}, "child-3", 1),
        )
        for extra, env_value, depth in table:
            with self.subTest(extra=extra, env=env_value):
                with _child_env(env_value):
                    calls = claude_adapter.translate_hook("PreToolUse", _agent("go", **extra))
                self.assertEqual(_duties(calls), ["delegation"])
                self.assertNotIsInstance(calls[0].context["child_depth"], bool)
                self.assertEqual(calls[0].context["child_depth"], depth)

    def test_post_tool_file_edits_check_state_integrity_for_the_written_path(self) -> None:
        for name in ("docs/a.md", "src/b.py"):
            for tool in ("Edit", "Write", "MultiEdit"):
                cwd, session_id = _fresh("/w"), _fresh("s")
                path = f"{cwd}/{name}"
                with self.subTest(tool=tool, path=path):
                    payload = {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": cwd,
                               "session_id": session_id}
                    calls = claude_adapter.translate_hook("PostToolUse", payload)
                    self.assertTrue(calls)
                    self.assertEqual(set(_duties(calls)), {"state_integrity"})
                    self.assertTrue(_mentions(calls, path))
                    _assert_payload_sourced(self, calls, cwd, session_id, path)


class SharedTranslateHookTest(unittest.TestCase):
    def test_bash_adds_custody_push_exactly_for_git_pushes(self) -> None:
        commands = _push_commands()
        self.assertTrue(any(guards.is_git_push(c) for c in commands))
        self.assertFalse(all(guards.is_git_push(c) for c in commands))
        for host_id, module in INTERCEPTING:
            for _ in range(2):
                for command in commands:
                    cwd, session_id = _fresh("/w"), _fresh("s")
                    with self.subTest(host=host_id, cwd=cwd, command=command):
                        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd,
                                   "session_id": session_id}
                        raw = module.translate_hook("PreToolUse", payload)
                        _assert_payload_sourced(self, raw, cwd, session_id, command)
                        calls = _calls(raw)
                        docs = [ctx for duty, ctx in calls if duty is GuardDuty.DOCUMENT_LOCATION]
                        self.assertEqual(docs, [{"command": command, "project_root": cwd}])
                        pushes = [ctx for duty, ctx in calls if duty is GuardDuty.CUSTODY_PUSH]
                        expected = 1 if guards.is_git_push(command) else 0
                        self.assertEqual(len(pushes), expected)
                        self.assertEqual(len(calls), 1 + expected)
                        for ctx in pushes:
                            self.assertEqual(ctx["command"], command)

    def test_stop_checks_reviews_live_jobs_and_departure(self) -> None:
        for host_id, module in INTERCEPTING:
            with self.subTest(host=host_id):
                payload = {"session_id": "s1", "cwd": "/w", "hook_event_name": "Stop", "stop_hook_active": False}
                calls = module.translate_hook("Stop", payload)
                self.assertEqual(_duties(calls), ["departure", "live_job", "review_completeness"])

    def test_session_start_reinjects_the_contract_card(self) -> None:
        for host_id, module in INTERCEPTING:
            with self.subTest(host=host_id):
                payload = {"session_id": "s1", "cwd": "/w", "hook_event_name": "SessionStart", "source": "compact"}
                calls = module.translate_hook("SessionStart", payload)
                self.assertEqual(_duties(calls), ["context_reinjection"])


PATCH = (
    "*** Begin Patch\n"
    "*** Add File: docs/a.md\n"
    "+hello\n"
    "*** Update File: src/b.py\n"
    "*** Move to: src/c.py\n"
    "@@\n"
    "-old\n"
    "+*** Add File: smuggled.md\n"
    "*** Delete File: old/d.py\n"
    "*** End Patch\n"
)
PATCH_PATHS = ("docs/a.md", "src/b.py", "src/c.py")


class CodexTranslateHookTest(unittest.TestCase):
    def _payload(self, patch: str, cwd: str) -> dict:
        return {"tool_name": "apply_patch", "tool_input": {"patch": patch}, "cwd": cwd}

    def _patches(self) -> tuple:
        """(patch, checked paths): the literal PATCH plus per-run random ones."""
        add, update, moved, update_only, deleted = (f"{_fresh('d')}/{_fresh('f')}.md" for _ in range(5))
        random_patch = (f"*** Begin Patch\n*** Update File: {update}\n*** Move to: {moved}\n@@\n-a\n+b\n"
                        f"*** Add File: {add}\n+x\n*** End Patch\n")
        return (
            (PATCH, PATCH_PATHS),
            (random_patch, (update, moved, add)),
            (f"*** Begin Patch\n*** Update File: {update_only}\n@@\n-a\n+b\n*** End Patch\n", (update_only,)),
            (f"*** Begin Patch\n*** Delete File: {deleted}\n*** End Patch\n", ()),
        )

    def test_apply_patch_checks_every_added_updated_and_moved_path(self) -> None:
        for patch, paths in self._patches():
            cwd = _fresh("/w")
            with self.subTest(cwd=cwd, paths=paths):
                calls = codex_adapter.translate_hook("PreToolUse", self._payload(patch, cwd))
                expected = [{"document_path": path, "project_root": cwd} for path in sorted(paths)]
                docs = [c for duty, c in _calls(calls) if duty is GuardDuty.DOCUMENT_LOCATION]
                self.assertEqual(len(docs), len(calls))
                self.assertEqual(sorted(docs, key=lambda c: c["document_path"]), expected)

    def test_apply_patch_without_file_headers_checks_no_document(self) -> None:
        calls = codex_adapter.translate_hook("PreToolUse", self._payload("*** Begin Patch\n*** End Patch\n", "/w"))
        self.assertNotIn("document_location", _duties(calls))

    def test_post_apply_patch_checks_state_integrity_for_the_patched_paths(self) -> None:
        calls = codex_adapter.translate_hook("PostToolUse", self._payload(PATCH, "/w"))
        self.assertEqual(set(_duties(calls)), {"state_integrity"})
        for path in PATCH_PATHS:
            self.assertTrue(_mentions(calls, path), path)
        self.assertFalse(_mentions(calls, "smuggled.md"))
        for patch, paths in self._patches()[1:3]:
            cwd, session_id = _fresh("/w"), _fresh("s")
            with self.subTest(cwd=cwd, paths=paths):
                payload = {**self._payload(patch, cwd), "session_id": session_id}
                calls = codex_adapter.translate_hook("PostToolUse", payload)
                self.assertEqual(set(_duties(calls)), {"state_integrity"})
                for path in paths:
                    self.assertTrue(_mentions(calls, path), path)
                # exactly its paths: no other path, no hardcoded root or session
                _assert_payload_sourced(self, calls, cwd, session_id, *paths)


if __name__ == "__main__":
    unittest.main()
