"""Recovery v3: a relative --project-root is the same request as its absolute spelling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from test_helper_recovery_v2 import ARTIFACT, MARKER_CHILD, OUTSIDE, child_argv
from test_helper_recovery_v2_sinks import APP_BODY, green_artifact
from test_helper_rework_sinks import commit_link
from test_local_boundary import World, git, library, make_world, one_json, run_cli

PARENT = "has a parent-directory component"
SYMLINK = "is a symlink"
TRACKED = "is tracked"
APP = Path("src") / "app.py"


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def candidates(root: Path) -> dict[Path, str | None]:
    """Sink candidates spelled from the resolved project root, with their refusal reason.

    The sibling shares the project root's whole path as a prefix, so a containment test
    that compares strings accepts it.
    """
    sibling = root.with_name(f"{root.name}-sibling")
    return {
        root / "logs" / "fresh.log": None,
        root / "logs" / ".." / "logs" / "run.log": PARENT,
        root / "loop-link" / "logs" / "linked.log": SYMLINK,
        root / APP: TRACKED,
        sibling / "run.log": OUTSIDE,
    }


def spelled_at(case: str, root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Moves cwd, then spells `root` relative to it: zero, one or two path components."""
    where = {"inside": root, "parent": root.parent, "grandparent": root.parent.parent}[case]
    monkeypatch.chdir(where)
    return Path(os.path.relpath(root, where))


def verify(world: World, root: Any, artifact: Path, log: Path, argv: list[str],
           cwd: Path) -> tuple[Any, Any]:
    proc, _ = run_cli(world, "--verify", "--project-root", root,
                      "--head-sha", git(world.target, "rev-parse", "HEAD"),
                      "--artifact", artifact, "--log", log, "--timeout", "60", "--", *argv,
                      cwd=cwd)
    return proc, one_json(proc)


def request_paths(root: Path, outputs: str, case: str, tail: Path) -> tuple[Path, Path, Path]:
    """The artifact and sink spelled against the project root or absolutely, plus the sink."""
    artifact = Path(ARTIFACT) if outputs == "relative" else root / ARTIFACT
    log = tail if outputs == "relative" else root / tail
    return artifact, log, root / tail


# --- refuse: the root may be spelled relatively, and every refusal survives it -----------------


@pytest.mark.parametrize("at", ["inside", "parent", "grandparent"],
                         ids=["dot-root", "one-component-root", "two-component-root"])
def test_refuse_judges_a_relative_project_root_exactly_as_its_absolute_spelling(
    world: World, isolated_git: None, monkeypatch: pytest.MonkeyPatch, at: str,
) -> None:
    """PATH in the documented contract is any path, so the same directory decides alike."""
    sink = library("log_sink_refusal")
    root = world.target.resolve()
    commit_link(world, "loop-link", root)
    root.with_name(f"{root.name}-sibling").mkdir()
    expected = candidates(root)
    relative = spelled_at(at, root, monkeypatch)
    assert not relative.is_absolute() and ".." not in relative.parts, relative
    for candidate, reason in expected.items():
        assert sink.refuse(candidate, root) == reason, candidate
        assert sink.refuse(candidate, relative) == reason, (str(relative), candidate)
    assert len({str(reason) for reason in expected.values()}) == len(expected)


# --- the verify operation: a relative root runs the gate instead of refusing the path ----------


@pytest.mark.parametrize("outputs", ["relative", "absolute"])
@pytest.mark.parametrize("at", ["inside", "parent"], ids=["dot-root", "one-component-root"])
def test_a_verify_run_under_a_relative_project_root_records_what_the_absolute_one_records(
    world: World, tmp_path: Path, at: str, outputs: str,
) -> None:
    """Same request, two spellings of one directory: the gate runs and writes both times."""
    root = world.target.resolve()
    where = root if at == "inside" else root.parent
    relative = Path(os.path.relpath(root, where))
    case = f"{at}-{outputs}"
    artifact, log, sink = request_paths(root, outputs, case, Path("logs") / f"{case}.log")
    marker = tmp_path / f"{case}-marker.txt"
    argv = child_argv(tmp_path, f"{case}-child", MARKER_CHILD, marker)
    proc, report = verify(world, relative, artifact, log, argv, where)
    assert report["ok"] is True, (proc.returncode, report)
    assert marker.read_text("utf-8") == str(root), "the child did not run in the project"
    green_artifact(report, root, argv, root / artifact, sink)
    marker.unlink()
    straight, plain = verify(world, root, artifact, log, argv, where)
    assert (straight.returncode, plain["ok"]) == (proc.returncode, True), plain
    assert marker.read_text("utf-8") == str(root)
    green_artifact(plain, root, argv, root / artifact, sink)
    assert plain["artifact"] == report["artifact"], (plain, report)
    if where != root:
        assert not (where / "logs").exists(), "an output path resolved against cwd"


@pytest.mark.parametrize("outputs", ["relative", "absolute"])
@pytest.mark.parametrize("at", ["inside", "parent"], ids=["dot-root", "one-component-root"])
def test_a_tracked_log_stays_refused_when_the_project_root_is_spelled_relatively(
    world: World, tmp_path: Path, at: str, outputs: str,
) -> None:
    """The reject case of the accepted run's shape: only the sink path differs."""
    root = world.target.resolve()
    where = root if at == "inside" else root.parent
    relative = Path(os.path.relpath(root, where))
    case = f"{at}-{outputs}-tracked"
    artifact, log, tracked = request_paths(root, outputs, case, APP)
    marker = tmp_path / f"{case}-marker.txt"
    argv = child_argv(tmp_path, f"{case}-child", MARKER_CHILD, marker)
    proc, report = verify(world, relative, artifact, log, argv, where)
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran against a tracked sink path"
    assert tracked.read_bytes() == APP_BODY, "the refused run wrote the tracked file"
    assert not (root / ARTIFACT).exists(), "the refused run wrote a result artifact"
    straight, plain = verify(world, root, artifact, log, argv, where)
    assert (straight.returncode, plain) == (proc.returncode, report), plain
