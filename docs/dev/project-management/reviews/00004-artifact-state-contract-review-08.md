---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 8
date: 2026-10-13
head_sha: 4083e1b4ded8827f56dd2d83fd01a43c939dbbe6
codex_thread_id: 01a13709-dd0f-77f0-9342-02546a27c02a
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `1991d18ab21462cbefdaa24720bda250c985c937..4083e1b4ded8827f56dd2d83fd01a43c939dbbe6`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 8. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-7 rework incrementally (`1991d18..4083e1b`: the fix commit `5d5ca92`, the re-approvals `4083e1b`, and the cycle-7 minutes `7bbde7a`, `4378bf4`). The target is spec 00004's `requirements.md`, with `design.md` as the design doc. All ten tasks are complete. Findings are reported here, not written as tasks.

Alice and Bob both checked the cycle-7 fixes (F1, F2, F5, F6) in the code and found them resolved, with no regression. No finding is above ⚪. Alice wants one more test row (a non-default specs folder for `hash --json`). Blake raised four small points against code that predates this rework; the three replay rows are noise (subtest artifact twice, a by-design pass once).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input (`sandbox-exec: sandbox_apply: Operation not permitted`), as in cycles 2 to 7. The refusal is kept at `docs/dev/tmp/bob-output-00004c8-first.txt`. The retry inlined the context and the diff (189 KB) and ran without `--resume-thread`. The `codex_thread_id` above is the retry's thread.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "Authentication failed", on the first run and on the one retry. One-off runtime failure (exit 1, not 4); standalone, nothing latched. Same cause as cycles 2 to 7.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 7.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 295 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay: this cycle used the cycle-7 decision, `uv run --no-project --with pytest --with pytest-subtests python -m pytest`. It still flagged 4 touched tests as passing against base. The lead re-ran them under unittest in a worktree at `1991d18` with the HEAD test files copied in: `test_hash_json_refuses_an_artifact_name_outside_the_specs_folder` (2 subtest failures), `test_spec_commands_refuse_a_spec_outside_the_repository` (2 subtest failures) and `test_stale_upstream_closes_the_implementation_gate` (2 subtest errors, the old `derive_phase` signature) fail there. So `pytest-subtests` did not fix the `subTest` artifact. `test_write_flushes_the_file_before_the_rename_and_the_folder_after` really passes at base, as the cycle-7 outcome stated (the code was right; the test fails with the file flush removed).
- Settled-decisions ledger: the script dismissed Blake's three placeholder/bugfix re-raises (cycle-1 F23). It printed the placeholder entry's reason for the bugfix line again; corrected below.
- Consolidation corrections (by hand): the three mechanical replay rows (F6 to F8) were added. Refs were renumbered from the script's `R1`..`R5`.
- Lead's checks:
  - F3 confirmed by reading `numbers.py:38-42`: `spec_folders` keeps only `NUMBER` (`^[0-9]{5}-`) matches, and `next_number` feeds only those names to `TAKEN`. A bare `00123` folder in the specs folder is not counted. Same class as cycle-6 F11, which fixed intake only.
  - F4 confirmed by reading `status.py:90-93`: `accepted` is built from `acceptedMarkers` with no look at the record's `status`.
  - F2 partly confirmed: `checks.py:143-151` runs `git check-ignore` and raises `GitError` on failure. That it aborts `status` with exit 2 is Blake's claim, not reproduced.
  - F5: the `problems` and `intake` half is the ledger's accepted entry (review 00004-03 F14); the `--dry-run` and config `schemaVersion` half is new.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/3] | ⚪ | `run_hash` now resolves the specs folder from `load_config(repo)["specsDir"]`, but no `hash --json` test sets a non-default `specsDir`. Add one row that configures another specs folder and expects an approval record for a spec inside it | tests/specflow/contract/test_cli.py:224 | T-026 | ALICE |
| F2 | [1/3] | ⚪ | STATE-003.3 says status is computed from repository files alone, but `status()` always runs the `specs-folder` check, which shells out to `git check-ignore`; a git failure raises `GitError` (exit 2 per Blake), and the result depends on git's ignore setup | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:224 | T-026 | BLAKE |
| F3 | [1/3] | ⚪ | `next-number` misses a bare five-digit folder (`00123`) in the specs folder: `spec_folders` filters with `NUMBER` before `TAKEN` sees the names. A small hole in "never reuse a number" (ART-001.3) (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:40 | T-029 | BLAKE |
| F4 | [1/3] | ⚪ | `marker_blockers` honors `acceptedMarkers` from the dependent record whatever its status; WF-002.7 says acceptance lapses with the approval. The closed artifact gate masks it today (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:90 | T-026 | BLAKE |
| F5 | [1/3] | ⚪ | Additions beyond the spec: top-level `intake` and `problems` in the status output (already accepted, ledger), plus a `--dry-run` flag on `reconcile` and a config `schemaVersion` field (new). All harmless and read-only | plugins/specflow/skills/spec-workflow/schemas/specflow-status.schema.json:7 | general | BLAKE |
| F6 | [1/3] | 🟡 | Replay flagged `test_hash_json_refuses_an_artifact_name_outside_the_specs_folder` and `test_spec_commands_refuse_a_spec_outside_the_repository` as passing against base. The lead's unittest replay at `1991d18` shows 4 subtest failures: the `subTest` artifact, even with `pytest-subtests`. Recommend dismissing | tests/specflow/contract/test_cli.py:224 | T-026 | mech-check |
| F7 | [1/3] | 🟡 | Replay flagged `test_stale_upstream_closes_the_implementation_gate` as passing against base. The unittest replay at `1991d18` shows 2 subtest errors (old `derive_phase` signature): the `subTest` artifact. Recommend dismissing | tests/specflow/contract/test_invalidation.py:197 | T-023 | mech-check |
| F8 | [1/3] | 🟡 | Replay: `test_write_flushes_the_file_before_the_rename_and_the_folder_after` (the cycle-7 F2 test) passes against base under unittest too. The code was already right; the cycle-7 outcome showed it fails with the file flush removed. Recommend dismissing | tests/specflow/contract/test_concurrency.py:74 | T-025 | mech-check |

Overlap: F6 and F7 are the same replay artifact. F2 to F5 concern code this rework did not touch.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json`:

- [BLAKE] 🟠 VAL-001.8 / ART-001.10 placeholder checks missing (`checks.py:69`): settled as cycle-1 F23, deferred by design to 00005 T-071; re-raised and dismissed in cycles 2 to 7.
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage checks missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006; re-raised and dismissed in cycles 2 to 7. (The script printed the placeholder entry's reason for this line; the ledger's own entry names 00006.)
- [BLAKE] 🟡 VAL-001.3 design placeholders not checked (`checks.py:385`): part of the same placeholder deferral (the ledger entry names VAL-001.3), deferred to 00005 T-071.

## Alice

Implementation-aware review of the cycle-7 rework (legacy consensus engine). She verified F1, F2, F5 and F6 in the code (F3, F4 and F7 stay dismissed or accepted) and ran the contract suite (295 OK). The design text and CHANGELOG match the code. Finding: F1.

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

Blind lens (spec only). He read the helper source, ran the contract tests (295 OK), and probed placeholder and bugfix-task validation on copies of the sample spec. He judged canonical hashing, stale propagation, reconcile, spec dependencies, the drift baseline, path refusal, number clashes, cross-spec references and the schemas as conforming. Findings: F2 to F5, plus the three F23 re-raises (auto-dismissed above).

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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input. The retry found no issues; FIX, VERIFY and KNOWN are all empty.

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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 8 findings

Tests: 359 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-13)

- F1: add a `hash --json` test with a non-default `specsDir`. Applied.
- F2: deferred (ledger entry added): it needs a design call (a soft check or a reworded STATE-003.3).
- F3: deferred (ledger entry added): a small hole, and fixing it would reopen design approval.
- F4: deferred (ledger entry added): the closed artifact gate masks it today.
- F5: accepted (ledger entry added): `--dry-run` and `schemaVersion` are read-only helper surface.
- F6, F7: dismissed (ledger entries added): the `subTest` replay artifact. The unittest replay at `1991d18` fails all three tests.
- F8: dismissed (ledger entry added): passes at base by design.
- Auto-dismissed F23 re-raises (placeholder and bugfix checks): settled earlier, no action.

### Outcome (2026-10-13)

- F1: `test_hash_json_follows_the_configured_specs_folder` sets `specsDir` to `docs/specs`. It checks that a spec there gets an approval record and that the default-folder spec is refused (exit 3). Mutation check: with `load_config` pinned to `.kiro/specs`, the test fails (`3 != 0`). Test only, with no design or tasks edits, so no re-approval is needed.
- Gate after the fix: `scripts` 12 OK, release 52 OK, contract 296 OK; `validate.py` and `verify_release.py` exit 0.
