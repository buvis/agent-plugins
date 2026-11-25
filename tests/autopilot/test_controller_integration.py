"""Manual-session fake-host lifecycle, end to end through protocol.apply.

Every controller call below is one independent `protocol.apply(root,
request_file, actor_file)` call. Nothing is carried between calls in memory:
each request is rebuilt from what a fresh session can read on disk, the actor
credential file and the public snapshot revision.
"""

from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

from controller_cli_support import ControllerCLITest, fresh_request, private_path, tree

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import files, lifecycle, protocol

JOBS_SOURCE = CONTROLLER / "autopilot_state" / "jobs.py"
SPAWN_MODULES = {"subprocess", "os", "posix", "pty", "multiprocessing"}
BUCKETS = ("backlog", "wip", "hold", "done")
PRD = "00002-b.md"
EXIT = {"outcome": "succeeded", "native_session_id": "session-gamma"}


def prd_text(eligibility: str | None = None) -> str:
    line = "" if eligibility is None else f"eligibility: {eligibility}\n"
    return f"---\n{line}---\n# PRD\n"


def make_buckets(root: Path, backlog: dict | None = None) -> None:
    for name in BUCKETS:
        (root / files.PRD_ROOT / name).mkdir(parents=True)
    for name, text in (backlog or {}).items():
        (root / files.PRD_ROOT / "backlog" / name).write_text(text)


def bucket_of(root: Path, prd: str) -> list[str]:
    return [name for name in BUCKETS if (root / files.PRD_ROOT / name / prd).exists()]


def record(task_id: str, *depends: str) -> dict:
    return {"id": task_id, "subject": "work", "status": "pending", "depends_on": list(depends)}


def spec(job_id: str, *depends: str) -> dict:
    """A complete caller spec: every key in schema.JOB_SPEC_KEYS is required."""
    return {"job_id": job_id, "role": "builder", "depends_on": list(depends),
            "input_digests": ["a" * 64], "isolation": "worktree", "tier": "opus",
            "effort": "high", "source_digest": "b" * 64, "resource_digest": "c" * 64,
            "permitted_operations": ["read", "write"]}


class ManualSessionIntegrationTest(ControllerCLITest):
    """A fake host drives the controller one independent apply() call at a time."""

    def setUp(self) -> None:
        super().setUp()
        make_buckets(self.root, backlog={PRD: prd_text()})

    # -- a fresh session: everything comes from disk, nothing from memory -----

    def open_workflow(self) -> Path:
        opened = protocol.apply(self.root, self.write_request(fresh_request(self.root)), None)
        self.assertTrue(opened["ok"])
        return Path(opened["result"]["actor_file"])

    def envelope(self, actor_file: Path, operation: str, request_id: str,
                 payload: dict) -> dict:
        credential = json.loads(actor_file.read_bytes())
        revision = protocol.snapshot(self.root)["revision"]
        return {"protocol_major": 1, "operation": operation, "request_id": request_id,
                "expected_revision": revision, "project_id": credential["project_id"],
                "workflow_id": credential["workflow_id"], "actor_id": credential["actor_id"],
                "job_id": None, "lease_epoch": credential["lease_epoch"], "payload": payload}

    def submit(self, request: dict, actor_file: Path) -> dict:
        return protocol.apply(self.root, self.write_request(request), actor_file)

    def call(self, actor_file: Path, operation: str, payload: dict,
             request_id: str | None = None) -> tuple[dict, dict]:
        request = self.envelope(actor_file, operation,
                                request_id or f"{operation}-{self.serial + 1}", payload)
        response = self.submit(request, actor_file)
        state = self.state()
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["revision"], state["revision"])
        self.assertEqual(state["receipts"][request["request_id"]]["response"], response)
        return request, response

    def refuse(self, actor_file: Path, operation: str, payload: dict,
               code: str = "rejected_evidence") -> None:
        request = self.envelope(actor_file, operation, f"refused-{self.serial + 1}", payload)
        before = tree(private_path(self.root))
        with self.assertRaises(protocol.ProtocolError) as caught:
            self.submit(request, actor_file)
        self.assertEqual(caught.exception.code, code)
        self.assertTrue(tree(private_path(self.root)) == before,
                        f"refused {operation} changed private state")

    def acquire(self, operator: Path, session: str) -> Path:
        _, acquired = self.call(operator, "owner.acquire",
                                {"mode": "manual", "native_session_id": session})
        owner = self.state()["owner"]
        self.assertEqual((owner["mode"], owner["native_session_id"]), ("manual", session))
        return Path(acquired["result"]["actor_file"])

    # -- 1. manual_session_handoff ------------------------------------------

    def test_manual_session_handoff(self) -> None:
        operator = self.open_workflow()
        alpha = self.acquire(operator, "session-alpha")
        _, entered = self.call(alpha, "prd.enter", {"prds": [PRD]})
        self.assertEqual(entered["result"], {"prd": PRD, "source": "backlog"})
        self.assertEqual(bucket_of(self.root, PRD), ["wip"])
        self.call(alpha, "task.replace", {"tasks": [record("a"), record("b", "a")],
                                          "allow_expansion": False})
        self.call(alpha, "task.start", {"id": "a"})
        self.call(alpha, "task.finish", {"id": "a", "outcome": "completed"})
        self.call(alpha, "owner.release", {})
        self.assertIsNone(self.state()["owner"])

        # Session alpha is gone; a new manual session resumes from disk alone.
        self.assertEqual(lifecycle.resume_target(self.state()),
                         "continue build at first non-completed task b")
        beta = self.acquire(operator, "session-beta")
        self.call(beta, "task.start", {"id": "b"})
        _, finished = self.call(beta, "task.finish", {"id": "b", "outcome": "completed"})
        self.assertEqual(finished["result"], {"task_id": "b", "status": "completed",
                                              "attempts": 0})
        self.assertEqual(lifecycle.resume_target(self.state()),
                         "all tasks done -> review gate")
        for phase, next_phase, outcome in (("build", "review", "tasks_done"),
                                           ("review", "review", "rework"),
                                           ("review", "done", "converged")):
            _, handed = self.call(beta, "phase.handoff", {"phase": phase,
                                                          "next_phase": next_phase,
                                                          "outcome": outcome})
            self.assertEqual(handed["result"], {"phase": next_phase, "next_phase": next_phase})
        work = self.state()["workflow"]["work"]
        self.assertEqual((work["phase"], work["completed_phases"]), ("done", ["review"]))
        _, completed = self.call(beta, "prd.complete", {})
        self.assertEqual(completed["result"], {"prd": PRD})

        self.assertEqual(bucket_of(self.root, PRD), ["done"])
        workflow = self.state()["workflow"]
        self.assertEqual(workflow["batch"]["completed_prds"], [PRD])
        self.assertIsNone(workflow["work"])
        self.assertIsNone(workflow["recovery"])

    # -- 2. false_success_no_advance ----------------------------------------

    def assert_complete_refused(self, actor_file: Path) -> None:
        self.refuse(actor_file, "prd.complete", {})
        self.assertEqual(bucket_of(self.root, PRD), ["wip"])
        self.assertEqual(self.state()["workflow"]["batch"]["completed_prds"], [])

    def test_false_success_no_advance(self) -> None:
        operator = self.open_workflow()
        self.call(operator, "prd.enter", {"prds": [PRD]})
        self.assert_complete_refused(operator)  # phase build, nothing reviewed

        self.call(operator, "phase.handoff", {"phase": "build", "next_phase": "",
                                              "outcome": "drained"})
        work = self.state()["workflow"]["work"]
        self.assertEqual((work["phase"], work["completed_phases"]), ("done", []))
        self.assert_complete_refused(operator)  # phase done, but review never ran

        self.call(operator, "phase.handoff", {"phase": "done", "next_phase": "build",
                                              "outcome": "more_prds"})
        self.call(operator, "phase.handoff", {"phase": "build", "next_phase": "review",
                                              "outcome": "tasks_done"})
        self.assertEqual(self.state()["workflow"]["work"]["phase"], "review")
        self.assert_complete_refused(operator)  # review entered, not converged

        # The CLI entry point surfaces the same refusal as a failed envelope.
        request = self.envelope(operator, "prd.complete", "complete-cli", {})
        before = tree(private_path(self.root))
        envelope = protocol.execute("apply", self.root, self.write_request(request), operator)
        self.assertEqual(envelope, protocol.response(revision=self.state()["revision"],
                                                     error="rejected_evidence"))
        self.assertTrue(tree(private_path(self.root)) == before)
        self.assertEqual(bucket_of(self.root, PRD), ["wip"])
        self.assertEqual(self.state()["workflow"]["batch"]["completed_prds"], [])

    # -- 3. drained_vs_ineligible -------------------------------------------

    def test_drained_vs_ineligible(self) -> None:
        empty = self.base / "empty"
        make_buckets(empty)
        before = tree(empty)
        self.assertEqual(lifecycle.select_eligible(empty),
                         {"prd": None, "source": "drained", "skipped": []})
        self.assertTrue(tree(empty) == before, "select_eligible wrote to an empty root")

        blocked = self.base / "blocked"
        make_buckets(blocked, backlog={"00003-c.md": prd_text('"exit 1"'),
                                       "00004-d.md": prd_text("exit 7"),
                                       "00005-e.md": prd_text("test -f missing.md")})
        before = tree(blocked)
        result = lifecycle.select_eligible(blocked)
        self.assertEqual((result["prd"], result["source"]), (None, "drained"))
        self.assertEqual([{key: entry[key] for key in ("prd", "command", "exit_code", "note")}
                          for entry in result["skipped"]], [
            {"prd": "00003-c.md", "command": "exit 1", "exit_code": 1, "note": ""},
            {"prd": "00004-d.md", "command": "exit 7", "exit_code": 7, "note": ""},
            {"prd": "00005-e.md", "command": "test -f missing.md", "exit_code": 1, "note": ""},
        ])
        self.assertTrue(all(entry["at"].endswith("Z") for entry in result["skipped"]))
        self.assertTrue(tree(blocked) == before, "select_eligible moved or wrote a file")
        self.assertFalse((blocked / ".autopilot").exists())

    # -- 4. job claim exclusivity and record_exit replay through apply -------

    def test_job_claim_exclusive_and_record_exit_replay_through_apply(self) -> None:
        operator = self.open_workflow()
        gamma = self.acquire(operator, "session-gamma")
        owner_id = json.loads(gamma.read_bytes())["actor_id"]
        _, planned = self.call(operator, "job.plan",
                               {"jobs": [spec("build"), spec("review", "build")]})
        self.assertEqual(planned["result"], {"job_count": 2})
        _, claimed = self.call(gamma, "job.claim", {"job_id": "build"})
        self.assertEqual(claimed["result"], {"job_id": "build", "claimed_by": owner_id,
                                             "claim_epoch": 1})
        self.refuse(operator, "job.claim", {"job_id": "build"})
        self.refuse(gamma, "job.claim", {"job_id": "build"})

        request, exited = self.call(gamma, "job.record_exit",
                                    {"job_id": "build", "exit_fact": EXIT})
        self.assertEqual(exited["result"], claimed["result"])
        rows = self.state()["workflow"]["jobs"]
        self.assertEqual([row["exit_fact"] for row in rows], [EXIT, None])

        # Replaying the identical request returns its receipt and writes nothing.
        before = tree(private_path(self.root))
        self.assertEqual(self.submit(request, gamma), exited)
        self.assertTrue(tree(private_path(self.root)) == before, "replay wrote state")

        # A fresh request carrying the same exit fact leaves every job row unchanged.
        self.call(gamma, "job.record_exit", {"job_id": "build", "exit_fact": dict(EXIT)})
        self.assertEqual(self.state()["workflow"]["jobs"], rows)

        self.refuse(gamma, "job.record_exit",
                    {"job_id": "build", "exit_fact": {**EXIT, "outcome": "failed"}})
        self.refuse(operator, "job.record_exit", {"job_id": "build", "exit_fact": EXIT})
        self.assertEqual(self.state()["workflow"]["jobs"], rows)

    def test_jobs_module_imports_no_spawn(self) -> None:
        source = ast.parse(JOBS_SOURCE.read_text(encoding="utf-8"))
        modules, attributes = set(), set()
        for node in ast.walk(source):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.add((node.module or "").split(".")[0])
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
        self.assertIn("policy", modules)  # control: the walk sees real imports
        self.assertFalse(modules & SPAWN_MODULES, modules & SPAWN_MODULES)
        spawning = {name for name in attributes
                    if name.startswith(("exec", "fork", "spawn", "posix_spawn"))}
        self.assertFalse(spawning, spawning)


if __name__ == "__main__":
    unittest.main()
