"""Bounded controller protocol, public metadata, snapshots, and operation dispatch."""

from __future__ import annotations

import copy
import dataclasses
import json
import secrets
from pathlib import Path

from . import actors, files, jobs, lifecycle, owner, policy, schema, tasks
from .paths import resolve_project_root
from .store import FutureSchemaError, RevisionConflictError, StateError, StateIOError, StateStore

REQUEST_LIMIT = 2097152
ENVELOPE_KEYS = {"protocol_major", "operation", "request_id", "expected_revision",
                 "project_id", "workflow_id", "actor_id", "job_id", "lease_epoch", "payload"}
OWNER_OPERATIONS = {"owner.acquire", "owner.release", "owner.recover"}
# lifecycle.py and files.py take StateStore's public lock per step, so these
# run after apply() releases its exclusive lock; never inside apply_locked.
SAGA_OPERATIONS = {"prd.enter", "phase.handoff", "prd.stall", "prd.park", "prd.defer",
                   "prd.complete"}
# Pure tasks/policy/jobs reducers commit inside apply_locked's lock.
REDUCER_OPERATIONS = {"task.replace", "task.start", "task.finish", "task.attempt",
                      "lane.route", "policy.bind", "job.plan", "job.claim", "job.record_exit",
                      "job.next"}
# apply_locked returns this instead of None when it admitted a stale saga
# request as a proven replay, so apply() can report the replay to the caller.
PROVEN_REPLAY: dict = {}


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
                "operations": ["workflow.open", "owner.acquire", "owner.release", "owner.recover",
                               "prd.enter", "phase.handoff", "prd.stall", "prd.park",
                               "prd.defer", "prd.complete", "task.replace", "task.start",
                               "task.finish", "task.attempt", "lane.route", "policy.bind",
                               "job.plan", "job.claim", "job.record_exit", "job.next"],
                "capabilities": ["workflow.core.v1", "workflow.lifecycle.v1",
                                 "workflow.tasks.v1", "workflow.policy.v1", "workflow.jobs.v1"]}
    return metadata, declared["x-controller"]


def validate_payload(operation: str, payload: object) -> None:
    if not isinstance(payload, dict):
        raise schema.SchemaError("invalid payload")
    if operation in ("workflow.open", "owner.release", "prd.complete"):
        schema._object(payload, set())
    elif operation in SAGA_OPERATIONS:
        validate_saga_payload(operation, payload)
    elif operation in REDUCER_OPERATIONS:
        validate_reducer_payload(operation, payload)
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
        jobs = payload["reconciled_job_ids"]
        if not isinstance(jobs, list):
            raise schema.SchemaError("invalid reconciled jobs")
        for job in jobs:
            schema._identity(job)
        if len(set(jobs)) != len(jobs):
            raise schema.SchemaError("duplicate reconciled jobs")


def validate_saga_payload(operation: str, payload: dict) -> None:
    if operation == "prd.enter":
        schema._object(payload, {"prds"})
        if not isinstance(payload["prds"], list):
            raise schema.SchemaError("invalid prds")
    elif operation == "phase.handoff":
        schema._object(payload, {"phase", "next_phase", "outcome"})
        if not all(isinstance(value, str) for value in payload.values()):
            raise schema.SchemaError("invalid handoff")
    elif operation in ("prd.stall", "prd.park"):
        schema._object(payload, {"prd", "site", "detail"})
        schema._identity(payload["prd"])
        schema._text(payload["site"])
        schema._text(payload["detail"])
    elif operation == "prd.defer":
        schema._object(payload, {"prd", "record"})
        schema._identity(payload["prd"])
        if not isinstance(payload["record"], dict):
            raise schema.SchemaError("invalid record")


def validate_reducer_payload(operation: str, payload: dict) -> None:
    if operation == "task.replace":
        schema._object(payload, {"tasks", "allow_expansion"})
        if (not isinstance(payload["tasks"], list)
                or not isinstance(payload["allow_expansion"], bool)):
            raise schema.SchemaError("invalid task plan")
        for item in payload["tasks"]:
            schema._task({**schema._object(item, {"id", "subject", "status", "depends_on"}),
                          "attempts": []})
    elif operation == "task.start":
        schema._object(payload, {"id"})
        schema._identity(payload["id"])
    elif operation == "task.finish":
        schema._object(payload, {"id", "outcome"})
        schema._identity(payload["id"])
    elif operation == "task.attempt":
        schema._object(payload, {"id", "implementor", "outcome"})
        schema._identity(payload["id"])
    elif operation == "lane.route":
        schema._object(payload, {"prd_frontmatter"})
        if not isinstance(payload["prd_frontmatter"], dict):
            raise schema.SchemaError("invalid frontmatter")
    elif operation == "policy.bind":
        schema._object(payload, {"lane", "reason"})
        if not isinstance(payload["lane"], str):
            raise schema.SchemaError("invalid lane")
        schema._text(payload["reason"])
    elif operation == "job.plan":
        schema._object(payload, {"jobs"})
        if not isinstance(payload["jobs"], list):
            raise schema.SchemaError("invalid job plan")
        for spec in payload["jobs"]:
            # A caller spec is closed: every key is required and every value
            # checked here, so a malformed spec is an invalid_request and never
            # reaches the state check that validates the committed row.
            schema._job_spec(spec, required=schema.JOB_SPEC_KEYS)
    elif operation == "job.next":
        schema._object(payload, set())
    elif operation == "job.claim":
        schema._object(payload, {"job_id"})
        schema._identity(payload["job_id"])
    elif operation == "job.record_exit":
        schema._object(payload, {"job_id", "exit_fact"})
        schema._identity(payload["job_id"])
        fact = schema._object(payload["exit_fact"], {"outcome", "native_session_id"})
        schema._text(fact["outcome"])
        if fact["native_session_id"] is not None:
            schema._identity(fact["native_session_id"])


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
                {"workflow.open"} | OWNER_OPERATIONS | SAGA_OPERATIONS | REDUCER_OPERATIONS
                | set(declared["reserved_operations"])):
            raise schema.SchemaError("unknown operation")
        if request["workflow_id"] is None:
            if (operation != "workflow.open" or request["actor_id"] is not None
                    or request["lease_epoch"] is not None
                    or request["expected_revision"] != 0):
                raise schema.SchemaError("unbound request must open at revision zero")
        else:
            schema._identity(request["actor_id"])
            schema._counter(request["lease_epoch"])
        validate_payload(operation, request["payload"])
        actors.canonical(request)
    except (ValueError, UnicodeError, RecursionError, TypeError) as error:
        raise ProtocolError("invalid_request") from error
    if request["protocol_major"] != 1:
        raise ProtocolError("incompatible_contract")
    if request["job_id"] is not None:
        raise ProtocolError("wrong_binding")
    return request


def project_identity(root: Path) -> str:
    return actors.digest(str(root).encode("utf-8"))


def state_binding(state: dict, root: Path) -> None:
    if state["project_id"] != project_identity(root) or state["repo_root"] != str(root):
        raise ProtocolError("wrong_binding", state["revision"])


# parse_request already refuses a job_id; the job_id clauses in fresh_binding
# and actor_binding are defence in depth for a caller that skips the parser.
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
            actors.authenticate_receipt(actor_file, receipt["authorizing_actor"], current, layout)
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
    actors.admit_staging(layout, [])
    store._transaction_locked(lambda unused: candidate, expected_revision=revision,
                              publication_guard=layout.verify)
    return completed


def proven_replay(request: dict, current: dict, layout: actors.PrivateLayout) -> bool:
    """True when a stale saga request's own operation is already recorded durably.

    The deferred ledger entry whose `op_id` is this request's id proves the
    saga committed and only its receipt is missing, so the request is this
    exact finished operation rather than a stale competitor.
    """
    return (request["operation"] in SAGA_OPERATIONS
            and files.recorded_operation(layout.private, current["workflow_id"],
                                         request["request_id"]))


def authorize(request: dict, actor_file: Path | None, current: dict,
              layout: actors.PrivateLayout) -> dict | None:
    """Return a replayed request's cached response, or None once a fresh one may run.

    Shared by every saga and reducer operation; any authenticated, registered
    actor qualifies. The caller holds the exclusive lock. A stale revision is
    a conflict unless the request is a `proven_replay`, which is admitted so a
    crash before its receipt can be retried to completion.
    """
    revision = current["revision"]
    receipt = current["receipts"].get(request["request_id"])
    if receipt is not None:
        actor_binding(request, receipt["authorizing_actor"], revision)
        actors.authenticate_receipt(actor_file, receipt["authorizing_actor"], current, layout)
        if receipt["request_digest"] != actors.digest(actors.canonical(request)):
            raise ProtocolError("invalid_request", revision)
        actors.verify_operator(layout, current)
        return receipt["response"]
    descriptor = current["actors"].get(request["actor_id"])
    if descriptor is None:
        raise ProtocolError("wrong_binding", revision)
    actor_binding(request, descriptor, revision)
    actors.authenticate(actor_file, descriptor, layout)
    if (request["expected_revision"] != revision
            and not proven_replay(request, current, layout)):
        raise ProtocolError("revision_conflict", revision)
    actors.verify_operator(layout, current)
    actors.admit_staging(layout, [])
    return None


def reduce_workflow(request: dict, workflow: dict, repo_root: str) -> dict:
    """Apply one pure tasks/policy/jobs reducer to `workflow` in place; return its result."""
    operation, payload = request["operation"], request["payload"]
    if operation == "task.replace":
        workflow["tasks"] = tasks.replace(payload["tasks"],
                                          allow_expansion=payload["allow_expansion"])
        return {"task_count": len(workflow["tasks"])}
    if operation == "task.start":
        workflow["tasks"] = tasks.start(workflow["tasks"], payload["id"],
                                        request["lease_epoch"])
    elif operation == "task.finish":
        workflow["tasks"] = tasks.finish(workflow["tasks"], payload["id"], payload["outcome"],
                                         request["lease_epoch"])
    elif operation == "task.attempt":
        workflow["tasks"] = tasks.attempt(workflow["tasks"], payload["id"],
                                          payload["implementor"], payload["outcome"])
    if operation.startswith("task."):
        task = next(item for item in workflow["tasks"] if item["id"] == payload["id"])
        return {"task_id": task["id"], "status": task["status"],
                "attempts": len(task["attempts"])}
    if operation == "lane.route":
        return policy.route(payload["prd_frontmatter"])
    if operation == "policy.bind":
        if workflow["work"] is None:
            raise ProtocolError("rejected_evidence")
        bound = policy.bind(payload["lane"], payload["reason"])
        workflow["work"].update(bound)
        return bound
    if operation == "job.plan":
        specs = payload["jobs"] or _derive_job_specs(workflow, repo_root)
        workflow["jobs"] = jobs.plan(workflow["jobs"], specs)
        return {"job_count": len(workflow["jobs"])}
    if operation == "job.next":
        row = jobs.next_job(workflow["jobs"])
        if row is None:
            raise ProtocolError("rejected_evidence")
        spec = row["spec"]
        # The whole spec, so a fresh session needs nothing else to run the job.
        return {**spec,
                "instruction": f"run job {spec['job_id']} ({spec['role']})"}
    if operation == "job.claim":
        workflow["jobs"] = jobs.claim(workflow["jobs"], payload["job_id"],
                                      request["actor_id"], request["lease_epoch"])
    else:
        workflow["jobs"] = jobs.record_exit(workflow["jobs"], payload["job_id"],
                                            request["actor_id"], request["lease_epoch"],
                                            payload["exit_fact"])
    row = next(item for item in workflow["jobs"] if item["spec"]["job_id"] == payload["job_id"])
    return {"job_id": row["spec"]["job_id"], "claimed_by": row["claimed_by"],
            "claim_epoch": row["claim_epoch"]}


def _resource_digest(prd: str, repo_root: str) -> str:
    """Attest the resource a derived job may touch: the active PRD in its repository."""
    try:
        content = (Path(repo_root) / files.PRD_ROOT / "wip" / prd).read_bytes()
    except OSError as error:
        raise ProtocolError("rejected_evidence") from error
    return actors.digest(actors.canonical(
        {"repo_root": repo_root, "prd": prd, "prd_digest": actors.digest(content)}))


def _derive_job_specs(workflow: dict, repo_root: str) -> list[dict]:
    """Derive one job spec per unfinished, not-yet-planned task, in task order.

    Nothing is invented: each digest attests real content, and the
    requirements come from the active work through `policy.job_requirements`.
    """
    planned_ids = {row["spec"]["job_id"] for row in workflow["jobs"]}
    scheduled = [task for task in workflow["tasks"]
                 if task["id"] not in planned_ids
                 and task["status"] in ("pending", "in_progress")]
    if not scheduled:
        return []
    work = workflow["work"]
    if work is None:
        raise ProtocolError("rejected_evidence")
    requirements = policy.job_requirements(work)
    resource_digest = _resource_digest(work["prd"], repo_root)
    return [{"job_id": task["id"], "depends_on": list(task["depends_on"]),
             "input_digests": [], "resource_digest": resource_digest,
             "source_digest": actors.digest(actors.canonical(task)),
             **requirements} for task in scheduled]


def apply_reducer(request: dict, actor_file: Path | None, current: dict,
                  layout: actors.PrivateLayout, store: StateStore) -> dict:
    """Commit one reducer result and its receipt under the held exclusive lock."""
    revision = current["revision"]
    cached = authorize(request, actor_file, current, layout)
    if cached is not None:
        return cached
    candidate = copy.deepcopy(current)
    try:
        result = reduce_workflow(request, candidate["workflow"], candidate["repo_root"])
    except policy.InvalidPlan as error:
        raise ProtocolError("rejected_evidence", revision) from error
    except ProtocolError as error:
        error.revision = revision
        raise
    candidate["revision"] += 1
    completed = response(result, candidate["revision"])
    candidate["receipts"][request["request_id"]] = {
        "request_digest": actors.digest(actors.canonical(request)),
        "authorizing_actor": current["actors"][request["actor_id"]], "response": completed}
    actors.admit(candidate, completed)
    store._transaction_locked(lambda unused: candidate, expected_revision=revision,
                              publication_guard=layout.verify)
    return completed


def run_saga(request: dict, current: dict, store: StateStore) -> dict:
    """Run one self-locking lifecycle reducer or files saga; return its result."""
    operation, payload = request["operation"], request["payload"]
    reducer = {"prd.enter": lifecycle.enter, "phase.handoff": lifecycle.handoff,
               "prd.complete": lifecycle.complete}.get(operation)
    if reducer is not None:
        return reducer(store, request, current)["result"]
    root = Path(current["repo_root"])

    # Deterministic from the request_id (not the default random uuid) so a
    # retry of an admitted-but-undelivered intent recomputes the same
    # operation id and `files._execute` can recognize its own durable ledger
    # entry as a replay instead of re-running a saga whose precondition the
    # first, successful run already invalidated.
    def operation_id_factory() -> str:
        return request["request_id"]

    if operation == "prd.defer":
        saga = files.defer_record(store, project_root=root, prd=payload["prd"],
                                  record=payload["record"],
                                  operation_id_factory=operation_id_factory)
    else:
        move = files.stall if operation == "prd.stall" else files.park
        saga = move(store, project_root=root, prd=payload["prd"], site=payload["site"],
                    detail=payload["detail"], operation_id_factory=operation_id_factory)
    return dataclasses.asdict(saga)


def record_receipt(request: dict, descriptor: dict, result: dict,
                   layout: actors.PrivateLayout, store: StateStore) -> dict:
    """Cache a finished saga's response in its own transaction, after the saga."""
    request_digest = actors.digest(actors.canonical(request))
    recorded = []

    def mutate(state: dict) -> None:
        if request["request_id"] in state["receipts"]:
            raise StateIOError("receipt already recorded")
        completed = response(result, state["revision"] + 1)
        state["receipts"][request["request_id"]] = {
            "request_digest": request_digest, "authorizing_actor": descriptor,
            "response": completed}
        actors.admit(state, completed)
        recorded.append(completed)

    store.transaction(mutate, publication_guard=layout.verify)
    return recorded[0]


def apply_unlocked(request: dict, layout: actors.PrivateLayout, store: StateStore,
                   replay: bool = False) -> dict:
    """Run a saga operation apply_locked admitted, outside StateStore._locked.

    `replay` says the admission was a `proven_replay`, so the response reports
    the operation as replayed instead of newly run.
    """
    revision = request["expected_revision"]
    try:
        layout.verify()
        current = store.read()
        revision = current["revision"]
        # Every commit bumps the revision, so an equal one is the admitted state.
        # A stale revision usually means a genuine conflict, but it can also
        # mean this exact request's saga already committed durably and only
        # its receipt is missing (a crash between the saga's commit and
        # record_receipt). run_saga's own replay detection tells the two
        # apart; only treat a stale revision as fatal when the saga itself
        # finds no matching durable record.
        stale = revision != request["expected_revision"]
        try:
            result = run_saga(request, current, store)
        except (files.PreconditionError, files.RecoveryConflictError,
                files.DeferredRecordConflictError) as error:
            if stale:
                raise ProtocolError("revision_conflict", revision) from error
            raise
        if replay:
            result = {**result, "replayed": True}
        return record_receipt(request, current["actors"][request["actor_id"]], result,
                              layout, store)
    except RevisionConflictError as error:
        raise ProtocolError("revision_conflict", revision) from error
    except FutureSchemaError as error:
        raise ProtocolError("incompatible_contract", revision) from error
    except (files.PreconditionError, files.RecoveryConflictError,
            files.DeferredRecordConflictError) as error:
        raise ProtocolError("rejected_evidence", revision) from error
    except (files.RecoveryRequiredError, StateError, OSError, ValueError, KeyError,
            TypeError) as error:
        raise ProtocolError("recovery_required", revision) from error


def apply_locked(request: dict, actor_file: Path | None, layout: actors.PrivateLayout,
                 store: StateStore) -> dict | None:
    current = store._read_locked() if layout.exists(store.path) else None
    revision = 0 if current is None else current["revision"]
    try:
        if current is not None:
            state_binding(current, layout.root)
        if request["project_id"] != project_identity(layout.root):
            raise ProtocolError("wrong_binding", revision)
        if current is not None and request["workflow_id"] not in (None, current["workflow_id"]):
            raise ProtocolError("wrong_binding", revision)
        intent = actors.read_intent(layout)
        if intent is not None:
            if intent["request"]["operation"] in OWNER_OPERATIONS:
                return owner.finish_intent(request, actor_file, intent, layout, store, current)
            fresh_binding(request, revision)
            if request != intent["request"]:
                code = ("invalid_request" if request["request_id"] ==
                        intent["request"]["request_id"] else "recovery_required")
                raise ProtocolError(code, revision)
            return actors.finish_bootstrap(intent, layout, store, current)
        if request["operation"] in OWNER_OPERATIONS and current is not None:
            return owner.apply_locked(request, actor_file, current, layout, store)
        if request["operation"] in REDUCER_OPERATIONS and current is not None:
            return apply_reducer(request, actor_file, current, layout, store)
        if request["operation"] in SAGA_OPERATIONS and current is not None:
            # None admits the request: apply() runs the saga after the lock is
            # released. authorize only admits a stale one as a proven replay.
            cached = authorize(request, actor_file, current, layout)
            if cached is None and request["expected_revision"] != current["revision"]:
                return PROVEN_REPLAY
            return cached
        if request["operation"] != "workflow.open":
            raise ProtocolError("missing_capability", revision)
        if current is not None:
            return existing_open(request, actor_file, current, layout, store)
        fresh_binding(request, revision)
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
            if request["project_id"] != project_identity(root):
                raise ProtocolError("wrong_binding")
            initialized = layout.exists(store.path) or layout.exists(
                layout.private / "credential-intent.json")
            if initialized and not layout.exists(layout.private / "state.json.lock"):
                raise ProtocolError("recovery_required")
            if not initialized:
                fresh_binding(request)
                layout.prepare()
            with store._locked(exclusive=True):
                layout.verify()
                completed = apply_locked(request, actor_file, layout, store)
            if completed is None or completed is PROVEN_REPLAY:
                completed = apply_unlocked(request, layout, store,
                                           replay=completed is PROVEN_REPLAY)
            return completed
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
            current = store._read_locked() if layout.exists(store.path) else None
            if layout.exists(layout.private / "credential-intent.json"):
                raise ProtocolError("recovery_required", 0 if current is None else current["revision"])
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
