"""Public CLI crash recovery and strict admission to credential intents."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from controller_cli_support import MAIN, cli, private_path, tree
from controller_owner_support import OwnerCLITest, credential

BOUNDARIES = ("stage_fsynced", "intent_dir_fsynced", "operator_credential_published",
              "state_published", "cleanup_dir_fsynced")


class OwnerRecoveryTest(OwnerCLITest):
    def prepared(self, name: str, suffix: str = "first") -> tuple[dict, Path, Path]:
        _, _, operator = self.bootstrap()
        actor = operator
        if name != "owner.acquire":
            _, _, owner, operator = self.acquire(operator)
            actor = owner if name == "owner.release" else operator
        payload = ({"mode": "supervised", "native_session_id": "session-crash-extra"}
                   if name == "owner.acquire" else
                   {"reason": "Explicit crash reconciliation", "reconciled_job_ids": []}
                   if name == "owner.recover" else {})
        return self.request(actor, name, f"crash-{suffix}", payload), actor, operator

    def pending_intent(self) -> Path:
        return private_path(self.root) / "credential-intent.json"

    def assert_pending_rejections(self, request: dict, actor: Path) -> None:
        before = tree(private_path(self.root))
        snapshot = cli(["--json", "snapshot", "--project-root", str(self.root)], cwd=self.base)
        self.response(snapshot, "recovery_required", revision=self.state()["revision"])
        self.assertTrue(tree(private_path(self.root)) == before)
        self.reject_unchanged(request | {"request_id": request["request_id"] + "-extra"},
                              actor, "recovery_required")
        for key, values in (("workflow_id", (request["workflow_id"] + "-extra",
                                              "prefix-" + request["workflow_id"])),
                            ("project_id", ("0" * 64, "f" * 64))):
            for value in values:
                self.reject_unchanged(request | {key: value}, actor, "wrong_binding")
        self.reject_unchanged(request | {"unexpected": True}, actor, "invalid_request")
        self.reject_unchanged(request | {"lease_epoch": True}, actor, "invalid_request")

    def assert_no_intent_secrets(self, intent: Path) -> None:
        encoded = intent.read_bytes()
        json.loads(encoded)
        for path in (private_path(self.root) / "actors").iterdir():
            if not path.is_file() or path == intent:
                continue
            try:
                value = json.loads(path.read_bytes())
            except (OSError, ValueError):
                continue
            if isinstance(value, dict) and isinstance(value.get("secret"), str):
                self.assertTrue(value["secret"].encode() not in encoded,
                                "intent contains plaintext credential material")
        self.assert_private()

    def recover_matching(self, request: dict, historical: Path, operator: Path) -> None:
        before = tree(private_path(self.root))
        completed = self.apply(request, historical)
        if completed.returncode == 1:
            self.response(completed, "recovery_required", revision=self.state()["revision"])
            self.assertTrue(tree(private_path(self.root)) == before,
                            "failed reconciliation discarded evidence")
            self.assertTrue(self.pending_intent().exists())
            return
        response = self.response(completed, revision=request["expected_revision"] + 1)
        self.assert_transition(request, response, historical)
        self.assertFalse(self.pending_intent().exists())
        after = tree(private_path(self.root))
        self.assertEqual(self.response(self.apply(request, historical)), response)
        if request["operation"] != "owner.release":
            current = Path(response["result"]["operator_actor_file"])
            self.assertEqual(self.response(self.apply(request, current)), response)
        self.assertTrue(tree(private_path(self.root)) == after)
        self.snapshot()

    def test_crashes_at_every_owner_publication_boundary_preserve_replay_or_evidence(self) -> None:
        project_base = self.root
        for name in ("owner.acquire", "owner.release", "owner.recover"):
            boundaries = BOUNDARIES + (("owner_credential_published",)
                                      if name == "owner.acquire" else ())
            for boundary in boundaries:
                with self.subTest(operation=name, boundary=boundary):
                    self.root = project_base / name / boundary
                    self.root.mkdir(parents=True)
                    request, actor, operator = self.prepared(name, boundary)
                    historical = self.retain(actor, f"historical-{name}-{boundary}.json")
                    old_state = self.state()
                    finals = {path: path.read_bytes() for path in (
                        private_path(self.root) / "actors").iterdir() if path.is_file()}
                    self.crash(request, actor, boundary)
                    if boundary == "stage_fsynced":
                        self.assertEqual(self.state(), old_state)
                        self.assertFalse(self.pending_intent().exists())
                        for path, payload in finals.items():
                            self.assertTrue(path.read_bytes() == payload)
                    if self.pending_intent().exists():
                        self.assert_no_intent_secrets(self.pending_intent())
                        self.assert_pending_rejections(request, historical)
                    self.recover_matching(request, historical, operator)

    def test_corrupt_real_intents_preserve_all_bytes_for_matching_and_unrelated_requests(self) -> None:
        original = self.root
        for name in ("owner.acquire", "owner.release", "owner.recover"):
            with self.subTest(operation=name):
                self.root = original / name
                self.root.mkdir(parents=True)
                request, actor, _ = self.prepared(name)
                historical = self.retain(actor, f"corrupt-intent-{name}.json")
                self.crash(request, actor, "intent_dir_fsynced")
                intent = self.pending_intent()
                self.assertTrue(intent.exists())
                intent.write_bytes(intent.read_bytes()[:19])
                self.reject_unchanged(request, historical, "recovery_required")
                self.reject_unchanged(request | {"request_id": "unrelated-corrupt-extra"},
                                      historical, "recovery_required")
                self.reject_unchanged(request | {"workflow_id": request["workflow_id"] + "-extra"},
                                      historical, "wrong_binding")

    def test_missing_or_corrupt_staged_credentials_cannot_finish_an_intent(self) -> None:
        original = self.root
        for damage in ("missing", "corrupt"):
            with self.subTest(damage=damage):
                self.root = original / damage
                self.root.mkdir()
                request, actor, _ = self.prepared("owner.acquire", damage)
                initial_paths = set((private_path(self.root) / "actors").iterdir())
                historical = self.retain(actor, f"historical-stage-{damage}.json")
                old_secret = credential(actor)["secret"]
                self.crash(request, actor, "intent_dir_fsynced")
                stages = []
                for path in (private_path(self.root) / "actors").iterdir():
                    if path in initial_paths or path == self.pending_intent() or not path.is_file():
                        continue
                    try:
                        value = json.loads(path.read_bytes())
                    except (OSError, ValueError):
                        continue
                    if isinstance(value, dict) and value.get("role") == "operator" and (
                            value.get("secret") != old_secret and "secret" in value):
                        stages.append(path)
                self.assertEqual(len(stages), 1, "one private staged operator credential is required")
                if damage == "missing":
                    stages[0].unlink()
                else:
                    stages[0].write_bytes(b"corrupt credential evidence")
                self.reject_unchanged(request, historical, "recovery_required")
                self.assert_pending_rejections(request, historical)

    def test_directory_fsync_failure_never_acknowledges_or_changes_final_credentials(self) -> None:
        original = self.root
        script = ("import errno,os,runpy,stat,sys; original=os.fsync\n"
                  "def fsync(fd):\n"
                  " if stat.S_ISDIR(os.fstat(fd).st_mode): raise OSError(errno.EINVAL,'fsync')\n"
                  " return original(fd)\n"
                  "os.fsync=fsync; main=sys.argv.pop(1); sys.argv[0]=main; "
                  "sys.path.insert(0,os.path.dirname(main)); runpy.run_path(main,run_name='__main__')")
        for name in ("owner.acquire", "owner.release", "owner.recover"):
            with self.subTest(operation=name):
                self.root = original / name
                self.root.mkdir()
                request, actor, _ = self.prepared(name)
                state = self.state()
                finals = {path: path.read_bytes() for path in (
                    private_path(self.root) / "actors").iterdir() if path.is_file()}
                completed = self.apply(request, actor, prefix=[sys.executable, "-c", script, str(MAIN)])
                self.response(completed, "recovery_required", revision=state["revision"])
                self.assertEqual(self.state(), state)
                for path, value in finals.items():
                    self.assertTrue(path.read_bytes() == value)


if __name__ == "__main__":
    unittest.main()
