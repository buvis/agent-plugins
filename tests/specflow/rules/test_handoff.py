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


CHOICES = (
    "greeting.py",
    "test_greeting.py",
    "repository root",
    "standard library",
    "python3 -m unittest",
    "no arguments",
)


class HandoffTest(unittest.TestCase):
    def test_requirements_request_supplies_every_contract_choice(self) -> None:
        # Live run 2026-11-24: five unstated choices became guesses and open
        # questions, and the generic approvals could not accept them.
        prompt = run_handoff.STEPS[0][2]
        for choice in CHOICES:
            self.assertIn(choice, prompt)

    def test_dependent_approvals_accept_remaining_markers_by_name(self) -> None:
        prompts = {step: prompt for step, _, prompt in run_handoff.STEPS}
        for step in ("tasks", "approve-tasks", "reapprove"):
            with self.subTest(step=step):
                self.assertIn("accept each such marker by name", prompts[step])
                for choice in CHOICES:
                    self.assertIn(choice, prompts[step])

    def test_verification_request_asks_to_complete_not_only_report(self) -> None:
        # The check needs phase complete; SR-VER-004 makes that ticking the
        # completion criteria, which a report-only request never asks for.
        prompts = {step: prompt for step, _, prompt in run_handoff.STEPS}
        self.assertIn("tick each completion criterion", prompts["verification"])

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
