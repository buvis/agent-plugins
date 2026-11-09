"""Pinned ownership and closed protocol examples without an OVCAQ checkout."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts" / "controller"
sys.path.insert(0, str(ROOT / "plugins" / "autopilot" / "controller"))

from autopilot_state import schema

FIXTURES = json.loads((CONTRACTS / "fixtures-v1.json").read_text())
CASES = {case["name"]: case for case in FIXTURES["cases"]}
CONTRACT = json.loads((CONTRACTS / "workflow-v1.json").read_text())


class RecoveryCharacterizationTest(unittest.TestCase):
    def assert_state_rejected(self, value: object) -> None:
        validator = Draft202012Validator({**CONTRACT, "$ref": "#/$defs/state"})
        self.assertFalse(validator.is_valid(value))
        with self.assertRaises(schema.SchemaError):
            schema.validate_state(value)

    def test_kernel_field_ownership_matches_pinned_source_characterization(self) -> None:
        provenance = json.loads((CONTRACTS / "provenance.json").read_text())
        ownership = FIXTURES["kernel_field_ownership"]
        pin = "cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7"
        self.assertEqual(provenance["source"]["commit"], pin)
        self.assertEqual(ownership["source_commit"], pin)
        self.assertEqual(len(provenance["field_ownership"]), 144)
        mappings = {
            row["source"]: row["target"]
            for row in provenance["field_ownership"]
            if row["disposition"] in ("preserved", "redesigned")
        }
        self.assertEqual(ownership["core_mappings"], {
            "WorkState.repo_root": "repo_root",
            "ReviewState.cap": "workflow.review.cap",
            "State.schema_version": "schema_version",
            "State.revision": "revision",
        })
        self.assertEqual(mappings, ownership["core_mappings"])
        self.assertEqual(CASES["kernel-initial"]["input"]["workflow"], {
            "batch": None, "work": None, "tasks": [], "review": {"cap": 2},
            "recovery": None, "jobs": [],
        })

    def test_kernel_field_ownership_rejects_unowned_fields(self) -> None:
        ownership = FIXTURES["kernel_field_ownership"]
        self.assertEqual(ownership["expected_error"], "invalid_request")
        validator = Draft202012Validator({**CONTRACT, "$ref": "#/$defs/state"})
        for name in ("kernel-initial", "kernel-owned"):
            original = CASES[name]["input"]
            validator.validate(original)
            self.assertEqual(schema.validate_state(original), original)
            for field in ownership["unowned_fields"]:
                for location in ((), ("workflow",)):
                    changed = copy.deepcopy(original)
                    target = changed[location[0]] if location else changed
                    target[field] = None
                    with self.subTest(case=name, field=field, location=location):
                        self.assertFalse(validator.is_valid(changed))
                        with self.assertRaises(schema.SchemaError):
                            schema.validate_state(changed)

    def test_kernel_state_requires_every_owned_top_level_field(self) -> None:
        self.assert_state_rejected({})
        original = CASES["kernel-initial"]["input"]
        for field in original:
            changed = copy.deepcopy(original)
            del changed[field]
            with self.subTest(missing=field):
                self.assert_state_rejected(changed)

    def test_kernel_revision_rejects_noninteger_text(self) -> None:
        changed = copy.deepcopy(CASES["kernel-initial"]["input"])
        changed["revision"] = "nonsense"
        self.assert_state_rejected(changed)

    def test_kernel_revisions_and_epochs_reject_negative_values(self) -> None:
        locations = (
            ("revision",), ("lease_epoch",), ("owner", "lease_epoch"),
            ("actors", "operator-synthetic", "lease_epoch"),
            ("actors", "owner-synthetic", "lease_epoch"),
            ("receipts", "open-synthetic", "authorizing_actor", "lease_epoch"),
            ("receipts", "open-synthetic", "response", "revision"),
            ("receipts", "open-synthetic", "response", "result", "lease_epoch"),
        )
        for location in locations:
            changed = copy.deepcopy(CASES["kernel-owned"]["input"])
            target = changed
            for field in location[:-1]:
                target = target[field]
            target[location[-1]] = -1
            with self.subTest(location=location):
                self.assert_state_rejected(changed)

    def test_kernel_owner_rejects_process_identity(self) -> None:
        changed = copy.deepcopy(CASES["kernel-owned"]["input"])
        changed["owner"]["process_identity"] = "synthetic-process"
        self.assert_state_rejected(changed)

    def test_kernel_actor_registry_rejects_three_valid_descriptors(self) -> None:
        changed = copy.deepcopy(CASES["kernel-owned"]["input"])
        extra = copy.deepcopy(changed["actors"]["operator-synthetic"])
        extra["actor_id"] = "operator-extra"
        changed["actors"]["operator-extra"] = extra
        validator = Draft202012Validator({**CONTRACT, "$ref": "#/$defs/actor"})
        for descriptor in changed["actors"].values():
            validator.validate(descriptor)
        self.assertEqual(len(changed["actors"]), 3)
        self.assert_state_rejected(changed)

    def test_kernel_tasks_cannot_be_populated(self) -> None:
        changed = copy.deepcopy(CASES["kernel-initial"]["input"])
        changed["workflow"]["tasks"] = ["synthetic-task"]
        self.assert_state_rejected(changed)

    def test_kernel_review_cap_remains_two(self) -> None:
        changed = copy.deepcopy(CASES["kernel-initial"]["input"])
        changed["workflow"]["review"]["cap"] = 99
        self.assert_state_rejected(changed)

    def test_kernel_accepts_independent_states_beyond_frozen_examples(self) -> None:
        validator = Draft202012Validator({**CONTRACT, "$ref": "#/$defs/state"})
        for revision in (0, 2):
            value = {
                "schema_version": 1, "revision": revision,
                "project_id": "f" * 64,
                "workflow_id": f"independent-workflow-{revision}",
                "repo_root": "/independent/project", "lease_epoch": 0,
                "owner": None, "actors": {}, "receipts": {},
                "workflow": {
                    "batch": None, "work": None, "tasks": [],
                    "review": {"cap": 2}, "recovery": None, "jobs": [],
                },
            }
            with self.subTest(revision=revision):
                validator.validate(value)
                self.assertEqual(schema.validate_state(value), value)

    def test_contract_examples_reject_unowned_envelope_payload_and_response_fields(self) -> None:
        self.assertEqual({example["case"] for example in FIXTURES["contract_examples"]}, {
            "open-fresh", "open-existing", "acquire", "release", "recover",
            "open-result", "acquire-result", "release-result", "recover-result",
        })
        for example in FIXTURES["contract_examples"]:
            case = CASES[example["case"]]
            validator = Draft202012Validator({
                **CONTRACT, "$ref": f"#/$defs/{case['definition']}",
            })
            self.assertTrue(case["valid"])
            self.assertEqual(example["expected_error"], "invalid_request")
            validator.validate(case["input"])
            for location in example["unowned_locations"]:
                changed = copy.deepcopy(case["input"])
                target = changed
                for field in location:
                    target = target[field]
                target["process_identity"] = "synthetic-unowned"
                with self.subTest(case=example["case"], location=location):
                    self.assertFalse(validator.is_valid(changed))


if __name__ == "__main__":
    unittest.main()
