"""Adversarial publication and initialization checks for the public store API."""

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

import test_controller_kernel as kernel


INITIALIZER = """
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from autopilot_state.store import StateStore, StateExistsError
path, gate, ready, rendezvous = map(Path, sys.argv[2:6])
candidate = json.loads(sys.argv[6])
real_open = os.open

def coordinated_open(file: str | bytes | os.PathLike, flags: int, *args: object, **kwargs: object) -> int:
    if os.fspath(file) in (str(path), path.name) and flags & os.O_CREAT:
        rendezvous.write_text('at creation')
        deadline = time.monotonic() + 2
        peers = [rendezvous.parent / ('creation-' + str(index)) for index in range(2)]
        while not all(peer.exists() for peer in peers) and time.monotonic() < deadline:
            time.sleep(0.005)
    return real_open(file, flags, *args, **kwargs)

os.open = coordinated_open
ready.write_text('ready')
deadline = time.monotonic() + 15
while not gate.exists():
    if time.monotonic() > deadline:
        raise RuntimeError('initializer start gate timeout')
    time.sleep(0.005)
try:
    result = StateStore(path).initialize(candidate)
    print(json.dumps({'outcome': 'initialized', 'state': result, 'bytes': path.read_bytes().hex()}))
except StateExistsError:
    print(json.dumps({'outcome': 'exists'}))
"""


class StoreGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.path = self.base / "state.json"
        self.backup = self.base / "state.json.bak"
        self.store = kernel.StateStore(self.path)
        self.initial = kernel.frozen_state()

    def seed_pair(self) -> dict:
        self.store.initialize(self.initial)
        return self.store.transaction(lambda value: None, expected_revision=0)

    def pair(self) -> tuple[bytes, bytes]:
        return self.path.read_bytes(), self.backup.read_bytes()

    def test_file_contents_are_synced_before_their_publication_boundaries(self) -> None:
        self.seed_pair()
        synced = []
        snapshots = {}
        real_fsync = os.fsync

        def fsync(fd: int) -> None:
            info = os.fstat(fd)
            real_fsync(fd)
            if stat.S_ISREG(info.st_mode):
                synced.append((info.st_dev, info.st_ino))

        def boundary(item: kernel.DurabilityBoundary) -> None:
            if item.name in ("BACKUP_TEMP_FSYNCED", "STATE_TEMP_FSYNCED"):
                self.assertTrue(synced, f"{item.name} requires a successful file fsync")
                snapshots[item.name] = tuple(synced)
                synced.clear()
            elif item.name in ("BACKUP_REPLACED", "STATE_REPLACED"):
                target = self.backup if item.name == "BACKUP_REPLACED" else self.path
                info = target.stat()
                key = item.name.replace("REPLACED", "TEMP_FSYNCED")
                self.assertIn((info.st_dev, info.st_ino), snapshots[key])

        store = kernel.StateStore(self.path, boundary_hook=boundary)
        with mock.patch("os.fsync", side_effect=fsync):
            result = store.transaction(lambda value: None, expected_revision=1)
        self.assertEqual(result, dict(self.initial, revision=2))
        self.assertEqual(self.store.read(), result)
        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=1))
        self.assertEqual(set(snapshots), {"BACKUP_TEMP_FSYNCED", "STATE_TEMP_FSYNCED"})

    def test_file_fsync_errors_reject_publication_and_preserve_the_exact_pair(self) -> None:
        current = self.seed_pair()
        before = self.pair()
        real_fsync = os.fsync
        for ordinal, boundary in enumerate((kernel.DurabilityBoundary.BACKUP_TEMP_FSYNCED,
                                            kernel.DurabilityBoundary.STATE_TEMP_FSYNCED), 1):
            synced = []
            observed = []

            def fsync(fd: int) -> None:
                if stat.S_ISREG(os.fstat(fd).st_mode):
                    synced.append(fd)
                    if len(synced) == ordinal:
                        raise OSError(errno.EIO, "file contents fsync failed")
                real_fsync(fd)

            with self.subTest(boundary=boundary):
                store = kernel.StateStore(self.path, boundary_hook=observed.append)
                with mock.patch("os.fsync", side_effect=fsync):
                    with self.assertRaises(kernel.StateIOError):
                        store.transaction(lambda value: None, expected_revision=1)
                self.assertGreaterEqual(len(synced), ordinal)
                self.assertNotIn(boundary, observed)
                self.assertEqual(self.pair(), before)
                self.assertEqual(self.store.read(), current)

    def test_replacement_mutators_reject_changed_guards_at_every_boundary(self) -> None:
        for revision in (1, 2):
            for boundary in kernel.DurabilityBoundary:
                directory = self.base / f"{revision}-{boundary.value}"
                directory.mkdir()
                path = directory / "state.json"
                backup = directory / "state.json.bak"
                seed = kernel.StateStore(path)
                seed.initialize(self.initial)
                for _ in range(revision):
                    current = seed.transaction(lambda value: None)
                before = (path.read_bytes(), backup.read_bytes())
                replacement = copy.deepcopy(current)
                replacement["repo_root"] = "/synthetic/replacement-project"
                self.assertEqual(kernel.schema.validate_state(replacement), replacement)
                calls = []
                observed = []

                def guard() -> None:
                    observed.append(tuple(calls))
                    if boundary in calls:
                        raise RuntimeError(f"publication evidence changed: {boundary.value}")

                with self.subTest(boundary=boundary, revision=revision):
                    store = kernel.StateStore(path, boundary_hook=calls.append)
                    with self.assertRaisesRegex(RuntimeError, f"changed: {boundary.value}"):
                        store.transaction(lambda value: replacement, expected_revision=revision,
                                          publication_guard=guard)
                    expected = list(kernel.DurabilityBoundary)
                    expected = expected[:expected.index(boundary) + 1]
                    self.assertEqual(calls, expected)
                    self.assertIn(tuple(expected), observed)
                    self.assertEqual((path.read_bytes(), backup.read_bytes()), before)
                    self.assertEqual(seed.read(), current)
                    self.assertEqual(seed.read()["revision"], revision)

    def run_initializers(self, candidates: list[dict]) -> list[dict]:
        gate = self.base / "start-gate"
        processes = []
        for index, candidate in enumerate(candidates):
            ready = self.base / f"ready-{index}"
            rendezvous = self.base / f"creation-{index}"
            command = [sys.executable, "-c", INITIALIZER, str(kernel.CONTROLLER),
                       str(self.path), str(gate), str(ready), str(rendezvous), json.dumps(candidate)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       cwd=self.base, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            processes.append(process)
            self.addCleanup(kernel.StoreTest.stop_process, process)
        deadline = time.monotonic() + 20
        while not all((self.base / f"ready-{index}").exists() for index in range(len(candidates))):
            self.assertLess(time.monotonic(), deadline, "initializers must reach the start gate")
            time.sleep(0.01)
        gate.write_text("start")
        results = []
        for process in processes:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
            self.assertEqual(error, b"")
            results.append(json.loads(output))
        return results

    def test_competing_initializers_publish_exactly_one_intact_winner(self) -> None:
        candidates = [dict(self.initial, repo_root=f"/synthetic/initializer-{index}")
                      for index in range(2)]
        for candidate in candidates:
            self.assertEqual(kernel.schema.validate_state(candidate), candidate)
        results = self.run_initializers(candidates)
        self.assertEqual([item["outcome"] for item in results].count("initialized"), 1)
        self.assertEqual([item["outcome"] for item in results].count("exists"), 1)
        success = next(item for item in results if item["outcome"] == "initialized")
        winner = success["state"]
        self.assertIn(winner, candidates)
        self.assertEqual(self.path.read_bytes(), bytes.fromhex(success["bytes"]))
        self.assertEqual(json.loads(self.path.read_bytes()), winner)
        self.assertEqual(self.store.read(), winner)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode) & 0o077, 0)
        self.assertFalse(self.backup.exists())


if __name__ == "__main__":
    unittest.main()
