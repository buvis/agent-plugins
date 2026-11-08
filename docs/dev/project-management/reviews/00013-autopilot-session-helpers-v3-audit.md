# Decision Audit Log: 00013-autopilot-session-helpers-v3

PRD: `00013-autopilot-session-helpers-v3.md`
Started: 2026-11-08T16:36:38Z
Completed: 2026-11-08T16:36:38Z
Autonomous: 36  |  Deferred: 1  |  Doubts: 0

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: v3 design approach for R1, R3 and the git-probe timeout

**Choice**: Shared _root_anchor (shortest realpath prefix equal to root) for refuse and _pinned_parent_fd plus a .. refusal; dup-kept descriptor invalidation (ftruncate, NUL pwrite, reported residual) replacing name-based _empty_pinned; TimeoutExpired/OSError in _is_inside_git_dir fail closed.

**Rationale**: Smallest diff that closes both HIGH rows at one shared primitive; 3 design dispatches, 1 blocker fixed; 9 non-blockers and 4 questions recorded in the design Review log

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: T2 tests would push tests/autopilot/test_helper_recovery_v3.py past the 800-line file limit, and the PRD write-path list names no sibling test file. Where do they go?

**Choice**: Move the failed_artifact tests into a new sibling tests/autopilot/test_helper_recovery_v3_artifact.py (test code only); sink_alias tests unchanged. The 800-line limit binds, and the v3 admission already treats extra test modules as test code (R5).

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: PRD T1(d) artifact-sink parent swap under mixed spelling is pinned for the log sink only; no v3 case swaps the artifact sink's parent under mixed spelling (R17)

**Choice**: routed to verification

**Rationale**: Eve's VERIFY item names an exact command; queued in reviews/00013-autopilot-session-helpers-v3-checks-1.json and run by the work phase's step-7 verification pass: rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R7 is a confirmed public-CLI regression: autopilot verify --project-root . now exits 2 (unsafe-artifact-path) where the base commit accepted it

**Choice**: auto-fix via rework (Protocol D verdict: proceed)

**Rationale**: High touching a documented public CLI option, so Protocol D ran. Verified both ends myself rather than trusting the single reviewer voice: at HEAD refuse(Path('docs/dev/tmp/x.log'), Path('.')) returns 'is a symlink' and _root_anchor returns None, while the same call against the base helper returns None (accepted). The fix is bounded and restores prior behavior, so the verdict is proceed, not escalate. Severity keeps the finding unresolved, so the cycle does not converge and rework runs at cycle 1 of cap 2.

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: `_root_anchor` returns None for any relative path, so `--verify` with a relative `--project-root` (for example `.`) is now refused with `unsafe-artifact-path`. The pre-change code (b786f5a) accepted it. README.md:263 documents `--project-root PATH` with no absolute-path requirement, and the CLI passes `Path(args.project_root)` through unchanged (plugins/autopilot/scripts/autopilot.py:171). `run_verification` builds `root / artifact_path` (plugins/autopilot/scripts/verification.py:469), which stays relative. Reproduced from the repo root: `_root_anchor(Path('docs/dev/tmp/x.log'), Path('.'))` returns None, and `refuse` returns "is a symlink" for it, but None for the absolute spelling. No test covers a relative root, and the CHANGELOG does not mention it. Anchoring on `path.absolute()` (no normalization) in `_root_anchor`, as design dispatch 2 suggested, would keep relative roots working. Or document and test the refusal.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The new `os.dup` failure branch of `_write_artifact` has no test. Pat flagged this as LOW in the recovery report, and `rg` finds no `dup` fault injection in tests/autopilot. The same branch leaves an existing leaf's earlier record in place, where the v2 `_empty_pinned` emptied it. The `_close_result_sink` docstring ("`_write_artifact` already emptied it") and the CHANGELOG ("leaves no reusable artifact after a failed write or close") are therefore not true on that path. The contract keeps this behavior, but it should be tested and the wording narrowed.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The new CHANGELOG bullet fuses two clauses badly. "...and no longer read a nested repository's Git pointer: any symlink there ... is refused" makes the colon explain the nested-repo clause instead of the root-anchored rule. It also duplicates the first bullet's "leaves no reusable artifact after a failed write or close" with the new T2 bullet. Split the symlink rule into its own bullet and drop the repeated clause.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The failed-artifact tests moved to tests/autopilot/test_helper_recovery_v3_artifact.py. That path is not in the PRD's complete write-path list (the PRD names only test_helper_recovery_v3.py). The split is justified because test_helper_recovery_v3.py is at 799 of 800 lines. Record the deviation in the PRD or report. The PRD's Verify line for T2 (`-k failed_artifact` on the old file) no longer selects those tests.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The recovery report and the receipt's T4 entry record only the pre-regeneration gate at 6888765 (24 failed, 1212 passed). They say that "3 failed" provenance nodes are unresolved. The reviewed HEAD run (19 failed, 1217 passed, only the AP 00018 nodes) is recorded in neither file. The delivery evidence is stale against the final state. Record the final run, or state clearly that the final gate lives elsewhere.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: `refuse` calls `_root_anchor` once directly and again inside `_symlinked_component`. That is two realpath scans of the same path, and the `toplevel` parameter of `_symlinked_component` is now unused. Both follow the design contract. Passing the computed anchor in would remove the duplicate work and the dead parameter.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The T1 receipt command contains literal `...`, violating the required exact-command evidence. Recover the complete invocation from its raw log, or record a fresh exact invocation and result without rewriting the historical measurement. Merged with R16 (Eve's same finding at :36, naming the `-k sink_alias ... -q` elision and `duration_seconds: "not captured"`), so this is a two-reviewer finding, not single-voice.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: log_sink_refusal.py:156 refuse computes _root_anchor twice and _symlinked_component's toplevel parameter is dead; passing the computed anchor in would remove both

**Choice**: deferred, not fixed in task 5

**Rationale**: behaviour-preserving tidy-up only (the finding itself says both follow the design contract), but closing it changes the signature of a private helper that two already-committed tests call directly with three arguments (tests/autopilot/test_helper_recovery_v3.py:223 and :293). That file sits at 799 of its 800-line limit and is outside this task's write set, so the cleanup would mean editing a security-critical module's test contract purely to accommodate a micro-optimisation during a cycle whose purpose is closing the R7 HIGH regression. The fix Ivan shipped left log_sink_refusal.py untouched, so neither the duplicate realpath scan nor the dead parameter is newly introduced.

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R1 receipt package_revision_note does not describe the product bytes at the re-pinned revision

**Choice**: swept (tail sweep task)

**Rationale**: cycle 2: two voices (BLAKE, BOB) on real stale delivery evidence; the sweep task carries EVE's R8 remedy verbatim, including the 921efc5 gate section and the report header pin

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R2 task 5's R6 deferral rationale is weak and state.json carries contradictory R6 decision rows

**Choice**: discarded (settled deferral + out-of-scope state artifact)

**Rationale**: cycle 2: the code change it argues for is the settled cycle-1 R6 deferral; the contradictory rows live in machine-written state.json outside this PRD's write paths

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R3 the merged --verify CHANGELOG bullet lost its conjunction before 'removes only a leaf it created'

**Choice**: swept (tail sweep task)

**Rationale**: cycle 2: two voices (ALICE, EVE), mechanical prose fix, verified present at plugins/autopilot/CHANGELOG.md:33

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R4 cycle-1 queued check for artifact-sink parent-swap coverage has no recorded result and the race stays unpinned

**Choice**: swept (tail sweep task)

**Rationale**: cycle 2: two voices (BOB, EVE) plus the carried-forward unrun check from checks-1.json, whose entry carries no result; the one real coverage gap this cycle

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R5 _root_anchor accepts any leading prefix whose realpath equals the root, so a third spelling is trusted

**Choice**: discarded (settled deferral, ledger)

**Rationale**: cycle 2: identical to cycle-1 R12 at the same log_sink_refusal.py:141; designed root-alias anchoring, BLAKE the only raiser in both cycles and in both he concedes containment holds with O_NOFOLLOW-pinned below-root components. --ledger-dismiss BLAKE did not match the text mechanically, so the dismissal is recorded by the gate and in the ledger

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R6 a missing or hung git still tracebacks out of stage_review through dirty_tree._git

**Choice**: discarded (settled deferral)

**Rationale**: cycle 2: this is cycle-1 R5, already in state.deferred_decisions; PRD T3 names _is_inside_git_dir only and dirty_tree.py is outside the T3 write paths

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R7 T4's requirement to merge the overlapping CHANGELOG --verify bullets is unmet

**Choice**: discarded (contradicts verified facts)

**Rationale**: cycle 2: misreads T4. The overlap T4 names (the log on spawn failure) was merged at CHANGELOG.md:33, verified against the PRD text and the file; lines 34-37 are distinct behaviours

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R8 the receipt and report claim a recorded gate covers the rework's product bytes when the latest recorded gate is feca0d1

**Choice**: discarded (duplicate of R1, swept there)

**Rationale**: cycle 2: same defect as the two-voice R1 row; the sweep task carries this row's remedy verbatim

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R9 the report cites its raw gate log in the gitignored docs/dev/tmp tree

**Choice**: discarded (single-voice)

**Rationale**: cycle 2: ALICE only, and she states the evidence is usable because the counts are inline; docs/dev/tmp is the designated scratch tree and tracking raw logs is not a PRD write path

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R10 the five new dup-failure cases pass against the pre-rework code

**Choice**: discarded (mechanical replay control)

**Rationale**: cycle 2: the raiser accepts the tests; same class as cycle-1 R14/R20, and cycle-1 R1 asked for exactly this pre-existing branch to be pinned

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R11 _write_artifact's NUL-byte pwrite fallback exceeds the spec's truncation requirement

**Choice**: discarded (single-voice)

**Rationale**: cycle 2: BLAKE only, and he states it is defensive and low risk; it serves the spec rule that a failed artifact can never stay reusable

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R12 prior R6 remains unresolved (duplicate anchor scans, unused parameter)

**Choice**: discarded (settled deferral)

**Rationale**: cycle 2: a restatement of the settled cycle-1 R6 deferral by its own author, asserting no new regression

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R13 prior R5 remains deferred (sibling staging git probes lack timeout handling)

**Choice**: discarded (settled deferral)

**Rationale**: cycle 2: a restatement of the settled cycle-1 R5 deferral by its own author, out of PRD scope

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R14 the CHANGELOG bullet says --verify accepts a relative --project-root 'again' though nothing was released

**Choice**: discarded (single-voice)

**Rationale**: cycle 2: EVE only, a wording preference on an unreleased entry; the changelog rule requires the entry and merging it back would re-fuse the clauses cycle-1 R2 asked to split

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R15 DUP_CALLS patches os.dup2 speculatively with a positional-only fake

**Choice**: discarded (single-voice)

**Rationale**: cycle 2: EVE only, test-internal tidying; ALICE reviewed the same cases and accepted them, and the patch is scoped to the test's own context manager

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R16 sibling git probes in dirty_tree._git have no timeout or OSError guard

**Choice**: discarded (settled deferral)

**Rationale**: cycle 2: the raiser files it as out of scope against the settled cycle-1 R5 deferral

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R17 state.json carries the R6 issue twice with contradictory actions and two D1-D5 verdict sets

**Choice**: discarded (single-voice, out of scope)

**Rationale**: cycle 2: EVE only and filed by her as out of scope; state.json is machine-written workflow state, and two D1-D5 sets is the documented shape when Bob and Eve both run

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R18 commit 1539f6d's subject names a test file it did not touch

**Choice**: discarded (single-voice, unamendable)

**Rationale**: cycle 2: EVE only and filed by her as out of scope; rewriting a pushed master commit needs a force push, which is not authorized

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R19 [MECH] 5 dup tests pass against the pre-change code

**Choice**: discarded (mechanical replay control)

**Rationale**: cycle 2: the mechanical replay cannot distinguish a pin of retained behaviour from a missing pin, and cycle-1 R1 asked for this pre-existing os.dup branch to be pinned; same class as cycle-1 R14/R20

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R20 [MECH] 28 relative_root tests pass against the pre-change code

**Choice**: discarded (mechanical replay control)

**Rationale**: cycle 2: the row's own text enumerates why each case passes at base and names the 5 corrective cases that did fail first; same class as cycle-1 R13/R19

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: R21 the receipt's reviewed_head_gate.log points at a gitignored scratch file

**Choice**: discarded (single-voice)

**Rationale**: cycle 2: EVE only and filed by her as out of scope; same fact as R9

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The receipt's `package_revision_note` says the per-task T1-T4 measurements were taken at 6888765, not at the re-pinned revision. This is disclosed honestly and the historical entries were preserved. But the receipt does not describe the product bytes at the pin.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: The edit that removed ", and leaves no reusable artifact after a failed write or close" left the first `--verify` bullet's list without its conjunction: "...stops the child's leftover processes when a sink fails late, removes only a leaf it created; ...". It needs "and" before "removes".

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [autonomous] 2026-11-08T16:36:38Z

**Decision**: Prior R17 has a queued check but no recorded result establishing artifact-parent race coverage. Run `rg -n "swap_artifact|artifact.*parent.*symlink|SPELLINGS" tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_recovery_v2_sinks.py`; inspect matching tests for mixed root/artifact spellings, a post-preflight parent swap, controlled refusal and unchanged sentinel bytes. Record the covering node or add the missing case.

**Choice**: auto-fixed

**Rationale**: fixed by review-close

### [deferred] 2026-11-08T16:36:38Z

**Decision**: The T3 fix covers only `_is_inside_git_dir`, as specified. Sibling Git probes on the same staging path still go through `dirty_tree._git`, which has no timeout and no OSError handling (`_resolve_roots` -> `_toplevel`, `_repo_problem`, `_tracked_problem`). If git is really missing, or one of these probes hangs, `stage_review` still raises before it reaches the guarded probe. The new tests stub only the `--is-inside-git-dir` call, so they do not exercise this. The PRD wording limits scope to `_is_inside_git_dir`, so this is a residual risk and not a spec violation.

**Choice**: deferred

**Rationale**: deferred by review-close
