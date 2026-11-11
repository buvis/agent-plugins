"""The runtime must agree with the frozen request schema and recorded scenarios."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from controller_cli_support import CONTRACT, canonical
from controller_owner_support import OwnerCLITest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import protocol

SCENARIO_KEYS = {"name", "setup", "action", "expected_error", "expected"}
EVIDENCE_CASE = "recover-nonempty-jobs"
NULL_OPEN = {"protocol_major": 1, "operation": "workflow.open",
             "request_id": "open-direct", "expected_revision": 0,
             "project_id": "a" * 64, "workflow_id": None, "actor_id": None,
             "job_id": None, "lease_epoch": None, "payload": {}}
BOUND_RELEASE = {"protocol_major": 1, "operation": "owner.release",
                 "request_id": "release-direct", "expected_revision": 3,
                 "project_id": "b" * 64, "workflow_id": "workflow-direct",
                 "actor_id": "operator-direct", "job_id": None,
                 "lease_epoch": 2, "payload": {}}


class RequestParsingAgreementTest(unittest.TestCase):
    """`parse_request` must accept and refuse exactly what the contract declares."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads((CONTRACT / "fixtures-v1.json").read_text(encoding="utf-8"))
        _, cls.declared = protocol.public_contract()

    def test_runtime_parser_agrees_with_every_frozen_request_case(self) -> None:
        cases = [case for case in self.fixtures["cases"]
                 if case["definition"] == "request"]
        self.assertGreater(len(cases), 1, "no frozen request case was collected")
        self.assertTrue([case for case in cases if case["valid"]])
        self.assertTrue([case for case in cases if not case["valid"]])
        for case in cases:
            with self.subTest(case=case["name"]):
                raw = canonical(case["input"])
                if case["valid"]:
                    self.assertIsNone(case["expected_error"])
                    self.assertEqual(protocol.parse_request(raw, self.declared),
                                     case["input"])
                    continue
                self.assertIsNotNone(case["expected_error"])
                with self.assertRaises(protocol.ProtocolError) as caught:
                    protocol.parse_request(raw, self.declared)
                self.assertEqual(caught.exception.code, case["expected_error"])

    def test_null_workflow_id_admits_only_a_zero_revision_unbound_open(self) -> None:
        self.assertEqual(protocol.parse_request(canonical(NULL_OPEN), self.declared),
                         NULL_OPEN)
        rejected = {
            "owner operation": {"operation": "owner.release"},
            "non-null actor at revision zero": {"actor_id": "operator-direct"},
            "non-null lease epoch": {"lease_epoch": 0},
            "nonzero expected revision": {"expected_revision": 1},
        }
        for clause, change in rejected.items():
            with self.subTest(clause=clause):
                with self.assertRaises(protocol.ProtocolError) as caught:
                    protocol.parse_request(canonical(NULL_OPEN | change), self.declared)
                self.assertEqual(caught.exception.code, "invalid_request")

    def test_bound_workflow_id_requires_an_identity_actor_and_nonnegative_epoch(self) -> None:
        self.assertEqual(protocol.parse_request(canonical(BOUND_RELEASE), self.declared),
                         BOUND_RELEASE)
        self.assertEqual(protocol.parse_request(
            canonical(BOUND_RELEASE | {"lease_epoch": 0}), self.declared),
            BOUND_RELEASE | {"lease_epoch": 0})
        rejected = {
            "null actor": {"actor_id": None},
            "empty actor": {"actor_id": ""},
            "null lease epoch": {"lease_epoch": None},
            "negative lease epoch": {"lease_epoch": -1},
        }
        for clause, change in rejected.items():
            with self.subTest(clause=clause):
                with self.assertRaises(protocol.ProtocolError) as caught:
                    protocol.parse_request(canonical(BOUND_RELEASE | change),
                                           self.declared)
                self.assertEqual(caught.exception.code, "invalid_request")


class RecoveryEvidenceScenarioTest(unittest.TestCase):
    """The refused recovery-evidence rule must be recorded in the frozen fixtures."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads((CONTRACT / "fixtures-v1.json").read_text(encoding="utf-8"))

    def test_scenarios_record_the_refused_nonempty_recovery_evidence(self) -> None:
        scenarios = self.fixtures["scenarios"]
        self.assertIn(EVIDENCE_CASE, [case["name"] for case in self.fixtures["cases"]
                                      if case["definition"] == "request"])
        others = [item for item in scenarios if EVIDENCE_CASE not in item["action"]]
        self.assertTrue(others, "no other scenario remained for a shape comparison")
        for item in others:
            self.assertEqual(set(item), SCENARIO_KEYS)
        matching = [item for item in scenarios if EVIDENCE_CASE in item["action"]]
        self.assertEqual(len(matching), 1,
                         f"scenarios must apply {EVIDENCE_CASE} exactly once")
        scenario = matching[0]
        self.assertEqual(set(scenario), SCENARIO_KEYS)
        self.assertEqual(scenario["expected_error"], "rejected_evidence")
        self.assertTrue(scenario["expected"])
        self.assertEqual(len({item["name"] for item in scenarios}), len(scenarios))


class RecoveryEvidenceRuntimeTest(OwnerCLITest):
    """Non-empty reconciled job evidence is refused; an empty list is admitted."""

    def recover(self, operator: Path, request_id: str, jobs: list[str]) -> dict:
        return self.request(operator, "owner.recover", request_id,
                            {"reason": "Explicit reconciliation evidence check",
                             "reconciled_job_ids": jobs})

    def test_owner_recover_refuses_nonempty_job_evidence_and_admits_an_empty_list(self) -> None:
        _, _, operator = self.bootstrap()
        _, _, _, operator = self.acquire(operator, session="session-evidence")
        owned = self.state()
        self.assertIsNotNone(owned["owner"])
        for index, jobs in enumerate((["job-alpha"], ["job-alpha", "job-beta"])):
            with self.subTest(reconciled_job_ids=jobs):
                request = self.recover(operator, f"recover-evidence-{index}", jobs)
                self.reject_unchanged(request, operator, "rejected_evidence")
                self.assertEqual(self.state(), owned)
        accepted = self.recover(operator, "recover-evidence-empty", [])
        response = self.response(self.apply(accepted, operator),
                                 revision=owned["revision"] + 1)
        self.assert_transition(accepted, response, operator)
        self.assertIsNone(self.state()["owner"])
        self.assertEqual(self.state()["revision"], owned["revision"] + 1)


if __name__ == "__main__":
    unittest.main()
