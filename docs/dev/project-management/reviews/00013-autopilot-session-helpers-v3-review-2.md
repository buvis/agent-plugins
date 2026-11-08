---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v3.md
review: 2
date: 2026-11-08
head_sha: 921efc5354a25a7a26607991303e735809bf8a90
codex_thread_id: 01a1bb4c-039d-73e2-b812-7bf04cb26d94
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: aa20a4a9
  carl: 28e86346
---

# Review: 00013-autopilot-session-helpers-v3

Diff range: `feca0d1a519c46fd2782d1cfd29f5ba4d14ac36e..921efc5354a25a7a26607991303e735809bf8a90`

codex_rung_guard: not fired

## Review Summary

Reviewed: 8 completed tasks (T1-T4 from cycle 0, tasks 5-8 from the cycle-1 rework)
PRDs checked: 00013-autopilot-session-helpers-v3.md
Scope: incremental — the cycle-1 rework only. Cycle 1 reviewed the full work range.

### Agent Status

- Alice (consensus, Claude subagent, opus/high): available
- Blake (blind lens, Claude subagent, PRD-only, opus/high): available
- Bob (doubt lens + de-slop, codex, static-only sandbox, resumed thread
  01a1bb4c): available
- Carl (UI/design, gemini-run backend=copilot): available
- Eve (doubt lens, Claude Fable 5.1, claude-fable-5-1): available

Notes recorded loud rather than smoothed over:

- **The staged test gate was skipped**, not run: `review-stage`'s
  `reuse_verdict` refused because the working tree is dirty outside the store
  (untracked `.herdr/icon.svg`, foreign dirt unrelated to this PRD, left
  alone). `autopilot verify` refuses on the same condition, so the four gate
  commands were run bare instead and the staged context's `## Test gate`
  section was patched by hand with their real results before any reviewer was
  dispatched. No `last-verification.json` was written this cycle. The `Tests:`
  line below therefore comes from those four bare runs, not from a reused
  record.
- **Bob's prompt was the inlined shape**, rebuilt to 246953 bytes over the
  30266-byte staged render. His dispatch row's `prompt_bytes` understates what
  codex received; the row was not re-opened by hand.
- **Dispatch message shape**: Alice went out in her own message, then Blake,
  then Eve plus the two CLI lanes plus the Watcher. The skill asks for one
  single message; the reviewers still ran concurrently and no lane waited on
  another, but the deviation is recorded.
- **Carl exited 0** this cycle (cycle 1 needed a salvage) and published a
  complete review: all twelve `R{n}` verdicts and `[CARL] ✅ No issues found`.
  He ran his own narrow test selections rather than the full suite.
- **Consensus engine**: `legacy` (single Alice subagent). No `review-fanout`
  run, so no `consensus_run_id`.
- **Engram context pack**: ok.
- **Settled-decisions ledger**: 12 entries from cycle 1 were fed to Alice, Bob,
  Carl and Eve and passed to `consolidate_findings.py` as `--ledger` with
  `--ledger-dismiss BLAKE`. **No row was auto-dismissed.** Blake's R5 below is
  cycle-1 R12 at the identical `log_sink_refusal.py:141`, so the mechanical
  matcher should have caught it and did not; the gate dismissed it by judgment
  instead and recorded the dismissal in the ledger. Treat the matcher's miss as
  a real gap, not as evidence the finding is new.

### Mechanical absorption

The staged context carried two `[MECH]` 🟡 lines, both from the fail-first
replay block, and no tautological-shape lines. Eve relayed both, so both
already had rows: `mech-check` was appended to R19 and R20 and their severity
raised from ⚪ to the 🟡 the mechanical line states.

### Carried-forward verification checks

Cycle 1's queue (`00013-autopilot-session-helpers-v3-checks-1.json`) holds one
entry and it carries **no `result`** — the queued `rg` for artifact-sink
parent-swap coverage was never run and never recorded. Per the carry-forward
rule that is a finding this cycle: it is folded into R4, whose `Found By` gains
`verify-check` and whose severity is raised to 🟡 (an unpinned race under mixed
spelling is a coverage gap, not a shown defect). This cycle's queue
(`-checks-2.json`) is empty: Eve's VERIFY bucket is `(none)`, and Bob's single
VERIFY item is the same R4 row, which is swept as a task rather than routed.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/5] | 🟡 | The receipt's `package_revision_note` says the per-task T1-T4 measurements were taken at 6888765, not at the re-pinned revision. This is disclosed honestly and the historical entries were preserved. But the receipt does not describe the product bytes at the pin. | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:6 | 4 | BLAKE, BOB |
| R2 | [2/5] | ⚪ | The task 5 deferral of R6 rests on the claim that the file is "outside task 5's write set" and "at 799 lines". Changing the two direct `_symlinked_component(..., given_root, given_root)` calls to a 2-argument form adds no lines. The ledger rows in state.json also mark the same R6 issue "auto-fixed / fixed by review-close" while a second row says "deferred, not fixed", so the two disagree. | plugins/autopilot/scripts/log_sink_refusal.py:164 | 5 | ALICE, EVE |
| R3 | [2/5] | ⚪ | The edit that removed ", and leaves no reusable artifact after a failed write or close" left the first `--verify` bullet's list without its conjunction: "...stops the child's leftover processes when a sink fails late, removes only a leaf it created; ...". It needs "and" before "removes". | plugins/autopilot/CHANGELOG.md:33 | 6 | ALICE, EVE |
| R4 | [3/5] | 🟡 | Prior R17 has a queued check but no recorded result establishing artifact-parent race coverage. Run `rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py`; inspect matching tests for mixed root/artifact spellings, a post-preflight parent swap, controlled refusal and unchanged sentinel bytes. Record the covering node or add the missing case. | docs/dev/project-management/reviews/00013-autopilot-session-helpers-v3-checks-1.json:7 | 1 | BOB, EVE, verify-check |
| R5 | [1/5] | 🟠 | `_root_anchor` accepts ANY leading prefix whose realpath equals the root, so a third spelling is trusted. A path such as /outside/back/x.log (back -> root) gets `refuse()` == None and `_pinned_parent_fd` opens it. I reproduced this with a temp repo. The PRD says a path "not under the root by either root spelling raises before any descriptor opens" and that a path returning through a symlink to the root itself is refused. The new tests only cover paths that start under the root spelling (tests/autopilot/test_helper_recovery_v3.py:387-434), so this gap is untested. The write still lands inside the root, and the components below the prefix are O_NOFOLLOW-pinned, so it is not an escape. It is still a contract deviation. | plugins/autopilot/scripts/log_sink_refusal.py:141 | 1 | BLAKE |
| R6 | [1/5] | 🟡 | Git missing or not executable still tracebacks out of `stage_review`. `_is_inside_git_dir` now fails closed (review_stage.py:420). But `_resolve_roots` calls `_toplevel` (review_stage.py:606), and `_destination_problem` and `_repo_problem` call it too. These go through `dirty_tree._git`, which has no timeout and no OSError handling (plugins/autopilot/scripts/dirty_tree.py:19). With PATH lacking git, `_resolve_roots` raised FileNotFoundError in my run. The T3 tests stub only the `--is-inside-git-dir` probe, so they pass while the real "git missing" case still crashes. The Phase 1 exit criterion "subprocess probes have explicit timeouts" is also unmet for those `_git` probes. dirty_tree.py is outside the T3 writable paths, so this may be a PRD scoping gap. | plugins/autopilot/scripts/review_stage.py:606 | 3 | BLAKE |
| R7 | [1/5] | 🟡 | T4 asks for the overlapping CHANGELOG `--verify` bullets to be merged into one. plugins/autopilot/CHANGELOG.md:32-37 still has several separate `--verify` bullets that overlap on creation and removal of the artifact and log. The README wording matches the fixed behavior. | plugins/autopilot/CHANGELOG.md:33 | 4 | BLAKE |
| R8 | [1/5] | 🟡 | The receipt's `package_revision_note` says "The gate that does cover the rework's product bytes is recorded in ...00013-helper-recovery-v3.md", and the report (line 36-38) says the feca0d1 gate is "the run that reflects the delivered state". Both are false: feca0d1 is the base of this diff and precedes 81c89e1 (task 5, verification.py `absolute()`), so no recorded gate covers the rework's product bytes; the post-rework gate (19 failed / 1255 passed at 921efc5, unittest 59 OK, validate 3/15, marketplace up to date) exists only in state.json's contract_card. The report header still says "Tested package revision: 6888765" against the 7a55dcd pin. Fix: append a "Gate at the rework head (921efc5)" section to the report with the four exact commands, results and the 8/7/4 controller breakdown, and update the header pin; the report is deliberately unhashed, so no map regeneration follows. | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md:36 | 6 | EVE |
| R9 | [1/5] | ⚪ | The new report section cites its raw gate log at docs/dev/tmp/gate-ap00013-v3-c1.log:467. That tree is gitignored under the working-documents rule, so a reader of the committed report cannot check the summary line. The counts are also written inline, so the evidence is usable. | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v3.md:204 | 6 | ALICE |
| R10 | [1/5] | ⚪ | The five new dup-failure cases pass against the pre-rework code, because they cover the existing T2 branch and not new behavior. They are labelled controls or gap-fill tests, bind to intent (prior bytes preserved, sink closed, token propagated, hook reached), and I accept them. I record it only so the replay row does not reopen it. | tests/autopilot/test_helper_recovery_v3_artifact.py:1181 | 5 | ALICE |
| R11 | [1/5] | ⚪ | `_write_artifact` adds a NUL-byte `pwrite` fallback when `ftruncate` fails, and a reason-suffix message. The spec only asks for truncation through the kept descriptor. This is defensive and low risk. If `os.dup` fails, an existing leaf keeps its earlier record, which the CHANGELOG discloses. | plugins/autopilot/scripts/verification.py:287 | 2 | BLAKE |
| R12 | [1/5] | ⚪ | Prior R6 remains unresolved: duplicate anchor scans and the unused parameter are explicitly deferred. The recorded reason limits task 5 to the relative-root correction and avoids changing existing private-helper test contracts; no new regression is shown. | docs/dev/project-management/autopilot/deferred/202610250001-deferred.json:815 | 5 | BOB |
| R13 | [1/5] | ⚪ | Prior R5 remains explicitly deferred: sibling staging Git probes lack timeout/start-error handling. Their implementation is unchanged and outside T3's specified `_is_inside_git_dir` correction. | plugins/autopilot/scripts/dirty_tree.py:19 | 3 | BOB |
| R14 | [1/5] | ⚪ | CHANGELOG bullet "`--verify` accepts a relative `--project-root` again": the file has only `[Unreleased]` (rg `^## \[`), so no user ever saw the refusal; "again" asserts a released regression that did not exist and the bullet records an intra-release no-op. Fix: fold the relative-root clause into the root-anchored bullet ("whichever way the root is spelled, relative or absolute") and drop the standalone bullet, or at minimum drop "again". | plugins/autopilot/CHANGELOG.md:32 | 5 | EVE |
| R15 | [1/5] | ⚪ | `DUP_CALLS = ("dup", "dup2")`: `_write_artifact` calls only `os.dup` (verification.py:296); patching `os.dup2` is speculative, and the fake's positional-only `(fd, *args)` signature would raise TypeError on a keyword `inheritable=` call to `os.dup2` from unrelated code while the global patch is live. Fix: patch `os.dup` only and delete `DUP_CALLS`. | tests/autopilot/test_helper_recovery_v3_artifact.py:240 | 5 | EVE |
| R16 | [1/5] | ⚪ | R5: sibling Git probes via `dirty_tree._git` (`_toplevel`, `_repo_problem`, `_tracked_problem`) still have no timeout or OSError guard, so a hung or missing git can raise out of `stage_review` before the guarded probe. Out of scope: PRD T3 names `_is_inside_git_dir` only; recorded in state.json `deferred_decisions`. | plugins/autopilot/scripts/dirty_tree.py:19 | 3 | EVE |
| R17 | [1/5] | ⚪ | state.json `autonomous_decisions` carries the R6 issue twice with contradictory actions ("auto-fixed / fixed by review-close" and "deferred, not fixed in task 5"), and `doubts_rubric_verdicts` holds D1-D5 twice (Bob and Eve). Out of scope: workflow state is read-only under the PRD and machine-written by review-close; the deferred journal and assumptions.md carry the truthful disposition. | docs/dev/project-management/autopilot/state.json:355 | general | EVE |
| R18 | [1/5] | ⚪ | Commit 1539f6d's subject "prune slop from [D1] tests/autopilot/test_helper_recovery_v3_artifact.py" names the task label, but `git show --stat` shows it touched only the recovery report (1+/2-), no test file. Out of scope: history on master; amending needs a force push, which is not authorized. | N/A | 8 | EVE |
| R19 | [2/5] | 🟡 | [MECH] 5 dup tests pass at base: they pin the pre-existing `os.dup` failure branch that R1 asked to test (present since a1aa604, so at feca0d1); the replay cannot tell a pin of retained behaviour from a missing pin. | tests/autopilot/test_helper_recovery_v3_artifact.py:268 | 5 | EVE, mech-check |
| R20 | [2/5] | 🟡 | [MECH] 28 relative_root tests pass at base: the `refuse` cases pass absolute candidates (a relative root already resolved via realpath at base), the absolute-output CLI runs never hit the None anchor, and the stays-refused controls got the same `unsafe-artifact-path` slug at base; the 5 relative-output success cases are the fail-first pins of 81c89e1 and the replay shows exactly 5 failed at base. | tests/autopilot/test_helper_recovery_v3_relative_root.py:106 | 5 | EVE, mech-check |
| R21 | [1/5] | ⚪ | The receipt's `reviewed_head_gate.log` and the report cite `docs/dev/tmp/gate-ap00013-v3-c1.log`, a gitignored scratch file, as the raw evidence; only the inline counts are durable. | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:139 | 7 | EVE |

## Decision gate dispositions

No 🔴 CRITICAL row. One 🟠 HIGH row (R5), discarded as a settled cycle-1 call —
see the ledger entry quoted below. Every disposition is also in
`00013-autopilot-session-helpers-v3-ledger.json` (12 → 30 entries).

- **R1 — swept (tail sweep).** Two voices on real stale delivery evidence. The
  task carries R8's remedy verbatim.
- **R3 — swept (tail sweep).** Two voices, mechanical prose fix, verified
  present at `plugins/autopilot/CHANGELOG.md:33`.
- **R4 — swept (tail sweep).** Two voices plus the carried-forward unrun check.
  The one real coverage gap this cycle.
- **R5 — settled deferral, discarded.** Identical to cycle-1 R12 at the same
  line; designed root-alias anchoring, and the raiser concedes containment
  holds.
- **R2, R6, R12, R13, R16 — settled deferral, discarded.** Restatements of the
  settled cycle-1 R5 and R6 deferrals, both out of PRD scope.
- **R7 — discarded, contradicts verified facts.** Misreads T4: the overlap T4
  names was merged at `CHANGELOG.md:33`; lines 34-37 are distinct behaviours.
- **R8 — discarded, duplicate of R1.** Same defect; its remedy is the swept R1
  task's text.
- **R9, R11, R14, R15, R17, R18, R21 — discarded, single-voice.** Medium or Low
  raised by one reviewer; each raiser's own text files it as accepted or out of
  scope.
- **R10, R19, R20 — discarded, mechanical replay controls.** Same class as
  cycle-1 R13/R14/R19/R20: the replay cannot distinguish a pin of retained
  behaviour from a missing pin, and cycle-1 R1 asked for exactly that pin.

The ledger entry that decides R5, verbatim from the `reason` field:

> settled in cycle 1 as the same finding at the same line (cycle-1 R12, ledger
> disposition discarded): the shortest-prefix anchor is the designed root-alias
> behaviour, and the PRD's own sentence 'a symlinked ancestor of the root stays
> allowed' is what it implements. Blake is the only raiser in both cycles and in
> both he concedes the write lands inside the root with every below-prefix
> component O_NOFOLLOW-pinned, so containment holds and nothing escapes. The
> cycle-2 re-raise adds a reproduction but no fact that breaks the cycle-1
> reason, so the settled call stands.

## Alice

Implementation-aware consensus lens, Claude subagent at high effort. She
verified 7 of 9 prior findings resolved, 1 partly (R4, the stale gate record),
1 not at all (R6, the recorded deferral), and raised four new ⚪ rows (R2, R3,
R9, R10). She did not rerun the suite and relied on the supplied gate; she did
run `git diff --stat 7a55dcd cabae3d` and confirmed the receipt's no-product-
drift claim holds.

R1: pass
R2: pass
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

## Blake

Blind lens, PRD-only, Claude subagent at high effort. He found the code
himself and relied on the supplied test gate rather than rerunning the suite.
Five findings (R5 🟠, R6 🟡, R7 🟡, R11 ⚪, and the receipt pin row folded into
R1). He verified by reading code: per-component `O_NOFOLLOW` with no `resolve()`
below the root, no later root-resolving stop in `_symlinked_component`,
truncation through a descriptor dup'd at the start, `(dev, ino)`-guarded unlink,
`LC_ALL=C` with the 60-second probe timeout, and the split
`effort_configured`/`effort_served` receipt fields.

B1: fail
B2: pass
B3: pass
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: fail
B18: pass
B19: pass

Blake's four `fail` verdicts are his own R5, R6 and R7 rows. The gate's
dispositions above resolve all four: R5 and R6 against the cycle-1 ledger and
the recorded deferrals, R7 against the PRD text and the file as it now reads.

## Bob

Doubt lens plus de-slop, codex in the static-only sandbox, resumed on his
cycle-1 thread 01a1bb4c so he verified his own prior critique rather than
re-reviewing from zero. One FIX (the stale gate pointer, folded into R1), one
VERIFY (R4's queued `rg`), two KNOWN (the settled R5 and R6 deferrals).

FIX:
- [BOB] 🟡 The new `package_revision_note` says the recovery report contains a gate covering the reworked product bytes, but that report's latest full gate is still `feca0d1`, before the relative-root fix. Append the supplied `921efc5` gate results to the report and point the receipt there; preserve historical runs. This is a new broken evidence pointer introduced by re-pinning. | File: docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:6 | Task: 7

VERIFY:
- [BOB] ⚪ Prior R17 has a queued check but no recorded result establishing artifact-parent race coverage. Run `rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py`; inspect matching tests for mixed root/artifact spellings, a post-preflight parent swap, controlled refusal and unchanged sentinel bytes. Record the covering node or add the missing case. | File: docs/dev/project-management/reviews/00013-autopilot-session-helpers-v3-checks-1.json:7 | Task: 1

KNOWN:
- [BOB] ⚪ Prior R6 remains unresolved: duplicate anchor scans and the unused parameter are explicitly deferred. The recorded reason limits task 5 to the relative-root correction and avoids changing existing private-helper test contracts; no new regression is shown. | File: docs/dev/project-management/autopilot/deferred/202610250001-deferred.json:815 | Task: 5
- [BOB] ⚪ Prior R5 remains explicitly deferred: sibling staging Git probes lack timeout/start-error handling. Their implementation is unchanged and outside T3's specified `_is_inside_git_dir` correction. | File: plugins/autopilot/scripts/dirty_tree.py:19 | Task: 3

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Bob's single `R9: fail` is his FIX row above, swept as R1.

## Carl

UI and design specialist, gemini-run on the copilot backend. Exit 0, complete
review. He read the context, the diff and the engram pack, checked file and
function sizes with `wc` and an `ast` walk, and ran narrow selections
(`test_helper_recovery_v3_artifact.py`, `test_helper_recovery_v3_relative_root.py`,
`test_helper_recovery_v3.py`, the provenance tests, and the three repo
validators) rather than the full suite.

[CARL] ✅ No issues found

R1: pass
R2: pass
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

## Eve

Doubt lens, Claude Fable 5.1 (`claude-fable-5-1`). Twelve findings: 5 FIX, 0
VERIFY, 7 KNOWN. She verified prior-finding resolution in code rather than from
the task table, ran pyflakes on the three touched Python files (clean), the
queued R17 `rg`, `git diff --stat` for both receipt revision claims,
`git show --stat` for 81c89e1 and 1539f6d, and a scratch script exercising
`refuse` under four root spellings against six candidates (identical verdicts
to the absolute root in all cases, confirming the R7 fix). She did not rerun
the full suite. She left one scratch file in the gitignored tree,
`docs/dev/tmp/eve-refuse-sibling-check.py`, because `rm` is warden-gated.

FIX (all five appear above as R8, R4, R14, R3 and R15):
- [EVE] 🟡 stale gate pointer in the receipt and report → R8, swept as R1
- [EVE] ⚪ cycle-1 VERIFY R17 has no recorded outcome; the artifact-sink parent-swap race under mixed spelling stays unpinned → R4, swept
- [EVE] ⚪ CHANGELOG "again" asserts a released regression that never existed → R14, discarded single-voice
- [EVE] ⚪ the merged `--verify` bullet lost its conjunction → R3, swept
- [EVE] ⚪ `DUP_CALLS` patches `os.dup2` speculatively → R15, discarded single-voice

VERIFY:
- (none)

KNOWN (all seven appear above as R16, R2, R17, R18, R19, R20 and R21).

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Follow-up Tasks Created

Three tail-sweep tasks from the converging cycle's two-voice Medium/Low rows
(R1, R3, R4). No `[C2]` retry and no `[D2]` CRITICAL rework task: the table
carries no critical row and no unresolved high row, so no rework design ran.

Verdict: 21 findings
Tests: 1255 passed, 19 failed, 0 skipped (suite run this cycle)

The 19 failures are the pre-existing AP 00018 controller deferral (8 in
`test_controller_capacity.py`, 7 in `test_controller_owner.py`, 4 in
`test_controller_owner_recovery.py`), a recorded external blocker this PRD must
not mask, delete, xfail or relabel. Gate commands at 921efc5, all run bare
because the staged gate refused on the untracked `.herdr/icon.svg`:
`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`
→ 19 failed, 1255 passed in 489.25s; `python3 -m unittest discover -s scripts`
→ Ran 59 tests, OK; `python3 scripts/validate.py` → 3 plugin packages, 15
skills; `python3 scripts/generate_marketplace.py --check` → up to date.
