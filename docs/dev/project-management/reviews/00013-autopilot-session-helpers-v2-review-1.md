---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v2.md
review: 1
date: 2026-11-04
head_sha: 2998ffbdfa57fac33042b78efa3fc9b32e066c1a
codex_thread_id: 01a1a56f-75f2-7a72-b860-dbedecf63943
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: e8df2aec
  carl: faf579b6
---

# Review: 00013-autopilot-session-helpers-v2

Diff range: `316557ecbe06895b7f90e33a133bc5d699f841ff..2998ffbdfa57fac33042b78efa3fc9b32e066c1a`

codex_rung_guard: not fired

## Review Summary

Reviewed: 4 completed tasks (cycle 1, full review over the PRD's whole work range `work_start_sha..HEAD`). All five lenses ran in fresh, isolated contexts, dispatched in one message from this native Claude loop session. Nothing was skipped and no guard was bypassed.

- Cycle id `00013v2-c1`. Raw reviewer outputs are `docs/dev/tmp/{alice,blake,bob,carl,eve}-output-00013v2-c1.txt`; the five prompts are the matching `-prompt-` files.
- **Eve ran as the opt-in fifth lens** because the PRD frontmatter resolves `doubt_reviewer: fable`. The codex doubt-roster guard did **not** fire: no task in `state.tasks` carries an `attempts[].implementor == "codex"` (all four ran `claude`/opus). Bob (codex) and Eve (fable) therefore both carried the doubt rubric.
- Blake's inputs stayed PRD-only. He was told explicitly not to read anything under `docs/dev/project-management/reviews/` or `docs/dev/project-management/autopilot/reports/`, and no design doc, settled-decisions block or prior-findings addendum was rendered into his prompt. No v1 review history, no 6d duplicate-review material, no Pat output and no coordinator ruling reached him.
- No settled-decisions ledger exists for v2 (`00013-autopilot-session-helpers-v2-ledger.json` is absent — cycle 1), so `consolidate_findings.py` ran without `--ledger`/`--ledger-dismiss` and there is no auto-dismissed section.
- pack: ok (`docs/dev/tmp/engram-pack-00013v2-c1.md`). `review-stage` reported no staging errors.
- Consensus engine: `legacy` (single Alice subagent). No `consensus_run_id`.
- Bob ran on the inlined prompt (600418 bytes: head block, review context verbatim, the full 443905-byte diff in a fenced block, then the persona). His dispatch row's `prompt_bytes` was measured against the 13615-byte staged render `review-stage` wrote, so that row understates what codex received.
- Eve needed her one format retry: her first return carried correct FIX/VERIFY/KNOWN buckets and complete `D1`-`D5` lines but no `[EVE] … | File: … | Task: …` issue lines, which would have dropped her entire voice from consolidation. `[RETRY] eve attempt 1/1` asked for the issue lines only; the reformatted return added 20 of them and changed no finding, severity or verdict. No other reviewer needed a retry.

### Measured test evidence (read, not re-derived)

The cycle's gate ran once at this HEAD:

`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` → exit 1, **23 failed, 967 passed in 235.21s**.

**The verify reader did not parse that summary.** `review-stage`'s gate step returned `verdict: "stale"` and `tests_line: "Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)"`, which is the same reader defect the build session recorded (`contract-card.md`: "the verify CLI returned recorded=false/null counts despite the readable pytest summary"). The counts in the `Tests:` line below are therefore read verbatim out of this cycle's own gate log, `docs/dev/tmp/gate-00013v2-c1.log:609`, whose `FAILED` lines (`:586`-`:608`) enumerate exactly 23 nodes: 19 AP00018 controller nodes plus the 4 AP00013 helper nodes named in R1/R2/R8. `last-verification.json` was **not** written or fabricated, and the suite was not re-run a second time to manufacture a parseable line. Provenance is stated rather than hidden.

Mechanical fail-first replay: 56 touched tests ran against the base, 33 failed there, 23 passed — the 4 `[MECH]` rows below.
Tautological-shape check: 84 test functions in 4 files, **no** finding.

### Agent Status

- Alice: ✅ Available
- Blake: ✅ Available
- Bob: ✅ Available (codex, exit 0; thread id captured)
- Carl: ✅ Available (gemini backend resolved via the copilot CLI, exit 0; output carries narrative tool-trace noise around its issue lines and `R{n}` verdicts, which consolidation ignores)
- Eve: ✅ Available (Claude Fable 5 Task subagent; one format retry, see above)

### Note on row R1 (fail loud)

`consolidate_findings.py` merged **four distinct `plugins/autopilot/scripts/verification.py` defects** onto R1 by stripping line suffixes (`:296 ~ :345 ~ :368 ~ :365 ~ :200 ~ :342 ~ :363 ~ :280` — its own warning line). R1's description is the first-seen wording (the ownership window), but the row also carries: the artifact write/close failure leaving a reusable record (Alice `:345`, Bob `:368`, Carl `:365`, Eve `:363`), the spawn-failed empty-log residue (Blake `:200`, Bob, Eve), the unguarded `os.close(pin[0])` in `_close_result_sink` (Bob `:342`), and the un-restorable truncated pre-existing artifact (Eve `:280`, raised as out of scope). Its full-consensus count is real, but it is **not** one fix. The same stripping folded `review_stage.py` `:402/:413/:410` onto R3, `:630/:629/:627` onto R5, `CHANGELOG.md` `:35/:32/:33` onto R6, and `log_sink_refusal.py` `:125/:97` onto R7. R8's single-voice consensus cell is an artefact of this merge, not a lone voice: Blake, Bob and Eve raised the same four-red-node regression under `verification.py:200`, which landed in R1. Any rework batch built from this table must treat R1, R2 and R8 as the one four-node regression plus the three separate `verification.py` defects listed here, not as a single task.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [5/5] | 🟠 | The ownership-window defect from reports/00013-v2-task2-followup-ruling.md is unresolved. _open_result_sink decides "this run created the leaf" with a separate `artifact.exists()` before the open (verification.py:296). It then takes the cleanup identity from a later `os.lstat` by name in _pin_sink_leaf (log_sink_refusal.py:235), not from `os.fstat` on the opened descriptor. A file created between the exists() check and the open, or swapped between the open and the lstat, is treated as owned and `_unlink_pinned` deletes it. A fix would take creation from the open itself (try O_CREAT\|O_EXCL first, then fall back to a plain open) and the identity from fstat of the sink fd. No test covers this window. The README line "identified ... matched by inode" and the matching CHANGELOG bullet overstate what is guaranteed. MERGED ROW — see "Note on row R1": also carries the artifact write/close failure leaving a reusable record (verification.py:363), the spawn-failed empty-log residue (verification.py:200), the unguarded `os.close(pin[0])` (verification.py:342) and the un-restorable truncated pre-existing artifact (verification.py:280, out of scope). | plugins/autopilot/scripts/verification.py:296 | 2 | ALICE, BOB, CARL, BLAKE, EVE |
| R2 | [4/5] | 🟠 | Two more v1 tests fail because _open_log_sink changed contract: tests/autopilot/test_local_paths.py::SafeSinkOpenerTest::test_sink_opener_creates_parents_and_a_fresh_unbuffered_binary_file and ::test_sink_opener_refuses_symlinked_parents_and_replaces_symlinked_leaf. The first expects the opener to truncate, but it now keeps prior bytes. The second expects a symlinked leaf to be replaced, but it now raises ELOOP at log_sink_refusal.py:216. The recovery report (00013-helper-recovery-v2.md:83-116) records both as v2 task-2 regressions and leaves them red, so the full gate shows 23 failures against the 19 known AP18 ones. The opener's callers are not wrong. These two tests need to be re-bound to the new contract (the PRD already moved truncation to the spawn, and refuse() already rejects symlinked leaves), or the red nodes remain a blocker. | plugins/autopilot/scripts/log_sink_refusal.py:203 | 2 | ALICE, BLAKE, BOB, CARL |
| R3 | [3/5] | 🟠 | _is_inside_git_dir fails closed unless stderr starts with the English "fatal: not a git repository". _git does not pin LC_ALL, so under a non-English locale a legitimate non-repo external destination is refused. This is a safe failure but a false refusal. Pin LC_ALL=C for that probe or document the limit. Eve verified it on this host: git 2.56.0 under `LC_ALL=de_DE.UTF-8 LANGUAGE=de` prints `Schwerwiegend: Kein Git-Repository ...`. | plugins/autopilot/scripts/review_stage.py:402 | 1 | ALICE, BLAKE, EVE |
| R4 | [3/5] | 🟠 | The shared context artifact is not limited to the granted union when no context-reading job is in the roster. `shared` falls back to full `CONTEXT_KINDS` when `variants` is empty (roster of only Blake/Eve, such as fast-track). The PRD says "an empty union grants no content". The test `test_staging_keeps_every_context_kind_when_no_roster_job_reads_the_shared_context` pins the opposite. It asserts that `review-context-u3.md` contains the implementation-audit context, the settled history, the pack precedent and the test gate, none of which Eve is granted. The CHANGELOG line "fills the shared context file with granted input kinds only" overclaims for this case. That pinning test also passes against the pre-change code (fail-first replay), so it pins nothing this change introduced. | plugins/autopilot/scripts/review_stage.py:380 | 1 | BLAKE, BOB, EVE, mech-check |
| R5 | [3/5] | 🟡 | The new missing-PRD refusal returns `"reason"` while every other staging refusal goes through _refusal and uses `"detail"` (review_stage.py:123 vs :630). A caller that reads `detail` gets nothing for this error. It is also a hand-built dict where a helper exists. Use _refusal, or align the key. The tests currently bind to `reason`, and one helper at test_helper_recovery_v2.py:62 accepts either key. | plugins/autopilot/scripts/review_stage.py:630 | 1 | ALICE, BLAKE, EVE |
| R6 | [3/5] | ⚪ | The CHANGELOG bullet "attempt validation holds its memory bound against a measured resource ceiling" describes a test-only change under Fixed. It is not a user-visible fix and contradicts the changelog rule that excludes test changes. Drop it. Bullet 33 and README:297 likewise restate implementation mechanics (pinned descriptors, inode matching) rather than the user-visible effect, and the README does not document the empty-log residue after a failed spawn. | plugins/autopilot/CHANGELOG.md:35 | 3 | ALICE, BLAKE, EVE |
| R7 | [2/5] | ⚪ | `_worktree_gitdir_pointer` reads any in-repo file that is the same inode as a sibling `.git` file, for example a nested repo's pointer. The PRD says only the supplied repository's actual worktree pointer may be read. The external hard-link case is correctly refused before any read. Eve's fix: guard the call with `pointer = _worktree_gitdir_pointer(resolved) if resolved.parent == toplevel else None`. | plugins/autopilot/scripts/log_sink_refusal.py:125 | 2 | BLAKE, EVE |
| R8 | [1/5] | 🟠 | Two v1 tests in test_cap_recovery_helpers.py fail at the reviewed HEAD. They are test_spawn_failure_is_controlled_and_preserves_outputs[missing-False] and [not-executable-False]. I re-ran them: `assert tree(world.target) == before` fails on an extra empty docs/dev/tmp/run.log, because the new _open_log_sink creates the log before the spawn and nothing removes it when the spawn fails. The v2 sibling test (test_helper_recovery_v2_sinks.py:98) asserts the opposite, an empty leftover log, and the coordinator correction allows it. The old test was never reconciled. PRD T2 says existing tests must stay green and the AP18 deferral covers only the 19 controller tests, so this is an uncovered helper regression. Either update the stale test to the "absent log may stay empty" contract, or drop the log the run created, as is already done for the artifact leaf. NOT single-voice — Blake, Bob and Eve raised the same regression under verification.py:200, which the consolidator merged into R1 (see "Note on row R1"). | tests/autopilot/test_cap_recovery_helpers.py:64 | 2 | ALICE |
| R9 | [1/5] | 🟠 | Late sink failures do not terminate surviving process-group descendants. A child can start a background process with redirected pipes, exit successfully, and leave that descendant running when log or artifact close fails. Retain the process-group identity through sink finalization and terminate the group on failure; test a real surviving descendant. | plugins/autopilot/scripts/verification.py:217 | 2 | BOB |
| R10 | [1/5] | 🟠 | The 19 AP00018 controller failures remain full-gate and push blockers. They are outside AP00013's corrective write paths and explicitly deferred; the supplied 23-failure result also includes the four helper regressions above. | N/A | general | BOB |
| R11 | [1/5] | 🟡 | The T3 contract requires the allocation measurement to hold when the parent runs with tracing already on (PYTHONTRACEMALLOC) and a prior peak above 8 MB. The child's `if tracemalloc.is_tracing(): tracemalloc.stop()` branch is never exercised, because measure() does not pass that env var to the child. Add an env variant to the measurement. | tests/autopilot/test_cap_recovery_helpers.py:158 | 3 | ALICE |
| R12 | [1/5] | 🟡 | Files outside the PRD's "complete implementation write paths" were created or changed: `tests/autopilot/test_helper_recovery_v2_sinks.py` (491 new lines, with sink contract tests that the receipt says oppose the older tests) and `tests/autopilot/test_review_helpers.py` (edited to grant the pack ref). The PRD names only `test_helper_recovery_v2.py` and `test_cap_recovery_helpers.py` for tests. | tests/autopilot/test_helper_recovery_v2_sinks.py | 2 | BLAKE |
| R13 | [1/5] | 🟡 | The Phase 2 exit criterion is not met. The full gate is red, and the receipt records 4 non-AP18 failures as "deferred to completion review". The PRD forbids a helper pass that relies on that deferral. The receipt text is otherwise honest and the historical receipt is preserved, but it records that the check is not green. `--check` on the source-map generator and the provenance tests do pass. | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:162 | 4 | BLAKE |
| R14 | [1/5] | 🟡 | A missing `O_NOFOLLOW` is refused only for `--export-policy --out`. `_open_log_sink`, `_pinned_parent_fd` and `review_stage._write` reference `os.O_NOFOLLOW` directly, and `_posix_supported` does not check for it. On a host without it, `--verify` and staging would raise `AttributeError` (a traceback) instead of a controlled refusal. The PRD's sentence on this sits in the policy-output behavior, so it is partly met. | plugins/autopilot/scripts/verification.py:48 | 2 | BLAKE |
| R15 | [1/5] | 🟡 | The FIFO-with-reader test starts a thread without confirming its reader opened. The exporter can therefore hit the already-covered no-reader refusal and still pass. Signal readiness after opening the descriptor, wait with a timeout before exporting, and assert that no bytes reached the FIFO. | tests/autopilot/test_helper_recovery_v2.py:735 | 2 | BOB |
| R16 | [1/5] | 🟡 | Redundant directory traversal in _pin_sink_leaf repeats parent descent immediately performed by _open_log_sink | plugins/autopilot/scripts/log_sink_refusal.py:235 | 2 | CARL |
| R17 | [1/5] | 🟡 | PRD T2 requires pre-spawn sink validation "including ... unresolved/resolved root aliases", but neither new test file drives `run_verification` with a symlinked `project_root` (macOS `/tmp` -> `/private/tmp` style) against a resolved-spelling `log_path`/`artifact_path`. Check: run `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_verification.py tests/autopilot/test_cycle1_boundaries_verify.py tests/autopilot/test_cap_recovery_helpers.py -k "alias or symlink" -q -rA` and confirm at least one passing node spawns nothing and refuses/accepts consistently under a symlinked root; if none does, add one to tests/autopilot/test_helper_recovery_v2_sinks.py using `child_argv` + a marker | tests/autopilot/test_helper_recovery_v2.py:608 | 2 | EVE |
| R18 | [1/5] | ⚪ | _run_against_sink wraps the drain in `except OSError` and labels every OSError "sink-write-failed". That includes an `os.read` failure on the child's pipes in _drain (verification.py:121), which is not a sink error. The ruling flagged this slug for judgement. Either narrow the catch to the sink writes or name the cause neutrally. | plugins/autopilot/scripts/verification.py:174 | 2 | ALICE |
| R19 | [1/5] | ⚪ | Unsafe artifact path refusal omits reason field present in all other gate errors | plugins/autopilot/scripts/verification.py:395 | 2 | CARL |
| R20 | [1/5] | ⚪ | `_open_log_sink`'s post-open validation checks `S_ISREG` and `st_nlink == 1` but not the executable bit that `refuse` checks by `lstat`; the old unlink+`O_EXCL` opener guaranteed a fresh 0o666 file, the reopen-in-place opener does not, so a leaf swapped for an executable between `refuse` and open is written. Fix: add `or info.st_mode & 0o111` to the refusal condition (one line, mirrors `refuse`) | plugins/autopilot/scripts/log_sink_refusal.py:226 | 2 | EVE |
| R21 | [1/5] | ⚪ | The recovery report never states the actual measured peak although the PRD Resource case and T3 say "report actual measurement". Fix: record the number with the exact command (this review measured 95,314 bytes for attempt 200000 on this host, ceiling 1,000,000; the injected `[0] * 200000` probe lands above the ceiling) | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md:22 | 4 | EVE |
| R22 | [1/5] | ⚪ | Receipt provenance records the alias, not the served model: `implementation.model: "opus"` while the recovery report says `claude-opus-5`; PRD: "Preserve actual model-family provenance". Fix: record the served model id and effort as the report does, then regenerate the map (`--check` must still pass since only the receipt hash changes) | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:33 | 4 | EVE |
| R23 | [1/5] | ⚪ | Dead code in the new test seam: `FailingSink.__enter__`/`__exit__` are never used (production no longer opens the sink with `with`; `_execute` and `_write_artifact` call `close()`). Fix: delete both methods | tests/autopilot/test_helper_recovery_v2.py:507 | 2 | EVE |
| R24 | [1/5] | ⚪ | `test_the_attempt_allocation_measurement_catches_a_proportional_allocation` is a framework-verification test: it allocates `[0] * 200000` in the harness and asserts tracemalloc saw it, exercises no production code and cannot fail when `check_evidence` changes; the task card asked for a "scratch-only copy/probe", not a committed test. Fix: drop the `mode`/`probe` plumbing (tests/autopilot/test_cap_recovery_helpers.py:179) and the test, keep the probe result as the recorded measurement in the recovery report; if the coordinator keeps it as a guard for the measurement window, say so in the assumptions ledger. The fail-first replay independently finds this same test passing against the pre-change code. | tests/autopilot/test_cap_recovery_helpers.py:199 | 3 | EVE, mech-check |
| R25 | [1/5] | ⚪ | The caller's full-suite rerun reports 23 failed; the recorded gate log for 9e89a59 holds exactly the 19 AP18 + 4 helper nodes named in the receipt. Check: from the caller's own run output (do not rerun), extract the 23 `FAILED` node ids and diff them against `final_gate.failing_nodes.ap00018_controller` (19) and `ap00013_contract_conflict` (4, docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:218); any node outside those lists is an unrecorded helper regression | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:162 | 4 | EVE |
| R26 | [1/5] | ⚪ | `_run_against_sink`'s `except OSError` labels a pipe-read failure (`os.read`/selectors) as `sink-write-failed`. Known/out of scope: cosmetic slug only, both paths kill the child and return a controlled result, and a distinct label needs a sink-error wrapper type the PRD's "no new output-management subsystem" rule excludes | plugins/autopilot/scripts/verification.py:174 | 2 | EVE |
| R27 | [1/5] | ⚪ | `tools/autopilot/source-map.json` stamps `evidence.status: "passed"` on the `verification.py` and `log_sink_refusal.py` rows while the receipt they cite records `failed: 4`; the generator (tools/autopilot/update_helper_map.py:498) validates only `passed > 0`. Known/out of scope: the generator is read-only under this PRD and its acceptance case defines "passed" as byte-binding ("exists at the recorded digest"); changing the semantics needs its own task | tools/autopilot/source-map.json:7711 | 4 | EVE |
| R28 | [1/5] | ⚪ | `_in_nested_repo` also parses a localized git message (`"work tree" in probe.stderr`) and misclassifies under non-English locales. Known/out of scope: pre-existing, outside this diff's hunks; apply the C-locale pattern from the `_is_inside_git_dir` FIX in a follow-up, not here | plugins/autopilot/scripts/log_sink_refusal.py:165 | general | EVE |
| R29 | [1/5] | ⚪ | `_destination_problem` raises `NotADirectoryError` (traceback) when the nearest existing ancestor of `artifact_root` is a file, because `_git(cwd=<file>)` fails in the parent before git runs; `_is_inside_git_dir`'s "fails closed on anything" claim does not cover an OSError from spawning git. Known/out of scope: pre-existing on the base commit and unchanged by this diff; not a silent grant (it refuses by crashing), so outside this corrective PRD | plugins/autopilot/scripts/review_stage.py:494 | general | EVE |
| R30 | [1/5] | 🟡 | Fail-first replay: `test_attempt_validation_does_not_allocate_from_the_supplied_attempt` passes against the pre-change code at 316557ecbe06, so it pins no behavior this change introduced. (Its sibling in the same file is R24.) | tests/autopilot/test_cap_recovery_helpers.py | general | mech-check |
| R31 | [1/5] | 🟡 | Fail-first replay: 11 touched tests pass against the pre-change code at 316557ecbe06, so they pin no behavior this change introduced — test_staging_keeps_refusing_other_unsafe_destinations_while_the_guard_is_active, test_staging_still_writes_to_a_clean_destination_outside_any_repository, test_staging_accepts_prd_inlining_jobs_whose_grant_names_another_prd_id, test_staging_accepts_a_context_reading_job_without_a_prd_grant_and_keeps_the_prd_out, test_staging_keeps_every_context_kind_when_no_roster_job_reads_the_shared_context (that one is R4) +5 more. Several are guard-regression tests whose behavior genuinely predates this diff, which is the documented behavior-preserving case; weigh the PRD's intent per finding rather than treating the block as a defect list. | tests/autopilot/test_helper_recovery_v2.py | general | mech-check |
| R32 | [1/5] | 🟡 | Fail-first replay: 9 touched tests pass against the pre-change code at 316557ecbe06 — test_a_failed_spawn_leaves_an_existing_log_and_artifact_byte_identical, test_a_failed_spawn_writes_no_result_artifact_when_none_existed, test_an_empty_command_is_refused_and_leaves_an_existing_log_byte_identical, test_a_dirty_tracked_file_refuses_the_run_before_the_child_is_spawned, test_a_successful_run_replaces_the_logs_prior_bytes_instead_of_appending +3 more. This is the new 491-line sink-contract file (R12): most of its preservation assertions held before the change too, so it pins less of the new contract than its size suggests. | tests/autopilot/test_helper_recovery_v2_sinks.py | general | mech-check |
| R33 | [1/5] | 🟡 | Fail-first replay: `test_staged_task_and_context_files_carry_task_rows_and_precedent_text` passes against the pre-change code at 316557ecbe06, so the pack-ref grant edit to this file pins no new behavior. | tests/autopilot/test_review_helpers.py | general | mech-check |

## Alice

Consensus lens, implementation-aware. Nine findings, reproduced in the table as R1, R2 (both 🟠), R5, R11 (🟡), R6, R18 and the locale probe folded into R3 (⚪), plus R8. She re-ran the named nodes herself rather than taking the receipt's word.

Checked and found no defect: the T1 staging changes against the design contract (fail-closed git probe, the Blake/Eve PRD-grant refusal, the union-based shared context, the `_resolve_roots` extraction); the T2 `_write_policy` FIFO and `O_NOFOLLOW` guards, with the descriptor owned by its `with` block; the containment-before-read reorder in `refuse()`; 151 sink/staging/provenance/cap-recovery tests passing except the two nodes of R8; 181 tests in the other named regression files; `_run_against_sink` at 49 lines (under the 50-line limit); `test_helper_recovery_v2.py` at 794 lines (under 800).

```
R1: fail
R2: pass
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

Blind lens, PRD-only. He located the code himself and confirmed the two cap-recovery failures with his own narrow run (2 failed, 47 passed). Ten findings: R2, R4 and the spawn-failure regression (merged into R1) at 🟠; R5, R12, R13, R14 at 🟡; R3's locale case, R7 and R6's CHANGELOG/README case at ⚪.

Verified as correct: T3's tracemalloc test exists, measures in a child process, carries the 1,000,000-byte ceiling and an injected `[0] * attempt` sensitivity check, and both its tests pass; containment now runs before pointer reads, and relative gitdir targets resolve against the pointer's parent; git detection fails closed with no Git safety override; the FIFO and missing-`O_NOFOLLOW` refusals in `--export-policy` work; mid-run sink write failures kill and reap the child; the README documents the plan-and-prd conjunction; the generator `--check` exits 0; a narrow run of the ten other named test files gave 235 passed.

```
B1: fail
B2: fail
B3: pass
B4: pass
B5: fail
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
```

## Bob

Doubt rubric (D1-D5) plus de-slop, on codex, static-only. Eight FIX items (R1's ownership window and artifact-close case, R9, R2, the spawn-failed log residue, the unguarded `os.close(pin[0])`, R4, R15), an empty VERIFY bucket, and one KNOWN item (R10, the 19 AP00018 controller failures as deferred full-gate/push blockers).

```
R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass
```

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

## Carl

Gemini, frontend & design specialist, generalist here (this diff has no UI surface). Five findings: R2 and the artifact-drop case of R1 at 🟠, the TOCTOU window of R1 and R16 at 🟡, R19 at ⚪. He re-ran `test_cap_recovery_helpers.py` and `test_local_paths.py` himself and pasted both failure tracebacks, independently confirming all four red helper nodes.

```
R1: pass
R2: pass
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

## Eve

Doubt rubric plus de-slop, Claude Fable 5. 20 residual findings: FIX 13, VERIFY 2, KNOWN 5. Her headline is that the four red helper nodes are in scope and the receipt's "no implementation satisfies both contracts" framing is a false dichotomy the PRD text resolves — the "leave an empty log" sentence comes from the design/task card, not the PRD, so T3's "named scoped tests pass" criterion was never met either.

Measured during her review (not a suite rerun): T3 peak for attempt 200000 = 95,314 bytes (uv python 3.12, `check_evidence`, fresh tracemalloc), with `attempt_sequence_invalid` present; host git 2.56.0 under `LC_ALL=de_DE.UTF-8 LANGUAGE=de` emits the German refusal quoted in R3; `git cat-file -e 3c7e218:plugins/autopilot/README.md` exits 0; `git diff --stat 3c7e218 HEAD -- plugins tests tools` touches only `tools/autopilot/source-map.json` (24/24 hash lines); the recorded gate log for 9e89a59 holds exactly the 19 AP18 + 4 helper FAILED nodes named in the receipt.

Her two VERIFY items: the symlinked-root alias check (R17) was queued to `docs/dev/project-management/reviews/00013-autopilot-session-helpers-v2-checks-1.json`, since it names one exact runnable pytest command. The second (R25, diff the 23 `FAILED` node ids against the receipt's two recorded lists) was **not queued: command shape** — it describes an extraction-and-compare over existing output, not a single project verification command.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 33 findings
Tests: 967 passed, 23 failed, 0 skipped (gate run this cycle, exit 1, treated as failed; counts read verbatim from docs/dev/tmp/gate-00013v2-c1.log:609 because the verify reader returned "counts unavailable" for this `-q` summary — last-verification.json was not written)

## Post-session provenance and coordinator disposition

Native coordinator session `b332b34b-5d72-49de-891e-194d5f101d83` exited 0.
Actual served reviewers: Alice and Blake used native Claude Sonnet 5.5/high;
Eve used native Claude Fable 5.1/xhigh; Bob used Codex `gpt-6-astra`/high
(thread `01a1a56f-75f2-7a72-b860-dbedecf63943`); Carl used Copilot with
explicit `gemini-3.8-flash`. No auto model or silent downgrade was used.
Bob's 600418-byte actual inline input remains distinguished from the smaller
staged telemetry row. Eve's one format retry preserved her complete findings.
Blake independently read the delivery receipt named by the PRD as an output
to assess; no coordinator ruling, prior review, Pat or 6d input was supplied.

Root adjudication is recorded in
`../autopilot/reports/00013-v2-cycle1-adjudication.md`. It supersedes the
incorrect older-test rebinding and unsupported single-voice dismissals in
the initial handoff, without rewriting the reviewers' findings or verdict.
The original handoff/ledger/task snapshot is committed separately.
