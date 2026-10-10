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
TASK_LINE = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]+\[([ xX~-])\](\*?)[ \t]*(.*)$")
TASK_ID = re.compile(r"^(T-\d+(?:\.\d+)*|\d+(?:\.\d+)*)\.?\s+(.*)$")
DEPENDS = re.compile(r"^[ \t]*[-*+][ \t]+Depends on:[ \t]*(.*)$")


class StateError(Exception):
    """The state file is malformed or of an unsupported version."""


def load_state(spec_dir: Path) -> dict | None:
    """The state, or None when .specflow.json is absent; StateError when unusable."""
    path = spec_dir / STATE_FILE
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StateError(f"{path}: not valid JSON: {error}") from error
    if not isinstance(state, dict):
        raise StateError(f"{path}: must contain a JSON object")
    version = state.get("schemaVersion")
    if not isinstance(version, int) or isinstance(version, bool):
        raise StateError(f"{path}: schemaVersion must be an integer")
    if version != SCHEMA_VERSION:
        raise StateError(f"{path}: unsupported state version {version}")
    errors = check_schema(state, load_schema("specflow-state.schema.json"))
    if errors:
        raise StateError(f"{path}: " + "; ".join(errors))
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
    if record.get("status") == "stale":
        return "stale"
    if record.get("status") != "approved" or "approvedSha256" not in record:
        return "draft"
    return "approved" if sha256_canonical(path) == record["approvedSha256"] else "stale"


def own_statuses(spec_dir: Path, state: dict | None) -> dict[str, str]:
    paths = artifact_paths(spec_dir, state)
    records = (state or {}).get("artifacts", {})
    return {name: own_status(paths[name], records.get(name, {})) for name in ARTIFACTS}


def order_of(state: dict | None) -> str:
    return (state or {}).get("workflowOrder", "requirements-first")


def artifact_status(spec_dir: Path, state: dict | None) -> dict[str, str]:
    """Status per artifact. Approval is bound to approvedSha256, never to a file's
    existence, and a stale artifact stales every approval downstream of it."""
    status = own_statuses(spec_dir, state)
    cause = stale_causes_from(status, order_of(state))
    return {name: "stale" if name in cause else status[name] for name in ARTIFACTS}


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
    """Stale artifact -> the most upstream artifact whose change caused it."""
    return stale_causes_from(own_statuses(spec_dir, state), order_of(state))


def task_items(text: str) -> list[dict]:
    """Checkbox items above `## Completion criteria`, in document order."""
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
            }
            items.append(item)
            stack.append(item)
        elif stack and (dep := DEPENDS.match(line)):
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


def derive_phase(spec_dir: Path, status: dict[str, str], order: str) -> str:
    """The first row of the phase table that matches, read in workflow order."""
    for name in (*ORDERS[order], "tasks"):
        if status[name] != "approved":
            return name
    text = (spec_dir / "tasks.md").read_bytes().decode("utf-8")
    items = task_items(text)
    open_items = required_open(items)
    boxes = completion_boxes(text)
    if boxes is None and spec_type(spec_dir, None)[0] == "bugfix":
        top = [item for item in items if item["parent"] is None]
        if top and open_items == [top[-1]]:
            return "verification"
    if open_items:
        return "implementation"
    if boxes and not all(boxes):
        return "verification"
    return "complete"
