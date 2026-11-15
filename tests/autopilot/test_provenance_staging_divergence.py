"""provenance.json records the intentionally dropped auto-delete stale-temp cleanup."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[2] / "plugins/autopilot/contracts/controller"


class ProvenanceStagingDivergenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provenance = json.loads((CONTRACTS / "provenance.json").read_text())

    def test_deliberate_divergences_names_the_dropped_stale_temp_cleanup(self) -> None:
        divergences = self.provenance["deliberate_divergences"]
        self.assertIsInstance(divergences, list)
        entries = [entry for entry in divergences if entry.get("topic") == "staging cleanup"]
        self.assertEqual(len(entries), 1, "expected exactly one 'staging cleanup' divergence")
        entry = entries[0]
        self.assertIn("_cleanup_stale_temps", entry["source"],
                      "source no longer names the dropped auto-delete cleanup")
        for replacement in ("admit_staging", "budget"):
            with self.subTest(replacement=replacement):
                self.assertIn(replacement, entry["target"],
                              "target no longer names the staging-admission budget")


if __name__ == "__main__":
    unittest.main()
