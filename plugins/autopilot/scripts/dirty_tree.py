#!/usr/bin/env python3
"""Working-tree dirt checks: everything that decides whether a repo's state
outside the project-management store counts as dirty, for the gate checks
and the ancestor-and-clean reuse check. Git reads only, never writes."""

from __future__ import annotations

import posixpath
import subprocess
from pathlib import Path

STORE_PREFIX = "docs/dev/project-management/"

# Dirty paths under these roots never refuse a record: the store, plus the
# agents' scratch dir, which a repo need not gitignore.
STORE_PREFIXES = (STORE_PREFIX, "docs/dev/tmp/")


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _dirty_path_is_in_store(
    new_path: str,
    old_path: str | None,
    store: str | tuple[str, ...],
) -> bool:
    """A porcelain -z status record's store check: the path field
    (and the second, source path field when the record is a rename/copy)
    must both be under `store`, or the record counts as dirty outside
    the store. Crossing the store boundary in either direction is dirty."""
    paths = (new_path, old_path) if old_path else (new_path,)
    return all(p.startswith(store) for p in paths)


def _iter_porcelain_z_records(raw: str) -> list[tuple[str, str | None]]:
    """Splits `git status --porcelain=1 -z` output into (path, source_path)
    pairs. XY is always two status-code bytes (either may be blank); a
    rename/copy record (R or C in EITHER column) carries a second,
    NUL-terminated source-path field."""
    fields = raw.split("\0")
    records = []
    i = 0
    while i < len(fields) and fields[i]:
        field = fields[i]
        code, path = field[:2], field[3:]
        if code[0] in "RC" or code[1] in "RC":
            i += 1
            records.append((path, fields[i]))
        else:
            records.append((path, None))
        i += 1
    return records


def _ancestor_and_clean(repo_root: Path, sha: str, head_sha: str) -> bool:
    """True iff `sha` is an ancestor of `head_sha`, every path in the
    endpoint diff `git diff --name-only --no-renames -z <sha> <head_sha>`
    is under STORE_PREFIX, no tracked symlink outside the store names a
    changed or dirty store path, and nothing is dirty outside the store."""
    if _git(repo_root, "merge-base", "--is-ancestor", sha, head_sha).returncode != 0:
        return False
    # Git paths are toplevel-relative; repo_root may sit below the toplevel.
    prefix = _git(repo_root, "rev-parse", "--show-prefix")
    if prefix.returncode != 0:
        return False
    store = prefix.stdout.strip() + STORE_PREFIX
    diff = _git(repo_root, "diff", "--name-only", "--no-renames", "-z", sha, head_sha)
    if diff.returncode != 0:
        return False
    paths = [p for p in diff.stdout.split("\0") if p]
    if not all(path.startswith(store) for path in paths):
        return False
    if _store_symlink_targets_changed(repo_root, paths):
        return False
    if _store_symlink_targets_changed(repo_root, _dirty_store_paths(repo_root)):
        return False
    return not _dirty_outside_store(repo_root)


class _GitProbeFailed(OSError):
    """A git call in the dirt probe exited non-zero (non-git cwd and the
    like); an OSError so `_dirty_outside_store` counts it as dirty."""


def _store_roots(repo_root: Path) -> tuple[str, ...]:
    """Toplevel-relative store roots: `git rev-parse --show-prefix` joined
    with each of STORE_PREFIXES. Raises `_GitProbeFailed` on a git failure."""
    prefix = _git(repo_root, "rev-parse", "--show-prefix")
    if prefix.returncode != 0:
        raise _GitProbeFailed("git rev-parse --show-prefix failed")
    return tuple(prefix.stdout.strip() + root for root in STORE_PREFIXES)


def _dirty_store_paths(repo_root: Path) -> list[str]:
    """Toplevel-relative paths of every porcelain status record path that
    lies under the store roots (the inverse of `_dirty_outside_store_paths`);
    a rename/copy contributes each of its paths that is in the store.
    Raises `_GitProbeFailed` on a git failure."""
    store = _store_roots(repo_root)
    status = _git(repo_root, "status", "--porcelain=1", "-z", "--untracked-files=all")
    if status.returncode != 0:
        raise _GitProbeFailed("git status failed")
    return [
        p
        for new, old in _iter_porcelain_z_records(status.stdout)
        for p in (new, old)
        if p and _dirty_path_is_in_store(p, None, store)
    ]


def _store_symlink_targets_changed(repo_root: Path, store_paths: list[str]) -> bool:
    """True iff `_store_symlink_hits` finds a tracked symlink for `store_paths`."""
    return bool(_store_symlink_hits(repo_root, store_paths))


def _store_symlink_hits(repo_root: Path, store_paths: list[str]) -> list[str]:
    """Toplevel-relative paths of the tracked symlinks outside the store
    whose blob target, resolved against the link's own directory, names one
    of `store_paths` (all toplevel-relative) or a directory above one.
    Absolute targets and symlink chains are taken at face value. Raises
    `_GitProbeFailed` on a git failure."""
    if not store_paths:
        return []
    store = _store_roots(repo_root)
    listing = _git(repo_root, "ls-files", "-s", "-z", "--full-name")
    if listing.returncode != 0:
        raise _GitProbeFailed("git ls-files failed")
    hits = []
    for entry in listing.stdout.split("\0"):
        if not entry:
            continue
        meta, link = entry.split("\t", 1)
        mode, blob, _stage = meta.split()
        if mode != "120000" or link.startswith(store):
            continue
        raw = _git(repo_root, "cat-file", "-p", blob)
        if raw.returncode != 0:
            raise _GitProbeFailed("git cat-file failed")
        target = posixpath.normpath(posixpath.join(posixpath.dirname(link), raw.stdout))
        # "." is the repo root: every store path is beneath it, but none
        # literally starts with "./", so it needs its own branch.
        if target == "." or any(
            p == target or p.startswith(target + "/") for p in store_paths
        ):
            hits.append(link)
    return hits


def _dirty_outside_store_paths(
    repo_root: Path,
    extra_excluded: tuple[str, ...] = (),
) -> list[str]:
    """Sorted, deduplicated paths of every porcelain status record outside
    the store roots, [] when clean. `extra_excluded` holds TOPLEVEL-relative
    POSIX file paths, used as given and matched exactly, never as prefixes.
    A rename/copy record contributes both of its paths. Catches nothing: a
    failing git call raises `_GitProbeFailed` (an OSError), never `[]`."""
    store = _store_roots(repo_root)
    status = _git(repo_root, "status", "--porcelain=1", "-z", "--untracked-files=all")
    if status.returncode != 0:
        raise _GitProbeFailed("git status failed")
    offending = set()
    for new, old in _iter_porcelain_z_records(status.stdout):
        excused = all(p in extra_excluded for p in (new, old) if p)
        if not excused and not _dirty_path_is_in_store(new, old, store):
            offending.update(p for p in (new, old) if p)
    offending.update(_hidden_flag_edits(repo_root, store))
    # A dirty store file that a tracked product symlink names is product dirt.
    store_dirt = [p for p in _dirty_store_paths(repo_root) if p not in extra_excluded]
    offending.update(_store_symlink_hits(repo_root, store_dirt))
    return sorted(offending)


def _hidden_flag_edits(repo_root: Path, store: tuple[str, ...]) -> list[str]:
    """Toplevel-relative paths outside `store` whose index entry carries the
    skip-worktree or assume-unchanged flag. Either flag alone is dirt: both
    hide the path from `git status`, so its on-disk content can never be
    trusted to match the index blob. Raises `_GitProbeFailed` when a git
    call fails."""
    top = _git(repo_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise _GitProbeFailed("git rev-parse --show-toplevel failed")
    toplevel = Path(top.stdout.strip())
    listing = _git(toplevel, "ls-files", "-v", "-s", "-z")
    if listing.returncode != 0:
        raise _GitProbeFailed("git ls-files failed")
    flagged = []
    for entry in listing.stdout.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        tag, _mode, _blob, _stage = meta.split()
        # "S" is skip-worktree; a lowercase tag is assume-unchanged.
        if (tag == "S" or tag.islower()) and not path.startswith(store):
            flagged.append(path)
    return flagged


def _dirty_outside_store(
    repo_root: Path,
    extra_excluded: tuple[str, ...] = (),
) -> bool:
    """True iff the working tree has any change outside the store roots,
    or the git calls themselves fail (fail toward refusing the record)."""
    try:
        return bool(_dirty_outside_store_paths(repo_root, extra_excluded))
    except OSError:
        return True


def _dirty_check(cwd: Path, extra_excluded: tuple[str, ...]) -> tuple[bool, list[str]]:
    """(dirty, dirty_paths). A failing git probe is dirty with no path."""
    try:
        paths = _dirty_outside_store_paths(cwd, extra_excluded)
    except OSError:
        return True, []
    return bool(paths), paths


def _log_rel_and_tracked(cwd: Path, log_path: Path | None) -> tuple[str, bool] | None:
    """(toplevel-relative POSIX path of `log_path`, whether it is tracked
    there), when `log_path` resolves inside cwd's git toplevel; None when
    there is no log, it resolves outside the toplevel, or any git call
    fails."""
    if log_path is None:
        return None
    try:
        top = _git(cwd, "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return None
        toplevel = Path(top.stdout.strip())
        rel = log_path.resolve().relative_to(toplevel.resolve()).as_posix()
        tracked = _git(toplevel, "ls-files", "-z", "--", ":(literal)" + rel)
    except (OSError, ValueError):
        return None
    if tracked.returncode != 0:
        return None
    # Exact entry match: a directory holding tracked files is not tracked.
    return rel, rel in tracked.stdout.split("\0")


def _untracked_log_exclusion(cwd: Path, log_path: Path | None) -> tuple[str, ...]:
    """`(toplevel-relative POSIX path of log_path,)` when the log resolves
    inside cwd's git toplevel and is NOT tracked there; `()` otherwise.
    A tracked log is never excused: its edits stay dirt."""
    resolved = _log_rel_and_tracked(cwd, log_path)
    if resolved is None:
        return ()
    rel, tracked = resolved
    return () if tracked else (rel,)
