"""Aggregate host probes and guard library checks into one report.

Guards run against a FakeSeam that always allows, so `guards_simulated` is
True: the report proves only that each library call succeeds end to end,
never that a real controller is reachable (AP 00016 ships the real seam).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from guards import GuardDuty, GuardOutcome, run_guard
from hosts import ProbeResult, probe_host
from jobs import FakeSeam

_HOSTS_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "hosts.json"


@dataclass(frozen=True)
class DoctorReport:
    hosts: list[ProbeResult]
    guards: list[GuardOutcome]
    guards_simulated: bool
    profile: str  # "claude-free" | "mixed", derived from contracts/hosts.json
    generated_at: str


def diagnose(*, project_root: Path) -> DoctorReport:
    seam = FakeSeam(guard_rules={duty.value: (True, None) for duty in GuardDuty})
    declared = json.loads(_HOSTS_CONTRACT.read_text(encoding="utf-8"))["hosts"]
    covered = set(declared["codex"]["capabilities"]) | set(declared["gemini"]["capabilities"])
    return DoctorReport(
        hosts=[probe_host(host_id, project_root=project_root)
               for host_id in ("claude", "codex", "gemini")],
        guards=[run_guard(duty, {}, seam=seam) for duty in GuardDuty],
        guards_simulated=True,
        profile="claude-free" if "identity" in covered else "mixed",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
