---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v1.md
review: 3
date: 2026-11-02
head_sha: 43f2fd9519f322ae79e0adee2bd5b3c5192a6f23
codex_thread_id: 01a19b8f-6516-7a22-92b6-f45b995d9744
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: 506ddf25
  carl: 6e9a56ea
---

# Review: 00013-autopilot-session-helpers-v1

Incremental diff range: `498ab966e618db7a92a8e8a4c9592c379a9553dd..43f2fd9519f322ae79e0adee2bd5b3c5192a6f23`

codex_rung_guard: fired (1 codex-implemented task(s))

## Review Summary

Reviewed: 16 completed tasks (cycle 3, incremental post-repair verification review against the cycle-2 head `498ab966e618db7a92a8e8a4c9592c379a9553dd`). All five lenses ran in fresh, isolated contexts, in one dispatch, from this native Claude loop session. Nothing was skipped and no guard was bypassed.

- Cycle id `ap00013-c3-20261102`. Raw reviewer outputs are `docs/dev/tmp/{alice,blake,bob,carl,eve}-output-ap00013-c3-20261102.txt`; the five prompts are the matching `-prompt-` files.
- **Eve ran this cycle.** The codex doubt-roster guard fired: task 16's attempt carries `implementor: "codex"`, so the resolved doubt reviewer became `fable` in memory (no state write) and Eve joined as the fifth lens alongside Bob. Cycle 2 recorded `codex_rung_guard: not fired`; task 16 is what changed.
- **The full suite was re-run at this HEAD**, which cycle 2 and the branch repair had not done: 917 passed, 19 failed, 0 skipped, exit 1. Every one of the 19 failures is in `test_controller_capacity.py` (8), `test_controller_owner.py` (7) and `test_controller_owner_recovery.py` (4) — the AP 00018 red-first controller suite documented in `reviews/00013-preexisting-suite-failures.md`. **No AP 00013 helper test failed.** A red suite is not a pass and forbids push.
- Prior-findings input (cycle-2 consolidated findings) and the settled ledger went to the implementation-aware lenses only (Alice, Bob, Carl, Eve). Blake received the PRD-only prompt plus the raw test-gate line: no history, no design doc, no reconciliation, no diff and no file list. He located the code himself.
- Bob resumed his codex thread `01a19b8f-6516-7a22-92b6-f45b995d9744` with the inlined prompt (372842 bytes), exit 0. **Dispatch row `506ddf25` was opened by `review-stage` against the 40485-byte staged render, so its `prompt_bytes` understates what codex received by roughly 9x.** Stated here rather than silently left wrong.
- Carl ran through the Gemini helper on the `copilot` backend with model `gemini-3.8-flash`, exit 0, dispatch row `6e9a56ea`. Verified from the launcher's first stderr line, `gemini-run: backend=copilot model=gemini-3.8-flash`. Not native gemini.
- Alice, Blake and Eve are native Claude Task subagents (`autopilot:alice`, `autopilot:blake`, `autopilot:eve`); Eve is pinned to `model: fable` by her own persona frontmatter.
- Consolidation was the script, not model-side. It merged two row pairs that matched only after suffix stripping: `verification.py:162 ~ verification.py:70` (row R2, Alice + Eve) and `autopilot.py:272 ~ autopilot.py:270` (row R3, Bob + Eve). Eve's bucketed prose was rewritten into the mandated `[EVE] {emoji} ... | File: ... | Task: ...` line shape for the consolidator, preserving her FIX/VERIFY/KNOWN buckets and her wording; the severities on her rows are this gate's assignment, because the doubt contract emits buckets rather than emojis. That transform is stated so nothing reads as her own emoji choice.
- `--ledger-dismiss BLAKE` ran against the 14-entry settled ledger and dismissed nothing: no Blake row this cycle matched a settled entry.
- No `[MECH]` findings: the tautological-test scan checked 52 test functions in 3 test files and found none. The fail-first replay was not run (no `--replay-cmd`), so there is no replay block — a skip, not a pass.
- No prior `checks-2.json` exists, so there was no carry-forward of failed checks into this cycle.
- Context pack: `ok`. `review-stage` reported no errors.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/5] | 🟠 | The full-suite exit criterion remains unmet: 917 passed and 19 failed. These failures belong to the documented AP00018 controller work, outside this helper repair; they remain a push blocker. | tests/autopilot/test_controller_capacity.py:94 | general | BOB, EVE |
| R2 | [2/5] | 🟡 | The log sink now opens after `Popen`, so a sink failure happens after the child has started instead of before it. I probed a log path under a regular file (`afile/x.log`). `refuse()` accepted it, the child was spawned, and `NotADirectoryError` escaped uncaught. The PRD says to validate both artifacts before spawning, and this is a new post-spawn failure path. Open the log first and delete it on spawn failure, or pre-validate the descent without spawning. | plugins/autopilot/scripts/verification.py:162 | 9 | ALICE, EVE |
| R3 | [2/5] | 🟡 | `_write_policy` opens destinations with blocking `O_WRONLY` before checking their type. A FIFO without a reader hangs indefinitely instead of reaching the nonregular-file refusal. Use a nonblocking guarded open, validate the descriptor before truncation, and test a FIFO without a reader. | plugins/autopilot/scripts/autopilot.py:272 | 16 | BOB, EVE |
| R4 | [2/5] | ⚪ | The recovery report has missing spaces: "map0f86a75", "passed494", "Original15", "task16", "cap2", "review03" (and "provenance tests passed44"). | docs/dev/project-management/autopilot/reports/00013-cap-regression-recovery.md:47 | general | ALICE, EVE |
| R5 | [1/5] | 🟠 | Phase 2 exit criterion unmet at HEAD: `pytest tests/autopilot -q` fails with 19 failures (test_controller_capacity 8, test_controller_owner 7, test_controller_owner_recovery 4). The PRD requires this command to pass. For example, `owner.acquire` exits 1 or returns `missing_capability`. The failures are in controller code (separate workstream), not the helpers, but the PRD gate is still unmet and cannot be certified | tests/autopilot/controller_owner_support.py:169 | Phase 2 task 2 | BLAKE |
| R6 | [1/5] | 🟠 | Git-pointer detection can again read a refused external candidate: hard-link `outside/data.json` to `outside/.git`, and `samefile` succeeds, permitting `read_text()` before containment refusal. Perform containment checks before pointer-content reads and identify the supplied repository's actual pointer. Add this alias regression. | plugins/autopilot/scripts/log_sink_refusal.py:123 | 16 | BOB |
| R7 | [1/5] | 🟠 | External Git metadata directories are not detected when safe.bareRepository is explicit, permitting staging inside Git internals and failing test_staging_refuses_nonstandard_external_git_directory | plugins/autopilot/scripts/review_stage.py:464 | 12 | CARL |
| R8 | [1/5] | 🟠 | The new `_scoped` line blanks the PRD when a job's manifest lacks a `prd:` ref; probe with blake's manifest minus `prd:00019` returned `ok: true` and a blake prompt containing no PRD text. A blind reviewer with an empty PRD is reported as a successful staging. Refuse `invalid-input` when a roster job whose prompt inlines the PRD (blake, eve) has no `prd:` ref instead of substituting `""`; add a test. | plugins/autopilot/scripts/review_stage.py:290 | 16 | EVE |
| R9 | [1/5] | 🟠 | The shared `review-context-ID.md` is still written with every kind (`shared = CONTEXT_KINDS`) even when no job is granted the full set, so with the new gating the artifact root holds a context file carrying broad context, tasks, merged PRD+design, pack, history and gate that no manifest granted; "isolation includes references/paths". Build the shared file from the union of granted variants (`frozenset().union(*variants.values())`, falling back to `CONTEXT_KINDS` only when there are no variants) and assert in a test that the staged `review-context` artifact carries no ungranted marker. | plugins/autopilot/scripts/review_stage.py:365 | 16 | EVE |
| R10 | [1/5] | 🟡 | `_worktree_gitdir_pointer` now resolves a relative `gitdir:` pointer against the file's parent directory. It used to resolve it against the current directory. The change is correct, but no test covers a relative pointer, and the new `.GIT` alias test skips on case-sensitive filesystems. Add a relative-pointer test that runs on every filesystem. | plugins/autopilot/scripts/log_sink_refusal.py:133 | 13 | ALICE |
| R11 | [1/5] | 🟡 | `stage_review` never binds `diff_text` to anything. `_input_problem` checks only the `prd` and `repo-tree` refs against the bound context. A `diff:` ref's content in `input_texts` is never compared with `diff_text`, and base_sha/head_sha are never verified against it. A stale or wrong diff can be staged to reviewers while the evidence stays valid. Only the PRD and tree are pinned | plugins/autopilot/scripts/review_stage.py:128 | Phase 1 task 1 | BLAKE |
| R12 | [1/5] | 🟡 | Policy export now unconditionally accesses `os.O_NOFOLLOW`, which is unavailable on Windows. The resulting AttributeError escapes the export handler, regressing the legacy operation. Provide a supported safe-writing implementation or a controlled platform refusal before effects; test with that flag unavailable. | plugins/autopilot/scripts/autopilot.py:272 | 16 | BOB |
| R13 | [1/5] | 🟡 | `test_attempt_validation_does_not_allocate_from_the_supplied_attempt` pins an implementation shape (monkeypatching module-level `range`), not the intent; a `[0] * highest` regression would pass it. Bound peak memory with `tracemalloc` around `check_evidence` (attempt 10**12, peak under 1 MB) instead of the `range` patch. | tests/autopilot/test_cap_recovery_helpers.py:158 | 16 | EVE |
| R14 | [1/5] | 🟡 | The receipt's "494 passed / 0 failed / 0 skipped" binds to cce5dad (pre-merge); hashes match at HEAD but the focused command has not been re-run at 43f2fd9 and I did not run it. Run exactly the 17-file focused pytest command and confirm `494 passed`, 0 failed, 0 skipped. | docs/dev/project-management/autopilot/reports/00013-cap-regression-recovery.md | 16 | EVE |
| R15 | [1/5] | ⚪ | `_write_policy` checks regular file and link count but not the executable bit, git internals or tracked state. The contract's existing-file rules also refuse executable files. It is partial parity, but the repair scope was the hard link. | plugins/autopilot/scripts/autopilot.py:269 | 11 | ALICE |
| R16 | [1/5] | ⚪ | The README says `plan` grants tasks and design text. Design text reaches the context file only when `prd` is also granted, because the merged PRD file is what carries it (plugins/autopilot/scripts/review_stage.py:330). Reword the sentence. | plugins/autopilot/README.md:286 | 12 | ALICE |
| R17 | [1/5] | ⚪ | Staged writes are hardened less than verification writes. `_destination_problem` checks for symlinks and then `_write` uses `O_NOFOLLOW` on the leaf only. An intermediate directory swapped to a symlink after the check is followed. `_write_all` can also leave partial artifacts after a mid-sequence `write-failed`. `verification.py` uses descriptor-pinned opens instead | plugins/autopilot/scripts/review_stage.py:471 | Phase 1 task 1 | BLAKE |
| R18 | [1/5] | ⚪ | `custody.refresh_hold_prd` interpolates `entry['batch']`, `entry['op_id']` and `entry['commit_range']` into frontmatter and the notice without a newline check. Only `detail` is collapsed. A hostile or buggy controller caller could inject frontmatter lines. The function is not exposed through the facade, so exposure is low | plugins/autopilot/scripts/custody.py:37 | Phase 1 task 1 | BLAKE |
| R19 | [1/5] | ⚪ | The facade exposes `--prepare-close`, `--verify` and `--controller-action`, beyond the four exports named in the Helpers module line. The spec's file list and tasks imply them, so this is not treated as scope creep. The spec text should list them | plugins/autopilot/scripts/autopilot.py:28 | Phase 2 task 1 | BLAKE |
| R20 | [1/5] | ⚪ | The `custody.py` notice tells users to "run autopilot custody resolve". That command exists nowhere in this package | plugins/autopilot/scripts/custody.py:76 | Phase 1 task 1 | BLAKE |
| R21 | [1/5] | ⚪ | Stale repair worktree and merged branch left behind: `/Users/bob/git/src/worktrees/agent-plugins/ap00013-repair` (at 0f86a75) and `repair/ap00013-cap-regression` still exist after the merge in 10a1c73 (AGENTS.md cleanup rule). | N/A | general | EVE |
| R22 | [1/5] | ⚪ | Task-16 attempt record mixes one full SHA with two abbreviated ones (`"cce5dad...", "a4d4ad0", "0f86a75"`) in a durable record. Expand to full 40-hex SHAs via statectl. | docs/dev/project-management/autopilot/state.json:976 | 16 | EVE |
| R23 | [1/5] | ⚪ | CHANGELOG entry uses internal workflow jargon ("cap recovery refuses hardlinked policy outputs...") in a user-facing changelog. Reword to the user-visible effect. | plugins/autopilot/CHANGELOG.md:32 | 16 | EVE |
| R24 | [1/5] | ⚪ | KNOWN-1: No packaged fixture grants `implementation-audit:`, `plan:` or `test-results:` refs, so under every packaged expected context alice/bob/carl now get only the PRD path in their context file; the grants exist only in the modified test helper `context_for`. Out of scope: the manifest producer is the controller (AP 00018+). | plugins/autopilot/scripts/review_stage.py | 16 | EVE |
| R25 | [1/5] | ⚪ | KNOWN-2: A tail sweep can now re-propose a row the decision gate already tasked (the snapshot carries only carry refs, no tasked-row set). Out of scope: faithful to the pinned source; durable application/dedup is controller-owned by the PRD. | plugins/autopilot/scripts/review_close.py | 16 | EVE |
| R26 | [1/5] | ⚪ | KNOWN-3: `test_verify_refuses_case_alias_of_an_argv_file` and `test_sink_refuses_case_alias_of_worktree_pointer` skip on case-sensitive filesystems (Linux CI), so the R7/R8 fixes are only exercised on case-insensitive hosts. Out of scope: no portable way to create a case alias on a case-sensitive FS. | tests/autopilot/test_cycle1_hardening_sinks.py | 16 | EVE |
| R27 | [1/5] | ⚪ | KNOWN-4: Hold stubs 00022, 00023, 00025-00029 and the batch `cap-overflow` records for R1, R2, R4-R8 remain open although the repair fixed them (only 00024/R3 is still live). Out of scope: closing them is a human triage decision. | N/A | general | EVE |
| R28 | [1/5] | ⚪ | KNOWN-6: The settled ledger JSON was reflowed from one-line records to multi-line (whole-file churn over 14 entries). Out of scope: formatter-hook reflow on touched files (known host quirk). | docs/dev/project-management/reviews/00013-autopilot-session-helpers-v1-ledger.json | general | EVE |

## Decision gate

Cycle 3, `rework_cap` 2. No 🔴 CRITICAL row, so no rework design applies.

### Prior-cycle verification: the branch repair holds

Alice and Eve independently confirmed, by reading the code and by probing it, that all nine supported cycle-2 findings the repair claimed are fixed: R1 (spawn `OSError` caught, `spawn-failed`), R2 (`_link(coverage=False)` for tail sweep), R4 (`_context_file` per-kind gating), R5 (`rev-parse --is-inside-git-dir`), R6 (`fstat` `st_nlink` before `ftruncate`), R7 (`samefile` pointer identity), R8 (`_same_path` by `samefile`), R13 (test asserts the `dirty-tree` refusal with a spawn marker) and R15 (`enumerate` walk, no `range` allocation). Eve additionally verified provenance: `10a1c73` is a true merge of `7c9070c` and `0f86a75`, and the sha256 of README, CHANGELOG, `verification.py`, `review_stage.py`, `autopilot.py` and the receipt all match the source-map and receipt entries, so `tested_package_revision: cce5dad` is consistent.

### Verified this cycle, before classifying

Three rows were checked against the code or probed directly rather than taken at face value:

- **R6 — discarded, verified reason.** Bob's ordering claim is correct: `_identity_hit` (`log_sink_refusal.py:30`) runs before the containment check at `:35`, so `_worktree_gitdir_pointer` can `read_text()` a candidate that is about to be refused as outside the repository. But `_identity_hit` returns either a refusal reason or `None`; it can only ever ADD refusals. The containment check then refuses the external path regardless. No path that should be refused becomes acceptable, so this is not the boundary bypass the 🟠 asserts. It is an ordering/hygiene defect on a path the caller named as its own log sink, with no disclosure channel. Discarded with reason `verified not a bypass: pointer read can only add refusals` and recorded in the ledger so it is not re-argued.
- **R7 — confirmed real, evidence corrected.** Carl's defect is real and I reproduced the mechanism: `git -c safe.bareRepository=explicit -C <bare> rev-parse --is-inside-git-dir` exits 128 (`fatal: cannot use bare repository ... (safe.bareRepository is 'explicit')`) on git 2.56.0, and `review_stage.py:465` requires `returncode == 0` to refuse, so the git-internals guard **fails open** on a host carrying that config; `_toplevel` then also fails, leaving `top` `None` and the destination accepted. Carl's stated evidence is wrong, though: `test_staging_refuses_nonstandard_external_git_directory` **passed** in this cycle's gate (the only 19 failures are controller tests), because this host sets no such config. The finding stands on the mechanism, not on his test claim.
- **R8 and R9 — confirmed real by reading the code.** `review_stage.py:290-291` substitutes `scoped["prd"] = ""` whenever a job's manifest omits a `prd:` ref, and `:365` sets `shared = CONTEXT_KINDS` unconditionally, so the shared `review-context-{id}.md` always carries every input kind even when no job was granted the full set. Both fail open where the PRD requires fail-closed: the first lets a blind review of an empty PRD report `ok: true`, the second leaves ungranted content readable in the shared artifact root that every reviewer can open.

### Settled deferrals, excluded from the convergence test

**R1 and R5 — the same finding, two citations.** Both state the PRD's Phase 2 exit criterion is unmet because the full suite is red. This is cycle 2's R3, which cycle 2's cap-out recorded as a `cap-overflow` deferral and which its stall migrated into the batch deferred JSON; hold stub 00024 is still live for it (Eve's KNOWN-4). It is therefore a **settled deferral recorded by a prior cycle** and is excluded from "unresolved" under the Cap check's exclusion rule — a decision already taken is not re-counted. It is not excluded because it is false: the suite is red, 19 controller tests fail, and ownership is AP 00018's. **The criterion remains unmet and this forbids a push.** No controller code was touched during this review.

### Routed to verification, and resolved by evidence

**R14** named an exact runnable command, so it was queued to `reviews/00013-autopilot-session-helpers-v1-checks-3.json`. A cap-out cycle runs no work pass, which would have left the check unrun with no later cycle to reach it, so this gate ran it directly as decision-gate evidence: the 17-file focused command returned **494 passed, 0 failed, 0 skipped** at HEAD `43f2fd9`. The receipt's count therefore holds at the merged head, not only at `cce5dad`. Recorded with `result: {"exit": 0}`. R14 is resolved, not deferred.

### Discard, single-voice Medium or Low

R10, R11, R12, R13, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24, R25, R26, R27 and R28 are each `[1/5]` at 🟡 or ⚪, so they are discarded and appended to the settled ledger with reason `single-voice`, auto-dismissing a re-raise next cycle. This is not a claim that any is false — R12's Windows `os.O_NOFOLLOW` claim in particular is also not a regression of this repair (the flag is used the same way elsewhere in `verification.py`) and this package targets macOS and Linux. R24-R28 are Eve's own KNOWN bucket, which she already scoped out to the controller workstream or to host quirks; the ledger keeps them visible rather than dropping them.

### Convergence test

Three genuine unresolved 🟠 HIGH rows remain after the exclusions above: **R7**, **R8** and **R9**. A 🟠 is never single-voiced away and none of the three matches a settled ledger entry or an existing deferral. **The cycle does not converge.**

`state.cycle` 3 >= `state.rework_cap` 2, so no further automatic rework is permitted, and no 🔴 CRITICAL is open. This is the loop-mode cap-out path with all unresolved findings at or below high, which requires `autopilot cap-check` before any deferral.

Every unresolved finding of this cycle is recorded in `state.deferred_decisions` as a `cap-overflow` record, regressed or not, before any stall — R7, R8, R9, and the multi-voice Medium/Low rows R2, R3 and R4 that a converged cycle would have swept.

Verdict: 28 findings
Tests: 917 passed, 19 failed, 0 skipped (suite run this cycle, exit 1, treated as failed)

## Alice

Available: native Claude Task subagent (`autopilot:alice`, high effort), exit 0. Raw output at `docs/dev/tmp/alice-output-ap00013-c3-20261102.txt`.

Alice verified every supported cycle-2 finding as resolved in the code, citing the fix site for each, and ran two probes against `verification.run_verification` in a temporary repository. She did not re-run the suite (the staged test-gate block carried it). She raised rows R2, R10, R15, R16 and R4.

R1: fail
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

## Blake

Available: native Claude Task subagent (`autopilot:blake`, high effort), PRD-only, exit 0. Raw output at `docs/dev/tmp/blake-output-ap00013-c3-20261102.txt`.

Blake received the PRD plus the raw test-gate line and nothing else — no review history, no design doc, no reconciliation, no diff, no file list. He located the code himself, read the scripts, the facade, the README and the changelog, and ran only narrow checks: `tests/autopilot -k "not controller"` (819 passed), `tests/autopilot -k controller` (98 passed, 19 failed, matching the gate), and `scripts/validate.py` (3 packages, 15 skills). He confirmed the spec's file list, the no-runtime-import and no-state-discovery constraints, the `catchup.py` source parity, and all nine named scenarios as traceable. He modified nothing. He raised rows R5, R11, R17, R18, R19 and R20.

B1: pass
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

Available: codex (doubt lens plus de-slop), exit 0, resumed thread `01a19b8f-6516-7a22-92b6-f45b995d9744`, inlined prompt of 372842 bytes. Raw output at `docs/dev/tmp/bob-output-ap00013-c3-20261102.txt`. FIX bucket: three findings (rows R6, R3, R12). VERIFY bucket: none. KNOWN: one (row R1). Every residual finding lands in exactly one of FIX, VERIFY or KNOWN. The doubt lens never dropped and no Claude fallback was used.

R1: fail
R2: pass
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
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Available: `copilot` backend, model `gemini-3.8-flash`, exit 0, dispatch row `6e9a56ea`. Backend and model verified from the launcher's stderr line `gemini-run: backend=copilot model=gemini-3.8-flash`. Raw output at `docs/dev/tmp/carl-output-ap00013-c3-20261102.txt`; the file holds his tool transcript before his finding and verdict lines. He raised one row, R7, whose mechanism this gate reproduced and whose test-failure evidence this gate refuted (see Decision gate).

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

## Eve

Available: native Claude Task subagent (`autopilot:eve`, `model: fable` pinned by her persona), exit 0. Raw output at `docs/dev/tmp/eve-output-ap00013-c3-20261102.txt`. She joined because the codex doubt-roster guard fired on task 16's codex implementor.

Eve verified every supported cycle-2 fix with its own probe, verified the merge and hash provenance of the repair chain, and reported 16 residual findings as 9 FIX, 1 VERIFY and 6 KNOWN. Her probes ran against temporary clones under `/tmp`; `git status` after them showed only the pre-existing modified state files. She raised rows R2, R3, R8, R9, R13, R14, R21, R22, R23 and the KNOWN rows R24-R28 and R1.

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Coordinator evidence correction after session exit

This addendum corrects the R7 evidence attribution without changing any
reviewer's submitted finding or the cap disposition. At unchanged review
head 43f2fd9519f322ae79e0adee2bd5b3c5192a6f23, the command below passed
2 tests in 0.28s (exit 0) with the default Git configuration:

`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_cap_recovery_helpers.py::test_staging_refuses_nonstandard_external_git_directory -q`

The same command with `--tb=short` and command-scoped environment
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.bareRepository GIT_CONFIG_VALUE_0=explicit`
failed both cases in 0.30s (exit 1): staging returned no refusal/error key.
Carl's failing-test evidence is reproducible under that configuration; the
unqualified statement above that his test claim is wrong is withdrawn.
The default full-suite result remains exactly 917 passed and 19 failed.

Actual reviewer models verified from native session JSONL and launch evidence:
Alice and Blake: claude-sonnet-5-5; Eve: claude-fable-5-1; Bob:
gpt-6-astra with high effort, resumed original thread
01a19b8f-6516-7a22-92b6-f45b995d9744; Carl: Copilot backend,
gemini-3.8-flash. No unavailable model identifier is inferred.
