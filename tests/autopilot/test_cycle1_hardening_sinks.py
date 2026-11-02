"""Cycle-1 hardening: sink validation reads nothing it refuses by location and sees nested repos."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from test_local_paths import PM, git, load_helper, write

OUTSIDE = "resolves outside the repository"
GITDIR = "resolves inside the git directory"
STATE = PM + "autopilot/state.json"
STATE_TEXT = '{"phase": "review", "queue": ["T1"]}\n'
OPENED: list[tuple[str, str, int]] = []
ARMED: list[bool] = []


def _audit(event: str, args: tuple) -> None:
    if ARMED and event == "open" and isinstance(args[0], (str, bytes)):
        mode = args[1] if isinstance(args[1], str) else "r"
        flags = args[2] if isinstance(args[2], int) else 0
        OPENED.append((os.path.realpath(os.fsdecode(args[0])), mode, flags))


sys.addaudithook(_audit)


@pytest.fixture
def sink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    return load_helper("log_sink_refusal")


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path.resolve()


@pytest.fixture
def recorder():
    """Opens are recorded from the moment a test calls `recorder.clear()`, so
    fixture setup writes never count."""
    ARMED.append(True)
    OPENED.clear()
    yield OPENED
    ARMED.clear()


def make_repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True)
    git(root, "init", "-q")
    write(root, files)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    return root


def opens_of(opened: list[tuple[str, str, int]], path: Path) -> list[tuple[str, int]]:
    """Every recorded open of `path` (mode, flags)."""
    target = os.path.realpath(path)
    return [(m, f) for p, m, f in opened if p == target]


def listing(base: Path) -> list[Path]:
    return sorted(p.relative_to(base) for p in base.rglob("*") if ".git" not in p.parts)


# --- 1. no read of a candidate that is refused by location --------------------------------------


def test_sink_refuses_the_parent_repositorys_state_file_without_opening_it(
    base: Path, sink, recorder
) -> None:
    parent = make_repo(base / "parent", {"sub/keep.txt": "k\n", STATE: STATE_TEXT})
    project = parent / "sub"
    candidate = parent / STATE
    recorder.clear()
    assert sink.refuse(candidate, project) is not None
    assert opens_of(recorder, candidate) == []
    assert candidate.read_text("utf-8") == STATE_TEXT


def test_sink_refuses_a_file_outside_every_repository_without_opening_it(
    base: Path, sink, recorder
) -> None:
    root = make_repo(base / "repo", {"b.py": "b\n"})
    stranger = base / "elsewhere" / "state.json"
    write(base, {"elsewhere/state.json": "gitdir: " + str(root / ".git") + "\n"})
    recorder.clear()
    assert sink.refuse(stranger, root) == OUTSIDE
    assert opens_of(recorder, stranger) == []


def test_sink_refuses_a_sibling_directory_candidate_of_the_same_repository_unopened(
    base: Path, sink, recorder
) -> None:
    parent = make_repo(base / "parent", {"sub/keep.txt": "k\n", "other/p.md": "p\n"})
    write(parent, {"other/state.json": "gitdir: " + str(parent / ".git") + "\n"})
    candidate = parent / "other" / "state.json"
    recorder.clear()
    assert sink.refuse(candidate, parent / "sub") is not None
    assert opens_of(recorder, candidate) == []


def test_sink_still_recognizes_a_linked_worktree_git_pointer_file(
    base: Path, sink, recorder
) -> None:
    root = make_repo(base / "repo", {"b.py": "b\n"})
    worktree = base / "wt"
    git(root, "worktree", "add", "-q", "-b", "wt", str(worktree))
    assert (worktree / ".git").is_file()
    assert sink.refuse(worktree / ".git", worktree) == GITDIR
    assert sink.refuse(worktree / "logs" / "new.log", worktree) is None


def test_sink_still_accepts_ordinary_outputs_inside_the_project(
    base: Path, sink, recorder
) -> None:
    parent = make_repo(base / "parent", {"sub/keep.txt": "k\n", STATE: STATE_TEXT})
    project = parent / "sub"
    write(project, {"logs/plain.log": "p"})
    (project / "logs/plain.log").chmod(0o644)
    assert sink.refuse(project / "logs/new.log", project) is None
    assert sink.refuse(project / "logs/plain.log", project) is None
    assert sink.refuse(parent / STATE, parent) is not None


# --- 2. nested repository under a directory that does not exist yet -----------------------------


@pytest.mark.parametrize("tail", ["x.log", "new/x.log", "new/deeper/x.log"])
def test_sink_refuses_a_path_in_a_nested_repository_whether_or_not_its_dirs_exist(
    base: Path, sink, tail: str
) -> None:
    root = make_repo(base / "repo", {"b.py": "b\n"})
    inner = root / "vendor" / "inner"
    inner.mkdir(parents=True)
    git(inner, "init", "-q")
    (inner / "existing").mkdir()
    assert sink.refuse(inner / "existing" / "x.log", root) == OUTSIDE
    before = listing(base)
    assert sink.refuse(inner / tail, root) == OUTSIDE
    assert listing(base) == before


@pytest.mark.parametrize("tail", ["x.log", "new/x.log", "new/deeper/x.log"])
def test_sink_accepts_a_path_under_a_new_directory_of_an_ordinary_project_dir(
    base: Path, sink, tail: str
) -> None:
    root = make_repo(base / "repo", {"b.py": "b\n", "vendor/plain/keep.txt": "k\n"})
    before = listing(base)
    assert sink.refuse(root / "vendor" / "plain" / tail, root) is None
    assert sink.refuse(root / "fresh" / tail, root) is None
    assert listing(base) == before
    assert not (root / "fresh").exists()
