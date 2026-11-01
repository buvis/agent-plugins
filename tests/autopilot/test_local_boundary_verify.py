"""The --verify facade maps bounded verification outcomes to the documented exit codes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import POISON, STATE, World, assert_usage, git, make_world, one_json
from test_local_boundary import run_cli, tree

GREEN = "PASS 3 FAIL 0 SKIP 1 EXIT 0"
ARTIFACT = "docs/dev/tmp/artifact.json"
LOG = "docs/dev/tmp/run.log"


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


def py(*lines: str) -> list[str]:
    return [sys.executable, "-c", "\n".join(lines)]


def marker_argv(world: World) -> list[str]:
    marker = world.base / "spawned"
    return py(f"open({str(marker)!r}, 'w').write('spawned')", f"print({GREEN!r})")


def verify(world: World, argv: list[str], *, head: str | None = None, artifact: str = ARTIFACT,
           log: str = LOG, timeout: str | None = None, cwd: Path | None = None,
           audited: bool = False) -> tuple[Any, dict | None]:
    head = head or git(world.target, "rev-parse", "HEAD")
    extra = ["--timeout", timeout] if timeout is not None else []
    return run_cli(world, "--verify", "--project-root", world.target, "--head-sha", head,
                   "--artifact", artifact, "--log", log, *extra, "--", *argv,
                   cwd=cwd, audited=audited)


def written_artifact(world: World, report: dict) -> dict:
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert report["ok"] is True
    art = report["artifact"]
    assert json.loads((world.target / ARTIFACT).read_bytes()) == art
    assert (world.target / LOG).is_file()
    return art


def test_green_verification_resolves_relative_paths_against_the_project_root(
    world: World,
) -> None:
    head = git(world.target, "rev-parse", "HEAD")
    argv = py("import os, sys", "print('ARGS', sys.argv[1:], os.getcwd())",
              f"print({GREEN!r})") + ["--project-root", "decoy", "--", "tail"]
    proc, _ = verify(world, argv, head=head)
    assert proc.returncode == 0, proc.stderr
    art = written_artifact(world, one_json(proc))
    assert art["argv"] == argv and art["head_sha"] == head
    assert art["exit_code"] == 0 and art["reusable"] is True
    assert art["summary"] == {"passed": 3, "failed": 0, "skipped": 1, "exit_code": 0}
    log = (world.target / LOG).read_text("utf-8")
    assert "['--project-root', 'decoy', '--', 'tail']" in log
    assert str(world.target.resolve()) in log
    assert list(world.cwd.iterdir()) == []


@pytest.mark.parametrize(
    ("argv_lines", "timeout", "field", "value"),
    [
        ((f"print({GREEN!r})", "raise SystemExit(3)"), None, "exit_code", 3),
        (("print('PASS 7 FAIL 2 SKIP 0 EXIT 1')",), None, "summary",
         {"passed": 7, "failed": 2, "skipped": 0, "exit_code": 1}),
        (("import time", "print('started', flush=True)", "time.sleep(30)"), "1",
         "timed_out", True),
        (("import sys", "sys.stdout.write('x' * 2_500_000)", f"print({GREEN!r})"), None,
         "output_limit_exceeded", True),
    ],
    ids=["nonzero-exit", "summary-failure", "timeout", "output-overflow"],
)
def test_real_verification_failures_exit_1_with_the_written_artifact(
    world: World, argv_lines: tuple[str, ...], timeout: str | None, field: str, value: Any,
) -> None:
    proc, _ = verify(world, py(*argv_lines), timeout=timeout)
    assert proc.returncode == 1, proc.stderr
    art = written_artifact(world, one_json(proc))
    assert art[field] == value
    assert art["reusable"] is False


def dirty(world: World) -> dict[str, str]:
    (world.target / "src" / "new.py").write_text("x = 1\n", encoding="utf-8")
    return {}


def stale_head(world: World) -> dict[str, str]:
    return {"head": "0" * 40}


def live_state_artifact(world: World) -> dict[str, str]:
    return {"artifact": str(STATE / "last-verification.json")}


def git_internal_log(world: World) -> dict[str, str]:
    return {"log": ".git/run.log"}


@pytest.mark.parametrize(
    ("arrange", "error", "codes"),
    [
        (dirty, "dirty-tree", {1, 2}),
        (stale_head, "head-moved", {1, 2}),
        (live_state_artifact, "unsafe-artifact-path", {2}),
        (git_internal_log, "unsafe-artifact-path", {2}),
    ],
    ids=["dirty-tree", "head-moved", "live-state-artifact", "git-internal-log"],
)
def test_pre_spawn_refusal_reports_ok_false_without_spawning_or_writing(
    world: World, arrange, error: str, codes: set[int],
) -> None:
    overrides = arrange(world)
    before = tree(world.target / STATE)
    proc, _ = verify(world, marker_argv(world), **overrides)
    assert proc.returncode in codes, (proc.returncode, proc.stderr)
    report = one_json(proc)
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert (report["ok"], report["error"]) == (False, error)
    assert not (world.base / "spawned").exists()
    assert not (world.target / ARTIFACT).exists() and not (world.target / LOG).exists()
    assert tree(world.target / STATE) == before
    assert (world.target / STATE / "last-verification.json").read_text("utf-8") == (
        POISON["last-verification.json"])


@pytest.mark.parametrize("arguments", [("--timeout", "abc"), ("--timeout", "1801"),
                                       ("--timeout", "-5"), ("no-argv",)],
                         ids=["non-numeric", "above-bound", "negative", "missing-argv"])
def test_invalid_verify_arguments_are_usage_errors_before_spawn(
    world: World, arguments: tuple[str, ...],
) -> None:
    head = git(world.target, "rev-parse", "HEAD")
    common = ["--verify", "--project-root", world.target, "--head-sha", head,
              "--artifact", ARTIFACT, "--log", LOG]
    if arguments == ("no-argv",):
        proc, _ = run_cli(world, *common, "--")
    else:
        proc, _ = run_cli(world, *common, *arguments, "--", *marker_argv(world))
    assert_usage(proc)
    assert not (world.base / "spawned").exists()
    assert not (world.target / ARTIFACT).exists()
    accepted, _ = verify(world, marker_argv(world), timeout="5")
    assert accepted.returncode == 0, accepted.stderr
    assert (world.base / "spawned").read_text("utf-8") == "spawned"
