"""Codex host adapter — native host seam for the Codex CLI.

STATIC checks only: binary-on-PATH and auth-file/env-var presence. Never
invokes `codex` as a subprocess and never performs a live dispatch.

Codex hooks send Claude Code's payload shape for Bash, Stop and SessionStart
and read Claude Code's reply JSON, so `translate_shared_hook` and
`render_hook_reply` serve claude.py as well. This module never imports claude.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from guards import GuardDuty, is_git_push
from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    NativeSession,
    ProbeResult,
    statuses_from,
    unavailable,
)
from interception import DutyCall, HookRegistration, HookReply
from jobs import JobRequest

HOST_ID = "codex"
IMPLEMENTED_CAPABILITIES = frozenset({"identity", "isolation", "interception"})
SESSION_ENV_VAR = "CODEX_SESSION_ID"
HOOK_REGISTRATIONS = (
    HookRegistration("PreToolUse", "Bash", 10),
    HookRegistration("PreToolUse", "apply_patch", 5),
    HookRegistration("PostToolUse", "apply_patch", 5),
    HookRegistration("Stop", None, 10),
    HookRegistration("SessionStart", None, 5),
)

_AUTH_ENV_VAR = "CODEX_API_KEY"
_AUTH_FILE = Path.home() / ".codex" / "auth.json"
# Only these headers name a path the patch writes; a "+" content line that
# looks like a header is file text, and a deleted file is never written.
_PATCH_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Move to: ")
_STOP_DUTIES = (GuardDuty.REVIEW_COMPLETENESS, GuardDuty.LIVE_JOB, GuardDuty.DEPARTURE)


def _has_auth() -> bool:
    return bool(os.environ.get(_AUTH_ENV_VAR)) or _AUTH_FILE.exists()


def probe(*, project_root: Path) -> ProbeResult:
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("codex") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    has_auth = _has_auth()
    return ProbeResult(
        host_id=HOST_ID,
        available=True,
        capability=HostCapability(
            host_id=HOST_ID,
            statuses=statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=has_auth),
        ),
        probed_at=probed_at,
        evidence_path=None,
        authenticated=has_auth,
    )


def _session(value: object, source: str) -> NativeSession | None:
    """The native session for `value`, or None when NativeSession rejects it."""
    if not isinstance(value, str):
        return None
    try:
        return NativeSession(HOST_ID, value, source)
    except ValueError:
        return None


def session_from_environment(env: Mapping[str, str]) -> NativeSession | None:
    return _session(env.get(SESSION_ENV_VAR), "environment")


def session_from_hook_input(payload: Mapping[str, object]) -> NativeSession | None:
    return _session(payload.get("session_id"), "hook_input")


def can_delegate() -> bool:
    return False


def build_job_argv(request: JobRequest) -> list[str]:
    """The fixed argv; the job request travels on standard input."""
    return ["codex", "exec", "-"]


def translate_shared_hook(event: str, payload: Mapping[str, object]) -> tuple[DutyCall, ...]:
    """Duty calls for a Bash pre-tool, Stop or SessionStart payload."""
    cwd = payload.get("cwd")
    if event == "PreToolUse" and payload.get("tool_name") == "Bash":
        command = payload.get("tool_input", {}).get("command")
        calls = [DutyCall(GuardDuty.DOCUMENT_LOCATION, {"command": command, "project_root": cwd})]
        if isinstance(command, str) and is_git_push(command):
            calls.append(DutyCall(GuardDuty.CUSTODY_PUSH, {"command": command, "project_root": cwd}))
        return tuple(calls)
    session = payload.get("session_id")
    if event == "Stop":
        return tuple(DutyCall(duty, {"project_root": cwd, "session": session}) for duty in _STOP_DUTIES)
    if event == "SessionStart":
        return (DutyCall(GuardDuty.CONTEXT_REINJECTION, {"project_root": cwd, "session": session}),)
    return ()


def _patch_paths(payload: Mapping[str, object]) -> tuple[str, ...]:
    patch = payload.get("tool_input", {}).get("patch", "")
    return tuple(
        sorted(
            {
                line[len(header) :]
                for line in patch.splitlines()
                for header in _PATCH_HEADERS
                if line.startswith(header)
            }
        )
    )


def translate_hook(event: str, payload: Mapping[str, object]) -> tuple[DutyCall, ...]:
    if payload.get("tool_name") != "apply_patch":
        return translate_shared_hook(event, payload)
    cwd = payload.get("cwd")
    paths = _patch_paths(payload)
    if event == "PreToolUse":
        return tuple(
            DutyCall(GuardDuty.DOCUMENT_LOCATION, {"document_path": path, "project_root": cwd})
            for path in paths
        )
    if event == "PostToolUse":
        context = {"paths": paths, "project_root": cwd, "session": payload.get("session_id")}
        return (DutyCall(GuardDuty.STATE_INTEGRITY, context),)
    return ()


def render_hook_reply(event: str, decision, *, stop_active: bool) -> HookReply:
    """A pre-tool deny names the first denied reason; a post-tool failure is
    reported, never blocked; a Stop blocks once (not while stop_active)."""
    denied = [outcome.reason for outcome in decision.outcomes if not outcome.allowed]
    body: dict | None = None
    if event == "PreToolUse" and denied:
        body = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": denied[0],
            }
        }
    elif event == "PostToolUse" and denied:
        body = {"systemMessage": "autopilot: " + "; ".join(denied)}
    elif event == "Stop" and denied and not stop_active:
        body = {"decision": "block", "reason": "; ".join(denied)}
    elif event == "SessionStart" and decision.additional_context:
        body = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": decision.additional_context,
            }
        }
    return HookReply(stdout=json.dumps(body) if body else "", exit_code=0)
