from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from hosts import (
    CapabilityStatus,
    HostCapability,
    ProbeResult,
    UNAVAILABLE_NO_AUTH,
    UNAVAILABLE_NO_BINARY,
)

HOST_ID = "gemini"


def probe(*, project_root: Path) -> ProbeResult:
    binary = shutil.which("gemini")
    if binary is None:
        identity_status = CapabilityStatus(
            name="identity", status="unavailable", reason=UNAVAILABLE_NO_BINARY
        )
        available = False
    elif os.environ.get("GEMINI_API_KEY"):
        identity_status = CapabilityStatus(name="identity", status="available", reason=None)
        available = True
    else:
        identity_status = CapabilityStatus(
            name="identity", status="unavailable", reason=UNAVAILABLE_NO_AUTH
        )
        available = False

    statuses = {
        "identity": identity_status,
        "delegation": CapabilityStatus(name="delegation", status="unimplemented", reason=None),
        "isolation": CapabilityStatus(name="isolation", status="unimplemented", reason=None),
        "interception": CapabilityStatus(name="interception", status="unimplemented", reason=None),
    }

    return ProbeResult(
        host_id=HOST_ID,
        available=available,
        capability=HostCapability(host_id=HOST_ID, statuses=statuses),
        probed_at=datetime.now(timezone.utc).isoformat(),
        evidence_path=None,
    )


def session_identity() -> dict | None:
    return None


def can_delegate() -> bool:
    return False


def build_job_argv(intent) -> list[str] | None:
    return None
