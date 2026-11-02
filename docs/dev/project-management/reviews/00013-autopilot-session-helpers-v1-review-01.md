---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v1.md
review: 1
date: 2026-11-02
head_sha: 6c1352c6416e7a21bbbb72980973a01541c7e926
codex_thread_id: 01a19b8f-6516-7a22-92b6-f45b995d9744
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 36212110
  carl: 86208e5a
---

# Review: 00013-autopilot-session-helpers-v1

Diff range: `843e6e7d51c56377adc1c01fab9ae7ea7755e1f4..6c1352c6416e7a21bbbb72980973a01541c7e926`

codex_rung_guard: not fired

## Review Summary

Reviewed: 11 completed tasks (cycle 1, full review). All four lenses ran in fresh, isolated contexts: Alice (consensus, Claude subagent), Blake (blind, PRD-only, Claude subagent), Bob (doubt plus de-slop, codex, first dispatch inlined, no refusal), Carl (frontend and design, copilot backend with model gemini-3.8-flash, exit 0). Eve did not run: no task attempt has `implementor: codex`.

Scope notes, stated so nothing reads as silent:

- This file was restored. A second session (the `agent-plugins-6d` autopilot loop) ran its own cycle-1 review of the same PRD and overwrote this untracked file and its ledger at 10:40, after the decision gate below had been applied from this version. This text is rewritten from the session that applied the gate, so the findings table matches the four rework tasks (12-15) byte for byte. The other session's review is kept as scratch at `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` (ledger: `docs/dev/tmp/00013-ledger-by-agent-plugins-6d.json`) and was not used for any decision. Its raw reviewer outputs are `docs/dev/tmp/{alice,blake,bob,carl}-output-20261102a.txt`.
- The review range holds foreign commits that are not AP 00013 tasks: the remote specflow and validator merge (`6c1352c` and its parents), `4cb0ff7` (registers the AP 00018 controller files in the source map and narrows `test_helper_provenance_real.py`), and the AP 00018 replan and drift ledgers. The staged 1.4 MB diff was path-scoped to the PRD's task files before dispatch (`plugins/autopilot`, `tests/autopilot`, `tools/autopilot/update_helper_map.py`, the characterization report and the delivery receipts; 535 KB). `tools/autopilot/source-map.json` (8196 added lines, a generated map) was left out of the inlined diff. The full diff is kept at `docs/dev/tmp/review-diff-full-ap00013-c1.diff`.
- Context pack: failed (`engram pack exit 1: sqlite3.IntegrityError: UNIQUE constraint failed: chunks.repo, chunks.path, chunks.content_hash, chunks.chunk_ordinal`). Degraded, not blocking; the prompts carry the no-pack sentinel.
- Test gate: the full suite ran this cycle (`uv run pytest tests/autopilot`): 800 passed, 20 failed. 19 are the AP 00018 task-7 red-first tests (`test_controller_capacity`, `test_controller_owner`, `test_controller_owner_recovery`), documented in `reviews/00013-preexisting-suite-failures.md`. The 20th is new and not listed there: `test_package.py::TargetPackageTest::test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job` fails because Renovate PRs #8 and #11, merged in `6c1352c`, bumped the `plugins` job's `actions/setup-python` pin, its Python version and added a marketplace step, while the test still pinned the old values (finding R2). The other session's run at the same HEAD counted 793 passed and 20 failed; the 7-test difference is unexplained and was not chased.
- Mechanical checks: the fail-first replay flags only invariant-preserving tests (the helper provenance real-source tests, `test_export_policy_is_the_unwrapped_canonical_policy`, the capability test), which pass pre-change by design; Alice adjudicated them and the one that matters is R3. No tautological-shape `[MECH]` line is outstanding.
- Alice's file citations carry diff-file line offsets (for example `review_stage.py:3564`). The consolidator merged on file path only. R5 is re-cited to the real line (`review_stage.py:397`); the other Alice citations that survive the gate are on rows that name a file and task, which is all the rework tasks use.
- The consolidator folded three pairs correctly (R1 size limits, R2 CI pin, R3 capability test). By hand I also folded Carl's `stage_review` row into R1 and merged three reports of the same malformed-request defect (Alice `prepare_close` types, Blake `group()` on non-dict findings, Bob `findings: [null]`) into R4. Raw reviewer outputs below are unchanged.
- Bob's `[BOB]` lines arrived bulleted; a bullet-stripped copy fed the consolidator. Carl's output file held the copilot tool transcript before his `[CARL]` lines; only his findings and verdicts are reproduced here.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/4] | 🟡 | prepare_close is 55 lines and stage_review is 52 lines (def through end), over the 50-line limit. The multi-line contract signatures account for most of the overage. The body of prepare_close can drop the inline tail-sweep ternaries into a helper (for example, build the output dict in _proposal_report), and stage_review (plugins/autopilot/scripts/review_stage.py:467) can move the inputs dict assembly into a helper. | plugins/autopilot/scripts/review_close.py:467 | 6 | ALICE, BOB, CARL |
| R2 | [2/4] | 🟠 | Suite is red beyond the 19 documented AP 00018 controller failures. tests/autopilot/test_package.py::TargetPackageTest::test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job fails (steps[:2] mismatch). The test pins SETUP at actions/setup-python@5fda3b95..., but .github/workflows/validate.yml:23 uses 6d4fd22b... (v7.1.0, bumped by c8e9b69 and merged in 6c1352c). Pushing master publishes a second red cause that reviews/00013-preexisting-suite-failures.md does not list. The full-suite run shows 20 failures: 19 controller tests plus this one. Update the pin or the workflow so they agree. | tests/autopilot/test_package.py:454 | 11 | ALICE, CARL |
| R3 | [2/4] | 🟡 | test_facade's capability test was relaxed to check only ids[:3] plus the canonical format, so it passes against the pre-change code and no longer fails if one of the seven new operation IDs is dropped (they are pinned only in test_package.py and test_local_boundary.py). Pin the full ID list in test_facade too. | tests/autopilot/test_facade.py:99 | 10 | ALICE, CARL |
| R4 | [3/4] | 🟡 | Malformed request values escape the documented exit-2 usage boundary. group() assumes every finding is a dict, so --group-findings with findings ["x"] or [null] raises AttributeError and exits 1 with a traceback (rework_groups.py:106). prepare_close and staging do not validate the types of cycle, batch_id, default_tier, review_ref or the task shapes: a string cycle formats into task names as "[D1]" and never matches snapshot cycle ints, and a non-string batch_id silently takes the decision-gate path. The facade _call maps only TypeError and ValueError to exit 2. Validate these fields explicitly and raise ValueError. | plugins/autopilot/scripts/autopilot.py:125 | 10 | ALICE, BLAKE, BOB |
| R5 | [1/4] | 🟠 | stage_review's live-state refusal is case-sensitive, so on case-insensitive filesystems (macOS, the owner's platform) an artifact_root spelled with different case, e.g. DOCS/dev/project-management/AUTOPILOT/x, is not refused. I checked: Path('.../DOCS/dev/project-management/AUTOPILOT').resolve() exists on this machine and is_relative_to(<project>/docs/dev/project-management/autopilot) is False. The artifacts (review-tasks-*, review-prd-*, prompts) would be written inside live workflow state, against "refuse live state". The facade only casefolds the request-file path (plugins/autopilot/scripts/autopilot.py:345), not the artifact_root carried in the JSON. log_sink_refusal does catch aliases by inode (samefile). Fix: compare by inode identity or casefold, as the verification path does. No test covers it. | plugins/autopilot/scripts/review_stage.py:397 | 5 | ALICE |
| R6 | [1/4] | 🟠 | `--export-policy --out PATH` writes without any live-state check. `_INPUTS` (the live-state guard list) omits `out`, so `--out <root>/docs/dev/project-management/autopilot/state.json` overwrote the file with exit 0. I reproduced this in a scratch tree. This breaks the PRD rule that no helper writes the executing repo's live autopilot state directory. `--artifact` and `--log` are protected by `refuse()` in log_sink_refusal.py, which blocks the whole store prefix, and `stage_review` has its own guard. `--out` has neither, and `out.write_bytes` also follows symlinks. | plugins/autopilot/scripts/autopilot.py:47 | 5 | BLAKE |
| R7 | [1/4] | 🟠 | Per-job manifests do not constrain rendered inputs: nonblind prompts receive context, diff, pack and history unconditionally, even when those refs are absent from their allowed inputs. Build each prompt and its referenced artifacts from that job’s validated manifest. | plugins/autopilot/scripts/review_stage.py:251 | 5 | BOB |
| R8 | [1/4] | 🟠 | Artifact roots outside the project bypass repository and ancestor-symlink checks. An external root can therefore overwrite tracked files in another repository or write inside another live autopilot directory. Apply destination protections to external roots too. | plugins/autopilot/scripts/review_stage.py:376 | 5 | BOB |
| R9 | [1/4] | 🟠 | Sink validation reads arbitrary existing candidate files through `_worktree_gitdir_pointer` before checking containment. With a subdirectory project root, an output naming the parent repository’s live state file reads that state before refusal. Inspect only the identified Git pointer after containment checks. | plugins/autopilot/scripts/log_sink_refusal.py:115 | 4 | BOB |
| R10 | [1/4] | 🟠 | Nested-repository detection fails open when the output’s immediate parent does not exist: `_git` raises OSError and `_in_nested_repo` returns false. Outputs beneath a new directory inside a nested repository are then created. Probe the nearest existing ancestor. | plugins/autopilot/scripts/log_sink_refusal.py:143 | 4 | BOB |
| R11 | [1/4] | 🟠 | Verification does not reject output/input overlap. An untracked script under scratch can also be the log destination; opening the log deletes the script before execution. Validate identifiable argv input paths against both destinations before opening either output. | plugins/autopilot/scripts/verification.py:70 | 9 | BOB |
| R12 | [1/4] | 🟠 | Verification can mark changed product content reusable when a tracked product symlink targets a modified management-store file. `_dirty_check` ignores the target modification; the symlink-target check runs only during later reuse assessment. Include that check before and after execution. | plugins/autopilot/scripts/dirty_tree.py:209 | 9 | BOB |
| R13 | [1/4] | 🟠 | Review-close authenticates the review bytes but permits a referenced table row’s issue to differ from its linked findings. `_backed` compares only ref, severity and file. Compare the linked finding key with the actual selected table row’s complete normalized key. | plugins/autopilot/scripts/review_close.py:232 | 6 | BOB |
| R14 | [1/4] | 🟠 | Carry snapshots can omit task status and still prove an unfinished task because `None != "completed"`. Validate all required CarryTaskSnapshot fields and their types before matching carry eligibility. | plugins/autopilot/scripts/review_close.py:120 | 6 | BOB |
| R15 | [1/4] | 🟡 | The case-variant live-state test passes against the pre-change code (the fail-first replay flags it) and cannot exercise the casefold branch on a case-sensitive filesystem. The variant path does not exist there, so exit 2 comes from "cannot read" (or argparse on the old facade), not from _in_live_state. Create a real directory with the variant spelling, containing valid JSON, so only the casefold check can refuse it. | tests/autopilot/test_local_boundary_state.py:250 | 10 | ALICE |
| R16 | [1/4] | 🟡 | Verification can fail after the command has run, and the failure is not controlled. _open_log_sink(artifact, root) runs after the child exits, and _pinned_parent_fd raises OSError when an absolute artifact is not lexically under an unresolved or relative root, for example a symlinked /tmp alias. _open_log_sink(log, root) can also raise OSError, and none of these OSErrors is caught. _call in the facade catches only TypeError/ValueError, so the user gets a traceback with no JSON report and no artifact after a full gate run. Check lexical containment in _unsafe_paths before spawning, or catch OSError and return ok=false with unsafe-artifact-path or write-failed. | plugins/autopilot/scripts/verification.py:4083 | 9 | ALICE |
| R17 | [1/4] | 🟡 | stage_review silently re-roots a subdirectory project_root to the git toplevel (the `top != project.resolve()` branch), and relative artifact_root then resolves against the toplevel. The contract says "relative paths resolve against explicit project_root" and "helpers never discover" roots. A test pins this as source 9dba4206 parity, and the CHANGELOG lists it under Fixed for unreleased code. Either document it as a deliberate contract exception or refuse a non-toplevel project_root. | plugins/autopilot/scripts/review_stage.py:3662 | 5 | ALICE |
| R18 | [1/4] | 🟡 | Shared Git probes have no timeout, contrary to the required 30-second bound. Verification can hang during preflight or post-run checks regardless of its command timeout. Add the timeout and map timeout failures to refusal or stale evidence. | plugins/autopilot/scripts/dirty_tree.py:19 | 9 | BOB |
| R19 | [1/4] | 🟡 | Regression classification returns false for a cell producing no path pairs, such as `;`, and can return true before examining a later invalid line reference. Validate every pair and line before choosing a verdict; unresolved cells must return null. | plugins/autopilot/scripts/cap_check.py:220 | 7 | BOB |
| R20 | [1/4] | 🟡 | Truncated table rows can be accepted when missing trailing columns because `_row_from_table` checks only selected column indexes and treats every unequal cell count as embedded issue pipes. Reject short rows before reconstructing surplus issue cells. | plugins/autopilot/scripts/findings.py:83 | 2 | BOB |
| R21 | [1/4] | 🟡 | Generated helper delivery evidence has `status: passed` but retains `tested_package_revision: null`: the receipt artifact dictionary never supplies the revision. Populate it from the validated receipt and assert the binding in provenance tests. | tools/autopilot/update_helper_map.py:478 | 11 | BOB |
| R22 | [1/4] | 🟡 | Function provenance claims extractions that were not delivered: custody journal readers are marked extracted despite being deliberately absent, and custody capture_range points to custody.py although implemented in cap_check.py. Record actual replacements, exclusions and target modules per function. | tools/autopilot/update_helper_map.py:286 | 11 | BOB |
| R23 | [1/4] | 🟡 | `_cap` retains an unreachable fallback: while more than four groups remain, removing at most one prose group cannot leave fewer than two code groups. Remove the `len(code) < 2` branch without changing behavior. | plugins/autopilot/scripts/rework_groups.py:73 | 2 | BOB |
| R24 | [1/4] | ⚪ | review_stage writes an extra review-pack-ID.md artifact when pack_text is supplied. The contract lists only review-tasks, review-prd-raw, review-prd, review-context, optional review-diff and the JOB prompts. | plugins/autopilot/scripts/review_stage.py:3484 | 5 | ALICE |
| R25 | [1/4] | ⚪ | test_helper_provenance_real.py:331 skips the real-source parity checks when the pinned source checkout is absent, which includes CI. That is an environmental skip, but the source-parity assertions never run in CI. | tests/autopilot/test_helper_provenance_real.py:331 | 11 | ALICE |
| R26 | [1/4] | ⚪ | The CHANGELOG mixes "**autopilot**:"-prefixed entries with unprefixed ones in the new Added block. | plugins/autopilot/CHANGELOG.md:179 | 11 | ALICE |
| R27 | [1/4] | ⚪ | The named acceptance scenario `source_inventory_mapping` appears in no test, README or characterization doc. The helper-by-helper disposition behavior is covered under other names (`test_dispositions_bind_every_helper_function_and_selected_regression`, `test_writers_and_supervisors_stay_controller_only`). The task 5 acceptance names this scenario, so it cannot be matched by name. The other eight named scenarios are present. | tests/autopilot/test_helper_provenance.py:527 | 5 | BLAKE |
| R28 | [1/4] | ⚪ | `cap_check.capture_range` accepts a `git_dir` option for a bare-backed store with `repo_root` as work tree. This is a source-store concept carried into a helper that is meant to be stateless, and it is only a read-only git probe. The PRD does not require it, so it is a minor boundary smell. | plugins/autopilot/scripts/cap_check.py:285 | 3 | BLAKE |

## Decision gate

Cycle 1 of cap 2: rework is allowed. No 🔴 row, so no rework design is needed. Ten 🟠 rows are unresolved (R2, R5-R14), so the cycle does not converge.

Fix (R1-R14): the three multi-reviewer Medium rows (R1, R3, R4), the CI pin drift (R2, a verified second red cause for the push gate) and every 🟠 row. A 🟠 is never single-voiced away. The ten 🟠 claims were not re-derived here: three were reproduced or checked by their reviewers (R5 by Alice, R6 by Blake, R4 by Blake) and the rework tasks write their tests first, so a claim that does not reproduce stops at the failing-test step and is recorded in the task's attempt log instead of changing code.

Defer to batch end (R18, R21, R22): single-voice Mediums that state a gap against an explicit delivery claim. R18 is verified (`dirty_tree.py` has no timeout at all); R21 and R22 concern the accuracy of the generated provenance and delivery evidence. They are kept visible in the batch report, not dropped.

Discard, single-voice Medium or Low (R15, R16, R17, R19, R20, R23-R28): recorded in the settled ledger so a re-raise is auto-dismissed. This is not a claim that each is false. R15 is covered by the test the R5 fix must add. R16 and R17 are left as documented limits for the follow-up PRD. The other rows are cosmetic or already pinned by an existing test.

Rework progress at the time of this restore: tasks 14 (R2) and 15 (R3) are committed (`b0361c1`, `fdb9918`) and Pat-closed. R2 turned out to have three layers (the setup-python pin, the Python version 3.10 to 3.15, and the new `generate_marketplace.py --check` step), all from the Renovate bumps; the test now follows the `plugins` job, and the `autopilot` job keeps its own v7.0.0 pin. Tasks 12 and 13 are queued.

## Alice

Available: Claude subagent (autopilot:alice, effort high). Raw output saved at `docs/dev/tmp/alice-output-ap00013-c1.txt`; findings are the rows above (R1-R5, R15, R16, R17, R24-R26, and the Alice share of R1-R4).

Verification run reported by Alice: `pytest tests/autopilot` gives 20 failed. `test_package.py` alone: 1 failed, 7 passed. No AP 00013 helper test failed.

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: pass

## Blake

Available: Claude subagent (autopilot:blake, effort high), PRD-only. Raw output saved at `docs/dev/tmp/blake-output-ap00013-c1.txt`.

Checks Blake reported as passed: every file in the PRD's repository structure exists; a narrow run of six test files gave 242 passed; `scripts/validate.py` passed; no OVCAQ, supervisor, record-store commit or controller-state imports in `plugins/autopilot/scripts/*.py`; lifecycle requests return `controller-required` with exit 3 and no mutation; `verify` refuses unsafe, tracked and store log paths before spawning; reuse requires an exact argv match, a green summary and an ancestor-and-clean check.

```
[BLAKE] 🟠 `--export-policy --out PATH` writes without any live-state check. | File: plugins/autopilot/scripts/autopilot.py:47 | Task: 5
[BLAKE] 🟡 `--group-findings` crashes with a raw Python traceback and exit 1 on a non-object finding. | File: plugins/autopilot/scripts/rework_groups.py:106 | Task: 5
[BLAKE] ⚪ The named acceptance scenario `source_inventory_mapping` appears in no test, README or characterization doc. | File: tests/autopilot/test_helper_provenance.py:527 | Task: 5
[BLAKE] ⚪ `cap_check.capture_range` accepts a `git_dir` option, a source-store concept carried into a stateless helper. | File: plugins/autopilot/scripts/cap_check.py:285 | Task: 3
```

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
B12: fail
B13: pass
B14: fail
B15: pass
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Available: codex (doubt lens plus de-slop), first dispatch with the inlined prompt, no refusal, exit 0, thread `01a19b8f-6516-7a22-92b6-f45b995d9744`. Raw output saved at `docs/dev/tmp/bob-output-ap00013-c1.txt`. FIX bucket: fifteen findings (rows R1, R4, R7-R14, R18-R23 above); VERIFY and KNOWN: none.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Available: copilot backend, model gemini-3.8-flash, exit 0, 66.28 AI credits. Raw output saved at `docs/dev/tmp/carl-output-ap00013-c1.txt`. He ran the full suite and the narrow suites himself and found the same 20-failure picture as Alice.

```
[CARL] 🟠 CI workflow validation test fails due to outdated setup-python action and version pin | File: tests/autopilot/test_package.py:454 | Task: 11
[CARL] 🟡 Function prepare_close exceeds the 50-line limit at 55 lines | File: plugins/autopilot/scripts/review_close.py:467 | Task: 6
[CARL] 🟡 Function stage_review exceeds the 50-line limit at 52 lines | File: plugins/autopilot/scripts/review_stage.py:467 | Task: 5
[CARL] 🟡 Weakened capability assertion self-compares output and passes against pre-change code without checking newly added helper capabilities | File: tests/autopilot/test_facade.py:99 | Task: 10
```

R1: pass
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: fail
R13: pass

Verdict: 28 findings
Tests: 800 passed, 20 failed, 0 skipped (suite run this cycle; 19 are AP 00018 task-7 red-first tests, 1 is the setup-python pin drift in R2, none is an AP 00013 helper test)
