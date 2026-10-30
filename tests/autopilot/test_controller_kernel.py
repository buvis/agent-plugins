"""Public guarded kernel behavior from the frozen AP00018 contract."""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "plugins" / "autopilot" / "controller"
sys.path.insert(0, str(CONTROLLER))

from autopilot_state import schema
from autopilot_state.paths import resolve_project_root
from autopilot_state.store import (
    BackupError, DurabilityBoundary, DurabilityUnsupportedError, FutureSchemaError,
    RevisionConflictError, StateError, StateExistsError, StateIOError,
    StateResourceLimitError, StateStore,
)


WORKFLOW = {
    "batch": None, "work": None, "tasks": [],
    "review": {"cap": 2}, "recovery": None, "jobs": [],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def actor(*, actor_id: str = "operator-synthetic", role: str = "operator",
          epoch: int = 0, digest: str = "b" * 64) -> dict:
    return {
        "actor_id": actor_id, "project_id": "a" * 64,
        "workflow_id": "workflow-synthetic", "role": role,
        "lease_epoch": epoch,
        "native_session_id": "session-synthetic" if role == "owner" else None,
        "secret_digest": digest,
    }


def frozen_state(*, owned: bool = False) -> dict:
    operator = actor()
    result = {
        "schema_version": 1, "revision": 0, "project_id": "a" * 64,
        "workflow_id": "workflow-synthetic", "repo_root": "/synthetic/project",
        "lease_epoch": 0, "owner": None,
        "actors": {operator["actor_id"]: operator},
        "receipts": {"open-synthetic": {
            "request_digest": "c" * 64, "authorizing_actor": copy.deepcopy(operator),
            "response": {
                "ok": True, "revision": 0, "result": {
                    "workflow_id": "workflow-synthetic",
                    "actor_id": "operator-synthetic",
                    "actor_file": "/synthetic/project/.autopilot/controller/actors/operator.json",
                    "lease_epoch": 0,
                }, "error_code": None, "retryable": False,
            },
        }},
        "workflow": copy.deepcopy(WORKFLOW),
    }
    if owned:
        owner = actor(actor_id="owner-synthetic", role="owner", epoch=1, digest="e" * 64)
        result.update(revision=1, lease_epoch=1, owner={
            "actor_id": owner["actor_id"], "mode": "supervised",
            "native_session_id": owner["native_session_id"], "lease_epoch": 1,
        })
        result["actors"] = {
            "operator-synthetic": actor(epoch=1, digest="d" * 64),
            "owner-synthetic": owner,
        }
    return result


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


class ProjectRootTest(unittest.TestCase):
    def test_resolves_existing_directory_without_inferring_an_ancestor_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / ".autopilot" / "controller").mkdir(parents=True)
            for name in ("project", "project-extra"):
                root = base / name
                root.mkdir()
                self.assertEqual(resolve_project_root(root), root.resolve())
                self.assertEqual(resolve_project_root(root / "."), root.resolve())
            alias = base / "alias"
            alias.symlink_to(base / "project", target_is_directory=True)
            self.assertEqual(resolve_project_root(alias), (base / "project").resolve())
            self.assertEqual(list((base / ".autopilot" / "controller").iterdir()), [])
    def test_refuses_missing_and_nondirectory_roots_without_creating_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            existing = base / "project"
            existing.mkdir()
            file = base / "project-file"
            file.write_bytes(b"unrelated file")
            for root in (base / "project-extra", base / "missing", file):
                with self.subTest(root=root):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
            self.assertEqual(resolve_project_root(existing), existing.resolve())
            self.assertEqual(list(existing.iterdir()), [])
            self.assertEqual(file.read_bytes(), b"unrelated file")

    def test_refuses_symlinked_private_components_and_aliased_fixed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for relative in (".autopilot", ".autopilot/controller",
                             ".autopilot/controller/actors"):
                root = base / relative.replace("/", "-").replace(".", "")
                root.mkdir()
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                outside = base / (root.name + "-outside")
                outside.mkdir()
                for parent in link.parents:
                    if parent == root:
                        break
                    parent.chmod(0o700)
                self.assertEqual(resolve_project_root(root), root.resolve())
                link.symlink_to(outside, target_is_directory=True)
                with self.subTest(relative=relative):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
                    self.assertEqual(list(outside.iterdir()), [])
            for name in ("state.json", "state.json.bak", "state.json.lock"):
                root = base / name
                private = root / ".autopilot" / "controller"
                private.mkdir(parents=True, mode=0o700)
                outside = base / (name + "-outside")
                outside.write_bytes(b"outside evidence")
                (root / ".autopilot").chmod(0o700)
                artifact = private / name
                artifact.write_bytes(canonical(frozen_state()) if name != "state.json.lock" else b"")
                artifact.chmod(0o600)
                self.assertEqual(resolve_project_root(root), root.resolve())
                artifact.unlink()
                os.link(outside, artifact)
                with self.subTest(name=name):
                    with self.assertRaises(StateIOError):
                        resolve_project_root(root)
                    self.assertEqual(outside.read_bytes(), b"outside evidence")


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.directory = self.base / "controller"
        self.directory.mkdir()
        self.path = self.directory / "state.json"
        self.backup = self.directory / "state.json.bak"
        self.store = StateStore(self.path)
        self.initial = frozen_state()

    def pair(self) -> tuple[bytes, bytes]:
        return self.path.read_bytes(), self.backup.read_bytes()

    def seed_pair(self) -> dict:
        self.store.initialize(self.initial)
        return self.store.transaction(lambda value: None, expected_revision=0)

    def test_initialization_is_create_only_and_returned_states_are_isolated(self) -> None:
        result = self.store.initialize(self.initial)
        self.assertEqual(result, self.initial)
        self.initial["workflow"]["tasks"].append("caller mutation")
        result["actors"].clear()
        expected = frozen_state()
        self.assertEqual(self.store.read(), expected)
        read = self.store.read()
        read["receipts"].clear()
        self.assertEqual(self.store.read(), expected)
        before = self.path.read_bytes()
        owned_initial = frozen_state(owned=True)
        owned_initial["revision"] = 0
        with self.assertRaises(StateExistsError):
            self.store.initialize(owned_initial)
        self.assertEqual(self.path.read_bytes(), before)
        other = self.directory / "state-extra.json"
        StateStore(other).initialize(owned_initial)
        self.assertEqual(StateStore(other).read(), dict(frozen_state(owned=True), revision=0))
        self.assertEqual(self.store.read(), expected)

    def test_initialization_refuses_nonzero_revision_without_creating_state_or_backup(self) -> None:
        with self.assertRaises(StateError):
            self.store.initialize(frozen_state(owned=True))
        self.assertFalse(self.path.exists())
        self.assertFalse(self.backup.exists())

    def test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup(self) -> None:
        self.store.initialize(self.initial)
        seen = []

        def acquire(candidate: dict) -> None:
            seen.append(candidate)
            candidate.update(frozen_state(owned=True))
            candidate["revision"] = 100

        first = self.store.transaction(acquire, expected_revision=0)
        self.assertEqual(first, frozen_state(owned=True))
        self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)
        seen[0]["actors"].clear()
        first["receipts"].clear()
        self.assertEqual(self.store.read(), frozen_state(owned=True))
        replacement = frozen_state(owned=True)
        replacement["revision"] = 99
        second = self.store.transaction(lambda value: replacement, expected_revision=1)
        expected = frozen_state(owned=True)
        expected["revision"] = 2
        self.assertEqual(second, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), frozen_state(owned=True))
        replacement["actors"].clear()
        second["receipts"].clear()
        self.assertEqual(self.store.read(), expected)

    def test_validation_conflict_mutator_and_publication_failures_preserve_exact_pair(self) -> None:
        current = self.seed_pair()
        before = self.pair()
        called = []
        with self.assertRaises(RevisionConflictError):
            self.store.transaction(lambda value: called.append(True), expected_revision=0)
        self.assertEqual(called, [])
        self.assertEqual(self.pair(), before)
        with self.assertRaises(schema.SchemaError):
            self.store.transaction(lambda value: value["workflow"]["jobs"].append("job"))
        self.assertEqual(self.pair(), before)

        def refuse(candidate: dict) -> None:
            candidate["actors"].clear()
            raise RuntimeError("mutator-refusal")

        with self.assertRaisesRegex(RuntimeError, "mutator-refusal"):
            self.store.transaction(refuse)
        self.assertEqual(self.pair(), before)

        def guard() -> None:
            called.append("publication")
            raise RuntimeError("publication-refusal")

        with self.assertRaisesRegex(RuntimeError, "publication-refusal"):
            self.store.transaction(lambda value: None, publication_guard=guard)
        self.assertEqual(called, ["publication"])
        self.assertEqual(self.pair(), before)
        self.assertEqual(self.store.read(), current)

    def test_all_six_boundaries_surface_errors_and_interrupts_and_repair_the_pair(self) -> None:
        expected = {
            "BACKUP_TEMP_FSYNCED": "backup_temp_fsynced",
            "BACKUP_REPLACED": "backup_replaced",
            "BACKUP_DIR_FSYNCED": "backup_dir_fsynced",
            "STATE_TEMP_FSYNCED": "state_temp_fsynced",
            "STATE_REPLACED": "state_replaced",
            "STATE_DIR_FSYNCED": "state_dir_fsynced",
        }
        self.assertEqual({item.name: item.value for item in DurabilityBoundary}, expected)
        self.seed_pair()
        before = self.pair()
        for boundary in DurabilityBoundary:
            for exception in (RuntimeError, KeyboardInterrupt):
                calls = []

                def fail_at(item: DurabilityBoundary) -> None:
                    calls.append(item)
                    if item == boundary:
                        raise exception(boundary.value)

                with self.subTest(boundary=boundary, exception=exception):
                    store = StateStore(self.path, boundary_hook=fail_at)
                    with self.assertRaisesRegex(exception, boundary.value):
                        store.transaction(lambda value: None, expected_revision=1)
                    self.assertIn(boundary, calls)
                    self.assertEqual(self.pair(), before)
                    self.assertEqual(self.store.read()["revision"], 1)

    def test_successful_publication_reports_all_six_boundaries_and_commits_only_its_path(self) -> None:
        self.seed_pair()
        calls = []
        other = self.directory / "state.json-extra"
        other.write_bytes(b"near-match evidence")
        store = StateStore(self.path, boundary_hook=calls.append)
        result = store.transaction(lambda value: None, expected_revision=1)
        self.assertEqual(calls, list(DurabilityBoundary))
        self.assertEqual(result, dict(self.initial, revision=2))
        self.assertEqual(self.store.read(), result)
        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=1))
        self.assertEqual(other.read_bytes(), b"near-match evidence")

    def test_corrupt_current_is_never_replaced_by_backup_or_restore(self) -> None:
        self.seed_pair()
        backup = self.backup.read_bytes()
        corruptions = ((b"{", StateIOError), (b"\xff", StateIOError),
                       (b"{}", schema.SchemaError),
                       (canonical(dict(self.initial, schema_version=2)), FutureSchemaError))
        for content, error in corruptions:
            self.path.write_bytes(content)
            for operation in (self.store.read, self.store.restore,
                              lambda: self.store.transaction(lambda value: None)):
                with self.subTest(content=content, operation=operation):
                    with self.assertRaises(error):
                        operation()
                    self.assertEqual(self.pair(), (content, backup))

    def test_bounded_reads_refuse_oversized_state_without_touching_backup(self) -> None:
        self.seed_pair()
        self.path.write_bytes(b" " * (schema.MAX_STATE_BYTES + 1))
        before = self.pair()
        with self.assertRaises(StateResourceLimitError):
            self.store.read()
        with self.assertRaises(StateResourceLimitError):
            self.store.transaction(lambda value: None)
        self.assertEqual(self.pair(), before)

    def test_restore_refuses_acquired_or_security_changed_backup_and_preserves_credentials(self) -> None:
        self.seed_pair()
        self.store.transaction(lambda value: frozen_state(owned=True), expected_revision=1)
        credential = self.directory / "actors" / "owner.json"
        credential.parent.mkdir()
        credential.write_bytes(b"private-owner-credential\n")
        before = self.pair()
        with self.assertRaises(BackupError):
            self.store.restore(precondition=lambda value: None)
        self.assertEqual(self.pair(), before)
        self.assertEqual(credential.read_bytes(), b"private-owner-credential\n")
        original = self.store.read()
        def newer_epoch(value: dict) -> None:
            value["lease_epoch"] = 3
            value["owner"]["lease_epoch"] = 3
            for descriptor in value["actors"].values():
                descriptor["lease_epoch"] = 3

        changes = (
            newer_epoch,
            lambda value: value["owner"].update(mode="manual"),
            lambda value: value["actors"]["operator-synthetic"].update(secret_digest="f" * 64),
            lambda value: value["receipts"].clear(),
        )
        for change in changes:
            backup = copy.deepcopy(original)
            change(backup)
            self.assertEqual(schema.validate_state(backup), backup)
            self.backup.write_bytes(canonical(backup))
            before = self.pair()
            with self.subTest(change=change):
                with self.assertRaises(BackupError):
                    self.store.restore(precondition=lambda value: None)
                self.assertEqual(self.pair(), before)
                self.assertEqual(credential.read_bytes(), b"private-owner-credential\n")

    def test_security_identical_restore_advances_current_revision_and_preserves_security(self) -> None:
        current = self.seed_pair()
        checked = []

        def precondition(value: dict) -> None:
            checked.append(copy.deepcopy(value))

        restored = self.store.restore(expected_revision=1, precondition=precondition)
        expected = copy.deepcopy(current)
        expected["revision"] = 2
        self.assertEqual(restored, expected)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(checked, [current])
        self.assertEqual(json.loads(self.backup.read_bytes()), current)
        restored["actors"].clear()
        self.assertEqual(self.store.read(), expected)
        again = self.store.restore(expected_revision=2)
        expected["revision"] = 3
        self.assertEqual(again, expected)
        self.assertEqual(json.loads(self.backup.read_bytes())["revision"], 2)

    def test_restore_checks_intent_conflict_precondition_and_invalid_backup_before_publication(self) -> None:
        self.seed_pair()
        before = self.pair()
        with self.assertRaises(RevisionConflictError):
            self.store.restore(expected_revision=0)
        self.assertEqual(self.pair(), before)

        current = self.store.read()

        def refuse(value: dict) -> None:
            self.assertEqual(value, current)
            raise RuntimeError("precondition-refusal")

        with self.assertRaisesRegex(RuntimeError, "precondition-refusal"):
            self.store.restore(precondition=refuse)
        self.assertEqual(self.pair(), before)
        intent = self.directory / "credential-intent.json"
        intent.write_bytes(b"private-intent-evidence")
        with self.assertRaises(BackupError):
            self.store.restore(precondition=lambda value: None)
        self.assertEqual(intent.read_bytes(), b"private-intent-evidence")
        self.assertEqual(self.pair(), before)
        intent.unlink()
        for content in (b"{", b"{}", canonical(dict(self.initial, schema_version=2))):
            self.backup.write_bytes(content)
            before = self.pair()
            with self.subTest(content=content):
                with self.assertRaises(BackupError):
                    self.store.restore()
                self.assertEqual(self.pair(), before)

    def test_restore_boundary_failures_preserve_security_identical_pair(self) -> None:
        self.seed_pair()
        before = self.pair()
        for boundary in DurabilityBoundary:
            calls = []

            def fail_at(item: DurabilityBoundary) -> None:
                calls.append(item)
                if item == boundary:
                    raise RuntimeError(boundary.value)

            with self.subTest(boundary=boundary):
                store = StateStore(self.path, boundary_hook=fail_at)
                with self.assertRaisesRegex(RuntimeError, boundary.value):
                    store.restore(expected_revision=1)
                self.assertIn(boundary, calls)
                self.assertEqual(self.pair(), before)

    def test_unsupported_directory_fsync_is_explicit_and_preserves_pair(self) -> None:
        self.seed_pair()
        before = self.pair()
        real_fsync = os.fsync
        directories = []

        def unsupported(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directories.append(fd)
                raise OSError(errno.EINVAL, "directory fsync unsupported")
            real_fsync(fd)

        with mock.patch("os.fsync", side_effect=unsupported):
            with self.assertRaises(DurabilityUnsupportedError):
                self.store.transaction(lambda value: None)
        self.assertTrue(directories)
        self.assertEqual(self.pair(), before)

    def test_store_refuses_aliased_state_backup_and_lock_artifacts(self) -> None:
        self.seed_pair()
        for suffix in ("", ".bak", ".lock"):
            artifact = Path(str(self.path) + suffix)
            original = artifact.read_bytes()
            mode = artifact.stat().st_mode & 0o777
            for kind in ("symlink", "hardlink"):
                outside = self.base / f"outside-{kind}"
                outside.write_bytes(original)
                artifact.unlink()
                if kind == "symlink":
                    artifact.symlink_to(outside)
                else:
                    os.link(outside, artifact)
                with self.subTest(suffix=suffix, kind=kind):
                    with self.assertRaises(StateError):
                        StateStore(self.path).transaction(lambda value: None)
                    self.assertEqual(outside.read_bytes(), original)
                artifact.unlink()
                artifact.write_bytes(original)
                artifact.chmod(mode)
                outside.unlink()
            artifact.unlink()
            artifact.mkdir()
            with self.subTest(suffix=suffix, kind="directory"):
                with self.assertRaises(StateError):
                    StateStore(self.path).transaction(lambda value: None)
            artifact.rmdir()
            artifact.write_bytes(original)
            artifact.chmod(mode)

    def test_directory_identity_substitution_cannot_redirect_publication(self) -> None:
        self.seed_pair()
        before = self.pair()
        displaced = self.base / "original-controller"
        substituted = []

        def swap(boundary: DurabilityBoundary) -> None:
            if boundary == DurabilityBoundary.BACKUP_TEMP_FSYNCED and not substituted:
                self.directory.rename(displaced)
                self.directory.mkdir()
                self.path.write_bytes(b"replacement-state-evidence")
                self.backup.write_bytes(b"replacement-backup-evidence")
                substituted.append(True)

        store = StateStore(self.path, boundary_hook=swap)
        with self.assertRaises(StateError):
            store.transaction(lambda value: None)
        self.assertEqual(substituted, [True])
        self.assertEqual(self.pair(), (b"replacement-state-evidence", b"replacement-backup-evidence"))
        self.assertEqual(((displaced / "state.json").read_bytes(),
                          (displaced / "state.json.bak").read_bytes()), before)

    def run_writers(self, *, writers: int, iterations: int, expected: int | None) -> list[dict]:
        script = """
import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from autopilot_state.store import StateStore, RevisionConflictError
path, gate, ready = map(Path, sys.argv[2:5])
iterations = int(sys.argv[5])
expected = None if sys.argv[6] == 'none' else int(sys.argv[6])
ready.write_text('ready')
deadline = time.monotonic() + 15
while not gate.exists():
    if time.monotonic() > deadline:
        raise RuntimeError('start gate timeout')
    time.sleep(0.005)
try:
    for _ in range(iterations):
        state = StateStore(path).transaction(lambda value: None, expected_revision=expected)
    print(json.dumps({'outcome': 'committed', 'revision': state['revision']}))
except RevisionConflictError:
    print(json.dumps({'outcome': 'conflict'}))
"""
        gate = self.base / "start-gate"
        processes = []
        for index in range(writers):
            ready = self.base / f"ready-{index}"
            command = [sys.executable, "-c", script, str(CONTROLLER), str(self.path),
                       str(gate), str(ready), str(iterations), str(expected) if expected is not None else "none"]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       cwd=self.base, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            processes.append(process)
            self.addCleanup(lambda process=process: process.kill() if process.poll() is None else None)
        deadline = time.monotonic() + 20
        while not all((self.base / f"ready-{index}").exists() for index in range(writers)):
            self.assertLess(time.monotonic(), deadline, "writers must reach the shared start gate")
            time.sleep(0.01)
        gate.write_text("start")
        results = []
        for process in processes:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
            self.assertEqual(error, b"")
            results.append(json.loads(output))
        return results

    def test_real_process_cas_allows_exactly_one_writer_for_the_same_revision(self) -> None:
        self.store.initialize(self.initial)
        results = self.run_writers(writers=3, iterations=1, expected=0)
        self.assertEqual([item["outcome"] for item in results].count("committed"), 1)
        self.assertEqual([item["outcome"] for item in results].count("conflict"), 2)
        self.assertIn({"outcome": "committed", "revision": 1}, results)
        expected = dict(self.initial, revision=1)
        self.assertEqual(self.store.read(), expected)
        self.assertEqual(json.loads(self.backup.read_bytes()), self.initial)

    def test_real_process_writers_serialize_all_revision_increments_without_lost_updates(self) -> None:
        self.store.initialize(self.initial)
        results = self.run_writers(writers=3, iterations=4, expected=None)
        self.assertEqual([item["outcome"] for item in results], ["committed"] * 3)
        self.assertEqual(max(item["revision"] for item in results), 12)
        self.assertEqual(self.store.read(), dict(self.initial, revision=12))
        self.assertEqual(json.loads(self.backup.read_bytes()), dict(self.initial, revision=11))


if __name__ == "__main__":
    unittest.main()
