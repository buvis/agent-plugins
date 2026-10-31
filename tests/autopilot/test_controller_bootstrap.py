"""Bootstrap, snapshot, parsing and replay through the public controller CLI."""

from __future__ import annotations

import concurrent.futures
import fcntl
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from controller_cli_support import (
    CONTRACT, MAIN, ControllerCLITest, canonical, cli, existing_request,
    fresh_request, private_path, project_id, tree,
)


class ControllerBootstrapTest(ControllerCLITest):
    def test_absent_snapshot_uses_selected_root_and_creates_nothing(self) -> None:
        for name in ("project", "project-extra"):
            root = self.base / name
            root.mkdir(exist_ok=True)
            before = tree(root)
            completed = cli(["--json", "snapshot", "--project-root", str(root)],
                            cwd=self.base)
            response = self.response(completed, revision=0)
            expected = {"project_id": project_id(root), "workflow_id": None,
                        "lease_epoch": 0, "owner": None, "health": "absent"}
            for key, value in expected.items():
                self.assertEqual(response["result"][key], value)
            self.assertEqual(tree(root), before)
        self.assertNotEqual(project_id(self.root), project_id(root))

    def test_bootstrap_publishes_one_private_operator_state_and_receipt(self) -> None:
        results = []
        for name in ("project", "project-extra"):
            self.root = self.base / name
            self.root.mkdir(exist_ok=True)
            request, response = self.open(f"open-{name}")
            self.assertEqual(set(self.state()["receipts"]), {request["request_id"]})
            self.assert_private()
            results.append(response["result"])
        self.assertNotEqual(results[0]["workflow_id"], results[1]["workflow_id"])
        self.assertNotEqual(results[0]["actor_id"], results[1]["actor_id"])
        self.assertNotEqual(results[0]["actor_file"], results[1]["actor_file"])

    def test_lost_ack_replay_returns_exact_response_and_preserves_all_bytes(self) -> None:
        request, original = self.open("open-é")
        before = tree(self.root)
        replay = self.response(self.apply(request, raw=json.dumps(
            request, ensure_ascii=True, indent=2).encode()), revision=0)
        self.assertEqual(replay, original)
        self.assertEqual(tree(self.root), before)
        changed = dict(request, request_id="open-é-extra")
        self.response(self.apply(changed), "revision_conflict", revision=0)
        self.assertEqual(tree(self.root), before)
        changed["request_id"] = "open-e\u0301"
        self.response(self.apply(changed), "revision_conflict", revision=0)
        self.assertEqual(tree(self.root), before)

    def test_existing_open_requires_authentication_and_records_exact_receipts(self) -> None:
        fresh, opened = self.open()
        actor = Path(opened["result"]["actor_file"])
        for index, request_id in enumerate(("existing-alpha", "existing-beta")):
            request = existing_request(self.root, opened["result"], request_id, index)
            before = tree(self.root)
            self.response(self.apply(request), "wrong_binding", revision=index)
            self.assertEqual(tree(self.root), before)
            completed = self.response(self.apply(request, actor), revision=index + 1)
            self.assertEqual(completed["result"], opened["result"])
            state = self.state()
            self.assertIsNone(state["owner"])
            self.assertEqual(state["lease_epoch"], 0)
            self.assertEqual(state["receipts"][request_id]["response"], completed)
            unchanged = tree(self.root)
            self.assertEqual(self.response(self.apply(request, actor)), completed)
            self.assertEqual(tree(self.root), unchanged)
        self.assertEqual(self.response(self.apply(fresh)), opened)
        self.assertEqual(len(self.state()["receipts"]), 3)

    def test_recorded_request_changes_and_stale_new_requests_do_not_write(self) -> None:
        _, opened = self.open()
        actor = Path(opened["result"]["actor_file"])
        request = existing_request(self.root, opened["result"], "existing-alpha")
        self.response(self.apply(request, actor), revision=1)
        before = tree(self.root)
        changed = dict(request, expected_revision=1)
        self.response(self.apply(changed, actor), "invalid_request", revision=1)
        self.assertEqual(tree(self.root), before)
        stale = dict(request, request_id="existing-alpha-extra")
        self.response(self.apply(stale, actor), "revision_conflict", revision=1)
        self.assertEqual(tree(self.root), before)
        changed = dict(request, payload={"extra": "untrusted-value"})
        self.response(self.apply(changed, actor), "invalid_request", revision=1)
        self.assertEqual(tree(self.root), before)

    def test_wrong_project_workflow_actor_epoch_and_job_never_change_bytes(self) -> None:
        _, opened = self.open()
        result = opened["result"]
        actor = Path(result["actor_file"])
        request = existing_request(self.root, result, "existing-alpha")
        before = tree(self.root)
        variants = [("project_id", "0" * 64),
                    ("workflow_id", result["workflow_id"] + "-extra"),
                    ("actor_id", result["actor_id"] + "-extra"),
                    ("lease_epoch", 1), ("lease_epoch", 2),
                    ("job_id", "job-alpha"), ("job_id", "job-alpha-extra")]
        for key, value in variants:
            with self.subTest(key=key, value=value):
                self.response(self.apply(dict(request, **{key: value}), actor),
                              "wrong_binding", revision=0)
                self.assertEqual(tree(self.root), before)
        self.response(self.apply(request, actor), revision=1)

    def test_strict_envelope_rejections_happen_before_store_creation(self) -> None:
        request = fresh_request(self.root)
        variants = [{}, [], None, dict(request, extra="untrusted-value"),
                    dict(request, payload={"unknown": True}),
                    dict(request, protocol_major=True),
                    dict(request, expected_revision=True),
                    dict(request, expected_revision=-1),
                    dict(request, lease_epoch=False),
                    dict(request, request_id=""),
                    dict(request, request_id="x" * 257),
                    dict(request, request_id="é" * 129),
                    dict(request, operation="workflow.open-extra"),
                    dict(request, operation="prefix-workflow.open")]
        variants += [{key: value for key, value in request.items() if key != field}
                     for field in request]
        for variant in variants:
            with self.subTest(variant=variant):
                completed = self.apply(variant)
                self.response(completed, "invalid_request", revision=0)
                self.assertNotIn(b"untrusted-value", completed.stdout + completed.stderr)
                self.assertEqual(tree(self.root), {})
        mismatches = [("expected_revision", 1, "revision_conflict"),
                      ("expected_revision", 2, "revision_conflict"),
                      ("actor_id", "actor-prefix", "wrong_binding"),
                      ("actor_id", "actor-prefix-extra", "wrong_binding")]
        for key, value, error in mismatches:
            with self.subTest(key=key, value=value):
                self.response(self.apply(dict(request, **{key: value})), error, revision=0)
                self.assertEqual(tree(self.root), {})
        self.response(self.apply(dict(request, protocol_major=2)),
                      "incompatible_contract", revision=0)
        self.assertEqual(tree(self.root), {})

    def test_strict_json_rejects_duplicate_nonfinite_utf8_trailing_and_deep_input(self) -> None:
        request = fresh_request(self.root)
        encoded = canonical(request)
        variants = [b"", b"{", b"[]", encoded + b" {}", b"\xff",
                    encoded[:-1] + b',"request_id":"different"}',
                    encoded.replace(b'"expected_revision":0', b'"expected_revision":NaN'),
                    encoded.replace(b'"expected_revision":0', b'"expected_revision":Infinity'),
                    encoded.replace(b'"expected_revision":0',
                                    b'"expected_revision":' + b"9" * 641),
                    b"[" * 33 + b"0" + b"]" * 33]
        for raw in variants:
            with self.subTest(raw=raw[:80]):
                self.response(self.apply(request, raw=raw), "invalid_request", revision=0)
                self.assertEqual(tree(self.root), {})

    def test_request_byte_and_utf8_identity_limits_accept_the_exact_boundary(self) -> None:
        request = fresh_request(self.root, "é" * 128)
        encoded = canonical(request)
        raw = encoded + b" " * (2097152 - len(encoded))
        response = self.response(self.apply(request, raw=raw), revision=0)
        self.assert_open_consistent(request, response)
        before = tree(self.root)
        self.response(self.apply(request, raw=raw + b" "), "invalid_request", revision=0)
        self.assertEqual(tree(self.root), before)

    def test_reserved_operations_reject_without_receipts_or_credentials(self) -> None:
        _, opened = self.open()
        actor = Path(opened["result"]["actor_file"])
        schema = json.loads((CONTRACT / "workflow-v1.json").read_bytes())
        before = tree(self.root)
        for operation in schema["x-controller"]["reserved_operations"]:
            request = existing_request(self.root, opened["result"], operation)
            request["operation"] = operation
            self.response(self.apply(request, actor), "missing_capability", revision=0)
            self.assertEqual(tree(self.root), before)

    def test_snapshot_reveals_named_metadata_without_credential_or_receipt_material(self) -> None:
        _, opened = self.open()
        actor = Path(opened["result"]["actor_file"])
        request = existing_request(self.root, opened["result"], "existing-private-id")
        self.response(self.apply(request, actor), revision=1)
        before = tree(self.root)
        completed = cli(["--json", "snapshot", "--project-root", str(self.root)])
        response = self.response(completed, revision=1)
        result = response["result"]
        for key in ("workflow_id", "lease_epoch"):
            self.assertEqual(result[key], opened["result"][key])
        self.assertEqual(result["project_id"], project_id(self.root))
        self.assertIsNone(result["owner"])
        credential = json.loads(actor.read_bytes())
        for forbidden in (credential["secret"], "secret_digest", "request_digest",
                          request["request_id"], "authorizing_actor"):
            self.assertNotIn(forbidden.encode(), completed.stdout + completed.stderr)
        for receipt in self.state()["receipts"].values():
            self.assertNotIn(receipt["request_digest"].encode(), completed.stdout)
        self.assertEqual(tree(self.root), before)

    def test_snapshot_waits_for_existing_exclusive_lock(self) -> None:
        self.open()
        lock = private_path(self.root) / "state.json.lock"
        arguments = [sys.executable, str(MAIN), "--json", "snapshot",
                     "--project-root", str(self.root)]
        with lock.open("rb") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.communicate(timeout=0.3)
                fcntl.flock(handle, fcntl.LOCK_UN)
                stdout, stderr = process.communicate(timeout=30)
                self.response(subprocess.CompletedProcess(arguments, process.returncode,
                                                          stdout, stderr), revision=0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=30)

    def test_concurrent_bootstrap_has_one_workflow_and_replays_same_request(self) -> None:
        request = fresh_request(self.root)
        path = self.write_request(request)
        arguments = ["--json", "apply", "--project-root", str(self.root),
                     "--request", str(path)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            outcomes = list(pool.map(lambda _: cli(arguments), range(4)))
        responses = [self.response(outcome, revision=0) for outcome in outcomes]
        self.assertEqual(responses, [responses[0]] * 4)
        self.assert_open_consistent(request, responses[0])
        self.assertEqual(len(self.state()["receipts"]), 1)

    def test_concurrent_distinct_bootstrap_requests_have_exactly_one_winner(self) -> None:
        requests = [fresh_request(self.root, name) for name in ("open-a", "open-a-extra")]
        paths = [self.write_request(request) for request in requests]
        arguments = [["--json", "apply", "--project-root", str(self.root),
                      "--request", str(path)] for path in paths]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(cli, arguments))
        self.assertEqual(sorted(outcome.returncode for outcome in outcomes), [0, 1])
        winner = next(index for index, outcome in enumerate(outcomes)
                      if outcome.returncode == 0)
        success = self.response(outcomes[winner], revision=0)
        self.response(outcomes[1 - winner], "revision_conflict", revision=0)
        self.assert_open_consistent(requests[winner], success)
        self.assertEqual(set(self.state()["receipts"]), {requests[winner]["request_id"]})

    def test_credentials_reject_wrong_permissions_symlinks_hardlinks_and_secrets(self) -> None:
        _, opened = self.open()
        actor = Path(opened["result"]["actor_file"])
        request = existing_request(self.root, opened["result"], "existing-alpha")
        original = actor.read_bytes()
        copied = self.base / "copy.json"
        variants = [{**json.loads(original), "secret": "SENTINEL-UNTRUSTED-SECRET"},
                    {**json.loads(original), "extra": "SENTINEL-UNTRUSTED-SECRET"}]
        for credential in variants:
            copied.write_bytes(canonical(credential))
            copied.chmod(0o600)
            self.assert_credential_rejected(request, copied)
        copied.write_bytes(original)
        copied.chmod(0o644)
        self.assert_credential_rejected(request, copied)
        copied.unlink()
        copied.symlink_to(actor)
        self.assert_credential_rejected(request, copied)
        copied.unlink()
        os.link(actor, copied)
        self.assert_credential_rejected(request, copied)
        copied.unlink()
        self.assertEqual(actor.read_bytes(), original)
        self.response(self.apply(request, actor), revision=1)

    def assert_credential_rejected(self, request: dict, actor: Path) -> None:
        before = tree(self.root)
        completed = self.apply(request, actor)
        self.response(completed, "wrong_binding", revision=0)
        self.assertNotIn(b"SENTINEL-UNTRUSTED-SECRET", completed.stdout + completed.stderr)
        self.assertEqual(tree(self.root), before)

    def test_private_ignores_cover_state_credentials_and_sibling_archives(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], timeout=30, check=True,
                       capture_output=True)
        _, opened = self.open()
        self.assert_private()
        for parent in (self.root / ".autopilot", private_path(self.root)):
            self.assertEqual((parent / ".gitignore").read_bytes(), b"*\n")
            self.assertEqual((parent / ".gitignore").stat().st_mode & 0o777, 0o600)
        paths = [".autopilot/controller/state.json", ".autopilot/controller/state.json.bak",
                 str(Path(opened["result"]["actor_file"]).relative_to(self.root)),
                 ".autopilot/archive-workflow/state.json"]
        checked = subprocess.run(["git", "check-ignore", "--", *paths], cwd=self.root,
                                 timeout=30, capture_output=True, check=False)
        self.assertEqual(checked.returncode, 0)
        self.assertEqual(checked.stdout.decode().splitlines(), paths)

    def test_argument_misuse_exits_two_without_echoing_untrusted_values(self) -> None:
        self.assertTrue(MAIN.is_file(), "public controller CLI is unavailable")
        for arguments in (["--json", "apply"], ["--json", "snapshot"],
                          ["--json", "SENTINEL-UNTRUSTED-ARGUMENT"]):
            completed = cli(arguments, cwd=self.root)
            self.assertEqual(completed.returncode, 2)
            self.assertNotIn(b"SENTINEL-UNTRUSTED-ARGUMENT",
                             completed.stdout + completed.stderr)
            self.assertEqual(tree(self.root), {})


if __name__ == "__main__":
    unittest.main()
