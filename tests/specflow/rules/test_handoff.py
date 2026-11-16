"""Compatibility checks cannot pass without actual stale and completion states."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals/runners"))
import run_handoff


def rows() -> list[dict]:
    result = []
    for step, host, _ in run_handoff.STEPS:
        stale = step in ("edit-requirements", "resume")
        result.append(
            {
                "step": step,
                "host": host,
                "instructions": {"classification": "clean"},
                "status": {
                    "specs": [
                        {
                            "spec": "00001-greeting",
                            "phase": "complete"
                            if step == "verification"
                            else "requirements",
                            "nextTask": None,
                            "artifacts": {
                                key: "stale" if stale else "approved"
                                for key in ("requirements", "design", "tasks")
                            },
                        }
                    ]
                },
                "hashes": {
                    name: {"sha256": "synthetic"}
                    for name in ("requirements.md", "design.md", "tasks.md")
                },
                "files": {
                    run_handoff.SPEC + "/.specflow.json": "state",
                    run_handoff.SPEC
                    + "/requirements.md": "External writer requires the greeting",
                },
            }
        )
    return result


class HandoffTest(unittest.TestCase):
    def test_complete_trace_satisfies_checks(self) -> None:
        self.assertEqual(run_handoff.checks(rows()), [])

    def test_missing_steps_never_pass(self) -> None:
        self.assertTrue(run_handoff.checks(rows()[:-1]))

    def test_unstaled_approval_is_detected(self) -> None:
        trace = rows()
        trace[-1]["status"]["specs"][0]["artifacts"]["design"] = "approved"
        self.assertIn(
            "resume: required approvals were not stale", run_handoff.checks(trace)
        )

    def test_reverted_external_edit_is_detected(self) -> None:
        trace = rows()
        trace[-1]["files"][run_handoff.SPEC + "/requirements.md"] = "reverted"
        self.assertIn("resume changed the external edit", run_handoff.checks(trace))

    def test_unmeasured_instructions_are_not_clean_evidence(self) -> None:
        trace = rows()
        trace[0]["instructions"]["classification"] = "unknown"
        self.assertIn(
            "requirements: instructions were not measured clean",
            run_handoff.checks(trace),
        )
