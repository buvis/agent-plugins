"""Cycle-2 staging: unanswerable git probes, PRD grants for inlining jobs, context unions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import git, library
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
