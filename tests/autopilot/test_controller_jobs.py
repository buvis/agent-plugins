"""Pure job reducers: deterministic plan, exclusive claim, replay-safe exit, no spawn."""

from __future__ import annotations

import ast
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import jobs, policy, protocol

JOBS_SOURCE = CONTROLLER / "autopilot_state" / "jobs.py"
SPAWN_MODULES = {"subprocess", "os", "posix", "pty", "multiprocessing"}


def spec(job_id: str, *depends: str) -> dict:
    return {"job_id": job_id, "role": "builder", "depends_on": list(depends),
            "input_digests": ["a" * 64], "isolation": "worktree", "tier": "opus",
            "effort": "high"}


def claimed(job_id: str = "build") -> list[dict]:
    return jobs.claim(jobs.plan([], [spec(job_id)]), job_id, "owner-1", 3)


EXIT = {"outcome": "succeeded", "native_session_id": "session-1"}


class PlanTest(unittest.TestCase):
    def test_appends_one_unclaimed_row_per_spec(self) -> None:
        existing = jobs.plan([], [spec("build")])
        result = jobs.plan(existing, [spec("review", "build"), spec("docs")])
        self.assertEqual(result[0], existing[0])
        self.assertEqual(result[1:], [
            {"spec": spec("review", "build"), "claimed_by": None, "claim_epoch": None,
             "exit_fact": None},
            {"spec": spec("docs"), "claimed_by": None, "claim_epoch": None, "exit_fact": None},
        ])

    def test_leaves_the_input_jobs_list_untouched(self) -> None:
        existing = jobs.plan([], [spec("build")])
        before = copy.deepcopy(existing)
        jobs.plan(existing, [spec("review", "build")])
        self.assertEqual(existing, before)

    def test_rejects_a_job_id_cycle(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "cycle"):
            jobs.plan([], [spec("a", "b"), spec("b", "a")])

    def test_rejects_a_duplicate_job_id_in_one_plan(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "duplicate"):
            jobs.plan([], [spec("a"), spec("a")])

    def test_rejects_a_job_id_already_planned(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "duplicate"):
            jobs.plan(jobs.plan([], [spec("a")]), [spec("a")])

    def test_rejects_an_unknown_dependency(self) -> None:
        with self.assertRaisesRegex(policy.InvalidPlan, "unknown"):
            jobs.plan([], [spec("a", "ghost")])

    def test_job_plan_stable(self) -> None:
        existing = jobs.plan([], [spec("build")])
        specs = [spec("review", "build"), spec("docs")]
        first = jobs.plan(existing, specs)
        second = jobs.plan(existing, specs)
        self.assertEqual(json.dumps(first).encode(), json.dumps(second).encode())


class ClaimTest(unittest.TestCase):
    def test_claim_binds_an_unclaimed_job_to_the_caller(self) -> None:
        row = claimed()[0]
        self.assertEqual((row["claimed_by"], row["claim_epoch"]), ("owner-1", 3))

    def test_job_claim_exclusive(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as caught:
            jobs.claim(claimed(), "build", "owner-2", 3)
        self.assertEqual(caught.exception.code, "rejected_evidence")
        self.assertIn("already claimed", " ".join(caught.exception.__notes__))

    def test_same_claimant_cannot_claim_twice(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as caught:
            jobs.claim(claimed(), "build", "owner-1", 3)
        self.assertEqual(caught.exception.code, "rejected_evidence")

    def test_claim_rejects_an_unknown_job(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as caught:
            jobs.claim(jobs.plan([], [spec("build")]), "ghost", "owner-1", 3)
        self.assertEqual(caught.exception.code, "rejected_evidence")


class RecordExitTest(unittest.TestCase):
    def test_claimant_records_its_exit_fact(self) -> None:
        result = jobs.record_exit(claimed(), "build", "owner-1", 3, EXIT)
        self.assertEqual(result[0]["exit_fact"], EXIT)

    def test_record_exit_idempotent_replay(self) -> None:
        recorded = jobs.record_exit(claimed(), "build", "owner-1", 3, EXIT)
        before = copy.deepcopy(recorded)
        replay = jobs.record_exit(recorded, "build", "owner-1", 3, dict(EXIT))
        self.assertIs(replay, recorded)
        self.assertEqual(replay, before)

    def test_rejects_a_conflicting_exit_fact(self) -> None:
        recorded = jobs.record_exit(claimed(), "build", "owner-1", 3, EXIT)
        with self.assertRaises(protocol.ProtocolError) as caught:
            jobs.record_exit(recorded, "build", "owner-1", 3, {**EXIT, "outcome": "failed"})
        self.assertEqual(caught.exception.code, "rejected_evidence")

    def test_rejects_a_caller_that_does_not_hold_the_claim(self) -> None:
        for actor_id, epoch in (("owner-2", 3), ("owner-1", 4)):
            with self.subTest(actor_id=actor_id, epoch=epoch):
                with self.assertRaises(protocol.ProtocolError) as caught:
                    jobs.record_exit(claimed(), "build", actor_id, epoch, EXIT)
                self.assertEqual(caught.exception.code, "rejected_evidence")

    def test_rejects_an_unclaimed_job(self) -> None:
        with self.assertRaises(protocol.ProtocolError) as caught:
            jobs.record_exit(jobs.plan([], [spec("build")]), "build", "owner-1", 3, EXIT)
        self.assertEqual(caught.exception.code, "rejected_evidence")


class NoSpawnTest(unittest.TestCase):
    def test_no_controller_spawn(self) -> None:
        tree = ast.parse(JOBS_SOURCE.read_text(encoding="utf-8"))
        modules, attributes = set(), set()
        for node in ast.walk(tree):
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
