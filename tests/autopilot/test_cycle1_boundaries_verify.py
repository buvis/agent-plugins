"""Cycle-1 hardening: verification refuses output/input overlap and symlinked store dirt."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import World, git, library, make_world, one_json, run_cli, tree

GREEN = "PASS 3 FAIL 0 SKIP 1 EXIT 0"
ARTIFACT = "docs/dev/tmp/artifact.json"
LOG = "docs/dev/tmp/run.log"
SCRIPT = "docs/dev/tmp/script.py"
STORE = "docs/dev/project-management"
REFUSED = {"schema_version": 1, "ok": False, "error": "unsafe-artifact-path"}


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path.resolve())


def py(*lines: str) -> list[str]:
    return [sys.executable, "-c", "\n".join(lines)]


def verify_call(world: World, argv: list[str], *, artifact: str | Path = ARTIFACT,
                log: str | Path = LOG) -> dict[str, Any]:
    return library("verification").run_verification(
        argv=argv, project_root=world.target, head_sha=git(world.target, "rev-parse", "HEAD"),
        artifact_path=Path(artifact), log_path=Path(log))


def write_script(world: World, rel: str = SCRIPT) -> tuple[Path, str]:
    """An untracked script that prints a green summary and leaves a spawn marker."""
    marker = world.base / "spawned"
    body = f"open({str(marker)!r}, 'w').write('spawned')\nprint({GREEN!r})\n"
    path = world.target / rel
    path.write_text(body, encoding="utf-8")
    return path, body


# --- 6. output/input overlap -------------------------------------------------------------------


@pytest.mark.parametrize("overlap", ["log", "artifact"])
@pytest.mark.parametrize("spelling", ["relative", "absolute", "dotted"])
def test_verification_refuses_an_output_that_is_an_argv_input_file(
    world: World, overlap: str, spelling: str,
) -> None:
    script, body = write_script(world)
    token = {"relative": SCRIPT, "absolute": str(script),
             "dotted": "docs/dev/tmp/../tmp/script.py"}[spelling]
    paths = {"log": LOG, "artifact": ARTIFACT, overlap: SCRIPT}
    before = tree(world.target)
    report = verify_call(world, [sys.executable, token], **paths)
    assert report == REFUSED
    assert script.read_text("utf-8") == body
    assert tree(world.target) == before and not (world.base / "spawned").exists()


def test_verification_refuses_an_overlapping_absolute_output_with_a_relative_argv_token(
    world: World,
) -> None:
    script, body = write_script(world)
    report = verify_call(world, [sys.executable, SCRIPT], log=script)
    assert report == REFUSED
    assert script.read_text("utf-8") == body and not (world.base / "spawned").exists()


def test_verification_refuses_equal_log_and_artifact_paths(world: World) -> None:
    report = verify_call(world, py(f"print({GREEN!r})"), artifact=LOG, log=LOG)
    assert report == REFUSED
    assert not (world.target / LOG).exists()


@pytest.mark.parametrize("log", ["docs/dev/tmp/script.py.log", "docs/dev/tmp/script.p",
                                 "docs/dev/tmp/xscript.py"])
def test_verification_still_runs_when_the_log_only_resembles_an_argv_input(
    world: World, log: str,
) -> None:
    script, body = write_script(world)
    report = verify_call(world, [sys.executable, SCRIPT], log=log)
    assert report["ok"] is True, report
    assert report["artifact"]["log"]["path"] == log
    assert script.read_text("utf-8") == body
    assert (world.base / "spawned").read_text("utf-8") == "spawned"
    assert GREEN in (world.target / log).read_text("utf-8")


def test_verify_facade_refuses_an_output_overlapping_an_argv_input_with_exit_2(
    world: World,
) -> None:
    script, body = write_script(world)
    head = git(world.target, "rev-parse", "HEAD")
    before = tree(world.target)
    proc, _ = run_cli(world, "--verify", "--project-root", world.target, "--head-sha", head,
                      "--artifact", ARTIFACT, "--log", SCRIPT, "--", sys.executable, SCRIPT)
    assert proc.returncode == 2, (proc.returncode, proc.stderr)
    report = one_json(proc)
    assert (report["ok"], report["error"]) == (False, "unsafe-artifact-path")
    assert script.read_text("utf-8") == body and not (world.base / "spawned").exists()
    assert tree(world.target) == before
    accepted, _ = run_cli(world, "--verify", "--project-root", world.target, "--head-sha", head,
                          "--artifact", ARTIFACT, "--log", LOG, "--", sys.executable, SCRIPT)
    assert accepted.returncode == 0, accepted.stderr


# --- 7. a tracked product symlink to a modified management-store file --------------------------


def link_world(world: World) -> tuple[Path, Path, str]:
    """Commit a store file, an unrelated store file and a product symlink to the first."""
    store = world.target / STORE
    (store / "notes.md").write_text("notes v1\n", encoding="utf-8")
    (store / "other.md").write_text("other v1\n", encoding="utf-8")
    os.symlink(f"../{STORE}/notes.md", world.target / "src" / "notes-link.md")
    git(world.target, "add", "-A")
    git(world.target, "commit", "-q", "-m", "store and link")
    return store / "notes.md", store / "other.md", git(world.target, "rev-parse", "HEAD")


def mutate_during_run(path: Path) -> list[str]:
    return py(f"open({str(path)!r}, 'a').write('changed mid run\\n')", f"print({GREEN!r})")


def test_a_symlink_target_modified_during_the_run_makes_the_artifact_non_reusable(
    world: World,
) -> None:
    notes, _, head = link_world(world)
    argv = mutate_during_run(notes)
    report = verify_call(world, argv)
    assert report["ok"] is True, report
    art = report["artifact"]
    assert art["exit_code"] == 0 and art["summary"]["failed"] == 0
    assert art["reusable"] is False and art["dirty_paths"]
    assert library("verification").reuse_verdict(
        prior=art, argv=argv, project_root=world.target, head_sha=head) == ("stale", {})


def test_a_symlink_target_modified_before_the_run_is_never_reusable_evidence(
    world: World,
) -> None:
    notes, _, head = link_world(world)
    notes.write_text("notes v2 edited after the commit\n", encoding="utf-8")
    marker = world.base / "spawned"
    argv = py(f"open({str(marker)!r}, 'w').write('spawned')", f"print({GREEN!r})")
    report = verify_call(world, argv)
    assert report == {"schema_version": 1, "ok": False, "error": "dirty-tree"}
    assert not marker.exists()
    assert not (world.target / ARTIFACT).exists() and not (world.target / LOG).exists()
    verdict, _ = library("verification").reuse_verdict(
        prior=None, argv=argv, project_root=world.target, head_sha=head)
    assert verdict == "stale"


def test_an_unchanged_symlink_target_keeps_the_artifact_reusable(world: World) -> None:
    _, _, head = link_world(world)
    argv = py(f"print({GREEN!r})")
    report = verify_call(world, argv)
    art = report["artifact"]
    assert report["ok"] is True and art["reusable"] is True and art["dirty_paths"] == []
    assert library("verification").reuse_verdict(
        prior=art, argv=argv, project_root=world.target, head_sha=head) == ("reused", art)


def test_a_modified_store_file_no_product_symlink_names_keeps_the_artifact_reusable(
    world: World,
) -> None:
    _, other, head = link_world(world)
    argv = mutate_during_run(other)
    report = verify_call(world, argv)
    art = report["artifact"]
    assert report["ok"] is True and art["reusable"] is True and art["dirty_paths"] == []
    assert library("verification").reuse_verdict(
        prior=art, argv=argv, project_root=world.target, head_sha=head) == ("reused", art)
