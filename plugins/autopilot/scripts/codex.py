"""Codex host adapter — native host seam for the Codex CLI.

STATIC checks only: binary-on-PATH and auth-file/env-var presence. Never
invokes `codex` as a subprocess and never performs a live dispatch.
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

HOST_ID = "codex"
IMPLEMENTED_CAPABILITIES = frozenset({"isolation"})

_AUTH_ENV_VAR = "CODEX_API_KEY"
_AUTH_FILE = Path.home() / ".codex" / "auth.json"


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


def session_identity() -> dict | None:
    return None


def can_delegate() -> bool:
    return False


def build_job_argv(intent: "JobIntent") -> list[str] | None:
    return None
