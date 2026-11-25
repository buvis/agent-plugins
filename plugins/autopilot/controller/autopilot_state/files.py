"""PRD bucket moves and deferred records through one crash-recoverable saga.

Adapted from OVCAQ src/ovcaq/workflow/records.py, _files.py and _rename.py at
cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7. The wip/ -> done/ completion move has
no OVCAQ source; it is net-new here under its own SagaBoundary pair.

MIT License

Copyright (c) 2026 Bob Buvis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import json
import os
import stat
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from . import actors, schema
from .paths import resolve_project_root
from .store import StateStore

PRD_ROOT = Path("docs", "dev", "project-management", "prds")


class SagaBoundary(StrEnum):
    """Characterized interruption points in the PRD filesystem sagas."""

    AFTER_MKDIR_BEFORE_INTENT = "after-mkdir-before-intent"
    AFTER_INTENT_BEFORE_MOVE = "after-intent-before-move"
    AFTER_RENAME_BEFORE_DIRECTORY_FSYNC = "after-rename-before-directory-fsync"
    AFTER_MOVE_BEFORE_APPEND = "after-move-before-append"
    AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC = "after-replace-before-directory-fsync"
    AFTER_APPEND_BEFORE_COMMIT = "after-append-before-commit"
    AFTER_COMMIT_BEFORE_MARKER_DELETE = "after-commit-before-marker-delete"
    PRD_COMPLETE_MOVE_STAGED = "prd-complete-move-staged"
    PRD_COMPLETE_MOVE_COMMITTED = "prd-complete-move-committed"


type BoundaryHook = Callable[[SagaBoundary], None]
type OperationIdFactory = Callable[[], str]
type TimestampFactory = Callable[[], str]


class PreconditionError(ValueError):
    """Raised when state refuses to start an operation; nothing was staged."""


class BucketError(PreconditionError):
    """Raised when the named PRD is not in the bucket the operation needs."""


class RecoveryConflictError(ValueError):
    """Raised when a request conflicts with the active recovery marker."""


class RecoveryRequiredError(RuntimeError):
    """Raised when an interrupted saga matches no resumable on-disk step."""


class DeferredRecordConflictError(ValueError):
    """Raised when an operation ID is reused for a different deferred record."""


@dataclass(frozen=True)
class SagaResult:
    """The committed result of one saga run or replay."""

    operation_id: str
    kind: str
    replayed: bool
    systemic_halt: bool


# workflow.recovery keeps its {"op", "boundary"} shape: "op" holds the
# canonical JSON operation descriptor, "boundary" the last durable step.
_DESTINATIONS = {"stall": "hold", "park": "hold", "complete": "done"}
_STEPS = {
    "stall": ("intent", "moved", "recorded", "committed"),
    "park": ("intent", "moved", "recorded", "committed"),
    "defer": ("intent", "recorded", "committed"),
    "complete": ("intent", "committed"),
}
_OPERATION_KEYS = {
    "id", "kind", "prd", "site", "detail", "record_digest", "artifact", "created_at",
}
_RESERVED_RECORD_KEYS = {"op_id", "prd"}


@dataclass(frozen=True)
class _Request:
    kind: str
    prd: str
    site: str | None = None
    detail: str | None = None
    record: dict | None = None

    @property
    def record_digest(self) -> str | None:
        if self.record is None:
            return None
        return actors.digest(actors.canonical(self.record))


@dataclass(frozen=True)
class _Move:
    name: str
    wip: Path
    destination: Path
    wip_fd: int
    destination_fd: int

    def locate(self) -> tuple[os.stat_result | None, os.stat_result | None]:
        _verify_directory(self.wip, self.wip_fd)
        _verify_directory(self.destination, self.destination_fd)
        return (_artifact(self.wip_fd, self.name),
                _artifact(self.destination_fd, self.name))


def _require_basename(value: object, label: str) -> str:
    if (not isinstance(value, str) or not value or value in {".", ".."}
            or not value.isprintable() or "/" in value or "\\" in value):
        raise PreconditionError(f"{label} must be one printable path component: {value!r}")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PreconditionError(f"{label} must be a non-empty string")
    return value


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _new_operation_id() -> str:
    return uuid.uuid4().hex


def _trip(hook: BoundaryHook | None, boundary: SagaBoundary) -> None:
    if hook is not None:
        hook(boundary)


def _fsync_path(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _verify_directory(path: Path, descriptor: int) -> None:
    opened = os.fstat(descriptor)
    linked = os.stat(path, follow_symlinks=False)
    if (not stat.S_ISDIR(linked.st_mode)
            or (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)):
        raise OSError(f"PRD bucket identity changed: {path}")


@contextmanager
def _open_directory(path: Path, *, create: bool = False) -> Iterator[int]:
    """Open a bucket without following its final link, creating it if asked."""
    if create and not path.exists():
        path.mkdir(exist_ok=True)
        _fsync_path(path.parent)
    try:
        descriptor = os.open(
            path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as error:
        raise BucketError(f"PRD bucket is not a real directory: {path}") from error
    try:
        _verify_directory(path, descriptor)
        yield descriptor
    finally:
        os.close(descriptor)


def _artifact(directory: int, name: str) -> os.stat_result | None:
    try:
        found = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(found.st_mode):
        raise OSError(f"PRD is not a regular non-symlink file: {name}")
    return found


def _identity(found: os.stat_result) -> dict:
    return {"device": found.st_dev, "inode": found.st_ino}


def _marker(operation: dict, step: str) -> dict:
    return {"op": actors.canonical(operation).decode("utf-8"), "boundary": step}


def _pending(state: dict) -> tuple[dict, str] | None:
    marker = state["workflow"]["recovery"]
    if marker is None:
        return None
    try:
        operation = schema.decode_json(marker["op"], source="recovery operation")
    except schema.SchemaError:
        operation = None
    if (not isinstance(operation, dict) or set(operation) != _OPERATION_KEYS
            or operation["kind"] not in _STEPS):
        raise RecoveryConflictError(
            f"recovery operation {marker['op']!r} is active; reconcile it first")
    if marker["boundary"] not in _STEPS[operation["kind"]]:
        raise RecoveryRequiredError(
            f"recovery operation {operation['id']} has unknown step {marker['boundary']!r}")
    return operation, marker["boundary"]


def _matches(operation: dict, request: _Request) -> bool:
    return (operation["kind"], operation["prd"], operation["site"],
            operation["detail"], operation["record_digest"]) == (
        request.kind, request.prd, request.site, request.detail, request.record_digest)


def _check_fresh(state: dict, request: _Request) -> None:
    workflow = state["workflow"]
    work = workflow["work"]
    if workflow["batch"] is None:
        raise PreconditionError(f"cannot {request.kind} without a running batch")
    if work is None or work["prd"] != request.prd:
        active = None if work is None else work["prd"]
        raise PreconditionError(
            f"requested PRD {request.prd!r} does not match active PRD {active!r}")
    if request.kind == "complete" and (
            work["phase"] != "done" or "review" not in work["completed_phases"]):
        raise PreconditionError("cannot complete a PRD outside the terminal reviewed state")


def _new_operation(request: _Request, operation_id: str, created_at: str) -> dict:
    return {
        "id": _require_basename(operation_id, "op_id"),
        "kind": request.kind,
        "prd": request.prd,
        "site": request.site,
        "detail": request.detail,
        "record_digest": request.record_digest,
        "artifact": None,
        "created_at": created_at,
    }


def _stamp(store: StateStore, state: dict, operation: dict,
           guard: Callable[[], None] | None) -> dict:
    def stamp(current: dict) -> None:
        if guard is not None:
            guard()
        if current["workflow"]["recovery"] is not None:
            raise RecoveryConflictError("another recovery operation is already active")
        current["workflow"]["recovery"] = _marker(operation, "intent")

    return store.transaction(stamp, expected_revision=state["revision"], publication_guard=guard)


def _advance(store: StateStore, operation: dict, expected: str, step: str,
             guard: Callable[[], None],
             bookkeeping: Callable[[dict], None] | None = None) -> None:
    marker = _marker(operation, expected)

    def advance(current: dict) -> None:
        guard()
        if current["workflow"]["recovery"] != marker:
            raise RecoveryConflictError(
                f"recovery operation {operation['id']} changed before {step}")
        if bookkeeping is not None:
            bookkeeping(current["workflow"])
        current["workflow"]["recovery"] = _marker(operation, step)

    store.transaction(advance, publication_guard=guard)


def _clear(store: StateStore, operation: dict, pause: dict | None) -> dict:
    """Delete the recovery marker, writing any pause in the same transaction."""
    marker = _marker(operation, "committed")

    def clear(current: dict) -> None:
        if current["workflow"]["recovery"] != marker:
            raise RecoveryConflictError(
                f"recovery operation {operation['id']} changed before marker delete")
        if pause is not None:
            # Terminal by contract: no controller operation clears workflow.pause,
            # prd.enter keeps rejecting while it is set, and it commits here so no
            # committed state has the marker gone and the pause missing.
            current["workflow"]["pause"] = pause
        current["workflow"]["recovery"] = None

    return store.transaction(clear)


def _bookkeeping(operation: dict) -> Callable[[dict], None]:
    kind, prd = operation["kind"], operation["prd"]

    def commit_kind(workflow: dict) -> None:
        batch = workflow["batch"]
        if kind == "defer":
            return
        if batch is None:
            raise RecoveryConflictError(f"batch ended before {kind} committed")
        if kind == "park":
            batch["parks_consecutive"] += 1
        else:
            batch["parks_consecutive"] = 0
        if kind == "complete" and prd not in batch["completed_prds"]:
            batch["completed_prds"].append(prd)
        workflow["work"] = None
        workflow["tasks"] = []

    return commit_kind


def _ledger_file(private: Path, workflow_id: str) -> Path:
    name = _require_basename(workflow_id, "workflow_id")
    return private / "deferred" / f"{name}-deferred.json"


def _ledger_path(store: StateStore, workflow_id: str) -> Path:
    return _ledger_file(store.path.parent, workflow_id)


def _records_entry(items: list[dict], request: _Request, operation_id: str) -> bool:
    """Whether `items` holds the very entry this request's own payload would write.

    An entry carrying the same `op_id` but different content was written by a
    different request, so it proves nothing about this one.
    """
    if request.kind == "defer":
        expected = {**(request.record or {}), "op_id": operation_id, "prd": request.prd}
    else:
        expected = {"type": "stall", "kind": request.kind, "site": request.site,
                    "detail": request.detail, "op_id": operation_id, "prd": request.prd}
    return expected in items


def recorded_request(private: Path, workflow_id: str, op_id: str, kind: str,
                     payload: dict) -> bool:
    """Whether the deferred ledger already records this exact request; reads only."""
    request = _Request(kind, payload["prd"], payload.get("site"), payload.get("detail"),
                       payload.get("record"))
    return _records_entry(_read_ledger(_ledger_file(private, workflow_id), workflow_id),
                          request, op_id)


def _read_ledger(path: Path, workflow_id: str) -> list[dict]:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        return []
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise OSError(f"deferred ledger is not a single-linked regular file: {path}")
        content = schema.decode_json(stream.read(), source=f"deferred ledger {path}")
    if (not isinstance(content, dict) or set(content) != {"workflow_id", "items"}
            or content["workflow_id"] != workflow_id
            or not isinstance(content["items"], list)
            or not all(isinstance(item, dict) for item in content["items"])):
        raise ValueError(f"corrupt deferred ledger {path}")
    return content["items"]


def _publish_ledger(path: Path, content: dict, hook: BoundaryHook | None) -> None:
    if not path.parent.exists():
        path.parent.mkdir(mode=0o700, exist_ok=True)
        _fsync_path(path.parent.parent)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    encoded = (json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True)
               + "\n").encode("utf-8")
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    _trip(hook, SagaBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC)
    _fsync_path(path.parent)


def _append_record(path: Path, workflow_id: str, item: dict,
                   hook: BoundaryHook | None) -> None:
    """Append one record, deduplicated by op_id so a replay never doubles it."""
    items = _read_ledger(path, workflow_id)
    existing = next((row for row in items if row.get("op_id") == item["op_id"]), None)
    if existing is not None:
        if existing != item:
            raise DeferredRecordConflictError(
                f"conflicting deferred record for op_id {item['op_id']!r}")
        _fsync_path(path.parent)
        return
    _publish_ledger(path, {"workflow_id": workflow_id, "items": [*items, item]}, hook)


def _ledger_item(operation: dict, request: _Request) -> dict:
    stamp = {"op_id": operation["id"], "prd": operation["prd"]}
    if operation["kind"] == "defer":
        return {**request.record, **stamp}
    return {"type": "stall", "kind": operation["kind"], "site": operation["site"],
            "detail": operation["detail"], **stamp}


def _verify_moved(move: _Move, artifact: object) -> None:
    source, destination = move.locate()
    if source is not None or destination is None or _identity(destination) != artifact:
        raise RecoveryRequiredError(
            f"PRD {move.name} is not the staged artifact alone in {move.destination}")


def _rename(move: _Move, artifact: object, hook: BoundaryHook | None) -> None:
    """Move the staged artifact, or accept a rename that already landed."""
    source, destination = move.locate()
    if source is not None and destination is None and _identity(source) == artifact:
        os.rename(move.name, move.name,
                  src_dir_fd=move.wip_fd, dst_dir_fd=move.destination_fd)
        _trip(hook, SagaBoundary.AFTER_RENAME_BEFORE_DIRECTORY_FSYNC)
    _verify_moved(move, artifact)
    os.fsync(move.wip_fd)
    os.fsync(move.destination_fd)
    _verify_moved(move, artifact)


def _stage(store: StateStore, state: dict, operation: dict, move: _Move,
           hook: BoundaryHook | None) -> dict:
    """Verify the PRD's actual bucket on disk, then stamp the intent."""
    source, destination = move.locate()
    if source is None:
        raise BucketError(f"PRD {move.name} is not in {move.wip}")
    if destination is not None:
        raise BucketError(f"PRD {move.name} already exists in {move.destination}")
    operation["artifact"] = _identity(source)

    def guard() -> None:
        current, landed = move.locate()
        if current is None or landed is not None or _identity(current) != operation["artifact"]:
            raise BucketError(f"PRD {move.name} changed before its intent was staged")

    if operation["kind"] != "complete":
        _trip(hook, SagaBoundary.AFTER_MKDIR_BEFORE_INTENT)
    return _stamp(store, state, operation, guard)


def _record_and_commit(store: StateStore, operation: dict, step: str, before: str,
                       ledger: tuple[Path, str], item: dict,
                       verify_move: Callable[[], None], hook: BoundaryHook | None) -> None:
    path, workflow_id = ledger

    def verify_recorded() -> None:
        verify_move()
        if item not in _read_ledger(path, workflow_id):
            raise RecoveryRequiredError(
                f"recovery operation {operation['id']} has no matching deferred record")

    if step == before:
        if operation["kind"] != "defer":
            _trip(hook, SagaBoundary.AFTER_MOVE_BEFORE_APPEND)
        verify_move()
        _append_record(path, workflow_id, item, hook)
        verify_recorded()
        _advance(store, operation, before, "recorded", verify_recorded)
        step = "recorded"
    if step == "recorded":
        _trip(hook, SagaBoundary.AFTER_APPEND_BEFORE_COMMIT)
        _advance(store, operation, "recorded", "committed", verify_recorded,
                 _bookkeeping(operation))
    else:
        verify_recorded()


def _run_move(store: StateStore, operation: dict, step: str, move: _Move,
              ledger: tuple[Path, str], request: _Request,
              hook: BoundaryHook | None, admitted_revision: int | None = None) -> None:
    artifact = operation["artifact"]

    def verify_move() -> None:
        _verify_moved(move, artifact)

    if operation["kind"] == "complete":
        if step == "intent":
            _trip(hook, SagaBoundary.PRD_COMPLETE_MOVE_STAGED)
            _rename(move, artifact, None)
            _advance(store, operation, "intent", "committed", verify_move,
                     _bookkeeping(operation))
        else:
            verify_move()
        return
    if step == "intent":
        _trip(hook, SagaBoundary.AFTER_INTENT_BEFORE_MOVE)
        if admitted_revision is not None and store.read()["revision"] != admitted_revision:
            raise RecoveryConflictError(
                f"recovery operation {operation['id']} for {operation['prd']} is no longer "
                "current; the workflow's revision advanced since this intent was admitted")
        _rename(move, artifact, hook)
        _advance(store, operation, "intent", "moved", verify_move)
        step = "moved"
    _record_and_commit(store, operation, step, "moved", ledger,
                       _ledger_item(operation, request), verify_move, hook)


def _replay_committed(store: StateStore, state: dict, request: _Request,
                      operation_id: str) -> SagaResult | None:
    """Return the prior result for a durably-committed op this call didn't stage.

    A caller may retry a request whose saga already ran to completion (its
    recovery marker cleared) but whose receipt never got recorded, e.g. a
    crash between the saga's own commit and `protocol.record_receipt`. The
    deferred ledger it appended to is the one durable, request-correlatable
    record of that; a match proves the retry is this exact, already-finished
    operation rather than a genuine conflict.
    """
    if request.kind not in ("stall", "park", "defer"):
        return None
    path = _ledger_path(store, state["workflow_id"])
    if not _records_entry(_read_ledger(path, state["workflow_id"]), request, operation_id):
        return None
    # Not a `_pending()`-marker resumption: the saga already ran to its
    # natural, non-replayed completion the first time.
    return SagaResult(operation_id, request.kind, False,
                      _systemic_park_halt(state, request))


def _run_saga_body(store: StateStore, project_root: Path, request: _Request, *,
                   prd_root: Path, boundary_hook: BoundaryHook | None,
                   operation_id_factory: OperationIdFactory,
                   now: TimestampFactory) -> SagaResult:
    state = store.read()
    project = resolve_project_root(project_root)
    if state["repo_root"] != str(project):
        raise PreconditionError(f"state belongs to {state['repo_root']}, not {project}")
    pending = _pending(state)
    admitted_revision = None
    if pending is None:
        candidate_id = operation_id_factory()
        replay = _replay_committed(store, state, request, candidate_id)
        if replay is not None:
            return replay
        _check_fresh(state, request)
        operation, step = _new_operation(request, candidate_id, now()), None
    else:
        operation, step = pending
        if not _matches(operation, request):
            raise RecoveryConflictError(
                f"recovery operation {operation['id']} for {operation['prd']} conflicts "
                f"with requested {request.kind} for {request.prd}")
    ledger = (_ledger_path(store, state["workflow_id"]), state["workflow_id"])
    destination = _DESTINATIONS.get(request.kind)
    if destination is None:
        if step is None:
            _stamp(store, state, operation, None)
            step = "intent"
        _record_and_commit(store, operation, step, "intent", ledger,
                           _ledger_item(operation, request), lambda: None, boundary_hook)
    else:
        buckets = project / prd_root
        with (_open_directory(buckets / "wip") as wip_fd,
              _open_directory(buckets / destination, create=True) as destination_fd):
            move = _Move(request.prd, buckets / "wip", buckets / destination,
                         wip_fd, destination_fd)
            if step is None:
                admitted_revision = _stage(store, state, operation, move,
                                           boundary_hook)["revision"]
                step = "intent"
            _run_move(store, operation, step, move, ledger, request, boundary_hook,
                     admitted_revision)
    _trip(boundary_hook, SagaBoundary.PRD_COMPLETE_MOVE_COMMITTED
          if request.kind == "complete" else SagaBoundary.AFTER_COMMIT_BEFORE_MARKER_DELETE)
    halt = _systemic_park_halt(store.read(), request)
    _clear(store, operation, {"site": "systemic_park",
                              "detail": f"second consecutive park for {request.prd}"}
           if halt else None)
    return SagaResult(operation["id"], request.kind, pending is not None, halt)


def _systemic_park_halt(state: dict, request: _Request) -> bool:
    """Whether this park is the second consecutive one, halting the batch."""
    batch = state["workflow"]["batch"]
    return (request.kind == "park" and batch is not None
            and batch["parks_consecutive"] >= 2)


def stall(store: StateStore, *, project_root: Path, prd: str, site: str, detail: str,
          prd_root: Path = PRD_ROOT, boundary_hook: BoundaryHook | None = None,
          operation_id_factory: OperationIdFactory = _new_operation_id,
          now: TimestampFactory = _utc_now) -> SagaResult:
    """Run or replay the stall saga: wip/ -> hold/, record, reset parks."""
    request = _Request("stall", _require_basename(prd, "prd"),
                       _require_text(site, "site"), _require_text(detail, "detail"))
    return _run_saga_body(store, project_root, request, prd_root=prd_root,
                    boundary_hook=boundary_hook,
                    operation_id_factory=operation_id_factory, now=now)


def park(store: StateStore, *, project_root: Path, prd: str,
         site: str = "wrapper_died",
         detail: str = "session ended without a committed transition",
         prd_root: Path = PRD_ROOT, boundary_hook: BoundaryHook | None = None,
         operation_id_factory: OperationIdFactory = _new_operation_id,
         now: TimestampFactory = _utc_now) -> SagaResult:
    """Run or replay the park saga; the second consecutive park halts the batch."""
    request = _Request("park", _require_basename(prd, "prd"),
                       _require_text(site, "site"), _require_text(detail, "detail"))
    return _run_saga_body(store, project_root, request, prd_root=prd_root,
                    boundary_hook=boundary_hook,
                    operation_id_factory=operation_id_factory, now=now)


def defer_record(store: StateStore, *, project_root: Path, prd: str, record: dict,
                 boundary_hook: BoundaryHook | None = None,
                 operation_id_factory: OperationIdFactory = _new_operation_id,
                 now: TimestampFactory = _utc_now) -> SagaResult:
    """Run or replay the defer saga: append one deferred record, move nothing."""
    if not isinstance(record, dict) or _RESERVED_RECORD_KEYS & set(record):
        raise PreconditionError("record must be an object without op_id or prd keys")
    try:
        schema.decode_json(actors.canonical(record).decode("utf-8"),
                           source="deferred record")
    except (TypeError, ValueError) as error:
        raise PreconditionError(f"record is not bounded JSON data: {error}") from error
    request = _Request("defer", _require_basename(prd, "prd"), record=record)
    return _run_saga_body(store, project_root, request, prd_root=PRD_ROOT,
                    boundary_hook=boundary_hook,
                    operation_id_factory=operation_id_factory, now=now)


def complete_prd(store: StateStore, *, project_root: Path, prd: str,
                 prd_root: Path = PRD_ROOT, boundary_hook: BoundaryHook | None = None,
                 operation_id_factory: OperationIdFactory = _new_operation_id,
                 now: TimestampFactory = _utc_now) -> SagaResult:
    """Run or replay the completion saga: wip/ -> done/ after accepted review."""
    request = _Request("complete", _require_basename(prd, "prd"))
    return _run_saga_body(store, project_root, request, prd_root=prd_root,
                    boundary_hook=boundary_hook,
                    operation_id_factory=operation_id_factory, now=now)


def load_deferred_records(store: StateStore) -> tuple[dict, ...]:
    """Load the workflow's deferred records."""
    workflow_id = store.read()["workflow_id"]
    return tuple(_read_ledger(_ledger_path(store, workflow_id), workflow_id))
