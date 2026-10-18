"""The runtime skill's size and its reference routing (T-030)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "plugins" / "specflow" / "skills" / "spec-workflow"
REFERENCES = SKILL / "references"

# Agent Skills specification: "Keep your main SKILL.md under 500 lines."
SIZE_LIMIT = 500
# Routed files a later task writes. Each task takes its own off the list; a
# listed file that exists fails, so the list cannot go stale.
NOT_WRITTEN_YET = {
    "references/review/cross-spec.md",  # 00007
}
# A record and a license, not guidance.
NOT_ROUTED = {"references/aws/adaptation.md", "references/aws/LICENSE"}
ROUTED = re.compile(r"`(references/[^`\s]+)`")


def routed() -> set[str]:
    return set(ROUTED.findall((SKILL / "SKILL.md").read_text(encoding="utf-8")))


class SkillTest(unittest.TestCase):
    def test_skill_md_is_within_the_size_limit(self) -> None:
        lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), SIZE_LIMIT)

    def test_routing_names_only_files_that_exist(self) -> None:
        paths = routed()
        self.assertTrue(paths, "SKILL.md routes no reference")
        self.assertEqual(NOT_WRITTEN_YET - paths, set(), "listed but not routed")
        for path in sorted(paths):
            with self.subTest(path=path):
                exists = (SKILL / path).exists()
                if path in NOT_WRITTEN_YET:
                    self.assertFalse(exists, "written: take it off NOT_WRITTEN_YET")
                else:
                    self.assertTrue(exists, "routed but missing")

    def test_every_reference_is_routed(self) -> None:
        paths = routed()
        folders = tuple(p for p in paths if p.endswith("/"))
        for file in sorted(p for p in REFERENCES.rglob("*") if p.is_file()):
            name = file.relative_to(SKILL).as_posix()
            with self.subTest(file=name):
                self.assertTrue(
                    name in paths or name in NOT_ROUTED or name.startswith(folders),
                    "no routing row names it",
                )


if __name__ == "__main__":
    unittest.main()
