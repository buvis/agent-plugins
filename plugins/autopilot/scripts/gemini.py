"""Gemini host adapter - native host seam for the Gemini CLI.

STATIC checks only: binary-on-PATH and GEMINI_API_KEY presence. Never invokes
`gemini` as a subprocess and never performs a live dispatch. Implements
identity and isolation only: no in-session delegation, and no interception
because the package has no local surface to register Gemini hooks on.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    NativeSession,
    ProbeResult,
    statuses_from,
    unavailable,
)
from jobs import JobRequest

HOST_ID = "gemini"
IMPLEMENTED_CAPABILITIES = frozenset({"identity", "isolation"})
SESSION_ENV_VAR = "GEMINI_SESSION_ID"
INTERCEPTION_BLOCKER = "no_package_local_registration_surface"


def probe(*, project_root: Path) -> ProbeResult:
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("gemini") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    authenticated = bool(os.environ.get("GEMINI_API_KEY"))
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


def session_from_environment(env: Mapping[str, str]) -> NativeSession | None:
    """The native session env names, or None when NativeSession rejects it."""
    value = env.get(SESSION_ENV_VAR)
    if not isinstance(value, str):
        return None
    try:
        return NativeSession(HOST_ID, value, "environment")
    except ValueError:
        return None


def can_delegate() -> bool:
    return False


def build_job_argv(request: JobRequest) -> list[str]:
    """The fixed argv; the job request travels on standard input."""
    return ["gemini", "-p", "Follow the instructions on standard input."]
