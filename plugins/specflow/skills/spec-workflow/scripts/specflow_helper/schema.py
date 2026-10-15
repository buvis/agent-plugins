"""The part of JSON Schema draft 2020-12 the shipped schemas use, and the state content scan."""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"

ANNOTATIONS = frozenset({"$schema", "$id", "title", "description", "$defs"})
KEYWORDS = frozenset(
    {
        "type",
        "const",
        "enum",
        "required",
        "properties",
        "additionalProperties",
        "items",
        "pattern",
        "minLength",
        "oneOf",
        "$ref",
    },
)
BANNED_KEYS = frozenset(
    k.lower()
    for k in (
        "transcript",
        "prompt",
        "messages",
        "conversation",
        "sessionId",
        "session_id",
        "token",
        "secret",
        "password",
        "credential",
        "apiKey",
    )
)
ABSOLUTE = re.compile(r"^(?:/|~|[A-Za-z]:[\\/])")
FREE_TEXT = re.compile(
    r"^\$\.(?:artifacts\.\w+\.acceptedMarkers\[\d+\]\.line"
    r"|hold\.reason"
    r"|artifacts\.\w+\.approvedCode\.reason)$",
)


def load_schema(name: str) -> dict:
    """One of the shipped schema files, by file name."""
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def same(a: object, b: object) -> bool:
    """JSON equality: 1 and true differ."""
    return json_type(a) == json_type(b) and a == b


def has_type(value: object, wanted: str) -> bool:
    actual = json_type(value)
    return actual == wanted or (wanted == "number" and actual == "integer")


def resolve(ref: str, root: dict) -> dict:
    prefix = "#/$defs/"
    if not ref.startswith(prefix) or ref[len(prefix) :] not in root.get("$defs", {}):
        raise KeyError(ref)
    return root["$defs"][ref[len(prefix) :]]


def check_schema(instance: object, schema: dict, path: str = "$") -> list[str]:
    """Every way `instance` fails `schema`, each naming the path of the value."""
    return _check(instance, schema, path, schema)


def _check(value: object, schema: dict, path: str, root: dict) -> list[str]:
    errors = [
        f"{path}: schema keyword {key} is not supported"
        for key in schema
        if key not in KEYWORDS and key not in ANNOTATIONS
    ]
    if "$ref" in schema:
        try:
            target = resolve(schema["$ref"], root)
        except KeyError:
            errors.append(
                f"{path}: schema reference {schema['$ref']} cannot be resolved",
            )
        else:
            errors += _check(value, target, path, root)
    if "type" in schema:
        wanted = (
            schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        )
        if not any(has_type(value, t) for t in wanted):
            return [
                *errors,
                f"{path}: expected {' or '.join(wanted)}, got {json_type(value)}",
            ]
    if "const" in schema and not same(value, schema["const"]):
        errors.append(f"{path}: expected {json.dumps(schema['const'])}")
    if "enum" in schema and not any(same(value, v) for v in schema["enum"]):
        allowed = ", ".join(json.dumps(v) for v in schema["enum"])
        errors.append(f"{path}: {json.dumps(value)} is not one of {allowed}")
    if isinstance(value, str):
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(
                f"{path}: {json.dumps(value)} does not match {schema['pattern']}",
            )
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']} characters")
    if isinstance(value, dict):
        errors += _check_object(value, schema, path, root)
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += _check(item, schema["items"], f"{path}[{i}]", root)
    if "oneOf" in schema:
        passing = [s for s in schema["oneOf"] if not _check(value, s, path, root)]
        if len(passing) != 1:
            errors.append(
                f"{path}: matches {len(passing)} of the oneOf choices, not exactly 1",
            )
    return errors


def _check_object(value: dict, schema: dict, path: str, root: dict) -> list[str]:
    errors = [
        f"{path}: missing required field {key}"
        for key in schema.get("required", [])
        if key not in value
    ]
    properties = schema.get("properties", {})
    for key, sub in properties.items():
        if key in value:
            errors += _check(value[key], sub, f"{path}.{key}", root)
    if schema.get("additionalProperties") is False:
        errors += [
            f"{path}.{key}: field is not allowed"
            for key in value
            if key not in properties
        ]
    return errors


def check_content(state: dict) -> list[str]:
    """STATE-001.3: no banned key at any depth, no absolute path outside free text."""
    return _scan(state, "$")


def _scan(value: object, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if str(key).lower() in BANNED_KEYS:
                errors.append(f"{child}: state must not hold a {key} field")
            errors += _scan(item, child)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            errors += _scan(item, f"{path}[{i}]")
    elif isinstance(value, str) and ABSOLUTE.match(value) and not FREE_TEXT.match(path):
        errors.append(f"{path}: state must not hold an absolute path")
    return errors
