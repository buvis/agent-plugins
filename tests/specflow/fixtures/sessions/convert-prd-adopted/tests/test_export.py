"""Tests of PRD 00005 (T3), green since commit 3f2a9c1."""

import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ExportTest(unittest.TestCase):
    def setUp(self) -> None:
        from export import write_csv

        self.write_csv = write_csv
        self.db = sqlite3.connect(":memory:")
        self.db.execute("create table orders (id integer, day text, total real)")
        self.db.execute("insert into orders values (1, '2026-09-30', 12.5)")

    def test_header_row(self) -> None:
        self.assertTrue(self.write_csv(self.db, "2026-09-30").startswith(b"id,day,total"))

    def test_one_row_per_order(self) -> None:
        self.assertEqual(self.write_csv(self.db, "2026-09-30").count(b"\n"), 2)


if __name__ == "__main__":
    unittest.main()
