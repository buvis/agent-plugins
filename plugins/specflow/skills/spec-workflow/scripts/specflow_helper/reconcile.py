"""Reconciliation: derived facts from the files, and what only the developer can decide."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .canonical import sha256_canonical, sha256_raw
from .state import (
    ARTIFACTS,
    ORDERS,
    STATE_FILE,
    artifact_paths,
    artifact_status,
    derive_phase,
    load_state,
    workflow_order,
)

DERIVED_STATUS = ("missing", "draft", "stale")


class ConflictError(Exception):
    """A file changed between the operation's read and its write."""


def write_guarded(path: Path, data: bytes, read_sha256: str | None) -> None:
    """Write only if the file still has the hash read at the start (None: still absent).

    Not a lock: one active writer per spec is the contract (WF-006).
    """
    current = sha256_raw(path) if path.exists() else None
    if current != read_sha256:
        raise ConflictError(f"{path}: changed since it was read; nothing was written")
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def recovery(spec_dir: Path) -> dict:
    """No state file: objective facts only, and every approval left to the developer."""
    statuses = artifact_status(spec_dir, None)
    order = workflow_order(spec_dir, None)
    paths = artifact_paths(spec_dir, None)
    ambiguous = [
        {
            "artifact": name,
            "path": paths[name].name,
            "reason": f"no {STATE_FILE} records whether it was approved",
        }
        for name in (*ORDERS[order], "tasks")
        if statuses[name] != "missing"
    ]
    return {
        "spec": spec_dir.name,
        "statuses": statuses,
        "phase": derive_phase(spec_dir, statuses, order),
        "changes": [],
        "ambiguous": ambiguous,
    }


def derived_changes(
    spec_dir: Path,
    state: dict,
    statuses: dict[str, str],
) -> tuple[list, list]:
    """The sha256 and status values reconcile may write, and the approvals it cannot read."""
    paths = artifact_paths(spec_dir, state)
    changes: list[dict] = []
    ambiguous: list[dict] = []
    for name in ARTIFACTS:
        record = state["artifacts"][name]
        if record.get("status") == "approved" and "approvedSha256" not in record:
            ambiguous.append(
                {
                    "artifact": name,
                    "path": paths[name].name,
                    "reason": "recorded approved without an approvedSha256",
                },
            )
            continue
        wanted = {}
        if paths[name].exists():
            wanted["sha256"] = sha256_canonical(paths[name])
        if statuses[name] in DERIVED_STATUS:
            wanted["status"] = statuses[name]
        for field, value in wanted.items():
            if record.get(field) != value:
                changes.append(
                    {
                        "artifact": name,
                        "field": field,
                        "from": record.get(field),
                        "to": value,
                    },
                )
    return changes, ambiguous


def apply_changes(state: dict, changes: list[dict]) -> dict:
    """A copy of the state with the derived values set; every other key keeps its place."""
    updated = json.loads(json.dumps(state))
    for change in changes:
        updated["artifacts"][change["artifact"]][change["field"]] = change["to"]
    return updated


def render(state: dict) -> bytes:
    return (json.dumps(state, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def reconcile(spec_dir: Path, *, dry_run: bool) -> dict:
    """Recompute hashes and statuses; write only derived facts, and only when not a dry run.

    Never creates a state file and never replaces a malformed one: load_state raises
    StateError for those, and the file is left as it is.
    """
    path = spec_dir / STATE_FILE
    read_sha256 = sha256_raw(path) if path.exists() else None
    state = load_state(spec_dir)
    if state is None:
        return recovery(spec_dir)
    statuses = artifact_status(spec_dir, state)
    changes, ambiguous = derived_changes(spec_dir, state, statuses)
    if changes and not dry_run:
        write_guarded(path, render(apply_changes(state, changes)), read_sha256)
    return {
        "spec": spec_dir.name,
        "statuses": statuses,
        "phase": derive_phase(spec_dir, statuses, state["workflowOrder"]),
        "changes": changes,
        "ambiguous": ambiguous,
    }
