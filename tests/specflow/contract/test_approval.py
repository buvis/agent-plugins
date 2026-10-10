"""Approval bound to content, the phase table, and the spec type (T-022)."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.state import (
    StateError,
    artifact_status,
    derive_phase,
    load_state,
    spec_type,
)


class ApprovalTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.spec = support.write_spec(
            self.tmp / "00042-sample",
            {
                "requirements.md": support.REQUIREMENTS,
                "design.md": support.DESIGN,
                "tasks.md": support.TASKS,
            },
        )
        self.state = support.approve(
            self.spec, support.new_state(), "requirements", "design", "tasks"
        )

    def status_after(self, name: str, text: str) -> str:
        (self.spec / name).write_text(text)
        return artifact_status(self.spec, self.state)[name.removesuffix(".md")]

    def test_content_edit_stales_the_approval(self) -> None:
        self.assertEqual(self.status_after("design.md", support.DESIGN + "More.\n"), "stale")

    def test_layout_only_edits_keep_the_approval(self) -> None:
        crlf = support.DESIGN.replace("\n", "  \r\n") + "\n\n"
        self.assertEqual(self.status_after("design.md", crlf), "approved")

    def test_progress_keeps_the_task_plan_approved(self) -> None:
        text = support.TASKS.replace("- [ ] T-001", "- [x] T-001").replace(
            "  - Verify: run the greeting test",
            "  - Verify: run the greeting test\n  - Outcome: passed",
        )
        self.assertEqual(self.status_after("tasks.md", text), "approved")

    def test_x_in_a_fenced_command_stales_the_plan(self) -> None:
        self.status_after("tasks.md", support.TASKS + "\n```\n- [ ] run\n```\n")
        self.state = support.approve(self.spec, self.state, "tasks")
        text = support.TASKS + "\n```\n- [x] run\n```\n"
        self.assertEqual(self.status_after("tasks.md", text), "stale")

    def test_outcome_outside_a_task_item_stales_the_plan(self) -> None:
        text = support.TASKS + "\n- Outcome: free text\n"
        self.assertEqual(self.status_after("tasks.md", text), "stale")

    def test_recorded_stale_stays_stale_even_if_the_hash_matches(self) -> None:
        self.state["artifacts"]["design"]["status"] = "stale"
        self.assertEqual(artifact_status(self.spec, self.state)["design"], "stale")

    def test_approval_is_never_inferred_from_a_file(self) -> None:
        self.assertEqual(
            artifact_status(self.spec, None),
            {"requirements": "draft", "design": "draft", "tasks": "draft"},
        )

    def test_missing_file_is_missing_whatever_the_state_says(self) -> None:
        (self.spec / "tasks.md").unlink()
        self.assertEqual(artifact_status(self.spec, self.state)["tasks"], "missing")

    def test_files_specflow_does_not_own_are_never_read(self) -> None:
        other = self.spec / "tasks.meta.json"
        other.write_text("{}")
        other.chmod(0)
        self.addCleanup(other.chmod, 0o644)
        self.assertEqual(set(artifact_status(self.spec, self.state).values()), {"approved"})


class LoadStateTest(support.TempTest):
    def test_absent_state_is_none(self) -> None:
        self.assertIsNone(load_state(self.tmp))

    def test_malformed_and_unsupported_state_raise(self) -> None:
        for text in ("{", "[]", json.dumps(support.new_state(schemaVersion=2))):
            with self.subTest(text=text[:20]):
                (self.tmp / ".specflow.json").write_text(text)
                with self.assertRaises(StateError):
                    load_state(self.tmp)


class PhaseTest(support.TempTest):
    """One test per row of the phase table from requirements on, in both orders."""

    def make(self, order: str, approved: tuple[str, ...], tasks: str = support.TASKS) -> str:
        spec = support.write_spec(
            self.tmp / order,
            {
                "requirements.md": support.REQUIREMENTS,
                "design.md": support.DESIGN,
                "tasks.md": tasks,
            },
        )
        state = support.approve(spec, support.new_state(workflowOrder=order), *approved)
        return derive_phase(spec, artifact_status(spec, state), order)

    def test_first_artifact_in_order_comes_first(self) -> None:
        self.assertEqual(self.make("requirements-first", ()), "requirements")
        self.assertEqual(self.make("design-first", ()), "design")

    def test_second_artifact_follows_the_first(self) -> None:
        self.assertEqual(self.make("requirements-first", ("requirements",)), "design")
        self.assertEqual(self.make("design-first", ("design",)), "requirements")

    def test_tasks_phase_after_both_upstream_approvals(self) -> None:
        for order in ("requirements-first", "design-first"):
            with self.subTest(order=order):
                self.assertEqual(self.make(order, ("requirements", "design")), "tasks")

    def test_implementation_while_a_task_is_unchecked(self) -> None:
        for order in ("requirements-first", "design-first"):
            with self.subTest(order=order):
                phase = self.make(order, ("requirements", "design", "tasks"))
                self.assertEqual(phase, "implementation")

    def test_verification_while_a_completion_criterion_is_unchecked(self) -> None:
        tasks = support.TASKS.replace("- [ ] T-00", "- [x] T-00")
        phase = self.make("design-first", ("requirements", "design", "tasks"), tasks)
        self.assertEqual(phase, "verification")

    def test_complete_when_every_box_is_checked(self) -> None:
        tasks = support.TASKS.replace("[ ]", "[x]")
        phase = self.make("requirements-first", ("requirements", "design", "tasks"), tasks)
        self.assertEqual(phase, "complete")

    def test_in_progress_and_queued_boxes_count_as_unchecked(self) -> None:
        for box in ("-", "~"):
            with self.subTest(box=box):
                tasks = support.TASKS.replace("[ ]", "[x]")
                tasks = tasks.replace("[x] T-002", f"[{box}] T-002")
                phase = self.make("requirements-first", ("requirements", "design", "tasks"), tasks)
                self.assertEqual(phase, "implementation")

    def test_unchecked_optional_task_holds_no_phase(self) -> None:
        tasks = support.TASKS.replace("[ ]", "[x]").replace("- [x] T-002", "- [ ]* T-002")
        phase = self.make("requirements-first", ("requirements", "design", "tasks"), tasks)
        self.assertEqual(phase, "complete")


class KiroPhaseTest(support.TempTest):
    def kiro_spec(self, folder: str) -> Path:
        spec = self.tmp / folder
        shutil.copytree(support.FIXTURES / "kiro" / folder, spec)
        return spec

    def approve_all(self, spec: Path, kind: str, order: str) -> str:
        state = support.new_state(specType=kind, workflowOrder=order)
        if kind == "bugfix":
            state["artifacts"]["requirements"]["path"] = "bugfix.md"
        state = support.approve(spec, state, "requirements", "design", "tasks")
        return derive_phase(spec, artifact_status(spec, state), order)

    def test_bugfix_is_in_verification_while_only_the_checkpoint_is_open(self) -> None:
        spec = self.kiro_spec("bugfix")
        tasks = (spec / "tasks.md").read_text()
        tasks = tasks.replace("- [-] 4.", "- [x] 4.").replace("- [~] 5.", "- [x] 5.")
        (spec / "tasks.md").write_text(tasks)
        self.assertEqual(self.approve_all(spec, "bugfix", "requirements-first"), "verification")

    def test_bugfix_capture_as_found_is_in_implementation(self) -> None:
        spec = self.kiro_spec("bugfix")
        self.assertEqual(self.approve_all(spec, "bugfix", "requirements-first"), "implementation")

    def test_kiro_plan_without_completion_criteria_skips_verification(self) -> None:
        spec = self.kiro_spec("design-first")
        self.assertEqual(self.approve_all(spec, "feature", "design-first"), "complete")

    def test_optional_kiro_tasks_do_not_hold_the_plan_open(self) -> None:
        spec = self.kiro_spec("requirements-first")
        tasks = (spec / "tasks.md").read_text().replace("- [-] 13.", "- [x] 13.")
        (spec / "tasks.md").write_text(tasks)
        self.assertEqual(self.approve_all(spec, "feature", "requirements-first"), "complete")


class SpecTypeTest(support.TempTest):
    def test_config_kiro_wins_then_state_then_files(self) -> None:
        spec = support.write_spec(self.tmp / "s", {"requirements.md": "# R\n"})
        self.assertEqual(spec_type(spec, None), ("feature", []))
        state = support.new_state(specType="bugfix")
        found, disagree = spec_type(spec, state)
        self.assertEqual(found, "bugfix")
        self.assertEqual(disagree, [".specflow.json: bugfix", "files: feature"])
        (spec / ".config.kiro").write_text('{"specType": "feature"}')
        found, disagree = spec_type(spec, state)
        self.assertEqual(found, "feature")
        self.assertIn(".specflow.json: bugfix", disagree)

    def test_agreeing_sources_report_nothing(self) -> None:
        spec = support.write_spec(self.tmp / "s", {"bugfix.md": "# B\n"})
        (spec / ".config.kiro").write_text('{"specType": "bugfix"}')
        self.assertEqual(spec_type(spec, support.new_state(specType="bugfix")), ("bugfix", []))

    def test_spec_type_rewrites_nothing(self) -> None:
        spec = support.write_spec(self.tmp / "s", {"bugfix.md": "# B\n"})
        (spec / ".config.kiro").write_text('{"specType": "feature"}')
        before = sorted((p.name, p.read_bytes()) for p in spec.iterdir())
        spec_type(spec, support.new_state())
        self.assertEqual(sorted((p.name, p.read_bytes()) for p in spec.iterdir()), before)

    def test_unreadable_config_kiro_is_reported(self) -> None:
        spec = support.write_spec(self.tmp / "s", {"bugfix.md": "# B\n"})
        (spec / ".config.kiro").write_text("{")
        self.assertEqual(spec_type(spec, None), ("bugfix", [".config.kiro: unreadable"]))


if __name__ == "__main__":
    unittest.main()
