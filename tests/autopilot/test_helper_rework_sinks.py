"""Cycle-1 rework: sink acquisition, ownership, late-failure cleanup and root aliases."""

from __future__ import annotations

import json
import os
import signal
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from test_helper_recovery_v2 import ARTIFACT, GITDIR, MARKER_CHILD, OUTSIDE, child_argv
from test_helper_recovery_v2 import commit_repo, failure_shape, reap, run_gate, spy_on_spawn
from test_helper_recovery_v2_sinks import ALT_ARTIFACT, APP_BODY, CHILD_OUTPUT, PRIOR_ARTIFACT
from test_helper_recovery_v2_sinks import break_artifact_sink, green_artifact, seed, unspawnable
from test_local_boundary import World, git, library, make_world

FRESH_LOG = b"FRESH-LOG-BYTES-11a4\n"
OTHER_LOG = b"FRESH-LOG-BYTES-11a5\n"  # near miss: differs from FRESH_LOG in one byte
SWAP_EXEC = b"SWAPPED-EXECUTABLE-6d10\n"
SWAP_LINKED = b"SWAPPED-HARD-LINKED-6d11\n"
SWAP_PLAIN = b"SWAPPED-PLAIN-FILE-6d12\n"
LEAF_ONE = b"REPLACEMENT-LEAF-ONE-73c8\n"
LEAF_TWO = b"REPLACEMENT-LEAF-TWO-73c9\n"
DESCENDANT_CHILD = (
    "import pathlib, subprocess, sys\n"
    "late, pidfile, payload = sys.argv[1:4]\n"
    "code = ('import pathlib, sys, time\\n'\n"
    "        'time.sleep(1.5)\\n'\n"
    "        'pathlib.Path(sys.argv[1]).write_text(sys.argv[2], encoding=\"utf-8\")\\n')\n"
    "proc = subprocess.Popen([sys.executable, '-I', '-c', code, late, payload],\n"
    "                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,\n"
    "                        stderr=subprocess.DEVNULL)\n"
    "pathlib.Path(pidfile).write_text(str(proc.pid), encoding='utf-8')\n"
    "print('PASS 2 FAIL 0 SKIP 1 EXIT 0')\n"
)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def gate_at(world: World, argv: list[str], root: Path, log: Path, artifact: Path) -> dict:
    """The gate with every path spelled exactly as given, not as run_gate spells them."""
    return library("verification").run_verification(
        argv=argv, project_root=root, head_sha=git(world.target, "rev-parse", "HEAD"),
        artifact_path=artifact, log_path=log, timeout=60,
    )


def patch_opener(monkeypatch: pytest.MonkeyPatch, opener: Callable[..., Any]) -> None:
    for module in (library("verification"), library("log_sink_refusal")):
        monkeypatch.setattr(module, "_open_log_sink", opener)


def swap_log_before_open(monkeypatch: pytest.MonkeyPatch, log: Path,
                         replace: Callable[[Path], None]) -> list[Path]:
    """Replaces the log's file once, after the path was judged and before its sink opens."""
    real = library("log_sink_refusal")._open_log_sink
    swapped: list[Path] = []

    def opener(log_path: Any, repo_root: Any, *args: Any, **kwargs: Any) -> Any:
        if Path(log_path).resolve() == log.resolve() and not swapped:
            swapped.append(log)
            replace(log)
        return real(log_path, repo_root, *args, **kwargs)

    patch_opener(monkeypatch, opener)
    return swapped


def swap_artifact_after_open(monkeypatch: pytest.MonkeyPatch, artifact: Path,
                             payload: bytes) -> list[Path]:
    """Puts a different file under the artifact's name once its sink is open."""
    real = library("log_sink_refusal")._open_log_sink
    swapped: list[Path] = []

    def opener(log_path: Any, repo_root: Any, *args: Any, **kwargs: Any) -> Any:
        handle = real(log_path, repo_root, *args, **kwargs)
        if Path(log_path).resolve() == artifact.resolve() and not swapped:
            swapped.append(artifact)
            artifact.unlink()
            artifact.write_bytes(payload)
        return handle

    patch_opener(monkeypatch, opener)
    return swapped


def stored_record(artifact: Path) -> dict | None:
    """Whatever the artifact path holds, offered for reuse as a prior record."""
    try:
        record = json.loads(artifact.read_bytes())
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def verdict(world: World, prior: dict | None, argv: list[str]) -> tuple[str, dict]:
    return library("verification").reuse_verdict(
        prior=prior, argv=argv, project_root=world.target,
        head_sha=git(world.target, "rev-parse", "HEAD"),
    )


# --- R-B1. a failed spawn invents no log --------------------------------------------------------


@pytest.mark.parametrize("kind", ["absent-program", "unexecutable-program"])
def test_an_absent_log_stays_absent_after_a_failed_spawn(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    log = world.target / "logs" / f"{kind}-fresh.log"
    report = run_gate(world, unspawnable(tmp_path, kind), log=log)
    failure_shape(report, "spawn-failed")
    assert not log.exists(), "the failed spawn invented a log that did not exist before"
    assert not (world.target / ARTIFACT).exists()
    marker = tmp_path / f"{kind}-fresh-marker.txt"
    argv = child_argv(tmp_path, f"{kind}-fresh-child", MARKER_CHILD, marker)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        accepted = run_gate(world, argv, log=log)
    finally:
        reap(children)
    assert accepted["ok"] is True, accepted
    assert CHILD_OUTPUT in log.read_bytes(), "a child that starts must still write the log"


@pytest.mark.parametrize(("kind", "prior_log", "prior_artifact"),
                         [("absent-program", FRESH_LOG, PRIOR_ARTIFACT),
                          ("unexecutable-program", OTHER_LOG, ALT_ARTIFACT)])
def test_a_failed_spawn_keeps_an_existing_log_and_artifact_byte_identical(
    world: World, tmp_path: Path, isolated_git: None, kind: str,
    prior_log: bytes, prior_artifact: bytes,
) -> None:
    log = seed(world.target / "logs" / f"{kind}-kept.log", prior_log)
    artifact = seed(world.target / ARTIFACT, prior_artifact)
    report = run_gate(world, unspawnable(tmp_path, kind), log=log, artifact=artifact)
    failure_shape(report, "spawn-failed")
    assert log.read_bytes() == prior_log
    assert artifact.read_bytes() == prior_artifact


# --- R-B2. an unsafe sink inode is refused on what was opened -----------------------------------


def chmod_in_place(path: Path) -> None:
    path.chmod(0o755)


def link_in_place(path: Path) -> None:
    os.link(path, path.with_name(path.name + ".twin"))


def leave_untouched(path: Path) -> None:
    return None


def swap_in_other_file(path: Path) -> None:
    staged = path.with_name(path.name + ".staged")
    staged.write_bytes(SWAP_PLAIN)
    staged.chmod(0o644)
    os.replace(staged, path)


@pytest.mark.parametrize(("case", "seeded", "mutate", "accepted"),
                         [("executable", SWAP_EXEC, chmod_in_place, False),
                          ("hard-linked", SWAP_LINKED, link_in_place, False),
                          ("untouched", FRESH_LOG, leave_untouched, True),
                          ("swapped-file", OTHER_LOG, swap_in_other_file, False)])
def test_a_log_is_judged_by_the_file_opened_not_by_the_path_judged_earlier(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    case: str, seeded: bytes, mutate: Callable[[Path], None], accepted: bool,
) -> None:
    log = seed(world.target / "logs" / f"judged-{case}.log", seeded)
    log.chmod(0o644)
    marker = tmp_path / f"judged-{case}-marker.txt"
    argv = child_argv(tmp_path, f"judged-{case}-child", MARKER_CHILD, marker)
    swapped = swap_log_before_open(monkeypatch, log, mutate)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        report = run_gate(world, argv, log=log)
    finally:
        reap(children)
    assert swapped == [log], "the window before the sink opened was never reached"
    if accepted:
        assert report["ok"] is True, report
        assert CHILD_OUTPUT in log.read_bytes()
        assert marker.is_file()
        return
    failure_shape(report, "sink-failed")
    assert not marker.exists(), "the child ran against an unsafe sink"
    expected = SWAP_PLAIN if case == "swapped-file" else seeded
    assert log.read_bytes() == expected, "the refused run rewrote the log"
    assert not (world.target / ARTIFACT).exists()


# --- R-B3. ownership of a created leaf ----------------------------------------------------------


@pytest.mark.parametrize("prior", [PRIOR_ARTIFACT, ALT_ARTIFACT, None],
                         ids=["existing-one", "existing-two", "absent"])
def test_an_artifact_leaf_survives_only_when_it_existed_before_a_run_that_wrote_no_record(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    prior: bytes | None,
) -> None:
    artifact = world.target / "docs" / "dev" / "tmp" / "owned.json"
    if prior is not None:
        seed(artifact, prior)
    log = world.target / "logs" / "owned.log"
    report = run_gate(world, unspawnable(tmp_path, "absent-program"), log=log, artifact=artifact)
    failure_shape(report, "spawn-failed")
    if prior is None:
        assert not artifact.exists(), "the run kept a leaf it never wrote a record into"
    else:
        assert artifact.read_bytes() == prior, "the run lost or rewrote a pre-existing artifact"
    marker = tmp_path / "owned-marker.txt"
    argv = child_argv(tmp_path, "owned-child", MARKER_CHILD, marker)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        accepted = run_gate(world, argv, log=log, artifact=artifact)
    finally:
        reap(children)
    assert accepted["ok"] is True, accepted
    assert json.loads(artifact.read_bytes())["argv"] == argv


@pytest.mark.parametrize(("existing", "payload"), [(False, LEAF_ONE), (True, LEAF_TWO)],
                         ids=["created-by-run", "pre-existing"])
def test_a_different_file_that_took_the_artifacts_name_survives_a_run_without_a_record(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    existing: bool, payload: bytes,
) -> None:
    artifact = world.target / "docs" / "dev" / "tmp" / f"leaf-{existing}.json"
    if existing:
        seed(artifact, PRIOR_ARTIFACT)
    swapped = swap_artifact_after_open(monkeypatch, artifact, payload)
    log = world.target / "logs" / f"leaf-{existing}.log"
    report = run_gate(world, unspawnable(tmp_path, "absent-program"), log=log, artifact=artifact)
    assert swapped == [artifact], "the artifact leaf was never replaced after its sink opened"
    failure_shape(report, "spawn-failed")
    assert artifact.is_file(), "cleanup deleted the replacement by its name"
    assert artifact.read_bytes() == payload, "cleanup rewrote the replacement file"


# --- R-B4. a failed artifact write or close leaves no reusable record ---------------------------


@pytest.mark.parametrize(("slug", "fail_write", "fail_close"),
                         [("sink-close-failed", None, True), ("sink-write-failed", 0, False)])
def test_a_failed_artifact_write_or_close_leaves_nothing_reuse_verdict_accepts(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    slug: str, fail_write: int | None, fail_close: bool,
) -> None:
    artifact = world.target / ARTIFACT
    log = world.target / "docs" / "dev" / "tmp" / f"{slug}.log"
    marker = tmp_path / f"{slug}-marker.txt"
    argv = child_argv(tmp_path, f"{slug}-child", MARKER_CHILD, marker)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        first = run_gate(world, argv, log=log)
        assert first["ok"] is True, first
        green_artifact(first, world.target, argv, artifact, log)
        genuine = stored_record(artifact)
        assert verdict(world, genuine, argv) == ("reused", genuine)
        break_artifact_sink(monkeypatch, artifact, fail_write_after=fail_write,
                            fail_close=fail_close)
        report = run_gate(world, argv, log=log)
    finally:
        reap(children)
    failure_shape(report, slug)
    assert verdict(world, stored_record(artifact), argv) == ("stale", {})


# --- R-B5. a late sink failure terminates descendants the child left running --------------------


def kill_descendant(pidfile: Path, late: Path) -> None:
    """The test owns the descendant: end it unless it already finished its work."""
    try:
        pid = int(pidfile.read_text("utf-8"))
    except (OSError, ValueError):
        return
    if late.exists():
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def test_a_late_artifact_close_failure_ends_the_descendant_the_child_left_running(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    late, pidfile = tmp_path / "late-marker.txt", tmp_path / "descendant.pid"
    argv = child_argv(tmp_path, "descendant-child", DESCENDANT_CHILD, late, pidfile, "LATE-ONE")
    break_artifact_sink(monkeypatch, world.target / ARTIFACT, fail_close=True)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        report = run_gate(world, argv, log=world.target / "logs" / "descendant.log")
        failure_shape(report, "sink-close-failed")
        assert pidfile.is_file(), "the child never started its descendant"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            assert not late.exists(), "the descendant outlived the late sink failure"
            time.sleep(0.05)
    finally:
        kill_descendant(pidfile, late)
        reap(children)


def test_a_descendant_the_child_left_running_still_works_when_no_sink_fails(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control: without a sink failure the same descendant does write its late marker."""
    late, pidfile = tmp_path / "control-late.txt", tmp_path / "control.pid"
    argv = child_argv(tmp_path, "control-child", DESCENDANT_CHILD, late, pidfile, "LATE-TWO")
    children = spy_on_spawn(monkeypatch, argv)
    try:
        report = run_gate(world, argv, log=world.target / "logs" / "control.log")
        assert report["ok"] is True, report
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline and not late.exists():
            time.sleep(0.05)
        assert late.read_text("utf-8") == "LATE-TWO"
    finally:
        kill_descendant(pidfile, late)
        reap(children)


# --- R-B6. refuse judges a nested repository's .git pointer by location ------------------------


def test_refuse_calls_a_nested_repositorys_git_pointer_outside_without_reading_it(
    tmp_path: Path, isolated_git: None,
) -> None:
    base = tmp_path.resolve()
    project = commit_repo(base / "repo", {"src/app.py": "a\n"})
    worktree = base / "wt"
    git(project, "worktree", "add", "-q", "-b", "wt", str(worktree))
    sink = library("log_sink_refusal")
    for name, pointee in (("nested-one", project / ".git"),
                          ("nested-two", project / ".git" / "worktrees" / "wt")):
        nested = project / name
        nested.mkdir()
        (nested / ".git").write_text(f"gitdir: {pointee}\n", encoding="utf-8")
        assert sink.refuse(nested / ".git", project) == OUTSIDE, name
    assert sink.refuse(project / "logs" / "fresh.log", project) is None
    assert sink.refuse(worktree / ".git", worktree) == GITDIR


# --- R-B7. unresolved and resolved spellings of the project root behave alike -------------------


def token_child(tmp_path: Path, name: str, token: str, marker: Path) -> list[str]:
    return child_argv(tmp_path, name, MARKER_CHILD + f"print('{token}')\n", marker)


def alias_of(world: World, tmp_path: Path) -> Path:
    alias = tmp_path / "root-alias"
    alias.symlink_to(world.target.resolve(), target_is_directory=True)
    return alias


@pytest.mark.parametrize(("case", "token"), [("unresolved-root", "ROOT-TOKEN-0f21"),
                                             ("unresolved-outputs", "ROOT-TOKEN-0f22")])
def test_a_run_is_accepted_when_the_root_and_the_output_paths_are_spelled_differently(
    world: World, tmp_path: Path, isolated_git: None, case: str, token: str,
) -> None:
    resolved, alias = world.target.resolve(), alias_of(world, tmp_path)
    root, spelled = (alias, resolved) if case == "unresolved-root" else (resolved, alias)
    marker = tmp_path / f"{case}-marker.txt"
    argv = token_child(tmp_path, f"{case}-child", token, marker)
    report = gate_at(world, argv, root, spelled / "logs" / f"{case}.log", spelled / ARTIFACT)
    assert report["ok"] is True, report
    assert marker.read_text("utf-8") == str(resolved)
    assert token.encode() in (resolved / "logs" / f"{case}.log").read_bytes()
    assert json.loads((resolved / ARTIFACT).read_bytes())["argv"] == argv


@pytest.mark.parametrize("case", ["unresolved-root", "unresolved-outputs", "both-resolved"])
def test_a_tracked_log_is_refused_under_every_spelling_of_the_project_root(
    world: World, tmp_path: Path, isolated_git: None, case: str,
) -> None:
    resolved, alias = world.target.resolve(), alias_of(world, tmp_path)
    root = alias if case == "unresolved-root" else resolved
    spelled = alias if case == "unresolved-outputs" else resolved
    marker = tmp_path / f"{case}-refused-marker.txt"
    argv = token_child(tmp_path, f"{case}-refused-child", "REFUSED-TOKEN", marker)
    report = gate_at(world, argv, root, spelled / "src" / "app.py", spelled / ARTIFACT)
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran against a tracked output path"
    assert (resolved / "src" / "app.py").read_bytes() == APP_BODY
    accepted = gate_at(world, argv, root, spelled / "logs" / f"{case}.log", spelled / ARTIFACT)
    assert accepted["ok"] is True, accepted
