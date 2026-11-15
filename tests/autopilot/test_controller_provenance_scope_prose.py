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
# Any honest scope says a runtime exists and that executed tests cover it; each
# group lists the wordings that satisfy one of those two claims.
AFFIRMATIONS = (("runtime",),
                ("extracted", "exists", "ships"),
                ("tests/autopilot", "executed tests", "covered by tests",
                 "test coverage"))
RUNTIME_SUBJECTS = ("runtime implementation", "runtime test")
RETAINED_UNVERIFIED = ("host support or certification",
                       "installation, publication, package version changes")
SECTION_MINIMUM = {"source": 7, "symbol_map": 4, "field_ownership": 144,
                   "preserved_invariants": 9, "deliberate_divergences": 9,
                   "new_protocol_obligations": 5}
MAPPED_ROWS = 17
DISTINCT_TARGETS = 8
DISTINCT_TARGET_FILES = 3
CONTROL = ("tests/autopilot/test_provenance_staging_divergence.py"
           "::test_deliberate_divergences_names_the_dropped_stale_temp_cleanup")
# Prose that says the mapped runtime checks are configuration-only or not yet
# executed contradicts the scope.
CONTRADICTIONS = DENIALS + ("configuration only", "validate configuration",
                            "future runtime", "not executed")
# A test_map note describes a test, so there the bare words are claims too. A
# divergence may name a pending intent, which is controller vocabulary.
NOTE_CONTRADICTIONS = CONTRADICTIONS + ("pending", "planned")
GAP_PREFIX = "gap: "
LISTED_GAP_PREFIX = "test_map gap: "


def mapping_problems(entry: dict, unverified: list[str]) -> list[str]:
    """Return why a test_map row is neither a real test nor an explicit gap."""
    target, note = entry["target"], str(entry["note"])
    if target is None:
        problems = []
        if not note.startswith(GAP_PREFIX) or len(note.split()) < 4:
            problems.append("null target without an explicit gap note")
        if not any(item.startswith(LISTED_GAP_PREFIX + entry["source"])
                   for item in unverified):
            problems.append("null target whose source is not listed in unverified")
        return problems
    if not resolve_test_target(target):
        return [f"target does not name an existing test: {target}"]
    if len(note.split()) < 2:
        return [f"mapped target carries no note: {target}"]
    if note.startswith(GAP_PREFIX):
        return [f"a mapped target carries a gap note: {target}"]
    if Path(target.partition("::")[0]).name == Path(__file__).name:
        return ["a mapped obligation points at this test module"]
    return []


class ProvenanceScopeProseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.provenance = json.loads((CONTRACTS / "provenance.json").read_text(encoding="utf-8"))

    def test_document_keeps_every_other_top_level_section(self) -> None:
        self.assertEqual(set(self.provenance), DOCUMENT_KEYS)
        for section, minimum in SECTION_MINIMUM.items():
            with self.subTest(section=section):
                self.assertGreaterEqual(len(self.provenance[section]), minimum,
                                        "the correction emptied a recorded section")

    def test_scope_no_longer_denies_runtime_extraction_or_certification(self) -> None:
        scope = self.provenance["scope"]
        self.assertIsInstance(scope, str)
        self.assertTrue(scope.strip(), "scope must still characterize the port")
        for denial in DENIALS:
            with self.subTest(denial=denial):
                self.assertNotIn(denial, scope.lower(),
                                 "scope still denies the extracted runtime")
        for group in AFFIRMATIONS:
            with self.subTest(claim=group[0]):
                self.assertTrue(any(phrase in scope.lower() for phrase in group),
                                "scope does not state that a runtime exists and "
                                f"that executed tests cover it: {group}")

    def test_unverified_no_longer_lists_runtime_implementation_or_test_execution(self) -> None:
        unverified = self.provenance["unverified"]
        self.assertIsInstance(unverified, list)
        for retained in RETAINED_UNVERIFIED:
            with self.subTest(retained=retained):
                self.assertIn(retained, unverified,
                              "the correction dropped a genuinely open item")
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
        self.assertEqual(len(test_map), MAPPED_ROWS,
                         "a mapped obligation was dropped, or a junk row padded the map")
        self.assertEqual(len({entry["source"] for entry in test_map}), MAPPED_ROWS)
        for entry in test_map:
            with self.subTest(source=entry["source"]):
                self.assertEqual(set(entry), {"source", "target", "note"})
                self.assertEqual(mapping_problems(entry, self.provenance["unverified"]), [])
        targets = [entry["target"] for entry in test_map if entry["target"] is not None]
        self.assertGreaterEqual(len(set(targets)), DISTINCT_TARGETS,
                                "mapped obligations collapse onto too few tests")
        self.assertGreaterEqual(
            len({target.partition("::")[0] for target in targets}),
            DISTINCT_TARGET_FILES, "mapped obligations collapse onto too few modules")

    def test_every_listed_gap_names_a_row_that_still_has_no_target(self) -> None:
        open_sources = [entry["source"] for entry in self.provenance["test_map"]
                        if entry["target"] is None]
        listed = [item for item in self.provenance["unverified"]
                  if item.startswith(LISTED_GAP_PREFIX)]
        self.assertEqual(len(listed), len(open_sources))
        for item in listed:
            with self.subTest(item=item):
                self.assertTrue(
                    any(item.startswith(LISTED_GAP_PREFIX + source) for source in open_sources),
                    "unverified lists a gap whose test_map row has a target")

    def test_null_target_is_allowed_only_as_an_explicit_listed_gap(self) -> None:
        source = "tests/state/test_store.py::test_example"
        gap = {"source": source, "target": None,
               "note": "gap: no tests/autopilot test exercises this"}
        listed = [f"test_map gap: {source}"]
        self.assertEqual(mapping_problems(gap, listed), [])
        for name, entry, unverified, problem in (
                ("silent null", dict(gap, note="runtime lock modes serialize"), listed,
                 "null target without an explicit gap note"),
                ("bare gap prefix", dict(gap, note="gap: none"), listed,
                 "null target without an explicit gap note"),
                ("unlisted gap", gap, [],
                 "null target whose source is not listed in unverified"),
                ("gap named outside a gap line", gap, [f"see {source}"],
                 "null target whose source is not listed in unverified"),
                ("gap note on a real target", dict(gap, target=CONTROL), listed,
                 f"a mapped target carries a gap note: {CONTROL}")):
            with self.subTest(case=name):
                self.assertEqual(mapping_problems(entry, unverified), [problem])

    def test_divergences_and_test_map_notes_do_not_contradict_the_scope(self) -> None:
        texts = [(f"deliberate_divergences[{entry['topic']}].{key}", value, CONTRADICTIONS)
                 for entry in self.provenance["deliberate_divergences"]
                 for key, value in entry.items()]
        texts += [(f"test_map[{entry['source']}].note", entry["note"], NOTE_CONTRADICTIONS)
                  for entry in self.provenance["test_map"]]
        self.assertGreaterEqual(len(texts), MAPPED_ROWS)
        for where, text, phrases in texts:
            for phrase in phrases:
                with self.subTest(where=where, phrase=phrase):
                    self.assertNotIn(phrase, str(text).lower(),
                                     "prose contradicts the executed-tests scope")


if __name__ == "__main__":
    unittest.main()
