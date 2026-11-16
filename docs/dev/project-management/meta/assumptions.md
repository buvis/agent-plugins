# Assumptions ledger (batch 202611151706, PRD 00019)

## 1: Extend controller schema.py for lifecycle/tasks/jobs shapes

- (Tess) `role`, `isolation`, `tier` and `effort` accept any non-empty string; fixtures used "builder", "reviewer", "tester", "worktree", "opus", "high".
- (Tess) `input_digests` entries assumed to be 64-char lowercase hex.
- (Tess) `claimed_by`/`claim_epoch` kept paired in fixtures: (None, None) or (non-empty string, nonnegative int).
- (Tess) `exit_fact` content not specified; fixtures use only `None`.
- (Tess) `attempts` element shape not specified; fixtures use only `[]`.
- (Tess) `depends_on` in fixtures only points to ids existing in the same list; dangling/duplicate references untested.
- (Tess) rejections checked as `schema.SchemaError` (which `ResourceLimitError` subclasses).
- (Ivan) task ids, job ids, dependency entries and `claimed_by` use the existing `_identity` check (non-empty, <=256 UTF-8 bytes) rather than "any string".
- (Ivan) `input_digests` entries must be 64-character lowercase hex digests (`_digest`) rather than any string.
- (Ivan) free-text fields (`subject`, `role`, `isolation`, `tier`, `effort`, `prd`, `entered_at`, `phase`, `completed_phases`/`completed_prds` entries, `lane`, `lane_reason`, `op`, `boundary`) must be non-empty strings; no format check on `entered_at`, no fixed enum for `phase`/`lane`/`tier`/`effort`.
- (Ivan) `attempts` contents not checked beyond being a list; task/job id uniqueness, `depends_on` referential integrity, and `claimed_by`/`claim_epoch` pairing are not enforced by the schema layer.
- (Devon/orchestrator ruling) `op`/`boundary` have no fixed enum; only "non-empty string" is enforced.
