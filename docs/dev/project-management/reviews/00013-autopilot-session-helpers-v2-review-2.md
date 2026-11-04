---
prd: docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v2.md
review: 2
date: 2026-11-04
head_sha: 69ebc4b87a816020e398a05809b37d07cd290b1f
codex_thread_id: 01a1a56f-75f2-7a72-b860-dbedecf63943
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: available
dispatch_rows:
  bob: cc720045
  carl: 1aec4c56
---

# Review: 00013-autopilot-session-helpers-v2

Diff range: `2998ffbdfa57fac33042b78efa3fc9b32e066c1a..69ebc4b87a816020e398a05809b37d07cd290b1f`

codex_rung_guard: not fired

## Review Summary

Reviewed: 8 completed tasks (cycle 2, **incremental** review scoped to the cycle-1 rework commits). All five lenses ran in fresh, isolated contexts. Nothing was skipped, no lens was narrowed and no guard was bypassed.

- Cycle id `00013v2-c2`. Raw reviewer outputs are `docs/dev/tmp/{alice,blake,bob,carl,eve}-output-00013v2-c2.txt`; the five prompts are the matching `-prompt-` files.
- Scope: `review-stage --since 2998ffbdfa57fac33042b78efa3fc9b32e066c1a`, the cycle-1 review file's `head_sha`. Staging reported no errors. 38 files, 3367 insertions, 171 deletions.
- **Eve ran as the opt-in fifth lens** because the PRD frontmatter resolves `doubt_reviewer: fable`. The codex doubt-roster guard did **not** fire: no task in `state.tasks` carries an `attempts[].implementor == "codex"`. Bob (codex) and Eve (fable) therefore both carried the doubt rubric.
- **Bob resumed his cycle-1 codex thread** (`--resume-thread 01a1a56f-75f2-7a72-b860-dbedecf63943`), so his cycle-2 pass verifies the rework against his own cycle-1 critique rather than re-reviewing from zero. The thread id was re-emitted unchanged.
- Bob ran on the inlined prompt (561962 bytes: head block, review context verbatim, the full 343633-byte diff in a fenced block, then the persona). His dispatch row's `prompt_bytes` was measured against the 41784-byte staged render `review-stage` wrote, so that row understates what codex received.
- Blake's inputs stayed PRD-only. He was told explicitly not to read anything under `docs/dev/tmp/` (beyond his own prompt), `docs/dev/project-management/reviews/`, `.../autopilot/reports/`, `.../designs/`, or `state.json`/`session-brief.md`/`contract-card.md`. No design doc, settled-decisions block or prior-findings addendum was rendered into his prompt. No cycle-1 review, parent-alias audit, Pat output or coordinator ruling reached him. He records that limit himself in his section.
- The settled-decisions ledger (16 entries) was passed as `--settled-ledger` to Alice, Bob, Carl and Eve, and as `--ledger`/`--ledger-dismiss BLAKE` to consolidation. One Blake re-raise was auto-dismissed; it is reproduced below.
- pack: ok (`docs/dev/tmp/engram-pack-00013v2-c2.md`).
- Consensus engine: `legacy` (single Alice subagent). No `consensus_run_id`.
- No reviewer needed a format or verdict retry this cycle. Bob emitted his issue lines with a markdown bullet prefix (`- [BOB] …`), which `consolidate_findings.py` tolerates by design.

### Measured test evidence (read, not re-derived)

The cycle's gate ran once, inside `review-stage`, at this HEAD with a clean tree:

`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` → exit 1, **19 failed, 1091 passed in 279.28s**.

**The verify counts reader did not parse that summary** — the same defect recorded in cycle 1 and in the session brief (`autopilot verify --cycle 1` returned `recorded: false, raw_line: null` for the identical `-q` command at `852875a`). `review-stage` returned `verdict: "stale"` and `tests_line: "Tests: counts unavailable (suite run this cycle, exit 1, no PASS/FAIL/SKIP/EXIT summary line)"`. The counts in the `Tests:` line below are therefore read verbatim out of this cycle's own gate log, `docs/dev/tmp/gate-00013v2-c2.log:465`. `last-verification.json` was **not** written or fabricated.

**Deviation stated loud:** step 6's fallback for a non-counts gate line is to run `autopilot verify` once. That was NOT done, deliberately. The suite had already run this cycle under the same command at the same HEAD, and the reader provably cannot parse this `-q` summary (demonstrated at `852875a` in cycle 1), so the call would have been a second identical five-minute run whose only outcome is the same unparseable verdict. Provenance is stated rather than hidden; no counts are claimed that the log does not show.

**The 19 failures are EXACTLY the AP00018 controller nodes** — 8 in `tests/autopilot/test_controller_capacity.py`, 7 in `test_controller_owner.py`, 4 in `test_controller_owner_recovery.py` (`rg '^FAILED '` over the gate log returns 19 lines, all in those three files). They are a recorded external deferral owned by AP00018, outside this PRD's write paths. **No AP00013 helper node failed: all four helper nodes that were red at cycle 1 are green.**

Also green at this HEAD, re-run by the coordinator this cycle:

- `python3 -m unittest discover -s scripts` → Ran 59 tests, OK.
- `python3 scripts/validate.py` → Validated 3 plugin package(s) and 15 skill(s).
- `python3 scripts/generate_marketplace.py --check` → marketplace.json is up to date.

Mechanical fail-first replay: 131 touched tests ran, 73 failed against base, 58 passed; 0 files uncollectable at base — the four `[MECH]` rows absorbed below.
Tautological-shape check: 76 test functions in 5 files, **no** finding.

Cycle 1's verification-check queue (`00013-autopilot-session-helpers-v2-checks-1.json`) holds one entry and it exited **0**, so nothing was carried forward into this cycle's table.

### Agent Status

- Alice: ✅ Available (native Claude subagent; ran `test_helper_rework_stage.py` narrowly, 17 passed, plus three scratch probes under `/tmp/alice-probe-*`)
- Blake: ✅ Available (native Claude subagent, blind; ran `test_helper_recovery_v2.py` + `test_cap_recovery_helpers.py`, 48 passed, and `update_helper_map.py --check`)
- Bob: ✅ Available (codex `gpt-6-astra`, reasoning high, static-only sandbox, exit 0; cycle-1 thread resumed and re-emitted)
- Carl: ✅ Available (copilot backend, explicit `gemini-3.8-flash`, exit 0; output carries narrative tool-trace noise around its issue line and `R{n}` verdicts, which consolidation ignores)
- Eve: ✅ Available (Claude Fable 5 Task subagent; re-ran the recorded parent-alias probe against HEAD bytes and the T3 allocation probe)

### Note on row R1 (fail loud)

`consolidate_findings.py` merged four citations onto R1 by stripping line suffixes (`log_sink_refusal.py:157 ~ :194 ~ :192 ~ :191` — its own warning line). All four describe **one** defect, from two angles: Alice cites the `_symlinked_component` stop rule at `:157`; Bob, Carl and Eve cite the `_pinned_parent_fd` mixed-spelling `resolve()` fallback at `:191`/`:192`/`:194`. Eve's and Alice's fixes both touch the pair together, so this is genuinely one fix, not a merge artefact. Row R2 likewise merged `verification.py:234 ~ :440` — the same unguarded `_kill_group`-after-reap exposure at both call sites, which Alice's own text names explicitly.

Rows R4, R6, R9 and R12 are **four reviewers' independent reports of the same `TimeoutExpired` defect** at `review_stage.py:411` (Alice, Blake, Bob, Eve). The consolidator kept them separate because their descriptions diverge too far to merge, so the `[1/5]` cells understate real 4-of-5 agreement. Any rework batch must treat them as one fix. They are counted once for the convergence test.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [4/5] | 🟠 | Parent-alias defect confirmed at HEAD: `_pinned_parent_fd` resolves below-root symlinks in the mixed-spelling fallback, and `_symlinked_component`'s root-alias stop rule skips a path that leaves the repo and returns through a symlink to the root. Reproduced: with an aliased root, `run_verification` returns ok and writes the log through two symlinks, while the same-spelling run refuses with the wrong slug (`sink-failed`). Tracked targets are still refused and no outside-root write was observed. The CHANGELOG bullets "treat an aliased project root and a resolved one alike" and "refuses an output path that passes through a symlink ... whichever way ... spelled" overclaim until fixed. Fix: make the stop rule apply only to the leading root spelling, not to any later component, and drop `resolve()` from the fallback in favour of descending the unresolved names; add a test where the return symlink points at the root itself. Eve independently re-ran the recorded probe against HEAD bytes: the `mixed_symlink` row overwrote the internal sentinel, the `same_symlink` row refused with ENOTDIR. | plugins/autopilot/scripts/log_sink_refusal.py:157 | 5 | ALICE, BOB, CARL, EVE |
| R2 | [2/5] | ⚪ | `_kill_group(result["pgid"])` runs after the leader was reaped (`proc.wait`). If no descendant is left, the pid can be recycled and `killpg` could signal an unrelated process group. The window is tiny, and the same exposure applies to the artifact-failure kill at verification.py:440. Kill while the leader is still unreaped, or skip the call when `os.killpg(pgid, 0)` shows no live group owned by this run | plugins/autopilot/scripts/verification.py:234 | 5 | ALICE, BLAKE |
| R3 | [1/5] | 🟠 | R1's failed-artifact obligation remains incomplete: `_empty_pinned` invalidates by pathname after closing the written descriptor. If the child renames the artifact and installs a replacement, close failure leaves complete reusable JSON at the renamed location because the identity check skips cleanup. Retain a descriptor through finalization and invalidate the written inode on failure; test rename plus close failure while preserving the replacement. | plugins/autopilot/scripts/verification.py:365 | 5 | BOB |
| R4 | [1/5] | 🟡 | The new `subprocess.run(..., timeout=60)` in `_is_inside_git_dir` can raise `TimeoutExpired`, which escapes `stage_review` and the CLI as a traceback, unlike the sibling `_git` calls. It also duplicates `_git` just to add an env. Fix: catch `subprocess.TimeoutExpired` and return True to fail closed, matching the docstring, or extend `_git` with optional `env` and `timeout` arguments and drop the duplicate call; add a test with a stubbed timeout | plugins/autopilot/scripts/review_stage.py:411 | 6 | ALICE |
| R5 | [1/5] | 🟡 | Three extra test files exist beyond the PRD's "complete implementation write paths" list, which says tests may use temporary fixtures only: tests/autopilot/test_helper_rework_sinks.py (672 lines), tests/autopilot/test_helper_rework_stage.py (202 lines) and tests/autopilot/test_helper_recovery_v2_sinks.py (491 lines). The listed test files are test_helper_recovery_v2.py and test_cap_recovery_helpers.py. The extra files are added scope. | tests/autopilot/test_helper_rework_sinks.py | general | BLAKE |
| R6 | [1/5] | 🟡 | `_is_inside_git_dir` calls `subprocess.run` with no handling for `FileNotFoundError` (git missing) or `TimeoutExpired` (60 s). A detection failure then ends as an uncontrolled traceback, because the facade's `_call` catches only TypeError and ValueError. It fails closed because nothing is written, but the PRD asks for a controlled invalid-input or unsafe-output refusal. | plugins/autopilot/scripts/review_stage.py:411 | 1 | BLAKE |
| R7 | [1/5] | 🟡 | The 19 known AP18 controller failures leave the full gate red. This is the PRD's explicit deferral, but it must stay in the completion disposition and block any push. | N/A | general | BLAKE |
| R8 | [1/5] | 🟡 | `_acquire_sink` closes `parent_fd` without guarding cleanup errors. A close OSError replaces the acquisition failure; during cancellation it can replace the cancellation with a controlled `sink-failed` result. Use guarded cleanup preserving the original exception, and explicitly close the returned sink if its post-open validation fails. | plugins/autopilot/scripts/verification.py:337 | 5 | BOB |
| R9 | [1/5] | 🟡 | The new Git timeout raises uncaught `subprocess.TimeoutExpired`, violating staging's controlled-refusal contract. Catch timeout at this probe and fail closed through the existing refusal path; add a timeout-injection test asserting no artifacts are written. | plugins/autopilot/scripts/review_stage.py:411 | 6 | BOB |
| R10 | [1/5] | 🟡 | R15 is only partly resolved: reader readiness is synchronized, but `stop.set()` can end `drain_fifo` before buffered bytes are consumed. Joining then checking empty chunks can miss bytes actually written. Drain remaining bytes nonblockingly after the stop signal, before closing the reader and asserting zero output. | tests/autopilot/test_helper_recovery_v2.py:700 | 7 | BOB |
| R11 | [1/5] | 🟡 | The new nested-pointer test asserts refusal classification but never observes content reads. An implementation that reads the nested `.git` and then returns OUTSIDE still passes. Reuse the existing open-audit fixture to assert no nested-pointer content opens, retaining the genuine worktree-pointer control. | tests/autopilot/test_helper_rework_sinks.py:344 | 5 | BOB |
| R12 | [1/5] | 🟡 | `_is_inside_git_dir` passes `timeout=60` and does not catch `subprocess.TimeoutExpired`; `stage_review` would raise a traceback instead of returning the contracted refusal dict (pre-write, so nothing is staged, but not "controlled"); it is the only timed probe in the module while the other `_git` calls can hang forever | plugins/autopilot/scripts/review_stage.py:411 | 6 | EVE |
| R13 | [1/5] | 🟡 | [MECH] 50 nodes in the new sink module pass against the pre-change code; the R-C1 docstring declares the same-spelling crosses as controls and R-B1 (second test), R-B3 (existing params) are preservation controls, but the per-function coverage is not visible from the summary | tests/autopilot/test_helper_rework_sinks.py | 5 | EVE, mech-check |
| R14 | [1/5] | ⚪ | `_run_against_sink` is now exactly 50 lines (154-203) after the `pgid` addition, at the limit. Moving the result dict into a small helper would restore headroom | plugins/autopilot/scripts/verification.py:154 | 5 | ALICE |
| R15 | [1/5] | ⚪ | The CHANGELOG now has two overlapping `--verify` bullets: the unchanged one at line 32 and the new one that restates keeping existing outputs and killing the child. Merge them. This is a minor redundancy | plugins/autopilot/CHANGELOG.md:33 | 8 | ALICE |
| R16 | [1/5] | ⚪ | Every non-"not a git repository" git failure is treated as "inside git internals". A legitimate external artifact directory inside a foreign-owned work tree (dubious ownership) is therefore refused. This is fail-closed and arguably intended, but it narrows "preserve legitimate external artifact directories". | plugins/autopilot/scripts/review_stage.py:423 | 1 | BLAKE |
| R17 | [1/5] | ⚪ | `_descend` runs `mkdir` while `_acquire_sink` acquires the artifact sink, before the log sink is proven openable. If the log sink then refuses, newly created parent directories remain on disk. The created leaf is unlinked, but the directories are not. This is a minor gap against "no unauthorized file changes". | plugins/autopilot/scripts/log_sink_refusal.py:213 | 2 | BLAKE |
| R18 | [1/5] | ⚪ | The attempt-200000 test measures peak allocation with tracemalloc in a child process and asserts `attempt_sequence_invalid`. The test itself does not show it fails on a `[0] * attempt` regression, so "demonstrably sensitive" rests on reasoning only. 200000 × 8 bytes is about 1.6 MB, over the 1,000,000-byte ceiling. | tests/autopilot/test_cap_recovery_helpers.py:193 | 3 | BLAKE |
| R19 | [1/5] | ⚪ | I could not confirm the receipt contents, the recovery report and the exact-command records. `source-map.json` pins the helper `tested_package_revision` at 0ed4c17, with no package diff since. | tools/autopilot/source-map.json:165 | 4 | BLAKE |
| R20 | [1/5] | ⚪ | The refreshed receipt omits task 5's available served-model provenance. Its recovery report records native `claude-sonnet-5-5/medium` workers and `claude-sonnet-5-5/high` Pat, but `rework_lane` covers only tasks 6-8. Add task 5's evidenced provenance without inferring unrecorded continuation metadata. | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:57 | 8 | BOB |
| R21 | [1/5] | ⚪ | CHANGELOG bullet "`--verify` leaves no log behind after a failed spawn" reads as deleting a pre-existing log and contradicts bullet 32 ("keeps an existing log ... byte-identical when the spawn fails") and README:303-305 | plugins/autopilot/CHANGELOG.md:34 | 8 | EVE |
| R22 | [1/5] | ⚪ | The recorded T3 sensitivity evidence cannot be reproduced from the repository: the report records only the path of an untracked scratch probe, no digest and no source, and says the probe "replaces the committed framework-selftest" although a probe guards no regression; Eve reproduced its output (plain 95314, inject 1695370, prior peak 12000040) and its sha256 is `728e016e310ed3d9055ac2a404dce004ad12034b59ed2bc58009340e5e8207de` | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md:410 | 8 | EVE |
| R23 | [1/5] | ⚪ | Receipt `effort` values mix served (`high`), configured (`medium (agent frontmatter)`, `high (recorded in the loop session brief)`) and `not captured` under one key | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:57 | 8 | EVE |
| R24 | [1/5] | ⚪ | Cosmetic carry-overs from Pat task 5: `_Pin` is a 4-tuple read as `pin[0]`/`pin[3]`, `_unlink_pinned` and `_empty_pinned` repeat the lstat-and-identity prologue, and `_open_log_sink` branches on `if preserve:` twice | plugins/autopilot/scripts/verification.py:307 | 5 | EVE |
| R25 | [1/5] | ⚪ | `_open_log_sink`'s default replace mode has no production caller (only `tests/autopilot/test_local_paths.py`; production passes `preserve=True` at verification.py:329), and `_acquire_sink` opens every sink twice with two `_pinned_parent_fd` descents (its own O_EXCL/plain open, then the legacy opener's) to keep the legacy opener as the monkeypatch seam; R16's "covered by acquisition" is a relocation of the duplicate traversal, not its removal | plugins/autopilot/scripts/log_sink_refusal.py:221 | 5 | EVE |
| R26 | [1/5] | ⚪ | `cause()` still reads `report.get("reason") or report.get("detail")`; its one caller (`:132`) is a staging refusal and every staging refusal now uses `detail` after R5, so the `reason` branch is dead | tests/autopilot/test_helper_recovery_v2.py:62 | 6 | EVE |
| R27 | [1/5] | ⚪ | New-file slop: `__all__ = ["bare_guard", "project"]  # fixtures re-exported for pytest` misstates its purpose (pytest discovers fixtures as module attributes; the line only silences F401), and `project_git_internals(project, tmp_path)` carries an unused `tmp_path` to match the `make` signature | tests/autopilot/test_helper_rework_stage.py:25 | 6 | EVE |
| R28 | [1/5] | ⚪ | [MECH] `test_export_policy_refuses_a_drained_fifo_output_rather_than_writing_into_a_pipe` passes against the pre-change code | tests/autopilot/test_helper_recovery_v2.py:732 | 7 | EVE, mech-check |
| R29 | [1/5] | ⚪ | [MECH] 6 nodes in the new staging module pass against the pre-change code (German-locale refusals of git-internals/live-state/symlink-escape, the non-empty union, the different-PRD-id acceptance) | tests/autopilot/test_helper_rework_stage.py | 6 | EVE, mech-check |
| R30 | [1/5] | 🟡 | [MECH] Fail-first replay: `test_attempt_validation_does_not_allocate_from_the_supplied_attempt` passes against the pre-change code at `2998ffbdfa57`, so it pins no behavior this change introduced. Absorbed from the computed replay block (no reviewer re-raised it; the cycle-1 ledger already settled the same row). | tests/autopilot/test_cap_recovery_helpers.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ `_drain` shares one `except OSError` clause for sink writes and pipe reads. An `os.read` error is reported as `sink-write-failed`, which is a misleading label, though the child is still killed and reaped. | File: plugins/autopilot/scripts/verification.py:121 — Duplicate of R18; both paths already return controlled failure and run process cleanup. A distinct cosmetic label is not required by a caller contract.

## Alice

Consensus lens, implementation-aware, incremental. Five findings: R1 (🟠), R4 (🟡), R2, R14 and R15 (⚪). She walked every cycle-1 finding against the code and reports R1-R9, R13, R15, R17, R20-R24 as resolved, R16 as partly resolved (the duplicate descent moved rather than vanished, caught by the identity compare so not a correctness issue), and R17's alias matrix as resolved with a gap. She reproduced the parent-alias defect in scratch: with the root spelled through a symlink alias `run_verification` returns `ok: True` and writes the log through two symlinks; with the repo spelled directly it refuses but with the wrong slug (`sink-failed`, not `unsafe-artifact-path`). She saw no outside-root or tracked-file overwrite, and states the broader bypass hypothesis stays UNVERIFIED.

She verified the task-6 `TimeoutExpired` observation: it is the only call in `review_stage.py` that can raise it, `stage_review` has no handler, and the CLI's `_call` catches only `TypeError`/`ValueError`. It fails closed by crashing — no silent grant — so she classified it Medium, not a safety hole.

```
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
```

## Blake

Blind lens, PRD-only. Nine findings, none above Medium: R5, R6, R7 (🟡); R16, R17, R2's second call site, the auto-dismissed `_drain` label, R18 and R19 (⚪). He states his own limits: he did not open the reports directory, so he could not inspect the receipt JSON or recovery report, and confirmed only that `update_helper_map.py --check` passes and that `git diff 0ed4c17 HEAD -- plugins tests` is empty against the source map's pinned `tested_package_revision`. He did not re-run the full suite and reads the 19 AP18 failures as the known spec-deferred obligation that still leaves the original full-suite-green criterion unmet.

Verified as present and correct: `_missing_prd_grant` refusing Blake/Eve without a `prd:` ref; the union-based shared context with an empty union yielding no content; per-job context files only outside the union; `LC_ALL=C` git detection with no `safe.bareRepository` override, failing closed on anything but git's own "not a git repository"; containment before any pointer read in `refuse()`; only the supplied repo's own `.git` pointer read, with relative gitdir targets resolved against the pointer's parent; both sinks acquired and proven before `Popen`; existing bytes preserved on a failed spawn because truncation follows a successful spawn; later sink errors returning controlled failures and killing and reaping the process group; the policy output opening non-blocking, checking the opened inode before `ftruncate`, refusing FIFOs with or without a reader and refusing a missing `O_NOFOLLOW` before any effect; README documenting the plan-and-prd conjunction. His narrow run of `test_helper_recovery_v2.py` + `test_cap_recovery_helpers.py` gave 48 passed.

```
B1: pass
B2: pass
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
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass
```

## Bob

Doubt rubric (D1-D5) plus de-slop, on codex `gpt-6-astra` at reasoning high, static-only, resuming his cycle-1 thread. Seven FIX items (R1's `_pinned_parent_fd` fallback, R3, R8, R9, R10, R11, R20), an empty VERIFY bucket and an empty KNOWN bucket. He explicitly records that the full-runtime overwrite consequence of R1 remains unverified.

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

Copilot backend with explicit `gemini-3.8-flash`, frontend & design specialist, generalist here (this diff has no UI surface). One finding: the `_pinned_parent_fd` mixed-spelling resolve, folded into R1 at 🟡. He read all three production diffs, both new test modules, the parent-alias audit and the task-5 alias-defect probe, checked function and file sizes with `ast`, swept for debug markers, TODOs, `skip` and `xfail`, and ran the five touched test files himself. All twelve of his rule verdicts pass.

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
```

## Eve

Doubt rubric plus de-slop, Claude Fable 5. Twelve residual findings: FIX 6, VERIFY 1, KNOWN 5. She walked every cycle-1 finding and reports R1-R9, R13, R15, R17, R20-R24 resolved, and **R16 not actually eliminated** — the duplicate descent relocated from `_pin_sink_leaf` into `_acquire_sink` + `_open_log_sink(preserve=True)`, two `_pinned_parent_fd` walks and two opens per sink — carried as KNOWN because the cycle-1 ruling mandates preserving both `SafeSinkOpenerTest` nodes and collapsing the open would move the monkeypatch seam three tests depend on.

Measured during her review (not a suite rerun): she re-ran the recorded parent-alias probe against HEAD bytes after confirming the probe's recorded digests equal `shasum -a 256` of HEAD (`60e7303f…` for `log_sink_refusal.py`, `f444b356…` for `dirty_tree.py`) — the `mixed_symlink` row opened the symlink's target directory and wrote `HELPER_WRITE` over the internal sentinel, the `same_symlink` row refused with ENOTDIR. She reproduced the T3 allocation probe exactly (plain 95314, inject 1695370, prior peak 12000040, Python 3.12.16) and recorded its sha256. `update_helper_map.py --check` exit 0. `git diff --name-only 0ed4c17..HEAD -- plugins tests tools` touches only `tools/autopilot/source-map.json`.

Her adjudication of the parent-alias item: **confirmed at HEAD by execution**, not only by source inspection, but reachable from `run_verification` only after `refuse` has judged the path — a component swapped to a symlink between preflight and open under mixed spelling. Before this rework a mixed spelling was refused outright, so she classes the race window as rework-introduced in exactly the primitive the pinned descent exists to make race-free. The static preflight itself refuses every spelling (0 wrong of 96 in the coordinator's probe).

Her one VERIFY item — group the 50 base-passing sink-module nodes by test function and require a preservation-control docstring on each all-passing function — was **not queued: command shape**. It describes a grouping-and-compare over existing replay output, not a single runnable project verification command, so `00013-autopilot-session-helpers-v2-checks-2.json` was not written. Rubric rule D3 already fails a vague VERIFY, and this one is specific but not a command.

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```

Verdict: 30 findings
Tests: 1091 passed, 19 failed, 0 skipped (gate run this cycle inside review-stage, exit 1, treated as failed; counts read verbatim from docs/dev/tmp/gate-00013v2-c2.log:465 because the verify reader returned "counts unavailable" for this `-q` summary — last-verification.json was not written, and the suite was not re-run a second time to manufacture a parseable line; all 19 failures are the AP00018 controller nodes, a recorded external deferral)
