"""Closed controller state schema and bounded JSON decoding."""

from __future__ import annotations

import copy
import json
import math
import re
from collections.abc import Callable
from pathlib import Path

SCHEMA_VERSION = 1
MAX_STATE_BYTES = 16777216
MAX_COMMAND_PAYLOAD_BYTES = 2097152
MAX_STRING_BYTES = 1048576
MAX_JSON_DEPTH = 32
MAX_JSON_INTEGER_DIGITS = 640

_WORKFLOW = {
    "batch": None,
    "work": None,
    "tasks": [],
    "review": {"cap": 2},
    "recovery": None,
    "jobs": [],
}


class SchemaError(ValueError):
    """The value does not satisfy the controller schema."""


class ResourceLimitError(SchemaError):
    """The value exceeds a published resource limit."""


def _string_size(value: str) -> int:
    try:
        return len(value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise SchemaError("Strings must contain valid UTF-8") from error


def _check_json(value: object, depth: int = 0) -> None:
    if isinstance(value, str):
        if _string_size(value) > MAX_STRING_BYTES:
            raise ResourceLimitError("JSON string exceeds the byte limit")
    elif value is None or isinstance(value, bool):
        return
    elif isinstance(value, int):
        if abs(value) >= 10**MAX_JSON_INTEGER_DIGITS:
            raise ResourceLimitError("JSON integer exceeds the digit limit")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaError("JSON numbers must be finite")
    elif isinstance(value, (dict, list)):
        if depth >= MAX_JSON_DEPTH:
            raise ResourceLimitError("JSON exceeds the nesting limit")
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise SchemaError("JSON object keys must be strings")
                _check_json(key, depth + 1)
                _check_json(item, depth + 1)
        else:
            for item in value:
                _check_json(item, depth + 1)
    else:
        raise SchemaError("Value is not JSON data")


def _encoded_size(value: object) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8"))


def decode_json(text: str, *, source: str) -> object:
    """Decode a complete JSON document without duplicate keys or excess resources."""
    if not isinstance(text, str):
        raise SchemaError(f"{source}: expected JSON text")
    if _string_size(text) > MAX_STATE_BYTES:
        raise ResourceLimitError(f"{source}: JSON document exceeds the byte limit")

    def object_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise SchemaError(f"{source}: duplicate object key")
            result[key] = value
        return result

    def parse_integer(value: str) -> int:
        if len(value.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
            raise ResourceLimitError(f"{source}: JSON integer exceeds the digit limit")
        return int(value)

    def reject_constant(value: str) -> object:
        raise SchemaError(f"{source}: invalid JSON number {value}")

    try:
        value = json.loads(text, object_pairs_hook=object_pairs,
                           parse_int=parse_integer, parse_constant=reject_constant)
    except (json.JSONDecodeError, RecursionError) as error:
        raise SchemaError(f"{source}: invalid JSON document") from error
    _check_json(value)
    return value


def _object(value: object, fields: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise SchemaError("Object has missing or unknown fields")
    return value


def _counter(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SchemaError("Counter must be a nonnegative integer")


def _identity(value: object) -> None:
    if not isinstance(value, str) or not 1 <= _string_size(value) <= 256:
        raise SchemaError("Identity must contain 1 to 256 UTF-8 bytes")


def _digest(value: object) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise SchemaError("Digest must contain 64 lowercase hexadecimal characters")


def _absolute_path(value: object) -> None:
    if not isinstance(value, str) or not value.startswith("/"):
        raise SchemaError("Path must be absolute")


def _actor(value: object) -> dict:
    descriptor = _object(value, {
        "actor_id", "project_id", "workflow_id", "role", "lease_epoch",
        "native_session_id", "secret_digest",
    })
    _identity(descriptor["actor_id"])
    _digest(descriptor["project_id"])
    _identity(descriptor["workflow_id"])
    _counter(descriptor["lease_epoch"])
    _digest(descriptor["secret_digest"])
    if descriptor["role"] == "operator":
        if descriptor["native_session_id"] is not None:
            raise SchemaError("Operator cannot have a native session")
    elif descriptor["role"] == "owner":
        _identity(descriptor["native_session_id"])
    else:
        raise SchemaError("Unknown actor role")
    return descriptor


def _owner(value: object) -> None:
    if value is None:
        return
    owner = _object(value, {
        "actor_id", "mode", "native_session_id", "lease_epoch",
    })
    _identity(owner["actor_id"])
    _identity(owner["native_session_id"])
    _counter(owner["lease_epoch"])
    if owner["mode"] not in ("manual", "supervised"):
        raise SchemaError("Unknown owner mode")


def _actors(state: dict) -> None:
    actors = state["actors"]
    if not isinstance(actors, dict) or len(actors) > 2:
        raise SchemaError("Actor registry exceeds its limit")
    roles = {}
    for actor_id, value in actors.items():
        _identity(actor_id)
        descriptor = _actor(value)
        if descriptor["actor_id"] != actor_id:
            raise SchemaError("Actor identifier does not match registry key")
        for key in ("project_id", "workflow_id", "lease_epoch"):
            if descriptor[key] != state[key]:
                raise SchemaError("Active actor has an inconsistent binding")
        role = descriptor["role"]
        if role in roles:
            raise SchemaError("Actor registry contains duplicate roles")
        roles[role] = descriptor
    owner = state["owner"]
    if owner is None:
        if "owner" in roles:
            raise SchemaError("Owner actor requires an active owner")
    else:
        descriptor = roles.get("owner")
        if descriptor is None or "operator" not in roles:
            raise SchemaError("Active owner requires owner and operator actors")
        for key in ("actor_id", "native_session_id", "lease_epoch"):
            if owner[key] != descriptor[key]:
                raise SchemaError("Owner does not match its active actor")


def _result(value: object) -> None:
    fields = set(value)
    if fields == {"workflow_id", "actor_id", "actor_file", "lease_epoch"}:
        _identity(value["workflow_id"])
        _absolute_path(value["actor_file"])
    elif fields == {"actor_id", "actor_file", "lease_epoch", "operator_actor_file"}:
        _absolute_path(value["actor_file"])
        _absolute_path(value["operator_actor_file"])
    elif fields == {"actor_id", "operator_actor_file", "lease_epoch"}:
        _absolute_path(value["operator_actor_file"])
    else:
        _workflow_result(value, fields)
        return
    _identity(value["actor_id"])
    _counter(value["lease_epoch"])


def _lane(value: object) -> None:
    if value not in ("solo", "fast-track", "full"):
        raise SchemaError("Unknown lane")


def _workflow_result(value: dict, fields: set) -> None:
    """Result shapes of the lifecycle, tasks, policy and jobs operations."""
    if fields == {"prd", "source"}:
        _text(value["prd"])
        if value["source"] not in ("wip", "backlog"):
            raise SchemaError("Unknown work source")
    elif fields == {"phase", "next_phase"}:
        _text(value["phase"])
        if not isinstance(value["next_phase"], str):
            raise SchemaError("Next phase must be a string")
    elif fields == {"prd"}:
        _text(value["prd"])
    elif fields == {"operation_id", "kind", "replayed", "systemic_halt"}:
        _identity(value["operation_id"])
        if value["kind"] not in ("stall", "park", "defer"):
            raise SchemaError("Unknown saga kind")
        if not isinstance(value["replayed"], bool) or not isinstance(value["systemic_halt"], bool):
            raise SchemaError("Saga flags must be booleans")
    elif fields in ({"task_count"}, {"job_count"}):
        _counter(value[next(iter(fields))])
    elif fields == {"task_id", "status", "attempts"}:
        _identity(value["task_id"])
        if value["status"] not in ("pending", "in_progress", "completed", "aborted"):
            raise SchemaError("Unknown task status")
        _counter(value["attempts"])
    elif fields == {"lane", "reason"}:
        _lane(value["lane"])
        _text(value["reason"])
    elif fields == {"lane", "lane_reason"}:
        _lane(value["lane"])
        _text(value["lane_reason"])
    elif fields == {"job_id", "claimed_by", "claim_epoch"}:
        _identity(value["job_id"])
        _identity(value["claimed_by"])
        _counter(value["claim_epoch"])
    elif fields == JOB_SPEC_KEYS | {"instruction"}:
        _text(value["instruction"])
        _job_spec({key: item for key, item in value.items() if key != "instruction"},
                  required=JOB_SPEC_KEYS)
    elif fields == {"job_id", "instruction"}:
        _identity(value["job_id"])
        _text(value["instruction"])
    else:
        raise SchemaError("Response result has missing or unknown fields")


def _receipts(receipts: object) -> None:
    if not isinstance(receipts, dict) or len(receipts) > 4096:
        raise SchemaError("Receipt registry exceeds its limit")
    for request_id, value in receipts.items():
        _identity(request_id)
        receipt = _object(value, {"request_digest", "authorizing_actor", "response"})
        _digest(receipt["request_digest"])
        _actor(receipt["authorizing_actor"])
        response = _object(receipt["response"], {
            "ok", "revision", "result", "error_code", "retryable",
        })
        _counter(response["revision"])
        if (response["ok"] is not True or response["retryable"] is not False
                or response["error_code"] is not None
                or not isinstance(response["result"], dict)):
            raise SchemaError("Receipt must retain a complete success response")
        _result(response["result"])
        if _encoded_size(response) > 65536:
            raise ResourceLimitError("Receipt response exceeds the byte limit")


def _text(value: object) -> None:
    if not isinstance(value, str) or not value:
        raise SchemaError("Text must be a non-empty string")


def _list(value: object, check: Callable[[object], None]) -> None:
    if not isinstance(value, list):
        raise SchemaError("Expected a list")
    for item in value:
        check(item)


_TASK_ALLOWED = {"id", "subject", "status", "depends_on", "attempts", "start_epoch"}
_TASK_REQUIRED = _TASK_ALLOWED - {"start_epoch"}


def _task(value: object) -> None:
    if (not isinstance(value, dict) or not _TASK_REQUIRED <= set(value)
            or not set(value) <= _TASK_ALLOWED):
        raise SchemaError("Object has missing or unknown fields")
    task = value
    _identity(task["id"])
    _text(task["subject"])
    if task["status"] not in ("pending", "in_progress", "completed", "aborted"):
        raise SchemaError("Unknown task status")
    _list(task["depends_on"], _identity)
    if not isinstance(task["attempts"], list):
        raise SchemaError("Task attempts must be a list")
    if "start_epoch" in task:
        _counter(task["start_epoch"])


JOB_SPEC_KEYS = {"job_id", "role", "depends_on", "input_digests", "isolation", "tier",
                 "effort", "source_digest", "resource_digest", "permitted_operations"}
# A job row stored before the metadata keys existed still validates; a present
# value is always validated, and protocol.py requires all of them from a caller.
_JOB_SPEC_REQUIRED = JOB_SPEC_KEYS - {"source_digest", "resource_digest",
                                      "permitted_operations"}


def _job_spec(value: object, *, required: set[str]) -> None:
    if (not isinstance(value, dict) or not required <= set(value)
            or not set(value) <= JOB_SPEC_KEYS):
        raise SchemaError("Object has missing or unknown fields")
    spec = value
    _identity(spec["job_id"])
    _list(spec["depends_on"], _identity)
    _list(spec["input_digests"], _digest)
    for key in ("role", "isolation", "tier", "effort"):
        _text(spec[key])
    for key in ("source_digest", "resource_digest"):
        if key in spec:
            _digest(spec[key])
    if "permitted_operations" in spec:
        _list(spec["permitted_operations"], _text)
        if not spec["permitted_operations"]:
            raise SchemaError("Job spec must declare at least one permitted operation")


def _job(value: object) -> None:
    job = _object(value, {"spec", "claimed_by", "claim_epoch", "exit_fact"})
    _job_spec(job["spec"], required=_JOB_SPEC_REQUIRED)
    if job["claimed_by"] is not None:
        _identity(job["claimed_by"])
    if job["claim_epoch"] is not None:
        _counter(job["claim_epoch"])
    if job["exit_fact"] is not None and not isinstance(job["exit_fact"], dict):
        raise SchemaError("Job exit fact must be null or an object")


_WORKFLOW_ALLOWED = set(_WORKFLOW) | {"pause"}
_WORK_ALLOWED = {"prd", "source", "entered_at", "phase", "completed_phases", "lane",
                 "lane_reason", "rework_cap", "start_commit", "task_tier",
                 "plan_expansion"}
# The entry metadata keys are optional: a work record written before they
# existed still validates, and a present value is always validated.
_WORK_REQUIRED = _WORK_ALLOWED - {"rework_cap", "start_commit", "task_tier",
                                  "plan_expansion"}


def _workflow(value: object) -> None:
    if (not isinstance(value, dict) or not set(_WORKFLOW) <= set(value)
            or not set(value) <= _WORKFLOW_ALLOWED):
        raise SchemaError("Object has missing or unknown fields")
    workflow = value
    review = _object(workflow["review"], {"cap"})
    _counter(review["cap"])
    if review != _WORKFLOW["review"]:
        raise SchemaError("Workflow review must retain its frozen cap")
    if workflow["batch"] is not None:
        batch = _object(workflow["batch"], {"completed_prds", "parks_consecutive"})
        _list(batch["completed_prds"], _text)
        _counter(batch["parks_consecutive"])
    if workflow["work"] is not None:
        work = workflow["work"]
        if (not isinstance(work, dict) or not _WORK_REQUIRED <= set(work)
                or not set(work) <= _WORK_ALLOWED):
            raise SchemaError("Object has missing or unknown fields")
        for key in ("prd", "entered_at", "phase"):
            _text(work[key])
        if work["source"] not in ("wip", "backlog"):
            raise SchemaError("Unknown work source")
        _list(work["completed_phases"], _text)
        for key in ("lane", "lane_reason"):
            if work[key] is not None:
                _text(work[key])
        if "rework_cap" in work:
            _counter(work["rework_cap"])
        commit = work.get("start_commit")
        if commit is not None and (not isinstance(commit, str)
                                   or re.fullmatch(r"[0-9a-f]{40}", commit) is None):
            raise SchemaError("Start commit must contain 40 lowercase hexadecimal characters")
        for key in ("task_tier", "plan_expansion"):
            if work.get(key) is not None:
                _text(work[key])
    if workflow["recovery"] is not None:
        recovery = _object(workflow["recovery"], {"op", "boundary"})
        _text(recovery["op"])
        _text(recovery["boundary"])
    if workflow.get("pause") is not None:
        pause = _object(workflow["pause"], {"site", "detail"})
        _text(pause["site"])
        _text(pause["detail"])
    _list(workflow["tasks"], _task)
    _list(workflow["jobs"], _job)


def validate_state(value: object) -> dict:
    """Validate state before returning an independent, mutable copy."""
    _check_json(value)
    state = _object(value, {
        "schema_version", "revision", "project_id", "workflow_id", "repo_root",
        "lease_epoch", "owner", "actors", "receipts", "workflow",
    })
    _counter(state["schema_version"])
    if state["schema_version"] != SCHEMA_VERSION:
        raise SchemaError("Unsupported schema version")
    _counter(state["revision"])
    _counter(state["lease_epoch"])
    _digest(state["project_id"])
    _identity(state["workflow_id"])
    _absolute_path(state["repo_root"])

    _workflow(state["workflow"])
    _owner(state["owner"])
    _actors(state)
    _receipts(state["receipts"])
    serialized = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if len(serialized.encode("utf-8")) > MAX_STATE_BYTES:
        raise ResourceLimitError("State exceeds the byte limit")
    return copy.deepcopy(state)


def new_state(*, repo_root: Path, project_id: str, workflow_id: str) -> dict:
    """Create a state with fresh workflow reserves from explicit project inputs."""
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "project_id": project_id,
        "workflow_id": workflow_id,
        "repo_root": str(repo_root),
        "lease_epoch": 0,
        "owner": None,
        "actors": {},
        "receipts": {},
        "workflow": copy.deepcopy(_WORKFLOW),
    }
