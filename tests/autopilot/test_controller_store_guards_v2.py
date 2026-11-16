"""Adversarial publication and initialization checks for the public store API."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

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
