"""Staging admission on every publishing path, and a clean concurrent lock race."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import test_controller_kernel as kernel
from controller_cli_support import (
    MAIN, existing_request, fresh_request, private_path, tree,
)
from controller_owner_support import OwnerCLITest
from test_controller_bootstrap_recovery import CRASH_DRIVER

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import actors
from autopilot_state.store import StateExistsError, StateIOError, StateStore

CREATORS = 5
ROUNDS = 12

# Each creator stops at its first create-if-absent open of the state lock
# sidecar and spins until every peer is there, so all of them create the same
# name in the same instant. Only the two documented public outcomes are
# reported as such; a StateIOError is reported by exception type instead of
# being swallowed.
INITIALIZER = """
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from autopilot_state.store import StateExistsError, StateIOError, StateStore
path, gate, ready, rendezvous = map(Path, sys.argv[2:6])
peers = int(sys.argv[6])
candidate = json.loads(sys.argv[7])
lock = path.with_name(path.name + '.lock')
real_open = os.open
arrived = []

def coordinated_open(file, flags, *args, **kwargs):
    if not arrived and os.fspath(file) in (str(lock), lock.name) and flags & os.O_CREAT:
        arrived.append(True)
        rendezvous.write_text('at creation')
        deadline = time.monotonic() + 1.5
        waiting = [rendezvous.parent / ('creation-' + str(index)) for index in range(peers)]
        while not all(peer.exists() for peer in waiting) and time.monotonic() < deadline:
            pass
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
    print(json.dumps({'outcome': 'initialized', 'raced': len(arrived), 'state': result}))
except StateExistsError:
    print(json.dumps({'outcome': 'exists', 'raced': len(arrived)}))
except StateIOError as error:
    print(json.dumps({'outcome': 'io_error', 'raced': len(arrived),
                      'exception': type(error).__name__}))
"""


class StagingAdmissionTest(OwnerCLITest):
    """Retained controller-owned orphans must bound both publishing paths."""

    def project(self, label: str) -> None:
        self.root = self.base / label
        self.root.mkdir()

    def owned_name(self, index: int) -> Path:
        """A retained orphan name the frozen owned-artifact patterns match."""
        token = secrets.token_hex(16)
        private = private_path(self.root)
        return [private / f".intent-{token}.tmp",
                private / f".state.json.autopilot-{token}.tmp",
                private / "actors" / f".operator-{token}.stage",
                private / "actors" / f".owner-{token}.stage",
                private / "actors" / f".operator-{token}.rollback"][index % 5]

    def decoy_name(self, index: int) -> Path:
        """A near-miss name sharing a prefix or suffix with an owned pattern."""
        token = secrets.token_hex(16)
        private = private_path(self.root)
        return [private / f".intent-{token[:31]}.tmp",
                private / f".intent-{token.upper()}.tmp",
                private / f".state.json.autopilot-{token}.tmp.bak",
                private / "actors" / f".operator-{token}.stage.bak",
                private / "actors" / f".owner-{token}.rollback"][index % 5]

    def seed(self, count: int, *, owned: bool, size: int | None = None) -> list[Path]:
        created = []
        for index in range(count):
            path = self.owned_name(index) if owned else self.decoy_name(index)
            matched = (actors.PRIVATE_ARTIFACT.fullmatch(path.name) is not None
                       or actors.ACTOR_ARTIFACT.fullmatch(path.name) is not None)
            self.assertIs(matched, owned, f"fixture name contradicts its role: {path.name}")
            if size is None:
                path.write_bytes(b"retained staging evidence")
            else:
                with path.open("wb") as handle:
                    handle.truncate(size)
            path.chmod(0o600)
            created.append(path)
        self.assertEqual(len(set(created)), count)
        return created

    def seed_over_the_byte_budget(self) -> list[Path]:
        """Few enough orphans to pass the file budget, big enough to fail bytes."""
        count = 4
        self.assertLess(count, actors.STAGING_FILE_LIMIT)
        orphans = self.seed(count, owned=True,
                            size=actors.STAGING_BYTE_LIMIT // count + 1)
        self.assertGreater(sum(path.stat().st_size for path in orphans),
                           actors.STAGING_BYTE_LIMIT)
        return orphans

    def crashed_bootstrap(self, label: str) -> dict:
        """Leave a pending bootstrap intent and no published state on disk."""
        self.project(label)
        request = fresh_request(self.root, f"open-{label}")
        prefix = [sys.executable, "-c", CRASH_DRIVER, str(MAIN), str(self.root),
                  "intent_dir_fsynced"]
        completed = self.apply(request, prefix=prefix)
        self.assertEqual(completed.returncode, 97,
                         completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(completed.stdout, b"")
        private = private_path(self.root)
        self.assertTrue((private / "credential-intent.json").is_file())
        self.assertFalse((private / "state.json").exists())
        return request

    def test_existing_open_is_refused_while_retained_owned_orphans_exceed_the_budget(self) -> None:
        self.project("existing-refused")
        _, opened = self.open("open-existing-refused")
        actor = Path(opened["result"]["actor_file"])
        orphans = self.seed(actors.STAGING_FILE_LIMIT + 1, owned=True)
        before = {path: path.read_bytes() for path in orphans}
        for request_id in ("existing-refused", "existing-refused-near"):
            with self.subTest(request_id=request_id):
                request = existing_request(self.root, opened["result"], request_id, 0)
                self.reject_unchanged(request, actor, "recovery_required")
                self.assertEqual(self.state()["revision"], 0)
                self.assertEqual(self.state()["repo_root"], str(self.root))
                self.assertNotIn(request_id, self.state()["receipts"])
        self.assertEqual({path: path.read_bytes() for path in orphans}, before,
                         "admission removed or rewrote retained orphan evidence")

    def test_existing_open_is_refused_while_retained_orphan_bytes_exceed_the_budget(self) -> None:
        self.project("existing-bytes")
        _, opened = self.open("open-existing-bytes")
        actor = Path(opened["result"]["actor_file"])
        orphans = self.seed_over_the_byte_budget()
        self.assertLessEqual(len(orphans), actors.STAGING_FILE_LIMIT)
        request = existing_request(self.root, opened["result"], "existing-byte-budget", 0)
        response = self.response(self.apply(request, actor), "recovery_required",
                                 revision=0)
        self.assertIsNone(response["result"])
        self.assertEqual(self.state()["revision"], 0)
        self.assertNotIn("existing-byte-budget", self.state()["receipts"])
        self.assertEqual([path.stat().st_size for path in orphans],
                         [actors.STAGING_BYTE_LIMIT // len(orphans) + 1] * len(orphans),
                         "admission truncated retained orphan evidence")

    def test_existing_open_still_publishes_with_large_orphans_under_both_budgets(self) -> None:
        self.project("existing-large")
        _, opened = self.open("open-existing-large")
        actor = Path(opened["result"]["actor_file"])
        each = actors.STAGING_BYTE_LIMIT // 4 - 262144
        orphans = self.seed(4, owned=True, size=each)
        total = sum(path.stat().st_size for path in orphans)
        self.assertLess(total, actors.STAGING_BYTE_LIMIT)
        self.assertGreater(total, actors.STAGING_BYTE_LIMIT // 2)
        request = existing_request(self.root, opened["result"], "existing-large", 0)
        response = self.response(self.apply(request, actor), revision=1)
        self.assertEqual(self.state()["revision"], 1)
        self.assertEqual(self.state()["receipts"]["existing-large"]["response"], response)
        self.assertTrue(all(path.is_file() for path in orphans))

    def test_existing_open_without_owned_orphans_advances_the_revision_by_one(self) -> None:
        self.project("existing-admitted")
        _, opened = self.open("open-existing-admitted")
        actor = Path(opened["result"]["actor_file"])
        self.assertEqual(list(private_path(self.root).glob(".*.tmp")), [])
        for index, request_id in enumerate(("existing-alpha", "existing-beta")):
            with self.subTest(request_id=request_id):
                request = existing_request(self.root, opened["result"], request_id, index)
                response = self.response(self.apply(request, actor), revision=index + 1)
                state = self.state()
                self.assertEqual(state["revision"], index + 1)
                self.assertEqual(state["repo_root"], str(self.root))
                self.assertEqual(state["project_id"], request["project_id"])
                self.assertEqual(state["receipts"][request_id]["response"], response)

    def test_near_miss_artifact_names_never_consume_the_existing_open_budget(self) -> None:
        self.project("existing-decoys")
        _, opened = self.open("open-existing-decoys")
        actor = Path(opened["result"]["actor_file"])
        decoys = self.seed(actors.STAGING_FILE_LIMIT + 1, owned=False)
        request = existing_request(self.root, opened["result"], "existing-decoyed", 0)
        response = self.response(self.apply(request, actor), revision=1)
        state = self.state()
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["receipts"]["existing-decoyed"]["response"], response)
        self.assertTrue(all(path.is_file() for path in decoys))

    def test_bootstrap_reconciliation_is_refused_while_owned_orphans_exceed_the_budget(self) -> None:
        request = self.crashed_bootstrap("bootstrap-refused")
        orphans = self.seed(actors.STAGING_FILE_LIMIT + 1, owned=True)
        private = private_path(self.root)
        before = tree(private)
        response = self.response(self.apply(request), "recovery_required", revision=0)
        self.assertIs(response["ok"], False)
        self.assertIsNone(response["result"])
        self.assertFalse((private / "state.json").exists(),
                         "a refused reconciliation published a revision anyway")
        self.assertTrue((private / "credential-intent.json").is_file())
        self.assertEqual(tree(private), before, "refusal changed private evidence")
        self.assertTrue(all(path.is_file() for path in orphans))

    def test_bootstrap_reconciliation_is_refused_while_orphan_bytes_exceed_the_budget(self) -> None:
        request = self.crashed_bootstrap("bootstrap-bytes")
        orphans = self.seed_over_the_byte_budget()
        self.assertLessEqual(len(orphans), actors.STAGING_FILE_LIMIT)
        private = private_path(self.root)
        response = self.response(self.apply(request), "recovery_required", revision=0)
        self.assertIsNone(response["result"])
        self.assertFalse((private / "state.json").exists(),
                         "a refused reconciliation published a revision anyway")
        self.assertTrue((private / "credential-intent.json").is_file())
        self.assertEqual([path.stat().st_size for path in orphans],
                         [actors.STAGING_BYTE_LIMIT // len(orphans) + 1] * len(orphans),
                         "admission truncated retained orphan evidence")

    def test_bootstrap_reconciliation_publishes_revision_zero_without_owned_orphans(self) -> None:
        request = self.crashed_bootstrap("bootstrap-admitted")
        decoys = self.seed(actors.STAGING_FILE_LIMIT + 1, owned=False)
        response = self.response(self.apply(request), revision=0)
        self.assert_open_consistent(request, response)
        private = private_path(self.root)
        self.assertFalse((private / "credential-intent.json").exists())
        self.assertEqual(self.state()["revision"], 0)
        self.assertEqual(self.state()["repo_root"], str(self.root))
        self.assertTrue(all(path.is_file() for path in decoys))


class StateLockRaceTest(unittest.TestCase):
    """A losing concurrent initializer reports `exists`, never an I/O failure."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.initial = kernel.frozen_state()

    def run_initializers(self, round_base: Path, candidates: list[dict]) -> list[dict]:
        gate = round_base / "start-gate"
        path = round_base / "state.json"
        processes = []
        for index, candidate in enumerate(candidates):
            command = [sys.executable, "-c", INITIALIZER, str(kernel.CONTROLLER),
                       str(path), str(gate), str(round_base / f"ready-{index}"),
                       str(round_base / f"creation-{index}"), str(len(candidates)),
                       json.dumps(candidate)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, cwd=round_base,
                                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            processes.append(process)
            self.addCleanup(kernel.StoreTest.stop_process, process)
        deadline = time.monotonic() + 20
        while not all((round_base / f"ready-{index}").exists()
                      for index in range(len(candidates))):
            self.assertLess(time.monotonic(), deadline,
                            "initializers must reach the start gate")
            time.sleep(0.01)
        gate.write_text("start")
        results = []
        for process in processes:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
            self.assertEqual(error, b"")
            results.append(json.loads(output))
        return results

    def corrupt_lock(self, label: str, kind: str) -> Path:
        """A state path whose lock sidecar is aliased, not a legitimate peer's."""
        directory = self.base / label
        directory.mkdir()
        path = directory / "state.json"
        lock = path.with_name(path.name + ".lock")
        if kind == "symlink":
            lock.symlink_to(directory / "elsewhere.lock")
        else:
            peer = directory / "peer.lock"
            peer.write_bytes(b"")
            os.link(peer, lock)
        return path

    def test_a_corrupt_state_lock_sidecar_is_an_io_error_not_a_lost_race(self) -> None:
        for kind in ("symlink", "hard-link"):
            with self.subTest(sidecar=kind):
                path = self.corrupt_lock(f"corrupt-{kind}", kind)
                with self.assertRaises(StateIOError) as caught:
                    StateStore(path).initialize(self.initial)
                self.assertNotIsInstance(caught.exception, StateExistsError,
                                         "a corrupt lock was reported as a lost race")
                self.assertFalse(path.exists(), "a refused initialize published state")

    def test_concurrent_lock_creators_either_win_or_lose_without_an_io_error(self) -> None:
        for attempt in range(ROUNDS):
            with self.subTest(round=attempt):
                round_base = self.base / f"round-{attempt}"
                round_base.mkdir()
                candidates = [dict(self.initial,
                                   repo_root=f"/synthetic/round-{attempt}-creator-{index}")
                              for index in range(CREATORS)]
                for candidate in candidates:
                    self.assertEqual(kernel.schema.validate_state(candidate), candidate)
                results = self.run_initializers(round_base, candidates)
                outcomes = [item["outcome"] for item in results]
                self.assertEqual([item["raced"] for item in results], [1] * CREATORS,
                                 "creators never met at the state lock creation")
                self.assertEqual([item.get("exception") for item in results
                                  if item["outcome"] == "io_error"], [],
                                 "a concurrent initializer surfaced StateIOError")
                self.assertEqual(set(outcomes), {"initialized", "exists"})
                self.assertEqual(outcomes.count("initialized"), 1)
                self.assertEqual(outcomes.count("exists"), CREATORS - 1)
                winner = next(item["state"] for item in results
                              if item["outcome"] == "initialized")
                self.assertIn(winner, candidates)
                path = round_base / "state.json"
                self.assertEqual(json.loads(path.read_bytes()), winner)
                self.assertEqual(kernel.StateStore(path).read(), winner)


if __name__ == "__main__":
    unittest.main()
