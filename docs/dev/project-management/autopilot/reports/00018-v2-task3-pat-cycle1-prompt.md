
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: Complete owner leases credential rotation and exact receipt replay

Description:
Implement the missing owner.acquire/release/recover dispatcher using the existing locked writer and bootstrap primitives. Shared mutable state across subprocesses requires exclusive CAS and authenticated crash intents. Preserve all existing owner/capacity/recovery tests without weakening. Split implementation into owner.py if needed; maintain existing public API. Owner tests and recovery/capacity tests are read-only acceptance, not permission to edit.
Scope: staging-orphan file/byte budget is next Task4; state/response capacity remains here. Errors retain the selected root revision, or0beforeinitialization; corrected oracle preserves both stores.


Acceptance criteria:
lease_exclusion, wrong_actor, epoch_revoked, lost_ack_replay and fresh_open_replay reject bypasses without partial writes.
tests/autopilot/test_controller_capacity.py, tests/autopilot/test_controller_owner.py, tests/autopilot/test_controller_owner_recovery.py, tests/autopilot/test_controller_bootstrap.py and tests/autopilot/test_controller_bootstrap_recovery.py pass without skips, weaker assertions or fixtures that bypass the public protocol.


## Diff under review

```diff
diff --git a/plugins/autopilot/CHANGELOG.md b/plugins/autopilot/CHANGELOG.md
index d7b7721..b386289 100644
--- a/plugins/autopilot/CHANGELOG.md
+++ b/plugins/autopilot/CHANGELOG.md
@@ -30,6 +30,8 @@
 
 ### Fixed
 
+- **autopilot**: report the current durable revision when snapshots refuse pending credential intents, without reconciling them.
+- **autopilot**: rotate owner leases and operator credentials recoverably, retaining exact receipt replay without restoring retired mutation authority.
 - **autopilot**: restore transaction publication guard checks at every durability boundary, preserving exact state and backup rollback when evidence changes.
 - **autopilot**: `--verify` accepts a relative `--project-root` again and judges it exactly as its absolute spelling, instead of refusing every output path it resolves with `unsafe-artifact-path`.
 - **autopilot**: `--verify` proves both its log sink and its result-artifact sink openable before it spawns the child and judges each sink by the file it actually opened; when the spawn fails, an existing log and result artifact stay byte-identical and a log this run created is removed; it reports a sink open, write or close failure as its own controlled error with the child killed, stops the child's leftover processes when a sink fails late, and removes only a leaf it created; `--export-policy --out` refuses a reader-less FIFO instead of hanging and refuses up front where `O_NOFOLLOW` is missing; the log sink judges containment before it reads a Git pointer.
diff --git a/plugins/autopilot/controller/autopilot_state/actors.py b/plugins/autopilot/controller/autopilot_state/actors.py
index deafd6f..0c8a338 100644
--- a/plugins/autopilot/controller/autopilot_state/actors.py
+++ b/plugins/autopilot/controller/autopilot_state/actors.py
@@ -272,11 +272,25 @@ def verify_operator(layout: PrivateLayout, current: dict) -> None:
         raise StateIOError("current operator credential unavailable") from error
 
 
-def admit(candidate: dict, response: dict) -> dict:
+def authenticate_receipt(path: Path | None, descriptor: dict, current: dict,
+                         layout: PrivateLayout) -> None:
+    try:
+        authenticate(path, descriptor, layout)
+        return
+    except BindingError:
+        active = current["actors"].get(descriptor["actor_id"])
+        if (active is None or active["role"] != descriptor["role"]
+                or active["lease_epoch"] < descriptor["lease_epoch"]):
+            raise
+    authenticate(path, active, layout)
+
+
+def admit(candidate: dict, response: dict, *, emergency: bool = False) -> dict:
     candidate = schema.validate_state(candidate)
     stored = (json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True)
               + "\n").encode("utf-8")
-    if len(stored) > NORMAL_STATE_LIMIT or len(candidate["receipts"]) > 4094:
+    if not emergency and (len(stored) > NORMAL_STATE_LIMIT
+                          or len(candidate["receipts"]) > 4094):
         raise StateIOError("normal capacity exhausted")
     if len(canonical(response)) > 65536:
         raise StateIOError("response exceeds resource limit")
@@ -354,7 +368,12 @@ def read_intent(layout: PrivateLayout) -> dict | None:
     if not layout.exists(path):
         return None
     raw = layout.read(path, INTENT_LIMIT)
-    return validate_intent(schema.decode_json(raw.decode("utf-8"), source="intent"), layout)
+    value = schema.decode_json(raw.decode("utf-8"), source="intent")
+    if isinstance(value, dict) and isinstance(value.get("request"), dict) and (
+            value["request"].get("operation") in {"owner.acquire", "owner.release", "owner.recover"}):
+        from . import owner
+        return owner.validate_intent(value, layout)
+    return validate_intent(value, layout)
 
 
 def verify_credential(layout: PrivateLayout, path: Path, intent: dict) -> None:
diff --git a/plugins/autopilot/controller/autopilot_state/owner.py b/plugins/autopilot/controller/autopilot_state/owner.py
new file mode 100644
index 0000000..26d1db7
--- /dev/null
+++ b/plugins/autopilot/controller/autopilot_state/owner.py
@@ -0,0 +1,271 @@
+"""Owner lease transitions under the controller's existing exclusive lock."""
+
+from __future__ import annotations
+
+import copy
+import hmac
+import os
+import re
+import secrets
+from pathlib import Path
+
+from . import actors, schema
+from .store import StateIOError, StateStore
+
+INTENT_KEYS = {"version", "request", "request_digest", "old_revision",
+               "old_state_digest", "old_actor", "old_actors", "old_owner",
+               "candidate", "response", "receipt", "credentials"}
+
+
+def transition(current: dict, request: dict, operator: dict,
+               owner: dict | None, layout: actors.PrivateLayout) -> tuple[dict, dict]:
+    candidate = copy.deepcopy(current)
+    candidate["revision"] += 1
+    candidate["lease_epoch"] += 1
+    candidate["actors"] = {operator["actor_id"]: operator}
+    candidate["owner"] = None
+    result = {"actor_id": operator["actor_id"], "lease_epoch": candidate["lease_epoch"],
+              "operator_actor_file": str(layout.actors / "operator.json")}
+    if owner is not None:
+        candidate["actors"][owner["actor_id"]] = owner
+        candidate["owner"] = {"actor_id": owner["actor_id"],
+                              "lease_epoch": candidate["lease_epoch"], **request["payload"]}
+        result.update(actor_id=owner["actor_id"],
+                      actor_file=str(layout.actors / (owner["actor_id"] + ".json")))
+    completed = {"ok": True, "revision": candidate["revision"], "result": result,
+                 "error_code": None, "retryable": False}
+    candidate["receipts"][request["request_id"]] = {
+        "request_digest": actors.digest(actors.canonical(request)),
+        "authorizing_actor": current["actors"][request["actor_id"]], "response": completed}
+    emergency = current["owner"] is not None and request["operation"] != "owner.acquire"
+    return actors.admit(candidate, completed, emergency=emergency), completed
+
+
+def prepare(request: dict, current: dict, layout: actors.PrivateLayout) -> dict:
+    old_operator = next(row for row in current["actors"].values() if row["role"] == "operator")
+    old_raw = layout.read(layout.actors / "operator.json", 65536)
+    credentials, staged = [], []
+    descriptors = {}
+    roles = ("operator", "owner") if request["operation"] == "owner.acquire" else ("operator",)
+    for role in roles:
+        actor_id = old_operator["actor_id"] if role == "operator" else "owner-" + secrets.token_hex(16)
+        credential = {"actor_id": actor_id, "project_id": current["project_id"],
+                      "workflow_id": current["workflow_id"], "role": role,
+                      "lease_epoch": current["lease_epoch"] + 1,
+                      "native_session_id": (request["payload"]["native_session_id"]
+                                            if role == "owner" else None),
+                      "secret": secrets.token_urlsafe(32)}
+        raw = actors.canonical(credential)
+        descriptor = actors.credential_descriptor(raw)
+        descriptors[role] = descriptor
+        entry = {"stage": f".{role}-{secrets.token_hex(16)}.stage",
+                 "final": "operator.json" if role == "operator" else actor_id + ".json",
+                 "digest": actors.digest(raw), "actor": descriptor, "previous": None}
+        staged.append((entry["stage"], raw))
+        if role == "operator":
+            entry["previous"] = {"stage": f".operator-{secrets.token_hex(16)}.rollback",
+                                 "digest": actors.digest(old_raw), "actor": old_operator}
+            staged.append((entry["previous"]["stage"], old_raw))
+        credentials.append(entry)
+    candidate, completed = transition(current, request, descriptors["operator"],
+                                       descriptors.get("owner"), layout)
+    receipt = candidate["receipts"][request["request_id"]]
+    intent = {"version": 1, "request": request, "request_digest": receipt["request_digest"],
+              "old_revision": current["revision"],
+              "old_state_digest": actors.digest(actors.canonical(current)),
+              "old_actor": current["actors"][request["actor_id"]],
+              "old_actors": current["actors"], "old_owner": current["owner"],
+              "candidate": candidate, "response": completed, "receipt": receipt,
+              "credentials": credentials}
+    validate_intent(intent, layout)
+    encoded = actors.canonical(intent)
+    if len(encoded) > actors.INTENT_LIMIT:
+        raise StateIOError("intent exceeds resource limit")
+    for name, raw in staged:
+        layout.write_new(layout.actors / name, raw)
+    temporary = layout.private / f".intent-{secrets.token_hex(16)}.tmp"
+    layout.write_new(temporary, encoded)
+    layout.publish(temporary, layout.private / "credential-intent.json")
+    return intent
+
+
+def validate_intent(intent: object, layout: actors.PrivateLayout) -> dict:
+    from . import protocol
+
+    schema._object(intent, INTENT_KEYS)
+    if type(intent["version"]) is not int or intent["version"] != 1:
+        raise StateIOError("invalid owner intent")
+    request = protocol.parse_request(actors.canonical(intent["request"]), {"reserved_operations": {}})
+    if request["operation"] not in protocol.OWNER_OPERATIONS:
+        raise StateIOError("invalid owner operation")
+    candidate = schema.validate_state(intent["candidate"])
+    old = copy.deepcopy(candidate)
+    old["revision"] = intent["old_revision"]
+    old["lease_epoch"] = request["lease_epoch"]
+    old["actors"] = intent["old_actors"]
+    old["owner"] = intent["old_owner"]
+    del old["receipts"][request["request_id"]]
+    old = schema.validate_state(old)
+    authorizer = old["actors"][request["actor_id"]]
+    expected_role = "owner" if request["operation"] == "owner.release" else "operator"
+    if (old["repo_root"] != str(layout.root)
+            or old["project_id"] != protocol.project_identity(layout.root)
+            or request["expected_revision"] != old["revision"]
+            or intent["old_state_digest"] != actors.digest(actors.canonical(old))
+            or intent["old_actor"] != authorizer or authorizer["role"] != expected_role
+            or (request["operation"] == "owner.acquire" and old["owner"] is not None)
+            or (request["operation"] == "owner.recover" and request["payload"]["reconciled_job_ids"])):
+        raise StateIOError("inconsistent owner predecessor")
+    protocol.actor_binding(request, authorizer, old["revision"])
+    descriptors = _intent_credentials(intent, request, old)
+    expected, completed = transition(old, request, descriptors["operator"],
+                                     descriptors.get("owner"), layout)
+    receipt = expected["receipts"][request["request_id"]]
+    if (candidate != expected or intent["response"] != completed or intent["receipt"] != receipt
+            or intent["request_digest"] != receipt["request_digest"]):
+        raise StateIOError("inconsistent owner intent")
+    return intent
+
+
+def _intent_credentials(intent: dict, request: dict, old: dict) -> dict:
+    entries = intent["credentials"]
+    roles = ["operator", "owner"] if request["operation"] == "owner.acquire" else ["operator"]
+    if not isinstance(entries, list) or len(entries) != len(roles):
+        raise StateIOError("invalid owner credentials")
+    descriptors, names = {}, set()
+    old_operator = next(row for row in old["actors"].values() if row["role"] == "operator")
+    for entry, role in zip(entries, roles):
+        schema._object(entry, {"stage", "final", "digest", "actor", "previous"})
+        descriptor = schema._actor(entry["actor"])
+        schema._digest(entry["digest"])
+        final = "operator.json" if role == "operator" else descriptor["actor_id"] + ".json"
+        if (descriptor["role"] != role or entry["final"] != final
+                or descriptor["lease_epoch"] != old["lease_epoch"] + 1
+                or any(descriptor[key] != old[key] for key in ("project_id", "workflow_id"))
+                or re.fullmatch(r"\." + role + r"-[0-9a-f]{32}\.stage", entry["stage"]) is None):
+            raise StateIOError("inconsistent owner credential")
+        if role == "operator":
+            previous = schema._object(entry["previous"], {"stage", "digest", "actor"})
+            schema._digest(previous["digest"])
+            if (descriptor["actor_id"] != old_operator["actor_id"]
+                    or descriptor["secret_digest"] == old_operator["secret_digest"]
+                    or previous["actor"] != old_operator
+                    or re.fullmatch(r"\.operator-[0-9a-f]{32}\.rollback", previous["stage"]) is None):
+                raise StateIOError("invalid operator rotation")
+            names.add(previous["stage"])
+        elif (entry["previous"] is not None
+              or re.fullmatch(r"owner-[0-9a-f]{32}", descriptor["actor_id"]) is None
+              or descriptor["actor_id"] in old["actors"]
+              or descriptor["native_session_id"] != request["payload"]["native_session_id"]):
+            raise StateIOError("invalid owner issuance")
+        if entry["stage"] in names:
+            raise StateIOError("duplicate owner stage")
+        names.add(entry["stage"])
+        descriptors[role] = descriptor
+    return descriptors
+
+
+def verify_file(layout: actors.PrivateLayout, path: Path, entry: dict) -> None:
+    raw = layout.read(path, 65536)
+    if (not hmac.compare_digest(actors.digest(raw), entry["digest"])
+            or actors.credential_descriptor(raw) != entry["actor"]):
+        raise StateIOError("credential evidence does not match intent")
+
+
+def finish_intent(request: dict, actor_file: Path | None, intent: dict,
+                  layout: actors.PrivateLayout, store: StateStore, current: dict | None) -> dict:
+    from . import protocol
+
+    revision = 0 if current is None else current["revision"]
+    if request != intent["request"]:
+        raise protocol.ProtocolError("recovery_required", revision)
+    # A rotated operator can recover its lost acknowledgement at the same path.
+    actors.authenticate_receipt(actor_file, intent["old_actor"], intent["candidate"], layout)
+    validate_intent(intent, layout)
+    candidate = intent["candidate"]
+    if current is None or (current != candidate and (
+            current["revision"] != intent["old_revision"]
+            or actors.digest(actors.canonical(current)) != intent["old_state_digest"])):
+        raise StateIOError("state does not match owner intent")
+    _publish_credentials(intent, layout, current, candidate)
+
+    def guard() -> None:
+        layout.verify()
+        for entry in intent["credentials"]:
+            verify_file(layout, layout.actors / entry["final"], entry)
+
+    guard()
+    if current != candidate:
+        store._transaction_locked(lambda unused: candidate, expected_revision=intent["old_revision"],
+                                  publication_guard=guard)
+    guard()
+    for entry in intent["credentials"]:
+        layout.remove(layout.actors / entry["stage"])
+        if entry["previous"] is not None:
+            layout.remove(layout.actors / entry["previous"]["stage"])
+    os.fsync(layout.directories[layout.actors])
+    layout.remove(layout.private / "credential-intent.json")
+    os.fsync(layout.directories[layout.private])
+    return intent["response"]
+
+
+def _publish_credentials(intent: dict, layout: actors.PrivateLayout,
+                         current: dict, candidate: dict) -> None:
+    pending = []
+    # Validate every piece of evidence before publishing any credential.
+    for entry in intent["credentials"]:
+        stage, final = layout.actors / entry["stage"], layout.actors / entry["final"]
+        previous = entry["previous"]
+        if previous is not None:
+            verify_file(layout, layout.actors / previous["stage"], previous)
+        if layout.exists(stage):
+            verify_file(layout, stage, entry)
+        if layout.exists(final):
+            raw = layout.read(final, 65536)
+            if actors.digest(raw) == entry["digest"]:
+                verify_file(layout, final, entry)
+                continue
+            if previous is None or current == candidate:
+                raise StateIOError("published credential does not match intent")
+            verify_file(layout, final, previous)
+        elif current == candidate or previous is not None:
+            raise StateIOError("committed credential missing")
+        verify_file(layout, stage, entry)
+        pending.append((stage, final))
+    for stage, final in pending:
+        layout.verify()
+        os.replace(stage.name, final.name, src_dir_fd=layout.directories[layout.actors],
+                   dst_dir_fd=layout.directories[layout.actors])
+        layout.verify()
+        os.fsync(layout.directories[layout.actors])
+
+
+def apply_locked(request: dict, actor_file: Path | None, current: dict,
+                 layout: actors.PrivateLayout, store: StateStore) -> dict:
+    from . import protocol
+
+    revision = current["revision"]
+    receipt = current["receipts"].get(request["request_id"])
+    if receipt is not None:
+        protocol.actor_binding(request, receipt["authorizing_actor"], revision)
+        actors.authenticate_receipt(actor_file, receipt["authorizing_actor"], current, layout)
+        if receipt["request_digest"] != actors.digest(actors.canonical(request)):
+            raise protocol.ProtocolError("invalid_request", revision)
+        actors.verify_operator(layout, current)
+        return receipt["response"]
+    descriptor = current["actors"].get(request["actor_id"])
+    role = "owner" if request["operation"] == "owner.release" else "operator"
+    if descriptor is None or descriptor["role"] != role:
+        raise protocol.ProtocolError("wrong_binding", revision)
+    protocol.actor_binding(request, descriptor, revision)
+    actors.authenticate(actor_file, descriptor, layout)
+    if request["expected_revision"] != revision:
+        raise protocol.ProtocolError("revision_conflict", revision)
+    if request["operation"] == "owner.acquire" and current["owner"] is not None:
+        raise protocol.ProtocolError("wrong_binding", revision)
+    if request["operation"] == "owner.recover" and (
+            request["payload"]["reconciled_job_ids"] or current["workflow"]["jobs"]):
+        raise protocol.ProtocolError("rejected_evidence", revision)
+    actors.verify_operator(layout, current)
+    intent = prepare(request, current, layout)
+    return finish_intent(request, actor_file, intent, layout, store, current)
diff --git a/plugins/autopilot/controller/autopilot_state/protocol.py b/plugins/autopilot/controller/autopilot_state/protocol.py
index 7c2f5ea..c26df4e 100644
--- a/plugins/autopilot/controller/autopilot_state/protocol.py
+++ b/plugins/autopilot/controller/autopilot_state/protocol.py
@@ -7,7 +7,7 @@ import json
 import secrets
 from pathlib import Path
 
-from . import actors, schema
+from . import actors, owner, schema
 from .paths import resolve_project_root
 from .store import FutureSchemaError, RevisionConflictError, StateError, StateIOError, StateStore
 
@@ -42,7 +42,8 @@ def public_contract() -> tuple[dict, dict]:
     metadata = {"protocol_major": 1, "package_version": manifest["version"],
                 "schema_digest": actors.digest(raw_schema),
                 "fixture_digest": actors.digest(raw_fixtures),
-                "operations": ["workflow.open"], "capabilities": ["workflow.core.v1"]}
+                "operations": ["workflow.open", "owner.acquire", "owner.release", "owner.recover"],
+                "capabilities": ["workflow.core.v1"]}
     return metadata, declared["x-controller"]
 
 
@@ -61,8 +62,13 @@ def validate_payload(operation: str, payload: object) -> None:
         reason = payload["reason"]
         if not isinstance(reason, str) or not 1 <= len(reason.encode("utf-8")) <= 4096:
             raise schema.SchemaError("invalid reason")
-        if payload["reconciled_job_ids"] != []:
+        jobs = payload["reconciled_job_ids"]
+        if not isinstance(jobs, list):
             raise schema.SchemaError("invalid reconciled jobs")
+        for job in jobs:
+            schema._identity(job)
+        if len(set(jobs)) != len(jobs):
+            raise schema.SchemaError("duplicate reconciled jobs")
 
 
 def parse_request(raw: bytes, declared: dict) -> dict:
@@ -126,7 +132,7 @@ def existing_open(request: dict, actor_file: Path | None, current: dict,
             fresh_binding(request, revision)
         else:
             actor_binding(request, receipt["authorizing_actor"], revision)
-            actors.authenticate(actor_file, receipt["authorizing_actor"], layout)
+            actors.authenticate_receipt(actor_file, receipt["authorizing_actor"], current, layout)
         actors.verify_operator(layout, current)
         return receipt["response"]
     if request["workflow_id"] is None:
@@ -163,14 +169,20 @@ def apply_locked(request: dict, actor_file: Path | None, layout: actors.PrivateL
             state_binding(current, layout.root)
         if request["project_id"] != project_identity(layout.root) or request["job_id"] is not None:
             raise ProtocolError("wrong_binding", revision)
+        if current is not None and request["workflow_id"] not in (None, current["workflow_id"]):
+            raise ProtocolError("wrong_binding", revision)
         intent = actors.read_intent(layout)
         if intent is not None:
+            if intent["request"]["operation"] in OWNER_OPERATIONS:
+                return owner.finish_intent(request, actor_file, intent, layout, store, current)
             fresh_binding(request, revision)
             if request != intent["request"]:
                 code = ("invalid_request" if request["request_id"] ==
                         intent["request"]["request_id"] else "recovery_required")
                 raise ProtocolError(code, revision)
             return actors.finish_bootstrap(intent, layout, store, current)
+        if request["operation"] in OWNER_OPERATIONS and current is not None:
+            return owner.apply_locked(request, actor_file, current, layout, store)
         if request["operation"] != "workflow.open":
             raise ProtocolError("missing_capability", revision)
         if current is not None:
@@ -258,9 +270,9 @@ def snapshot(root: Path) -> dict:
             return response(snapshot_projection(root, None))
         with store._locked(exclusive=False):
             layout.verify()
-            if layout.exists(layout.private / "credential-intent.json"):
-                raise ProtocolError("recovery_required")
             current = store._read_locked() if layout.exists(store.path) else None
+            if layout.exists(layout.private / "credential-intent.json"):
+                raise ProtocolError("recovery_required", 0 if current is None else current["revision"])
             if current is not None:
                 state_binding(current, root)
             return response(snapshot_projection(root, current), 0 if current is None else current["revision"])
diff --git a/tests/autopilot/test_controller_owner.py b/tests/autopilot/test_controller_owner.py
index 5336747..2fc7fe3 100644
--- a/tests/autopilot/test_controller_owner.py
+++ b/tests/autopilot/test_controller_owner.py
@@ -10,7 +10,7 @@ import unittest
 from pathlib import Path
 
 from controller_cli_support import MAIN, canonical, fresh_request, private_path, tree
-from controller_owner_support import OwnerCLITest, credential, operation
+from controller_owner_support import OwnerCLITest, credential
 
 
 class OwnerTest(OwnerCLITest):
@@ -136,7 +136,10 @@ class OwnerTest(OwnerCLITest):
             self.reject_unchanged(request, fake, "wrong_binding")
         near_root = self.base / "project-extra"
         near_root.mkdir()
-        self.reject_unchanged(request, owner, "wrong_binding", root=near_root)
+        before = tree(private_path(self.root))
+        self.response(self.apply(request, owner, root=near_root), "wrong_binding", revision=0)
+        self.assertTrue(tree(private_path(self.root)) == before,
+                        "rejection changed original project evidence")
         self.assertFalse(private_path(near_root).exists())
         self.clear(owner)
 
diff --git a/tests/autopilot/test_controller_owner_v2.py b/tests/autopilot/test_controller_owner_v2.py
new file mode 100644
index 0000000..1f66721
--- /dev/null
+++ b/tests/autopilot/test_controller_owner_v2.py
@@ -0,0 +1,320 @@
+"""Receipt authority survives rotation without granting retired credentials a lease."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import unittest
+from pathlib import Path
+
+from controller_cli_support import canonical, private_path, tree
+from controller_owner_support import OwnerCLITest, credential
+
+
+class OwnerV2Test(OwnerCLITest):
+    def test_wrong_binding_reports_selected_root_revision_and_preserves_both_projects(self) -> None:
+        _, _, operator = self.bootstrap()
+        _, _, owner, _ = self.acquire(operator)
+        request = self.request(owner, "owner.release", "cross-project-release")
+        original_root = self.root
+        original_before = tree(private_path(original_root))
+        selected_root = self.base / "project-extra"
+        selected_root.mkdir()
+        self.response(self.apply(request, owner, root=selected_root),
+                      "wrong_binding", revision=0)
+        self.assertFalse(private_path(selected_root).exists())
+        self.assertTrue(tree(private_path(original_root)) == original_before,
+                        "empty selected-root rejection changed original project evidence")
+        self.root = selected_root
+        _, _, selected_operator = self.bootstrap()
+        _, _, selected_owner, _ = self.acquire(selected_operator)
+        self.clear(selected_owner)
+        selected_revision = self.state()["revision"]
+        self.assertEqual(selected_revision, 2)
+        selected_before = tree(private_path(selected_root))
+        self.root = original_root
+        self.assertEqual(self.state()["revision"], 1)
+        self.response(self.apply(request, owner, root=selected_root),
+                      "wrong_binding", revision=selected_revision)
+        self.assertTrue(tree(private_path(selected_root)) == selected_before,
+                        "rejection changed selected project evidence")
+        self.assertTrue(tree(private_path(original_root)) == original_before,
+                        "rejection changed original project evidence")
+
+    def history(self, tag: str) -> tuple[list[tuple], dict[int, Path], Path]:
+        fresh, opened, operator = self.bootstrap()
+        operators = {0: self.retain(operator, f"{tag}-operator-zero.json")}
+        first, first_response, owner, operator = self.acquire(
+            operator, "manual", f"séance-{tag}", f"{tag}-acquire")
+        operators[1] = self.retain(operator, f"{tag}-operator-one.json")
+        released, released_response, operator = self.clear(
+            owner, request_id=f"{tag}-release")
+        operators[2] = self.retain(operator, f"{tag}-operator-two.json")
+        second, second_response, second_owner, operator = self.acquire(
+            operator, "supervised", f"séance-{tag}-extra", f"{tag}-acquire-extra")
+        operators[3] = self.retain(operator, f"{tag}-operator-three.json")
+        recovered = self.request(operator, "owner.recover", f"{tag}-recover", {
+            "reason": f"Explicit reconciliation {tag}", "reconciled_job_ids": []})
+        recovered_response = self.response(self.apply(recovered, operator), revision=4)
+        self.assert_transition(recovered, recovered_response, operators[3])
+        records = [(fresh, opened, None), (first, first_response, operators[0]),
+                   (released, released_response, owner),
+                   (second, second_response, operators[2]),
+                   (recovered, recovered_response, operators[3])]
+        self.assertNotEqual(owner, second_owner)
+        issued = [*operators.values(), operator, owner, second_owner]
+        digests = {hashlib.sha256(credential(path)["secret"].encode()).digest()
+                   for path in issued}
+        self.assertEqual(len(digests), len(issued), "issued secrets must be distinct")
+        return records, operators, operator
+
+    def test_canonical_receipts_replay_after_rotation_with_different_json_encodings(self) -> None:
+        parent = self.root
+        for tag in ("alpha", "alpha-extra"):
+            self.root = parent / tag
+            self.root.mkdir()
+            records, _, operator = self.history(tag)
+            before = tree(private_path(self.root))
+            for request, response, historical in records:
+                reordered = dict(reversed(tuple(request.items())))
+                reordered["payload"] = dict(reversed(tuple(request["payload"].items())))
+                raw = json.dumps(reordered, ensure_ascii=True, indent=3).encode()
+                self.assertNotEqual(raw, canonical(request))
+                actors = ((None,) if historical is None else
+                          (historical, operator) if request["operation"] != "owner.release"
+                          else (historical,))
+                for actor in actors:
+                    actual = self.response(self.apply(request, actor, raw=raw))
+                    self.assertEqual(actual, response)
+                    self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
+            recovered = records[-1][0]
+            for jobs in (["job-alpha", "job-beta"], ["job-alpha-extra", "job-beta-extra"]):
+                changed = recovered | {"payload": recovered["payload"] | {
+                    "reconciled_job_ids": jobs}}
+                self.reject_unchanged(changed, operator, "invalid_request")
+            self.assert_fresh_requests_validate_revision_payload_and_operation(operator, tag)
+            self.assertIsNone(self.snapshot()["owner"])
+
+    def test_retired_intermediate_operator_cannot_borrow_another_epochs_receipt_authority(self) -> None:
+        records, operators, current = self.history("authority")
+        before = tree(private_path(self.root))
+        for request, response, historical in (records[1], records[3], records[4]):
+            epoch = request["lease_epoch"]
+            self.assertEqual(self.response(self.apply(request, historical)), response)
+            self.assertEqual(self.response(self.apply(request, current)), response)
+            for retired_epoch, actor in operators.items():
+                if retired_epoch != epoch:
+                    self.reject_unchanged(request, actor, "wrong_binding")
+            self.reject_unchanged(request, None, "wrong_binding")
+            self.reject_unchanged(request | {"request_id": request["request_id"] + "-extra"},
+                                  historical, "wrong_binding")
+        self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
+        self.assertEqual(self.state()["lease_epoch"], 4)
+        self.assertEqual(set(self.state()["actors"]), {credential(current)["actor_id"]})
+        for request, _, historical in (records[1], records[3], records[4]):
+            for source in (historical, current):
+                self.assert_replay_rejects_changed_credential_bindings(request, source)
+        _, _, owner, operator = self.acquire(current, request_id="authority-current-owner")
+        wrong_release = self.request(operator, "owner.release", "authority-operator-release")
+        self.reject_unchanged(wrong_release, operator, "wrong_binding")
+        wrong_acquire = self.request(owner, "owner.acquire", "authority-owner-acquire", {
+            "mode": "manual", "native_session_id": "authority-wrong-role"})
+        self.reject_unchanged(wrong_acquire, owner, "wrong_binding")
+
+    def test_exact_receipt_replay_still_checks_credential_file_safety(self) -> None:
+        records, _, current = self.history("private")
+        for request, response, historical in (records[1], records[2], records[4]):
+            for index, source in enumerate((historical, current)):
+                if index and request["operation"] == "owner.release":
+                    continue
+                stem = f"{request['request_id']}-{index}"
+                valid = self.retain(source, stem + ".json")
+                self.assertEqual(self.response(self.apply(request, valid)), response)
+                forged = self.retain(source, stem + "-forged.json")
+                value = credential(forged)
+                value["secret"] = self.changed_secret(value["secret"])
+                forged.write_bytes(canonical(value))
+                self.reject_unchanged(request, forged, "wrong_binding")
+                invalid = self.base / (stem + ".json-extra")
+                invalid.symlink_to(valid)
+                self.reject_unchanged(request, invalid, "wrong_binding")
+                linked = self.base / ("prefix-" + stem + ".json")
+                os.link(valid, linked)
+                self.reject_unchanged(request, valid, "wrong_binding")
+                self.reject_unchanged(request, linked, "wrong_binding")
+                linked.unlink()
+                valid.chmod(0o644)
+                self.reject_unchanged(request, valid, "wrong_binding")
+                valid.chmod(0o600)
+                self.assertEqual(self.response(self.apply(request, valid)), response)
+                for raw in (b"", b"{}", b"{\"secret\":\"x\",\"secret\":\"y\"}"):
+                    invalid_copy = self.retain(source, stem + "-malformed.json")
+                    invalid_copy.write_bytes(raw)
+                    self.reject_unchanged(request, invalid_copy, "wrong_binding")
+
+    @staticmethod
+    def changed_secret(secret: str) -> str:
+        return ("A" if secret[0] != "A" else "B") + secret[1:]
+
+    def assert_replay_rejects_changed_credential_bindings(self, request: dict,
+                                                        source: Path) -> None:
+        original = credential(source)
+        changes = {"project_id": "0" * 64,
+                   "workflow_id": original["workflow_id"] + "-extra",
+                   "lease_epoch": original["lease_epoch"] + 1, "role": "owner"}
+        for field, replacement in changes.items():
+            with self.subTest(operation=request["operation"], credential_field=field):
+                forged = self.retain(source, f"binding-{field}.json")
+                forged.write_bytes(canonical(original | {field: replacement}))
+                self.reject_unchanged(request, forged, "wrong_binding")
+
+    def assert_fresh_requests_validate_revision_payload_and_operation(self, operator: Path,
+                                                                    tag: str) -> None:
+        stale = self.request(operator, "owner.acquire", f"{tag}-stale-acquire", {
+            "mode": "manual", "native_session_id": "stale-session"})
+        stale["expected_revision"] -= 1
+        self.reject_unchanged(stale, operator, "revision_conflict")
+        invalid = (({"reason": "", "reconciled_job_ids": []}, "invalid_request"),
+                   ({"reason": "é" * 2049, "reconciled_job_ids": []}, "invalid_request"),
+                   ({"reason": "Attended", "reconciled_job_ids": [1]}, "invalid_request"),
+                   ({"reason": "Attended", "reconciled_job_ids": ["job", "job"]},
+                    "invalid_request"),
+                   ({"reason": "Attended", "reconciled_job_ids": ["job"]},
+                    "rejected_evidence"))
+        for index, (payload, error) in enumerate(invalid):
+            with self.subTest(recovery_payload=index):
+                request = self.request(operator, "owner.recover", f"{tag}-invalid-{index}",
+                                       payload)
+                self.reject_unchanged(request, operator, error)
+        unknown = self.request(operator, "owner.unknown", f"{tag}-unknown-operation")
+        self.reject_unchanged(unknown, operator, "invalid_request")
+
+    def prepared_crash(self, name: str, tag: str) -> tuple[dict, Path]:
+        _, _, operator = self.bootstrap()
+        actor = operator
+        if name != "owner.acquire":
+            _, _, owner, operator = self.acquire(
+                operator, "supervised", f"session-{tag}", f"{tag}-initial-acquire")
+            actor = owner if name == "owner.release" else operator
+        payload = ({"mode": "manual", "native_session_id": f"session-{tag}-extra"}
+                   if name == "owner.acquire" else
+                   {"reason": f"Attended reconciliation {tag}", "reconciled_job_ids": []}
+                   if name == "owner.recover" else {})
+        return self.request(actor, name, tag, payload), actor
+
+    def assert_crash_completes_once(self, request: dict, historical: Path) -> None:
+        before = tree(private_path(self.root))
+        receipts = set(self.state()["receipts"])
+        intent = private_path(self.root) / "credential-intent.json"
+        if intent.exists():
+            changed = request | {"request_id": request["request_id"] + "-extra"}
+            self.reject_unchanged(changed, historical, "recovery_required")
+            for field, value in (("project_id", "0" * 64),
+                                 ("workflow_id", request["workflow_id"] + "-extra")):
+                changed = request | {field: value}
+                self.reject_unchanged(changed, historical, "wrong_binding")
+            self.assertTrue(tree(private_path(self.root)) == before, "private evidence changed")
+        completed = self.response(self.apply(request, historical),
+                                  revision=request["expected_revision"] + 1)
+        self.assert_transition(request, completed, historical)
+        self.assertFalse(intent.exists())
+        after = tree(private_path(self.root))
+        self.assertEqual(self.response(self.apply(request, historical)), completed)
+        if request["operation"] != "owner.release":
+            current = Path(completed["result"]["operator_actor_file"])
+            self.assertEqual(self.response(self.apply(request, current)), completed)
+        self.assertTrue(tree(private_path(self.root)) == after, "private evidence changed")
+        self.assertEqual(set(self.state()["receipts"]), receipts | {request["request_id"]})
+        self.snapshot()
+
+    @staticmethod
+    def response_objects(value: object) -> list[dict]:
+        # Locate contract-defined responses without assuming an intent field name.
+        if isinstance(value, dict):
+            responses = ([value] if set(value) == {
+                "ok", "revision", "result", "error_code", "retryable"} else [])
+            return responses + [response for item in value.values()
+                                for response in OwnerV2Test.response_objects(item)]
+        if isinstance(value, list):
+            return [response for item in value
+                    for response in OwnerV2Test.response_objects(item)]
+        return []
+
+    def tamper_pending_evidence(self, damage: str, request: dict,
+                               initial_paths: set[Path], index: int = 0) -> tuple[Path, bytes]:
+        root = private_path(self.root)
+        if damage == "response":
+            path = root / "credential-intent.json"
+            original = path.read_bytes()
+            value = json.loads(original)
+            responses = [response for response in self.response_objects(value)
+                         if response["revision"] == request["expected_revision"] + 1]
+            self.assertTrue(bool(responses), "intent must retain its complete response")
+            responses[index]["revision"] += 7
+        elif damage == "state":
+            path = root / "state.json"
+            original = path.read_bytes()
+            value = json.loads(original)
+            value["revision"] += 7
+        else:
+            stages = [path for path in (root / "actors").iterdir()
+                      if path not in initial_paths and path.is_file()
+                      and credential(path).get("role") == "operator"
+                      and credential(path).get("lease_epoch") == request["lease_epoch"] + 1]
+            self.assertEqual(len(stages), 1, "one staged operator credential is required")
+            path = stages[0]
+            original = path.read_bytes()
+            value = credential(path)
+            value["secret"] = self.changed_secret(value["secret"])
+        path.write_bytes(canonical(value))
+        return path, original
+
+    def assert_tampered_crash_preserves_evidence(self, name: str, damage: str,
+                                               parent: Path) -> None:
+        tag = f"{name}-tampered-{damage}"
+        self.root = parent / name / f"tampered-{damage}"
+        self.root.mkdir(parents=True)
+        request, actor = self.prepared_crash(name, tag)
+        historical = self.retain(actor, tag + "-historical.json")
+        initial_paths = set((private_path(self.root) / "actors").iterdir())
+        self.crash(request, actor, "intent_dir_fsynced")
+        intent = private_path(self.root) / "credential-intent.json"
+        probes = (len([response for response in self.response_objects(json.loads(intent.read_bytes()))
+                       if response["revision"] == request["expected_revision"] + 1])
+                  if damage == "response" else 1)
+        self.assertGreater(probes, 0, "intent must retain its complete response")
+        for index in range(probes):
+            with self.subTest(response_copy=index):
+                path, original = self.tamper_pending_evidence(damage, request, initial_paths, index)
+                self.reject_unchanged(request, historical, "recovery_required")
+                self.assertTrue(intent.exists())
+                path.write_bytes(original)
+        self.assert_crash_completes_once(request, historical)
+
+    def test_intact_owner_crash_evidence_finishes_and_replays_exactly_once(self) -> None:
+        parent = self.root
+        common = ("stage_fsynced", "intent_dir_fsynced", "operator_credential_published",
+                  "state_published", "cleanup_dir_fsynced")
+        for name in ("owner.acquire", "owner.release", "owner.recover"):
+            for damage in ("response", "staged-credential", "state"):
+                with self.subTest(operation=name, damage=damage):
+                    self.assert_tampered_crash_preserves_evidence(name, damage, parent)
+            boundaries = common + (("owner_credential_published",)
+                                   if name == "owner.acquire" else ())
+            for boundary in boundaries:
+                with self.subTest(operation=name, boundary=boundary):
+                    tag = f"{name}-{boundary}"
+                    self.root = parent / name / boundary
+                    self.root.mkdir(parents=True)
+                    request, actor = self.prepared_crash(name, tag)
+                    historical = self.retain(actor, tag + "-historical.json")
+                    state = self.state()
+                    self.crash(request, actor, boundary)
+                    if boundary == "stage_fsynced":
+                        self.assertEqual(self.state(), state)
+                    self.assert_crash_completes_once(request, historical)
+
+
+if __name__ == "__main__":
+    unittest.main()
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Exact command: mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_owner.py tests/autopilot/test_controller_owner_recovery.py tests/autopilot/test_controller_capacity.py tests/autopilot/test_controller_bootstrap.py tests/autopilot/test_controller_bootstrap_recovery.py tests/autopilot/test_controller_owner_v2.py -q --tb=line
Final after style fix: exit0,49passed in106.55s, subprocess timeout300. Final style/split gates exit0. Corrected original+new selected-root oracle tests:2passed in1.32s on canonical Python3.12. All prior scenarios retained; no skips/xfails or weaker auth checks. Full PRD review remains pending.


Judge only from this prompt: the diff above, the task text, and this recorded
result. Do not read other files, run commands, or re-run the tests. What is not
in this prompt is not evidence, and a finding you cannot ground in what is here
is one you should not report.

# Simplification Mandate (step 5.7 reviewer-prompt appendix)

Append this block **verbatim** to every per-task code-reviewer prompt (see
`SKILL.md` step 5.7). It ships inside the prompt, so it must stay
self-contained.

> Beyond bugs, actively hunt for simplification in the diff under review. For
> every added or changed file, ask "what would make this simpler to read
> without changing what it does?" and flag concrete behavior-preserving
> opportunities to: reduce complexity (needless indirection, dead branches,
> single-caller abstractions, nesting deeper than 4 levels, functions over 50
> lines); eliminate redundancy (logic duplicated within the diff or against
> existing code, a helper that reimplements a stdlib or existing utility);
> improve naming (names that state intent, no opaque abbreviations); and
> remove dead code. Follow CLAUDE.md / AGENTS.md conventions and the
> surrounding code's style.
>
> Report each concrete behavior-preserving simplification as a LOW finding,
> with file:line, the current shape, and the simpler replacement. LOW findings
> are carried to the PRD-level review, never retried here.
>
> Do not over-simplify: never propose a change that trades clarity for
> brevity, drops error handling, collapses a deliberate boundary, or removes a
> documented invariant. Simpler means easier to read and maintain, not shorter
> at any cost. If a change would alter behavior, it is out of scope — do not
> flag it.


## Reporting contract

Report one finding per line, in exactly this shape:

SEVERITY | file:line | issue | fix

Severities are CRITICAL, HIGH, MEDIUM, LOW.

Severity has a fixed meaning here, and it decides what happens next. MEDIUM is
reserved for a correctness or security defect this diff introduces that its own
tests do not catch: a wrong result, an unhandled error path, data loss,
injection, secret exposure, or a missing authorization check. Style, naming,
duplication, structure and maintainability are LOW, and so is every
behavior-preserving simplification, whatever its size. A LOW is noted and
carried to the PRD-level review; it is never retried in this loop.

If the diff has no findings, emit the literal line:

NO FINDINGS

## Closure verdicts (only when the description carries a findings block)

When the Description above contains a `### Findings (verbatim)` block, this is
a rework task and each quoted finding is a claim to check. Before your findings
lines, emit one verdict per quoted finding, in this shape:

CLOSURE | resolved|unresolved | <the finding, quoted> | <one line of evidence from the diff>

Judge each finding against the diff, not against the commit message and not
against how clean the code reads. A diff that improves the file while leaving
the quoted defect reachable is `unresolved`. Quote the line that resolves it,
or say what still reaches the defect. Emit a verdict for every quoted finding,
including ones you judge already fixed elsewhere.


