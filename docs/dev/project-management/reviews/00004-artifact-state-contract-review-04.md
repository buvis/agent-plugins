---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 4
date: 2026-10-12
head_sha: 60ae7e10c32e57221a8c7110573ea890f673365f
codex_thread_id: 01a1313b-2ce4-7a91-a58d-d313356b82c1
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `d293581f2e08076ed06cdcea545888922a9c47ba..60ae7e10c32e57221a8c7110573ea890f673365f`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 4. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-3 rework incrementally (`d293581..60ae7e1`: the fix commit `b3bd780` plus the design edits and re-approvals). The target is spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. Findings are reported here, not written as tasks.

Every cycle-3 fix holds. Alice checked each against the code: F1+F9, F2, F3, F4, F5, F7, F8, F10, F11, F12, F13 and F14. Two reviewers found that the F3 rework pushed `spec_status` past the 50-line limit, and two found that its new `resolve().relative_to(repo)` reference can raise on a symlink. Blake's blind pass found two new spec-vs-code gaps (WF-002.4 hash scope, WF-004.8 drift in `validate`).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on his resumed thread, refused for lack of input: codex's sandbox blocked file reads with `sandbox_apply: Operation not permitted`, as in cycles 2 and 3. The refusal is kept at `docs/dev/tmp/bob-output-00004c4-first.txt`. The retry inlined the context and the diff (242 KB) and ran without `--resume-thread`.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "Authentication failed", on the first run and on the one retry. This is a one-off runtime failure (exit 1, not 4), so nothing was latched. It is the same failure as cycles 2 and 3.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid.
- Gate: `review-stage` ran the full gate (exit 0) but could not parse the unittest counts. The counts below come from suite runs this cycle at HEAD: contract 271 OK, release 52 OK, `scripts` 12 OK.
- Fail-first replay: the pytest replay flagged 5 touched tests as passing against base. The lead re-ran them under unittest in a worktree at `d293581` with the new test files copied in. 3 fail there (`test_structure_ids_take_ascii_digits_only` 5 subtests, `test_upstream_reapproval_without_reconcile_never_revives_downstream` 2 errors, `test_every_shipped_pattern_is_anchored_for_external_validators` 5 subtests): the `subTest` artifact of cycle-2 F9 and cycle-3 F6. 2 really pass at base (F6 below).
- Consolidation corrections (by hand):
  - The script did not parse Bob's `- [BOB] ...` bucket lines, so his three findings are added by hand (F1, F2, F5).
  - The script merged Blake's two 🟠 re-raises (placeholders, bugfix task checks) into one row. Both are dismissed below.
  - Alice's and Bob's `spec_status` length findings merge as F1. Blake's spec-folder symlink and Bob's sidecar symlink findings name the same line and merge as F2.
  - Alice's pass-at-base note merges with the two genuine replay rows as F6.
- Lead's checks:
  - F2 confirmed by reading `status.py:161-163`: `problem.path.resolve()` follows a link, and `relative_to(repo.resolve())` raises `ValueError` when the target is outside the repo. Not run.
  - F3 confirmed by reading `canonical.py:76` against WF-002.4 (`requirements.md:96`): the spec normalizes "the checkbox state of task and completion-criteria items", while the code, and design §7.3.5 (`design.md:670`), normalize any list-item checkbox outside a fence. The code matches the design; the design is wider than the spec.
  - F5: holds for Python validators. `jsonschema` uses `re.search`, where `$` also matches before a final newline. ECMA-262 engines do not. Not run.
- No verification-check queue was written, and no dispatch rows were opened (standalone run).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/3] | 🟡 | `spec_status` is now 57 lines (49 at `d293581`), crossing the 50-line limit in this rework. Extract the invalid-state blocker into a helper | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:142 | T-026 | ALICE, BOB |
| F2 | [2/3] | 🟡 | The new invalid-state `reference` does `problem.path.resolve().relative_to(repo.resolve())`. A malformed `.specflow.json` symlink, or a spec folder symlink, pointing outside the repo raises an uncaught `ValueError` and aborts the whole `status` (confirmed by reading). Build the reference from the lexical repo-relative path, and add a symlink regression test | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:161 | T-026 | BLAKE, BOB |
| F3 | [1/3] | 🟡 | WF-002.4 hash scope: the `tasks.md` canonical text normalizes every non-fenced list checkbox, not only task and completion-criteria items. A `- [x]` flipped under `## Unresolved questions` or `## Risks` does not stale the approval. Code matches design §7.3.5; the design is wider than the spec (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/canonical.py:76 | T-022 | BLAKE |
| F4 | [1/3] | 🟡 | WF-004.8: drift warnings come only from `status`. `validate --phase implementation` (the `gates` check) emits no drift or not-checked warning, so the before-implementation comparison relies on the caller also running `status` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:587 | T-026 | BLAKE |
| F5 | [1/3] | 🟡 | F13 is incomplete: the anchored schema patterns end in `$`, which in Python `re.search` (used by `jsonschema`) also matches before a final newline. `"a"*64 + "\n"` passes the shipped `sha256` pattern externally but fails the helper's `fullmatch`. Use an absolute end both engines honor, or document the gap, and test that value | plugins/specflow/skills/spec-workflow/schemas/specflow-state.schema.json:55 | T-021 | BOB |
| F6 | [1/3] | 🟡 | Replay: `test_design_sections_lets_kiro_designs_keep_their_headings` (`test_checks.py`) and `test_new_file_takes_the_umask_mode_not_the_temporary_files` (`test_concurrency.py`) pass against the pre-change code (the lead's unittest replay agrees). Alice adds `test_approval_without_an_upstream_binding_binds_nothing`. All three pin behavior that was already right (a no-false-positive guard, the F10 coverage test, the no-binding case), so recommend dismissing | tests/specflow/contract/test_concurrency.py:55 | T-025 | ALICE, mech-check |
| F7 | [1/3] | 🟡 | Replay flagged `test_structure_ids_take_ascii_digits_only`, `test_upstream_reapproval_without_reconcile_never_revives_downstream` and `test_every_shipped_pattern_is_anchored_for_external_validators` as passing against base. The lead's unittest replay at `d293581` shows all 3 fail there (`subTest` artifact). Recommend dismissing | tests/specflow/contract/test_checks.py:471 | T-026 | mech-check |
| F8 | [1/3] | ⚪ | The F8 ASCII-digit test covers five patterns only. Others changed in the same sweep have no test: `canonical.LIST_MARKER` (it feeds the hash), `checks.ID_ENTRY`, `BAD_CHECKBOX`, `state.TASK_LINE`, `status.LIST_ITEM`, `CROSS_SPEC`, `traced_ids` | tests/specflow/contract/test_checks.py:471 | T-026 | ALICE |
| F9 | [1/3] | ⚪ | `hash --json` now calls `load_state`, so a malformed sibling `.specflow.json` makes it exit 2 where it used to succeed. Probably right under STATE-002.5, but no test pins it and the design does not say so | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:154 | T-026 | ALICE |
| F10 | [1/3] | ⚪ | The F11 template trigger matches section names case-sensitively. A hand-edited Kiro design with lowercase `## Error handling` is classed as a specflow template and must hold all 16 sections | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:361 | T-026 | ALICE |
| F11 | [1/3] | ⚪ | SEC-002.5: a configured path holding NUL makes `Path.resolve()` raise `ValueError`. `main()` does not catch it: a traceback and exit 1, not `configuration error` and exit 2 | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/config.py:30 | T-028 | BLAKE |
| F12 | [1/3] | ⚪ | INT-001.1: `templates/specflow.json` ships this repo's own `docs/dev/project-management` root and specs folder. Copied verbatim, it sets non-default locations in a user's repo | plugins/specflow/skills/spec-workflow/templates/specflow.json:3 | T-028 | BLAKE |
| F13 | [1/3] | ⚪ | VAL-001.8: an indented or misspelled `Depends on:` line, and a bugfix `Depends on:` not at the end of the Introduction, give no "malformed" finding | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/deps.py:48 | T-026 | BLAKE |

Overlap: F1 and F2 are both the F3 rework in `spec_status`; one helper extraction can fix both. F6 and F7 are both replay noise.

### Auto-dismissed (ledger)

No ledger file exists for this spec. These were dismissed by hand against the settled minutes of cycles 1 to 3:

- [BLAKE] 🟠 VAL-001.8 / ART-001.10 / VAL-001.3 placeholder checks missing: settled as cycle-1 F23, deferred to 00005 T-071 (re-raised in cycle 3 too).
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage missing: settled as cycle-1 F23, deferred to 00006 (re-raised in cycle 3 too).

## Alice

Findings: F1, F6 (merged), F8, F9, F10. She verified every cycle-3 fix in the code and found no regression in them. She judged the pass-at-base tests to be behavior pins, not tautologies.

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
R12: fail
R13: pass

## Blake

Blind lens (spec only). He read the helper, schemas and templates, probed `validate` against a scratch spec, and ran the contract tests (271 OK) and `validate.py`. He judged these conforming: the state schema and precedence, hash-bound approvals, downstream invalidation surviving upstream re-approval, accepted markers, hold, the guarded state write, drift baselines, number scanning, config path refusal, the dependency graph and cycle checks, and the read-only status output. Findings: F2 (merged), F3, F4, F11, F12, F13, plus two F23 re-raises (dismissed above).

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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input (the sandbox blocked file reads). The retry wrote FIX/VERIFY/KNOWN buckets. FIX: F5, F2 (merged), F1 (merged). VERIFY and KNOWN: none.

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 13 findings

Tests: 335 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-12)

- F1 + F2: move the invalid-state blocker into a helper. This also brings `spec_status` back under 50 lines, as the standing rule requires. The helper builds `reference` from the path relative to the repo, without resolving it. Add one symlink regression test (a malformed sidecar or spec folder linked outside the repo). Queued.
- F3: narrow the code to the spec. The `tasks.md` hash resets only the boxes of task items and `## Completion criteria` items. Every other box outside a fence stays hash-bound. Design §7.3.5 changes, so design and tasks need re-approval. Queued.
- F4: the `gates` check under `--phase implementation` emits the drift and not-checked warnings, reusing `drift_warnings`. Queued.
- F5: put a no-newline guard beside each anchored schema `pattern` (it must work in both Python and ECMA-262 engines). Test a 64-hex `sha256` value followed by a newline. Queued.
- F6: dismissed. The three tests pin behaviour that was already right. Each fix has its own test that fails at base.
- F7: dismissed. This is the `subTest` replay artifact again (cycle-2 F9, cycle-3 F6): the lead's unittest replay shows all 3 tests fail at base.
- F8: add one ASCII-digit table row for each pattern still untested (`LIST_MARKER`, `ID_ENTRY`, `BAD_CHECKBOX`, `TASK_LINE`, `LIST_ITEM`, `CROSS_SPEC`, `traced_ids`). Queued.
- F9: add a test that `hash --json` exits 2 on a malformed sibling `.specflow.json`, and one design line citing STATE-002.5 (part of F3's design edit). Queued.
- F10: match template section names without regard to case in the `design-sections` trigger. Queued.
- F11: a `ValueError` from resolving a configured path (NUL) becomes `configuration error`, exit 2. Add a test. Queued.
- F12: the shipped `templates/specflow.json` holds default values. This repo keeps its own config. Queued.
- F13: report an indented or near-miss `Depends on:` line, and a bugfix `Depends on:` out of place, as malformed. Queued.
- Dismissed re-raises (cycle-1 F23: placeholders, bugfix task checks): settled earlier, no action.
