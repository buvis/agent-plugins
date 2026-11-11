"""owner.recover: the published contract lets reconciled_job_ids carry entries;
business logic, not the schema, rejects nonempty job claims (owner.apply_locked's
rejected_evidence, since workflow.jobs is always frozen to [] in kernel v2)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
CONTRACT = ROOT / "plugins" / "autopilot" / "contracts" / "controller" / "workflow-v1.json"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import protocol, schema
from controller_cli_support import private_path, tree
from controller_owner_support import OwnerCLITest

REASON = "Explicit crash reconciliation"


def published_jobs_schema() -> dict:
    document = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return document["$defs"]["recover_payload"]["properties"]["reconciled_job_ids"]


def assert_contract_admits(test: unittest.TestCase, count: int) -> None:
    jobs = published_jobs_schema()
    test.assertGreaterEqual(count, jobs.get("minItems", 0))
    test.assertTrue(jobs.get("maxItems") is None or count <= jobs["maxItems"],
                    f"published contract caps reconciled_job_ids below {count}")


class OwnerRecoverReconciledJobsContractTest(unittest.TestCase):
    def test_accepts_reconciled_job_ids_with_multiple_entries(self) -> None:
        assert_contract_admits(self, 2)
        payload = {"reason": REASON, "reconciled_job_ids": ["a" * 64, "b" * 64]}
        protocol.validate_payload("owner.recover", payload)

    def test_accepts_reconciled_job_ids_with_a_single_entry(self) -> None:
        assert_contract_admits(self, 1)
        payload = {"reason": REASON, "reconciled_job_ids": ["c" * 64]}
        protocol.validate_payload("owner.recover", payload)

    def test_rejects_duplicate_reconciled_job_ids(self) -> None:
        assert_contract_admits(self, 2)
        self.assertIs(published_jobs_schema().get("uniqueItems"), True)
        payload = {"reason": REASON, "reconciled_job_ids": ["d" * 64, "d" * 64]}
        with self.assertRaises(schema.SchemaError):
            protocol.validate_payload("owner.recover", payload)


class OwnerRecoverRefusesJobClaimsTest(OwnerCLITest):
    def test_controller_refuses_nonempty_reconciled_job_ids_with_rejected_evidence(self) -> None:
        assert_contract_admits(self, 2)
        _, _, operator = self.bootstrap()
        for index, jobs in enumerate((["a" * 64], ["a" * 64, "b" * 64])):
            request = self.request(operator, "owner.recover", f"claim-{index}",
                                   {"reason": REASON, "reconciled_job_ids": jobs})
            before = tree(private_path(self.root))
            self.reject_unchanged(request, operator, "rejected_evidence")
            self.assertEqual(self.state()["revision"], 0)
            self.assertTrue(tree(private_path(self.root)) == before)


if __name__ == "__main__":
    unittest.main()
