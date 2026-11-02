---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v1.md
review: 2
date: 2026-11-02
head_sha: 498ab966e618db7a92a8e8a4c9592c379a9553dd
codex_thread_id: 01a19b8f-6516-7a22-92b6-f45b995d9744
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
dispatch_rows:
  bob: 4a23053d
  carl: 82ec3e41
---

# Review: 00013-autopilot-session-helpers-v1

Diff range: `843e6e7d51c56377adc1c01fab9ae7ea7755e1f4..498ab966e618db7a92a8e8a4c9592c379a9553dd`

codex_rung_guard: not fired

## Review Summary

Reviewed: 15 completed tasks (cycle 2, incremental rework review against the cycle-1 head `6c1352c6416e7a21bbbb72980973a01541c7e926`). All four lenses ran in fresh, isolated contexts. Eve did not run: no task attempt has `implementor: codex`.

This cycle was assembled across two host sessions. That is stated here so nothing reads as silent:

- Alice and Blake ran first, dispatched from a Codex coordinator session into fresh native Claude sessions (`claude-sonnet-5-5`, high effort; Alice session `807ecf32-911e-4a79-840f-c723308d51f6`, Blake session `858c6af6-aef3-4289-9744-41cd4f9e258a`, both exit 0). Their complete raw outputs and the model evidence are preserved in `docs/dev/project-management/autopilot/reports/00013-cycle2-host-recovery.md`.
- Bob and Carl could not run from that coordinator: `codex-run.sh` and `gemini-run.sh` both exited 3 on their recursion guard ("already inside a CLI agent"). No marker was cleared and no guard was bypassed. Their first dispatch rows were closed `error` (`437e79ba`, `64303074`) and the staged placeholder row `c9ec8601` was closed `superseded`.
- Bob and Carl then ran from this session, a native Claude loop session where neither `CODEX_SESSION_ID` nor `AUTOPILOT_DISPATCH_DEPTH` is set, so the guard did not fire. Bob resumed his cycle-1 codex thread `01a19b8f-6516-7a22-92b6-f45b995d9744` with the 247928-byte inlined prompt (design excluded; diff scoped to `plugins/autopilot`, `tests/autopilot`, `tools/autopilot/update_helper_map.py`), exit 0. Carl ran on the native `gemini` backend, exit 0. New dispatch rows `4a23053d` and `82ec3e41`, both closed `ok`.
- Prior-findings input (restored cycle-1 dispositions plus the duplicate-review reconciliation, `reviews/00013-duplicate-review-reconciliation.md`, committed as `49a27f9`) was supplied to the implementation-aware lenses only. Blake received the PRD-only prompt plus the raw test-gate result: no history, no design, no reconciliation, no diff and no file list.
- Scratch cycle id `ap00013-c2-20261102`. Raw reviewer outputs are `docs/dev/tmp/{alice,blake,bob,carl}-output-ap00013-c2-20261102.txt`; the four prompts are the matching `-prompt-` files.
- Consolidation folded Bob's `verification.py:139` row onto Alice's `verification.py:144` row (R1) after suffix stripping; both describe the same uncaught spawn failure (reconciliation D13). Bob's bulleted `[BOB]` lines were bullet-stripped for the consolidator. Carl's output file holds his gemini tool transcript before his verdict lines; only his verdicts and his no-issues line are reproduced here.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟡 | A missing or non-executable argv[0] raises an uncaught `FileNotFoundError` from `Popen` in `_execute`, after the log sink is opened. I ran `run_verification(argv=['/no/such/cmd'])` and got the exception plus an empty `l.log`. This contradicts the docstring ("nothing written"), and the facade `_call` catches only TypeError/ValueError, so the user gets a traceback and no JSON report. This is the spawn failure from the reconciliation's D13, not the discarded R16 sink case. Catch the spawn `OSError`, remove or avoid the log, and return `ok=false` with a controlled error | plugins/autopilot/scripts/verification.py:144 | 9 | alice, bob |
| R2 | [1/4] | 🟠 | Tail-sweep close is refused whenever the chosen rows are a subset of the review's evidence findings. `_link` demands every evidence finding be linked by exactly one chosen row, but tail sweep is designed to skip coverage (`_cross_check(..., coverage=False)`). I probed R2 and R4 chosen out of R2, R3 and R4 with a valid snapshot: `ok: False`, `attribution_mismatch`, "never linked ['F5']". The tail-sweep path only succeeds when the evidence holds exactly the swept findings, and the tests build evidence that way. | plugins/autopilot/scripts/review_close.py:222 | 3 | blake |
| R3 | [1/4] | 🟠 | The PRD's Phase 2 exit criterion is not met. The full `tests/autopilot` suite ran with 19 failures in `test_controller_capacity.py`, `test_controller_owner.py` and `test_controller_owner_recovery.py`. I reproduced the first one: the `self.acquire(operator)` step returns exit 1 instead of 0. These are controller tests, not helper tests, so I can't tie the cause to this PRD. The criterion is still red. | tests/autopilot/test_controller_capacity.py:94 | general | blake |
| R4 | [1/4] | 🟠 | R7 remains incomplete: per-job context variants filter only pack and history. `_context_file` still exposes broad context, tasks, merged PRD/design and test results when their refs are absent from that job's manifest. Filter every supplied input and referenced artifact, or reject inconsistent manifests before writing. | plugins/autopilot/scripts/review_stage.py:315 | 12 | bob |
| R5 | [1/4] | 🟠 | R8 still permits external Git internals with nonstandard directory names. An external `--separate-git-dir` directory makes `_toplevel` return None, which is treated as an ordinary destination. Detect Git metadata directories before accepting external roots; add a separate-git-dir regression. | plugins/autopilot/scripts/review_stage.py:432 | 12 | bob |
| R6 | [1/4] | 🟠 | R6 still permits live-state overwrite through hard links. An ordinary output pathname hard-linked to state.json passes `_in_live_state`, then `write_bytes` truncates the shared inode. Refuse multiply linked output files before export. | plugins/autopilot/scripts/autopilot.py:223 | 12 | bob |
| R7 | [1/4] | 🟠 | The new exact-name `.git` guard misses `.GIT` on case-insensitive filesystems. A linked-worktree pointer addressed with that spelling passes the remaining regular-file checks and can be replaced by the log writer. Identify the actual worktree pointer by filesystem identity and test the alternate spelling. | plugins/autopilot/scripts/log_sink_refusal.py:117 | 13 | bob |
| R8 | [1/4] | 🟠 | R11 compares resolved path spellings rather than file identity. On case-insensitive filesystems, argv `SCRIPT.PY` and log `script.py` can name the same file while comparing unequal, allowing the script to be deleted before execution. Compare existing candidates with samefile and retain lexical checks for absent destinations. | plugins/autopilot/scripts/verification.py:70 | 12 | bob |
| R9 | [1/4] | 🟡 | External artifact roots are now refused whenever any ancestor is a symlink, so macOS system aliases like `/tmp` and `/var` are refused. I ran `_destination_problem` with a root under `/tmp` and it returned "artifact_root is reached through a symlink". The contract only refuses symlink components below the supplied root, and the new test passes only because pytest `tmp_path` is pre-resolved. Compare the root's own components, or accept ancestors that resolve to the same location | plugins/autopilot/scripts/review_stage.py:457 | 5 | alice |
| R10 | [1/4] | 🟡 | Simplification: `_in_live_state` is implemented twice with the same casefold four-part scan, in the facade and in review_stage. Only the inputs differ (facade also applies realpath). Have the facade import the review_stage helper and pass both spellings | plugins/autopilot/scripts/autopilot.py:88 | 10 | alice |
| R11 | [1/4] | 🟡 | `reuse_verdict` checks that the prior artifact's head is an ancestor of the supplied `head_sha`, that only store paths changed between them, and that the working tree is clean. It never checks that `head_sha` is the repository's actual HEAD. A caller passing an older `head_sha` while HEAD carries later product commits gets "reused", because cleanliness is judged against HEAD. This weakens "changed code invalidates it". | plugins/autopilot/scripts/dirty_tree.py:62 | 4 | blake |
| R12 | [1/4] | 🟡 | The facade's live-state refusal covers only request and policy inputs (`_INPUTS`) plus `--out`. `--project-root`, `--artifact` and `--log` are not checked. Writes under the project-management store are still refused by `log_sink_refusal.refuse`, but the facade does not itself refuse a `--project-root` inside `docs/dev/project-management/autopilot`. The verification argv would run with that directory as cwd. | plugins/autopilot/scripts/autopilot.py:188 | 11 | blake |
| R13 | [1/4] | 🟡 | The new pre-run symlink-dirt test accepts either refusal or execution producing non-reusable evidence, although the contract requires refusal before spawning. Assert the dirty-tree refusal and use a spawn marker to prove the command never runs. | tests/autopilot/test_cycle1_boundaries_verify.py:144 | 12 | bob |
| R14 | [1/4] | 🟡 | `_stage_inputs` packs eight named inputs into two positional tuples solely to unpack them immediately. Keep the extracted helper, but use named keyword parameters so callers cannot silently interchange same-typed inputs. | plugins/autopilot/scripts/review_stage.py:531 | 13 | bob |
| R15 | [1/4] | 🟡 | Reconciliation D22 remains open: attempt-sequence validation allocates `list(range(1, highest + 1))` from an unbounded supplied attempt. A small evidence document can exhaust memory. Validate sequence length and consecutive values without allocating proportional to the highest attempt. | plugins/autopilot/scripts/review_evidence.py:276 | 3 | bob |
| R16 | [1/4] | ⚪ | `_write` opens staged review artifacts with `O_TRUNC` and `O_NOFOLLOW` but not `O_EXCL`. `_file_problem` checks the destination before the write, so a hard link or file swapped in between would be truncated. The window is small and only affects caller-supplied artifact roots. | plugins/autopilot/scripts/review_stage.py:463 | 5 | blake |
| R17 | [1/4] | ⚪ | `cap_check`, `custody` and `gate_lead` have no facade command. They are covered only by function-level tests and source-map entries. This fits the PRD's "port by function", and I flag it only because the README's facade list omits them. | plugins/autopilot/README.md:252 | 12 | blake |
| R18 | [1/4] | ⚪ | Resolve reconciliation D30 with a temporary-repository index-refresh check: change only a tracked file's mtime, record index bytes/mtime, call `_dirty_check`, and compare the index afterward; repeat with GIT_OPTIONAL_LOCKS=0 to establish whether the claimed read-only probe writes metadata. | plugins/autopilot/scripts/dirty_tree.py:19 | 4 | bob |

## Decision gate

Cycle 2 of cap 2. No 🔴 row, so no rework design applies. Seven 🟠 rows are unresolved (R2-R8), so the cycle does NOT converge, and `state.cycle >= state.rework_cap`, so no third rework cycle is allowed. This is the loop-mode cap-out path.

Convergence test: a 🟠 is never single-voiced away, and none of R2-R8 matches a settled deferral. The three settled deferrals on record (`state.deferred_decisions`, cycle 1) are all 🟡 and sit at `dirty_tree.py:19` (probe timeout), `update_helper_map.py:478` and `update_helper_map.py:286`. R18 names `dirty_tree.py:19` but is a different claim (index-refresh side effects, reconciliation D30), and is single-voice ⚪ in any case.

Cap-out recording: every unresolved finding of this cycle is recorded in `state.deferred_decisions` as a `cap-overflow` record, regressed or not, before the stall.

Discard, single-voice Medium or Low (R9-R18): appended to the settled ledger with reason `single-voice`, so a re-raise is auto-dismissed. This is not a claim that any of them is false. R15 and R18 restate reconciliation items D22 and D30, which the reconciliation already records as open coordinator decisions; the ledger keeps them visible rather than dropping them.

R1 is the one multi-voice row (Alice and Bob, 🟡): the uncaught `Popen` spawn failure, reconciliation D13. It does not block convergence and the cap-out path runs no rework pass, so it is recorded as a cap-overflow deferral with the rest rather than swept.

R3 is Blake's blind reading of the PRD's Phase 2 exit criterion against the live suite. The 19 failures he reproduced are the AP 00018 controller task-7 red-first tests, documented in `reviews/00013-preexisting-suite-failures.md`; they are not AP 00013 helper tests. The criterion is nevertheless red at this head, which is why it is recorded and not discarded.

## Alice

Available: fresh native Claude session (`claude-sonnet-5-5`, high effort), session `807ecf32-911e-4a79-840f-c723308d51f6`, exit 0. Model verified from the native session JSONL. Raw output saved at `docs/dev/tmp/alice-output-ap00013-c2-20261102.txt`; complete output also preserved in `reports/00013-cycle2-host-recovery.md`.

Alice confirmed cycle-1 findings R1-R14 resolved in the code, and raised three new rework issues (rows R1, R9, R10 above), two of which she reproduced by running the code. She read each fix and did not re-run the suite. She did not re-derive reconciliation items D19 and D22, which the reconciliation reports as open coordinator decisions.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: fail
R11: pass
R12: pass
R13: pass

## Blake

Available: fresh native Claude session (`claude-sonnet-5-5`, high effort), PRD-only, session `858c6af6-aef3-4289-9744-41cd4f9e258a`, exit 0. Model verified from the native session JSONL. Raw output saved at `docs/dev/tmp/blake-output-ap00013-c2-20261102.txt`.

Blake received the PRD-only prompt plus the raw test-gate result. No review history, no design doc, no reconciliation, no diff and no file list were supplied; he located the code himself. He raised rows R2, R3, R11, R12, R16 and R17 above, probing R2 and the first controller failure directly.

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
B15: pass
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Available: codex (doubt lens plus de-slop), exit 0, resumed thread `01a19b8f-6516-7a22-92b6-f45b995d9744`, inlined first prompt of 247928 bytes with the design excluded. Raw output saved at `docs/dev/tmp/bob-output-ap00013-c2-20261102.txt`. FIX bucket: nine findings (rows R1, R4-R8, R13-R15 above). VERIFY bucket: one (R18). KNOWN: none. Every residual finding lands in exactly one of FIX, VERIFY or KNOWN.

Bob's first dispatch from the Codex coordinator session exited 3 on the recursion guard without running a model (row `437e79ba`, closed `error`). He ran from this native session instead, where the guard does not fire. The doubt lens never dropped and no Claude fallback was used.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Available: native `gemini` backend, exit 0, dispatch row `82ec3e41`. Raw output saved at `docs/dev/tmp/carl-output-ap00013-c2-20261102.txt`. His first dispatch from the Codex coordinator session exited 3 on the same recursion guard without running a model (row `64303074`, closed `error`); this was never model unavailability, so Carl is not batch-latched unavailable.

Carl read the scoped diff and the changed scripts, ran `scripts/validate.py`, the validator unit tests, and the cycle-1 regression and touched test files himself, and checked the line counts of every changed script.

```
[CARL] ✅ No issues found
```

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

Verdict: 18 findings
Tests: TESTS_LINE_PLACEHOLDER
