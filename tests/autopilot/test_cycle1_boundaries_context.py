"""Cycle-1 hardening: files a job prompt references are built from that job's manifest."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from test_cycle1_boundaries_stage import HISTORY_REF, PACK_REF, PACK_WITH_PRECEDENT, PRECEDENT
from test_local_boundary import git, library
from test_review_helpers import CONTEXT, DIFF_REF, PRD, PRIOR, SETTLED, call, context_for, text

PATH_RE = re.compile(r"/[^\s`'\"<>()|\[\]]+")
BASE_STAGED = {"review-tasks", "review-prd-raw", "review-prd", "review-context", "review-diff",
               "review-pack"}
FULL = [DIFF_REF, PACK_REF, HISTORY_REF]


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path.resolve() / "project"
    (root / "docs" / "dev" / "tmp").mkdir(parents=True)
    git(root, "init", "-q", "-b", "master")
    return root


def grant(extras: dict[str, list[str]]) -> dict[str, Any]:
    """Expected context where alice and bob get the no-diff base plus their own extra refs."""
    context = context_for(PRD)
    allowed = context["allowed_inputs"]
    thin = sorted(ref for ref in allowed["per_job"]["alice"] if not ref.startswith("diff:"))
    refs = sorted({*allowed["input_refs"], PACK_REF, HISTORY_REF})
    per_job = {"blake": allowed["per_job"]["blake"]}
    per_job.update({job: sorted({*thin, *more}) for job, more in extras.items()})
    digest = library("review_evidence").digest({"input_refs": refs, "per_job": per_job})
    allowed.update(input_refs=refs, per_job=per_job, manifest_sha256=digest)
    context["source_bindings"]["allowed_input_manifest_sha256"] = digest
    return context


def stage(project: Path, extras: dict[str, list[str]], cycle: str = "x1") -> dict[str, Any]:
    report = call(library("review_stage"), project, expected_context=grant(extras),
                  cycle_id=cycle, pack_text=PACK_WITH_PRECEDENT)
    assert report["ok"] is True, report
    return report


def reached(prompt: str) -> tuple[str, set[Path]]:
    """The prompt text plus the text of every staged file it names, directly or through
    other staged files (paths are extracted from the text, never hard-coded)."""
    prompt_path = Path(prompt).resolve()
    art, seen, queue, combined = prompt_path.parent, set(), [prompt_path], []
    while queue:
        body = text(queue.pop())
        combined.append(body)
        for raw in PATH_RE.findall(body):
            path = Path(raw.rstrip(".,;:"))
            if not path.is_file() or path.resolve().parent != art or "-prompt-" in path.name:
                continue
            if path.resolve() not in seen:
                seen.add(path.resolve())
                queue.append(path.resolve())
    return "\n".join(combined), seen


@pytest.mark.parametrize(("full_job", "thin_job"), [("alice", "bob"), ("bob", "alice")])
def test_a_thin_job_reaches_no_pack_findings_or_history_through_any_file_its_prompt_names(
    project: Path, full_job: str, thin_job: str,
) -> None:
    report = stage(project, {full_job: FULL, thin_job: []})
    thin, thin_files = reached(report["prompts"][thin_job])
    full, full_files = reached(report["prompts"][full_job])
    assert thin_files and full_files
    assert CONTEXT in thin and CONTEXT in full
    for leaked in (PRECEDENT, SETTLED, PRIOR):
        assert leaked not in thin, (thin_job, leaked)
        assert leaked in full, (full_job, leaked)


@pytest.mark.parametrize("job", ["alice", "bob"])
@pytest.mark.parametrize(("granted", "seen", "hidden"), [
    (HISTORY_REF, (SETTLED, PRIOR), (PRECEDENT,)),
    (PACK_REF, (PRECEDENT,), (SETTLED, PRIOR)),
], ids=["history-only", "pack-only"])
def test_a_job_reaches_only_the_pack_or_history_text_its_manifest_lists(
    project: Path, job: str, granted: str, seen: tuple[str, ...], hidden: tuple[str, ...],
) -> None:
    other = "bob" if job == "alice" else "alice"
    report = stage(project, {job: [granted], other: FULL})
    body, files = reached(report["prompts"][job])
    assert files and CONTEXT in body
    for marker in seen:
        assert marker in body, (job, marker)
    for marker in hidden:
        assert marker not in body, (job, marker)
    assert report["input_manifest"][job] == sorted(
        grant({job: [granted], other: FULL})["allowed_inputs"]["per_job"][job])


def test_staging_with_every_job_granted_the_full_set_lists_every_file_a_prompt_needs(
    project: Path,
) -> None:
    report = stage(project, {"alice": FULL, "bob": FULL}, cycle="f1")
    listed = {Path(row["path"]).resolve() for row in report["artifacts"]}
    kinds = {row["kind"] for row in report["artifacts"]}
    assert BASE_STAGED <= kinds
    art = Path(report["prompts"]["alice"]).resolve().parent
    assert {p.resolve() for p in art.iterdir()} == listed
    for job in ("alice", "bob"):
        body, files = reached(report["prompts"][job])
        assert files <= listed, job
        for marker in (CONTEXT, PRECEDENT, SETTLED, PRIOR):
            assert marker in body, (job, marker)
        assert "review-diff-f1.diff" in body and "review-pack-f1.md" in body
