"""Standalone review evidence schema checks."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError


def documents(count: int = 4) -> tuple[dict[str, Any], dict[str, Any]]:
    source = dict(prd_sha256="a" * 64, base_sha="b" * 40, head_sha="c" * 40,
        tree_sha="d" * 40, scope={"kind": "task", "refs": ["T1", "T2"]},
        allowed_input_manifest_sha256="e" * 64, prior_evidence_sha256=None)
    evidence = dict(schema_version=1, lane="full", review_pass="initial",
        policy_binding=dict(policy_digest="f" * 64, execution_profile="portable"),
        source_bindings=source,
        reviewer_results=[dict(result_id=f"r{i}", job_ref=f"j{i}", role_id="blind",
            provider=f"p{i}", adapter=f"a{i}", attempt=i, native_session_ref=f"s{i}",
            source_binding_digest=str(i) * 64, received_input_refs=["prd:a", "diff:b"],
            artifact_ids=[f"a{i}"], outcome="findings", finding_ids=[f"f{i}"], reason=None)
            for i in range(1, count + 1)],
        artifacts=[dict(artifact_id=f"a{i}", kind="review", path=f"docs/{i}.md",
            sha256=str(i) * 64, result_id=f"r{i}") for i in (1, 2)],
        findings=[dict(finding_id=f"f{i}", result_id=f"r{i}", severity="low",
            title=f"Title {i}", file=None, task_ref=None, evidence=f"Proof {i}") for i in (1, 2)],
        groups=[dict(group_id="g", finding_ids=["f1", "f2"], rationale="Related")],
        rubric_verdicts=[dict(result_id=f"r{i}", namespace=n, rule_id=f"{n}{i}",
            verdict="pass", evidence=f"Checked {i}") for i, n in ((1, "R"), (2, "B"))],
        verification=dict(status="ran", argv=["python", "check.py"], exit_code=0,
            output_artifact_id="a1", code_identity="c" * 40, outcome="passed"))
    activation = dict(predicate_id="has-ui", observed=dict(capability="ui", value=False))
    context = dict(lane="full", review_pass="initial", execution_profile="portable",
        consensus_engine="workflow", policy_digest="f" * 64, source_bindings=copy.deepcopy(source),
        resolved_roster=[dict(job_id="j1", role_id="blind", required=True, activation=None),
            dict(job_id="j2", role_id="ui", required=False, activation=activation)],
        excluded_jobs=[dict(job_id="j3", **activation)],
        allowed_inputs=dict(manifest_sha256="e" * 64, input_refs=["prd:a", "diff:b"],
            per_job={"j1": ["prd:a", "diff:b"], "j2": []}),
        session_identities=dict(builder_session_refs=["builder1", "builder2"],
            independent_contexts_required=True))
    return evidence, context


def uppercase_digests(size: int) -> list[str]:
    return [v for c in "ABCDEF" for v in (c * size, "a" * (size // 2) + c + "b" * (size // 2 - 1))]


def objects(value: Any, path: tuple = ()) -> Any:
    if isinstance(value, dict):
        if path != ("allowed_inputs", "per_job"):
            yield path, value
        for key, child in value.items():
            yield from objects(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from objects(child, (*path, index))


class EvidenceWireTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = Path(__file__).resolve().parents[2] / "plugins/autopilot/contracts/review-evidence-v1.json"
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)
        cls.validators = [Draft202012Validator(schema), Draft202012Validator(
            {"$ref": "#/$defs/expected_context", "$defs": schema["$defs"]})]

    def check(self, value: Any, context: int = 0, valid: bool = True) -> None:
        if valid:
            self.validators[context].validate(value)
        else:
            with self.assertRaises(ValidationError):
                self.validators[context].validate(value)

    def test_requires_all_fields_and_closes_every_declared_object(self) -> None:
        for context, original in enumerate(documents()):
            lanes = ("full", "fast-track", "solo") if context else (
                "full", *(f"{p}-lane" for p in ("future", "custom", "canary")), "λ")
            for lane in lanes:
                original["lane"] = lane
                self.check(original, context)
                for path, node in objects(original):
                    for key in (*node, "extra"):
                        changed = copy.deepcopy(original)
                        target = changed
                        for part in path:
                            target = target[part]
                        if key == "extra":
                            target[key] = "value"
                        else:
                            del target[key]
                        with self.subTest(context=context, lane=lane, path=path, key=key):
                            self.check(changed, context, False)

    def test_accepts_empty_arrays_and_rejects_bad_digest(self) -> None:
        for count in (0, 1, 2, 3, 7):
            self.check(documents(count)[0])
        evidence, _ = documents()
        for key in ("reviewer_results", "artifacts", "findings", "groups", "rubric_verdicts"):
            evidence[key] = []
        evidence["lane"] = "future-lane"
        self.check(evidence)
        evidence["policy_binding"]["policy_digest"] = "a" * 65
        self.check(evidence, valid=False)

    def test_enforces_result_outcome_conditions(self) -> None:
        for index, outcome in ((i, o) for i in range(4)
                for o in ("clean", "findings", "failed", "unavailable")):
            evidence, _ = documents()
            result = evidence["reviewer_results"][index]
            result.update(outcome=outcome, finding_ids=["f2"] if outcome == "findings" else [],
                reason="missing tool" if outcome in ("failed", "unavailable") else None)
            self.check(evidence)
            result["native_session_ref"] = None
            self.check(evidence, valid=outcome in ("failed", "unavailable"))
            if outcome in ("failed", "unavailable"):
                result["reason"] = None
            else:
                result["native_session_ref"] = "s2"
                result["finding_ids"] = [] if outcome == "findings" else ["f2"]
            self.check(evidence, valid=False)

    def test_enforces_delta_digest_and_activation(self) -> None:
        for review_pass, prior, valid in (("initial", None, True), ("initial", "a" * 64, False),
                                         ("delta", "b" * 64, True), ("delta", None, False)):
            evidence, _ = documents()
            evidence["review_pass"] = review_pass
            evidence["source_bindings"]["prior_evidence_sha256"] = prior
            self.check(evidence, valid=valid)
        for required in (True, False):
            for active in (True, False):
                _, context = documents()
                row = context["resolved_roster"][1]
                row["required"] = required
                if not active:
                    row["activation"] = None
                self.check(context, 1, valid=required != active)

    def assert_pairs(self, context: int, rows: list) -> None:
        rows = [((path[0], i, *path[2:]) if path[0] == "reviewer_results" and len(path) > 1 else path, a, r)
            for path, a, r in rows for i in (range(4) if path[0] == "reviewer_results" and len(path) > 1 else (0,))]
        for path, accepted, rejected in rows:
            for variant in (0, 1):
                original = documents()[context]
                if context:
                    original["execution_profile"] = ("portable", "native")[variant]
                else:
                    original["lane"] = ("full", "future-lane")[variant]
                for valid, values in ((True, accepted), (False, rejected)):
                    for value in values:
                        changed = copy.deepcopy(original)
                        target = changed
                        for part in path[:-1]:
                            target = target[part]
                        target[path[-1]] = copy.deepcopy(value)
                        with self.subTest(context=context, path=path, value=value, variant=variant):
                            self.check(changed, context, valid)

    def test_integers_reject_bools_strings_and_fractions(self) -> None:
        self.assert_pairs(0, [
            (("schema_version",), [1], [True, False, "1", 1.5, 0, 2, None]),
            (("reviewer_results", 1, "attempt"), [1, 7], [True, False, "1", 1.5, 0, -1, None]),
            (("verification", "exit_code"), [0, -7], [True, False, "0", 0.5, None]),
        ])

    def test_enum_boundaries_allow_declared_values_only(self) -> None:
        self.assert_pairs(0, [
            (("review_pass",), ["initial"], ["initial-more", "Initial", "", None, 1]),
            (("source_bindings", "scope", "kind"), ["prd", "task", "card"], ["tasks", "Task", "", None, 1]),
            (("reviewer_results", 1, "role_id"), ["consensus", "blind", "doubt", "ui"],
                ["consensus-more", "Blind", "", None, 1]),
            (("reviewer_results", 1, "outcome"), ["findings"],
                ["cleaner", "findings ", "Failed", "", None, 1]),
            (("findings", 1, "severity"), ["critical", "high", "medium", "low"],
                ["critical-more", "High", "", None, 1]),
            (("rubric_verdicts", 1, "namespace"), ["B"], ["BB", "b", "D", "", None, 1]),
            (("rubric_verdicts", 1, "rule_id"), ["B1", "B20"], ["B", "B-1", "B1x", "b1", "R1", "", None, 1]),
            (("rubric_verdicts", 1, "verdict"), ["pass", "fail"], ["passed", "FAIL", "", None, True]),
            (("verification", "outcome"), ["passed", "failed"], ["pass", "FAILED", "", None, 1]),
        ])
        self.assert_pairs(1, [
            (("lane",), ["full", "fast-track", "solo"], ["full-extra", "Solo", "", None, 1]),
            (("review_pass",), ["initial"], ["initial-more", "Initial", "", None, 1]),
            (("consensus_engine",), ["legacy", "workflow", "shadow"], ["workflows", "Legacy", "", None, 1]),
            (("resolved_roster", 1, "role_id"), ["consensus", "blind", "doubt", "ui"],
                ["consensus-more", "UI", "", None, True]),
        ])

    def test_rubric_rules_match_namespace(self) -> None:
        for namespace in ("R", "B", "D"):
            for number in (1, 23):
                evidence, _ = documents()
                verdict = evidence["rubric_verdicts"][1]
                verdict.update(namespace=namespace, rule_id=f"{namespace}{number}")
                self.check(evidence)
                verdict["namespace"] = namespace.lower()
                self.check(evidence, valid=False)
                verdict["namespace"] = namespace
                verdict["rule_id"] = f"{'B' if namespace == 'R' else 'R'}{number}"
                self.check(evidence, valid=False)

    def test_strings_reject_empty_and_non_string_values(self) -> None:
        evidence_paths = [
            ("lane",), ("policy_binding", "execution_profile"),
            *(("reviewer_results", 1, key) for key in ("result_id", "job_ref", "provider", "adapter", "native_session_ref")),
            *(("artifacts", 1, key) for key in ("artifact_id", "kind")),
            *(("findings", 1, key) for key in ("finding_id", "result_id", "title", "evidence")),
            ("groups", 0, "group_id"), ("groups", 0, "rationale"),
            ("rubric_verdicts", 1, "result_id"), ("rubric_verdicts", 1, "evidence"),
            ("verification", "output_artifact_id"),
        ]
        context_paths = [
            ("execution_profile",), ("resolved_roster", 1, "job_id"),
            ("resolved_roster", 1, "activation", "predicate_id"),
            ("resolved_roster", 1, "activation", "observed", "capability"),
            ("excluded_jobs", 0, "job_id"), ("excluded_jobs", 0, "predicate_id"),
            ("excluded_jobs", 0, "observed", "capability"),
        ]
        for context, paths in ((0, evidence_paths), (1, context_paths)):
            self.assert_pairs(context, [(path, ["one", "two"], ["", None, True, 3, [], {}]) for path in paths])

    def test_nullable_strings_accept_null_or_nonempty_strings(self) -> None:
        paths = [
            ("artifacts", 1, "result_id"), ("findings", 1, "file"),
            ("findings", 1, "task_ref"), ("reviewer_results", 1, "reason"),
        ]
        self.assert_pairs(0, [(path, [None, "one", "two"], ["", True, 3, [], {}]) for path in paths])

    def test_digests_require_exact_lowercase_hex_lengths(self) -> None:
        source_paths = {
            "prd_sha256": 64, "base_sha": 40, "head_sha": 40, "tree_sha": 40,
            "allowed_input_manifest_sha256": 64,
        }
        for context in (0, 1):
            paths = [(("source_bindings", key), size) for key, size in source_paths.items()]
            paths += [(("policy_binding", "policy_digest"), 64)] if not context else [
                (("policy_digest",), 64), (("allowed_inputs", "manifest_sha256"), 64)]
            if not context:
                paths += [(("reviewer_results", 1, "source_binding_digest"), 64),
                    (("artifacts", 1, "sha256"), 64), (("verification", "code_identity"), 40)]
            self.assert_pairs(context, [
                (path, ["0" * size, "abcdef0123456789" * (size // 16) + "a" * (size % 16)],
                    ["", "a" * (size - 1), "a" * (size + 1), *uppercase_digests(size), "g" * size,
                     "a" * size + "\n", None, 3, True, []])
                for path, size in paths
            ])

    def test_string_arrays_reject_empty_items_and_duplicates(self) -> None:
        for context in (0, 1):
            self.assert_pairs(context, [
                (("source_bindings", "scope", "refs"), [["T1"], ["T2", "T3"]],
                    [[], [""], ["T1", "T1"], [None], [2], "T1", None]),
            ])
        self.assert_pairs(0, [
            (("reviewer_results", 1, "artifact_ids"), [[], ["a", "b"]], [[""], ["a", "a"], [1], None]),
            (("reviewer_results", 1, "finding_ids"), [["f1"], ["f2", "f3"]],
                [[], [""], ["f1", "f1"], [False], None]),
            (("groups", 0, "finding_ids"), [["f1"], ["f2", "f3"]],
                [[], [""], ["f1", "f1"], [None], "f1"]),
            (("verification", "argv"), [["check"], ["python", "check.py"]],
                [[], [""], [True], ["check", None], "check", None]),
        ])
        self.assert_pairs(1, [
            (("session_identities", "builder_session_refs"), [[], ["s1", "s2"]],
                [[""], [None], [3], "s1", None]),
        ])

    def test_input_refs_require_kind_payload_and_uniqueness(self) -> None:
        accepted = [[], ["prd:alpha", "git-diff:beta"]]
        malformed = [[""], ["prd:"], [":a"], ["Prd:a"], ["prd1:a"], ["1prd:a"],
            ["prd:a b"], ["prd:a\tb"], ["prd:a\nb"], *([f"prd:a{w}b"] for w in "\r\f\v\u00a0\u2003\u2028\u2029"), [None], [7], [True], "prd:a", None]
        self.assert_pairs(0, [
            (("reviewer_results", 1, "received_input_refs"), accepted,
                [*malformed, ["prd:a", "prd:a"]]),
        ])
        self.assert_pairs(1, [
            (("allowed_inputs", "input_refs"), accepted, [*malformed, ["prd:a", "prd:a"]]),
            *((("allowed_inputs", "per_job", key), accepted, [*malformed, {}])
                for key in ("j1", "j2", "new-job")),
        ])

    def test_artifact_paths_allow_embedded_dots_and_reject_unsafe_paths(self) -> None:
        self.assert_pairs(0, [
            (("artifacts", 1, "path"), ["docs/a..b.md", "other/review.json", "review.md"],
                ["", "/review.md", "../review.md", "docs/../review.md", "docs/..",
                 *("docs/" * depth + suffix for depth in (2, 3, 7, 16) for suffix in ("../review.md", "..")),
                 "..", "C:/review.md", "z:review.md", "docs\\review.md", "\\server\\review",
                 None, 1, True, []]),
        ])

    def test_context_booleans_and_observed_values_are_typed(self) -> None:
        activation = dict(predicate_id="has-ui", observed=dict(capability="ui", value="yes"))
        for required, active in ((True, None), (False, activation)):
            for bad in (None, 0, 1, "true", [], {}):
                _, context = documents()
                context["resolved_roster"][1].update(required=required, activation=active)
                self.check(context, 1)
                context["resolved_roster"][1]["required"] = bad
                self.check(context, 1, False)
        self.assert_pairs(1, [
            (("session_identities", "independent_contexts_required"), [True, False],
                [None, 0, 1, "false", [], {}]),
            (("resolved_roster", 1, "activation", "observed", "value"), [True, False, "yes", "no"],
                ["", None, 0, 1, [], {}]),
            (("excluded_jobs", 0, "observed", "value"), [True, False, "yes", "no"],
                ["", None, 0, 1, [], {}]),
        ])

    def test_rejects_wrong_shapes_and_empty_roster(self) -> None:
        for context, original in enumerate(documents()):
            for value in ({}, [], None, True, 1, "document"):
                self.check(value, context, False)
            paths = list(objects(original))
            if context:
                paths.append((("allowed_inputs", "per_job"), original["allowed_inputs"]["per_job"]))
            for path, node in paths:
                if path:
                    self.assert_pairs(context, [(path, [node], [[], None, True, 1, "object"])])
        for context, paths in ((0, ["reviewer_results", "artifacts", "findings", "groups", "rubric_verdicts"]),
                               (1, ["resolved_roster", "excluded_jobs"])):
            self.assert_pairs(context, [((key,), [documents()[context][key]], [{}, None, True, "array"])
                for key in paths])
        self.assert_pairs(1, [(("resolved_roster",), [documents()[1]["resolved_roster"]], [[]])])

    def test_not_applicable_requires_a_reason_and_is_closed(self) -> None:
        for reason in ("documentation only", "no executable changes"):
            evidence, _ = documents()
            evidence["verification"] = {"status": "not-applicable", "reason": reason}
            self.check(evidence)
            for bad in ("", None, True, 1, [], {}):
                evidence["verification"]["reason"] = bad
                self.check(evidence, valid=False)
            evidence["verification"]["reason"] = reason
            evidence["verification"]["exit_code"] = 0
            self.check(evidence, valid=False)
        self.assert_pairs(0, [
            (("verification",), [], [{}, {"status": "not-applicable"}, {"reason": "docs only"}]),
            (("verification", "status"), ["ran"], ["run", "Ran", "", None, True]),
        ])

    def test_delta_digests_in_evidence_and_context(self) -> None:
        for context in (0, 1):
            for digest in ("0" * 64, "abcdef01" * 8):
                original = documents()[context]
                original["review_pass"] = "delta"
                original["source_bindings"]["prior_evidence_sha256"] = digest
                self.check(original, context)
                for bad in ("", "a" * 63, "a" * 65, *uppercase_digests(64), "g" * 64, True, 1, None):
                    original["source_bindings"]["prior_evidence_sha256"] = bad
                    self.check(original, context, False)
            original = documents()[context]
            original["source_bindings"]["prior_evidence_sha256"] = "a" * 64
            self.check(original, context, False)
