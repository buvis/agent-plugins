"""Rework 17, review cycle 2: contract rules C1, C2, C3 (PRD 00019).

C1 prd.enter captures real entry metadata from the PRD in its final location.
C2 build -> review needs every task row finished.
C3 task.finish needs durable start evidence for the lease epoch that finishes it.

Each test states the rule it enforces and must fail against the current tree.
"""

from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest
from controller_test_support import commit_all

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import files, lifecycle, policy, schema, tasks
from autopilot_state.protocol import ProtocolError

from test_controller_lifecycle import (
    bucket_of, make_root, make_store, prd_text, rejected, run, work,
)

PRD = "00002-b.md"
TASKS_DONE = {"phase": "build", "next_phase": "review", "outcome": "tasks_done"}


def prd_with(tier: str | None = None, expansion: str | None = None,
             cap: int | None = None) -> str:
    """A PRD whose frontmatter declares only the metadata under test."""
    declared = ""
    if tier is not None:
        declared += f"default_model: {tier}\n"
    if expansion is not None:
        declared += f"plan_expansion: {expansion}\n"
    if cap is not None:
        declared += f"rework_cap: {cap}\n"
    return f"---\n{declared}---\n# PRD\n"


def prd_path(root: Path, bucket: str, prd: str = PRD) -> Path:
    return root / files.PRD_ROOT / bucket / prd


def task_row(task_id: str, status: str) -> dict:
    return {"id": task_id, "subject": f"subject {task_id}", "status": status,
            "depends_on": [], "attempts": []}


def with_tasks(store, rows: list[dict]) -> None:
    def seed(state: dict) -> None:
        state["workflow"]["tasks"] = copy.deepcopy(rows)

    store.transaction(seed)


def payload_rows(*statuses: str) -> list[dict]:
    return [{"id": f"t{index}", "subject": f"subject t{index}", "status": status,
             "depends_on": []} for index, status in enumerate(statuses, start=1)]


# -- C1.1 entry metadata: HEAD commit, declared tier, declared plan expansion --


@pytest.mark.parametrize("tier,expansion", [("opus", "allow"), ("sonnet", "deny")])
def test_enter_captures_the_head_commit_the_declared_tier_and_plan_expansion(
        tmp_path, monkeypatch, tier, expansion):
    root = make_root(tmp_path, backlog={PRD: prd_with(tier, expansion)})
    head = commit_all(root, monkeypatch)
    assert len(head) == 40, "control: git answered with a commit id"
    store = make_store(root)

    response = run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    assert response["ok"] and response["result"] == {"prd": PRD, "source": "backlog"}
    committed = store.read()["workflow"]["work"]
    assert committed["start_commit"] == head
    assert committed["task_tier"] == tier
    assert committed["plan_expansion"] == expansion
    assert committed["rework_cap"] == 2


def test_enter_captures_the_rework_cap_the_prd_declares_instead_of_the_default(tmp_path):
    root = make_root(tmp_path, backlog={PRD: prd_with("opus", "allow", cap=5)})
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    committed = store.read()["workflow"]["work"]
    assert committed["rework_cap"] == 5
    assert (committed["task_tier"], committed["plan_expansion"]) == ("opus", "allow")


def test_enter_ignores_a_tier_or_plan_expansion_declared_only_in_the_prd_body(tmp_path):
    body = "---\nrework_cap: 3\n---\n# PRD\ndefault_model: opus\nplan_expansion: allow\n"
    root = make_root(tmp_path, backlog={PRD: body})
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    committed = store.read()["workflow"]["work"]
    assert committed["task_tier"] is None
    assert committed["plan_expansion"] is None
    assert committed["rework_cap"] == 3


def test_enter_captures_the_head_commit_of_a_repository_whose_refs_are_packed(
        tmp_path, monkeypatch):
    root = make_root(tmp_path, backlog={PRD: prd_with("opus", "allow")})
    head = commit_all(root, monkeypatch)
    subprocess.run(["git", "pack-refs", "--all"], cwd=root, check=True, capture_output=True)
    loose = root / ".git" / "refs" / "heads"
    assert not loose.exists() or not any(loose.rglob("*")), "control: the ref is packed"
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    committed = store.read()["workflow"]["work"]
    assert committed["start_commit"] == head
    assert len(head) == 40


def test_enter_records_a_null_start_commit_when_the_project_is_not_a_repository(tmp_path):
    root = make_root(tmp_path, backlog={PRD: prd_with("opus", "allow")})
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    committed = store.read()["workflow"]["work"]
    assert committed["start_commit"] is None
    assert (committed["task_tier"], committed["plan_expansion"]) == ("opus", "allow")


def test_enter_records_a_null_tier_and_plan_expansion_when_the_prd_declares_none(
        tmp_path, monkeypatch):
    root = make_root(tmp_path, backlog={PRD: prd_text()})
    head = commit_all(root, monkeypatch)
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    committed = store.read()["workflow"]["work"]
    assert committed["task_tier"] is None
    assert committed["plan_expansion"] is None
    assert committed["start_commit"] == head


# -- C1.2 the metadata belongs to the file in its final location --------------


def test_enter_captures_the_metadata_of_the_prd_bytes_that_landed_in_wip(tmp_path, monkeypatch):
    root = make_root(tmp_path, backlog={PRD: prd_with("sonnet", "deny")})
    head = commit_all(root, monkeypatch)
    store = make_store(root)

    run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    assert bucket_of(root, PRD) == ["wip"]
    assert not prd_path(root, "backlog").exists()
    moved = prd_path(root, "wip").read_text()
    assert "default_model: sonnet" in moved and "plan_expansion: deny" in moved
    committed = store.read()["workflow"]["work"]
    assert (committed["task_tier"], committed["plan_expansion"]) == ("sonnet", "deny")
    assert committed["start_commit"] == head


# -- C1.3 an unreadable or undecodable PRD is rejected, never defaulted -------


@pytest.mark.parametrize("bucket", ["wip", "backlog"])
def test_enter_rejects_a_prd_whose_bytes_cannot_be_decoded(tmp_path, bucket):
    root = make_root(tmp_path / f"broken-{bucket}")
    prd_path(root, bucket).write_bytes(b"---\ndefault_model: \xff\xfe\n---\n# PRD\n")
    store = make_store(root)

    rejected(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    assert store.read()["workflow"]["work"] is None
    assert bucket_of(root, PRD) == [bucket]
    readable = make_root(tmp_path / f"readable-{bucket}", wip={PRD: prd_with("opus")})
    control = make_store(readable)
    response = run(lifecycle.enter, control, "prd.enter", {"prds": [PRD]})
    assert response["ok"] and control.read()["workflow"]["work"]["task_tier"] == "opus"


def test_enter_rejects_a_prd_it_cannot_read_and_enters_it_once_readable(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_with("opus", "allow")})
    locked = prd_path(root, "wip")
    locked.chmod(0o000)
    store = make_store(root)

    rejected(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})

    assert store.read()["workflow"]["work"] is None
    locked.chmod(0o600)
    response = run(lifecycle.enter, store, "prd.enter", {"prds": [PRD]})
    assert response["ok"]
    committed = store.read()["workflow"]["work"]
    assert (committed["prd"], committed["task_tier"]) == (PRD, "opus")


# -- C1.4 the three metadata keys are optional on a stored work record --------


def test_state_validates_with_and_without_the_new_work_metadata_keys(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    legacy = store.read()

    assert schema.validate_state(copy.deepcopy(legacy)) == legacy

    for metadata in ({"start_commit": "a" * 40, "task_tier": "opus",
                      "plan_expansion": "allow"},
                     {"start_commit": None, "task_tier": None, "plan_expansion": None}):
        upgraded = copy.deepcopy(legacy)
        upgraded["workflow"]["work"].update(metadata)
        assert schema.validate_state(copy.deepcopy(upgraded)) == upgraded


@pytest.mark.parametrize("metadata", [{"start_commit": 12345}, {"start_commit": "a" * 39},
                                      {"start_commit": "a" * 41}, {"start_commit": "A" * 40},
                                      {"start_commit": "z" * 40}, {"task_tier": 7},
                                      {"task_tier": ""}, {"plan_expansion": []},
                                      {"plan_expansion": ""}])
def test_state_rejects_a_malformed_start_commit_tier_or_plan_expansion(tmp_path, metadata):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    broken = store.read()
    broken["workflow"]["work"].update(metadata)

    with pytest.raises(schema.SchemaError):
        schema.validate_state(broken)


# -- C2 build -> review requires every task row to be finished ---------------


@pytest.mark.parametrize("statuses", [("pending", "completed"), ("completed", "in_progress"),
                                      ("aborted", "pending"), ("in_progress", "in_progress"),
                                      ("completed", "completed", "pending"),
                                      ("completed", "aborted", "completed", "in_progress")])
def test_handoff_to_review_is_rejected_while_any_task_row_is_unfinished(tmp_path, statuses):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    with_tasks(store, [task_row(f"t{index}", status)
                       for index, status in enumerate(statuses, start=1)])

    rejected(lifecycle.handoff, store, "phase.handoff", TASKS_DONE)

    assert store.read()["workflow"]["work"]["phase"] == "build"


@pytest.mark.parametrize("statuses", [(), ("completed", "aborted"), ("aborted",),
                                      ("completed", "completed", "aborted")])
def test_handoff_to_review_is_accepted_when_no_task_row_is_unfinished(tmp_path, statuses):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    with_tasks(store, [task_row(f"t{index}", status)
                       for index, status in enumerate(statuses, start=1)])

    response = run(lifecycle.handoff, store, "phase.handoff", TASKS_DONE)

    assert response["result"] == {"phase": "review", "next_phase": "review"}
    assert store.read()["workflow"]["work"]["phase"] == "review"


# -- C3 task.finish needs durable start evidence -----------------------------


@pytest.mark.parametrize("lease_epoch", [0, 1, 7])
def test_finish_is_rejected_when_a_lease_epoch_finishes_a_task_that_never_started(lease_epoch):
    plan = tasks.replace(payload_rows("in_progress", "in_progress"))
    before = copy.deepcopy(plan)

    for task_id in ("t1", "t2"):
        with pytest.raises(ProtocolError) as caught:
            tasks.finish(plan, task_id, "completed", lease_epoch)
        assert caught.value.code == "rejected_evidence"

    assert plan == before


@pytest.mark.parametrize("lease_epoch", [0, 1, 7])
def test_finish_closes_a_task_started_under_the_same_lease_epoch(lease_epoch):
    plan = tasks.replace(payload_rows("pending", "pending"))

    started = tasks.start(plan, "t1", lease_epoch)
    finished = tasks.finish(started, "t1", "completed", lease_epoch)

    assert started[0]["start_epoch"] == lease_epoch
    assert [(row["id"], row["status"]) for row in finished] == [("t1", "completed"),
                                                               ("t2", "pending")]
    with pytest.raises(ProtocolError) as caught:
        tasks.finish(started, "t1", "aborted", lease_epoch + 1)
    assert caught.value.code == "rejected_evidence"


def test_finish_without_a_lease_epoch_still_closes_a_task_that_has_no_start_epoch():
    plan = tasks.replace(payload_rows("in_progress", "in_progress"))

    finished = tasks.finish(plan, "t2", "aborted")

    assert [(row["id"], row["status"]) for row in finished] == [("t1", "in_progress"),
                                                               ("t2", "aborted")]
    assert "start_epoch" not in finished[1]


def test_replace_rejects_an_item_that_forges_start_evidence():
    item = {"id": "t1", "subject": "subject t1", "status": "pending", "depends_on": []}

    with pytest.raises(policy.InvalidPlan):
        tasks.replace([{**item, "start_epoch": 7}])

    assert tasks.replace([item]) == [{**item, "attempts": []}]
