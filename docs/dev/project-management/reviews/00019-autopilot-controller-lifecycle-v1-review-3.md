---
prd: 00019-autopilot-controller-lifecycle-v1.md
cycle: 3
date: 2026-11-25
head_sha: 827de63b2c3d34ed5eaa70775602ac35d1a37d31
reviewers: alice,blake,bob,carl
---

# Review cycle 3 - 00019-autopilot-controller-lifecycle-v1

Diff range: `24f3a4a4ba7a04517b9be066b5f9ab478a125c9e..827de63b2c3d34ed5eaa70775602ac35d1a37d31`
(incremental: the rework since cycle 2)

codex_rung_guard: not fired

## Review Summary

Cycle 3 is an incremental review of the cycle-2 rework. All four reviewers ran:
Alice (consensus, Claude subagent), Blake (blind, PRD-only), Bob (doubt lens
D1-D5 plus de-slop, codex, resumed on his cycle-2 thread) and Carl (gemini).
Eve did not run: the codex doubt-roster guard did not fire, because no task in
this PRD was implemented by codex.

Consolidation was run by `consolidate_findings.py` with the settled-decisions
ledger and `--ledger-dismiss BLAKE`; its auto-dismissed section is reproduced
below. The mechanical test checks were absorbed afterwards: eight `[MECH]`
lines merged onto rows that already named the same test file and test (R1, R26,
R27, R28, R29, R30, R31, R37), and three became their own rows (R38, R39, R40).
The previous cycle's verification-check queue
(`00019-autopilot-controller-lifecycle-v1-checks-2.json`) recorded exit 0, so
nothing carried forward.

Staging note: the `## Test gate` line in the staged review context read
`exit 2, no PASS/FAIL/SKIP/EXIT summary line`. That was a staging artifact, not
a red suite - the staged gate command omitted this project's test
dependencies (`tools/autopilot/requirements-test.txt`, which supplies
`jsonschema` and `PyYAML`), so pytest stopped at a collection ImportError
before running a test. Every reviewer was told so explicitly. The suite below
was run separately this cycle with those requirements installed, using the CI
command from `.github/workflows/validate.yml`.

pack: ok

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟡 | Several touched tests pass against the pre-change code, so they do not pin this change. The clearest is `test_the_second_park_commits_the_pause_with_the_recovery_marker_it_clears`. The boundary hook never fires between the old separate clear and pause transactions, so the old code passes it. Only `test_a_crash_while_the_second_park_commits_never_loses_the_systemic_pause` binds. The stale enter and handoff tests call `lifecycle.enter` and `lifecycle.handoff` directly, and those already checked the revision. Mark them as controls, or drive the crash case through them. | tests/autopilot/test_cycle2_replay_pause.py:171 | 13 | ALICE, BOB, mech-check |
| R2 | [1/4] | 🟠 | Prior R4/R10/R19 only deferred: `phase.handoff` review to done with outcome `converged` is accepted with no review evidence, so `prd.complete` can close a PRD on a bare claim. This contradicts the PRD's "prose or exit zero cannot bypass review". It is now a strict xfail with a durable deferral to AP00020, so only the gate can accept it as a deferral. | plugins/autopilot/controller/autopilot_state/lifecycle.py:106 | general | ALICE |
| R3 | [1/4] | 🟠 | Jobs are never scoped to a PRD or cleared between PRDs. `reset_prd_fields` keeps `jobs` (lifecycle.py:57-67, docstring "keep batch, recovery, jobs"). `_derive_job_specs` skips every task whose id is already a planned `job_id` (protocol.py:382-385), and `jobs.plan` rejects duplicate ids (jobs.py:58). In a multi-PRD batch the second PRD's tasks (for example "1", "2") are silently never planned, or collide on an explicit plan. Unclaimed or exited jobs from the first PRD stay in `next_job`, carrying a stale `resource_digest`. No test covers a second PRD. | plugins/autopilot/controller/autopilot_state/lifecycle.py:57 | Phase 1 task 2 | BLAKE |
| R4 | [1/4] | 🟠 | The stale-revision check still races with saga staging. `apply_unlocked` checks one snapshot, then `_run_saga_body` rereads state and stages against that newer revision. Pass the admitted revision into staging and test a lease change between those two reads. | plugins/autopilot/controller/autopilot_state/files.py:555 | 17 | BOB |
| R5 | [1/4] | 🟠 | Replay admission treats a ledger row as proof of commit, although the saga appends it before committing. The row also lacks the authorizing actor and request digest. A crash before the append still leaves the original request unable to resume. Bind the durable intent to the authenticated request, resume from its recorded step, and test public retries before and after the append. | plugins/autopilot/controller/autopilot_state/protocol.py:269 | 17 | BOB |
| R6 | [1/4] | 🟠 | Derived planning drops completed tasks but retains dependency IDs that point to them. A pending task that depends on a completed task therefore has an unknown job dependency unless that task already has a job row. Resolve dependencies against completed task state and scheduled jobs, and test this resumed plan. | plugins/autopilot/controller/autopilot_state/protocol.py:380 | 17 | BOB |
| R7 | [1/4] | 🟠 | The full suite’s single strict xfail covers the still-open review acceptance gap. The batch ledger assigns evidence-backed acceptance to AP00020. Until that work lands, the passing integration path still relies on a bare `converged` claim. | tests/autopilot/test_controller_rework13_lifecycle.py:131 | 18 | BOB |
| R8 | [1/4] | 🟡 | `policy.job_requirements` raises a bare KeyError for any phase other than build or review. A derived `job.plan` in phase `done` (after `task.replace` adds unfinished rows) therefore returns `recovery_required` for a plain precondition failure. I confirmed `job_requirements({'phase':'done',...})` raises `KeyError 'done'`, and `apply_locked` maps KeyError to `recovery_required`. The assumptions note records the KeyError as "closed vocabulary" and no test covers it. Reject with `rejected_evidence` instead, and add a test. | plugins/autopilot/controller/autopilot_state/policy.py:143 | 13 | ALICE |
| R9 | [1/4] | 🟡 | The `_runnable` docstring says a spec lacking the metadata "is reconciled by replanning the job". That cannot happen. `jobs.plan` only appends, and `validate_plan_shape` over existing plus new specs rejects a repeated job id. Such a job stays stuck, and every job that depends on it never becomes ready. Either allow replanning an unclaimed, non-runnable row, or correct the docstring and say operator reseeding is the only repair. | plugins/autopilot/controller/autopilot_state/jobs.py:16 | 13 | ALICE |
| R10 | [1/4] | 🟡 | Two new branches have no test that fails when they are removed (R1). (a) `_verify_entered` raises `RecoveryRequiredError` when the moved PRD's bytes differ from the parsed bytes. The assumptions file says no test exercises it. (b) `apply_unlocked` raises `revision_conflict` when `stale and not replay`. Every stale test is stopped earlier by `authorize`, so nothing tests the window between lock release and re-read. | plugins/autopilot/controller/autopilot_state/lifecycle.py:379 | 13 | ALICE |
| R11 | [1/4] | 🟡 | `start_commit` is stored as raw `git rev-parse HEAD` output, but the schema accepts only 40 hex characters. The assumptions file admits a sha256 repository fails at commit time. That failure happens after the verified rename, as `recovery_required`, and the same failure repeats on every retry. The PRD stays in wip with no entry. Accept 40 or 64 hex characters in both the schema and the JSON contract, or record null when git returns anything else. | plugins/autopilot/controller/autopilot_state/schema.py:397 | 13 | ALICE |
| R12 | [1/4] | 🟡 | `test_workflow_schema_permits_an_empty_tasks_or_jobs_array_too` still passes against the pre-change code (prior R31/R23). It validates only the empty state against the shipped schema. Its junk `populated` rows are checked by the runtime validator alone. The comment still says the shipped file "declares no `items` for tasks/jobs" and that "a separate task tightens that JSON file". This diff made that tightening, so the comment is false. Assert `jsonschema` rejects the junk rows, or delete the comment and the runtime-only check. | tests/autopilot/test_controller_rework13_contracts.py:48 | 13 | ALICE |
| R13 | [1/4] | 🟡 | A failed dependency unlocks its dependents. `next_job` treats any non-null `exit_fact` as finished (jobs.py:67), and `outcome` is free text. A job whose exit fact says "failed" lets the next job be offered. | plugins/autopilot/controller/autopilot_state/jobs.py:67 | Phase 1 task 2 | BLAKE |
| R14 | [1/4] | 🟡 | `false_success_no_advance` is only partly enforced. `phase.handoff review->converged` is accepted from any registered actor with no review or job evidence (lifecycle.py:453-472). `prd.complete` then moves the PRD, so a false "converged" bypasses review. The tests only prove that `complete` is refused before a handoff (tests/autopilot/test_controller_integration.py:164). The spec's Risks section admits acceptance is unavailable until AP 00020. Exit facts are correctly never consulted. `rework_cap` is captured (lifecycle.py:355) but never enforced. | plugins/autopilot/controller/autopilot_state/lifecycle.py:453 | Phase 2 task 1 | BLAKE |
| R15 | [1/4] | 🟡 | Crash recovery for claimed jobs deadlocks. `claim` rejects any already-claimed job whatever its epoch (jobs.py:80). `owner.recover` is refused whenever any job has `claimed_by` set or `reconciled_job_ids` is non-empty (owner.py:275-278). No operation clears or reassigns a claim. The spec says "one valid claim per job/epoch", and `claim_epoch` is stored, but a crashed claimant's job can never be re-claimed in a new epoch. | plugins/autopilot/controller/autopilot_state/owner.py:275 | Phase 1 task 2 | BLAKE |
| R16 | [1/4] | 🟡 | `manual_session_handoff` never exercises jobs. Phase 2 task 1 says to export core/jobs capabilities and run a manual-session fake-host lifecycle. The test (tests/autopilot/test_controller_integration.py:116) covers tasks, handoff and complete only. Job claim and exit run in a separate test. `job.next` has no end-to-end test in a handoff. | tests/autopilot/test_controller_integration.py:116 | Phase 2 task 1 | BLAKE |
| R17 | [1/4] | 🟡 | Reviewer jobs cannot be derived through the normal handoff. `tasks_done` requires all task rows to be finished, then derivation in `review` selects only unfinished rows. The policy test reaches its reviewer branch by directly seeding a state that the public handoff cannot produce. Derive review work from completed build state and test it after a public handoff. | tests/autopilot/test_cycle2_jobs_metadata.py:168 | 17 | BOB |
| R18 | [1/4] | 🟡 | Legacy job rows without metadata are now loadable but permanently unclaimable. `_runnable` says replanning reconciles them, yet `jobs.plan` rejects an existing ID and derivation skips it. Add a bounded way to replace an unclaimed legacy spec and test the upgrade through the dispatcher. | plugins/autopilot/controller/autopilot_state/jobs.py:16 | 17 | BOB |
| R19 | [1/4] | 🟡 | `prd.enter` captures `plan_expansion`, but `task.replace` still uses only the caller’s flag. A PRD that denies expansion can receive a plan over the ceiling. Enforce the captured policy and test a conflicting request. | plugins/autopilot/controller/autopilot_state/protocol.py:318 | 17 | BOB |
| R20 | [1/4] | 🟡 | Backlog entry verifies that the bytes in `wip` match the parsed bytes. Direct `wip` entry checks only that a regular file still exists, so a replacement can inherit metadata from the old file. Apply the same byte and identity check to direct entry and test a replacement before publication. | plugins/autopilot/controller/autopilot_state/lifecycle.py:406 | 17 | BOB |
| R21 | [1/4] | 🟡 | HEAD capture accepts any successful Git output, while state validation requires a 40-character SHA-1. A SHA-256 repository can reach the backlog rename and then fail state publication. Validate the Git result before any move and align both schemas with the supported object formats. | plugins/autopilot/controller/autopilot_state/lifecycle.py:340 | 17 | BOB |
| R22 | [1/4] | 🟡 | The published contract adds a `job.next` request and fixtures but still lacks its expanded success result. Add the result shape and validate an actual dispatcher response and its persisted receipt against the shipped contract. | plugins/autopilot/contracts/controller/workflow-v1.json:1604 | 19 | BOB |
| R23 | [1/4] | 🟡 | Caller and stored JobSpec definitions duplicate every property and differ only in required keys. Reference the stored shape from the caller definition and require the three extra keys there. | plugins/autopilot/contracts/controller/workflow-v1.json:713 | 19 | BOB |
| R24 | [1/4] | 🟡 | The updated delivery receipt records 2,185 passes and zero failures but omits the known expected failure. Include the xfail count in the delivery evidence so it matches the supplied test result. | docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json:31 | 12 | BOB |
| R25 | [1/4] | 🟡 | The packed-reference test uses a disjunctive fixture check. Assert that `packed-refs` contains the tested branch and that its specific loose ref is absent. | tests/autopilot/test_cycle2_entry_tasks.py:120 | general | BOB |
| R26 | [2/4] | 🟡 | The earlier-epoch test remains flagged for having no direct assertion. Keep the rejection helper and assert the persisted task still carries its original status and start epoch. The earlier- and same-epoch tests both pass on the base, so keep them as controls for the new missing-start refusal case. | tests/autopilot/test_controller_rework13_recovery.py:158 | 20 | BOB, mech-check |
| R27 | [2/4] | 🟡 | The mechanical replay reports five contract tests, the empty-array test, and the malformed JobSpec test passing on the base. Keep the unchanged expectations as controls and isolate the new contract behavior. The empty-array test’s malformed case checks only Python validation, although the shipped JSON Schema now defines row shapes. Validate both instances against JSON Schema and remove the stale comment. | tests/autopilot/test_controller_rework13_contracts.py:48 | 19 | BOB, mech-check |
| R28 | [2/4] | 🟡 | The mechanical replay reports 18 entry/task cases passing on the base. Separate retained controls from regressions and pair malformed metadata cases with a valid record carrying the same new fields, so rejection of an unknown key cannot satisfy the test. | tests/autopilot/test_cycle2_entry_tasks.py:232 | 17 | BOB, mech-check |
| R29 | [2/4] | 🟡 | The mechanical replay reports four job-metadata cases and the populated-plan owner recovery test passing on the base. Keep complete-spec and owner-recovery cases as controls. For legacy specs, assert the stored state loads successfully before checking that dispatch refuses the claim. | tests/autopilot/test_cycle2_jobs_metadata.py:307 | 20 | BOB, mech-check |
| R30 | [2/4] | 🟡 | test_finish_rejects_an_inprogress_status_from_an_earlier_lease_epoch has no assertion: it only proves the code does not raise | tests/autopilot/test_controller_rework13_recovery.py:158 | general | CARL, mech-check |
| R31 | [2/4] | 🟡 | test_enter_captures_the_head_commit_of_a_repository_whose_refs_are_packed hedges with `or`: either outcome satisfies it | tests/autopilot/test_cycle2_entry_tasks.py:120 | general | CARL, mech-check |
| R32 | [1/4] | ⚪ | The mechanical hedge flag on `test_enter_captures_the_head_commit_of_a_repository_whose_refs_are_packed` is a precondition check (`not loose.exists() or not any(loose.rglob("*"))`), not the outcome assert. The outcome assert is `start_commit == head`. Rewrite the precondition without `or` to silence the shape. | tests/autopilot/test_cycle2_entry_tasks.py:120 | 13 | ALICE |
| R33 | [1/4] | ⚪ | `_head_commit` turns every git failure (timeout, missing binary) into `start_commit: null` with no signal. It also inherits any ambient `GIT_DIR` or `GIT_WORK_TREE`, which could record another repository's HEAD. Consider clearing those variables and noting the null case in the result. | plugins/autopilot/controller/autopilot_state/lifecycle.py:340 | 13 | ALICE |
| R34 | [1/4] | ⚪ | Small duplication and naming. `_derive_job_specs` hardcodes `("pending", "in_progress")` while `lifecycle._UNFINISHED` already holds that tuple. The `tasks_done` gate raises `UnknownTransition` for an unfinished-task precondition, which is misleading even though it maps to `rejected_evidence`. | plugins/autopilot/controller/autopilot_state/protocol.py:380 | 13 | ALICE |
| R35 | [1/4] | ⚪ | `job.next` is a REDUCER_OPERATION (protocol.py:24-26). Each read-only call bumps the revision and stores a receipt, which counts against the 4096-receipt cap. In `policy.job_requirements`, `_ROLES[work["phase"]]` raises KeyError outside build or review (policy.py:145). That error surfaces as `recovery_required` rather than `rejected_evidence`. Derived specs always carry `input_digests: []` (protocol.py:394). | plugins/autopilot/controller/autopilot_state/protocol.py:350 | Phase 1 task 2 | BLAKE |
| R36 | [1/4] | ⚪ | "Early supervisor-start revert from OVCAQ 00062 is incorporated" has no trace in plugins/, tools/ or tests/. The only "00062" hits are unrelated tracon text. I could not verify this requirement. | N/A | general | BLAKE |
| R37 | [2/4] | ⚪ | The entry crash test passes on the base and records `source: wip` on retry. It now exercises the real interrupted entry, but preserving the original `backlog` source requires durable metadata that the batch ledger defers beyond task 18’s test-only scope. | tests/autopilot/test_controller_rework13_lifecycle.py:65 | 18 | BOB, mech-check |
| R38 | [1/4] | 🟡 | 5 touched test(s) pass against the pre-change code: test_advertised_capability_and_operation_lists_are_pinned, test_bundle_shape_and_implemented_only_advertisement, test_malformed_workflow_fields_are_rejected, test_reserved_operations_parse_but_need_unavailable_capability, test_workflow_default_matches_frozen_initial_state | tests/autopilot/test_controller_protocol.py | general | mech-check |
| R39 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_owner_recover_succeeds_with_a_nonempty_job_plan | tests/autopilot/test_controller_rework13_jobs.py | general | mech-check |
| R40 | [1/4] | 🟡 | 1 touched test(s) pass against the pre-change code: test_rejects_job_and_job_spec_records_with_missing_extra_or_mistyped_fields | tests/autopilot/test_controller_schema_lifecycle.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] 🟠 `jobs.claim` ignores `depends_on`. It only checks that the job is unclaimed and has valid metadata (jobs.py:76-87). Only `next_job` filters on finished dependencies (jobs.py:65-73), and `job.claim` takes a caller-chosen `job_id`. Any registered actor, operator included, can claim and run a dependent job (for example `review` before `build`) by id. The spec says plans carry dependency ids and are driven by task dependencies. No test claims a job whose dependency has not exited. | File: plugins/autopilot/controller/autopilot_state/jobs.py:76 — single-voice
- [BLAKE] 🟡 "Controller never launches processes" is contradicted outside jobs.py. `lifecycle.evaluate` runs `/bin/sh -c <PRD-declared command>` (lifecycle.py:240). `prd.enter` runs `git rev-parse HEAD` through `_head_commit` (lifecycle.py:343). The `no_controller_spawn` test only AST-scans jobs.py (tests/autopilot/test_controller_jobs.py:133-148). It does not cover resume or duplicate requests, which the Phase 1 acceptance names. plugins/autopilot/CHANGELOG.md:7 repeats the no-launch claim. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:240 — single-voice
- [BLAKE] 🟡 Eligibility and the drain-versus-ineligible distinction exist only as library code. `select_eligible` and `evaluate` have no protocol operation. `prd.enter` never runs eligibility and takes a caller-supplied `prds` list. `prd.enter` also returns the same `rejected_evidence` for drained, ineligible and already-completed (lifecycle.py:425-432). The `drained_vs_ineligible` test (tests/autopilot/test_controller_integration.py:194) calls the library function directly. A host driving the CLI contract cannot tell an empty queue from an ineligible one. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:256 — single-voice
- [BLAKE] ⚪ None of the named acceptance scenarios exist as test names: `entry_wip_first`, `completion_moves_once`, `task_attempt_replay`, `interrupted_move_recovery`, `lifecycle_source_map` and `transition_preconditions`. Equivalent behavior is tested under other names (for example tests/autopilot/test_controller_rework13_lifecycle.py:68 for the interrupted entry, tests/autopilot/test_controller_tasks.py:284 for attempt replay). The scenarios cannot be traced mechanically. | File: tests/autopilot/test_controller_lifecycle.py — single-voice


## Alice

Consensus lens, Claude subagent, implementation-aware, incremental.

### Alice - cycle 3 (incremental) review of 24f3a4a..827de63

I read the full diff, the context file, the pack and the prior-findings table. I also probed `policy.job_requirements` directly. I did not run the suite. I took the 2185 passed / 1 xfailed / exit 0 at 65e4f0f as given, since HEAD only adds bookkeeping commits. I did not count the exit-2 gate line as a failure. I did not re-raise the discarded items or the false positive on the lease-epoch finish test.

### Prior findings: most are resolved
- **Resolved, no new issues found:**
  - Entry metadata: start commit, tier and plan_expansion, read from the PRD bytes before the rename and checked after it.
  - Unreadable or undecodable PRDs are now rejected instead of defaulted.
  - The published workflow schema now declares batch, work, recovery, pause, task rows and job rows.
  - `finish` now needs a recorded `start_epoch`.
  - `tasks_done` is gated on all task rows being finished.
  - The second park commits `workflow.pause` in the same transaction that clears the marker. The pause is documented as terminal and shown in `resume_target`.
  - A caller job spec is a closed object, so bad input gives `invalid_request` instead of `recovery_required`.
  - The fabricated digests and permissions are gone. Derived specs now use real PRD content and row digests.
  - `job.next` returns the whole spec.
  - A stale saga request now conflicts at both `authorize` and `apply_unlocked`, unless `proven_replay` finds its own entry in the ledger.
- **Carried, not fixed (prior R4/R10/R19):** review acceptance can still be bypassed through `phase.handoff` review to done with outcome `converged`. It is pinned by a strict xfail and recorded in `docs/dev/project-management/autopilot/deferred/202611242306-deferred.json`. I count this as a documented deferral, not a fix.
- **Partly resolved (prior R21):** stored jobs without the new metadata are never offered or claimed. Nothing can reconcile them afterwards (see the third issue below).
- **Not resolved (prior R31):** the empty-array contract test still does not check a populated state against the shipped schema.

### Issues
[ALICE] 🟠 Prior R4/R10/R19 only deferred: `phase.handoff` review to done with outcome `converged` is accepted with no review evidence, so `prd.complete` can close a PRD on a bare claim. This contradicts the PRD's "prose or exit zero cannot bypass review". It is now a strict xfail with a durable deferral to AP00020, so only the gate can accept it as a deferral. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:106 | Task: general
[ALICE] 🟡 `policy.job_requirements` raises a bare KeyError for any phase other than build or review. A derived `job.plan` in phase `done` (after `task.replace` adds unfinished rows) therefore returns `recovery_required` for a plain precondition failure. I confirmed `job_requirements({'phase':'done',...})` raises `KeyError 'done'`, and `apply_locked` maps KeyError to `recovery_required`. The assumptions note records the KeyError as "closed vocabulary" and no test covers it. Reject with `rejected_evidence` instead, and add a test. | File: plugins/autopilot/controller/autopilot_state/policy.py:143 | Task: 13
[ALICE] 🟡 The `_runnable` docstring says a spec lacking the metadata "is reconciled by replanning the job". That cannot happen. `jobs.plan` only appends, and `validate_plan_shape` over existing plus new specs rejects a repeated job id. Such a job stays stuck, and every job that depends on it never becomes ready. Either allow replanning an unclaimed, non-runnable row, or correct the docstring and say operator reseeding is the only repair. | File: plugins/autopilot/controller/autopilot_state/jobs.py:16 | Task: 13
[ALICE] 🟡 Two new branches have no test that fails when they are removed (R1). (a) `_verify_entered` raises `RecoveryRequiredError` when the moved PRD's bytes differ from the parsed bytes. The assumptions file says no test exercises it. (b) `apply_unlocked` raises `revision_conflict` when `stale and not replay`. Every stale test is stopped earlier by `authorize`, so nothing tests the window between lock release and re-read. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:379 | Task: 13
[ALICE] 🟡 `start_commit` is stored as raw `git rev-parse HEAD` output, but the schema accepts only 40 hex characters. The assumptions file admits a sha256 repository fails at commit time. That failure happens after the verified rename, as `recovery_required`, and the same failure repeats on every retry. The PRD stays in wip with no entry. Accept 40 or 64 hex characters in both the schema and the JSON contract, or record null when git returns anything else. | File: plugins/autopilot/controller/autopilot_state/schema.py:397 | Task: 13
[ALICE] 🟡 `test_workflow_schema_permits_an_empty_tasks_or_jobs_array_too` still passes against the pre-change code (prior R31/R23). It validates only the empty state against the shipped schema. Its junk `populated` rows are checked by the runtime validator alone. The comment still says the shipped file "declares no `items` for tasks/jobs" and that "a separate task tightens that JSON file". This diff made that tightening, so the comment is false. Assert `jsonschema` rejects the junk rows, or delete the comment and the runtime-only check. | File: tests/autopilot/test_controller_rework13_contracts.py:48 | Task: 13
[ALICE] 🟡 Several touched tests pass against the pre-change code, so they do not pin this change. The clearest is `test_the_second_park_commits_the_pause_with_the_recovery_marker_it_clears`. The boundary hook never fires between the old separate clear and pause transactions, so the old code passes it. Only `test_a_crash_while_the_second_park_commits_never_loses_the_systemic_pause` binds. The stale enter and handoff tests call `lifecycle.enter` and `lifecycle.handoff` directly, and those already checked the revision. Mark them as controls, or drive the crash case through them. | File: tests/autopilot/test_cycle2_replay_pause.py:171 | Task: 13
[ALICE] ⚪ The mechanical hedge flag on `test_enter_captures_the_head_commit_of_a_repository_whose_refs_are_packed` is a precondition check (`not loose.exists() or not any(loose.rglob("*"))`), not the outcome assert. The outcome assert is `start_commit == head`. Rewrite the precondition without `or` to silence the shape. | File: tests/autopilot/test_cycle2_entry_tasks.py:120 | Task: 13
[ALICE] ⚪ `_head_commit` turns every git failure (timeout, missing binary) into `start_commit: null` with no signal. It also inherits any ambient `GIT_DIR` or `GIT_WORK_TREE`, which could record another repository's HEAD. Consider clearing those variables and noting the null case in the result. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:340 | Task: 13
[ALICE] ⚪ Small duplication and naming. `_derive_job_specs` hardcodes `("pending", "in_progress")` while `lifecycle._UNFINISHED` already holds that tuple. The `tasks_done` gate raises `UnknownTransition` for an unfinished-task precondition, which is misleading even though it maps to `rejected_evidence`. | File: plugins/autopilot/controller/autopilot_state/protocol.py:380 | Task: 13

### Rubric verdicts
R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

Notes on the verdicts:
- R3: the single xfail is strict, documented and recorded durably, and it covers a deferral that the prior cycle itself recommended.
- R9: it fails on the carried review-bypass gap.
- R12: the largest functions, `_run_saga_body` and `reduce_workflow`, are exactly 50 lines.
- R13: the data contracts that exceed 800 lines were already over it and are settled.

## Blake

Blind lens, Claude subagent, PRD-only, no diff and no review history.

[BLAKE] 🟠 Jobs are never scoped to a PRD or cleared between PRDs. `reset_prd_fields` keeps `jobs` (lifecycle.py:57-67, docstring "keep batch, recovery, jobs"). `_derive_job_specs` skips every task whose id is already a planned `job_id` (protocol.py:382-385), and `jobs.plan` rejects duplicate ids (jobs.py:58). In a multi-PRD batch the second PRD's tasks (for example "1", "2") are silently never planned, or collide on an explicit plan. Unclaimed or exited jobs from the first PRD stay in `next_job`, carrying a stale `resource_digest`. No test covers a second PRD. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:57 | Task: Phase 1 task 2
[BLAKE] 🟠 `jobs.claim` ignores `depends_on`. It only checks that the job is unclaimed and has valid metadata (jobs.py:76-87). Only `next_job` filters on finished dependencies (jobs.py:65-73), and `job.claim` takes a caller-chosen `job_id`. Any registered actor, operator included, can claim and run a dependent job (for example `review` before `build`) by id. The spec says plans carry dependency ids and are driven by task dependencies. No test claims a job whose dependency has not exited. | File: plugins/autopilot/controller/autopilot_state/jobs.py:76 | Task: Phase 1 task 2
[BLAKE] 🟡 A failed dependency unlocks its dependents. `next_job` treats any non-null `exit_fact` as finished (jobs.py:67), and `outcome` is free text. A job whose exit fact says "failed" lets the next job be offered. | File: plugins/autopilot/controller/autopilot_state/jobs.py:67 | Task: Phase 1 task 2
[BLAKE] 🟡 "Controller never launches processes" is contradicted outside jobs.py. `lifecycle.evaluate` runs `/bin/sh -c <PRD-declared command>` (lifecycle.py:240). `prd.enter` runs `git rev-parse HEAD` through `_head_commit` (lifecycle.py:343). The `no_controller_spawn` test only AST-scans jobs.py (tests/autopilot/test_controller_jobs.py:133-148). It does not cover resume or duplicate requests, which the Phase 1 acceptance names. plugins/autopilot/CHANGELOG.md:7 repeats the no-launch claim. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:240 | Task: Phase 1 task 2
[BLAKE] 🟡 Eligibility and the drain-versus-ineligible distinction exist only as library code. `select_eligible` and `evaluate` have no protocol operation. `prd.enter` never runs eligibility and takes a caller-supplied `prds` list. `prd.enter` also returns the same `rejected_evidence` for drained, ineligible and already-completed (lifecycle.py:425-432). The `drained_vs_ineligible` test (tests/autopilot/test_controller_integration.py:194) calls the library function directly. A host driving the CLI contract cannot tell an empty queue from an ineligible one. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:256 | Task: Phase 2 task 1
[BLAKE] 🟡 `false_success_no_advance` is only partly enforced. `phase.handoff review->converged` is accepted from any registered actor with no review or job evidence (lifecycle.py:453-472). `prd.complete` then moves the PRD, so a false "converged" bypasses review. The tests only prove that `complete` is refused before a handoff (tests/autopilot/test_controller_integration.py:164). The spec's Risks section admits acceptance is unavailable until AP 00020. Exit facts are correctly never consulted. `rework_cap` is captured (lifecycle.py:355) but never enforced. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:453 | Task: Phase 2 task 1
[BLAKE] 🟡 Crash recovery for claimed jobs deadlocks. `claim` rejects any already-claimed job whatever its epoch (jobs.py:80). `owner.recover` is refused whenever any job has `claimed_by` set or `reconciled_job_ids` is non-empty (owner.py:275-278). No operation clears or reassigns a claim. The spec says "one valid claim per job/epoch", and `claim_epoch` is stored, but a crashed claimant's job can never be re-claimed in a new epoch. | File: plugins/autopilot/controller/autopilot_state/owner.py:275 | Task: Phase 1 task 2
[BLAKE] 🟡 `manual_session_handoff` never exercises jobs. Phase 2 task 1 says to export core/jobs capabilities and run a manual-session fake-host lifecycle. The test (tests/autopilot/test_controller_integration.py:116) covers tasks, handoff and complete only. Job claim and exit run in a separate test. `job.next` has no end-to-end test in a handoff. | File: tests/autopilot/test_controller_integration.py:116 | Task: Phase 2 task 1
[BLAKE] ⚪ None of the named acceptance scenarios exist as test names: `entry_wip_first`, `completion_moves_once`, `task_attempt_replay`, `interrupted_move_recovery`, `lifecycle_source_map` and `transition_preconditions`. Equivalent behavior is tested under other names (for example tests/autopilot/test_controller_rework13_lifecycle.py:68 for the interrupted entry, tests/autopilot/test_controller_tasks.py:284 for attempt replay). The scenarios cannot be traced mechanically. | File: tests/autopilot/test_controller_lifecycle.py | Task: general
[BLAKE] ⚪ `job.next` is a REDUCER_OPERATION (protocol.py:24-26). Each read-only call bumps the revision and stores a receipt, which counts against the 4096-receipt cap. In `policy.job_requirements`, `_ROLES[work["phase"]]` raises KeyError outside build or review (policy.py:145). That error surfaces as `recovery_required` rather than `rejected_evidence`. Derived specs always carry `input_digests: []` (protocol.py:394). | File: plugins/autopilot/controller/autopilot_state/protocol.py:350 | Task: Phase 1 task 2
[BLAKE] ⚪ "Early supervisor-start revert from OVCAQ 00062 is incorporated" has no trace in plugins/, tools/ or tests/. The only "00062" hits are unrelated tracon text. I could not verify this requirement. | File: N/A | Task: general

Verified as present:
- Selection puts wip first, then the lowest backlog sequence (lifecycle.py:177). Hold is unreachable.
- Pre-intent path validation is in `files._require_basename`.
- Entry is wip-first. The backlog-to-wip rename is verified by identity. A crash between rename and commit is recovered by a wip-first re-select (lifecycle.py:387-403). A crash test exists at tests/autopilot/test_controller_rework13_lifecycle.py:68.
- `start_commit`, `rework_cap`, tier and `plan_expansion` are captured once at entry (lifecycle.py:351-358).
- Completion requires phase done and "review" in `completed_phases` (lifecycle.py:488). The move runs through `files.complete_prd`.
- Task reducers and the job plan, claim and `record_exit` reducers are pure, deep-copying and replay-safe. Job claims are exclusive against re-claim. Plans are append-only, and `validate_plan_shape` checks cycles and unknown dependencies.
- I did not rerun the full suite. Per the caller, it is 2185 passed, 1 xfailed, exit 0.

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
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Doubt lens (rubric D1-D5) plus de-slop, codex, resumed on the cycle-2 thread.

FIX:
[BOB] 🟠 The stale-revision check still races with saga staging. `apply_unlocked` checks one snapshot, then `_run_saga_body` rereads state and stages against that newer revision. Pass the admitted revision into staging and test a lease change between those two reads. | File: plugins/autopilot/controller/autopilot_state/files.py:555 | Task: 17  
[BOB] 🟠 Replay admission treats a ledger row as proof of commit, although the saga appends it before committing. The row also lacks the authorizing actor and request digest. A crash before the append still leaves the original request unable to resume. Bind the durable intent to the authenticated request, resume from its recorded step, and test public retries before and after the append. | File: plugins/autopilot/controller/autopilot_state/protocol.py:269 | Task: 17  
[BOB] 🟠 Derived planning drops completed tasks but retains dependency IDs that point to them. A pending task that depends on a completed task therefore has an unknown job dependency unless that task already has a job row. Resolve dependencies against completed task state and scheduled jobs, and test this resumed plan. | File: plugins/autopilot/controller/autopilot_state/protocol.py:380 | Task: 17  
[BOB] 🟡 Reviewer jobs cannot be derived through the normal handoff. `tasks_done` requires all task rows to be finished, then derivation in `review` selects only unfinished rows. The policy test reaches its reviewer branch by directly seeding a state that the public handoff cannot produce. Derive review work from completed build state and test it after a public handoff. | File: tests/autopilot/test_cycle2_jobs_metadata.py:168 | Task: 17  
[BOB] 🟡 Legacy job rows without metadata are now loadable but permanently unclaimable. `_runnable` says replanning reconciles them, yet `jobs.plan` rejects an existing ID and derivation skips it. Add a bounded way to replace an unclaimed legacy spec and test the upgrade through the dispatcher. | File: plugins/autopilot/controller/autopilot_state/jobs.py:16 | Task: 17  
[BOB] 🟡 `prd.enter` captures `plan_expansion`, but `task.replace` still uses only the caller’s flag. A PRD that denies expansion can receive a plan over the ceiling. Enforce the captured policy and test a conflicting request. | File: plugins/autopilot/controller/autopilot_state/protocol.py:318 | Task: 17  
[BOB] 🟡 Backlog entry verifies that the bytes in `wip` match the parsed bytes. Direct `wip` entry checks only that a regular file still exists, so a replacement can inherit metadata from the old file. Apply the same byte and identity check to direct entry and test a replacement before publication. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:406 | Task: 17  
[BOB] 🟡 HEAD capture accepts any successful Git output, while state validation requires a 40-character SHA-1. A SHA-256 repository can reach the backlog rename and then fail state publication. Validate the Git result before any move and align both schemas with the supported object formats. | File: plugins/autopilot/controller/autopilot_state/lifecycle.py:340 | Task: 17  
[BOB] 🟡 The published contract adds a `job.next` request and fixtures but still lacks its expanded success result. Add the result shape and validate an actual dispatcher response and its persisted receipt against the shipped contract. | File: plugins/autopilot/contracts/controller/workflow-v1.json:1604 | Task: 19  
[BOB] 🟡 Caller and stored JobSpec definitions duplicate every property and differ only in required keys. Reference the stored shape from the caller definition and require the three extra keys there. | File: plugins/autopilot/contracts/controller/workflow-v1.json:713 | Task: 19  
[BOB] 🟡 The updated delivery receipt records 2,185 passes and zero failures but omits the known expected failure. Include the xfail count in the delivery evidence so it matches the supplied test result. | File: docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json:31 | Task: 12  
[BOB] 🟡 The packed-reference test uses a disjunctive fixture check. Assert that `packed-refs` contains the tested branch and that its specific loose ref is absent. | File: tests/autopilot/test_cycle2_entry_tasks.py:120 | Task: general  
[BOB] 🟡 The earlier-epoch test remains flagged for having no direct assertion. Keep the rejection helper and assert the persisted task still carries its original status and start epoch. The earlier- and same-epoch tests both pass on the base, so keep them as controls for the new missing-start refusal case. | File: tests/autopilot/test_controller_rework13_recovery.py:158 | Task: 20  
[BOB] 🟡 The mechanical replay reports five contract tests, the empty-array test, and the malformed JobSpec test passing on the base. Keep the unchanged expectations as controls and isolate the new contract behavior. The empty-array test’s malformed case checks only Python validation, although the shipped JSON Schema now defines row shapes. Validate both instances against JSON Schema and remove the stale comment. | File: tests/autopilot/test_controller_rework13_contracts.py:48 | Task: 19  
[BOB] 🟡 The mechanical replay reports 18 entry/task cases passing on the base. Separate retained controls from regressions and pair malformed metadata cases with a valid record carrying the same new fields, so rejection of an unknown key cannot satisfy the test. | File: tests/autopilot/test_cycle2_entry_tasks.py:232 | Task: 17  
[BOB] 🟡 The mechanical replay reports four job-metadata cases and the populated-plan owner recovery test passing on the base. Keep complete-spec and owner-recovery cases as controls. For legacy specs, assert the stored state loads successfully before checking that dispatch refuses the claim. | File: tests/autopilot/test_cycle2_jobs_metadata.py:307 | Task: 20  
[BOB] 🟡 Five replay/pause tests pass on the base. The three stale requests become stale before dispatch, and the pause boundary hook never observes a state after marker removal. Inject the revision change after admission and observe the state immediately after the marker-clear transaction. | File: tests/autopilot/test_cycle2_replay_pause.py:109 | Task: 17  

VERIFY:
- (none)

KNOWN:
[BOB] 🟠 The full suite’s single strict xfail covers the still-open review acceptance gap. The batch ledger assigns evidence-backed acceptance to AP00020. Until that work lands, the passing integration path still relies on a bare `converged` claim. | File: tests/autopilot/test_controller_rework13_lifecycle.py:131 | Task: 18  
[BOB] ⚪ The entry crash test passes on the base and records `source: wip` on retry. It now exercises the real interrupted entry, but preserving the original `backlog` source requires durable metadata that the batch ledger defers beyond task 18’s test-only scope. | File: tests/autopilot/test_controller_rework13_lifecycle.py:65 | Task: 18  

R1: fail  
R2: fail  
R3: fail  
R4: fail  
R6: pass  
R7: fail  
R8: pass  
R9: fail  
R10: fail  
R11: pass  
R12: pass  
R13: pass  

D1: pass  
D2: pass  
D3: pass  
D4: pass  
D5: pass

## Carl

Backend: gemini via the `use-gemini` helper, exit 0, non-empty output.

[CARL] 🟡 test_finish_rejects_an_inprogress_status_from_an_earlier_lease_epoch has no assertion: it only proves the code does not raise | File: tests/autopilot/test_controller_rework13_recovery.py:158 | Task: general
[CARL] 🟡 test_enter_captures_the_head_commit_of_a_repository_whose_refs_are_packed hedges with `or`: either outcome satisfies it | File: tests/autopilot/test_cycle2_entry_tasks.py:120 | Task: general

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

Verdict: 40 findings
Tests: 2185 passed, 0 failed, 0 skipped (exit 0) (suite run this cycle; 1 xfailed)
