"""owner.recover payload validation accepts reconciled_job_ids; business logic,
not schema validation, rejects nonempty job claims (owner.apply_locked's
rejected_evidence, since workflow.jobs is always frozen to [] in kernel v2)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import protocol, schema

REASON = "Explicit crash reconciliation"


class OwnerRecoverReconciledJobsValidationTest(unittest.TestCase):
    def test_accepts_reconciled_job_ids_with_multiple_entries(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": ["a" * 64, "b" * 64]}
        protocol.validate_payload("owner.recover", payload)  # must not raise

    def test_accepts_reconciled_job_ids_with_a_single_entry(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": ["c" * 64]}
        protocol.validate_payload("owner.recover", payload)  # must not raise

    def test_accepts_empty_reconciled_job_ids(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": []}
        protocol.validate_payload("owner.recover", payload)  # must not raise

    def test_rejects_duplicate_reconciled_job_ids(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": ["d" * 64, "d" * 64]}
        with self.assertRaises(schema.SchemaError):
            protocol.validate_payload("owner.recover", payload)


if __name__ == "__main__":
    unittest.main()
