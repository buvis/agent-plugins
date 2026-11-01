"""Packaged review close enforces single-voice, carry and tail-sweep gates from caller snapshots."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from test_review_close_helpers import (
    DROP,
    EMOJI,
    REVIEW_REF,
    assert_ok,
    assert_refused,
    load_sibling,
    proposals_with,
    row,
    run,
    scenario,
)


@pytest.fixture
def rc():
    return load_sibling("review_close")


# --- caller snapshots -----------------------------------------------------------------------------


def carry_task(**over: Any) -> dict[str, Any]:
    task = {
        "id": "T7",
        "name": "Fix typo",
        "carry_refs": ["R3"],
        "carry_cycle": 2,
        "escalation_reason": "review_flag",
        "status": "pending",
    }
    task.update(over)
    return task


def snapshot(**over: Any) -> dict[str, Any]:
    snap = {
        "cycle": 2,
        "tasks": [carry_task()],
        "rework_task_ids": ["T7"],
        "decision_gate_review_ref": REVIEW_REF,
        "deferred_decisions": [],
    }
    snap.update(over)
    return snap


def carry_batch() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case = scenario(["R1", "R2", "R3"])
    return case, [
        row("R1", "fix"),
        row("R2", "defer"),
        row("R3", "carry", reason="re-queued as T7"),
    ]


def assert_controller_required(report: Any) -> None:
    assert isinstance(report, dict), report
    assert (
        report["ok"] is False
        and report["schema_version"] == 1
        and type(report["schema_version"]) is int
    )
    assert (
        report["error"] == "controller-required"
        and report["operation"] == "prepare-close"
    )
    assert not report.get("task_proposals")


def deferral(**over: Any) -> dict[str, Any]:
    entry = {
        "cycle": 1,
        "issue": "earlier",
        "severity": "medium",
        "file": "src/b.py",
        "action": "deferred",
        "reason": "r",
    }
    entry.update(over)
    return entry


# --- decision-gate single voice ---------------------------------------------------------------


@pytest.mark.parametrize(
    "found_by", [["bob"], ["bob", "bob"], DROP], ids=["one", "duplicated", "missing"]
)
def test_decision_gate_low_fix_from_one_reviewer_is_single_voice(rc, found_by):
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix"), row("R2", "defer"), row("R3", "fix", found_by=found_by)]
    assert_refused(run(rc, case, chosen), "single_voice_fix")


def test_decision_gate_single_voice_applies_only_to_medium_or_low_fix_rows(rc):
    groups = load_sibling("rework_groups")
    case = scenario(["R2", "R3", "R5"])
    chosen = [row("R2", "fix"), row("R3", "defer"), row("R5", "fix")]
    report = run(rc, case, chosen)
    assert_ok(report)
    expected = [f"[D2] {g['name_hint']}" for g in groups.group([chosen[0], chosen[2]])]
    assert [t["name"] for t in report["task_proposals"]] == expected
    medium_single = scenario(["R2"])
    f4 = next(
        f for f in medium_single["evidence"]["findings"] if f["finding_id"] == "F4"
    )
    f4["result_id"] = "alice-1"
    for result in medium_single["evidence"]["reviewer_results"]:
        if result["job_ref"] == "alice":
            result["finding_ids"] = ["F3", "F4"]
        if result["job_ref"] == "bob":
            result["outcome"], result["finding_ids"] = "clean", []
    assert_refused(
        run(rc, medium_single, [row("R2", "fix", found_by=["alice"])]),
        "single_voice_fix",
    )
    assert_ok(run(rc, medium_single, [row("R2", "defer", found_by=["alice"])]))


def test_caller_label_cannot_invent_a_second_finder(rc):
    case = scenario(["R1", "R2", "R3"])
    chosen = [
        row("R1", "fix"),
        row("R2", "defer"),
        row("R3", "fix", found_by=["bob", "carl"]),
    ]
    assert_refused(run(rc, case, chosen))


# --- carry ----------------------------------------------------------------------------------------


def test_carry_row_without_a_snapshot_requires_the_controller(rc):
    case, chosen = carry_batch()
    assert_controller_required(run(rc, case, chosen))
    assert_controller_required(run(rc, case, chosen, read_snapshot=None))


@pytest.mark.parametrize(
    "snap",
    [
        snapshot(),
        snapshot(tasks=[carry_task(carry_refs=["r3"])]),
        snapshot(
            tasks=[
                carry_task(id="T1", status="completed"),
                carry_task(escalation_reason="fable_rescue"),
            ],
            rework_task_ids=["T1", "T7"],
        ),
        snapshot(tasks=[carry_task(carry_refs=["R1", "R3"])]),
    ],
    ids=["exact", "lowercase-ref", "second-task-matches", "second-carry-ref"],
)
def test_carry_row_backed_by_an_unfinished_requeued_task_is_proposed_without_a_task(
    rc, snap
):
    case, chosen = carry_batch()
    before = copy.deepcopy(snap)
    report = run(rc, case, chosen, read_snapshot=snap)
    assert_ok(report)
    assert [t["name"] for t in report["task_proposals"]] == ["[D2] src/a.py"]
    [carry] = proposals_with(report, "classification", "carry")
    assert carry["reason"] == "re-queued as T7"
    assert snap == before


@pytest.mark.parametrize(
    "snap",
    [
        snapshot(tasks=[carry_task(status="completed")]),
        snapshot(tasks=[carry_task(carry_cycle=1)]),
        snapshot(rework_task_ids=["T70"]),
        snapshot(tasks=[carry_task(escalation_reason="manual")]),
        snapshot(tasks=[carry_task(carry_refs=["R33"])]),
        snapshot(
            tasks=[carry_task(id="T1"), carry_task(carry_cycle=1)],
            rework_task_ids=["T7"],
        ),
        snapshot(tasks=[]),
    ],
    ids=[
        "completed",
        "old-cycle",
        "not-requeued",
        "other-escalation",
        "near-miss-ref",
        "split",
        "no-tasks",
    ],
)
def test_carry_row_without_one_task_meeting_every_condition_is_unmatched(rc, snap):
    case, chosen = carry_batch()
    assert_refused(run(rc, case, chosen, read_snapshot=snap), "carry_unmatched")


def test_snapshot_from_another_cycle_is_refused(rc):
    case, chosen = carry_batch()
    assert_ok(run(rc, case, chosen, cycle=2, read_snapshot=snapshot()))
    assert_refused(run(rc, case, chosen, cycle=3, read_snapshot=snapshot()))
    sweep = [row("R2", "fix"), row("R4", "defer")]
    for cycle, snap_cycle in ((2, 3), (3, 2)):
        snap = snapshot(cycle=snap_cycle, tasks=[], rework_task_ids=[])
        assert_refused(tail(rc, ["R2", "R4"], sweep, cycle=cycle, read_snapshot=snap))


@pytest.mark.parametrize(
    "snap",
    [
        [],
        "snapshot",
        snapshot(tasks="T7"),
        snapshot(rework_task_ids="T7"),
        {k: v for k, v in snapshot().items() if k != "cycle"},
    ],
    ids=["list", "string", "tasks-string", "rework-string", "no-cycle"],
)
def test_malformed_supplied_snapshot_is_invalid_input(rc, snap):
    case, chosen = carry_batch()
    report = run(rc, case, chosen, read_snapshot=snap)
    assert_refused(report)
    assert report["error"] == "invalid-input"


# --- tail sweep -----------------------------------------------------------------------------------


def tail(
    rc, refs: list[str], chosen: list[dict[str, Any]], **over: Any
) -> dict[str, Any]:
    over.setdefault("read_snapshot", snapshot(tasks=[], rework_task_ids=[]))
    return run(rc, scenario(refs), chosen, batch_id="tail-sweep", **over)


@pytest.mark.parametrize("cycle,tier", [(2, "sonnet"), (3, "opus")])
def test_tail_sweep_prefixes_task_names_and_keeps_cycle_and_tier(rc, cycle, tier):
    snap = snapshot(cycle=cycle, tasks=[], rework_task_ids=[])
    report = tail(
        rc,
        ["R2", "R4"],
        [row("R2", "fix"), row("R4", "defer")],
        cycle=cycle,
        default_tier=tier,
        read_snapshot=snap,
    )
    assert_ok(report)
    [task] = report["task_proposals"]
    assert (task["name"], task["model"]) == (f"[D{cycle}] Tail sweep: src/b.py", tier)
    [defer] = proposals_with(report, "action", "deferred")
    assert (defer["cycle"], defer["severity"], defer["file"]) == (
        cycle,
        EMOJI["medium"],
        "docs/guide.md",
    )


def test_tail_sweep_without_a_snapshot_requires_the_controller(rc):
    report = run(
        rc,
        scenario(["R2", "R4"]),
        [row("R2", "fix"), row("R4", "defer")],
        batch_id="tail-sweep",
    )
    assert_controller_required(report)


def test_tail_sweep_refuses_a_carry_row_before_the_missing_receipt(rc):
    chosen = [row("R2", "fix"), row("R4", "carry")]
    snap = snapshot(decision_gate_review_ref=None, tasks=[], rework_task_ids=[])
    assert_refused(
        tail(rc, ["R2", "R4"], chosen, read_snapshot=snap), "carry_in_tail_sweep"
    )


@pytest.mark.parametrize(
    "receipt", [None, REVIEW_REF + ".old", "docs/dev/tmp/review/review-file"]
)
def test_tail_sweep_needs_this_reviews_decision_gate_receipt_before_any_row_check(
    rc, receipt
):
    snap = snapshot(decision_gate_review_ref=receipt, tasks=[], rework_task_ids=[])
    chosen = [row("R1", "fix"), row("R2", "fix")]
    assert_refused(
        tail(rc, ["R1", "R2"], chosen, read_snapshot=snap),
        "tail_sweep_before_decision_gate",
    )
    assert_refused(
        tail(rc, [], [], read_snapshot=snap), "tail_sweep_before_decision_gate"
    )


def test_empty_tail_sweep_is_refused(rc):
    assert_refused(tail(rc, [], []), "tail_sweep_empty")


@pytest.mark.parametrize(
    "chosen",
    [
        [row("R1", "fix"), row("R2", "fix"), row("R3", "defer")],
        [row("R2", "fix"), row("R1", "defer"), row("R3", "defer")],
    ],
    ids=["high-fix", "high-defer"],
)
def test_tail_sweep_refuses_rows_above_medium_before_single_voice_and_deferrals(
    rc, chosen
):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral()])
    assert_refused(
        tail(rc, ["R1", "R2", "R3"], chosen, read_snapshot=snap),
        "tail_sweep_above_medium",
    )


@pytest.mark.parametrize(
    "chosen",
    [
        [row("R2", "fix"), row("R3", "defer")],
        [row("R2", "defer"), row("R3", "fix")],
    ],
    ids=["single-voice-defer", "single-voice-fix"],
)
def test_tail_sweep_refuses_a_single_voice_row_before_deferrals(rc, chosen):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral()])
    assert_refused(
        tail(rc, ["R2", "R3"], chosen, read_snapshot=snap), "tail_sweep_single_voice"
    )


@pytest.mark.parametrize(
    "over,duplicate",
    [
        ({"severity": "medium", "file": " src/b.py "}, True),
        ({"severity": EMOJI["medium"], "file": "src/b.py"}, True),
        ({"severity": "medium", "file": "docs/guide.md"}, True),
        ({"severity": EMOJI["medium"], "file": "src/b.py.orig"}, False),
        ({"severity": "low", "file": "src/b.py"}, False),
    ],
    ids=["word-padded", "emoji", "second-row", "near-miss-file", "other-severity"],
)
def test_tail_sweep_refuses_a_row_duplicating_an_open_deferral(rc, over, duplicate):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral(**over)])
    report = tail(
        rc, ["R2", "R4"], [row("R2", "fix"), row("R4", "defer")], read_snapshot=snap
    )
    if duplicate:
        assert_refused(report, "tail_sweep_duplicates_deferral")
    else:
        assert_ok(report)
