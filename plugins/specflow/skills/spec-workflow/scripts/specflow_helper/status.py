"""Read-only status for external runners, computed from the repository files alone."""

from __future__ import annotations

import re
from pathlib import Path

from .canonical import canonical, scan_lines
from .checks import CHECKS, Context, validate, workspace_config
from .deps import dependency_blockers
from .drift import code_drift, warning
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
LIST_ITEM = re.compile(r"^(?:[-*+]|\d+\.)\s")
REPOSITORY_CHECKS = ("specs-folder", "number-clashes")
NOT_PER_SPEC = ("gates", "spec-dependencies", *REPOSITORY_CHECKS)


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
            if not paths[name].exists():
                continue
            text = paths[name].read_bytes().decode("utf-8")
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


def drift_warnings(
    repo: Path,
    state: dict | None,
    statuses: dict[str, str],
) -> list[dict]:
    """Code drift since the design approval; omitted outside Git."""
    if not (repo / ".git").exists() or statuses["design"] not in ("approved", "stale"):
        return []
    if statuses["design"] == "stale":
        message = "the design approval is stale; code is checked again after reapproval"
        return [warning("not-checked", message)]
    return code_drift(repo, (state or {})["artifacts"]["design"].get("approvedCode"))


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
    blockers: list[dict] = []
    if kind == "missing":
        blockers.append({"gate": second, "reason": "state missing"})
    if problem is not None:
        blockers.append({"gate": second, "reason": f"state invalid: {problem}"})
    blockers += artifact_blockers(order, statuses, paths)
    blockers += marker_blockers(order, state, paths)
    blockers += dependency_blockers(spec_dir, specs_dir)
    blockers += [
        {
            "gate": "implementation",
            "reason": f"validation failed: {f['rule']}: {f['message']}",
            "reference": f["file"],
        }
        for f in validate(repo, spec_dir)
        if f["level"] == "error" and f["rule"] not in NOT_PER_SPEC
    ]
    gate_names = (second, "tasks", "implementation")
    gates = {
        g: "closed" if any(b["gate"] == g for b in blockers) else "open"
        for g in gate_names
    }
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
