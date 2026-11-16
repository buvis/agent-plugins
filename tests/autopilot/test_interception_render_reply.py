"""Tests for the claude and codex render_hook_reply shapes (split from test_interception.py)."""

from __future__ import annotations

import unittest

from test_interception import (
    GuardDuty,
    INTERCEPTING,
    _allow,
    _body,
    _decision,
    _deny,
    _fresh,
    claude_adapter,
    codex_adapter,
)


class RenderHookReplyTest(unittest.TestCase):
    def test_pre_tool_deny_joins_every_reason(self) -> None:
        # Claude's shapes are identical to codex's (see
        # CodexRenderHookReplyContractTest.test_pre_tool_deny_joins_every_reason):
        # a multi-reason deny must name every reason, not just the first.
        for host_id, module in (("claude", claude_adapter),):
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
                        "permissionDecisionReason": f"{first}; {second}"}})

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

    def test_post_tool_refusal_blocks_with_a_reason(self) -> None:
        # Claude's shapes are identical to codex's (see
        # CodexRenderHookReplyContractTest.test_post_tool_refused_blocks_with_a_reason):
        # a refusal blocks, it does not merely report a systemMessage.
        for host_id, module in (("claude", claude_adapter),):
            for reason in ("store-a broken", "store-b broken"):
                with self.subTest(host=host_id, reason=reason):
                    denied = _decision(host_id, "PostToolUse", [_deny(GuardDuty.STATE_INTEGRITY, reason)])
                    reply = module.render_hook_reply("PostToolUse", denied, stop_active=False)
                    self.assertEqual(reply.exit_code, 0)
                    self.assertEqual(_body(reply), {"decision": "block", "reason": reason})
            allowed = _decision(host_id, "PostToolUse", [_allow(GuardDuty.STATE_INTEGRITY)])
            reply = module.render_hook_reply("PostToolUse", allowed, stop_active=False)
            self.assertEqual(reply.exit_code, 0)
            self.assertNotEqual(_body(reply).get("decision"), "block")

    def _assert_block_names_a_denied_reason(self, module, host_id: str) -> None:
        """The deny need not be the last outcome, and an allow's None reason never leaks."""
        first, second = _fresh("review missing"), _fresh("lane live")
        for outcomes, reasons in (
            ([_deny(GuardDuty.LIVE_JOB, first), _allow(GuardDuty.DEPARTURE)], (first,)),
            ([_deny(GuardDuty.REVIEW_COMPLETENESS, first), _deny(GuardDuty.LIVE_JOB, second),
              _allow(GuardDuty.DEPARTURE)], (first, second)),
        ):
            with self.subTest(host=host_id, reasons=reasons):
                body = _body(module.render_hook_reply("Stop", _decision(host_id, "Stop", outcomes), stop_active=False))
                self.assertEqual(body["decision"], "block")
                self.assertTrue(any(reason in body["reason"] for reason in reasons), body["reason"])
                self.assertNotIn("None", body["reason"])

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
            self._assert_block_names_a_denied_reason(module, host_id)
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

    def test_stop_refused_with_stop_active_still_surfaces_a_system_message(self) -> None:
        # Claude's shapes are identical to codex's (see
        # CodexRenderHookReplyContractTest.test_stop_refused_with_stop_active_still_surfaces_a_system_message).
        for reason in (_fresh("review missing"), _fresh("lane live")):
            with self.subTest(reason=reason):
                denied = _decision("claude", "Stop", [_deny(GuardDuty.LIVE_JOB, reason)])
                reply = claude_adapter.render_hook_reply("Stop", denied, stop_active=True)
                self.assertEqual(reply.exit_code, 0)
                body = _body(reply)
                self.assertIn("systemMessage", body)
                self.assertIn(reason, body["systemMessage"])
                self.assertNotEqual(body.get("decision"), "block")

    def test_session_start_refusal_surfaces_a_system_message(self) -> None:
        # Claude's shapes are identical to codex's (see
        # CodexRenderHookReplyContractTest.test_session_start_refused_surfaces_a_system_message).
        for reason in (_fresh("no card"), _fresh("card stale")):
            with self.subTest(reason=reason):
                denied = _decision("claude", "SessionStart", [_deny(GuardDuty.CONTEXT_REINJECTION, reason)])
                reply = claude_adapter.render_hook_reply("SessionStart", denied, stop_active=False)
                self.assertEqual(reply.exit_code, 0)
                body = _body(reply)
                self.assertIn("systemMessage", body)
                self.assertIn(reason, body["systemMessage"])
                self.assertNotIn("additionalContext", body.get("hookSpecificOutput", {}))


class CodexRenderHookReplyContractTest(unittest.TestCase):
    """codex.py:147's reply shapes diverge from claude's: PostToolUse refusal
    blocks, Stop/SessionStart refusal always surfaces a systemMessage, and a
    PreToolUse deny names every reason, not just the first."""

    def test_pre_tool_deny_joins_every_reason(self) -> None:
        for first, second in (("r-alpha", "r-beta"), ("r-beta", "r-alpha")):
            with self.subTest(first=first):
                outcomes = [_allow(GuardDuty.DOCUMENT_LOCATION), _deny(GuardDuty.DOCUMENT_LOCATION, first),
                            _deny(GuardDuty.CUSTODY_PUSH, second)]
                reply = codex_adapter.render_hook_reply(
                    "PreToolUse", _decision("codex", "PreToolUse", outcomes), stop_active=False
                )
                self.assertEqual(reply.exit_code, 0)
                self.assertEqual(_body(reply), {"hookSpecificOutput": {
                    "hookEventName": "PreToolUse", "permissionDecision": "deny",
                    "permissionDecisionReason": f"{first}; {second}"}})

    def test_pre_tool_deny_with_a_single_reason_does_not_add_a_separator(self) -> None:
        outcomes = [_allow(GuardDuty.DOCUMENT_LOCATION), _deny(GuardDuty.DOCUMENT_LOCATION, "r-solo")]
        reply = codex_adapter.render_hook_reply(
            "PreToolUse", _decision("codex", "PreToolUse", outcomes), stop_active=False
        )
        self.assertEqual(
            _body(reply)["hookSpecificOutput"]["permissionDecisionReason"], "r-solo"
        )

    def test_post_tool_refused_blocks_with_a_reason(self) -> None:
        for reason in ("store-a broken", "store-b broken"):
            with self.subTest(reason=reason):
                denied = _decision("codex", "PostToolUse", [_deny(GuardDuty.STATE_INTEGRITY, reason)])
                reply = codex_adapter.render_hook_reply("PostToolUse", denied, stop_active=False)
                self.assertEqual(reply.exit_code, 0)
                self.assertEqual(_body(reply), {"decision": "block", "reason": reason})
        allowed = _decision("codex", "PostToolUse", [_allow(GuardDuty.STATE_INTEGRITY)])
        reply = codex_adapter.render_hook_reply("PostToolUse", allowed, stop_active=False)
        self.assertEqual(reply.exit_code, 0)
        self.assertNotEqual(_body(reply).get("decision"), "block")

    def test_stop_refused_with_stop_active_still_surfaces_a_system_message(self) -> None:
        reason = _fresh("review missing")
        denied = _decision("codex", "Stop", [_deny(GuardDuty.LIVE_JOB, reason)])
        reply = codex_adapter.render_hook_reply("Stop", denied, stop_active=True)
        self.assertEqual(reply.exit_code, 0)
        self.assertNotEqual(reply.stdout.strip(), "")
        body = _body(reply)
        self.assertIn("systemMessage", body)
        self.assertIn(reason, body["systemMessage"])
        self.assertTrue(body["systemMessage"].startswith("autopilot: "))

    def test_session_start_refused_surfaces_a_system_message(self) -> None:
        reason = _fresh("no card")
        denied = _decision("codex", "SessionStart", [_deny(GuardDuty.CONTEXT_REINJECTION, reason)])
        reply = codex_adapter.render_hook_reply("SessionStart", denied, stop_active=False)
        self.assertEqual(reply.exit_code, 0)
        body = _body(reply)
        self.assertIn("systemMessage", body)
        self.assertIn(reason, body["systemMessage"])


if __name__ == "__main__":
    unittest.main()
