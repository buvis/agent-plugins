"""Pure reducers for `job.plan`, `job.claim`, and `job.record_exit` over workflow.jobs.

Each reducer takes the current jobs list and returns a new one; nothing here
reads a file, touches the store, or launches a process. A job claim is
exclusive through the null check on `claimed_by`, the same acquire pattern
the owner lease uses, so no separate lock exists.
"""

from __future__ import annotations

import copy

from . import actors, policy


def _reject(note: str) -> Exception:
    from . import protocol

    error = protocol.ProtocolError("rejected_evidence")
    error.add_note(note)
    return error


def _find(jobs: list[dict], job_id: str) -> int:
    for index, row in enumerate(jobs):
        if row["spec"]["job_id"] == job_id:
            return index
    raise _reject(f"unknown job: {job_id}")


def _replace(jobs: list[dict], index: int, row: dict) -> list[dict]:
    updated = copy.deepcopy(jobs)
    updated[index] = row
    return updated


def plan(jobs: list[dict], job_specs: list[dict]) -> list[dict]:
    """Append one unclaimed row per spec after checking ids and dependencies.

    New specs are checked together with the specs already planned, so a new
    id cannot repeat an existing one and a new job may depend on an old one.
    """
    if not isinstance(job_specs, list):
        raise policy.InvalidPlan("plan must be a list")
    policy.validate_plan_shape([row["spec"] for row in jobs] + job_specs,
                               id_key="job_id", depends_key="depends_on")
    rows = [{"spec": copy.deepcopy(spec), "claimed_by": None, "claim_epoch": None,
             "exit_fact": None} for spec in job_specs]
    return copy.deepcopy(jobs) + rows


def next_job(jobs: list[dict]) -> dict | None:
    """Return the first unclaimed job whose dependencies have already exited."""
    finished = {row["spec"]["job_id"] for row in jobs if row["exit_fact"] is not None}
    for row in jobs:
        if row["claimed_by"] is not None:
            continue
        if all(dependency in finished for dependency in row["spec"]["depends_on"]):
            return row
    return None


def claim(jobs: list[dict], job_id: str, actor_id: str, lease_epoch: int) -> list[dict]:
    """Bind an unclaimed job to the caller; a claimed job rejects every new claim."""
    index = _find(jobs, job_id)
    current = jobs[index]
    if current["claimed_by"] is not None:
        raise _reject(f"job already claimed: {job_id}")
    row = copy.deepcopy(current)
    row["claimed_by"] = actor_id
    row["claim_epoch"] = lease_epoch
    return _replace(jobs, index, row)


def record_exit(jobs: list[dict], job_id: str, actor_id: str, lease_epoch: int,
                exit_fact: dict) -> list[dict]:
    """Record the claimant's exit fact; an identical replay returns `jobs` unchanged."""
    index = _find(jobs, job_id)
    current = jobs[index]
    if current["claimed_by"] is None:
        raise _reject(f"job not claimed: {job_id}")
    if (current["claimed_by"], current["claim_epoch"]) != (actor_id, lease_epoch):
        raise _reject(f"caller does not hold the job claim: {job_id}")
    if current["exit_fact"] is not None:
        if actors.canonical(current["exit_fact"]) == actors.canonical(exit_fact):
            return jobs
        raise _reject(f"conflicting exit fact: {job_id}")
    row = copy.deepcopy(current)
    row["exit_fact"] = copy.deepcopy(exit_fact)
    return _replace(jobs, index, row)
