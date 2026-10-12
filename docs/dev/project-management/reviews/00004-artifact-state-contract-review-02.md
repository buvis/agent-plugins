---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 2
date: 2026-10-11
head_sha: 4efec99f8484ba5918866831bdfb19979d01e30d
codex_thread_id: 01a12ad2-d991-7283-8b9a-6a95877cc4fe
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `4d000aa9c292b87c494f532c27d53b876d07f793..4efec99f8484ba5918866831bdfb19979d01e30d`

codex_rung_guard: not fired

## Review Summary

Standalone run (no autopilot `state.json`, no wip PRD), cycle 2. This is an incremental review of the rework since cycle 1 (`43c4748` and the commits after it, up to `4efec99`). Alice and Bob verified the cycle-1 fixes and looked for regressions. Blake reviewed blind, from the spec alone, as in every cycle. As in cycle 1, the target was spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. Findings are reported here, not written as tasks.

Cycle-1 items now closed by this diff: F31 (the CI contract-test step landed in `4efec99`). All other cycle-1 fixes held: no reviewer found a regression in F1, F2, F3, F4/F5/F16/F17, F6, F8, F11, F12, F13, F14, F15, F21, F24, F25, F26, or F29. F7 and F22 are only partly closed (F1 and F7 below).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined): his resumed-thread run refused because codex's sandbox blocked `cat` with `sandbox_apply: Operation not permitted`. The refusal is kept at `docs/dev/tmp/bob-output-00004c2-first.txt`)
- Carl: ⚠️ Unavailable: copilot backend (`gemini-3.8-flash`) exited 1 with "No authentication information found", on the first run and on the one retry, which ran with the sandbox off. This is a one-off runtime failure (exit 1, not 4), so nothing was latched.
- Eve: ⏸️ Disabled (doubt_reviewer resolved to codex; no codex-implemented tasks recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid.
- Gate: `review-stage` ran the full gate (exit 0) but could not parse unittest counts. The counts below come from suite runs this cycle at HEAD: contract 247 OK, release 52 OK, `scripts` 12 OK. `validate.py` and `verify_release.py` exited 0 inside the gate.
- Fail-first replay: the pytest replay flagged 9 touched tests as passing against base (`[MECH]` lines). The lead re-ran all 9 under unittest in a worktree at `4d000aa`. Three fail there: `test_stale_approvals_name_each_stale_artifact_and_its_cause`, `test_marker_skipped_by_the_second_approval_closes_implementation`, and `test_each_refused_path_yields_not_checked` (the `C:/` subcase). The other six pass by design: three pin kept behavior (`test_recorded_stale_outlives_the_upstream_reapproval`, `test_no_repository_and_quiet_misses_are_absence_not_errors`, `test_withdrawn_id_stays_reserved`), two had formatting-only edits (`test_bugfix_sources_closes_the_introduction`, `test_references_resolve_in_the_configured_specs_folder_only`), and `test_helper_reads_the_placed_line_in_every_capture` is the retargeted parser test. Bob's VERIFY item is resolved by this replay (F9).
- Consolidation corrections (by hand): the script merged four Blake `checks.py` findings into one row (placeholders, design placeholders, bugfix task checks, cross-spec references), plus his NFR finding. They are split again: the three deferred-by-design items are under Auto-dismissed, and cross-spec and NFR are F4 and F8. The script's merge of Alice's F7 residual with Bob's F7 residual (F1) is correct.
- Lead's checks:
  - F1 confirmed by reading `checks.py:384-392`: `malformed_boxes` scans every line above `## Completion criteria`, and a Kiro-native plan has no such heading.
  - F2 confirmed by Blake's run, but downgraded from 🟠 to 🟡. The design pins the drop rule to one list line (design.md:646, :659), so the code matches the design. The open question is whether WF-002.4's "progress fields dropped" covers continuation lines.
  - F4 confirmed by reading `checks.py:521`: the cited reference is compared with the declared list as a raw string, before resolution.
  - F5 confirmed by reading `state.py:124-131`: a record whose `status` is not `approved` reads as `draft`, even when `approvedSha256` still matches.
  - F6 confirmed by reading `checks.py:388`: the `COMPLETION` break ignores `in_fence`, while `scan_lines` does not.
  - F10 downgraded from 🟡 to ⚪. Only folder names are listed, never content, and ART-001.8 makes the `.kiro/specs` link the repository's own setup.
- No verification-check queue was written, and no dispatch rows were opened (standalone run).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/3] | 🟡 | F7 residual: `BAD_CHECKBOX` still errors on bracket labels (`- [Q1] note`) above `## Completion criteria`, and anywhere in a Kiro-native `tasks.md` that has no such heading. The new test puts its labels below the heading only (confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:388 | T-026 | ALICE, BOB |
| F2 | [1/3] | 🟡 | The `tasks.md` hash keeps continuation lines of a multi-line `Outcome:` or `Exception:`, so recording one stales the tasks approval. The code matches the design's one-line rule (design.md:646). Spec gap (lead: downgraded from 🟠) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/canonical.py:70 | T-022 | BLAKE |
| F3 | [1/3] | 🟡 | The withdrawn-requirement exemption (`### <ID>: withdrawn`) is not in the approved VAL-001.2 text or in the design's `requirement-ids`/`requirement-coverage` rows. "Nothing may cite it" is enforced only through the design's traceability table | docs/dev/project-management/specs/00004-artifact-state-contract/design.md:232 | T-026 | ALICE |
| F4 | [1/3] | 🟡 | `cross-spec-references` compares the cited spec with the `Depends on:` list as a raw string. `00004 WF-004...` against `folder:00004-artifact-state-contract` is reported as not declared (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:521 | T-026 | BLAKE |
| F5 | [1/3] | 🟡 | After `reconcile` records a deleted artifact as `missing`, restoring the file unchanged reads as `draft`, not `stale`. The approval is dropped silently (WF-005.4). Fail-safe but lossy | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:91 | T-024 | BLAKE |
| F6 | [1/3] | 🟡 | `malformed_boxes` stops at a `## Completion criteria` line even inside a fence, so a fenced example hides later malformed boxes (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:388 | T-026 | BOB |
| F7 | [1/3] | 🟡 | F22 residual: `test_placement_keeps_headings_and_ids_in_every_capture` still tests the test-local insertion helper; the new parser test sits beside it rather than replacing it | tests/specflow/contract/test_templates.py:278 | T-020 | BOB |
| F8 | [1/3] | 🟡 | Performance NFR: every unfiltered `validate` runs `number-clashes` and `specs-folder`, which list folders outside the spec and run `git check-ignore`. VAL-001.8 requires the reports, so the two spec lines conflict mildly | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:598 | T-026 | BLAKE |
| F9 | [1/3] | 🟡 | The fail-first replay flagged 9 touched tests as passing against base. Resolved by the lead's unittest replay: 3 fail at base, and 6 pass by design (see Run notes). Recommend dismissing | tests/specflow/contract/test_status.py:184 | T-026 | BOB, mech-check |
| F10 | [1/3] | ⚪ | The `.kiro/specs` leftover scan in `next_number` follows a link to a target outside the repository and lists its folder names (lead: downgraded from 🟡) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:57 | T-029 | BOB |
| F11 | [1/3] | ⚪ | The design is out of sync with the refactor: `Finding` moved to `findings.py`, text helpers to `spec_text.py`, `Context` gained `phase`, and `validate` gained `skip`. The module table lists neither new module | docs/dev/project-management/specs/00004-artifact-state-contract/design.md:146 | T-026 | ALICE |
| F12 | [1/3] | ⚪ | `\d{5}` matches non-ASCII digits (`valid_item('١٢٣٤٥')` is True), while the contract says five ASCII digits. The same pattern is in `numbers.py:11` and `spec_text.py:13` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/deps.py:13 | T-026 | BLAKE |
| F13 | [1/3] | ⚪ | `reconcile` and `status` accept a spec directory outside the repository. `write_guarded` uses a fixed temp name and drops file permissions | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:29 | T-025 | BLAKE |
| F14 | [1/3] | ⚪ | Drift baselines hash raw bytes, so CRLF or autocrlf churn gives false `code-drift` warnings (advisory only) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/drift.py:53 | T-026 | BLAKE |
| F15 | [1/3] | ⚪ | `SKILL.md` is still a shell; the agent side of WF-004.2-5 and WF-006 waits on 00006 (out of scope here) | plugins/specflow/skills/spec-workflow/SKILL.md:6 | general | BLAKE |
| F16 | [1/3] | ⚪ | KNOWN: T-027 Kiro IDE Bug Fix display and link trials pending (cycle-1 F32) | docs/dev/project-management/specs/00004-artifact-state-contract/tasks.md:21 | T-027 | BOB |

Overlap: F1 and F6 both concern `malformed_boxes` and fit one fix. F3 and F11 are both design-text updates.

### Auto-dismissed (ledger)

No ledger file exists for this spec. These were dismissed by hand against the settled cycle-1 minutes:

- [BLAKE] 🟠 VAL-001.8 / ART-001.10 placeholder detection not implemented: settled as F23, deferred by design to 00005 T-071 (accepted 2026-10-11).
- [BLAKE] 🟠 VAL-001.3 unresolved design placeholders not checked: settled as F23, deferred to 00005 T-071.
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage missing: settled as F23, deferred to 00006.
- [BOB] ⚪ KNOWN placeholder and bugfix task-order checks deferred: same as F23.
- [BLAKE] ⚪ Scope extras (`cross-spec-review.md`, `hash --raw`, `code-baseline`, `next-number`): settled as F28 (accepted).

## Alice

Findings: F3, F1 (merged), F11. She saw no regression in the cycle-1 fixes.

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

## Blake

Blind lens (spec only). He ran the contract tests (247 OK). He judged these conforming: config path refusal, number scanning and clashes, the state schema and content scan, derived phase and sticky stale, downstream invalidation, the dependency grammar, cycles and blockers, the status JSON and its schema, the all-or-nothing baseline and drift warnings, preserved malformed state, and unknown fields kept on reconcile. Findings: F2 (downgraded), F4, F5, F8, F12, F13, F14, F15, and three re-raised F23 items plus one F28 item (auto-dismissed above).

B1: fail
B2: fail
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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input (the sandbox blocked `cat`). The retry carried the context and the full diff inline (270 KB), ran without `--resume-thread`, and wrote the issue lines in the right shape under FIX/VERIFY/KNOWN headers. FIX: F1 (merged), F6, F10, F7. VERIFY: F9 (resolved by the lead's replay). KNOWN: F16, plus the F23 deferral (auto-dismissed).

R1: fail
R2: fail
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

Verdict: 16 findings

Tests: 311 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-11)

- F1 + F6: `malformed_boxes` scans from the first task to the next level-2 heading and skips fenced lines. This covers Kiro-native plans and a fenced `## Completion criteria`. Add 2-3 tests. Queued.
- F2: Outcome and Exception stay one line. No change to the hash rules. State it in `artifact-contract.md` and the tasks template, and have `progress-fields` warn on a continuation line under one. Queued.
- F3 + F11: edit the design. Add the withdrawn exemption to the `requirement-ids` and `requirement-coverage` rows, and update the interface block and module table for `findings.py`, `spec_text.py`, `Context.phase` and `validate(skip=...)`. Then re-approve the design, and the tasks it stales. Queued.
- F4: `cross-spec-references` compares resolved folders, not raw strings. Add one test per direction (number against `folder:`, and the reverse). Queued.
- F5: a file restored over a recorded `missing` that still has `approvedSha256` reads as `stale`, with the cause "deleted since approval" in `stale-approvals`. Add one test. Queued.
- F7: delete `test_placement_keeps_headings_and_ids_in_every_capture`. Queued.
- F8: accepted. Add one design line saying VAL-001.8's repository reports count as repository discovery under the Performance NFR. Queued with F3.
- F9: dismissed. The lead's unittest replay at `4d000aa` shows the named tests fail at base, and the six that pass do so by design.
- F10: `next_number` scans `.kiro/specs` leftovers only when it is a real directory inside the repository. Add a link test. Queued.
- F12: `[0-9]{5}` in place of `\d{5}` in `deps.py`, `numbers.py` and `spec_text.py`. Add one test. Queued.
- F13: refuse a spec directory outside the repository in `reconcile` and `status`. `write_guarded` uses a unique temp name and keeps the file mode. Queued.
- F14: drift hashes use line-ending-normalized content. Note that existing `approvedCode` baselines may show drift once. Queued.
- F15: out of scope (00006). Accepted.
- F16: known open item (T-027 Kiro IDE trials, cycle-1 F32). The developer owns it.
- Auto-dismissed (F23/F28 re-raises): settled in cycle 1, no action.

### Outcome (2026-10-12, commits b99b7d5 and 2eb3f1b)

Every queued item is applied:

- F1 + F6: the scan covers only the part above the first level-two heading and the `## Tasks` section, and it skips fenced lines. This departs from the minutes ("from the first task to the next `##`"). That rule would have stopped at `## Tasks` whenever a bracketed item stood in a Kiro `## Overview` above it, so it would have skipped every task.
- F2: `progress-fields` now warns on a line that continues an `Outcome:` or `Exception:` field, once per field, in any plan. The contract and the tasks template state the one-line rule.
- F3 + F8 + F11: design edits, plus the design-text side of F1, F2, F4, F5, F13 and F14. They are recorded in the qa-log. The design and tasks approvals are now stale and need the developer's re-approval.
- F7: the helper-only placement test is deleted.
- Code: F4, F5, F10, F12, F13 and F14, with one regression test each (12 new tests). Fail-first: all 12 fail against the old code at `a039b6c`, with 15 failures and 1 error across subtests.
- Housekeeping: a stray `specflow_helper/__pycache__` from Blake's 2026-10-11 probe was removed. It failed the no-bytecode test.
- Checks: 257 contract tests on Python 3.14 and 3.10, 52 release tests and 12 validator tests, all OK. `validate.py` and `verify_release.py` exit 0.
