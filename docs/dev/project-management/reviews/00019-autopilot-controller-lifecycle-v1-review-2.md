---
prd: docs/dev/project-management/prds/wip/00019-autopilot-controller-lifecycle-v1.md
review: 2
date: 2026-11-25
head_sha: 24f3a4a4ba7a04517b9be066b5f9ab478a125c9e
codex_thread_id: 01a21036-d960-7f42-8f24-82f0f2f24c19
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: dbca184c
  carl: 4ae9a4a8
---

# Review: 00019-autopilot-controller-lifecycle-v1 (cycle 2)

Diff range: `b725abf75ac118662695d95086af0a592d72a8d3..24f3a4a4ba7a04517b9be066b5f9ab478a125c9e`

codex_rung_guard: not fired

## Review Summary

Reviewed: 16 completed tasks (incremental review of the cycle-1 rework, tasks 13-16)
PRDs checked: 00019-autopilot-controller-lifecycle-v1.md

### Agent Status

- Alice: available (consensus lens, native subagent)
- Blake: available (blind lens, PRD-only)
- Bob: available (doubt lens + de-slop, codex, resumed thread 01a21036-d960-7f42-8f24-82f0f2f24c19)
- Carl: available (gemini via copilot backend, model gemini-3.8-flash). His cycle-1 output was discarded for copying another reviewer; this cycle his prompt carried an explicit independence requirement and his five findings are his own (two of them, the assertion-free tests, nobody else raised in those words). His voice counts this cycle, so consensus denominators are `/4`.

Consolidation ran via `consolidate_findings.py` over ALICE, BLAKE, BOB, CARL with `--ledger` and `--ledger-dismiss BLAKE`. The consolidator merged six row groups only after citation-suffix stripping (lifecycle.py:327~329~335, workflow-v1.json:173~132, tasks.py:96~85, lifecycle.py:106~92, protocol.py:365~369, protocol.py:346~343); each merge was checked by hand and kept. The engram context pack built cleanly (`pack: ok`). `review-stage` reported no errors.

### Mechanical checks

Both tautological-shape findings and all five fail-first replay findings were absorbed into rows that already name the same test or test file: R37 and R38 (no-assertion tests), and R31, R32, R33, R34, R35 (touched tests that pass against the pre-change code). Each of those seven rows therefore carries `mech-check` as a second voice.

### Test gate provenance (read this before the Tests line)

`review-stage` ran the full suite once at HEAD and its parser could not read pytest's summary, so it emitted `Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)`. The parser expects the counts line to begin with `N passed`; this suite ended `5 failed, 2118 passed in 837.52s`, where `failed` comes first. The counts in the `Tests:` line below are read verbatim from that same run's log, `docs/dev/tmp/gate-00019-c2.log:159`. The suite was **not** run a second time: a `autopilot verify` rerun would feed the identical output to the identical parser.

The five failures are the central finding of this cycle, not an environment gap:

- `test_controller_protocol.py::test_bundle_shape_and_implemented_only_advertisement`
- `test_controller_protocol.py::test_contract_examples`
- `test_controller_protocol.py::test_kernel_defaults_and_deferred_families`
- `test_controller_recovery_characterization.py::test_kernel_tasks_cannot_be_populated`
- `test_controller_rework13_lifecycle.py::test_bypass_review_via_handoff_converged_is_rejected_without_evidence`

Cycle 1 ran 2097 passed, 0 failed on the same interpreter and the same pinned requirements. Alice, Blake and Carl independently traced the first four to the cycle-1 rework widening `workflow.tasks`/`workflow.jobs` to `maxItems: 256` with no `items` schema, and widening `bundle.operations`/`bundle.capabilities`, so the schema now accepts exactly what those tests assert it rejects. The "known jsonschema environment gap" recorded in `autonomous_decisions` during the rework is therefore **wrong** and is reopened as R7/R13. The fifth is the cycle-1 R3 review-acceptance bypass, carried as a committed red test (R10/R19).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟡 | Prior R1 is only partly resolved. Only `rework_cap` is persisted. The start commit is not captured, and the parser's `_warnings`, `defaults` and `overwrite_warnings` stay unused. The deviation is recorded only in a test comment and a docstring, not in a PRD or design note. `_frontmatter_work_fields` swallows `OSError` and `UnicodeDecodeError` into empty text, so an unreadable PRD silently enters with default values. That is an unreported error path. The function-local `from . import frontmatter` is redundant if `lifecycle.py` already imports from `frontmatter` at module level. | plugins/autopilot/controller/autopilot_state/lifecycle.py:327 | 13 | ALICE, BLAKE, CARL |
| R2 | [2/4] | 🟠 | Prior R10 is only partly resolved. `batch`, `work` and `recovery` are still `{"type":"null"}` (lines 134-138, 157). The workflow object has `additionalProperties:false` (line 173), but the rework added a persisted `workflow.pause` and a `work.rework_cap` key. A state produced by `prd.enter` or a second park therefore violates the published schema. The new tests only check the `maxItems` keyword, never a real state against the schema. | plugins/autopilot/contracts/controller/workflow-v1.json:173 | 13 | ALICE, CARL |
| R3 | [2/4] | 🟠 | Prior R14 is only half fixed. `finish` skips the epoch check when `start_epoch` is absent. A task submitted via `task.replace` with `status: in_progress` has no `start_epoch`, so it can still be finished. Worse, `schema._task` now permits a caller-supplied `start_epoch` inside `task.replace` items, so start evidence can be forged. Strip or reject `start_epoch` in `task.replace` and refuse `finish` when it is missing. Only the earlier-lease case is tested. | plugins/autopilot/controller/autopilot_state/tasks.py:96 | 13 | ALICE, BOB |
| R4 | [2/4] | 🟠 | Completion can be reached without any review evidence. `phase.handoff` accepts `tasks_done`, `rework` and `converged` from any authenticated actor, and `converged` marks `review` completed. `prd.complete` only checks `phase == done` and `"review" in completed_phases`. `test_manual_session_handoff` does exactly this: tasks_done, rework, converged, then complete, with no review record. The spec says completion moves "after accepted review" and "prose or exit zero cannot bypass review". The Risks section says review acceptance is unavailable until AP 00020, so a bare assertion currently stands in for acceptance. `false_success_no_advance` therefore only proves the refusal when the phase handoffs were skipped. | plugins/autopilot/controller/autopilot_state/lifecycle.py:106 | Phase 1 task 1 / Phase 2 task 1 | BLAKE, CARL |
| R5 | [2/4] | 🟡 | Fabricated job digests and permissions. `_with_job_defaults` sets `source_digest` and `resource_digest` to `sha256("source:<job_id>")` and `sha256("resource:<job_id>")`. These are not digests of any source or resource, so they are placeholder data presented as evidence. It also defaults `permitted_operations` to `["read","write"]`, which is a permissive default. `_derive_job_specs` hardcodes `role=builder`, `tier=opus`, `effort=high` and `isolation=worktree` for every task, ignoring policy and lane. Require callers to supply the digests and permissions, or derive them from real inputs. | plugins/autopilot/controller/autopilot_state/protocol.py:365 | 13 | ALICE, BLAKE |
| R6 | [2/4] | 🟡 | `job.next` returns only `{job_id, instruction: "run job X (role)"}`. This is not a "structured standalone next-job instruction". It omits role details, dependency IDs, digests, isolation, tier/effort and permitted operations. A fresh session must read the whole snapshot. | plugins/autopilot/controller/autopilot_state/protocol.py:346 | Phase 1 task 2 | BLAKE, BOB |
| R7 | [1/4] | 🟠 | Rework regression: 4 previously green tests now fail. The `tasks`/`jobs` schema nodes are only `{"type":"array","maxItems":256}` with no `items` schema, so a populated array of junk passes. `bundle.operations` (20 entries) and `bundle.capabilities` (open enum) were widened. `job.next` was added to `implemented_operations` with no valid or invalid fixture, so `test_contract_examples` fails on that too. The old tests (`test_bundle_shape_and_implemented_only_advertisement`, `test_kernel_defaults_and_deferred_families`, `test_contract_examples`, `test_kernel_tasks_cannot_be_populated`) were not updated and the schema was not tightened. Add `items` schemas for task and job rows, add `job.next` fixtures, and update the bundle test to the full runtime set. | plugins/autopilot/contracts/controller/workflow-v1.json:140 | 13 | ALICE |
| R8 | [1/4] | 🟠 | The prior R11 fix is unreachable through the public API. The retry path in `apply_unlocked` only runs after `apply_locked`, and `apply_locked` calls `authorize` for saga operations. `authorize` raises `revision_conflict` for any stale `expected_revision` that has no cached receipt. A retry after a crash between the saga commit and the receipt therefore never reaches the new `_replay_committed` logic. The test calls `apply_unlocked` directly and bypasses `authorize`. Prove it through `protocol.execute`, or move the replay check into `authorize`. | plugins/autopilot/controller/autopilot_state/protocol.py:481 | 13 | ALICE |
| R9 | [1/4] | 🟠 | The same change weakens optimistic concurrency in the TOCTOU window. A stale revision (the state changed between lock release and re-read) no longer short-circuits to `revision_conflict`. The saga now runs against the newer state whenever its own preconditions still hold. `revision_conflict` is raised only if the saga throws `PreconditionError`, `RecoveryConflictError` or `DeferredRecordConflictError`. This undercuts the R12 admission-guarantee fix. | plugins/autopilot/controller/autopilot_state/protocol.py:481 | 13 | ALICE |
| R10 | [1/4] | 🟠 | The prior R3 review-acceptance bypass is deferred, and a committed red test records it. A deferral is defensible: the PRD says acceptance is unavailable until AP00020. But a known-red test in the gate suite breaks CI and tracks nothing durable. Either fix it (reject `review`→`done` `converged` while no review evidence exists, which is what the PRD literally says), or mark the test strict xfail with an AP00020 reason and record the deferral in the PRD or an issue. The test body (`try/except` with an early `return`) also lets either outcome through, which is a hedge shape. | tests/autopilot/test_controller_rework13_lifecycle.py:1725 | general | ALICE |
| R11 | [1/4] | 🟠 | `job.plan` boundary validation regressed. `_validate_caller_job_spec` checks only the seven base keys. A caller spec with a malformed `source_digest`, `resource_digest` or `permitted_operations`, or with unknown keys, passes `validate_reducer_payload`. I confirmed this with a probe. The failure then happens at commit-time `schema._job`. `apply_locked` maps that `SchemaError` (a `ValueError`) to `recovery_required`, so plain bad input now looks like a recovery state. Validate the optional keys and reject unknown keys in `validate_payload`. | plugins/autopilot/controller/autopilot_state/protocol.py:115 | 13 | ALICE |
| R12 | [1/4] | 🟠 | The prior R13 `workflow.pause` is write-only. `prd.enter` rejects forever once it is set. No operation (`owner.recover`, `prd.*`, etc.) clears it and no read projection shows it. The batch can never resume. It is also absent from the published schema (see above). Add a clearing path, or document pause as terminal. | plugins/autopilot/controller/autopilot_state/files.py:591 | 13 | ALICE |
| R13 | [1/4] | 🟠 | The Phase 2 exit criterion (full `tests/autopilot` pytest passes) fails at HEAD. Three tests in `test_controller_protocol.py` fail: `test_bundle_shape_and_implemented_only_advertisement`, `test_contract_examples` and `test_kernel_defaults_and_deferred_families`. Their `assert_invalid` calls now find no schema error. The first still expects a bundle with `job.plan` or `workflow.jobs.v1` to be invalid, but `contracts/controller/workflow-v1.json:1342-1385` now allows both. Either the schema or fixture edits and these tests drifted apart, or the tests were never updated. This matches the test gate's exit 1. | tests/autopilot/test_controller_protocol.py:393 | Phase 2 task 2 | BLAKE |
| R14 | [1/4] | 🟠 | `build -> review` (`tasks_done`) does not check that tasks are completed. `lifecycle.apply` applies the row regardless of `workflow.tasks` status, so an actor can skip pending tasks. | plugins/autopilot/controller/autopilot_state/lifecycle.py:118 | Phase 1 task 1 | BLAKE |
| R15 | [1/4] | 🟠 | `apply_unlocked` now runs a saga even when the admitted revision is stale. A fresh stall, park, or defer can read the newer state and mutate it after the original authorization has expired. Validate the admitted revision and actor when staging the intent. Allow stale requests only after a read-only lookup proves they match a durable intent or receipt. | plugins/autopilot/controller/autopilot_state/protocol.py:467 | 13 | BOB |
| R16 | [1/4] | 🟠 | The new crash-replay test calls `apply_unlocked` directly and skips `authorize`, which still rejects the original stale request before replay can start. The ledger fallback also lacks the original request digest and excludes entry and completion. Bind recovery to the authenticated request and commit its receipt before clearing the marker. Test retries through the public dispatcher. | plugins/autopilot/controller/autopilot_state/protocol.py:285 | 13 | BOB |
| R17 | [1/4] | 🟠 | The second park clears its recovery marker before persisting `systemic_park`. A crash leaves the batch unpaused, and a concurrent entry can start another PRD in that gap. Commit the pause with the park counter and work reset in the existing bookkeeping transaction. | plugins/autopilot/controller/autopilot_state/files.py:578 | 13 | BOB |
| R18 | [1/4] | 🟠 | Entry now captures `rework_cap` alone. It still omits the start commit, effective task tier, and plan-expansion policy. The metadata read also precedes the verified move, so it can capture a different file from the one moved. Capture the required metadata from the verified PRD and preserve it in a staged entry intent. | plugins/autopilot/controller/autopilot_state/lifecycle.py:329 | 13 | BOB |
| R19 | [1/4] | 🟠 | The reported review regression still fails, and the new receipt test relies on that same unsupported `converged` handoff to complete a PRD. Keep completion unavailable until accepted evidence exists. Assert through the public dispatcher that an unsupported convergence claim changes neither phase nor bucket. | tests/autopilot/test_controller_rework13_lifecycle.py:84 | 13 | BOB |
| R20 | [1/4] | 🟠 | Job enrichment hashes labels derived from the job ID and presents them as source and resource digests. The derived plan also schedules every task regardless of status and hardcodes role, tier, effort, and permissions. Use actual digests and derive job requirements from phase, tasks, policy, and accepted results. Test that changing those inputs changes the plan where required. | plugins/autopilot/controller/autopilot_state/protocol.py:369 | 13 | BOB |
| R21 | [1/4] | 🟠 | State saved by cycle 1 with a populated job plan now fails validation because stored jobs require three new fields. Request-time enrichment cannot repair state that fails to load. Preserve compatibility for existing rows and require real metadata before offering those jobs for execution. | plugins/autopilot/controller/autopilot_state/schema.py:315 | 13 | BOB |
| R22 | [1/4] | 🟡 | `job.next` is incomplete and under-tested. There is no request or response schema entry, no fixture, and no CHANGELOG or doc mention. The result is only `{job_id, instruction}`, with no readiness, digests or permitted operations. The one test covers a single job with no dependencies. The dependency-blocked skip and the all-claimed and all-blocked rejection are untested. It is read-only but goes through the mutating reducer path, so every poll bumps the revision and writes a receipt. | plugins/autopilot/controller/autopilot_state/jobs.py:52 | 13 | ALICE |
| R23 | [1/4] | 🟡 | Weak or tautological rework tests. `test_workflow_schema_permits_an_empty_tasks_or_jobs_array_too` is true before and after the change, because it reads `minItems` with a default. The `maxItems` tests use `.get(..., default)` and never validate a real state. The finding-10 test accepts any of four exception types (`pytest.raises((RevisionConflictError, RecoveryConflictError, PreconditionError, RecoveryRequiredError))`). Its name, `test_stall_does_not_recheck_revision...`, says the opposite of what it asserts. The finding-2 test passes against the pre-change code because no code changed for it. Test files are named by task number (`rework13_*`) rather than by the rule they enforce. | tests/autopilot/test_controller_rework13_contracts.py:22 | 13 | ALICE |
| R24 | [1/4] | 🟡 | Claims have no scope or role check beyond "any registered actor". Operator and owner can both claim, and `claim_epoch` is the actor's lease epoch. The spec's "one valid claim per job/epoch" holds only as "one claim per job ever": a re-planned job at a later epoch cannot be reclaimed. There is no claim-release or reclaim path other than `owner.recover` (not verified to reset claims). | plugins/autopilot/controller/autopilot_state/jobs.py:63 | Phase 1 task 2 | BLAKE |
| R25 | [1/4] | 🟡 | `job.plan` has no active-PRD or phase precondition. It also accepts caller-supplied digests and permitted operations unvalidated against any source, and it allows an empty `jobs` list to trigger derivation as a side channel. | plugins/autopilot/controller/autopilot_state/protocol.py:341 | Phase 1 task 2 | BLAKE |
| R26 | [1/4] | 🟡 | The contract rework only loosens array lengths and bundle enumeration. It still disagrees with runtime state and adds no request, result, or fixture for `job.next`. Define the new shapes and validate real persisted state and dispatcher responses against the installed schema. | plugins/autopilot/contracts/controller/workflow-v1.json:139 | 13 | BOB |
| R27 | [1/4] | 🟡 | `owner.recover` still rejects jobs with a recorded exit because their `claimed_by` remains set. The updated README implies an operator can finish jobs and then recover ownership. Permit recovery when every claim has an exit fact and retain the guard for outstanding claims. | plugins/autopilot/controller/autopilot_state/owner.py:275 | 13 | BOB |
| R28 | [1/4] | 🟡 | The new committed-replay path rebuilds ledger rows independently of `_ledger_item`. Use the same builder for append and comparison so a record format change cannot break replay. | plugins/autopilot/controller/autopilot_state/files.py:500 | 13 | BOB |
| R29 | [1/4] | 🟡 | The exporter now duplicates the expanded operation and capability lists. Read them from the controller contract metadata already packaged with the schema and retain the installed-bundle parity test. | tools/autopilot/export-controller-contract.py:32 | 15 | BOB |
| R30 | [1/4] | 🟡 | The mechanical check flags the valid JobSpec test and the earlier-epoch refusal test for lacking direct assertions. Assert persisted job metadata in the first test and the unchanged task state after rejection in the second. | tests/autopilot/test_controller_rework13_jobs.py:100 | general | BOB |
| R31 | [2/4] | 🟡 | The empty-array contract test passes on the base and inspects only `minItems`. Pair an actual valid empty state with a malformed populated state and validate both against the shipped schema. | tests/autopilot/test_controller_rework13_contracts.py:45 | 13 | BOB, mech-check |
| R32 | [2/4] | 🟡 | Five job tests pass on the base. The three missing-field cases can pass because the base rejects the other added fields, and the two empty-state cases exercise existing behavior. Pair each missing-field case with a valid control and use the empty cases as controls for derivation and owner recovery with a populated plan. | tests/autopilot/test_controller_rework13_jobs.py:63 | 13 | BOB, mech-check |
| R33 | [2/4] | 🟡 | The entry recovery test passes on the base because it renames the file itself and retries with a fresh request. Drive the actual entry operation to the interruption point and assert replay of the original request preserves `source: backlog` and commits once. | tests/autopilot/test_controller_rework13_lifecycle.py:52 | 13 | BOB, mech-check |
| R34 | [2/4] | 🟡 | The same-epoch success test passes on the base because it checks only final status. Assert that start persists the authorizing epoch before finishing. | tests/autopilot/test_controller_rework13_recovery.py:164 | 13 | BOB, mech-check |
| R35 | [2/4] | 🟡 | The expanded receipt-dispatch test passes on the base and omits this cycle’s new `job.next` result. Cover the new receipt shape while it exists, or validate the new response directly if the query moves to a read-only projection. | tests/autopilot/test_controller_schema_lifecycle.py:455 | 16 | BOB, mech-check |
| R36 | [1/4] | 🟡 | The supplied suite reports 2,118 passed and five failed, including four schema rejection failures described as an environment gap. Run `test_bundle_shape_and_implemented_only_advertisement`, `test_contract_examples`, `test_kernel_defaults_and_deferred_families`, and `test_kernel_tasks_cannot_be_populated` under the pinned requirements. Identify each accepted instance and its intended rejecting keyword before attributing the failures to the environment. | tests/autopilot/test_controller_protocol.py:142 | 13 | BOB |
| R37 | [2/4] | 🟡 | test_accepts_a_spec_declaring_source_resource_digest_and_permitted_operations has no assertion: it only proves the code does not raise | tests/autopilot/test_controller_rework13_jobs.py:100 | general | CARL, mech-check |
| R38 | [2/4] | 🟡 | test_finish_rejects_an_inprogress_status_from_an_earlier_lease_epoch has no assertion: it only proves the code does not raise | tests/autopilot/test_controller_rework13_recovery.py:151 | general | CARL, mech-check |
| R39 | [1/4] | ⚪ | Prior R9 is only partly resolved. `owner.recover` now rejects only when a job is claimed or `reconciled_job_ids` is non-empty. A crashed owner that holds a claim is still unrecoverable. Reconciliation wiring was deferred by design (settled R45), so this is a note only. The new test covers only planned-but-unclaimed jobs. | plugins/autopilot/controller/autopilot_state/owner.py:276 | 13 | ALICE |
| R40 | [1/4] | ⚪ | `reduce_workflow` is exactly 50 lines (313-362) after this rework. The next addition breaches R12. Split job reducers out. | plugins/autopilot/controller/autopilot_state/protocol.py:313 | 13 | ALICE |
| R41 | [1/4] | ⚪ | Native session IDs in exit facts are recorded unverified. That is consistent with the spec ("recorded, never substitute acceptance"), and `record_exit` does not touch tasks or phase, which is good. | plugins/autopilot/controller/autopilot_state/jobs.py:75 | Phase 1 task 2 | BLAKE |
| R42 | [1/4] | ⚪ | The named scenarios `entry_wip_first`, `completion_moves_once`, `task_attempt_replay` and `interrupted_move_recovery` have no tests under those exact names. Equivalent coverage exists under other names, for example `test_enter_picks_wip_before_backlog_and_moves_nothing`, `test_complete_after_review_moves_once_and_records_the_prd` and `test_crash_at_each_complete_boundary_replays_without_double_entry`. Naming is traceability only. | tests/autopilot/test_controller_lifecycle.py:220 | general | BLAKE |

### Auto-dismissed (ledger)

- [BLAKE] 🟠 `jobs.claim` does not enforce dependencies. A job whose `depends_on` jobs have no exit fact can be claimed directly. Only `next_job` honours dependencies, and `job.claim` does not go through it. The result is out-of-order claims and wrong "required execution" ordering. | File: plugins/autopilot/controller/autopilot_state/jobs.py:63 — single-voice
- [BLAKE] ⚪ `lifecycle.evaluate` runs the PRD eligibility command through `/bin/sh -c`. The code comment documents this as a deliberate contract with a 30 s timeout, so it is an accepted risk. A backlog PRD's frontmatter command is therefore arbitrary code execution at selection time. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:229 — single-voice

## Alice

Alice review, PRD 00019, cycle 2 (incremental).

I read the diff, the context and the pack. I also read the live code in protocol.py, workflow-v1.json and the failing tests. I ran two throwaway checks: a payload-validation probe and a schema probe. I did not rerun the full suite.

**Verdict on the five failures: not defensible as an environment gap.** Cycle 1 ran 2097 passed, 0 failed with the same validator.

- The four `assert_invalid` failures come from the rework. It changed `workflow.tasks` and `workflow.jobs` in workflow-v1.json from `maxItems: 0` to `maxItems: 256`, with no `items` schema.
- It also loosened `bundle.operations` and `bundle.capabilities`, and added `job.next` to `implemented_operations` with no fixture.
- The loosened schema now accepts exactly what those tests assert it rejects (`tasks: ["synthetic-task"]`, `tasks: [{}]`, and a bundle with `job.plan`).
- The fifth failure is the cycle-1 R3 review bypass. I judge it separately below.

[ALICE] 🟠 Rework regression: 4 previously green tests now fail. The `tasks`/`jobs` schema nodes are only `{"type":"array","maxItems":256}` with no `items` schema, so a populated array of junk passes. `bundle.operations` (20 entries) and `bundle.capabilities` (open enum) were widened. `job.next` was added to `implemented_operations` with no valid or invalid fixture, so `test_contract_examples` fails on that too. The old tests (`test_bundle_shape_and_implemented_only_advertisement`, `test_kernel_defaults_and_deferred_families`, `test_contract_examples`, `test_kernel_tasks_cannot_be_populated`) were not updated and the schema was not tightened. Add `items` schemas for task and job rows, add `job.next` fixtures, and update the bundle test to the full runtime set. | File: plugins/autopilot/contracts/controller/workflow-v1.json:140 | Task: 13

[ALICE] 🟠 Prior R10 is only partly resolved. `batch`, `work` and `recovery` are still `{"type":"null"}` (lines 134-138, 157). The workflow object has `additionalProperties:false` (line 173), but the rework added a persisted `workflow.pause` and a `work.rework_cap` key. A state produced by `prd.enter` or a second park therefore violates the published schema. The new tests only check the `maxItems` keyword, never a real state against the schema. | File: plugins/autopilot/contracts/controller/workflow-v1.json:173 | Task: 13

[ALICE] 🟠 The prior R11 fix is unreachable through the public API. The retry path in `apply_unlocked` only runs after `apply_locked`, and `apply_locked` calls `authorize` for saga operations. `authorize` raises `revision_conflict` for any stale `expected_revision` that has no cached receipt. A retry after a crash between the saga commit and the receipt therefore never reaches the new `_replay_committed` logic. The test calls `apply_unlocked` directly and bypasses `authorize`. Prove it through `protocol.execute`, or move the replay check into `authorize`. | File: plugins/autopilot/controller/autopilot_state/protocol.py:481 | Task: 13

[ALICE] 🟠 The same change weakens optimistic concurrency in the TOCTOU window. A stale revision (the state changed between lock release and re-read) no longer short-circuits to `revision_conflict`. The saga now runs against the newer state whenever its own preconditions still hold. `revision_conflict` is raised only if the saga throws `PreconditionError`, `RecoveryConflictError` or `DeferredRecordConflictError`. This undercuts the R12 admission-guarantee fix. | File: plugins/autopilot/controller/autopilot_state/protocol.py:481 | Task: 13

[ALICE] 🟠 The prior R3 review-acceptance bypass is deferred, and a committed red test records it. A deferral is defensible: the PRD says acceptance is unavailable until AP00020. But a known-red test in the gate suite breaks CI and tracks nothing durable. Either fix it (reject `review`→`done` `converged` while no review evidence exists, which is what the PRD literally says), or mark the test strict xfail with an AP00020 reason and record the deferral in the PRD or an issue. The test body (`try/except` with an early `return`) also lets either outcome through, which is a hedge shape. | File: tests/autopilot/test_controller_rework13_lifecycle.py:1725 | Task: general

[ALICE] 🟠 `job.plan` boundary validation regressed. `_validate_caller_job_spec` checks only the seven base keys. A caller spec with a malformed `source_digest`, `resource_digest` or `permitted_operations`, or with unknown keys, passes `validate_reducer_payload`. I confirmed this with a probe. The failure then happens at commit-time `schema._job`. `apply_locked` maps that `SchemaError` (a `ValueError`) to `recovery_required`, so plain bad input now looks like a recovery state. Validate the optional keys and reject unknown keys in `validate_payload`. | File: plugins/autopilot/controller/autopilot_state/protocol.py:115 | Task: 13

[ALICE] 🟠 Prior R14 is only half fixed. `finish` skips the epoch check when `start_epoch` is absent. A task submitted via `task.replace` with `status: in_progress` has no `start_epoch`, so it can still be finished. Worse, `schema._task` now permits a caller-supplied `start_epoch` inside `task.replace` items, so start evidence can be forged. Strip or reject `start_epoch` in `task.replace` and refuse `finish` when it is missing. Only the earlier-lease case is tested. | File: plugins/autopilot/controller/autopilot_state/tasks.py:96 | Task: 13

[ALICE] 🟠 The prior R13 `workflow.pause` is write-only. `prd.enter` rejects forever once it is set. No operation (`owner.recover`, `prd.*`, etc.) clears it and no read projection shows it. The batch can never resume. It is also absent from the published schema (see above). Add a clearing path, or document pause as terminal. | File: plugins/autopilot/controller/autopilot_state/files.py:591 | Task: 13

[ALICE] 🟡 Fabricated job digests and permissions. `_with_job_defaults` sets `source_digest` and `resource_digest` to `sha256("source:<job_id>")` and `sha256("resource:<job_id>")`. These are not digests of any source or resource, so they are placeholder data presented as evidence. It also defaults `permitted_operations` to `["read","write"]`, which is a permissive default. `_derive_job_specs` hardcodes `role=builder`, `tier=opus`, `effort=high` and `isolation=worktree` for every task, ignoring policy and lane. Require callers to supply the digests and permissions, or derive them from real inputs. | File: plugins/autopilot/controller/autopilot_state/protocol.py:365 | Task: 13

[ALICE] 🟡 `job.next` is incomplete and under-tested. There is no request or response schema entry, no fixture, and no CHANGELOG or doc mention. The result is only `{job_id, instruction}`, with no readiness, digests or permitted operations. The one test covers a single job with no dependencies. The dependency-blocked skip and the all-claimed and all-blocked rejection are untested. It is read-only but goes through the mutating reducer path, so every poll bumps the revision and writes a receipt. | File: plugins/autopilot/controller/autopilot_state/jobs.py:52 | Task: 13

[ALICE] 🟡 Prior R1 is only partly resolved. Only `rework_cap` is persisted. The start commit is not captured, and the parser's `_warnings`, `defaults` and `overwrite_warnings` stay unused. The deviation is recorded only in a test comment and a docstring, not in a PRD or design note. `_frontmatter_work_fields` swallows `OSError` and `UnicodeDecodeError` into empty text, so an unreadable PRD silently enters with default values. That is an unreported error path. The function-local `from . import frontmatter` is redundant if `lifecycle.py` already imports from `frontmatter` at module level. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:327 | Task: 13

[ALICE] 🟡 Weak or tautological rework tests. `test_workflow_schema_permits_an_empty_tasks_or_jobs_array_too` is true before and after the change, because it reads `minItems` with a default. The `maxItems` tests use `.get(..., default)` and never validate a real state. The finding-10 test accepts any of four exception types (`pytest.raises((RevisionConflictError, RecoveryConflictError, PreconditionError, RecoveryRequiredError))`). Its name, `test_stall_does_not_recheck_revision...`, says the opposite of what it asserts. The finding-2 test passes against the pre-change code because no code changed for it. Test files are named by task number (`rework13_*`) rather than by the rule they enforce. | File: tests/autopilot/test_controller_rework13_contracts.py:22 | Task: 13

[ALICE] ⚪ Prior R9 is only partly resolved. `owner.recover` now rejects only when a job is claimed or `reconciled_job_ids` is non-empty. A crashed owner that holds a claim is still unrecoverable. Reconciliation wiring was deferred by design (settled R45), so this is a note only. The new test covers only planned-but-unclaimed jobs. | File: plugins/autopilot/controller/autopilot_state/owner.py:276 | Task: 13

[ALICE] ⚪ `reduce_workflow` is exactly 50 lines (313-362) after this rework. The next addition breaches R12. Split job reducers out. | File: plugins/autopilot/controller/autopilot_state/protocol.py:313 | Task: 13

Prior findings now resolved: R4, R15 and R5 (exporter lists, bundle, README and the runtime-derived export test). The R6 and R8 schema fields exist, with the caveats above. R7 is partly addressed by `job.next`. R2's wip-first self-heal is now tested.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: fail
R12: pass
R13: pass

## Blake

BLAKE blind review of PRD 00019 (autopilot controller lifecycle, tasks, job plans)

Method: I read `plugins/autopilot/controller/autopilot_state/{lifecycle,tasks,jobs,policy,protocol}.py`, the controller contract, and the lifecycle/jobs/integration tests. I ran `tests/autopilot/test_controller_protocol.py` (3 failed, 10 passed). I ran `test_package.py`, `test_helper_provenance_real.py`, `test_controller_export.py` and `test_controller_contract_agreement.py` (49 passed). The full suite run with `-x` stopped at the first failure (1 failed, 443 passed). I did not run the suite past that. `python3 scripts/validate.py` passed.

[BLAKE] 🟠 The Phase 2 exit criterion (full `tests/autopilot` pytest passes) fails at HEAD. Three tests in `test_controller_protocol.py` fail: `test_bundle_shape_and_implemented_only_advertisement`, `test_contract_examples` and `test_kernel_defaults_and_deferred_families`. Their `assert_invalid` calls now find no schema error. The first still expects a bundle with `job.plan` or `workflow.jobs.v1` to be invalid, but `contracts/controller/workflow-v1.json:1342-1385` now allows both. Either the schema or fixture edits and these tests drifted apart, or the tests were never updated. This matches the test gate's exit 1. | File: tests/autopilot/test_controller_protocol.py:393 | Task: Phase 2 task 2
[BLAKE] 🟠 Completion can be reached without any review evidence. `phase.handoff` accepts `tasks_done`, `rework` and `converged` from any authenticated actor, and `converged` marks `review` completed. `prd.complete` only checks `phase == done` and `"review" in completed_phases`. `test_manual_session_handoff` does exactly this: tasks_done, rework, converged, then complete, with no review record. The spec says completion moves "after accepted review" and "prose or exit zero cannot bypass review". The Risks section says review acceptance is unavailable until AP 00020, so a bare assertion currently stands in for acceptance. `false_success_no_advance` therefore only proves the refusal when the phase handoffs were skipped. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:106 | Task: Phase 1 task 1 / Phase 2 task 1
[BLAKE] 🟠 `build -> review` (`tasks_done`) does not check that tasks are completed. `lifecycle.apply` applies the row regardless of `workflow.tasks` status, so an actor can skip pending tasks. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:118 | Task: Phase 1 task 1
[BLAKE] 🟠 `jobs.claim` does not enforce dependencies. A job whose `depends_on` jobs have no exit fact can be claimed directly. Only `next_job` honours dependencies, and `job.claim` does not go through it. The result is out-of-order claims and wrong "required execution" ordering. | File: plugins/autopilot/controller/autopilot_state/jobs.py:63 | Task: Phase 1 task 2
[BLAKE] 🟡 "Start commit/frontmatter captured once" is only partly implemented. The entry persists just `rework_cap` from the frontmatter (`lifecycle.py:343`). No start commit is captured or stored: `rg` for `start_commit`, `rev-parse` and `head_commit` finds nothing in the controller or schema. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:329 | Task: Phase 1 task 1
[BLAKE] 🟡 The job plan digests are not real digests. `_with_job_defaults` fills `source_digest` and `resource_digest` with `sha256("source:<job_id>")`. They bind to nothing, so they cannot detect input drift. Spec says "source/input/resource digests". Derived specs also hard-code `tier: "opus"`, `effort: "high"`, `isolation: "worktree"` and `role: "builder"` (`protocol.py:385-389`), ignoring the PRD's tier policy. | File: plugins/autopilot/controller/autopilot_state/protocol.py:369 | Task: Phase 1 task 2
[BLAKE] 🟡 `job.next` returns only `{job_id, instruction: "run job X (role)"}`. This is not a "structured standalone next-job instruction". It omits role details, dependency IDs, digests, isolation, tier/effort and permitted operations. A fresh session must read the whole snapshot. | File: plugins/autopilot/controller/autopilot_state/protocol.py:346 | Task: Phase 1 task 2
[BLAKE] 🟡 Claims have no scope or role check beyond "any registered actor". Operator and owner can both claim, and `claim_epoch` is the actor's lease epoch. The spec's "one valid claim per job/epoch" holds only as "one claim per job ever": a re-planned job at a later epoch cannot be reclaimed. There is no claim-release or reclaim path other than `owner.recover` (not verified to reset claims). | File: plugins/autopilot/controller/autopilot_state/jobs.py:63 | Task: Phase 1 task 2
[BLAKE] 🟡 `job.plan` has no active-PRD or phase precondition. It also accepts caller-supplied digests and permitted operations unvalidated against any source, and it allows an empty `jobs` list to trigger derivation as a side channel. | File: plugins/autopilot/controller/autopilot_state/protocol.py:341 | Task: Phase 1 task 2
[BLAKE] ⚪ Native session IDs in exit facts are recorded unverified. That is consistent with the spec ("recorded, never substitute acceptance"), and `record_exit` does not touch tasks or phase, which is good. | File: plugins/autopilot/controller/autopilot_state/jobs.py:75 | Task: Phase 1 task 2
[BLAKE] ⚪ The named scenarios `entry_wip_first`, `completion_moves_once`, `task_attempt_replay` and `interrupted_move_recovery` have no tests under those exact names. Equivalent coverage exists under other names, for example `test_enter_picks_wip_before_backlog_and_moves_nothing`, `test_complete_after_review_moves_once_and_records_the_prd` and `test_crash_at_each_complete_boundary_replays_without_double_entry`. Naming is traceability only. | File: tests/autopilot/test_controller_lifecycle.py:220 | Task: general
[BLAKE] ⚪ `lifecycle.evaluate` runs the PRD eligibility command through `/bin/sh -c`. The code comment documents this as a deliberate contract with a 30 s timeout, so it is an accepted risk. A backlog PRD's frontmatter command is therefore arbitrary code execution at selection time. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:229 | Task: general

Per-rule verdicts:
B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

Notes on verdicts:
- B1 fails on the start-commit gap, the fake digests and the unstructured `job.next`.
- B15 fails on the unmet dependency-ordered claim and the `tasks_done` precondition.
- B16 fails because the exit-criterion pytest run fails and review is bypassable.
- B17 is trivially pass: the PRD has no Phase 3.

## Bob

FIX:
[BOB] 🟠 `apply_unlocked` now runs a saga even when the admitted revision is stale. A fresh stall, park, or defer can read the newer state and mutate it after the original authorization has expired. Validate the admitted revision and actor when staging the intent. Allow stale requests only after a read-only lookup proves they match a durable intent or receipt. | File: plugins/autopilot/controller/autopilot_state/protocol.py:467 | Task: 13  
[BOB] 🟠 The new crash-replay test calls `apply_unlocked` directly and skips `authorize`, which still rejects the original stale request before replay can start. The ledger fallback also lacks the original request digest and excludes entry and completion. Bind recovery to the authenticated request and commit its receipt before clearing the marker. Test retries through the public dispatcher. | File: plugins/autopilot/controller/autopilot_state/protocol.py:285 | Task: 13  
[BOB] 🟠 The second park clears its recovery marker before persisting `systemic_park`. A crash leaves the batch unpaused, and a concurrent entry can start another PRD in that gap. Commit the pause with the park counter and work reset in the existing bookkeeping transaction. | File: plugins/autopilot/controller/autopilot_state/files.py:578 | Task: 13  
[BOB] 🟠 Entry now captures `rework_cap` alone. It still omits the start commit, effective task tier, and plan-expansion policy. The metadata read also precedes the verified move, so it can capture a different file from the one moved. Capture the required metadata from the verified PRD and preserve it in a staged entry intent. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:329 | Task: 13  
[BOB] 🟠 The reported review regression still fails, and the new receipt test relies on that same unsupported `converged` handoff to complete a PRD. Keep completion unavailable until accepted evidence exists. Assert through the public dispatcher that an unsupported convergence claim changes neither phase nor bucket. | File: tests/autopilot/test_controller_rework13_lifecycle.py:84 | Task: 13  
[BOB] 🟠 `task.finish` still accepts a task with no `start_epoch`, including one installed as `in_progress` by `task.replace`. Require a matching start epoch for public finish requests and test rejection of a plan-supplied `in_progress` task. | File: plugins/autopilot/controller/autopilot_state/tasks.py:85 | Task: 13  
[BOB] 🟠 Job enrichment hashes labels derived from the job ID and presents them as source and resource digests. The derived plan also schedules every task regardless of status and hardcodes role, tier, effort, and permissions. Use actual digests and derive job requirements from phase, tasks, policy, and accepted results. Test that changing those inputs changes the plan where required. | File: plugins/autopilot/controller/autopilot_state/protocol.py:369 | Task: 13  
[BOB] 🟠 State saved by cycle 1 with a populated job plan now fails validation because stored jobs require three new fields. Request-time enrichment cannot repair state that fails to load. Preserve compatibility for existing rows and require real metadata before offering those jobs for execution. | File: plugins/autopilot/controller/autopilot_state/schema.py:315 | Task: 13  
[BOB] 🟡 `job.next` returns an ID and a prose instruction while consuming a revision and receipt slot. It omits the digests, isolation, tier, effort, and permitted operations an executor needs. Return the structured job specification through a read-only projection and test that repeated reads leave state unchanged. | File: plugins/autopilot/controller/autopilot_state/protocol.py:343 | Task: 13  
[BOB] 🟡 The contract rework only loosens array lengths and bundle enumeration. It still disagrees with runtime state and adds no request, result, or fixture for `job.next`. Define the new shapes and validate real persisted state and dispatcher responses against the installed schema. | File: plugins/autopilot/contracts/controller/workflow-v1.json:139 | Task: 13  
[BOB] 🟡 `owner.recover` still rejects jobs with a recorded exit because their `claimed_by` remains set. The updated README implies an operator can finish jobs and then recover ownership. Permit recovery when every claim has an exit fact and retain the guard for outstanding claims. | File: plugins/autopilot/controller/autopilot_state/owner.py:275 | Task: 13  
[BOB] 🟡 The new committed-replay path rebuilds ledger rows independently of `_ledger_item`. Use the same builder for append and comparison so a record format change cannot break replay. | File: plugins/autopilot/controller/autopilot_state/files.py:500 | Task: 13  
[BOB] 🟡 The exporter now duplicates the expanded operation and capability lists. Read them from the controller contract metadata already packaged with the schema and retain the installed-bundle parity test. | File: tools/autopilot/export-controller-contract.py:32 | Task: 15  
[BOB] 🟡 The mechanical check flags the valid JobSpec test and the earlier-epoch refusal test for lacking direct assertions. Assert persisted job metadata in the first test and the unchanged task state after rejection in the second. | File: tests/autopilot/test_controller_rework13_jobs.py:100 | Task: general  
[BOB] 🟡 The empty-array contract test passes on the base and inspects only `minItems`. Pair an actual valid empty state with a malformed populated state and validate both against the shipped schema. | File: tests/autopilot/test_controller_rework13_contracts.py:45 | Task: 13  
[BOB] 🟡 Five job tests pass on the base. The three missing-field cases can pass because the base rejects the other added fields, and the two empty-state cases exercise existing behavior. Pair each missing-field case with a valid control and use the empty cases as controls for derivation and owner recovery with a populated plan. | File: tests/autopilot/test_controller_rework13_jobs.py:63 | Task: 13  
[BOB] 🟡 The entry recovery test passes on the base because it renames the file itself and retries with a fresh request. Drive the actual entry operation to the interruption point and assert replay of the original request preserves `source: backlog` and commits once. | File: tests/autopilot/test_controller_rework13_lifecycle.py:52 | Task: 13  
[BOB] 🟡 The same-epoch success test passes on the base because it checks only final status. Assert that start persists the authorizing epoch before finishing. | File: tests/autopilot/test_controller_rework13_recovery.py:164 | Task: 13  
[BOB] 🟡 The expanded receipt-dispatch test passes on the base and omits this cycle’s new `job.next` result. Cover the new receipt shape while it exists, or validate the new response directly if the query moves to a read-only projection. | File: tests/autopilot/test_controller_schema_lifecycle.py:455 | Task: 16  

VERIFY:
[BOB] 🟡 The supplied suite reports 2,118 passed and five failed, including four schema rejection failures described as an environment gap. Run `test_bundle_shape_and_implemented_only_advertisement`, `test_contract_examples`, `test_kernel_defaults_and_deferred_families`, and `test_kernel_tasks_cannot_be_populated` under the pinned requirements. Identify each accepted instance and its intended rejecting keyword before attributing the failures to the environment. | File: tests/autopilot/test_controller_protocol.py:142 | Task: 13  

KNOWN:
- (none)

R1: fail  
R2: fail  
R3: pass  
R4: fail  
R6: pass  
R7: fail  
R8: pass  
R9: fail  
R10: fail  
R11: fail  
R12: pass  
R13: pass  

D1: pass  
D2: pass  
D3: pass  
D4: pass  
D5: pass

## Carl

Backend: copilot, model gemini-3.8-flash (from the runner's stderr). Output non-empty and independent.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass
[CARL] 🟠 Review acceptance can still be bypassed with no review evidence checked: phase.handoff outcome=converged advances to done and prd.complete moves the PRD to done/, causing test_bypass_review_via_handoff_converged_is_rejected_without_evidence to fail | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:92 | Task: 13
[CARL] 🟠 Published workflow schema leaves batch, work, and recovery as null-only, while relaxing tasks and jobs to maxItems 256 breaks pre-existing kernel tests in test_controller_protocol.py and test_controller_recovery_characterization.py | File: plugins/autopilot/contracts/controller/workflow-v1.json:132 | Task: 13
[CARL] 🟡 test_accepts_a_spec_declaring_source_resource_digest_and_permitted_operations has no assertion: it only proves the code does not raise | File: tests/autopilot/test_controller_rework13_jobs.py:100 | Task: general
[CARL] 🟡 test_finish_rejects_an_inprogress_status_from_an_earlier_lease_epoch has no assertion: it only proves the code does not raise | File: tests/autopilot/test_controller_rework13_recovery.py:151 | Task: general
[CARL] 🟡 Simplification: lifecycle.py:335 uses inline from . import frontmatter inside _frontmatter_work_fields; import parse from .frontmatter at module top level where command_for is already imported | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:335 | Task: 13

Verdict: 42 findings
Tests: 2118 passed, 5 failed, 0 skipped (exit 1) (suite run this cycle)
