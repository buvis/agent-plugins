"""Epoch fencing, owner exclusion, and receipt-only historical authority."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from controller_cli_support import MAIN, canonical, fresh_request, private_path, tree
from controller_owner_support import OwnerCLITest, credential


class OwnerTest(OwnerCLITest):
    def test_rotates_operator_and_issues_fresh_owners_for_both_modes_and_sessions(self) -> None:
        _, opened, operator = self.bootstrap()
        identity = opened["result"]["actor_id"]
        original_operator = operator
        owner_ids = set()
        for index, (mode, session) in enumerate((("manual", "session-alpha"),
                                               ("supervised", "session-alpha-extra"))):
            old = credential(operator)
            _, acquired, owner, operator = self.acquire(
                operator, mode, session, f"acquire-{index}")
            current = credential(operator)
            self.assertEqual(operator, original_operator)
            self.assertEqual(current["actor_id"], identity)
            self.assertTrue(current["secret"] != old["secret"], "operator secret did not rotate")
            self.assertEqual(credential(owner)["native_session_id"], session)
            self.assertEqual(credential(owner)["actor_id"], acquired["result"]["actor_id"])
            self.assertNotIn(acquired["result"]["actor_id"], owner_ids)
            owner_ids.add(acquired["result"]["actor_id"])
            self.snapshot()
            name = "owner.release" if index == 0 else "owner.recover"
            authorizer = owner if index == 0 else operator
            previous = credential(operator)
            _, cleared, operator = self.clear(authorizer, name, f"clear-{index}")
            self.assertEqual(operator, original_operator)
            self.assertEqual(cleared["result"]["actor_id"], identity)
            self.assertTrue(credential(operator)["secret"] != previous["secret"])
            self.assertEqual(self.state()["lease_epoch"], 2 * index + 2)
            self.assertTrue(owner.exists(), "revoked owner evidence was removed")
            self.snapshot()
        self.assertEqual(len(owner_ids), 2)

    def test_historical_and_reopened_operator_retrieve_only_exact_receipts_after_all_rotations(self) -> None:
        fresh, opened, operator = self.bootstrap()
        old_operator = self.retain(operator, "operator-epoch-zero.json")
        acquired, acquire_response, owner, operator = self.acquire(operator)
        released, release_response, operator = self.clear(owner)
        _, _, newer_owner, operator = self.acquire(
            operator, "supervised", "session-beta", "acquire-second")
        recovery_authorizer = self.retain(operator, "operator-epoch-three.json")
        recovered, recovery_response, operator = self.clear(
            operator, "owner.recover", "recover-second")
        before = tree(private_path(self.root))
        self.assertEqual(self.response(self.apply(fresh)), opened)
        self.assertTrue(tree(private_path(self.root)) == before)
        self.reject_unchanged(fresh_request(self.root, "open-first-extra"),
                              None, "revision_conflict")
        for request, response, paths in (
                (acquired, acquire_response, (old_operator, operator)),
                (released, release_response, (owner,)),
                (recovered, recovery_response, (recovery_authorizer, operator))):
            for path in paths:
                self.assertEqual(self.response(self.apply(request, path)), response)
                self.assertTrue(tree(private_path(self.root)) == before)
        self.assertEqual(self.state()["receipts"][acquired["request_id"]][
            "authorizing_actor"]["secret_digest"],
            hashlib.sha256(credential(old_operator)["secret"].encode()).hexdigest())
        for path, name in ((old_operator, "owner.acquire"), (owner, "owner.release"),
                           (newer_owner, "owner.release"),
                           (recovery_authorizer, "owner.recover")):
            payload = ({"mode": "manual", "native_session_id": "session-new"}
                       if name == "owner.acquire" else
                       {"reason": "new recovery", "reconciled_job_ids": []}
                       if name == "owner.recover" else {})
            request = self.request(path, name, f"revoked-{path.name}", payload)
            self.reject_unchanged(request, path, "wrong_binding")
        self.reject_unchanged(released, operator, "wrong_binding")

    def test_changed_historical_envelopes_conflict_without_reapplying_effects(self) -> None:
        _, _, operator = self.bootstrap()
        historical = self.retain(operator, "old-operator.json")
        request, _, owner, operator = self.acquire(operator)
        _, _, operator = self.clear(owner)
        before = self.state()
        for path in (historical, operator):
            for change in ({"expected_revision": request["expected_revision"] + 1},
                           {"payload": {"mode": "manual", "native_session_id": "session-alpha-extra"}},
                           {"payload": {"mode": "supervised", "native_session_id": "session-alpha"}}):
                changed = copy.deepcopy(request)
                changed.update(change)
                self.reject_unchanged(changed, path, "invalid_request")
                self.assertEqual(self.state(), before)

    def test_checks_exact_identity_scope_epoch_job_and_role_before_mutation(self) -> None:
        _, opened, operator = self.bootstrap()
        _, _, owner, operator = self.acquire(operator)
        occupied = self.request(operator, "owner.acquire", "occupied", {
            "mode": "supervised", "native_session_id": "session-alpha-extra"})
        self.reject_unchanged(occupied, operator, "wrong_binding")
        valid = self.request(owner, "owner.release", "release-binding")
        for key, values in (
                ("actor_id", (valid["actor_id"] + "-extra", "prefix-" + valid["actor_id"])),
                ("workflow_id", (valid["workflow_id"] + "-extra", "prefix-" + valid["workflow_id"])),
                ("project_id", ("0" * 64, "f" * 64)),
                ("lease_epoch", (0, valid["lease_epoch"] + 1)),
                ("job_id", ("job-alpha", "job-alpha-extra"))):
            for value in values:
                with self.subTest(field=key, value=value):
                    self.reject_unchanged(valid | {key: value}, owner, "wrong_binding")
        self.reject_unchanged(valid, operator, "wrong_binding")
        self.reject_unchanged(self.request(operator, "owner.release", "operator-release"),
                              operator, "wrong_binding")
        for name, payload in (("owner.acquire", {"mode": "manual", "native_session_id": "a"}),
                              ("owner.recover", {"reason": "a", "reconciled_job_ids": []})):
            self.reject_unchanged(self.request(owner, name, name + "-wrong-role", payload),
                                  owner, "wrong_binding")
        self.assertEqual(self.state()["workflow_id"], opened["result"]["workflow_id"])
        self.clear(owner)

    def test_rejects_near_miss_credentials_and_does_not_fall_back_to_cwd_binding(self) -> None:
        _, _, operator = self.bootstrap()
        _, _, owner, operator = self.acquire(operator)
        request = self.request(owner, "owner.release", "release-evidence")
        for key, suffix in (("secret", "x"), ("native_session_id", "-extra"),
                            ("actor_id", "-extra"), ("workflow_id", "-extra")):
            fake = self.retain(owner, f"wrong-{key}.json")
            value = credential(fake)
            value[key] = (value[key][:-1] + ("A" if value[key][-1] != "A" else "B")
                          if key == "secret" else value[key] + suffix)
            fake.write_bytes(canonical(value))
            self.reject_unchanged(request, fake, "wrong_binding")
        near_root = self.base / "project-extra"
        near_root.mkdir()
        before = tree(private_path(self.root))
        self.response(self.apply(request, owner, root=near_root), "wrong_binding", revision=0)
        self.assertTrue(tree(private_path(self.root)) == before,
                        "rejection changed original project evidence")
        self.assertFalse(private_path(near_root).exists())
        self.clear(owner)

    def test_closed_payloads_reject_empty_oversized_and_multielement_reconciliation(self) -> None:
        _, _, operator = self.bootstrap()
        for payload in ({}, {"mode": "manual", "native_session_id": ""},
                        {"mode": "manual-extra", "native_session_id": "session-alpha"},
                        {"mode": "supervised-extra", "native_session_id": "session-beta"},
                        {"mode": "manual", "native_session_id": "é" * 129},
                        {"mode": "manual", "native_session_id": "s", "extra": 1}):
            request = self.request(operator, "owner.acquire", "bad-acquire", payload)
            self.reject_unchanged(request, operator, "invalid_request")
        _, _, owner, operator = self.acquire(operator, session="é" * 128)
        for payload in ({}, {"reason": "", "reconciled_job_ids": []},
                        {"reason": "é" * 2049, "reconciled_job_ids": []},
                        {"reason": "explicit", "reconciled_job_ids": None},
                        {"reason": "explicit", "reconciled_job_ids": "job-a"},
                        {"reason": "explicit", "reconciled_job_ids": [1]},
                        {"reason": "explicit", "reconciled_job_ids": ["job-a", "job-a"]},
                        {"reason": "explicit", "reconciled_job_ids": [], "extra": 1}):
            request = self.request(operator, "owner.recover", "bad-recover", payload)
            self.reject_unchanged(request, operator, "invalid_request")
        for jobs in (["job-a", "job-b"], ["job-a-extra", "job-b-extra"]):
            request = self.request(operator, "owner.recover", "unreconciled-recover", {
                "reason": "Explicit reconciliation", "reconciled_job_ids": jobs})
            self.reject_unchanged(request, operator, "rejected_evidence")
        bad_release = self.request(owner, "owner.release", "bad-release", {"reason": "extra"})
        self.reject_unchanged(bad_release, owner, "invalid_request")
        request = self.request(operator, "owner.recover", "recover-at-bound", {
            "reason": "é" * 2048, "reconciled_job_ids": []})
        self.response(self.apply(request, operator), revision=2)
        self.assertIsNone(self.state()["owner"])

    def test_two_independent_subprocess_acquires_have_exactly_one_winner(self) -> None:
        _, _, operator = self.bootstrap()
        gate = self.base / "start-gate"
        script = ("import pathlib,runpy,sys,time; gate=pathlib.Path(sys.argv.pop(1)); "
                  "deadline=time.monotonic()+25\n"
                  "while not gate.exists():\n"
                  " if time.monotonic()>deadline: raise TimeoutError('gate')\n"
                  " time.sleep(0.005)\n"
                  "main=sys.argv.pop(1); sys.argv[0]=main; "
                  "sys.path.insert(0,str(pathlib.Path(main).parent)); "
                  "runpy.run_path(main,run_name='__main__')")
        processes, requests = [], []
        for index, mode in enumerate(("manual", "supervised")):
            actor = self.retain(operator, f"client-{index}.json")
            request = self.request(actor, "owner.acquire", f"racing-{index}", {
                "mode": mode, "native_session_id": f"independent-session-{index}"})
            requests.append(request)
            arguments = [sys.executable, "-c", script, str(gate), str(MAIN), "--json",
                         "apply", "--project-root", str(self.root), "--request",
                         str(self.write_request(request)), "--actor-file", str(actor)]
            process = subprocess.Popen(arguments, cwd=self.base, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            self.addCleanup(lambda p=process: p.kill() if p.poll() is None else None)
            processes.append(process)
        gate.touch()
        results = [subprocess.CompletedProcess(p.args, p.wait(timeout=30), *p.communicate(timeout=30))
                   for p in processes]
        self.assertEqual(sorted(p.returncode for p in results), [0, 1])
        winner = next(index for index, value in enumerate(results) if value.returncode == 0)
        response = self.response(results[winner], revision=1)
        loser = results[1 - winner]
        self.response(loser, "wrong_binding", revision=1)
        self.assert_transition(requests[winner], response, operator)
        self.assertEqual(set(self.state()["receipts"]), {"open-first", f"racing-{winner}"})
        self.assertEqual(self.state()["owner"]["native_session_id"], f"independent-session-{winner}")


if __name__ == "__main__":
    unittest.main()
