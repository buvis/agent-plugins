"""Aggregate static host probes, observed probe evidence, profile resolution
and a guard simulation into one schema_version 2 report.

`observed` comes only from the newest `<host_id>-<ts>.json` evidence under
docs/dev/tmp/autopilot/probes/ (written by tools/autopilot/probe-host.py); a
record whose resource check did not pass observes nothing. The guard
`simulation` runs every duty against valid contexts and a seam that always
allows, so it proves only that each library call succeeds end to end, never
that a real controller is reachable (AP 00016 ships the real seam). The
report is never `certified`.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import hosts
from guards import GuardDuty, run_guard
from review_evidence import load_policy
from roles import ProfileFacts, resolve_profile

_PROBES = Path("docs") / "dev" / "tmp" / "autopilot" / "probes"
# Pure duties decide from their own context; these allow by construction.
_SIMULATION_CONTEXTS = {
    GuardDuty.DOCUMENT_LOCATION: {"command": "true"},
    GuardDuty.DELEGATION: {"dispatch_skill": "doctor-simulation", "child_depth": 0},
    GuardDuty.POST_HANDOFF: {"requested_skill": "doctor-simulation", "leave_recorded": False},
    GuardDuty.DEPARTURE: {"leave_row_written": True, "last_store_write_at": 0, "leave_row_at": 0},
    GuardDuty.CONTEXT_REINJECTION: {"contract_card_present": True,
                                    "contract_card_body": "doctor simulation card"},
}


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


def _newest_evidence(project_root: Path, host_id: str) -> tuple[str, dict] | None:
    """The single newest `<host_id>-<ts>[-n].json` evidence file; an older
    valid record is never consulted as a fallback, so a malformed or
    wrong-schema newest candidate reports no evidence rather than resurrecting
    a stale one."""
    probes = project_root / _PROBES
    pattern = re.compile(rf"{re.escape(host_id)}-(\d{{8}}T\d{{6}}Z)(?:-(\d+))?\.json")
    found = []
    for path in probes.iterdir() if probes.is_dir() else ():
        match = pattern.fullmatch(path.name)
        if match and path.is_file():
            found.append(((match[1], int(match[2] or 1)), path))
    if not found:
        return None
    found.sort(key=lambda item: item[0], reverse=True)
    _, path = found[0]
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("schema_version") != 2:
        return None
    return (_PROBES / path.name).as_posix(), record


def _observed_capabilities(record: dict) -> frozenset[str]:
    if record.get("resource_check") != "passed":
        return frozenset()
    return frozenset(cap for cap, verdict in record["observed"].items()
                     if verdict["status"] == "observed")


def diagnose(*, project_root: Path) -> dict:
    policy = load_policy()
    evidence = {host_id: _newest_evidence(project_root, host_id) for host_id in hosts.ADAPTERS}
    observed = {host_id: _observed_capabilities(found[1])
                for host_id, found in evidence.items() if found}
    implemented = {host_id: hosts.adapter(host_id).IMPLEMENTED_CAPABILITIES
                   for host_id in hosts.ADAPTERS}
    gemini = evidence.get("gemini")
    gemini_ran = gemini is not None and any(
        invocation["exit_code"] == 0 for invocation in gemini[1]["invocations"])
    profiles = []
    for profile_id, profile in policy["execution_profiles"].items():
        facts = ProfileFacts(
            gemini_cli_available=gemini_ran, doubt_reviewer=None,
            implementor_codex_present="openai" in profile["implementor_providers"],
        )
        profiles.append(asdict(resolve_profile(
            policy, profile_id=profile_id, lane="full", facts=facts,
            implemented=implemented, observed=observed,
        )))
    seam = _AlwaysAllowSeam()
    return {
        "schema_version": 2,
        "hosts": [asdict(hosts.probe_host(host_id, project_root=project_root))
                  for host_id in hosts.ADAPTERS],
        "observed": {
            host_id: {"status": "not_probed"} if found is None else {
                "status": "probed", "evidence_path": found[0],
                "capabilities": sorted(observed[host_id]),
            }
            for host_id, found in evidence.items()
        },
        "profiles": profiles,
        "simulation": {
            "simulated": True,
            "guards": [asdict(run_guard(duty, _SIMULATION_CONTEXTS.get(duty, {}), seam=seam))
                       for duty in GuardDuty],
        },
        "certified": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
