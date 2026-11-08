"""Gemini host adapter - native host seam for the Gemini CLI.

STATIC checks only: binary-on-PATH and GEMINI_API_KEY presence. Never invokes
`gemini` as a subprocess and never performs a live dispatch. Implements no
capability yet: session identity and in-session delegation are both inert, so
IMPLEMENTED_CAPABILITIES is empty and the declared contract is empty with it.
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

HOST_ID = "gemini"
IMPLEMENTED_CAPABILITIES: frozenset[str] = frozenset()


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


def session_identity() -> dict | None:
    return None


def can_delegate() -> bool:
    return False


def build_job_argv(intent) -> list[str] | None:
    return None
