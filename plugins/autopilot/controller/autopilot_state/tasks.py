"""Pure reducers for task.replace, task.start, task.finish, and task.attempt.

Each reducer takes the current `workflow.tasks` list and returns a new one;
the input is never mutated. Nothing here touches a file or the store: the
dispatcher wraps these in its transaction and receipt cache. `replace`
raises `policy.InvalidPlan` for the caller to translate; the other reducers
raise `protocol.ProtocolError("rejected_evidence")`.
"""

from __future__ import annotations

import copy

from . import policy

STATUSES = ("pending", "in_progress", "completed", "aborted")
FINISH_OUTCOMES = ("completed", "aborted")
ATTEMPT_OUTCOMES = ("completed", "aborted", "stalled")
_PAYLOAD_KEYS = {"id", "subject", "status", "depends_on"}


def _is_identity(value: object) -> bool:
    return isinstance(value, str) and 1 <= len(value.encode("utf-8")) <= 256


def _rejected() -> Exception:
    from . import protocol

    return protocol.ProtocolError("rejected_evidence")


def _check_record(index: int, item: dict) -> None:
    if set(item) != _PAYLOAD_KEYS:
        raise policy.InvalidPlan(f"tasks[{index}] must have exactly {sorted(_PAYLOAD_KEYS)}")
    if not _is_identity(item["id"]):
        raise policy.InvalidPlan(f"tasks[{index}].id must contain 1 to 256 UTF-8 bytes")
    if not isinstance(item["subject"], str) or not item["subject"]:
        raise policy.InvalidPlan(f"tasks[{index}].subject must be a non-empty string")
    if item["status"] not in STATUSES:
        raise policy.InvalidPlan(f"tasks[{index}].status must be one of {STATUSES}")
    if not all(_is_identity(dependency) for dependency in item["depends_on"]):
        raise policy.InvalidPlan(f"tasks[{index}].depends_on entries must be 1 to 256 UTF-8 bytes")


def replace(tasks: list[dict], *, allow_expansion: bool = False) -> list[dict]:
    """Validate a full task plan and return it as the new `workflow.tasks`."""
    policy.validate_plan_shape(tasks, id_key="id", depends_key="depends_on")
    over, count = policy.plan_over_ceiling({"tasks": tasks}, ceiling=policy.LOOP_TASK_CEILING)
    if over and not allow_expansion:
        raise policy.InvalidPlan(
            f"plan has {count} tasks, over the {policy.LOOP_TASK_CEILING}-task ceiling")
    for index, item in enumerate(tasks):
        _check_record(index, item)
    return [{**copy.deepcopy(item), "attempts": []} for item in tasks]


def _find(tasks: list[dict], task_id: object) -> int:
    for index, item in enumerate(tasks):
        if item["id"] == task_id:
            return index
    raise _rejected()


def _with_task(tasks: list[dict], index: int, **changes: object) -> list[dict]:
    result = copy.deepcopy(tasks)
    result[index] = {**result[index], **copy.deepcopy(changes)}
    return result


def start(tasks: list[dict], task_id: str, lease_epoch: int | None = None) -> list[dict]:
    """Move a pending task whose dependencies all completed to `in_progress`."""
    index = _find(tasks, task_id)
    target = tasks[index]
    if target["status"] != "pending":
        raise _rejected()
    completed = {item["id"] for item in tasks if item["status"] == "completed"}
    if any(dependency not in completed for dependency in target["depends_on"]):
        raise _rejected()
    changes = {"status": "in_progress"}
    if lease_epoch is not None:
        changes["start_epoch"] = lease_epoch
    return _with_task(tasks, index, **changes)


def finish(tasks: list[dict], task_id: str, outcome: str,
          lease_epoch: int | None = None) -> list[dict]:
    """Close a started task as `completed` or `aborted`.

    A task started under an earlier lease epoch than the one finishing it is
    rejected: durable start evidence must stay scoped to its own lease epoch.
    """
    if outcome not in FINISH_OUTCOMES:
        raise _rejected()
    index = _find(tasks, task_id)
    target = tasks[index]
    if target["status"] != "in_progress":
        raise _rejected()
    started_epoch = target.get("start_epoch")
    if (lease_epoch is not None and started_epoch is not None
            and started_epoch != lease_epoch):
        raise _rejected()
    return _with_task(tasks, index, status=outcome)


def attempt(tasks: list[dict], task_id: str, implementor: str, outcome: str) -> list[dict]:
    """Append one attempt record to a task; the task status never changes."""
    if outcome not in ATTEMPT_OUTCOMES or not _is_identity(implementor):
        raise _rejected()
    index = _find(tasks, task_id)
    attempts = [*tasks[index]["attempts"], {"implementor": implementor, "outcome": outcome}]
    return _with_task(tasks, index, attempts=attempts)
