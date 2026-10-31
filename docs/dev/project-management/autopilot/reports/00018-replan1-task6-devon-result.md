Task6 broken: eight cumulative adversarial variants passed all 20 tests.

Wrong implementation excerpts:

```python
# 1: Universally predictable credential.
secret = "A" * 43

# 2: Identity depends only on the public project path hash.
workflow_id = "workflow-" + pid[:16]
actor_id = "actor-" + pid[:16]

# 3: Other credential bindings are ignored.
if (set(credential) != CREDS
        or credential.get("secret") != "A" * 43
        or credential.get("actor_id") != actor_id):
    reject()

# 4: Only the exact tested oversized length is rejected.
if len(raw) == 2097153:
    reject()

# 5: Only the exact invalid identity fixtures are rejected.
if request_id in {"", "x" * 257, "é" * 129}:
    reject()

# 6: Additional operation suffixes silently become workflow.open.
if operation.startswith("workflow.open") and operation != "workflow.open-extra":
    operation = "workflow.open"

# 7: State contents are never fsynced.
if path.name != "state.json":
    os.fsync(handle.fileno())

# 8: Public contract command is unavailable.
if command == "contract":
    raise SystemExit(2)
```

Actual narrow-run evidence, one run per variant:

```text
1. 20 passed in 8.79s
2. 20 passed in 8.49s
3. 20 passed in 8.49s
4. 20 passed in 8.47s
5. 20 passed in 8.44s
6. 20 passed in 8.48s
7. 20 passed in 8.48s
8. 20 passed in 8.46s
```

One initial attempt failed: `4 failed, 16 passed in 8.80s`. The tests caught concurrency setup races, incorrect fresh-request conflict handling, and acceptance of the supplied oversized integer. Those were repaired before the eight passing variants.

Weak points:

1. `test_bootstrap_publishes_one_private_operator_state_and_receipt` — every operator receives the same known secret — assert independently generated secrets differ; inject deterministic entropy failures where practical.
2. `test_bootstrap_publishes_one_private_operator_state_and_receipt` — identities are deterministic functions of the project path — test independent bootstraps at the same canonical path produce new workflow and actor identities, if identity renewal is required.
3. `test_credentials_reject_wrong_permissions_symlinks_hardlinks_and_secrets` — credentials with changed project, workflow, role, epoch, or native-session bindings authenticate — mutate each credential binding individually and require `wrong_binding` without writes.
4. `test_request_byte_and_utf8_identity_limits_accept_the_exact_boundary` — requests larger than the limit by two or more bytes are accepted — exercise several oversized lengths, including substantially oversized requests.
5. `test_strict_envelope_rejections_happen_before_store_creation` — only its exact overlong request-ID strings are rejected — parameterize varied ASCII and multibyte strings across the UTF-8 boundary.
6. `test_strict_envelope_rejections_happen_before_store_creation` — untested `workflow.open` suffixes execute successfully — generate multiple unknown operation names and require `invalid_request` without writes.
7. `test_bootstrap_recovers_exactly_once_at_every_declared_crash_boundary` — state is published without syncing its file contents — instrument filesystem calls and assert state-file fsync precedes its publication/directory durability boundary.
8. CLI suite — the declared `--json contract` interface exits two unconditionally — invoke it and assert successful, valid contract output.

Cleanup complete. The only candidate path touched was:

`/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/autopilot/controller/main.py`

It now contains exactly:

```python
# adversarial placeholder - overwritten by implementor
```

No test/dependency edits, commits, or task-state writes. `protocol.py` and `actors.py` were untouched.