"""Crash-recoverable PRD bucket moves and deferred records (files.py sagas)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "autopilot" / "controller"))

from autopilot_state import files, schema
from autopilot_state.files import SagaBoundary
from autopilot_state.store import StateStore

PRD = "00042-sample.md"
OTHER = "00043-other.md"
BUCKETS = ("backlog", "wip", "hold", "done")
MOVE_BOUNDARIES = (
    SagaBoundary.AFTER_MKDIR_BEFORE_INTENT,
    SagaBoundary.AFTER_INTENT_BEFORE_MOVE,
    SagaBoundary.AFTER_RENAME_BEFORE_DIRECTORY_FSYNC,
    SagaBoundary.AFTER_MOVE_BEFORE_APPEND,
    SagaBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC,
    SagaBoundary.AFTER_APPEND_BEFORE_COMMIT,
    SagaBoundary.AFTER_COMMIT_BEFORE_MARKER_DELETE,
)
DEFER_BOUNDARIES = (
    SagaBoundary.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC,
    SagaBoundary.AFTER_APPEND_BEFORE_COMMIT,
    SagaBoundary.AFTER_COMMIT_BEFORE_MARKER_DELETE,
)
COMPLETE_BOUNDARIES = (
    SagaBoundary.PRD_COMPLETE_MOVE_STAGED,
    SagaBoundary.PRD_COMPLETE_MOVE_COMMITTED,
)


class Crash(Exception):
    """Simulated process death at a saga boundary."""


@dataclass(frozen=True)
class Project:
    root: Path
    store: StateStore

    def bucket(self, name: str) -> Path:
        return self.root / files.PRD_ROOT / name

    def where(self, prd: str = PRD) -> list[str]:
        return [name for name in BUCKETS if (self.bucket(name) / prd).exists()]

    def workflow(self) -> dict:
        return self.store.read()["workflow"]

    def activate(self, prd: str) -> None:
        def enter(state: dict) -> None:
            state["workflow"]["work"] = work(prd, "build", [])
        self.store.transaction(enter)


def work(prd: str, phase: str, completed_phases: list[str]) -> dict:
    return {"prd": prd, "source": "wip", "entered_at": "2026-11-24T10:00:00Z",
            "phase": phase, "completed_phases": completed_phases,
            "lane": None, "lane_reason": None}


def make_project(tmp_path: Path, *, parks: int = 0, phase: str = "build",
                 completed_phases: tuple[str, ...] = ()) -> Project:
    root = tmp_path.resolve() / "project"
    for name in BUCKETS:
        (root / files.PRD_ROOT / name).mkdir(parents=True)
    for prd in (PRD, OTHER):
        (root / files.PRD_ROOT / "wip" / prd).write_text(f"---\n---\n# {prd}\n")
    controller = root / ".autopilot" / "controller"
    controller.mkdir(parents=True)
    store = StateStore(controller / "state.json")
    state = schema.new_state(repo_root=root, project_id="a" * 64,
                             workflow_id="workflow-test")
    state["workflow"]["batch"] = {"completed_prds": [], "parks_consecutive": parks}
    state["workflow"]["work"] = work(PRD, phase, list(completed_phases))
    state["workflow"]["tasks"] = [{"id": "task-1", "subject": "Build it",
                                   "status": "in_progress", "depends_on": [],
                                   "attempts": []}]
    store.initialize(state)
    return Project(root, store)


def crash_at(boundary: SagaBoundary):
    def hook(reached: SagaBoundary) -> None:
        if reached is boundary:
            raise Crash(boundary)
    return hook


def run_kind(project: Project, kind: str, **extra: object) -> files.SagaResult:
    if kind == "stall":
        return files.stall(project.store, project_root=project.root, prd=PRD,
                           site="cap_regression", detail="review cap hit", **extra)
    if kind == "park":
        return files.park(project.store, project_root=project.root, prd=PRD, **extra)
    if kind == "complete":
        return files.complete_prd(project.store, project_root=project.root, prd=PRD,
                                  **extra)
    return files.defer_record(project.store, project_root=project.root, prd=PRD,
                              record={"type": "deferred_decision", "summary": "later"},
                              **extra)


@pytest.mark.parametrize("kind", ["stall", "park"])
def test_clean_stall_and_park_move_wip_to_hold_and_record_once(tmp_path, kind):
    project = make_project(tmp_path)
    content = (project.bucket("wip") / PRD).read_text()

    result = run_kind(project, kind)

    assert project.where() == ["hold"]
    assert (project.bucket("hold") / PRD).read_text() == content
    records = files.load_deferred_records(project.store)
    assert len(records) == 1
    assert records[0]["type"] == "stall"
    assert records[0]["kind"] == kind
    assert records[0]["prd"] == PRD
    assert records[0]["op_id"] == result.operation_id
    workflow = project.workflow()
    assert workflow["recovery"] is None
    assert workflow["work"] is None
    assert workflow["tasks"] == []
    assert result.replayed is False


def test_stall_records_caller_site_and_resets_park_counter(tmp_path):
    project = make_project(tmp_path, parks=1)

    result = run_kind(project, "stall")

    assert files.load_deferred_records(project.store)[0]["site"] == "cap_regression"
    assert project.workflow()["batch"]["parks_consecutive"] == 0
    assert result.systemic_halt is False


def test_second_consecutive_park_signals_systemic_halt(tmp_path):
    project = make_project(tmp_path)

    first = run_kind(project, "park")
    assert first.systemic_halt is False
    assert project.workflow()["batch"]["parks_consecutive"] == 1

    project.activate(OTHER)
    second = files.park(project.store, project_root=project.root, prd=OTHER)

    assert second.systemic_halt is True
    assert project.workflow()["batch"]["parks_consecutive"] == 2
    assert project.where(OTHER) == ["hold"]


def test_park_after_a_stall_does_not_halt(tmp_path):
    project = make_project(tmp_path, parks=1)
    run_kind(project, "stall")
    project.activate(OTHER)

    result = files.park(project.store, project_root=project.root, prd=OTHER)

    assert result.systemic_halt is False
    assert project.workflow()["batch"]["parks_consecutive"] == 1


@pytest.mark.parametrize("kind", ["stall", "park"])
@pytest.mark.parametrize("boundary", MOVE_BOUNDARIES, ids=str)
def test_crash_at_each_move_boundary_replays_without_double_move_or_append(
        tmp_path, kind, boundary):
    project = make_project(tmp_path)

    with pytest.raises(Crash):
        run_kind(project, kind, boundary_hook=crash_at(boundary))
    result = run_kind(project, kind)

    assert project.where() == ["hold"]
    records = files.load_deferred_records(project.store)
    assert len(records) == 1
    assert records[0]["op_id"] == result.operation_id
    workflow = project.workflow()
    assert workflow["recovery"] is None
    assert workflow["work"] is None
    assert workflow["batch"]["parks_consecutive"] == (1 if kind == "park" else 0)
    assert result.replayed is (boundary is not SagaBoundary.AFTER_MKDIR_BEFORE_INTENT)


@pytest.mark.parametrize("boundary", DEFER_BOUNDARIES, ids=str)
def test_crash_at_each_defer_boundary_replays_without_double_append(tmp_path, boundary):
    project = make_project(tmp_path)

    with pytest.raises(Crash):
        run_kind(project, "defer", boundary_hook=crash_at(boundary))
    result = run_kind(project, "defer")

    records = files.load_deferred_records(project.store)
    assert records == ({"type": "deferred_decision", "summary": "later",
                        "op_id": result.operation_id, "prd": PRD},)
    assert result.replayed is True
    assert project.workflow()["recovery"] is None
    assert project.where() == ["wip"]


def test_defer_appends_record_without_moving_or_resetting_work(tmp_path):
    project = make_project(tmp_path, parks=1)

    run_kind(project, "defer")

    assert project.where() == ["wip"]
    workflow = project.workflow()
    assert workflow["work"]["prd"] == PRD
    assert workflow["batch"]["parks_consecutive"] == 1
    assert len(files.load_deferred_records(project.store)) == 1


def test_defer_replay_with_a_different_record_conflicts(tmp_path):
    project = make_project(tmp_path)
    with pytest.raises(Crash):
        run_kind(project, "defer",
                 boundary_hook=crash_at(SagaBoundary.AFTER_APPEND_BEFORE_COMMIT))

    with pytest.raises(files.RecoveryConflictError):
        files.defer_record(project.store, project_root=project.root, prd=PRD,
                           record={"type": "deferred_decision", "summary": "other"})

    assert len(files.load_deferred_records(project.store)) == 1


@pytest.mark.parametrize("kind", ["stall", "park"])
def test_replay_after_file_vanished_requires_recovery(tmp_path, kind):
    project = make_project(tmp_path)
    with pytest.raises(Crash):
        run_kind(project, kind,
                 boundary_hook=crash_at(SagaBoundary.AFTER_INTENT_BEFORE_MOVE))
    (project.bucket("wip") / PRD).unlink()

    with pytest.raises(files.RecoveryRequiredError):
        run_kind(project, kind)

    assert project.workflow()["recovery"] is not None
    assert files.load_deferred_records(project.store) == ()


def test_replay_after_file_replaced_in_wip_requires_recovery(tmp_path):
    project = make_project(tmp_path)
    with pytest.raises(Crash):
        run_kind(project, "stall",
                 boundary_hook=crash_at(SagaBoundary.AFTER_INTENT_BEFORE_MOVE))
    original = project.bucket("wip") / PRD
    original.rename(project.bucket("backlog") / "keep-inode-alive.md")
    original.write_text("a different artifact\n")

    with pytest.raises(files.RecoveryRequiredError):
        run_kind(project, "stall")

    assert project.where() == ["wip"]
    assert files.load_deferred_records(project.store) == ()


def test_replay_after_moved_file_returned_to_wip_requires_recovery(tmp_path):
    project = make_project(tmp_path)
    with pytest.raises(Crash):
        run_kind(project, "park",
                 boundary_hook=crash_at(SagaBoundary.AFTER_MOVE_BEFORE_APPEND))
    os.rename(project.bucket("hold") / PRD, project.bucket("wip") / PRD)

    with pytest.raises(files.RecoveryRequiredError):
        run_kind(project, "park")

    assert project.where() == ["wip"]
    assert files.load_deferred_records(project.store) == ()
    assert project.workflow()["batch"]["parks_consecutive"] == 0


def test_pending_stall_intent_refuses_a_competing_park(tmp_path):
    project = make_project(tmp_path)
    with pytest.raises(Crash):
        run_kind(project, "stall",
                 boundary_hook=crash_at(SagaBoundary.AFTER_INTENT_BEFORE_MOVE))

    with pytest.raises(files.RecoveryConflictError):
        run_kind(project, "park")

    assert project.where() == ["wip"]


@pytest.mark.parametrize("kind", ["stall", "park"])
@pytest.mark.parametrize("bucket", ["hold", "backlog", "missing"])
def test_stall_and_park_refuse_when_prd_is_not_in_wip_on_disk(tmp_path, kind, bucket):
    project = make_project(tmp_path)
    source = project.bucket("wip") / PRD
    if bucket == "missing":
        source.unlink()
    else:
        os.rename(source, project.bucket(bucket) / PRD)
    before = project.store.read()

    with pytest.raises(files.BucketError):
        run_kind(project, kind)

    assert project.where() == ([] if bucket == "missing" else [bucket])
    assert project.store.read() == before
    assert before["workflow"]["work"]["prd"] == PRD
    assert files.load_deferred_records(project.store) == ()


def test_stall_refuses_a_prd_that_is_not_the_active_one(tmp_path):
    project = make_project(tmp_path)

    with pytest.raises(files.PreconditionError):
        files.stall(project.store, project_root=project.root, prd=OTHER,
                    site="cap_regression", detail="wrong PRD")

    assert project.where(OTHER) == ["wip"]


def test_complete_moves_wip_to_done_and_records_completion(tmp_path):
    project = make_project(tmp_path, parks=1, phase="done",
                           completed_phases=("build", "review"))
    seen: list[SagaBoundary] = []

    result = run_kind(project, "complete", boundary_hook=seen.append)

    assert project.where() == ["done"]
    workflow = project.workflow()
    assert workflow["batch"]["completed_prds"] == [PRD]
    assert workflow["batch"]["parks_consecutive"] == 0
    assert workflow["work"] is None
    assert workflow["recovery"] is None
    assert result.kind == "complete"
    assert files.load_deferred_records(project.store) == ()
    assert seen == list(COMPLETE_BOUNDARIES)


def test_stall_never_trips_the_complete_boundary_pair(tmp_path):
    project = make_project(tmp_path)
    seen: list[SagaBoundary] = []

    run_kind(project, "stall", boundary_hook=seen.append)

    assert seen == list(MOVE_BOUNDARIES)
    assert not set(seen) & set(COMPLETE_BOUNDARIES)


@pytest.mark.parametrize("boundary", COMPLETE_BOUNDARIES, ids=str)
def test_crash_at_each_complete_boundary_replays_without_double_entry(tmp_path, boundary):
    project = make_project(tmp_path, phase="done", completed_phases=("review",))

    with pytest.raises(Crash):
        run_kind(project, "complete", boundary_hook=crash_at(boundary))
    result = run_kind(project, "complete")

    assert project.where() == ["done"]
    assert project.workflow()["batch"]["completed_prds"] == [PRD]
    assert project.workflow()["recovery"] is None
    assert result.replayed is True


def test_complete_replay_resumes_after_rename_landed_before_commit(tmp_path):
    project = make_project(tmp_path, phase="done", completed_phases=("review",))
    with pytest.raises(Crash):
        run_kind(project, "complete",
                 boundary_hook=crash_at(SagaBoundary.PRD_COMPLETE_MOVE_STAGED))
    os.rename(project.bucket("wip") / PRD, project.bucket("done") / PRD)

    run_kind(project, "complete")

    assert project.where() == ["done"]
    assert project.workflow()["batch"]["completed_prds"] == [PRD]


def test_complete_refuses_before_accepted_review(tmp_path):
    project = make_project(tmp_path, phase="review", completed_phases=("build",))

    with pytest.raises(files.PreconditionError):
        run_kind(project, "complete")

    assert project.where() == ["wip"]
    assert project.workflow()["recovery"] is None
