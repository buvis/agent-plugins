"""Workflow lifecycle, task and job shapes accepted by the controller schema."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from controller_test_support import WORKFLOW, frozen_state

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import schema

DEFAULT_WORKFLOW = {"batch": None, "work": None, "tasks": [],
                    "review": {"cap": 2}, "recovery": None, "jobs": []}


def task(task_id: str, status: str, depends_on: list) -> dict:
    return {"id": task_id, "subject": f"Subject of {task_id}", "status": status,
            "depends_on": depends_on, "attempts": []}


def job(job_id: str, role: str, depends_on: list, claimed_by: object,
        claim_epoch: object) -> dict:
    return {
        "spec": {"job_id": job_id, "role": role, "depends_on": depends_on,
                 "input_digests": ["a" * 64, "b" * 64], "isolation": "worktree",
                 "tier": "opus", "effort": "high"},
        "claimed_by": claimed_by, "claim_epoch": claim_epoch, "exit_fact": None,
    }


def valid_tasks() -> list:
    return [task("task-1", "pending", []),
            task("task-2", "in_progress", ["task-1"]),
            task("task-3", "completed", ["task-1", "task-2"]),
            task("task-4", "aborted", [])]


def valid_jobs() -> list:
    return [job("job-1", "builder", [], None, None),
            job("job-2", "reviewer", ["job-1"], "worker-2", 3)]


def batch() -> dict:
    return {"completed_prds": ["00012-x.md"], "parks_consecutive": 0}


def work(lane: object, lane_reason: object) -> dict:
    return {"prd": "00019-autopilot-controller-lifecycle-v1.md", "source": "wip",
            "entered_at": "2026-11-16T10:00:00Z", "phase": "build",
            "completed_phases": ["plan"], "lane": lane, "lane_reason": lane_reason}


def recovery() -> dict:
    return {"op": "advance", "boundary": "review"}


def state_with(**workflow: object) -> dict:
    value = frozen_state()
    value["workflow"].update(copy.deepcopy(workflow))
    return value


class WorkflowLifecycleSchemaTest(unittest.TestCase):
    def assert_invalid(self, value: object) -> None:
        with self.assertRaises(schema.SchemaError):
            schema.validate_state(value)

    def assert_valid(self, value: dict) -> None:
        original = copy.deepcopy(value)
        self.assertEqual(schema.validate_state(value), original)

    def test_untouched_default_workflow_is_still_accepted(self) -> None:
        self.assertEqual(WORKFLOW, DEFAULT_WORKFLOW)
        value = frozen_state()
        value["workflow"] = copy.deepcopy(DEFAULT_WORKFLOW)
        self.assert_valid(value)
        fresh = schema.new_state(repo_root=Path("/project"), project_id="c" * 64,
                                 workflow_id="lifecycle")
        self.assertEqual(schema.validate_state(fresh)["workflow"], DEFAULT_WORKFLOW)

    def test_accepts_task_records_in_every_status_and_returns_independent_copy(self) -> None:
        value = state_with(tasks=valid_tasks())
        original = copy.deepcopy(value)
        validated = schema.validate_state(value)
        self.assertEqual(validated, original)
        self.assertEqual([item["status"] for item in validated["workflow"]["tasks"]],
                         ["pending", "in_progress", "completed", "aborted"])
        validated["workflow"]["tasks"][1]["depends_on"].append("local mutation")
        validated["workflow"]["tasks"].pop()
        self.assertEqual(value, original)
        self.assert_valid(state_with(tasks=[task("only", "completed", [])]))
        self.assert_valid(state_with(tasks=[]))

    def test_rejects_task_status_outside_the_four_lifecycle_values(self) -> None:
        for status in ("complete", "completed-extra", "Completed", "in-progress",
                       "inprogress", "pending_extra", "abort", "", None, 1):
            for index in (0, 3):
                tasks = valid_tasks()
                tasks[index]["status"] = status
                with self.subTest(status=status, index=index):
                    self.assert_invalid(state_with(tasks=tasks))

    def test_rejects_non_string_task_ids_and_dependency_entries(self) -> None:
        for task_id in (7, None, True, ["task-1"], {"id": "task-1"}):
            for index in (0, 3):
                tasks = valid_tasks()
                tasks[index]["id"] = task_id
                with self.subTest(task_id=task_id, index=index):
                    self.assert_invalid(state_with(tasks=tasks))
        for depends_on in ([7], [None], ["task-1", 7], [["task-1"]], "task-1"):
            tasks = valid_tasks()
            tasks[2]["depends_on"] = depends_on
            with self.subTest(depends_on=depends_on):
                self.assert_invalid(state_with(tasks=tasks))

    def test_rejects_task_records_missing_a_field_or_not_objects(self) -> None:
        for key in ("id", "subject", "status", "depends_on", "attempts"):
            tasks = valid_tasks()
            del tasks[1][key]
            with self.subTest(missing=key):
                self.assert_invalid(state_with(tasks=tasks))
        for tasks in (["task"], [valid_tasks()[0], "task"], {"task-1": valid_tasks()[0]}):
            with self.subTest(tasks=tasks):
                self.assert_invalid(state_with(tasks=tasks))

    def test_accepts_job_records_claimed_and_unclaimed(self) -> None:
        value = state_with(jobs=valid_jobs())
        original = copy.deepcopy(value)
        validated = schema.validate_state(value)
        self.assertEqual(validated, original)
        jobs = validated["workflow"]["jobs"]
        self.assertEqual([item["spec"]["job_id"] for item in jobs], ["job-1", "job-2"])
        self.assertEqual([(item["claimed_by"], item["claim_epoch"]) for item in jobs],
                         [(None, None), ("worker-2", 3)])
        jobs[0]["spec"]["input_digests"].append("local mutation")
        self.assertEqual(value, original)
        self.assert_valid(state_with(jobs=[job("job-solo", "tester", [], "worker-9", 0)]))
        self.assert_valid(state_with(jobs=[]))

    def test_rejects_jobs_missing_or_with_non_string_job_id(self) -> None:
        for index in (0, 1):
            jobs = valid_jobs()
            del jobs[index]["spec"]["job_id"]
            with self.subTest(missing_at=index):
                self.assert_invalid(state_with(jobs=jobs))
        for job_id in (7, None, True, ["job-1"], {"job_id": "job-1"}):
            for index in (0, 1):
                jobs = valid_jobs()
                jobs[index]["spec"]["job_id"] = job_id
                with self.subTest(job_id=job_id, index=index):
                    self.assert_invalid(state_with(jobs=jobs))
        for jobs in (["job"], [valid_jobs()[0], "job"], {"job-1": valid_jobs()[0]}):
            with self.subTest(jobs=jobs):
                self.assert_invalid(state_with(jobs=jobs))

    def test_batch_work_and_recovery_reject_values_that_are_neither_null_nor_object(self) -> None:
        for key in ("batch", "work", "recovery"):
            self.assert_valid(state_with(**{key: None}))
            for replacement in ([], ["batch"], "batch", 0, 1, True, False, 1.5):
                with self.subTest(key=key, replacement=replacement):
                    self.assert_invalid(state_with(**{key: replacement}))

    def assert_rejects_shape_breaks(self, key: str, valid: dict, bad_values: dict) -> None:
        for field in valid:
            broken = copy.deepcopy(valid)
            del broken[field]
            with self.subTest(key=key, missing=field):
                self.assert_invalid(state_with(**{key: broken}))
        with self.subTest(key=key, extra="unknown"):
            self.assert_invalid(state_with(**{key: {**valid, "unknown": None}}))
        for field, values in bad_values.items():
            for bad in values:
                with self.subTest(key=key, field=field, bad=bad):
                    self.assert_invalid(state_with(**{key: {**valid, field: bad}}))

    def test_accepts_populated_batch_and_rejects_malformed_batch(self) -> None:
        self.assert_valid(state_with(batch=batch()))
        self.assert_valid(state_with(batch={"completed_prds": [], "parks_consecutive": 3}))
        self.assert_rejects_shape_breaks("batch", batch(), {
            "completed_prds": ["00012-x.md", None, {"prd": "00012-x.md"}, 0],
            "parks_consecutive": ["0", None, 1.5, [0]],
        })

    def test_accepts_populated_work_and_rejects_malformed_work(self) -> None:
        self.assert_valid(state_with(work=work("solo", "docs-only diff")))
        self.assert_valid(state_with(work=work(None, None)))
        self.assert_valid(state_with(work={**work(None, None), "source": "backlog"}))
        self.assert_rejects_shape_breaks("work", work("solo", "docs-only diff"), {
            "source": ["done", "WIP", "Backlog", "hold", "", None],
            "completed_phases": ["plan", None, {"plan": True}],
        })

    def test_accepts_populated_recovery_and_rejects_malformed_recovery(self) -> None:
        self.assert_valid(state_with(recovery=recovery()))
        self.assert_rejects_shape_breaks("recovery", recovery(), {
            "op": [None, 1, ["advance"]],
            "boundary": [None, 1, {"name": "review"}],
        })

    def test_review_still_accepts_only_the_frozen_cap(self) -> None:
        self.assert_valid(state_with(review={"cap": 2}, tasks=valid_tasks(), jobs=valid_jobs()))
        for review in ({"cap": 1}, {"cap": 3}, {"cap": 0}, {"cap": True},
                       {"cap": "2"}, {"cap": None}, {"cap": 2, "cap_extra": 2},
                       {"cap": 2, "cycle": 0}, {"cap_extra": 2}, {}, None, [2], 2):
            for populated in (False, True):
                workflow = {"review": review}
                if populated:
                    workflow.update(tasks=valid_tasks(), jobs=valid_jobs())
                with self.subTest(review=review, populated=populated):
                    self.assert_invalid(state_with(**workflow))

    def test_workflow_rejects_unknown_and_missing_keys_when_populated(self) -> None:
        for field in ("batch_extra", "tasks_extra", "phase", "next_phase"):
            for populated in (False, True):
                value = state_with(tasks=valid_tasks(), jobs=valid_jobs()) if populated \
                    else frozen_state()
                value["workflow"][field] = None
                with self.subTest(field=field, populated=populated):
                    self.assert_invalid(value)
        for key in DEFAULT_WORKFLOW:
            value = state_with(tasks=valid_tasks(), jobs=valid_jobs())
            del value["workflow"][key]
            with self.subTest(missing=key):
                self.assert_invalid(value)


if __name__ == "__main__":
    unittest.main()
