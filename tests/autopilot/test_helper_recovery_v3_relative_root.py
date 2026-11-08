"""Recovery v3: a relative --project-root is the same request as its absolute spelling."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from test_helper_recovery_v2 import ARTIFACT, GITDIR, MARKER_CHILD, OUTSIDE, child_argv
from test_helper_recovery_v2 import commit_repo
from test_helper_recovery_v2_sinks import APP_BODY, green_artifact, seed
from test_helper_rework_sinks import commit_link
from test_local_boundary import World, git, library, make_world, one_json, run_cli, tree

PARENT = "has a parent-directory component"
SYMLINK = "is a symlink"
TRACKED = "is tracked"
STORE = "resolves inside the store"
NOT_REGULAR = "is not a regular file"
EXECUTABLE = "is executable"
HARD_LINKS = "has more than one hard link"
REASONS = {None, PARENT, SYMLINK, TRACKED, OUTSIDE, GITDIR, STORE, NOT_REGULAR, EXECUTABLE,
           HARD_LINKS}
APP = Path("src") / "app.py"
PM = Path("docs") / "dev" / "project-management"
ROOT_SPELLINGS = ["dot", "one-component", "two-component", "redundant-dot", "through-a-sibling"]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def make_candidates(world: World, root: Path) -> dict[Path, str | None]:
    """Sink candidates spelled from the resolved project root, with their refusal reason.

    The sibling shares the project root's whole path as a prefix, so a containment test
    that compares strings accepts it. Every documented reason appears exactly once.
    """
    commit_link(world, "loop-link", root)
    sibling = root.with_name(f"{root.name}-sibling")
    sibling.mkdir()
    logs = root / "logs"
    logs.mkdir()
    for name in ("exec.log", "a.log", "real.log"):
        seed(logs / name, b"prior\n").chmod(0o644)
    (logs / "exec.log").chmod(0o755)
    os.link(logs / "a.log", logs / "b.log")
    (logs / "alias.log").symlink_to(logs / "real.log")  # an eligible file behind a linked leaf
    return {
        logs / "fresh.log": None,
        logs / "real.log": None,
        logs / ".." / "logs" / "run.log": PARENT,
        root / "loop-link" / "logs" / "linked.log": SYMLINK,
        logs / "alias.log": SYMLINK,
        root / APP: TRACKED,
        sibling / "run.log": OUTSIDE,
        root / PM / "run.log": STORE,
        root / ".git" / "run.log": GITDIR,
        logs: NOT_REGULAR,
        logs / "exec.log": EXECUTABLE,
        logs / "a.log": HARD_LINKS,
    }


def spelling_of(case: str, root: Path) -> tuple[Path, str]:
    """A cwd, and `root` spelled relative to it: one directory, five relative spellings."""
    return {
        "dot": (root, "."),
        "one-component": (root.parent, root.name),
        "two-component": (root.parent.parent, f"{root.parent.name}/{root.name}"),
        "redundant-dot": (root.parent, f"./{root.name}"),
        "through-a-sibling": (root.parent, f"unrelated cwd/../{root.name}"),
    }[case]


def verify(world: World, root: Any, artifact: Path, log: Path, argv: list[str],
           cwd: Path) -> tuple[Any, Any]:
    proc, _ = run_cli(world, "--verify", "--project-root", root,
                      "--head-sha", git(world.target, "rev-parse", "HEAD"),
                      "--artifact", artifact, "--log", log, "--timeout", "60", "--", *argv,
                      cwd=cwd)
    return proc, one_json(proc)


def request_paths(root: Path, outputs: str, tail: Path) -> tuple[Path, Path, Path]:
    """The artifact and sink spelled against the project root or absolutely, plus the sink."""
    artifact = Path(ARTIFACT) if outputs == "relative" else root / ARTIFACT
    log = tail if outputs == "relative" else root / tail
    return artifact, log, root / tail


# --- refuse: the root may be spelled relatively, and every refusal survives it -----------------


@pytest.mark.parametrize("at", ROOT_SPELLINGS[:3])
def test_refuse_judges_a_relative_project_root_exactly_as_its_absolute_spelling(
    world: World, isolated_git: None, monkeypatch: pytest.MonkeyPatch, at: str,
) -> None:
    """PATH in the documented contract is any path, so the same directory decides alike."""
    sink = library("log_sink_refusal")
    root = world.target.resolve()
    expected = make_candidates(world, root)
    assert set(expected.values()) == REASONS, "a documented refusal reason went uncovered"
    where, relative = spelling_of(at, root)
    monkeypatch.chdir(where)
    assert not Path(relative).is_absolute(), relative
    for candidate, reason in expected.items():
        assert sink.refuse(candidate, root) == reason, candidate
        assert sink.refuse(candidate, Path(relative)) == reason, (relative, candidate)


def test_refuse_decides_by_the_project_root_and_not_by_the_candidate_spelling(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One candidate spelling, two project roots: the verdict follows the root either way."""
    sink = library("log_sink_refusal")
    root = world.target.resolve()
    commit_link(world, "loop-link", root)
    other = commit_repo(tmp_path.resolve() / "other repo", {"src/app.py": "o\n"})
    (other / "loop-link" / "logs").mkdir(parents=True)  # a real directory of the linked name
    monkeypatch.chdir(tmp_path.resolve())
    for spelled in (other, Path(other.name)):
        assert sink.refuse(root / "logs" / "fresh.log", spelled) == OUTSIDE, spelled
        assert sink.refuse(root / APP, spelled) == OUTSIDE, spelled
        assert sink.refuse(other / "loop-link" / "logs" / "x.log", spelled) is None, spelled
    assert sink.refuse(root / "logs" / "fresh.log", root) is None
    assert sink.refuse(root / APP, root) == TRACKED
    assert sink.refuse(root / "loop-link" / "logs" / "x.log", root) == SYMLINK


# --- the verify operation: a relative root runs the gate instead of refusing the path ----------


@pytest.mark.parametrize("outputs", ["relative", "absolute"])
@pytest.mark.parametrize("at", ROOT_SPELLINGS)
def test_a_verify_run_under_a_relative_project_root_records_what_the_absolute_one_records(
    world: World, tmp_path: Path, at: str, outputs: str,
) -> None:
    """Same request, two spellings of one directory: the gate runs and writes both times."""
    root = world.target.resolve()
    where, relative = spelling_of(at, root)
    case = f"{at}-{outputs}"
    tail = Path("logs") / f"{case}.log"
    artifact, log, sink = request_paths(root, outputs, tail)
    marker = tmp_path / f"{case}-marker.txt"
    argv = child_argv(tmp_path, f"{case}-child", MARKER_CHILD, marker)
    proc, report = verify(world, relative, artifact, log, argv, where)
    assert report["ok"] is True, (proc.returncode, report)
    assert marker.read_text("utf-8") == str(root), "the child did not run in the project"
    green_artifact(report, root, argv, root / artifact, sink)
    assert (root / report["artifact"]["log"]["path"]).resolve() == sink.resolve(), report
    if outputs == "relative":
        assert report["artifact"]["log"]["path"] == log.as_posix(), report
    marker.unlink()
    straight, plain = verify(world, root, artifact, log, argv, where)
    assert (straight.returncode, plain["ok"]) == (proc.returncode, True), plain
    assert marker.read_text("utf-8") == str(root)
    green_artifact(plain, root, argv, root / artifact, sink)
    assert plain["artifact"] == report["artifact"], (plain, report)
    if where != root:
        assert not (where / tail).exists(), "an output path resolved against cwd"


@pytest.mark.parametrize("outputs", ["relative", "absolute"])
@pytest.mark.parametrize("at", ROOT_SPELLINGS)
def test_a_tracked_log_stays_refused_when_the_project_root_is_spelled_relatively(
    world: World, tmp_path: Path, at: str, outputs: str,
) -> None:
    """The reject case of the accepted run's shape: only the sink path differs."""
    root = world.target.resolve()
    where, relative = spelling_of(at, root)
    case = f"{at}-{outputs}-tracked"
    artifact, log, tracked = request_paths(root, outputs, APP)
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


# --- the verify operation: an output the relative root resolves is judged all the same ---------

UNSAFE_TAILS = {
    "parent-component": Path("logs") / ".." / "logs" / "x.log",
    "escaping-parent": Path("logs") / ".." / ".." / "escape.log",
    "symlinked-component": Path("loop-link") / "logs" / "x.log",
}


@pytest.mark.parametrize("through", ["log", "artifact"])
@pytest.mark.parametrize("kind", list(UNSAFE_TAILS))
def test_an_unsafe_relative_output_under_a_relative_project_root_stays_refused(
    world: World, tmp_path: Path, kind: str, through: str,
) -> None:
    """A relative root resolves its outputs; it does not exempt them from the path rules."""
    root = world.target.resolve()
    commit_link(world, "loop-link", root)
    case = f"{kind}-{through}"
    safe = Path("logs") / f"{case}.log"
    log, artifact = ((UNSAFE_TAILS[kind], Path(ARTIFACT)) if through == "log"
                     else (safe, UNSAFE_TAILS[kind]))
    marker = tmp_path / f"{case}-marker.txt"
    argv = child_argv(tmp_path, f"{case}-child", MARKER_CHILD, marker)
    before = tree(world.target)
    proc, report = verify(world, ".", artifact, log, argv, root)
    assert (report["schema_version"], report["ok"]) == (1, False), (proc.returncode, report)
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran against an unsafe output path"
    assert not (root.parent / "escape.log").exists(), "the run wrote outside the project"
    assert tree(world.target) == before, "the refused run wrote inside the project"


OVERLAP = Path("docs") / "dev" / "tmp" / "overlap.json"
SCRIPT = Path("docs") / "dev" / "tmp" / "overlap-child.py"
PRIOR_OVERLAP = b'{"schema_version": 1, "ok": true, "marker": "RELATIVE-ROOT-PRIOR-6b01"}\n'


@pytest.mark.parametrize("case", ["one-file-both-relative", "one-file-mixed-spellings",
                                  "output-is-an-argv-input"])
def test_an_overlapping_output_under_a_relative_project_root_stays_refused(
    world: World, tmp_path: Path, case: str,
) -> None:
    """Two outputs naming one file, or an output naming an argv input, stay refused."""
    root = world.target.resolve()
    overlap = seed(root / OVERLAP, PRIOR_OVERLAP)
    body = MARKER_CHILD.encode("utf-8")
    script = seed(root / SCRIPT, body)
    marker = tmp_path / f"{case}-marker.txt"
    argv = [sys.executable, "-I", str(SCRIPT), str(marker)]
    if case == "output-is-an-argv-input":
        artifact, log = Path(ARTIFACT), SCRIPT
    else:
        artifact = OVERLAP if case == "one-file-both-relative" else root / OVERLAP
        log = OVERLAP
    proc, report = verify(world, ".", artifact, log, argv, root)
    assert (report["schema_version"], report["ok"]) == (1, False), (proc.returncode, report)
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran against an overlapping output path"
    assert overlap.read_bytes() == PRIOR_OVERLAP, "the refused run rewrote the named file"
    assert script.read_bytes() == body, "the refused run rewrote an argv input"
    assert not (root / ARTIFACT).exists(), "the refused run wrote a result artifact"
