"""Executable controller configuration checks; no runtime imports or host claims."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

CONTRACTS = Path(__file__).resolve().parents[2] / "plugins/autopilot/contracts/controller"
FORMATS = FormatChecker()


def bounded_utf8(limit: int):
    def check(value: object) -> bool:
        if not isinstance(value, str):
            return True
        try:
            return len(value.encode("utf-8")) <= limit
        except UnicodeEncodeError:
            return False

    return check


for _limit in (256, 4096, 1048576):
    FORMATS.checks(f"utf8-{_limit}")(bounded_utf8(_limit))


class ControllerProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((CONTRACTS / "workflow-v1.json").read_text())
        cls.fixtures = json.loads((CONTRACTS / "fixtures-v1.json").read_text())
        cls.provenance = json.loads((CONTRACTS / "provenance.json").read_text())
        cls.cases = {case["name"]: case for case in cls.fixtures["cases"]}
        cls.scenarios = {case["name"]: case for case in cls.fixtures["scenarios"]}
        cls.contract = cls.schema["x-controller"]

    def validator(self, definition: str) -> Draft202012Validator:
        return Draft202012Validator(
            {"$ref": f"#/$defs/{definition}", "$defs": self.schema["$defs"]},
            format_checker=FORMATS,
        )

    def assert_valid(self, definition: str, value: object) -> None:
        self.assertEqual(list(self.validator(definition).iter_errors(value)), [])

    def assert_invalid(self, definition: str, value: object) -> None:
        self.assertTrue(list(self.validator(definition).iter_errors(value)))

    def test_schema_is_valid_and_local_references_resolve(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        pending = [self.schema]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/$defs/"))
                    self.assertIn(value["$ref"].removeprefix("#/$defs/"), self.schema["$defs"])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)

    def test_contract_examples(self) -> None:
        self.assertEqual(len(self.cases), len(self.fixtures["cases"]))
        for case in self.fixtures["cases"]:
            with self.subTest(case=case["name"]):
                check = self.assert_valid if case["valid"] else self.assert_invalid
                check(case["definition"], case["input"])
                if case["valid"]:
                    self.assertIsNone(case["expected_error"])
                else:
                    self.assertIn(case["expected_error"], self.contract["error_codes"])
        for operation in self.contract["implemented_operations"]:
            examples = [
                case for case in self.fixtures["cases"]
                if case["definition"] == "request" and case["input"]["operation"] == operation
            ]
            self.assertTrue(any(case["valid"] for case in examples), operation)
            self.assertTrue(any(not case["valid"] for case in examples), operation)

    def test_kernel_field_ownership(self) -> None:
        state = self.cases["kernel-owned"]["input"]
        operator = "operator-synthetic"
        paths = [
            (), ("workflow",), ("workflow", "review"), ("owner",),
            ("actors", operator), ("actors", "owner-synthetic"),
            ("receipts", "open-synthetic"),
            ("receipts", "open-synthetic", "authorizing_actor"),
            ("receipts", "open-synthetic", "response"),
            ("receipts", "open-synthetic", "response", "result"),
        ]
        for path in paths:
            node = state
            for key in path:
                node = node[key]
            for field in [*node, "unowned"]:
                changed = copy.deepcopy(state)
                target = changed
                for key in path:
                    target = target[key]
                if field == "unowned":
                    target[field] = "forbidden"
                else:
                    del target[field]
                with self.subTest(path=path, field=field):
                    self.assert_invalid("state", changed)

    def test_protocol_objects_are_closed_and_require_declared_fields(self) -> None:
        for name in ("open-fresh", "acquire", "release", "recover", "open-existing",
                     "open-result", "acquire-result", "release-result", "recover-result"):
            case = self.cases[name]
            nested = "payload" if case["definition"] == "request" else "result"
            for path in ((), (nested,)):
                original = case["input"] if not path else case["input"][nested]
                for field in [*original, "unowned"]:
                    value = copy.deepcopy(case["input"])
                    node = value if not path else value[nested]
                    if field == "unowned":
                        node[field] = "forbidden"
                    else:
                        del node[field]
                    with self.subTest(case=name, path=path, field=field):
                        if path and nested == "result":
                            definition = {
                                "open-result": "open_result",
                                "acquire-result": "acquire_result",
                                "release-result": "rotation_result",
                                "recover-result": "rotation_result",
                            }[name]
                            self.assert_invalid(definition, node)
                        else:
                            self.assert_invalid(case["definition"], value)

    def test_kernel_defaults_and_deferred_families(self) -> None:
        defaults = {
            "batch": None, "work": None, "tasks": [], "review": {"cap": 2},
            "recovery": None, "jobs": [],
        }
        self.assertEqual(self.schema["$defs"]["workflow"]["default"], defaults)
        self.assertEqual(self.cases["kernel-initial"]["input"]["workflow"], defaults)
        for field, value in (
            ("batch", {}), ("work", {}), ("tasks", [{}]), ("review", {"cap": 3}),
            ("recovery", {}), ("jobs", [{}]), ("pid", 123), ("process_id", "p"),
            ("launcher", "shell"), ("heartbeat", 1), ("resource_usage", {}),
            ("tui", {}), ("extensions", {}),
        ):
            state = copy.deepcopy(self.cases["kernel-initial"]["input"])
            state["workflow"][field] = value
            with self.subTest(field=field):
                self.assert_invalid("state", state)
        self.assertEqual(self.contract["capabilities"], ["workflow.core.v1"])
        self.assertEqual(
            self.contract["implemented_operations"],
            ["workflow.open", "owner.acquire", "owner.release", "owner.recover"],
        )
        self.assertEqual(
            set(self.contract["reserved_operations"]),
            {
                "policy.bind", "prd.enter", "task.replace", "task.start", "task.finish",
                "task.attempt", "lane.route", "job.plan", "job.claim", "job.record_exit",
                "review.record_stage", "review.close", "custody.record", "custody.discharge",
                "verification.record", "phase.handoff", "prd.stall", "prd.park", "prd.defer",
                "prd.complete", "artifact.record", "records.commit",
            },
        )
        for operation, capability in self.contract["reserved_operations"].items():
            self.assertIn(capability, self.contract["unavailable_capabilities"])
            self.assertNotIn(capability, self.contract["capabilities"])
            request = copy.deepcopy(self.cases["acquire"]["input"])
            request.update(operation=operation, payload={})
            self.assert_valid("request", request)
        self.assertEqual(self.scenarios["reserved-operation"]["expected_error"], "missing_capability")

    def test_utf8_byte_limits(self) -> None:
        for definition, limit in (("identity", 256), ("absolute_path", 1048576)):
            prefix = "/" if definition == "absolute_path" else ""
            at_limit = prefix + "é" * ((limit - len(prefix)) // 2)
            at_limit += "x" * (limit - len(at_limit.encode("utf-8")))
            self.assert_valid(definition, at_limit)
            self.assert_invalid(definition, at_limit + "x")
            self.assert_invalid(definition, prefix + "\ud800")
        recovery = copy.deepcopy(self.cases["recover"]["input"])
        recovery["payload"]["reason"] = "é" * 2048
        self.assert_valid("request", recovery)
        recovery["payload"]["reason"] += "x"
        self.assert_invalid("request", recovery)

    def test_integer_versions_and_response_errors(self) -> None:
        for definition in ("nonnegative_integer",):
            for value in (True, False, -1, 1.5, "1", None, 10**640):
                self.assert_invalid(definition, value)
            for value in (0, 1, 10**639):
                self.assert_valid(definition, value)
        for field in ("schema_version", "revision", "lease_epoch"):
            state = copy.deepcopy(self.cases["kernel-initial"]["input"])
            state[field] = True
            self.assert_invalid("state", state)
        self.assertEqual(
            self.contract["error_codes"],
            ["invalid_request", "incompatible_contract", "revision_conflict", "wrong_binding",
             "missing_capability", "rejected_evidence", "recovery_required"],
        )
        for code in self.contract["error_codes"]:
            response = {
                "ok": False, "revision": 0, "result": None,
                "error_code": code, "retryable": code == "revision_conflict",
            }
            self.assert_valid("response", response)
            response["retryable"] = not response["retryable"]
            self.assert_invalid("response", response)
        rejected = self.cases["error-invalid_request"]["input"]
        self.assert_invalid("core_response", rejected)

    def test_actor_and_receipt_bounds(self) -> None:
        state = copy.deepcopy(self.cases["kernel-owned"]["input"])
        state["actors"]["third"] = copy.deepcopy(state["actors"]["operator-synthetic"])
        self.assert_invalid("state", state)
        state = copy.deepcopy(self.cases["kernel-initial"]["input"])
        receipt = state["receipts"]["open-synthetic"]
        state["receipts"] = {f"request-{number}": receipt for number in range(4096)}
        self.assert_valid("state", state)
        state["receipts"]["one-too-many"] = receipt
        self.assert_invalid("state", state)
        for field, invalid in (("role", "job"), ("secret_digest", "A" * 64),
                               ("secret_digest", "a" * 63), ("actor_id", "")):
            actor = copy.deepcopy(self.cases["kernel-initial"]["input"]["actors"]["operator-synthetic"])
            actor[field] = invalid
            self.assert_invalid("actor", actor)
        owner = copy.deepcopy(self.cases["kernel-owned"]["input"]["actors"]["owner-synthetic"])
        owner["native_session_id"] = None
        self.assert_invalid("actor", owner)

    def test_frozen_resource_limits(self) -> None:
        self.assertEqual(self.contract["limits"], {
            "state_bytes": 16777216, "request_bytes": 2097152,
            "normal_candidate_bytes": 14680064, "emergency_reserved_bytes": 2097152,
            "core_response_bytes": 65536, "intent_bytes": 33554432,
            "string_bytes": 1048576, "identity_bytes": 256, "reason_bytes": 4096,
            "json_depth": 32, "json_integer_digits": 640,
            "normal_receipts": 4094, "hard_receipts": 4096, "current_actors": 2,
        })
        self.assertEqual(self.contract["python_minimum"], "3.12")
        self.assertEqual(self.contract["runtime_dependencies"], "stdlib only")
        for name in ("normal-count-capacity", "normal-byte-capacity", "emergency-capacity",
                     "no-owner-reserve", "sealed-capacity", "corrupt-active-owner-hard-cap",
                     "oversized-response", "archive-roundtrip"):
            self.assertIn(name, self.scenarios)
        self.assertEqual(
            self.contract["limits"]["normal_candidate_bytes"]
            + self.contract["limits"]["emergency_reserved_bytes"],
            self.contract["limits"]["state_bytes"],
        )

    def test_frozen_durability_and_credential_scenarios(self) -> None:
        boundaries = {
            "backup_temp_fsynced", "backup_replaced", "backup_dir_fsynced",
            "state_temp_fsynced", "state_replaced", "state_dir_fsynced",
        }
        self.assertEqual(set(self.fixtures["durability_boundaries"]), boundaries)
        self.assertEqual(len(self.scenarios), len(self.fixtures["scenarios"]))
        for boundary in boundaries:
            self.assertIn(f"store-boundary-{boundary}", self.scenarios)
        for operation in ("owner.acquire", "owner.release", "owner.recover", "bootstrap"):
            for boundary in ("stage_fsynced", "intent_dir_fsynced",
                             "operator_credential_published", "state_published",
                             "cleanup_dir_fsynced"):
                self.assertIn(f"{operation}-crash-{boundary}", self.scenarios)
        self.assertIn("owner.acquire-crash-owner_credential_published", self.scenarios)
        for name in ("restore-after-acquire", "restore-security-identical",
                     "restore-pending-intent", "corrupt-current", "unsupported-directory-fsync",
                     "receipt-current-after-rotation", "receipt-historical-only",
                     "receipt-changed-envelope", "historical-new-request",
                     "unrelated-intent-request", "wrong-binding-intent",
                     "private-gitignore", "aliased-or-incompatible-ignore", "path-race"):
            self.assertIn(name, self.scenarios)
        for case in self.scenarios.values():
            self.assertTrue(case["setup"])
            self.assertTrue(case["action"])
            self.assertTrue(case["expected"])
            self.assertIn(case["expected_error"], [None, *self.contract["error_codes"]])

    def test_provenance_pin_hashes_and_symbol_maps(self) -> None:
        source = self.provenance["source"]
        self.assertEqual(source["repository"], "https://github.com/buvis/ovcaq")
        self.assertEqual(source["commit"], "cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7")
        self.assertEqual(source["license"]["spdx"], "MIT")
        self.assertEqual(source["license"]["copyright"], "Copyright (c) 2026 Bob Buvis")
        files = {entry["path"]: entry["sha256"] for entry in source["files"]}
        self.assertEqual(len(files), len(source["files"]))
        for digest in files.values():
            self.assertRegex(digest, r"^[a-f0-9]{64}$")
        self.assertEqual(
            files["src/ovcaq/state/store.py"],
            "b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7",
        )
        self.assertEqual(
            files["src/ovcaq/state/schema.py"],
            "1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b",
        )
        for row in self.provenance["symbol_map"]:
            self.assertIn(row["source"], files)
            self.assertTrue(row["symbols"])
            self.assertTrue(row["disposition"])
        for row in self.provenance["test_map"]:
            self.assertIn(row["source"].split("::")[0], files)
            if row["target"] is not None:
                self.assertTrue(hasattr(self, row["target"].split("::")[1]))
        restore = next(row for row in self.provenance["deliberate_divergences"]
                       if row["topic"] == "restore")
        for invariant in ("exclusive lock", "lease_epoch/owner/actors/receipts",
                          "credential-intent.json", "BackupError"):
            self.assertIn(invariant, restore["target"])

    def test_source_field_ownership_is_complete_and_explicit(self) -> None:
        expected = {
            "CatchupCache": "completed_at,head_sha",
            "CompletedPrd": "filename,cycles,autonomous_decisions,escalated_decisions,tasks_completed,tasks_total",
            "CapabilityAttempt": "id,status,started_at,finished_at,session_id,detail",
            "CapabilityEntry": "required,launcher,plugin,version,failure,status,attempts",
            "BatchState": "id,status,started_at,completed_at,completed_prds,parks_consecutive,catchup,capabilities",
            "TaskEstimates": "input_tokens,context_peak",
            "EscalationEntry": "reason,from_tier,diagnosis,repair_used",
            "AttemptEntry": "number,tier,driver,outcome,review_cycle,cause,pipeline,cleanup_outcome,started_at,finished_at,commit_sha,escalation,metadata",
            "TaskEntry": "id,name,description,active_form,status,blocked_by,tier,files_touched,public_contract_edit,estimates,attempts,metadata",
            "WorkState": "prd,phase,next_phase,completed_phases,work_start_sha,repo_root,design_doc,contract_card,tasks_total,tasks_completed,extensions",
            "DecisionGate": "decision,detail,decided_at",
            "TestRun": "command,exit_code,summary",
            "ReviewCycle": "cycle,review_file,reviewers,issues_found,follow_up_tasks,deferred,recurring_issues,decision_gate,rework_commits,rework_notes,fix_audit,test_run",
            "DecisionEntry": "id,kind,summary,rationale,cycle,created_at,status",
            "DoubtEntry": "id,description,category,justification,status,source",
            "RubricVerdict": "rule_id,verdict,source",
            "ReviewState": "cycle,cap,cycles,decisions,doubts,rubric_verdicts,rework_task_ids,lenses,extensions",
            "Notice": "site,detail,created_at",
            "ControlState": "pause_requested,pause_reason,attention",
            "ArtifactIdentity": "device,inode",
            "RecoveryOperation": "id,kind,step,prd,site,detail,source,destination,artifact,created_at",
            "RecoveryState": "operation,replan_count,phase_fingerprint,phase_repeats",
            "State": "schema_version,revision,batch,work,tasks,review,control,recovery",
        }
        rows = self.provenance["field_ownership"]
        self.assertEqual(
            {row["source"] for row in rows},
            {f"{owner}.{field}" for owner, fields in expected.items() for field in fields.split(",")},
        )
        self.assertEqual(len(rows), len({row["source"] for row in rows}))
        for row in rows:
            self.assertTrue(row["owner"])
            self.assertIn(row["disposition"], {"preserved", "deferred", "excluded", "redesigned"})
        self.assertIn("not a full legacy schema equivalence", self.provenance["scope"].lower())

    def test_bundle_shape_and_implemented_only_advertisement(self) -> None:
        bundle = {
            "protocol_major": 1, "package_version": "0.1.0",
            "schema_digest": "a" * 64, "fixture_digest": "b" * 64,
            "operations": list(self.contract["implemented_operations"]),
            "capabilities": ["workflow.core.v1"],
        }
        self.assert_valid("bundle", bundle)
        for key in bundle:
            changed = copy.deepcopy(bundle)
            del changed[key]
            self.assert_invalid("bundle", changed)
        for field, value in (
            ("protocol_major", True), ("schema_digest", "A" * 64),
            ("operations", ["workflow.open"] * 4),
            ("operations", [*bundle["operations"], "job.plan"]),
            ("capabilities", ["workflow.core.v1", "workflow.jobs.v1"]),
            ("live_state", {}),
        ):
            self.assert_invalid("bundle", dict(bundle, **{field: value}))


if __name__ == "__main__":
    unittest.main()
