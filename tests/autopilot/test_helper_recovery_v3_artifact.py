"""Recovery v3: a failed result artifact is invalidated through a kept descriptor."""

from __future__ import annotations

import errno
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, NamedTuple

import pytest
from test_helper_recovery_v2 import MARKER_CHILD, child_argv, failure_shape, reap, run_gate
from test_helper_recovery_v2 import spy_on_spawn
from test_helper_recovery_v2_sinks import ALT_ARTIFACT, PRIOR_ARTIFACT, seed
from test_helper_rework_sinks import patch_opener
from test_local_boundary import World, library, make_world


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


# --- run_verification: a failed result artifact is invalidated through a kept descriptor --------

INVALID = "artifact invalidation failed"
REPLACE_ONE = b'{"schema_version": 1, "reusable": true, "marker": "REPLACEMENT-8b01"}\n'
REPLACE_TWO = b'{"schema_version": 1, "reusable": true, "marker": "REPLACEMENT-8b02"}\n'
MOVE_CHILD = (  # an empty plan moves nothing; else it names artifact, new name, replacement
    "import os, pathlib, sys\n"
    "plan = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()\n"
    "if plan:\n"
    "    os.rename(plan[0], plan[1])\n"
    "    pathlib.Path(plan[0]).write_bytes(pathlib.Path(plan[2]).read_bytes())\n"
    "print('PASS 2 FAIL 0 SKIP 1 EXIT 0')\n"
)


class Moved(NamedTuple):
    report: dict
    artifact: Path
    held: Path  # where the child moved the artifact inode
    argv: list[str]
    hits: list  # (kind, sink inode, bytes sent) per injected sink failure
    calls: list[tuple[str, int]]  # (syscall, inode) per invalidation call after a hit
    refused: dict[str, str]  # syscall -> its injected per-run error message
    fds: tuple[set[str], set[str]]  # open descriptors before and after the gate


def open_fds() -> set[str]:
    return set(os.listdir("/dev/fd"))


class BrokenArtifactSink:
    """The real artifact sink; close, or the write completing the JSON, raises after it ran."""

    def __init__(self, handle: Any, mode: str, hits: list) -> None:
        self._handle, self._mode, self._hits, self._sent = handle, mode, hits, b""
        self._inode = os.fstat(handle.fileno()).st_ino

    def __getattr__(self, name: str) -> Any:
        return getattr(self._handle, name)

    def _fail(self, kind: str) -> None:
        if self._mode == kind:
            self._hits.append((kind, self._inode, self._sent))
            raise OSError(errno.EIO, f"injected artifact {kind} failure")

    def write(self, data: Any) -> Any:
        written = self._handle.write(data)
        self._sent += bytes(data)
        try:
            json.loads(self._sent)
        except ValueError:
            return written
        self._fail("write")
        return written

    def close(self) -> None:
        self._handle.close()
        self._fail("close")


def refuse_after(monkeypatch: pytest.MonkeyPatch, hits: list, broken: tuple[str, ...]
                 ) -> tuple[list[tuple[str, int]], dict[str, str]]:
    """Once a sink failure fired, records each call's inode and fails the `broken` ones.

    Each refusal carries a fresh random token, so a reason can only name it by passing
    the real error through.
    """
    calls: list[tuple[str, int]] = []
    refused = {name: f"{name}-refused-{secrets.token_hex(6)}" for name in ("ftruncate", "pwrite")}
    for name in ("ftruncate", "pwrite"):
        def fake(fd: int, *args: Any, _name: str = name, _real: Any = getattr(os, name)) -> Any:
            if hits:
                calls.append((_name, os.fstat(fd).st_ino))
                if _name in broken:
                    raise OSError(errno.EIO, refused[_name])
            return _real(fd, *args)

        monkeypatch.setattr(library("verification").os, name, fake)
    return calls, refused


@pytest.fixture
def run_moved(world: World, tmp_path: Path, isolated_git: None,
              monkeypatch: pytest.MonkeyPatch) -> Any:
    """Runs MOVE_CHILD with only the artifact sink broken; its folder is ignored by git.

    With `away`, the child moves the artifact into a sibling directory, not the pinned one.
    """
    (world.target / ".git" / "info").mkdir(exist_ok=True)
    (world.target / ".git" / "info" / "exclude").write_text("/docs/dev/tmp/moved/\n", "utf-8")
    real_open = library("log_sink_refusal")._open_log_sink

    def run(case: str, prior: bytes | None, moved: bytes | None, mode: str | None,
            broken: tuple[str, ...] = (), away: bool = False) -> Moved:
        artifact = world.target / "docs" / "dev" / "tmp" / "moved" / case / "result.json"
        artifact.parent.mkdir(parents=True)
        if prior is not None:
            seed(artifact, prior)
        held = artifact.parent.parent / f"{case}-away" / "held.json" if away else (
            artifact.with_name("held.json"))
        held.parent.mkdir(exist_ok=True)
        hits: list = []
        plan = [artifact, held, seed(tmp_path / f"{case}.src", moved)] if moved else []
        seed(tmp_path / f"{case}.plan", "\n".join(map(str, plan)).encode("utf-8"))
        seed(tmp_path / f"{case}.py", MOVE_CHILD.encode("utf-8"))
        argv = [sys.executable, "-I", str(tmp_path / f"{case}.py"), str(tmp_path / f"{case}.plan")]

        def opener(log_path: Any, repo_root: Any, *args: Any, **kwargs: Any) -> Any:
            handle = real_open(log_path, repo_root, *args, **kwargs)
            if mode and Path(log_path).resolve() == artifact.resolve():
                return BrokenArtifactSink(handle, mode, hits)
            return handle

        patch_opener(monkeypatch, opener)
        calls, refused = refuse_after(monkeypatch, hits, broken)
        children = spy_on_spawn(monkeypatch, argv)
        before = open_fds()
        try:
            report = run_gate(world, argv, log=world.target / "logs" / f"{case}.log",
                              artifact=artifact, timeout=60)
        finally:
            reap(children)
        return Moved(report, artifact, held, argv, hits, calls, refused, (before, open_fds()))

    return run


@pytest.mark.parametrize(("mode", "prior", "moved", "away"), [
    pytest.param("close", PRIOR_ARTIFACT, REPLACE_ONE, False, id="close-existing-renamed"),
    pytest.param("write", ALT_ARTIFACT, REPLACE_TWO, False, id="write-existing-renamed"),
    pytest.param("close", None, REPLACE_TWO, False, id="close-created-renamed"),
    pytest.param("write", None, REPLACE_ONE, False, id="write-created-renamed"),
    pytest.param("close", PRIOR_ARTIFACT, REPLACE_TWO, True, id="close-existing-moved-away"),
    pytest.param("write", ALT_ARTIFACT, REPLACE_ONE, True, id="write-existing-moved-away"),
    pytest.param("close", None, REPLACE_ONE, True, id="close-created-moved-away"),
    pytest.param("write", None, REPLACE_TWO, True, id="write-created-moved-away"),
    pytest.param(None, PRIOR_ARTIFACT, REPLACE_ONE, False, id="control-no-failure-existing"),
    pytest.param(None, None, REPLACE_TWO, False, id="control-no-failure-created"),
    pytest.param("close", None, None, False, id="control-close-created-kept"),
    pytest.param("write", ALT_ARTIFACT, None, False, id="control-write-existing-kept"),
])
def test_failed_artifact_is_emptied_through_its_descriptor_wherever_its_name_points(
    run_moved: Any, mode: str | None, prior: bytes | None, moved: bytes | None, away: bool,
) -> None:
    """Controls pass at v2: the record would otherwise be reusable, and a leaf the child
    leaves in place goes if this run created it and is emptied if it existed before.
    `moved-away` cases leave the pinned directory, so only a kept descriptor reaches them."""
    case = f"{mode}-{prior is None}-{moved is None}-{away}"
    run = run_moved(case, prior, moved, mode, away=away)
    report, artifact, held, hits = run.report, run.artifact, run.held, run.hits
    assert run.fds[1] == run.fds[0], "the run left descriptors open"
    if mode is None:
        assert report["ok"] is True and report["artifact"]["reusable"] is True, report
        assert json.loads(held.read_bytes()) == report["artifact"]
        assert artifact.read_bytes() == moved
        return
    failure_shape(report, f"sink-{mode}-failed")
    assert "artifact" not in report and INVALID not in report["reason"], report
    assert [hit[0] for hit in hits] == [mode], "the injected sink failure was never reached"
    assert json.loads(hits[0][2])["argv"] == run.argv, "the record never reached the sink"
    if moved is None:
        assert os.listdir(artifact.parent) == (["result.json"] if prior else [])
        if prior is not None:
            assert artifact.read_bytes() == b"", "the existing leaf kept the record"
        else:
            assert not artifact.exists(), "the created leaf survived"
        return
    assert hits[0][1] == held.stat().st_ino, "the sink was not the inode the child moved"
    assert held.read_bytes() == b"", "the moved inode still holds the failed record"
    assert artifact.read_bytes() == moved, "the replacement under the original name changed"
    assert run.calls == [("ftruncate", hits[0][1])], run.calls


@pytest.mark.parametrize("moved", [REPLACE_ONE, None], ids=["renamed", "existing-kept"])
@pytest.mark.parametrize("broken", [("ftruncate",), ("ftruncate", "pwrite")],
                         ids=["ftruncate-fails", "both-fail"])
@pytest.mark.parametrize("mode", ["close", "write"])
def test_failed_artifact_falls_back_to_a_nul_byte_then_reports_the_invalidation_failure(
    run_moved: Any, mode: str, broken: tuple[str, ...], moved: bytes | None,
) -> None:
    """A leaf the child leaves in place gets the same fallback as a renamed one."""
    case = f"fallback-{mode}-{len(broken)}-{moved is None}"
    run = run_moved(case, PRIOR_ARTIFACT, moved, mode, broken)
    report = run.report
    failure_shape(report, f"sink-{mode}-failed")
    assert "artifact" not in report, report
    assert run.fds[1] == run.fds[0], "the run left descriptors open"
    assert [hit[0] for hit in run.hits] == [mode], "the injected sink failure was never reached"
    target = run.held if moved else run.artifact
    if moved:
        assert run.artifact.read_bytes() == REPLACE_ONE, "the replacement changed"
    else:
        assert os.listdir(run.artifact.parent) == ["result.json"]
    inode = target.stat().st_ino
    assert run.hits[0][1] == inode, "the sink was not the inode under test"
    assert run.calls == [("ftruncate", inode), ("pwrite", inode)], run.calls
    _, found, tail = report["reason"].partition(INVALID)
    if broken == ("ftruncate",):
        assert target.read_bytes()[:1] == b"\0", "the record does not start with NUL"
        assert not found, report
        return
    first, second = (tail.find(run.refused[name]) for name in ("ftruncate", "pwrite"))
    assert found and -1 < first < second, report


# --- _write_artifact: the invalidation descriptor cannot be duplicated -------------------------

DUP_CALLS = ("dup", "dup2")
RECORD_ONE = {"schema_version": 1, "reusable": True, "marker": "DUP-RECORD-7a01"}
RECORD_TWO = {"schema_version": 1, "reusable": True, "marker": "DUP-RECORD-7a02"}
PAD = b"PRIOR-ARTIFACT-9c04-" * 256  # a prior record longer than any record stored over it
LONG_ARTIFACT = b'{"schema_version": 1, "ok": true, "marker": "' + PAD + b'"}\n'


def break_dup(monkeypatch: pytest.MonkeyPatch, inodes: set[int]) -> tuple[list[str], str]:
    """Fails only the duplication of a descriptor on one of `inodes`, with a fresh token.

    The token is random per run, so a reason can only name it by passing the real error on.
    """
    calls: list[str] = []
    token = f"dup-refused-{secrets.token_hex(6)}"
    for name in DUP_CALLS:
        def fake(fd: int, *args: Any, _name: str = name, _real: Any = getattr(os, name)) -> Any:
            if os.fstat(fd).st_ino in inodes:
                calls.append(_name)
                raise OSError(errno.EMFILE, token)
            return _real(fd, *args)

        monkeypatch.setattr(library("verification").os, name, fake)
    return calls, token


@pytest.mark.parametrize(("prior", "record"),
                         [(PRIOR_ARTIFACT, RECORD_ONE), (ALT_ARTIFACT, RECORD_TWO)],
                         ids=["prior-record", "alternate-record"])
def test_write_artifact_closes_the_sink_and_keeps_a_prior_record_when_the_dup_fails(
    world: World, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    prior: bytes, record: dict,
) -> None:
    """The one failure path that must not empty the leaf: nothing went through it yet."""
    artifact = seed(world.target / "docs" / "dev" / "tmp" / f"{record['marker']}.json", prior)
    before = open_fds()
    with open(artifact, "r+b") as sink:  # a writable sink that keeps the leaf's prior bytes
        assert open_fds() != before, "the artifact sink never opened"
        calls, token = break_dup(monkeypatch, {artifact.stat().st_ino})
        result = library("verification")._write_artifact(record, sink)
        assert calls, "the invalidation descriptor was never duplicated"
        assert set(result) == {"error", "reason"}, result
        assert result["error"] == "sink-write-failed", result
        assert token in result["reason"], result
        assert open_fds() == before, "the failed duplication left the sink open"
    assert artifact.read_bytes() == prior, "the prior record was emptied or NUL-prefixed"


def test_write_artifact_stores_the_record_over_a_prior_one_when_the_dup_succeeds(
    world: World, isolated_git: None,
) -> None:
    """The accept case of the same shape: only the duplication's outcome differs.

    The prior record is longer than the stored one, so a leaf that is written over
    without being emptied first keeps a tail and is no longer one JSON value.
    """
    artifact = seed(world.target / "docs" / "dev" / "tmp" / "dup-control.json", LONG_ARTIFACT)
    before = open_fds()
    with open(artifact, "r+b") as sink:
        assert library("verification")._write_artifact(RECORD_ONE, sink) is None
        assert open_fds() == before, "the stored record left the sink open"
    stored = artifact.read_bytes()
    assert json.loads(stored) == RECORD_ONE, stored  # json.loads rejects a surviving tail
    assert PAD not in stored, "the prior record's bytes outlived it"
    assert len(stored) < len(LONG_ARTIFACT) and stored.endswith(b"\n"), stored


@pytest.mark.parametrize(("prior", "name"), [(PRIOR_ARTIFACT, "prior"), (ALT_ARTIFACT, "alt")],
                         ids=["prior-record", "alternate-record"])
def test_run_verification_reports_a_failed_invalidation_dup_and_keeps_the_prior_record(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    prior: bytes, name: str,
) -> None:
    artifact = seed(world.target / "docs" / "dev" / "tmp" / f"dup-gate-{name}.json", prior)
    marker = tmp_path / f"dup-gate-{name}-marker.txt"
    argv = child_argv(tmp_path, f"dup-gate-{name}-child", MARKER_CHILD, marker)
    calls, token = break_dup(monkeypatch, {artifact.stat().st_ino})
    children = spy_on_spawn(monkeypatch, argv)
    before = open_fds()
    try:
        report = run_gate(world, argv, log=world.target / "logs" / f"dup-gate-{name}.log",
                          artifact=artifact, timeout=60)
    finally:
        reap(children)
    assert calls, "the invalidation descriptor was never duplicated"
    failure_shape(report, "sink-write-failed")
    assert token in report["reason"], report
    assert "artifact" not in report, "a failed duplication returned a reusable record"
    assert open_fds() == before, "the run left descriptors open"
    assert artifact.read_bytes() == prior, "the run emptied or NUL-prefixed the prior record"
    assert marker.read_text("utf-8") == str(world.target.resolve()), "the child never ran"
