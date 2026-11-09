"""Receipt authority survives rotation without granting retired credentials a lease."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from controller_cli_support import canonical, private_path, tree
from controller_owner_support import OwnerCLITest, credential


class OwnerV2Test(OwnerCLITest):
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
                    self.assertEqual(tree(private_path(self.root)), before)
            recovered = records[-1][0]
            for jobs in (["job-alpha", "job-beta"], ["job-alpha-extra", "job-beta-extra"]):
                changed = recovered | {"payload": recovered["payload"] | {
                    "reconciled_job_ids": jobs}}
                self.reject_unchanged(changed, operator, "invalid_request")
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
        self.assertEqual(tree(private_path(self.root)), before)
        self.assertEqual(self.state()["lease_epoch"], 4)
        self.assertEqual(set(self.state()["actors"]), {credential(current)["actor_id"]})

    def test_exact_receipt_replay_still_checks_credential_file_safety(self) -> None:
        records, _, current = self.history("private")
        for request, response, historical in (records[1], records[2], records[4]):
            for index, source in enumerate((historical, current)):
                if index and request["operation"] == "owner.release":
                    continue
                stem = f"{request['request_id']}-{index}"
                valid = self.retain(source, stem + ".json")
                self.assertEqual(self.response(self.apply(request, valid)), response)
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
            self.assertEqual(tree(private_path(self.root)), before)
        completed = self.response(self.apply(request, historical),
                                  revision=request["expected_revision"] + 1)
        self.assert_transition(request, completed, historical)
        self.assertFalse(intent.exists())
        after = tree(private_path(self.root))
        self.assertEqual(self.response(self.apply(request, historical)), completed)
        if request["operation"] != "owner.release":
            current = Path(completed["result"]["operator_actor_file"])
            self.assertEqual(self.response(self.apply(request, current)), completed)
        self.assertEqual(tree(private_path(self.root)), after)
        self.assertEqual(set(self.state()["receipts"]), receipts | {request["request_id"]})
        self.snapshot()

    def test_intact_owner_crash_evidence_finishes_and_replays_exactly_once(self) -> None:
        parent = self.root
        common = ("stage_fsynced", "intent_dir_fsynced", "operator_credential_published",
                  "state_published", "cleanup_dir_fsynced")
        for name in ("owner.acquire", "owner.release", "owner.recover"):
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
