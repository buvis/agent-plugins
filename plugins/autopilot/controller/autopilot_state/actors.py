"""Private credentials and durable, secret-free bootstrap intent recovery."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
from pathlib import Path

from . import schema
from .store import StateIOError, StateStore

CREDENTIAL_KEYS = {"actor_id", "project_id", "workflow_id", "role",
                   "lease_epoch", "native_session_id", "secret"}
INTENT_KEYS = {"version", "request", "request_digest", "old_revision",
               "old_state_digest", "old_actor", "candidate", "response",
               "receipt", "new_actor", "stage", "final", "credential_digest"}
INTENT_LIMIT = 33554432
NORMAL_STATE_LIMIT = 14680064


class BindingError(ValueError):
    """The supplied credential does not authorize the request."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class PrivateLayout:
    """Hold ancestor directory descriptors across inspection and publication."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.private = root / ".autopilot" / "controller"
        self.actors = self.private / "actors"
        self.directories: dict[Path, int] = {}

    def __enter__(self) -> PrivateLayout:
        try:
            self.directory(self.root)
            for path in (self.root / ".autopilot", self.private, self.actors):
                descriptor = self.directory(path)
                if descriptor is not None and stat.S_IMODE(
                        os.fstat(descriptor).st_mode) != 0o700:
                    raise StateIOError("controller directory is not private")
            self.verify()
            for name in ("state.json", "state.json.bak", "state.json.lock"):
                path = self.private / name
                if self.exists(path):
                    self._regular(os.stat(path.name, dir_fd=self.directories[self.private],
                                          follow_symlinks=False), True)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *unused: object) -> None:
        for descriptor in reversed(list(self.directories.values())):
            os.close(descriptor)
        self.directories.clear()

    def directory(self, path: Path, *, create: bool = False) -> int | None:
        if path in self.directories:
            return self.directories[path]
        parent = None if path == Path("/") else self.directory(path.parent, create=create)
        if path != Path("/") and parent is None:
            return None
        name = str(path) if parent is None else path.name
        if create:
            try:
                os.mkdir(name, 0o700, dir_fd=parent)
                if parent is not None:
                    os.fsync(parent)
            except FileExistsError:
                pass
        try:
            before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return None
        if not stat.S_ISDIR(before.st_mode):
            raise StateIOError("unsafe directory")
        descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=parent)
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            os.close(descriptor)
            raise StateIOError("directory changed while opening")
        self.directories[path] = descriptor
        return descriptor

    def verify(self) -> None:
        for path, descriptor in self.directories.items():
            parent = self.directories.get(path.parent) if path != Path("/") else None
            linked = os.stat(str(path) if parent is None else path.name,
                             dir_fd=parent, follow_symlinks=False)
            opened = os.fstat(descriptor)
            if (not stat.S_ISDIR(linked.st_mode) or
                    (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino)):
                raise StateIOError("directory changed during operation")
            if path in (self.root / ".autopilot", self.private, self.actors):
                if stat.S_IMODE(linked.st_mode) != 0o700:
                    raise StateIOError("controller directory is not private")

    def exists(self, path: Path) -> bool:
        parent = self.directory(path.parent)
        if parent is None:
            return False
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True

    def read(self, path: Path, limit: int, *, private: bool = True) -> bytes:
        parent = self.directory(path.parent)
        if parent is None:
            raise FileNotFoundError
        self.verify()
        before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        self._regular(before, private)
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            self._regular(opened, private)
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise StateIOError("file changed while opening")
            raw = stream.read(limit + 1)
            linked = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            self._regular(linked, private)
            if (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino):
                raise StateIOError("file changed during reading")
        self.verify()
        if len(raw) > limit:
            raise StateIOError("file exceeds resource limit")
        return raw

    @staticmethod
    def _regular(info: os.stat_result, private: bool) -> None:
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise StateIOError("unsafe regular file")
        if private and stat.S_IMODE(info.st_mode) != 0o600:
            raise StateIOError("file is not private")

    def prepare(self) -> None:
        # Inspect both ignores before creating anything, including the lock.
        if self.exists(self.private / "state.json.lock"):
            # Our bootstrap creates all three directories before the lock.
            # An incomplete layout with a lock is forensic, never repaired.
            if any(self.directory(path) is None for path in
                   (self.root / ".autopilot", self.private, self.actors)):
                raise StateIOError("incomplete private layout")
            self.verify()
            return
        try:
            self.check_ignores()
        except (StateIOError, OSError):
            # A concurrent bootstrap can acquire its lock after our check.
            # Defer ignore inspection to that lock without creating paths.
            if self.exists(self.private / "state.json.lock"):
                return self.prepare()
            raise
        for path in (self.root / ".autopilot", self.private, self.actors):
            self.directory(path, create=True)
        self.verify()
        # Establish the fixed inode with create-exclusive semantics before
        # concurrent StateStore opens add flock to that same inode.
        try:
            self.write_new(self.private / "state.json.lock", b"")
        except FileExistsError:
            pass

    def check_ignores(self) -> None:
        for parent in (self.root / ".autopilot", self.private):
            ignore = parent / ".gitignore"
            if self.exists(ignore) and self.read(ignore, 2) != b"*\n":
                raise StateIOError("incompatible private ignore")

    def prepare_ignores(self) -> None:
        self.check_ignores()
        for parent in (self.root / ".autopilot", self.private):
            ignore = parent / ".gitignore"
            if not self.exists(ignore):
                try:
                    self.write_new(ignore, b"*\n")
                except FileExistsError:
                    pass
            if self.read(ignore, 2) != b"*\n":
                raise StateIOError("incompatible private ignore")

    def write_new(self, path: Path, raw: bytes) -> None:
        self.verify()
        parent = self.directories[path.parent]
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.verify()
        os.fsync(parent)

    def publish(self, stage: Path, target: Path) -> None:
        self.verify()
        if self.exists(target):
            raise StateIOError("publication target already exists")
        os.replace(stage.name, target.name,
                   src_dir_fd=self.directories[stage.parent],
                   dst_dir_fd=self.directories[target.parent])
        self.verify()
        os.fsync(self.directories[target.parent])

    def remove(self, path: Path) -> None:
        self.verify()
        if self.exists(path):
            self.read(path, INTENT_LIMIT)
            os.unlink(path.name, dir_fd=self.directories[path.parent])


def read_public(path: Path, limit: int = 16777216) -> bytes:
    """Read installed metadata without traversing directory or file symlinks."""
    with PrivateLayout(Path("/")) as layout:
        return layout.read(path, limit, private=False)


def credential_descriptor(raw: bytes) -> dict:
    value = schema.decode_json(raw.decode("utf-8"), source="credential")
    if not isinstance(value, dict) or set(value) != CREDENTIAL_KEYS:
        raise BindingError("invalid credential")
    secret = value["secret"]
    if not isinstance(secret, str) or re.fullmatch(r"[A-Za-z0-9_-]{43}", secret) is None:
        raise BindingError("invalid credential")
    descriptor = {key: item for key, item in value.items() if key != "secret"}
    descriptor["secret_digest"] = digest(secret.encode("utf-8"))
    schema._actor(descriptor)
    return descriptor


def authenticate(path: Path | None, descriptor: dict, layout: PrivateLayout) -> None:
    try:
        if path is None:
            raise BindingError("credential required")
        supplied = credential_descriptor(layout.read(path.absolute(), 65536))
        expected = dict(descriptor)
        supplied_digest = supplied.pop("secret_digest")
        expected_digest = expected.pop("secret_digest")
        if supplied != expected or not hmac.compare_digest(supplied_digest, expected_digest):
            raise BindingError("credential mismatch")
    except (OSError, StateIOError, ValueError, UnicodeError) as error:
        raise BindingError("credential rejected") from error


def verify_operator(layout: PrivateLayout, current: dict) -> None:
    descriptor = next((row for row in current["actors"].values()
                       if row["role"] == "operator"), None)
    if descriptor is None:
        raise StateIOError("current operator missing")
    try:
        authenticate(layout.actors / "operator.json", descriptor, layout)
    except BindingError as error:
        raise StateIOError("current operator credential unavailable") from error


def admit(candidate: dict, response: dict) -> dict:
    candidate = schema.validate_state(candidate)
    stored = (json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True)
              + "\n").encode("utf-8")
    if len(stored) > NORMAL_STATE_LIMIT or len(candidate["receipts"]) > 4094:
        raise StateIOError("normal capacity exhausted")
    if len(canonical(response)) > 65536:
        raise StateIOError("response exceeds resource limit")
    return candidate


def prepare_bootstrap(request: dict, layout: PrivateLayout, response: dict) -> dict:
    workflow_id = response["result"]["workflow_id"]
    actor_id = response["result"]["actor_id"]
    credential = {"actor_id": actor_id, "project_id": request["project_id"],
                  "workflow_id": workflow_id, "role": "operator", "lease_epoch": 0,
                  "native_session_id": None, "secret": secrets.token_urlsafe(32)}
    raw = canonical(credential)
    descriptor = credential_descriptor(raw)
    receipt = {"request_digest": digest(canonical(request)),
               "authorizing_actor": descriptor, "response": response}
    candidate = schema.new_state(repo_root=layout.root, project_id=request["project_id"],
                                 workflow_id=workflow_id)
    candidate["actors"] = {actor_id: descriptor}
    candidate["receipts"] = {request["request_id"]: receipt}
    candidate = admit(candidate, response)
    intent = {"version": 1, "request": request, "request_digest": receipt["request_digest"],
              "old_revision": None, "old_state_digest": None, "old_actor": None,
              "candidate": candidate, "response": response, "receipt": receipt,
              "new_actor": descriptor, "stage": f".operator-{secrets.token_hex(16)}.stage",
              "final": "operator.json", "credential_digest": digest(raw)}
    validate_intent(intent, layout)
    encoded = canonical(intent)
    if len(encoded) > INTENT_LIMIT:
        raise StateIOError("intent exceeds resource limit")
    layout.write_new(layout.actors / intent["stage"], raw)
    temporary = layout.private / f".intent-{secrets.token_hex(16)}.tmp"
    layout.write_new(temporary, encoded)
    layout.publish(temporary, layout.private / "credential-intent.json")
    return intent


def validate_intent(intent: object, layout: PrivateLayout) -> dict:
    if not isinstance(intent, dict) or set(intent) != INTENT_KEYS:
        raise StateIOError("invalid bootstrap intent")
    if type(intent["version"]) is not int or intent["version"] != 1:
        raise StateIOError("invalid bootstrap intent")
    if any(intent[key] is not None for key in ("old_revision", "old_state_digest", "old_actor")):
        raise StateIOError("invalid bootstrap predecessor")
    candidate = admit(intent["candidate"], intent["response"])
    request, descriptor = intent["request"], intent["new_actor"]
    actor_id = descriptor["actor_id"]
    project_id = digest(str(layout.root).encode("utf-8"))
    response = {"ok": True, "revision": 0, "error_code": None, "retryable": False,
                "result": {"workflow_id": candidate["workflow_id"], "actor_id": actor_id,
                           "actor_file": str(layout.actors / "operator.json"), "lease_epoch": 0}}
    receipt = {"request_digest": digest(canonical(request)),
               "authorizing_actor": descriptor, "response": response}
    if (candidate["repo_root"] != str(layout.root) or candidate["project_id"] != project_id
            or candidate["revision"] != 0 or candidate["lease_epoch"] != 0
            or candidate["owner"] is not None or descriptor["role"] != "operator"
            or candidate["actors"] != {actor_id: descriptor}
            or candidate["receipts"] != {request["request_id"]: receipt}
            or intent["response"] != response or intent["receipt"] != receipt
            or intent["request_digest"] != receipt["request_digest"]
            or request["project_id"] != project_id
            or any(request[key] is not None for key in ("workflow_id", "actor_id", "lease_epoch", "job_id"))
            or request["operation"] != "workflow.open" or request["expected_revision"] != 0
            or request["payload"] != {} or intent["final"] != "operator.json"):
        raise StateIOError("inconsistent bootstrap intent")
    if (not isinstance(intent["stage"], str) or re.fullmatch(
            r"\.operator-[0-9a-f]{32}\.stage", intent["stage"]) is None):
        raise StateIOError("unsafe stage path")
    schema._digest(intent["credential_digest"])
    return intent


def read_intent(layout: PrivateLayout) -> dict | None:
    path = layout.private / "credential-intent.json"
    if not layout.exists(path):
        return None
    raw = layout.read(path, INTENT_LIMIT)
    return validate_intent(schema.decode_json(raw.decode("utf-8"), source="intent"), layout)


def verify_credential(layout: PrivateLayout, path: Path, intent: dict) -> None:
    raw = layout.read(path, 65536)
    if (not hmac.compare_digest(digest(raw), intent["credential_digest"])
            or credential_descriptor(raw) != intent["new_actor"]):
        raise StateIOError("bootstrap credential does not match intent")


def finish_bootstrap(intent: dict, layout: PrivateLayout, store: StateStore,
                     current: dict | None) -> dict:
    validate_intent(intent, layout)
    candidate = intent["candidate"]
    if current is not None and current != candidate:
        raise StateIOError("state does not match bootstrap intent")
    final, stage = layout.actors / intent["final"], layout.actors / intent["stage"]
    if layout.exists(final):
        verify_credential(layout, final, intent)
        if layout.exists(stage):
            verify_credential(layout, stage, intent)
    else:
        if current is not None:
            raise StateIOError("committed bootstrap credential missing")
        verify_credential(layout, stage, intent)
        layout.publish(stage, final)
    verify_credential(layout, final, intent)
    previous_hook = store._boundary_hook

    def guard(unused: object) -> None:
        layout.verify()
        verify_credential(layout, final, intent)

    try:
        store._boundary_hook = guard
        if current is None:
            store._initialize_locked(candidate)
        guard(None)
    finally:
        store._boundary_hook = previous_hook
    layout.remove(stage)
    os.fsync(layout.directories[layout.actors])
    layout.remove(layout.private / "credential-intent.json")
    os.fsync(layout.directories[layout.private])
    return intent["response"]
