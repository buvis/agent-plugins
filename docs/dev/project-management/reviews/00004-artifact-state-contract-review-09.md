---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 9
date: 2026-10-13
head_sha: b9f37de5f9d2085c55e491fca4e0b3ff67e3ab5d
codex_thread_id: 01a13712-0ec1-74f3-948d-934c0616d91a
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `4083e1b4ded8827f56dd2d83fd01a43c939dbbe6..b9f37de5f9d2085c55e491fca4e0b3ff67e3ab5d`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 9. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-8 rework incrementally (`4083e1b..b9f37de`): the test commit `b9f37de` and the cycle-8 minutes `0fc72de`, `4d763ad`. The target is spec 00004's `requirements.md`, with `design.md` as the design doc. All ten tasks are complete. Findings are reported here, not written as tasks.

Alice, Bob and Carl found nothing: the cycle-8 F1 test is in place and binds to `run_hash`'s use of `load_config`. Blake's blind pass raised three points the ledger does not cover, all against code this rework did not touch. One is 🟡 (an unreadable state file aborts `status` for every spec); two are ⚪. The one replay row is by design.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input (it asked for the context and diff to be pasted), as in cycles 2 to 8. The refusal is kept at `docs/dev/tmp/bob-output-00004c9-first.txt`. The retry inlined the context and the diff (162 KB) and ran without `--resume-thread`. The `codex_thread_id` above is the retry's thread.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run). The "Authentication failed" error of cycles 2 to 8 did not recur.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 8.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 296 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay (`python3 -m pytest`) flagged `test_hash_json_follows_the_configured_specs_folder` as passing against base. The lead re-ran it under unittest in a worktree at `4083e1b` with the HEAD test files copied in: it passes there too. That is by design (F4).
- Settled-decisions ledger: the script dismissed four Blake re-raises (placeholder and bugfix checks, `next-number` bare folder, CLI surface). It printed the placeholder entry's reason for the bugfix line again, as in cycle 8; the ledger's own entry names 00006.
- Consolidation corrections (by hand): the mechanical replay row (F4) was added. Refs were renumbered from the script's `R1`..`R3`.
- Lead's checks:
  - F1 confirmed by reading: `load_state` (`state.py:66-69`) catches only `UnicodeDecodeError` and `json.JSONDecodeError`, so `read_bytes()` on a directory or an unreadable file raises `OSError`. `spec_status` (`status.py:161-165`) catches only `StateError`, so the error reaches `main` (`validate_spec.py:253-255`), which prints `state error: cannot read: ...` and exits 2 for the whole run. A malformed (but readable) file is reported per spec as `invalid`; an unreadable one is not.
  - F2: the ledger already accepts `cross-spec-review.md` as a scope extra (cycle 1); the intake `SPEC.md` spike template is the new half.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/4] | 🟡 | An unreadable `.specflow.json` (a directory, or permission denied) escapes `load_state` as a raw `OSError`. `validate` and `status` (one spec or all) exit 2 with no finding and no JSON, so one bad spec hides every other spec from an external runner (STATE-003.1; VAL-001.1/.6 want a finding naming file, rule and fix). A malformed but readable file is already reported per spec as `invalid` (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:66 | general | BLAKE |
| F2 | [1/4] | ⚪ | Templates beyond this spec: `templates/cross-spec-review.md` (already accepted, ledger) and the intake `SPEC.md` spike template (new). They look like 00006/00007 material | plugins/specflow/skills/spec-workflow/templates/cross-spec-review.md:1 | general | BLAKE |
| F3 | [1/4] | ⚪ | `hash --json` returns the key `sha256`, while the state schema records `approvedSha256`; the recording agent must map the field. A contract seam for 00006 | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:159 | general | BLAKE |
| F4 | [1/4] | 🟡 | Replay: `test_hash_json_follows_the_configured_specs_folder` (the cycle-8 F1 test) passes against base, under pytest and under the lead's unittest replay at `4083e1b`. By design: the fix was test-only, and the cycle-8 outcome shows it fails with `load_config` pinned to `.kiro/specs`. Recommend dismissing | tests/specflow/contract/test_cli.py:236 | T-026 | mech-check |

Overlap: none. F1 to F3 concern code this rework did not touch.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json`:

- [BLAKE] 🟠 VAL-001.8 / ART-001.10 / VAL-001.3 placeholder detection not implemented (`checks.py:742`): settled as cycle-1 F23, deferred by design to 00005 T-071.
- [BLAKE] 🟠 VAL-001.4 bugfix tasks validation missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006. (The script printed the placeholder entry's reason for this line; the ledger's own entry names 00006.)
- [BLAKE] 🟡 `next-number` ignores a bare five-digit folder (`numbers.py:38`): deferred in the cycle-8 walkthrough (cycle-8 F3).
- [BLAKE] ⚪ CLI surface beyond `--json` (`validate_spec.py:204`): accepted as in-scope helper surface in the cycle-1 walkthrough.

## Alice

Implementation-aware review of the cycle-8 rework (legacy consensus engine). She verified F1 of cycle 8 in the code (`run_hash` reads `load_config(repo)["specsDir"]`, `validate_spec.py:151`) and ran `test_cli.py` (23 OK). She judged the replay pass as by design. No findings.

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

Blind lens (spec only). He read the helper source, ran the contract tests (296 OK), and probed an unreadable state file and a bare number folder in a scratch repo. He judged canonical hashing, invalidation, state and config handling, reconcile, spec dependencies, the drift baseline and status as conforming. Findings: F1 to F3, plus four re-raises (auto-dismissed above).

B1: fail
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

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0. He read the context and diff, ran the five CI steps, and found no issues.

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

Verdict: 4 findings

Tests: 360 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-13)

- F1: `load_state` turns a read `OSError` into `StateError`, with a regression test. Applied.
- F2: accepted (ledger entry added): read-only templates shipped early.
- F3: accepted (ledger entry added): the field mapping belongs to the 00006 recording agent.
- F4: dismissed (ledger entry added): passes at base by design.
- Auto-dismissed re-raises: settled earlier, no action.

### Outcome (2026-10-13)

- F1: `load_state` (`state.py`) catches `OSError` on the read and raises `StateError(path, "cannot read: <strerror>")`; the reason names no path. Every caller already handles `StateError`, so `status` marks that one spec `invalid` (exit 1, document still printed) and `validate` reports it as a state error, as for a malformed file. `deps.completeness` maps a `StateError` caused by an `OSError` back to `unreadable target: <strerror>`, which keeps the label `test_unreadable_target_reason_names_no_absolute_path` pins. Regression test `test_status_reports_an_unreadable_state_and_spares_the_other_specs` (`.specflow.json` as a folder, a second spec beside it): fails before the fix (`2 != 1`), passes after. CHANGELOG entry added. No design or tasks edit, so no re-approval: design.md's status rule names malformed or unsupported state, and an unreadable file now takes that same path. The design does not name the unreadable case word for word.
- Gate after the fix: `scripts` 12 OK, release 52 OK, contract 297 OK, `validate.py` exit 0; `verify_release.py` re-run after the commit.
