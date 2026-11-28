"""Compatibility checks cannot pass without actual stale and completion states."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_requirements_edit_adds_no_requirement_for_tasks_to_cover(self) -> None:
        # Live run 2026-11-25: a new requirement ID left the existing task
        # plan without coverage, so "approve the existing tasks" was refused.
        prompts = {step: prompt for step, _, prompt in run_handoff.STEPS}
        self.assertIn("Add no new requirement", prompts["edit-requirements"])
        self.assertNotIn("Add this requirement", prompts["edit-requirements"])

    def test_tasks_request_limits_verify_commands_to_ones_that_can_run(self) -> None:
        # Live run 2026-11-28: a drafted AST one-liner raised AttributeError,
        # so its task stayed unchecked and completion was out of reach.
        prompts = {step: prompt for step, _, prompt in run_handoff.STEPS}
        self.assertIn("Write no other verification command", prompts["tasks"])

    def test_approval_request_names_every_open_marker_by_its_exact_line(self) -> None:
        # Live run 2026-11-25: a host wrote an open question no fixed prompt
        # predicted, so the design approval was refused for lack of a name.
        question = "- Minimum Python 3 version the code must support."
        earlier = "- The runner is unittest. (guess)"
        status = {
            "specs": [
                {
                    "spec": "00001-greeting",
                    "blockers": [
                        {"reason": "design is draft", "reference": "design.md"},
                        {
                            "reason": "requirements marker not accepted for the design approval",
                            "reference": question,
                        },
                    ],
                }
            ]
        }
        state = {
            "artifacts": {
                "design": {
                    "acceptedMarkers": [{"artifact": "requirements", "line": earlier}]
                }
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / run_handoff.SPEC).mkdir(parents=True)
            (workspace / run_handoff.SPEC / ".specflow.json").write_text(
                json.dumps(state)
            )
            with mock.patch.object(
                run_handoff.runner, "capture_status", return_value=status
            ):
                for step in ("tasks", "approve-tasks", "reapprove"):
                    with self.subTest(step=step):
                        prompt = run_handoff.step_prompt(step, "Approve.", workspace)
                        self.assertIn(question, prompt)
                        # A rewritten approval must not drop an earlier acceptance.
                        self.assertIn(earlier, prompt)
                        self.assertNotIn("design.md", prompt)
                self.assertEqual(
                    run_handoff.step_prompt("design", "Draft.", workspace), "Draft."
                )

    def test_approval_request_without_open_markers_is_unchanged(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(run_handoff.runner, "capture_status", return_value=None),
        ):
            self.assertEqual(
                run_handoff.step_prompt("tasks", "Approve.", Path(directory)),
                "Approve.",
            )

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
