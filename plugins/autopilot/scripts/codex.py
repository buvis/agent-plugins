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
    UNAVAILABLE_NO_AUTH,
    CapabilityStatus,
    HostCapability,
    ProbeResult,
)

HOST_ID = "codex"

_AUTH_ENV_VAR = "CODEX_API_KEY"
_AUTH_FILE = Path.home() / ".codex" / "auth.json"


def _has_auth() -> bool:
    return bool(os.environ.get(_AUTH_ENV_VAR)) or _AUTH_FILE.exists()


def probe(*, project_root: Path) -> ProbeResult:
    probed_at = datetime.now(timezone.utc).isoformat()
    binary = shutil.which("codex")
    if binary is None:
        return ProbeResult(
            host_id="codex",
            available=False,
            capability=None,
            probed_at=probed_at,
            evidence_path=None,
        )

    has_auth = _has_auth()
    status = "available" if has_auth else "unavailable"
    reason = None if has_auth else UNAVAILABLE_NO_AUTH

    statuses = {
        name: CapabilityStatus(name=name, status=status, reason=reason)
        for name in ("identity", "delegation", "isolation")
    }
    statuses["interception"] = CapabilityStatus(
        name="interception", status="unimplemented", reason=None
    )

    return ProbeResult(
        host_id="codex",
        available=True,
        capability=HostCapability(host_id="codex", statuses=statuses),
        probed_at=probed_at,
        evidence_path=None,
    )


def session_identity() -> dict | None:
    return None


def can_delegate() -> bool:
    return False


def build_job_argv(intent: "JobIntent") -> list[str] | None:
    return None
