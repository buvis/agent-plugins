"""Cycle-2 sinks: the log and the artifact keep prior bytes unless the run succeeds."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from test_helper_recovery_v2 import ARTIFACT, GITDIR, MARKER_CHILD, child_argv, commit_repo
from test_helper_recovery_v2 import failure_shape, run_gate
from test_local_boundary import World, git, library, make_world

PRIOR_MARKER = b"PRIOR-LOG-MARKER-7f31"
ALT_MARKER = b"PRIOR-LOG-MARKER-7f32"  # near miss: differs from PRIOR_MARKER in one byte
PRIOR_LOG = PRIOR_MARKER + b"\nPASS 9 FAIL 0 SKIP 0 EXIT 0\n"
ALT_LOG = ALT_MARKER + b"\nPASS 4 FAIL 1 SKIP 2 EXIT 1\n"
PRIOR_ARTIFACT = b'{"schema_version": 1, "ok": true, "marker": "PRIOR-ARTIFACT-9c02"}\n'
ALT_ARTIFACT = b'{"schema_version": 1, "ok": false, "marker": "PRIOR-ARTIFACT-9c03"}\n'
CHILD_OUTPUT = b"PASS 2 FAIL 0 SKIP 1 EXIT 0"
CHILD_SUMMARY = {"passed": 2, "failed": 0, "skipped": 1, "exit_code": 0}
ERR_MARK = b"ERR-MARK-3d81"
NOISY_CHILD = MARKER_CHILD + "sys.stderr.write('ERR-MARK-3d81\\n')\n"
APP_BODY = b"print('app')\n"


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def seed(path: Path, body: bytes) -> Path:
    """A file that already holds known bytes before the gate runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def unspawnable(tmp_path: Path, kind: str) -> list[str]:
    """A command whose child process cannot be started."""
    program = tmp_path / f"{kind}-program"
    if kind == "unexecutable-program":
        program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        program.chmod(0o644)
    return [str(program), "--version"]


def green_artifact(report: dict, root: Path, argv: list[str], artifact: Path, log: Path) -> dict:
    """The artifact holds this run's own record, not merely some bytes at that path."""
    art = json.loads(artifact.read_bytes())
    assert art == report["artifact"], report
    assert (art["argv"], art["head_sha"]) == (argv, git(root, "rev-parse", "HEAD")), art
    assert art["summary"] == CHILD_SUMMARY, art
    assert art["log"]["sha256"] == hashlib.sha256(log.read_bytes()).hexdigest(), art
    assert art["dirty_paths"] == [] and art["reusable"] is True, art
    return art


@pytest.mark.parametrize(("kind", "prior_log", "prior_artifact"),
                         [("absent-program", PRIOR_LOG, PRIOR_ARTIFACT),
                          ("unexecutable-program", ALT_LOG, ALT_ARTIFACT)],
                         ids=["absent-program", "unexecutable-program"])
def test_a_failed_spawn_leaves_an_existing_log_and_artifact_byte_identical(
    world: World, tmp_path: Path, isolated_git: None, kind: str,
    prior_log: bytes, prior_artifact: bytes,
) -> None:
    log = seed(world.target / "logs" / f"{kind}.log", prior_log)
    artifact = seed(world.target / ARTIFACT, prior_artifact)
    report = run_gate(world, unspawnable(tmp_path, kind), log=log, artifact=artifact, timeout=60)
    failure_shape(report, "spawn-failed")
    assert log.read_bytes() == prior_log, "the failed spawn rewrote an existing log"
    assert artifact.read_bytes() == prior_artifact, "the failed spawn rewrote an existing artifact"


def test_a_failed_spawn_writes_no_result_artifact_when_none_existed(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    log = seed(world.target / "logs" / "no-artifact.log", PRIOR_LOG)
    artifact = world.target / "docs" / "dev" / "tmp" / "verify-absent.json"
    report = run_gate(world, unspawnable(tmp_path, "absent-program"), log=log,
                      artifact=artifact, timeout=60)
    failure_shape(report, "spawn-failed")
    assert not artifact.exists(), "the failed spawn invented a result artifact"
    assert not (world.target / ARTIFACT).exists(), "the gate ignored the given artifact path"
    assert log.read_bytes() == PRIOR_LOG


def test_an_unopenable_sink_is_reported_instead_of_an_unspawnable_command(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    """The sink is proven openable first, so its failure never arrives as the spawn's."""
    report = run_gate(world, unspawnable(tmp_path, "absent-program"),
                      log=world.target / "src" / "app.py" / "run.log", timeout=60)
    failure_shape(report, "sink-failed")
    assert (world.target / "src" / "app.py").read_bytes() == APP_BODY
    assert not (world.target / ARTIFACT).exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root opens a file whose mode forbids writing")
def test_an_unopenable_existing_log_is_reported_before_the_spawn_and_keeps_its_bytes(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    """The openability proof comes before the spawn whether or not the log already exists."""
    log = seed(world.target / "logs" / "sealed.log", PRIOR_LOG)
    log.chmod(0o000)
    try:
        report = run_gate(world, unspawnable(tmp_path, "absent-program"), log=log, timeout=60)
    finally:
        log.chmod(0o644)
    failure_shape(report, "sink-failed")
    assert log.read_bytes() == PRIOR_LOG, "the unopenable log lost its prior bytes"
    assert not (world.target / ARTIFACT).exists()


def test_an_empty_command_is_refused_and_leaves_an_existing_log_byte_identical(
    world: World, isolated_git: None,
) -> None:
    log = seed(world.target / "logs" / "empty-command.log", ALT_LOG)
    with pytest.raises(ValueError):
        run_gate(world, [], log=log, timeout=60)
    assert log.read_bytes() == ALT_LOG
    assert not (world.target / ARTIFACT).exists()


def test_a_dirty_tracked_file_refuses_the_run_before_the_child_is_spawned(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    """A product edit that the given head_sha does not describe stops the run."""
    log = seed(world.target / "logs" / "dirty.log", PRIOR_LOG)
    marker = tmp_path / "dirty-marker.txt"
    argv = child_argv(tmp_path, "dirty-child", MARKER_CHILD, marker)
    (world.target / "src" / "app.py").write_text("print('edited')\n", encoding="utf-8")
    report = run_gate(world, argv, log=log, timeout=60)
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "dirty-tree", report
    assert not marker.exists(), "the child ran against a dirty tree"
    assert log.read_bytes() == PRIOR_LOG, "the refused run rewrote the log"
    assert not (world.target / ARTIFACT).exists()


def test_a_successful_run_replaces_the_logs_prior_bytes_instead_of_appending(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    log = seed(world.target / "logs" / "replaced.log", PRIOR_LOG + ALT_LOG)
    artifact = world.target / "docs" / "dev" / "tmp" / "verify-replaced.json"
    marker = tmp_path / "replaced-marker.txt"
    argv = child_argv(tmp_path, "replaced-child", NOISY_CHILD, marker)
    report = run_gate(world, argv, log=log, artifact=artifact, timeout=60)
    assert report["ok"] is True, report
    body = log.read_bytes()
    assert CHILD_OUTPUT in body, "the successful run did not write the child's output to the log"
    assert ERR_MARK in body, "the run never drained the child's stderr into the log"
    assert PRIOR_MARKER not in body, "the old log content survived a successful run"
    assert ALT_MARKER not in body, "the old log content survived a successful run"
    green_artifact(report, world.target, argv, artifact, log)
    assert not (world.target / ARTIFACT).exists()
    assert Path(marker.read_text("utf-8")).resolve() == world.target.resolve()


def test_an_aliased_log_path_is_refused_before_the_alias_targets_bytes_change(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    app = world.target / "src" / "app.py"
    control = seed(world.target / "logs" / "alias-control.log", PRIOR_LOG)
    control_marker = tmp_path / "alias-control-marker.txt"
    control_argv = child_argv(tmp_path, "control-child", MARKER_CHILD, control_marker)
    accepted = run_gate(world, control_argv, log=control, timeout=60)
    assert accepted["ok"] is True, accepted
    assert CHILD_OUTPUT in control.read_bytes(), "the accepted sink was never written"
    assert PRIOR_MARKER not in control.read_bytes()
    green_artifact(accepted, world.target, control_argv, world.target / ARTIFACT, control)
    artifact_bytes = (world.target / ARTIFACT).read_bytes()
    alias = world.target / "logs" / "alias.log"
    os.symlink(app, alias)
    marker = tmp_path / "alias-marker.txt"
    report = run_gate(world, child_argv(tmp_path, "alias-child", MARKER_CHILD, marker),
                      log=alias, timeout=60)
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran before the log path was judged"
    assert app.read_bytes() == APP_BODY, "the refused run changed the alias target"
    assert (world.target / ARTIFACT).read_bytes() == artifact_bytes
    assert control.read_bytes().count(CHILD_OUTPUT) == 1, "the refused run appended to a log"


def test_the_sink_judges_a_worktree_git_pointer_by_its_target_not_by_the_file_name(
    tmp_path: Path, isolated_git: None,
) -> None:
    """Only the pointer's content tells a git directory from an ordinary directory."""
    base = tmp_path.resolve()
    project = commit_repo(base / "repo", {"src/app.py": "a\n"})
    plain = project / "not-a-git-dir"
    plain.mkdir()
    worktree = base / "wt"
    git(project, "worktree", "add", "-q", "-b", "wt", str(worktree))
    sink = library("log_sink_refusal")
    assert sink.refuse(worktree / ".git", worktree) == GITDIR
    assert sink.refuse(project / ".git" / "objects" / "run.log", project) == GITDIR
    (worktree / ".git").write_text(f"gitdir: {plain}\n", encoding="utf-8")
    assert sink.refuse(worktree / ".git", worktree) != GITDIR, "the name decided, not the target"


def test_the_policy_still_prints_to_stdout_when_o_nofollow_support_is_missing(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
    """Only the --out export needs O_NOFOLLOW, so the stdout export keeps working without it."""
    facade = library("autopilot")
    monkeypatch.delattr(getattr(facade, "os", os), "O_NOFOLLOW", raising=False)
    assert not hasattr(os, "O_NOFOLLOW")
    capfd.readouterr()
    code = facade.main(["--export-policy"])
    captured = capfd.readouterr()
    assert (code, captured.err) == (0, ""), captured
    assert json.loads(captured.out)["schema_version"] == 1, captured.out
