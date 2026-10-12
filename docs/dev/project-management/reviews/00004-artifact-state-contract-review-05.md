---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 5
date: 2026-10-12
head_sha: 8cee2d8744fe5a4644a8b6147b0e47418d22de47
codex_thread_id: 01a13189-137a-7792-a698-736f8cb0532b
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `60ae7e10c32e57221a8c7110573ea890f673365f..8cee2d8744fe5a4644a8b6147b0e47418d22de47`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 5. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-4 rework incrementally (`60ae7e1..8cee2d8`: the fix commit `140ea26`, the design edits and re-approvals, and the cycle-4 minutes). The target is spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. Findings are reported here, not written as tasks.

Every cycle-4 fix holds except one. Alice checked each against the code: F1+F2, F4, F5, F8, F9, F10, F11, F12 and F13 are resolved. F3 (WF-002.4 hash scope) is only partly fixed: the rework narrowed the reset to task items and the `## Completion criteria` section, but the scanner still classes every checkbox above the completion section as a task item, so a box in a section placed above it is still reset. Alice and Bob found this independently. Blake's blind pass added two spec-vs-code gaps (a required `schemaVersion` the spec does not name; an upstream re-approval revives a record that carries no `upstreamSha256`) and three low items.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input: it asked for the context and the diff to be inlined, and failed every R rule for want of evidence, as in cycles 2 to 4 (codex's sandbox blocks file reads). The refusal is kept at `docs/dev/tmp/bob-output-00004c5-first.txt`. The retry inlined the context and the diff (228 KB) and ran without `--resume-thread`; the `codex_thread_id` above is the retry's thread.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "Authentication failed", on the first run and on the one retry. This is a one-off runtime failure (exit 1, not 4), so nothing was latched. It is the same failure as cycles 2 to 4; the agent launcher denies the GitHub config copilot reads its token from.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 and 4.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 280 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay: the pytest replay flagged 8 touched tests in 5 files as passing against base. The lead re-ran them under unittest in a worktree at `60ae7e1` with the HEAD test files copied in. 4 fail there (`test_each_refused_path_is_named_before_use` 1 error, `test_bugfix_declaration_not_last_in_its_introduction_is_misplaced` 2 subtests, `test_indented_or_recased_declaration_is_malformed` 3 subtests, `test_every_shipped_pattern_is_anchored_for_external_validators` 5 subtests): the `subTest` artifact of cycles 2 to 4 (F6 below). 4 really pass at base (F5 below).
- Settled-decisions ledger: this cycle introduces `00004-artifact-state-contract-ledger.json`, built from the minutes of cycles 1 to 4, so that the cycle-1 F23 deferrals Blake re-raised in cycles 2, 3 and 4 are absorbed mechanically. It worked for those two. It also mis-dismissed one Blake finding (restored as F8 below): the consolidator's "two shared all-digit tokens" merge rule, meant for line numbers, fires on requirement IDs such as `VAL-001.8`, which tokenize to `001` and `8`. The same rule paired the bugfix re-raise with the placeholder entry, so its printed reason is the wrong one; corrected under Auto-dismissed below.
- Consolidation corrections (by hand):
  - The script does not parse Bob's `- [BOB] ...` bucket lines; a copy with the bullet stripped (`bob-output-00004c5-lines.txt`) was fed to it. His one FIX finding merged with Alice's as F1.
  - The two mechanical replay rows (F5, F6) were added by hand after the lead's unittest replay; the `[MECH]` line for `test_checks.py` also names the test whose row F2 is about, so `mech-check` is added to F2's finders.
- Lead's checks:
  - F1 confirmed by reading `canonical.py:58`: `scan_lines` marks a box as a task item whenever `above_completion` holds, whatever section it is in. Alice ran it as well.
  - F2 confirmed by reading `spec_text.py:14`: `CROSS_SPEC` needs a space after the fifth digit. The row's text has eight digit characters before the space, so even a `\d{5}` regression returns `None` under `match`. The sibling row `00042 REQ-{arabic}` does bind.
  - F3 confirmed by reading `specflow-config.schema.json:7` (`required: ["schemaVersion"]`).
  - F4 confirmed by reading `state.py:201`. The behavior is the one design §7.4 documents (`design.md:660`: "A record without the field binds nothing and keeps the earlier rule"), decided as the cycle-3 F1 fix. Blake's point is that the requirement (STATE-002.4) does not carry that exception.
  - F8: not run. Blake read `checks.py:660`; the Performance NFR (`requirements.md:251`) allows a scan outside the spec directory "when a new spec number is claimed", not on every phase.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/3] | 🟡 | Cycle-4 F3 (WF-002.4 hash scope) is only partly fixed. `scan_lines` treats every checkbox item above `## Completion criteria` as a task item, so `canonical` still resets the box of a list item in any section placed above the completion criteria, or anywhere when that section is absent. Alice ran it: `- [x] open risk` under `## Risks` above `## Completion criteria` becomes `- [ ] open risk`. The fix and its test cover only a section after the completion criteria. The claim "A checkbox in any other section ... is hashed like other text" (artifact-contract.md:332, CHANGELOG, design §7.3.5) is wrong for those placements. Either narrow `in_task` to the task-list region (as `task-structure` does), or state the limit in the docs; add a test for a box above the completion criteria (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/canonical.py:82 | T-022 | ALICE, BOB |
| F2 | [1/3] | 🟡 | The new ASCII-digit row `(CROSS_SPEC, f"{arabic}{arabic}00 REQ-001")` can never fail. `arabic` is 3 digits, so the text starts with 8 digit characters; even if `[0-9]{5}` regressed to `\d{5}`, `match` would take 5 digits, need a space, find a sixth digit, and return `None`. Use `f"{arabic}00 REQ-001"` so the row binds to the ASCII rule (confirmed by reading) | tests/specflow/contract/test_checks.py:500 | T-026 | ALICE, mech-check |
| F3 | [1/3] | 🟡 | `.agents/specflow.json` must carry `schemaVersion`. INT-001.1 only says the file supplies the root and specs folder. A config such as `{"root": "x"}` makes every command exit 2 with a configuration error, including `hash` and `next-number` (confirmed by reading) | plugins/specflow/skills/spec-workflow/schemas/specflow-config.schema.json:7 | T-028 | BLAKE |
| F4 | [1/3] | 🟡 | STATE-002.4 ("an upstream re-approval never revives a downstream approval") holds only when the downstream record carries `upstreamSha256`. `rebound` ignores a record without the field, and the schema does not require it. A hand-written or older record that `reconcile` has not stale-marked goes back to approved once the upstream is re-approved. Code matches design §7.4 (`design.md:660`), which keeps the earlier rule for such records; the requirement carries no such exception (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:202 | T-023 | BLAKE |
| F5 | [1/3] | 🟡 | Replay: 4 touched tests pass against the pre-change code under unittest too: `test_structure_ids_take_ascii_digits_only` and `test_traced_ids_take_ascii_digits_only` (the F8 coverage rows; the patterns already used `[0-9]` at base), `test_malformed_or_unsupported_state_is_2` (`test_cli.py`; the F9 pin of an existing exit code) and `test_fenced_and_list_fields_declare_nothing` (`test_deps.py`; the F13 contract change moved the indented case out, the rest was already right). All four are coverage pins by the cycle-4 outcome's own account. Recommend dismissing, with F2 as the one row that needs fixing | tests/specflow/contract/test_checks.py:471 | T-026 | mech-check |
| F6 | [1/3] | 🟡 | Replay flagged `test_each_refused_path_is_named_before_use` (`test_config.py`), `test_bugfix_declaration_not_last_in_its_introduction_is_misplaced` and `test_indented_or_recased_declaration_is_malformed` (`test_deps.py`) and `test_every_shipped_pattern_is_anchored_for_external_validators` (`test_state_schema.py`) as passing against base. The lead's unittest replay at `60ae7e1` shows all 4 fail there (1 error, 10 subtest failures): the `subTest` artifact again. Recommend dismissing | tests/specflow/contract/test_config.py:75 | T-026 | mech-check |
| F7 | [1/3] | ⚪ | `gates` re-implements the approved branch of `status.drift_warnings` (the `.git` exists check, then `code_drift` on `approvedCode`) to avoid a circular import. Moving `drift_warnings` into `drift.py` would let `status` and `gates` share it | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:622 | T-026 | ALICE |
| F8 | [1/3] | ⚪ | `validate` runs `number-clashes` and `specs-folder` (directory listings plus `git check-ignore`) on every phase. This reaches outside the selected spec directory, against the Performance NFR (`requirements.md:251`), which allows it when a new spec number is claimed. The scan is names only, and VAL-001.8 asks for the reports, so the spec pulls both ways (restored from a wrong ledger dismissal; not run) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:660 | T-026 | BLAKE |
| F9 | [1/3] | ⚪ | The status JSON has no explicit "stale artifacts" list as STATE-003.1 words it. Staleness is visible only through the `artifacts` status map and the blockers | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:205 | T-026 | BLAKE |
| F10 | [1/3] | ⚪ | `write_guarded` is a check-then-replace sequence, which WF-006.4 accepts explicitly. A symlinked `.specflow.json` would be replaced by a regular file | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:31 | T-025 | BLAKE |

Overlap: F2 and F5 both concern the F8 ASCII-digit rows; fixing F2 settles the one real gap in F5. F5 and F6 are both replay noise once F2 is handled.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json`:

- [BLAKE] 🟠 VAL-001.8 / VAL-001.3 placeholder and unfilled design template checks missing (`checks.py:61`): settled as cycle-1 F23, deferred by design to 00005 T-071; re-raised and dismissed in cycles 2, 3 and 4.
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage checks missing (`checks.py:470`): settled as cycle-1 F23, deferred by design to 00006; re-raised and dismissed in cycles 2, 3 and 4. (The script printed the placeholder entry's reason for this line; the ledger's own entry for it names 00006.)
- [BLAKE] ⚪ `validate` runs `number-clashes` and `specs-folder` on every phase (`checks.py:660`): a wrong dismissal, matched to the placeholder entry on shared requirement-ID digits. Restored as F8 above.

## Alice

Implementation-aware review of the cycle-4 rework (legacy consensus engine). She verified every cycle-4 fix in the code and found one regression in them (F1). She also ran the contract suite (280 OK). Findings: F1 (merged), F2, F7. The settled and dismissed items were not re-raised.

R1: pass
R2: fail
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

Blind lens (spec only). He found the helper himself and ran the contract tests (280 OK). He judged these conforming: canonical hashing and the `tasks.md` normalization as WF-002.4 words it, the state schema, stale propagation, `reconcile` (derived facts only, guarded, never replacing malformed state), recovery mode, the whole-or-nothing code baseline and drift warnings, the dependency grammar and cycle blockers, `nextTask: null` on a closed gate, the status schema, config path refusal (SEC-002.5), spec numbering, and the clash, sources-line and specs-folder checks. Findings: F3, F4, F8, F9, F10, plus two F23 re-raises (auto-dismissed above).

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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input (the sandbox blocked file reads). The retry wrote FIX/VERIFY/KNOWN buckets. FIX: F1 (merged). VERIFY and KNOWN: none.

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

Verdict: 10 findings

Tests: 344 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-12)

- F1: narrow task-item detection to the task-list region (before the first `## ` heading, or under `## Tasks`, as `task-structure` does), so a box in any other section is hashed as text wherever it sits. Add a test for a box in a section above `## Completion criteria`. Queued.
- F2: change the `CROSS_SPEC` row text to `f"{arabic}00 REQ-001"` so the row fails under a `\d` regression. Queued.
- F3: `schemaVersion` becomes optional in the config schema (still `const: 1` when present); the loader treats an absent field as version 1. Queued.
- F4: an approved design or tasks record without `upstreamSha256` derives as `stale`, cause "approval binds no upstream"; re-approval heals it. Design §7.4 changes, so design and tasks need re-approval. Add a test. Queued.
- F5: dismissed. The four tests pin behavior that was already right; F2 is the one row that needs fixing.
- F6: dismissed. The `subTest` replay artifact again (cycle-2 F9, cycle-3 F6, cycle-4 F7): the lead's unittest replay shows all 4 fail at base.
- F7: move `drift_warnings` into `drift.py` so `status` and `gates` share it. Queued.
- F8: run `number-clashes` and `specs-folder` in the requirements phase only. Queued.
- F9: add a top-level `stale` array of artifact names to the status JSON and its schema. Queued.
- F10: one sentence in the artifact contract stating that a symlinked `.specflow.json` is replaced by a regular file. Queued.
- Auto-dismissed re-raises (cycle-1 F23 placeholders and bugfix checks): settled earlier, no action.
