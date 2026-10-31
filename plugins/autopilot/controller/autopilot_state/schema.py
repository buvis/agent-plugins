"""Closed controller state schema and bounded JSON decoding."""

from __future__ import annotations

import copy
import json
import math
import re
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
        raise SchemaError("Response result has missing or unknown fields")
    _identity(value["actor_id"])
    _counter(value["lease_epoch"])


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

    workflow = _object(state["workflow"], set(_WORKFLOW))
    review = _object(workflow["review"], {"cap"})
    _counter(review["cap"])
    if workflow != _WORKFLOW:
        raise SchemaError("Workflow reserves must retain their initial values")

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
