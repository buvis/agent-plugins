# AP 00012 bounded recovery

## Failure Capture
- Session / task: interactive recovery, 2026-10-28; AP 00012 task 20.
- Goal in progress: make the unfinished foundation resumable so dependent PRDs can become eligible.
- Error: every backlog eligibility check fails; the launcher calls this `backlog drained`.
- Last successful step: cycle 1 review consolidated; 19 tasks completed and two repair tasks queued.
- Last failed tool / command: plan-tasks rejected the 13,229,895-byte source map against the 75,000-token replan budget.
- Repeated pattern seen: automatic replanning treats the entire data file as model input; subsequent launches skip the held prerequisite.
- Environment assumptions verified: PRD 00012 is in hold; no live state exists; the archived pre-replan state retains tasks, attempts, review receipts and work base. The installed dispatch procedure already uses the valid build phase for recovery.

## Recovery Action
- Diagnosis chosen: a context-sizing failure, followed by correct dependency exclusion and misleading drain reporting.
- Smallest action: prepare bounded JSON projections and guarded updates, then restore the archived work with sequential repair slices. Do not apply the archived candidate or declare either finding resolved.
- Why safe: all existing data, source identities, completed tasks, attempt history and review receipts remain authoritative. Updates reject stale inputs, changes outside their selected rows, removed identities and oversized diffs.
- Proof required: helper mutation tests; measured complete persona renders below 50,000 bytes; actual projected-input estimates below 75,000 tokens; selector and resume checks against the restored state.

This is an operator-authorized recovery plan, not another invocation of the failed whole-file planner. Large structured data is processed by a local program; only the selected records and relevant source lines enter model context. Estimates include those exact inputs, task text and the existing 55,000-token overhead. The 75,000-token planning budget, 50,000-byte dispatch budget, 100K worker input guard, cycle 1 and cap 3 remain unchanged. Every actual dispatch must still be rendered and measured by the installed renderer. Splitting does not permit excerpting a task's diff for review.

The two original findings remain open. After bounded repairs, the original task 20 owns the whole-map closure gate; task 21 owns the changelog repair. Rework must then hand off to a fresh full review session with every required lens. No PRD is moved to done by this recovery.

## Verified recovery, 2026-10-29

- Restored through the installed `autopilot restore` CLI under the autocodex loop lock; moved the unchanged PRD from hold to wip.
- 43 tasks: all 19 original completed task objects are identical; 22 sequential data slices precede original task 20's independent closure tests and original task 21's changelog correction. These are children of one existing repair group, not 22 new findings.
- Original failed task-20 attempt, cycle-1 review artifacts/receipts, applied review batches, work base and rework cap are unchanged. The reviewed implementation audit remains unchanged. New recovery-tool implementation has raw native model evidence in `00012-recovery/implementation-evidence.json` for the next cycle audit.
- The selector picks 00012 from wip. `routing.rework_resume` returns true; the host's `adapter.review_gap` returns no gap. Actual `driver.py --dry-run` routes to cycle-1 rework on `gpt-6.1-sol/low`, not bootstrap/drained. No new agent run was launched from this recovery session.
- Sizing includes fresh snapshot bytes, bounded source/proposal inputs, helper and tests, task text, contract allowance and the unchanged 55,000-token overhead. Maximum estimated task context: 73,008 tokens. The installed renderer accepted every measured prompt; the two closure tasks also have reserved future-diff/test capacity. Runtime renders remain mandatory.
- Temporary-copy rehearsal applied all 22 *unreviewed* candidate slices through the guarded updater in 13.83 seconds: 710 resulting edges, every original identity retained, all other collections unchanged, and every complete per-task diff below 24,000 bytes. This tests the recovery mechanism, not the semantic correctness of those candidates. The real source map and inventory remain byte-unchanged.
- Verification: original full Autopilot suite plus the first 11 helper tests: **100 passed**; after final diff-helper improvements and an additional regression case: **12 helper tests passed**. Validator tests: **12 passed**. Repository validator: **3 packages / 15 skills**. CLI show/apply smoke test and diff whitespace check passed.

## Skeptical self-review

Ten concrete doubts were adjudicated:

1. **FIX — slow real-data diff.** Python difflib stalled on the repetitive 13 MB map. Replaced it with a bounded Git text diff; the complete rehearsal then finished in 13.83 seconds.
2. **FIX — duplicate worker input.** Preview and write originally printed the same full diff. Write now emits a short size acknowledgement; preview retains the full diff.
3. **FIX — misleading diff content.** Normalizing temporary names across the entire diff could alter string data in the displayed patch. Normalize header lines only; a regression test preserves matching data literals.
4. **FIX — redundant artifacts.** Removed per-task JSON duplicates and per-slice diff copies after measurement. The canonical prepared-state snapshot, bounded inputs, original candidate and sizing evidence suffice.
5. **VERIFY — silent loss of work/history.** Compared all 19 completed task objects, original failed attempts, review-cycle records, applied batches, cap and work base against the archive: identical.
6. **VERIFY — another bootstrap drain.** Schema, selector, rework routing, receipt guard and the real launcher dry run all accept the recovered state.
7. **VERIFY — hidden budget overflow.** Measured complete persona renders, fresh snapshots and sequential full diffs. The worst estimate remains below 75K; the dispatch cap remains 50KB. No whole map or inventory is a model input.
8. **KNOWN — semantic repair remains unfinished.** Candidate proposals require the normal implementor/reviewer pipeline and independent whole-package closure tests. Declaring them correct here would bypass the requested review boundaries. The original two findings remain open and their tasks remain pending.
9. **VERIFY — temporary legacy-count failure.** The installed work procedure runs narrow checks per task and the full suite once after all tasks. Original task 20 retains the independent replacement for the legacy exact-202 premise before that final gate.
10. **FIX — micro-lane compatibility.** Task 21 now explicitly honors the source's Edit-only rule if code routes it through micro; it still reads only the bounded asset row and verifies the untouched complement.

Slop review removed duplicate task/diff artifacts and duplicate tool output. The helper's separate diff function is an actual process boundary needed for bounded runtime; its scope, stale-snapshot, identity and preservation tests exercise recovery behavior, not library internals. The second pass verified the fixes and found no additional blocking defect.

## Agent Self-Debug Report
- Session / task: interactive AP 00012 recovery; native session `01a184a7-c0b9-7b32-a084-b9b6bf06686a`.
- Failure: held prerequisite caused every dependent backlog PRD to be skipped.
- Root cause: treating a large structured-data artifact as an indivisible model input, then treating no eligible PRDs as an empty backlog.
- Recovery action: guarded bounded IO, pre-sized serial repair tasks, preserved review history, canonical restore and wip selection.
- Result: success for recovery/resume; implementation and review convergence remain pending.
- Token / time burn risk: no whole-file redispatch; 22 bounded slices replace the original oversized patch. Existing per-task and review caps still apply.
- Follow-up needed: run autocodex in a fresh session; finish queued repair and all required review lenses before marking 00012 done. Its dependent PRDs become eligible only afterwards.
- Preventive change to encode later: the shared selector/launcher should distinguish an empty backlog from a nonempty backlog whose eligibility checks all fail. Its installed `drained` wording remains unchanged in this project-local recovery.
