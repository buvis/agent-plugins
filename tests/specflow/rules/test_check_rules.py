"""Tests for tools/specflow/check_rules.py; fixtures are built in temporary folders."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "specflow"))
import check_rules

# Copied from the 00005 design (decision 2026-10-04 #4 and ruling D8), not read
# from the list, so an edit to the list fails here instead of passing silently.
REVIEWED_IDS = [
    "WF-003.11", "WF-003.12", "WF-003.13", "WF-003.14",
    "WF-003.15", "WF-003.16", "WF-003.17", "WF-003.18",
    "ART-002.12", "ART-002.13", "ART-002.14", "ART-002.15",
    "ART-002.16", "ART-002.17", "ART-002.18",
    "ART-001.11", "ART-003.12", "INT-001.8", "INT-002.8",
    "WF-001.9", "WF-004.8", "VAL-001.11", "VAL-001.12",
    "INT-001.5", "SEC-002.2", "ART-002.11", "WF-002.1",
    "STATE-001.2", "STATE-003.1", "VAL-001.5", "VAL-001.8",
    "ART-004.16", "VAL-001.13",
]  # fmt: skip

HEADER = "| id | source skill | phase | row | classification | reason | code-only | evidence |"
ROWS = {"ELI-01": "port", "ELI-02": "redesign", "ELI-03": "drop", "ELI-04": "struck"}
REFS = Path("plugins/specflow/skills/spec-workflow/references")
PLAN_A = "docs/dev/project-management/discovery/00001-specflow-port-agent-skills.md"


def plan(rows: dict[str, str] = ROWS, header: str = HEADER, extra: str = "") -> str:
    body = "".join(
        f"| {i} | skill | phase | row | {c} | why | no | E/SKILL.md:1 |\n"
        for i, c in rows.items()
    )
    return (
        f"# Plan\n\n## Inventory Matrix\n\n{header}\n"
        f"|---|---|---|---|---|---|---|---|\n{body}{extra}\n## Next\n"
    )


def dlg_rule(**changes: object) -> dict:
    rule = {
        "id": "SR-DLG-001",
        "file": "artifact-contract.md",
        "kind": "behavioral",
        "check": "evals/SR-DLG-001.json",
        "sources": ["A:ELI-01"],
        "criteria": ["ART-002.14"],
    }
    rule.update(changes)
    return rule


def val_rule(**changes: object) -> dict:
    rule = {
        "id": "SR-VAL-001",
        "file": "validation-rules.md",
        "kind": "structural",
        "check": "validator:requirement-ids",
        "sources": ["A:ELI-02"],
    }
    rule.update(changes)
    return rule


class Fixture:
    """A repository holding one plan, the two lists, two tagged files, and an eval."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.write("docs/plan-a.md", plan())
        self.inventory([dlg_rule(), val_rule()])
        self.criteria(["ART-002.14"])
        self.write(REFS / "artifact-contract.md", "- [SR-DLG-001] Ask one question.\n")
        self.write(REFS / "validation-rules.md", "- [SR-VAL-001] Stable IDs.\n")
        assertions = [{"kind": "one_question_per_message"}]
        record = {"schemaVersion": 1, "rule": "SR-DLG-001", "session": "one-question"}
        self.write(
            "tests/specflow/evals/SR-DLG-001.json",
            json.dumps({**record, "assertions": assertions}),
        )
        session = {"schemaVersion": 1, "name": "one-question", "fixture": "specs/a"}
        self.write(
            "tests/specflow/evals/sessions/one-question.json",
            json.dumps({**session, "turns": [{"developer": "Create a spec."}]}),
        )

    def write(self, rel: str | Path, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def inventory(self, rules: list[dict], version: object = 1) -> None:
        data = {
            "schemaVersion": version,
            "plans": {"A": "docs/plan-a.md"},
            "rules": rules,
        }
        self.write("tools/specflow/rules/inventory.json", json.dumps(data))

    def criteria(self, ids: object, version: object = 1) -> None:
        data = {"schemaVersion": version, "requiredCriteria": ids}
        self.write("tools/specflow/rules/criteria.json", json.dumps(data))

    def run(self, areas: frozenset[str] | None = None) -> tuple[list[str], list[str]]:
        return check_rules.check(self.root, areas)


class CheckRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Fixture(Path(tmp.name))

    def assert_error(self, errors: list[str], *parts: str) -> None:
        hits = [e for e in errors if all(p in e for p in parts)]
        self.assertTrue(hits, f"no error with {parts} in {errors}")

    def test_fixture_passes(self) -> None:
        self.assertEqual(self.repo.run()[0], [])

    def test_every_approved_plan_a_row_has_a_rule(self) -> None:
        errors, info = check_rules.check(REPO, frozenset())
        self.assertEqual(errors, [])
        # Counted here by line shape, not by the checker, so a row it skips fails.
        text = (REPO / PLAN_A).read_text(encoding="utf-8")
        matrix = text.split("\n## Inventory Matrix\n", 1)[1].split("\n## ", 1)[0]
        rows = [
            line
            for line in matrix.splitlines()
            if line.startswith("| ") and not line.startswith("| id |")
        ]
        self.assertIn(f"plan A: {len(rows)} rows read from {PLAN_A}", info)

    def test_no_drop_or_struck_row_has_a_rule(self) -> None:
        self.repo.inventory(
            [
                dlg_rule(sources=["A:ELI-01", "A:ELI-03"]),
                val_rule(sources=["A:ELI-02", "A:ELI-04"]),
            ],
        )
        errors, _ = self.repo.run()
        self.assert_error(errors, "SR-DLG-001", "A:ELI-03", "drop")
        self.assert_error(errors, "SR-VAL-001", "A:ELI-04", "struck")

    def test_rejects_unmapped_row(self) -> None:
        self.repo.inventory([dlg_rule()])
        self.assert_error(self.repo.run()[0], "A:ELI-02", "no rule")

    def test_rejects_rule_without_check(self) -> None:
        rule = val_rule()
        del rule["check"]
        self.repo.inventory([dlg_rule(), rule])
        self.assert_error(self.repo.run()[0], "SR-VAL-001", "no check")

    def test_rejects_missing_check(self) -> None:
        self.repo.inventory([dlg_rule(), val_rule(check="validator:no-such-check")])
        (self.repo.root / "tests/specflow/evals/SR-DLG-001.json").unlink()
        errors, _ = self.repo.run()
        self.assert_error(errors, "SR-VAL-001", "validator:no-such-check")
        self.assert_error(errors, "SR-DLG-001", "evals/SR-DLG-001.json")

    def test_rejects_missing_test_check(self) -> None:
        test = "tests/specflow/review/test_x.py"
        self.repo.write(test, "def test_other():\n    pass\n")
        self.repo.inventory([dlg_rule(), val_rule(check=f"test:{test}::test_y")])
        self.assert_error(self.repo.run()[0], "SR-VAL-001", "test_y")
        self.repo.write(test, "class T:\n    def test_y(self):\n        pass\n")
        self.assertEqual(self.repo.run()[0], [])

    def test_test_check_needs_a_function_definition(self) -> None:
        test = "tests/specflow/review/test_x.py"
        self.repo.write(
            test, '"""Renamed from:\ndef test_y(self):\n"""\n# def test_y():\n'
        )
        self.repo.inventory([dlg_rule(), val_rule(check=f"test:{test}::test_y")])
        self.assert_error(self.repo.run()[0], "SR-VAL-001", "test_y", "does not exist")

    def test_rejects_missing_rule_file(self) -> None:
        self.repo.inventory([dlg_rule(file="phases/requirements.md"), val_rule()])
        self.assert_error(self.repo.run()[0], "SR-DLG-001", "phases/requirements.md")

    def test_rejects_rule_tag_in_two_files(self) -> None:
        self.repo.write(REFS / "phases/intake.md", "- [SR-DLG-001] Ask one question.\n")
        self.assert_error(self.repo.run()[0], "SR-DLG-001", "phases/intake.md")

    def test_rejects_rule_tag_twice_in_its_file(self) -> None:
        self.repo.write(
            REFS / "artifact-contract.md",
            "- [SR-DLG-001] Ask one question.\n- [SR-DLG-001] Ask one question.\n",
        )
        self.assert_error(
            self.repo.run()[0], "SR-DLG-001", "2 times", "artifact-contract.md"
        )

    def test_required_list_is_the_reviewed_ids(self) -> None:
        path = REPO / "tools/specflow/rules/criteria.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["requiredCriteria"], REVIEWED_IDS)
        self.assertEqual(len(set(REVIEWED_IDS)), 33)

    def test_rejects_criterion_with_only_a_decision_source(self) -> None:
        rule = dlg_rule(sources=["A:ELI-01", "D:2026-10-03#11"])
        del rule["criteria"]
        self.repo.inventory([rule, val_rule()])
        self.assert_error(self.repo.run()[0], "ART-002.14", "no rule")

    def test_rejects_missing_criteria_list(self) -> None:
        (self.repo.root / "tools/specflow/rules/criteria.json").unlink()
        self.assert_error(self.repo.run()[0], "criteria.json", "missing")

    def test_rejects_duplicate_criterion_id(self) -> None:
        self.repo.criteria(["ART-002.14", "ART-002.14"])
        self.assert_error(self.repo.run()[0], "ART-002.14", "repeated")

    def test_rejects_malformed_or_empty_criteria_list(self) -> None:
        self.repo.criteria(["ART-002.14", "art 2"])
        self.assert_error(self.repo.run()[0], "art 2", "malformed")
        self.repo.criteria([])
        self.assert_error(self.repo.run()[0], "criteria.json", "empty")
        self.repo.criteria(["ART-002.14"], version=2)
        self.assert_error(self.repo.run()[0], "criteria.json", "schemaVersion")

    def test_rejects_unknown_criterion_id(self) -> None:
        rule = dlg_rule(criteria=["ART-002.14", "ART-002.99"])
        self.repo.inventory([rule, val_rule()])
        self.assert_error(self.repo.run()[0], "SR-DLG-001", "ART-002.99")

    def test_accepts_shared_rule_and_mixed_kind_split(self) -> None:
        # ELI-02 splits into a behavioral and a structural rule; one rule covers two criteria.
        self.repo.criteria(["ART-002.14", "ART-002.16"])
        shared = dlg_rule(
            sources=["A:ELI-01", "A:ELI-02", "D:2026-10-03#12"],
            criteria=["ART-002.14", "ART-002.16"],
        )
        self.repo.inventory([shared, val_rule(sources=["A:ELI-02", "A:ELI-01"])])
        errors, info = self.repo.run()
        self.assertEqual(errors, [])
        self.assertIn("ART-002.16 -> SR-DLG-001 -> evals/SR-DLG-001.json", info)

    def test_area_filter_skips_other_areas_files_only(self) -> None:
        self.repo.inventory(
            [
                dlg_rule(file="phases/requirements.md"),
                val_rule(check="validator:no-such-check"),
            ],
        )
        errors, _ = self.repo.run(frozenset({"VAL"}))
        self.assertFalse([e for e in errors if "SR-DLG-001" in e], errors)
        self.assert_error(errors, "SR-VAL-001", "validator:no-such-check")

    def test_area_filter_still_rejects_unmapped_criterion(self) -> None:
        self.repo.criteria(["ART-002.14", "ART-002.16"])
        self.assert_error(self.repo.run(frozenset({"VAL"}))[0], "ART-002.16", "no rule")
        self.assert_error(self.repo.run(frozenset())[0], "ART-002.16", "no rule")

    def test_prints_criterion_rule_check_rows(self) -> None:
        _, info = self.repo.run()
        self.assertIn("ART-002.14 -> SR-DLG-001 -> evals/SR-DLG-001.json", info)

    def test_prints_row_count_per_plan(self) -> None:
        _, info = self.repo.run()
        self.assertIn("plan A: 4 rows read from docs/plan-a.md", info)

    def test_rejects_table_with_another_header(self) -> None:
        header = "| id | skill | phase | row | classification | reason | code-only | evidence |"
        self.repo.write("docs/plan-a.md", plan(header=header))
        self.assert_error(self.repo.run()[0], "docs/plan-a.md", "header")

    def test_rejects_row_without_eight_cells(self) -> None:
        extra = "| ELI-05 | skill | phase | row | port | why | no |\n"
        self.repo.write("docs/plan-a.md", plan(extra=extra))
        self.assert_error(self.repo.run()[0], "ELI-05", "8 cells")

    def test_splits_cells_on_unescaped_pipes_only(self) -> None:
        extra = "| ELI-05 | skill | phase | a \\| b | port | why \\| not | no | E/SKILL.md:1 |\n"
        self.repo.write("docs/plan-a.md", plan(extra=extra))
        self.repo.inventory([dlg_rule(sources=["A:ELI-01", "A:ELI-05"]), val_rule()])
        errors, info = self.repo.run()
        self.assertEqual(errors, [])
        self.assertIn("plan A: 5 rows read from docs/plan-a.md", info)

    def test_rejects_unknown_classification(self) -> None:
        extra = "| ELI-05 | skill | phase | row | maybe | why | no | e |\n"
        self.repo.write("docs/plan-a.md", plan(extra=extra))
        self.assert_error(self.repo.run()[0], "ELI-05", "maybe")

    def test_rejects_plan_without_matrix_table_or_with_empty_classification(
        self,
    ) -> None:
        self.repo.write(
            "docs/plan-a.md", "# Plan\n\n## Inventory Matrix\n\nNo table.\n"
        )
        self.assert_error(self.repo.run()[0], "docs/plan-a.md", "no matrix table")
        extra = "| ELI-05 | skill | phase | row |  | why | no | e |\n"
        self.repo.write("docs/plan-a.md", plan(extra=extra))
        self.assert_error(self.repo.run()[0], "ELI-05", "empty classification")

    def test_rejects_matrix_table_without_a_row(self) -> None:
        self.repo.write("docs/plan-a.md", plan(rows={}))
        self.assert_error(self.repo.run()[0], "docs/plan-a.md", "no row")

    def test_rejects_plan_key_or_path_of_another_shape(self) -> None:
        for plans in (
            {"A": 42},
            {"A": ""},
            {"D": "docs/plan-a.md"},
            {"AB": "docs/plan-a.md"},
        ):
            with self.subTest(plans=plans):
                data = {"schemaVersion": 1, "plans": plans, "rules": [val_rule()]}
                self.repo.write("tools/specflow/rules/inventory.json", json.dumps(data))
                self.assert_error(self.repo.run()[0], "inventory.json", "plan key")

    def test_rejects_source_naming_unknown_row_or_plan(self) -> None:
        rule = dlg_rule(sources=["A:ELI-01", "A:ELI-99", "B:PLT-01"])
        self.repo.inventory([rule, val_rule()])
        errors, _ = self.repo.run()
        self.assert_error(errors, "SR-DLG-001", "A:ELI-99", "unknown row")
        self.assert_error(errors, "SR-DLG-001", "B:PLT-01", "unknown plan")

    def test_rejects_folder_as_rule_file(self) -> None:
        (self.repo.root / REFS / "review/design").mkdir(parents=True)
        self.repo.inventory([dlg_rule(file="review/design"), val_rule()])
        self.assert_error(self.repo.run()[0], "SR-DLG-001", "not a file")

    def test_only_the_list_item_form_is_a_tag(self) -> None:
        text = (
            "See SR-DLG-001 and [SR-DLG-001].\n* [SR-DLG-001] star item\n"
            "```\n- [SR-DLG-001] fenced\n```\n"
        )
        self.repo.write(REFS / "artifact-contract.md", text)
        self.assert_error(
            self.repo.run()[0], "SR-DLG-001", "tag", "artifact-contract.md"
        )
        self.repo.write(
            REFS / "artifact-contract.md", text + "  - [SR-DLG-001] Nested.\n"
        )
        self.assertEqual(self.repo.run()[0], [])

    def test_script_tag_is_a_comment_line(self) -> None:
        script = self.repo.write(
            "plugins/specflow/skills/spec-workflow/scripts/check_links.py",
            "# [SR-RVX-001] Scan the specs folder.\n",
        )
        test = "tests/specflow/review/test_check_links.py"
        self.repo.write(test, "def test_scan():\n    pass\n")
        rule = val_rule(
            id="SR-RVX-001",
            file="scripts/check_links.py",
            check=f"test:{test}::test_scan",
        )
        self.repo.inventory([dlg_rule(), val_rule(), rule])
        self.assertEqual(self.repo.run()[0], [])
        script.write_text('"""[SR-RVX-001] in a docstring."""\n', encoding="utf-8")
        self.assert_error(self.repo.run()[0], "SR-RVX-001", "tag")

    def test_rejects_unreadable_inventory(self) -> None:
        self.repo.write("tools/specflow/rules/inventory.json", "{not json")
        self.assert_error(self.repo.run()[0], "inventory.json", "JSON")
        (self.repo.root / "tools/specflow/rules/inventory.json").unlink()
        self.assert_error(self.repo.run()[0], "inventory.json", "missing")

    def test_rejects_inventory_that_fails_its_schema(self) -> None:
        self.repo.inventory(
            [dlg_rule(text="Ask one question."), val_rule(kind="other")]
        )
        errors, _ = self.repo.run()
        self.assert_error(errors, "inventory.json", "text")
        self.assert_error(errors, "inventory.json", "kind")

    def test_rejects_unsupported_inventory_version(self) -> None:
        self.repo.inventory([dlg_rule(), val_rule()], version=2)
        self.assert_error(self.repo.run()[0], "inventory.json", "schemaVersion")

    def test_rejects_criteria_list_that_fails_its_schema(self) -> None:
        self.repo.criteria("ART-002.14")
        self.assert_error(self.repo.run()[0], "criteria.json", "requiredCriteria")

    def test_rejects_repeated_rule_id(self) -> None:
        self.repo.inventory([dlg_rule(), val_rule(), val_rule(sources=["A:ELI-01"])])
        self.assert_error(self.repo.run()[0], "SR-VAL-001", "repeated")

    def test_rejects_kind_and_check_mismatch(self) -> None:
        self.repo.inventory([dlg_rule(kind="structural"), val_rule(kind="behavioral")])
        errors, _ = self.repo.run()
        self.assert_error(errors, "SR-DLG-001", "structural")
        self.assert_error(errors, "SR-VAL-001", "behavioral")

    def test_rejects_eval_check_of_another_rule(self) -> None:
        self.repo.inventory([dlg_rule(check="evals/SR-DLG-002.json"), val_rule()])
        errors, _ = self.repo.run()
        self.assert_error(errors, "SR-DLG-001", "evals/SR-DLG-002.json", "another rule")

    def test_rejects_rule_file_under_aws(self) -> None:
        self.repo.write(
            REFS / "aws/requirements.md", "- [SR-DLG-001] Ask one question.\n"
        )
        (self.repo.root / REFS / "artifact-contract.md").unlink()
        self.repo.inventory([dlg_rule(file="aws/requirements.md"), val_rule()])
        self.assert_error(self.repo.run()[0], "SR-DLG-001", "aws/")

    def test_rejects_tag_of_no_rule(self) -> None:
        self.repo.write(
            REFS / "phases/intake.md", "- [SR-INT-009] Not in the inventory.\n"
        )
        self.assert_error(
            self.repo.run(frozenset())[0], "SR-INT-009", "phases/intake.md"
        )

    def test_area_none_skips_file_tag_and_check_tests(self) -> None:
        (self.repo.root / REFS / "artifact-contract.md").unlink()
        (self.repo.root / REFS / "validation-rules.md").unlink()
        (self.repo.root / "tests/specflow/evals/SR-DLG-001.json").unlink()
        self.assertEqual(self.repo.run(frozenset())[0], [])
        self.assertTrue(self.repo.run()[0])

    def test_unknown_area_is_a_usage_error(self) -> None:
        stderr = io.StringIO()
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(stderr),
        ):
            self.assertEqual(check_rules.main(["--area", "XYZ"], self.repo.root), 2)
            self.assertEqual(check_rules.main(["--area", "VAL"], self.repo.root), 0)
        self.assertIn("XYZ", stderr.getvalue())

    def test_main_exits_1_on_a_failure(self) -> None:
        self.repo.inventory([dlg_rule()])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(check_rules.main([], self.repo.root), 1)
        self.assertIn("error: A:ELI-02: ", err.getvalue())
        self.assertIn("plan A: 4 rows read", out.getvalue())

    def test_eval_format_tests_run_on_their_own(self) -> None:
        discover = [
            "discover",
            "-s",
            "tests/specflow/rules",
            "-p",
            "test_eval_formats.py",
        ]
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", *discover],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sets_the_bytecode_flag_before_importing_the_helper(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
        with tempfile.TemporaryDirectory() as cache:
            env["PYTHONPYCACHEPREFIX"] = cache
            result = subprocess.run(
                [sys.executable, "tools/specflow/check_rules.py", "--area", "none"],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            written = [
                p
                for p in Path(cache).rglob("*.pyc")
                if "specflow_helper" in p.relative_to(cache).as_posix()
            ]
            self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
