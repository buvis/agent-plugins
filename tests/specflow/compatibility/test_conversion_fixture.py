"""Compare conversion structure; semantic obligation coverage uses the live rubric."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/specflow/evals/runners"))
import score

FIXTURE = ROOT / "tests/specflow/fixtures/conversion/calcard-00032"
NAME = "00032-add-if-match-preconditions-to-event-writes"
SPEC = f"docs/dev/project-management/specs/{NAME}"
INTAKE = f"docs/dev/project-management/intake/processed/{NAME}"


def read_tree(path: Path) -> dict[str, str]:
    return {
        p.relative_to(path).as_posix(): p.read_text()
        for p in path.rglob("*")
        if p.is_file()
    }


def compare_conversion(actual: dict[str, str], expected: dict[str, str]) -> list[str]:
    """Compare stable shape, not timestamps, identifiers, hashes, or model prose."""
    failures = []
    expected_paths = set(expected)
    actual_paths = {p for p in actual if p.startswith((SPEC + "/", INTAKE + "/"))}
    if actual_paths != expected_paths:
        failures.append("artifact file set differs")
    bugfix = actual.get(SPEC + "/bugfix.md", "")
    reference = expected[SPEC + "/bugfix.md"]
    headings = lambda text: re.findall(r"^#{2,3} (.+)$", text, re.MULTILINE)
    if headings(bugfix) != headings(reference):
        failures.append("bugfix headings differ")
    clauses = lambda text: re.findall(r"^(\d+\.\d+)\s+\S", text, re.MULTILINE)
    if clauses(bugfix) != clauses(reference):
        failures.append("behavior clause numbers differ")
    if not re.search(r"^Sources:.*" + re.escape(INTAKE), bugfix, re.MULTILINE):
        failures.append("processed intake provenance missing")
    tasks = actual.get(SPEC + "/tasks.md", "")
    reference_tasks = expected[SPEC + "/tasks.md"]
    task_order = lambda text: re.findall(
        r"^- \[[ xX]\] (\d+)\. (.+)$", text, re.MULTILINE
    )
    actual_order = task_order(tasks)
    if [n for n, _ in actual_order] != ["1", "2", "3", "4"]:
        failures.append("four top-level tasks missing or reordered")
    for (_, title), words in zip(
        actual_order, ("explor", "preserv", "implement", "checkpoint|verif")
    ):
        if not re.search(words, title, re.IGNORECASE):
            failures.append("bugfix task order differs")
    checked = lambda text: set(
        re.findall(r"^\s*- \[[xX]\] ([\d.]+)", text, re.MULTILINE)
    )
    if not checked(reference_tasks) <= checked(tasks):
        failures.append("completed task unchecked")
    return failures


class ConversionFixtureTest(unittest.TestCase):
    def test_faithful_reference(self) -> None:
        expected = read_tree(FIXTURE / "expected")
        self.assertEqual(compare_conversion(expected, expected), [])

    def test_dropped_clause(self) -> None:
        expected = read_tree(FIXTURE / "expected")
        actual = dict(expected)
        key = SPEC + "/bugfix.md"
        actual[key] = re.sub(r"^2\.7 .*\n", "", actual[key], flags=re.MULTILINE)
        self.assertIn(
            "behavior clause numbers differ", compare_conversion(actual, expected)
        )

    def test_unchecked_completed_task(self) -> None:
        expected = read_tree(FIXTURE / "seeded")
        actual = dict(expected)
        key = SPEC + "/tasks.md"
        actual[key] = actual[key].replace("- [x] 1.", "- [ ] 1.", 1)
        self.assertIn("completed task unchecked", compare_conversion(actual, expected))

    def test_seeded_completion_is_preserved(self) -> None:
        expected = read_tree(FIXTURE / "seeded")
        self.assertEqual(compare_conversion(expected, expected), [])

    def check_host(self, host: str) -> None:
        folder = ROOT / "tests/specflow/evals/results" / host / "conversion-calcard"
        records = sorted(folder.glob("*.json"), key=lambda p: int(p.stem))
        if not records:
            self.skipTest(f"{host}: no live conversion record")
        record = score.read_json(records[-1])
        self.assertNotIn("notRun", record)
        self.assertNotIn("brokenAt", record)
        files = score.finished_files(record, ROOT / "tests/specflow/evals/results")
        self.assertEqual(compare_conversion(files, read_tree(FIXTURE / "expected")), [])
        self.assertEqual(
            score.validation_findings(
                files, "conversion-receipt", record["runtimeRevision"]
            ),
            [],
        )

    def test_claude_record(self) -> None:
        self.check_host("claude-code")

    def test_codex_record(self) -> None:
        self.check_host("codex")

    def test_kiro_record(self) -> None:
        self.check_host("kiro-ide")
