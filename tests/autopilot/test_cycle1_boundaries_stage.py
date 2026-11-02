"""Cycle-1 hardening: usage boundary, live-state and external roots, per-job manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import PACKAGE, STATE, World, assert_usage, canonical, findings_sets, git
from test_local_boundary import library, make_world, run_cli, stage_payload, tree, write_input
from test_review_close_helpers import kwargs_for, valid_batch
from test_review_helpers import DIFF, PACK, PRD, PRIOR, SETTLED, call, context_for, snapshot, text

LIVE = ("docs", "dev", "project-management", "autopilot")
PRECEDENT = "PRECEDENT-MARKER-77c1"
PACK_WITH_PRECEDENT = f"{PACK}\n\n## Findings precedent\n{PRECEDENT}\n\n## Other\nrest\n"
PACK_REF, HISTORY_REF = "context-pack:pk1", "history:hs1"


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path.resolve())


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path.resolve() / "project"
    (root / "docs" / "dev" / "tmp").mkdir(parents=True)
    root.joinpath(*LIVE).mkdir(parents=True)
    git(root, "init", "-q", "-b", "master")
    return root


def stage_module():
    return library("review_stage")


# --- 1. malformed request values stay inside the exit-2 usage boundary --------------------------


def assert_clean_usage_refusal(world: World, option: str, payload: dict[str, Any]) -> None:
    before = tree(world.target)
    proc, _ = run_cli(world, option, write_input(world, payload))
    assert_usage(proc)
    assert b"Traceback" not in proc.stderr, proc.stderr
    assert tree(world.target) == before and list(world.cwd.iterdir()) == []


@pytest.mark.parametrize("bad", [["x"], [None], [1], [["a"]], [[]], [True]],
                         ids=["string", "null", "int", "list", "empty-list", "bool"])
def test_group_findings_rejects_a_non_object_element_with_exit_2(world: World, bad: list) -> None:
    assert_clean_usage_refusal(world, "--group-findings", {"findings": bad})
    mixed = [*findings_sets()[0], bad[0]]
    assert_clean_usage_refusal(world, "--group-findings", {"findings": mixed})
    for findings in (findings_sets()[0], []):
        proc, _ = run_cli(world, "--group-findings", write_input(world, {"findings": findings}))
        assert proc.returncode == 0, proc.stderr


PREPARE_BAD = {
    "cycle": ["1", "2", True, 1.5, None],
    "batch_id": ["", 5, None, ["decision-gate"]],
    "default_tier": ["gpt-9", "sonnet-4", "", 7, None],
    "review_ref": [5, None, ["x"]],
}


@pytest.mark.parametrize("field", sorted(PREPARE_BAD))
def test_prepare_close_rejects_mistyped_request_fields_with_exit_2(
    world: World, field: str,
) -> None:
    case, chosen = valid_batch()
    for bad in PREPARE_BAD[field]:
        assert_clean_usage_refusal(world, "--prepare-close", kwargs_for(case, chosen, **{field: bad}))
    for over in ({}, {"cycle": 5, "default_tier": "opus"}):
        proc, _ = run_cli(world, "--prepare-close",
                          write_input(world, kwargs_for(case, chosen, **over)))
        assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("tasks", [["x"], [None], [1], [{"id": "T1"}, "x"], {"id": "T1"}, "T1"],
                         ids=["string", "null", "int", "valid-then-string", "dict", "text"])
def test_stage_review_rejects_non_object_task_entries_with_exit_2(
    world: World, tasks: Any,
) -> None:
    assert_clean_usage_refusal(world, "--stage-review",
                               {**stage_payload(world.target), "tasks": tasks})
    good = [{"id": "T1", "name": "first", "status": "done"}, {"id": "T2", "name": "second"}]
    for ok_tasks in (good, []):
        proc, _ = run_cli(world, "--stage-review",
                          write_input(world, {**stage_payload(world.target), "tasks": ok_tasks}))
        assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("cycle", [7, True, 1.5, None, ["c1"]])
def test_stage_review_rejects_a_non_string_cycle_id_with_exit_2(world: World, cycle: Any) -> None:
    assert_clean_usage_refusal(world, "--stage-review",
                               {**stage_payload(world.target), "cycle_id": cycle})


# --- 2. live-state refusal ignores the spelling case of the path --------------------------------

SPELLINGS = [("docs", "dev", "project-management", "autopilot", "x"),
             ("DOCS", "dev", "project-management", "AUTOPILOT", "x"),
             ("docs", "dev", "project-management", "Autopilot", "x"),
             ("Docs", "Dev", "Project-Management", "autopilot", "x", "deeper")]


@pytest.mark.parametrize("spelling", SPELLINGS, ids=["exact", "upper", "title", "mixed-deep"])
def test_stage_review_refuses_a_live_state_root_in_every_spelling_case(
    project: Path, spelling: tuple[str, ...],
) -> None:
    variant_dir = project.joinpath(*spelling[:4])
    variant_dir.mkdir(parents=True, exist_ok=True)  # a real directory where the fs is case-sensitive
    live = project.joinpath(*LIVE)
    before = snapshot(project)
    for root_arg in ("/".join(spelling), project.joinpath(*spelling)):
        report = call(stage_module(), project, artifact_root=root_arg)
        assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
    assert list(live.iterdir()) == [] and list(variant_dir.iterdir()) == []
    assert snapshot(project) == before


def test_stage_review_still_writes_beside_a_near_miss_of_the_live_directory(project: Path) -> None:
    for sibling in ("autopilot-notes", "autopilots"):
        report = call(stage_module(), project,
                      artifact_root=f"docs/dev/project-management/{sibling}/x")
        assert report["ok"] is True, report
        assert all(Path(a["path"]).is_file() for a in report["artifacts"])
    assert list(project.joinpath(*LIVE).iterdir()) == []


# --- 3. export-policy never writes into live workflow state -------------------------------------


def test_export_policy_refuses_an_out_file_inside_live_state_and_changes_nothing(
    world: World,
) -> None:
    live = world.target / STATE
    links = world.base / "links"
    links.mkdir()
    (links / "dir-link").symlink_to(live, target_is_directory=True)
    (links / "file-link.json").symlink_to(live / "state.json")
    targets = [live / "state.json", live / "fresh.json", live / "sub" / "deep.json",
               links / "dir-link" / "state.json", links / "dir-link" / "via-link.json",
               links / "file-link.json"]
    before, state = tree(world.target), (live / "state.json").read_bytes()
    for out in targets:
        proc, _ = run_cli(world, "--export-policy", "--out", out)
        assert_usage(proc)
        assert proc.stdout == b"" and b"Traceback" not in proc.stderr
        assert (live / "state.json").read_bytes() == state
    assert tree(world.target) == before
    assert (links / "file-link.json").is_symlink() and not (live / "fresh.json").exists()


def test_export_policy_still_writes_the_canonical_policy_to_ordinary_paths(world: World) -> None:
    policy = json.loads((PACKAGE / "contracts" / "review-policy-v1.json").read_bytes())
    near_miss = world.target / "docs" / "dev" / "project-management" / "autopilot-archive"
    for directory in (world.base / "out", near_miss):
        directory.mkdir(parents=True)
        proc, _ = run_cli(world, "--export-policy", "--out", directory / "policy.json")
        assert proc.returncode == 0, proc.stderr
        assert (directory / "policy.json").read_bytes() == canonical(policy) + b"\n"


# --- 4. per-job manifests constrain the rendered inputs -----------------------------------------


def context_with(full_job: str, thin_job: str) -> dict[str, Any]:
    context = context_for(PRD)
    allowed = context["allowed_inputs"]
    thin = [ref for ref in allowed["per_job"]["alice"] if not ref.startswith("diff:")]
    refs = sorted({*allowed["input_refs"], PACK_REF, HISTORY_REF})
    per_job = {"blake": allowed["per_job"]["blake"], full_job: refs, thin_job: sorted(thin)}
    digest = library("review_evidence").digest({"input_refs": refs, "per_job": per_job})
    allowed.update(input_refs=refs, per_job=per_job, manifest_sha256=digest)
    context["source_bindings"]["allowed_input_manifest_sha256"] = digest
    return context


@pytest.mark.parametrize(("full_job", "thin_job"), [("alice", "bob"), ("bob", "alice")])
def test_a_job_prompt_omits_diff_pack_and_history_its_manifest_does_not_list(
    project: Path, full_job: str, thin_job: str,
) -> None:
    context = context_with(full_job, thin_job)
    report = call(stage_module(), project, expected_context=context, cycle_id="m1",
                  pack_text=PACK_WITH_PRECEDENT)
    assert report["ok"] is True, report
    assert report["input_manifest"][thin_job] == sorted(
        context["allowed_inputs"]["per_job"][thin_job])
    thin, full = text(report["prompts"][thin_job]), text(report["prompts"][full_job])
    for leaked in ("review-diff-m1.diff", "review-pack-m1.md", PRECEDENT, SETTLED, PRIOR):
        assert leaked not in thin, (thin_job, leaked)
        assert leaked in full, (full_job, leaked)
    assert DIFF.splitlines()[1] not in thin


# --- 5. artifact roots outside the project get the same destination protections -----------------


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    repo = tmp_path.resolve() / "second repo"
    (repo / "docs" / "rev").mkdir(parents=True)
    (repo / "docs" / "rev" / "review-tasks-e1.md").write_text("TRACKED-ORIGINAL\n", "utf-8")
    repo.joinpath(*LIVE).mkdir(parents=True)
    (repo.joinpath(*LIVE) / "state.json").write_text('{"phase": "review"}', "utf-8")
    git(repo, "init", "-q", "-b", "master")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def test_stage_review_refuses_an_external_root_that_would_overwrite_a_tracked_file(
    project: Path, outside: Path,
) -> None:
    before = snapshot(outside)
    report = call(stage_module(), project, cycle_id="e1", artifact_root=outside / "docs" / "rev")
    assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
    assert snapshot(outside) == before
    tracked = outside / "docs" / "rev" / "review-tasks-e1.md"
    assert tracked.read_text("utf-8") == "TRACKED-ORIGINAL\n"


@pytest.mark.parametrize("rel", [LIVE, (*LIVE, "review"), (*LIVE, "a", "b")],
                         ids=["live-dir", "under-live", "deep-under-live"])
def test_stage_review_refuses_another_repositorys_live_state_directory(
    project: Path, outside: Path, rel: tuple[str, ...],
) -> None:
    before = snapshot(outside)
    report = call(stage_module(), project, artifact_root=outside.joinpath(*rel))
    assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
    assert snapshot(outside) == before


def test_stage_review_refuses_an_external_root_reached_through_a_symlinked_ancestor(
    project: Path, outside: Path, tmp_path: Path,
) -> None:
    clean = tmp_path.resolve() / "clean target"
    clean.mkdir()
    links = tmp_path.resolve() / "links"
    links.mkdir()
    (links / "to-clean").symlink_to(clean, target_is_directory=True)
    (links / "to-live").symlink_to(outside.joinpath(*LIVE), target_is_directory=True)
    before = (snapshot(clean), snapshot(outside))
    for root_arg in (links / "to-clean" / "rev", links / "to-live" / "rev"):
        report = call(stage_module(), project, artifact_root=root_arg)
        assert (report["ok"], report["error"]) == (False, "unsafe-output"), report
    assert (snapshot(clean), snapshot(outside)) == before


def test_stage_review_still_writes_to_a_clean_root_outside_any_repository(
    project: Path, tmp_path: Path,
) -> None:
    for name in ("plain one", "plain two"):
        art = tmp_path.resolve() / name / "rev"
        report = call(stage_module(), project, cycle_id="k1", artifact_root=art)
        assert report["ok"] is True, report
        assert {Path(a["path"]).parent for a in report["artifacts"]} == {art}
        assert (art / "review-tasks-k1.md").is_file()
