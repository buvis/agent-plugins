---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 10
date: 2026-10-14
head_sha: 7897f61dd8afd956da8cb4d5496dd140930d75ee
codex_thread_id: 01a13b2f-46ff-7c50-a1c4-695531d70dc8
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `b9f37de5f9d2085c55e491fca4e0b3ff67e3ab5d..7897f61dd8afd956da8cb4d5496dd140930d75ee`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 10. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-9 rework incrementally (`b9f37de..7897f61`): the fix commit `7897f61` (`state.py`, `deps.py`, `test_cli.py`, CHANGELOG, ledger) and the cycle-9 record `1517be6`. The target is spec 00004's `requirements.md`, with `design.md` as the design doc. All ten tasks are complete. Findings are reported here, not written as tasks.

Cycle-9 F1 is resolved for the case it named: a `.specflow.json` that is a folder or that `read_bytes()` cannot read. Alice confirmed it in a scratch repo, and Carl found nothing. Two siblings of the same class remain, so one bad spec can still abort `status` for every spec with exit 2:

- F1 (Bob): `path.exists()` sits outside the new handler. Confirmed on Python 3.10.
- F2 (Blake): `own_status` lets an `OSError` out of `sha256_canonical`. Confirmed by reading.

Alice's 🟡 (F3, an untested `deps` branch) is refuted by a mutation run. Blake's two other 🟡s (F4, F5) are confirmed by reading, against code this rework did not touch.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input (both read tools stopped with `sandbox-exec: sandbox_apply: Operation not permitted`), as in cycles 2 to 9. The refusal is kept at `docs/dev/tmp/bob-output-00004c10-first.txt`. The retry inlined the context and the diff (165 KB) and ran without `--resume-thread`. The `codex_thread_id` above is the retry's thread.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run)
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 9.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 297 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay (`python3 -m pytest`): 2 touched tests ran. `test_status_reports_an_unreadable_state_and_spares_the_other_specs` fails at base, as a regression test should. `test_hash_json_follows_the_configured_specs_folder` passes at base. This diff only reformats that test, and the ledger already dismisses its replay row (cycle-9 F4). Its row is merged into F8.
- Settled-decisions ledger: the script auto-dismissed six Blake findings. The lead checked each one against the ledger. Four matched a settled entry. Two were wrong dismissals caused by the shared-digit-token merge rule, and both are restored as F5 and F10 (see below).
- Consolidation corrections (by hand): the replay `[MECH]` row was merged into F8 (same test). Refs were renumbered from the script's `R1`..`R8`, and severity order was kept within each consensus level.
- Lead's checks:
  - F1, confirmed on Python 3.10.22, the version CI pins. The probe was a `.specflow.json` symlink into a folder without search permission. `Path.exists()` raises `PermissionError`, which `load_state` (`state.py:64`) does not catch. On 3.14.6 the same probe returns `False`, so `load_state` reports the spec as having no state, silently.
  - F2, confirmed by reading. `own_status` (`state.py:146-150`) catches only `UnicodeDecodeError` around `sha256_canonical`. `spec_status` (`status.py:161-165`) catches only `StateError` around `load_state`, so the `OSError` from an unreadable approved artifact reaches `main`, as in cycle-9 F1. `own_status`'s own `path.exists()` (`state.py:138`) has F1's 3.10 problem too. F1 and F2 likely share one root fix.
  - F3, refuted. In a scratch worktree at `7897f61`, the lead deleted the two added `deps.py` lines (`deps.py:146-147`) and ran the contract suite: 1 failure of 297. `test_unreadable_target_reason_names_no_absolute_path` got `state cannot be reconciled: cannot read: Permission denied` instead of `unreadable target: Permission denied`. Its `read_bytes` mock reaches `load_state` on the prerequisite, so the branch is covered.
  - F4, confirmed by reading. `gates` (`checks.py:607-645`) checks approvals, dependency blockers and drift, but never `marker_blockers`, which `status` uses to close the implementation gate.
  - F5, confirmed by reading. `requirement_coverage` (`checks.py:479-498`) checks only that every requirement ID is traced. A traced ID with no matching requirement is never checked. No ledger entry covers this. The script matched it to the bugfix-checks entry (00006).
  - F10: the ledger's specs-folder entry (cycle-8 F2) covers `status` failing when git fails, not `validate` scanning outside the spec. The script matched it to the placeholder entry, so it is restored.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/4] | 🟡 | The unreadable-state fix leaves `path.exists()` outside the error handler. On Python 3.10 (the CI version), a `.specflow.json` symlink into a folder without search permission raises `PermissionError` there, so one unreadable state still aborts the whole `status` run with exit 2. On 3.14, `exists()` returns `False` instead and the state is read as absent. Confirmed on 3.10.22 | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:64 | general | BOB |
| F2 | [1/4] | 🟡 | `own_status` catches only `UnicodeDecodeError` around `sha256_canonical`, so a permission error on an approved artifact raises `OSError`. `spec_status` catches only `StateError`, so `status` for all specs aborts with exit 2 instead of marking one spec invalid (the cycle-9 F1 class). `own_status`'s `path.exists()` has F1's 3.10 problem too. Blake also noted that an embedded NUL in a CLI path argument raises an uncaught `ValueError` in `folder()`. Confirmed by reading; the lead raised Blake's ⚪ to 🟡 to match cycle-9 F1 | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:146 | general | BLAKE |
| F3 | [1/4] | 🟡 | The new `deps.completeness` branch for a `StateError` caused by an `OSError` is untested: Alice says deleting the two added lines leaves all 297 tests passing. **Refuted by the lead:** with those lines deleted, `test_unreadable_target_reason_names_no_absolute_path` fails (1 of 297). Recommend dismissing | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/deps.py:146 | T-026 | ALICE |
| F4 | [1/4] | 🟡 | `validate --phase implementation` disagrees with `status`. Status closes the implementation gate on unaccepted upstream markers (WF-002.7), while the `gates` check ignores them. In Blake's scratch run, status showed the gate closed with `nextTask` null, and `validate --phase implementation` printed "valid". Confirmed by reading (`gates` never calls `marker_blockers`) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:607 | general | BLAKE |
| F5 | [1/4] | 🟡 | VAL-001.4 requirement traceability runs in one direction only. `requirement_coverage` checks that every requirement is cited, but a task citing a requirement that does not exist ("Requirements: REQ-999") or a criterion that does not exist ("REQ-001 criteria 1, 7") passes. Cross-spec references are checked (`checks.py:569`), but the spec's own are not. Confirmed by reading. Restored from a wrong ledger dismissal | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:478 | general | BLAKE |
| F6 | [1/4] | ⚪ | `StateError` still documents itself as "malformed or unsupported version" (`state.py:50`). It now also covers an unreadable file, so the docstring is stale. The design's interface comment has the same wording | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:50 | T-026 | ALICE |
| F7 | [1/4] | ⚪ | `error.strerror` can be `None` for an `OSError` raised without an errno, which would print "cannot read: None". `deps.unreadable` already guards this with `or "cannot be read"` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:69 | T-026 | ALICE |
| F8 | [1/4] | ⚪ | Unrelated reformatting of two lines in `test_hash_json_follows_the_configured_specs_folder` (the `shutil.copytree` call and the `assertEqual(..., 3)` call) does not trace to the F1 fix. The replay also flags this test as passing at base, which the ledger already dismisses (cycle-9 F4) | tests/specflow/contract/test_cli.py:259 | T-026 | ALICE, mech-check |
| F9 | [1/4] | ⚪ | Unrequested output and flags: the status JSON adds `problems`, `intake`, `specType`, `profile` and `state`, and the CLI adds `hash --raw` and `reconcile --dry-run`. The ledger already accepts `problems`, `intake`, `hash --raw` and `reconcile --dry-run`. `specType`, `profile` and `state` are the new half | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:204 | general | BLAKE |
| F10 | [1/4] | ⚪ | An unfiltered `validate` runs `number-clashes` and `specs-folder`. These list the intake and specs folders and call `git check-ignore`, which reaches outside the selected spec folder beyond what the NFR allows. The scans read names only, and VAL-001.8 requires them, so this is a note. Restored from a wrong ledger dismissal | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:739 | general | BLAKE |

Overlap: F1 and F2 are one class: a per-spec read error escapes to `main` and aborts every spec. F2 also notes that `own_status`'s own `exists()` call has F1's 3.10 problem. F4, F5, F9 and F10 concern code this rework did not touch.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json` and kept after the lead's check:

- [BLAKE] 🟠 VAL-001.8 placeholder scan not implemented (`checks.py:183`): settled as cycle-1 F23, deferred by design to 00005 T-071.
- [BLAKE] 🟠 VAL-001.4 bugfix task validation missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006. (The script printed the placeholder entry's reason for this line, as in cycles 8 and 9; the ledger's own entry names 00006.)
- [BLAKE] 🟡 VAL-001.3 unresolved design placeholders not checked (`checks.py:384`): covered by the placeholder entry ("unfilled design template sections"), deferred to 00005 T-071.
- [BLAKE] ⚪ `next-number` skips a bare five-digit folder (`numbers.py:11`): deferred in the cycle-8 walkthrough (cycle-8 F3).

Wrongly dismissed by the script and restored by the lead:

- [BLAKE] 🟡 one-direction traceability (`checks.py:478`), matched to the bugfix-checks entry. Now F5.
- [BLAKE] ⚪ unfiltered `validate` scans outside the spec (`checks.py:739`), matched to the placeholder entry. Now F10.

## Alice

Implementation-aware review of the cycle-9 rework (legacy consensus engine). She confirmed the cycle-9 F1 fix in a scratch repo whose `.specflow.json` is a folder: `status` marks only that spec `invalid` and exits 1; `validate` reports `state-valid` and exits 2; a dependent spec gets `unreadable target: Is a directory`. She ran the contract suite (297 OK). Findings: F3 (refuted by the lead), F6, F7, F8.

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

Blind lens (spec only). He read the helper source, ran the contract tests (297 OK), and probed scratch repos for placeholders, bugfix task order, traceability and the gate. He judged hashing, invalidation, the guarded state write, config path refusal, the code baseline, spec dependencies, cross-spec references and read-only validate/status as conforming. Findings: F2, F4, F5, F9, F10, plus four re-raises auto-dismissed above.

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: fail
B7: fail
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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input. The retry raised F1. FIX holds one item (guard the existence check too, and add a regression test for its `PermissionError`); VERIFY and KNOWN are empty.

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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0. He read the context and diff and found no issues.

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

Verdict: 10 findings

Tests: 361 passed, 0 failed, 0 skipped (suite run this cycle)
