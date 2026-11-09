Same task, next review cycle. You already reviewed this task's diff earlier in
this conversation; below is only what changed since.

You already reviewed0c51c0a..84d23d2 earlier in this conversation. That range is unchanged and is not repeated here.
New recorded verification: exact six-file managed Python3.12/requirements acceptance command from first review ran once, timeout300: exit0,50passed in111.89s. New cleanup regression failed before fix (1failed in2.69s), then passed within expanded acceptance. Style/split checks exit0. Missing precommit evidence and present corrupt stage/rollback/final evidence remain rejected with bytes preserved; committed state/backup/final credentials do not republish. Other LOW code was unchanged. Coordinator corruption probe for malformed predecessor returned structured recovery_required at current revision, stderr empty, all evidence unchanged. No full implementation-suite or PRD-review completion claim.


## Findings you raised, sent to the implementor

MEDIUM | plugins/autopilot/controller/autopilot_state/owner.py:~214 (`_publish_credentials`; cleanup loop in `finish_intent` ~198) | Cleanup is not idempotent. `finish_intent` removes each entry's stage and rollback file one at a time. `_publish_credentials` then verifies every operator `previous["stage"]` unconditionally, before it checks whether `final` already matches. A crash after the operator rollback file is removed but before the intent is removed, for example between the operator and owner entries of `owner.acquire`, leaves the intent in place. Every later recovery then fails reading the missing rollback file, so the project is stuck in `recovery_required`. The tests only crash at `cleanup_dir_fsynced`, which is after all removals, so they miss this. | When `current == candidate` and `final` already matches `entry["digest"]`, skip the stage and rollback checks. Only require `previous["stage"]` while `final` still holds the old credential. Add a crash test between the per-entry removals.


## What changed since your last review

```diff
diff --git a/plugins/autopilot/CHANGELOG.md b/plugins/autopilot/CHANGELOG.md
index b386289..6864644 100644
--- a/plugins/autopilot/CHANGELOG.md
+++ b/plugins/autopilot/CHANGELOG.md
@@ -30,6 +30,7 @@
 
 ### Fixed
 
+- **autopilot**: finish interrupted owner credential cleanup after state publication, while rejecting missing precommit evidence and corrupt remaining files.
 - **autopilot**: report the current durable revision when snapshots refuse pending credential intents, without reconciling them.
 - **autopilot**: rotate owner leases and operator credentials recoverably, retaining exact receipt replay without restoring retired mutation authority.
 - **autopilot**: restore transaction publication guard checks at every durability boundary, preserving exact state and backup rollback when evidence changes.
diff --git a/plugins/autopilot/controller/autopilot_state/owner.py b/plugins/autopilot/controller/autopilot_state/owner.py
index 26d1db7..a94ad56 100644
--- a/plugins/autopilot/controller/autopilot_state/owner.py
+++ b/plugins/autopilot/controller/autopilot_state/owner.py
@@ -216,7 +216,8 @@ def _publish_credentials(intent: dict, layout: actors.PrivateLayout,
     for entry in intent["credentials"]:
         stage, final = layout.actors / entry["stage"], layout.actors / entry["final"]
         previous = entry["previous"]
-        if previous is not None:
+        if previous is not None and (
+                current != candidate or layout.exists(layout.actors / previous["stage"])):
             verify_file(layout, layout.actors / previous["stage"], previous)
         if layout.exists(stage):
             verify_file(layout, stage, entry)
diff --git a/tests/autopilot/test_controller_owner_v2.py b/tests/autopilot/test_controller_owner_v2.py
index 1f66721..6371128 100644
--- a/tests/autopilot/test_controller_owner_v2.py
+++ b/tests/autopilot/test_controller_owner_v2.py
@@ -292,6 +292,105 @@ class OwnerV2Test(OwnerCLITest):
                 path.write_bytes(original)
         self.assert_crash_completes_once(request, historical)
 
+    def pending_cleanup_files(self, request: dict, actor: Path,
+                              historical: Path) -> tuple[dict[tuple[str, int], Path],
+                                                         dict[Path, bytes]]:
+        actors = private_path(self.root) / "actors"
+        initial_paths = set(actors.iterdir())
+        before = self.state()
+        self.crash(request, actor, "intent_dir_fsynced")
+        self.assertEqual(self.state(), before)
+        stages = {}
+        for path in set(actors.iterdir()) - initial_paths:
+            value = credential(path)
+            key = (value["role"], value["lease_epoch"])
+            self.assertNotIn(key, stages, "staging evidence must be unambiguous")
+            self.assertEqual(value["project_id"], request["project_id"])
+            self.assertEqual(value["workflow_id"], request["workflow_id"])
+            stages[key] = path
+        expected = {("operator", request["lease_epoch"]),
+                    ("operator", request["lease_epoch"] + 1)}
+        if request["operation"] == "owner.acquire":
+            expected.add(("owner", request["lease_epoch"] + 1))
+        self.assertEqual(set(stages), expected)
+        intact = tree(private_path(self.root))
+        for key, path in stages.items():
+            with self.subTest(missing_before_publication=key):
+                original = path.read_bytes()
+                path.unlink()
+                try:
+                    self.reject_unchanged(request, historical, "recovery_required")
+                    self.assertTrue((private_path(self.root) / "credential-intent.json").exists())
+                finally:
+                    path.write_bytes(original)
+                    path.chmod(0o600)
+        self.assertTrue(tree(private_path(self.root)) == intact,
+                        "restoring missing evidence must preserve the pending transaction")
+        staged_bytes = {path: path.read_bytes() for path in stages.values()}
+        self.crash(request, historical, "state_published")
+        return stages, staged_bytes
+
+    def assert_corrupt_cleanup_evidence_is_retained(self, request: dict, historical: Path,
+                                                   evidence: dict[Path, bytes]) -> None:
+        intact = tree(private_path(self.root))
+        for index, (path, staged) in enumerate(evidence.items()):
+            with self.subTest(corrupt_after_publication=index):
+                original = path.read_bytes() if path.exists() else None
+                value = json.loads(staged)
+                value["secret"] = self.changed_secret(value["secret"])
+                path.write_bytes(canonical(value))
+                path.chmod(0o600)
+                try:
+                    self.reject_unchanged(request, historical, "recovery_required")
+                    self.assertTrue((private_path(self.root) / "credential-intent.json").exists())
+                finally:
+                    if original is None:
+                        path.unlink(missing_ok=True)
+                    else:
+                        path.write_bytes(original)
+        self.assertTrue(tree(private_path(self.root)) == intact,
+                        "corruption controls must restore every original byte")
+
+    def test_partial_cleanup_recovers_owner_receipts_without_waiving_evidence_checks(self) -> None:
+        parent = self.root
+        for name in ("owner.acquire", "owner.release", "owner.recover"):
+            for removed in ("stage", "rollback", "stage-and-rollback"):
+                with self.subTest(operation=name, removed=removed):
+                    tag = f"{name}-partial-cleanup-{removed}"
+                    self.root = parent / tag
+                    self.root.mkdir()
+                    request, actor = self.prepared_crash(name, tag)
+                    historical = self.retain(actor, tag + "-historical.json")
+                    stages, staged_bytes = self.pending_cleanup_files(request, actor, historical)
+                    committed = self.state()
+                    response = committed["receipts"][request["request_id"]]["response"]
+                    self.assert_transition(request, response, historical)
+                    store = private_path(self.root)
+                    pair = {path: path.read_bytes() for path in
+                            (store / "state.json", store / "state.json.bak")}
+                    finals = [Path(response["result"]["operator_actor_file"])]
+                    if name == "owner.acquire":
+                        finals.append(Path(response["result"]["actor_file"]))
+                    final_bytes = {path: path.read_bytes() for path in finals}
+                    self.assert_corrupt_cleanup_evidence_is_retained(
+                        request, historical, staged_bytes | final_bytes)
+                    self.assertTrue(stages[("operator", request["lease_epoch"])].is_file())
+                    epochs = ((request["lease_epoch"] + 1,) if removed == "stage" else
+                              (request["lease_epoch"],) if removed == "rollback" else
+                              (request["lease_epoch"] + 1, request["lease_epoch"]))
+                    for epoch in epochs:
+                        stages[("operator", epoch)].unlink(missing_ok=True)
+                    self.assertTrue((store / "credential-intent.json").exists())
+                    self.assert_crash_completes_once(request, historical)
+                    self.assertEqual(self.state(), committed)
+                    self.assertTrue(all(path.read_bytes() == raw for path, raw in pair.items()),
+                                    "cleanup replay must not republish committed state or backup")
+                    self.assertTrue(all(path.read_bytes() == raw
+                                        for path, raw in final_bytes.items()),
+                                    "cleanup replay must not rotate final credentials again")
+                    self.assertTrue(all(not path.exists() for path in stages.values()),
+                                    "successful reconciliation must finish credential cleanup")
+
     def test_intact_owner_crash_evidence_finishes_and_replays_exactly_once(self) -> None:
         parent = self.root
         common = ("stage_fsynced", "intent_dir_fsynced", "operator_credential_published",
```

Judge two things, in this order:

1. For each finding above, is it resolved by this delta? Ground the verdict in a
   line of the delta, not in how clean the code now reads. A change that
   improves the file while leaving the defect reachable is not resolved.
   **Re-emit every finding you judge unresolved as a contract line of its own**,
   carrying the severity and `file:line` it had before. That line is the only
   thing that carries an unresolved finding out of this cycle: silence reads as
   fixed, and the defect ships.
2. Report new findings from THIS delta only. Do not re-report anything else from
   the earlier range — you already reviewed it — and do not re-raise a finding
   you are calling resolved.

Judge from this prompt and what you already read in this conversation.

Your reporting contract is unchanged: the one you were given at the top of this
conversation (`agents/pat.md`). Same line shape, same severities, and CLOSURE
verdicts still apply wherever they applied on the first dispatch. Emit
`NO FINDINGS` only when the delta is clean AND every finding above is resolved.
