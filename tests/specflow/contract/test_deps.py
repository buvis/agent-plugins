"""Spec dependencies: grammar, resolution, graph, and the implementation gate (T-026)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import support
from specflow_helper.deps import dependency_blockers, parse_depends_on

DONE_TASKS = support.TASKS.replace("[ ]", "[x]")
BUGFIX = """# Bugfix Requirements Document

## Introduction

Rows go missing.

Depends on: {deps}
Sources: docs/intake/processed/00050-rows

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a file ends early THEN the system drops a row
"""


def requirements(deps: str | None) -> str:
    if deps is None:
        return support.REQUIREMENTS
    return support.REQUIREMENTS.replace(
        "\n\n## Purpose",
        f"\nDepends on: {deps}\n\n## Purpose",
        1,
    )


class DepsTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.specs = self.tmp / "specs"
        self.specs.mkdir()

    def make(
        self,
        name: str,
        deps: str | None = None,
        *,
        complete: bool = True,
        order: str = "requirements-first",
    ) -> Path:
        spec = support.write_spec(
            self.specs / name,
            {
                "requirements.md": requirements(deps),
                "design.md": support.DESIGN,
                "tasks.md": DONE_TASKS if complete else support.TASKS,
            },
        )
        state = support.new_state(name, workflowOrder=order)
        support.approve(spec, state, "requirements", "design", "tasks")
        return spec

    def reasons(self, spec: Path) -> list[tuple[str, str, str]]:
        return [
            (b["spec"], b["reference"], b["reason"])
            for b in dependency_blockers(spec, self.specs)
        ]


class GrammarTest(unittest.TestCase):
    def test_absent_declaration_means_no_prerequisite(self) -> None:
        self.assertEqual(parse_depends_on(support.REQUIREMENTS, bugfix=False), ([], []))

    def test_items_are_trimmed_and_repeats_dropped(self) -> None:
        text = requirements(" 00012 , folder:login-fix,00012")
        self.assertEqual(
            parse_depends_on(text, bugfix=False),
            (["00012", "folder:login-fix"], []),
        )

    def test_each_unsupported_form_is_named(self) -> None:
        for item in (
            "12",
            "folder:",
            "folder:..",
            "folder:a/b",
            "https://x",
            "folder:a\\b",
        ):
            with self.subTest(item=item):
                refs, findings = parse_depends_on(requirements(item), bugfix=False)
                self.assertEqual(refs, [])
                self.assertEqual(
                    [f["message"] for f in findings],
                    [f"unsupported reference {item!r}"],
                )

    def test_empty_repeated_and_misplaced_declarations(self) -> None:
        _, empty = parse_depends_on(requirements(""), bugfix=False)
        self.assertEqual([f["message"] for f in empty], ["empty declaration"])
        twice = requirements("00012").replace(
            "Depends on: 00012",
            "Depends on: 00012\nDepends on: 00013",
        )
        _, repeated = parse_depends_on(twice, bugfix=False)
        self.assertEqual(
            [f["message"] for f in repeated],
            ["repeated declaration: Depends on: 00013"],
        )
        late = support.REQUIREMENTS + "\nDepends on: 00012\n"
        refs, misplaced = parse_depends_on(late, bugfix=False)
        self.assertEqual(refs, [])
        self.assertEqual(
            [f["message"] for f in misplaced],
            ["misplaced declaration: Depends on: 00012"],
        )

    def test_fenced_indented_and_list_fields_declare_nothing(self) -> None:
        for text in (
            "# R\n\n```\nDepends on: 00012\n```\n\n## Purpose\n",
            "# R\n\n  Depends on: 00012\n\n## Purpose\n",
            "# R\n\n- Depends on: 00012\n\n## Purpose\n",
        ):
            with self.subTest(text=text):
                self.assertEqual(parse_depends_on(text, bugfix=False), ([], []))

    def test_bugfix_declares_at_the_end_of_its_introduction(self) -> None:
        refs, findings = parse_depends_on(BUGFIX.format(deps="00012"), bugfix=True)
        self.assertEqual((refs, findings), (["00012"], []))
        header = "Depends on: 00012\n\n" + BUGFIX.format(deps="00013")
        refs, findings = parse_depends_on(header, bugfix=True)
        self.assertEqual(refs, ["00013"])
        self.assertEqual(
            [f["message"] for f in findings],
            ["misplaced declaration: Depends on: 00012"],
        )


class ResolutionTest(DepsTest):
    def test_numbered_and_native_references_to_complete_specs_open_the_gate(
        self,
    ) -> None:
        self.make("00012-base")
        self.make("login-fix")
        spec = self.make("00050-main", "00012, folder:login-fix")
        self.assertEqual(self.reasons(spec), [])

    def test_two_references_to_one_folder_count_once(self) -> None:
        self.make("00012-base", complete=False)
        spec = self.make("00050-main", "00012, folder:00012-base")
        self.assertEqual(
            self.reasons(spec),
            [("00050-main", "00012", "incomplete prerequisite (phase implementation)")],
        )

    def test_stale_prerequisite_blocks(self) -> None:
        base = self.make("00012-base")
        spec = self.make("00050-main", "00012")
        (base / "design.md").write_text(support.DESIGN + "Changed.\n")
        self.assertEqual(
            self.reasons(spec),
            [("00050-main", "00012", "incomplete prerequisite (phase design)")],
        )

    def test_missing_ambiguous_and_unreadable_targets(self) -> None:
        self.make("00013-one")
        self.make("00013-two")
        unreadable = self.make("00014-locked")
        (unreadable / "requirements.md").write_bytes(b"\xff\xfe")
        spec = self.make("00050-main", "00012, 00013, 00014")
        reasons = {ref: reason for _, ref, reason in self.reasons(spec)}
        self.assertEqual(reasons["00012"], "missing target")
        self.assertEqual(reasons["00013"], "ambiguous target: 00013-one, 00013-two")
        self.assertTrue(reasons["Depends on:"].startswith("unreadable target"))

    def test_prerequisite_state_that_cannot_be_reconciled_blocks(self) -> None:
        base = self.make("00012-base")
        (base / ".specflow.json").write_text("{")
        spec = self.make("00050-main", "00012")
        [(_, ref, reason)] = self.reasons(spec)
        self.assertEqual(ref, "00012")
        self.assertTrue(reason.startswith("state cannot be reconciled"))

    def test_declaration_errors_close_the_gate_with_their_message(self) -> None:
        spec = self.make("00050-main", "folder:a/b")
        self.assertEqual(
            self.reasons(spec),
            [("00050-main", "Depends on:", "unsupported reference 'folder:a/b'")],
        )

    def test_bugfix_and_design_first_specs_resolve_alike(self) -> None:
        self.make("00012-base")
        bugfix = support.write_spec(
            self.specs / "00051-bug",
            {"bugfix.md": BUGFIX.format(deps="00012")},
        )
        self.assertEqual(self.reasons(bugfix), [])
        design_first = self.make("00052-df", "00012", order="design-first")
        self.assertEqual(self.reasons(design_first), [])


class GraphTest(DepsTest):
    def test_self_reference(self) -> None:
        spec = self.make("00050-main", "00050")
        self.assertEqual(
            self.reasons(spec),
            [("00050-main", "00050", "self-reference")],
        )

    def test_cycle_names_its_path(self) -> None:
        self.make("login-fix", "00050")
        spec = self.make("00050-main", "folder:login-fix")
        cycle = [
            b for b in dependency_blockers(spec, self.specs) if b["reason"] == "cycle"
        ]
        self.assertEqual(len(cycle), 1)
        self.assertEqual(cycle[0]["path"], "00050-main → login-fix → 00050-main")

    def test_invalid_reference_deeper_in_the_graph_blocks(self) -> None:
        self.make("00012-base", "00099")
        spec = self.make("00050-main", "00012")
        self.assertEqual(
            self.reasons(spec),
            [("00012-base", "00099", "missing target")],
        )

    def test_complete_prerequisite_stays_complete_when_its_own_prerequisite_is_not(
        self,
    ) -> None:
        self.make("00011-root", complete=False)
        self.make("00012-base", "00011")
        spec = self.make("00050-main", "00012")
        self.assertEqual(self.reasons(spec), [])

    def test_unrelated_specs_are_never_read_and_nothing_is_written(self) -> None:
        self.make("00012-base")
        unrelated = self.make("00070-unrelated") / "requirements.md"
        unrelated.chmod(0)
        self.addCleanup(unrelated.chmod, 0o644)
        spec = self.make("00050-main", "00012")
        files = [p for p in self.specs.rglob("*") if p.is_file() and p != unrelated]
        before = {p: p.read_bytes() for p in files}
        self.assertEqual(self.reasons(spec), [])
        self.assertEqual({p: p.read_bytes() for p in files}, before)

    def test_blockers_change_no_approval_record(self) -> None:
        spec = self.make("00050-main", "00099", complete=False)
        before = json.loads((spec / ".specflow.json").read_text())
        self.assertTrue(self.reasons(spec))
        self.assertEqual(json.loads((spec / ".specflow.json").read_text()), before)


if __name__ == "__main__":
    unittest.main()
