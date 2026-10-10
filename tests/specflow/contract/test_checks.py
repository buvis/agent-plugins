"""One seeded defect per row of the check table; template-filled specs pass (T-026)."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.checks import CHECKS, validate

SPECS = support.FIXTURES / "specs"
T026_ROWS = {
    "required-files",
    "state-valid",
    "state-content",
    "spec-type",
    "requirement-ids",
    "design-sections",
    "task-structure",
    "requirement-coverage",
    "progress-fields",
    "cross-spec-references",
    "gates",
    "spec-dependencies",
}


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


class ChecksTest(support.TempTest):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.tmp / "repo"
        self.specs = self.repo / ".kiro" / "specs"
        self.specs.mkdir(parents=True)

    def copy(self, name: str, as_name: str | None = None) -> Path:
        target = self.specs / (as_name or name)
        shutil.copytree(SPECS / name, target)
        return target

    def rules(
        self,
        spec: Path,
        phase: str | None = None,
        level: str = "error",
    ) -> set[str]:
        return {
            f["rule"] for f in validate(self.repo, spec, phase) if f["level"] == level
        }

    def edit(self, path: Path, old: str, new: str) -> None:
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1))

    def assert_seeded(self, spec: Path, rule: str, phase: str | None = None) -> None:
        findings = [f for f in validate(self.repo, spec, phase) if f["rule"] == rule]
        self.assertTrue(findings, f"no {rule} finding")
        for finding in findings:
            self.assertTrue(
                finding["file"] and finding["message"] and finding["fix"],
                finding,
            )


class TemplateSpecsPassTest(ChecksTest):
    def test_spec_filled_from_each_template_passes_with_no_error(self) -> None:
        for name in ("00101-feature-sample", "00102-bugfix-sample"):
            with self.subTest(name=name):
                self.assertEqual(self.rules(self.copy(name)), set())

    def test_every_t026_row_is_registered(self) -> None:
        self.assertEqual(T026_ROWS - set(CHECKS), set())

    def test_validate_writes_nothing(self) -> None:
        spec = self.copy("00101-feature-sample")
        (spec / "tasks.md").write_text("- []  broken\n")
        before = snapshot(self.repo)
        validate(self.repo, spec)
        validate(self.repo, spec, "implementation")
        self.assertEqual(snapshot(self.repo), before)


class SeededDefectTest(ChecksTest):
    def test_required_files(self) -> None:
        spec = self.copy("00101-feature-sample")
        state = support.approve(
            spec,
            support.new_state("00101-feature-sample"),
            "requirements",
        )
        (spec / "requirements.md").unlink()
        support.write_state(spec, state)
        self.assert_seeded(spec, "required-files")

    def test_required_files_reports_an_unreadable_artifact(self) -> None:
        spec = self.copy("00101-feature-sample")
        (spec / "design.md").write_bytes(b"\xff\xfe")
        self.assert_seeded(spec, "required-files")

    def test_state_valid(self) -> None:
        spec = self.copy("00101-feature-sample")
        (spec / ".specflow.json").write_text('{"schemaVersion": 1}')
        self.assert_seeded(spec, "state-valid")

    def test_state_content(self) -> None:
        spec = self.copy("00101-feature-sample")
        state = support.new_state("00101-feature-sample", transcript="hello")
        support.write_state(spec, state)
        self.assert_seeded(spec, "state-content")

    def test_spec_type(self) -> None:
        spec = self.copy("00101-feature-sample")
        support.write_state(
            spec,
            support.new_state("00101-feature-sample", specType="bugfix"),
        )
        self.assert_seeded(spec, "spec-type")

    def test_requirement_ids_duplicate_and_missing_criterion(self) -> None:
        spec = self.copy("00101-feature-sample")
        path = spec / "requirements.md"
        self.edit(path, "### REQ-002: Report", "### REQ-001: Report")
        self.assert_seeded(spec, "requirement-ids")
        spec = self.copy("00101-feature-sample", "00103-copy")
        text = (spec / "requirements.md").read_text()
        cut = text.split("### REQ-002")[0] + "### REQ-002: Empty\n\n## Risks\n"
        (spec / "requirements.md").write_text(cut)
        self.assert_seeded(spec, "requirement-ids")

    def test_requirement_ids_bugfix_clause_pattern_and_numbering(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "bugfix.md", "2.1 WHEN", "2.2 WHEN")
        self.assert_seeded(spec, "requirement-ids")
        spec = self.copy("00102-bugfix-sample", "00104-copy")
        self.edit(spec / "bugfix.md", "SHALL CONTINUE TO import", "SHALL import")
        self.assert_seeded(spec, "requirement-ids")

    def test_design_sections_missing_section_and_empty_reason(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "design.md", "## Reuse inventory\n", "")
        self.assert_seeded(spec, "design-sections")
        spec = self.copy("00101-feature-sample", "00103-copy")
        old = "Not applicable: the retry file starts empty."
        self.edit(spec / "design.md", old, "Not applicable:")
        self.assert_seeded(spec, "design-sections")

    def test_design_sections_traceability_cites_an_unknown_criterion(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "design.md", "REQ-002.1 |", "REQ-002.7 |")
        self.assert_seeded(spec, "design-sections")

    def test_design_sections_skips_cross_spec_and_non_id_entries(self) -> None:
        spec = self.copy("00101-feature-sample")
        new = "| 00004 WF-004 criterion 8, Portability |"
        self.edit(spec / "design.md", "| Portability |", new)
        self.assertNotIn("design-sections", self.rules(spec))

    def test_design_sections_lets_kiro_designs_keep_their_headings(self) -> None:
        spec = self.specs / "kiro-design-first"
        shutil.copytree(support.FIXTURES / "kiro" / "design-first", spec)
        self.assertNotIn("design-sections", self.rules(spec))

    def test_design_sections_ignores_the_heading_inside_a_fence(self) -> None:
        spec = self.copy("00101-feature-sample")
        fenced = (
            "```\n## Requirement traceability\n| x | Criteria |\n| a | REQ-999.1 |\n```\n\n"
            "## Open decisions\n"
        )
        self.edit(spec / "design.md", "## Open decisions\n", fenced)
        self.assertNotIn("design-sections", self.rules(spec))

    def test_task_structure(self) -> None:
        for number, (old, new) in enumerate(
            (
                ("- [ ] T-002 Log", "- [] T-002 Log"),
                ("- [ ] T-002 Log", "- [ ] T-001 Log"),
                ("- [ ] T-002 Log", "- [ ] Log"),
                ("  - Depends on: T-001", "  - Depends on: T-009"),
                ("  - Verify: `python -m unittest tests.test_log`\n", ""),
            ),
        ):
            with self.subTest(new=new):
                spec = self.copy("00101-feature-sample", f"0011{number}-case")
                self.edit(spec / "tasks.md", old, new)
                self.assert_seeded(spec, "task-structure")

    def test_requirement_coverage(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: REQ-001\n",
        )
        self.assert_seeded(spec, "requirement-coverage")

    def test_requirement_coverage_reads_kiro_traces(self) -> None:
        spec = self.specs / "kiro-design-first"
        shutil.copytree(support.FIXTURES / "kiro" / "design-first", spec)
        findings = [
            f for f in validate(self.repo, spec) if f["rule"] == "requirement-coverage"
        ]
        self.assertEqual([f["message"] for f in findings], ["no task references 8"])

    def test_progress_fields_warn_only_before_approval(self) -> None:
        spec = self.copy("00101-feature-sample")
        verify = "  - Verify: `python -m unittest tests.test_log`"
        self.edit(spec / "tasks.md", verify, f"{verify}\n  - Outcome: done")
        self.assertIn("progress-fields", self.rules(spec, level="warning"))
        self.assertNotIn("progress-fields", self.rules(spec))
        state = support.new_state("00101-feature-sample")
        support.approve(spec, state, "requirements", "design", "tasks")
        self.assertNotIn("progress-fields", self.rules(spec, level="warning"))

    def test_cross_spec_references(self) -> None:
        self.copy("00101-feature-sample", "00090-base")
        cases = (
            ("00090 REQ-001 criterion 1", False, "not on the Depends on: line"),
            ("00090 REQ-009 criterion 1", True, "holds no REQ-009"),
            ("00090 REQ-001 criteria 1, 7", True, "holds no criterion 7"),
        )
        for number, (cited, declared, message) in enumerate(cases):
            with self.subTest(cited=cited):
                spec = self.copy("00101-feature-sample", f"0012{number}-dep")
                if declared:
                    self.edit(
                        spec / "requirements.md",
                        "Sources:",
                        "Depends on: 00090\nSources:",
                    )
                requirements = f"  - Requirements: REQ-002; {cited}\n"
                self.edit(
                    spec / "tasks.md",
                    "  - Requirements: REQ-002\n",
                    requirements,
                )
                findings = [
                    f
                    for f in validate(self.repo, spec)
                    if f["rule"] == "cross-spec-references"
                ]
                self.assertTrue(
                    any(message in f["message"] for f in findings),
                    findings,
                )

    def test_cross_spec_reference_to_a_held_criterion_passes(self) -> None:
        self.copy("00101-feature-sample", "00090-base")
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "requirements.md", "Sources:", "Depends on: 00090\nSources:")
        requirements = "  - Requirements: REQ-002; 00090 REQ-001 criteria 1, 2\n"
        self.edit(spec / "tasks.md", "  - Requirements: REQ-002\n", requirements)
        self.assertNotIn("cross-spec-references", self.rules(spec))

    def test_gates(self) -> None:
        spec = self.copy("00101-feature-sample")
        support.approve(
            spec,
            support.new_state("00101-feature-sample"),
            "requirements",
            "design",
        )
        self.assert_seeded(spec, "gates", "implementation")
        self.assertNotIn("gates", self.rules(spec))

    def test_spec_dependencies(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md",
            "## Scope",
            "## Scope\n\nDepends on: 00090\n",
        )
        self.assert_seeded(spec, "spec-dependencies")
        self.assert_seeded(spec, "spec-dependencies", "implementation")
        self.assertNotIn("spec-dependencies", self.rules(spec, "design"))


class IntakeTest(ChecksTest):
    def test_intake_item_needs_its_idea(self) -> None:
        item = self.repo / ".kiro" / "specflow" / "intake" / "new" / "00105-idea"
        item.mkdir(parents=True)
        self.assertEqual(self.rules(item, "intake"), {"required-files"})
        (item / "idea.md").write_text("Make imports retry.\n")
        self.assertEqual(self.rules(item, "intake"), set())


class StateErrorTest(ChecksTest):
    def test_unsupported_version_is_a_state_valid_error(self) -> None:
        spec = self.copy("00101-feature-sample")
        (spec / ".specflow.json").write_text(
            json.dumps(support.new_state(schemaVersion=2)),
        )
        self.assertIn("state-valid", self.rules(spec))


if __name__ == "__main__":
    unittest.main()
