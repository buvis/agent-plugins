"""Canonical text: the six steps and every pinned detail, one test each (T-022)."""

from __future__ import annotations

import hashlib
import unittest

import support
from specflow_helper.canonical import canonical, scan_lines, sha256_canonical, sha256_raw


def tasks_equal(a: str, b: str) -> bool:
    return canonical(a, tasks=True) == canonical(b, tasks=True)


class StepsTest(unittest.TestCase):
    def test_leading_byte_order_mark_is_dropped(self) -> None:
        self.assertEqual(canonical("﻿# A\n"), canonical("# A\n"))

    def test_crlf_and_cr_line_endings_become_lf(self) -> None:
        self.assertEqual(canonical("a\r\nb\rc\n"), "a\nb\nc\n")

    def test_trailing_spaces_and_tabs_are_stripped(self) -> None:
        self.assertEqual(canonical("a \t\nb  \n"), "a\nb\n")

    def test_no_break_space_stays(self) -> None:
        self.assertEqual(canonical("a \n"), "a \n")

    def test_form_feed_stays_inside_its_line(self) -> None:
        self.assertEqual(canonical("a\fb\n"), "a\fb\n")

    def test_every_trailing_blank_line_goes_before_one_final_newline(self) -> None:
        self.assertEqual(canonical("a\n\n \n\n"), "a\n")
        self.assertEqual(canonical("a"), "a\n")

    def test_checkboxes_outside_tasks_md_stay_as_written(self) -> None:
        self.assertNotEqual(canonical("- [x] a\n"), canonical("- [ ] a\n"))


class CheckboxTest(unittest.TestCase):
    def test_each_progress_box_normalizes_to_open(self) -> None:
        for box in ("x", "X", "-", "~"):
            with self.subTest(box=box):
                self.assertTrue(tasks_equal(f"- [{box}] T-001 a\n", "- [ ] T-001 a\n"))

    def test_numbered_and_other_list_markers_count(self) -> None:
        for marker in ("*", "+", "1."):
            with self.subTest(marker=marker):
                self.assertTrue(tasks_equal(f"{marker} [x] a\n", f"{marker} [ ] a\n"))

    def test_optional_star_stays_hash_bound(self) -> None:
        self.assertTrue(tasks_equal("- [x]* 2.2 a\n", "- [ ]* 2.2 a\n"))
        self.assertFalse(tasks_equal("- [ ]* 2.2 a\n", "- [ ] 2.2 a\n"))

    def test_x_later_in_a_line_stays(self) -> None:
        self.assertFalse(tasks_equal("- note [x] here\n", "- note [ ] here\n"))

    def test_x_inside_a_fence_stays(self) -> None:
        a = "```sh\n- [x] run it\n```\n"
        self.assertFalse(tasks_equal(a, a.replace("[x]", "[ ]")))

    def test_longer_fence_holds_a_shorter_one(self) -> None:
        a = "````\n```\n- [x] a\n```\n- [x] b\n````\n"
        self.assertFalse(tasks_equal(a, a.replace("[x] b", "[ ] b")))

    def test_tilde_fence_is_not_closed_by_backticks(self) -> None:
        a = "~~~\n```\n- [x] a\n~~~\n"
        self.assertFalse(tasks_equal(a, a.replace("[x]", "[ ]")))

    def test_completion_criteria_box_normalizes_too(self) -> None:
        a = "# T\n\n## Completion criteria\n\n- [x] done\n"
        self.assertTrue(tasks_equal(a, a.replace("[x]", "[ ]")))


class ProgressFieldTest(unittest.TestCase):
    def test_outcome_nested_under_a_task_is_dropped_at_any_depth(self) -> None:
        plain = "- [ ] T-001 a\n  - Details:\n"
        with_outcome = plain + "    - Outcome: done\n"
        self.assertTrue(tasks_equal(plain, with_outcome))

    def test_exception_line_is_dropped(self) -> None:
        self.assertTrue(tasks_equal("- [ ] T-001 a\n", "- [ ] T-001 a\n  - Exception: no CI\n"))

    def test_plain_item_at_task_depth_ends_the_task(self) -> None:
        a = "- [ ] T-001 a\n- Notes\n  - Outcome: kept\n"
        self.assertFalse(tasks_equal(a, "- [ ] T-001 a\n- Notes\n"))

    def test_blank_line_does_not_end_the_task(self) -> None:
        a = "- [ ] T-001 a\n\n  - Outcome: done\n- [ ] T-002 b\n"
        self.assertTrue(tasks_equal(a, "- [ ] T-001 a\n\n- [ ] T-002 b\n"))

    def test_tab_counts_as_four_columns(self) -> None:
        a = "  - [ ] T-001 a\n\t- Outcome: done\n"
        self.assertTrue(tasks_equal(a, "  - [ ] T-001 a\n"))

    def test_outcome_outside_a_task_item_stays(self) -> None:
        self.assertFalse(tasks_equal("# T\n\n- Outcome: x\n", "# T\n"))

    def test_outcome_under_a_completion_criterion_stays(self) -> None:
        a = "## Completion criteria\n\n- [ ] done\n  - Outcome: x\n"
        self.assertFalse(tasks_equal(a, "## Completion criteria\n\n- [ ] done\n"))

    def test_outcome_inside_a_fence_stays(self) -> None:
        a = "- [ ] T-001 a\n  ```\n  - Outcome: x\n  ```\n"
        self.assertFalse(tasks_equal(a, "- [ ] T-001 a\n  ```\n  ```\n"))


class ScannerTest(unittest.TestCase):
    def test_scanner_marks_fence_lines_and_task_items(self) -> None:
        rows = scan_lines("- [ ] T-001 a\n  ```\n  x\n  ```\n# H\n")
        self.assertEqual(
            [(fence, task) for _, fence, task in rows],
            [(False, True), (True, True), (True, True), (True, True), (False, False), (False, False)],
        )


class FileHashTest(support.TempTest):
    def test_tasks_rules_apply_only_to_tasks_md(self) -> None:
        for name, same in (("tasks.md", True), ("design.md", False)):
            with self.subTest(name=name):
                one = self.tmp / "one" / name
                two = self.tmp / "two" / name
                one.parent.mkdir(exist_ok=True)
                two.parent.mkdir(exist_ok=True)
                one.write_text("- [x] T-001 a\n")
                two.write_text("- [ ] T-001 a\n")
                self.assertEqual(sha256_canonical(one) == sha256_canonical(two), same)

    def test_raw_hash_covers_the_exact_bytes(self) -> None:
        path = self.tmp / "f"
        path.write_bytes(b"a\r\n")
        self.assertEqual(sha256_raw(path), hashlib.sha256(b"a\r\n").hexdigest())


if __name__ == "__main__":
    unittest.main()
