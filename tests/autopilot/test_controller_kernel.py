"""Public guarded kernel behavior from the frozen AP00018 contract."""

from __future__ import annotations

import copy
import errno
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from controller_test_support import canonical, frozen_state

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import schema
from autopilot_state.store import (
    BackupError, DurabilityBoundary, DurabilityUnsupportedError, FutureSchemaError,
    RevisionConflictError, StateError, StateExistsError, StateIOError,
    StateResourceLimitError, StateStore,
)


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.directory = self.base / "controller"
        self.directory.mkdir()
        self.path = self.directory / "state.json"
        self.backup = self.directory / "state.json.bak"
        self.store = StateStore(self.path)
        self.initial = frozen_state()

    def pair(self) -> tuple[bytes, bytes]:
        return self.path.read_bytes(), self.backup.read_bytes()

    def seed_pair(self) -> dict:
        self.store.initialize(self.initial)
        return self.store.transaction(lambda value: None, expected_revision=0)

    def test_initialization_is_create_only_and_returned_states_are_isolated(self) -> None:
        result = self.store.initialize(self.initial)
        self.assertEqual(result, self.initial)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode) & 0o077, 0)
        self.initial["workflow"]["tasks"].append("caller mutation")
        result["actors"].clear()
        expected = frozen_state()
        self.assertEqual(self.store.read(), expected)
        read = self.store.read()
        read["receipts"].clear()
        self.assertEqual(self.store.read(), expected)
        before = self.path.read_bytes()
        owned_initial = frozen_state(owned=True)
        owned_initial["revision"] = 0
        with self.assertRaises(StateExistsError):
            self.store.initialize(owned_initial)
        self.assertEqual(self.path.read_bytes(), before)
        other = self.directory / "state-extra.json"
        owned_initial["workflow_id"] = "workflow-independent"
        for descriptor in owned_initial["actors"].values():
            descriptor["workflow_id"] = owned_initial["workflow_id"]
        receipt = owned_initial["receipts"]["open-synthetic"]
        receipt["authorizing_actor"]["workflow_id"] = owned_initial["workflow_id"]
        receipt["response"]["result"]["workflow_id"] = owned_initial["workflow_id"]
        self.assertEqual(schema.validate_state(owned_initial), owned_initial)
        self.assertEqual(StateStore(other).initialize(owned_initial), owned_initial)
        self.assertEqual(StateStore(other).read(), owned_initial)
        self.assertEqual(stat.S_IMODE(other.stat().st_mode) & 0o077, 0)
        self.assertEqual(self.store.read(), expected)

    def test_initialization_refuses_nonzero_revision_without_creating_state_or_backup(self) -> None:
        with self.assertRaises(StateError):
            self.store.initialize(frozen_state(owned=True))
        self.assertFalse(self.path.exists())
        self.assertFalse(self.backup.exists())

    def test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup(self) -> None:
        self.store.initialize(self.initial)
        seen = []

        def acquire(candidate: dict) -> None:
            seen.append(candidate)
            candidate.update(frozen_state(owned=True))
            candidate["revision"] = 100

        first = self.store.transaction(acquire, expected_revision=0)
        self.assertEqual(first, frozen_state(owned=True))
        self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)
        seen[0]["actors"].clear()
        first["receipts"].clear()
        self.assertEqual(self.store.read(), frozen_state(owned=True))
        replacement = frozen_state(owned=True)
        replacement["revision"] = 99
        second = self.store.transaction(lambda value: replacement, expected_revision=1)
        expected = frozen_state(owned=True)
        expected["revision"] = 2
        self.assertEqual(second, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), frozen_state(owned=True))
        replacement["actors"].clear()
        second["receipts"].clear()
        self.assertEqual(self.store.read(), expected)

    def test_validation_conflict_mutator_and_publication_failures_preserve_exact_pair(self) -> None:
        current = self.seed_pair()
        before = self.pair()
        called = []
        with self.assertRaises(RevisionConflictError):
            self.store.transaction(lambda value: called.append(True), expected_revision=0)
        self.assertEqual(called, [])
        self.assertEqual(self.pair(), before)
        with self.assertRaises(schema.SchemaError):
            self.store.transaction(lambda value: value["workflow"]["jobs"].append("job"))
        self.assertEqual(self.pair(), before)

        def refuse(candidate: dict) -> None:
            candidate["actors"].clear()
            raise RuntimeError("mutator-refusal")

        with self.assertRaisesRegex(RuntimeError, "mutator-refusal"):
            self.store.transaction(refuse)
        self.assertEqual(self.pair(), before)

        def guard() -> None:
            called.append("publication")
            raise RuntimeError("publication-refusal")

        with self.assertRaisesRegex(RuntimeError, "publication-refusal"):
            self.store.transaction(lambda value: None, publication_guard=guard)
        self.assertEqual(called, ["publication"])
        self.assertEqual(self.pair(), before)
        self.assertEqual(self.store.read(), current)
        called.clear()
        result = self.store.transaction(lambda value: None,
                                        publication_guard=lambda: called.append("success"))
        self.assertEqual(called, ["success"])
        self.assertEqual(result, dict(current, revision=2))
        self.assertEqual(self.store.read(), result)
        self.assertEqual(json.loads(self.backup.read_bytes()), current)

    def test_all_six_boundaries_surface_errors_and_interrupts_and_repair_the_pair(self) -> None:
        expected = {
            "BACKUP_TEMP_FSYNCED": "backup_temp_fsynced",
            "BACKUP_REPLACED": "backup_replaced",
            "BACKUP_DIR_FSYNCED": "backup_dir_fsynced",
            "STATE_TEMP_FSYNCED": "state_temp_fsynced",
            "STATE_REPLACED": "state_replaced",
            "STATE_DIR_FSYNCED": "state_dir_fsynced",
        }
        self.assertEqual({item.name: item.value for item in DurabilityBoundary}, expected)
        self.seed_pair()
        before = self.pair()
        for boundary in DurabilityBoundary:
            for exception in (RuntimeError, KeyboardInterrupt):
                calls = []

                def fail_at(item: DurabilityBoundary) -> None:
                    calls.append(item)
                    if item == boundary:
                        raise exception(boundary.value)

                with self.subTest(boundary=boundary, exception=exception):
                    store = StateStore(self.path, boundary_hook=fail_at)
                    with self.assertRaisesRegex(exception, boundary.value):
                        store.transaction(lambda value: None, expected_revision=1)
                    self.assertIn(boundary, calls)
                    self.assertEqual(self.pair(), before)
                    self.assertEqual(self.store.read()["revision"], 1)

    def test_successful_publication_reports_all_six_boundaries_and_commits_only_its_path(self) -> None:
        self.seed_pair()
        calls = []
        other = self.directory / "state.json-extra"
        other.write_bytes(b"near-match evidence")
        store = StateStore(self.path, boundary_hook=calls.append)
        result = store.transaction(lambda value: None, expected_revision=1)
        self.assertEqual(calls, list(DurabilityBoundary))
        self.assertEqual(result, dict(self.initial, revision=2))
        self.assertEqual(self.store.read(), result)
        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=1))
        self.assertEqual(other.read_bytes(), b"near-match evidence")

    def test_corrupt_current_is_never_replaced_by_backup_or_restore(self) -> None:
        self.seed_pair()
        backup = self.backup.read_bytes()
        duplicate = canonical(self.initial)[:-1] + b',"revision":999}'
        corruptions = ((b"{", StateIOError), (b"\xff", StateIOError),
                       (duplicate, StateIOError),
                       (b"{}", schema.SchemaError),
                       (canonical(dict(self.initial, schema_version=2)), FutureSchemaError))
        for content, error in corruptions:
            self.path.write_bytes(content)
            for operation in (self.store.read, self.store.restore,
                              lambda: self.store.transaction(lambda value: None)):
                with self.subTest(content=content, operation=operation):
                    with self.assertRaises(error):
                        operation()
                    self.assertEqual(self.pair(), (content, backup))

    def test_bounded_reads_refuse_oversized_state_without_touching_backup(self) -> None:
        self.seed_pair()
        self.path.write_bytes(b" " * (schema.MAX_STATE_BYTES + 1))
        before = self.pair()
        with self.assertRaises(StateResourceLimitError):
            self.store.read()
        with self.assertRaises(StateResourceLimitError):
            self.store.transaction(lambda value: None)
        self.assertEqual(self.pair(), before)

    def test_restore_refuses_acquired_or_security_changed_backup_and_preserves_credentials(self) -> None:
        self.seed_pair()
        self.store.transaction(lambda value: frozen_state(owned=True), expected_revision=1)
        credential = self.directory / "actors" / "owner.json"
        credential.parent.mkdir()
        credential.write_bytes(b"private-owner-credential\n")
        before = self.pair()
        with self.assertRaises(BackupError):
            self.store.restore(precondition=lambda value: None)
        self.assertEqual(self.pair(), before)
        self.assertEqual(credential.read_bytes(), b"private-owner-credential\n")
        original = self.store.read()
        def newer_epoch(value: dict) -> None:
            value["lease_epoch"] = 3
            value["owner"]["lease_epoch"] = 3
            for descriptor in value["actors"].values():
                descriptor["lease_epoch"] = 3

        changes = (
            newer_epoch,
            lambda value: value["owner"].update(mode="manual"),
            lambda value: value["actors"]["operator-synthetic"].update(secret_digest="f" * 64),
            lambda value: value["receipts"].clear(),
        )
        for change in changes:
            backup = copy.deepcopy(original)
            change(backup)
            self.assertEqual(schema.validate_state(backup), backup)
            self.backup.write_bytes(canonical(backup))
            before = self.pair()
            with self.subTest(change=change):
                with self.assertRaises(BackupError):
                    self.store.restore(precondition=lambda value: None)
                self.assertEqual(self.pair(), before)
                self.assertEqual(credential.read_bytes(), b"private-owner-credential\n")

    def test_security_identical_restore_advances_current_revision_and_preserves_security(self) -> None:
        current = self.seed_pair()
        backup = copy.deepcopy(current)
        backup["revision"] = 0
        backup["repo_root"] = "/synthetic/restored-project"
        self.assertEqual(schema.validate_state(backup), backup)
        self.backup.write_bytes(canonical(backup))
        checked = []

        def precondition(value: dict) -> None:
            checked.append(copy.deepcopy(value))

        restored = self.store.restore(expected_revision=1, precondition=precondition)
        expected = copy.deepcopy(backup)
        expected["revision"] = 2
        self.assertEqual(restored, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(checked, [current])
        self.assertEqual(json.loads(self.backup.read_bytes()), current)
        restored["actors"].clear()
        self.assertEqual(self.store.read(), expected)
        previous = copy.deepcopy(expected)
        again = self.store.restore(expected_revision=2)
        expected = dict(current, revision=3)
        self.assertEqual(again, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), previous)

    def test_restore_checks_intent_conflict_precondition_and_invalid_backup_before_publication(self) -> None:
        self.seed_pair()
        before = self.pair()
        with self.assertRaises(RevisionConflictError):
            self.store.restore(expected_revision=0)
        self.assertEqual(self.pair(), before)

        current = self.store.read()

        def refuse(value: dict) -> None:
            self.assertEqual(value, current)
            raise RuntimeError("precondition-refusal")

        with self.assertRaisesRegex(RuntimeError, "precondition-refusal"):
            self.store.restore(precondition=refuse)
        self.assertEqual(self.pair(), before)
        intent = self.directory / "credential-intent.json"
        intent.write_bytes(b"private-intent-evidence")
        with self.assertRaises(BackupError):
            self.store.restore(precondition=lambda value: None)
        self.assertEqual(intent.read_bytes(), b"private-intent-evidence")
        self.assertEqual(self.pair(), before)
        intent.unlink()
        for content in (b"{", b"{}", canonical(dict(self.initial, schema_version=2))):
            self.backup.write_bytes(content)
            before = self.pair()
            with self.subTest(content=content):
                with self.assertRaises(BackupError):
                    self.store.restore()
                self.assertEqual(self.pair(), before)

    def test_restore_boundary_failures_preserve_security_identical_pair(self) -> None:
        self.seed_pair()
        before = self.pair()
        for boundary in DurabilityBoundary:
            calls = []

            def fail_at(item: DurabilityBoundary) -> None:
                calls.append(item)
                if item == boundary:
                    raise RuntimeError(boundary.value)

            with self.subTest(boundary=boundary):
                store = StateStore(self.path, boundary_hook=fail_at)
                with self.assertRaisesRegex(RuntimeError, boundary.value):
                    store.restore(expected_revision=1)
                self.assertIn(boundary, calls)
                self.assertEqual(self.pair(), before)

    def test_unsupported_directory_fsync_is_explicit_and_preserves_pair(self) -> None:
        self.seed_pair()
        before = self.pair()
        real_fsync = os.fsync
        directories = []

        def unsupported(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directories.append(fd)
                raise OSError(errno.EINVAL, "directory fsync unsupported")
            real_fsync(fd)

        with mock.patch("os.fsync", side_effect=unsupported):
            with self.assertRaises(DurabilityUnsupportedError):
                self.store.transaction(lambda value: None)
        self.assertTrue(directories)
        self.assertEqual(self.pair(), before)

    def test_store_refuses_aliased_state_backup_and_lock_artifacts(self) -> None:
        self.seed_pair()
        for suffix in ("", ".bak", ".lock"):
            artifact = Path(str(self.path) + suffix)
            original = artifact.read_bytes()
            mode = artifact.stat().st_mode & 0o777
            for kind in ("symlink", "hardlink"):
                outside = self.base / f"outside-{kind}"
                outside.write_bytes(original)
                artifact.unlink()
                if kind == "symlink":
                    artifact.symlink_to(outside)
                else:
                    os.link(outside, artifact)
                with self.subTest(suffix=suffix, kind=kind):
                    with self.assertRaises(StateError):
                        StateStore(self.path).transaction(lambda value: None)
                    self.assertEqual(outside.read_bytes(), original)
                artifact.unlink()
                artifact.write_bytes(original)
                artifact.chmod(mode)
                outside.unlink()
            artifact.unlink()
            artifact.mkdir()
            with self.subTest(suffix=suffix, kind="directory"):
                with self.assertRaises(StateError):
                    StateStore(self.path).transaction(lambda value: None)
            artifact.rmdir()
            artifact.write_bytes(original)
            artifact.chmod(mode)

    def test_directory_identity_substitution_cannot_redirect_publication(self) -> None:
        self.seed_pair()
        before = self.pair()
        displaced = self.base / "original-controller"
        substituted = []

        def swap(boundary: DurabilityBoundary) -> None:
            if boundary == DurabilityBoundary.BACKUP_TEMP_FSYNCED and not substituted:
                self.directory.rename(displaced)
                self.directory.mkdir()
                self.path.write_bytes(b"replacement-state-evidence")
                self.backup.write_bytes(b"replacement-backup-evidence")
                substituted.append(True)

        store = StateStore(self.path, boundary_hook=swap)
        with self.assertRaises(StateError):
            store.transaction(lambda value: None)
        self.assertEqual(substituted, [True])
        self.assertEqual(self.pair(), (b"replacement-state-evidence", b"replacement-backup-evidence"))
        self.assertEqual(((displaced / "state.json").read_bytes(),
                          (displaced / "state.json.bak").read_bytes()), before)

    def run_writers(self, *, writers: int, iterations: int, expected: int | None) -> list[dict]:
        script = """
import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from autopilot_state.store import StateStore, RevisionConflictError
path, gate, ready = map(Path, sys.argv[2:5])
iterations = int(sys.argv[5])
expected = None if sys.argv[6] == 'none' else int(sys.argv[6])
ready.write_text('ready')
deadline = time.monotonic() + 15
while not gate.exists():
    if time.monotonic() > deadline:
        raise RuntimeError('start gate timeout')
    time.sleep(0.005)
try:
    for _ in range(iterations):
        state = StateStore(path).transaction(lambda value: None, expected_revision=expected)
    print(json.dumps({'outcome': 'committed', 'revision': state['revision']}))
except RevisionConflictError:
    print(json.dumps({'outcome': 'conflict'}))
"""
        gate = self.base / "start-gate"
        processes = []
        for index in range(writers):
            ready = self.base / f"ready-{index}"
            command = [sys.executable, "-c", script, str(CONTROLLER), str(self.path),
                       str(gate), str(ready), str(iterations), str(expected) if expected is not None else "none"]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       cwd=self.base, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            processes.append(process)
            self.addCleanup(lambda process=process: process.kill() if process.poll() is None else None)
        deadline = time.monotonic() + 20
        while not all((self.base / f"ready-{index}").exists() for index in range(writers)):
            self.assertLess(time.monotonic(), deadline, "writers must reach the shared start gate")
            time.sleep(0.01)
        gate.write_text("start")
        results = []
        for process in processes:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
            self.assertEqual(error, b"")
            results.append(json.loads(output))
        return results

    def test_real_process_cas_allows_exactly_one_writer_for_the_same_revision(self) -> None:
        self.store.initialize(self.initial)
        results = self.run_writers(writers=3, iterations=1, expected=0)
        self.assertEqual([item["outcome"] for item in results].count("committed"), 1)
        self.assertEqual([item["outcome"] for item in results].count("conflict"), 2)
        self.assertIn({"outcome": "committed", "revision": 1}, results)
        expected = dict(self.initial, revision=1)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)

    def test_real_process_writers_serialize_all_revision_increments_without_lost_updates(self) -> None:
        self.store.initialize(self.initial)
        results = self.run_writers(writers=3, iterations=4, expected=None)
        self.assertEqual([item["outcome"] for item in results], ["committed"] * 3)
        self.assertEqual(max(item["revision"] for item in results), 12)
        self.assertEqual(self.store.read(), dict(self.initial, revision=12))
        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=11))


if __name__ == "__main__":
    unittest.main()
