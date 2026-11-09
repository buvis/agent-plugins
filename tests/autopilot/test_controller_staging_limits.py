"""Bound real pre-intent crash evidence before bootstrap and owner admission."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import subprocess
import sys
import unittest
from pathlib import Path

from controller_cli_support import MAIN, fresh_request, private_path
from controller_owner_support import CRASH_SCRIPT, OwnerCLITest
from test_controller_bootstrap_recovery import CRASH_DRIVER

FILE_LIMIT = 64
BYTE_LIMIT = 16777216
OPERATIONS = ("workflow.open", "owner.acquire", "owner.release", "owner.recover")
BOUNDARIES = ("stage_fsynced", "intent_replace")
KERNEL_BOUNDARIES = ("backup_temp_fsynced", "state_temp_fsynced")
DAMAGE_KINDS = ("unreadable", "permissions", "symlink", "hardlink", "directory", "fifo")

# Stop immediately before publishing the fixed intent. This leaves the real
# fsynced intent temporary and credential stages, without reading runtime code.
INTENT_REPLACE_CRASH = r'''
import os, runpy, sys
from pathlib import Path
main, project = sys.argv[1:3]
root = Path(project) / ".autopilot" / "controller"
real_replace = os.replace

def destination(value, directory):
    path = Path(os.fsdecode(value))
    if path.is_absolute() or directory is None:
        return path.absolute()
    info = os.fstat(directory)
    current = root.stat()
    if (info.st_dev, info.st_ino) == (current.st_dev, current.st_ino):
        return root / path
    return None

def replace(source, target, *args, **kwargs):
    if destination(target, kwargs.get("dst_dir_fd")) == root / "credential-intent.json":
        os._exit(89)
    return real_replace(source, target, *args, **kwargs)

os.replace = replace
sys.argv = [main] + sys.argv[3:]
sys.path.insert(0, str(Path(main).parent))
runpy.run_path(main, run_name="__main__")
'''

# Supply the documented public boundary hook to the real CLI's StateStore.
# Abrupt process exit retains the publication temporary instead of unwinding it.
STORE_TEMP_CRASH = r'''
import os, runpy, sys
from pathlib import Path
main, boundary = sys.argv[1:3]
sys.path.insert(0, str(Path(main).parent))
from autopilot_state.store import StateStore
real_initialize = StateStore.__init__

def initialize(self, path, *, boundary_hook=None):
    def stop(item):
        if boundary_hook is not None:
            boundary_hook(item)
        if item.value == boundary:
            os._exit(88)
    real_initialize(self, path, boundary_hook=stop)

StateStore.__init__ = initialize
sys.argv = [main] + sys.argv[3:]
runpy.run_path(main, run_name="__main__")
'''


def signature(path: Path, *, changed: bool = True) -> tuple:
    """Compare evidence without putting credential plaintext in test failures.

    The inode change time exposes writes hidden by restored bytes or reset
    modification times. Only an attended archive rename omits it, and the
    contract's state.json.lock sidecar, whose metadata every locked call
    refreshes; its bytes, mode and mtime still count.
    """
    info = path.lstat()
    content = None
    if stat.S_ISLNK(info.st_mode):
        content = hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
    elif stat.S_ISREG(info.st_mode):
        try:
            content = hashlib.sha256(path.read_bytes()).hexdigest()
        except PermissionError:
            content = "unreadable"
    value = (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
             info.st_uid, info.st_gid, info.st_size, info.st_mtime_ns, content)
    if not changed or path.name == "state.json.lock":
        return value
    return value + (info.st_ctime_ns,)


def evidence(root: Path) -> dict:
    return {path: signature(path) for path in [root, *root.rglob("*")]}


class ControllerStagingLimitsTest(OwnerCLITest):
    def project(self, label: str) -> None:
        self.root = self.base / label
        self.root.mkdir()

    def prepared(self, name: str, label: str) -> tuple[dict, Path | None]:
        if name == "workflow.open":
            return fresh_request(self.root, f"open-{label}"), None
        _, _, operator = self.bootstrap()
        actor = operator
        if name != "owner.acquire":
            _, _, owner, operator = self.acquire(operator, session=f"session-{label}")
            actor = owner if name == "owner.release" else operator
        payload = ({"mode": "manual" if label.endswith("0") else "supervised",
                    "native_session_id": f"native-{label}"}
                   if name == "owner.acquire" else
                   {"reason": f"Attended orphan admission {label}", "reconciled_job_ids": []}
                   if name == "owner.recover" else {})
        return self.request(actor, name, f"mutate-{label}", payload), actor

    def crash_attempt(self, request: dict, actor: Path | None,
                      boundary: str) -> tuple[subprocess.CompletedProcess, int]:
        if boundary == "intent_replace":
            prefix = [sys.executable, "-c", INTENT_REPLACE_CRASH,
                      str(MAIN), str(self.root)]
            crash_code = 89
        elif actor is None:
            prefix = [sys.executable, "-c", CRASH_DRIVER, str(MAIN),
                      str(self.root), "stage_fsynced"]
            crash_code = 97
        else:
            prefix = [sys.executable, "-c", CRASH_SCRIPT, str(MAIN),
                      str(self.root), "stage_fsynced",
                      str(request["expected_revision"] + 1)]
            crash_code = 87
        return self.apply(request, actor, prefix=prefix), crash_code

    def checked_response(self, completed: subprocess.CompletedProcess,
                         request: dict, error: str | None = None) -> dict:
        self.assertTrue(completed.returncode == (0 if error is None else 1),
                        "CLI did not surface the expected structured outcome")
        value = json.loads(completed.stdout)
        self.assertTrue(set(value) == {"ok", "revision", "result", "error_code", "retryable"})
        self.assertIs(value["ok"], error is None)
        self.assertTrue(value["error_code"] == error)
        self.assertIs(value["retryable"], False)
        revision = request["expected_revision"] + (
            error is None and request["operation"] != "workflow.open")
        self.assertTrue(type(value["revision"]) is int and value["revision"] == revision)
        if error is not None:
            self.assertIsNone(value["result"])
        return value

    def stages_after_crash(self, request: dict, actor: Path | None,
                           boundary: str) -> list[Path]:
        root = private_path(self.root)
        old = set(root.rglob("*")) if root.exists() else set()
        completed, crash_code = self.crash_attempt(request, actor, boundary)
        self.assertTrue(completed.returncode == crash_code, "pre-intent crash was not reached")
        self.assertTrue(completed.stdout == b"", "crash acknowledged an unfinished mutation")
        self.assertFalse((root / "credential-intent.json").exists())
        stages = [path for path in root.rglob("*") if path not in old
                  and path.name not in {".gitignore", "state.json.lock"} and path.is_file()]
        self.assertTrue(bool(stages), "crash must leave real owned staging evidence")
        for path in stages:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(path.stat().st_nlink, 1)
        if boundary == "intent_replace":
            self.assertTrue(any(path.parent == root for path in stages),
                            "intent temporary must participate in resource admission")
        return stages

    def refuse_unchanged(self, request: dict, actor: Path | None) -> None:
        root = private_path(self.root)
        before = evidence(root)
        self.checked_response(self.apply(request, actor), request, "recovery_required")
        self.assertTrue(evidence(root) == before,
                        "refusal changed evidence or created proposed files")
        self.assertFalse((root / "credential-intent.json").exists())

    def refuse_without_authority(self, request: dict, actor: Path | None) -> None:
        """Bad revisions and forged credentials report state, never request echoes."""
        root = private_path(self.root)
        current = self.state()["revision"] if (root / "state.json").exists() else 0
        cases = [(request | {"expected_revision": request["expected_revision"] + 7}, actor, None)]
        if actor is not None:
            forged = self.retain(actor, f"forged-{self.serial}.json")
            fields = json.loads(forged.read_bytes()) | {"secret": secrets.token_urlsafe(32)}
            forged.write_bytes(json.dumps(fields).encode("utf-8"))
            cases.append((request, forged, "recovery_required"))
        for candidate, credential, excluded in cases:
            before = evidence(root)
            completed = self.apply(candidate, credential)
            self.assertTrue(completed.returncode == 1, "invalid authority was not rejected")
            value = json.loads(completed.stdout)
            self.assertIs(value["ok"], False)
            self.assertIsNone(value["result"])
            self.assertTrue(type(value["revision"]) is int and value["revision"] == current,
                            "rejection did not carry the current state revision")
            self.assertTrue(value["error_code"] not in {None, excluded},
                            "staging admission ran before actor authentication")
            self.assertTrue(evidence(root) == before, "rejection changed evidence")

    def crash_until_refused(self, request: dict, actor: Path | None, boundary: str,
                            stages: list[Path]) -> list[Path]:
        root = private_path(self.root)
        stages = list(stages)
        for _ in range(FILE_LIMIT + 1):
            before = evidence(root)
            completed, crash_code = self.crash_attempt(request, actor, boundary)
            if completed.returncode != crash_code:
                self.checked_response(completed, request, "recovery_required")
                self.assertTrue(evidence(root) == before)
                return stages
            self.assertTrue(completed.stdout == b"")
            new = [path for path in root.rglob("*") if path not in before and path.is_file()]
            self.assertTrue(bool(new), "repeated crash must retain new evidence")
            self.assertTrue(all(signature(path) == value for path, value in before.items()
                                if path.is_file()))
            stages.extend(new)
            self.assertLessEqual(len(stages), FILE_LIMIT)
            self.assertLess(sum(path.stat().st_size for path in stages), BYTE_LIMIT // 2)
            self.assertFalse((root / "credential-intent.json").exists())
        self.fail("repeated crashes did not reach a fail-closed resource boundary")

    def admit_at_count_boundary(self, request: dict, actor: Path | None, owned: list[Path],
                                archivable: list[Path], proposal: int) -> None:
        """Archive real orphans offline to one file over, then exactly at, the limit."""
        self.assertGreater(len(owned) + proposal, FILE_LIMIT,
                           "refused although the complete proposal fit the file limit")
        owned, archivable = list(owned), list(archivable)
        while len(owned) + proposal > FILE_LIMIT:
            if len(owned) + proposal == FILE_LIMIT + 1:
                self.refuse_unchanged(request, actor)
            path = archivable.pop()
            self.archive_one(path)
            owned.remove(path)
        self.assertEqual(len(owned) + proposal, FILE_LIMIT)
        self.succeed_preserving(request, actor, owned)

    def succeed_preserving(self, request: dict, actor: Path | None,
                           orphans: list[Path]) -> None:
        before = {path: signature(path) for path in orphans}
        historical = self.retain(actor, f"replay-{self.serial}.json") if actor is not None else None
        response = self.checked_response(self.apply(request, actor), request)
        self.assertTrue({path: signature(path) for path in orphans} == before,
                        "successful admission removed or rewrote orphan evidence")
        state = self.state()
        self.assertEqual(state["repo_root"], str(self.root))
        self.assertEqual(state["project_id"], request["project_id"])
        self.assertTrue(state["receipts"][request["request_id"]]["response"] == response)
        committed = evidence(private_path(self.root))
        self.assertTrue(self.checked_response(self.apply(request, historical), request) == response)
        self.assertTrue(evidence(private_path(self.root)) == committed)

    def archive_one(self, path: Path) -> None:
        archive = self.base / f"offline-{self.root.name}"
        archive.mkdir(mode=0o700, exist_ok=True)
        # A rename legitimately updates the inode change time.
        before = signature(path, changed=False)
        destination = archive / path.name
        path.rename(destination)
        self.assertTrue(signature(destination, changed=False) == before,
                        "attended fixture archive did not retain the original evidence")

    def read_only_at_saturation(self) -> None:
        root = private_path(self.root)
        before = evidence(root)
        state = self.state()
        opened = state["receipts"]["open-first"]["response"]
        operator = Path(opened["result"]["actor_file"])
        snapshot = self.snapshot()
        self.assertEqual(snapshot["lease_epoch"], state["lease_epoch"])
        original = fresh_request(self.root)
        replay = self.checked_response(self.apply(original, operator), original)
        self.assertTrue(replay == opened, "saturation changed an existing exact receipt")
        self.assertTrue(evidence(root) == before,
                        "read-only calls changed saturated staging evidence")

    def test_repeated_pre_intent_crashes_stop_at_file_budget_without_changing_evidence(self) -> None:
        proposals: dict[str, int] = {}
        for name in OPERATIONS:
            # An intent_replace crash stages the complete proposal; measure it first.
            for boundary in reversed(BOUNDARIES):
                with self.subTest(operation=name, boundary=boundary):
                    label = f"count-{name}-{boundary}"
                    self.project(label)
                    request, actor = self.prepared(name, label)
                    stages = self.stages_after_crash(request, actor, boundary)
                    if boundary == "intent_replace":
                        proposals[name] = len(stages)
                    self.assertIn(name, proposals, "complete proposal size was not measured")
                    proposal = proposals[name]
                    self.assertLessEqual(len(stages), proposal)
                    fixed = {path: signature(path) for path in private_path(self.root).rglob("*")
                             if path.is_file() and path not in stages}
                    stages = self.crash_until_refused(request, actor, boundary, stages)
                    self.assertGreater(len(stages), 1)
                    self.assertTrue(all(signature(path) == value for path, value in fixed.items()))
                    self.refuse_unchanged(request, actor)
                    self.refuse_unchanged(request | {"request_id": request["request_id"] + "-near"}, actor)
                    self.refuse_without_authority(request, actor)
                    if actor is not None:
                        self.read_only_at_saturation()
                    # Retain crash files offline one at a time: one file over
                    # the limit still refuses, an exact fit is admitted.
                    self.admit_at_count_boundary(request, actor, stages, stages, proposal)

    def test_byte_budget_refuses_below_at_and_above_limit_independently_of_count(self) -> None:
        for name in OPERATIONS:
            for boundary in BOUNDARIES:
                for delta in (-1, 0, 1):
                    with self.subTest(operation=name, boundary=boundary, delta=delta):
                        label = f"bytes-{name}-{boundary}-{delta}"
                        self.project(label)
                        request, actor = self.prepared(name, label)
                        stages = self.stages_after_crash(request, actor, boundary)
                        self.assertLess(len(stages), FILE_LIMIT // 2)
                        other = sum(path.stat().st_size for path in stages[1:])
                        with stages[0].open("r+b") as stream:
                            stream.truncate(BYTE_LIMIT + delta - other)
                        self.assertEqual(sum(path.stat().st_size for path in stages), BYTE_LIMIT + delta)
                        self.refuse_unchanged(request, actor)
                        self.refuse_unchanged(request | {"request_id": request["request_id"] + "-near"}, actor)
                        self.refuse_without_authority(request, actor)
                        if actor is not None:
                            self.read_only_at_saturation()

    def test_complete_proposed_byte_batch_fits_exact_ceiling_but_next_byte_refuses(self) -> None:
        for name in OPERATIONS:
            for delta in (0, 1):
                with self.subTest(operation=name, excess_bytes=delta):
                    label = f"inclusive-{name}-{delta}"
                    self.project(label)
                    request, actor = self.prepared(name, label)
                    stages = self.stages_after_crash(request, actor, "intent_replace")
                    proposal = sum(path.stat().st_size for path in stages)
                    other = sum(path.stat().st_size for path in stages[1:])
                    self.assertLess(2 * len(stages), FILE_LIMIT)
                    self.assertLess(2 * proposal, BYTE_LIMIT)
                    with stages[0].open("r+b") as stream:
                        stream.truncate(BYTE_LIMIT + delta - proposal - other)
                    existing = sum(path.stat().st_size for path in stages)
                    self.assertEqual(existing + proposal, BYTE_LIMIT + delta)
                    if delta:
                        self.refuse_unchanged(request, actor)
                        self.refuse_without_authority(request, actor)
                        if actor is not None:
                            self.read_only_at_saturation()
                    else:
                        self.succeed_preserving(request, actor, stages)

    def publication_orphans(self, request: dict, actor: Path,
                            boundary: str) -> tuple[list[Path], dict]:
        root = private_path(self.root)
        before = set(root.iterdir())
        historical = self.retain(actor, f"kernel-authorizer-{self.serial}.json")
        prefix = [sys.executable, "-c", STORE_TEMP_CRASH, str(MAIN), boundary]
        completed = self.apply(request, actor, prefix=prefix)
        self.assertTrue(completed.returncode == 88, "kernel temporary crash was not reached")
        self.assertTrue(completed.stdout == b"", "crash acknowledged unfinished publication")
        self.assertTrue((root / "credential-intent.json").is_file())
        orphans = [path for path in root.iterdir() if path not in before
                   and path.name not in {"credential-intent.json", "state.json", "state.json.bak"}
                   and path.is_file()]
        self.assertTrue(bool(orphans), "public kernel boundary must retain a real temporary")
        retained = {path: signature(path) for path in orphans}
        response = self.checked_response(self.apply(request, historical), request)
        self.assertFalse((root / "credential-intent.json").exists())
        self.assertTrue({path: signature(path) for path in orphans} == retained,
                        "matching intent reconciliation changed the kernel orphan")
        self.assertTrue(self.state()["receipts"][request["request_id"]]["response"] == response)
        committed = evidence(root)
        self.assertTrue(self.checked_response(self.apply(request, historical), request) == response)
        self.assertTrue(evidence(root) == committed)
        return orphans, response

    def following_mutation(self, name: str, response: dict) -> tuple[dict, Path]:
        operator = Path(response["result"]["operator_actor_file"])
        next_name = "owner.recover" if name == "owner.acquire" else "owner.acquire"
        payload = ({"reason": "Attended kernel orphan recovery", "reconciled_job_ids": []}
                   if next_name == "owner.recover" else
                   {"mode": "manual", "native_session_id": "after-kernel-orphan"})
        return self.request(operator, next_name, "after-kernel-orphan", payload), operator

    def test_reconciled_kernel_publication_orphans_count_toward_next_mutation_byte_budget(self) -> None:
        for name in OPERATIONS[1:]:
            for boundary in KERNEL_BOUNDARIES:
                with self.subTest(operation=name, boundary=boundary):
                    label = f"kernel-{name}-{boundary}"
                    self.project(label)
                    request, actor = self.prepared(name, label)
                    self.assertIsNotNone(actor)
                    orphans, response = self.publication_orphans(request, actor, boundary)
                    self.assertLess(len(orphans), FILE_LIMIT // 2)
                    other = sum(path.stat().st_size for path in orphans[1:])
                    with orphans[0].open("r+b") as stream:
                        stream.truncate(BYTE_LIMIT - other)
                    self.assertEqual(sum(path.stat().st_size for path in orphans), BYTE_LIMIT)
                    following, operator = self.following_mutation(name, response)
                    self.refuse_unchanged(following, operator)
                    self.refuse_without_authority(following, operator)
                    self.read_only_at_saturation()

    def test_reconciled_kernel_publication_orphans_count_toward_next_mutation_file_budget(self) -> None:
        for name in OPERATIONS[1:]:
            for boundary in KERNEL_BOUNDARIES:
                with self.subTest(operation=name, boundary=boundary):
                    label = f"kernel-count-{name}-{boundary}"
                    self.project(label)
                    request, actor = self.prepared(name, label)
                    orphans, response = self.publication_orphans(request, actor, boundary)
                    following, operator = self.following_mutation(name, response)
                    batch = self.stages_after_crash(following, operator, "intent_replace")
                    owned = self.crash_until_refused(following, operator, "intent_replace",
                                                     orphans + batch)
                    self.refuse_without_authority(following, operator)
                    self.read_only_at_saturation()
                    # Only crash stages are archived, so every kernel orphan
                    # stays in the owned set at both count boundaries.
                    crashed = [path for path in owned if path not in orphans]
                    self.admit_at_count_boundary(following, operator, owned, crashed, len(batch))

    def test_unsafe_kernel_publication_orphans_refuse_next_mutation_without_touching_evidence(self) -> None:
        for name in OPERATIONS[1:]:
            for boundary in KERNEL_BOUNDARIES:
                with self.subTest(operation=name, boundary=boundary):
                    label = f"kernel-unsafe-{name}-{boundary}"
                    self.project(label)
                    request, actor = self.prepared(name, label)
                    orphans, response = self.publication_orphans(request, actor, boundary)
                    following, operator = self.following_mutation(name, response)
                    for kind in DAMAGE_KINDS:
                        for target in orphans:
                            self.refuse_damaged(following, operator, target, kind)
                    # Every orphan is restored, so the same mutation is admitted.
                    self.succeed_preserving(following, operator, orphans)

    def test_safe_orphans_below_both_limits_allow_real_mutations_and_exact_replay(self) -> None:
        for name in OPERATIONS:
            for boundary in BOUNDARIES:
                for size in (1048576, 2097152):
                    with self.subTest(operation=name, boundary=boundary, size=size):
                        label = f"allowed-{name}-{boundary}-{size}"
                        self.project(label)
                        request, actor = self.prepared(name, label)
                        stages = self.stages_after_crash(request, actor, boundary)
                        with stages[0].open("r+b") as stream:
                            stream.truncate(size)
                        self.assertLess(len(stages), FILE_LIMIT)
                        self.assertLess(sum(path.stat().st_size for path in stages), BYTE_LIMIT)
                        self.succeed_preserving(request, actor, stages)

    def damage(self, path: Path, kind: str) -> Path | None:
        if kind == "unreadable":
            path.chmod(0)
            self.addCleanup(path.chmod, 0o600)
            return None
        if kind == "permissions":
            path.chmod(0o640)
            return None
        outside = self.base / f"outside-{self.serial}"
        outside.write_bytes(path.read_bytes())
        outside.chmod(0o600)
        path.unlink()
        if kind == "symlink":
            path.symlink_to(outside)
        elif kind == "hardlink":
            os.link(outside, path)
        elif kind == "directory":
            path.mkdir(mode=0o700)
        else:
            os.mkfifo(path, 0o600)
        return outside

    def restore(self, path: Path, kind: str, outside: Path | None) -> None:
        """Put the original bytes back as a safe private file after a refusal."""
        if outside is None:
            path.chmod(0o600)
            return
        if kind == "directory":
            path.rmdir()
        else:
            path.unlink()
        outside.rename(path)

    def refuse_damaged(self, request: dict, actor: Path | None, target: Path, kind: str) -> None:
        outside = self.damage(target, kind)
        before = signature(outside) if outside is not None else None
        self.refuse_unchanged(request, actor)
        if outside is not None:
            self.assertTrue(signature(outside) == before)
        self.restore(target, kind, outside)

    def test_unsafe_or_unreadable_owned_artifacts_refuse_without_touching_evidence(self) -> None:
        for name in OPERATIONS:
            for boundary in BOUNDARIES:
                for kind in DAMAGE_KINDS:
                    with self.subTest(operation=name, boundary=boundary, kind=kind):
                        label = f"unsafe-{name}-{boundary}-{kind}"
                        self.project(label)
                        request, actor = self.prepared(name, label)
                        stages = self.stages_after_crash(request, actor, boundary)
                        # Exercise the root intent temporary first, then every
                        # credential stage and rollback copy the crash left.
                        ordered = sorted(stages, key=lambda path: path.parent != private_path(self.root))
                        target = ordered[0]
                        outside = self.damage(target, kind)
                        before = signature(outside) if outside is not None else None
                        self.refuse_unchanged(request, actor)
                        self.refuse_unchanged(request | {"request_id": request["request_id"] + "-near"}, actor)
                        self.refuse_without_authority(request, actor)
                        if outside is not None:
                            self.assertTrue(signature(outside) == before)
                        self.restore(target, kind, outside)
                        for path in ordered[1:]:
                            self.refuse_damaged(request, actor, path, kind)

    def test_empty_staging_set_allows_bootstrap_and_all_owner_mutations(self) -> None:
        for suffix in ("alpha", "beta"):
            with self.subTest(project=suffix):
                self.project(f"empty-{suffix}")
                request, actor = self.prepared("workflow.open", suffix)
                self.succeed_preserving(request, actor, [])
                operator = Path(self.state()["receipts"][request["request_id"]]["response"]["result"]["actor_file"])
                _, _, owner, operator = self.acquire(operator, mode="manual", session=f"native-{suffix}")
                _, _, operator = self.clear(owner, request_id=f"release-{suffix}")
                _, _, _, operator = self.acquire(operator, mode="supervised", session=f"next-{suffix}",
                                                  request_id=f"reacquire-{suffix}")
                self.clear(operator, "owner.recover", request_id=f"recover-{suffix}")
                self.assertIsNone(self.state()["owner"])
                self.assertFalse((private_path(self.root) / "credential-intent.json").exists())

    def test_retained_historical_final_credentials_do_not_consume_staging_file_budget(self) -> None:
        _, _, operator = self.bootstrap()
        historical = []
        for index in range(FILE_LIMIT + 2):
            _, _, owner, operator = self.acquire(
                operator, session=f"history-session-{index}", request_id=f"history-acquire-{index}")
            content = owner.read_bytes()
            _, _, operator = self.clear(owner, request_id=f"history-release-{index}")
            # Retain the exact returned final path and bytes if revocation
            # removes that file. No staging filename is invented here.
            if not owner.exists():
                owner.write_bytes(content)
                owner.chmod(0o600)
            self.assertTrue(owner.read_bytes() == content)
            historical.append(owner)
        self.assertGreater(len(set(historical)), FILE_LIMIT)
        before = {path: signature(path) for path in historical}
        request = self.request(operator, "owner.acquire", "after-history",
                               {"mode": "supervised", "native_session_id": "history-final"})
        self.succeed_preserving(request, operator, historical)
        self.assertTrue({path: signature(path) for path in historical} == before)


if __name__ == "__main__":
    unittest.main()
