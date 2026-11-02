"""Bounded AP 00013 cap-recovery regressions; no workflow state mutations."""

from __future__ import annotations

import copy
import os
import sys
from pathlib import Path

import pytest
from test_cycle1_boundaries_context import reached
from test_cycle1_boundaries_verify import ARTIFACT, LOG, verify_call, write_script
from test_local_boundary import World, git, library, make_world, one_json, run_cli, tree
from test_review_close_helpers import assert_ok, row, run, scenario
from test_review_close_helpers_gates import snapshot
from test_review_evidence_helpers import clean, result
from test_review_helpers import CASES, CONTEXT, DESIGN, GATE, PRD, call, context_for, sha


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path.resolve())


def test_policy_export_refuses_a_hard_link_to_live_state(world: World) -> None:
    state = world.target / "docs/dev/project-management/autopilot/state.json"
    out = world.base / "ordinary-policy.json"
    os.link(state, out)
    before = state.read_bytes()
    proc, _ = run_cli(world, "--export-policy", "--out", out)
    assert proc.returncode != 0
    assert b"Traceback" not in proc.stderr
    assert state.read_bytes() == out.read_bytes() == before


@pytest.mark.parametrize("output", ["log", "artifact"])
def test_verify_refuses_case_alias_of_an_argv_file(world: World, output: str) -> None:
    script, body = write_script(world)
    alias = script.with_name(script.name.upper())
    if not alias.exists():
        pytest.skip("filesystem is case sensitive")
    before = tree(world.target)
    report = verify_call(world, [sys.executable, str(alias)], **{output: script})
    assert report == {"schema_version": 1, "ok": False, "error": "unsafe-artifact-path"}
    assert script.read_text() == body
    assert tree(world.target) == before
    assert not (world.base / "spawned").exists()


def test_sink_refuses_case_alias_of_worktree_pointer(world: World) -> None:
    worktree = world.base / "linked"
    git(world.target, "worktree", "add", "-q", "-b", "linked", str(worktree))
    alias = worktree / ".GIT"
    if not alias.exists():
        pytest.skip("filesystem is case sensitive")
    assert library("log_sink_refusal").refuse(alias, worktree) == "resolves inside the git directory"


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("executable", ["missing", "not-executable"])
def test_spawn_failure_is_controlled_and_preserves_outputs(
    world: World, existing: bool, executable: str,
) -> None:
    if existing:
        (world.target / LOG).write_text("old log")
        (world.target / ARTIFACT).write_text("old artifact")
    before = tree(world.target)
    command = world.base / executable
    if executable == "not-executable":
        command.write_text("#!/bin/sh\nexit 0\n")
        command.chmod(0o644)
    head = git(world.target, "rev-parse", "HEAD")
    proc, _ = run_cli(world, "--verify", "--project-root", world.target, "--head-sha", head,
                      "--artifact", ARTIFACT, "--log", LOG, "--", command)
    assert proc.returncode == 1
    assert b"Traceback" not in proc.stderr
    report = one_json(proc)
    assert (report["ok"], report["error"]) == (False, "spawn-failed")
    assert tree(world.target) == before


def test_tail_sweep_accepts_a_subset_of_evidence_findings() -> None:
    report = run(library("review_close"), scenario(["R2", "R3", "R4"]),
                 [row("R2", "fix"), row("R4", "defer")], batch_id="tail-sweep",
                 read_snapshot=snapshot(tasks=[], rework_task_ids=[]))
    assert_ok(report)
    assert len(report["task_proposals"]) == 1
    assert len(report["decision_proposals"]) == 2
    assert report["reviewer_results"] == report["rubric_verdicts"] == []


def test_staging_hides_ungranted_context_plan_and_test_results(world: World) -> None:
    context = copy.deepcopy(CASES["full-clean"]["expected_context"])
    context["source_bindings"]["prd_sha256"] = sha(PRD)
    project = world.base / "review-project"
    project.mkdir()
    git(project, "init", "-q")
    # This fixture grants only PRD, tree, rubric and diff: none grant these bodies.
    report = call(library("review_stage"), project, expected_context=context,
                  tasks=[{"id": "T1", "name": "TASK-PRIVATE-MARKER"}])
    assert report["ok"] is True, report
    for job in ("alice", "bob"):
        body, _ = reached(report["prompts"][job])
        for marker in (CONTEXT, DESIGN, GATE, "TASK-PRIVATE-MARKER"):
            assert marker not in body, (job, marker)
        assert PRD in body


@pytest.mark.parametrize("kind", ["separate", "bare"])
def test_staging_refuses_nonstandard_external_git_directory(world: World, kind: str) -> None:
    outside = world.base / "outside"
    metadata = world.base / "metadata"
    outside.mkdir()
    if kind == "separate":
        git(outside, "init", "-q", "--separate-git-dir", str(metadata))
    else:
        git(outside, "init", "-q", "--bare", str(metadata))
    before = tree(metadata)
    report = call(library("review_stage"), world.target, artifact_root=metadata / "reviews")
    assert (report["ok"], report["error"]) == (False, "unsafe-output")
    assert tree(metadata) == before


@pytest.mark.parametrize("omitted,hidden", [
    ("implementation-audit", (CONTEXT,)),
    ("plan", (DESIGN, "TASK-PRIVATE-MARKER")),
    ("test-results", (GATE,)),
    ("prd", (PRD,)),
])
def test_staged_context_filters_each_input_kind_independently(
    tmp_path: Path, omitted: str, hidden: tuple[str, ...],
) -> None:
    project = tmp_path.resolve() / "project"
    project.mkdir()
    git(project, "init", "-q")
    context = context_for(PRD)
    allowed = context["allowed_inputs"]
    allowed["per_job"]["bob"] = [
        ref for ref in allowed["per_job"]["bob"] if ref.split(":", 1)[0] != omitted
    ]
    manifest = {key: allowed[key] for key in ("input_refs", "per_job")}
    digest = library("review_evidence").digest(manifest)
    allowed["manifest_sha256"] = digest
    context["source_bindings"]["allowed_input_manifest_sha256"] = digest
    report = call(library("review_stage"), project, expected_context=context,
                  tasks=[{"id": "T1", "name": "TASK-PRIVATE-MARKER"}])
    assert report["ok"] is True, report
    thin, _ = reached(report["prompts"]["bob"])
    full, _ = reached(report["prompts"]["alice"])
    for marker in hidden:
        assert marker not in thin
        assert marker in full


def test_attempt_validation_does_not_allocate_from_the_supplied_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = library("review_evidence")
    context, evidence = clean()
    result(evidence, "alice")["attempt"] = 10**12

    def bounded_range(*args: int) -> range:
        assert max(args) <= 100, "attempt controls an unbounded allocation"
        return range(*args)

    monkeypatch.setattr(checker, "range", bounded_range, raising=False)
    report = checker.check_evidence(checker.load_policy(), context, evidence)
    assert not report["ok"]
    assert "attempt_sequence_invalid" in report["defects"]
