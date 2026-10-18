"""The ported section weight audit (T-077): headings, containers, fences, and the usage contract."""

from __future__ import annotations

import json
import unittest

import support

SCRIPT = support.SCRIPTS / "section_weight_audit.py"


class SectionWeightAuditTest(unittest.TestCase):
    def test_ignores_text_before_the_first_level_two_heading(self) -> None:
        sections = support.load(SCRIPT).parse_sections(
            "# Title\n\nintro words that count nowhere\n\n## A\n\none two three\n\n## B\n\nfour five six\n"
        )
        self.assertEqual([s.title for s in sections], ["A", "B"])
        self.assertEqual([s.word_count for s in sections], [3, 3])

    def test_marks_a_container_by_child_count_and_word_share(self) -> None:
        module = support.load(SCRIPT)
        twenty = " ".join(["word"] * 20)
        container = module.parse_sections(
            f"## C\n\nshort\n\n### C1\n\n{twenty}\n\n### C2\n\n{twenty}\n"
        )[0]
        self.assertTrue(container.is_container)
        self.assertEqual(module.audit_sections([container])[0]["flag"], "container")
        thirty = " ".join(["word"] * 30)
        heavy_parent = module.parse_sections(
            f"## P\n\n{thirty}\n\n### P1\n\nfew words\n\n### P2\n\nfew words\n"
        )[0]
        self.assertFalse(
            heavy_parent.is_container, "own words over 30% of the children's"
        )
        one_child = module.parse_sections(f"## O\n\nshort\n\n### O1\n\n{twenty}\n")[0]
        self.assertFalse(one_child.is_container, "one child is no container")

    def test_parses_fences_line_by_line_when_a_fence_holds_a_backtick(self) -> None:
        sections = support.load(SCRIPT).parse_sections(
            "## A\n\nreal words here\n\n```\ncode with a ` backtick\n## Fenced heading\nmore code\n```\n\n## B\n\nmore real words\n"
        )
        self.assertEqual([s.title for s in sections], ["A", "B"])
        self.assertEqual(sections[0].word_count, 3, "fenced lines are not counted")
        self.assertEqual(sections[1].start_line, 11, "line numbers match the file")

    def test_prints_a_summary_line_and_exits_by_the_usage_contract(self) -> None:
        self.assertEqual(support.run(SCRIPT).returncode, 2)
        self.assertEqual(support.run(SCRIPT, "/no/such/doc.md").returncode, 1)
        with support.temp_folder() as folder:
            doc = support.document(
                folder, "## A\n\none two three\n\n## B\n\nfour five six\n"
            )
            result = support.run(SCRIPT, str(doc))
        self.assertEqual(result.returncode, 0)
        last = result.stdout.rstrip("\n").splitlines()[-1]
        self.assertTrue(last.startswith("SUMMARY: "))
        summary = json.loads(last.removeprefix("SUMMARY: "))
        self.assertEqual(summary["total_sections"], 2)
        self.assertEqual(
            sorted(summary),
            ["containers", "heavy_outliers", "light_outliers", "total_sections"],
        )

    def test_docstring_names_the_plugin_relative_skill_path(self) -> None:
        doc = support.load(SCRIPT).__doc__
        self.assertIn("scripts/review/section_weight_audit.py", doc)
        self.assertIn("references/review/design/triage.md", doc)
        self.assertNotIn("~/", doc)
        self.assertNotIn("/Users/", doc)

    def test_unreadable_document_exits_1_without_a_traceback(self) -> None:
        with support.temp_folder() as folder:
            doc = support.document(folder, b"## A\n\xff\xfe not utf-8\n")
            result = support.run(SCRIPT, str(doc))
        self.assertEqual(result.returncode, 1)
        self.assertIn("error: cannot read", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
