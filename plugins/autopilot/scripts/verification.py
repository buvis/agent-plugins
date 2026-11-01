#!/usr/bin/env python3
"""Bounded verification of an explicit argv, and the reuse check for its
artifact. No workflow state: every input and output path is explicit, and
both functions fail toward re-running the verification, never skipping it."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import selectors
import signal
import subprocess
import time
from pathlib import Path

from dirty_tree import _ancestor_and_clean, _dirty_check, _git, _untracked_log_exclusion
from log_sink_refusal import _open_log_sink, refuse

GATE_TIMEOUT_S = 1800
GATE_OUTPUT_CAP = 2_000_000  # final stdout bytes kept for the summary parse
GATE_LOG_CAP = 20_000_000  # combined stdout+stderr bytes written to the log

KIND = "verification-artifact-v1"
SUMMARY_RE = re.compile(r"PASS (\d+) FAIL (\d+) SKIP (\d+) EXIT (\d+)")
_SHA_RE = re.compile(r"[0-9a-f]{40}")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_ARTIFACT_KEYS = {
    "schema_version",
    "kind",
    "argv",
    "head_sha",
    "exit_code",
    "summary",
    "timed_out",
    "output_limit_exceeded",
    "dirty_paths",
    "head_moved",
    "log",
    "reusable",
}
_SUMMARY_KEYS = {"passed", "failed", "skipped", "exit_code"}
_STALE: tuple[str, dict] = ("stale", {})


def _validate_inputs(argv: object, timeout: object) -> None:
    """Raises ValueError for a timeout that is not a finite number in
    (0, GATE_TIMEOUT_S] (booleans included) or an empty argv/executable."""
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or not 0 < timeout <= GATE_TIMEOUT_S
    ):
        raise ValueError(f"invalid timeout: {timeout!r}")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(token, str) for token in argv)
        or not argv[0]
    ):
        raise ValueError(f"invalid argv: {argv!r}")


def _unsafe_paths(root: Path, artifact: Path, log: Path) -> bool:
    """True when either output path is refused as a sink, escapes `root`,
    or both name the same file."""
    for path in (artifact, log):
        if refuse(path, root) is not None:
            return True
        if not path.resolve().is_relative_to(root.resolve()):
            return True
    return artifact.resolve() == log.resolve()


def _head_moved(root: Path, head_sha: str) -> bool:
    head = _git(root, "rev-parse", "HEAD")
    return head.returncode != 0 or head.stdout.strip() != head_sha


def _write_all(sink, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[sink.write(view) :]


def _drain(proc, sink, digest, deadline: float) -> tuple[bytes, bool, bool]:
    """Streams both pipes to `sink` in read order until EOF or `deadline`,
    keeping the final GATE_OUTPUT_CAP stdout bytes. A chunk that would push
    the log past GATE_LOG_CAP is cut to the remaining room and ends the
    drain. Returns (stdout_tail, drained, capped)."""
    log_room, out_cap = GATE_LOG_CAP, GATE_OUTPUT_CAP
    tail = bytearray()
    sel = selectors.DefaultSelector()
    open_pipes = {proc.stdout, proc.stderr}
    for pipe in open_pipes:
        sel.register(pipe, selectors.EVENT_READ)
    try:
        while open_pipes and (remaining := deadline - time.monotonic()) > 0:
            ready = sel.select(timeout=remaining)
            # stdout first: when both pipes are ready, keep its earlier bytes first.
            for key, _ in sorted(ready, key=lambda e: e[0].fileobj is not proc.stdout):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    sel.unregister(key.fileobj)
                    open_pipes.discard(key.fileobj)
                    continue
                part = chunk[:log_room]
                _write_all(sink, part)
                digest.update(part)
                log_room -= len(part)
                if key.fileobj is proc.stdout:
                    tail += part
                    del tail[:-out_cap]
                if len(part) < len(chunk):
                    return bytes(tail), False, True
    finally:
        sel.close()
    return bytes(tail), not open_pipes, False


def _kill(proc) -> None:
    """Kills and reaps `proc`'s process group; a gone group is not an error."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    proc.wait()


def _execute(argv: list[str], root: Path, sink, deadline: float) -> dict:
    """Spawns `argv` without a shell in its own session, drains and reaps
    it against `deadline`, killing the group on expiry, log overflow or
    any error. The deadline bounds drain and child exit together."""
    digest = hashlib.sha256()
    proc = subprocess.Popen(
        argv,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        tail, drained, capped = _drain(proc, sink, digest, deadline)
        exited = False
        if drained:
            try:
                proc.wait(timeout=max(0.0, deadline - time.monotonic()))
                exited = True
            except subprocess.TimeoutExpired:
                pass
        if not exited:
            _kill(proc)
    except BaseException:
        _kill(proc)
        raise
    finally:
        proc.stdout.close()
        proc.stderr.close()
    return {
        "exit_code": proc.returncode if exited else None,
        "tail": tail,
        "timed_out": not exited and not capped,
        "capped": capped,
        "sha256": digest.hexdigest(),
    }


def _parse_summary(tail: bytes) -> dict | None:
    """The last complete PASS/FAIL/SKIP/EXIT line in `tail`, or None."""
    found = None
    for line in tail.decode("utf-8", errors="ignore").splitlines():
        found = SUMMARY_RE.search(line) or found
    if found is None:
        return None
    keys = ("passed", "failed", "skipped", "exit_code")
    return dict(zip(keys, (int(group) for group in found.groups())))


def _green_summary(summary: object) -> bool:
    return (
        isinstance(summary, dict)
        and set(summary) == _SUMMARY_KEYS
        and all(type(value) is int for value in summary.values())
        and summary["failed"] == 0
        and summary["exit_code"] == 0
    )


def _artifact(argv, root, head_sha, log_rel, excluded, run) -> dict:
    """The artifact for a finished run, with the post-run dirt and HEAD
    re-checks that decide whether it is reusable."""
    summary = _parse_summary(run["tail"])
    dirty, dirty_paths = _dirty_check(root, excluded)
    head_moved = _head_moved(root, head_sha)
    reusable = (
        run["exit_code"] == 0
        and _green_summary(summary)
        and not (run["timed_out"] or run["capped"] or dirty or head_moved)
    )
    return {
        "schema_version": 1,
        "kind": KIND,
        "argv": list(argv),
        "head_sha": head_sha,
        "exit_code": run["exit_code"],
        "summary": summary,
        "timed_out": run["timed_out"],
        "output_limit_exceeded": run["capped"],
        "dirty_paths": dirty_paths,
        "head_moved": head_moved,
        "log": {"path": log_rel, "sha256": run["sha256"]},
        "reusable": reusable,
    }


def run_verification(
    *,
    argv: list[str],
    project_root: Path,
    head_sha: str,
    artifact_path: Path,
    log_path: Path,
    timeout: float = GATE_TIMEOUT_S,
) -> dict:
    """Runs `argv` once in `project_root` and writes its artifact. Invalid
    argv/timeout raise ValueError; an unsafe output path, a dirty tree or a
    moved HEAD is refused before spawning, with nothing written."""
    _validate_inputs(argv, timeout)
    root = project_root
    artifact = artifact_path if artifact_path.is_absolute() else root / artifact_path
    log = log_path if log_path.is_absolute() else root / log_path
    if _unsafe_paths(root, artifact, log):
        return {"schema_version": 1, "ok": False, "error": "unsafe-artifact-path"}
    excluded = _untracked_log_exclusion(root, log) + _untracked_log_exclusion(
        root, artifact
    )
    if _dirty_check(root, excluded)[0]:
        return {"schema_version": 1, "ok": False, "error": "dirty-tree"}
    if _head_moved(root, head_sha):
        return {"schema_version": 1, "ok": False, "error": "head-moved"}
    log_rel = log.resolve().relative_to(root.resolve()).as_posix()
    with _open_log_sink(log, root) as sink:
        run = _execute(argv, root, sink, time.monotonic() + timeout)
    art = _artifact(argv, root, head_sha, log_rel, excluded, run)
    with _open_log_sink(artifact, root) as sink:
        _write_all(sink, json.dumps(art, indent=2).encode() + b"\n")
    return {"schema_version": 1, "ok": True, "artifact": art, "controller_required": True}


def _reusable_shape(prior: object, argv: list[str]) -> bool:
    """Strict artifact shape and types of a green, clean run of exactly
    `argv` (no normalization within arguments)."""
    if not isinstance(prior, dict) or set(prior) != _ARTIFACT_KEYS:
        return False
    log = prior["log"]
    return (
        type(prior["schema_version"]) is int
        and prior["schema_version"] == 1
        and prior["kind"] == KIND
        and type(prior["argv"]) is list
        and prior["argv"] == argv
        and isinstance(prior["head_sha"], str)
        and _SHA_RE.fullmatch(prior["head_sha"]) is not None
        and type(prior["exit_code"]) is int
        and prior["exit_code"] == 0
        and _green_summary(prior["summary"])
        and prior["timed_out"] is False
        and prior["output_limit_exceeded"] is False
        and prior["head_moved"] is False
        and prior["reusable"] is True
        and type(prior["dirty_paths"]) is list
        and prior["dirty_paths"] == []
        and isinstance(log, dict)
        and set(log) == {"path", "sha256"}
        and isinstance(log["path"], str)
        and isinstance(log["sha256"], str)
        and _DIGEST_RE.fullmatch(log["sha256"]) is not None
    )


def reuse_verdict(
    *,
    prior: dict | None,
    argv: list[str],
    project_root: Path,
    head_sha: str,
) -> tuple[str, dict]:
    """("reused", prior) only for a strictly shaped green artifact of
    exactly `argv` whose head is an ancestor of `head_sha` with only
    management-store changes since and a clean product tree; ("stale", {})
    otherwise, including on any Git error."""
    if not _reusable_shape(prior, argv):
        return _STALE
    try:
        if not _ancestor_and_clean(project_root, prior["head_sha"], head_sha):
            return _STALE
    except OSError:
        return _STALE
    return ("reused", prior)
