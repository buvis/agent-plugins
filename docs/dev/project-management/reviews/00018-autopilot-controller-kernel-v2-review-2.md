---
prd: docs/dev/project-management/prds/wip/00018-autopilot-controller-kernel-v2.md
review: 2
date: 2026-11-11
head_sha: da798294f5c48c92f3610f28458181bd6202d78e
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: codex unavailable (usage limit), claude fallback ran the doubt prompt
  carl: available (copilot/gemini-3.8-flash, one retry for the missing R5 verdict)
  eve: available
dispatch_rows:
  bob: d33c717e
  carl: 79391de7
---

# Review: 00018-autopilot-controller-kernel-v2

Diff range: `292f893e16d64ada8fe4933acb8b0ede539d20aa..da798294f5c48c92f3610f28458181bd6202d78e` (incremental — cycle 1 reviewed the full `dacba71..292f893` range)

codex_rung_guard: fired (7 codex-implemented task(s))

Tests: 1571 passed, 1 failed, 0 skipped (suite run this cycle)

## Cycle notes (read these before the findings)

**Incremental scope.** Cycle 1's review file carries `head_sha 292f893`, so this
cycle diffed only the rework commits since then (124 KB, `--since 292f893`).
Reviewers had two jobs: verify each cycle-1 finding is resolved, and hunt for
regressions the rework introduced. Unchanged code was not re-reviewed.

**Bob ran on Claude, not codex.** `codex-run.sh` exited 1 on both the
thread-resume and the fresh-session attempt. A direct probe returned
`You've hit your usage limit ... try again at 8:09 AM`, so this is the
quota class, with no complete review in the sidecar to salvage. Per the
doubt-lens fallback rule a Claude subagent ran Bob's exact assembled doubt
prompt (rebuilt with Read-tool instructions in place of the read-only-shell
instructions), so the doubt lens did not drop. `codex_thread_id` is deliberately
omitted from this file's frontmatter: codex produced no review this cycle.

**Carl needed his one retry.** His first dispatch omitted the `R5` per-rule
verdict. The retry re-dispatched the same prompt plus the verdict correction
and returned all thirteen verdicts, `R5: fail` among them. Both runs produced
the same three findings. First output kept at
`docs/dev/tmp/carl-output-ap00018-c2.first.txt`.

**The test gate is red, and the cause is this PRD's own code.** The staged gate
run reported `0 passed, 0 failed, 0 skipped` because the untracked gate wrapper
`docs/dev/tmp/ap00018-gate.sh` could not parse pytest's `1572 passed in 599.47s`
summary — its `sed` patterns require a non-digit before the count, which a
line-initial count does not supply. The wrapper was fixed (prepend a space
before matching) and `autopilot verify` re-run at HEAD: **1571 passed, 1 failed**,
the failure being
`test_controller_store_guards_v2.py::StoreGuardTest::test_competing_initializers_publish_exactly_one_intact_winner`
with `FileNotFoundError: [Errno 2] ... 'state.json.lock'` raised as
`StateIOError` from `store.py:253`. The earlier run of the same wrapper, at the
same HEAD and the same pinned Python 3.12, passed 1572/1572. So the test is
genuinely flaky (the brief measured 2/10), not version-gated. Alice independently
reproduced it and attributed it to Python 3.15 — that attribution is wrong for
this cycle's evidence, because the failing run used `--python 3.12`. It is
carried below as R45. `last-verification.json` now records the real counts.

**Four hand-corrected consensus cells.** `consolidate_findings.py` matches
citations on `path:line`, so it left three single-voice rows for one fail-open
defect in `verify_listed_paths_match_revision` (R17, R20, R26, three different
lines of the same function), two for one documentation defect (R21, R35) and two
for one frozen-fixture gap (R36, R42). Each group was raised by two or three
reviewers, so the surviving row's Consensus cell is corrected to the true count
and the duplicates are recorded in the ledger as duplicates of it. The
corrections are stated inline in each row. Without them the mechanical
single-voice rule in `review-close` would have discarded a three-voice defect.

**Consolidation merged two distinct findings into R3.** The script's
suffix-stripping merge folded Bob's `protocol.py:158` finding (staging admission
bypassed in `existing_open`) onto Alice's `protocol.py:74` finding (request
fixtures contradict the runtime). They are separate defects in one file; the
decision gate treats R3 as covering both, and R19 carries the bootstrap half of
the same admission gap.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/5] | 🟠 | R3 is only one-quarter fixed. The rework added only the `_cleanup_stale_temps` divergence entry. `provenance.json` still says "Configuration characterization only. No runtime has been extracted or certified" (line 78). It still lists "runtime implementation and runtime test execution" as unverified (line 1165). About 11 `test_map` rows still target null with "runtime ... pending" notes (lines 1098-1153). The successor receipt still certifies this file as passed. The new `test_provenance_staging_divergence.py` only keyword-matches `json.dumps` of the divergence list, so it does not check scope, `test_map` or `file::test` targets. | plugins/autopilot/contracts/controller/provenance.json:78 | 12 | ALICE, BOB, EVE |
| R2 | [3/5] | 🟠 | The R7 tests are tautological. `test_accepts_reconciled_job_ids_with_multiple_entries`, `..._a_single_entry` and `test_accepts_empty_reconciled_job_ids` assert nothing, so they only prove no exception. All four tests in the file pass against the pre-change code, because the fix is in `workflow-v1.json` and `protocol.validate_payload` is unchanged. Nothing in the file would fail if the schema regressed to `maxItems: 0`. Replace them with a test that checks a non-empty `reconciled_job_ids` request against `workflow-v1.json` and expects `rejected_evidence` from `owner.apply_locked`, or delete the file. | tests/autopilot/test_controller_kernel_recover_jobs.py:21 | 12 | ALICE, BOB, EVE, mech-check |
| R3 | [3/5] | 🟠 | The fixture-vs-runtime gap is still there, so the settled R12 reason no longer holds. That discard was conditional on R7's fix covering the family. The R7 diff touches only the `recover-nonempty-jobs` fixture and leaves `parse_request` unchanged. `parse_request` run over every request fixture: `null-existing-actor`, `bootstrap-nonzero-revision` and `bootstrap-acquire` are all marked `valid:false` / `invalid_request`, and all three still parse successfully. The controller can answer differently from the pinned contract. `recover-nonempty-jobs` now says `expected_error: null`, but the controller returns `rejected_evidence` for it. No test applies fixture cases through the controller. (Merged by consolidation: Bob's separate finding that staging admission is still bypassed in `protocol.existing_open:158` — an authenticated new-request `workflow.open` commits a revision with no `actors.admit_staging`, so with 65+ retained temporaries `owner.acquire` refuses while this path still publishes. Eve probed the same gap on the bootstrap path, `actors.py:428` (R19): with 70 retained temporaries the identical bootstrap request still returns ok at revision 0. This row's fix covers all three: the fixture/runtime alignment, `existing_open` admission and bootstrap-reconciliation admission.) | plugins/autopilot/controller/autopilot_state/protocol.py:74 | general | ALICE, BOB, EVE |
| R4 | [3/5] | 🟡 | R9 traceability is mostly unresolved. A search of `tests/autopilot` finds only `lost_ack_replay` (`test_controller_bootstrap.py`). The other PRD-named scenarios appear nowhere by name: `kernel_equivalence`, `concurrent_cas`, `corrupt_state_recovery`, `lease_exclusion`, `wrong_actor`, `epoch_revoked`, `fresh_open_replay`, `unsupported_operation_refused`. Task 13 added the missing `test_controller_actors.py` file but deliberately did not name or alias the covering tests. | tests/autopilot/test_controller_actors.py | 13 | ALICE, BOB, EVE |
| R5 | [3/5] | 🟡 | `AuthenticateTest.test_a_missing_path_is_reported_as_credential_rejected_not_credential_required` pins a quirk. `authenticate` raises `BindingError("credential required")` inside its own `try` that catches `ValueError`, so that message is dead. The test codifies the dead branch instead of fixing it or leaving it uncovered. Fix the exception shape in `authenticate` (`actors.py:292`), or drop the test. It also covers only the `path is None` case, not the mismatch or secret-digest paths. | tests/autopilot/test_controller_actors.py:92 | 13 | ALICE, BOB, EVE |
| R6 | [2/5] | 🟠 | R6 is unproven at the reworked head: no CI run exists at or after da79829, and the most recent `autopilot` job (run 42881113193, 2026-11-10T19:09Z, PR branch `chore/renovate-shared-preset`) still fails on `test_new_helper_files_are_owned_and_digested_from_current_bytes` with `fatal: path 'plugins/autopilot/README.md' exists on disk, but not in '50c8c2f...'`. `fetch-depth: 0` is on the right job and addresses the named cause, but nothing has exercised it. master is 23 commits ahead of origin. | .github/workflows/validate.yml:63 | general | BOB, EVE |
| R7 | [2/5] | 🟡 | The R11 oversize test does not pin the new guard. `test_controller_bundle_reproducible_check_rejects_an_oversized_committed_bundle` passes against the old `matches()`, which read the whole file and compared it, so it also returned False and gave exit 1. The `st_size != len(expected)` check added in `matches()` is only a memory optimisation, so the test cannot fail if the guard is removed. Spy on `Path.read_bytes`, or on the exporter's `matches`, and assert the oversized file is never read. | tests/autopilot/test_controller_export.py:394 | 15 | ALICE, BOB |
| R8 | [2/5] | 🟡 | The R5 reconciliation test covers only the file-count ceiling, using 64 six-byte orphans. The byte ceiling (16 MiB) and repeated recovery crashes, which R5 asked for, are untested on the `finish_intent` path. The refusal test asserts only `error_code is not None`, not the expected `recovery_required`. | tests/autopilot/test_controller_owner_recovery_staging_budget.py:60 | 12 | ALICE, EVE |
| R9 | [2/5] | 🟡 | Prior R15 survives the R1 dedup and the map regeneration exactly as reported: listed controller rows still carry `evidence.status: "passed"` with `tested_package_revision: 441b15c...` beside `acceptance_cases[0].status: "planned"`, "AP00018 delivery evidence is still planned" and "AP00018 is on hold", because the refresh loop rewrites only digest and evidence | tools/autopilot/update_helper_map.py:631 | 14 | BOB, EVE |
| R10 | [2/5] | 🟡 | The 7-line git init/config/add/commit/rev-parse block is duplicated verbatim in both new successor tests | tests/autopilot/test_helper_provenance_successor.py:485 | 14 | BOB, EVE |
| R11 | [2/5] | ⚪ | `update_helper_map.py` is now 799 lines, one under the 800-line limit, so the next edit breaches it. Plan a split, for example moving the successor and receipt functions into a module. | tools/autopilot/update_helper_map.py:799 | 14 | ALICE, BOB |
| R12 | [1/5] | 🟠 | The pin test can only resolve a `test_map` target that is a method of its own TestCase (`hasattr(self, row["target"].split("::")[1])`), which is the mechanism forcing those 11 nulls: no target in another test file can be cited without failing | tests/autopilot/test_controller_protocol.py:314 | 12 | BOB |
| R13 | [1/5] | 🟠 | The successor receipt was re-pinned twice by hand (50c8c2f, 8825c40, 441b15c) without re-running its tasks: it still records passed 92 / 69 / 46, while the same commands collect 89 / 71 / 48 at 441b15c (3 guard tests removed, 2 export and 2 successor tests added). The five new rework test files are in no task. The PRD requires truthful current-revision evidence and the design requires "actual test results". | docs/dev/project-management/autopilot/reports/00018-v2-controller-delivery-receipts.json:8 | 14 | EVE |
| R14 | [1/5] | 🟡 | Only 4 of the spec's closed operations are implemented (workflow.open and owner.acquire/release/recover). The contract lists one capability, workflow.core.v1. The spec names workflow.jobs.v1, workflow.reviews.v1 and workflow.records.v1 as capability IDs. They are declared only under x-controller.unavailable_capabilities, and the workflow state schema forces tasks and jobs to be empty. The spec's "publish only implemented kernel operations" wording allows this. Still, the "one installed writer" currently writes only ownership state, not workflow truth. Confirm that is the intended scope for this PRD. | plugins/autopilot/controller/autopilot_state/protocol.py:45 | general | BLAKE |
| R15 | [1/5] | 🟡 | --request and --actor-file paths are opened with O_NOFOLLOW on every ancestor. A request file under a symlinked ancestor, such as macOS /var/folders or /tmp, returns the generic invalid_request or wrong_binding. Reproduced directly: a request file under an unresolved /var/folders temp path failed with invalid_request. This is strict and defensible for containment, but it is undocumented and the error is misleading. Document that callers must pass realpath'd paths. | plugins/autopilot/controller/autopilot_state/actors.py:80 | Phase 1 task 2 | BLAKE |
| R16 | [1/5] | 🟡 | The budget-exhausted test hedges on the error code (`assertIsNotNone(result["error_code"])`), so any refusal passes, and its seeded count is off by one against its own recorded intent: 64 orphans do not exceed `count > STAGING_FILE_LIMIT`; it only refuses because the crashed acquire leaves credential stage files that `ACTOR_ARTIFACT` also counts | tests/autopilot/test_controller_owner_recovery_staging_budget.py:61 | 12 | BOB |
| R17 | [3/5] | 🟡 | `verify_listed_paths_match_revision` fails open. It disables itself silently when the `rev-parse --is-inside-work-tree` probe does not return "true", so R39's stale-receipt guard can vanish with no signal; any `git rev-parse` failure (no repo, dubious ownership, broken GIT_DIR) skips the integrity check; `git` being absent raises an uncaught `FileNotFoundError` from `subprocess.run`; an unresolvable revision (shallow clone, the R6 case) is misreported as "stale ... bytes do not match"; and git's stderr is discarded from that message. (Hand-merged: consolidation left this one defect as three single-voice rows — R17 at :592, R20 at :588, R26 at :1523 — because its file matcher compares `path:line` and these cite different lines of the same function. Three reviewers raised it, so the consensus cell is corrected to [3/5] and R20/R26 are recorded as duplicates of this row.) | tools/autopilot/update_helper_map.py:592 | 14 | BOB, EVE, ALICE |
| R18 | [1/5] | 🟡 | test_accepts_reconciled_job_ids_with_multiple_entries has no assertion: it only proves the code does not raise | tests/autopilot/test_controller_kernel_recover_jobs.py:21 | general | CARL, mech-check |
| R19 | [1/5] | 🟡 | (Covered by R3's fix, which owns all three admission paths.) R5 half fixed: bootstrap intent reconciliation has no staging admission. Probe: pending bootstrap intent plus 70 retained `.state.json.autopilot-*.tmp` files, identical request returns ok at revision 0. Repeated crashes at the init publication boundary still grow orphans without limit. | plugins/autopilot/controller/autopilot_state/actors.py:428 | 12 | EVE |
| R20 | [1/5] | 🟡 | `verify_listed_paths_match_revision` fails open: any `git rev-parse` failure (no repo, dubious ownership, broken GIT_DIR) silently skips the integrity check, and production code is shaped around a test fixture. An unresolvable revision (shallow clone, the R6 case) is reported as "stale ... bytes do not match". | tools/autopilot/update_helper_map.py:588 | 14 | EVE |
| R21 | [2/5] | 🟡 | The R5 and R7 behavior changes are undocumented. README still says only "a bootstrap or owner mutation" refuses and "The next mutation then refuses", while reconciliation of a pending owner intent now refuses too, which makes "pending intent plus over-budget orphans" a state needing the manual procedure where the intent-named stage and rollback files must stay. The CHANGELOG was not touched this cycle: no Unreleased entry records the published-contract change (workflow-v1.json dropping `maxItems: 0` and the resulting `schema_digest`/`fixture_digest` change), and the existing staging entry still says the refusal fires "when the full proposal would exceed either limit", which is not how the new reconciliation check works. (Hand-merged with R35, Bob's CHANGELOG row: one documentation defect raised by two reviewers, so the consensus cell is corrected to [2/5] and R35 is recorded as a duplicate of this row.) | plugins/autopilot/README.md:407 | 12 | EVE, BOB |
| R22 | [1/5] | 🟡 | [MECH] 9 tests pass at base. | tests/autopilot/test_controller_actors.py | 13 | EVE, mech-check |
| R23 | [1/5] | 🟡 | [MECH] 3 tests pass at base. | tests/autopilot/test_controller_export.py | 15 | EVE, mech-check |
| R24 | [1/5] | 🟡 | [MECH] 1 test passes at base. | tests/autopilot/test_controller_owner_recovery_staging_budget.py | 12 | EVE, mech-check |
| R25 | [1/5] | 🟡 | [MECH] 1 test passes at base. | tests/autopilot/test_helper_provenance_successor.py | 14 | EVE, mech-check |
| R26 | [1/5] | ⚪ | `verify_listed_paths_match_revision` fails open. Outside a git work tree, or with `git` unavailable (an uncaught `FileNotFoundError` from `subprocess.run`), it either skips the check or crashes without a message. A relocated or tarball checkout would regenerate and certify with no staleness check. The git stderr is also discarded from the "stale" message. Consider failing closed when `--successor` is used outside git, with the fixture opting out explicitly. | tools/autopilot/update_helper_map.py:1523 | 14 | ALICE |
| R27 | [1/5] | ⚪ | The unavailable-capability list invents IDs beyond the spec's set: workflow.policy.v1, lifecycle, tasks, custody, verification. Minor extra surface, not harmful. | plugins/autopilot/contracts/controller/workflow-v1.json:811 | general | BLAKE |
| R28 | [1/5] | ⚪ | The README intro still says "Only the two local facade operations documented at the end are current". The controller CLI and its four operations are now also current, so the statement is stale. | plugins/autopilot/README.md:3 | Phase 2 task 2 | BLAKE |
| R29 | [1/5] | ⚪ | Several acceptance scenario names from the PRD do not appear as test names: lease_exclusion, wrong_actor, epoch_revoked, fresh_open_replay, kernel_equivalence, concurrent_cas, corrupt_state_recovery and unsupported_operation_refused. Equivalent behavior is covered under other names, for example test_two_independent_subprocess_acquires_have_exactly_one_winner and test_real_process_cas_allows_exactly_one_writer_for_the_same_revision. Traceability to the PRD's named scenarios is weak. | tests/autopilot/test_controller_owner.py:176 | general | BLAKE |
| R30 | [1/5] | ⚪ | The lock wait is an unbounded blocking flock. The README says callers must bound execution time, which matches the spec's "bound time in clients". No server-side timeout exists. | plugins/autopilot/controller/autopilot_state/store.py:234 | Phase 1 task 1 | BLAKE |
| R31 | [1/5] | ⚪ | store.restore and _restore_locked are retained from the source but are not exposed through the CLI, matching "no generic restore CLI". They are dead code for the public surface. | plugins/autopilot/controller/autopilot_state/store.py:181 | Phase 1 task 1 | BLAKE |
| R32 | [1/5] | ⚪ | `OWNER_OPERATIONS` is a mutable `set` now read cross-module as a dispatch gate; the new test patches it with a frozenset | plugins/autopilot/controller/autopilot_state/protocol.py:17 | 12 | BOB |
| R33 | [1/5] | ⚪ | R9's traceability half is unresolved: the declared file now exists, but exactly the same 8 PRD acceptance scenarios appear nowhere by name (kernel_equivalence, concurrent_cas, corrupt_state_recovery, lease_exclusion, wrong_actor, epoch_revoked, fresh_open_replay, unsupported_operation_refused) | N/A | 13 | BOB |
| R34 | [1/5] | ⚪ | The cycle-2 review context's Test gate block reads "Tests: 0 passed, 0 failed, 0 skipped (suite run this cycle)" while the same gate run passed 1572 at the same head; a reader of the review artifact alone cannot tell the suite ran | docs/dev/tmp/review-context-ap00018-c2.md:587 | general | BOB |
| R35 | [1/5] | ⚪ | No Unreleased entry records this cycle's published-contract change (workflow-v1.json dropping `maxItems: 0`, and the resulting `schema_digest`/`fixture_digest` change in the pinned bundle), and the existing staging entry still describes the refusal as "when the full proposal would exceed either limit", which is not how the new reconciliation check works (orphans only, empty proposal) | plugins/autopilot/CHANGELOG.md:36 | general | BOB |
| R36 | [2/5] | ⚪ | No fixtures scenario records that nonempty `reconciled_job_ids` is refused with `rejected_evidence`: the requests case now reads `valid: true` with reason "not supported" and the bundle says nothing about the runtime refusal, so the kernel rule the design states ("requires ... reconciled_job_ids empty") is gone from the frozen contract. (Hand-merged with R42, Eve's row on the same fixture: consolidation kept them apart on issue wording although both cite `fixtures-v1.json:462`, so the consensus cell is corrected to [2/5] and R42 is recorded as a duplicate of this row.) | plugins/autopilot/contracts/controller/fixtures-v1.json:462 | 12 | BOB, EVE |
| R37 | [1/5] | ⚪ | `test_reconciliation_succeeds_well_under_the_staging_budget` passes against the pre-change code | tests/autopilot/test_controller_owner_recovery_staging_budget.py:68 | 12 | BOB, mech-check |
| R38 | [1/5] | ⚪ | `test_successor_is_accepted_when_listed_files_match_its_revision` passes against the pre-change code | tests/autopilot/test_helper_provenance_successor.py:505 | 14 | BOB, mech-check |
| R39 | [1/5] | ⚪ | The new receipt pin turns any later edit of a listed path into a red suite until `package_revision` is re-pinned, including a dirty work tree and a CI merge commit where master moved under the branch | tools/autopilot/update_helper_map.py:581 | 14 | BOB |
| R40 | [1/5] | ⚪ | R2's fix adds a fifth function-local import to the actors/owner/protocol cycle instead of one shared home, and its test pins the lookup mechanism by monkeypatching three module globals; it asserts a mis-dispatch as the desired outcome and breaks under the fix R2 actually asked for. | plugins/autopilot/controller/autopilot_state/actors.py:412 | 12 | EVE |
| R41 | [1/5] | ⚪ | The divergence test passes if any entry mentions any of four keywords, with two redundant precondition asserts. | tests/autopilot/test_provenance_staging_divergence.py:17 | 12 | EVE |
| R42 | [1/5] | ⚪ | After the flip, fixture `recover-nonempty-jobs` is `valid: true` with reason "not supported", and no scenario freezes `rejected_evidence` for nonempty `reconciled_job_ids`. The kernel rule is gone from the frozen contract. | plugins/autopilot/contracts/controller/fixtures-v1.json:462 | 12 | EVE |
| R43 | [1/5] | ⚪ | `finish_intent` admits with an empty proposal, so each crash during reconciliation can still add one state-sized temporary above the ceiling before the next attempt refuses. | plugins/autopilot/controller/autopilot_state/owner.py:197 | 12 | EVE |
| R44 | [1/5] | ⚪ | Rework tasks 13-15 had no independent test writer and tasks 12-15 no patch review (`failed:runner_auth` four times), against the PRD's "do not ... omit test/review roles". | docs/dev/project-management/meta/assumptions.md:171 | general | EVE |
| R45 | [2/5] | 🟠 | The suite is red at HEAD on the project's own pinned Python 3.12: `test_competing_initializers_publish_exactly_one_intact_winner` fails with `FileNotFoundError: [Errno 2] ... 'state.json.lock'`, surfaced as `StateIOError: state lock failed .../state.json.lock` from `store.py:253`, while the same wrapper at the same HEAD passed 1572/1572 on an earlier run. Two competing initializers race on the lock file: one unlinks or replaces it between the other's directory open and its `openat`, so a legitimate concurrent initializer gets an I/O error instead of losing the CAS cleanly. This is the PRD's own concurrency guarantee ("exactly one intact winner") failing intermittently, not a test-only artifact, and the fix belongs in the lock-acquisition path. | plugins/autopilot/controller/autopilot_state/store.py:253 | general | gate-run, ALICE |

## Alice

See `docs/dev/tmp/alice-output-ap00018-c2.txt`. Nine findings: one 🟠 (R1,
provenance.json still contradicts the shipped runtime), four 🟡, four ⚪.
Verified cycle-1 R6, R7, R39, R1, R2, R11, R20, R22 and R36 as resolved; R3 and
R9 as partly resolved; did not re-raise settled R4, R15 or R16. Ran
`scripts/validate.py` (pass) and the full suite under Python 3.12. She
reproduced the `store.py` lock failure and attributed it to Python 3.15; this
cycle's own 3.12 gate run contradicts that attribution, so it is carried as R45.

R1: pass, R2: fail, R3: pass, R4: pass, R6: pass, R7: pass, R8: pass, R9: fail,
R10: pass, R11: pass, R12: pass, R13: pass

## Blake

See `docs/dev/tmp/blake-output-ap00018-c2.txt`. Blind, PRD-only, as every
cycle. No Critical or High. Seven findings: two 🟡, five ⚪. Ran two narrow
pytest selections (65 and 66 tests, all passing, no skips), the validator, a
`--json contract` byte-comparison against the committed bundle, a sha256 check
against the README-documented digest, and a manual open/acquire/release/replay
smoke test in a temp root. All nineteen blind rubric rules pass.

B1-B19: all pass

## Bob

See `docs/dev/tmp/bob-output-ap00018-c2.txt`. **Codex was quota-exhausted;** a
Claude subagent ran his exact assembled doubt prompt, so the doubt lens held.
Twenty-two findings: four 🟠, seven 🟡, eleven ⚪, bucketed 16 FIX / 1 VERIFY /
5 KNOWN. All 8 mechanical input lines accounted for.

D1: pass, D2: pass, D3: pass, D4: pass, D5: pass

R1: fail, R2: fail, R3: pass, R4: pass, R6: pass, R7: pass, R8: pass, R9: fail,
R10: pass, R11: pass, R12: pass, R13: pass

## Carl

See `docs/dev/tmp/carl-output-ap00018-c2.txt` (backend copilot, model
gemini-3.8-flash). Three 🟡 findings, all on the assertion-free tests in
`test_controller_kernel_recover_jobs.py`. First dispatch omitted `R5`; the one
retry returned the complete verdict set.

R1: pass, R2: fail, R3: pass, R4: pass, R5: fail, R6: pass, R7: pass, R8: pass,
R9: pass, R10: pass, R11: pass, R12: pass, R13: pass

## Eve

See `docs/dev/tmp/eve-output-ap00018-c2.txt`. Twenty-three findings: three 🟠,
twelve 🟡, eight ⚪, bucketed 16 FIX / 1 VERIFY / 6 KNOWN. Probed the controller
CLI in three temp project roots and confirmed, by execution, that bootstrap
reconciliation and `existing_open` both still publish over the staging budget
while `owner.acquire` refuses on the same store. Also re-counted the successor
receipt's task evidence (89 / 71 / 48 collected against the pinned 92 / 69 / 46).

D1: pass, D2: pass, D3: pass, D4: pass, D5: pass

Verdict: 45 findings
Tests: 1571 passed, 1 failed, 0 skipped (suite run this cycle)
