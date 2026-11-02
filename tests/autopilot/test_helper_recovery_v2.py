"""Cycle-2 staging: unanswerable git probes, PRD grants for inlining jobs, context unions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import git, library
from test_review_helpers import DIFF_REF, GATE, PACK, PRD, PRD_REF, TREE_REF
from test_review_helpers import assert_invalid_input, assert_refused, call, context_for
from test_review_helpers import snapshot, text

LIVE = ("docs", "dev", "project-management", "autopilot")
GUARD = "[safe]\n\tbareRepository = explicit\n"
GATE_ALT = "TEST-GATE-MARKER-0a9c 7 failed"  # near miss: shares GATE's marker prefix
PRECEDENT = "PRECEDENT-MARKER-5e2a"
PRECEDENT_ALT = "PRECEDENT-MARKER-5e2b"  # near miss: differs from PRECEDENT in one byte
RUBRIC_REF = "rubric:review-policy-v1"
AUDIT_REF = "implementation-audit:review"
PLAN_REF = "plan:review"
GATE_REF = "test-results:review"
PACK_REF = "context-pack:pk1"
CORE = [DIFF_REF, PRD_REF, TREE_REF, RUBRIC_REF, AUDIT_REF, PLAN_REF]


def stage_module():
    return library("review_stage")


def pack_with(marker: str) -> str:
    return f"{PACK}\n\n## Findings precedent\n{marker}\n\n## Other\nrest\n"


def staged_files(destination: Path) -> set[str]:
    if not destination.is_dir():
        return set()
    return {path.name for path in destination.rglob("*") if path.is_file()}


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


def bare_metadata(tmp_path: Path) -> tuple[Path, Path]:
    meta = tmp_path.resolve() / "bare meta"
    git(tmp_path, "init", "-q", "--bare", str(meta))
    return meta / "review", meta / "config"


def separate_metadata(tmp_path: Path) -> tuple[Path, Path]:
    meta = tmp_path.resolve() / "separate meta"
    git(tmp_path, "init", "-q", "-b", "master", "--separate-git-dir", str(meta),
        str(tmp_path.resolve() / "separate work"))
    return meta / "review", meta / "config"


@pytest.mark.parametrize("make", [bare_metadata, separate_metadata],
                         ids=["bare-metadata", "separate-git-dir"])
def test_staging_refuses_git_metadata_when_the_bare_guard_blocks_the_probe(
    project: Path, tmp_path: Path, bare_guard: Path, make: Any,
) -> None:
    destination, config = make(tmp_path)
    before = (snapshot(tmp_path), config.read_bytes(), snapshot(bare_guard))
    report = call(stage_module(), project, cycle_id="gp1", artifact_root=destination)
    assert_refused(report)
    assert report["error"] == "unsafe-output", report
    assert isinstance(report["reason"], str) and report["reason"]
    assert report.get("artifacts", []) == [] and report.get("prompts", {}) == {}
    assert not destination.exists() and staged_files(destination) == set()
    assert (snapshot(tmp_path), config.read_bytes(), snapshot(bare_guard)) == before


def test_staging_refuses_guarded_metadata_without_relaxing_any_git_safety_setting(
    project: Path, tmp_path: Path, bare_guard: Path,
) -> None:
    """Both metadata layouts refuse while the guard stays exactly as configured."""
    bare, bare_config = bare_metadata(tmp_path)
    separate, separate_config = separate_metadata(tmp_path)
    for destination in (bare, separate, bare / "deeper", separate / "a" / "b"):
        report = call(stage_module(), project, cycle_id="gp2", artifact_root=destination)
        assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
        assert staged_files(destination) == set()
    assert "bareRepository" not in bare_config.read_text("utf-8")
    assert "bareRepository" not in separate_config.read_text("utf-8")
    assert snapshot(bare_guard) == {".gitconfig": GUARD.encode("utf-8")}
    assert staged_files(project.joinpath(*LIVE)) == {"state.json"}


def test_staging_still_writes_to_a_clean_destination_outside_any_repository(
    project: Path, tmp_path: Path, bare_guard: Path,
) -> None:
    for name, cycle in (("plain one", "ok1"), ("notes.gitlike", "ok2")):
        destination = tmp_path.resolve() / name / "rev"
        report = call(stage_module(), project, cycle_id=cycle, artifact_root=destination)
        assert report["ok"] is True, report
        assert {Path(a["path"]).parent for a in report["artifacts"]} == {destination}
        assert f"review-tasks-{cycle}.md" in staged_files(destination)
        assert "review-tasks-ok9.md" not in staged_files(destination)
    assert snapshot(bare_guard) == {".gitconfig": GUARD.encode("utf-8")}


# --- 2. a job that inlines the PRD needs an explicit prd grant ----------------------------------


def regranted(case: str, strip_prd_from: tuple[str, ...]) -> dict[str, Any]:
    context = context_for(PRD, case)
    per_job = {
        job: sorted(ref for ref in refs
                    if not (job in strip_prd_from and ref.startswith("prd:")))
        for job, refs in context["allowed_inputs"]["per_job"].items()
    }
    return rebound(context, per_job, sorted(context["allowed_inputs"]["input_refs"]))


@pytest.mark.parametrize("job", ["blake", "eve"])
def test_staging_refuses_a_prd_inlining_job_whose_grant_lists_no_prd_ref(
    project: Path, tmp_path: Path, job: str,
) -> None:
    context = regranted("full-eve-guard", (job,))
    destination = project / "docs" / "dev" / "tmp" / "rev"
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="pg1", expected_context=context)
    assert_invalid_input(report)
    assert job in report["reason"], report["reason"]
    assert not destination.exists() and staged_files(destination) == set()
    assert snapshot(tmp_path) == before


def test_staging_names_the_alphabetically_first_job_when_blake_and_eve_both_lack_the_prd(
    project: Path, tmp_path: Path,
) -> None:
    context = regranted("full-eve-guard", ("blake", "eve"))
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="pg2", expected_context=context)
    assert_invalid_input(report)
    assert "blake" in report["reason"], report["reason"]
    assert not re.search(r"\beve\b", report["reason"]), report["reason"]
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


def test_staging_accepts_a_context_reading_job_without_a_prd_grant_and_keeps_the_prd_out(
    project: Path,
) -> None:
    context = regranted("full-eve-guard", ("bob",))
    report = call(stage_module(), project, cycle_id="pg3", expected_context=context)
    assert report["ok"] is True, report
    assert PRD not in text(report["prompts"]["bob"])
    assert PRD in text(report["prompts"]["blake"])
    assert PRD_REF not in report["input_manifest"]["bob"]
    assert PRD_REF in report["input_manifest"]["blake"]


# --- 3. the shared context artifact carries the union of the granted kinds ----------------------


def union_context(alice: list[str], bob: list[str], refs: list[str]) -> dict[str, Any]:
    context = context_for(PRD)
    blake = sorted(context["allowed_inputs"]["per_job"]["blake"])
    per_job = {"alice": sorted(alice), "blake": blake, "bob": sorted(bob)}
    return rebound(context, per_job, sorted(set(refs)))


@pytest.mark.parametrize(("bob_refs", "gate_text", "present"),
                         [(CORE + [PACK_REF], GATE, False),
                          (CORE + [PACK_REF, GATE_REF], GATE_ALT, True)],
                         ids=["kind-granted-to-nobody", "kind-granted-to-one-job"])
def test_staging_fills_the_shared_context_artifact_from_granted_kinds_only(
    project: Path, bob_refs: list[str], gate_text: str, present: bool,
) -> None:
    context = union_context(CORE + [PACK_REF], bob_refs, CORE + [PACK_REF, GATE_REF])
    destination = project / "docs" / "dev" / "tmp" / "rev"
    before = snapshot(project, skip=destination)
    report = call(stage_module(), project, cycle_id="u1", expected_context=context,
                  pack_text=pack_with(PRECEDENT), test_gate_text=gate_text)
    assert report["ok"] is True, report
    shared = text(destination / "review-context-u1.md")
    assert (gate_text in shared) is present, shared
    assert (GATE_ALT if gate_text == GATE else GATE) not in shared, shared
    assert PRECEDENT in shared, shared
    assert PRECEDENT_ALT not in shared, shared
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
    shared = text(project / "docs" / "dev" / "tmp" / "rev" / "review-context-u3.md")
    assert PRECEDENT_ALT in shared and GATE_ALT in shared, shared
    assert PRECEDENT not in shared and GATE not in shared, shared
