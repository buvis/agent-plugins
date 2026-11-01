"""Bounded verification runs real argv and judges explicit artifact reuse without workflow state."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
REAL_RUN = subprocess.run
PM = "docs/dev/project-management/"
SCRATCH = "docs/dev/tmp/"
BASE_FILES = {
    "src/app.py": "print('app')\n",
    PM + "notes.md": "store notes\n",
    SCRATCH + "keep.txt": "keep\n",
    "logs/tracked.log": "tracked\n",
}
ARTIFACT_KEYS = {
    "schema_version", "kind", "argv", "head_sha", "exit_code", "summary", "timed_out",
    "output_limit_exceeded", "dirty_paths", "head_moved", "log", "reusable",
}
SUMMARY_KEYS = {"passed", "failed", "skipped", "exit_code"}
GREEN = "PASS 3 FAIL 0 SKIP 1 EXIT 0"


def load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


@pytest.fixture
def verification():
    return load("verification")


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    env = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": f"{tmp_path}:{tmp_path.resolve()}",
        "GIT_AUTHOR_NAME": "Tess",
        "GIT_AUTHOR_EMAIL": "tess@example.invalid",
        "GIT_COMMITTER_NAME": "Tess",
        "GIT_COMMITTER_EMAIL": "tess@example.invalid",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def git(cwd: Path, *args: str) -> str:
    result = REAL_RUN(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip()


def write(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    write(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "master")
    commit(root, BASE_FILES, "base")
    return root


def script(*lines: str) -> list[str]:
    return [sys.executable, "-c", "\n".join(lines)]


def marker_script(marker: Path) -> list[str]:
    return script(f"open({str(marker)!r}, 'w').write('spawned')", f"print({GREEN!r})")


def paths(repo: Path) -> tuple[Path, Path]:
    return repo / SCRATCH / "artifact.json", repo / SCRATCH / "run.log"


def run(verification, repo: Path, argv: list[str], **overrides):
    artifact, log = paths(repo)
    kwargs = {
        "argv": argv, "project_root": repo, "head_sha": head(repo),
        "artifact_path": artifact, "log_path": log, **overrides,
    }
    return verification.run_verification(**kwargs)


def checked_artifact(result: dict, repo: Path, artifact_path: Path, log_path: Path) -> dict:
    assert set(result) == {"schema_version", "ok", "artifact", "controller_required"}
    assert result["schema_version"] == 1 and result["ok"] is True
    assert result["controller_required"] is True
    art = result["artifact"]
    assert set(art) == ARTIFACT_KEYS
    assert art["schema_version"] == 1 and art["kind"] == "verification-artifact-v1"
    assert art["exit_code"] is None or type(art["exit_code"]) is int
    if art["summary"] is not None:
        assert set(art["summary"]) == SUMMARY_KEYS
        assert all(type(value) is int for value in art["summary"].values())
    for key in ("timed_out", "output_limit_exceeded", "head_moved", "reusable"):
        assert type(art[key]) is bool
    assert all(isinstance(item, str) for item in art["dirty_paths"])
    assert set(art["log"]) == {"path", "sha256"}
    assert (repo / art["log"]["path"]).resolve() == log_path.resolve()
    assert art["log"]["sha256"] == hashlib.sha256(log_path.read_bytes()).hexdigest()
    assert json.loads(artifact_path.read_bytes()) == art
    return art


def checked_run(verification, repo: Path, argv: list[str], **overrides) -> dict:
    result = run(verification, repo, argv, **overrides)
    artifact, log = paths(repo)
    return checked_artifact(result, repo, artifact, log)


def snapshot(*items: Path) -> dict[Path, bytes | None]:
    return {item: item.read_bytes() if item.exists() else None for item in items}


def refused(call) -> bool:
    try:
        result = call()
    except (ValueError, TypeError):
        return True
    return isinstance(result, dict) and result.get("ok") is False


def test_gate_bounds_match_the_contract(verification) -> None:
    assert verification.GATE_TIMEOUT_S == 1800
    assert verification.GATE_OUTPUT_CAP == 2_000_000
    assert verification.GATE_LOG_CAP == 20_000_000


def test_green_run_writes_exact_artifact_with_hashed_log_of_real_streams(
    verification, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TESS_MARK", "tess-7")
    argv = script(
        "import os, sys",
        "sys.stdout.write('OUT-MARK ' + os.environ['TESS_MARK'] + ' ' + os.getcwd() + '\\n')",
        "sys.stdout.flush()",
        "sys.stderr.write('ERR-MARK\\n')",
        "sys.stderr.flush()",
        f"print({GREEN!r})",
    )
    art = checked_run(verification, repo, argv)
    log = paths(repo)[1].read_bytes()
    assert f"OUT-MARK tess-7 {repo.resolve()}\n".encode() in log
    assert b"ERR-MARK\n" in log
    assert art["argv"] == argv and art["head_sha"] == head(repo)
    assert art["exit_code"] == 0
    assert art["summary"] == {"passed": 3, "failed": 0, "skipped": 1, "exit_code": 0}
    assert art["timed_out"] is False and art["output_limit_exceeded"] is False
    assert art["dirty_paths"] == [] and art["head_moved"] is False
    assert art["reusable"] is True


def test_failing_command_still_returns_attempted_run_for_its_own_head(
    verification, repo: Path
) -> None:
    second = commit(repo, {"src/app.py": "print('second')\n"}, "second")
    argv = script("import sys", "print('PASS 7 FAIL 2 SKIP 0 EXIT 1')", "sys.exit(3)")
    art = checked_run(verification, repo, argv, head_sha=second)
    assert art["head_sha"] == second
    assert art["exit_code"] == 3
    assert art["summary"] == {"passed": 7, "failed": 2, "skipped": 0, "exit_code": 1}


@pytest.mark.parametrize(("line", "code", "summary_exit"), [
    ("PASS 1 FAIL 0 SKIP 0 EXIT 5", 0, 5),
    ("PASS 1 FAIL 0 SKIP 0 EXIT 0", 2, 0),
], ids=["summary-fails-process-passes", "summary-passes-process-fails"])
def test_actual_exit_is_kept_apart_from_summary_exit(
    verification, repo: Path, line: str, code: int, summary_exit: int
) -> None:
    art = checked_run(verification, repo, script("import sys", f"print({line!r})", f"sys.exit({code})"))
    assert art["exit_code"] == code
    assert art["summary"]["exit_code"] == summary_exit


def test_last_complete_summary_line_wins(verification, repo: Path) -> None:
    argv = script(
        "print('PASS 1 FAIL 4 SKIP 0 EXIT 1')",
        "print('== PASS 9 FAIL 0 SKIP 2 EXIT 0 ==')",
        "print('PASS 8 FAIL 1 SKIP 2')",
        "print('PASS x FAIL 0 SKIP 0 EXIT 0')",
    )
    art = checked_run(verification, repo, argv)
    assert art["summary"] == {"passed": 9, "failed": 0, "skipped": 2, "exit_code": 0}


@pytest.mark.parametrize(("lines", "code", "expected_log"), [
    (["import sys", "print('just output')", "print('PASS 2 FAIL 0 SKIP 0')",
      "sys.stderr.write('boom\\n')", "sys.exit(4)"], 4, [b"just output\n", b"boom\n"]),
    (["pass"], 0, []),
], ids=["output-without-summary", "empty-output"])
def test_command_without_summary_keeps_actual_output_and_exit_but_is_not_reusable(
    verification, repo: Path, lines: list[str], code: int, expected_log: list[bytes]
) -> None:
    art = checked_run(verification, repo, script(*lines))
    assert art["summary"] is None
    assert art["exit_code"] == code
    assert art["reusable"] is False
    log = paths(repo)[1].read_bytes()
    assert all(part in log for part in expected_log)
    if not expected_log:
        assert log == b""


def test_argv_tokens_reach_the_process_verbatim_without_a_shell(verification, repo: Path) -> None:
    tokens = ["a  b", " lead", "$HOME", "*", "x;echo INJECTED", "naïve"]
    argv = [*script("import json, sys", "print(json.dumps(sys.argv[1:]))", f"print({GREEN!r})"), *tokens]
    art = checked_run(verification, repo, argv)
    assert art["argv"] == argv
    log = paths(repo)[1].read_bytes()
    assert json.loads(log.splitlines()[0]) == tokens
    assert b"\nINJECTED\n" not in log


@pytest.mark.parametrize("timeout", [
    True, False, 0, 0.0, -1, float("nan"), float("inf"), 1800.001, 1801, "10", None,
], ids=["true", "false", "zero", "zero-float", "negative", "nan", "inf", "over-max-float",
        "over-max", "string", "none"])
def test_invalid_timeout_is_refused_before_spawn(
    verification, repo: Path, tmp_path: Path, timeout
) -> None:
    marker = tmp_path / "spawned"
    assert refused(lambda: run(verification, repo, marker_script(marker), timeout=timeout))
    assert not marker.exists()
    assert snapshot(*paths(repo)) == dict.fromkeys(paths(repo))


@pytest.mark.parametrize("timeout", [1800, 1800.0, 5, 0.5], ids=["max-int", "max-float", "small-int", "fraction"])
def test_finite_timeout_within_bounds_is_accepted(
    verification, repo: Path, tmp_path: Path, timeout
) -> None:
    marker = tmp_path / "spawned"
    art = checked_run(verification, repo, marker_script(marker), timeout=timeout)
    assert marker.read_text() == "spawned"
    assert art["timed_out"] is False


@pytest.mark.parametrize("argv", [[], [""], ["", "-c", "print(1)"]], ids=["empty", "empty-exe", "empty-exe-with-args"])
def test_empty_argv_or_executable_is_refused_before_writing(verification, repo: Path, argv) -> None:
    assert refused(lambda: run(verification, repo, argv))
    assert snapshot(*paths(repo)) == dict.fromkeys(paths(repo))


@pytest.mark.parametrize(("dirt", "is_refused"), [
    ({"src/app.py": "print('edited')\n"}, True),
    ({"src/new.py": "x = 1\n"}, True),
    ({"docs/dev/project-management-old/x.md": "x\n"}, True),
    ({PM + "notes.md": "edited store\n"}, False),
    ({SCRATCH + "scratch.txt": "s\n"}, False),
], ids=["tracked-product-edit", "untracked-product", "store-name-near-miss", "store-edit", "scratch-file"])
def test_pre_spawn_dirt_outside_store_and_scratch_refuses_without_effects(
    verification, repo: Path, tmp_path: Path, dirt: dict[str, str], is_refused: bool
) -> None:
    write(repo, dirt)
    marker = tmp_path / "spawned"
    result = run(verification, repo, marker_script(marker))
    if not is_refused:
        art = checked_artifact(result, repo, *paths(repo))
        assert art["dirty_paths"] == [] and art["reusable"] is True
        assert marker.exists()
        return
    assert result["schema_version"] == 1 and result["ok"] is False
    assert result["error"] == "dirty-tree"
    assert not marker.exists()
    assert snapshot(*paths(repo)) == dict.fromkeys(paths(repo))


@pytest.mark.parametrize("which", ["previous", "unknown"])
def test_head_sha_mismatch_refuses_before_spawn(
    verification, repo: Path, tmp_path: Path, which: str
) -> None:
    base = head(repo)
    commit(repo, {"src/app.py": "print('moved')\n"}, "moved")
    stale_sha = base if which == "previous" else "0" * 40
    marker = tmp_path / "spawned"
    result = run(verification, repo, marker_script(marker), head_sha=stale_sha)
    assert result["schema_version"] == 1 and result["ok"] is False
    assert result["error"] == "head-moved"
    assert not marker.exists()
    assert snapshot(*paths(repo)) == dict.fromkeys(paths(repo))


def _symlinked_parent(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    os.symlink(repo / "logs", repo / SCRATCH / "linkdir")
    return paths(repo)[0], repo / SCRATCH / "linkdir" / "run.log"


def _executable_artifact(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    target = repo / SCRATCH / "exec.json"
    target.write_text("{}")
    target.chmod(0o755)
    return target, paths(repo)[1]


def _nested_repo_log(repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    inner = repo / SCRATCH / "inner"
    inner.mkdir()
    git(inner, "init", "-q")
    return paths(repo)[0], inner / "run.log"


UNSAFE = {
    "log-outside-root": lambda r, t: (paths(r)[0], t / "outside.log"),
    "artifact-outside-root": lambda r, t: (t / "outside.json", paths(r)[1]),
    "log-escapes-root": lambda r, t: (paths(r)[0], r / SCRATCH / ".." / ".." / ".." / ".." / "x.log"),
    "artifact-in-live-state": lambda r, t: (r / PM / "autopilot" / "artifact.json", paths(r)[1]),
    "log-in-store": lambda r, t: (paths(r)[0], r / PM / "run.log"),
    "log-in-git-dir": lambda r, t: (paths(r)[0], r / ".git" / "run.log"),
    "tracked-log": lambda r, t: (paths(r)[0], r / "logs" / "tracked.log"),
    "tracked-artifact": lambda r, t: (r / "logs" / "tracked.log", paths(r)[1]),
    "equal-paths": lambda r, t: (r / SCRATCH / "same.out", r / SCRATCH / "same.out"),
    "symlinked-log-parent": _symlinked_parent,
    "executable-artifact": _executable_artifact,
    "nested-repo-log": _nested_repo_log,
}


@pytest.mark.parametrize("case", sorted(UNSAFE))
def test_unsafe_artifact_or_log_path_refuses_before_spawn_and_writes_nothing(
    verification, repo: Path, tmp_path: Path, case: str
) -> None:
    artifact, log = UNSAFE[case](repo, tmp_path)
    before = snapshot(artifact, log)
    marker = tmp_path / "spawned"
    result = run(verification, repo, marker_script(marker), artifact_path=artifact, log_path=log)
    assert result["schema_version"] == 1 and result["ok"] is False
    assert result["error"] == "unsafe-artifact-path"
    assert not marker.exists()
    assert snapshot(artifact, log) == before
    assert not (repo / PM / "autopilot").exists()


def test_safe_log_outside_scratch_is_accepted_as_the_near_miss(verification, repo: Path) -> None:
    artifact, log = repo / SCRATCH / "a.json", repo / "logs" / "fresh.log"
    result = run(verification, repo, script(f"print({GREEN!r})"), artifact_path=artifact, log_path=log)
    art = checked_artifact(result, repo, artifact, log)
    assert art["dirty_paths"] == [] and art["reusable"] is True


@pytest.mark.parametrize(("created", "dirty"), [
    ("src/generated.py", ["src/generated.py"]),
    (SCRATCH + "out.txt", []),
], ids=["product-dirt", "scratch-only"])
def test_post_run_dirt_invalidates_reusable_evidence(
    verification, repo: Path, created: str, dirty: list[str]
) -> None:
    target = repo / created
    argv = script(f"open({str(target)!r}, 'w').write('x')", f"print({GREEN!r})")
    art = checked_run(verification, repo, argv)
    assert art["dirty_paths"] == dirty
    assert art["head_moved"] is False
    assert art["reusable"] is (not dirty)


def test_post_run_head_movement_invalidates_reusable_evidence(verification, repo: Path) -> None:
    before = head(repo)
    argv = script(
        "import subprocess",
        "subprocess.run(['git', '-c', 'user.name=T', '-c', 'user.email=t@example.invalid',"
        " 'commit', '-q', '--allow-empty', '-m', 'moved'], check=True)",
        f"print({GREEN!r})",
    )
    art = checked_run(verification, repo, argv, head_sha=before)
    assert head(repo) != before
    assert art["head_sha"] == before
    assert art["head_moved"] is True and art["reusable"] is False


@pytest.mark.parametrize("summary_first", [True, False], ids=["summary-before-cap", "summary-in-tail"])
def test_retained_stdout_is_only_the_final_output_cap_bytes(
    verification, repo: Path, summary_first: bool
) -> None:
    rows = verification.GATE_OUTPUT_CAP // 100 + 41
    flood = f"sys.stdout.write(('x' * 99 + '\\n') * {rows})"
    green = f"print({GREEN!r})"
    lines = ["import sys", green, flood] if summary_first else ["import sys", flood, green]
    art = checked_run(verification, repo, script(*lines))
    assert art["exit_code"] == 0
    if summary_first:
        assert art["summary"] is None and art["reusable"] is False
    else:
        assert art["summary"] == {"passed": 3, "failed": 0, "skipped": 1, "exit_code": 0}
    assert paths(repo)[1].stat().st_size == rows * 100 + len(GREEN) + 1


def test_output_overflow_caps_log_kills_command_and_fails(
    verification, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verification, "GATE_LOG_CAP", 8192)
    argv = script(
        "import sys, time",
        "sys.stdout.write('FIRST-MARK\\n'); sys.stdout.flush()",
        f"sys.stdout.write({GREEN!r} + '\\n'); sys.stdout.flush()",
        "block = b'o' * 65536",
        "for _ in range(64):",
        "    sys.stdout.buffer.write(block); sys.stdout.buffer.flush()",
        "    sys.stderr.buffer.write(block); sys.stderr.buffer.flush()",
        "time.sleep(30)",
    )
    started = time.monotonic()
    art = checked_run(verification, repo, argv)
    assert time.monotonic() - started < 20
    log = paths(repo)[1].read_bytes()
    assert len(log) == 8192
    assert log.startswith(b"FIRST-MARK\n")
    assert art["output_limit_exceeded"] is True
    assert art["reusable"] is False


def test_output_under_log_cap_is_kept_whole_and_not_flagged(
    verification, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(verification, "GATE_LOG_CAP", 8192)
    argv = script(
        "import sys",
        "sys.stdout.write('o' * 3000); sys.stdout.flush()",
        "sys.stderr.write('e' * 3000); sys.stderr.flush()",
        f"sys.stdout.write('\\n' + {GREEN!r} + '\\n')",
    )
    art = checked_run(verification, repo, argv)
    assert len(paths(repo)[1].read_bytes()) == 6000 + len(GREEN) + 2
    assert art["output_limit_exceeded"] is False
    assert art["reusable"] is True


def _gone(pid: int, wait_s: float) -> bool:
    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def test_timeout_kills_and_reaps_the_whole_process_group(
    verification, repo: Path, tmp_path: Path
) -> None:
    pidfile = tmp_path / "grandchild.pid"
    argv = script(
        "import subprocess, sys, time",
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
        f"open({str(pidfile)!r}, 'w').write(str(child.pid))",
        f"print({GREEN!r}, flush=True)",
        "time.sleep(60)",
    )
    started = time.monotonic()
    art = checked_run(verification, repo, argv, timeout=1.5)
    assert time.monotonic() - started < 20
    assert art["timed_out"] is True
    assert art["reusable"] is False
    assert _gone(int(pidfile.read_text()), 5.0)


REUSE_ARGV = [*script(f"print({GREEN!r})"), "a  b"]


@pytest.fixture
def prior(verification, repo: Path) -> dict:
    art = checked_run(verification, repo, REUSE_ARGV)
    assert art["reusable"] is True
    for item in paths(repo):
        item.unlink()
    return art


def verdict(verification, repo: Path, prior, argv=None, head_sha=None) -> tuple[str, dict]:
    return verification.reuse_verdict(
        prior=prior, argv=REUSE_ARGV if argv is None else argv,
        project_root=repo, head_sha=head(repo) if head_sha is None else head_sha,
    )


@pytest.mark.parametrize("change", ["none", "store-commit", "store-dirt"])
def test_green_artifact_is_reused_across_store_only_changes(
    verification, repo: Path, prior: dict, change: str
) -> None:
    if change == "store-commit":
        commit(repo, {PM + "notes.md": "later notes\n"}, "store only")
    elif change == "store-dirt":
        write(repo, {PM + "draft.md": "draft\n"})
    assert verdict(verification, repo, copy.deepcopy(prior)) == ("reused", prior)


def _mutate(art: dict, path: tuple, value) -> dict:
    changed = copy.deepcopy(art)
    target = changed
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return changed


MUTATIONS = {
    "kind-near-miss": (("kind",), "verification-artifact-v2"),
    "schema-bool": (("schema_version",), True),
    "schema-two": (("schema_version",), 2),
    "missing-reusable": (("reusable",), KeyError),
    "extra-field": (("extra",), 1),
    "reusable-false": (("reusable",), False),
    "reusable-int": (("reusable",), 1),
    "output-limit": (("output_limit_exceeded",), True),
    "exit-nonzero": (("exit_code",), 1),
    "exit-null": (("exit_code",), None),
    "exit-string": (("exit_code",), "0"),
    "summary-null": (("summary",), None),
    "summary-missing-passed": (("summary", "passed"), KeyError),
    "summary-passed-null": (("summary", "passed"), None),
    "summary-failed": (("summary", "failed"), 1),
    "summary-exit": (("summary", "exit_code"), 1),
    "argv-not-list": (("argv",), "python"),
}


@pytest.mark.parametrize("case", sorted(MUTATIONS))
def test_malformed_or_failed_artifact_is_stale(verification, repo: Path, prior: dict, case: str) -> None:
    path, value = MUTATIONS[case]
    assert verdict(verification, repo, _mutate(prior, path, value)) == ("stale", {})


@pytest.mark.parametrize("bad", [None, "artifact", [], {}], ids=["none", "string", "list", "empty"])
def test_missing_or_non_object_prior_is_stale(verification, repo: Path, bad) -> None:
    assert verdict(verification, repo, bad) == ("stale", {})


@pytest.mark.parametrize("form", ["short", "upper", "symbolic"])
def test_prior_sha_must_be_full_lowercase_hex(verification, repo: Path, prior: dict, form: str) -> None:
    sha = prior["head_sha"]
    forged = {"short": sha[:12], "upper": sha.upper(), "symbolic": "HEAD"}[form]
    assert verdict(verification, repo, _mutate(prior, ("head_sha",), forged)) == ("stale", {})


@pytest.mark.parametrize("argv", [
    [*REUSE_ARGV[:-1], "a b"],
    [*REUSE_ARGV[:-1], "a  b "],
    REUSE_ARGV[:-1],
    [*REUSE_ARGV, "extra"],
    [],
], ids=["collapsed-space", "trailing-space", "fewer", "more", "empty"])
def test_argv_must_match_exactly_without_normalization(
    verification, repo: Path, prior: dict, argv: list[str]
) -> None:
    assert verdict(verification, repo, prior, argv=argv) == ("stale", {})


def test_product_change_after_artifact_head_is_stale(verification, repo: Path, prior: dict) -> None:
    commit(repo, {"src/app.py": "print('changed')\n"}, "product change")
    assert verdict(verification, repo, prior) == ("stale", {})


def test_scratch_commit_after_artifact_head_is_stale(verification, repo: Path, prior: dict) -> None:
    commit(repo, {SCRATCH + "keep.txt": "changed\n"}, "scratch change")
    assert verdict(verification, repo, prior) == ("stale", {})


@pytest.mark.parametrize("dirt", [{"src/app.py": "print('dirty')\n"}, {"untracked.py": "x\n"}], ids=["tracked", "untracked"])
def test_dirty_product_tree_is_stale(verification, repo: Path, prior: dict, dirt: dict[str, str]) -> None:
    write(repo, dirt)
    assert verdict(verification, repo, prior) == ("stale", {})


def test_artifact_head_that_is_not_an_ancestor_is_stale(verification, repo: Path, prior: dict) -> None:
    git(repo, "checkout", "-q", "-b", "side")
    side = commit(repo, {PM + "side.md": "side\n"}, "side")
    git(repo, "checkout", "-q", "master")
    master = commit(repo, {PM + "main.md": "main\n"}, "master store")
    sibling = _mutate(prior, ("head_sha",), side)
    assert verdict(verification, repo, sibling, head_sha=master) == ("stale", {})
    assert verdict(verification, repo, prior, head_sha=master) == ("reused", prior)


@pytest.mark.parametrize("failure", ["not-a-repo", "unknown-prior-sha", "unknown-head"])
def test_git_errors_are_stale(
    verification, repo: Path, tmp_path: Path, prior: dict, failure: str
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    root = plain if failure == "not-a-repo" else repo
    art = _mutate(prior, ("head_sha",), "f" * 40) if failure == "unknown-prior-sha" else prior
    head_sha = "e" * 40 if failure == "unknown-head" else prior["head_sha"]
    result = verification.reuse_verdict(prior=art, argv=REUSE_ARGV, project_root=root, head_sha=head_sha)
    assert result == ("stale", {})
