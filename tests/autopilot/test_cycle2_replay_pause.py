"""Rework 17, review cycle 2: contract rules C5, C6 (PRD 00019).

C5 a stale revision conflicts before any saga stages anything, and only a saga
whose own operation is already in the durable deferred ledger may replay.
C6 the second consecutive park commits its pause together with the cleared
recovery marker, and that pause is terminal.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from controller_cli_support import private_path
from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import files, lifecycle
from autopilot_state.protocol import ProtocolError

from test_controller_lifecycle import (
    bucket_of, make_root, make_store, prd_text, rejected, request, run, work,
)

PRD = "00042-sample.md"
OTHER = "00043-other.md"
SPARE = "00001-a.md"
BUCKETS = ("backlog", "wip", "hold", "done")
DEFER = {"prd": PRD, "record": {"type": "deferred_decision", "summary": "later"}}
PARK = {"prd": PRD, "site": "wrapper_died", "detail": "session ended"}


def state_of(root: Path) -> dict:
    return json.loads((private_path(root) / "state.json").read_bytes())


# -- C5.1 a stale saga request conflicts before it stages anything -----------


def test_a_stale_enter_conflicts_without_moving_the_prd_into_wip(tmp_path):
    root = make_root(tmp_path, backlog={PRD: prd_text()})
    store = make_store(root)
    stale = request(store, "prd.enter", {"prds": [PRD]}, "req-stale")
    store.transaction(lambda state: None)
    before = store.read()

    with pytest.raises(ProtocolError) as caught:
        lifecycle.enter(store, stale, before)

    assert caught.value.code == "revision_conflict"
    assert bucket_of(root, PRD) == ["backlog"]
    assert store.read() == before
    fresh = request(store, "prd.enter", {"prds": [PRD]}, "req-fresh")
    response = lifecycle.enter(store, fresh, store.read())
    assert response["ok"] and bucket_of(root, PRD) == ["wip"]


def test_a_stale_handoff_conflicts_without_advancing_the_phase(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    payload = {"phase": "build", "next_phase": "review", "outcome": "tasks_done"}
    stale = request(store, "phase.handoff", payload, "req-stale")
    store.transaction(lambda state: None)
    before = store.read()

    with pytest.raises(ProtocolError) as caught:
        lifecycle.handoff(store, stale, before)

    assert caught.value.code == "revision_conflict"
    assert store.read() == before
    assert before["workflow"]["work"]["phase"] == "build"
    response = run(lifecycle.handoff, store, "phase.handoff", payload)
    assert response["result"] == {"phase": "review", "next_phase": "review"}


# -- C5.2 and C5.3 through the public dispatcher -----------------------------


class StaleSagaDispatchTest(OwnerCLITest):
    """protocol.apply admits a proven replay and refuses every other stale request."""

    def setUp(self) -> None:
        super().setUp()
        for bucket in BUCKETS:
            (self.root / files.PRD_ROOT / bucket).mkdir(parents=True)
        (self.root / files.PRD_ROOT / "backlog" / PRD).write_text("---\n---\n# PRD\n")
        _, _, self.operator = self.bootstrap()
        self.call("prd.enter", {"prds": [PRD]})

    def call(self, name: str, payload: dict) -> tuple[dict, dict]:
        value = self.request(self.operator, name, f"{name}-{self.serial}", payload)
        return value, self.response(self.apply(value, self.operator))

    def where(self, prd: str = PRD) -> list[str]:
        return [name for name in BUCKETS
                if (self.root / files.PRD_ROOT / name / prd).exists()]

    def ledger(self) -> list[dict]:
        name = f"{self.state()['workflow_id']}-deferred.json"
        path = private_path(self.root) / "deferred" / name
        return json.loads(path.read_text())["items"] if path.exists() else []

    def test_a_stale_park_conflicts_without_running_its_saga(self) -> None:
        stale = self.request(self.operator, "prd.park", "park-stale", PARK)
        _, deferred = self.call("prd.defer", DEFER)

        self.reject_unchanged(stale, self.operator, "revision_conflict")

        self.assertEqual(self.where(), ["wip"])
        self.assertEqual([item["op_id"] for item in self.ledger()],
                         [deferred["result"]["operation_id"]])
        _, parked = self.call("prd.park", PARK)
        self.assertEqual(parked["result"]["kind"], "park")
        self.assertEqual(self.where(), ["hold"])
        self.assertEqual([item["op_id"] for item in self.ledger()],
                         [deferred["result"]["operation_id"], parked["result"]["operation_id"]])

    def replay(self, name: str, payload: dict) -> dict:
        """Commit a saga, lose its receipt, re-apply the very same stale request."""
        value, committed = self.call(name, payload)
        operation_id = committed["result"]["operation_id"]
        self.assertEqual(operation_id, value["request_id"])
        self.assertEqual([item["op_id"] for item in self.ledger()], [operation_id])
        state = self.state()
        del state["receipts"][value["request_id"]]
        self.seed(state)

        replayed = self.response(self.apply(value, self.operator))

        self.assertTrue(replayed["ok"])
        self.assertIs(replayed["result"]["replayed"], True)
        self.assertEqual([item["op_id"] for item in self.ledger()], [operation_id])
        self.assertIn(value["request_id"], self.state()["receipts"])
        return value

    def test_a_ledger_recorded_saga_replays_while_an_unrecorded_stale_request_conflicts(
            self) -> None:
        value = self.replay("prd.defer", DEFER)

        unrecorded = dict(value, request_id="defer-unrecorded")
        self.reject_unchanged(unrecorded, self.operator, "revision_conflict")

    def test_a_ledger_recorded_park_replays_through_the_dispatcher_like_any_other_saga(
            self) -> None:
        self.replay("prd.park", PARK)

        self.assertEqual(self.where(), ["hold"])


# -- C6 the systemic-park pause ----------------------------------------------


def paused(base: Path) -> tuple[Path, object]:
    """Drive a real workflow to its second consecutive park; return root and store."""
    root = make_root(base, wip={PRD: prd_text(), OTHER: prd_text()},
                     backlog={SPARE: prd_text()})
    store = make_store(root, work=work(PRD))
    files.park(store, project_root=root, prd=PRD)
    store.transaction(lambda state: state["workflow"].update(work=work(OTHER)))
    result = files.park(store, project_root=root, prd=OTHER)
    assert result.systemic_halt is True
    return root, store


def test_the_second_park_commits_the_pause_with_the_recovery_marker_it_clears(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_text(), OTHER: prd_text()})
    store = make_store(root, work=work(PRD))
    first = files.park(store, project_root=root, prd=PRD)
    assert first.systemic_halt is False
    assert not state_of(root)["workflow"].get("pause")
    store.transaction(lambda state: state["workflow"].update(work=work(OTHER)))
    seen: list[tuple[object, dict]] = []

    second = files.park(store, project_root=root, prd=OTHER, boundary_hook=(
        lambda boundary: seen.append((boundary, state_of(root)["workflow"]))))

    assert second.systemic_halt is True
    workflow = state_of(root)["workflow"]
    pause = workflow.get("pause")
    assert pause is not None and set(pause) == {"site", "detail"}
    assert pause["site"] == "systemic_park"
    assert isinstance(pause["detail"], str) and pause["detail"]
    assert workflow["recovery"] is None
    marked = [index for index, (_, flow) in enumerate(seen) if flow["recovery"] is not None]
    assert marked, "control: the park saga recorded a recovery marker"
    for boundary, flow in seen[marked[0]:]:
        if flow["recovery"] is None:
            assert flow.get("pause") == pause, f"marker cleared without the pause: {boundary}"


class FailingStore:
    """A real store whose nth transaction fails, the way a crash would."""

    def __init__(self, store, fail_on: int) -> None:
        self._store = store
        self._fail_on = fail_on
        self.transactions = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self._store, name)

    def transaction(self, *args, **kwargs):
        self.transactions += 1
        if self.transactions == self._fail_on:
            raise RuntimeError(f"injected crash at transaction {self._fail_on}")
        return self._store.transaction(*args, **kwargs)


def park_twice(base: Path, fail_on: int) -> tuple[Path, bool]:
    """Park two PRDs; the second park's nth transaction fails. Report the root."""
    root = make_root(base, wip={PRD: prd_text(), OTHER: prd_text()})
    store = make_store(root, work=work(PRD))
    files.park(store, project_root=root, prd=PRD)
    store.transaction(lambda state: state["workflow"].update(work=work(OTHER)))
    try:
        files.park(FailingStore(store, fail_on), project_root=root, prd=OTHER)
    except (RuntimeError, ProtocolError):  # the injected crash, or the saga's own refusal
        return root, True
    return root, False


def test_a_crash_while_the_second_park_commits_never_loses_the_systemic_pause(tmp_path):
    interrupted, paused_runs = 0, 0

    for fail_on in range(7):
        root, raised = park_twice(tmp_path / f"crash-{fail_on}", fail_on)
        workflow = state_of(root)["workflow"]
        if workflow["recovery"] is None and bucket_of(root, OTHER) == ["hold"]:
            assert workflow.get("pause"), f"marker cleared without the pause: {fail_on}"
        interrupted += int(raised)
        paused_runs += int(not raised and bool(workflow.get("pause")))

    assert interrupted, "control: an injected failure interrupted the park saga"
    assert paused_runs, "control: an uninterrupted second park records the pause"


def test_prd_enter_keeps_rejecting_while_the_pause_is_set(tmp_path):
    root, store = paused(tmp_path / "paused")

    rejected(lifecycle.enter, store, "prd.enter", {"prds": [SPARE]})

    assert bucket_of(root, SPARE) == ["backlog"]
    assert state_of(root)["workflow"]["pause"]["site"] == "systemic_park"
    control_root = make_root(tmp_path / "control", backlog={SPARE: prd_text()})
    control = make_store(control_root)
    response = run(lifecycle.enter, control, "prd.enter", {"prds": [SPARE]})
    assert response["ok"] and bucket_of(control_root, SPARE) == ["wip"]


def test_resume_target_reports_operator_reconciliation_only_while_the_pause_is_set(tmp_path):
    _, store = paused(tmp_path / "paused")
    state = store.read()
    without_pause = copy.deepcopy(state)
    without_pause["workflow"].pop("pause", None)

    target = lifecycle.resume_target(state)

    assert isinstance(target, str)
    assert "reconcil" in target.lower()
    assert "systemic_park" in target, "the operator learns which pause site to reconcile"
    assert OTHER in target, "the operator learns which PRD the batch parked on"
    assert target != lifecycle.resume_target(without_pause)
