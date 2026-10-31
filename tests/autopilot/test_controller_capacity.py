"""Normal admission, emergency reserves, and private archival round trips."""

from __future__ import annotations

import shutil
import stat
import unittest
from pathlib import Path

from controller_cli_support import cli, fresh_request, private_path, tree
from controller_owner_support import (
    NORMAL_BYTES, STATE_BYTES, OwnerCLITest, credential, hashes, seed_bytes,
    seed_receipts, state_bytes,
)


class CapacityTest(OwnerCLITest):
    def test_last_normal_slot_then_release_reserve_preserve_every_prior_receipt(self) -> None:
        _, _, operator = self.bootstrap()
        self.seed(seed_receipts(self.state(), self.root, 4093))
        prior = self.state()["receipts"]
        _, _, owner, operator = self.acquire(operator)
        self.assertEqual(len(self.state()["receipts"]), 4094)
        self.assertLess(len(state_bytes(self.state())), NORMAL_BYTES)
        normal = self.request(operator, "workflow.open", "normal-after-cap")
        self.reject_unchanged(normal, operator, "recovery_required")
        _, _, operator = self.clear(owner)
        self.assertEqual(len(self.state()["receipts"]), 4095)
        retained = self.state()["receipts"]
        for request_id, receipt in prior.items():
            self.assertEqual(retained[request_id], receipt)
        self.assertIsNone(self.snapshot()["owner"])
        no_owner = self.request(operator, "owner.recover", "no-owner-reserve", {
            "reason": "Explicit empty-owner reconciliation", "reconciled_job_ids": []})
        self.reject_unchanged(no_owner, operator, "recovery_required")

    def saturated_recovery(self) -> tuple[dict, dict, Path, Path]:
        _, _, operator = self.bootstrap()
        old_operator = self.retain(operator, "archive-old-operator.json")
        acquired, response, _, operator = self.acquire(operator)
        self.seed(seed_receipts(self.state(), self.root, 4095))
        prior = self.state()["receipts"]
        _, _, operator = self.clear(operator, "owner.recover", "emergency-recover")
        self.assertEqual(len(self.state()["receipts"]), 4096)
        self.assertEqual(len(self.state()["actors"]), 1)
        retained = self.state()["receipts"]
        for name, receipt in prior.items():
            self.assertEqual(retained[name], receipt)
        return acquired, response, old_operator, operator

    def assert_sealed_replay(self, request: dict, response: dict,
                             historical: Path, operator: Path) -> None:
        before = tree(private_path(self.root))
        for actor in (historical, operator):
            self.assertEqual(self.response(self.apply(request, actor)), response)
        for name, payload in (("owner.acquire", {"mode": "manual", "native_session_id": "sealed"}),
                              ("owner.recover", {"reason": "sealed", "reconciled_job_ids": []}),
                              ("workflow.open", {})):
            self.reject_unchanged(self.request(operator, name, f"sealed-{name}", payload),
                                  operator, "recovery_required")
        self.assertIsNone(self.snapshot()["owner"])
        self.assertTrue(tree(private_path(self.root)) == before)

    def test_hard_capacity_seals_new_mutations_but_preserves_snapshot_and_exact_replay(self) -> None:
        self.assert_sealed_replay(*self.saturated_recovery())

    def test_no_owner_cannot_use_either_reserved_count_slot(self) -> None:
        original = self.root
        for count in (4094, 4095):
            with self.subTest(count=count):
                self.root = original / str(count)
                self.root.mkdir()
                _, _, operator = self.bootstrap()
                self.seed(seed_receipts(self.state(), self.root, count))
                before = self.state()
                request = self.request(operator, "owner.recover", "reserve-empty", {
                    "reason": "No active owner", "reconciled_job_ids": []})
                self.reject_unchanged(request, operator, "recovery_required")
                acquire = self.request(operator, "owner.acquire", "reserve-acquire", {
                    "mode": "supervised", "native_session_id": "reserve-session"})
                self.reject_unchanged(acquire, operator, "recovery_required")
                self.assertEqual(self.state()["receipts"], before["receipts"])
                self.assertEqual(self.state()["revision"], before["revision"])
                self.assertIsNone(self.state()["owner"])

    def test_both_emergency_operations_use_either_reserve_but_never_override_hard_capacity(self) -> None:
        original = self.root
        for count in (4094, 4095, 4096):
            for name in ("owner.release", "owner.recover"):
                with self.subTest(count=count, operation=name):
                    self.root = original / str(count) / name
                    self.root.mkdir(parents=True)
                    _, _, operator = self.bootstrap()
                    _, _, owner, operator = self.acquire(operator)
                    self.seed(seed_receipts(self.state(), self.root, count))
                    actor = owner if name == "owner.release" else operator
                    payload = ({"reason": "Capacity reconciliation", "reconciled_job_ids": []}
                               if name == "owner.recover" else {})
                    request = self.request(actor, name, f"capacity-{name}", payload)
                    if count == 4096:
                        self.reject_unchanged(request, actor, "recovery_required")
                    else:
                        response = self.response(self.apply(request, actor), revision=2)
                        self.assert_transition(request, response, actor)
                        self.assertEqual(len(self.state()["receipts"]), count + 1)

    def test_normal_byte_admission_is_independent_of_receipt_count(self) -> None:
        original = self.root
        for offset, succeeds in ((-40000, True), (-1, False)):
            with self.subTest(offset=offset):
                self.root = original / str(offset)
                self.root.mkdir()
                _, _, operator = self.bootstrap()
                self.seed(seed_bytes(self.state(), self.root, NORMAL_BYTES + offset))
                self.assertLess(len(self.state()["receipts"]), 4094)
                request = self.request(operator, "owner.acquire", "byte-acquire", {
                    "mode": "supervised", "native_session_id": "byte-session-extra"})
                if succeeds:
                    response = self.response(self.apply(request, operator), revision=1)
                    self.assert_transition(request, response, operator)
                    self.assertLessEqual(len(state_bytes(self.state())), NORMAL_BYTES)
                else:
                    self.reject_unchanged(request, operator, "recovery_required")

    def test_only_active_owner_clearing_can_use_reserved_bytes_below_hard_ceiling(self) -> None:
        original = self.root
        for name in ("owner.release", "owner.recover"):
            with self.subTest(operation=name):
                self.root = original / name
                self.root.mkdir()
                _, _, operator = self.bootstrap()
                _, _, owner, operator = self.acquire(operator)
                self.seed(seed_bytes(self.state(), self.root, NORMAL_BYTES + 1000))
                self.assertLess(len(self.state()["receipts"]), 4094)
                prior = self.state()["receipts"]
                self.clear(owner if name == "owner.release" else operator, name)
                self.assertGreater(len(state_bytes(self.state())), NORMAL_BYTES)
                self.assertLessEqual(len(state_bytes(self.state())), STATE_BYTES)
                retained = self.state()["receipts"]
                for request_id, receipt in prior.items():
                    self.assertEqual(retained[request_id], receipt)

    def test_no_owner_cannot_consume_byte_reserve_and_emergency_cannot_exceed_state_ceiling(self) -> None:
        original = self.root
        for owned in (False, True):
            with self.subTest(owned=owned):
                self.root = original / str(owned)
                self.root.mkdir()
                _, _, operator = self.bootstrap()
                if owned:
                    _, _, owner, operator = self.acquire(operator)
                target = STATE_BYTES - 1 if owned else NORMAL_BYTES + 1000
                self.seed(seed_bytes(self.state(), self.root, target))
                self.assertLess(len(self.state()["receipts"]), 4094)
                recover = self.request(operator, "owner.recover", "oversize-recover", {
                    "reason": "Boundary reconciliation", "reconciled_job_ids": []})
                self.reject_unchanged(recover, operator, "recovery_required")
                if owned:
                    release = self.request(owner, "owner.release", "oversize-release")
                    self.reject_unchanged(release, owner, "recovery_required")

    def test_private_archive_hash_restore_and_distinct_workflow_roundtrip(self) -> None:
        acquired, response, historical, operator = self.saturated_recovery()
        self.assertIsNone(self.snapshot()["owner"])
        private = private_path(self.root)
        old_id = self.state()["workflow_id"]
        original = hashes(private)
        offline = self.base / "private-offline-archive"
        shutil.copytree(private, offline)
        self.assertEqual(stat.S_IMODE(offline.stat().st_mode), 0o700)
        self.assertEqual(hashes(offline), original)
        archived = private.with_name(old_id)
        private.rename(archived)
        self.assertEqual(stat.S_IMODE(archived.stat().st_mode), 0o700)
        self.assertEqual(hashes(archived), original)
        new_request = fresh_request(self.root, "open-distinct-after-archive")
        opened = self.response(self.apply(new_request), revision=0)
        self.assert_open_consistent(new_request, opened)
        self.assertNotEqual(opened["result"]["workflow_id"], old_id)
        self.assertNotEqual(opened["result"]["actor_id"], credential(historical)["actor_id"])
        newer = private.with_name(opened["result"]["workflow_id"])
        private.rename(newer)
        archived.rename(private)
        self.assertEqual(hashes(private), original)
        self.assertEqual(hashes(offline), original)
        self.assertTrue(newer.exists())
        self.assert_sealed_replay(acquired, response, historical, operator)
        self.assertEqual(hashes(private), original)


if __name__ == "__main__":
    unittest.main()
