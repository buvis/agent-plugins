"""Claude host adapter.

Static capability probing, native session identity, in-session delegation
reporting, job-argv construction and hook translation for the Claude host.
Never spawns a subprocess or invokes a provider CLI (AP 00014 architecture
fit). Bash, Stop and SessionStart translation and the reply rendering are
shared with codex.py, whose hooks speak the same wire format.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import codex
from guards import GuardDuty
from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    NativeSession,
    ProbeResult,
    statuses_from,
    unavailable,
)
from interception import DutyCall, HookRegistration
from jobs import JobRequest

HOST_ID = "claude"
IMPLEMENTED_CAPABILITIES = frozenset({"identity", "delegation", "isolation", "interception"})
SESSION_ENV_VAR = "CLAUDE_CODE_SESSION_ID"
CHILD_SESSION_ENV = "CLAUDE_CODE_CHILD_SESSION"
HOOK_REGISTRATIONS = (
    HookRegistration("PreToolUse", "Edit|Write|MultiEdit", 5),
    HookRegistration("PreToolUse", "Bash", 10),
    HookRegistration("PreToolUse", "Skill", 5),
    HookRegistration("PreToolUse", "Agent", 5),
    HookRegistration("PostToolUse", "Edit|Write|MultiEdit", 5),
    HookRegistration("Stop", None, 10),
    HookRegistration("SessionStart", "compact|resume", 5),
)

_FILE_TOOLS = ("Edit", "Write", "MultiEdit")
# A whole-token skill name, optionally slash-prefixed: no word, ":", "/" or
# "-" may touch it, so "plugin:autopilot:work" and "git-ferry:catchups" miss.
_SKILL_NAME = re.compile(r"(?<![\w:/-])/?(autopilot:[a-z0-9-]+|git-ferry:catchup)(?![\w:-])")


def probe(*, project_root: Path) -> ProbeResult:
    """STATIC checks only: binary-on-PATH and auth presence. Never a live
    dispatch, never a real Agent-tool round-trip."""
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("claude") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    authenticated = bool(
        os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    )
    return ProbeResult(
        host_id=HOST_ID,
        available=True,
        capability=HostCapability(
            host_id=HOST_ID,
            statuses=statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=authenticated),
        ),
        probed_at=probed_at,
        evidence_path=None,
        authenticated=authenticated,
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
    """True: the Agent tool is a true in-session subagent dispatch
    primitive - a tool call inside the running session, not a subprocess."""
    return True


def build_job_argv(request: JobRequest) -> list[str]:
    """The fixed argv; the job request travels on standard input."""
    return ["claude", "-p"]


def translate_hook(event: str, payload: Mapping[str, object]) -> tuple[DutyCall, ...]:
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input", {})
    cwd = payload.get("cwd")
    session = payload.get("session_id")
    if event == "PreToolUse" and tool in _FILE_TOOLS:
        context = {"document_path": tool_input.get("file_path"), "project_root": cwd}
        return (DutyCall(GuardDuty.DOCUMENT_LOCATION, context),)
    if event == "PostToolUse" and tool in _FILE_TOOLS:
        context = {"paths": (tool_input.get("file_path"),), "project_root": cwd, "session": session}
        return (DutyCall(GuardDuty.STATE_INTEGRITY, context),)
    if event == "PreToolUse" and tool == "Skill":
        context = {"requested_skill": tool_input.get("skill"), "session": session}
        return (DutyCall(GuardDuty.POST_HANDOFF, context),)
    if event == "PreToolUse" and tool == "Agent":
        match = _SKILL_NAME.search(tool_input.get("prompt", ""))
        depth = int(bool(payload.get("agent_id") or os.environ.get(CHILD_SESSION_ENV)))
        context = {"dispatch_skill": match.group(1) if match else "", "child_depth": depth}
        return (DutyCall(GuardDuty.DELEGATION, context),)
    return codex.translate_shared_hook(event, payload)


render_hook_reply = codex.render_hook_reply
