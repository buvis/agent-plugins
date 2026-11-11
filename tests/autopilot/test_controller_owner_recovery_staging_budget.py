"""Crash reconciliation is bounded by the staging-admission ceiling, not unlimited."""

from __future__ import annotations

import json
import secrets
import sys
import unittest
from pathlib import Path

from controller_cli_support import private_path
from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors


class OwnerRecoveryStagingBudgetTest(OwnerCLITest):
    def prepared(self, name: str, suffix: str = "first") -> tuple[dict, Path, Path]:
        _, _, operator = self.bootstrap()
        actor = operator
        if name != "owner.acquire":
            _, _, owner, operator = self.acquire(operator)
            actor = owner if name == "owner.release" else operator
        payload = ({"mode": "supervised", "native_session_id": "session-budget-extra"}
                   if name == "owner.acquire" else
                   {"reason": "Explicit crash reconciliation", "reconciled_job_ids": []}
                   if name == "owner.recover" else {})
        return self.request(actor, name, f"budget-{suffix}", payload), actor, operator

    def pending_intent(self) -> Path:
        return private_path(self.root) / "credential-intent.json"

    def seed_orphans(self, count: int, name: str = "state.json.autopilot") -> None:
        private = private_path(self.root)
        for _ in range(count):
            path = private / f".{name}-{secrets.token_hex(16)}.tmp"
            path.write_bytes(b"orphan")
            path.chmod(0o600)

    def seed_orphan_bytes(self, ceiling: int) -> None:
        path = private_path(self.root) / f".state.json.autopilot-{secrets.token_hex(16)}.tmp"
        path.write_bytes(b"x" * (ceiling + 1))
        path.chmod(0o600)

    def result(self, completed) -> dict:
        payload = completed.stdout
        if isinstance(payload, bytes):
            payload = payload.decode()
        return json.loads(payload)

    def test_refuses_reconciliation_once_the_staging_budget_is_exhausted(self) -> None:
        request, actor, _ = self.prepared("owner.acquire")
        historical = self.retain(actor, "historical-budget-exhausted.json")
        self.crash(request, actor, "intent_dir_fsynced")
        self.assertTrue(self.pending_intent().exists())
        self.seed_orphans(actors.STAGING_FILE_LIMIT)
        before = sorted(p.name for p in private_path(self.root).iterdir())

        completed = self.apply(request, historical)

        result = self.result(completed)
        self.assertFalse(result["ok"],
                          "reconciliation must refuse once the staging budget is exhausted")
        self.assertEqual(result["error_code"], "recovery_required")
        after = sorted(p.name for p in private_path(self.root).iterdir())
        self.assertEqual(before, after,
                          "a refused reconciliation must not create a new publication temp file")

    def test_refuses_reconciliation_once_the_staging_byte_ceiling_is_exceeded(self) -> None:
        request, actor, _ = self.prepared("owner.acquire")
        historical = self.retain(actor, "historical-budget-bytes.json")
        self.crash(request, actor, "intent_dir_fsynced")
        self.assertTrue(self.pending_intent().exists())
        self.seed_orphan_bytes(actors.STAGING_BYTE_LIMIT)
        before = sorted(p.name for p in private_path(self.root).iterdir())

        result = self.result(self.apply(request, historical))

        self.assertFalse(result["ok"], "orphan bytes above the ceiling must refuse reconciliation")
        self.assertEqual(result["error_code"], "recovery_required")
        self.assertEqual(before, sorted(p.name for p in private_path(self.root).iterdir()))
        self.assertTrue(self.pending_intent().exists())

    def test_repeated_crashes_stay_refused_while_exhausted_and_finish_once_freed(self) -> None:
        request, actor, _ = self.prepared("owner.acquire")
        historical = self.retain(actor, "historical-budget-repeat.json")
        self.crash(request, actor, "intent_dir_fsynced")
        self.seed_orphans(actors.STAGING_FILE_LIMIT)
        orphans = [p for p in private_path(self.root).iterdir() if p.name.endswith(".tmp")]
        before = sorted(p.name for p in private_path(self.root).iterdir())
        for _ in range(2):
            result = self.result(self.apply(request, historical))
            self.assertEqual(result["error_code"], "recovery_required")
            self.assertEqual(before, sorted(p.name for p in private_path(self.root).iterdir()))
        for orphan in orphans:
            orphan.unlink()
        self.crash(request, historical, "state_published")
        self.assertTrue(self.pending_intent().exists())
        result = self.result(self.apply(request, historical))
        self.assertTrue(result["ok"], "reconciliation must finish once the budget is freed")
        self.assertFalse(self.pending_intent().exists())

    def test_reconciliation_succeeds_well_under_the_staging_budget(self) -> None:
        request, actor, _ = self.prepared("owner.acquire")
        historical = self.retain(actor, "historical-budget-under.json")
        self.crash(request, actor, "intent_dir_fsynced")
        self.assertTrue(self.pending_intent().exists())
        self.seed_orphans(10)
        (private_path(self.root) / "unrelated-notes.txt").write_bytes(b"not a staging artifact")

        completed = self.apply(request, historical)

        result = self.result(completed)
        self.assertTrue(result["ok"],
                         "reconciliation must succeed when well under the staging budget")
        self.assertFalse(self.pending_intent().exists())


if __name__ == "__main__":
    unittest.main()
