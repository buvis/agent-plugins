"""PRD 00019 close-out: the cycle-3 cap-overflow findings R3, R4, R5 and R6.

R3 jobs belong to one PRD and are cleared at its boundary.
R4 a saga stages only against the revision its request was admitted at.
R5 a saga interrupted before its ledger append resumes from its recovery marker.
R6 derived planning drops dependencies on tasks that are already finished.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
from controller_cli_support import private_path
from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import files, protocol
from autopilot_state.store import RevisionConflictError, StateStore
from test_controller_lifecycle import (
    bucket_of,
    make_root,
    make_store,
    prd_text,
    request,
    work,
)

PRD = "00042-sample.md"
OTHER = "00043-other.md"
BUCKETS = ("backlog", "wip", "hold", "done")
PARK = {"prd": PRD, "site": "wrapper_died", "detail": "session ended"}
ONE_TASK = [{"id": "t1", "subject": "build it", "status": "pending", "depends_on": []}]


class DispatchTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        for bucket in BUCKETS:
            (self.root / files.PRD_ROOT / bucket).mkdir(parents=True)
        for name in (PRD, OTHER):
            (self.root / files.PRD_ROOT / "backlog" / name).write_text(
                "---\n---\n# PRD\n"
            )
        _, _, self.operator = self.bootstrap()

    def call(self, name: str, payload: dict) -> dict:
        value = self.request(self.operator, name, f"{name}-{self.serial}", payload)
        return self.response(self.apply(value, self.operator))

    def ledger(self) -> list[dict]:
        name = f"{self.state()['workflow_id']}-deferred.json"
        path = private_path(self.root) / "deferred" / name
        return json.loads(path.read_text())["items"] if path.exists() else []


# -- R3 jobs are scoped to the PRD that planned them --------------------------


class JobScopeTest(DispatchTest):
    def test_a_second_prd_plans_its_own_jobs_after_the_first_prd_leaves(self) -> None:
        self.call("prd.enter", {"prds": [PRD]})
        self.call(
            "task.replace", {"tasks": copy.deepcopy(ONE_TASK), "allow_expansion": False}
        )
        self.call("job.plan", {"jobs": []})
        first = self.state()["workflow"]["jobs"][0]["spec"]["resource_digest"]

        self.call("prd.park", PARK)

        self.assertEqual(
            self.state()["workflow"]["jobs"], [], "the parked PRD's jobs leave with it"
        )
        entered = self.call("prd.enter", {"prds": [OTHER]})
        self.assertEqual(entered["result"]["prd"], OTHER)
        self.call(
            "task.replace", {"tasks": copy.deepcopy(ONE_TASK), "allow_expansion": False}
        )
        planned = self.call("job.plan", {"jobs": []})

        self.assertEqual(planned["result"], {"job_count": 1})
        second = self.state()["workflow"]["jobs"][0]["spec"]["resource_digest"]
        self.assertNotEqual(
            first, second, "the second PRD's job attests the second PRD"
        )


# -- R6 derived planning drops dependencies on finished tasks -----------------


class DerivedDependencyTest(DispatchTest):
    def test_a_pending_task_that_depends_on_a_completed_task_is_planned_runnable(
        self,
    ) -> None:
        self.call("prd.enter", {"prds": [PRD]})
        plan = [
            {"id": "t1", "subject": "done", "status": "completed", "depends_on": []},
            {"id": "t2", "subject": "next", "status": "pending", "depends_on": ["t1"]},
            {"id": "t3", "subject": "after", "status": "pending", "depends_on": ["t2"]},
        ]
        self.call("task.replace", {"tasks": plan, "allow_expansion": False})

        planned = self.call("job.plan", {"jobs": []})

        self.assertEqual(planned["result"], {"job_count": 2})
        depends = {
            row["spec"]["job_id"]: row["spec"]["depends_on"]
            for row in self.state()["workflow"]["jobs"]
        }
        self.assertEqual(
            depends,
            {"t2": [], "t3": ["t2"]},
            "a finished dependency is satisfied; a planned one is kept",
        )
        offered = self.call("job.next", {})
        self.assertEqual(offered["result"]["job_id"], "t2")


# -- R5 an interrupted saga resumes from its own recovery marker --------------


class InterruptedSagaReplayTest(DispatchTest):
    def interrupt_park(self, value: dict) -> None:
        """Run the request's park saga in process and crash it before the ledger append."""

        def crash(boundary: files.SagaBoundary) -> None:
            if boundary is files.SagaBoundary.AFTER_MOVE_BEFORE_APPEND:
                raise RuntimeError("injected crash before the ledger append")

        store = StateStore(private_path(self.root) / "state.json")
        with pytest.raises(RuntimeError):
            files.park(
                store,
                project_root=self.root,
                prd=PRD,
                site=PARK["site"],
                detail=PARK["detail"],
                boundary_hook=crash,
                operation_id_factory=lambda: value["request_id"],
            )

    def test_a_park_crashed_before_its_ledger_append_resumes_on_retry(self) -> None:
        self.call("prd.enter", {"prds": [PRD]})
        value = self.request(self.operator, "prd.park", "park-interrupted", PARK)
        self.interrupt_park(value)
        self.assertNotEqual(self.state()["revision"], value["expected_revision"])
        self.assertIsNotNone(self.state()["workflow"]["recovery"])
        self.assertEqual(self.ledger(), [])

        resumed = self.response(self.apply(value, self.operator))

        self.assertIs(resumed["result"]["replayed"], True)
        self.assertIsNone(self.state()["workflow"]["recovery"])
        self.assertEqual(
            [item["op_id"] for item in self.ledger()], [value["request_id"]]
        )
        self.assertEqual(
            [
                name
                for name in BUCKETS
                if (self.root / files.PRD_ROOT / name / PRD).exists()
            ],
            ["hold"],
        )

    def test_a_stale_request_with_another_id_still_conflicts_with_the_marker(
        self,
    ) -> None:
        self.call("prd.enter", {"prds": [PRD]})
        value = self.request(self.operator, "prd.park", "park-interrupted", PARK)
        self.interrupt_park(value)

        competitor = dict(value, request_id="park-competitor")
        self.reject_unchanged(competitor, self.operator, "revision_conflict")


# -- R4 a saga stages only at its admitted revision ---------------------------


def test_a_park_admitted_at_an_older_revision_stages_nothing(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    admitted = store.read()["revision"]
    store.transaction(lambda state: None)
    before = store.read()

    with pytest.raises(RevisionConflictError):
        files.park(store, project_root=root, prd=PRD, expected_revision=admitted)

    assert store.read() == before
    assert bucket_of(root, PRD) == ["wip"]


def test_the_dispatcher_refuses_a_saga_when_a_commit_lands_after_admission(tmp_path):
    root = make_root(tmp_path, wip={PRD: prd_text()})
    store = make_store(root, work=work(PRD))
    admitted = request(store, "prd.park", PARK, "park-raced")
    original = files.park

    def raced_park(target, **kwargs):
        target.transaction(lambda state: None)  # another actor commits in the window
        return original(target, **kwargs)

    with (
        mock.patch.object(files, "park", raced_park),
        pytest.raises(protocol.ProtocolError) as caught,
    ):
        protocol.apply_unlocked(admitted, SimpleNamespace(verify=lambda: None), store)

    assert caught.value.code == "revision_conflict"
    assert bucket_of(root, PRD) == ["wip"]
    assert store.read()["workflow"]["recovery"] is None
