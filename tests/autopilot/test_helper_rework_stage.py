"""Rework staging: locale-proof git probe, empty context union, established refusal shape."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
from test_helper_recovery_v2 import ALT_PRD_REF, CORE, GATE_ALT, GATE_REF, PACK_REF
from test_helper_recovery_v2 import PRECEDENT, PRECEDENT_ALT, bare_guard, bare_metadata
from test_helper_recovery_v2 import core_names, guarded_live_state, guarded_symlink
from test_helper_recovery_v2 import pack_with, project, regranted, separate_metadata
from test_helper_recovery_v2 import stage_module, staged_files, texts_renamed, union_context
from test_review_helpers import CONTEXT, DIFF_REF, GATE, PRD, SETTLED
from test_review_helpers import assert_invalid_input, assert_refused, call, context_for
from test_review_helpers import snapshot, text

__all__ = ["bare_guard", "project"]  # fixtures re-exported for pytest

GERMAN = {"LC_ALL": "de_DE.UTF-8", "LANGUAGE": "de"}


# --- B1. the git probe does not depend on the ambient message locale ----------------------------


@pytest.fixture
def german(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """German message locale for the process; skips when this host cannot translate Git."""
    probe = tmp_path.resolve() / "probe"
    probe.mkdir()
    env = {**os.environ, **GERMAN, "GIT_CEILING_DIRECTORIES": str(tmp_path.resolve())}
    done = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=probe, env=env,
                          capture_output=True, text=True, timeout=60)
    stderr = done.stderr.strip()
    english = stderr.startswith("fatal:") and "not a git repository" in stderr.lower()
    if done.returncode == 0 or english:
        pytest.skip(f"German Git translation is not active on this host (stderr: {stderr!r})")
    for key, value in GERMAN.items():
        monkeypatch.setenv(key, value)
    return GERMAN


@pytest.mark.parametrize(("name", "cycle"), [("plain one", "lo1"), ("notes.gitlike", "lo2")])
def test_staging_accepts_a_destination_outside_any_repository_under_a_german_locale(
    project: Path, tmp_path: Path, german: dict[str, str], name: str, cycle: str,
) -> None:
    destination = tmp_path.resolve() / name / "rev"
    report = call(stage_module(), project, cycle_id=cycle, artifact_root=destination)
    assert report["ok"] is True, report
    assert {Path(a["path"]).parent for a in report["artifacts"]} == {destination}
    assert core_names(cycle) | {f"review-pack-{cycle}.md"} <= staged_files(destination)
    assert os.environ["LC_ALL"] == german["LC_ALL"] and os.environ["LANGUAGE"] == "de"


@pytest.mark.parametrize("make", [bare_metadata, separate_metadata],
                         ids=["bare-metadata", "separate-git-dir"])
def test_staging_refuses_guarded_git_metadata_under_a_german_locale_without_touching_config(
    project: Path, tmp_path: Path, bare_guard: Path, german: dict[str, str], make: Any,
) -> None:
    destination, config, control = make(tmp_path)
    before = (snapshot(tmp_path), config.read_bytes())
    report = call(stage_module(), project, cycle_id="lo3", artifact_root=destination)
    assert_refused(report)
    assert report["error"] == "unsafe-output", report
    assert report.get("artifacts", []) == [] and report.get("prompts", {}) == {}
    assert not destination.exists() and staged_files(destination) == set()
    assert (snapshot(tmp_path), config.read_bytes()) == before
    accepted = call(stage_module(), project, cycle_id="lo3b", artifact_root=control)
    assert accepted["ok"] is True, accepted
    assert core_names("lo3b") <= staged_files(control)


def project_git_internals(project: Path, tmp_path: Path) -> Path:
    return project / ".git" / "review"


@pytest.mark.parametrize("make", [project_git_internals, guarded_live_state, guarded_symlink],
                         ids=["git-internals", "live-state", "symlink-escape"])
def test_staging_keeps_refusing_unsafe_destinations_under_a_german_locale(
    project: Path, tmp_path: Path, german: dict[str, str], make: Any,
) -> None:
    destination = make(project, tmp_path)
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="lo4", artifact_root=destination)
    assert_refused(report)
    assert report["error"] == "unsafe-output", report
    assert staged_files(destination) == set()
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


# --- B2. an empty granted context union grants no content ---------------------------------------

KINDS = ("review-tasks-{c}.md", "review-prd-{c}.md", "review-pack-{c}.md")


@pytest.mark.parametrize(("cycle", "precedent", "gate", "other_precedent", "other_gate"),
                         [("e1", PRECEDENT, GATE, PRECEDENT_ALT, GATE_ALT),
                          ("e2", PRECEDENT_ALT, GATE_ALT, PRECEDENT, GATE)],
                         ids=["first-values", "near-miss-values"])
def test_staging_leaves_the_shared_context_empty_of_every_kind_for_a_roster_that_reads_none(
    project: Path, cycle: str, precedent: str, gate: str, other_precedent: str,
    other_gate: str,
) -> None:
    context = context_for(PRD, "fast-track-delta-clean")
    assert [row["job_id"] for row in context["resolved_roster"]] == ["eve"]
    report = call(stage_module(), project, cycle_id=cycle, expected_context=context,
                  pack_text=pack_with(precedent), test_gate_text=gate)
    assert report["ok"] is True, report
    assert set(report["prompts"]) == {"eve"}
    assert text(report["prompts"]["eve"]).strip()
    destination = project / "docs" / "dev" / "tmp" / "rev"
    shared = text(destination / f"review-context-{cycle}.md")
    for marker in (CONTEXT, SETTLED, precedent, gate, other_precedent, other_gate,
                   *(name.format(c=cycle) for name in KINDS)):
        assert marker not in shared, marker
    names = staged_files(destination)
    assert core_names(cycle) | {f"review-pack-{cycle}.md", f"eve-prompt-{cycle}.md"} <= names
    assert "Tokens stay literal" in text(destination / f"review-prd-raw-{cycle}.md")
    assert "DIFF-MARKER-55d0" in text(destination / f"review-diff-{cycle}.diff")
    assert precedent in text(destination / f"review-pack-{cycle}.md")


@pytest.mark.parametrize(("cycle", "precedent", "gate", "other_precedent", "other_gate"),
                         [("e3", PRECEDENT, GATE, PRECEDENT_ALT, GATE_ALT),
                          ("e4", PRECEDENT_ALT, GATE_ALT, PRECEDENT, GATE)],
                         ids=["first-values", "near-miss-values"])
def test_staging_still_fills_the_shared_context_from_the_union_of_a_context_reading_roster(
    project: Path, cycle: str, precedent: str, gate: str, other_precedent: str,
    other_gate: str,
) -> None:
    refs = CORE + [PACK_REF, GATE_REF]
    context = union_context(refs, refs, refs)
    report = call(stage_module(), project, cycle_id=cycle, expected_context=context,
                  pack_text=pack_with(precedent), test_gate_text=gate)
    assert report["ok"] is True, report
    destination = project / "docs" / "dev" / "tmp" / "rev"
    shared = text(destination / f"review-context-{cycle}.md")
    for marker in (CONTEXT, precedent, gate, f"review-tasks-{cycle}.md",
                   f"review-prd-{cycle}.md", f"review-pack-{cycle}.md"):
        assert marker in shared, marker
    assert other_precedent not in shared and other_gate not in shared, shared
    names = staged_files(destination)
    assert not {n for n in names if n.endswith(f"-review-context-{cycle}.md")}, names
    assert core_names(cycle) <= names


# --- B3. the missing PRD grant uses the established refusal shape -------------------------------

SHAPE = {"schema_version", "ok", "error", "detail"}


@pytest.mark.parametrize("prd_ref", ["prd:00019", ALT_PRD_REF], ids=["prd-00019", "prd-00020"])
@pytest.mark.parametrize("job", ["blake", "eve"])
def test_staging_reports_a_missing_prd_grant_under_detail_with_the_four_established_keys(
    project: Path, tmp_path: Path, job: str, prd_ref: str,
) -> None:
    context = regranted("full-eve-guard", (job,), prd_ref)
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="rs1", expected_context=context,
                  input_texts=texts_renamed(context, prd_ref))
    assert_invalid_input(report)
    assert set(report) == SHAPE, report
    assert report["ok"] is False and report["schema_version"] == 1
    assert "reason" not in report
    detail = report["detail"]
    assert isinstance(detail, str) and "prd" in detail.lower(), report
    assert re.search(rf"\b{job}\b", detail), detail
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


def test_staging_names_only_the_alphabetically_first_job_under_detail_when_both_lack_the_prd(
    project: Path, tmp_path: Path,
) -> None:
    context = regranted("full-eve-guard", ("blake", "eve"))
    before = snapshot(tmp_path)
    report = call(stage_module(), project, cycle_id="rs2", expected_context=context)
    assert_invalid_input(report)
    assert set(report) == SHAPE and "reason" not in report, report
    detail = report["detail"]
    assert re.search(r"\bblake\b", detail) and "prd" in detail.lower(), detail
    assert not re.search(r"\beve\b", detail), detail
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


def test_staging_accepts_the_same_roster_when_the_grant_names_a_different_prd_id(
    project: Path,
) -> None:
    context = regranted("full-eve-guard", (), ALT_PRD_REF)
    report = call(stage_module(), project, cycle_id="rs3", expected_context=context,
                  input_texts=texts_renamed(context, ALT_PRD_REF))
    assert report["ok"] is True, report
    assert "detail" not in report and "reason" not in report
    for job in ("blake", "eve"):
        assert ALT_PRD_REF in report["input_manifest"][job], job
    assert DIFF_REF not in report["input_manifest"]["blake"]
    assert core_names("rs3") <= staged_files(project / "docs" / "dev" / "tmp" / "rev")
