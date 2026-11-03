"""Cycle-2 staging: unanswerable git probes, PRD grants for inlining jobs, context unions."""

from __future__ import annotations

import errno
import json
import os
import re
import select
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import World, git, library, make_world
from test_review_helpers import CONTEXT, DIFF_REF, GATE, PRD, PRD_REF, SETTLED, TREE_REF
from test_review_helpers import assert_invalid_input, assert_refused, call, context_for
from test_review_helpers import snapshot, text, texts_for

LIVE = ("docs", "dev", "project-management", "autopilot")
GUARD = "[safe]\n\tbareRepository = explicit\n"
GATE_ALT = "TEST-GATE-MARKER-0a9c 7 failed"  # near miss: shares GATE's marker prefix
PRECEDENT = "PRECEDENT-MARKER-5e2a"
PRECEDENT_ALT = "PRECEDENT-MARKER-5e2b"  # near miss: differs from PRECEDENT in one byte
DIFF_MARKER = "DIFF-MARKER-55d0"
RUBRIC_REF = "rubric:review-policy-v1"
AUDIT_REF = "implementation-audit:review"
PLAN_REF = "plan:review"
GATE_REF = "test-results:review"
PACK_REF = "context-pack:pk1"
ALT_PRD_REF = "prd:00020"
CORE = [DIFF_REF, PRD_REF, TREE_REF, RUBRIC_REF, AUDIT_REF, PLAN_REF]
CAUSE = re.compile(r"git (internals|metadata|directory)|probe|bare repos", re.IGNORECASE)


def stage_module():
    return library("review_stage")


def pack_with(marker: str) -> str:
    return f"PACK-MARKER-a1b2\n\n## Findings precedent\n{marker}\n\n## Other\nrest\n"


def staged_files(destination: Path) -> set[str]:
    if not destination.is_dir():
        return set()
    return {path.name for path in destination.rglob("*") if path.is_file()}


def core_names(cycle: str) -> set[str]:
    return {f"review-tasks-{cycle}.md", f"review-prd-raw-{cycle}.md",
            f"review-prd-{cycle}.md", f"review-context-{cycle}.md",
            f"review-diff-{cycle}.diff"}


def cause(report: dict[str, Any], *paths: Path) -> str:
    """The refusal message with the fixture paths cut out, so only its prose can match."""
    message = str(report.get("reason") or report.get("detail") or "")
    for path in paths:
        message = message.replace(str(path), " ")
    return message


@pytest.fixture
def project(tmp_path: Path) -> Path:
    base = tmp_path.resolve() / "project"
    (base / "docs" / "dev" / "tmp").mkdir(parents=True)
    base.joinpath(*LIVE).mkdir(parents=True)
    (base.joinpath(*LIVE) / "state.json").write_text('{"phase": "review"}', "utf-8")
    git(base, "init", "-q", "-b", "master")
    return base


def rebound(context: dict[str, Any], per_job: dict[str, list[str]],
            refs: list[str]) -> dict[str, Any]:
    digest = library("review_evidence").digest({"input_refs": refs, "per_job": per_job})
    context["allowed_inputs"].update(input_refs=refs, per_job=per_job, manifest_sha256=digest)
    context["source_bindings"]["allowed_input_manifest_sha256"] = digest
    return context


# --- 1. a git probe that cannot answer refuses the destination ----------------------------------


@pytest.fixture
def bare_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git configuration that refuses bare-repository access, in an empty fake home."""
    home = tmp_path.resolve() / "guard home"
    home.mkdir()
    (home / ".gitconfig").write_text(GUARD, "utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    monkeypatch.delenv("GIT_CONFIG_SYSTEM", raising=False)
    return home


def bare_metadata(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A bare repository's metadata directory, beside a plain directory named alike."""
    vault = tmp_path.resolve() / "vault one"
    git(tmp_path, "init", "-q", "--bare", str(vault))
    control = tmp_path.resolve() / "vault two"
    control.mkdir()
    return vault / "review", vault / "config", control / "review"


def separate_metadata(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Metadata moved out of the work tree, beside a plain directory named alike."""
    vault = tmp_path.resolve() / "vault three"
    git(tmp_path, "init", "-q", "-b", "master", "--separate-git-dir", str(vault),
        str(tmp_path.resolve() / "tree three"))
    control = tmp_path.resolve() / "vault four"
    control.mkdir()
    return vault / "review", vault / "config", control / "review"


@pytest.mark.parametrize("make", [bare_metadata, separate_metadata],
                         ids=["bare-metadata", "separate-git-dir"])
def test_staging_refuses_git_metadata_when_the_bare_guard_blocks_the_probe(
    project: Path, tmp_path: Path, bare_guard: Path, make: Any,
) -> None:
    """Only the git state tells the refused destination from its identically shaped sibling."""
    destination, config, control = make(tmp_path)
    before = (snapshot(tmp_path), config.read_bytes(), snapshot(bare_guard))
    report = call(stage_module(), project, cycle_id="gp1", artifact_root=destination)
    assert_refused(report)
    assert report["error"] == "unsafe-output", report
    assert CAUSE.search(cause(report, destination, tmp_path)), report
    assert report.get("artifacts", []) == [] and report.get("prompts", {}) == {}
    assert not destination.exists() and staged_files(destination) == set()
    assert (snapshot(tmp_path), config.read_bytes(), snapshot(bare_guard)) == before
    accepted = call(stage_module(), project, cycle_id="gp1b", artifact_root=control)
    assert accepted["ok"] is True, accepted
    assert core_names("gp1b") <= staged_files(control)


def test_staging_refuses_guarded_metadata_without_relaxing_any_git_safety_setting(
    project: Path, tmp_path: Path, bare_guard: Path,
) -> None:
    """Both metadata layouts refuse while the guard stays exactly as configured."""
    bare, bare_config, _ = bare_metadata(tmp_path)
    separate, separate_config, _ = separate_metadata(tmp_path)
    for destination in (bare, separate, bare / "deeper", separate / "a" / "b"):
        report = call(stage_module(), project, cycle_id="gp2", artifact_root=destination)
        assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
        assert staged_files(destination) == set()
    assert "bareRepository" not in bare_config.read_text("utf-8")
    assert "bareRepository" not in separate_config.read_text("utf-8")
    assert snapshot(bare_guard) == {".gitconfig": GUARD.encode("utf-8")}


def guarded_live_state(project: Path, tmp_path: Path) -> Path:
    return project.joinpath(*LIVE) / "review"


def guarded_symlink(project: Path, tmp_path: Path) -> Path:
    outside = tmp_path.resolve() / "outside"
    outside.mkdir()
    (project / "docs" / "dev" / "tmp" / "link").symlink_to(outside, target_is_directory=True)
    return project / "docs" / "dev" / "tmp" / "link" / "rev"


@pytest.mark.parametrize("make", [guarded_live_state, guarded_symlink],
                         ids=["live-state", "symlink-escape"])
def test_staging_keeps_refusing_other_unsafe_destinations_while_the_guard_is_active(
    project: Path, tmp_path: Path, bare_guard: Path, make: Any,
) -> None:
    destination = make(project, tmp_path)
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="gp4", artifact_root=destination)
    assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
    assert staged_files(destination) == set()
    assert staged_files(project.joinpath(*LIVE)) == {"state.json"}
    assert snapshot(tmp_path) == before


def test_staging_still_writes_to_a_clean_destination_outside_any_repository(
    project: Path, tmp_path: Path, bare_guard: Path,
) -> None:
    for name, cycle in (("plain one", "ok1"), ("notes.gitlike", "ok2")):
        destination = tmp_path.resolve() / name / "rev"
        report = call(stage_module(), project, cycle_id=cycle, artifact_root=destination)
        assert report["ok"] is True, report
        assert {Path(a["path"]).parent for a in report["artifacts"]} == {destination}
        names = staged_files(destination)
        assert core_names(cycle) | {f"review-pack-{cycle}.md"} <= names
        assert "review-tasks-ok9.md" not in names
    assert snapshot(bare_guard) == {".gitconfig": GUARD.encode("utf-8")}


# --- 2. a job that inlines the PRD needs an explicit prd grant ----------------------------------


def regranted(case: str, strip_prd_from: tuple[str, ...],
              prd_ref: str = PRD_REF) -> dict[str, Any]:
    """The fixture grants, with the PRD ref renamed and dropped for the named jobs."""
    context = context_for(PRD, case)
    allowed = context["allowed_inputs"]
    renamed = [prd_ref if ref == PRD_REF else ref for ref in allowed["input_refs"]]
    per_job = {
        job: sorted(prd_ref if ref == PRD_REF else ref for ref in refs
                    if not (job in strip_prd_from and ref.startswith("prd:")))
        for job, refs in allowed["per_job"].items()
    }
    return rebound(context, per_job, sorted(renamed))


def texts_renamed(context: dict[str, Any], prd_ref: str) -> dict[str, str]:
    texts = texts_for(context, PRD)
    texts[prd_ref] = PRD
    return texts


@pytest.mark.parametrize("prd_ref", [PRD_REF, ALT_PRD_REF], ids=["prd-00019", "prd-00020"])
@pytest.mark.parametrize("job", ["blake", "eve"])
def test_staging_refuses_a_prd_inlining_job_whose_grant_lists_no_prd_ref(
    project: Path, tmp_path: Path, job: str, prd_ref: str,
) -> None:
    context = regranted("full-eve-guard", (job,), prd_ref)
    destination = project / "docs" / "dev" / "tmp" / "rev"
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="pg1", expected_context=context,
                  input_texts=texts_renamed(context, prd_ref))
    assert_invalid_input(report)
    reason = report["reason"]
    assert job in reason and "prd" in reason.lower(), reason
    assert not destination.exists() and staged_files(destination) == set()
    assert snapshot(tmp_path) == before


def test_staging_accepts_prd_inlining_jobs_whose_grant_names_another_prd_id(
    project: Path,
) -> None:
    """The grant is read by ref kind, so a different PRD number is still a PRD grant."""
    context = regranted("full-eve-guard", (), ALT_PRD_REF)
    report = call(stage_module(), project, cycle_id="pg5", expected_context=context,
                  input_texts=texts_renamed(context, ALT_PRD_REF))
    assert report["ok"] is True, report
    for job in ("blake", "eve"):
        assert ALT_PRD_REF in report["input_manifest"][job], job
        assert PRD_REF not in report["input_manifest"][job], job
        assert PRD in text(report["prompts"][job]), job
    assert core_names("pg5") <= staged_files(project / "docs" / "dev" / "tmp" / "rev")


def test_staging_names_the_alphabetically_first_job_when_blake_and_eve_both_lack_the_prd(
    project: Path, tmp_path: Path,
) -> None:
    context = regranted("full-eve-guard", ("blake", "eve"))
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="pg2", expected_context=context)
    assert_invalid_input(report)
    reason = report["reason"]
    assert "blake" in reason and "prd" in reason.lower(), reason
    assert not re.search(r"\beve\b", reason), reason
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


def test_staging_accepts_a_context_reading_job_without_a_prd_grant_and_keeps_the_prd_out(
    project: Path,
) -> None:
    context = regranted("full-eve-guard", ("bob",))
    report = call(stage_module(), project, cycle_id="pg3", expected_context=context)
    assert report["ok"] is True, report
    blake = text(report["prompts"]["blake"])
    assert PRD not in text(report["prompts"]["bob"])
    assert PRD in blake
    assert PRD_REF not in report["input_manifest"]["bob"]
    assert PRD_REF in report["input_manifest"]["blake"]
    assert DIFF_REF not in report["input_manifest"]["blake"]
    assert DIFF_MARKER not in blake and CONTEXT not in blake
    assert core_names("pg3") <= staged_files(project / "docs" / "dev" / "tmp" / "rev")


# --- 3. the shared context artifact carries the union of the granted kinds ----------------------


def union_context(alice: list[str], bob: list[str], refs: list[str]) -> dict[str, Any]:
    context = context_for(PRD)
    blake = sorted(context["allowed_inputs"]["per_job"]["blake"])
    per_job = {"alice": sorted(alice), "blake": blake, "bob": sorted(bob)}
    return rebound(context, per_job, sorted(set(refs)))


@pytest.mark.parametrize(("bob_refs", "gate_text", "gate_in", "pack_in", "overrides"),
                         [(CORE + [PACK_REF], GATE, False, True, set()),
                          (CORE + [PACK_REF, GATE_REF], GATE_ALT, True, True,
                           {"alice-review-context-u1.md"}),
                          (CORE + [GATE_REF], GATE_ALT, True, False,
                           {"alice-review-context-u1.md"})],
                         ids=["gate-granted-to-nobody", "gate-granted-to-one-job",
                              "pack-granted-to-nobody"])
def test_staging_fills_the_shared_context_artifact_from_granted_kinds_only(
    project: Path, bob_refs: list[str], gate_text: str, gate_in: bool, pack_in: bool,
    overrides: set[str],
) -> None:
    context = union_context(CORE + [PACK_REF] if pack_in else CORE, bob_refs,
                            CORE + [PACK_REF, GATE_REF])
    destination = project / "docs" / "dev" / "tmp" / "rev"
    before = snapshot(project, skip=destination)
    report = call(stage_module(), project, cycle_id="u1", expected_context=context,
                  pack_text=pack_with(PRECEDENT), test_gate_text=gate_text)
    assert report["ok"] is True, report
    shared = text(destination / "review-context-u1.md")
    assert (gate_text in shared) is gate_in, shared
    assert (GATE_ALT if gate_text == GATE else GATE) not in shared, shared
    assert (PRECEDENT in shared) is pack_in, shared
    assert ("review-pack-u1.md" in shared) is pack_in, shared
    assert PRECEDENT_ALT not in shared, shared
    assert CONTEXT in shared, shared
    assert "review-tasks-u1.md" in shared and "review-prd-u1.md" in shared, shared
    names = staged_files(destination)
    assert {n for n in names if n.endswith("-review-context-u1.md")} == overrides, names
    assert core_names("u1") <= names
    assert snapshot(project, skip=destination) == before


def test_staging_writes_a_per_job_context_artifact_only_for_a_job_outside_the_union(
    project: Path,
) -> None:
    thin = [ref for ref in CORE + [PACK_REF] if ref != PLAN_REF]
    context = union_context(CORE + [PACK_REF], thin, CORE + [PACK_REF])
    report = call(stage_module(), project, cycle_id="u2", expected_context=context,
                  pack_text=pack_with(PRECEDENT_ALT))
    assert report["ok"] is True, report
    destination = project / "docs" / "dev" / "tmp" / "rev"
    listed = {Path(row["path"]).name for row in report["artifacts"]}
    for names in (staged_files(destination), listed):
        assert "review-context-u2.md" in names
        assert "bob-review-context-u2.md" in names
        assert "alice-review-context-u2.md" not in names
    shared = text(destination / "review-context-u2.md")
    assert PRECEDENT_ALT in shared and PRECEDENT not in shared, shared
    assert "review-tasks-u2.md" in shared, shared
    override = text(destination / "bob-review-context-u2.md")
    assert PRECEDENT_ALT in override, override
    assert "review-tasks-u2.md" not in override, override
    prompt = text(report["prompts"]["bob"])
    assert "bob-review-context-u2.md" in prompt, prompt
    assert re.search(r"(?<!bob-)review-context-u2\.md", prompt) is None, prompt
    assert core_names("u2") <= staged_files(destination)


def test_staging_keeps_every_context_kind_when_no_roster_job_reads_the_shared_context(
    project: Path,
) -> None:
    context = context_for(PRD, "fast-track-delta-clean")
    granted = set(context["allowed_inputs"]["per_job"]["eve"])
    assert PACK_REF not in granted and GATE_REF not in granted
    report = call(stage_module(), project, cycle_id="u3", expected_context=context,
                  pack_text=pack_with(PRECEDENT_ALT), test_gate_text=GATE_ALT)
    assert report["ok"] is True, report
    assert set(report["prompts"]) == {"eve"}
    destination = project / "docs" / "dev" / "tmp" / "rev"
    shared = text(destination / "review-context-u3.md")
    for marker in (CONTEXT, SETTLED, PRECEDENT_ALT, GATE_ALT, "review-tasks-u3.md",
                   "review-prd-u3.md", "review-pack-u3.md"):
        assert marker in shared, marker
    assert PRECEDENT not in shared and GATE not in shared, shared
    assert core_names("u3") | {"review-pack-u3.md"} <= staged_files(destination)


# --- 4. containment is decided before any candidate content is read ----------------------------

OUTSIDE = "resolves outside the repository"
GITDIR = "resolves inside the git directory"
OPENED: list[tuple[str, str, int]] = []
WATCHING: list[bool] = []


def _watch_open(event: str, args: tuple) -> None:
    if WATCHING and event == "open" and isinstance(args[0], (str, bytes)):
        mode = args[1] if isinstance(args[1], str) else "r"
        flags = args[2] if isinstance(args[2], int) else 0
        OPENED.append((os.path.realpath(os.fsdecode(args[0])), mode, flags))


sys.addaudithook(_watch_open)


@pytest.fixture
def opened():
    """Opens count from the moment a test calls `opened.clear()`, so setup never counts."""
    WATCHING.append(True)
    OPENED.clear()
    yield OPENED
    WATCHING.clear()


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def opens_of(recorded: list[tuple[str, str, int]], path: Path) -> list[tuple[str, int]]:
    """Every recorded open of `path` (mode, flags)."""
    target = os.path.realpath(path)
    return [(mode, flags) for seen, mode, flags in recorded if seen == target]


def commit_repo(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "master")
    for relative, body in files.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(body, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


@pytest.mark.parametrize("name", ["state.json", ".git"],
                         ids=["plain-name", "git-pointer-name"])
def test_sink_calls_an_external_hard_linked_git_pointer_outside_without_reading_it(
    tmp_path: Path, isolated_git: None, opened: list[tuple[str, str, int]], name: str,
) -> None:
    """A pointer-shaped candidate sharing an inode with an external .git stays unread."""
    base = tmp_path.resolve()
    project = commit_repo(base / "repo", {"src/app.py": "a\n"})
    external = commit_repo(base / "repo-elsewhere", {"src/other.py": "o\n"})
    stranger = base / "repo-sibling"
    stranger.mkdir()
    pointer = f"gitdir: {project / '.git'}\n"
    twin = external / ".git" / "pointer-source"
    twin.write_text(pointer, encoding="utf-8")
    candidate = stranger / name
    os.link(twin, candidate)
    assert candidate.stat().st_nlink == 2
    inside = project / "logs" / "run.log"
    inside.parent.mkdir(parents=True)
    inside.write_text(pointer, encoding="utf-8")
    inside.chmod(0o644)
    sink = library("log_sink_refusal")
    opened.clear()
    assert sink.refuse(candidate, project) == OUTSIDE
    assert sink.refuse(stranger / "logs" / "fresh.log", project) == OUTSIDE
    assert sink.refuse(inside, project) is None
    assert opens_of(opened, candidate) == []
    assert opens_of(opened, twin) == []
    assert candidate.read_text("utf-8") == pointer


def test_sink_calls_a_relative_worktree_gitdir_pointer_a_git_directory_path(
    tmp_path: Path, isolated_git: None,
) -> None:
    """A relative `gitdir:` pointer resolves exactly like the absolute one git wrote."""
    base = tmp_path.resolve()
    project = commit_repo(base / "repo", {"src/app.py": "a\n"})
    worktree = base / "wt"
    git(project, "worktree", "add", "-q", "-b", "wt", str(worktree))
    link = worktree / ".git"
    absolute = link.read_text("utf-8")
    target = project / ".git" / "worktrees" / "wt"
    relative = "gitdir: " + os.path.relpath(target, worktree) + "\n"
    assert relative != absolute and not relative.split(" ", 1)[1].startswith("/")
    sink = library("log_sink_refusal")
    assert sink.refuse(link, worktree) == GITDIR
    link.write_text(relative, encoding="utf-8")
    assert sink.refuse(link, worktree) == GITDIR
    assert link.read_text("utf-8") == relative
    decoy = worktree / "gitdir.log"
    decoy.write_text(relative, encoding="utf-8")
    decoy.chmod(0o644)
    assert sink.refuse(decoy, worktree) is None
    assert sink.refuse(worktree / "logs" / "new.log", worktree) is None
    assert sink.refuse(base / "outside.log", worktree) == OUTSIDE


# --- 5. the log sink is proven openable before the child is spawned ----------------------------

ARTIFACT = Path("docs/dev/tmp/verify-t2.json")
MARKER_CHILD = (
    "import os, pathlib, sys\n"
    "pathlib.Path(sys.argv[1]).write_text(os.getcwd(), encoding='utf-8')\n"
    "print('PASS 2 FAIL 0 SKIP 1 EXIT 0')\n"
)
SLOW_CHILD = (
    "import os, pathlib, sys, time\n"
    "started, late, pidfile = (pathlib.Path(p) for p in sys.argv[1:4])\n"
    "pidfile.write_text(str(os.getpid()), encoding='utf-8')\n"
    "started.write_text('started', encoding='utf-8')\n"
    "for _ in range(15): print('chatter', flush=True); time.sleep(0.1)\n"
    "late.write_text('late', encoding='utf-8')\n"
    "print('PASS 1 FAIL 0 SKIP 0 EXIT 0')\n"
)


class FailingSink:
    """The real sink handle, with a chosen write or the close raising OSError."""

    def __init__(self, handle: Any, fail_write_after: int | None, fail_close: bool) -> None:
        self._handle = handle
        self._fail_write_after = fail_write_after
        self._fail_close = fail_close
        self._writes = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._handle, name)

    def __enter__(self) -> Any:
        return self

    def __exit__(self, *exc: object) -> bool:
        self.close()
        return False

    def write(self, data: Any) -> Any:
        self._writes += 1
        if self._fail_write_after is not None and self._writes > self._fail_write_after:
            raise OSError(errno.EIO, "the test broke this sink write")
        return self._handle.write(data)

    def close(self) -> None:
        self._handle.close()
        if self._fail_close:
            raise OSError(errno.EIO, "the test broke this sink close")


def break_sink(monkeypatch: pytest.MonkeyPatch, *, fail_write_after: int | None = None,
               fail_close: bool = False) -> list[Path]:
    """Wraps the packaged sink opener; the returned list records the opened sinks."""
    verification, sink = library("verification"), library("log_sink_refusal")
    real = sink._open_log_sink
    calls: list[Path] = []

    def opener(log_path: Any, repo_root: Any, *args: Any, **kwargs: Any) -> FailingSink:
        calls.append(Path(log_path))
        handle = real(log_path, repo_root, *args, **kwargs)
        return FailingSink(handle, fail_write_after, fail_close)

    assert hasattr(verification, "_open_log_sink"), "no sink-opener seam in the gate module"
    for module in (verification, sink):
        monkeypatch.setattr(module, "_open_log_sink", opener)
    return calls


def run_gate(world: World, argv: list[str], *, log: Path | None = None,
             artifact: Path | None = None, timeout: float = 60) -> dict:
    return library("verification").run_verification(
        argv=argv, project_root=world.target,
        head_sha=git(world.target, "rev-parse", "HEAD"),
        artifact_path=artifact or world.target / ARTIFACT,
        log_path=log or world.target / "logs" / "run.log", timeout=timeout,
    )


def child_argv(tmp_path: Path, name: str, body: str, *args: Path) -> list[str]:
    script = tmp_path / f"{name}.py"
    script.write_text(body, encoding="utf-8")
    return [sys.executable, "-I", str(script), *(str(a) for a in args)]


def still_running(pid: int) -> bool:
    """True while `ps` reports the pid as a live, non-zombie process."""
    probe = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], check=False,
                           capture_output=True, text=True, timeout=30)
    state = probe.stdout.strip()
    return bool(state) and not state.startswith("Z")


def kill_child(pid: int) -> None:
    if still_running(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass


def failure_shape(report: dict, slug: str) -> None:
    assert (report["schema_version"], report["ok"], report["error"]) == (1, False, slug), report
    assert isinstance(report["reason"], str) and report["reason"].strip(), report


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


def aliased_leaf(target: Path) -> Path:
    """An aliased leaf stays an unsafe output path, not a sink that failed to open."""
    (target / "logs").mkdir(parents=True, exist_ok=True)
    os.symlink(target / "src" / "app.py", target / "logs" / "alias.log")
    return target / "logs" / "alias.log"


@pytest.mark.parametrize("tail", [("app.py", "run.log"), ("app.py", "deep", "run.log")],
                         ids=["parent-is-a-file", "grandparent-is-a-file"])
def test_verification_refuses_an_unopenable_log_sink_before_it_spawns_the_child(
    world: World, tmp_path: Path, isolated_git: None, tail: tuple[str, ...],
) -> None:
    case = "-".join(tail)
    marker = tmp_path / f"marker-{case}.txt"
    argv = child_argv(tmp_path, f"child-{case}", MARKER_CHILD, marker)
    report = run_gate(world, argv, log=world.target.joinpath("src", *tail))
    failure_shape(report, "sink-failed")
    assert not marker.exists(), "the child ran before the sink was proven openable"
    assert not (world.target / ARTIFACT).exists()
    assert (world.target / "src" / "app.py").read_text("utf-8") == "print('app')\n"
    accepted = run_gate(world, argv, log=world.target / "logs" / f"run-{case}.log")
    assert accepted["ok"] is True, accepted
    assert Path(marker.read_text("utf-8")).resolve() == world.target.resolve()
    assert (world.target / "logs" / f"run-{case}.log").is_file()
    assert (world.target / ARTIFACT).is_file()


def test_verification_refuses_an_aliased_log_leaf_before_the_spawn_under_the_legacy_slug(
    world: World, tmp_path: Path, isolated_git: None,
) -> None:
    """An alias is still an unsafe output path; only an open failure becomes sink-failed."""
    marker = tmp_path / "marker-alias.txt"
    argv = child_argv(tmp_path, "child-alias", MARKER_CHILD, marker)
    report = run_gate(world, argv, log=aliased_leaf(world.target))
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran before the log path was judged"
    assert not (world.target / ARTIFACT).exists()
    assert (world.target / "src" / "app.py").read_text("utf-8") == "print('app')\n"


def test_verification_reports_a_mid_run_sink_write_failure_and_kills_the_child(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, late, pidfile = (tmp_path / name for name in ("started", "late", "pid"))
    argv = child_argv(tmp_path, "slow", SLOW_CHILD, started, late, pidfile)
    calls = break_sink(monkeypatch, fail_write_after=1)
    report = run_gate(world, argv)
    pid = None
    try:
        assert calls, "the patched sink opener never ran"
        failure_shape(report, "sink-write-failed")
        assert started.read_text("utf-8") == "started"
        pid = int(pidfile.read_text("utf-8"))
        assert not still_running(pid), "the spawned child outlived the failed run"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            assert not late.exists(), "the child kept working after the call returned"
            time.sleep(0.05)
    finally:
        if pid:
            kill_child(pid)


@pytest.mark.parametrize(("fail_write", "slug"),
                         [(False, "sink-close-failed"), (True, "sink-write-failed")],
                         ids=["close-only", "write-then-close"])
def test_verification_keeps_the_write_failure_when_the_sink_close_also_fails(
    world: World, tmp_path: Path, isolated_git: None, monkeypatch: pytest.MonkeyPatch,
    fail_write: bool, slug: str,
) -> None:
    marker = tmp_path / f"marker-{slug}.txt"
    argv = child_argv(tmp_path, f"child-{slug}", MARKER_CHILD, marker)
    calls = break_sink(monkeypatch, fail_write_after=0 if fail_write else None, fail_close=True)
    report = run_gate(world, argv)
    assert calls, "the patched sink opener never ran"
    failure_shape(report, slug)
    if not fail_write:
        assert Path(marker.read_text("utf-8")).resolve() == world.target.resolve()


@pytest.mark.parametrize("kind", ["absent-program", "unexecutable-program"])
def test_verification_preserves_its_outputs_on_a_spawn_failure_but_leaves_an_empty_log(
    world: World, tmp_path: Path, isolated_git: None, kind: str,
) -> None:
    program = tmp_path / kind
    if kind == "unexecutable-program":
        program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        program.chmod(0o644)
    log = world.target / "logs" / f"{kind}.log"
    report = run_gate(world, [str(program), "--version"], log=log)
    failure_shape(report, "spawn-failed")
    assert not (world.target / ARTIFACT).exists()
    assert log.is_file() and log.read_bytes() == b""
    with pytest.raises(ValueError):
        run_gate(world, [], log=world.target / "logs" / f"{kind}-empty.log")
    marker = tmp_path / f"{kind}-marker.txt"
    accepted = run_gate(world, child_argv(tmp_path, kind, MARKER_CHILD, marker), log=log)
    assert accepted["ok"] is True, accepted
    assert b"PASS 2 FAIL 0 SKIP 1 EXIT 0" in log.read_bytes()
    assert (world.target / ARTIFACT).is_file()


# --- 6. the exported policy never blocks on a fifo and never assumes O_NOFOLLOW ----------------

FIFO_CAUSE = re.compile(r"fifo|pipe|reader|regular file", re.IGNORECASE)


def export(world: World, *args: Any, timeout: float = 30) -> subprocess.CompletedProcess:
    """The policy export as a bounded CLI probe: a hang fails instead of stalling the suite."""
    return subprocess.run(
        [sys.executable, "-I", str(world.facade), "--export-policy", *(str(a) for a in args)],
        check=False, cwd=world.cwd, env=world.env, capture_output=True, timeout=timeout,
    )


def refusal_line(proc: subprocess.CompletedProcess) -> str:
    stderr = proc.stderr.decode("utf-8")
    lines = [line for line in stderr.splitlines() if line.strip()]
    assert "Traceback" not in stderr, stderr
    assert len(lines) == 1 and lines[0].startswith("autopilot: "), stderr
    return lines[0]


def drain_fifo(fifo: Path, stop: threading.Event, chunks: list[bytes]) -> None:
    """Keeps a reader on `fifo` without ever blocking, so the thread always joins."""
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    try:
        deadline = time.monotonic() + 60
        while not stop.is_set() and time.monotonic() < deadline:
            if select.select([reader], [], [], 0.05)[0]:
                chunks.append(os.read(reader, 65536))
    finally:
        os.close(reader)


def test_export_policy_refuses_a_fifo_output_without_a_reader_instead_of_blocking(
    world: World,
) -> None:
    fifo = world.base / "policy.fifo"
    os.mkfifo(fifo)
    try:
        refused = export(world, "--out", fifo)
    finally:
        fifo.unlink()
    assert refused.returncode == 1, (refused.returncode, refused.stderr)
    assert refused.stdout == b""
    assert FIFO_CAUSE.search(refusal_line(refused)), refused.stderr
    named_alike = world.base / "plain.fifo"
    accepted = export(world, "--out", named_alike)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(named_alike.read_bytes())["schema_version"] == 1


def test_export_policy_refuses_a_drained_fifo_output_rather_than_writing_into_a_pipe(
    world: World,
) -> None:
    fifo = world.base / "drained.fifo"
    os.mkfifo(fifo)
    stop, chunks = threading.Event(), []
    reader = threading.Thread(target=drain_fifo, args=(fifo, stop, chunks), daemon=True)
    reader.start()
    try:
        refused = export(world, "--out", fifo)
    finally:
        stop.set()
        reader.join(timeout=10)
        fifo.unlink()
    assert not reader.is_alive(), "the fifo reader thread leaked"
    assert refused.returncode == 1, (refused.returncode, refused.stderr)
    assert refused.stdout == b""
    assert FIFO_CAUSE.search(refusal_line(refused)), refused.stderr
    assert b"schema_version" not in b"".join(chunks), chunks


def test_export_policy_refuses_up_front_when_o_nofollow_support_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
    facade = library("autopilot")
    monkeypatch.delattr(getattr(facade, "os", os), "O_NOFOLLOW", raising=False)
    assert not hasattr(os, "O_NOFOLLOW")
    out = tmp_path / "policy.json"
    capfd.readouterr()
    code = facade.main(["--export-policy", "--out", str(out)])
    captured = capfd.readouterr()
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert code == 1, (code, captured.err)
    assert not out.exists()
    assert captured.out == ""
    assert len(lines) == 1 and lines[0].startswith("autopilot: "), captured.err
    assert "O_NOFOLLOW" in lines[0].upper(), lines[0]


def test_export_policy_writes_a_plain_file_and_refuses_a_hard_linked_one(world: World) -> None:
    printed = export(world)
    assert printed.returncode == 0, printed.stderr
    fresh, stale = world.base / "policy one.json", world.base / "policy two.json"
    stale.write_text("stale\n", encoding="utf-8")
    for out in (fresh, stale):
        accepted = export(world, "--out", out)
        assert accepted.returncode == 0, accepted.stderr
        assert accepted.stdout == b""
        assert out.read_bytes().strip() == printed.stdout.strip()
        assert json.loads(out.read_bytes())["schema_version"] == 1
    linked, twin = world.base / "linked.json", world.base / "twin.json"
    linked.write_text("keep\n", encoding="utf-8")
    os.link(linked, twin)
    try:
        refused = export(world, "--out", linked)
    finally:
        twin.unlink()
    assert refused.returncode == 1, (refused.returncode, refused.stderr)
    assert refusal_line(refused)
    assert linked.read_text("utf-8") == "keep\n"
