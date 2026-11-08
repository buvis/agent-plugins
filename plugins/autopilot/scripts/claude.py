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
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    ProbeResult,
    statuses_from,
    unavailable,
)

HOST_ID = "claude"
IMPLEMENTED_CAPABILITIES = frozenset({"identity", "delegation", "isolation", "interception"})


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


def session_identity() -> dict | None:
    """Native session id + process identity for the CURRENT session, or
    None when this host exposes none (e.g. running outside that host).

    CLAUDE_SESSION_ID is the Claude Code session-id environment variable; absent, this host exposes no native session identity."""
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
