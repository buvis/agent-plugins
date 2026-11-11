"""provenance.json must stop denying the extracted, tested controller runtime."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from controller_test_support import resolve_test_target

CONTRACTS = Path(__file__).resolve().parents[2] / "plugins/autopilot/contracts/controller"
DOCUMENT_KEYS = {"provenance_version", "source", "scope", "symbol_map",
                 "field_ownership", "preserved_invariants", "deliberate_divergences",
                 "test_map", "new_protocol_obligations", "unverified"}
DENIALS = ("no runtime has been extracted", "remain obligations")
RUNTIME_SUBJECTS = ("runtime implementation", "runtime test")
MAPPED_ROWS = 17
CONTROL = ("tests/autopilot/test_provenance_staging_divergence.py"
           "::test_deliberate_divergences_names_the_dropped_stale_temp_cleanup")


class ProvenanceScopeProseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provenance = json.loads((CONTRACTS / "provenance.json").read_text(encoding="utf-8"))

    def test_document_keeps_every_other_top_level_section(self) -> None:
        self.assertEqual(set(self.provenance), DOCUMENT_KEYS)

    def test_scope_no_longer_denies_runtime_extraction_or_certification(self) -> None:
        scope = self.provenance["scope"]
        self.assertIsInstance(scope, str)
        self.assertTrue(scope.strip(), "scope must still characterize the port")
        for denial in DENIALS:
            with self.subTest(denial=denial):
                self.assertNotIn(denial, scope.lower(),
                                 "scope still denies the extracted runtime")

    def test_unverified_no_longer_lists_runtime_implementation_or_test_execution(self) -> None:
        unverified = self.provenance["unverified"]
        self.assertIsInstance(unverified, list)
        self.assertTrue(unverified, "unverified must still record its open items")
        for entry in unverified:
            self.assertIsInstance(entry, str)
            for subject in RUNTIME_SUBJECTS:
                with self.subTest(entry=entry, subject=subject):
                    self.assertNotIn(subject, entry.lower(),
                                     "unverified still claims the runtime is unverified")

    def test_target_resolution_accepts_a_real_test_and_rejects_near_misses(self) -> None:
        self.assertTrue(resolve_test_target(CONTROL))
        for near_miss in (CONTROL + "-extra",
                          CONTROL.replace(".py::", ".py.bak::"),
                          CONTROL.rpartition("::")[0]):
            with self.subTest(target=near_miss):
                self.assertFalse(resolve_test_target(near_miss))

    def test_every_test_map_entry_names_a_test_that_exists(self) -> None:
        test_map = self.provenance["test_map"]
        self.assertIsInstance(test_map, list)
        self.assertGreaterEqual(len(test_map), MAPPED_ROWS,
                                "a mapped obligation was dropped instead of mapped")
        self.assertEqual(len({entry["source"] for entry in test_map}), len(test_map))
        for entry in test_map:
            with self.subTest(source=entry["source"]):
                self.assertEqual(set(entry), {"source", "target", "note"})
                target = entry["target"]
                self.assertIsNotNone(target, "mapped runtime check has no target test")
                self.assertTrue(resolve_test_target(target),
                                f"target does not name an existing test: {target}")


if __name__ == "__main__":
    unittest.main()
