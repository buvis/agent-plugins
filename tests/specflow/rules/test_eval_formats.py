"""Tests for the session and eval formats and how check_rules.py resolves an eval check."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "specflow"))
import check_rules
from test_check_rules import Fixture, dlg_rule, val_rule

EVALS = REPO / "tests" / "specflow" / "evals"
# Copied from the 00005 design (Data model, assertion kinds), not read from the schema.
KINDS = {
    "file_exists",
    "file_unchanged",
    "file_matches",
    "one_question_per_message",
    "recommended_option_first",
    "rubric",
    "file_absent",
    "file_lacks",
    "message_matches",
    "message_lacks",
    "question_count_at_most",
    "file_read",
    "file_not_read",
    "validation_passes",
    "validation_reports",
}
EVAL = "tests/specflow/evals/SR-DLG-001.json"
SESSION = "tests/specflow/evals/sessions/one-question.json"


def schema(name: str) -> dict:
    return json.loads((EVALS / "schemas" / name).read_text(encoding="utf-8"))


def example(name: str) -> dict:
    return json.loads((EVALS / "examples" / name).read_text(encoding="utf-8"))


class EvalFormatTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Fixture(Path(tmp.name))

    def write_eval(self, **changes: object) -> None:
        record = {
            "schemaVersion": 1,
            "rule": "SR-DLG-001",
            "session": "one-question",
            "assertions": [{"kind": "one_question_per_message"}],
        }
        record.update(changes)
        self.repo.write(EVAL, json.dumps(record))

    def errors(self) -> list[str]:
        return self.repo.run()[0]

    def assert_error(self, *parts: str) -> None:
        errors = self.errors()
        self.assertTrue(
            [e for e in errors if all(p in e for p in parts)],
            f"no error with {parts} in {errors}",
        )

    def test_both_examples_validate(self) -> None:
        session = check_rules.check_schema(
            example("session.json"),
            schema("session.schema.json"),
        )
        self.assertEqual(session, [])
        record = example("eval.json")
        self.assertEqual(
            check_rules.check_schema(record, schema("eval.schema.json")), []
        )
        self.assertEqual({a["kind"] for a in record["assertions"]}, KINDS)

    def test_examples_are_exempt_from_the_name_rule(self) -> None:
        self.assertNotEqual(example("eval.json")["rule"], "eval")
        self.assertNotEqual(example("session.json")["name"], "session")
        self.assertEqual(check_rules.check(REPO, frozenset())[0], [])

    def test_only_rubric_is_judged_by_hand(self) -> None:
        self.write_eval(assertions=[{"kind": "rubric", "rubric": "Is it plain?"}])
        self.assertEqual(self.errors(), [])
        self.write_eval(
            assertions=[{"kind": "one_question_per_message", "rubric": "x"}]
        )
        self.assert_error(EVAL, "$.assertions[0]")

    def test_eval_check_resolves_only_to_a_valid_file(self) -> None:
        self.assertEqual(self.errors(), [])
        self.write_eval(assertions="all of them")
        self.assert_error("SR-DLG-001", "evals/SR-DLG-001.json", "does not validate")

    def test_rejects_malformed_eval_record(self) -> None:
        self.write_eval(assertions=[{"kind": "file_matches", "path": "a.md"}])
        self.assert_error(EVAL, "$.assertions[0]")
        self.repo.write(EVAL, "{not json")
        self.assert_error(EVAL, "JSON")

    def test_rejects_malformed_eval_through_a_criterion_mapping(self) -> None:
        self.write_eval(assertions=[{"kind": "maybe"}])
        errors, info = self.repo.run()
        self.assertIn("ART-002.14 -> SR-DLG-001 -> evals/SR-DLG-001.json", info)
        bad_value = [e for e in errors if EVAL in e and "$.assertions[0]" in e]
        self.assertTrue(bad_value, errors)
        self.assertTrue([e for e in errors if e.startswith("SR-DLG-001: ")], errors)

    def test_several_criteria_may_share_one_eval(self) -> None:
        criteria = ["ART-002.14", "ART-002.16", "ART-002.17"]
        self.repo.criteria(criteria)
        self.repo.inventory([dlg_rule(criteria=criteria), val_rule()])
        errors, info = self.repo.run()
        self.assertEqual(errors, [])
        rows = [line for line in info if line.endswith("-> evals/SR-DLG-001.json")]
        self.assertEqual(len(rows), 3)
        records = list((self.repo.root / "tests/specflow/evals").glob("SR-*.json"))
        self.assertEqual(len(records), 1)

    def test_rejects_eval_naming_a_missing_session(self) -> None:
        self.write_eval(session="no-such-session")
        self.assert_error(EVAL, "no-such-session")
        self.assert_error("SR-DLG-001", "does not validate")

    def test_rejects_eval_with_no_assertion(self) -> None:
        self.write_eval(assertions=[])
        self.assert_error(EVAL, "no assertion")

    def test_rejects_record_whose_name_differs_from_its_file(self) -> None:
        self.write_eval(rule="SR-DLG-002")
        self.assert_error(EVAL, "SR-DLG-002")
        self.write_eval()
        session = json.loads((self.repo.root / SESSION).read_text(encoding="utf-8"))
        self.repo.write(SESSION, json.dumps({**session, "name": "two-questions"}))
        self.assert_error(SESSION, "two-questions")

    def test_session_has_exactly_one_of_fixture_and_continues(self) -> None:
        base = {
            "schemaVersion": 1,
            "name": "one-question",
            "turns": [{"developer": "Go."}],
        }
        for extra in ({}, {"fixture": "specs/a", "continues": "first"}):
            with self.subTest(extra=extra):
                self.repo.write(SESSION, json.dumps({**base, **extra}))
                self.assert_error(SESSION, "oneOf")
        self.repo.write(SESSION, json.dumps({**base, "continues": "first"}))
        self.assertEqual(self.errors(), [])


if __name__ == "__main__":
    unittest.main()
