"""Cycle-2 sinks: the log and the artifact keep prior bytes unless the run succeeds."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from test_helper_recovery_v2 import ARTIFACT, MARKER_CHILD, child_argv, failure_shape, run_gate
from test_local_boundary import World, make_world

PRIOR_MARKER = b"PRIOR-LOG-MARKER-7f31"
ALT_MARKER = b"PRIOR-LOG-MARKER-7f32"  # near miss: differs from PRIOR_MARKER in one byte
PRIOR_LOG = PRIOR_MARKER + b"\nPASS 9 FAIL 0 SKIP 0 EXIT 0\n"
ALT_LOG = ALT_MARKER + b"\nPASS 4 FAIL 1 SKIP 2 EXIT 1\n"
PRIOR_ARTIFACT = b'{"schema_version": 1, "ok": true, "marker": "PRIOR-ARTIFACT-9c02"}\n'
ALT_ARTIFACT = b'{"schema_version": 1, "ok": false, "marker": "PRIOR-ARTIFACT-9c03"}\n'
CHILD_OUTPUT = b"PASS 2 FAIL 0 SKIP 1 EXIT 0"
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


def test_an_empty_command_is_refused_and_leaves_an_existing_log_byte_identical(
    world: World, isolated_git: None,
) -> None:
    log = seed(world.target / "logs" / "empty-command.log", ALT_LOG)
    with pytest.raises(ValueError):
        run_gate(world, [], log=log, timeout=60)
    assert log.read_bytes() == ALT_LOG
    assert not (world.target / ARTIFACT).exists()


def test_a_successful_run_replaces_the_logs_prior_bytes_instead_of_appending(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    log = seed(world.target / "logs" / "replaced.log", PRIOR_LOG + ALT_LOG)
    artifact = world.target / "docs" / "dev" / "tmp" / "verify-replaced.json"
    marker = tmp_path / "replaced-marker.txt"
    argv = child_argv(tmp_path, "replaced-child", MARKER_CHILD, marker)
    report = run_gate(world, argv, log=log, artifact=artifact, timeout=60)
    assert report["ok"] is True, report
    body = log.read_bytes()
    assert CHILD_OUTPUT in body, "the successful run did not write the child's output to the log"
    assert PRIOR_MARKER not in body, "the old log content survived a successful run"
    assert ALT_MARKER not in body, "the old log content survived a successful run"
    assert artifact.is_file(), "the successful run wrote no artifact at the path it was given"
    assert not (world.target / ARTIFACT).exists()
    assert Path(marker.read_text("utf-8")).resolve() == world.target.resolve()


def test_an_aliased_log_path_is_refused_before_the_alias_targets_bytes_change(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    app = world.target / "src" / "app.py"
    control = seed(world.target / "logs" / "alias-control.log", PRIOR_LOG)
    control_marker = tmp_path / "alias-control-marker.txt"
    accepted = run_gate(world, child_argv(tmp_path, "control-child", MARKER_CHILD, control_marker),
                        log=control, timeout=60)
    assert accepted["ok"] is True, accepted
    assert CHILD_OUTPUT in control.read_bytes(), "the accepted sink was never written"
    assert PRIOR_MARKER not in control.read_bytes()
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
