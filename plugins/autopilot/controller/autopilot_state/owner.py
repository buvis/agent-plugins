"""Owner lease transitions under the controller's existing exclusive lock."""

from __future__ import annotations

import copy
import hmac
import os
import re
import secrets
from pathlib import Path

from . import actors, schema
from .store import StateIOError, StateStore

INTENT_KEYS = {"version", "request", "request_digest", "old_revision",
               "old_state_digest", "old_actor", "old_actors", "old_owner",
               "candidate", "response", "receipt", "credentials"}


def transition(current: dict, request: dict, operator: dict,
               owner: dict | None, layout: actors.PrivateLayout) -> tuple[dict, dict]:
    candidate = copy.deepcopy(current)
    candidate["revision"] += 1
    candidate["lease_epoch"] += 1
    candidate["actors"] = {operator["actor_id"]: operator}
    candidate["owner"] = None
    result = {"actor_id": operator["actor_id"], "lease_epoch": candidate["lease_epoch"],
              "operator_actor_file": str(layout.actors / "operator.json")}
    if owner is not None:
        candidate["actors"][owner["actor_id"]] = owner
        candidate["owner"] = {"actor_id": owner["actor_id"],
                              "lease_epoch": candidate["lease_epoch"], **request["payload"]}
        result.update(actor_id=owner["actor_id"],
                      actor_file=str(layout.actors / (owner["actor_id"] + ".json")))
    completed = {"ok": True, "revision": candidate["revision"], "result": result,
                 "error_code": None, "retryable": False}
    candidate["receipts"][request["request_id"]] = {
        "request_digest": actors.digest(actors.canonical(request)),
        "authorizing_actor": current["actors"][request["actor_id"]], "response": completed}
    emergency = current["owner"] is not None and request["operation"] != "owner.acquire"
    return actors.admit(candidate, completed, emergency=emergency), completed


def prepare(request: dict, current: dict, layout: actors.PrivateLayout) -> dict:
    old_operator = next(row for row in current["actors"].values() if row["role"] == "operator")
    old_raw = layout.read(layout.actors / "operator.json", 65536)
    credentials, staged = [], []
    descriptors = {}
    roles = ("operator", "owner") if request["operation"] == "owner.acquire" else ("operator",)
    for role in roles:
        actor_id = old_operator["actor_id"] if role == "operator" else "owner-" + secrets.token_hex(16)
        credential = {"actor_id": actor_id, "project_id": current["project_id"],
                      "workflow_id": current["workflow_id"], "role": role,
                      "lease_epoch": current["lease_epoch"] + 1,
                      "native_session_id": (request["payload"]["native_session_id"]
                                            if role == "owner" else None),
                      "secret": secrets.token_urlsafe(32)}
        raw = actors.canonical(credential)
        descriptor = actors.credential_descriptor(raw)
        descriptors[role] = descriptor
        entry = {"stage": f".{role}-{secrets.token_hex(16)}.stage",
                 "final": "operator.json" if role == "operator" else actor_id + ".json",
                 "digest": actors.digest(raw), "actor": descriptor, "previous": None}
        staged.append((entry["stage"], raw))
        if role == "operator":
            entry["previous"] = {"stage": f".operator-{secrets.token_hex(16)}.rollback",
                                 "digest": actors.digest(old_raw), "actor": old_operator}
            staged.append((entry["previous"]["stage"], old_raw))
        credentials.append(entry)
    candidate, completed = transition(current, request, descriptors["operator"],
                                       descriptors.get("owner"), layout)
    receipt = candidate["receipts"][request["request_id"]]
    intent = {"version": 1, "request": request, "request_digest": receipt["request_digest"],
              "old_revision": current["revision"],
              "old_state_digest": actors.digest(actors.canonical(current)),
              "old_actor": current["actors"][request["actor_id"]],
              "old_actors": current["actors"], "old_owner": current["owner"],
              "candidate": candidate, "response": completed, "receipt": receipt,
              "credentials": credentials}
    validate_intent(intent, layout)
    encoded = actors.canonical(intent)
    if len(encoded) > actors.INTENT_LIMIT:
        raise StateIOError("intent exceeds resource limit")
    for name, raw in staged:
        layout.write_new(layout.actors / name, raw)
    temporary = layout.private / f".intent-{secrets.token_hex(16)}.tmp"
    layout.write_new(temporary, encoded)
    layout.publish(temporary, layout.private / "credential-intent.json")
    return intent


def validate_intent(intent: object, layout: actors.PrivateLayout) -> dict:
    from . import protocol

    schema._object(intent, INTENT_KEYS)
    if type(intent["version"]) is not int or intent["version"] != 1:
        raise StateIOError("invalid owner intent")
    request = protocol.parse_request(actors.canonical(intent["request"]), {"reserved_operations": {}})
    if request["operation"] not in protocol.OWNER_OPERATIONS:
        raise StateIOError("invalid owner operation")
    candidate = schema.validate_state(intent["candidate"])
    old = copy.deepcopy(candidate)
    old["revision"] = intent["old_revision"]
    old["lease_epoch"] = request["lease_epoch"]
    old["actors"] = intent["old_actors"]
    old["owner"] = intent["old_owner"]
    del old["receipts"][request["request_id"]]
    old = schema.validate_state(old)
    authorizer = old["actors"][request["actor_id"]]
    expected_role = "owner" if request["operation"] == "owner.release" else "operator"
    if (old["repo_root"] != str(layout.root)
            or old["project_id"] != protocol.project_identity(layout.root)
            or request["expected_revision"] != old["revision"]
            or intent["old_state_digest"] != actors.digest(actors.canonical(old))
            or intent["old_actor"] != authorizer or authorizer["role"] != expected_role
            or (request["operation"] == "owner.acquire" and old["owner"] is not None)
            or (request["operation"] == "owner.recover" and request["payload"]["reconciled_job_ids"])):
        raise StateIOError("inconsistent owner predecessor")
    protocol.actor_binding(request, authorizer, old["revision"])
    descriptors = _intent_credentials(intent, request, old)
    expected, completed = transition(old, request, descriptors["operator"],
                                     descriptors.get("owner"), layout)
    receipt = expected["receipts"][request["request_id"]]
    if (candidate != expected or intent["response"] != completed or intent["receipt"] != receipt
            or intent["request_digest"] != receipt["request_digest"]):
        raise StateIOError("inconsistent owner intent")
    return intent


def _intent_credentials(intent: dict, request: dict, old: dict) -> dict:
    entries = intent["credentials"]
    roles = ["operator", "owner"] if request["operation"] == "owner.acquire" else ["operator"]
    if not isinstance(entries, list) or len(entries) != len(roles):
        raise StateIOError("invalid owner credentials")
    descriptors, names = {}, set()
    old_operator = next(row for row in old["actors"].values() if row["role"] == "operator")
    for entry, role in zip(entries, roles):
        schema._object(entry, {"stage", "final", "digest", "actor", "previous"})
        descriptor = schema._actor(entry["actor"])
        schema._digest(entry["digest"])
        final = "operator.json" if role == "operator" else descriptor["actor_id"] + ".json"
        if (descriptor["role"] != role or entry["final"] != final
                or descriptor["lease_epoch"] != old["lease_epoch"] + 1
                or any(descriptor[key] != old[key] for key in ("project_id", "workflow_id"))
                or re.fullmatch(r"\." + role + r"-[0-9a-f]{32}\.stage", entry["stage"]) is None):
            raise StateIOError("inconsistent owner credential")
        if role == "operator":
            previous = schema._object(entry["previous"], {"stage", "digest", "actor"})
            schema._digest(previous["digest"])
            if (descriptor["actor_id"] != old_operator["actor_id"]
                    or descriptor["secret_digest"] == old_operator["secret_digest"]
                    or previous["actor"] != old_operator
                    or re.fullmatch(r"\.operator-[0-9a-f]{32}\.rollback", previous["stage"]) is None):
                raise StateIOError("invalid operator rotation")
            names.add(previous["stage"])
        elif (entry["previous"] is not None
              or re.fullmatch(r"owner-[0-9a-f]{32}", descriptor["actor_id"]) is None
              or descriptor["actor_id"] in old["actors"]
              or descriptor["native_session_id"] != request["payload"]["native_session_id"]):
            raise StateIOError("invalid owner issuance")
        if entry["stage"] in names:
            raise StateIOError("duplicate owner stage")
        names.add(entry["stage"])
        descriptors[role] = descriptor
    return descriptors


def verify_file(layout: actors.PrivateLayout, path: Path, entry: dict) -> None:
    raw = layout.read(path, 65536)
    if (not hmac.compare_digest(actors.digest(raw), entry["digest"])
            or actors.credential_descriptor(raw) != entry["actor"]):
        raise StateIOError("credential evidence does not match intent")


def finish_intent(request: dict, actor_file: Path | None, intent: dict,
                  layout: actors.PrivateLayout, store: StateStore, current: dict | None) -> dict:
    from . import protocol

    revision = 0 if current is None else current["revision"]
    if request != intent["request"]:
        raise protocol.ProtocolError("recovery_required", revision)
    # A rotated operator can recover its lost acknowledgement at the same path.
    actors.authenticate_receipt(actor_file, intent["old_actor"], intent["candidate"], layout)
    validate_intent(intent, layout)
    candidate = intent["candidate"]
    if current is None or (current != candidate and (
            current["revision"] != intent["old_revision"]
            or actors.digest(actors.canonical(current)) != intent["old_state_digest"])):
        raise StateIOError("state does not match owner intent")
    _publish_credentials(intent, layout, current, candidate)

    def guard() -> None:
        layout.verify()
        for entry in intent["credentials"]:
            verify_file(layout, layout.actors / entry["final"], entry)

    guard()
    if current != candidate:
        store._transaction_locked(lambda unused: candidate, expected_revision=intent["old_revision"],
                                  publication_guard=guard)
    guard()
    for entry in intent["credentials"]:
        layout.remove(layout.actors / entry["stage"])
        if entry["previous"] is not None:
            layout.remove(layout.actors / entry["previous"]["stage"])
    os.fsync(layout.directories[layout.actors])
    layout.remove(layout.private / "credential-intent.json")
    os.fsync(layout.directories[layout.private])
    return intent["response"]


def _publish_credentials(intent: dict, layout: actors.PrivateLayout,
                         current: dict, candidate: dict) -> None:
    pending = []
    # Validate every piece of evidence before publishing any credential.
    for entry in intent["credentials"]:
        stage, final = layout.actors / entry["stage"], layout.actors / entry["final"]
        previous = entry["previous"]
        if previous is not None:
            verify_file(layout, layout.actors / previous["stage"], previous)
        if layout.exists(stage):
            verify_file(layout, stage, entry)
        if layout.exists(final):
            raw = layout.read(final, 65536)
            if actors.digest(raw) == entry["digest"]:
                verify_file(layout, final, entry)
                continue
            if previous is None or current == candidate:
                raise StateIOError("published credential does not match intent")
            verify_file(layout, final, previous)
        elif current == candidate or previous is not None:
            raise StateIOError("committed credential missing")
        verify_file(layout, stage, entry)
        pending.append((stage, final))
    for stage, final in pending:
        layout.verify()
        os.replace(stage.name, final.name, src_dir_fd=layout.directories[layout.actors],
                   dst_dir_fd=layout.directories[layout.actors])
        layout.verify()
        os.fsync(layout.directories[layout.actors])


def apply_locked(request: dict, actor_file: Path | None, current: dict,
                 layout: actors.PrivateLayout, store: StateStore) -> dict:
    from . import protocol

    revision = current["revision"]
    receipt = current["receipts"].get(request["request_id"])
    if receipt is not None:
        protocol.actor_binding(request, receipt["authorizing_actor"], revision)
        actors.authenticate_receipt(actor_file, receipt["authorizing_actor"], current, layout)
        if receipt["request_digest"] != actors.digest(actors.canonical(request)):
            raise protocol.ProtocolError("invalid_request", revision)
        actors.verify_operator(layout, current)
        return receipt["response"]
    descriptor = current["actors"].get(request["actor_id"])
    role = "owner" if request["operation"] == "owner.release" else "operator"
    if descriptor is None or descriptor["role"] != role:
        raise protocol.ProtocolError("wrong_binding", revision)
    protocol.actor_binding(request, descriptor, revision)
    actors.authenticate(actor_file, descriptor, layout)
    if request["expected_revision"] != revision:
        raise protocol.ProtocolError("revision_conflict", revision)
    if request["operation"] == "owner.acquire" and current["owner"] is not None:
        raise protocol.ProtocolError("wrong_binding", revision)
    if request["operation"] == "owner.recover" and (
            request["payload"]["reconciled_job_ids"] or current["workflow"]["jobs"]):
        raise protocol.ProtocolError("rejected_evidence", revision)
    actors.verify_operator(layout, current)
    intent = prepare(request, current, layout)
    return finish_intent(request, actor_file, intent, layout, store, current)
