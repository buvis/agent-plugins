"""Template conformance: headings, header lines, and no banned placeholder (T-020)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "plugins" / "specflow" / "skills" / "spec-workflow"
TEMPLATES = SKILL / "templates"
KIRO = REPO / "tests" / "specflow" / "fixtures" / "kiro"

# Copied from the design's Data model, not read from the templates, so a
# dropped heading fails a test.
REQUIREMENTS_HEADINGS = [
    "# Requirements: <Feature>",
    "## Purpose",
    "## Scope",
    "## Assumptions",
    "## Requirements",
    "### REQ-001: <Title>",
    "#### Acceptance criteria",
    "## Non-functional requirements",
    "## Risks",
    "## Out of scope",
    "## Unresolved questions",
]
DESIGN_HEADINGS = [
    "# Design: <Feature>",
    "## Overview",
    "## Context and constraints",
    "## Architecture",
    "## Module placement",
    "## Components and interfaces",
    "## Data model",
    "## Data and control flow",
    "## Error handling",
    "## Security and privacy",
    "## Testing strategy",
    "## Rollout and migration",
    "## Risks and edge cases",
    "## Requirement traceability",
    "## Alternatives considered",
    "## Reuse inventory",
    "## Open decisions",
]
TASKS_HEADINGS = ["# Tasks: <Feature>", "## Completion criteria", "## Unresolved questions"]
TASK_FIELDS = [
    "Requirements:",
    "Depends on:",
    "Location:",
    "Reuse:",
    "Premise:",
    "Contract:",
    "Details:",
    "Acceptance criteria:",
    "Risk:",
    "Verify:",
]
BUGFIX_HEADINGS = [
    "# Bugfix Requirements Document",
    "## Introduction",
    "## Bug Analysis",
    "### Current Behavior (Defect)",
    "### Expected Behavior (Correct)",
    "### Unchanged Behavior (Regression Prevention)",
]
BUGFIX_DESIGN_HEADINGS = [
    "## Overview",
    "## Glossary",
    "## Bug Details",
    "### Bug Condition",
    "### Examples",
    "## Expected Behavior",
    "### Preservation Requirements",
    "## Hypothesized Root Cause",
    "## Correctness Properties",
    "## Fix Implementation",
    "### Changes Required",
    "## Testing Strategy",
    "### Validation Approach",
    "### Exploratory Bug Condition Checking",
    "### Fix Checking",
    "### Preservation Checking",
    "### Unit Tests",
    "### Property-Based Tests",
    "### Integration Tests",
]
OTHER_HEADINGS = {
    "intake/SPEC.md": ["## Idea", "## Smallest end-to-end outcome", "## Guessed contract"],
    "cross-spec-review.md": [
        "## Verdict",
        "## Spec map",
        "## Findings",
        "## Reshapes",
        "## Gaps",
        "## End state",
        "## Decisions applied",
    ],
}
ALL_TEMPLATES = (
    "requirements.md",
    "design.md",
    "tasks.md",
    "bugfix/bugfix.md",
    "bugfix/design.md",
    "bugfix/tasks.md",
    "intake/idea.md",
    "intake/qa-log.md",
    "intake/SPEC.md",
    "cross-spec-review.md",
)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
BANNED = re.compile(r"\bTBD\b|\bTODO\b|\?\?\?|^\s*(?:[-*+]\s+)?N/A\s*$|\|\s*N/A\s*\|")


def read(relative: str) -> str:
    return (TEMPLATES / relative).read_text(encoding="utf-8")


def prose_lines(text: str) -> list[str]:
    """Lines outside fenced blocks, with inline code removed."""
    lines, fence = [], None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence is None and match:
            fence = match[1]
        elif fence is not None:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
        else:
            lines.append(re.sub(r"`[^`]*`", "", line))
    return lines


def headings(text: str) -> list[str]:
    return [line for line in prose_lines(text) if line.startswith("#")]


def insert_depends_on(text: str, *, bugfix: bool) -> str:
    """Put a Depends on: line where the contract places it."""
    lines = text.splitlines()
    if bugfix:
        intro = lines.index("## Introduction")
        end = next(i for i in range(intro + 1, len(lines)) if lines[i].startswith("## "))
        sources = [i for i in range(intro, end) if lines[i].startswith("Sources:")]
        at = sources[0] if sources else end - 1
    else:
        at = next(i for i, line in enumerate(lines) if line.startswith("## "))
    return "\n".join([*lines[:at], "Depends on: 00012, folder:login-fix", "", *lines[at:]])


class FeatureTemplatesTest(unittest.TestCase):
    def test_requirements_template_has_the_data_model_headings_in_order(self) -> None:
        self.assertEqual(headings(read("requirements.md")), REQUIREMENTS_HEADINGS)

    def test_requirements_template_has_requirements_heading_above_first_block(self) -> None:
        found = headings(read("requirements.md"))
        self.assertLess(found.index("## Requirements"), found.index("### REQ-001: <Title>"))

    def test_requirements_template_carries_every_header_line(self) -> None:
        text = read("requirements.md")
        for field in ("Sources:", "Supersedes:", "Blocks:", "Depends on:"):
            with self.subTest(field=field):
                self.assertRegex(text, rf"(?m)^{field} ")
        self.assertRegex(text, r"(?m)^Source: ")

    def test_requirements_depends_on_sits_once_before_the_first_section(self) -> None:
        lines = read("requirements.md").splitlines()
        first_section = next(i for i, line in enumerate(lines) if line.startswith("## "))
        found = [i for i, line in enumerate(lines) if line.startswith("Depends on:")]
        self.assertEqual(len(found), 1)
        self.assertLess(found[0], first_section)

    def test_design_template_keeps_every_section(self) -> None:
        self.assertEqual(headings(read("design.md")), DESIGN_HEADINGS)

    def test_tasks_template_has_its_headings_and_task_fields(self) -> None:
        text = read("tasks.md")
        self.assertEqual(headings(text), TASKS_HEADINGS)
        for field in TASK_FIELDS:
            with self.subTest(field=field):
                self.assertRegex(text, rf"(?m)^  - {field} ")
        self.assertRegex(text, r"(?m)^- \[ \] T-001 ")

    def test_spike_and_cross_spec_review_templates_have_their_headings(self) -> None:
        for name, expected in OTHER_HEADINGS.items():
            with self.subTest(name=name):
                self.assertEqual(headings(read(name))[1:], expected)


class BugfixTemplatesTest(unittest.TestCase):
    def test_bugfix_template_has_kiro_headings(self) -> None:
        self.assertEqual(headings(read("bugfix/bugfix.md")), BUGFIX_HEADINGS)

    def test_bugfix_template_headings_match_the_kiro_capture(self) -> None:
        capture = headings((KIRO / "bugfix" / "bugfix.md").read_text(encoding="utf-8"))
        self.assertEqual(capture[: len(BUGFIX_HEADINGS)], BUGFIX_HEADINGS)

    def test_bugfix_design_template_has_the_kiro_skeleton(self) -> None:
        self.assertEqual(headings(read("bugfix/design.md"))[1:], BUGFIX_DESIGN_HEADINGS)

    def test_bugfix_design_skeleton_appears_in_order_in_the_capture(self) -> None:
        capture = headings((KIRO / "bugfix" / "design.md").read_text(encoding="utf-8"))
        positions = [capture.index(h) for h in BUGFIX_DESIGN_HEADINGS]
        self.assertEqual(positions, sorted(positions))

    def test_bugfix_tasks_template_follows_the_capture_order(self) -> None:
        template = read("bugfix/tasks.md")
        capture = (KIRO / "bugfix" / "tasks.md").read_text(encoding="utf-8")
        self.assertTrue(capture.startswith("# Implementation Plan"))
        for line in (
            "- [ ] 1. Write bug condition exploration test",
            "- [ ] 2. Write preservation property tests (BEFORE implementing fix)",
            "  - [ ] 3.2 Verify bug condition exploration test now passes",
            "  - [ ] 3.3 Verify preservation tests still pass",
        ):
            with self.subTest(line=line):
                self.assertIn(line, template)
                self.assertIn(line.replace("[ ]", "[x]"), capture)
        last = [line for line in template.splitlines() if line.startswith("- [ ] ")][-1]
        self.assertTrue(last.startswith("- [ ] 4. Checkpoint"))

    def test_bugfix_depends_on_sits_just_before_sources_in_the_introduction(self) -> None:
        lines = read("bugfix/bugfix.md").splitlines()
        depends = lines.index(next(x for x in lines if x.startswith("Depends on:")))
        self.assertTrue(lines[depends + 1].startswith("Sources:"))
        intro = lines.index("## Introduction")
        analysis = lines.index("## Bug Analysis")
        self.assertTrue(intro < depends < analysis)


class PrerequisitePlacementTest(unittest.TestCase):
    """A Depends on: line placed per the contract leaves native headings and IDs alone."""

    def test_placement_keeps_headings_and_ids_in_every_capture(self) -> None:
        for folder, name, bugfix in (
            ("requirements-first", "requirements.md", False),
            ("design-first", "requirements.md", False),
            ("bugfix", "bugfix.md", True),
        ):
            with self.subTest(folder=folder):
                before = (KIRO / folder / name).read_text(encoding="utf-8")
                after = insert_depends_on(before, bugfix=bugfix)
                self.assertEqual(headings(after), headings(before))
                ids = re.compile(r"(?m)^(?:### Requirement \d+|\d+\.\d+ WHEN)")
                self.assertEqual(ids.findall(after), ids.findall(before))
                self.assertEqual(after.count("\nDepends on: "), 1)


class PlaceholderTest(unittest.TestCase):
    def test_no_template_holds_a_banned_placeholder(self) -> None:
        for name in ALL_TEMPLATES:
            with self.subTest(name=name):
                bad = [line for line in prose_lines(read(name)) if BANNED.search(line)]
                self.assertEqual(bad, [])

    def test_placeholder_pattern_catches_each_banned_form(self) -> None:
        for line in ("Owner: TBD", "- TODO write it", "Why???", "N/A", "- N/A", "| N/A |"):
            with self.subTest(line=line):
                self.assertRegex(line, BANNED)
        self.assertNotRegex("Not applicable: no data is stored.", BANNED)


class ContractReferenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = (SKILL / "references" / "artifact-contract.md").read_text(encoding="utf-8")

    def test_reference_holds_each_data_model_shape(self) -> None:
        for marker in (
            "## Spec directory",
            "# Requirements: <Feature>",
            "### Spec dependencies",
            "# Design: <Feature>",
            "# Tasks: <Feature>",
            "## Kiro-native specs",
            "# Bugfix Requirements Document",
            "## Workspace root and intake items",
            "### Q&A log",
            "00004 WF-004 criterion 8",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_reference_leaves_out_the_state_model(self) -> None:
        for key in ("approvedSha256", "approvedAt", "acceptedMarkers", "approvedCode"):
            with self.subTest(key=key):
                self.assertNotIn(key, self.text)

    def test_no_artifact_path_depends_on_the_host(self) -> None:
        for host_path in (".claude/", ".codex/", ".cursor/", "CLAUDE_", "AGENTS.md"):
            with self.subTest(host_path=host_path):
                self.assertNotIn(host_path, self.text)


if __name__ == "__main__":
    unittest.main()
