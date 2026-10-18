"""The ported claim ladder scan (T-077): fences, line numbers, ID tokens, the qualifier list, and the usage contract."""

from __future__ import annotations

import json
import unittest

import support

SCRIPT = support.SCRIPTS / "claim_ladder_scan.py"


def scan(text: str) -> list[dict]:
    with support.temp_folder() as folder:
        return support.load(SCRIPT).scan(support.document(folder, text))


class ClaimLadderScanTest(unittest.TestCase):
    def test_fence_holding_a_backtick_is_stripped(self) -> None:
        findings = scan(
            "## A\n\n```\nthe `fast` path in code\n```\n\nprose with nothing vague\n"
        )
        self.assertEqual(
            findings,
            [],
            "a qualifier inside a fence that holds a backtick is not scanned",
        )

    def test_prose_between_fences_is_scanned(self) -> None:
        findings = scan(
            "```\ncode with a ` backtick\n```\n\nthis prose is fast\n\n```\nmore code\n```\n"
        )
        self.assertEqual([f["qualifier"] for f in findings], ["fast"])

    def test_reported_line_numbers_match_the_file(self) -> None:
        text = "## A\n\n```\nline three\nline four\n```\n\nline eight is robust\n"
        findings = scan(text)
        self.assertEqual(
            [(f["qualifier"], f["line"]) for f in findings], [("robust", 8)]
        )
        self.assertIn("robust", text.split("\n")[7])

    def test_parses_fences_line_by_line_when_a_fence_holds_a_backtick(self) -> None:
        findings = scan("```\na ` backtick\n```\nscalable prose\n```\nfast code\n```\n")
        self.assertEqual(
            [(f["qualifier"], f["line"]) for f in findings], [("scalable", 4)]
        )

    def test_id_tokens_are_not_measurements(self) -> None:
        for token in (
            "REQ-001",
            "T-003",
            "SR-REQ-007",
            "ART-003.9",
            "00007",
            "00007-reviews",
        ):
            with self.subTest(token=token):
                findings = scan(f"{token} makes the import scalable.\n")
                self.assertFalse(
                    findings[0]["grounded"], f"{token} grounded the qualifier"
                )

    def test_id_tokens_do_not_ground_a_qualifier(self) -> None:
        grounded = scan("the import is scalable: 5000 rows a minute.\n")
        self.assertTrue(grounded[0]["grounded"], "a real measurement still grounds")
        self.assertTrue(
            scan("scalable to 10000 users\n")[0]["grounded"],
            "a five-digit count is a measurement",
        )
        self.assertFalse(scan("see REQ-012 for why it is scalable\n")[0]["grounded"])

    def test_matches_the_qualifier_list_as_whole_words_in_any_case(self) -> None:
        module = support.load(SCRIPT)
        self.assertEqual(len(module.QUALIFIERS), 34)
        findings = scan(
            "A FAST path; a fastening is not a match; Highly Available too.\n"
        )
        self.assertEqual(
            [f["qualifier"].lower() for f in findings], ["fast", "highly available"]
        )

    def test_prints_a_summary_line_and_exits_by_the_usage_contract(self) -> None:
        self.assertEqual(support.run(SCRIPT).returncode, 2)
        self.assertEqual(support.run(SCRIPT, "/no/such/doc.md").returncode, 1)
        with support.temp_folder() as folder:
            clean = support.run(
                SCRIPT, str(support.document(folder, "nothing vague here\n"))
            )
            vague = support.run(
                SCRIPT, str(support.document(folder, "it is robust\n", "v.md"))
            )
        for result in (clean, vague):
            self.assertEqual(result.returncode, 0)
            last = result.stdout.rstrip("\n").splitlines()[-1]
            self.assertTrue(
                last.startswith("SUMMARY: "),
                "the summary line is printed even with no finding",
            )
        self.assertEqual(
            json.loads(
                vague.stdout.rstrip("\n").splitlines()[-1].removeprefix("SUMMARY: ")
            )["ungrounded"],
            1,
        )

    def test_docstring_names_the_plugin_relative_skill_path(self) -> None:
        doc = support.load(SCRIPT).__doc__
        self.assertIn("scripts/review/claim_ladder_scan.py", doc)
        self.assertIn("references/review/design/triage.md", doc)
        self.assertNotIn("~/", doc)
        self.assertNotIn("/Users/", doc)

    def test_unreadable_document_exits_1_without_a_traceback(self) -> None:
        with support.temp_folder() as folder:
            result = support.run(
                SCRIPT, str(support.document(folder, b"\xff\xfe robust\n"))
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("error: cannot read", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
