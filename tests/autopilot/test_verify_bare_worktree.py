"""--verify on a project root tracked by a bare repository with a separate
work tree (~/.claude under ~/.buvis with work tree $HOME): no .git of its own,
and a work tree full of files the repository never tracks."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from test_local_boundary import World, assert_usage, git, make_world, one_json, run_cli

GREEN = "PASS 1 FAIL 0 SKIP 0 EXIT 0"
ARTIFACT = "docs/dev/tmp/artifact.json"
LOG = "docs/dev/tmp/run.log"


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def bare(world: World) -> tuple[Path, Path, Path]:
    """(git_dir, work_tree, project): `project` sits below the work tree,
    which holds untracked files inside and outside the project."""
    git_dir, home = world.base / "dotfiles.git", world.base / "bare home"
    project = home / ".agent"
    git(world.base, "init", "-q", "--bare", str(git_dir))
    (project / "docs" / "dev" / "tmp").mkdir(parents=True)
    (project / "src.py").write_text("print('x')\n", encoding="utf-8")
    (project / "cache.bin").write_text("untracked\n", encoding="utf-8")
    (home / "notes.txt").write_text("untracked\n", encoding="utf-8")
    ctx = ("--git-dir", str(git_dir), "--work-tree", str(home))
    git(home, *ctx, "add", str(project / "src.py"))
    git(home, *ctx, "commit", "-q", "-m", "base")
    return git_dir, home, project


def verify(world: World, bare: tuple[Path, Path, Path], *flags: object):
    git_dir, home, project = bare
    head = git(home, "--git-dir", str(git_dir), "--work-tree", str(home), "rev-parse", "HEAD")
    return run_cli(world, "--verify", "--project-root", project, "--head-sha", head,
                   "--artifact", ARTIFACT, "--log", LOG, *flags,
                   "--", sys.executable, "-c", f"print({GREEN!r})")


def test_bare_backed_root_verifies_green_despite_untracked_work_tree_files(
    world: World, bare: tuple[Path, Path, Path],
) -> None:
    git_dir, home, project = bare
    proc, _ = verify(world, bare, "--git-dir", git_dir, "--work-tree", home)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    art = one_json(proc)["artifact"]
    assert art["reusable"] is True and art["dirty_paths"] == []
    assert (project / ARTIFACT).is_file()


def test_bare_backed_root_still_refuses_a_tracked_edit(
    world: World, bare: tuple[Path, Path, Path],
) -> None:
    git_dir, home, project = bare
    (project / "src.py").write_text("edited\n", encoding="utf-8")
    proc, _ = verify(world, bare, "--git-dir", git_dir, "--work-tree", home)
    assert proc.returncode == 1
    assert one_json(proc)["error"] == "dirty-tree"


def test_bare_backed_root_without_git_context_is_refused(
    world: World, bare: tuple[Path, Path, Path],
) -> None:
    proc, _ = verify(world, bare)
    assert proc.returncode != 0
    assert one_json(proc)["ok"] is False


@pytest.mark.parametrize("flag", ["--git-dir", "--work-tree"])
def test_git_dir_and_work_tree_come_as_a_pair(
    world: World, bare: tuple[Path, Path, Path], flag: str,
) -> None:
    proc, _ = verify(world, bare, flag, bare[0])
    assert_usage(proc)
