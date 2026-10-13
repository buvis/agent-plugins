"""State file, artifact status, task items, and the derived phase."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .canonical import COMPLETION, canonical, indent_of, scan_lines, sha256_canonical
from .schema import check_schema, load_schema

STATE_FILE = ".specflow.json"
SCHEMA_VERSION = 1
ARTIFACTS = ("requirements", "design", "tasks")
ARTIFACT_STATUS = ("missing", "draft", "approved", "stale")
PHASES = (
    "intake",
    "requirements",
    "design",
    "tasks",
    "implementation",
    "verification",
    "complete",
)
ORDERS = {
    "requirements-first": ("requirements", "design"),
    "design-first": ("design", "requirements"),
}
# The invalidation graph: a stale artifact stales every approval downstream of it.
DOWNSTREAM = {
    "requirements-first": {
        "requirements": ("design", "tasks"),
        "design": ("tasks",),
        "tasks": (),
    },
    "design-first": {
        "design": ("requirements", "tasks"),
        "requirements": ("tasks",),
        "tasks": (),
    },
}
SPEC_TYPES = ("feature", "bugfix")
TASK_LINE = re.compile(r"^[ \t]*(?:[-*+]|[0-9]+\.)[ \t]+\[([ xX~-])\](\*?)[ \t]*(.*)$")
TASK_ID = re.compile(r"^(T-[0-9]+(?:\.[0-9]+)*|[0-9]+(?:\.[0-9]+)*)\.?\s+(.*)$")
DEPENDS = re.compile(r"^[ \t]*[-*+][ \t]+Depends on:[ \t]*(.*)$")
FIELD = re.compile(r"^[ \t]*[-*+][ \t]+([A-Z][A-Za-z ]*):")


class StateError(Exception):
    """The state file is malformed or of an unsupported version.

    `reason` names no path, so output that every host must render alike can use it.
    """

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


def load_state(spec_dir: Path) -> dict | None:
    """The state, or None when .specflow.json is absent; StateError when unusable."""
    path = spec_dir / STATE_FILE
    if not path.exists():
        return None
    try:
        data = path.read_bytes()
    except OSError as error:
        raise StateError(path, f"cannot read: {error.strerror}") from error
    try:
        state = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StateError(path, f"not valid JSON: {error}") from error
    if not isinstance(state, dict):
        raise StateError(path, "must contain a JSON object")
    version = state.get("schemaVersion")
    if not isinstance(version, int) or isinstance(version, bool):
        raise StateError(path, "schemaVersion must be an integer")
    if version != SCHEMA_VERSION:
        raise StateError(path, f"unsupported state version {version}")
    errors = check_schema(state, load_schema("specflow-state.schema.json"))
    if errors:
        raise StateError(path, "; ".join(errors))
    return state


def read_config_kiro(spec_dir: Path) -> tuple[str | None, str | None]:
    """(specType, problem) from .config.kiro; both None when the file is absent."""
    path = spec_dir / ".config.kiro"
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, ".config.kiro: unreadable"
    value = data.get("specType") if isinstance(data, dict) else None
    if value not in SPEC_TYPES:
        return None, f".config.kiro: unknown specType {value!r}"
    return value, None


def spec_type(spec_dir: Path, state: dict | None) -> tuple[str, list[str]]:
    """The spec type, and the sources that disagree (ART-001.7); never rewrites a file."""
    kiro, problem = read_config_kiro(spec_dir)
    sources = []
    if kiro:
        sources.append((".config.kiro", kiro))
    if state and state.get("specType") in SPEC_TYPES:
        sources.append((STATE_FILE, state["specType"]))
    if (spec_dir / "bugfix.md").exists():
        sources.append(("files", "bugfix"))
    elif (spec_dir / "requirements.md").exists():
        sources.append(("files", "feature"))
    found = sources[0][1] if sources else "feature"
    disagree = []
    if len({value for _, value in sources}) > 1:
        disagree = [f"{name}: {value}" for name, value in sources]
    return found, [problem, *disagree] if problem else disagree


def artifact_paths(spec_dir: Path, state: dict | None) -> dict[str, Path]:
    """Each canonical artifact's file, from state when present."""
    kind, _ = spec_type(spec_dir, state)
    defaults = {
        "requirements": "bugfix.md" if kind == "bugfix" else "requirements.md",
        "design": "design.md",
        "tasks": "tasks.md",
    }
    records = (state or {}).get("artifacts", {})
    return {
        name: spec_dir / records.get(name, {}).get("path", defaults[name])
        for name in ARTIFACTS
    }


def own_status(path: Path, record: dict) -> str:
    """One artifact's status from its file and its approval record alone."""
    if not path.exists():
        return "missing"
    recorded = record.get("status")
    # A file restored after a recorded deletion needs its approval renewed too.
    if recorded == "stale" or (recorded == "missing" and "approvedSha256" in record):
        return "stale"
    if recorded != "approved" or "approvedSha256" not in record:
        return "draft"
    try:
        current = sha256_canonical(path)
    except UnicodeDecodeError:
        # The approved text was UTF-8, so it changed; required-files reports it.
        return "stale"
    return "approved" if current == record["approvedSha256"] else "stale"


def own_statuses(spec_dir: Path, state: dict | None) -> dict[str, str]:
    paths = artifact_paths(spec_dir, state)
    records = (state or {}).get("artifacts", {})
    return {name: own_status(paths[name], records.get(name, {})) for name in ARTIFACTS}


def order_of(state: dict | None) -> str:
    return (state or {}).get("workflowOrder", "requirements-first")


def workflow_order(spec_dir: Path, state: dict | None) -> str:
    """The state's order, else .config.kiro's workflowType, else requirements-first."""
    if state:
        return order_of(state)
    try:
        data = json.loads((spec_dir / ".config.kiro").read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "requirements-first"
    value = data.get("workflowType") if isinstance(data, dict) else None
    return value if value in ORDERS else "requirements-first"


def spec_phase(spec_dir: Path, state: dict | None) -> tuple[dict[str, str], str]:
    """(artifact statuses, derived phase) of one spec."""
    statuses = artifact_status(spec_dir, state)
    order = workflow_order(spec_dir, state)
    return statuses, derive_phase(spec_dir, statuses, order, state)


def artifact_status(spec_dir: Path, state: dict | None) -> dict[str, str]:
    """Status per artifact. Approval is bound to approvedSha256, never to a file's
    existence, and a stale artifact stales every approval downstream of it."""
    status = own_statuses(spec_dir, state)
    cause = stale_causes(spec_dir, state)
    return {name: "stale" if name in cause else status[name] for name in ARTIFACTS}


def upstream_of(name: str, order: str) -> list[str]:
    """The artifacts whose approval an approval of `name` depends on, most upstream first."""
    graph = DOWNSTREAM[order]
    return [above for above in (*ORDERS[order], "tasks") if name in graph[above]]


def upstream_hashes(spec_dir: Path, state: dict | None, name: str) -> dict[str, str]:
    """Canonical hash of each existing upstream artifact, as an approval of `name` binds it."""
    paths = artifact_paths(spec_dir, state)
    return {
        above: sha256_canonical(paths[above])
        for above in upstream_of(name, workflow_order(spec_dir, state))
        if paths[above].exists()
    }


def unbound(spec_dir: Path, state: dict | None, order: str) -> set[str]:
    """Artifacts recorded approved whose record does not bind every existing upstream
    artifact: no `upstreamSha256`, or one that leaves an upstream out (review 00004-06 F1)."""
    paths = artifact_paths(spec_dir, state)
    records = (state or {}).get("artifacts", {})
    return {
        name
        for name in ARTIFACTS
        if records.get(name, {}).get("status") == "approved"
        and any(
            paths[above].exists()
            and above not in (records[name].get("upstreamSha256") or {})
            for above in upstream_of(name, order)
        )
    }


def rebound(spec_dir: Path, state: dict | None, order: str) -> dict[str, str]:
    """Artifact -> the most upstream artifact no longer matching the hash its approval
    bound in `upstreamSha256`. An upstream the record leaves out is `unbound`, not compared."""
    paths = artifact_paths(spec_dir, state)
    records = (state or {}).get("artifacts", {})
    found = {}
    for name in ARTIFACTS:
        bound = records.get(name, {}).get("upstreamSha256", {})
        for above in upstream_of(name, order):
            if above not in bound or not paths[above].exists():
                continue
            try:
                current = sha256_canonical(paths[above])
            except UnicodeDecodeError:
                current = None
            if current != bound[above]:
                found[name] = above
                break
    return found


def stale_causes_from(status: dict[str, str], order: str) -> dict[str, str]:
    """Walk the graph top-down, so each stale artifact keeps its most upstream cause."""
    graph = DOWNSTREAM[order]
    causes: dict[str, str] = {}
    for name in (*ORDERS[order], "tasks"):
        if status[name] != "stale" or name in causes:
            continue
        causes[name] = name
        for below in graph[name]:
            if status[below] in ("approved", "stale"):
                causes.setdefault(below, name)
    return causes


def stale_causes(spec_dir: Path, state: dict | None) -> dict[str, str]:
    """Stale artifact -> the most upstream artifact whose change caused it. An approval
    whose bound upstream hash no longer matches is stale even after the upstream's
    re-approval, so the order of reconcile and approvals does not matter; one that
    does not bind every existing upstream is stale, with itself as the cause, until
    approved again (STATE-002.4)."""
    order = workflow_order(spec_dir, state)
    status = own_statuses(spec_dir, state)
    moved = {
        name: above
        for name, above in rebound(spec_dir, state, order).items()
        if status[name] == "approved"
    }
    stale = set(moved) | {
        n for n in unbound(spec_dir, state, order) if status[n] == "approved"
    }
    status = {name: "stale" if name in stale else status[name] for name in ARTIFACTS}
    causes = stale_causes_from(status, order)
    rank = (*ORDERS[order], "tasks").index
    for name, above in moved.items():
        if rank(above) < rank(causes[name]):
            causes[name] = above
    return causes


def task_items(text: str) -> list[dict]:
    """Checkbox items of the task list (`scan_lines`), in document order."""
    items: list[dict] = []
    stack: list[dict] = []
    for index, (line, in_fence, in_task) in enumerate(scan_lines(canonical(text))):
        if in_fence:
            continue
        if line.strip():
            while stack and indent_of(line) <= stack[-1]["indent"]:
                stack.pop()
        if not in_task:
            continue
        match = TASK_LINE.match(line)
        if match:
            ident = TASK_ID.match(match[3])
            item = {
                "line": index + 1,
                "indent": indent_of(line),
                "checked": match[1] in "xX",
                "optional": match[2] == "*",
                "parent": stack[-1]["index"] if stack else None,
                "index": len(items),
                "id": ident[1] if ident else None,
                "title": (ident[2] if ident else match[3]).strip(),
                "depends": None,
                "fields": [],
            }
            items.append(item)
            stack.append(item)
        elif stack and (field := FIELD.match(line)):
            stack[-1]["fields"].append(field[1])
            if dep := DEPENDS.match(line):
                value = dep[1].strip()
                parts = [part.strip() for part in value.split(",") if part.strip()]
                stack[-1]["depends"] = [] if value.lower() == "none" else parts
    return items


def completion_boxes(text: str) -> list[bool] | None:
    """Checked state of each box under `## Completion criteria`; None without the section."""
    boxes: list[bool] | None = None
    for line, in_fence, _ in scan_lines(canonical(text)):
        if in_fence:
            continue
        if line == COMPLETION:
            boxes = []
        elif boxes is not None and line.startswith("## "):
            break
        elif boxes is not None and (match := TASK_LINE.match(line)):
            boxes.append(match[1] in "xX")
    return boxes


def required_open(items: list[dict]) -> list[dict]:
    """Unchecked items that are not marked optional."""
    return [item for item in items if not item["checked"] and not item["optional"]]


def derive_phase(
    spec_dir: Path,
    status: dict[str, str],
    order: str,
    state: dict | None,
) -> str:
    """The first row of the phase table that matches, read in workflow order."""
    for name in (*ORDERS[order], "tasks"):
        if status[name] != "approved":
            return name
    text = (spec_dir / "tasks.md").read_bytes().decode("utf-8")
    items = task_items(text)
    open_items = required_open(items)
    boxes = completion_boxes(text)
    if boxes is None and spec_type(spec_dir, state)[0] == "bugfix":
        top = [item for item in items if item["parent"] is None]
        if top and open_items == [top[-1]]:
            return "verification"
    if open_items or not items:  # a plan with no task is not complete
        return "implementation"
    if boxes and not all(boxes):
        return "verification"
    return "complete"
