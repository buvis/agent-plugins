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

from autopilot_state import files, protocol, schema

from test_cycle2_jobs_metadata import BUCKETS, PRD, PRD_TEXT

# The three keys task 19 added: a caller must declare them, a stored row may omit them.
METADATA_KEYS = {"source_digest", "resource_digest", "permitted_operations"}


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
        for bucket in BUCKETS:
            (self.root / files.PRD_ROOT / bucket).mkdir(parents=True)
        (self.root / files.PRD_ROOT / "backlog" / PRD).write_text(PRD_TEXT)
        _, _, self.operator = self.bootstrap()
        self.enter()

    def enter(self) -> None:
        """Make PRD the active work: derivation digests the active PRD file."""
        request = self.request(self.operator, "prd.enter", "enter-prd", {"prds": [PRD]})
        response = self.response(self.apply(request, self.operator))
        self.assertEqual(response["result"]["prd"], PRD)

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
        self.assertEqual(planned["result"], {"job_count": 2})
        derived = [item["spec"] for item in self.state()["workflow"]["jobs"]]
        self.assertEqual({value["job_id"] for value in derived}, {"t1", "t2"})
        self.assertEqual([set(value) for value in derived], [schema.JOB_SPEC_KEYS] * 2)

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
        # Task 19 published "job.next" in the contract's operation list; the
        # result is the whole spec plus a standalone "instruction" string.
        metadata, _ = protocol.public_contract()
        self.assertIn("job.next", metadata["operations"])
        self.call("job.plan", {"jobs": [full_spec("build")]})
        _, instructed = self.call("job.next", {})
        result = instructed["result"]
        self.assertEqual(set(result), schema.JOB_SPEC_KEYS | {"instruction"})
        self.assertEqual({key: result[key] for key in schema.JOB_SPEC_KEYS},
                         full_spec("build"))
        self.assertIn("build", result["instruction"])
        self.assertIn("builder", result["instruction"])


# -- finding 6: job specs must require source/resource digests and perms ----


class JobSpecSchemaTest(unittest.TestCase):
    def caller(self, job_spec: dict) -> None:
        """Validate a spec the way protocol.py validates a caller's job.plan payload."""
        protocol.validate_payload("job.plan", {"jobs": [job_spec]})

    def reject_missing(self, key: str) -> None:
        """The complete spec is accepted; the same spec without `key` is rejected."""
        job_spec = full_spec("build")
        self.caller(job_spec)
        del job_spec[key]
        self.assertEqual(schema.JOB_SPEC_KEYS - set(job_spec), {key})
        with self.assertRaises(schema.SchemaError):
            self.caller(job_spec)

    def test_the_caller_path_requires_the_metadata_a_stored_row_may_omit(self) -> None:
        # Task 19 published this asymmetry: a caller spec is validated against
        # schema.JOB_SPEC_KEYS, a stored row only against _JOB_SPEC_REQUIRED,
        # so a row written before the metadata existed still loads.
        self.assertEqual(schema.JOB_SPEC_KEYS - schema._JOB_SPEC_REQUIRED, METADATA_KEYS)
        complete = full_spec("build")
        self.assertEqual(set(complete), schema.JOB_SPEC_KEYS)
        legacy = {key: value for key, value in complete.items()
                  if key not in METADATA_KEYS}

        self.caller(complete)
        schema._job(row(complete))
        schema._job(row(legacy))
        with self.assertRaises(schema.SchemaError):
            self.caller(legacy)

    def test_the_caller_path_rejects_a_spec_missing_source_digest(self) -> None:
        self.reject_missing("source_digest")

    def test_the_caller_path_rejects_a_spec_missing_resource_digest(self) -> None:
        self.reject_missing("resource_digest")

    def test_the_caller_path_rejects_a_spec_missing_permitted_operations(self) -> None:
        self.reject_missing("permitted_operations")


# -- finding 7: owner.recover must not be blocked by a nonempty job plan ----


class RecoverWithPlannedJobsTest(OwnerCLITest):
    def setUp(self) -> None:
        super().setUp()
        _, _, self.operator = self.bootstrap()

    def test_owner_recover_succeeds_with_a_nonempty_job_plan(self) -> None:
        plan_request = self.request(self.operator, "job.plan", "plan-1",
                                    {"jobs": [full_spec("build")]})
        planned = self.response(self.apply(plan_request, self.operator),
                                revision=plan_request["expected_revision"] + 1)
        self.assertEqual(planned["result"], {"job_count": 1})
        recover_request = self.request(self.operator, "owner.recover", "recover-1",
                                        {"reason": "crash recovery", "reconciled_job_ids": []})
        recovered = self.response(self.apply(recover_request, self.operator),
                                  revision=recover_request["expected_revision"] + 1)
        self.assertTrue(recovered["ok"])
        self.assertIsNone(self.state()["owner"])
        self.assertEqual(self.state()["workflow"]["jobs"][0]["spec"], full_spec("build"))

    def test_owner_recover_succeeds_with_no_planned_jobs(self) -> None:
        recover_request = self.request(self.operator, "owner.recover", "recover-1",
                                        {"reason": "crash recovery", "reconciled_job_ids": []})
        recovered = self.response(self.apply(recover_request, self.operator),
                                  revision=recover_request["expected_revision"] + 1)
        self.assertTrue(recovered["ok"])


if __name__ == "__main__":
    unittest.main()
