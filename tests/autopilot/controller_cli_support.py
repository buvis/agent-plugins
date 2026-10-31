"""Public CLI helpers; no controller implementation imports."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "plugins" / "autopilot" / "controller" / "main.py"
CONTRACT = ROOT / "plugins" / "autopilot" / "contracts" / "controller"
RESPONSE_KEYS = {"ok", "revision", "result", "error_code", "retryable"}
CREDENTIAL_KEYS = {"actor_id", "project_id", "workflow_id", "role",
                   "lease_epoch", "native_session_id", "secret"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def project_id(root: Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()


def private_path(root: Path) -> Path:
    return root / ".autopilot" / "controller"


def fresh_request(root: Path, request_id: str = "open-first") -> dict:
    return {"protocol_major": 1, "operation": "workflow.open",
            "request_id": request_id, "expected_revision": 0,
            "project_id": project_id(root), "workflow_id": None,
            "actor_id": None, "job_id": None, "lease_epoch": None, "payload": {}}


def existing_request(root: Path, opened: dict, request_id: str,
                     revision: int = 0) -> dict:
    request = fresh_request(root, request_id)
    request.update(workflow_id=opened["workflow_id"], actor_id=opened["actor_id"],
                   lease_epoch=opened["lease_epoch"], expected_revision=revision)
    return request


def cli(arguments: list[str], cwd: Path | None = None,
        prefix: list[str] | None = None) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(MAIN)] if prefix is None else prefix
    return subprocess.run(argv + arguments, cwd=cwd, capture_output=True,
                          timeout=30, check=False)


def tree(root: Path) -> dict:
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        kind = stat.S_IFMT(info.st_mode)
        content = (os.readlink(path) if path.is_symlink() else
                   path.read_bytes() if stat.S_ISREG(info.st_mode) else None)
        result[str(path.relative_to(root))] = (kind, stat.S_IMODE(info.st_mode),
                                             info.st_nlink, content)
    return result


class ControllerCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        self.serial = 0

    def write_request(self, value: object, raw: bytes | None = None) -> Path:
        self.serial += 1
        path = self.base / f"request-{self.serial}.json"
        path.write_bytes(canonical(value) if raw is None else raw)
        path.chmod(0o600)
        return path

    def apply(self, request: object, actor: Path | None = None,
              raw: bytes | None = None, root: Path | None = None,
              prefix: list[str] | None = None) -> subprocess.CompletedProcess:
        path = self.write_request(request, raw)
        arguments = ["--json", "apply", "--project-root", str(root or self.root),
                     "--request", str(path)]
        if actor is not None:
            arguments += ["--actor-file", str(actor)]
        return cli(arguments, cwd=self.base, prefix=prefix)

    def response(self, completed: subprocess.CompletedProcess,
                 error: str | None = None, revision: int | None = None) -> dict:
        self.assertEqual(completed.returncode, 0 if error is None else 1,
                         completed.stderr.decode("utf-8", errors="replace"))
        self.assertLessEqual(len(completed.stdout), 16777216)
        response = json.loads(completed.stdout)
        self.assertEqual(set(response), RESPONSE_KEYS)
        self.assertIs(response["ok"], error is None)
        self.assertEqual(response["error_code"], error)
        self.assertIs(response["retryable"], error == "revision_conflict")
        self.assertIs(type(response["revision"]), int)
        if revision is not None:
            self.assertEqual(response["revision"], revision)
        if error is not None:
            self.assertIsNone(response["result"])
        return response

    def open(self, request_id: str = "open-first") -> tuple[dict, dict]:
        request = fresh_request(self.root, request_id)
        response = self.response(self.apply(request), revision=0)
        self.assert_open_consistent(request, response)
        return request, response

    def state(self) -> dict:
        return json.loads((private_path(self.root) / "state.json").read_bytes())

    def assert_open_consistent(self, request: dict, response: dict) -> None:
        result = response["result"]
        self.assertEqual(set(result), {"workflow_id", "actor_id", "actor_file",
                                       "lease_epoch"})
        self.assertEqual(result["lease_epoch"], 0)
        actor_file = Path(result["actor_file"])
        self.assertTrue(actor_file.is_absolute())
        self.assertTrue(actor_file.is_relative_to(private_path(self.root) / "actors"))
        credential = json.loads(actor_file.read_bytes())
        self.assertEqual(set(credential), CREDENTIAL_KEYS)
        self.assertEqual(credential["role"], "operator")
        self.assertIsNone(credential["native_session_id"])
        for key in ("actor_id", "workflow_id", "lease_epoch"):
            self.assertEqual(credential[key], result[key])
        self.assertEqual(credential["project_id"], project_id(self.root))
        self.assertRegex(credential["secret"], r"^[A-Za-z0-9_-]{43}$")
        state = self.state()
        self.assertEqual(set(state), {"schema_version", "revision", "project_id",
                                     "workflow_id", "repo_root", "lease_epoch",
                                     "owner", "actors", "receipts", "workflow"})
        self.assertEqual(state["workflow_id"], result["workflow_id"])
        self.assertEqual(state["project_id"], project_id(self.root))
        self.assertEqual(state["repo_root"], str(self.root))
        self.assertEqual(state["revision"], response["revision"])
        self.assertIsNone(state["owner"])
        self.assertEqual(state["lease_epoch"], 0)
        self.assertEqual(state["workflow"], {"batch": None, "work": None,
                         "tasks": [], "review": {"cap": 2}, "recovery": None,
                         "jobs": []})
        descriptor = state["actors"][result["actor_id"]]
        self.assertEqual(set(state["actors"]), {result["actor_id"]})
        self.assertEqual(descriptor, {key: value for key, value in credential.items()
                                     if key != "secret"} | {"secret_digest":
                         hashlib.sha256(credential["secret"].encode()).hexdigest()})
        receipt = state["receipts"][request["request_id"]]
        self.assertEqual(receipt, {"request_digest": hashlib.sha256(
            canonical(request)).hexdigest(), "authorizing_actor": descriptor,
            "response": response})
        self.assertNotIn(credential["secret"], json.dumps(state))
        self.assertNotIn(credential["secret"], json.dumps(response))

    def assert_private(self) -> None:
        for path in [self.root / ".autopilot", private_path(self.root),
                     private_path(self.root) / "actors"]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
        for path in private_path(self.root).rglob("*"):
            if path.is_file():
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_nlink, 1)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
