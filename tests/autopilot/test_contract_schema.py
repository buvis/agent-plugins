"""Draft 2020-12 evidence schema checks using the golden review documents."""

from __future__ import annotations

import copy
import unittest
from typing import Any

from jsonschema import Draft202012Validator

from test_contract import EVIDENCE_FILE, FIXTURES_FILE, load


class EvidenceSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(EVIDENCE_FILE)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.context_validator = Draft202012Validator({"$ref": "#/$defs/expected_context", "$defs": cls.schema["$defs"]})
        cls.cases = {c["name"]: c for c in load(FIXTURES_FILE)["cases"]}

    def assert_valid(self, value: Any, context: bool = False) -> None:
        validator = self.context_validator if context else self.validator
        self.assertEqual(list(validator.iter_errors(value)), [])

    def assert_invalid(self, value: Any, context: bool = False) -> None:
        validator = self.context_validator if context else self.validator
        self.assertTrue(list(validator.iter_errors(value)), repr(value))

    def test_schema_is_2020_12_and_all_golden_documents_have_expected_structural_validity(self) -> None:
        self.assertEqual(self.schema["$schema"].rstrip("#"), "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue({"expected_context", "source_bindings", "reviewer_result", "artifact", "finding", "group", "rubric_verdict", "verification"} <= self.schema["$defs"].keys())
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assert_valid(case["expected_context"], context=True)
                if name == "full-schema-invalid":
                    self.assert_invalid(case["input"])
                else:
                    self.assert_valid(case["input"])

    def test_schema_requires_every_declared_field_and_rejects_unexpected_object_fields(self) -> None:
        case = self.cases["full-clean"]
        paths = [(), ("policy_binding",), ("source_bindings",), ("source_bindings", "scope"),
                 ("reviewer_results", 0), ("artifacts", 0), ("verification",), ("rubric_verdicts", 0)]
        context_paths = [(), ("source_bindings",), ("resolved_roster", 0), ("excluded_jobs", 0),
                         ("excluded_jobs", 0, "observed"), ("allowed_inputs",), ("session_identities",)]
        for context, path_list in ((False, paths), (True, context_paths)):
            original = case["expected_context" if context else "input"]
            for path in path_list:
                target = original
                for key in path:
                    target = target[key]
                for key in [*target, "unexpected_field"]:
                    changed = copy.deepcopy(original)
                    node = changed
                    for part in path:
                        node = node[part]
                    if key == "unexpected_field":
                        node[key] = "unexpected"
                    else:
                        del node[key]
                    with self.subTest(context=context, path=path, field=key):
                        self.assert_invalid(changed, context)

    def test_schema_checks_nested_findings_groups_activation_and_not_applicable_objects(self) -> None:
        roster = self.cases["full-carl-activated"]["expected_context"]["resolved_roster"]
        carl_index = next(i for i, row in enumerate(roster) if row["job_id"] == "carl")
        documents = [
            (self.cases["full-unknown-finding-reference"]["input"], ("findings", 0), False),
            (self.cases["full-unknown-finding-reference"]["input"], ("groups", 0), False),
            (self.cases["full-carl-activated"]["expected_context"], ("resolved_roster", carl_index, "activation"), True),
        ]
        for original, path, context in documents:
            target = original
            for key in path:
                target = target[key]
            self.assertIsInstance(target, dict)
            for key in [*target, "disposition"]:
                changed = copy.deepcopy(original)
                node = changed
                for part in path:
                    node = node[part]
                if key == "disposition":
                    node[key] = "accepted"
                else:
                    del node[key]
                with self.subTest(path=path, field=key):
                    self.assert_invalid(changed, context)
        doc = copy.deepcopy(self.cases["full-clean"]["input"])
        doc["verification"] = {"status": "not-applicable", "reason": "docs-only"}
        self.assert_valid(doc)
        for extra in ({}, {"status": "not-applicable"}, {"status": "not-applicable", "reason": "docs-only", "exit_code": 0}):
            doc["verification"] = extra
            self.assert_invalid(doc)

    def test_schema_enforces_string_hash_enum_integer_and_array_boundaries(self) -> None:
        base = self.cases["full-clean"]["input"]
        mutations = [
            (("schema_version",), [0, 2, True, "1", None]),
            (("lane",), ["", None, 1]),
            (("review_pass",), ["initial-more", "delta ", "", None]),
            (("policy_binding", "policy_digest"), ["a" * 63, "a" * 65, "A" * 64, "x" + "a" * 64]),
            (("source_bindings", "head_sha"), ["a" * 39, "a" * 41, "A" * 40]),
            (("source_bindings", "scope", "refs"), [[], [""], ["card:1", "card:1"]]),
            (("reviewer_results", 0, "attempt"), [0, -1, True, 1.5, "1"]),
            (("reviewer_results", 0, "role_id"), ["consensus-more", "Blind", ""]),
            (("reviewer_results", 0, "outcome"), ["cleaner", "findings ", ""]),
            (("reviewer_results", 0, "result_id"), ["", None, 1]),
            (("reviewer_results", 0, "received_input_refs"), [["prd:"], ["prd:a b"], ["Prd:a"], ["prd:a", "prd:a"]]),
            (("verification", "argv"), [[], [""], None]),
            (("verification", "exit_code"), [True, 0.5, "0", None]),
        ]
        for path, values in mutations:
            for value in values:
                changed = copy.deepcopy(base)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.subTest(path=path, value=value):
                    self.assert_invalid(changed)
        for value in ({}, [], None):
            self.assert_invalid(value)
        for lane in ("full-extra", "canary"):
            self.assert_valid(dict(base, lane=lane))

    def test_schema_accepts_distinct_values_and_empty_semantic_collections(self) -> None:
        for name in ("full-clean", "fast-track-delta-clean", "full-findings-without-output"):
            self.assert_valid(self.cases[name]["input"])
        doc = copy.deepcopy(self.cases["full-clean"]["input"])
        for key in ("reviewer_results", "artifacts", "findings", "groups", "rubric_verdicts"):
            doc[key] = []
        self.assert_valid(doc)
        for path in ("docs/review-a.md", "other/review-b.json", "docs/a..b.md"):
            doc = copy.deepcopy(self.cases["full-clean"]["input"])
            doc["artifacts"][0]["path"] = path
            self.assert_valid(doc)
        for path in ("", "/review.md", "../review.md", "docs/../review.md", "C:/review.md", "docs\\review.md"):
            doc["artifacts"][0]["path"] = path
            self.assert_invalid(doc)

    def test_schema_conditions_require_sessions_reasons_findings_and_prior_evidence(self) -> None:
        base = self.cases["full-clean"]["input"]
        for outcome in ("clean", "findings", "failed", "unavailable"):
            doc = copy.deepcopy(base)
            result = doc["reviewer_results"][0]
            result.update(outcome=outcome, finding_ids=["F1"] if outcome == "findings" else [],
                          reason="format-invalid" if outcome in {"failed", "unavailable"} else None)
            self.assert_valid(doc)
            result["native_session_ref"] = None
            if outcome in {"clean", "findings"}:
                self.assert_invalid(doc)
            else:
                self.assert_valid(doc)
                result["reason"] = None
                self.assert_invalid(doc)
        for outcome, ids in (("clean", ["F1"]), ("findings", [])):
            doc = copy.deepcopy(base)
            doc["reviewer_results"][0].update(outcome=outcome, finding_ids=ids)
            self.assert_invalid(doc)
        for review_pass, prior, valid in (("initial", None, True), ("initial", "a" * 64, False), ("delta", "b" * 64, True), ("delta", None, False)):
            doc = copy.deepcopy(base)
            doc["review_pass"] = review_pass
            doc["source_bindings"]["prior_evidence_sha256"] = prior
            (self.assert_valid if valid else self.assert_invalid)(doc)

    def test_expected_context_requires_exact_enums_activation_and_unique_input_refs(self) -> None:
        base = self.cases["full-clean"]["expected_context"]
        for field, invalid in (("lane", "full-extra"), ("consensus_engine", "workflows"), ("resolved_roster", [])):
            self.assert_invalid(dict(base, **{field: invalid}), context=True)
        for engine in ("legacy", "workflow", "shadow"):
            self.assert_valid(dict(base, consensus_engine=engine), context=True)
        for required, activation, valid in ((True, None, True), (False, None, False),
                                           (False, {"predicate_id": "gemini_cli_available", "observed": {"capability": "gemini_cli", "value": True}}, True),
                                           (True, {"predicate_id": "gemini_cli_available", "observed": {"capability": "gemini_cli", "value": True}}, False)):
            context = copy.deepcopy(base)
            context["resolved_roster"][0].update(required=required, activation=activation)
            (self.assert_valid if valid else self.assert_invalid)(context, context=True)
        context = copy.deepcopy(base)
        context["allowed_inputs"]["input_refs"] = ["prd:a", "prd:b"]
        self.assert_valid(context, context=True)
        context["allowed_inputs"]["input_refs"] = ["prd:a", "prd:a"]
        self.assert_invalid(context, context=True)


if __name__ == "__main__":
    unittest.main()
