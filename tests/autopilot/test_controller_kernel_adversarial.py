"""Targeted guarded-kernel regressions for the proven adversarial gaps."""

from __future__ import annotations

import copy
import errno
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_controller_kernel import frozen_state

from autopilot_state import schema
from autopilot_state.store import DurabilityBoundary, StateIOError, StateStore


class DecoderRegressionTest(unittest.TestCase):
    def test_finite_decimals_preserve_positive_negative_and_exponent_values(self) -> None:
        text = '{"values":[1.25,-2.5,3.125e2,-4.5E-2,0.0625]}'
        expected = {"values": [1.25, -2.5, 312.5, -0.045, 0.0625]}
        self.assertEqual(schema.decode_json(text, source="finite-decimals"), expected)

    def test_identical_duplicate_keys_are_rejected_at_top_level_and_nested(self) -> None:
        texts = ('{"same":1,"same":1}',
                 '{"nested":{"same":1,"same":1}}',
                 '[{"same":null,"same":null}]')
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaises(schema.SchemaError):
                    schema.decode_json(text, source="identical-duplicates")

    def test_negative_integer_digit_limit_accepts_boundary_and_rejects_overflow(self) -> None:
        boundary = "-" + "9" * schema.MAX_JSON_INTEGER_DIGITS
        self.assertEqual(schema.decode_json(boundary, source="negative-boundary"),
                         int(boundary))
        with self.assertRaises(schema.ResourceLimitError):
            schema.decode_json(boundary + "9", source="negative-overflow")

    def test_object_key_limits_measure_utf8_bytes_for_ascii_and_multibyte_keys(self) -> None:
        for character, count in (("x", schema.MAX_STRING_BYTES),
                                 ("é", schema.MAX_STRING_BYTES // 2)):
            key = character * count
            accepted = {key: 1}
            with self.subTest(character=character):
                text = json.dumps(accepted, ensure_ascii=False)
                self.assertEqual(schema.decode_json(text, source="key-boundary"), accepted)
                overflow = json.dumps({key + character: 1}, ensure_ascii=False)
                with self.assertRaises(schema.ResourceLimitError):
                    schema.decode_json(overflow, source="key-overflow")


class SchemaRegressionTest(unittest.TestCase):
    def test_active_and_receipt_actor_ids_reject_invalid_types_and_oversized_strings(self) -> None:
        invalid = (None, True, False, 7, 1.5, [], {}, "", "x" * 257, "é" * 129)
        for location in ("active", "receipt"):
            for actor_id in invalid:
                value = frozen_state()
                if location == "active":
                    descriptor = value["actors"]["operator-synthetic"]
                else:
                    descriptor = value["receipts"]["open-synthetic"]["authorizing_actor"]
                descriptor["actor_id"] = actor_id
                with self.subTest(location=location, actor_id=actor_id):
                    with self.assertRaises(schema.SchemaError):
                        schema.validate_state(value)

    def test_receipt_response_revision_rejects_bool_string_and_negative_counters(self) -> None:
        for revision in (True, False, "0", -1, None, 0.5):
            value = frozen_state()
            value["receipts"]["open-synthetic"]["response"]["revision"] = revision
            with self.subTest(revision=revision):
                with self.assertRaises(schema.SchemaError):
                    schema.validate_state(value)


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
