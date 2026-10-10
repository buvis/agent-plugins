"""State schema and the state content scan (T-021)."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(
    0,
    str(REPO / "plugins" / "specflow" / "skills" / "spec-workflow" / "scripts"),
)

from specflow_helper import WORKFLOW_VERSION
from specflow_helper.schema import check_content, check_schema, load_schema

FIXTURES = REPO / "tests" / "specflow" / "fixtures" / "state"
SCHEMA_ID = (
    "https://raw.githubusercontent.com/buvis/agent-plugins/specflow-v{v}/"
    "plugins/specflow/skills/spec-workflow/schemas/specflow-state.schema.json"
)


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class StateSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load_schema("specflow-state.schema.json")
        self.full = fixture("full.specflow.json")

    def errors(self, state: dict) -> list[str]:
        return check_schema(state, self.schema)

    def assert_fails_at(self, state: dict, path: str) -> None:
        errors = self.errors(state)
        self.assertTrue(any(e.startswith(f"{path}:") for e in errors), errors)

    def test_valid_fixtures_pass(self) -> None:
        for name in ("full.specflow.json", "calcard-00032.specflow.json"):
            with self.subTest(name=name):
                self.assertEqual(self.errors(fixture(name)), [])

    def test_hand_written_state_with_fractional_seconds_passes(self) -> None:
        state = fixture("calcard-00032.specflow.json")
        self.assertIn(".", state["artifacts"]["requirements"]["approvedAt"])
        self.assertEqual(self.errors(state), [])

    def test_wrong_type_fails_with_its_path(self) -> None:
        self.full["specId"] = 42
        self.assert_fails_at(self.full, "$.specId")

    def test_missing_required_field_fails_with_its_parent_path(self) -> None:
        del self.full["artifacts"]["tasks"]["status"]
        self.assertIn(
            "$.artifacts.tasks: missing required field status",
            self.errors(self.full),
        )

    def test_unknown_artifact_status_fails(self) -> None:
        self.full["artifacts"]["design"]["status"] = "done"
        self.assert_fails_at(self.full, "$.artifacts.design.status")

    def test_unsupported_schema_version_fails(self) -> None:
        self.full["schemaVersion"] = 2
        self.assert_fails_at(self.full, "$.schemaVersion")

    def test_boolean_is_not_an_integer(self) -> None:
        self.full["schemaVersion"] = True
        self.assert_fails_at(self.full, "$.schemaVersion")

    def test_pattern_must_match_the_whole_string(self) -> None:
        self.full["artifacts"]["tasks"]["sha256"] = "4" * 64 + "x"
        self.assert_fails_at(self.full, "$.artifacts.tasks.sha256")

    def test_unknown_extra_field_passes(self) -> None:
        self.full["artifacts"]["tasks"]["laterField"] = [1, 2]
        self.assertEqual(self.errors(self.full), [])

    def test_approved_code_takes_one_of_three_shapes(self) -> None:
        design = self.full["artifacts"]["design"]
        for code in (
            {"status": "not_checked", "reason": "no placement section"},
            {"status": "not_applicable", "reason": "the design changes no file"},
        ):
            with self.subTest(status=code["status"]):
                design["approvedCode"] = code
                self.assertEqual(self.errors(self.full), [])
        design["approvedCode"] = {"status": "captured", "reason": "partial"}
        self.assert_fails_at(self.full, "$.artifacts.design.approvedCode")

    def test_code_file_needs_a_hash_or_a_missing_flag_not_both(self) -> None:
        files = self.full["artifacts"]["design"]["approvedCode"]["files"]
        files[0]["missing"] = True
        self.assert_fails_at(self.full, "$.artifacts.design.approvedCode")

    def test_hold_needs_a_known_status_and_a_date(self) -> None:
        bad = copy.deepcopy(self.full)
        bad["hold"]["status"] = "paused"
        self.assert_fails_at(bad, "$.hold.status")
        self.full["hold"]["since"] = "2026-10-01T00:00:00Z"
        self.assert_fails_at(self.full, "$.hold.since")

    def test_schema_carries_its_public_address(self) -> None:
        self.assertEqual(self.schema["$id"], SCHEMA_ID.format(v=WORKFLOW_VERSION))


class SchemaKeywordTest(unittest.TestCase):
    def test_unknown_keyword_in_a_schema_is_an_error(self) -> None:
        errors = check_schema(3, {"type": "integer", "minimum": 1})
        self.assertEqual(errors, ["$: schema keyword minimum is not supported"])

    def test_annotations_are_ignored(self) -> None:
        schema = {
            "$schema": "x",
            "$id": "y",
            "title": "t",
            "description": "d",
            "type": "string",
        }
        self.assertEqual(check_schema("ok", schema), [])

    def test_unresolvable_reference_is_an_error(self) -> None:
        errors = check_schema(1, {"$ref": "#/$defs/nothing"})
        self.assertEqual(
            errors,
            ["$: schema reference #/$defs/nothing cannot be resolved"],
        )

    def test_closed_object_rejects_an_extra_field(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {}},
            "additionalProperties": False,
        }
        self.assertEqual(
            check_schema({"a": 1, "b": 2}, schema),
            ["$.b: field is not allowed"],
        )


class StateContentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.full = fixture("full.specflow.json")

    def test_clean_fixtures_pass(self) -> None:
        for name in ("full.specflow.json", "calcard-00032.specflow.json"):
            with self.subTest(name=name):
                self.assertEqual(check_content(fixture(name)), [])

    def test_seeded_secret_transcript_and_session_id_are_caught(self) -> None:
        for key in ("secret", "transcript", "sessionId", "apiKey", "prompt"):
            with self.subTest(key=key):
                state = copy.deepcopy(self.full)
                state["artifacts"]["design"][key] = "x"
                self.assertEqual(
                    check_content(state),
                    [f"$.artifacts.design.{key}: state must not hold a {key} field"],
                )

    def test_seeded_absolute_paths_are_caught(self) -> None:
        for value in ("/Users/me/repo", "~/repo", "C:\\repo", "D:/repo"):
            with self.subTest(value=value):
                state = copy.deepcopy(self.full)
                state["artifacts"]["tasks"]["path"] = value
                self.assertEqual(
                    check_content(state),
                    ["$.artifacts.tasks.path: state must not hold an absolute path"],
                )

    def test_absolute_path_in_a_code_baseline_is_caught(self) -> None:
        self.full["artifacts"]["design"]["approvedCode"]["files"][0]["path"] = (
            "/etc/passwd"
        )
        self.assertEqual(len(check_content(self.full)), 1)

    def test_free_text_may_start_with_a_slash(self) -> None:
        self.full["artifacts"]["design"]["approvedCode"] = {
            "status": "not_checked",
            "reason": "/src is not readable",
        }
        self.assertEqual(check_content(self.full), [])


if __name__ == "__main__":
    unittest.main()
