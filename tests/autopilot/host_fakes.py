"""Controller-seam and host-adapter doubles plus job fixtures for autopilot tests.

The package ships no ControllerSeam implementation (design §4), so FakeSeam
and TripwireSeam live here, where production code cannot import them.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

hosts = importlib.import_module("hosts")

POLICY = ROOT / "plugins" / "autopilot" / "contracts" / "review-policy-v1.json"
WORKFLOW = ROOT / "plugins" / "autopilot" / "contracts" / "controller" / "workflow-v1.json"
LINEAGE_DIR = Path("docs/dev/tmp/autopilot/jobs")
BASE_INPUTS = {
    "docs/dev/tmp/a.diff": b"diff --git a/x b/x\n+alpha\n",
    "docs/dev/project-management/prds/wip/p.md": b"# PRD 00014\n\nBody.\n",
}
DIFF = {"kind": "diff", "path": "docs/dev/tmp/a.diff"}
PRD = {"kind": "prd", "path": "docs/dev/project-management/prds/wip/p.md"}


class FakeSeam:
    """Records submitted intents, answers evaluate_guard from fixture rules
    ({duty: (allowed, reason)}) and read_facts from fixture facts
    ({duty: facts}). Never launches anything."""

    def __init__(self, *, guard_rules: dict, facts: dict | None = None) -> None:
        self.guard_rules = guard_rules
        self.facts = facts
        self.submitted_intents: list = []
        self.fact_reads: list = []

    def submit_job(self, intent: dict) -> dict:
        self.submitted_intents.append(intent)
        return {
            "accepted": True,
            "job_ref": f"fake-job-{len(self.submitted_intents)}",
            "error": None,
        }

    def evaluate_guard(self, duty: str, context: dict) -> dict:
        allowed, reason = self.guard_rules.get(duty, (True, None))
        return {"allowed": allowed, "reason": reason}

    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict:
        self.fact_reads.append((duty, session, project_root))
        if self.facts is None or duty not in self.facts:
            return {}
        return copy.deepcopy(self.facts[duty])


class TripwireSeam:
    """Fails the test on any seam call, so a path that must not reach the
    controller is proven not to."""

    def __init__(self) -> None:
        self.calls: list = []

    def submit_job(self, intent: dict) -> dict:
        self.calls.append("submit_job")
        raise AssertionError("submit_job reached")

    def evaluate_guard(self, duty: str, context: dict) -> dict:
        self.calls.append("evaluate_guard")
        raise AssertionError("evaluate_guard reached")

    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict:
        self.calls.append("read_facts")
        raise AssertionError("read_facts reached")


class ScriptedSeam:
    """submit_job returns a caller-chosen reply (or raises it, when it is an
    exception) and records every intent it received."""

    def __init__(self, reply: object) -> None:
        self.reply = reply
        self.submitted_intents: list = []

    def submit_job(self, intent: dict) -> object:
        self.submitted_intents.append(intent)
        if isinstance(self.reply, BaseException):
            raise self.reply
        return copy.deepcopy(self.reply)

    def evaluate_guard(self, duty: str, context: dict) -> dict:
        raise AssertionError("request_job must not evaluate guards")

    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict:
        raise AssertionError("request_job must not read facts")


def input_kinds() -> tuple[str, ...]:
    return tuple(json.loads(POLICY.read_text(encoding="utf-8"))["input_kinds"])


def controller_error_codes() -> tuple[str, ...]:
    document = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    return tuple(document["x-controller"]["error_codes"])


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def native_session(host_id: str = "claude", session_id: str = "requester-1",
                   source: str = "environment") -> object:
    return hosts.NativeSession(host_id=host_id, session_id=session_id, source=source)


def seed(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def make_project(raw: str) -> Path:
    root = Path(raw) / "project"
    root.mkdir()
    root = root.resolve()
    for relative, data in BASE_INPUTS.items():
        seed(root, relative, data)
    return root


def job_fields(root: Path, **override) -> dict:
    fields = {
        "job_id": "alice-review",
        "role_id": "consensus-reviewer",
        "host_id": "codex",
        "tier": "opus",
        "effort": "high",
        "inputs": [{"kind": "diff", "path": "docs/dev/tmp/a.diff"}],
        "excluded_input_kinds": [],
        "requester": native_session(),
        "ancestry": (),
        "project_root": root,
    }
    return {**fields, **override}


def build(root: Path, **override) -> object:
    jobs = importlib.import_module("jobs")
    return jobs.build_job_request(**job_fields(root, **override))


def canonical_request_id(payload: dict) -> str:
    body = {key: value for key, value in payload.items() if key != "request_id"}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)
    return sha256_hex(text.encode("utf-8"))


def record_path(root: Path, host_id: str, session_id: str) -> Path:
    name = f"{host_id}-{sha256_hex(session_id.encode('utf-8'))}.json"
    return root / LINEAGE_DIR / name


def files_under(root: Path) -> set[str]:
    """Every file and symlink under root, as root-relative POSIX paths."""
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_symlink() or path.is_file()
    }


class ProjectCase(unittest.TestCase):
    """A fresh temporary project root with BASE_INPUTS seeded per test."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name).resolve()
        self.root = make_project(temp.name)

    def assert_refused(self, code: str, call, *args, **kwargs) -> BaseException:
        jobs = importlib.import_module("jobs")
        with self.assertRaises(jobs.JobRefused) as caught:
            call(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception


def install_adapter(case, host_id: str, **attrs) -> types.ModuleType:
    """Serve a fake adapter module for host_id through the import system, so
    hosts.adapter(host_id) returns it however jobs.py reaches the adapter."""
    module = types.ModuleType(f"fake_{host_id}_adapter")
    for name, value in attrs.items():
        setattr(module, name, value)
    patcher = mock.patch.dict(sys.modules, {hosts.ADAPTERS[host_id]: module})
    patcher.start()
    case.addCleanup(patcher.stop)
    return module
