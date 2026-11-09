"""Locked, durable controller state storage.

Adapted from OVCAQ src/ovcaq/state/store.py at cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7.

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

import copy
import errno
import fcntl
import json
import os
import stat
import secrets
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from pathlib import Path

from autopilot_state import schema

type State = dict

type Mutator = Callable[[State], State | None]
type Precondition = Callable[[State], None]
type BoundaryHook = Callable[[DurabilityBoundary], None]


class StateError(Exception):
    """Base class for state-store failures."""


class StateIOError(StateError):
    """Raised when state bytes cannot be read or durably published."""


class StateResourceLimitError(StateIOError):
    """Raised when stored state exceeds its byte limit."""


class StateExistsError(StateError):
    """Raised when create-only initialization finds existing state."""


class BackupError(StateError):
    """Raised when the rollback candidate is missing or invalid."""


class FutureSchemaError(StateError):
    """Raised when durable state uses a newer schema version."""


class RevisionConflictError(StateError):
    """Raised when an expected revision does not match durable state."""


class DurabilityUnsupportedError(StateIOError):
    """Raised when the filesystem cannot honor a durability operation."""


class DurabilityBoundary(StrEnum):
    BACKUP_TEMP_FSYNCED = "backup_temp_fsynced"
    BACKUP_REPLACED = "backup_replaced"
    BACKUP_DIR_FSYNCED = "backup_dir_fsynced"
    STATE_TEMP_FSYNCED = "state_temp_fsynced"
    STATE_REPLACED = "state_replaced"
    STATE_DIR_FSYNCED = "state_dir_fsynced"


def _canonical_bytes(state: State) -> bytes:
    encoded = (
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if len(encoded) > schema.MAX_STATE_BYTES:
        raise schema.ResourceLimitError(
            f"state: canonical stored document exceeds {schema.MAX_STATE_BYTES} bytes"
        )
    return encoded


class StateStore:
    def __init__(
        self,
        path: Path,
        *,
        boundary_hook: BoundaryHook | None = None,
    ) -> None:
        self._path = path
        self._lock_path = path.with_name(f"{path.name}.lock")
        self._backup_path = path.with_name(f"{path.name}.bak")
        self._boundary_hook = boundary_hook
        self._directory_fd: ContextVar[int] = ContextVar("state_directory_fd")

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> State:
        with self._locked(exclusive=False):
            return self._read_locked()

    def _read_locked(self) -> State:
        return self._decode_state(self._read_bytes(self._path))

    def initialize(self, initial: State) -> State:
        with self._locked(exclusive=True):
            return self._initialize_locked(initial)

    def _initialize_locked(self, initial: State) -> State:
        validated = schema.validate_state(initial)
        if type(validated["revision"]) is not int or validated["revision"] != 0:
            raise StateError("revision: initialization requires revision 0")
        if self._artifact_exists(self._path):
            raise StateExistsError(f"state already exists: {self._path}")
        self._publish_bytes(
            self._path, _canonical_bytes(validated),
            temp_boundary=DurabilityBoundary.STATE_TEMP_FSYNCED,
            replaced_boundary=DurabilityBoundary.STATE_REPLACED,
            directory_boundary=DurabilityBoundary.STATE_DIR_FSYNCED,
            create_only=True,
        )
        return validated

    def transaction(
        self, mutator: Mutator, *, expected_revision: int | None = None,
        publication_guard: Callable[[], None] | None = None,
    ) -> State:
        with self._locked(exclusive=True):
            return self._transaction_locked(
                mutator, expected_revision=expected_revision,
                publication_guard=publication_guard,
            )

    def _transaction_locked(
        self, mutator: Mutator, *, expected_revision: int | None = None,
        publication_guard: Callable[[], None] | None = None,
    ) -> State:
        current_raw = self._read_bytes(self._path)
        current = self._decode_state(current_raw)
        self._check_revision(current, expected_revision)
        previous_backup = self._snapshot(self._backup_path)
        candidate = copy.deepcopy(current)
        replacement = mutator(candidate)
        proposed = candidate if replacement is None else copy.deepcopy(replacement)
        if isinstance(proposed, dict):
            proposed["revision"] = current["revision"] + 1
        committed = schema.validate_state(proposed)
        state_bytes = _canonical_bytes(committed)
        if publication_guard is not None:
            publication_guard()
        self._commit_pair(
            backup_bytes=current_raw, state_bytes=state_bytes,
            old_state=current_raw, old_backup=previous_backup,
            publication_guard=publication_guard,
        )
        return committed

    def restore(
        self, *, expected_revision: int | None = None,
        precondition: Precondition | None = None,
    ) -> State:
        with self._locked(exclusive=True):
            return self._restore_locked(
                expected_revision=expected_revision, precondition=precondition,
            )

    def _restore_locked(
        self, *, expected_revision: int | None = None,
        precondition: Precondition | None = None,
    ) -> State:
        current_raw = self._read_bytes(self._path)
        current = self._decode_state(current_raw)
        self._check_revision(current, expected_revision)
        backup_raw = self._read_backup()
        try:
            restored = self._decode_state(backup_raw)
        except (schema.SchemaError, StateError) as error:
            raise BackupError(f"invalid backup {self._backup_path}: {error}") from error
        if precondition is not None:
            precondition(copy.deepcopy(current))
        if self._intent_exists() or any(
            current[key] != restored[key]
            for key in ("lease_epoch", "owner", "actors", "receipts")
        ):
            raise BackupError("restore cannot change security state or pending credentials")
        restored["revision"] = current["revision"] + 1
        committed = schema.validate_state(restored)
        self._commit_pair(
            backup_bytes=current_raw, state_bytes=_canonical_bytes(committed),
            old_state=current_raw, old_backup=backup_raw,
        )
        return committed

    def _intent_exists(self) -> bool:
        try:
            os.stat("credential-intent.json", dir_fd=self._directory_fd.get(),
                    follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True

    @contextmanager
    def _locked(self, *, exclusive: bool) -> Iterator[None]:
        directory = descriptor = -1
        token = None
        try:
            directory = os.open(self._path.parent, os.O_RDONLY | os.O_DIRECTORY)
            token = self._directory_fd.set(directory)
            self._verify_directory()
            descriptor = self._open_lock()
            fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            self._verify_directory()
            self._verify_open_artifact(self._lock_path, descriptor, "state lock")
            yield
        except OSError as error:
            raise StateIOError(f"state lock failed {self._lock_path}: {error}") from error
        finally:
            if descriptor >= 0:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
            if token is not None:
                self._directory_fd.reset(token)
            if directory >= 0:
                os.close(directory)

    def _open_lock(self) -> int:
        self._reject_aliased_artifact(self._lock_path, "state lock")
        descriptor = os.open(
            self._lock_path.name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600, dir_fd=self._directory_fd.get(),
        )
        try:
            self._verify_open_artifact(self._lock_path, descriptor, "state lock")
            os.fchmod(descriptor, 0o600)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    def _verify_directory(self) -> None:
        opened = os.fstat(self._directory_fd.get())
        linked = os.stat(self._path.parent)
        if (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino):
            raise StateIOError("state directory changed during operation")

    def _check_revision(self, state: State, expected: int | None) -> None:
        if expected is not None and (type(expected) is not int or expected < 0):
            raise StateError("expected revision must be a nonnegative integer")
        if expected is not None and state["revision"] != expected:
            raise RevisionConflictError(
                f"revision conflict: expected {expected}, found {state['revision']}"
            )

    def _read_bytes(self, path: Path) -> bytes:
        descriptor = -1
        try:
            self._reject_aliased_artifact(path, "state artifact")
            descriptor = os.open(
                path.name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=self._directory_fd.get(),
            )
            self._verify_open_artifact(path, descriptor, "state artifact")
            chunks: list[bytes] = []
            remaining = schema.MAX_STATE_BYTES + 1
            while remaining > 0:
                chunk = os.read(descriptor, min(remaining, 64 * 1024))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        except OSError as error:
            detail = " is a symlink" if error.errno == errno.ELOOP else f": {error}"
            raise StateIOError(f"cannot read state {path}{detail}") from error
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if len(raw) > schema.MAX_STATE_BYTES:
            raise StateResourceLimitError(
                f"state exceeds {schema.MAX_STATE_BYTES} bytes: {path}"
            )
        return raw

    def _read_backup(self) -> bytes:
        try:
            return self._read_bytes(self._backup_path)
        except StateIOError as error:
            raise BackupError(
                f"cannot read backup {self._backup_path}: {error}"
            ) from error

    def _decode_state(self, raw: bytes) -> State:
        try:
            text = raw.decode("utf-8")
            value = schema.decode_json(text, source="state")
        except schema.ResourceLimitError as error:
            raise StateResourceLimitError(str(error)) from error
        except (
            UnicodeDecodeError,
            ValueError,
        ) as error:
            raise StateIOError(f"invalid state JSON: {error}") from error
        if isinstance(value, dict):
            version = value.get("schema_version")
            if (
                isinstance(version, int)
                and not isinstance(version, bool)
                and version > schema.SCHEMA_VERSION
            ):
                raise FutureSchemaError(
                    f"schema_version {version} is newer than {schema.SCHEMA_VERSION}"
                )
        return schema.validate_state(value)

    def _commit_pair(
        self,
        *,
        backup_bytes: bytes,
        state_bytes: bytes,
        old_state: bytes,
        old_backup: bytes | None,
        publication_guard: Callable[[], None] | None = None,
    ) -> None:
        try:
            self._verify_directory()
            self._publish_bytes(
                self._backup_path,
                backup_bytes,
                temp_boundary=DurabilityBoundary.BACKUP_TEMP_FSYNCED,
                replaced_boundary=DurabilityBoundary.BACKUP_REPLACED,
                directory_boundary=DurabilityBoundary.BACKUP_DIR_FSYNCED,
                publication_guard=publication_guard,
            )
            self._publish_bytes(
                self._path,
                state_bytes,
                temp_boundary=DurabilityBoundary.STATE_TEMP_FSYNCED,
                replaced_boundary=DurabilityBoundary.STATE_REPLACED,
                directory_boundary=DurabilityBoundary.STATE_DIR_FSYNCED,
                publication_guard=publication_guard,
            )
        except BaseException:
            if (
                self._snapshot(self._path) != old_state
                or self._snapshot(self._backup_path) != old_backup
            ):
                self._repair(old_state=old_state, old_backup=old_backup)
            raise

    def _publish_bytes(
        self,
        target: Path,
        data: bytes,
        *,
        temp_boundary: DurabilityBoundary,
        replaced_boundary: DurabilityBoundary,
        directory_boundary: DurabilityBoundary,
        create_only: bool = False,
        publication_guard: Callable[[], None] | None = None,
    ) -> None:
        created = False

        def mark_created() -> None:
            nonlocal created
            created = True

        def checked_boundary(boundary: DurabilityBoundary) -> None:
            self._boundary(boundary)
            if publication_guard is not None:
                publication_guard()

        try:
            self._replace_bytes(
                target,
                data,
                create_only=create_only,
                temp_fsynced=lambda: checked_boundary(temp_boundary),
                target_created=mark_created if create_only else None,
            )
            checked_boundary(replaced_boundary)
            self._fsync_directory(target.parent)
            checked_boundary(directory_boundary)
        except BaseException as error:
            if created:
                try:
                    os.unlink(target.name, dir_fd=self._directory_fd.get())
                except OSError as repair_error:
                    raise StateIOError(
                        f"cannot remove failed publication {target}: {repair_error}"
                    ) from repair_error
                self._fsync_directory(target.parent)
            if isinstance(error, OSError):
                raise StateIOError(f"cannot publish {target}: {error}") from error
            raise

    def _replace_bytes(
        self, target: Path, data: bytes, *, create_only: bool = False,
        temp_fsynced: Callable[[], None] | None = None,
        target_created: Callable[[], None] | None = None,
    ) -> None:
        descriptor = -1
        temp_name = None
        directory = self._directory_fd.get()
        try:
            self._reject_aliased_artifact(target, "state publication target")
            temp_name = f".{self._path.name}.autopilot-{secrets.token_hex(16)}.tmp"
            descriptor = os.open(
                temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=directory,
            )
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                descriptor = -1
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if temp_fsynced is not None:
                temp_fsynced()
            if create_only:
                try:
                    os.link(temp_name, target.name, src_dir_fd=directory,
                            dst_dir_fd=directory, follow_symlinks=False)
                except FileExistsError as error:
                    raise StateExistsError(f"state already exists: {target}") from error
                if target_created is not None:
                    target_created()
                os.unlink(temp_name, dir_fd=directory)
            else:
                os.replace(temp_name, target.name,
                           src_dir_fd=directory, dst_dir_fd=directory)
            temp_name = None
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temp_name is not None:
                try:
                    os.unlink(temp_name, dir_fd=directory)
                except FileNotFoundError:
                    pass

    def _repair(self, *, old_state: bytes, old_backup: bytes | None) -> None:
        self._replace_without_hook(self._path, old_state)
        if old_backup is None:
            try:
                if self._artifact_exists(self._backup_path):
                    os.unlink(self._backup_path.name, dir_fd=self._directory_fd.get())
            except OSError as error:
                raise StateIOError(
                    f"cannot remove repaired backup {self._backup_path}: {error}"
                ) from error
        else:
            self._replace_without_hook(self._backup_path, old_backup)
        self._fsync_directory(self._path.parent)

    def _replace_without_hook(self, target: Path, data: bytes) -> None:
        try:
            self._replace_bytes(target, data)
        except OSError as error:
            raise StateIOError(f"cannot repair {target}: {error}") from error

    def _snapshot(self, path: Path) -> bytes | None:
        try:
            if not self._artifact_exists(path):
                return None
            return self._read_bytes(path)
        except StateIOError as error:
            raise StateIOError(f"cannot snapshot {path}: {error}") from error

    def _artifact_exists(self, path: Path) -> bool:
        self._reject_aliased_artifact(path, "state artifact")
        try:
            os.stat(path.name, dir_fd=self._directory_fd.get(), follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError as error:
            raise StateIOError(
                f"cannot inspect state artifact {path}: {error}"
            ) from error
        return True

    def _reject_aliased_artifact(self, path: Path, label: str) -> None:
        try:
            artifact = os.stat(path.name, dir_fd=self._directory_fd.get(), follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as error:
            raise StateIOError(f"cannot inspect {label} {path}: {error}") from error
        if stat.S_ISLNK(artifact.st_mode):
            raise StateIOError(f"{label} is a symlink: {path}")
        if not stat.S_ISREG(artifact.st_mode):
            raise StateIOError(f"{label} is not a regular file: {path}")
        if artifact.st_nlink != 1:
            raise StateIOError(f"{label} has multiple hard links: {path}")

    def _verify_open_artifact(self, path: Path, descriptor: int, label: str) -> None:
        try:
            opened = os.fstat(descriptor)
            linked = os.stat(path.name, dir_fd=self._directory_fd.get(), follow_symlinks=False)
        except OSError as error:
            raise StateIOError(f"cannot verify {label} {path}: {error}") from error
        if stat.S_ISLNK(linked.st_mode):
            raise StateIOError(f"{label} is a symlink: {path}")
        if (opened.st_dev, opened.st_ino) != (linked.st_dev, linked.st_ino):
            raise StateIOError(f"{label} changed while opening: {path}")
        if not stat.S_ISREG(opened.st_mode):
            raise StateIOError(f"{label} is not a regular file: {path}")
        if opened.st_nlink != 1 or linked.st_nlink != 1:
            raise StateIOError(f"{label} has multiple hard links: {path}")

    def _fsync_directory(self, directory: Path) -> None:
        try:
            os.fsync(self._directory_fd.get())
        except OSError as error:
            if error.errno in {errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP}:
                raise DurabilityUnsupportedError(
                    f"directory fsync unsupported for {directory}: {error}"
                ) from error
            raise StateIOError(f"cannot fsync directory {directory}: {error}") from error

    def _boundary(self, boundary: DurabilityBoundary) -> None:
        if self._boundary_hook is not None:
            self._boundary_hook(boundary)
        self._verify_directory()
