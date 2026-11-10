"""owner.recover payload validation enforces the published empty reconciled_job_ids schema."""

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
    def test_rejects_reconciled_job_ids_with_multiple_entries(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": ["a" * 64, "b" * 64]}
        with self.assertRaises(schema.SchemaError):
            protocol.validate_payload("owner.recover", payload)

    def test_rejects_reconciled_job_ids_with_a_single_entry(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": ["c" * 64]}
        with self.assertRaises(schema.SchemaError):
            protocol.validate_payload("owner.recover", payload)

    def test_accepts_empty_reconciled_job_ids(self) -> None:
        payload = {"reason": REASON, "reconciled_job_ids": []}
        protocol.validate_payload("owner.recover", payload)  # must not raise


if __name__ == "__main__":
    unittest.main()
