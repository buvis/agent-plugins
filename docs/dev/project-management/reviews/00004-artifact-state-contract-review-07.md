---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 7
date: 2026-10-13
head_sha: 1991d18ab21462cbefdaa24720bda250c985c937
codex_thread_id: 01a136b5-53e1-73a0-a86a-9c2572547341
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `14afdffa8da363a9c4622ab0678da39e4d819e1e..1991d18ab21462cbefdaa24720bda250c985c937`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 7. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-6 rework incrementally (`14afdff..1991d18`: the fix commit `ed8ae19`, the re-approvals `1991d18`, and the cycle-6 minutes `7fbec6c`, `310e1c3`). The target is spec 00004's `requirements.md`, with `design.md` as the design doc. All ten tasks are complete. Findings are reported here, not written as tasks.

Alice checked each cycle-6 fix in the code and found all twelve resolved, with no regression. Two of those fixes are thinner than they look (Bob): the F10 guard still emits an approval record for any file named `design.md`, `requirements.md` or `tasks.md`, wherever it lives, and the F12 test counts `fsync` calls without checking what they flush. Blake raised three small points, one new (`derive_phase` ignores the state's `specType`).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input, as in cycles 2 to 6. The refusal is kept at `docs/dev/tmp/bob-output-00004c7-first.txt`. The retry inlined the context and the diff (209 KB) and ran without `--resume-thread`. The `codex_thread_id` above is the retry's thread.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "Authentication failed", on the first run and on the one retry. One-off runtime failure (exit 1, not 4); standalone, nothing latched. Same cause as cycles 2 to 6.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 6.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 293 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay: the pytest replay flagged 3 touched tests as passing against base. The lead re-ran them under unittest in a worktree at `14afdff` with the HEAD test files copied in. `test_usage_errors_are_3` (1 subtest failure, the F10 row) and `test_partial_upstream_binding_never_revives_after_upstream_reapproval` (2 subtest failures, both orders) fail there: the `subTest` artifact. `test_implementation_validation_warns_that_a_stale_design_is_not_checked` really passes at base, as the cycle-6 outcome stated (it covers behavior that shipped in cycle 5).
- Settled-decisions ledger: Blake re-raised both cycle-1 F23 deferrals (placeholder and bugfix checks). The script dismissed only the bugfix one and kept the placeholder one in the table; the lead moved it to Auto-dismissed by hand (it is the ledger's placeholder entry word for word). The script again printed the placeholder entry's reason for the bugfix line; corrected below.
- Consolidation corrections (by hand):
  - The script does not parse Bob's `- [BOB] ...` bucket lines; a copy with the bullet stripped (`bob-output-00004c7-lines.txt`) was fed to it.
  - The placeholder re-raise was moved out of the table; the two mechanical replay rows (F3, F4) were added. Refs were renumbered from the script's `R1`..`R6`.
- Lead's checks:
  - F1 confirmed by running it: `validate_spec.py hash <scratch>/docs/design.md --json` on a folder with no spec files printed an approval record (`sha256`, `approvedAt`, `approvedCommit`, `workflowVersion`), exit 0. `run_hash` (`validate_spec.py:148`) builds the canonical paths from the file's own parent, so any `design.md` matches.
  - F2 confirmed by reading `test_concurrency.py:74`: it asserts only `fsync.call_count`.
  - F5 confirmed by reading `state.py:346`: `spec_type(spec_dir, None)`. Impact not reproduced.
  - F6: Blake raised the same point in cycle 6 as the second half of F10; that decision covered only `hash --json`, so this half is still open.
  - F7: an approved design choice (`design.md:234-237`, review 00004-03 F14); the status schema requires both fields.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/3] | 🟡 | The cycle-6 F10 guard still emits an approval record for any file named `design.md`, `requirements.md` or `tasks.md`: it builds the canonical paths from the file's own parent without checking that the parent is a spec folder. Check that the folder is a spec folder (under the configured specs folder, or carrying spec markers) before emitting the record; add a regression with an unrelated `docs/design.md` (confirmed by running it) | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:148 | T-026 | BOB |
| F2 | [1/3] | 🟡 | The cycle-6 F12 test counts `fsync` calls but not their targets or order; it would pass with two folder flushes and no file flush. Assert the temporary file is flushed before `os.replace` and the folder after it (confirmed by reading) | tests/specflow/contract/test_concurrency.py:74 | T-025 | BOB |
| F3 | [1/3] | 🟡 | Replay: `test_implementation_validation_warns_that_a_stale_design_is_not_checked` (the cycle-6 F3 test) passes against the pre-change code under unittest too. It covers behavior that shipped in cycle 5, as the cycle-6 outcome stated. Recommend dismissing | tests/specflow/contract/test_status.py:281 | T-026 | mech-check |
| F4 | [1/3] | 🟡 | Replay flagged `test_usage_errors_are_3` and `test_partial_upstream_binding_never_revives_after_upstream_reapproval` as passing against base. The lead's unittest replay at `14afdff` shows 3 subtest failures: the `subTest` artifact again. Recommend dismissing | tests/specflow/contract/test_invalidation.py:155 | T-023 | mech-check |
| F5 | [1/3] | ⚪ | `derive_phase` calls `spec_type(spec_dir, None)` and ignores the state's `specType`, while `artifact_paths` passes the state. A bugfix recorded only in `.specflow.json` could derive its phase under a different type than its artifact paths | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:346 | T-026 | BLAKE |
| F6 | [1/3] | ⚪ | `validate` and `code-baseline` accept a spec folder outside the repository (`folder()` without the repo bound); `status` and `reconcile` bound it. Both only read. (The open half of cycle-6 F10) | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:115 | T-026 | BLAKE |
| F7 | [1/3] | ⚪ | The status JSON adds top-level `problems` and `intake`, which STATE-003.1 does not list. Approved design choice (`design.md:234-237`, review 00004-03 F14). Recommend dismissing | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:224 | T-026 | BLAKE |

Overlap: F1 and F2 both say a cycle-6 fix is thinner than its minutes. F3 and F4 are replay noise.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json`, plus one by hand:

- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage checks missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006; re-raised and dismissed in cycles 2 to 6. (The script printed the placeholder entry's reason for this line; the ledger's own entry names 00006.)
- [BLAKE] 🟠 VAL-001.8 / ART-001.10 / VAL-001.3 placeholder and unfilled design template checks missing (`checks.py:69`): settled as cycle-1 F23, deferred by design to 00005 T-071; re-raised and dismissed in cycles 2 to 6. The script did not match it this cycle (Blake cited `checks.py:69` with a parenthetical); moved here by the lead.

## Alice

Implementation-aware review of the cycle-6 rework (legacy consensus engine). She verified all twelve cycle-6 fixes in the code (F1 to F5, F8 to F12; F6 and F7 stay dismissed) and ran the contract suite (293 OK). No findings.

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

Blind lens (spec only). He read the helper source, ran the contract tests (293 OK) and `scripts/validate.py`, and probed placeholder detection on a copy of the sample spec. He judged canonical hashing, approval binding, stale propagation, the state schema, reconcile, config path refusal, numbering, dependency resolution, the drift baseline and the status schema as conforming. Findings: F5, F6, F7, plus the two F23 re-raises (auto-dismissed above).

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
B16: pass
B17: fail
B18: pass
B19: pass

## Bob

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input. The retry wrote FIX/VERIFY/KNOWN buckets. FIX: F1, F2. VERIFY and KNOWN: none.

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
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

Verdict: 7 findings

Tests: 357 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-13)

- F1: `hash --json` refuses (exit 3) a file whose folder is not directly under the configured specs folder (`load_config` root). Regression with an unrelated `docs/design.md`. Queued.
- F2: the durability test records each `fsync` beside `os.replace` and asserts the temporary file is flushed before the replace and the folder after it on POSIX. Queued.
- F3: dismissed. Passes at base by design (ledger entry added).
- F4: dismissed. The `subTest` replay artifact; the unittest replay at `14afdff` fails both (ledger entry added). From cycle 8 the replay runs `uv run --no-project --with pytest --with pytest-subtests python -m pytest`, so subtest failures count; the project memory recipe says so. Applied.
- F5: `derive_phase` takes the loaded state and calls `spec_type(spec_dir, state)`; test with a bugfix recorded only in `.specflow.json`. Queued.
- F6: `validate` and `code-baseline` call `folder(value, repo)`; test that a spec outside the repository exits 3. Queued.
- F7: accepted as an approved design choice (ledger entry added). Applied.
- Auto-dismissed F23 re-raises (placeholder and bugfix checks): settled earlier, no action.

### Outcome (2026-10-13)

Every queued item is applied:

- F1: `hash --json` raises the usage error unless the file's folder sits directly in the configured specs folder (`load_config` `specsDir`, resolved). Test: an unrelated `docs/design.md` and a spec copied outside the specs folder both exit 3 with no output; the plain form still hashes them.
- F2: the durability test records each `fsync` (file or folder, from `fstat`) beside `os.replace` and asserts `file`, `replace`, `folder` on POSIX.
- F5: `derive_phase` takes the state and calls `spec_type(spec_dir, state)`; every caller passes it (`None` in recovery). Test: a bugfix that only `.specflow.json` records, with only the checkpoint open, is in `verification` through `spec_phase`.
- F6: `validate` and `code-baseline` call `folder(value, repo)`. The outside-repository test now covers all four commands.
- Fail-first: the F1, F5 and F6 tests fail against the old code (5 failures). The F2 test passes there, since the code was right; with the file flush removed it fails (`['replace', 'folder']`).
- Design text changed (F1, F5, F6), so design and tasks need the developer's re-approval (qa-log, "Review 00004-07 design edits").
