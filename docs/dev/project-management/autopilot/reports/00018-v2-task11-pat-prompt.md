
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: Restore pinned publication guard checks at every durability boundary

Description:
Restore pinned Store publication-guard rechecks discovered during task 2

Location: plugins/autopilot/controller/autopilot_state/store.py, tests/autopilot/test_controller_kernel.py

Contract:
Preserve pinned OVCAQ cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7 StateStore transaction publication_guard semantics and all six durability hooks. publication_guard must be checked before publication and after each durability hook before the next filesystem publication step. Evidence that becomes invalid at a hook must reject the transaction, retain a consistent previous state/backup pair, and never acknowledge a new revision. A valid guard permits normal commit and must observe every required boundary; never freeze success to a single guard call. Preserve CAS, recovery, secure path binding, private modes and post-replace restoration. No unrelated refactor, no fixture exemptions, no historical receipt repin.

Acceptance criteria:
A changed publication guard is rejected at each of BACKUP_TEMP_FSYNCED, BACKUP_REPLACED, BACKUP_DIR_FSYNCED, STATE_TEMP_FSYNCED, STATE_REPLACED and STATE_DIR_FSYNCED with the prior pair intact. A valid guard commits normally with complete required boundary observations. Existing kernel/adversarial/path/schema tests retain every scenario. Replace the proven contradictory single-call assertion with stronger required-boundary evidence, not a weaker assertion.

Verify: mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_kernel.py tests/autopilot/test_controller_store_guards_v2.py -q --tb=line

Task 2 remains pending until this bounded prerequisite passes. Keep caps, batch, work base, custody and historical evidence intact. No publication, installation or push.


Acceptance criteria:
Guard rejection at each of all six durability boundaries preserves exact old state/backup bytes and revision, never acknowledges success. Valid guard commits and observes each required boundary. No scenarios omitted or assertions weakened.

## Diff under review

```diff
diff --git a/plugins/autopilot/CHANGELOG.md b/plugins/autopilot/CHANGELOG.md
index f61941f..d7b7721 100644
--- a/plugins/autopilot/CHANGELOG.md
+++ b/plugins/autopilot/CHANGELOG.md
@@ -30,6 +30,7 @@
 
 ### Fixed
 
+- **autopilot**: restore transaction publication guard checks at every durability boundary, preserving exact state and backup rollback when evidence changes.
 - **autopilot**: `--verify` accepts a relative `--project-root` again and judges it exactly as its absolute spelling, instead of refusing every output path it resolves with `unsafe-artifact-path`.
 - **autopilot**: `--verify` proves both its log sink and its result-artifact sink openable before it spawns the child and judges each sink by the file it actually opened; when the spawn fails, an existing log and result artifact stay byte-identical and a log this run created is removed; it reports a sink open, write or close failure as its own controlled error with the child killed, stops the child's leftover processes when a sink fails late, and removes only a leaf it created; `--export-policy --out` refuses a reader-less FIFO instead of hanging and refuses up front where `O_NOFOLLOW` is missing; the log sink judges containment before it reads a Git pointer.
 - **autopilot**: `--verify` removes only the result artifact that its own failed run created; a file that took the artifact's name during the run, a leaf that became a directory, or a parent that became a symlink is left untouched and never replaces the run's own reported failure.
diff --git a/plugins/autopilot/controller/autopilot_state/store.py b/plugins/autopilot/controller/autopilot_state/store.py
index f6e0ac5..8476039 100644
--- a/plugins/autopilot/controller/autopilot_state/store.py
+++ b/plugins/autopilot/controller/autopilot_state/store.py
@@ -176,6 +176,7 @@ class StateStore:
         self._commit_pair(
             backup_bytes=current_raw, state_bytes=state_bytes,
             old_state=current_raw, old_backup=previous_backup,
+            publication_guard=publication_guard,
         )
         return committed
 
diff --git a/tests/autopilot/test_controller_kernel.py b/tests/autopilot/test_controller_kernel.py
index aad1794..8855d49 100644
--- a/tests/autopilot/test_controller_kernel.py
+++ b/tests/autopilot/test_controller_kernel.py
@@ -48,6 +48,11 @@ class StoreTest(unittest.TestCase):
         self.store.initialize(self.initial)
         return self.store.transaction(lambda value: None, expected_revision=0)
 
+    def assert_private_artifacts(self) -> None:
+        for suffix in ("", ".bak", ".lock"):
+            artifact = Path(str(self.path) + suffix)
+            self.assertEqual(stat.S_IMODE(artifact.stat().st_mode) & 0o077, 0, artifact)
+
     def test_initialization_is_create_only_and_returned_states_are_isolated(self) -> None:
         result = self.store.initialize(self.initial)
         self.assertEqual(result, self.initial)
@@ -83,6 +88,12 @@ class StoreTest(unittest.TestCase):
             self.store.initialize(frozen_state(owned=True))
         self.assertFalse(self.path.exists())
         self.assertFalse(self.backup.exists())
+        before = set(self.directory.iterdir())
+        with self.assertRaises(schema.SchemaError):
+            self.store.initialize({})
+        self.assertFalse(self.path.exists())
+        self.assertFalse(self.backup.exists())
+        self.assertEqual(set(self.directory.iterdir()), before)
 
     def test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup(self) -> None:
         self.store.initialize(self.initial)
@@ -94,6 +105,7 @@ class StoreTest(unittest.TestCase):
             candidate["revision"] = 100
 
         first = self.store.transaction(acquire, expected_revision=0)
+        self.assert_private_artifacts()
         self.assertEqual(first, frozen_state(owned=True))
         self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)
         seen[0]["actors"].clear()
@@ -102,6 +114,7 @@ class StoreTest(unittest.TestCase):
         replacement = frozen_state(owned=True)
         replacement["revision"] = 99
         second = self.store.transaction(lambda value: replacement, expected_revision=1)
+        self.assert_private_artifacts()
         expected = frozen_state(owned=True)
         expected["revision"] = 2
         self.assertEqual(second, expected)
@@ -140,13 +153,81 @@ class StoreTest(unittest.TestCase):
         self.assertEqual(called, ["publication"])
         self.assertEqual(self.pair(), before)
         self.assertEqual(self.store.read(), current)
-        called.clear()
-        result = self.store.transaction(lambda value: None,
-                                        publication_guard=lambda: called.append("success"))
-        self.assertEqual(called, ["success"])
-        self.assertEqual(result, dict(current, revision=2))
-        self.assertEqual(self.store.read(), result)
-        self.assertEqual(json.loads(self.backup.read_bytes()), current)
+
+    def test_valid_publication_guard_observes_every_boundary_before_proceeding(self) -> None:
+        current = self.seed_pair()
+        boundaries = []
+        observed = []
+        snapshots = []
+        other = self.directory / "state.json-extra"
+        other_backup = self.directory / "state.json.bak-extra"
+        other.write_bytes(b"near-match state evidence")
+        other_backup.write_bytes(b"near-match backup evidence")
+
+        def observe_boundary(boundary: DurabilityBoundary) -> None:
+            self.assertIn(tuple(boundaries), observed)
+            boundaries.append(boundary)
+            snapshots.append(self.pair())
+
+        def guard() -> None:
+            if tuple(boundaries) not in observed:
+                self.assertEqual(self.pair(), snapshots[-1])
+            observed.append(tuple(boundaries))
+
+        store = StateStore(self.path, boundary_hook=observe_boundary)
+        for revision in (1, 2):
+            with self.subTest(revision=revision):
+                boundaries.clear()
+                observed.clear()
+                snapshots[:] = [self.pair()]
+                result = store.transaction(lambda value: None, expected_revision=revision,
+                                           publication_guard=guard)
+                self.assertEqual(boundaries, list(DurabilityBoundary))
+                for count in range(len(boundaries) + 1):
+                    self.assertIn(tuple(boundaries[:count]), observed)
+                self.assertEqual(result, dict(current, revision=revision + 1))
+                self.assertEqual(self.store.read(), result)
+                self.assertEqual(json.loads(self.backup.read_bytes()), current)
+                self.assertEqual(other.read_bytes(), b"near-match state evidence")
+                self.assertEqual(other_backup.read_bytes(), b"near-match backup evidence")
+                current = result
+
+    def test_changed_publication_guard_rejects_every_boundary_and_preserves_exact_pair(self) -> None:
+        for revision in (1, 2):
+            for boundary in DurabilityBoundary:
+                directory = self.directory / f"{revision}-{boundary.value}"
+                directory.mkdir()
+                path = directory / "state.json"
+                backup = directory / "state.json.bak"
+                seed = StateStore(path)
+                initial = self.initial if revision == 1 else dict(frozen_state(owned=True), revision=0)
+                seed.initialize(initial)
+                for _ in range(revision):
+                    current = seed.transaction(lambda value: None)
+                before = (path.read_bytes(), backup.read_bytes())
+                calls = []
+                observed = []
+
+                def invalidate_evidence(item: DurabilityBoundary) -> None:
+                    calls.append(item)
+
+                def guard() -> None:
+                    observed.append(tuple(calls))
+                    if boundary in calls:
+                        raise RuntimeError(f"publication evidence changed: {boundary.value}")
+
+                with self.subTest(boundary=boundary, revision=revision):
+                    store = StateStore(path, boundary_hook=invalidate_evidence)
+                    with self.assertRaisesRegex(RuntimeError, f"changed: {boundary.value}"):
+                        store.transaction(lambda value: None, expected_revision=revision,
+                                          publication_guard=guard)
+                    expected = list(DurabilityBoundary)
+                    expected = expected[:expected.index(boundary) + 1]
+                    self.assertEqual(calls, expected)
+                    self.assertIn(tuple(expected), observed)
+                    self.assertEqual((path.read_bytes(), backup.read_bytes()), before)
+                    self.assertEqual(seed.read(), current)
+                    self.assertEqual(seed.read()["revision"], revision)
 
     def test_publication_guard_rechecks_changed_evidence_before_state_replace(self) -> None:
         self.seed_pair()
@@ -287,6 +368,7 @@ class StoreTest(unittest.TestCase):
             checked.append(copy.deepcopy(value))
 
         restored = self.store.restore(expected_revision=1, precondition=precondition)
+        self.assert_private_artifacts()
         expected = copy.deepcopy(backup)
         expected["revision"] = 2
         self.assertEqual(restored, expected)
@@ -297,6 +379,7 @@ class StoreTest(unittest.TestCase):
         self.assertEqual(self.store.read(), expected)
         previous = copy.deepcopy(expected)
         again = self.store.restore(expected_revision=2)
+        self.assert_private_artifacts()
         expected = dict(current, revision=3)
         self.assertEqual(again, expected)
         self.assertEqual(self.store.read(), expected)
@@ -333,6 +416,16 @@ class StoreTest(unittest.TestCase):
                     self.store.restore()
                 self.assertEqual(self.pair(), before)
 
+    def test_restore_requires_backup_without_creating_or_changing_artifacts(self) -> None:
+        current = self.seed_pair()
+        self.backup.unlink()
+        before = {item.name: item.read_bytes() for item in self.directory.iterdir()}
+        with self.assertRaises(BackupError):
+            self.store.restore(expected_revision=current["revision"])
+        self.assertEqual({item.name: item.read_bytes() for item in self.directory.iterdir()}, before)
+        self.assertFalse(self.backup.exists())
+        self.assertEqual(self.store.read(), current)
+
     def test_restore_boundary_failures_preserve_security_identical_pair(self) -> None:
         self.seed_pair()
         before = self.pair()
@@ -384,6 +477,9 @@ class StoreTest(unittest.TestCase):
                 else:
                     os.link(outside, artifact)
                 with self.subTest(suffix=suffix, kind=kind):
+                    if suffix == "":
+                        with self.assertRaises(StateError):
+                            StateStore(self.path).read()
                     with self.assertRaises(StateError):
                         StateStore(self.path).transaction(lambda value: None)
                     self.assertEqual(outside.read_bytes(), original)
@@ -422,6 +518,12 @@ class StoreTest(unittest.TestCase):
         self.assertEqual(((displaced / "state.json").read_bytes(),
                           (displaced / "state.json.bak").read_bytes()), before)
 
+    @staticmethod
+    def stop_process(process: subprocess.Popen) -> None:
+        if process.poll() is None:
+            process.kill()
+        process.communicate(timeout=5)
+
     def run_writers(self, *, writers: int, iterations: int, expected: int | None) -> list[dict]:
         script = """
 import json, sys, time
@@ -445,15 +547,17 @@ except RevisionConflictError:
     print(json.dumps({'outcome': 'conflict'}))
 """
         gate = self.base / "start-gate"
+        gate.unlink(missing_ok=True)
         processes = []
         for index in range(writers):
             ready = self.base / f"ready-{index}"
+            ready.unlink(missing_ok=True)
             command = [sys.executable, "-c", script, str(CONTROLLER), str(self.path),
                        str(gate), str(ready), str(iterations), str(expected) if expected is not None else "none"]
             process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        cwd=self.base, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
             processes.append(process)
-            self.addCleanup(lambda process=process: process.kill() if process.poll() is None else None)
+            self.addCleanup(self.stop_process, process)
         deadline = time.monotonic() + 20
         while not all((self.base / f"ready-{index}").exists() for index in range(writers)):
             self.assertLess(time.monotonic(), deadline, "writers must reach the shared start gate")
@@ -469,13 +573,30 @@ except RevisionConflictError:
 
     def test_real_process_cas_allows_exactly_one_writer_for_the_same_revision(self) -> None:
         self.store.initialize(self.initial)
-        results = self.run_writers(writers=3, iterations=1, expected=0)
-        self.assertEqual([item["outcome"] for item in results].count("committed"), 1)
-        self.assertEqual([item["outcome"] for item in results].count("conflict"), 2)
-        self.assertIn({"outcome": "committed", "revision": 1}, results)
-        expected = dict(self.initial, revision=1)
-        self.assertEqual(self.store.read(), expected)
-        self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)
+        for revision in (0, 1):
+            with self.subTest(revision=revision):
+                results = self.run_writers(writers=3, iterations=1, expected=revision)
+                self.assertEqual([item["outcome"] for item in results].count("committed"), 1)
+                self.assertEqual([item["outcome"] for item in results].count("conflict"), 2)
+                self.assertIn({"outcome": "committed", "revision": revision + 1}, results)
+                expected = dict(self.initial, revision=revision + 1)
+                self.assertEqual(self.store.read(), expected)
+                self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=revision))
+
+    def test_positive_stale_revisions_reject_transactions_and_restore_without_side_effects(self) -> None:
+        self.seed_pair()
+        current = self.store.transaction(lambda value: None, expected_revision=1)
+        before = self.pair()
+        called = []
+        with self.assertRaises(RevisionConflictError):
+            self.store.transaction(lambda value: called.append("mutator"), expected_revision=1)
+        self.assertEqual(called, [])
+        self.assertEqual(self.pair(), before)
+        with self.assertRaises(RevisionConflictError):
+            self.store.restore(expected_revision=1, precondition=lambda value: called.append("restore"))
+        self.assertEqual(called, [])
+        self.assertEqual(self.pair(), before)
+        self.assertEqual(self.store.read(), current)
 
     def test_real_process_writers_serialize_all_revision_increments_without_lost_updates(self) -> None:
         self.store.initialize(self.initial)
diff --git a/tests/autopilot/test_controller_store_guards_v2.py b/tests/autopilot/test_controller_store_guards_v2.py
new file mode 100644
index 0000000..63244a7
--- /dev/null
+++ b/tests/autopilot/test_controller_store_guards_v2.py
@@ -0,0 +1,208 @@
+"""Adversarial publication and initialization checks for the public store API."""
+
+from __future__ import annotations
+
+import copy
+import errno
+import json
+import os
+import stat
+import subprocess
+import sys
+import tempfile
+import time
+import unittest
+from pathlib import Path
+from unittest import mock
+
+import test_controller_kernel as kernel
+
+
+INITIALIZER = """
+import json, os, sys, time
+from pathlib import Path
+sys.path.insert(0, sys.argv[1])
+from autopilot_state.store import StateStore, StateExistsError
+path, gate, ready, rendezvous = map(Path, sys.argv[2:6])
+candidate = json.loads(sys.argv[6])
+real_open = os.open
+
+def coordinated_open(file: str | bytes | os.PathLike, flags: int, *args: object, **kwargs: object) -> int:
+    if os.fspath(file) in (str(path), path.name) and flags & os.O_CREAT:
+        rendezvous.write_text('at creation')
+        deadline = time.monotonic() + 2
+        peers = [rendezvous.parent / ('creation-' + str(index)) for index in range(2)]
+        while not all(peer.exists() for peer in peers) and time.monotonic() < deadline:
+            time.sleep(0.005)
+    return real_open(file, flags, *args, **kwargs)
+
+os.open = coordinated_open
+ready.write_text('ready')
+deadline = time.monotonic() + 15
+while not gate.exists():
+    if time.monotonic() > deadline:
+        raise RuntimeError('initializer start gate timeout')
+    time.sleep(0.005)
+try:
+    result = StateStore(path).initialize(candidate)
+    print(json.dumps({'outcome': 'initialized', 'state': result, 'bytes': path.read_bytes().hex()}))
+except StateExistsError:
+    print(json.dumps({'outcome': 'exists'}))
+"""
+
+
+class StoreGuardTest(unittest.TestCase):
+    def setUp(self) -> None:
+        self.temporary = tempfile.TemporaryDirectory()
+        self.addCleanup(self.temporary.cleanup)
+        self.base = Path(self.temporary.name)
+        self.path = self.base / "state.json"
+        self.backup = self.base / "state.json.bak"
+        self.store = kernel.StateStore(self.path)
+        self.initial = kernel.frozen_state()
+
+    def seed_pair(self) -> dict:
+        self.store.initialize(self.initial)
+        return self.store.transaction(lambda value: None, expected_revision=0)
+
+    def pair(self) -> tuple[bytes, bytes]:
+        return self.path.read_bytes(), self.backup.read_bytes()
+
+    def test_file_contents_are_synced_before_their_publication_boundaries(self) -> None:
+        self.seed_pair()
+        synced = []
+        snapshots = {}
+        real_fsync = os.fsync
+
+        def fsync(fd: int) -> None:
+            info = os.fstat(fd)
+            real_fsync(fd)
+            if stat.S_ISREG(info.st_mode):
+                synced.append((info.st_dev, info.st_ino))
+
+        def boundary(item: kernel.DurabilityBoundary) -> None:
+            if item.name in ("BACKUP_TEMP_FSYNCED", "STATE_TEMP_FSYNCED"):
+                self.assertTrue(synced, f"{item.name} requires a successful file fsync")
+                snapshots[item.name] = tuple(synced)
+                synced.clear()
+            elif item.name in ("BACKUP_REPLACED", "STATE_REPLACED"):
+                target = self.backup if item.name == "BACKUP_REPLACED" else self.path
+                info = target.stat()
+                key = item.name.replace("REPLACED", "TEMP_FSYNCED")
+                self.assertIn((info.st_dev, info.st_ino), snapshots[key])
+
+        store = kernel.StateStore(self.path, boundary_hook=boundary)
+        with mock.patch("os.fsync", side_effect=fsync):
+            result = store.transaction(lambda value: None, expected_revision=1)
+        self.assertEqual(result, dict(self.initial, revision=2))
+        self.assertEqual(self.store.read(), result)
+        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=1))
+        self.assertEqual(set(snapshots), {"BACKUP_TEMP_FSYNCED", "STATE_TEMP_FSYNCED"})
+
+    def test_file_fsync_errors_reject_publication_and_preserve_the_exact_pair(self) -> None:
+        current = self.seed_pair()
+        before = self.pair()
+        real_fsync = os.fsync
+        for ordinal, boundary in enumerate((kernel.DurabilityBoundary.BACKUP_TEMP_FSYNCED,
+                                            kernel.DurabilityBoundary.STATE_TEMP_FSYNCED), 1):
+            synced = []
+            observed = []
+
+            def fsync(fd: int) -> None:
+                if stat.S_ISREG(os.fstat(fd).st_mode):
+                    synced.append(fd)
+                    if len(synced) == ordinal:
+                        raise OSError(errno.EIO, "file contents fsync failed")
+                real_fsync(fd)
+
+            with self.subTest(boundary=boundary):
+                store = kernel.StateStore(self.path, boundary_hook=observed.append)
+                with mock.patch("os.fsync", side_effect=fsync):
+                    with self.assertRaises(kernel.StateIOError):
+                        store.transaction(lambda value: None, expected_revision=1)
+                self.assertGreaterEqual(len(synced), ordinal)
+                self.assertNotIn(boundary, observed)
+                self.assertEqual(self.pair(), before)
+                self.assertEqual(self.store.read(), current)
+
+    def test_replacement_mutators_reject_changed_guards_at_every_boundary(self) -> None:
+        for revision in (1, 2):
+            for boundary in kernel.DurabilityBoundary:
+                directory = self.base / f"{revision}-{boundary.value}"
+                directory.mkdir()
+                path = directory / "state.json"
+                backup = directory / "state.json.bak"
+                seed = kernel.StateStore(path)
+                seed.initialize(self.initial)
+                for _ in range(revision):
+                    current = seed.transaction(lambda value: None)
+                before = (path.read_bytes(), backup.read_bytes())
+                replacement = copy.deepcopy(current)
+                replacement["repo_root"] = "/synthetic/replacement-project"
+                self.assertEqual(kernel.schema.validate_state(replacement), replacement)
+                calls = []
+                observed = []
+
+                def guard() -> None:
+                    observed.append(tuple(calls))
+                    if boundary in calls:
+                        raise RuntimeError(f"publication evidence changed: {boundary.value}")
+
+                with self.subTest(boundary=boundary, revision=revision):
+                    store = kernel.StateStore(path, boundary_hook=calls.append)
+                    with self.assertRaisesRegex(RuntimeError, f"changed: {boundary.value}"):
+                        store.transaction(lambda value: replacement, expected_revision=revision,
+                                          publication_guard=guard)
+                    expected = list(kernel.DurabilityBoundary)
+                    expected = expected[:expected.index(boundary) + 1]
+                    self.assertEqual(calls, expected)
+                    self.assertIn(tuple(expected), observed)
+                    self.assertEqual((path.read_bytes(), backup.read_bytes()), before)
+                    self.assertEqual(seed.read(), current)
+                    self.assertEqual(seed.read()["revision"], revision)
+
+    def run_initializers(self, candidates: list[dict]) -> list[dict]:
+        gate = self.base / "start-gate"
+        processes = []
+        for index, candidate in enumerate(candidates):
+            ready = self.base / f"ready-{index}"
+            rendezvous = self.base / f"creation-{index}"
+            command = [sys.executable, "-c", INITIALIZER, str(kernel.CONTROLLER),
+                       str(self.path), str(gate), str(ready), str(rendezvous), json.dumps(candidate)]
+            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
+                                       cwd=self.base, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
+            processes.append(process)
+            self.addCleanup(kernel.StoreTest.stop_process, process)
+        deadline = time.monotonic() + 20
+        while not all((self.base / f"ready-{index}").exists() for index in range(len(candidates))):
+            self.assertLess(time.monotonic(), deadline, "initializers must reach the start gate")
+            time.sleep(0.01)
+        gate.write_text("start")
+        results = []
+        for process in processes:
+            output, error = process.communicate(timeout=30)
+            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
+            self.assertEqual(error, b"")
+            results.append(json.loads(output))
+        return results
+
+    def test_competing_initializers_publish_exactly_one_intact_winner(self) -> None:
+        candidates = [dict(self.initial, repo_root=f"/synthetic/initializer-{index}")
+                      for index in range(2)]
+        for candidate in candidates:
+            self.assertEqual(kernel.schema.validate_state(candidate), candidate)
+        results = self.run_initializers(candidates)
+        self.assertEqual([item["outcome"] for item in results].count("initialized"), 1)
+        self.assertEqual([item["outcome"] for item in results].count("exists"), 1)
+        success = next(item for item in results if item["outcome"] == "initialized")
+        winner = success["state"]
+        self.assertIn(winner, candidates)
+        self.assertEqual(self.path.read_bytes(), bytes.fromhex(success["bytes"]))
+        self.assertEqual(json.loads(self.path.read_bytes()), winner)
+        self.assertEqual(self.store.read(), winner)
+        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode) & 0o077, 0)
+        self.assertFalse(self.backup.exists())
+
+
+if __name__ == "__main__":
+    unittest.main()
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Command: mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_kernel.py tests/autopilot/test_controller_store_guards_v2.py -q --tb=line
Before implementation: exit1, 4 failed,22 passed in0.46s (three guard regressions and replacement-mutator guard regression).
After implementation: exit0, 26 passed in0.53s.
Canonical style gate: exit0. Split hygiene: exit0. Computed tautology check:26 functions,zero findings. Reflow:exit0.
Eight independent Devon wrong implementations were verified passing before all eight weak points were strengthened. No second Devon pass per workflow. All original scenarios retained; exact-one guard assertion replaced with stronger complete boundary evidence, no guard-call count ceiling.


Judge only from this prompt: the diff above, the task text, and this recorded
result. Do not read other files, run commands, or re-run the tests. What is not
in this prompt is not evidence, and a finding you cannot ground in what is here
is one you should not report.

# Simplification Mandate (step 5.7 reviewer-prompt appendix)

Append this block **verbatim** to every per-task code-reviewer prompt (see
`SKILL.md` step 5.7). It ships inside the prompt, so it must stay
self-contained.

> Beyond bugs, actively hunt for simplification in the diff under review. For
> every added or changed file, ask "what would make this simpler to read
> without changing what it does?" and flag concrete behavior-preserving
> opportunities to: reduce complexity (needless indirection, dead branches,
> single-caller abstractions, nesting deeper than 4 levels, functions over 50
> lines); eliminate redundancy (logic duplicated within the diff or against
> existing code, a helper that reimplements a stdlib or existing utility);
> improve naming (names that state intent, no opaque abbreviations); and
> remove dead code. Follow CLAUDE.md / AGENTS.md conventions and the
> surrounding code's style.
>
> Report each concrete behavior-preserving simplification as a LOW finding,
> with file:line, the current shape, and the simpler replacement. LOW findings
> are carried to the PRD-level review, never retried here.
>
> Do not over-simplify: never propose a change that trades clarity for
> brevity, drops error handling, collapses a deliberate boundary, or removes a
> documented invariant. Simpler means easier to read and maintain, not shorter
> at any cost. If a change would alter behavior, it is out of scope — do not
> flag it.


## Reporting contract

Report one finding per line, in exactly this shape:

SEVERITY | file:line | issue | fix

Severities are CRITICAL, HIGH, MEDIUM, LOW.

Severity has a fixed meaning here, and it decides what happens next. MEDIUM is
reserved for a correctness or security defect this diff introduces that its own
tests do not catch: a wrong result, an unhandled error path, data loss,
injection, secret exposure, or a missing authorization check. Style, naming,
duplication, structure and maintainability are LOW, and so is every
behavior-preserving simplification, whatever its size. A LOW is noted and
carried to the PRD-level review; it is never retried in this loop.

If the diff has no findings, emit the literal line:

NO FINDINGS

## Closure verdicts (only when the description carries a findings block)

When the Description above contains a `### Findings (verbatim)` block, this is
a rework task and each quoted finding is a claim to check. Before your findings
lines, emit one verdict per quoted finding, in this shape:

CLOSURE | resolved|unresolved | <the finding, quoted> | <one line of evidence from the diff>

Judge each finding against the diff, not against the commit message and not
against how clean the code reads. A diff that improves the file while leaving
the quoted defect reachable is `unresolved`. Quote the line that resolves it,
or say what still reaches the defect. Emit a verdict for every quoted finding,
including ones you judge already fixed elsewhere.


