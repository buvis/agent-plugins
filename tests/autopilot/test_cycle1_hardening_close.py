"""Cycle-1 hardening: review-close binds rows to linked findings and validates carry snapshots."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from test_review_close_helpers import (
    DROP,
    assert_ok,
    assert_refused,
    load_sibling,
    row,
    run,
    scenario,
    valid_batch,
)
from test_review_close_helpers_gates import carry_batch, carry_task, snapshot


@pytest.fixture
def rc():
    return load_sibling("review_close")


# --- 3. the row's issue is bound to the review table ------------------------------------------


def relabel(case: dict[str, Any], chosen: list[dict[str, Any]], ref: str, title: str) -> None:
    """Make chosen row `ref` and its linked findings agree on `title`, leaving
    the review file's consolidated table untouched."""
    index = {"R1": 0, "R2": 1}[ref]
    ids = {"R1": ("F1", "F2"), "R2": ("F3", "F4")}[ref]
    chosen[index]["issue"] = title
    for finding in case["evidence"]["findings"]:
        if finding["finding_id"] in ids:
            finding["title"] = title


@pytest.mark.parametrize(
    "title", ["Wrong defaults", "Right default", "Wrong default and more"]
)
def test_review_close_refuses_a_row_whose_issue_differs_from_the_table_row(rc, title):
    case, chosen = valid_batch()
    relabel(case, chosen, "R1", title)
    report = run(rc, case, chosen)
    assert_refused(report, "findings_mismatch")
    assert report["task_proposals"] == [] and report["decision_proposals"] == []


def test_review_close_refuses_a_differing_issue_on_a_deferred_row_too(rc):
    case, chosen = valid_batch()
    relabel(case, chosen, "R2", "Slow loops")
    assert_refused(run(rc, case, chosen), "findings_mismatch")


@pytest.mark.parametrize("title", ["WRONG DEFAULT", "wrong default", "Wrong Default"])
def test_review_close_accepts_an_issue_that_differs_only_by_case_normalization(
    rc, title
):
    case, chosen = valid_batch()
    relabel(case, chosen, "R1", title)
    report = run(rc, case, chosen)
    assert_ok(report)
    assert len(report["task_proposals"]) == 1


def test_review_close_accepts_the_untouched_valid_batch(rc):
    case, chosen = valid_batch()
    assert_ok(run(rc, case, chosen))


# --- 4. carry snapshots are validated before they can prove an unfinished task ------------------

FIELDS = ["id", "name", "carry_refs", "carry_cycle", "escalation_reason", "status"]
WRONG_TYPE = [
    ("status", None),
    ("status", 3),
    ("status", ["pending"]),
    ("id", 7),
    ("name", 5),
    ("name", None),
    ("escalation_reason", 1),
    ("escalation_reason", None),
    ("carry_cycle", "2"),
    ("carry_cycle", None),
    ("carry_refs", None),
]


def invalid_input(rc, snap: dict[str, Any]) -> None:
    case, chosen = carry_batch()
    before = copy.deepcopy(snap)
    report = run(rc, case, chosen, read_snapshot=snap)
    assert snap == before
    assert_refused(report, "invalid-input")


def broken_task(field: str, value: Any = DROP) -> dict[str, Any]:
    task = carry_task()
    if value is DROP:
        del task[field]
    else:
        task[field] = value
    return task


@pytest.mark.parametrize("field", FIELDS)
def test_carry_snapshot_task_missing_a_required_field_is_invalid_input(rc, field):
    invalid_input(rc, snapshot(tasks=[broken_task(field)]))


@pytest.mark.parametrize(("field", "value"), WRONG_TYPE)
def test_carry_snapshot_task_with_a_wrongly_typed_field_is_invalid_input(
    rc, field, value
):
    invalid_input(rc, snapshot(tasks=[broken_task(field, value)]))


def test_carry_snapshot_without_status_does_not_prove_an_unfinished_task(rc):
    case, chosen = carry_batch()
    snap = snapshot(tasks=[broken_task("status")])
    report = run(rc, case, chosen, read_snapshot=snap)
    assert_refused(report)
    assert report["task_proposals"] == []


def test_carry_snapshot_with_one_malformed_task_among_valid_ones_is_invalid_input(rc):
    other = carry_task(id="T8", carry_refs=["R9"])
    invalid_input(rc, snapshot(tasks=[carry_task(), {**other, "status": None}],
                               rework_task_ids=["T7", "T8"]))
    invalid_input(rc, snapshot(tasks=[other, broken_task("status")],
                               rework_task_ids=["T7", "T8"]))


def test_complete_snapshot_for_an_unfinished_task_still_backs_a_carry_row(rc):
    case, chosen = carry_batch()
    for status in ("pending", "in_progress"):
        snap = snapshot(tasks=[carry_task(status=status)])
        report = run(rc, case, chosen, read_snapshot=snap)
        assert_ok(report)
        assert [t["name"] for t in report["task_proposals"]] == ["[D2] src/a.py"]


def test_snapshot_with_a_completed_task_still_does_not_back_a_carry_row(rc):
    case, chosen = carry_batch()
    snap = snapshot(tasks=[carry_task(status="completed")])
    assert_refused(run(rc, case, chosen, read_snapshot=snap), "carry_unmatched")
    deferred = [row("R1", "fix"), row("R2", "defer"), row("R3", "defer")]
    assert_ok(run(rc, scenario(["R1", "R2", "R3"]), deferred))
