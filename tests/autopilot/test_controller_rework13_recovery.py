"""Rework 13, review cycle 1: findings 9-12 (PRD 00019 protocol.py, files.py, tasks.py).

Each test proves one named finding from the rework task description; see the
task report for which findings are genuinely ambiguous.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pytest

from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors, files, lifecycle, protocol, schema
from autopilot_state.store import RevisionConflictError, StateStore

from test_controller_lifecycle import (
    PROJECT_ID, WORKFLOW_ID, bucket_of, make_root, make_store, prd_text, rejected, request, run,
    work,
)


def private_root(tmp_path) -> Path:
    """A project root with a real 0o700 `.autopilot/controller` layout."""
    root = make_root(tmp_path)
    with actors.PrivateLayout(root) as layout:
        layout.prepare()
    return root


def seeded_store(root: Path, *, active_work: dict | None) -> StateStore:
    store = StateStore(root / ".autopilot" / "controller" / "state.json")
    state = schema.new_state(repo_root=root, project_id=PROJECT_ID, workflow_id=WORKFLOW_ID)
    state["actors"] = {"operator-test": {
        "actor_id": "operator-test", "project_id": PROJECT_ID, "workflow_id": WORKFLOW_ID,
        "role": "operator", "lease_epoch": 0, "native_session_id": None,
        "secret_digest": "b" * 64}}
    state["workflow"]["batch"] = {"completed_prds": [], "parks_consecutive": 0}
    state["workflow"]["work"] = active_work
    store.initialize(state)
    return store


# -- finding 9: a crash between a saga's commit and its receipt must recover -


def test_apply_unlocked_recovers_the_original_result_after_a_crash_before_the_receipt(tmp_path):
    root = private_root(tmp_path)
    (root / "docs" / "dev" / "project-management" / "prds" / "wip" / "00002-b.md").write_text(
        prd_text())
    store = seeded_store(root, active_work=work("00002-b.md"))
    stall_request = request(store, "prd.stall",
                            {"prd": "00002-b.md", "site": "wrapper_died",
                             "detail": "crash before receipt"})
    with actors.PrivateLayout(root) as layout:
        current = store.read()
        committed = protocol.run_saga(stall_request, current, store)
        # The saga's own commits are durable (its last transaction advanced the
        # revision); nothing cached a receipt for this request, simulating a
        # crash right after that commit and before protocol.record_receipt ran.
        retried = protocol.apply_unlocked(stall_request, layout, store)
    assert retried["ok"] is True
    assert retried["result"] == committed


# -- finding 10: an admitted stall/park/defer must recheck revision/actor ---


def test_stall_does_not_recheck_revision_after_an_intervening_commit(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))

    def intervene(boundary) -> None:
        if boundary == files.SagaBoundary.AFTER_INTENT_BEFORE_MOVE:
            # Another admitted operation commits concurrently, between this
            # saga's own internal, separately lock-protected steps.
            store.transaction(lambda state: None)

    # AMBIGUITY: the PRD names no exception for this recheck; any of the
    # store's/files' existing conflict signals is accepted as "rejected".
    with pytest.raises((RevisionConflictError, files.RecoveryConflictError,
                        files.PreconditionError, files.RecoveryRequiredError)):
        files.stall(store, project_root=root, prd="00002-b.md", site="s", detail="d",
                    boundary_hook=intervene)
    assert bucket_of(root, "00002-b.md") == ["wip"]


# -- finding 11: a second consecutive park must persist a blocking pause ----


def test_second_consecutive_park_persists_a_pause_that_blocks_prd_enter(tmp_path):
    root = make_root(tmp_path, wip={"00002-b.md": prd_text()},
                     backlog={"00003-c.md": prd_text(), "00004-d.md": prd_text()})
    store = make_store(root, work=work("00002-b.md"))

    first = files.park(store, project_root=root, prd="00002-b.md", site="s1", detail="d1")
    assert first.systemic_halt is False

    entered = run(lifecycle.enter, store, "prd.enter", {"prds": ["00003-c.md"]})
    assert entered["ok"] and entered["result"]["prd"] == "00003-c.md"

    second = files.park(store, project_root=root, prd="00003-c.md", site="s2", detail="d2")
    assert second.systemic_halt is True

    # AMBIGUITY: the PRD names no field for this pause beyond its "site"; a
    # top-level `workflow.pause` object is assumed.
    paused = store.read()["workflow"].get("pause")
    assert paused is not None and paused.get("site") == "systemic_park"

    rejected(lifecycle.enter, store, "prd.enter", {"prds": ["00004-d.md"]})
    assert bucket_of(root, "00004-d.md") == ["backlog"]


# -- finding 12: task.finish must bind to the lease epoch it started in -----


class TaskFinishLeaseEpochTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        _, _, self.operator = self.bootstrap()

    def call(self, name: str, payload: dict) -> tuple[dict, dict]:
        request = self.request(self.operator, name, f"{name}-{self.state()['revision']}",
                               payload)
        response = self.response(self.apply(request, self.operator),
                                 revision=request["expected_revision"] + 1)
        return request, response

    def _advance_lease_epoch(self) -> None:
        """Acquire then release the owner lease, advancing lease_epoch by 2."""
        request = self.request(self.operator, "owner.acquire",
                               f"acquire-{self.state()['revision']}",
                               {"mode": "manual", "native_session_id": "session-epoch"})
        response = self.response(self.apply(request, self.operator),
                                 revision=request["expected_revision"] + 1)
        owner_file = Path(response["result"]["actor_file"])
        self.operator = Path(response["result"]["operator_actor_file"])
        request = self.request(owner_file, "owner.release",
                               f"release-{self.state()['revision']}", {})
        response = self.response(self.apply(request, owner_file),
                                 revision=request["expected_revision"] + 1)
        self.operator = Path(response["result"]["operator_actor_file"])

    def test_finish_rejects_an_inprogress_status_from_an_earlier_lease_epoch(self) -> None:
        self.call("task.replace", {"tasks": [
            {"id": "t1", "subject": "build", "status": "pending", "depends_on": []}],
            "allow_expansion": False})
        self.call("task.start", {"id": "t1"})
        self._advance_lease_epoch()
        request = self.request(self.operator, "task.finish",
                               f"finish-{self.state()['revision']}",
                               {"id": "t1", "outcome": "completed"})
        # AMBIGUITY: the PRD names no error code for this rejection;
        # "rejected_evidence" is assumed, matching tasks.py's other guards.
        self.reject_unchanged(request, self.operator, "rejected_evidence")

    def test_finish_succeeds_for_a_task_started_and_finished_in_the_same_epoch(self) -> None:
        self.call("task.replace", {"tasks": [
            {"id": "t2", "subject": "build", "status": "pending", "depends_on": []}],
            "allow_expansion": False})
        self.call("task.start", {"id": "t2"})
        _, finished = self.call("task.finish", {"id": "t2", "outcome": "completed"})
        self.assertEqual(finished["result"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
