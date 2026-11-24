"""Pure plan validation, plan-size policy, and lane routing for workflow.policy.v1.

`InvalidPlan` and `plan_over_ceiling` port OVCAQ `workflow/policy.py`
unchanged; `validate_plan_shape` keeps its DFS cycle check over string ids
and a configurable dependency key. `route` copies the ordered decision table
of the run-autopilot skill's `cli/lane.py` `classify` over already-parsed
fields; `bind` admits a routed lane. Nothing here touches a file or the store.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final

LOOP_TASK_CEILING: Final[int] = 15
LANES = ("solo", "fast-track", "full")

# `cli/lane.py` SECURITY_RE (the review-fanout trigger), copied verbatim.
SECURITY_RE = re.compile(
    r"(?<![a-z0-9])(?:(?:exec|eval|auth|token|password|secret|sql|crypto|hash"
    r"|credential|session|cookie|csrf|xss|jwt|sanitize|injection|privilege)s?"
    r"(?![a-z0-9])|authenticat|authoriz|permission|login|forbidden|acl)",
)
_CAMEL_SPLIT = re.compile(r"([a-z0-9])([A-Z])")


class InvalidPlan(ValueError):
    """Raised when a task snapshot is not a valid dependency plan."""


def plan_over_ceiling(
    state: Mapping[str, object],
    ceiling: int = LOOP_TASK_CEILING,
) -> tuple[bool, int]:
    """Return the characterized tolerant plan-size decision."""
    tasks = state.get("tasks")
    count = len(tasks) if isinstance(tasks, list) else 0
    return count > ceiling, count


def validate_plan_shape(items: object, *, id_key: str = "id",
                        depends_key: str = "depends_on") -> int:
    """Validate item objects, string ids, dependency references, and acyclicity."""
    if not isinstance(items, list):
        raise InvalidPlan("plan must be a list")
    dependencies: dict[str, tuple[str, ...]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise InvalidPlan(f"items[{index}] must be an object")
        item_id = item.get(id_key)
        if not isinstance(item_id, str) or not item_id:
            raise InvalidPlan(f"items[{index}].{id_key} must be a non-empty string")
        if item_id in dependencies:
            raise InvalidPlan(f"duplicate {id_key}: {item_id}")
        depends = item.get(depends_key, [])
        if not isinstance(depends, list) or not all(
                isinstance(dependency, str) and dependency for dependency in depends):
            raise InvalidPlan(f"items[{index}].{depends_key} must be a list of non-empty strings")
        dependencies[item_id] = tuple(depends)

    for item_id, depends in dependencies.items():
        unknown = [dependency for dependency in depends if dependency not in dependencies]
        if unknown:
            raise InvalidPlan(f"{item_id} references unknown {depends_key}: {unknown}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise InvalidPlan(f"dependency cycle includes {item_id}")
        if item_id in visited:
            return
        visiting.add(item_id)
        for dependency in dependencies[item_id]:
            visit(dependency)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in dependencies:
        visit(item_id)
    return len(items)


def _is_hook_path(path: str) -> bool:
    """`cli/lane.py` `is_hook_path`: a `hooks` segment, `hooks.json`, or `*_hook.py`."""
    segments = path.split("/")
    if "hooks" in segments[:-1]:
        return True
    return segments[-1] == "hooks.json" or segments[-1].endswith("_hook.py")


def _securityish(text: str) -> bool:
    return SECURITY_RE.search(_CAMEL_SPLIT.sub(r"\1 \2", text).lower()) is not None


def _paths(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, list) or not all(isinstance(path, str) for path in value):
        return None
    return tuple(value)


def route(prd_frontmatter: dict) -> dict:
    """The `cli/lane.py` `classify` rules, first match wins, failing toward `full`.

    Reads `lane` (override), `design`, `named_paths`, `production_paths`
    (the named paths that are not tests, docs, or packaging) and
    `plan_cards` (the fast-track card count). Malformed or missing evidence
    takes the expensive lane: absent `production_paths` counts every named
    path as production.
    """
    fields = prd_frontmatter if isinstance(prd_frontmatter, dict) else {}
    paths = _paths(fields.get("named_paths")) or ()
    production = _paths(fields.get("production_paths"))
    if production is None:
        production = paths
    cards = fields.get("plan_cards")
    if not isinstance(cards, int) or isinstance(cards, bool):
        cards = 0

    if fields.get("lane") in LANES:
        return {"lane": fields["lane"], "reason": "override"}
    if any(_is_hook_path(path) for path in paths):
        return {"lane": "full", "reason": "hook"}
    if any(_securityish(path) for path in paths):
        return {"lane": "full", "reason": "security_path"}
    if not paths:
        return {"lane": "full", "reason": "unparsed"}
    if fields.get("design") != "skip":
        return {"lane": "full", "reason": "design"}
    if not production:
        return {"lane": "solo", "reason": "no_production_code"}
    if cards > 0:
        return {"lane": "fast-track", "reason": "card_sized"}
    return {"lane": "full", "reason": "uncardable"}


def bind(lane: str, reason: str) -> dict:
    """Admit a routed lane as the `workflow.work` lane fields."""
    from . import protocol

    if not isinstance(lane, str) or lane not in LANES:
        raise protocol.ProtocolError("rejected_evidence")
    return {"lane": lane, "lane_reason": reason}
