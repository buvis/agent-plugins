# AP00018 implementation assumptions

## 1: Freeze pinned controller ownership, schemas and fixtures

- actors is keyed by actor ID; descriptors use secret_digest.
- Receipts contain request_digest, authorizing_actor and response.
- Operator descriptors have null native_session_id.
- Release/recover results contain actor_id, operator_actor_file and lease_epoch.
- Deferred capability IDs use workflow.<family>.v1.
- Core apply responses and snapshot/contract projections have separate schemas.
