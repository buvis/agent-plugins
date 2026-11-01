"""Classify a review's HIGH/CRITICAL findings as regressions introduced by the
rework range `previous_head..head`, and capture a custody commit range.

Port of the pinned `cli/cap_check.py` plus custody's `capture_range`. The
heads are explicit arguments; nothing is read from frontmatter, evidence or
live state. Every git call runs at the toplevel of `repo_root` with a
30-second timeout. A File cell git cannot resolve at head makes its row
`regression: None` (a stall), never a clean `False` (a deferral).
Stdlib only.
"""

from __future__ import annotations

import os
import posixpath
import re
import subprocess
from pathlib import Path

from findings import reviewed_rows

GIT_TIMEOUT_SECS = 30
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

_FILE_LINE_RE = re.compile(r"^(.*):(\d+(?:[-,]\d+)*)$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_BASE_RE = re.compile(r"[0-9a-f]{40}")
# A trailing parenthesised note, one nesting level deep.
_ANNOTATION_RE = re.compile(r"\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*$")
# ';' and a backticked path after whitespace always split; ',' splits only
# when whitespace follows and the next non-space char is not a digit, so
# `a.py:3,9` stays one segment for _FILE_LINE_RE's comma list and `a,b.py`
# stays one path.
_NOTE_RE = re.compile(r"\s+\((?:[^()]|\([^()]*\))*\)")
_SPLIT_RE = re.compile(r";|\s+(?=`)|,(?=\s)(?!\s*\d)")
_HASH_L_RE = re.compile(r"^(.*)#[Ll](\d+)(?:-[Ll]?(\d+))?$")
_COLON_L_RE = re.compile(r"^(.*?):\s*[Ll]\s*(\d+)(?:-[Ll]?(\d+))?$")
# `path:N`, `path: N`, `path:N-M`; the comma list falls through to _FILE_LINE_RE.
_COLON_RANGE_RE = re.compile(r"^(.*?):\s*(\d+)(?:\s*-\s*(\d+))?$")


class CapCheckError(RuntimeError):
    """Review text could not be parsed, or git could not prove or diff the
    range. `.stderr` carries git's raw stderr for a failed git call, else "";
    missing-path detection inspects only this field, never the message."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


def _git(cwd: str | Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT_SECS,
            env={**os.environ, "LC_ALL": "C", "LANGUAGE": "C"},
        )
    except subprocess.CalledProcessError as err:
        stderr = err.stderr.strip() if err.stderr else ""
        reason = stderr or str(err)
        raise CapCheckError(f"git {' '.join(args)} failed: {reason}", stderr) from err
    except (OSError, subprocess.SubprocessError) as err:
        raise CapCheckError(f"git {' '.join(args)} failed: {err}") from err
    return result.stdout.strip()


def _parse_number_list(spec: str) -> list[int]:
    """Every line `spec` (e.g. "3-5,9") names, a range expanded in full."""
    lines: list[int] = []
    for token in spec.split(","):
        if "-" in token:
            first_s, last_s = token.split("-", 1)
            first, last = int(first_s), int(last_s)
            lines.extend(range(first, max(first, last) + 1))
        else:
            lines.append(int(token))
    return lines


def _segment_lines(segment: str) -> tuple[str, list[int] | None]:
    for regex in (_HASH_L_RE, _COLON_L_RE, _COLON_RANGE_RE):
        matched = regex.match(segment)
        if matched is not None:
            first = int(matched.group(2))
            last = int(matched.group(3)) if matched.group(3) else first
            return matched.group(1).strip(), list(range(first, max(first, last) + 1))
    matched = _FILE_LINE_RE.match(segment)
    if matched is None:
        return segment.strip(), None
    return matched.group(1).strip(), _parse_number_list(matched.group(2))


def _normalise_path(path: str, toplevel: Path, changed_files: set[str]) -> str:
    if Path(path).is_absolute():
        for candidate, top in (
            (Path(path), toplevel),
            (Path(path).resolve(), toplevel.resolve()),
        ):
            try:
                path = candidate.relative_to(top).as_posix()
                break
            except ValueError:
                continue
    else:
        path = posixpath.normpath(path)
    if path not in changed_files:
        folded = [f for f in changed_files if f.casefold() == path.casefold()]
        if len(folded) == 1:
            path = folded[0]
    return path


def _parse_file_cell(
    cell: str, toplevel: Path, changed_files: set[str]
) -> list[tuple[str, list[int] | None]]:
    """One File cell's (path, lines) pairs; `lines` is None for a path with no
    line spec, else every line the cell names."""
    cell = _NOTE_RE.sub("", _ANNOTATION_RE.sub("", cell.strip()))
    pairs = []
    for segment in _SPLIT_RE.split(cell):
        segment = _ANNOTATION_RE.sub("", segment.replace("`", "").strip()).strip()
        if not segment:
            continue
        path, lines = _segment_lines(segment)
        if path:
            pairs.append((_normalise_path(path, toplevel, changed_files), lines))
    return pairs


def _verify_range(toplevel: Path, previous_head: str, head: str) -> None:
    """CapCheckError unless both shas are full 40-hex commits, differ,
    previous_head is an ancestor of head and head is reachable from HEAD."""
    for sha in (previous_head, head):
        if not _SHA_RE.match(sha):
            raise CapCheckError(f"{sha!r} is not a full 40-hex sha")
    for sha in (previous_head, head):
        try:
            _git(toplevel, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        except CapCheckError as err:
            raise CapCheckError(f"{sha} does not resolve to a commit", err.stderr) from err
    if previous_head.casefold() == head.casefold():
        raise CapCheckError(f"previous_head equals head ({head}); the rework range is empty")
    checks = (
        (previous_head, head, f"previous_head {previous_head} is not an ancestor of head {head}"),
        (head, "HEAD", f"head {head} is not reachable from HEAD"),
    )
    for ancestor, descendant, message in checks:
        try:
            _git(toplevel, "merge-base", "--is-ancestor", ancestor, descendant)
        except CapCheckError as err:
            raise CapCheckError(message, err.stderr) from err


def _missing_path_error(err: CapCheckError) -> bool:
    """True only when git's own stderr names a missing path; the formatted
    message carries the command text and is never read."""
    stderr = err.stderr.lower()
    return (
        "no such path" in stderr
        or "does not exist" in stderr
        or "exists on disk, but not in" in stderr
    )


def _unreadable_cell_error(err: CapCheckError) -> bool:
    """True only when git's stderr says the cell itself is unreadable: a line
    past the file's end or below 1, or a path outside the repository."""
    stderr = err.stderr.lower()
    return (
        "invalid line number" in stderr
        or " has only " in stderr
        or "is outside repository" in stderr
    )


def _introducing_commit(toplevel: Path, head: str, file: str, line: int) -> str | None:
    try:
        blame = _git(toplevel, "blame", "-L", f"{line},{line}", "--porcelain", head, "--", file)
    except CapCheckError as err:
        if _missing_path_error(err):
            return None
        raise
    return blame.splitlines()[0].split()[0] if blame else None


def _file_exists_at(toplevel: Path, head: str, file: str) -> bool:
    try:
        _git(toplevel, "cat-file", "-e", f"{head}:{file}")
    except CapCheckError as err:
        if _missing_path_error(err):
            return False
        raise
    return True


def _pair_commit(
    toplevel: Path,
    rework: tuple[str, str],
    path: str,
    lines: list[int] | None,
    rework_commits: set[str],
    changed_files: set[str],
) -> str | None:
    """The abbreviated commit that made an existing pair a regression, else None."""
    previous_head, head = rework
    if lines is None:
        if path in changed_files or any(f.startswith(path + "/") for f in changed_files):
            log = _git(toplevel, "log", "--format=%h", "--reverse", f"{previous_head}..{head}", "--", path)
            return log.splitlines()[0] if log else None
        return None
    for line in lines:
        introducing = _introducing_commit(toplevel, head, path, line)
        if introducing is not None and introducing in rework_commits:
            return _git(toplevel, "log", "--format=%h", "-1", introducing)
    return None


def _pairs_verdict(
    toplevel: Path,
    rework: tuple[str, str],
    pairs: list[tuple[str, list[int] | None]],
    rework_commits: set[str],
    changed_files: set[str],
) -> tuple[tuple, dict]:
    """(decider, result): null when a path is missing at head, else true at
    the first pair the rework range introduced, else false."""
    missing = [pair for pair in pairs if not _file_exists_at(toplevel, rework[1], pair[0])]
    if missing:
        reason = f"unresolved path {missing[0][0]}"
        return missing[0], {"regression": None, "commit": None, "reason": reason}
    for path, lines in pairs:
        commit = _pair_commit(toplevel, rework, path, lines, rework_commits, changed_files)
        if commit is not None:
            return (path, lines), {"regression": True, "commit": commit}
    return (pairs[0] if pairs else ("", None)), {"regression": False, "commit": None}


def _classify_row(
    toplevel: Path, rework: tuple[str, str], row, rework_commits: set[str], changed_files: set[str]
) -> dict:
    """Row verdict over every pair of its File cell; `file`/`line` name the
    pair that decided it."""
    pairs = _parse_file_cell(row.file, toplevel, changed_files)
    try:
        decider, result = _pairs_verdict(toplevel, rework, pairs, rework_commits, changed_files)
    except CapCheckError as err:
        if not _unreadable_cell_error(err):
            raise
        decider = pairs[0] if pairs else ("", None)
        result = {"regression": None, "commit": None, "reason": f"unresolved cell: {err}"}
    return {
        "ref": row.ref,
        "severity": row.severity,
        "file": decider[0],
        "line": decider[1][0] if decider[1] else None,
        **result,
    }


def classify_findings(
    *, repo_root: Path, review_text: str, previous_head: str | None, head: str
) -> list[dict]:
    """Every high/critical row of `review_text`'s Consolidated Findings
    section, classified against `previous_head..head`. [] without a
    previous head; no git call when no high/critical row exists."""
    if not previous_head:
        return []
    rows, problem = reviewed_rows(review_text)
    if problem is not None:
        raise CapCheckError(f"review text unreadable: {problem}")
    rows = [row for row in rows if row.severity in ("high", "critical")]
    if not rows:
        return []
    toplevel = Path(_git(repo_root, "rev-parse", "--show-toplevel"))
    _verify_range(toplevel, previous_head, head)
    rework_commits = set(_git(toplevel, "rev-list", f"{previous_head}..{head}").splitlines())
    diff = _git(toplevel, "diff", "--name-only", "-z", previous_head, head)
    changed_files = {name for name in diff.split("\0") if name}
    rework = (previous_head, head)
    return [_classify_row(toplevel, rework, row, rework_commits, changed_files) for row in rows]


def capture_range(repo_root: str, git_dir: str | None, base: str) -> tuple[str, int, str]:
    """("<base>..<end>", count, branch) with `end` = HEAD captured once;
    `git_dir` selects a bare-backed store with `repo_root` as work tree."""
    if not _BASE_RE.fullmatch(base):
        raise CapCheckError(f"base is not a 40-hex sha: {base!r}")
    if not Path(repo_root).is_dir():
        raise CapCheckError(f"repo_root is not a directory: {repo_root}")
    prefix = ("--git-dir", git_dir, "--work-tree", repo_root) if git_dir else ()
    end = _git(repo_root, *prefix, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if base != EMPTY_TREE:
        _git(repo_root, *prefix, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    count = int(_git(repo_root, *prefix, "rev-list", "--count", f"{base}..{end}"))
    branch = _git(repo_root, *prefix, "rev-parse", "--abbrev-ref", "HEAD")
    return f"{base}..{end}", count, branch
