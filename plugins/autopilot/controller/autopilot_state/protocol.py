"""Bounded controller protocol, public metadata, snapshots, and workflow open."""

from __future__ import annotations

import copy
import json
import secrets
from pathlib import Path

from . import actors, schema
from .paths import resolve_project_root
from .store import FutureSchemaError, RevisionConflictError, StateError, StateIOError, StateStore

REQUEST_LIMIT = 2097152
RESPONSE_LIMIT = 16777216
ENVELOPE_KEYS = {"protocol_major", "operation", "request_id", "expected_revision",
                 "project_id", "workflow_id", "actor_id", "job_id", "lease_epoch", "payload"}
OWNER_OPERATIONS = {"owner.acquire", "owner.release", "owner.recover"}


class ProtocolError(Exception):
    """A fixed, redacted public failure, with its observed revision."""

    def __init__(self, code: str, revision: int = 0) -> None:
        super().__init__(code)
        self.code = code
        self.revision = revision


def response(result: object = None, revision: int = 0, error: str | None = None) -> dict:
    return {"ok": error is None, "revision": revision, "result": result,
            "error_code": error, "retryable": error == "revision_conflict"}


def public_contract() -> tuple[dict, dict]:
    package = Path(__file__).absolute().parents[2]
    contract = package / "contracts" / "controller"
    raw_schema = actors.read_public(contract / "workflow-v1.json")
    raw_fixtures = actors.read_public(contract / "fixtures-v1.json")
    declared = schema.decode_json(raw_schema.decode("utf-8"), source="contract")
    manifest = schema.decode_json(actors.read_public(package / "plugin.json").decode("utf-8"),
                                  source="manifest")
    metadata = {"protocol_major": 1, "package_version": manifest["version"],
                "schema_digest": actors.digest(raw_schema),
                "fixture_digest": actors.digest(raw_fixtures),
                "operations": ["workflow.open"], "capabilities": ["workflow.core.v1"]}
    return metadata, declared["x-controller"]


def validate_payload(operation: str, payload: object) -> None:
    if not isinstance(payload, dict):
        raise schema.SchemaError("invalid payload")
    if operation in ("workflow.open", "owner.release"):
        schema._object(payload, set())
    elif operation == "owner.acquire":
        schema._object(payload, {"mode", "native_session_id"})
        if payload["mode"] not in ("manual", "supervised"):
            raise schema.SchemaError("invalid mode")
        schema._identity(payload["native_session_id"])
    elif operation == "owner.recover":
        schema._object(payload, {"reason", "reconciled_job_ids"})
        reason = payload["reason"]
        if not isinstance(reason, str) or not 1 <= len(reason.encode("utf-8")) <= 4096:
            raise schema.SchemaError("invalid reason")
        if payload["reconciled_job_ids"] != []:
            raise schema.SchemaError("invalid reconciled jobs")


def parse_request(raw: bytes, declared: dict) -> dict:
    try:
        if len(raw) > REQUEST_LIMIT:
            raise schema.SchemaError("request exceeds limit")
        request = schema.decode_json(raw.decode("utf-8"), source="request")
        schema._object(request, ENVELOPE_KEYS)
        schema._counter(request["protocol_major"])
        schema._counter(request["expected_revision"])
        schema._identity(request["request_id"])
        schema._digest(request["project_id"])
        for key in ("workflow_id", "actor_id", "job_id"):
            if request[key] is not None:
                schema._identity(request[key])
        if request["lease_epoch"] is not None:
            schema._counter(request["lease_epoch"])
        operation = request["operation"]
        if not isinstance(operation, str) or operation not in (
                {"workflow.open"} | OWNER_OPERATIONS | set(declared["reserved_operations"])):
            raise schema.SchemaError("unknown operation")
        validate_payload(operation, request["payload"])
        actors.canonical(request)
    except (ValueError, UnicodeError, RecursionError, TypeError) as error:
        raise ProtocolError("invalid_request") from error
    if request["protocol_major"] != 1:
        raise ProtocolError("incompatible_contract")
    return request


def project_identity(root: Path) -> str:
    return actors.digest(str(root).encode("utf-8"))


def state_binding(state: dict, root: Path) -> None:
    if state["project_id"] != project_identity(root) or state["repo_root"] != str(root):
        raise ProtocolError("wrong_binding", state["revision"])


def fresh_binding(request: dict, revision: int = 0) -> None:
    if any(request[key] is not None for key in ("workflow_id", "actor_id", "lease_epoch", "job_id")):
        raise ProtocolError("wrong_binding", revision)


def actor_binding(request: dict, descriptor: dict, revision: int) -> None:
    if request["job_id"] is not None or any(
            request[key] != descriptor[key] for key in
            ("project_id", "workflow_id", "actor_id", "lease_epoch")):
        raise ProtocolError("wrong_binding", revision)


def existing_open(request: dict, actor_file: Path | None, current: dict,
                  layout: actors.PrivateLayout, store: StateStore) -> dict:
    revision = current["revision"]
    receipt = current["receipts"].get(request["request_id"])
    request_digest = actors.digest(actors.canonical(request))
    if receipt is not None:
        if receipt["request_digest"] != request_digest:
            raise ProtocolError("invalid_request", revision)
        if request["workflow_id"] is None:
            fresh_binding(request, revision)
        else:
            actor_binding(request, receipt["authorizing_actor"], revision)
            actors.authenticate(actor_file, receipt["authorizing_actor"], layout)
        actors.verify_operator(layout, current)
        return receipt["response"]
    if request["workflow_id"] is None:
        fresh_binding(request, revision)
        raise ProtocolError("revision_conflict", revision)
    descriptor = current["actors"].get(request["actor_id"])
    if descriptor is None or descriptor["role"] != "operator":
        raise ProtocolError("wrong_binding", revision)
    actor_binding(request, descriptor, revision)
    actors.authenticate(actor_file, descriptor, layout)
    if request["expected_revision"] != revision:
        raise ProtocolError("revision_conflict", revision)
    actors.verify_operator(layout, current)
    result = {"workflow_id": current["workflow_id"], "actor_id": descriptor["actor_id"],
              "actor_file": str(layout.actors / "operator.json"),
              "lease_epoch": current["lease_epoch"]}
    completed = response(result, revision + 1)
    candidate = copy.deepcopy(current)
    candidate["revision"] += 1
    candidate["receipts"][request["request_id"]] = {
        "request_digest": request_digest, "authorizing_actor": descriptor, "response": completed}
    actors.admit(candidate, completed)
    store._transaction_locked(lambda unused: candidate, expected_revision=revision,
                              publication_guard=layout.verify)
    return completed


def apply_locked(request: dict, actor_file: Path | None, layout: actors.PrivateLayout,
                 store: StateStore) -> dict:
    current = store._read_locked() if layout.exists(store.path) else None
    revision = 0 if current is None else current["revision"]
    try:
        if current is not None:
            state_binding(current, layout.root)
        if request["project_id"] != project_identity(layout.root) or request["job_id"] is not None:
            raise ProtocolError("wrong_binding", revision)
        intent = actors.read_intent(layout)
        if intent is not None:
            fresh_binding(request, revision)
            if request != intent["request"]:
                code = ("invalid_request" if request["request_id"] ==
                        intent["request"]["request_id"] else "recovery_required")
                raise ProtocolError(code, revision)
            return actors.finish_bootstrap(intent, layout, store, current)
        if request["operation"] != "workflow.open":
            raise ProtocolError("missing_capability", revision)
        if current is not None:
            return existing_open(request, actor_file, current, layout, store)
        fresh_binding(request, revision)
        if request["expected_revision"] != 0:
            raise ProtocolError("revision_conflict", revision)
        layout.prepare_ignores()
        result = {"workflow_id": "workflow-" + secrets.token_hex(16),
                  "actor_id": "operator-" + secrets.token_hex(16),
                  "actor_file": str(layout.actors / "operator.json"), "lease_epoch": 0}
        completed = response(result)
        if layout.exists(layout.actors / "operator.json"):
            raise StateIOError("unreferenced final credential")
        intent = actors.prepare_bootstrap(request, layout, completed)
        return actors.finish_bootstrap(intent, layout, store, None)
    except actors.BindingError as error:
        raise ProtocolError("wrong_binding", revision) from error
    except RevisionConflictError as error:
        raise ProtocolError("revision_conflict", revision) from error
    except FutureSchemaError as error:
        raise ProtocolError("incompatible_contract", revision) from error
    except (StateError, OSError, ValueError, KeyError, TypeError) as error:
        raise ProtocolError("recovery_required", revision) from error


def apply(root: Path, request_file: Path, actor_file: Path | None) -> dict:
    try:
        _, declared = public_contract()
        try:
            raw = actors.read_public(request_file.absolute(), REQUEST_LIMIT)
        except (OSError, StateError) as error:
            raise ProtocolError("invalid_request") from error
        request = parse_request(raw, declared)
        root = resolve_project_root(root)
        with actors.PrivateLayout(root) as layout:
            store = StateStore(layout.private / "state.json")
            if request["project_id"] != project_identity(root) or request["job_id"] is not None:
                raise ProtocolError("wrong_binding")
            initialized = layout.exists(store.path) or layout.exists(
                layout.private / "credential-intent.json")
            if initialized and not layout.exists(layout.private / "state.json.lock"):
                raise ProtocolError("recovery_required")
            if not initialized:
                fresh_binding(request)
                if request["operation"] != "workflow.open":
                    raise ProtocolError("missing_capability")
                if request["expected_revision"] != 0:
                    raise ProtocolError("revision_conflict")
                layout.prepare()
            with store._locked(exclusive=True):
                layout.verify()
                return apply_locked(request, actor_file, layout, store)
    except ProtocolError as error:
        if error.revision == 0:
            error.revision = revision_hint(root)
        raise


def snapshot_projection(root: Path, state: dict | None) -> dict:
    if state is None:
        return {"project_id": project_identity(root), "workflow_id": None,
                "lease_epoch": 0, "owner": None, "health": "absent"}
    stored_bytes = len((json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
                        + "\n").encode("utf-8"))
    count = len(state["receipts"])
    return {"project_id": state["project_id"], "workflow_id": state["workflow_id"],
            "lease_epoch": state["lease_epoch"], "owner": state["owner"],
            "workflow": state["workflow"],
            "actors": [{"actor_id": actor["actor_id"], "role": actor["role"]}
                       for actor in state["actors"].values()],
            "receipt_count": count, "health": "ready",
            "capacity": {"normal_receipts_remaining": max(0, 4094 - count),
                         "hard_receipts_remaining": max(0, 4096 - count),
                         "normal_bytes_remaining": max(0, actors.NORMAL_STATE_LIMIT - stored_bytes)}}


def snapshot(root: Path) -> dict:
    root = resolve_project_root(root)
    with actors.PrivateLayout(root) as layout:
        store = StateStore(layout.private / "state.json")
        if not layout.exists(layout.private / "state.json.lock"):
            if layout.exists(store.path) or layout.exists(layout.private / "credential-intent.json"):
                raise ProtocolError("recovery_required")
            return response(snapshot_projection(root, None))
        with store._locked(exclusive=False):
            layout.verify()
            if layout.exists(layout.private / "credential-intent.json"):
                raise ProtocolError("recovery_required")
            current = store._read_locked() if layout.exists(store.path) else None
            if current is not None:
                state_binding(current, root)
            return response(snapshot_projection(root, current), 0 if current is None else current["revision"])


def revision_hint(root: Path) -> int:
    """Best-effort read-only revision for errors rejected before request admission."""
    try:
        root = resolve_project_root(root)
        with actors.PrivateLayout(root) as layout:
            store = StateStore(layout.private / "state.json")
            if layout.exists(store.path) and layout.exists(layout.private / "state.json.lock"):
                with store._locked(exclusive=False):
                    return store._read_locked()["revision"]
    except (StateError, OSError, ValueError, KeyError, TypeError):
        pass
    return 0


def execute(command: str, root: Path | None, request_file: Path | None,
            actor_file: Path | None) -> dict:
    try:
        if command == "contract":
            return public_contract()[0]
        if command == "snapshot":
            return snapshot(root)
        return apply(root, request_file, actor_file)
    except ProtocolError as error:
        return response(revision=error.revision, error=error.code)
    except FutureSchemaError:
        return response(error="incompatible_contract")
    except (StateError, OSError, ValueError, KeyError, TypeError, RecursionError):
        return response(error="recovery_required")
