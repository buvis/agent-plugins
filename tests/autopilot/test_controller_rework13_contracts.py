"""Rework 13, review cycle 1: findings 8 and 13 (controller contract fixtures).

Each test proves one named finding from the rework task description.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
CONTRACTS = ROOT / "plugins" / "autopilot" / "contracts" / "controller"
BUNDLE = ROOT / "plugins" / "autopilot" / "contracts" / "controller-v1.json"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import protocol


def node(schema: dict, *path: str) -> dict:
    for key in path:
        schema = schema[key]
    return schema


# -- finding 8: the published schema must not contradict runtime shape ------


class WorkflowSchemaMatchesRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads((CONTRACTS / "workflow-v1.json").read_text())

    def test_workflow_schema_permits_a_two_item_tasks_array(self) -> None:
        tasks = node(self.schema, "$defs", "workflow", "properties", "tasks")
        self.assertGreaterEqual(tasks.get("maxItems", 2), 2,
                                "workflow-v1.json still caps workflow.tasks below runtime")

    def test_workflow_schema_permits_a_onejob_jobs_array(self) -> None:
        jobs = node(self.schema, "$defs", "workflow", "properties", "jobs")
        self.assertGreaterEqual(jobs.get("maxItems", 1), 1,
                                "workflow-v1.json still caps workflow.jobs below runtime")

    def test_workflow_schema_permits_an_empty_tasks_or_jobs_array_too(self) -> None:
        # Edge case: the schema must still accept the drained/default shape.
        tasks = node(self.schema, "$defs", "workflow", "properties", "tasks")
        jobs = node(self.schema, "$defs", "workflow", "properties", "jobs")
        self.assertLessEqual(tasks.get("minItems", 0), 0)
        self.assertLessEqual(jobs.get("minItems", 0), 0)

    def test_bundle_schema_permits_every_runtime_capability(self) -> None:
        metadata, _ = protocol.public_contract()
        capabilities = node(self.schema, "$defs", "bundle", "properties", "capabilities")
        permitted = set(capabilities.get("const") or capabilities.get("items", {}).get(
            "enum", []))
        self.assertTrue(set(metadata["capabilities"]) <= permitted,
                        "the schema's capabilities node does not permit every "
                        "runtime-discovered capability")

    def test_bundle_schema_permits_every_runtime_operation(self) -> None:
        metadata, _ = protocol.public_contract()
        operations = node(self.schema, "$defs", "bundle", "properties", "operations")
        permitted = set(operations.get("items", {}).get("enum", []))
        self.assertTrue(set(metadata["operations"]) <= permitted,
                        "the schema's operations node does not permit every "
                        "runtime-discovered operation")
        max_items = operations.get("maxItems")
        if max_items is not None:
            self.assertGreaterEqual(max_items, len(metadata["operations"]))


# -- finding 13: the installed bundle must equal runtime discovery ----------


class InstalledBundleMatchesRuntimeTest(unittest.TestCase):
    def test_installed_bundle_operations_equal_runtime_discovery(self) -> None:
        metadata, _ = protocol.public_contract()
        bundle = json.loads(BUNDLE.read_text())
        self.assertEqual(set(bundle["operations"]), set(metadata["operations"]))

    def test_installed_bundle_capabilities_equal_runtime_discovery(self) -> None:
        metadata, _ = protocol.public_contract()
        bundle = json.loads(BUNDLE.read_text())
        self.assertEqual(set(bundle["capabilities"]), set(metadata["capabilities"]))


if __name__ == "__main__":
    unittest.main()
