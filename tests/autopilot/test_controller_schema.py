"""Public schema and decoder behavior from the frozen controller contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from controller_test_support import WORKFLOW, actor, canonical, frozen_state

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import schema


class SchemaTest(unittest.TestCase):
    def assert_invalid(self, value: object) -> None:
        with self.assertRaises((schema.SchemaError, schema.ResourceLimitError)):
            schema.validate_state(value)

    def test_published_resource_limits_are_exact(self) -> None:
        expected = {
            "SCHEMA_VERSION": 1, "MAX_STATE_BYTES": 16777216,
            "MAX_COMMAND_PAYLOAD_BYTES": 2097152, "MAX_STRING_BYTES": 1048576,
            "MAX_JSON_DEPTH": 32, "MAX_JSON_INTEGER_DIGITS": 640,
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(schema, name), value)
                self.assertIs(type(getattr(schema, name)), int)

    def test_decodes_complete_json_and_preserves_distinct_nested_values(self) -> None:
        values = ({}, [], {"alpha": [1, 2], "alpha-extra": [3, 4]},
                  {"東京": {"first": "žluť", "last": "other"}})
        for index, value in enumerate(values):
            with self.subTest(value=value):
                text = canonical(value).decode("utf-8")
                self.assertEqual(schema.decode_json(text, source=f"fixture-{index}"), value)

    def test_rejects_duplicate_keys_nonfinite_numbers_and_malformed_json(self) -> None:
        texts = ("", "{", "{} trailing", "{\"same\":1,\"same\":2}",
                 "{\"nested\":{\"same\":1,\"same\":2}}",
                 "[NaN]", "{\"first\":Infinity}", "[0,-Infinity]",
                 "{\"value\":1e999}")
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaises((schema.SchemaError, schema.ResourceLimitError)):
                    schema.decode_json(text, source="invalid-fixture")

    def test_decoder_rejects_byte_depth_and_integer_resource_overflow(self) -> None:
        texts = ("[" * 34 + "0" + "]" * 34, "9" * 641,
                 json.dumps("x" * 1048577), json.dumps("é" * 524289, ensure_ascii=False),
                 " " * 16777216 + "{}")
        for text in texts:
            with self.subTest(prefix=text[:30], size=len(text)):
                with self.assertRaises((schema.SchemaError, schema.ResourceLimitError)):
                    schema.decode_json(text, source="oversized-fixture")
        self.assertEqual(schema.decode_json("9" * 640, source="integer-boundary"),
                         int("9" * 640))

    def test_accepts_both_frozen_states_and_retains_receipt_history(self) -> None:
        for owned in (False, True):
            value = frozen_state(owned=owned)
            original = copy.deepcopy(value)
            with self.subTest(owned=owned):
                self.assertEqual(schema.validate_state(value), original)
                self.assertEqual(value, original)
                decoded = schema.decode_json(canonical(value).decode(), source="frozen")
                self.assertEqual(schema.validate_state(decoded), original)
        self.assertEqual(frozen_state(owned=True)["receipts"]["open-synthetic"]
                         ["authorizing_actor"]["lease_epoch"], 0)

    def test_new_state_uses_explicit_project_and_workflow_inputs_with_fresh_reserves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for name in ("project", "project-extra"):
                root = Path(temporary) / name
                root.mkdir()
                project_id = hashlib.sha256(str(root).encode()).hexdigest()
                value = schema.new_state(repo_root=root, project_id=project_id, workflow_id=name)
                self.assertEqual(value, {
                    "schema_version": 1, "revision": 0, "project_id": project_id,
                    "workflow_id": name, "repo_root": str(root), "lease_epoch": 0,
                    "owner": None, "actors": {}, "receipts": {},
                    "workflow": WORKFLOW,
                })
                self.assertEqual(schema.validate_state(value), value)
                value["workflow"]["tasks"].append("local mutation")
                fresh = schema.new_state(repo_root=root, project_id=project_id, workflow_id=name)
                self.assertEqual(fresh["workflow"], WORKFLOW)

    def test_rejects_missing_unknown_and_process_owned_fields(self) -> None:
        self.assert_invalid(None)
        self.assert_invalid([])
        self.assert_invalid({})
        for key in frozen_state():
            value = frozen_state()
            del value[key]
            with self.subTest(missing=key):
                self.assert_invalid(value)
        fields = ("schema_version_extra", "revision_extra", "pid", "launcher",
                  "heartbeat", "resource_usage", "tui", "process_identity")
        for field in fields:
            for location in ((), ("workflow",)):
                value = frozen_state()
                target = value[location[0]] if location else value
                target[field] = None
                with self.subTest(field=field, location=location):
                    self.assert_invalid(value)

    def test_rejects_unsupported_versions_bool_integers_and_fractional_counters(self) -> None:
        for version in (0, 2, -1, True, False, "1", 1.0, None):
            value = frozen_state()
            value["schema_version"] = version
            with self.subTest(version=version):
                self.assert_invalid(value)
        for key in ("revision", "lease_epoch"):
            for number in (True, False, -1, 0.5, "0", None, float("nan")):
                value = frozen_state()
                value[key] = number
                with self.subTest(key=key, number=number):
                    self.assert_invalid(value)

    def test_workflow_reserves_cannot_be_extended_or_populated(self) -> None:
        changes = (("batch", {}), ("work", {}), ("tasks", ["task"]),
                   ("recovery", {}), ("jobs", ["job"]),
                   ("review", {"cap": 1}), ("review", {"cap": True}),
                   ("review", {"cap": 2, "cap_extra": 2}),
                   ("tasks", ["first", "last"]))
        for key, replacement in changes:
            value = frozen_state()
            value["workflow"][key] = replacement
            with self.subTest(key=key, replacement=replacement):
                self.assert_invalid(value)
        for key in WORKFLOW:
            value = frozen_state()
            del value["workflow"][key]
            with self.subTest(missing=key):
                self.assert_invalid(value)

    def test_actor_owner_and_receipt_objects_have_closed_fields_and_bounded_identities(self) -> None:
        locations = (("owner",), ("actors", "operator-synthetic"),
                     ("actors", "owner-synthetic"),
                     ("receipts", "open-synthetic"),
                     ("receipts", "open-synthetic", "authorizing_actor"),
                     ("receipts", "open-synthetic", "response"))
        for location in locations:
            value = frozen_state(owned=True)
            target = value
            for key in location:
                target = target[key]
            target["actor_id_extra"] = "unowned"
            with self.subTest(location=location):
                self.assert_invalid(value)
        for identity in ("", "é" * 129, "x" * 257):
            value = frozen_state()
            value["workflow_id"] = identity
            with self.subTest(identity=identity):
                self.assert_invalid(value)

    def test_actor_roles_owner_modes_and_secret_fields_reject_near_matches(self) -> None:
        changes = (("role", "operator-extra"), ("role", "owner-extra"),
                   ("secret_digest", "b" * 63), ("secret_digest", "B" * 64),
                   ("native_session_id", "session-for-operator"),
                   ("lease_epoch", True), ("secret", "credential-secret"))
        for key, replacement in changes:
            value = frozen_state()
            value["actors"]["operator-synthetic"][key] = replacement
            with self.subTest(key=key, replacement=replacement):
                self.assert_invalid(value)
        for mode in ("manual-extra", "supervised-extra", "", None):
            value = frozen_state(owned=True)
            value["owner"]["mode"] = mode
            with self.subTest(mode=mode):
                self.assert_invalid(value)
        for mode in ("manual", "supervised"):
            value = frozen_state(owned=True)
            value["owner"]["mode"] = mode
            self.assertEqual(schema.validate_state(value), value)

    def test_receipts_retain_complete_success_responses_and_reject_oversized_responses(self) -> None:
        value = frozen_state()
        receipt = value["receipts"]["open-synthetic"]
        value["receipts"]["open-synthetic-extra"] = copy.deepcopy(receipt)
        value["receipts"]["open-synthetic-extra"]["request_digest"] = "d" * 64
        self.assertEqual(schema.validate_state(value), value)
        for key in receipt["response"]:
            changed = copy.deepcopy(value)
            del changed["receipts"]["open-synthetic-extra"]["response"][key]
            with self.subTest(missing=key):
                self.assert_invalid(changed)
        changed = copy.deepcopy(value)
        changed["receipts"]["open-synthetic-extra"]["response"]["result"]["actor_file"] = "/" + "x" * 65536
        self.assert_invalid(changed)

    def test_actor_and_receipt_cardinality_limits_include_empty_and_multi_element_cases(self) -> None:
        value = frozen_state()
        value["actors"] = {}
        value["receipts"] = {}
        self.assertEqual(schema.validate_state(value), value)
        value = frozen_state(owned=True)
        self.assertEqual(schema.validate_state(value), value)
        value["actors"]["operator-extra"] = actor(actor_id="operator-extra")
        self.assert_invalid(value)
        value = frozen_state()
        receipt = value["receipts"]["open-synthetic"]
        value["receipts"] = {f"request-{index}": copy.deepcopy(receipt)
                             for index in range(4096)}
        self.assertEqual(schema.validate_state(value), value)
        value["receipts"]["request-4096"] = copy.deepcopy(receipt)
        self.assert_invalid(value)

    def test_total_state_byte_limit_is_independent_of_receipt_count_and_string_limits(self) -> None:
        value = frozen_state()
        receipt = value["receipts"]["open-synthetic"]
        receipt["response"]["result"]["actor_file"] = "/" + "x" * 60000
        self.assertLess(len(canonical(receipt["response"])), 65536)
        self.assertEqual(schema.validate_state(value), value)
        value["receipts"] = {f"request-{index}": copy.deepcopy(receipt) for index in range(280)}
        self.assertLess(len(value["receipts"]), 4094)
        self.assertGreater(len(canonical(value)), schema.MAX_STATE_BYTES)
        self.assert_invalid(value)

    def test_validation_rejects_invalid_data_before_copying_objects(self) -> None:
        copies = []

        class InvalidValue:
            def __deepcopy__(self, memo: dict) -> object:
                copies.append(True)
                raise AssertionError("Invalid values must be rejected before copying")

        for field in ("workflow_id", "revision"):
            value = frozen_state()
            value[field] = InvalidValue()
            with self.subTest(field=field):
                self.assert_invalid(value)
        self.assertEqual(copies, [])


class DecoderRegressionTest(unittest.TestCase):
    def test_finite_decimals_preserve_positive_negative_and_exponent_values(self) -> None:
        text = '{"values":[1.25,-2.5,3.125e2,-4.5E-2,0.0625]}'
        expected = {"values": [1.25, -2.5, 312.5, -0.045, 0.0625]}
        self.assertEqual(schema.decode_json(text, source="finite-decimals"), expected)

    def test_identical_duplicate_keys_are_rejected_at_top_level_and_nested(self) -> None:
        texts = ('{"same":1,"same":1}',
                 '{"nested":{"same":1,"same":1}}',
                 '[{"same":null,"same":null}]')
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaises(schema.SchemaError):
                    schema.decode_json(text, source="identical-duplicates")

    def test_negative_integer_digit_limit_accepts_boundary_and_rejects_overflow(self) -> None:
        boundary = "-" + "9" * schema.MAX_JSON_INTEGER_DIGITS
        self.assertEqual(schema.decode_json(boundary, source="negative-boundary"),
                         int(boundary))
        with self.assertRaises(schema.ResourceLimitError):
            schema.decode_json(boundary + "9", source="negative-overflow")

    def test_object_key_limits_measure_utf8_bytes_for_ascii_and_multibyte_keys(self) -> None:
        for character, count in (("x", schema.MAX_STRING_BYTES),
                                 ("é", schema.MAX_STRING_BYTES // 2)):
            key = character * count
            accepted = {key: 1}
            with self.subTest(character=character):
                text = json.dumps(accepted, ensure_ascii=False)
                self.assertEqual(schema.decode_json(text, source="key-boundary"), accepted)
                overflow = json.dumps({key + character: 1}, ensure_ascii=False)
                with self.assertRaises(schema.ResourceLimitError):
                    schema.decode_json(overflow, source="key-overflow")


class SchemaRegressionTest(unittest.TestCase):
    def test_active_and_receipt_actor_ids_reject_invalid_types_and_oversized_strings(self) -> None:
        invalid = (None, True, False, 7, 1.5, [], {}, "", "x" * 257, "é" * 129)
        for location in ("active", "receipt"):
            for actor_id in invalid:
                value = frozen_state()
                if location == "active":
                    descriptor = value["actors"]["operator-synthetic"]
                else:
                    descriptor = value["receipts"]["open-synthetic"]["authorizing_actor"]
                descriptor["actor_id"] = actor_id
                with self.subTest(location=location, actor_id=actor_id):
                    with self.assertRaises(schema.SchemaError):
                        schema.validate_state(value)

    def test_receipt_response_revision_rejects_bool_string_and_negative_counters(self) -> None:
        for revision in (True, False, "0", -1, None, 0.5):
            value = frozen_state()
            value["receipts"]["open-synthetic"]["response"]["revision"] = revision
            with self.subTest(revision=revision):
                with self.assertRaises(schema.SchemaError):
                    schema.validate_state(value)


if __name__ == "__main__":
    unittest.main()
