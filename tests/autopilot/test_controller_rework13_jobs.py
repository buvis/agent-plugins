"""Rework 13, review cycle 1: findings 4-7 (PRD 00019 jobs.py, protocol.py, owner.py).

Each test proves one named finding from the rework task description; see the
task report for which findings are genuinely ambiguous.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import protocol, schema


def spec(job_id: str, *depends: str) -> dict:
    return {"job_id": job_id, "role": "builder", "depends_on": list(depends),
            "input_digests": ["a" * 64], "isolation": "worktree", "tier": "opus",
            "effort": "high"}


def full_spec(job_id: str, **overrides: object) -> dict:
    base = {**spec(job_id), "source_digest": "b" * 64, "resource_digest": "c" * 64,
            "permitted_operations": ["read", "write"]}
    base.update(overrides)
    return base


def row(job_spec: dict) -> dict:
    return {"spec": job_spec, "claimed_by": None, "claim_epoch": None, "exit_fact": None}


# -- finding 4: job.plan must derive a plan when the caller supplies none ----


class DerivedPlanTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        _, _, self.operator = self.bootstrap()

    def call(self, name: str, payload: dict) -> tuple[dict, dict]:
        request = self.request(self.operator, name, f"{name}-{self.state()['revision']}",
                               payload)
        response = self.response(self.apply(request, self.operator),
                                 revision=request["expected_revision"] + 1)
        return request, response

    def test_job_plan_with_no_caller_specs_derives_a_nonempty_plan_from_tasks(self) -> None:
        self.call("task.replace", {"tasks": [
            {"id": "t1", "subject": "build", "status": "pending", "depends_on": []},
            {"id": "t2", "subject": "review", "status": "pending", "depends_on": ["t1"]},
        ], "allow_expansion": False})
        _, planned = self.call("job.plan", {"jobs": []})
        self.assertGreater(planned["result"]["job_count"], 0)
        self.assertTrue(self.state()["workflow"]["jobs"], "no jobs were derived from the plan")

    def test_job_plan_with_no_caller_specs_and_no_tasks_stays_empty(self) -> None:
        _, planned = self.call("job.plan", {"jobs": []})
        self.assertEqual(planned["result"], {"job_count": 0})
        self.assertEqual(self.state()["workflow"]["jobs"], [])


# -- finding 5: a structured, standalone next-job instruction operation ------


class NextJobInstructionTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        _, _, self.operator = self.bootstrap()

    def call(self, name: str, payload: dict) -> tuple[dict, dict]:
        request = self.request(self.operator, name, f"{name}-{self.state()['revision']}",
                               payload)
        response = self.response(self.apply(request, self.operator),
                                 revision=request["expected_revision"] + 1)
        return request, response

    def test_next_job_instruction_operation_is_declared_and_structured(self) -> None:
        # AMBIGUITY: the PRD names no operation for this; "job.next" is assumed,
        # matching the job.plan/job.claim/job.record_exit naming convention.
        metadata, _ = protocol.public_contract()
        self.assertIn("job.next", metadata["operations"])
        self.call("job.plan", {"jobs": [spec("build")]})
        _, instructed = self.call("job.next", {})
        result = instructed["result"]
        self.assertEqual(result.get("job_id"), "build")
        self.assertIn("instruction", result)


# -- finding 6: job specs must require source/resource digests and perms ----


class JobSpecSchemaTest(unittest.TestCase):
    def test_accepts_a_spec_declaring_source_resource_digest_and_permitted_operations(self) -> None:
        schema._job(row(full_spec("build")))

    def test_rejects_a_spec_missing_source_digest(self) -> None:
        job_spec = full_spec("build")
        del job_spec["source_digest"]
        with self.assertRaises(schema.SchemaError):
            schema._job(row(job_spec))

    def test_rejects_a_spec_missing_resource_digest(self) -> None:
        job_spec = full_spec("build")
        del job_spec["resource_digest"]
        with self.assertRaises(schema.SchemaError):
            schema._job(row(job_spec))

    def test_rejects_a_spec_missing_permitted_operations(self) -> None:
        job_spec = full_spec("build")
        del job_spec["permitted_operations"]
        with self.assertRaises(schema.SchemaError):
            schema._job(row(job_spec))


# -- finding 7: owner.recover must not be blocked by a nonempty job plan ----


class RecoverWithPlannedJobsTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        _, _, self.operator = self.bootstrap()

    def test_owner_recover_succeeds_with_a_nonempty_job_plan(self) -> None:
        plan_request = self.request(self.operator, "job.plan", "plan-1",
                                    {"jobs": [spec("build")]})
        planned = self.response(self.apply(plan_request, self.operator),
                                revision=plan_request["expected_revision"] + 1)
        self.assertEqual(planned["result"], {"job_count": 1})
        recover_request = self.request(self.operator, "owner.recover", "recover-1",
                                        {"reason": "crash recovery", "reconciled_job_ids": []})
        recovered = self.response(self.apply(recover_request, self.operator),
                                  revision=recover_request["expected_revision"] + 1)
        self.assertTrue(recovered["ok"])
        self.assertIsNone(self.state()["owner"])
        self.assertEqual(self.state()["workflow"]["jobs"][0]["spec"]["job_id"], "build")

    def test_owner_recover_succeeds_with_no_planned_jobs(self) -> None:
        recover_request = self.request(self.operator, "owner.recover", "recover-1",
                                        {"reason": "crash recovery", "reconciled_job_ids": []})
        recovered = self.response(self.apply(recover_request, self.operator),
                                  revision=recover_request["expected_revision"] + 1)
        self.assertTrue(recovered["ok"])


if __name__ == "__main__":
    unittest.main()
