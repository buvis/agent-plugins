"""The source record in the package and the cursors outside it stay in step."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "plugins/specflow/skills/spec-workflow/references/aws/adaptation.md"
CURSORS = ROOT / "tools/specflow/upstream/sources.md"
ROW = re.compile(r"^\| (A\d) [^|]+\|(.*)$", re.MULTILINE)


def rows(path: Path) -> dict[str, list[str]]:
    """Source ID -> the row's remaining cells, for every table row naming one."""
    return {
        source: [cell.strip() for cell in rest.split("|")[:-1]]
        for source, rest in ROW.findall(path.read_text(encoding="utf-8"))
    }


class SourcesTest(unittest.TestCase):
    def test_every_recorded_source_has_a_cursor_row(self) -> None:
        recorded = set(rows(RECORD))
        self.assertEqual(recorded, {"A1", "A2", "A3"})
        self.assertEqual(recorded - set(rows(CURSORS)), set())

    def test_cursor_rows_carry_an_https_url(self) -> None:
        for source, cells in rows(CURSORS).items():
            with self.subTest(source=source):
                # Cells after the source: role, URL, reviewed through, on, scope.
                self.assertRegex(cells[1], r"^https://github\.com/[\w.-]+/[\w.-]+$")


if __name__ == "__main__":
    unittest.main()
