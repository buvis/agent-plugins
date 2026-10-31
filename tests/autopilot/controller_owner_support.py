"""Owner test helpers using only the public CLI and private JSON artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import stat
import sys
from pathlib import Path

from controller_cli_support import (
    CREDENTIAL_KEYS, MAIN, ControllerCLITest, canonical, cli, fresh_request,
    private_path, project_id, strict_json, tree,
)

NORMAL_BYTES = 14680064
STATE_BYTES = 16777216


def state_bytes(state: dict) -> bytes:
    return (json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def credential(path: Path) -> dict:
    return strict_json(path.read_bytes())


def operation(root: Path, actor: Path, name: str, request_id: str,
              revision: int, payload: dict | None = None) -> dict:
    value = credential(actor)
    request = fresh_request(root, request_id)
    request.update(operation=name, expected_revision=revision,
                   workflow_id=value["workflow_id"], actor_id=value["actor_id"],
                   lease_epoch=value["lease_epoch"], payload=payload or {})
    return request


def hashes(root: Path) -> dict:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def seed_receipts(state: dict, root: Path, count: int) -> dict:
    value = copy.deepcopy(state)
    first = next(iter(value["receipts"].values()))
    while len(value["receipts"]) < count:
        name = f"capacity-history-{len(value['receipts']):04d}"
        receipt = copy.deepcopy(first)
        receipt["request_digest"] = hashlib.sha256(
            canonical(fresh_request(root, name))).hexdigest()
        value["receipts"][name] = receipt
    return value


def seed_bytes(state: dict, root: Path, target: int) -> dict:
    value = copy.deepcopy(state)
    first = copy.deepcopy(next(iter(value["receipts"].values())))
    sample = copy.deepcopy(first)
    sample["response"]["result"]["actor_file"] = "/" + "p" * 54000
    before = len(state_bytes(value))
    value["receipts"]["byte-size-sample"] = sample
    increment = len(state_bytes(value)) - before + 2
    del value["receipts"]["byte-size-sample"]
    count = max(0, (target - before - 3000) // increment)
    for _ in range(count):
        name = f"byte-history-{len(value['receipts']):04d}"
        receipt = copy.deepcopy(sample)
        receipt["request_digest"] = hashlib.sha256(
            canonical(fresh_request(root, name))).hexdigest()
        value["receipts"][name] = receipt
    name = f"byte-history-{len(value['receipts']):04d}"
    value["receipts"][name] = copy.deepcopy(first)
    value["receipts"][name]["request_digest"] = hashlib.sha256(
        canonical(fresh_request(root, name))).hexdigest()
    result = value["receipts"][name]["response"]["result"]
    result["actor_file"] += "x" * (target - len(state_bytes(value)))
    if len(state_bytes(value)) != target:
        raise AssertionError("capacity fixture does not meet its exact byte target")
    return value


# This subprocess wraps OS boundaries, never a controller module or private API.
CRASH_SCRIPT = r'''
import json, os, runpy, stat, sys
from pathlib import Path
main, project, boundary, target = sys.argv[1:5]
target = int(target)
root = Path(project) / ".autopilot" / "controller"
actors = root / "actors"
intent = root / "credential-intent.json"
original_files = {p.resolve() for p in actors.iterdir() if p.is_file()}
real_fsync, real_replace = os.fsync, os.replace

def pending():
    return intent.exists()

def published():
    try:
        return json.loads((root / "state.json").read_bytes())["revision"] == target
    except (OSError, ValueError, KeyError):
        return False

def destination(value, directory):
    path = Path(os.fsdecode(value))
    if path.is_absolute() or directory is None:
        return path.resolve()
    identity = os.fstat(directory)
    for parent in (root, actors, root.parent, root.parent.parent):
        info = parent.stat()
        if (info.st_dev, info.st_ino) == (identity.st_dev, identity.st_ino):
            return parent / path
    return None

def fsync(fd):
    real_fsync(fd)
    info = os.fstat(fd)
    if stat.S_ISDIR(info.st_mode):
        if boundary == "intent_dir_fsynced" and pending():
            os._exit(87)
        if boundary == "cleanup_dir_fsynced" and published() and not pending():
            os._exit(87)
    elif boundary == "stage_fsynced" and not pending() and not published():
        for path in actors.iterdir():
            candidate = path.stat()
            if path.resolve() not in original_files and (
                    candidate.st_dev, candidate.st_ino) == (info.st_dev, info.st_ino):
                os._exit(87)

def replace(source, dest, *args, **kwargs):
    real_replace(source, dest, *args, **kwargs)
    path = destination(dest, kwargs.get("dst_dir_fd"))
    if boundary == "state_published" and path == root / "state.json" and published():
        os._exit(87)
    if path is None or path.parent != actors:
        return
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError):
        return
    label = value.get("role", "") + "_credential_published"
    if boundary == label and value.get("lease_epoch") == target:
        os._exit(87)

os.fsync, os.replace = fsync, replace
sys.argv = [main] + sys.argv[5:]
sys.path.insert(0, str(Path(main).parent))
runpy.run_path(main, run_name="__main__")
'''


class OwnerCLITest(ControllerCLITest):
    def bootstrap(self) -> tuple[dict, dict, Path]:
        request, opened = self.open()
        return request, opened, Path(opened["result"]["actor_file"])

    def request(self, actor: Path, name: str, request_id: str,
                payload: dict | None = None) -> dict:
        return operation(self.root, actor, name, request_id,
                         self.state()["revision"], payload)

    def acquire(self, operator: Path, mode: str = "manual",
                session: str = "session-alpha", request_id: str = "acquire-first"
                ) -> tuple[dict, dict, Path, Path]:
        request = self.request(operator, "owner.acquire", request_id,
                               {"mode": mode, "native_session_id": session})
        response = self.response(self.apply(request, operator),
                                 revision=request["expected_revision"] + 1)
        self.assert_transition(request, response, operator)
        result = response["result"]
        return (request, response, Path(result["actor_file"]),
                Path(result["operator_actor_file"]))

    def clear(self, actor: Path, name: str = "owner.release",
              request_id: str = "clear-first") -> tuple[dict, dict, Path]:
        payload = ({"reason": "Explicit reconciliation alpha", "reconciled_job_ids": []}
                   if name == "owner.recover" else {})
        request = self.request(actor, name, request_id, payload)
        response = self.response(self.apply(request, actor),
                                 revision=request["expected_revision"] + 1)
        self.assert_transition(request, response, actor)
        return request, response, Path(response["result"]["operator_actor_file"])

    def retain(self, actor: Path, name: str) -> Path:
        path = self.base / name
        shutil.copyfile(actor, path)
        path.chmod(0o600)
        return path

    def reject_unchanged(self, request: dict, actor: Path | None,
                         error: str, root: Path | None = None) -> None:
        before = tree(private_path(self.root))
        completed = self.apply(request, actor, root=root)
        self.response(completed, error, revision=self.state()["revision"])
        self.assertTrue(tree(private_path(self.root)) == before,
                        "rejection changed private evidence")

    def assert_transition(self, request: dict, response: dict,
                          authorizer: Path) -> None:
        state = self.state()
        self.assertEqual(state["revision"], response["revision"])
        self.assertEqual(state["lease_epoch"], response["result"]["lease_epoch"])
        self.assertEqual(state["lease_epoch"], request["lease_epoch"] + 1)
        self.assertEqual(state["workflow"], {"batch": None, "work": None,
                         "tasks": [], "review": {"cap": 2}, "recovery": None,
                         "jobs": []})
        receipt = state["receipts"][request["request_id"]]
        self.assertEqual(receipt["request_digest"], hashlib.sha256(canonical(request)).hexdigest())
        self.assertEqual(receipt["response"], response)
        self.assertEqual(receipt["authorizing_actor"]["actor_id"], request["actor_id"])
        self.assertEqual(receipt["authorizing_actor"]["lease_epoch"], request["lease_epoch"])
        self.assertLessEqual(len(canonical(response)), 65536)
        operator = Path(response["result"]["operator_actor_file"])
        self.assert_current_credential(operator, "operator", state)
        if request["operation"] == "owner.acquire":
            self.assertEqual(set(response["result"]),
                             {"actor_id", "actor_file", "lease_epoch", "operator_actor_file"})
            owner = Path(response["result"]["actor_file"])
            self.assert_current_credential(owner, "owner", state)
            self.assertEqual(state["owner"], {
                "actor_id": response["result"]["actor_id"],
                "lease_epoch": response["result"]["lease_epoch"],
                **request["payload"]})
            self.assertEqual(set(state["actors"]),
                             {credential(operator)["actor_id"], credential(owner)["actor_id"]})
        else:
            self.assertEqual(set(response["result"]),
                             {"actor_id", "operator_actor_file", "lease_epoch"})
            self.assertIsNone(state["owner"])
            self.assertEqual(set(state["actors"]), {credential(operator)["actor_id"]})
        self.assert_private()

    def assert_current_credential(self, path: Path, role: str, state: dict) -> None:
        value = credential(path)
        self.assertEqual(set(value), CREDENTIAL_KEYS)
        self.assertTrue(path.is_absolute())
        self.assertTrue(path.is_relative_to(private_path(self.root) / "actors"))
        self.assertEqual(value["role"], role)
        self.assertEqual(value["project_id"], project_id(self.root))
        self.assertEqual(value["workflow_id"], state["workflow_id"])
        self.assertEqual(value["lease_epoch"], state["lease_epoch"])
        expected = {key: item for key, item in value.items() if key != "secret"}
        expected["secret_digest"] = hashlib.sha256(value["secret"].encode()).hexdigest()
        self.assertTrue(state["actors"][value["actor_id"]] == expected,
                        "published credential does not match its descriptor")
        self.assertNotIn(value["secret"], json.dumps(state))
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def snapshot(self) -> dict:
        before = tree(private_path(self.root))
        result = cli(["--json", "snapshot", "--project-root", str(self.root)], cwd=self.base)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertLessEqual(len(result.stdout), STATE_BYTES)
        response = self.response(result, revision=self.state()["revision"])
        value = response["result"]
        self.assertTrue(tree(private_path(self.root)) == before,
                        "snapshot changed private evidence")
        encoded = json.dumps(value)
        self.assertNotIn('"secret"', encoded)
        self.assertNotIn('"secret_digest"', encoded)
        self.assertNotIn('"request_digest"', encoded)
        for key in ("project_id", "workflow_id", "lease_epoch", "owner"):
            self.assertEqual(value[key], self.state()[key])
        return value

    def seed(self, state: dict) -> None:
        sys.path.insert(0, str(MAIN.parent))
        from autopilot_state.schema import validate_state
        validate_state(state)
        path = private_path(self.root) / "state.json"
        path.write_bytes(state_bytes(state))
        path.chmod(0o600)

    def crash(self, request: dict, actor: Path, boundary: str):
        prefix = [sys.executable, "-c", CRASH_SCRIPT, str(MAIN), str(self.root),
                  boundary, str(request["expected_revision"] + 1)]
        completed = self.apply(request, actor, prefix=prefix)
        self.assertEqual(completed.returncode, 87,
                         f"OS crash boundary was not reached: {boundary}")
        self.assertEqual(completed.stdout, b"")
        return completed
