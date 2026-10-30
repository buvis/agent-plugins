"""Targeted guarded-kernel regressions for the proven adversarial gaps."""

from __future__ import annotations

import copy
import errno
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from controller_test_support import frozen_state

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state.store import DurabilityBoundary, StateIOError, StateStore


class StoreRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "state.json"
        self.backup = self.path.with_name("state.json.bak")
        self.store = StateStore(self.path)

    def seed_pair(self) -> dict:
        self.store.initialize(frozen_state())
        return self.store.transaction(lambda value: None, expected_revision=0)

    def test_actor_digest_rotation_survives_unchanged_ownership_and_keeps_previous_backup(self) -> None:
        initial = frozen_state(owned=True)
        initial["revision"] = 0
        self.store.initialize(initial)

        def rotate(candidate: dict) -> None:
            candidate["actors"]["operator-synthetic"]["secret_digest"] = "f" * 64

        result = self.store.transaction(rotate, expected_revision=0)
        expected = copy.deepcopy(initial)
        expected["revision"] = 1
        expected["actors"]["operator-synthetic"]["secret_digest"] = "f" * 64
        self.assertEqual(result, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.path.read_bytes()), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), initial)
        self.assertEqual(result["owner"], initial["owner"])

    def test_publication_synchronizes_each_file_before_its_durability_boundary(self) -> None:
        current = self.seed_pair()
        real_fsync = os.fsync
        pending = []
        synced = {}
        calls = []

        def synchronize(fd: int) -> None:
            real_fsync(fd)
            identity = os.fstat(fd)
            if stat.S_ISREG(identity.st_mode):
                pending.append((identity.st_dev, identity.st_ino))

        def boundary(item: DurabilityBoundary) -> None:
            calls.append(item)
            if item in (DurabilityBoundary.BACKUP_TEMP_FSYNCED,
                        DurabilityBoundary.STATE_TEMP_FSYNCED):
                self.assertTrue(pending, "each temp boundary requires a successful file fsync")
                synced[item] = set(pending)
                pending.clear()
            for replaced, temporary, path in (
                (DurabilityBoundary.BACKUP_REPLACED, DurabilityBoundary.BACKUP_TEMP_FSYNCED,
                 self.backup),
                (DurabilityBoundary.STATE_REPLACED, DurabilityBoundary.STATE_TEMP_FSYNCED,
                 self.path),
            ):
                if item == replaced:
                    identity = path.stat()
                    self.assertIn((identity.st_dev, identity.st_ino), synced[temporary])

        store = StateStore(self.path, boundary_hook=boundary)
        with mock.patch("os.fsync", side_effect=synchronize):
            result = store.transaction(lambda value: None, expected_revision=1)
        self.assertEqual(calls, list(DurabilityBoundary))
        self.assertEqual(result, dict(current, revision=2))
        self.assertEqual(self.store.read(), result)
        self.assertEqual(json.loads(self.backup.read_bytes()), current)

    def test_file_sync_failures_refuse_publication_and_preserve_the_exact_pair(self) -> None:
        current = self.seed_pair()
        before = self.path.read_bytes(), self.backup.read_bytes()
        real_fsync = os.fsync
        for fail_at, forbidden in (
            (1, DurabilityBoundary.BACKUP_TEMP_FSYNCED),
            (2, DurabilityBoundary.STATE_TEMP_FSYNCED),
        ):
            files = []
            calls = []

            def synchronize(fd: int) -> None:
                if stat.S_ISREG(os.fstat(fd).st_mode):
                    files.append(fd)
                    if len(files) == fail_at:
                        raise OSError(errno.EIO, "file fsync failed")
                real_fsync(fd)

            with self.subTest(failing_file=fail_at):
                store = StateStore(self.path, boundary_hook=calls.append)
                with mock.patch("os.fsync", side_effect=synchronize):
                    with self.assertRaises(StateIOError):
                        store.transaction(lambda value: None, expected_revision=1)
                self.assertGreaterEqual(len(files), fail_at)
                self.assertNotIn(forbidden, calls)
                self.assertEqual((self.path.read_bytes(), self.backup.read_bytes()), before)
                self.assertEqual(self.store.read(), current)


if __name__ == "__main__":
    unittest.main()
