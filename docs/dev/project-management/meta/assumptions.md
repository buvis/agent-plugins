# AP00018 implementation assumptions

## 1: Freeze pinned controller ownership, schemas and fixtures

- actors is keyed by actor ID; descriptors use secret_digest.
- Receipts contain request_digest, authorizing_actor and response.
- Operator descriptors have null native_session_id.
- Release/recover results contain actor_id, operator_actor_file and lease_epoch.
- Deferred capability IDs use workflow.<family>.v1.
- Core apply responses and snapshot/contract projections have separate schemas.

## 6: Implement bounded CLI bootstrap, snapshot and matching-intent recovery

- Tess: crash labels correspond to observable credential-file and directory fsync boundaries.
- Tess: snapshot assertions cover only explicitly named public fields and redaction.
- Ivan: snapshot actors use ID/role rows; capacity uses remaining byte/receipt counters because no complete snapshot schema is declared.
