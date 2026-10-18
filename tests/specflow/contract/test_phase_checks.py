"""Seeded defects for the checks of 00006 (T-072, T-034, T-039)."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.checks import validate
from test_checks import ChecksTest

SKETCH = support.FIXTURES / "sketch"


class SketchScreensTest(ChecksTest):
    """sketch-screens on an intake item's spike (T-072, INT-002.8)."""

    def sketch(self, *overlays: str) -> Path:
        item = self.repo / ".kiro" / "specflow" / "intake" / "new" / "00107-carts"
        shutil.copytree(SKETCH / "good", item / "spike")
        (item / "idea.md").write_text("Let customers save a cart.\n")
        for overlay in overlays:
            shutil.copytree(
                SKETCH / "malformed" / overlay, item / "spike", dirs_exist_ok=True
            )
        return item

    def messages(self, item: Path) -> list[str]:
        return [
            f["message"]
            for f in validate(self.repo, item, "intake")
            if f["rule"] == "sketch-screens"
        ]

    def test_well_formed_sketch_passes(self) -> None:
        item = self.sketch()
        self.assertEqual(self.messages(item), [])
        self.assertEqual(self.rules(item, "intake"), set())

    def test_intake_item_without_a_sketch_passes(self) -> None:
        item = self.sketch()
        shutil.rmtree(item / "spike")
        self.assertEqual(self.messages(item), [])

    def test_missing_screen_mockup_fails(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "orders.html").unlink()
        self.assert_seeded(item, "sketch-screens", "intake")
        self.assertEqual(
            self.messages(item), ["screen orders has no spike/mockups/orders.html"]
        )

    def test_orphan_mockup_fails(self) -> None:
        item = self.sketch("orphan-mockup")
        self.assertEqual(
            self.messages(item),
            ["spike/mockups/profile.html belongs to no screen of spike/journey.md"],
        )

    def test_navigation_index_is_no_screen(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "index.html").unlink()
        self.assertEqual(self.messages(item), [])

    def test_wrong_link_fails_with_its_edge(self) -> None:
        item = self.sketch("wrong-link")
        [message] = self.messages(item)
        self.assertIn("line 9: the action 'Check out' from cart", message)
        self.assertIn("checkout.html", message)

    def test_mermaid_line_of_no_accepted_kind_fails_with_its_line_number(self) -> None:
        item = self.sketch("bad-line")
        [message] = self.messages(item)
        self.assertTrue(message.startswith("line 9: click cart"), message)

    def test_screen_shared_across_journeys_needs_one_mockup(self) -> None:
        journey = (SKETCH / "good" / "journey.md").read_text()
        starts = [
            line for line in journey.splitlines() if line.strip().startswith("login")
        ]
        self.assertEqual(len(starts), 2)
        self.assertEqual(self.messages(self.sketch()), [])

    def test_check_runs_only_for_intake(self) -> None:
        spec = self.copy("00101-feature-sample")
        shutil.copytree(SKETCH / "good", spec / "spike")
        (spec / "spike" / "mockups" / "orders.html").unlink()
        self.assertNotIn("sketch-screens", self.rules(spec))

    def test_reserved_screen_id_index_fails(self) -> None:
        item = self.sketch()
        self.edit(
            item / "spike" / "journey.md",
            "checkout -->|Pay| done(Order placed)\n",
            "checkout -->|Pay| done(Order placed)\n    index[Home]\n",
        )
        self.assertEqual(
            self.messages(item), ["screen ID index is reserved for the navigation file"]
        )

    def test_journey_without_a_flowchart_screen_fails(self) -> None:
        item = self.sketch()
        (item / "spike" / "journey.md").write_text("# Journeys\n\nNone drawn yet.\n")
        self.assertIn("spike/journey.md holds no flowchart screen", self.messages(item))

    def test_missing_or_unreadable_journey_fails(self) -> None:
        for case, content in (("missing", None), ("unreadable", b"\xff\xfe")):
            with self.subTest(case=case):
                item = self.sketch()
                journey = item / "spike" / "journey.md"
                journey.unlink()
                if content is not None:
                    journey.write_bytes(content)
                self.assertEqual(
                    self.messages(item), ["spike/journey.md is missing or unreadable"]
                )
                shutil.rmtree(item)

    def test_directory_named_like_a_mockup_is_no_mockup(self) -> None:
        item = self.sketch()
        orders = item / "spike" / "mockups" / "orders.html"
        orders.unlink()
        orders.mkdir()
        self.assertEqual(
            self.messages(item), ["screen orders has no spike/mockups/orders.html"]
        )

    def test_unreadable_mockup_is_reported_once(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "login.html").write_bytes(b"\xff\xfe<a>")
        self.assertEqual(
            self.messages(item), ["spike/mockups/login.html cannot be read as UTF-8"]
        )

    def test_unreadable_terminal_mockup_is_reported(self) -> None:
        item = self.sketch()
        (item / "spike" / "mockups" / "done.html").write_bytes(b"\xff\xfe<p>")
        self.assertEqual(
            self.messages(item), ["spike/mockups/done.html cannot be read as UTF-8"]
        )


class PlacementDriftTest(ChecksTest):
    """placement-drift on the task plan, and the T-026 rejections on the same plan (T-034)."""

    def drift(self, spec: Path, level: str = "warning") -> list[dict]:
        return [
            f
            for f in validate(self.repo, spec, "tasks")
            if f["rule"] == "placement-drift" and f["level"] == level
        ]

    def test_two_modules_absent_from_placement_warn(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "`src/import/log.py`",
            "`src/import/log.py`, `src/report/rate.py`, `src/report/mail.py`",
        )
        [warning] = self.drift(spec)
        self.assertIn("src/report/rate.py, src/report/mail.py", warning["message"])
        self.assertNotIn("placement-drift", self.rules(spec, "tasks"))

    def test_plain_location_paths_count_too(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "`src/import/log.py`",
            "src/import/log.py, src/report/rate.py, src/report/mail.py",
        )
        [warning] = self.drift(spec)
        self.assertIn("src/report/rate.py, src/report/mail.py", warning["message"])

    def test_one_module_absent_does_not_warn(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md", "`src/import/log.py`", "`src/import/log.py`, `src/x.py`"
        )
        self.assertEqual(self.drift(spec), [])

    def test_placed_modules_and_a_placed_folder_do_not_warn(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.assertEqual(self.drift(spec), [])
        self.edit(spec / "design.md", "`src/import/log.py`", "`src/import/`")
        self.edit(
            spec / "tasks.md",
            "`src/import/log.py`",
            "`src/import/log.py`, `src/import/rate.py`",
        )
        self.assertEqual(self.drift(spec), [])

    def test_design_without_a_placement_section_is_not_checked(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "design.md", "## Module placement", "## Layout")
        self.edit(spec / "tasks.md", "`src/import/log.py`", "`src/a.py`, `src/b.py`")
        self.assertEqual(self.drift(spec), [])

    def test_task_plan_defects_are_rejected(self) -> None:
        cases = {
            "orphan requirement": (
                "requirement-coverage",
                [
                    ("  - Requirements: REQ-002", "  - Requirements: REQ-001"),
                    ("REQ-002 criterion 1", "REQ-001 criterion 1"),
                ],
            ),
            "dependency cycle": (
                "task-structure",
                [("  - Depends on: none", "  - Depends on: T-002")],
            ),
            "missing verification": (
                "task-structure",
                [("  - Verify: `python -m unittest tests.test_log`\n", "")],
            ),
            "unstable syntax": ("task-structure", [("- [ ] T-002", "- [o] T-002")]),
        }
        for case, (rule, edits) in cases.items():
            with self.subTest(case=case):
                spec = self.copy("00101-feature-sample", f"00101-{case.split()[0]}")
                for old, new in edits:
                    self.edit(spec / "tasks.md", old, new)
                self.assertIn(rule, self.rules(spec, "tasks"))


class BugfixChecksTest(ChecksTest):
    """The five bugfix checks (T-039, ART-005)."""

    RULES = frozenset(
        {
            "bugfix-sections",
            "bugfix-clauses",
            "bugfix-design-sections",
            "bugfix-task-order",
            "bugfix-clause-trace",
        }
    )

    def messages(self, spec: Path, rule: str) -> list[str]:
        return [f["message"] for f in validate(self.repo, spec) if f["rule"] == rule]

    def test_kiro_capture_and_template_sample_pass(self) -> None:
        capture = self.specs / "kiro-bugfix"
        shutil.copytree(support.FIXTURES / "kiro" / "bugfix", capture)
        for spec in (capture, self.copy("00102-bugfix-sample")):
            with self.subTest(spec=spec.name):
                self.assertEqual(self.rules(spec) & self.RULES, set())

    def test_missing_behavior_section_fails_once(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        text = (spec / "bugfix.md").read_text()
        cut = text.split("### Unchanged Behavior")[0]
        (spec / "bugfix.md").write_text(cut)
        self.assertEqual(
            self.messages(spec, "bugfix-sections"),
            [
                (
                    "missing section ### Unchanged Behavior (Regression Prevention)"
                    " under ## Bug Analysis"
                )
            ],
        )
        self.assertNotIn("requirement-ids", self.rules(spec))

    def test_shall_in_a_current_behavior_clause_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "bugfix.md", "the system skips", "the system SHALL skip")
        [message] = self.messages(spec, "bugfix-clauses")
        self.assertTrue(
            message.startswith("a Current Behavior clause uses SHALL: 1.1 WHEN"),
            message,
        )

    def test_design_without_hypothesized_root_cause_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(
            spec / "design.md", "## Hypothesized Root Cause", "## Suspected Cause"
        )
        self.assertEqual(
            self.messages(spec, "bugfix-design-sections"),
            ["missing section ## Hypothesized Root Cause"],
        )

    def test_bug_condition_may_sit_in_bugfix_md(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "design.md", "### Bug Condition", "### Trigger")
        self.assertEqual(
            self.messages(spec, "bugfix-design-sections"),
            ["no Bug Condition heading in design.md or bugfix.md"],
        )
        bugfix = spec / "bugfix.md"
        bugfix.write_text(
            bugfix.read_text()
            + "\n### Bug Condition\n\nA file without a final newline.\n"
        )
        self.assertEqual(self.messages(spec, "bugfix-design-sections"), [])

    def test_fix_task_before_task_1_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        path = spec / "tasks.md"
        head, rest = path.read_text().split("- [ ] 1. ", 1)
        first_two, rest = rest.split("- [ ] 3. ", 1)
        fix, checkpoint = rest.split("- [ ] 4. ", 1)
        path.write_text(
            f"{head}- [ ] 3. {fix}- [ ] 1. {first_two}- [ ] 4. {checkpoint}"
        )
        messages = self.messages(spec, "bugfix-task-order")
        self.assertIn(
            "the first top-level task is not 'Write bug condition exploration test'...:"
            " 3. Fix the reader",
            messages,
        )

    def test_untraced_unchanged_clause_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        bugfix = spec / "bugfix.md"
        clause = "3.2 WHEN a source file is empty THEN the system SHALL CONTINUE TO import nothing\n"
        bugfix.write_text(bugfix.read_text() + "\n" + clause)
        self.assertEqual(
            self.messages(spec, "bugfix-clause-trace"),
            [
                (
                    "clause 3.2 is traced by no _Requirements: line of task 1, task 2,"
                    " or a subtask of task 3"
                )
            ],
        )

    def test_trace_on_the_checkpoint_does_not_count(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        path = spec / "tasks.md"
        self.edit(path, "  - _Requirements: 3.1_\n", "")
        self.edit(path, "    - _Requirements: 2.1, 3.1_", "    - _Requirements: 2.1_")
        self.edit(
            path,
            "- [ ] 4. Checkpoint - Ensure all tests pass",
            "- [ ] 4. Checkpoint - Ensure all tests pass\n  - _Requirements: 3.1_",
        )
        [message] = self.messages(spec, "bugfix-clause-trace")
        self.assertTrue(message.startswith("clause 3.1 is traced by no"), message)

    def test_checks_skip_a_feature_spec(self) -> None:
        self.assertEqual(
            self.rules(self.copy("00101-feature-sample")) & self.RULES, set()
        )

    def test_missing_introduction_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "bugfix.md", "## Introduction", "## Summary")
        self.assertEqual(
            self.messages(spec, "bugfix-sections"), ["missing section ## Introduction"]
        )

    def test_missing_bug_analysis_fails_with_its_sections(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "bugfix.md", "## Bug Analysis", "## Analysis")
        messages = self.messages(spec, "bugfix-sections")
        self.assertEqual(messages[0], "missing section ## Bug Analysis")
        self.assertEqual(len(messages), 4)

    def test_behavior_section_without_a_clause_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        text = (spec / "bugfix.md").read_text()
        kept, _ = text.split("3.1 WHEN", 1)
        (spec / "bugfix.md").write_text(kept)
        self.assertEqual(
            self.messages(spec, "bugfix-sections"),
            ["### Unchanged Behavior (Regression Prevention) has no clause"],
        )

    def test_preservation_clause_under_expected_behavior_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(
            spec / "bugfix.md",
            "SHALL import its last row",
            "SHALL CONTINUE TO import its last row",
        )
        [message] = self.messages(spec, "bugfix-clauses")
        self.assertTrue(
            message.startswith("clause does not follow the pattern: 2.1 WHEN"), message
        )

    def test_fewer_than_four_top_level_tasks_fails(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        path = spec / "tasks.md"
        kept, _ = path.read_text().split("- [ ] 4. ", 1)
        path.write_text(kept)
        self.assertEqual(
            self.messages(spec, "bugfix-task-order"),
            ["3 top-level tasks; a bugfix plan has four"],
        )

    def test_second_third_and_last_task_mismatches_are_each_named(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        path = spec / "tasks.md"
        self.edit(path, "2. Write preservation property tests", "2. Preservation tests")
        self.edit(path, "3. Fix the reader", "3. Repair the reader")
        self.edit(path, "4. Checkpoint - Ensure", "4. Final - Ensure")
        messages = self.messages(spec, "bugfix-task-order")
        self.assertEqual(
            [m.split(" top-level task")[0] for m in messages],
            ["the second", "the third", "the last"],
        )


if __name__ == "__main__":
    unittest.main()
