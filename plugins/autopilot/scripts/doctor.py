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

_HOSTS_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "hosts.json"


class _AlwaysAllowSeam:
    """Doctor-only stand-in: every evaluate_guard call is allowed. The
    package ships no ControllerSeam implementation (design §4); FakeSeam is
    a test double that lives under tests/, never imported by production
    code."""

    def submit_job(self, intent: dict) -> dict:
        raise AssertionError("doctor never submits a job")

    def evaluate_guard(self, duty: str, context: dict) -> dict:
        return {"allowed": True, "reason": None}

    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict:
        return {}


@dataclass(frozen=True)
class DoctorReport:
    hosts: list[ProbeResult]
    guards: list[GuardOutcome]
    guards_simulated: bool
    profile: str  # "claude-free" | "mixed", derived from contracts/hosts.json
    generated_at: str


def diagnose(*, project_root: Path) -> DoctorReport:
    seam = _AlwaysAllowSeam()
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
