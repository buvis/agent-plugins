"""One seeded defect per structural check of T-071 (00005, VAL-001.9-12)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
from pathlib import Path

import support
from specflow_helper.checks import CHECKS, validate
from test_checks import ChecksTest


class StructuralRuleTest(ChecksTest):
    """The five checks T-071 adds for the structural rules of 00005 (VAL-001.9-12)."""

    def findings(self, spec: Path, rule: str, phase: str | None = None) -> list[dict]:
        return [f for f in validate(self.repo, spec, phase) if f["rule"] == rule]

    def test_every_structural_rule_check_is_registered(self) -> None:
        path = support.REPO / "tools" / "specflow" / "rules" / "inventory.json"
        rules = json.loads(path.read_text(encoding="utf-8"))["rules"]
        names = {
            rule["check"].removeprefix("validator:")
            for rule in rules
            if rule["kind"] == "structural" and rule["check"].startswith("validator:")
        }
        self.assertIn("open-markers", names)
        self.assertEqual(names - set(CHECKS), set())

    def test_placeholders(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md", "the retry file first.", "the retry file TBD."
        )
        self.edit(
            spec / "tasks.md",
            "## Completion criteria",
            "Not applicable: none\n\n## Completion criteria",
        )
        self.assert_seeded(spec, "placeholders")
        files = {
            f["file"].rsplit("/", 1)[-1] for f in self.findings(spec, "placeholders")
        }
        self.assertEqual(files, {"requirements.md", "tasks.md"})

    def test_placeholders_skip_inline_code_and_fences_and_a_design_reason(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md", "the retry file first.", "the `TBD` file first."
        )
        self.edit(
            spec / "requirements.md",
            "## Out of scope",
            "```\nTODO ??? N/A\n```\n\n## Out of scope",
        )
        self.assertEqual(self.findings(spec, "placeholders"), [])
        design = (spec / "design.md").read_text()
        self.assertIn("Not applicable: ", design)
        for seeded in ("N/A", "???", "TODO", "Not applicable:"):
            with self.subTest(seeded=seeded):
                (spec / "design.md").write_text(design + f"\n{seeded}\n")
                self.assert_seeded(spec, "placeholders")
        (spec / "design.md").write_text(design)

    def test_open_markers_reads_only_upstream_artifacts(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "requirements.md", "100,000 rows", "100,000 rows (guess)")
        self.edit(
            spec / "design.md",
            "## Open decisions",
            "## Open decisions\n\n- Which log format?",
        )
        self.edit(
            spec / "tasks.md",
            "## Completion criteria",
            "Cap at 5 (guess).\n\n## Completion criteria",
        )
        self.assertEqual(self.findings(spec, "open-markers", "requirements"), [])
        design = self.findings(spec, "open-markers", "design")
        self.assertEqual(
            {f["file"].rsplit("/", 1)[-1] for f in design}, {"requirements.md"}
        )
        tasks = self.findings(spec, "open-markers", "tasks")
        self.assertEqual(
            sorted(f["file"].rsplit("/", 1)[-1] for f in tasks),
            ["design.md", "requirements.md"],
        )
        for finding in tasks:
            self.assertTrue(finding["message"] and finding["fix"], finding)
            self.assertEqual(finding["level"], "error")

    def test_open_markers_follow_a_design_first_order(self) -> None:
        spec = self.copy("00101-feature-sample")
        support.write_state(
            spec,
            support.new_state("00101-feature-sample", workflowOrder="design-first"),
        )
        self.edit(
            spec / "design.md",
            "## Open decisions",
            "## Open decisions\n\n- Which log format?",
        )
        found = self.findings(spec, "open-markers", "requirements")
        self.assertEqual({f["file"].rsplit("/", 1)[-1] for f in found}, {"design.md"})

    def test_accepted_marker_clears_open_markers_until_the_line_changes(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "requirements.md", "100,000 rows", "100,000 rows (guess)")
        line = "- The source sends at most 100,000 rows (guess) a night (Q1)."
        self.assertIn(line, (spec / "requirements.md").read_text())
        state = support.new_state("00101-feature-sample")
        state["artifacts"]["design"]["acceptedMarkers"] = [
            {"artifact": "requirements", "line": line}
        ]
        support.write_state(spec, state)
        self.assertEqual(self.findings(spec, "open-markers", "design"), [])
        self.edit(
            spec / "requirements.md", "100,000 rows (guess)", "200,000 rows (guess)"
        )
        self.assertTrue(self.findings(spec, "open-markers", "design"))

    def test_portable_links(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md",
            "## Out of scope",
            "See `~/notes/retry.md`, /Users/sam/retry.log and [[retry memory]].\n"
            "Also /tmp, (/config.json) and $HOME/retry.md as well.\n\n## Out of scope",
        )
        found = self.findings(spec, "portable-links")
        self.assertEqual(
            [f["message"].split(": ", 1)[1].split(" does not")[0] for f in found],
            [
                "~/notes/retry.md",
                "/Users/sam/retry.log",
                "[[retry memory]]",
                "/tmp",
                "/config.json",
                "$HOME/retry.md",
            ],
        )
        self.assertEqual({f["level"] for f in found}, {"warning"})
        self.assertTrue(
            all(f["file"] and f["message"] and f["fix"] for f in found), found
        )
        self.assertNotIn("portable-links", self.rules(spec))

    def test_portable_links_skip_urls_relative_paths_and_slashed_words(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md",
            "## Out of scope",
            "Read https://example.com/a/b, docs/dev/a.md, and/or 1/2 of it, `<root>/intake/new/`,"
            " `plugins/*/skills/`, the `/.claude/` ignore line, a lone / slash,"
            " and `[[...]]` links.\n\n## Out of scope",
        )
        self.assertEqual(self.findings(spec, "portable-links"), [])
        self.edit(spec / "requirements.md", "a lone / slash", "a lone /tmp path")
        (found,) = self.findings(spec, "portable-links")
        self.assertIn("/tmp does not resolve", found["message"])

    def test_closed_fences(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "## Completion criteria",
            "```text\nrun it\n\n## Completion criteria",
        )
        self.assert_seeded(spec, "closed-fences")
        (found,) = self.findings(spec, "closed-fences")
        self.assertEqual(found["level"], "error")
        self.assertTrue(found["file"].endswith("tasks.md"))

    def test_closed_fences_accept_a_longer_closing_fence(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "tasks.md",
            "## Completion criteria",
            "````\n```\n`````\n\n## Completion criteria",
        )
        self.assertEqual(self.findings(spec, "closed-fences"), [])
        self.edit(spec / "tasks.md", "`````\n", "```\n")
        (found,) = self.findings(spec, "closed-fences")
        self.assertIn("code fence ```` never closes", found["message"])

    def test_requirement_source(self) -> None:
        spec = self.copy("00101-feature-sample")
        self.edit(spec / "requirements.md", "Source: Q2\n", "")
        (found,) = self.findings(spec, "requirement-source")
        self.assertEqual(found["level"], "warning")
        self.assertIn("REQ-002", found["message"])
        self.assertTrue(found["file"] and found["fix"])
        self.assertNotIn("requirement-source", self.rules(spec))

    def test_requirement_source_skips_bugfix_and_withdrawn_requirements(self) -> None:
        self.assertEqual(
            self.findings(self.copy("00102-bugfix-sample"), "requirement-source"), []
        )
        spec = self.copy("00101-feature-sample")
        self.edit(
            spec / "requirements.md",
            "## Non-functional",
            "### REQ-003: withdrawn\n\n## Non-functional",
        )
        self.assertEqual(self.findings(spec, "requirement-source"), [])
        self.edit(spec / "requirements.md", "Source: Q2\n", "")
        (found,) = self.findings(spec, "requirement-source")
        self.assertIn("REQ-002", found["message"])

    def test_warnings_never_change_the_exit_status(self) -> None:
        import validate_spec

        spec = self.copy("00101-feature-sample")
        self.edit(spec / "requirements.md", "Source: Q2\n", "See [[retry memory]].\n")
        cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = validate_spec.main(["validate", str(spec), "--json"])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(
            {f["rule"] for f in result["findings"]},
            {"portable-links", "requirement-source"},
        )


if __name__ == "__main__":
    unittest.main()
