"""Optimistic concurrency: an edit between read and write is caught, never overwritten (T-025)."""

from __future__ import annotations

import unittest
from unittest import mock

import support
from specflow_helper import reconcile as reconcile_module
from specflow_helper.canonical import sha256_raw
from specflow_helper.reconcile import ConflictError, reconcile, write_guarded


class WriteGuardedTest(support.TempTest):
    def test_unchanged_file_is_written(self) -> None:
        path = self.tmp / "f.json"
        path.write_text("old")
        write_guarded(path, b"new", sha256_raw(path))
        self.assertEqual(path.read_bytes(), b"new")

    def test_file_changed_between_read_and_write_raises_and_keeps_the_edit(
        self,
    ) -> None:
        path = self.tmp / "f.json"
        path.write_text("old")
        read = sha256_raw(path)
        path.write_text("someone else's edit")
        with self.assertRaises(ConflictError) as caught:
            write_guarded(path, b"mine", read)
        self.assertEqual(path.read_text(), "someone else's edit")
        self.assertIn(str(path), str(caught.exception))

    def test_file_created_since_it_was_read_as_absent_raises(self) -> None:
        path = self.tmp / "f.json"
        path.write_text("appeared")
        with self.assertRaises(ConflictError):
            write_guarded(path, b"mine", None)
        self.assertEqual(path.read_text(), "appeared")

    def test_file_deleted_since_it_was_read_raises(self) -> None:
        path = self.tmp / "f.json"
        with self.assertRaises(ConflictError):
            write_guarded(path, b"mine", "0" * 64)
        self.assertFalse(path.exists())


class ReconcileConflictTest(support.TempTest):
    def test_reconcile_raises_when_state_changes_between_read_and_write(self) -> None:
        spec = support.write_spec(
            self.tmp / "00042-sample",
            {"requirements.md": support.REQUIREMENTS, "design.md": support.DESIGN},
        )
        support.approve(spec, support.new_state(), "requirements")
        (spec / "requirements.md").write_text(support.REQUIREMENTS + "Changed.\n")
        real = reconcile_module.artifact_status
        intervening = b'{"edited": "by another tool"}\n'

        def edit_then_read(*args: object) -> dict:
            result = real(*args)
            (spec / ".specflow.json").write_bytes(intervening)
            return result

        with mock.patch.object(reconcile_module, "artifact_status", edit_then_read):
            with self.assertRaises(ConflictError):
                reconcile(spec, dry_run=False)
        self.assertEqual((spec / ".specflow.json").read_bytes(), intervening)


if __name__ == "__main__":
    unittest.main()
