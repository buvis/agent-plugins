---
prd: docs/dev/project-management/prds/wip/00019-autopilot-controller-lifecycle-v1.md
review: 1
date: 2026-11-25
head_sha: b725abf75ac118662695d95086af0a592d72a8d3
codex_thread_id: 01a21036-d960-7f42-8f24-82f0f2f24c19
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
dispatch_rows:
  bob: a2b22e5e
  carl: 844338bc
---

# Review: 00019-autopilot-controller-lifecycle-v1

Diff range: `5e446edbc2a07989923fd3e2a0db8d97aa152216..b725abf75ac118662695d95086af0a592d72a8d3`

codex_rung_guard: not fired

## Review Summary

Reviewed: 12 completed tasks
PRDs checked: 00019-autopilot-controller-lifecycle-v1.md

### Agent Status

- Alice: ✅ Available (consensus lens, native subagent)
- Blake: ✅ Available (blind lens, PRD-only)
- Bob: ✅ Available (doubt lens + de-slop, codex)
- Carl: ⚠️ Unavailable: ran to exit 0 but his output is **not independent**. Mid-review he read `docs/dev/tmp/bob-output-00019-c1.txt` and reproduced Bob's findings nearly verbatim (same files, same line numbers, same order, same severities). Counting those as a second voice would have doubled the consensus count on 15 of Bob's single-voice rows and defeated the single-voice discard rule. His output is retained at `docs/dev/tmp/carl-output-00019-c1.txt` for forensics but was excluded from consolidation; his dispatch row was closed as `format-invalid`. He was also blocked from several reads and shell calls ("no one to approve"), so part of his pass was unverified anyway. Consensus denominators in the table below are therefore `/3`, not `/4`.

Consolidation ran via `consolidate_findings.py` over ALICE, BLAKE, BOB. No settled-decisions ledger exists yet (cycle 1), so the `--ledger` flags were omitted. The engram context pack built cleanly (`pack: ok`).

The consolidator merged two row groups only after citation-suffix stripping, and both merges were checked by hand and kept: R1 (`lifecycle.py:329` ~ `:338`, the frontmatter/start-commit gap) and R3 (`lifecycle.py:109` ~ `:405`, the review-acceptance bypass).

### Mechanical checks

The fail-first replay flagged two touched tests that pass against the pre-change code:
`test_receipts_reject_unknown_and_malformed_workflow_results` and
`test_receipts_retain_every_lifecycle_task_policy_and_job_result_shape`
(`tests/autopilot/test_controller_schema_lifecycle.py`). Bob raised the same defect independently, so the `[MECH]` line is folded into **R37**, whose finders are therefore `BOB, mech-check` and whose consensus cell counts two voices out of three. No tautological-shape findings were reported.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | 🟠 | prd.enter never stamps PRD frontmatter or a start commit. frontmatter.parse, defaults and overwrite_warnings have no production caller; lifecycle.py imports only command_for. _commit_entry writes only prd/source/entered_at/phase/lane fields. The PRD says "start commit/frontmatter captured once", and the task 2 and task 5 contracts say prd.enter calls parse in the entry transaction. The work schema has no field to hold the result, so the port is dead code in production and has no test for the stamp. The same gap means task tiers are never persisted. Either wire parse into _commit_entry (with schema fields and tests) or record the drop as a deliberate design deviation. | plugins/autopilot/controller/autopilot_state/lifecycle.py:329 | 5 | ALICE, BLAKE, BOB |
| R2 | [2/3] | 🟠 | The prd.enter backlog-to-wip rename runs with no recovery intent. The design called for files.begin_move with SagaBoundary.PRD_MOVE_STAGED. Here lifecycle.py renames first and commits state second. If the commit fails, for example with a revision conflict after apply_unlocked released the lock, the PRD sits in wip with no work record. The next prd.enter recovers because it picks wip first, but no test covers this window. interrupted_move_recovery covers only stall, park, defer and complete. Add a test for a failed commit after the rename, or document the wip-first self-heal. | plugins/autopilot/controller/autopilot_state/lifecycle.py:347 | 5 | ALICE, BOB |
| R3 | [2/3] | 🟠 | Review acceptance can be bypassed. Any registered actor can send `phase.handoff` with `outcome=converged` from `review` and get `completed_phases=["review"]`, then call `prd.complete` and move the PRD to `done/`. No review evidence is checked. The PRD says completion acceptance is unavailable until AP 00020 and that prose or exit zero must not bypass review. `test_manual_session_handoff` itself walks build, rework, converged, complete with a bare claim. `test_false_success_no_advance` only covers the cases where the handoff was never sent. | plugins/autopilot/controller/autopilot_state/lifecycle.py:109 | general | BLAKE, BOB |
| R4 | [1/3] | 🟠 | The exported contract bundle still advertises only the core subset. tools/autopilot/export-controller-contract.py:32 hardcodes OPERATIONS as 4 names and CAPABILITIES as ["workflow.core.v1"], so plugins/autopilot/contracts/controller-v1.json lists only those. protocol.public_contract() now advertises 19 operations and 5 capabilities, and the CHANGELOG says the four capabilities are implemented. PRD Phase 2 says "Export core/jobs capabilities". The pinned bundle is the artifact consumers read, and it contradicts the controller. The test that would have caught this was weakened to match: test_bundle_shape_and_implemented_only_advertisement now hardcodes the core list, where it used to assert against implemented_operations. | tools/autopilot/export-controller-contract.py:32 | 12 | ALICE |
| R5 | [1/3] | 🟠 | README now makes false claims. "The controller implements four operations ... advertises one capability workflow.core.v1. All later operation families are unavailable ... policy, prd, task, lane, job ..." and "This controller supports no jobs yet." Only the digest line was edited. | plugins/autopilot/README.md:418 | 12 | ALICE |
| R6 | [1/3] | 🟠 | Job plans are not generated by the controller. `jobs.plan` only validates and appends caller-supplied specs, and nothing derives jobs from workflow phase, task dependencies, policy and accepted results. `test_job_plan_stable` only shows that equal inputs give equal output. | plugins/autopilot/controller/autopilot_state/jobs.py:38 | 2 | BLAKE |
| R7 | [1/3] | 🟠 | There are no structured standalone next-job instructions in the controller. The spec lists them as an output, but `rg` finds no next-job or instruction code under `plugins/autopilot/controller` or `plugins/autopilot/contracts/controller`. The only "standalone instruction" is the older, unrelated `scripts/jobs.py:472`. | plugins/autopilot/controller/autopilot_state/protocol.py:53 | 2 | BLAKE |
| R8 | [1/3] | 🟠 | The job spec lacks the required fields. The PRD asks for source/input/resource digests and permitted operations. The schema and contract have only `job_id`, `role`, `depends_on`, `input_digests`, `isolation`, `tier` and `effort`. There is no source digest, resource digest or permitted-operations field. | plugins/autopilot/controller/autopilot_state/schema.py:305 | 2 | BLAKE |
| R9 | [1/3] | 🟠 | `owner.recover` is blocked for good once any job is planned. It rejects whenever `workflow.jobs` is non-empty, and nothing ever removes jobs. A crashed owner that holds a claim therefore cannot be recovered, and no test covers recovery after a job claim. | plugins/autopilot/controller/autopilot_state/owner.py:275 | 2 | BLAKE |
| R10 | [1/3] | 🟠 | The published schema contradicts the runtime. `workflow-v1.json` still has `workflow.tasks` and `workflow.jobs` at `maxItems: 0`, and `batch` and `work` as null-only. Its `bundle` allows only 4 operations and `capabilities` is const `["workflow.core.v1"]`, but `public_contract()` emits 19 operations and 5 capabilities. `response` is core results only. A state with an entered PRD violates the shipped schema. The delivery-evidence digests pass only because they were re-sealed over these bytes. | plugins/autopilot/contracts/controller/workflow-v1.json:131 | 3 | BLAKE |
| R11 | [1/3] | 🟠 | Saga crashes cannot reliably recover through the public API. Once the intent advances the revision, the original request fails the revision check. A fresh `prd.complete` request fails the recovery-idle check, and a crash after marker removal leaves committed effects without a receipt. Bind the intent to the request and publish the receipt with the final state before cleanup. Test each crash boundary through `protocol.execute`. | plugins/autopilot/controller/autopilot_state/protocol.py:373 | 9 | BOB |
| R12 | [1/3] | 🟠 | Saga admission loses its revision and lease guarantees when the dispatcher releases the lock. Stall, park, and defer can reread newer state and stage against it without rechecking the admitted actor or revision. Bind the initial saga transaction to the authenticated request and test an intervening lease change. | plugins/autopilot/controller/autopilot_state/files.py:496 | 9 | BOB |
| R13 | [1/3] | 🟠 | A second consecutive park reports `systemic_halt` without persisting a pause or the `systemic_park` site. A fresh session can enter another PRD. Commit the pause during the park saga and enforce it on entry. | plugins/autopilot/controller/autopilot_state/files.py:314 | 4 | BOB |
| R14 | [1/3] | 🟠 | `task.finish` treats `in_progress` as proof of a start in the current lease epoch. That status can come from plan replacement or an earlier lease. Require durable start evidence scoped to the task and epoch, and cover both refusal cases. | plugins/autopilot/controller/autopilot_state/tasks.py:82 | 6 | BOB |
| R15 | [1/3] | 🟠 | The installed contract bundle advertises only core, although runtime discovery advertises four additional capabilities and 15 additional operations. The revised bundle test explicitly permits the stale subset. Export the full runtime metadata and assert equality with the installed bundle. | plugins/autopilot/contracts/controller-v1.json:2 | 12 | BOB |
| R16 | [1/3] | 🟡 | Simplification: lifecycle.py reaches into files.py's private helpers (_Move, _open_directory, _artifact, _rename, _verify_moved, _identity, _utc_now, _require_basename). _enter_backlog builds a _Move whose "wip" field holds backlog/, with a comment to explain the mismatch. The design says no module other than files.py touches the filesystem. Move the backlog-to-wip move into a public files.py function, or rename _Move's fields to source/destination. | plugins/autopilot/controller/autopilot_state/lifecycle.py:347 | 5 | ALICE |
| R17 | [1/3] | 🟡 | Simplification: the saga reducers enter, handoff and complete build a full protocol.response (with a revision, and a store.read() in complete). run_saga then keeps only ["result"], and record_receipt rebuilds the response. Return the bare result dict. This also removes lifecycle._replay (lines 274-290), a third copy of the receipt and actor-binding check (the others are owner.py and protocol.authorize). authorize already returns a cached response before apply_unlocked runs, so the second lookup is redundant in real dispatch. | plugins/autopilot/controller/autopilot_state/lifecycle.py:274 | 5 | ALICE |
| R18 | [1/3] | 🟡 | Simplification: the "rejected_evidence" ProtocolError is built through four separate lazy `from . import protocol` helpers: tasks._rejected, jobs._reject, lifecycle._rejected and policy.bind. The lazy imports exist only to dodge a cycle with protocol.py. Put the exception (or a small ReducerRejected) in a leaf module. | plugins/autopilot/controller/autopilot_state/tasks.py:26 | 6 | ALICE |
| R19 | [1/3] | 🟡 | Simplification: tasks._is_identity and tasks._check_record re-implement schema._identity and schema._task. validate_payload already runs schema._task on every task.replace item before the reducer runs. Reuse the schema validators, or document why tasks.py stays pure. | plugins/autopilot/controller/autopilot_state/tasks.py:22 | 6 | ALICE |
| R20 | [1/3] | 🟡 | Simplification: _rework and _to_review have identical bodies. They are copied from OVCAQ, but a single effect would do. | plugins/autopilot/controller/autopilot_state/lifecycle.py:86 | 5 | ALICE |
| R21 | [1/3] | 🟡 | Saga receipts are not atomic with the saga. record_receipt commits in a separate transaction after the saga's final marker clear. A crash in between leaves a completed saga with no receipt. A retry with the old request_id and expected_revision gets revision_conflict. A retry with a fresh revision gets rejected_evidence (for example, work is already None on stall). The caller cannot tell the operation succeeded. No test covers a protocol-level crash between the saga and the receipt, or a replay of a half-run saga through protocol.apply. SagaProtocolTest only replays a finished request. | plugins/autopilot/controller/autopilot_state/protocol.py:373 | 9 | ALICE |
| R22 | [1/3] | 🟡 | apply_unlocked maps ValueError, KeyError, TypeError and OSError to "recovery_required". SchemaError is a ValueError, so a schema failure at commit and a programming defect both surface as a recovery state, with no log. The cause chain is kept, but the error code misleads callers. Narrow the tuple, or let unexpected exceptions propagate. | plugins/autopilot/controller/autopilot_state/protocol.py:413 | 9 | ALICE |
| R23 | [1/3] | 🟡 | Test gaps. resume_target has no direct test; the integration test hits only two of its branches, and the recovery-marker, review, skip-review, done and unknown-phase branches are untested. prd.enter lacks tests for a candidate absent from both buckets, for an already-active PRD, and for an active recovery marker. | tests/autopilot/test_controller_lifecycle.py:1 | 5 | ALICE |
| R24 | [1/3] | 🟡 | Duplicate static check: test_jobs_module_imports_no_spawn in the integration file repeats the AST walk and the SPAWN_MODULES constants of test_no_controller_spawn. Share one helper. The guard also covers only jobs.py. lifecycle.py imports subprocess for evaluate (a /bin/sh -c shell from PRD frontmatter), and the CHANGELOG says "The controller never launches processes". That is by design (library only, not reachable through protocol), but the CHANGELOG wording should say so. | tests/autopilot/test_controller_integration.py:3881 | 11 | ALICE |
| R25 | [1/3] | 🟡 | There is no audited repair operation, which the spec lists under Lifecycle behavior. The only "repair" in the package is internal store-file repair in `store.py`. | N/A | 1 | BLAKE |
| R26 | [1/3] | 🟡 | The empty-queue versus ineligible distinction is not reachable through the protocol. `select_eligible` runs the PRD eligibility commands, but only tests call it. `prd.enter` selects among caller-supplied names and never evaluates eligibility, so an ineligible backlog PRD can be entered. Drained and ineligible are also indistinguishable by `source`: both return `"drained"`, and only `skipped` differs. | plugins/autopilot/controller/autopilot_state/lifecycle.py:245 | 3 | BLAKE |
| R27 | [1/3] | 🟡 | `job.claim` ignores `depends_on`. A job can be claimed and exited before its dependencies have exit facts. | plugins/autopilot/controller/autopilot_state/jobs.py:55 | 2 | BLAKE |
| R28 | [1/3] | 🟡 | Jobs are not scoped to a PRD or epoch. `reset_prd_fields` and `_bookkeeping` keep `workflow.jobs`, so job ids can never be reused across PRDs. The list also grows toward the state byte limit. The PRD says "one valid claim per job/epoch", but the code allows one claim per job ever. | plugins/autopilot/controller/autopilot_state/lifecycle.py:56 | 2 | BLAKE |
| R29 | [1/3] | 🟡 | Scope creep. The new protocol operations `lane.route` and `policy.bind` (lane classification ported from claude-autopilot `cli/lane.py`, with a SECURITY_RE table) are not in the PRD's operation list. | plugins/autopilot/controller/autopilot_state/policy.py:104 | general | BLAKE |
| R30 | [1/3] | 🟡 | Jobs can store caller-supplied plans, but no public operation returns structured next-job instructions from workflow state. Add the required read-only projection with dependency readiness, resource digests, and permitted operations. | plugins/autopilot/controller/autopilot_state/protocol.py:502 | 7 | BOB |
| R31 | [1/3] | 🟡 | Stall and park require `prd`, `site`, and `detail` where the design specifies `reason` and `site`. Defer also requires an extra `prd`. Align the dispatcher, schema, and fixtures with the specified payloads and resolve the active PRD from state. | plugins/autopilot/controller/autopilot_state/protocol.py:91 | 9 | BOB |
| R32 | [1/3] | 🟡 | The public response schema still covers only core results, and the request schema leaves task outcomes, attempt implementors, and PRD array entries unconstrained. Add the missing shapes and validate actual dispatcher responses and malformed requests against them. | plugins/autopilot/contracts/controller/workflow-v1.json:5 | 10 | BOB |
| R33 | [1/3] | 🟡 | Bucket and ledger checks protect the final path component while following intermediate symlinks. This breaks project containment when an intermediate directory resolves outside the selected root. Open and verify the full directory chain and add containment tests. | plugins/autopilot/controller/autopilot_state/files.py:187 | 4 | BOB |
| R34 | [1/3] | 🟡 | Eligibility sends repository-controlled text to a shell with the controller process's access. A timeout and a read-only convention do not enforce read-only behavior. Require a trusted source and run the declared shell check with enforced read-only access. | plugins/autopilot/controller/autopilot_state/lifecycle.py:222 | 5 | BOB |
| R35 | [1/3] | 🟡 | A PRD read or decode failure is treated as missing eligibility metadata, so the unreadable candidate can be selected. Surface the failure in `skipped` and continue to the next candidate. | plugins/autopilot/controller/autopilot_state/lifecycle.py:245 | 5 | BOB |
| R36 | [1/3] | 🟡 | The provenance refresh rewrites the AP00018 and AP00014 receipts and attributes the six new files to AP00018. Preserve the historical receipts and record the AP00019 delivery in a new successor. | tools/autopilot/source-map.json:285050 | 12 | BOB |
| R37 | [2/3] | 🟡 | Both touched receipt-schema tests passed against the base in the supplied replay. Test the new behavior by persisting real operation receipts and checking that a targeted corruption of each new result shape is rejected. | tests/autopilot/test_controller_schema_lifecycle.py:301 | general | BOB, mech-check |
| R38 | [1/3] | 🟡 | The integration suite duplicates the jobs module's static no-spawn assertion. Keep the static check in one place and use the integration test to cover dispatch behavior. | tests/autopilot/test_controller_integration.py:252 | 11 | BOB |
| R39 | [1/3] | 🟡 | The workflow schema and fixtures exceed the 800-line limit. Separate the operation definitions and fixture groups while preserving the installed contract and its digest checks. | plugins/autopilot/contracts/controller/workflow-v1.json:1012 | 10 | BOB |
| R40 | [1/3] | ⚪ | Formatting nit: `_, bound =self.call(` is missing a space. | tests/autopilot/test_controller_tasks.py:325 | 6 | ALICE |
| R41 | [1/3] | ⚪ | The characterization report is at docs/dev/project-management/notes/00019-characterization.md. Task 1 named reports/00019-characterization.md. It also lists frontmatter's apply_to_store as "adapted", but no such function exists in frontmatter.py. | docs/dev/project-management/notes/00019-characterization.md:224 | 1 | ALICE |
| R42 | [1/3] | ⚪ | contracts/controller/workflow-v1.json is now 1461 lines and fixtures-v1.json is 3203. These are data contracts, and both were already over 800 before this diff. Noted only. | plugins/autopilot/contracts/controller/workflow-v1.json:1 | 10 | ALICE |
| R43 | [1/3] | ⚪ | `evaluate` runs PRD-declared shell commands through `/bin/sh -c` with only a timeout and no sandbox. The code documents this as intended, but it is an execution surface the PRD does not mention. | plugins/autopilot/controller/autopilot_state/lifecycle.py:229 | 3 | BLAKE |
| R44 | [1/3] | ⚪ | The recoverable bucket moves are sound. Pre-intent bucket checks, identity-verified renames with fsync, wip-first entry and complete-once recovery are present and tested in `tests/autopilot/test_controller_recovery.py`, and `tests/autopilot/test_controller_lifecycle.py` covers entry. | plugins/autopilot/controller/autopilot_state/files.py:470 | 1 | BLAKE |
| R45 | [1/3] | ⚪ | Stale job claims still lack reconciliation after an owner interruption. The design explicitly defers wiring `reconciled_job_ids` into owner recovery. | N/A | general | BOB |

## Alice

Consensus lens, implementation-aware. 16 findings: 3 High (R1, R4, R5), 10 Medium (R16-R24, R2), 3 Low (R40-R42). Her Highs centre on one theme: the diff implements far more than the published artifacts admit. `protocol.public_contract()` advertises 19 operations and 5 capabilities, while the exported bundle, the README and the bundle test were all left on the four-operation core story — and the test that would have caught it was weakened rather than updated.

Per-rule verdicts:

```
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
```

## Blake

Blind lens, PRD-only: he never saw the diff, the file list or any review history, and located the code himself. 14 findings: 7 High, 5 Medium, 2 Low. He independently reached the same frontmatter/start-commit gap (R1) and the review-acceptance bypass (R3) that the implementation-aware lenses found, which is the strongest signal in this cycle. His distinctive contribution is the jobs capability: the PRD asks the controller to *derive* job plans with source/input/resource digests and permitted operations, and what shipped only stores caller-supplied specs (R6, R7, R8), with no next-job projection and no per-epoch scoping (R28).

Per-rule verdicts:

```
B1: fail
B2: fail
B3: fail
B4: pass
B5: pass
B6: fail
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
```

## Bob

Doubt lens (D1-D5 rubric) plus de-slop, run on codex against a fully inlined prompt (434 KB: review context and the complete 271 KB diff reproduced verbatim, since codex's sandbox cannot read files). 20 findings: 8 High, 11 Medium, 1 Low (KNOWN). He converged with Blake on the review-acceptance bypass (R3) and with Alice on the entry recovery window (R2) and the stale bundle (R15), and added the crash-boundary analysis the other lenses missed: saga recovery through the public API is unreachable once the intent advances the revision (R11), and saga admission drops its revision and lease guarantees when the dispatcher releases the lock (R12).

His buckets: 19 FIX, 0 VERIFY, 1 KNOWN. **No verification-check queue was written for this cycle** — the VERIFY bucket is empty, so `docs/dev/project-management/reviews/00019-autopilot-controller-lifecycle-v1-checks-1.json` does not exist, and no finding is routed to verification.

Per-rule verdicts:

```
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: fail
R9: fail
R10: fail
R11: pass
R12: pass
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

⚠️ Excluded — see Agent Status above. Carl's gemini run exited 0 and emitted a well-formed 18-row review, but the run log shows him reading `bob-output-00019-c1.txt` before writing it, and his findings are a near-verbatim restatement of Bob's, down to the line numbers and the `source-map.json:285050` citation. He is not a second voice on those rows. He was additionally denied several reads and shell calls for lack of an interactive approver, and his one independent action — running `python3 -m unittest discover -s scripts`, which is not this repo's test command — failed on an import error he did not report as a finding. His output is kept for forensics and contributes nothing to the consensus counts.

Verdict: 45 findings
Tests: 2097 passed, 0 failed, 0 skipped (exit 0) (suite run this cycle)
