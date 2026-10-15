---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 6
date: 2026-10-12
head_sha: 14afdffa8da363a9c4622ab0678da39e4d819e1e
codex_thread_id: 01a131d5-502f-7eb0-a07f-37168d019715
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `8cee2d8744fe5a4644a8b6147b0e47418d22de47..14afdffa8da363a9c4622ab0678da39e4d819e1e`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 6. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-5 rework incrementally (`8cee2d8..14afdff`: the fix commit `24919c4`, the T-027 close-out `183380c` and `363778b`, the re-approvals, the cycle-5 minutes, and two commits that touch spec 00008 docs only). The target is spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. All ten tasks are now complete (T-027 closed on 2026-10-12). Findings are reported here, not written as tasks.

Every cycle-5 fix holds. Alice checked each against the code: F1, F2, F3, F4, F7, F8, F9 and F10 are resolved, and the T-027 and Kiro-link edits to requirements and design agree with the code. The new findings are smaller: the F4 fix still lets a record that binds only part of its upstream come back (Bob), the new `stale` list uses the wrong order for design-first specs (Alice), the new `gates` warning has no test (Alice), and the shipped artifact contract still says the Kiro link is unconfirmed, though T-027 confirmed it (Blake, restored from a wrong ledger dismissal).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input (`sandbox_apply: Operation not permitted`), as in cycles 2 to 5. The refusal is kept at `docs/dev/tmp/bob-output-00004c6-first.txt`. The retry inlined the context and the diff (244 KB) and ran without `--resume-thread`. The `codex_thread_id` above is the retry's thread.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "Authentication failed", on the first run and on the one retry. One-off runtime failure (exit 1, not 4); standalone, nothing latched. Same cause as cycles 2 to 5: the agent launcher blocks access to the GitHub config copilot reads its token from.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 5.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 287 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay: the pytest replay flagged 3 touched tests as passing against base. The lead re-ran them under unittest in a worktree at `8cee2d8` with the HEAD test files copied in. `test_folder_scans_run_in_the_requirements_phase_only` fails there (3 subtest failures): the `subTest` artifact again (F7). `test_structure_ids_take_ascii_digits_only` and `test_first_artifact_of_the_order_needs_no_binding` really pass at base, as the cycle-5 outcome predicted (F6).
- Settled-decisions ledger: it absorbed the two cycle-1 F23 re-raises (placeholder and bugfix checks) again. It also dismissed Blake's Kiro-link finding against the "T-027 trials pending" entry; that entry's reason (the trial is open) no longer holds now that T-027 is closed, so the finding is restored as F5. The script again printed the placeholder entry's reason for the bugfix line (00005 T-071, not 00006); corrected under Auto-dismissed below.
- Consolidation corrections (by hand):
  - The script does not parse Bob's `- [BOB] ...` bucket lines; a copy with the bullet stripped (`bob-output-00004c6-lines.txt`) was fed to it.
  - The restored F5 and the two mechanical replay rows (F6, F7) were added by hand. Refs were renumbered from the script's `R1`..`R9`.
- Lead's checks:
  - F1 confirmed by reading `state.py:202-232`: `unbound` flags only an empty `upstreamSha256`, and `rebound` skips (`continue`) every upstream that the map does not name. Design §7.4 (`design.md:663`) covers a record with no field, not a partial one.
  - F2 confirmed by reading `status.py:199`: the list walks `statuses`, which is keyed in the fixed artifact order.
  - F4: the code matches the approved design (`design.md:92,268`: `status [--json]`, "`validate_spec.py status --json` is the only interface an external runner needs"). Blake's point is that STATE-003.1 (`requirements.md:187`) says the helper "SHALL print ... a JSON status" with no flag.
  - F5 confirmed by reading `artifact-contract.md:16`: "whether Kiro follows such a link is not yet confirmed".
  - F9: the `intake` array is an approved design choice (`design.md:906`); the hold rule was not checked.
  - F11: the second half (an unfiltered `validate` runs both folder scans) is the cycle-5 F8 decision ("a run with no phase still runs both"); only the first half (`next_number` reading folders only) is new.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/3] | 🟡 | Cycle-5 F4 is incomplete for partial upstream bindings. `unbound` accepts any non-empty `upstreamSha256`, and `rebound` skips any upstream the map does not name. A `tasks` approval that binds only `design` comes back after requirements change and requirements and design are approved again with the design text unchanged. Require a binding for every existing upstream in the workflow order; add a regression for this sequence in both orders (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:202 | T-023 | BOB |
| F2 | [1/3] | 🟡 | The new `stale` list in the status JSON follows the fixed artifact order (requirements, design, tasks), not the workflow order that the design (`specs[].stale[]` row) and the cycle-5 F9 decision promise. A design-first spec with all three stale lists `["requirements","design","tasks"]`, not `["design","requirements","tasks"]`. Use `[n for n in (*ORDERS[order], "tasks") if statuses[n] == "stale"]` and add a design-first row to `test_stale_artifacts_are_listed_by_name` (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:199 | T-026 | ALICE |
| F3 | [1/3] | 🟡 | New behavior untested: since cycle-5 F7, `gates` also emits a warning-level `not-checked: the design approval is stale...` finding for a stale design, because it shares `drift_warnings` with `status`. The gates drift test (`test_status.py:254`) covers only the approved-and-drifted case. Add a case with a stale design that asserts the gates warning | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:633 | T-026 | ALICE |
| F4 | [1/3] | 🟡 | STATE-003.1 says the helper "SHALL print ... a JSON status", but `status` (and `validate`) print human text unless `--json` is passed. An external runner that omits the flag gets output it cannot parse. Code matches the approved design (`design.md:92,268`); the requirement carries no flag | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:88 | T-026 | BLAKE |
| F5 | [1/3] | 🟡 | The shipped `artifact-contract.md` still says "whether Kiro follows such a link is not yet confirmed" and that a spec in another specs folder "may not appear there". T-027 settled this on 2026-10-12 (requirements Risks and Unresolved questions, `kiro-captures.md`): Kiro lists, opens and watches specs through a `.kiro/specs` link. Update the line (restored from a stale ledger dismissal; confirmed by reading) | plugins/specflow/skills/spec-workflow/references/artifact-contract.md:16 | T-027 | BLAKE |
| F6 | [1/3] | 🟡 | Replay: `test_structure_ids_take_ascii_digits_only` (the cycle-5 F2 row, a coverage fix) and `test_first_artifact_of_the_order_needs_no_binding` (the F4 exemption pin) pass against the pre-change code under unittest too. Both pass at base by design, as the cycle-5 outcome stated. Recommend dismissing | tests/specflow/contract/test_invalidation.py:155 | T-023 | mech-check |
| F7 | [1/3] | 🟡 | Replay flagged `test_folder_scans_run_in_the_requirements_phase_only` (`test_config.py`) as passing against base. The lead's unittest replay at `8cee2d8` shows 3 subtest failures there: the `subTest` artifact again. Recommend dismissing | tests/specflow/contract/test_config.py:148 | T-028 | mech-check |
| F8 | [1/3] | ⚪ | The migration paragraph of design.md says the helper "reads them as they are" for the two hand-written calcard state files. After cycle-5 F4, the design record of the calcard-00032 fixture, which has no `upstreamSha256`, reads as stale until approved again. Say so, as §7.4 now does | docs/dev/project-management/specs/00004-artifact-state-contract/design.md:823 | general | ALICE |
| F9 | [1/3] | ⚪ | `status` returns `nextTask: null` when a hold is set, though STATE-003.1 yields null only for a closed implementation gate. The `intake` array goes beyond STATE-003.1 too, but it is an approved design choice (`design.md:906`) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:190 | T-026 | BLAKE |
| F10 | [1/3] | ⚪ | `hash --json` emits an approval-shaped record (`approvedAt`, `approvedCommit`, `workflowVersion`) for any file path, not only the three canonical artifacts, which sits poorly with ART-001.9 ("SHALL NOT hash or approve" files it does not own). `validate` and `code-baseline` also accept spec folders outside the repository, though they only read | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:137 | T-026 | BLAKE |
| F11 | [1/3] | ⚪ | `next_number` reads only subfolder names under `<root>/intake/` with an `NNNNN-` prefix; a bare `00123` folder or a file `00123-x.md` directly under intake is ignored, though the requirement says "highest five-digit prefix under `<root>/intake/`". (Blake's second point, that an unfiltered `validate` runs both folder scans, is the cycle-5 F8 decision.) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:53 | T-029 | BLAKE |
| F12 | [1/3] | ⚪ | `write_guarded` writes the temp file and calls `os.replace` with no `fsync`, so a crash can leave an empty or partial `.specflow.json`. (The check-then-replace gap is accepted by WF-006.4 and documented since cycle-5 F10.) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:31 | T-025 | BLAKE |

Overlap: F1 and F8 both follow from the cycle-5 F4 decision. F6 and F7 are replay noise.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json`:

- [BLAKE] 🟠 VAL-001.8 / VAL-001.3 placeholder and unfilled design template checks missing (`checks.py:183`): settled as cycle-1 F23, deferred by design to 00005 T-071; re-raised and dismissed in cycles 2 to 5.
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage checks missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006; re-raised and dismissed in cycles 2 to 5. (The script printed the placeholder entry's reason for this line; the ledger's own entry names 00006.)
- [BLAKE] 🟡 `artifact-contract.md` says the Kiro link is not yet confirmed (`artifact-contract.md:16`): a wrong dismissal, matched to the "T-027 trials pending" entry, whose reason stopped holding when T-027 closed. Restored as F5 above.

## Alice

Implementation-aware review of the cycle-5 rework (legacy consensus engine). She verified every cycle-5 fix in the code, the T-027 and Kiro-link text, and the 00008 design edit; she ran the contract suite (287 passed) and `scripts/validate.py` (clean). Findings: F2, F3, F8.

R1: fail
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

Blind lens (spec only). He found the helper himself, ran the contract tests (287 OK), `scripts/validate.py` and `validate_spec.py status --json` (schema-shaped). He judged canonical hashing, the invalidation cascade, recovery without a state file, the `Depends on:` grammar, cycle detection, config path refusal (SEC-002.5), the all-or-nothing drift baseline and the guarded reconcile write as conforming. Findings: F4, F5 (restored), F9, F10, F11, F12, plus the two F23 re-raises (auto-dismissed above).

B1: fail
B2: pass
B3: fail
B4: pass
B5: pass
B6: fail
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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input (the sandbox blocked file reads). The retry wrote FIX/VERIFY/KNOWN buckets. FIX: F1. VERIFY and KNOWN: none.

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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 12 findings

Tests: 351 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-13)

- F1: an approved record whose `upstreamSha256` lacks the hash of any existing upstream in the workflow order is unbound, through the same path and message as cycle-5 F4. Regression for the partial-binding sequence in both orders. Design §7.4 changes. Queued.
- F2: build `stale` in workflow order (`(*ORDERS[order], "tasks")`); add a design-first row to `test_stale_artifacts_are_listed_by_name`. Queued.
- F3: add one gates test with a stale design that asserts the warning-level `not-checked` finding. Queued.
- F4: reword STATE-003.1 so the helper prints the JSON status with `--json`, matching the design. Requirements, design and tasks need re-approval. Queued.
- F5: `artifact-contract.md:16` states the T-027 result (Kiro lists, opens and watches specs through a `.kiro/specs` link and ignores `.kiro/specflow/`). The ledger's "T-027 trials pending" entry (cycle-2 F16) is retired, so it stops dismissing. Ledger: applied. Doc: queued.
- F6: dismissed. Both tests pass at base by design (ledger entry added).
- F7: dismissed. The `subTest` replay artifact again; the unittest replay at `8cee2d8` fails it (ledger entry added).
- F8: one sentence in the design migration paragraph: an approved calcard record that binds no upstream reads as stale until approved again. Queued.
- F9: STATE-003.1 also yields `nextTask: null` when a hold is set (folds into the F4 requirement edit). Queued.
- F10: `hash --json` refuses (exit 3) a file that is not one of the three canonical artifacts of a spec folder; the plain and `--raw` forms stay open. Test. Queued.
- F11: `next_number` scans folders and files directly under `<root>/intake/`, with a five-digit prefix followed by `-` or the end of the name. Test. Queued.
- F12: `write_guarded` calls `os.fsync` on the temp file before `os.replace`, and on the directory after. Test that both flushes happen. Queued.
- Auto-dismissed F23 re-raises (placeholder and bugfix checks): settled earlier, no action.

### Outcome (2026-10-13)

Every queued item is applied:

- F1: `state.unbound` takes the spec folder and flags an approved record when any existing upstream artifact is missing from its `upstreamSha256`, so a partial binding is stale with itself as the cause. Test: a `tasks` record that drops its most upstream binding stays stale through the edit-and-re-approve sequence in both orders, and heals when approved again. Design §7.4 and its approval rule say so.
- F2: `stale` walks `(*ORDERS[order], "tasks")`. Test: a design-first spec lists `design`, `requirements`, `tasks`.
- F3: test that `validate --phase implementation` warns `not-checked` for a stale design in a Git repository.
- F4, F9: STATE-003.1 prints the JSON status with `--json`, and a hold yields `nextTask: null`.
- F5: `artifact-contract.md` states the T-027 result. Ledger entry retired in `310e1c3`.
- F8: the design migration paragraph says an approved calcard record that binds no upstream reads as stale until approved again.
- F10: `hash --json` exits 3 for a file that is not a canonical artifact of a spec folder; plain and `--raw` still hash it. Test with `.config.kiro`.
- F11: `next_number` reads every name straight under `<root>/intake/`, and `TAKEN` (`^[0-9]{5}(?:-|$)`) matches every name it scans; `NUMBER` keeps its meaning for clashes and `Sources:`. Test: a bare `00012` folder and a `00020-note.md` file count, `00030x` does not.
- F12: `write_guarded` fsyncs the temporary file before `os.replace`, and the folder after it on POSIX. Test that both flushes happen. The artifact contract and design say so.
- Fail-first: 5 of the 6 new tests fail against the old code (F1 in both orders, F2, F10, F11, F12). The F3 test passes there, since it covers behavior that shipped in cycle 5.
- Checks: contract 293 OK, release 52 OK, validator 12 OK, `scripts/validate.py` OK; `verify_release.py` after the commit (it refuses uncommitted package files). `ruff check` on the changed files: clean except three warnings that were already there (SIM102 in `spec_text.py`, SIM117 twice in `test_concurrency.py`); `ruff format` applied to `test_concurrency.py`.
- Requirements, design and tasks need the developer's re-approval (qa-log, "Review 00004-06 requirements and design edits").
