"""PRD frontmatter parsing and the eligibility command lookup."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state.frontmatter import (
    MALFORMED_WARNING,
    command_for,
    defaults,
    overwrite_warnings,
    parse,
)

PRD = """---
catchup: skip
design: skip
rework_cap: 4
design_gate: user
pause_on_ambiguity: true
default_model: opus
eligibility: "test -f docs/x.md"
---
# PRD body
"""


class ParseTest(unittest.TestCase):
    def test_reads_every_declared_field_from_the_frontmatter_block(self) -> None:
        fields, warnings = parse(PRD, available_tiers={"opus", "sonnet"})
        self.assertEqual(fields, {
            "catchup_mode": "skip",
            "design_mode": "skip",
            "rework_cap": 4,
            "design_gate": "user",
            "pause_on_ambiguity": True,
            "tier": "opus",
        })
        self.assertEqual(warnings, [])

    def test_fills_absent_fields_with_defaults(self) -> None:
        self.assertEqual(defaults(),
                         {"catchup_mode": "run", "design_mode": "run", "rework_cap": 2})
        fields, warnings = parse("---\ntitle: x\n---\n")
        self.assertEqual(fields, defaults())
        self.assertEqual(warnings, [])

    def test_missing_block_defaults_with_malformed_warning(self) -> None:
        fields, warnings = parse("# no frontmatter\n")
        self.assertEqual(fields, defaults())
        self.assertEqual(warnings, [MALFORMED_WARNING])

    def test_closing_fence_beyond_head_window_is_malformed(self) -> None:
        text = "---\n" + "x: y\n" * 20 + "catchup: skip\n---\n"
        self.assertEqual(parse(text), (defaults(), [MALFORMED_WARNING]))

    def test_invalid_values_keep_defaults_and_warn(self) -> None:
        text = "---\ncatchup: maybe\nrework_cap: 0\ndefault_model: opus\n---\n"
        fields, warnings = parse(text)
        self.assertEqual(fields, defaults())
        self.assertEqual(len(warnings), 3)
        self.assertIn("catchup='maybe'", warnings[0])
        self.assertIn("rework_cap='0'", warnings[1])
        self.assertIn("tier 'opus' is unavailable", warnings[2])


class OverwriteWarningsTest(unittest.TestCase):
    def test_flags_only_values_that_replace_a_different_prior_value(self) -> None:
        existing = {"rework_cap": 3, "design_mode": "run"}
        effective = {"rework_cap": 2, "design_mode": "run", "catchup_mode": "skip"}
        self.assertEqual(overwrite_warnings(existing, effective),
                         ["ovcaq: PRD frontmatter reset rework_cap 3 -> 2"])

    def test_unchanged_and_new_keys_are_silent(self) -> None:
        self.assertEqual(overwrite_warnings({"rework_cap": 2}, defaults()), [])
        self.assertEqual(overwrite_warnings({}, defaults()), [])


class CommandForTest(unittest.TestCase):
    def test_returns_unquoted_eligibility_command(self) -> None:
        self.assertEqual(command_for(PRD), "test -f docs/x.md")

    def test_strips_only_one_layer_of_matching_quotes(self) -> None:
        text = "---\neligibility: \"'test $(ls 'a b')'\"\n---\n"
        self.assertEqual(command_for(text), "'test $(ls 'a b')'")
        self.assertEqual(command_for("---\neligibility: 'true\n---\n"), "'true")

    def test_returns_none_when_absent(self) -> None:
        self.assertIsNone(command_for("---\ncatchup: run\n---\n"))
        self.assertIsNone(command_for("---\neligibility: \"\"\n---\n"))
        self.assertIsNone(command_for("no frontmatter\n"))


if __name__ == "__main__":
    unittest.main()
