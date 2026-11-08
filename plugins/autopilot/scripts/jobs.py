"""Cross-session job intents and the controller seam.

Builds host-neutral job intents and either returns a standalone launch
instruction or forwards the intent to a controller seam. Never starts a
process (AP 00014 architecture fit).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from types import ModuleType
from typing import Protocol


@dataclass(frozen=True)
class JobIntent:
    job_id: str
    role: str
    inputs: dict
    isolation: str
    tier: str
    effort: str  # characterized only; CLI forwarding is OV 00059
    policy_constraints: dict


class ControllerSeam(Protocol):
    def submit_job(self, intent: JobIntent) -> dict: ...

    def evaluate_guard(self, duty: str, context: dict) -> dict: ...


class FakeSeam:
    """Records submitted intents and answers evaluate_guard from fixture
    rules ({duty: (allowed, reason)}). Never launches anything."""

    def __init__(self, *, guard_rules: dict) -> None:
        self.guard_rules = guard_rules
        self.submitted_intents: list[JobIntent] = []

    def submit_job(self, intent: JobIntent) -> dict:
        self.submitted_intents.append(intent)
        return {"accepted": True, "job_ref": f"fake-job-{len(self.submitted_intents)}"}

    def evaluate_guard(self, duty: str, context: dict) -> dict:
        allowed, reason = self.guard_rules.get(duty, (True, None))
        return {"allowed": allowed, "reason": reason}


def build_job_intent(
    *,
    job_id: str,
    role: str,
    inputs: dict,
    isolation: str,
    tier: str,
    effort: str,
    policy_constraints: dict,
) -> JobIntent:
    return JobIntent(
        job_id=job_id,
        role=role,
        inputs=inputs,
        isolation=isolation,
        tier=tier,
        effort=effort,
        policy_constraints=policy_constraints,
    )


def recursive_child_denied(intent: JobIntent, *, host: ModuleType, ancestry: list[dict]) -> bool:
    """True when the inherited ancestry already holds this host and job."""
    return any(
        entry["host_id"] == host.HOST_ID and entry["job_id"] == intent.job_id
        for entry in ancestry
    )


def request_cross_session_job(
    intent: JobIntent, *, seam: ControllerSeam | None, host: ModuleType, ancestry: list[dict]
) -> dict:
    """Standalone mode (seam None) returns the host argv plus the complete
    intent; controller mode forwards to seam.submit_job. Never starts a
    process."""
    if recursive_child_denied(intent, host=host, ancestry=ancestry):
        raise RecursionError(
            f"recursive job denied: host {host.HOST_ID!r} job {intent.job_id!r} already in ancestry"
        )
    if seam is None:
        return {
            "mode": "standalone",
            "instruction": {"argv": host.build_job_argv(intent), "intent": asdict(intent)},
        }
    return {"mode": "controller", **seam.submit_job(intent)}
