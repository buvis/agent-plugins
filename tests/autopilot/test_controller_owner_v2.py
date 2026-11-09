"""Receipt authority survives rotation without granting retired credentials a lease."""

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path

from controller_cli_support import canonical, private_path, tree
from controller_owner_support import OwnerCLITest, credential


class OwnerV2Test(OwnerCLITest):
    def test_wrong_binding_reports_selected_root_revision_and_preserves_both_projects(self) -> None:
        _, _, operator = self.bootstrap()
        _, _, owner, _ = self.acquire(operator)
        request = self.request(owner, "owner.release", "cross-project-release")
        original_root = self.root
        original_before = tree(private_path(original_root))
        selected_root = self.base / "project-extra"
        selected_root.mkdir()
        self.response(self.apply(request, owner, root=selected_root),
                      "wrong_binding", revision=0)
        self.assertFalse(private_path(selected_root).exists())
        self.assertTrue(tree(private_path(original_root)) == original_before,
                        "empty selected-root rejection changed original project evidence")
        self.root = selected_root
        _, _, selected_operator = self.bootstrap()
        _, _, selected_owner, _ = self.acquire(selected_operator)
        self.clear(selected_owner)
        selected_revision = self.state()["revision"]
        self.assertEqual(selected_revision, 2)
        selected_before = tree(private_path(selected_root))
        self.root = original_root
        self.assertEqual(self.state()["revision"], 1)
        self.response(self.apply(request, owner, root=selected_root),
                      "wrong_binding", revision=selected_revision)
        self.assertTrue(tree(private_path(selected_root)) == selected_before,
                        "rejection changed selected project evidence")
        self.assertTrue(tree(private_path(original_root)) == original_before,
                        "rejection changed original project evidence")

    def history(self, tag: str) -> tuple[list[tuple], dict[int, Path], Path]:
        fresh, opened, operator = self.bootstrap()
        operators = {0: self.retain(operator, f"{tag}-operator-zero.json")}
        first, first_response, owner, operator = self.acquire(
            operator, "manual", f"séance-{tag}", f"{tag}-acquire")
        operators[1] = self.retain(operator, f"{tag}-operator-one.json")
        released, released_response, operator = self.clear(
            owner, request_id=f"{tag}-release")
        operators[2] = self.retain(operator, f"{tag}-operator-two.json")
        second, second_response, second_owner, operator = self.acquire(
            operator, "supervised", f"séance-{tag}-extra", f"{tag}-acquire-extra")
        operators[3] = self.retain(operator, f"{tag}-operator-three.json")
        recovered = self.request(operator, "owner.recover", f"{tag}-recover", {
            "reason": f"Explicit reconciliation {tag}", "reconciled_job_ids": []})
        recovered_response = self.response(self.apply(recovered, operator), revision=4)
        self.assert_transition(recovered, recovered_response, operators[3])
        records = [(fresh, opened, None), (first, first_response, operators[0]),
                   (released, released_response, owner),
                   (second, second_response, operators[2]),
                   (recovered, recovered_response, operators[3])]
        self.assertNotEqual(owner, second_owner)
        issued = [*operators.values(), operator, owner, second_owner]
        digests = {hashlib.sha256(credential(path)["secret"].encode()).digest()
                   for path in issued}
        self.assertEqual(len(digests), len(issued), "issued secrets must be distinct")
        return records, operators, operator

    def test_canonical_receipts_replay_after_rotation_with_different_json_encodings(self) -> None:
        parent = self.root
        for tag in ("alpha", "alpha-extra"):
            self.root = parent / tag
            self.root.mkdir()
            records, _, operator = self.history(tag)
            before = tree(private_path(self.root))
            for request, response, historical in records:
                reordered = dict(reversed(tuple(request.items())))
                reordered["payload"] = dict(reversed(tuple(request["payload"].items())))
                raw = json.dumps(reordered, ensure_ascii=True, indent=3).encode()
                self.assertNotEqual(raw, canonical(request))
                actors = ((None,) if historical is None else
                          (historical, operator) if request["operation"] != "owner.release"
                          else (historical,))
                for actor in actors:
                    actual = self.response(self.apply(request, actor, raw=raw))
                    self.assertEqual(actual, response)
                    self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
            recovered = records[-1][0]
            for jobs in (["job-alpha", "job-beta"], ["job-alpha-extra", "job-beta-extra"]):
                changed = recovered | {"payload": recovered["payload"] | {
                    "reconciled_job_ids": jobs}}
                self.reject_unchanged(changed, operator, "invalid_request")
            self.assert_fresh_requests_validate_revision_payload_and_operation(operator, tag)
            self.assertIsNone(self.snapshot()["owner"])

    def test_retired_intermediate_operator_cannot_borrow_another_epochs_receipt_authority(self) -> None:
        records, operators, current = self.history("authority")
        before = tree(private_path(self.root))
        for request, response, historical in (records[1], records[3], records[4]):
            epoch = request["lease_epoch"]
            self.assertEqual(self.response(self.apply(request, historical)), response)
            self.assertEqual(self.response(self.apply(request, current)), response)
            for retired_epoch, actor in operators.items():
                if retired_epoch != epoch:
                    self.reject_unchanged(request, actor, "wrong_binding")
            self.reject_unchanged(request, None, "wrong_binding")
            self.reject_unchanged(request | {"request_id": request["request_id"] + "-extra"},
                                  historical, "wrong_binding")
        self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
        self.assertEqual(self.state()["lease_epoch"], 4)
        self.assertEqual(set(self.state()["actors"]), {credential(current)["actor_id"]})
        for request, _, historical in (records[1], records[3], records[4]):
            for source in (historical, current):
                self.assert_replay_rejects_changed_credential_bindings(request, source)
        _, _, owner, operator = self.acquire(current, request_id="authority-current-owner")
        wrong_release = self.request(operator, "owner.release", "authority-operator-release")
        self.reject_unchanged(wrong_release, operator, "wrong_binding")
        wrong_acquire = self.request(owner, "owner.acquire", "authority-owner-acquire", {
            "mode": "manual", "native_session_id": "authority-wrong-role"})
        self.reject_unchanged(wrong_acquire, owner, "wrong_binding")

    def test_exact_receipt_replay_still_checks_credential_file_safety(self) -> None:
        records, _, current = self.history("private")
        for request, response, historical in (records[1], records[2], records[4]):
            for index, source in enumerate((historical, current)):
                if index and request["operation"] == "owner.release":
                    continue
                stem = f"{request['request_id']}-{index}"
                valid = self.retain(source, stem + ".json")
                self.assertEqual(self.response(self.apply(request, valid)), response)
                forged = self.retain(source, stem + "-forged.json")
                value = credential(forged)
                value["secret"] = self.changed_secret(value["secret"])
                forged.write_bytes(canonical(value))
                self.reject_unchanged(request, forged, "wrong_binding")
                invalid = self.base / (stem + ".json-extra")
                invalid.symlink_to(valid)
                self.reject_unchanged(request, invalid, "wrong_binding")
                linked = self.base / ("prefix-" + stem + ".json")
                os.link(valid, linked)
                self.reject_unchanged(request, valid, "wrong_binding")
                self.reject_unchanged(request, linked, "wrong_binding")
                linked.unlink()
                valid.chmod(0o644)
                self.reject_unchanged(request, valid, "wrong_binding")
                valid.chmod(0o600)
                self.assertEqual(self.response(self.apply(request, valid)), response)
                for raw in (b"", b"{}", b"{\"secret\":\"x\",\"secret\":\"y\"}"):
                    invalid_copy = self.retain(source, stem + "-malformed.json")
                    invalid_copy.write_bytes(raw)
                    self.reject_unchanged(request, invalid_copy, "wrong_binding")

    @staticmethod
    def changed_secret(secret: str) -> str:
        return ("A" if secret[0] != "A" else "B") + secret[1:]

    def assert_replay_rejects_changed_credential_bindings(self, request: dict,
                                                        source: Path) -> None:
        original = credential(source)
        changes = {"project_id": "0" * 64,
                   "workflow_id": original["workflow_id"] + "-extra",
                   "lease_epoch": original["lease_epoch"] + 1, "role": "owner"}
        for field, replacement in changes.items():
            with self.subTest(operation=request["operation"], credential_field=field):
                forged = self.retain(source, f"binding-{field}.json")
                forged.write_bytes(canonical(original | {field: replacement}))
                self.reject_unchanged(request, forged, "wrong_binding")

    def assert_fresh_requests_validate_revision_payload_and_operation(self, operator: Path,
                                                                    tag: str) -> None:
        stale = self.request(operator, "owner.acquire", f"{tag}-stale-acquire", {
            "mode": "manual", "native_session_id": "stale-session"})
        stale["expected_revision"] -= 1
        self.reject_unchanged(stale, operator, "revision_conflict")
        invalid = (({"reason": "", "reconciled_job_ids": []}, "invalid_request"),
                   ({"reason": "é" * 2049, "reconciled_job_ids": []}, "invalid_request"),
                   ({"reason": "Attended", "reconciled_job_ids": [1]}, "invalid_request"),
                   ({"reason": "Attended", "reconciled_job_ids": ["job", "job"]},
                    "invalid_request"),
                   ({"reason": "Attended", "reconciled_job_ids": ["job"]},
                    "rejected_evidence"))
        for index, (payload, error) in enumerate(invalid):
            with self.subTest(recovery_payload=index):
                request = self.request(operator, "owner.recover", f"{tag}-invalid-{index}",
                                       payload)
                self.reject_unchanged(request, operator, error)
        unknown = self.request(operator, "owner.unknown", f"{tag}-unknown-operation")
        self.reject_unchanged(unknown, operator, "invalid_request")

    def prepared_crash(self, name: str, tag: str) -> tuple[dict, Path]:
        _, _, operator = self.bootstrap()
        actor = operator
        if name != "owner.acquire":
            _, _, owner, operator = self.acquire(
                operator, "supervised", f"session-{tag}", f"{tag}-initial-acquire")
            actor = owner if name == "owner.release" else operator
        payload = ({"mode": "manual", "native_session_id": f"session-{tag}-extra"}
                   if name == "owner.acquire" else
                   {"reason": f"Attended reconciliation {tag}", "reconciled_job_ids": []}
                   if name == "owner.recover" else {})
        return self.request(actor, name, tag, payload), actor

    def assert_crash_completes_once(self, request: dict, historical: Path) -> None:
        before = tree(private_path(self.root))
        receipts = set(self.state()["receipts"])
        intent = private_path(self.root) / "credential-intent.json"
        if intent.exists():
            changed = request | {"request_id": request["request_id"] + "-extra"}
            self.reject_unchanged(changed, historical, "recovery_required")
            for field, value in (("project_id", "0" * 64),
                                 ("workflow_id", request["workflow_id"] + "-extra")):
                changed = request | {field: value}
                self.reject_unchanged(changed, historical, "wrong_binding")
            self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
        completed = self.response(self.apply(request, historical),
                                  revision=request["expected_revision"] + 1)
        self.assert_transition(request, completed, historical)
        self.assertFalse(intent.exists())
        after = tree(private_path(self.root))
        self.assertEqual(self.response(self.apply(request, historical)), completed)
        if request["operation"] != "owner.release":
            current = Path(completed["result"]["operator_actor_file"])
            self.assertEqual(self.response(self.apply(request, current)), completed)
        self.assertTrue(tree(private_path(self.root)) == after, "private evidence changed")
        self.assertEqual(set(self.state()["receipts"]), receipts | {request["request_id"]})
        self.snapshot()

    @staticmethod
    def response_objects(value: object) -> list[dict]:
        # Locate contract-defined responses without assuming an intent field name.
        if isinstance(value, dict):
            responses = ([value] if set(value) == {
                "ok", "revision", "result", "error_code", "retryable"} else [])
            return responses + [response for item in value.values()
                                for response in OwnerV2Test.response_objects(item)]
        if isinstance(value, list):
            return [response for item in value
                    for response in OwnerV2Test.response_objects(item)]
        return []

    def tamper_pending_evidence(self, damage: str, request: dict,
                               initial_paths: set[Path], index: int = 0) -> tuple[Path, bytes]:
        root = private_path(self.root)
        if damage == "response":
            path = root / "credential-intent.json"
            original = path.read_bytes()
            value = json.loads(original)
            responses = [response for response in self.response_objects(value)
                         if response["revision"] == request["expected_revision"] + 1]
            self.assertTrue(bool(responses), "intent must retain its complete response")
            responses[index]["revision"] += 7
        elif damage == "state":
            path = root / "state.json"
            original = path.read_bytes()
            value = json.loads(original)
            value["revision"] += 7
        else:
            stages = [path for path in (root / "actors").iterdir()
                      if path not in initial_paths and path.is_file()
                      and credential(path).get("role") == "operator"
                      and credential(path).get("lease_epoch") == request["lease_epoch"] + 1]
            self.assertEqual(len(stages), 1, "one staged operator credential is required")
            path = stages[0]
            original = path.read_bytes()
            value = credential(path)
            value["secret"] = self.changed_secret(value["secret"])
        path.write_bytes(canonical(value))
        return path, original

    def assert_tampered_crash_preserves_evidence(self, name: str, damage: str,
                                               parent: Path) -> None:
        tag = f"{name}-tampered-{damage}"
        self.root = parent / name / f"tampered-{damage}"
        self.root.mkdir(parents=True)
        request, actor = self.prepared_crash(name, tag)
        historical = self.retain(actor, tag + "-historical.json")
        initial_paths = set((private_path(self.root) / "actors").iterdir())
        self.crash(request, actor, "intent_dir_fsynced")
        intent = private_path(self.root) / "credential-intent.json"
        probes = (len([response for response in self.response_objects(json.loads(intent.read_bytes()))
                       if response["revision"] == request["expected_revision"] + 1])
                  if damage == "response" else 1)
        self.assertGreater(probes, 0, "intent must retain its complete response")
        for index in range(probes):
            with self.subTest(response_copy=index):
                path, original = self.tamper_pending_evidence(damage, request, initial_paths, index)
                self.reject_unchanged(request, historical, "recovery_required")
                self.assertTrue(intent.exists())
                path.write_bytes(original)
        self.assert_crash_completes_once(request, historical)

    def pending_cleanup_files(self, request: dict, actor: Path,
                              historical: Path) -> tuple[dict[tuple[str, int], Path],
                                                         dict[Path, bytes]]:
        actors = private_path(self.root) / "actors"
        initial_paths = set(actors.iterdir())
        before = self.state()
        self.crash(request, actor, "intent_dir_fsynced")
        self.assertEqual(self.state(), before)
        stages = {}
        for path in set(actors.iterdir()) - initial_paths:
            value = credential(path)
            key = (value["role"], value["lease_epoch"])
            self.assertNotIn(key, stages, "staging evidence must be unambiguous")
            self.assertEqual(value["project_id"], request["project_id"])
            self.assertEqual(value["workflow_id"], request["workflow_id"])
            stages[key] = path
        expected = {("operator", request["lease_epoch"]),
                    ("operator", request["lease_epoch"] + 1)}
        if request["operation"] == "owner.acquire":
            expected.add(("owner", request["lease_epoch"] + 1))
        self.assertEqual(set(stages), expected)
        intact = tree(private_path(self.root))
        for key, path in stages.items():
            with self.subTest(missing_before_publication=key):
                original = path.read_bytes()
                path.unlink()
                try:
                    self.reject_unchanged(request, historical, "recovery_required")
                    self.assertTrue((private_path(self.root) / "credential-intent.json").exists())
                finally:
                    path.write_bytes(original)
                    path.chmod(0o600)
        self.assertTrue(tree(private_path(self.root)) == intact,
                        "restoring missing evidence must preserve the pending transaction")
        staged_bytes = {path: path.read_bytes() for path in stages.values()}
        self.crash(request, historical, "state_published")
        return stages, staged_bytes

    def assert_corrupt_cleanup_evidence_is_retained(self, request: dict, historical: Path,
                                                   evidence: dict[Path, bytes]) -> None:
        intact = tree(private_path(self.root))
        for index, (path, staged) in enumerate(evidence.items()):
            with self.subTest(corrupt_after_publication=index):
                original = path.read_bytes() if path.exists() else None
                value = json.loads(staged)
                value["secret"] = self.changed_secret(value["secret"])
                path.write_bytes(canonical(value))
                path.chmod(0o600)
                try:
                    self.reject_unchanged(request, historical, "recovery_required")
                    self.assertTrue((private_path(self.root) / "credential-intent.json").exists())
                finally:
                    if original is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(original)
        self.assertTrue(tree(private_path(self.root)) == intact,
                        "corruption controls must restore every original byte")

    def test_partial_cleanup_recovers_owner_receipts_without_waiving_evidence_checks(self) -> None:
        parent = self.root
        for name in ("owner.acquire", "owner.release", "owner.recover"):
            for removed in ("stage", "rollback", "stage-and-rollback"):
                with self.subTest(operation=name, removed=removed):
                    tag = f"{name}-partial-cleanup-{removed}"
                    self.root = parent / tag
                    self.root.mkdir()
                    request, actor = self.prepared_crash(name, tag)
                    historical = self.retain(actor, tag + "-historical.json")
                    stages, staged_bytes = self.pending_cleanup_files(request, actor, historical)
                    committed = self.state()
                    response = committed["receipts"][request["request_id"]]["response"]
                    self.assert_transition(request, response, historical)
                    store = private_path(self.root)
                    pair = {path: path.read_bytes() for path in
                            (store / "state.json", store / "state.json.bak")}
                    finals = [Path(response["result"]["operator_actor_file"])]
                    if name == "owner.acquire":
                        finals.append(Path(response["result"]["actor_file"]))
                    final_bytes = {path: path.read_bytes() for path in finals}
                    self.assert_corrupt_cleanup_evidence_is_retained(
                        request, historical, staged_bytes | final_bytes)
                    self.assertTrue(stages[("operator", request["lease_epoch"])].is_file())
                    epochs = ((request["lease_epoch"] + 1,) if removed == "stage" else
                              (request["lease_epoch"],) if removed == "rollback" else
                              (request["lease_epoch"] + 1, request["lease_epoch"]))
                    for epoch in epochs:
                        stages[("operator", epoch)].unlink(missing_ok=True)
                    self.assertTrue((store / "credential-intent.json").exists())
                    self.assert_crash_completes_once(request, historical)
                    self.assertEqual(self.state(), committed)
                    self.assertTrue(all(path.read_bytes() == raw for path, raw in pair.items()),
                                    "cleanup replay must not republish committed state or backup")
                    self.assertTrue(all(path.read_bytes() == raw
                                        for path, raw in final_bytes.items()),
                                    "cleanup replay must not rotate final credentials again")
                    self.assertTrue(all(not path.exists() for path in stages.values()),
                                    "successful reconciliation must finish credential cleanup")

    def test_intact_owner_crash_evidence_finishes_and_replays_exactly_once(self) -> None:
        parent = self.root
        common = ("stage_fsynced", "intent_dir_fsynced", "operator_credential_published",
                  "state_published", "cleanup_dir_fsynced")
        for name in ("owner.acquire", "owner.release", "owner.recover"):
            for damage in ("response", "staged-credential", "state"):
                with self.subTest(operation=name, damage=damage):
                    self.assert_tampered_crash_preserves_evidence(name, damage, parent)
            boundaries = common + (("owner_credential_published",)
                                   if name == "owner.acquire" else ())
            for boundary in boundaries:
                with self.subTest(operation=name, boundary=boundary):
                    tag = f"{name}-{boundary}"
                    self.root = parent / name / boundary
                    self.root.mkdir(parents=True)
                    request, actor = self.prepared_crash(name, tag)
                    historical = self.retain(actor, tag + "-historical.json")
                    state = self.state()
                    self.crash(request, actor, boundary)
                    if boundary == "stage_fsynced":
                        self.assertEqual(self.state(), state)
                    self.assert_crash_completes_once(request, historical)


if __name__ == "__main__":
    unittest.main()
