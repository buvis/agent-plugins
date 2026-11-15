"""Tests for interception.py: find_binding, evaluate_hook and run_hook.

Scope note: hook_characterization.json also carries custody_push and
delegation/skill-lexicon fixtures. Those duties either need a live controller
seam (custody_push is stateful) or depend on the adapter's own translate_hook
extraction logic, which lands in a later task (Premise, task description).
test_hook_behavior_equivalence here covers only the document_location
fixtures, which are fully decidable from this module and guards.py alone.
"""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

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

GuardDuty = guards.GuardDuty
DutyCall = interception.DutyCall
HookDecision = interception.HookDecision

CHARACTERIZATION = TESTS_DIR / "hook_characterization.json"


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


if __name__ == "__main__":
    unittest.main()
