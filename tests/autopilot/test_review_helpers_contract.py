"""Review staging refuses corrupt contexts and identities and keeps every reviewer input."""

from __future__ import annotations

import copy
import importlib
import os
from pathlib import Path
from typing import Any

import pytest
import test_contract as contract
import test_review_helpers as helpers
from test_review_helpers import (
    CASES,
    DESIGN,
    DIFF_REF,
    FIXTURES,
    GATE,
    PRD,
    PRIOR,
    SETTLED,
    TREE_REF,
    assert_invalid_input,
    assert_refused,
    call,
    context_for,
    sha,
    snapshot,
    text,
    texts_for,
)

stage = helpers.stage
root = helpers.root
RUBRIC_REF = "rubric:review-policy-v1"
OTHER_TREE = "6" * 40
OTHER_TREE_REF = f"repo-tree:{OTHER_TREE}"
R9 = "R9: Implementation matches PRD feature behavior exactly."
EVE_D1 = "D1: every residual finding is in exactly one of FIX/VERIFY/KNOWN."
FALLBACK = "(the pack has no Findings precedent section)"


def rebind_manifest(context: dict[str, Any]) -> None:
    allowed = context["allowed_inputs"]
    manifest = {
        "input_refs": sorted(allowed["input_refs"]),
        "per_job": {job: sorted(set(r)) for job, r in allowed["per_job"].items()},
    }
    allowed["manifest_sha256"] = contract.digest(manifest)
    context["source_bindings"]["allowed_input_manifest_sha256"] = allowed[
        "manifest_sha256"
    ]


# --- expected context validation ---------------------------------------------------------------


def drop_roster_job(context: dict[str, Any]) -> None:
    context["resolved_roster"] = [
        row for row in context["resolved_roster"] if row["job_id"] != "bob"
    ]


def drop_per_job_entry(context: dict[str, Any]) -> None:
    del context["allowed_inputs"]["per_job"]["bob"]
    rebind_manifest(context)


def mismatch_manifest_digest(context: dict[str, Any]) -> None:
    context["allowed_inputs"]["manifest_sha256"] = "0" * 64


def mismatch_policy_digest(context: dict[str, Any]) -> None:
    context["policy_digest"] = "0" * 64


@pytest.mark.parametrize(
    "corrupt",
    [
        drop_roster_job,
        drop_per_job_entry,
        mismatch_manifest_digest,
        mismatch_policy_digest,
    ],
    ids=lambda f: f.__name__,
)
def test_corrupt_expected_context_is_refused_before_any_write(
    stage, root, tmp_path, corrupt
):
    context = copy.deepcopy(CASES["full-clean"]["expected_context"])
    corrupt(context)
    evidence = importlib.import_module("review_evidence").check_evidence(
        FIXTURES["policies"]["v1"], context, CASES["full-clean"]["input"]
    )
    assert "invalid_expected_context" in evidence["defects"]
    context["source_bindings"]["prd_sha256"] = sha(PRD)
    before = snapshot(tmp_path)
    report = call(
        stage, root, expected_context=context, input_texts=texts_for(context, PRD)
    )
    assert_refused(report)
    assert snapshot(tmp_path) == before


# --- repo-tree identity ------------------------------------------------------------------------


def other_tree_context() -> dict[str, Any]:
    context = context_for(PRD)
    allowed = context["allowed_inputs"]
    swap = {TREE_REF: OTHER_TREE_REF}
    allowed["input_refs"] = sorted(swap.get(r, r) for r in allowed["input_refs"])
    for job, refs in allowed["per_job"].items():
        allowed["per_job"][job] = sorted(swap.get(r, r) for r in refs)
    context["source_bindings"]["tree_sha"] = OTHER_TREE
    rebind_manifest(context)
    return context


def other_tree_texts(context: dict[str, Any]) -> dict[str, str]:
    texts = texts_for(context, PRD)
    texts[OTHER_TREE_REF] = OTHER_TREE
    return texts


def test_repo_tree_ref_naming_a_different_bound_tree_sha_is_accepted(stage, root):
    context = other_tree_context()
    report = call(
        stage, root, expected_context=context, input_texts=other_tree_texts(context)
    )
    assert report["ok"] is True
    allowed = context["allowed_inputs"]["per_job"]
    for job, refs in report["input_manifest"].items():
        assert set(refs) <= set(allowed[job]), job
        assert TREE_REF not in refs, job


def test_repo_tree_ref_for_the_fixture_tree_is_refused_when_another_tree_is_bound(
    stage, root, tmp_path
):
    context = other_tree_context()
    stale = other_tree_texts(context)
    del stale[OTHER_TREE_REF]
    stale[TREE_REF] = helpers.TREE
    wrong_value = other_tree_texts(context)
    wrong_value[OTHER_TREE_REF] = helpers.TREE
    before = snapshot(tmp_path)
    for texts in (stale, wrong_value):
        assert_invalid_input(
            call(stage, root, expected_context=context, input_texts=texts)
        )
    assert snapshot(tmp_path) == before


# --- required refs -----------------------------------------------------------------------------


@pytest.mark.parametrize("missing", [RUBRIC_REF, DIFF_REF])
def test_missing_required_per_job_ref_is_refused_before_any_write(
    stage, root, tmp_path, missing
):
    context = context_for(PRD)
    texts = texts_for(context, PRD)
    del texts[missing]
    before = snapshot(tmp_path)
    assert_refused(call(stage, root, expected_context=context, input_texts=texts))
    assert snapshot(tmp_path) == before


# --- reviewer inputs reach the nonblind artifacts ------------------------------------------------


def nonblind_texts(report: dict[str, Any]) -> list[str]:
    blake = Path(report["prompts"]["blake"]).resolve()
    paths = [Path(row["path"]) for row in report["artifacts"]]
    paths += [Path(p) for p in report["prompts"].values()]
    return [text(p) for p in paths if p.resolve() != blake]


@pytest.mark.parametrize("marker", [SETTLED, PRIOR, GATE, FALLBACK])
def test_settled_prior_gate_and_precedent_inputs_reach_a_nonblind_artifact(
    stage, root, marker
):
    report = call(stage, root)
    assert report["ok"] is True
    assert any(marker in body for body in nonblind_texts(report)), marker
    assert marker not in text(report["prompts"]["blake"])


def test_alice_and_bob_prompts_carry_context_diff_rubric_and_the_merged_prd(
    stage, root
):
    report = call(stage, root, cycle_id="p4")
    art = root / "docs" / "dev" / "tmp" / "rev"
    for job in ("alice", "bob"):
        prompt = text(report["prompts"][job])
        assert "review-context-p4.md" in prompt, job
        assert "review-diff-p4.diff" in prompt, job
        assert R9 in prompt, job
    assert DESIGN in text(art / "review-prd-p4.md")


def test_eve_prompt_carries_the_prd_and_the_doubt_rubric_with_tokens_resolved(
    stage, root
):
    context = context_for(PRD, "fast-track-clean")
    report = call(stage, root, cycle_id="e1", expected_context=context)
    assert report["ok"] is True
    prompt = text(report["prompts"]["eve"])
    assert PRD in prompt
    assert EVE_D1 in prompt
    for bucket in ("FIX:", "VERIFY:", "KNOWN:"):
        assert bucket in prompt, bucket
    assert "{PACK_FINDINGS}" not in prompt


# --- path safety outside the project -------------------------------------------------------------


def outside_executable_existing(tmp_path: Path) -> Path:
    art = tmp_path / "elsewhere" / "rev"
    art.mkdir(parents=True)
    (art / "review-prd-c1.md").write_text("OLD", encoding="utf-8")
    (art / "review-prd-c1.md").chmod(0o755)
    return art


def outside_hardlinked_existing(tmp_path: Path) -> Path:
    art = tmp_path / "elsewhere" / "rev"
    art.mkdir(parents=True)
    other = tmp_path / "elsewhere" / "other.txt"
    other.write_text("SHARED", encoding="utf-8")
    os.link(other, art / "review-prd-c1.md")
    return art


def outside_symlink_output(tmp_path: Path) -> Path:
    art = tmp_path / "elsewhere" / "rev"
    art.mkdir(parents=True)
    target = tmp_path / "elsewhere" / "target.md"
    target.write_text("TARGET", encoding="utf-8")
    (art / "alice-prompt-c1.md").symlink_to(target)
    return art


@pytest.mark.parametrize(
    "make",
    [outside_executable_existing, outside_hardlinked_existing, outside_symlink_output],
    ids=lambda f: f.__name__,
)
def test_unsafe_output_under_an_artifact_root_outside_the_project_is_refused(
    stage, root, tmp_path, make
):
    art = make(tmp_path)
    before = snapshot(tmp_path)
    assert_refused(call(stage, root, artifact_root=art))
    assert snapshot(tmp_path) == before
