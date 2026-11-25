# Assumptions ledger (batch 202611242306, PRD 00019)

> Tasks 1-11 of this plan ran in earlier sessions that did not append to this
> ledger, so their implementors' `ASSUMPTIONS:` lines were not captured. Only
> task 12's are recorded below. The file previously held batch 202611160843 /
> PRD 00067 entries and was replaced per the per-plan ledger rule.

## 12: Refresh delivery evidence for final package bytes

- (Ivan) The six paths added to the AP00018 v2 successor receipt's `paths` list are the complete delta; confirmed against the regenerated map's controller rows and the controller directory listing rather than trusting the task's enumeration alone.
- (Ivan) Keeping each receipt task's `passed` count unchanged is correct because the fresh runs returned the same numbers (89/71/48/79); only the `duration_seconds` values differ.
- (Ivan) The two pre-commit `test_package.py` failures were out of scope to force green in the work tree, since `TargetPackageTest.setUpClass` builds from `git archive HEAD` and the only fix is the orchestrator's commit; `plugins/` and the frozen inventory were left untouched.

## 17: [D2] controller state package - entry metadata, start evidence, job metadata, saga replay, park pause (review cycle 2)

- (Tess) `plan_expansion` and `default_model` values are captured verbatim, so the tests use `allow`/`deny` and `opus`/`sonnet` literals; an implementation that validates an enum would need them changed.
- (Tess) `source_digest` is `sha256(canonical(stored task row))` including the row's `attempts: []` key, with `canonical` as `controller_cli_support.canonical`.
- (Tess) Derived `job_id` naming is unpinned, so derived-plan tests key on digests and counts, never on job ids.
- (Tess) `job.plan` must still derive specs when `work.phase` is `review`, which is what proves the requirements are phase-dependent.
- (Tess) `workflow.pause` is read tolerantly (`workflow.get("pause")`), so an unpaused workflow may omit the key or hold `None`.
- (Tess) `resume_target`'s paused answer is pinned only by containing "reconcil", the site and the PRD name, plus differing from the unpaused answer.
- (Tess) The unreadable-PRD case uses `chmod 0o000`, which assumes the suite does not run as root.
- (Tess) `A8`'s `prd_digest` is the lowercase sha256 hex of the PRD file's raw bytes.
- (Tess) `files.park` performs every state write through `store.transaction`, so wrapping the store is a faithful crash injection for the pause-atomicity test.
- (Ivan) `replayed: True` for a proven replay is a dispatcher-level fact (a `PROVEN_REPLAY` sentinel from `apply_locked` plus `apply_unlocked(replay=...)`), chosen so the pre-existing direct-`apply_unlocked` assertion in `test_controller_rework13_recovery.py` keeps its original-result semantics.
- (Ivan) A derived `job.plan` with no active `work` raises `rejected_evidence`, because neither the requirements nor the resource digest can be derived without an active PRD.
- (Ivan) `policy.job_requirements` raises `KeyError` for a phase other than `build`/`review` (closed vocabulary), and an unknown tier string falls back to `effort: "medium"`.
- (Ivan) A final-location byte mismatch after the verified rename raises `files.RecoveryRequiredError`; the amendment mandates the check but names no public code and no test exercises it.
- (Ivan) `start_commit` is whatever `git rev-parse HEAD` prints, unfiltered, so a sha256 repository would fail schema validation at commit time rather than record `None`.
- (Ivan) `_head_commit` uses a 30 s timeout, mirroring `lifecycle.evaluate`.
- (Ivan) The operation-to-ledger-kind map for the replay admission lives inline in `protocol.proven_replay`, since `files.py` speaks in saga kinds.
- (Ivan) `recorded_request` reads `payload["prd"]` directly and `site`/`detail`/`record` with `.get`, relying on `validate_saga_payload` having already closed the payload shape.

## 18: [D2] tests/autopilot/ (review cycle 2)

- (Ivan) Digest fillers for the new job-spec keys are synthetic 64-char lowercase hex and `permitted_operations` is `["read", "write"]`; the findings only asked for realistic values.
- (Ivan) "Cover the new receipt shape" for `job.next` is read as full parity with the other twelve operations (real dispatch, exact result equality, `WORKFLOW_RESULTS` membership, per-field corruption rejection), which forced the 12 -> 13 rename of the dispatch test.
- (Ivan) The entry-recovery "interruption point" is a crash between the committed rename and the published entry, injected through the store's existing `boundary_hook` at `STATE_TEMP_FSYNCED` - the only interruption that leaves the original request's `expected_revision` valid and therefore literally replayable.
- (Ivan) The review's `source: "backlog"` expectation was replaced by the shipped `source: "wip"`: `lifecycle.enter` selects wip-first and nothing records the interrupted attempt's origin bucket. Recorded as a controller gap in the batch deferred JSON instead of patched.
- (Ivan) Driving task `a` to `completed` in `_dispatch_prd_lifecycle` uses `task.start` + `task.finish`, deliberately not appended to `checks`, so the `set(WORKFLOW_RESULTS)` assertion keeps its meaning.
- (Ivan) "Public dispatch path" means the owner-CLI `protocol.apply` route `OwnerCLITest` wraps, with `reject_unchanged(..., "rejected_evidence")` as the harness-blessed rejection assertion across the CLI boundary.
