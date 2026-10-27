"""Golden evidence must satisfy policy beyond its declared case labels."""

from __future__ import annotations

import unittest

from test_contract import FIXTURES_FILE, load
from test_contract_fixtures import ACCEPTED, REJECTED
from test_contract_semantics import validate_review


class GoldenFixtureAdversarialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load(FIXTURES_FILE)
        cls.cases = {case["name"]: case for case in cls.document["cases"]}

    def test_accepted_allowed_and_received_inputs_respect_lane_exclusions(self) -> None:
        for name in ACCEPTED:
            case = self.cases[name]
            context, evidence = case["expected_context"], case["input"]
            policy = self.document["policies"][case["policy"]]
            lane = policy["procedure"]["lanes"][context["lane"]]
            for exclusion in lane["input_exclusions"]:
                job = exclusion["job_id"]
                prohibited = set(exclusion["excluded_input_kinds"])
                with self.subTest(case=name, job=job):
                    allowed = context["allowed_inputs"]["per_job"].get(job, [])
                    self.assertFalse({ref.split(":", 1)[0] for ref in allowed} & prohibited)
                    for result in evidence["reviewer_results"]:
                        if result["job_ref"] == job:
                            received = result["received_input_refs"]
                            self.assertFalse({ref.split(":", 1)[0] for ref in received} & prohibited)

    def test_accepted_execution_bindings_and_fallback_history_are_policy_valid(self) -> None:
        for name in ACCEPTED:
            case = self.cases[name]
            context, evidence = case["expected_context"], case["input"]
            policy = self.document["policies"][case["policy"]]
            bindings = policy["execution_profiles"][context["execution_profile"]]["role_bindings"]
            with self.subTest(case=name):
                self.assertEqual(validate_review(policy, context, evidence), {"outcome": "accepted"})
                for result in evidence["reviewer_results"]:
                    binding = bindings[result["job_ref"]]
                    permitted = {(binding["provider"], adapter) for adapter in binding["adapters"]}
                    fallback = binding["fallback"]
                    if fallback is not None:
                        permitted.update((fallback["provider"], adapter) for adapter in fallback["adapters"])
                    self.assertIn((result["provider"], result["adapter"]), permitted)

    def test_roster_roles_and_accepted_result_roles_match_policy_jobs(self) -> None:
        for name in ACCEPTED | REJECTED.keys():
            case = self.cases[name]
            policy = self.document["policies"][case["policy"]]
            roles = {job["job_id"]: job["role_id"] for job in policy["reviewer_jobs"]}
            with self.subTest(case=name):
                for entry in case["expected_context"]["resolved_roster"]:
                    self.assertEqual(entry["role_id"], roles[entry["job_id"]])
                if name in ACCEPTED:
                    for result in case["input"]["reviewer_results"]:
                        self.assertEqual(result["role_id"], roles[result["job_ref"]])

    def test_accepted_artifact_owners_resolve_to_existing_results(self) -> None:
        for name in ACCEPTED:
            evidence = self.cases[name]["input"]
            result_ids = {result["result_id"] for result in evidence["reviewer_results"]}
            with self.subTest(case=name):
                for artifact in evidence["artifacts"]:
                    if artifact["result_id"] is not None:
                        self.assertIn(artifact["result_id"], result_ids)

    def test_accepted_artifact_identifiers_are_unique(self) -> None:
        for name in ACCEPTED:
            artifacts = self.cases[name]["input"]["artifacts"]
            with self.subTest(case=name):
                self.assertEqual(len({artifact["artifact_id"] for artifact in artifacts}), len(artifacts))

    def test_accepted_rubric_verdict_rows_are_unique_per_result_and_rule(self) -> None:
        for name in ACCEPTED:
            verdicts = self.cases[name]["input"]["rubric_verdicts"]
            identities = [(row["result_id"], row["namespace"], row["rule_id"]) for row in verdicts]
            with self.subTest(case=name):
                self.assertEqual(len(set(identities)), len(identities))

    def test_accepted_job_attempts_start_at_one_and_are_contiguous(self) -> None:
        for name in ACCEPTED:
            case = self.cases[name]
            results = case["input"]["reviewer_results"]
            for entry in case["expected_context"]["resolved_roster"]:
                job = entry["job_id"]
                attempts = sorted(result["attempt"] for result in results if result["job_ref"] == job)
                with self.subTest(case=name, job=job):
                    self.assertTrue(attempts)
                    self.assertEqual(attempts, list(range(1, len(attempts) + 1)))

    def test_rejected_cases_have_exactly_the_specified_complete_semantic_defects(self) -> None:
        for name, defects in REJECTED.items():
            case = self.cases[name]
            policy = self.document["policies"][case["policy"]]
            with self.subTest(case=name):
                self.assertEqual(
                    validate_review(policy, case["expected_context"], case["input"]),
                    {"outcome": "rejected", "defects": sorted(defects)},
                )


if __name__ == "__main__":
    unittest.main()
