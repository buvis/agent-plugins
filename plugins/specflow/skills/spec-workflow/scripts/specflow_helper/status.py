"""Read-only status for external runners, computed from the repository files alone."""

from __future__ import annotations

import re
from pathlib import Path

from .canonical import canonical, scan_lines
from .checks import CHECKS, Context, read_text, validate, workspace_config
from .deps import dependency_blockers
from .drift import drift_warnings
from .numbers import numbered_items, spec_folders
from .state import (
    ORDERS,
    StateError,
    artifact_paths,
    artifact_status,
    derive_phase,
    load_state,
    spec_type,
    task_items,
    workflow_order,
)

STATUS_VERSION = 1
MARKER_SECTIONS = ("## Unresolved questions", "## Open decisions")
LIST_ITEM = re.compile(r"^(?:[-*+]|[0-9]+\.)\s")
REPOSITORY_CHECKS = ("specs-folder", "number-clashes")
# Covered by the artifact and dependency blockers, or reported once under problems.
NOT_PER_SPEC = frozenset(
    {"gates", "spec-dependencies", "stale-approvals", *REPOSITORY_CHECKS},
)


def markers(text: str) -> list[str]:
    """Open marker lines: any `(guess)` outside code, and list items under the marker sections."""
    found: list[str] = []
    section = ""
    for line, in_fence, _ in scan_lines(canonical(text)):
        if in_fence:
            continue
        if line.startswith("## "):
            section = line.strip()
            continue
        if (
            section in MARKER_SECTIONS and LIST_ITEM.match(line)
        ) or "(guess)" in re.sub(r"`[^`]*`", "", line):
            found.append(line)
    return found


def gate_after(order: str, artifact: str) -> str:
    """The gate an artifact's approval opens."""
    chain = (*ORDERS[order], "tasks", "implementation")
    return chain[chain.index(artifact) + 1]


def artifact_blockers(
    order: str,
    statuses: dict[str, str],
    paths: dict[str, Path],
) -> list[dict]:
    first, second = ORDERS[order]
    upstream = {
        second: (first,),
        "tasks": (first, second),
        "implementation": (first, second, "tasks"),
    }
    return [
        {
            "gate": gate,
            "reason": f"{name} is {statuses[name]}",
            "reference": paths[name].name,
        }
        for gate, names in upstream.items()
        for name in names
        if statuses[name] != "approved"
    ]


def marker_blockers(
    order: str,
    state: dict | None,
    paths: dict[str, Path],
) -> list[dict]:
    """Upstream markers not accepted by name on the dependent approval (WF-002.7)."""
    first, second = ORDERS[order]
    blockers = []
    for dependent, upstream in ((second, (first,)), ("tasks", (first, second))):
        record = (state or {}).get("artifacts", {}).get(dependent, {})
        accepted = {
            (a["artifact"], a["line"]) for a in record.get("acceptedMarkers", [])
        }
        for name in upstream:
            text = read_text(paths[name])
            if text is None:  # required-files reports it
                continue
            blockers += [
                {
                    "gate": gate_after(order, dependent),
                    "reason": f"{name} marker not accepted for the {dependent} approval",
                    "reference": line,
                }
                for line in markers(text)
                if (name, line) not in accepted
            ]
    return blockers


def next_task(tasks_path: Path) -> dict | None:
    """The first unchecked required task whose Depends on: tasks are checked.

    A task with an unchecked required sub-task is not itself next.
    """
    items = task_items(tasks_path.read_bytes().decode("utf-8"))
    checked = {item["id"] for item in items if item["checked"] and item["id"]}
    for item in items:
        if item["checked"] or item["optional"]:
            continue
        children = [c for c in items if c["parent"] == item["index"]]
        if any(not c["checked"] and not c["optional"] for c in children):
            continue
        if all(d in checked for d in item["depends"] or []):
            return {"id": item["id"], "title": item["title"]}
    return None


def repo_reference(repo: Path, path: Path) -> str:
    """The path relative to the repository, never through a link that leads out of it."""
    for base, target in (
        (repo, path),
        (repo.resolve(), path.parent.resolve() / path.name),
    ):
        if target.is_relative_to(base):
            return target.relative_to(base).as_posix()
    return path.name


def state_blockers(
    repo: Path,
    gate: str,
    kind: str,
    problem: StateError | None,
) -> list[dict]:
    """The blocker a missing or invalid state file puts on the second gate."""
    if kind == "missing":
        return [{"gate": gate, "reason": "state missing"}]
    if problem is None:
        return []
    return [
        {
            "gate": gate,
            "reason": f"state invalid: {problem.reason}",
            "reference": repo_reference(repo, problem.path),
        },
    ]


def spec_status(repo: Path, specs_dir: Path, spec_dir: Path) -> dict:
    """One entry of `specs`."""
    try:
        state = load_state(spec_dir)
        kind, problem = ("valid" if state else "missing"), None
    except StateError as error:
        state, kind, problem = None, "invalid", error
    order = workflow_order(spec_dir, state)
    statuses = artifact_status(spec_dir, state)
    paths = artifact_paths(spec_dir, state)
    second = ORDERS[order][1]
    blockers = state_blockers(repo, second, kind, problem)
    blockers += artifact_blockers(order, statuses, paths)
    blockers += marker_blockers(order, state, paths)
    blockers += dependency_blockers(spec_dir, specs_dir)
    blockers += [
        {
            "gate": "implementation",
            "reason": f"validation failed: {f['rule']}: {f['message']}",
            "reference": f["file"],
        }
        for f in validate(repo, spec_dir, skip=NOT_PER_SPEC)
        if f["level"] == "error"
    ]
    # A closed gate closes every later gate too, whatever blocker closed it.
    gates: dict[str, str] = {}
    closed = False
    for g in (second, "tasks", "implementation"):
        closed = closed or any(b["gate"] == g for b in blockers)
        gates[g] = "closed" if closed else "open"
    hold = (state or {}).get("hold")
    ready = gates["implementation"] == "open" and not hold
    return {
        "spec": spec_dir.name,
        "specType": spec_type(spec_dir, state)[0],
        "profile": (state or {}).get("profile"),
        "phase": derive_phase(spec_dir, statuses, order),
        "state": kind,
        "hold": hold,
        "artifacts": statuses,
        "stale": [n for n in (*ORDERS[order], "tasks") if statuses[n] == "stale"],
        "gates": gates,
        "blockers": blockers,
        "warnings": drift_warnings(repo, state, statuses),
        "nextTask": next_task(paths["tasks"]) if ready else None,
    }


def intake_items(repo: Path, config: dict[str, object]) -> list[str]:
    """Items under <root>/intake/new/ whose number has no spec folder."""
    taken = {p.name[:5] for p in spec_folders(repo, config)}
    return [
        p.name
        for p in numbered_items(repo, config, ("new",))
        if p.name[:5] not in taken
    ]


def status(repo: Path, spec_dirs: list[Path]) -> dict:
    """The document of the status schema; read-only, with no way to record an approval."""
    config = workspace_config(repo)
    specs_dir = repo / str(config["specsDir"])
    if not spec_dirs and specs_dir.is_dir():
        spec_dirs = sorted(p for p in specs_dir.iterdir() if p.is_dir())
    context = Context(repo, config, specs_dir, None)
    problems = [
        {"rule": f["rule"], "message": f["message"], "fix": f["fix"]}
        for name in REPOSITORY_CHECKS
        if name in CHECKS
        for f in CHECKS[name][1](context)
    ]
    return {
        "statusVersion": STATUS_VERSION,
        "specs": [spec_status(repo, specs_dir, d) for d in spec_dirs],
        "problems": problems,
        "intake": intake_items(repo, config),
    }
