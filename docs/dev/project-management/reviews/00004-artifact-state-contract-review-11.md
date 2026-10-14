---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 11
date: 2026-10-14
head_sha: c4ff602c14c71b1e53aa64f4119c11c6705a9d59
codex_thread_id: 01a13bf6-f975-7ae0-8896-4cf7e6208c2c
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `7897f61dd8afd956da8cb4d5496dd140930d75ee..c4ff602c14c71b1e53aa64f4119c11c6705a9d59`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 11. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-10 rework incrementally (`7897f61..c4ff602`): the fix commit `6c8f842` (`state.py`, `status.py`, `checks.py`, `design.md`, CHANGELOG, three test files), the cycle-10 records `eef6aae`, `7c2df40` and `35edf56`, and the re-approvals `c4ff602` (qa-log, ledger). The target is spec 00004's `requirements.md`, with `design.md` as the design doc. All ten tasks are complete. Findings are reported here, not written as tasks.

All six cycle-10 fixes hold: F1, F2, F4, F5, F6 and F7 are resolved in the code. Alice verified each by reading and through its regression test. The lead's unittest replay at `7897f61` fails all six regression tests and passes only the no-false-positive guard, and the contract suite passes under Python 3.10.22 (304 OK). Carl found nothing. Blake's blind pass found one new ⚪ and three re-raises the ledger absorbs.

This cycle's findings sit in the new reverse-traceability check (cycle-10 F5). Alice and Bob each found the same class of defect in its citation grammar (F1: stray digits and whitespace produce bogus `cites N` errors, and an ID typo such as `REQ-0010` silently passes as `REQ-001`), and Alice showed by mutation that two of its branches are untested (F2). The lead confirmed both.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run, on the resumed cycle-10 thread, refused for lack of input: both read tools stopped with `sandbox-exec: sandbox_apply: Operation not permitted`, as in cycles 2 to 10. This time the refusal was prose only, with no `[BOB]` line at all, so the three-pattern refusal rule did not match literally; the output had no issue line and no verdict line, which is the malformed-output trigger, and the one retry was the inlined prompt (214 KB: context, diff, persona with the two edits) without `--resume-thread`. The first output is kept at `docs/dev/tmp/bob-output-00004c11-first.txt`. The `codex_thread_id` above is the retry's thread.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run)
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex: the spec has no frontmatter, so the default applies; with no state file there is no codex-implemented task record to fire the guard)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid. Same as cycles 3 to 10.
- Gate: `review-stage` ran the five CI steps (exit 0) but could not parse the unittest counts. The counts below come from that run's logs: `scripts` 12 OK, release 52 OK, contract 304 OK; `validate.py` and `verify_release.py` exit 0.
- Fail-first replay (`python3 -m pytest`): 7 touched tests ran, 6 fail at base, 1 passes: `test_requirement_coverage_accepts_every_held_citation`. The lead's unittest replay in a worktree at `7897f61` with HEAD's test files copied in agrees (6 failures, 1 pass). That test is the no-false-positive guard for the F5 fix and passes at base by design, as the cycle-10 outcome said. It is F4 below.
- Python 3.10: the lead re-ran the contract suite under 3.10.22, the version CI pins: 304 OK.
- Settled-decisions ledger: the script auto-dismissed three Blake findings. The lead checked each against the ledger; all three match a settled entry (below). For the bugfix line it printed the placeholder entry's reason again, as in cycles 8 to 10; the ledger's own entry names 00006. No wrong dismissal this cycle.
- Consolidation corrections (by hand): the script merged four `checks.py` findings into one row ("matched only after suffix stripping"): Alice's untested-branches finding (`:528`) with Alice's and Bob's three grammar findings (`:507`, `:508`). Those are two defects with two fixes, so the lead split them into F1 (grammar, Alice and Bob, [2/4]) and F2 (untested branches, Alice, [1/4]). The replay `[MECH]` row was added as F4. Refs were renumbered from the script's `R1`..`R4`, severity order kept within each consensus level.
- Carl's shell: his copilot run executed the suite without `PYTHONDONTWRITEBYTECODE`, which wrote `__pycache__` into the package and failed `verify_release.py`; it then ran `find . -name __pycache__ -exec rm -rf {} +` in the repo and re-ran the check clean. Only ignored bytecode folders were touched, and `git status` is clean afterwards.
- Lead's checks:
  - F1, confirmed by calling `unheld_citations` directly. Conforming lines pass: `REQ-001, REQ-002`; `REQ-001 criteria 1, 2; REQ-002 criterion 1`; `REQ-001.2`; the cross-spec `00004 WF-004 criterion 8`; Kiro's `1.1, 2.1`. Stray text fails: `criteria 1 and 2` and `criteria 1-2` cite `2`; `(see design §3)` cites `3`; `(T-003 covers the rest)` cites `T-003`; `decided 2026-10-14` cites `2026`, `10` and `14`; `criteria 1,  2` with two spaces, a tab, or ` ,` cites `2`. Typos pass: `REQ-0010` and `REQ-001a` beside a defined `REQ-001` are read as `REQ-001` (the ID alternative has no trailing boundary), while `traced_ids` ignores both tokens. The contract (`references/artifact-contract.md:98,105,122`) prescribes comma or semicolon lists only, so every false positive needs a line outside the contract grammar; the false negative does not.
  - F2, confirmed by two mutation runs in a worktree at `c4ff602`: with the `CROSS_SPEC.sub` strip removed, 304 OK; with the `\b[0-9]+` alternative and the `_` strip removed, 304 OK.
  - F3, confirmed by `rg`: `state.py:71`, `status.py:250`, and `deps.py:137` (`error.strerror or "cannot be read"`).
  - F5, confirmed: `wc -l` gives 790.
  - F6, confirmed by reading `numbers.py:79-95`: each kind is grouped on its own. The design row for `number-clashes` says the same ("two intake items or two spec folders"), so this is a gap between the design and INT-001.4, not between the code and the design.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/4] | 🟡 | The `CITATION` grammar of the new reverse-traceability check tokenizes loosely, unlike `traced_ids`. False positives: any bare number on a `Requirements:` or `Acceptance criteria:` line of a REQ-numbered spec is read as a citation, so `REQ-001 criteria 1 and 2`, `criteria 1-2`, `(see section 2)`, a task ID such as `T-003`, a date, and `criteria 1,  2` with two spaces (or a tab) each report `cites N, which requirements.md does not hold`. False negative: the ID alternative has no trailing boundary, so `REQ-0010` or `REQ-001a` beside a defined `REQ-001` is read as `REQ-001` and the typo passes. One fix covers all of it: split the value on `[,;\s]+` and full-match each token as `traced_ids` does, taking the bare-number form only when `held` has numeric keys (Kiro), with a regression test per case. Confirmed by the lead's direct probe | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:507 | T-026 | ALICE, BOB |
| F2 | [1/4] | 🟡 | `unheld_citations` has two untested branches. Removing the cross-spec strip (`CROSS_SPEC.sub`), which would turn `00004 WF-004 criterion 8` into bogus `cites 00004` and `cites WF-004` errors, fails no test; removing the Kiro numeric form (`1.2`) and the `_..._` wrapper also fails no test. Add a fixture task with a cross-spec citation that must produce no `requirement-coverage` finding, and a Kiro-numbered spec citing an unheld `9.1`. Confirmed by the lead's mutation runs (304 OK each) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:528 | T-026 | ALICE |
| F3 | [1/4] | 🟡 | The `cannot read: {strerror}` else `cannot be read` expression is written twice (`state.py:71`, `status.py:250`), and `deps.unreadable` (`deps.py:137`) carries a third variant. One small helper, for example `read_failure(error: OSError) -> str` in `state.py`, would replace the copies with no behavior change. A quality item | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:250 | T-026 | ALICE |
| F4 | [1/4] | 🟡 | 1 touched test passes against the pre-change code: `test_requirement_coverage_accepts_every_held_citation`. It is the no-false-positive guard for the F5 fix and passes at base by design; the other six touched tests fail at base under both pytest and unittest. Recommend dismissing with a ledger entry | tests/specflow/contract/test_checks.py | general | mech-check |
| F5 | [1/4] | ⚪ | `checks.py` is 790 lines against the 800-line limit; any further check pushes it over. The `CITATION` and `unheld_citations` block (about 40 lines) could move to `spec_text.py`, beside `traced_ids` and `CROSS_SPEC`, which it already uses | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:505 | T-026 | ALICE |
| F6 | [1/4] | ⚪ | `number_clashes` compares intake items with intake items and spec folders with spec folders, never a new intake item with a spec folder of the same number that has no processed item, so `validate --phase intake` cannot catch that clash after the fact (INT-001.4). `next-number` does count those folders, so only a concurrent claim slips through. The design row reads as the code does, so this is a design gap | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:79 | general | BLAKE |

Overlap: F1 and F2 both sit in `unheld_citations`, and one rework closes both: the tokenizer fix of F1 plus the two fixtures of F2. F3 and F5 are quality items on code this rework added. F6 concerns code this rework did not touch.

### Auto-dismissed (ledger)

Dismissed by `consolidate_findings.py --ledger-dismiss BLAKE` against `00004-artifact-state-contract-ledger.json` and kept after the lead's check:

- [BLAKE] 🟠 VAL-001.8 / ART-001.10 / VAL-001.3 placeholder detection not implemented (`checks.py:369`): settled as cycle-1 F23, deferred by design to 00005 T-071.
- [BLAKE] 🟠 VAL-001.4 bugfix task validation missing (`checks.py:481`): settled as cycle-1 F23, deferred by design to 00006. (The script printed the placeholder entry's reason for this line, as in cycles 8 to 10; the ledger's own entry names 00006.)
- [BLAKE] 🟡 unfiltered `validate` and `status` run `specs-folder` and `number-clashes` outside the spec folder (`checks.py:732`): accepted in the cycle-10 walkthrough (cycle-10 F10): VAL-001.8 requires the scans and they read names only. Blake raised it one level and added `status`; the design has `status` run both checks, so the reason still holds.

## Alice

Implementation-aware review of the cycle-10 rework (legacy consensus engine). She verified F1, F2, F4, F5, F6 and F7 resolved, ran the contract suite (304 OK), and ran `status --json` over the repo's nine specs (no new blockers, empty `problems`). She ran two mutation probes on a scratch copy. Findings: F1 (her stray-digit half), F2, F3, F5.

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

Blind lens (spec only). He read the helper source and the shipped schemas, ran the 304 contract tests, and probed a scratch repo for placeholders. He judged hashing, invalidation, reconcile, the guarded state write, config path refusal, the code baseline, spec dependencies, cross-spec references and read-only status and validate as conforming. B15 and B16 pass vacuously (Phase 3 tasks only); B13 passes because no migration exists to reverse. Findings: F6, plus three re-raises auto-dismissed above.

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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input. The retry raised the two grammar defects merged into F1 (the `REQ-0010` prefix match and the comma whitespace). FIX holds those two items with their regression tests; VERIFY and KNOWN are empty.

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

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0. He read the context and diff, ran the suites and `validate` over every spec, and found no issues.

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

Verdict: 6 findings

Tests: 368 passed, 0 failed, 0 skipped (suite run this cycle)
