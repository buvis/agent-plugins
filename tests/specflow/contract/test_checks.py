"""One seeded defect per row of the check table; template-filled specs pass (T-026)."""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

import support
from specflow_helper.canonical import CHECKBOX
from specflow_helper.checks import BAD_CHECKBOX, CHECKS, ID_ENTRY, validate
from specflow_helper.reconcile import reconcile
from specflow_helper.spec_text import (
    CLAUSE,
    CRITERION,
    CROSS_SPEC,
    REQUIREMENT_HEADING,
    traced_ids,
)
from specflow_helper.state import TASK_ID, TASK_LINE
from specflow_helper.status import LIST_ITEM

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

    def test_bugfix_clause_pattern_and_numbering(self) -> None:
        spec = self.copy("00102-bugfix-sample")
        self.edit(spec / "bugfix.md", "2.1 WHEN", "2.2 WHEN")
        self.assert_seeded(spec, "bugfix-clauses")
        spec = self.copy("00102-bugfix-sample", "00104-copy")
        self.edit(spec / "bugfix.md", "SHALL CONTINUE TO import", "SHALL import")
        self.assert_seeded(spec, "bugfix-clauses")

    def test_design_sections_missing_section_and_empty_reason(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "design.md", "## Reuse inventory\n", "")
        self.assert_seeded(spec, "design-sections")
        spec = self.copy("00101-feature-sample", "00103-copy")
        old = "Not applicable: the retry file starts empty."
        self.edit(spec / "design.md", old, "Not applicable:")
        self.assert_seeded(spec, "design-sections")

    def test_design_sections_still_apply_to_a_retitled_template_design(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "design.md", "# Design: ", "# Design Document: ")
        self.edit(spec / "design.md", "## Reuse inventory\n", "")
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
        for capture in ("design-first", "requirements-first", "bugfix"):
            with self.subTest(capture=capture):
                spec = self.specs / f"kiro-{capture}"
                shutil.copytree(support.FIXTURES / "kiro" / capture, spec)
                self.assertNotIn("design-sections", self.rules(spec))

    def test_design_sections_lets_a_recased_kiro_design_keep_its_headings(self) -> None:
        spec = self.specs / "kiro-recased"
        shutil.copytree(support.FIXTURES / "kiro" / "requirements-first", spec)
        for old in ("Components and Interfaces", "Error Handling", "Testing Strategy"):
            self.edit(spec / "design.md", f"## {old}\n", f"## {old.capitalize()}\n")
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

    def coverage_messages(self, spec: Path) -> list[str]:
        return [
            f["message"]
            for f in validate(self.repo, spec)
            if f["rule"] == "requirement-coverage"
        ]

    def test_requirement_coverage_refuses_a_cited_requirement_the_spec_lacks(
        self,
    ) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: REQ-002, REQ-999\n",
        )
        self.assertEqual(
            self.coverage_messages(spec),
            ["line 12: cites REQ-999, which requirements.md does not hold"],
        )

    def test_requirement_coverage_refuses_a_cited_criterion_the_spec_lacks(
        self,
    ) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Acceptance criteria: REQ-001 criteria 1, 2\n",
            "  - Acceptance criteria: REQ-001 criteria 1, 7\n",
        )
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: REQ-002.4\n",
        )
        self.assertEqual(
            self.coverage_messages(spec),
            [
                "line 9: cites REQ-001 criterion 7, which requirements.md does not hold",
                "line 12: cites REQ-002 criterion 4, which requirements.md does not hold",
            ],
        )

    def test_requirement_coverage_accepts_every_held_citation(self) -> None:
        self.assertEqual(self.coverage_messages(self.copy("00101-feature-sample")), [])

    def test_requirement_coverage_reads_stray_prose_as_no_citation(self) -> None:
        values = (
            "REQ-001 criteria 1 and 2",
            "REQ-001 criteria 1-2",
            "REQ-001 criteria 1,  2",
            "REQ-001 criteria 1, 2 (see design §3)",
            "REQ-001 criteria 1, 2, decided 2026-10-14",
            "REQ-001 criteria 1, 2 in section 7",
        )
        for i, value in enumerate(values):
            with self.subTest(value=value):
                spec = self.copy("00101-feature-sample", f"0011{i}-prose")
                self.edit(
                    spec / "tasks.md",
                    "  - Acceptance criteria: REQ-001 criteria 1, 2\n",
                    f"  - Acceptance criteria: {value}\n",
                )
                self.assertEqual(self.coverage_messages(spec), [])

    def test_requirement_coverage_refuses_an_id_that_only_starts_like_a_held_one(
        self,
    ) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: REQ-002, REQ-0010, REQ-001a\n",
        )
        self.assertEqual(
            self.coverage_messages(spec),
            [
                "line 12: cites REQ-0010, which requirements.md does not hold",
                "line 12: cites REQ-001a, which requirements.md does not hold",
            ],
        )

    def test_requirement_coverage_skips_cross_spec_citations(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: 00090 REQ-009 criterion 1, REQ-002\n",
        )
        self.assertEqual(self.coverage_messages(spec), [])

    def test_requirement_coverage_refuses_an_unheld_kiro_citation(self) -> None:
        spec = self.specs / "kiro-design-first"
        shutil.copytree(support.FIXTURES / "kiro" / "design-first", spec)
        self.edit(
            spec / "tasks.md",
            "    - _Requirements: 6.1, 6.2, 6.3, 6.4_\n",
            "    - _Requirements: 6.1, 6.2, 6.3, 6.4, 12.1, 1.9_\n",
        )
        self.assertEqual(
            self.coverage_messages(spec),
            [
                "no task references 8",
                "line 13: cites 12, which requirements.md does not hold",
                "line 13: cites 1 criterion 9, which requirements.md does not hold",
            ],
        )

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

    def test_task_structure_ignores_bracket_labels_below_the_task_list(self) -> None:
        spec = self.copy("00101-feature-sample")
        path = spec / "tasks.md"
        labels = "\n## Unresolved questions\n\n- [Q1] note\n- [RFC] y\n- [] x\n"
        path.write_text(path.read_text() + labels)
        self.assertNotIn("task-structure", self.rules(spec))

    def test_task_structure_ignores_bracket_labels_beside_a_kiro_task_section(
        self,
    ) -> None:
        spec = self.specs / "kiro-design-first"
        shutil.copytree(support.FIXTURES / "kiro" / "design-first", spec)
        self.edit(spec / "tasks.md", "## Tasks\n", "- [Q1] note\n\n## Tasks\n")
        self.edit(spec / "tasks.md", "## Notes\n", "## Notes\n\n- [RFC] y\n- [] x\n")
        self.assertNotIn("task-structure", self.rules(spec))
        self.edit(spec / "tasks.md", "## Notes\n", "- [] 9. Broken\n\n## Notes\n")
        self.assert_seeded(spec, "task-structure")

    def test_task_structure_sees_past_a_fenced_completion_heading(self) -> None:
        spec = self.copy("00101-feature-sample")
        fenced = "```\n## Completion criteria\n```\n- [ ] T-002 Log"
        self.edit(spec / "tasks.md", "- [ ] T-002 Log", fenced)
        self.edit(spec / "tasks.md", "- [ ] T-002 Log", "- [] T-002 Log")
        self.assert_seeded(spec, "task-structure")

    def test_progress_fields_warn_on_a_continued_outcome_even_when_approved(
        self,
    ) -> None:
        spec = self.copy("00101-feature-sample")
        support.approve(
            spec,
            support.new_state("00101-feature-sample"),
            "requirements",
            "design",
            "tasks",
        )
        verify = "  - Verify: `python -m unittest tests.test_log`"
        self.edit(spec / "tasks.md", verify, f"{verify}\n  - Outcome: done")
        self.assertNotIn("progress-fields", self.rules(spec, level="warning"))
        self.edit(
            spec / "tasks.md", "  - Outcome: done", "  - Outcome: done,\n    and more"
        )
        messages = [
            f["message"]
            for f in validate(self.repo, spec)
            if f["rule"] == "progress-fields"
        ]
        continued = [m for m in messages if "continues an Outcome: or Exception:" in m]
        self.assertEqual(len(continued), 1, messages)

    def test_nested_progress_field_is_not_a_continuation(self) -> None:
        spec = self.copy("00101-feature-sample")
        verify = "  - Verify: `python -m unittest tests.test_log`"
        nested = f"{verify}\n  - Outcome: done\n    - Exception: flaky on CI"
        self.edit(spec / "tasks.md", verify, nested)
        state = support.approve(
            spec,
            support.new_state("00101-feature-sample"),
            "requirements",
            "design",
            "tasks",
        )
        self.assertEqual(state["artifacts"]["tasks"]["status"], "approved")
        self.assertNotIn("progress-fields", self.rules(spec, level="warning"))

    def test_cross_spec_reference_matches_either_declared_form(self) -> None:
        self.copy("00101-feature-sample", "00090-base")
        cases = (
            ("folder:00090-base", "00090 REQ-001 criterion 1"),
            ("00090", "folder:00090-base REQ-001 criterion 1"),
        )
        for number, (declared, cited) in enumerate(cases):
            with self.subTest(declared=declared):
                spec = self.copy("00101-feature-sample", f"0013{number}-dep")
                self.edit(
                    spec / "requirements.md",
                    "Sources:",
                    f"Depends on: {declared}\nSources:",
                )
                self.edit(
                    spec / "tasks.md",
                    "  - Requirements: REQ-002\n",
                    f"  - Requirements: REQ-002; {cited}\n",
                )
                self.assertNotIn("cross-spec-references", self.rules(spec))

    def test_restored_artifact_reads_stale_and_says_it_was_deleted(self) -> None:
        spec = self.copy("00101-feature-sample")
        support.approve(spec, support.new_state("00101-feature-sample"), "requirements")
        text = (spec / "requirements.md").read_bytes()
        (spec / "requirements.md").unlink()
        reconcile(spec, dry_run=False)
        (spec / "requirements.md").write_bytes(text)
        messages = [
            f["message"]
            for f in validate(self.repo, spec)
            if f["rule"] == "stale-approvals"
        ]
        self.assertEqual(
            messages,
            [
                "the requirements.md approval is stale: "
                "the file was deleted after its approval",
            ],
        )

    def test_withdrawn_requirement_needs_no_criterion_or_task(self) -> None:
        spec = self.copy("00101-feature-sample")
        withdrawn = "### REQ-009: withdrawn\n\nWithdrawn: cut from scope.\n\n"
        self.edit(spec / "requirements.md", "### REQ-002:", withdrawn + "### REQ-002:")
        rules = self.rules(spec)
        self.assertNotIn("requirement-ids", rules)
        self.assertNotIn("requirement-coverage", rules)

    def test_withdrawn_id_stays_reserved(self) -> None:
        spec = self.copy("00101-feature-sample")
        withdrawn = "### REQ-001: withdrawn\n\n"
        self.edit(spec / "requirements.md", "### REQ-002:", withdrawn + "### REQ-002:")
        self.assert_seeded(spec, "requirement-ids")

    def test_requirement_coverage_counts_a_cited_criterion(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "  - Requirements: REQ-002\n",
            "  - Requirements: REQ-002.1\n",
        )
        self.assertNotIn("requirement-coverage", self.rules(spec))

    def test_required_files_follow_the_requested_phase(self) -> None:
        spec = self.specs / "00106-empty"
        spec.mkdir()
        self.assertNotIn("required-files", self.rules(spec))
        missing = {
            f["file"]
            for f in validate(self.repo, spec, "tasks")
            if f["rule"] == "required-files"
        }
        folder = ".kiro/specs/00106-empty"
        self.assertEqual(missing, {f"{folder}/requirements.md", f"{folder}/design.md"})

    def test_stale_approvals_name_each_stale_artifact_and_its_cause(self) -> None:
        spec = self.copy("00101-feature-sample")
        state = support.new_state("00101-feature-sample")
        support.approve(spec, state, "requirements", "design")
        self.assertNotIn("stale-approvals", self.rules(spec))
        self.edit(spec / "requirements.md", "### REQ-002: Report", "### REQ-002: Tell")
        for phase in (None, "tasks"):
            with self.subTest(phase=phase):
                messages = [
                    f["message"]
                    for f in validate(self.repo, spec, phase)
                    if f["rule"] == "stale-approvals"
                ]
                self.assertEqual(
                    messages,
                    [
                        "the requirements.md approval is stale: "
                        "its content changed since the approval",
                        "the design.md approval is stale: "
                        "upstream requirements.md changed since its approval",
                    ],
                )

    def test_stale_approvals_name_an_approval_that_binds_no_upstream(self) -> None:
        spec = self.copy("00101-feature-sample")
        state = support.new_state("00101-feature-sample")
        support.approve(spec, state, "requirements", "design", "tasks")
        del state["artifacts"]["tasks"]["upstreamSha256"]
        support.write_state(spec, state)
        messages = [
            f["message"]
            for f in validate(self.repo, spec)
            if f["rule"] == "stale-approvals"
        ]
        self.assertEqual(
            messages,
            ["the tasks.md approval is stale: it binds no upstream artifact"],
        )

    def test_specs_folder_starting_with_a_dash_is_not_a_git_option(self) -> None:
        support.git(self.repo, "init", "-q")
        (self.repo / ".agents").mkdir()
        config = {"schemaVersion": 1, "specsDir": "-specs"}
        (self.repo / ".agents" / "specflow.json").write_text(json.dumps(config))
        spec = self.repo / "-specs" / "00101-feature-sample"
        shutil.copytree(SPECS / "00101-feature-sample", spec)
        self.assertNotIn("specs-folder", self.rules(spec))

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


RECEIPT = """
## Conversion receipt 2026-10-18

- Source: docs/prds/00101-import-retries.md
- Destination: .kiro/specs/00101-feature-sample/
- Number, type, folders: 00101, feature, requirements-first
- Obligation coverage: 3 of 3
- Decisions and public-behavior changes: none
- Implementation evidence: none; nothing is built
- Gates: requirements approved; design approved; tasks draft
- Review outcomes: one pre-pass, one walkthrough
- Checks run and limits: validate --phase tasks
- Outstanding questions: none
- Next action: approve the tasks
- Verdict: AWAITING_DECISION (the tasks gate)
"""


class ConversionReceiptTest(ChecksTest):
    """conversion-receipt reads the last receipt of the intake log the Sources: line names (T-080)."""

    def spec_and_log(self, text: str) -> Path:
        spec = self.copy("00101-feature-sample")
        item = (
            self.repo
            / "docs/dev/project-management/intake/processed/00101-import-retries"
        )
        item.mkdir(parents=True)
        (item / "qa-log.md").write_text("# Q&A log: 00101\n" + text, encoding="utf-8")
        return spec

    def test_a_spec_with_no_receipt_block_draws_no_finding(self) -> None:
        spec = self.spec_and_log('\n## Q1 - Size (2026-10-18)\n\n- Answer: "small"\n')
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_receipt_with_every_label_and_a_known_verdict_passes(self) -> None:
        spec = self.spec_and_log(RECEIPT)
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_verdict_with_a_note_and_a_full_stop_passes(self) -> None:
        spec = self.spec_and_log(
            RECEIPT.replace(
                "AWAITING_DECISION (the tasks gate)",
                "COMPLETE (7 tasks planned; implementation not started).",
            )
        )
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_receipt_missing_a_label_is_an_error(self) -> None:
        gates = "- Gates: requirements approved; design approved; tasks draft\n"
        spec = self.spec_and_log(RECEIPT.replace(gates, ""))
        self.assert_seeded(spec, "conversion-receipt")
        messages = [
            f["message"]
            for f in validate(self.repo, spec)
            if f["rule"] == "conversion-receipt"
        ]
        self.assertEqual(messages, ["the last conversion receipt lacks Gates:"])

    def test_a_receipt_with_an_unknown_verdict_is_an_error(self) -> None:
        spec = self.spec_and_log(
            RECEIPT.replace("AWAITING_DECISION (the tasks gate)", "DONE")
        )
        self.assert_seeded(spec, "conversion-receipt")

    def test_the_unfilled_verdict_template_line_is_an_error(self) -> None:
        spec = self.spec_and_log(
            RECEIPT.replace(
                "AWAITING_DECISION (the tasks gate)",
                "<COMPLETE, AWAITING_DECISION, or INCOMPLETE; an optional (note) and full stop>",
            )
        )
        self.assert_seeded(spec, "conversion-receipt")

    def test_the_three_verdicts_as_alternatives_are_an_error(self) -> None:
        spec = self.spec_and_log(
            RECEIPT.replace(
                "AWAITING_DECISION (the tasks gate)",
                "COMPLETE | AWAITING_DECISION | INCOMPLETE",
            )
        )
        self.assert_seeded(spec, "conversion-receipt")

    def test_a_verdict_followed_by_free_text_is_an_error(self) -> None:
        spec = self.spec_and_log(
            RECEIPT.replace(
                "AWAITING_DECISION (the tasks gate)",
                "COMPLETE, but the design is unreviewed",
            )
        )
        self.assert_seeded(spec, "conversion-receipt")

    def test_a_sources_path_outside_the_repo_draws_no_receipt_finding(self) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        broken = RECEIPT.replace("AWAITING_DECISION (the tasks gate)", "DONE")
        (outside / "qa-log.md").write_text(broken, encoding="utf-8")
        for value in (str(outside), "../outside"):
            with self.subTest(value=value):
                spec = self.copy("00101-feature-sample", f"00101-{len(value)}")
                self.edit(
                    spec / "requirements.md",
                    "Sources: docs/dev/project-management/intake/processed/00101-import-retries",
                    f"Sources: {value}",
                )
                self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_sources_item_linked_outside_the_repo_is_not_read(self) -> None:
        outside = self.tmp / "outside"
        outside.mkdir()
        broken = RECEIPT.replace("AWAITING_DECISION (the tasks gate)", "DONE")
        (outside / "qa-log.md").write_text(broken, encoding="utf-8")
        spec = self.copy("00101-feature-sample")
        processed = self.repo / "docs/dev/project-management/intake/processed"
        processed.mkdir(parents=True)
        (processed / "00101-import-retries").symlink_to(outside)
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_looped_sources_item_draws_no_finding_and_no_crash(self) -> None:
        spec = self.copy("00101-feature-sample")
        processed = self.repo / "docs/dev/project-management/intake/processed"
        processed.mkdir(parents=True)
        loop = processed / "00101-import-retries"
        loop.symlink_to(loop)
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_sources_item_with_no_qa_log_draws_no_finding(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_complete_receipt_after_a_broken_one_passes(self) -> None:
        broken = RECEIPT.replace("- Verdict: AWAITING_DECISION (the tasks gate)\n", "")
        spec = self.spec_and_log(broken + RECEIPT.replace("2026-10-18", "2026-10-19"))
        self.assertNotIn("conversion-receipt", self.rules(spec))

    def test_a_broken_receipt_after_a_complete_one_is_an_error(self) -> None:
        broken = RECEIPT.replace("- Verdict: AWAITING_DECISION (the tasks gate)\n", "")
        spec = self.spec_and_log(RECEIPT + broken.replace("2026-10-18", "2026-10-19"))
        self.assert_seeded(spec, "conversion-receipt")

    def test_a_receipt_inside_a_fence_is_not_read(self) -> None:
        fenced = (
            "\n```markdown"
            + RECEIPT.replace("AWAITING_DECISION (the tasks gate)", "DONE")
            + "```\n"
        )
        spec = self.spec_and_log(fenced)
        self.assertNotIn("conversion-receipt", self.rules(spec))


class AsciiDigitsTest(unittest.TestCase):
    def test_structure_ids_take_ascii_digits_only(self) -> None:
        arabic = "١٢٣"
        for pattern, text in (
            (REQUIREMENT_HEADING, f"### REQ-{arabic}: Retry"),
            (REQUIREMENT_HEADING, f"### Requirement {arabic}"),
            (CRITERION, f"{arabic}. WHEN"),
            (CLAUSE, f"{arabic}.{arabic} WHEN"),
            (TASK_ID, f"T-{arabic} Build"),
            (CHECKBOX, f"{arabic}. [x] Build"),
            (ID_ENTRY, f"REQ-{arabic}"),
            (BAD_CHECKBOX, f"{arabic}. [] Build"),
            (TASK_LINE, f"{arabic}. [x] Build"),
            (LIST_ITEM, f"{arabic}. Who owns the log?"),
            (CROSS_SPEC, f"{arabic}00 REQ-001"),
            (CROSS_SPEC, f"00042 REQ-{arabic}"),
        ):
            with self.subTest(text=text):
                self.assertIsNone(pattern.match(text))

    def test_traced_ids_take_ascii_digits_only(self) -> None:
        self.assertEqual(traced_ids("- Requirements: REQ-١٢٣, ١.١\n"), set())


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
