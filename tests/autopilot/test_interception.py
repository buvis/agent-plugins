"""Tests for interception.py: find_binding, evaluate_hook and run_hook.

Scope note: hook_characterization.json also carries custody_push and
delegation/skill-lexicon fixtures. Those duties either need a live controller
seam (custody_push is stateful) or depend on the adapter's own translate_hook
extraction logic, which lands in a later task (Premise, task description).
test_hook_behavior_equivalence here covers only the document_location
fixtures, which are fully decidable from this module and guards.py alone.
The real claude/codex translate_hook and render_hook_reply are driven below
(ClaudeTranslateHookTest onward): push-* fixtures pin the duty-call shape,
skill-* and phase-* fixtures pin post_handoff and delegation extraction.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
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
# This fixture names its skill only in tool_input.description; the §2 contract
# scans tool_input.prompt alone. Held out until that conflict is settled.
PROMPT_CONTRACT_CONFLICTS = frozenset({"phase-denies-explicit-skill-name-fixture"})
INTERCEPTING = (("claude", claude_adapter), ("codex", codex_adapter))


def _doc_translate_hook(event: str, payload: dict) -> tuple:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input", {})
    if tool_name in ("Write", "Edit"):
        return (
            DutyCall(
                GuardDuty.DOCUMENT_LOCATION,
                {"document_path": tool_input["file_path"], "project_root": "<repo>"},
            ),
        )
    if tool_name == "MultiEdit":
        return tuple(
            DutyCall(
                GuardDuty.DOCUMENT_LOCATION,
                {"document_path": edit["file_path"], "project_root": "<repo>"},
            )
            for edit in tool_input["edits"]
        )
    if tool_name == "Bash":
        return (DutyCall(GuardDuty.DOCUMENT_LOCATION, {"command": tool_input["command"]}),)
    return ()


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

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            outer_binding = root.parent / ".autopilot" / "controller"
            outer_binding.mkdir(parents=True)
            try:
                self.assertIsNone(interception.find_binding(root))
            finally:
                import shutil

                shutil.rmtree(root.parent / ".autopilot")

    def test_a_binding_marker_that_is_a_file_not_a_directory_does_not_count(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".autopilot").mkdir()
            (root / ".autopilot" / "controller").write_text("not a dir")
            self.assertIsNone(interception.find_binding(root))


class EvaluateHookUnboundTest(unittest.TestCase):
    def test_unbound_skips_stateful_and_controller_keyed_pure_duties(self) -> None:
        host_fakes.install_adapter(
            self,
            "claude",
            translate_hook=lambda event, payload: (
                DutyCall(GuardDuty.CUSTODY_PUSH, {}),
                DutyCall(GuardDuty.POST_HANDOFF, {"requested_skill": "autopilot:work", "session": "s1"}),
                DutyCall(GuardDuty.DOCUMENT_LOCATION, {"document_path": "src/app.py"}),
            ),
            session_from_environment=lambda env: None,
        )
        decision = interception.evaluate_hook(
            "claude", "PreToolUse", {"cwd": "/does/not/exist"}, env={}, seam=None
        )
        self.assertFalse(decision.bound)
        self.assertEqual(
            set(decision.skipped), {("custody_push", "unbound"), ("post_handoff", "unbound")}
        )
        self.assertEqual(len(decision.outcomes), 1)
        self.assertTrue(decision.outcomes[0].allowed)
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


class HookBehaviorEquivalenceTest(unittest.TestCase):
    def test_hook_behavior_equivalence(self) -> None:
        document = json.loads(CHARACTERIZATION.read_text(encoding="utf-8"))
        cases = [
            case
            for case in document["cases"]
            if case["case_id"].startswith("doc-file-") or case["case_id"].startswith("doc-bash-")
        ]
        self.assertTrue(cases, "expected at least one doc-* fixture")
        host_fakes.install_adapter(
            self, "claude", translate_hook=_doc_translate_hook, session_from_environment=lambda env: None
        )
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                decision = interception.evaluate_hook(
                    "claude", case["event"], {**case["payload"], "cwd": "<repo>"}, env={}, seam=None
                )
                allowed = case["expected"] == "allow"
                self.assertIs(decision.allowed, allowed, msg=decision.outcomes)


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
                calls = claude_adapter.translate_hook(case["event"], case["payload"])
                self.assertEqual(_duties(calls), ["post_handoff"])
                self.assertEqual(calls[0].context["requested_skill"], case["payload"]["tool_input"]["skill"])

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
        with _child_env(None):
            for prompt, expected in table:
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
        paths = ("/w/docs/a.md", "/w/src/b.py")
        for path in paths:
            for tool in ("Edit", "Write", "MultiEdit"):
                with self.subTest(tool=tool, path=path):
                    payload = {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": "/w"}
                    calls = claude_adapter.translate_hook("PostToolUse", payload)
                    self.assertTrue(calls)
                    self.assertEqual(set(_duties(calls)), {"state_integrity"})
                    self.assertTrue(_mentions(calls, path))
                    self.assertFalse(_mentions(calls, next(p for p in paths if p != path)))


class SharedTranslateHookTest(unittest.TestCase):
    def test_bash_adds_custody_push_exactly_for_git_pushes(self) -> None:
        commands = _push_commands()
        self.assertTrue(any(guards.is_git_push(c) for c in commands))
        self.assertFalse(all(guards.is_git_push(c) for c in commands))
        for host_id, module in INTERCEPTING:
            for cwd in ("/w1", "/w2"):
                for command in commands:
                    with self.subTest(host=host_id, cwd=cwd, command=command):
                        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
                        calls = _calls(module.translate_hook("PreToolUse", payload))
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

    def test_apply_patch_checks_every_added_updated_and_moved_path(self) -> None:
        for cwd in ("/w1", "/w2"):
            with self.subTest(cwd=cwd):
                calls = codex_adapter.translate_hook("PreToolUse", self._payload(PATCH, cwd))
                expected = [{"document_path": path, "project_root": cwd} for path in PATCH_PATHS]
                self.assertEqual(_duties(calls), ["document_location"] * 3)
                self.assertEqual(sorted((c for _, c in _calls(calls)), key=lambda c: c["document_path"]), expected)

    def test_apply_patch_without_file_headers_checks_no_document(self) -> None:
        calls = codex_adapter.translate_hook("PreToolUse", self._payload("*** Begin Patch\n*** End Patch\n", "/w"))
        self.assertNotIn("document_location", _duties(calls))

    def test_post_apply_patch_checks_state_integrity_for_the_patched_paths(self) -> None:
        calls = codex_adapter.translate_hook("PostToolUse", self._payload(PATCH, "/w"))
        self.assertEqual(set(_duties(calls)), {"state_integrity"})
        for path in PATCH_PATHS:
            self.assertTrue(_mentions(calls, path), path)
        self.assertFalse(_mentions(calls, "smuggled.md"))


class RenderHookReplyTest(unittest.TestCase):
    def test_pre_tool_deny_carries_the_first_denied_reason(self) -> None:
        for host_id, module in INTERCEPTING:
            for first, second in (("r-alpha", "r-beta"), ("r-beta", "r-alpha")):
                with self.subTest(host=host_id, first=first):
                    outcomes = [_allow(GuardDuty.DOCUMENT_LOCATION), _deny(GuardDuty.DOCUMENT_LOCATION, first),
                                _deny(GuardDuty.CUSTODY_PUSH, second)]
                    reply = module.render_hook_reply(
                        "PreToolUse", _decision(host_id, "PreToolUse", outcomes), stop_active=False
                    )
                    self.assertEqual(reply.exit_code, 0)
                    self.assertEqual(_body(reply), {"hookSpecificOutput": {
                        "hookEventName": "PreToolUse", "permissionDecision": "deny",
                        "permissionDecisionReason": first}})

    def test_pre_tool_allow_never_denies(self) -> None:
        for host_id, module in INTERCEPTING:
            for outcomes in ([], [_allow(GuardDuty.DOCUMENT_LOCATION), _allow(GuardDuty.DELEGATION)]):
                with self.subTest(host=host_id, count=len(outcomes)):
                    reply = module.render_hook_reply(
                        "PreToolUse", _decision(host_id, "PreToolUse", outcomes), stop_active=False
                    )
                    self.assertEqual(reply.exit_code, 0)
                    output = _body(reply).get("hookSpecificOutput", {})
                    self.assertIn(output.get("permissionDecision"), ("allow", None))

    def test_post_tool_failure_is_reported_without_blocking(self) -> None:
        for host_id, module in INTERCEPTING:
            for reason in ("store-a broken", "store-b broken"):
                with self.subTest(host=host_id, reason=reason):
                    denied = _decision(host_id, "PostToolUse", [_deny(GuardDuty.STATE_INTEGRITY, reason)])
                    reply = module.render_hook_reply("PostToolUse", denied, stop_active=False)
                    self.assertEqual(reply.exit_code, 0)
                    self.assertIn(reason, _body(reply)["systemMessage"])
                    self.assertNotEqual(_body(reply).get("decision"), "block")
            allowed = _decision(host_id, "PostToolUse", [_allow(GuardDuty.STATE_INTEGRITY)])
            reply = module.render_hook_reply("PostToolUse", allowed, stop_active=False)
            self.assertEqual(reply.exit_code, 0)
            self.assertNotIn("systemMessage", _body(reply))

    def test_stop_blocks_once_then_lets_the_stop_through(self) -> None:
        for host_id, module in INTERCEPTING:
            for reason in ("lane L1 live", "review missing"):
                with self.subTest(host=host_id, reason=reason):
                    denied = _decision(host_id, "Stop", [_allow(GuardDuty.REVIEW_COMPLETENESS),
                                                         _deny(GuardDuty.LIVE_JOB, reason)])
                    blocked = module.render_hook_reply("Stop", denied, stop_active=False)
                    self.assertEqual(blocked.exit_code, 0)
                    self.assertEqual(_body(blocked)["decision"], "block")
                    self.assertIn(reason, _body(blocked)["reason"])
                    released = module.render_hook_reply("Stop", denied, stop_active=True)
                    self.assertEqual(released.exit_code, 0)
                    self.assertNotEqual(_body(released).get("decision"), "block")
            allowed = _decision(host_id, "Stop", [_allow(GuardDuty.LIVE_JOB)])
            self.assertNotEqual(_body(module.render_hook_reply("Stop", allowed, stop_active=False)).get("decision"),
                                "block")

    def test_session_start_surfaces_additional_context_only_when_present(self) -> None:
        for host_id, module in INTERCEPTING:
            for text in ("step: build | next: review", "step: review | next: close"):
                with self.subTest(host=host_id, text=text):
                    decision = _decision(host_id, "SessionStart", [_allow(GuardDuty.CONTEXT_REINJECTION)], text)
                    reply = module.render_hook_reply("SessionStart", decision, stop_active=False)
                    self.assertEqual(reply.exit_code, 0)
                    output = _body(reply)["hookSpecificOutput"]
                    self.assertEqual(output["hookEventName"], "SessionStart")
                    self.assertEqual(output["additionalContext"], text)
            empty = _decision(host_id, "SessionStart", [_deny(GuardDuty.CONTEXT_REINJECTION, "no card")])
            reply = module.render_hook_reply("SessionStart", empty, stop_active=False)
            self.assertEqual(reply.exit_code, 0)
            self.assertNotIn("additionalContext", reply.stdout)


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
                    expected = (("custody_push", "unbound"),) if guards.is_git_push(command) else ()
                    self.assertEqual(decision.skipped, expected)
                    self.assertEqual([o.duty for o in decision.outcomes], [GuardDuty.DOCUMENT_LOCATION])

    def test_phase_fixtures_match_their_recorded_verdict(self) -> None:
        cases = _cases("phase-")
        self.assertLessEqual(PROMPT_CONTRACT_CONFLICTS, {case["case_id"] for case in cases})
        with _child_env(None):
            for case in cases:
                if case["case_id"] in PROMPT_CONTRACT_CONFLICTS:
                    continue
                with self.subTest(case_id=case["case_id"]):
                    payload = {**case["payload"], "cwd": UNBOUND_CWD}
                    decision = interception.evaluate_hook("claude", case["event"], payload, env={}, seam=None)
                    self.assertIs(decision.allowed, case["expected"] == "allow", msg=decision.outcomes)

    def test_dispatching_a_whole_phase_skill_in_the_prompt_is_denied(self) -> None:
        table = (("Call /autopilot:plan-tasks", False), ("Run autopilot:work", False),
                 ("Call /autopilot:plan-tasks-notes", True), ("Summarize the diff", True))
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
                    self.assertEqual(decision.outcomes[0].reason, "recursion_depth")

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
