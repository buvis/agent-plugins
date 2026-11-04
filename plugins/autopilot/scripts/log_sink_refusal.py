#!/usr/bin/env python3
"""The one place that decides whether `verify`'s log sink may be opened,
plus the descriptor-pinned opener that writes it. `refuse` is pure: git
and filesystem reads only, no printing."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from dirty_tree import STORE_PREFIX, _git, _log_rel_and_tracked

_OUTSIDE = "resolves outside the repository"


def refuse(log_path: Path, repo_root: Path) -> str | None:
    """The refusal reason for `log_path` as a log sink, or None when it may
    be opened. `log_path` must be the UNRESOLVED candidate: resolving it
    first would follow a symlink in its ancestry and hide it. Every probe is
    scoped to `repo_root`, never to cwd. First match wins. A path that does
    not exist yet is eligible."""
    toplevel = _toplevel(repo_root)
    if toplevel is None:
        return _OUTSIDE  # a failing git probe fails closed
    try:
        resolved = log_path.resolve()
    except RuntimeError:
        return "is a symlink"  # Python 3.12 raises on a symlink loop
    # Containment runs before any pointer-content read: a path that never
    # touches the repository is refused before `_identity_hit` can open it,
    # even though `_identity_hit` can only ever add a refusal, never clear one.
    if not resolved.is_relative_to(toplevel) or not resolved.is_relative_to(
        repo_root.resolve()
    ):
        return _OUTSIDE
    identity = _identity_hit(resolved, repo_root, toplevel)
    if identity is not None:
        return identity
    probe = _log_rel_and_tracked(repo_root, log_path)
    if probe is None:
        return _OUTSIDE  # a failing tracked-probe fails closed
    if probe[1]:
        return "is tracked"
    if _symlinked_component(log_path, repo_root, toplevel):
        return "is a symlink"
    if _in_nested_repo(resolved, toplevel):
        return _OUTSIDE
    try:
        st = os.lstat(resolved)
    except OSError:
        return None  # nothing on disk to inspect yet
    if not stat.S_ISREG(st.st_mode):
        return "is not a regular file"
    if st.st_mode & 0o111:
        return "is executable"
    if st.st_nlink > 1:
        return "has more than one hard link"
    return None


def _toplevel(repo_root: Path) -> Path | None:
    """`repo_root`'s git toplevel, resolved; None when the probe fails."""
    top = _git(repo_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return None
    return Path(top.stdout.strip()).resolve()


def _identity_targets(repo_root: Path) -> list[tuple[Path, str]]:
    """The directories the sink may not resolve inside, by inode identity:
    the store, and both spellings of the git directory (a worktree's own
    `--absolute-git-dir` and the shared `--git-common-dir`)."""
    targets = [(repo_root / STORE_PREFIX, "resolves inside the store")]
    for flag in ("--absolute-git-dir", "--git-common-dir"):
        probe = _git(repo_root, "rev-parse", flag)
        if probe.returncode == 0:
            # A relative answer joins onto repo_root; an absolute one
            # replaces it.
            targets.append(
                (
                    repo_root / probe.stdout.strip(),
                    "resolves inside the git directory",
                ),
            )
    return targets


def _identity_hit(resolved: Path, repo_root: Path, toplevel: Path) -> str | None:
    """The reason when ANY existing ancestor of `resolved` is one of
    `_identity_targets`, walking up to `toplevel` (or the filesystem root).
    The literal store-prefix check comes first: it still refuses a store
    path whose directory does not exist yet."""
    if resolved.is_relative_to((repo_root / STORE_PREFIX).resolve()):
        return "resolves inside the store"
    targets = _identity_targets(repo_root)
    # Only the supplied repository's own pointer is read, never a nested one's.
    pointer = _worktree_gitdir_pointer(resolved) if resolved.parent == toplevel else None
    if pointer is not None:
        for target, reason in targets:
            try:
                if os.path.samefile(pointer, target):
                    return reason
            except OSError:
                continue  # one of the two does not exist
    current = resolved.parent
    while True:
        for target, reason in targets:
            try:
                if os.path.samefile(current, target):
                    return reason
            except OSError:
                continue  # one of the two does not exist
        if current == toplevel or current.parent == current:
            return None
        current = current.parent


def _worktree_gitdir_pointer(resolved: Path) -> Path | None:
    """The target of a linked worktree's `.git` FILE (`gitdir: <path>`), or
    None when `resolved` is not such a file. The file is itself the
    candidate sink, so it is checked by what it points at. Only the actual
    `.git` file is read: any other candidate is refused or accepted by location,
    never by its content."""
    try:
        if not resolved.samefile(resolved.parent / ".git"):
            return None
        if not stat.S_ISREG(os.lstat(resolved).st_mode):
            return None
        text = resolved.read_text()
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("gitdir:"):
        return None
    return resolved.parent / text.split(":", 1)[1].strip()


def _symlinked_component(log_path: Path, repo_root: Path, toplevel: Path) -> bool:
    """True iff any component of the UNRESOLVED `log_path` BELOW the
    repository is a symlink (the final component included). A component is
    below the repository exactly when its own parent resolves inside it; the
    walk stops at the first component whose parent resolves outside (the
    root itself or a root alias). A symlink in the repository's own ancestry
    (macOS `/tmp`, a root alias) is not the sink's, while one below the root
    always is, at any depth."""
    stops = (repo_root, repo_root.resolve(), toplevel)
    current = log_path
    while current not in stops and current.parent != current:
        try:
            inside = current.parent.resolve().is_relative_to(repo_root.resolve())
        except OSError:
            inside = False
        if not inside:
            break
        if os.path.islink(current):
            return True
        current = current.parent
    return False


def _in_nested_repo(resolved: Path, toplevel: Path) -> bool:
    """True iff `resolved` lives in a second repository nested inside
    `toplevel`'s working tree, probed from the nearest existing ancestor
    (a directory not created yet inherits its nearest existing ancestor's
    repository). Git's "must be run in a work tree" failure can only come
    from another repo's git internals here (this repo's `.git` was ruled out
    above), so it counts as nested."""
    nearest = resolved.parent
    while not nearest.is_dir() and nearest.parent != nearest:
        nearest = nearest.parent
    try:
        probe = _git(nearest, "rev-parse", "--show-toplevel")
    except OSError:
        return False
    if probe.returncode != 0:
        return "work tree" in probe.stderr
    return Path(probe.stdout.strip()).resolve() != toplevel


def _pinned_parent_fd(parent: Path, root: Path) -> int:
    """A descriptor for `parent`, opened without following a symlink at any
    level below `root`: every component beneath `root` is taken one at a
    time with `O_DIRECTORY | O_NOFOLLOW`. `root` itself is trusted (a repo
    reached through a symlinked ancestor is normal)."""
    try:
        names = parent.relative_to(root).parts
    except ValueError:
        try:
            names = parent.resolve().relative_to(root.resolve()).parts
        except ValueError as exc:
            # Raised as OSError, before `root` is opened, so no fd leaks.
            raise OSError(f"{parent} is not under {root}") from exc
    parent_fd = os.open(root.resolve(), os.O_DIRECTORY)
    for name in names:
        try:
            parent_fd = _descend(parent_fd, name)
        except OSError:
            os.close(parent_fd)
            raise
    return parent_fd


def _descend(parent_fd: int, name: str) -> int:
    """`name`'s directory descriptor, opened relative to `parent_fd` and
    created there first when missing (a symlinked one fails the reopen).
    Closes `parent_fd` once replaced; leaves it open when either step
    raises."""
    try:
        os.mkdir(name, dir_fd=parent_fd)
    except FileExistsError:
        pass
    next_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    os.close(parent_fd)
    return next_fd


def _open_log_sink(log_path: Path, root: Path, *, preserve: bool = False):
    """Opens `log_path` for an unbuffered binary write without following a
    symlink at any level below `root`. By default the leaf is REPLACED: an
    existing file (a symlink included, whose target is never touched) is
    unlinked and a fresh regular file is created exclusively, mode 0o666.
    With `preserve=True` an EXISTING leaf is opened without creating it and
    without changing a byte, and the OPENED inode must be a regular file
    with one hard link and no execute bit, or the open raises OSError. The
    leaf is opened relative to a pinned parent descriptor, so a symlink swap
    of the pathname cannot redirect the open and a raced FIFO cannot block
    it."""
    parent_fd = _pinned_parent_fd(log_path.parent, root)
    try:
        if preserve:
            sink_fd = os.open(
                log_path.name,
                os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=parent_fd,
            )
        else:
            try:
                os.unlink(log_path.name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            # 0o666 like builtin `open`; os.open's 0o777 default would leave
            # the sink executable.
            sink_fd = os.open(
                log_path.name,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o666,
                dir_fd=parent_fd,
            )
    finally:
        os.close(parent_fd)
    if preserve:
        try:
            os.set_blocking(sink_fd, True)
            info = os.fstat(sink_fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o111:
                raise OSError(f"{log_path} must be a plain regular file with one hard link")
        except BaseException:
            os.close(sink_fd)
            raise
    return os.fdopen(sink_fd, "wb", buffering=0)
