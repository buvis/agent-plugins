"""Claude host adapter.

Static capability probing, native session identity, in-session delegation
reporting, and job-argv construction for the Claude host. Never spawns a
subprocess or invokes a provider CLI (AP 00014 architecture fit).
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from hosts import (
    CAPABILITY_NAMES,
    UNAVAILABLE_NO_AUTH,
    CapabilityStatus,
    HostCapability,
    ProbeResult,
)


def probe(*, project_root: Path) -> ProbeResult:
    """STATIC checks only: binary-on-PATH and auth presence. Never a live
    dispatch, never a real Agent-tool round-trip."""
    probed_at = datetime.now(timezone.utc).isoformat()
    binary = shutil.which("claude")
    if binary is None:
        return ProbeResult(
            host_id="claude",
            available=False,
            capability=None,
            probed_at=probed_at,
            evidence_path=None,
        )

    authenticated = bool(
        os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    )

    statuses: dict[str, CapabilityStatus] = {}
    for name in CAPABILITY_NAMES:
        if name == "interception":
            # Hardcoded "available" for Claude: client-native hook
            # registration (PreToolUse/PostToolUse/Stop) is a first-class
            # host feature, unlike codex/gemini, and is not gated by auth.
            statuses[name] = CapabilityStatus(name=name, status="available", reason=None)
        elif authenticated:
            statuses[name] = CapabilityStatus(name=name, status="available", reason=None)
        else:
            statuses[name] = CapabilityStatus(
                name=name, status="unavailable", reason=UNAVAILABLE_NO_AUTH
            )

    return ProbeResult(
        host_id="claude",
        available=True,
        capability=HostCapability(host_id="claude", statuses=statuses),
        probed_at=probed_at,
        evidence_path=None,
    )


def session_identity() -> dict | None:
    """Native session id + process identity for the CURRENT session, or
    None when this host exposes none (e.g. running outside that host)."""
    session_id = os.environ.get("CLAUDE_SESSION_ID")
    if session_id is None:
        return None
    return {"host": "claude", "session_id": session_id, "pid": os.getpid()}


def can_delegate() -> bool:
    """True: the Agent tool is a true in-session subagent dispatch
    primitive - a tool call inside the running session, not a subprocess."""
    return True


def build_job_argv(intent: "JobIntent") -> list[str] | None:
    """Claude has no documented native CLI job-launch argv convention -
    return None rather than inventing one."""
    return None
