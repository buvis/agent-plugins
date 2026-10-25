# Cardinal sins

The one shared list: the pre-pass reviewer receives it in full, and the walkthrough checks it at every tier.

- [SR-RVD-052] Each item below is a blocker whatever the justification, because getting it wrong has an asymmetric and usually irreversible cost. A cardinal sin is walked first, before any other severity, and it blocks the design approval until it is fixed or the developer disputes it with a reason recorded in the minutes.
- [SR-RVD-053] No rollback plan for a stateful change.
- [SR-RVD-054] Secrets in configuration files, plaintext environment variables, or source code.
- [SR-RVD-055] A single point of failure on a write path, without explicit acceptance and justification.
- [SR-RVD-056] No identified human owner for production operation.
- [SR-RVD-057] No observability for user-visible operations: no way to know that it is broken.
- [SR-RVD-058] "We will figure it out later" attached to a load-bearing concern (security, data integrity, observability, compliance).
- [SR-RVD-059] Unbounded resource consumption with no limit, quota, or backpressure.
- [SR-RVD-060] A schema change without a migration plan.
- [SR-RVD-061] Vendor lock-in for critical infrastructure without an exit strategy.
- [SR-RVD-062] Authentication or authorisation deferred to a later phase.
- [SR-RVD-063] Data deletion, correction, or export with no defined path (the compliance trap).
- [SR-RVD-064] Persistent data without a backup and a tested restore procedure.
- [SR-RVD-065] A public API contract without a versioning strategy.
- [SR-RVD-066] Hardcoded credentials, keys, or tokens anywhere in the design or the code it references.
- [SR-RVD-067] A critical decision made by acclamation, without recorded alternatives or rationale.
