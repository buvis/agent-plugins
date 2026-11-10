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
        self.assertTrue(divergences, "deliberate_divergences must not be empty")
        keywords = ("_cleanup_stale_temps", "staging budget", "staging-admission",
                    "admit_staging")
        texts = [json.dumps(entry) for entry in divergences]
        self.assertTrue(
            any(any(keyword in text for keyword in keywords) for text in texts),
            "no deliberate_divergences entry mentions the dropped auto-delete "
            "stale-temp cleanup or its staging-budget replacement",
        )


if __name__ == "__main__":
    unittest.main()
