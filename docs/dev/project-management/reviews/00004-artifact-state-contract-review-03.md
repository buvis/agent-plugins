---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 3
date: 2026-10-12
head_sha: d293581f2e08076ed06cdcea545888922a9c47ba
codex_thread_id: 01a1309a-25e9-7002-afdf-676f36096588
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `4efec99f8484ba5918866831bdfb19979d01e30d..d293581f2e08076ed06cdcea545888922a9c47ba`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 3. There is no autopilot `state.json` and no wip PRD. It reviews the cycle-2 rework incrementally (`81a2d09..d293581`). The target is spec 00004's `requirements.md`, with `design.md` as the design doc and `tasks.md` as the task source. Findings are reported here, not written as tasks.

Every cycle-2 fix holds. Alice checked each against the code: F1+F6, F2, F3+F11, F4, F5, F7, F8, F10, F12, F13 and F14. She found no regression. The new findings come mostly from Blake's blind pass, which found spec gaps that earlier cycles did not raise.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His run on the resumed thread refused for lack of input: codex's sandbox blocked file reads with `sandbox_apply: Operation not permitted`, as in cycle 2. The refusal is kept at `docs/dev/tmp/bob-output-00004c3-first.txt`. The retry inlined the context and the diff (213 KB) and ran without `--resume-thread`.
- Carl: ⚠️ Unavailable. The copilot backend (`gemini-3.8-flash`) exited 1 with "No authentication information found", on the first run and on the one retry. This is a one-off runtime failure (exit 1, not 4), so nothing was latched. It is the same failure as cycle 2.
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no codex-implemented tasks are recorded)

### Run notes

- pack: failed (engram pack exit 1: `sqlite3.OperationalError: attempt to write a readonly database`). The review is degraded, not invalid.
- Gate: `review-stage` ran the full gate (exit 0) but could not parse the unittest counts. The counts below come from suite runs this cycle at HEAD: contract 257 OK, release 52 OK, `scripts` 12 OK.
- Fail-first replay: the pytest replay flagged 3 touched tests as passing against base. The lead re-ran them under unittest in a worktree at `4efec99`. All 3 fail there, with 5 subtest failures in total. Each test loops with `subTest`, and pytest without the subtests plugin reports those failures as passes. This is the same artifact as cycle-2 F9. Alice reached the same conclusion by reading the tests (F6).
- Consolidation corrections (by hand):
  - The script did not parse Bob's `- [BOB] ...` bucket lines, so his findings are added by hand (F5, F6, F7, and one dismissal).
  - The script merged Blake's two F23 re-raises (placeholders, and bugfix task checks) into one row. Both are dismissed below.
  - Blake's T-027 finding is merged with Bob's KNOWN T-027 line as F7.
- Lead's checks:
  - F1 confirmed by reading `state.py:124-147`. `own_status` derives an artifact's status from its own record and file. A downstream approval goes stale only through a recorded `stale` or through the current upstream status, and no upstream hash is bound into the approval. This is the gap that cycle-1 F26 left open: `stale` is sticky only once `reconcile` has recorded it.
  - F4 confirmed by reading `README.md:30-33`.
  - F5 confirmed by reading `checks.py:490-500` against `canonical.py:75`. The continuation branch runs before the `PROGRESS` match, so a nested `Outcome:` or `Exception:` line gets a "hashed" warning, though `canonical` drops it from the hash. The result is a wrong warning only, never an error.
- No verification-check queue was written, and no dispatch rows were opened (standalone run).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/3] | 🟠 | WF-002.6 and STATE-002.4 hold only if `reconcile` runs between the upstream edit and the upstream re-approval. Approvals bind no upstream hash. If requirements are edited and re-approved with no `reconcile` in between, design and tasks read `approved` again (Blake ran it, and the lead confirmed it by reading). No doc states the ordering | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:144 | T-023 | BLAKE |
| F2 | [1/3] | 🟡 | `status` and `validate` crash with `UnicodeEncodeError` on a non-UTF-8 stdout (`PYTHONIOENCODING=cp1252`, a cycle path with "→"). `emit` uses `ensure_ascii=False`, and `main` does not catch the error. This is the Windows piped-output case | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:83 | T-026 | BLAKE |
| F3 | [1/3] | 🟡 | `status` output embeds the absolute machine path in `StateError` blocker reasons (malformed `.specflow.json`). This breaks "same result on every host" (STATE-003.3, STATE-001.5) and leaks a local path | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:61 | T-026 | BLAKE |
| F4 | [1/3] | 🟡 | README Security still says "no scripts ... or persistent data". The package now ships `validate_spec.py`, which runs git subprocesses and writes `.specflow.json` (confirmed by reading) | plugins/specflow/README.md:32 | general | BLAKE |
| F5 | [1/3] | 🟡 | `progress_fields` warns that a nested `Outcome:` or `Exception:` under an open field "continues" it and is hashed, although `canonical` drops progress fields at any depth. It is a wrong warning only (confirmed by reading) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:490 | T-026 | BOB |
| F6 | [1/3] | 🟡 | The fail-first replay flagged `test_cross_spec_reference_matches_either_declared_form`, `test_each_unsupported_form_is_named` and `test_line_ending_churn_is_no_drift` as passing against base. Resolved by the lead's unittest replay at `4efec99`: all 3 fail (5 subtests). Recommend dismissing | tests/specflow/contract/test_checks.py:315 | T-026 | BOB, mech-check |
| F7 | [2/3] | 🟡 | T-027's Kiro IDE link trial is still pending (known item cycle-2 F16). New part: the risk fallback ("a configured specs folder is invisible to Kiro's spec panel") is in an intake note only, not in the shipped plugin docs | plugins/specflow/README.md:6 | T-027 | BLAKE, BOB |
| F8 | [1/3] | ⚪ | The F12 fix covers only five-digit spec numbers. Requirement ID patterns still use `\d{3}`, which accepts non-ASCII digits | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/spec_text.py:9 | T-026 | ALICE |
| F9 | [1/3] | ⚪ | Style: the parenthesised `"stale"` return in `own_status` with a trailing comment. It could merge into the `status == "stale"` branch | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:130 | T-024 | ALICE |
| F10 | [1/3] | ⚪ | No test covers the new-file branch of `write_guarded` (`0o666 & ~umask`) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:42 | T-025 | ALICE |
| F11 | [1/3] | ⚪ | `design-sections` runs only when the title starts with `# Design: `. A retitled design skips the keep-every-section rule (ART-001.10) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:356 | T-026 | BLAKE |
| F12 | [1/3] | ⚪ | `next_number` ignores items inside a numbered group folder and entries placed directly under `<root>/intake/` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:21 | T-029 | BLAKE |
| F13 | [1/3] | ⚪ | The `specs-folder` ignore probe `.specflow-probe` is caught by a repo-wide `.*` rule (a false "ignored"). The shipped JSON schemas use unanchored `pattern`s, while the helper uses `re.fullmatch` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:648 | T-028 | BLAKE |
| F14 | [1/3] | ⚪ | Unspecified extras in the status output: the `intake` and top-level `problems` arrays, and `nextTask` nulled on any hold (STATE-003.1 does not state this) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:203 | T-026 | BLAKE |

Overlap: F2 and F3 are both portability of the `status` output. F4 and F7 are both README text.

### Auto-dismissed (ledger)

No ledger file exists for this spec. These were dismissed by hand against the settled minutes of cycles 1 and 2:

- [BLAKE] 🟠 VAL-001.8 / VAL-001.3 placeholder and unfilled design template checks missing: settled as cycle-1 F23, deferred to 00005 T-071.
- [BLAKE] 🟠 VAL-001.4 bugfix task order and `2.x`/`3.x` coverage missing: settled as cycle-1 F23, deferred to 00006.
- [BOB] ⚪ KNOWN: runtime skill is still a shell: settled as cycle-2 F15 (00006 scope).

## Alice

Findings: F8, F9, F10. She verified every cycle-2 fix in the code and found no regression. She read the three replay-flagged tests and judged them a `subTest` artifact, not tautologies.

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

Blind lens (spec only). He ran the contract tests (257 OK), the release tests (52 OK) and `validate.py`. He judged these conforming: the canonical hash rules, the state schema, config path refusal, `write_guarded`, recovery mode, the dependency graph, cross-spec references, the code baseline and drift, marker gating, number clashes and the Sources check, and the status schema. Findings: F1, F2, F3, F4, F7 (merged), F11, F12, F13, F14, plus two F23 re-raises (dismissed above).

B1: fail
B2: pass
B3: fail
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

Codex, exit 0, after one retry (inlined). His first run, on his resumed thread, refused for lack of input (the sandbox blocked file reads). The retry wrote FIX/VERIFY/KNOWN buckets. FIX: F5. VERIFY: F6 (three items, resolved by the lead's replay). KNOWN: F7 (merged), and the SKILL.md shell (dismissed as F15).

R1: fail
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

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 14 findings

Tests: 321 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-12)

- F1: bind the upstream hash. Each approval records `upstreamSha256` of the artifact it was approved against, and status reads `stale` when that no longer matches, whatever order `reconcile` ran in. A record without the field has no binding. Schema, design and tests change, so the design and tasks need re-approval. Queued.
- F2: ASCII-safe output. JSON keeps the default `ensure_ascii=True`, and human messages use `->` in place of "→". Add one cp1252 test. Queued.
- F3: path-bearing error messages (`StateError` and its siblings) cite paths relative to the repository root. Add one test. Queued.
- F4: the README Security section states the real boundary: an optional stdlib helper that runs local `git` read commands and writes only `.specflow.json` (through `reconcile`), with no network, MCP or auth. Queued.
- F5: `progress_fields` checks for a progress field before the continuation branch. Add one nested-field regression test. Queued.
- F6: dismissed. It repeats the cycle-2 F9 decision: the lead's unittest replay at `4efec99` shows all 3 tests fail at base.
- F7: ship the caveat now. One line in the plugin docs says a non-default specs folder may not appear in Kiro's spec panel, pending the T-027 trial. The T-027 trial stays open (developer-owned). Queued.
- F8: `[0-9]{3}` in place of `\d{3}` in the requirement ID patterns, with a test. Queued.
- F9: fold the restored-`missing` return into the `stale` branch of `own_status`. Do it inside the F1 rewrite. Queued.
- F10: a test for the new-file mode branch of `write_guarded` (it restores the umask). Queued.
- F11: run `design-sections` on the design artifact whatever its title. Check Kiro-native designs for new findings. Queued.
- F12: `next_number` also scans items inside numbered group folders and entries placed directly under `<root>/intake/`. Queued.
- F13: a non-dot probe name for the `specs-folder` ignore check, and `^...$` anchors on the shipped JSON schema `pattern`s. Queued.
- F14: document the `intake` and `problems` arrays and `nextTask: null` on hold in the design. Do it together with F1's design edit. Queued.
- Dismissed re-raises (F23 placeholders and bugfix checks; F15 runtime skill): settled earlier, no action.

### Outcome (2026-10-12)

Every queued item is applied:

- F1 + F9: `hash --json` returns `upstreamSha256` for a canonical artifact, and `stale_causes` stales an approval whose bound upstream hash no longer matches, naming that upstream artifact as the cause. A record without the field binds nothing. The schema gains the field. `own_status` folds the restored-`missing` case into the `stale` branch.
- F2: JSON uses ASCII escapes, the cycle path uses `->`, and stdout uses `backslashreplace`, so text that quotes an artifact cannot crash either. The last part goes beyond the minutes, for the same Windows case.
- F3: `StateError` carries `path` and a path-free `reason`. The `status` blocker uses the reason plus a repository-relative `reference`. Going beyond the minutes, the same class was fixed in `deps.py`, where an `OSError` text carried the absolute path of an unreadable target.
- F4 + F7: the README Security section states the real boundary. `artifact-contract.md` carries the Kiro spec-panel caveat. T-027 stays open.
- F5: `progress_fields` tests for a progress field before the continuation branch.
- F8: every `\d` in the spec grammar (`spec_text`, `state`, `canonical`, `checks`, `status`) is now `[0-9]`. That covers the whole class, not just the 3-digit IDs.
- F10: a new-file mode test under a set umask.
- F11: `design-sections` also runs when the design holds a template-only section. `Overview`, `Architecture` and `Open decisions` do not count, since Kiro designs and marker sections use them.
- F12: `next_number` counts items inside a numbered group folder, and folders placed straight under `intake/`. The existing rule that items deeper than one group do not count stays, pinned by its own test.
- F13: the ignore probe is `specflow-probe`, and every shipped schema pattern is anchored and ASCII.
- F14 and the design text of F1, F2, F3, F11, F12 and F13 are recorded in the qa-log. The design and tasks approvals are now stale and need the developer's re-approval.
- Tests: 14 new tests, and 3 existing ones extended. Fail-first: run against the old code, every new regression test fails. The F10 coverage test passes, as expected for a test of behavior that was already right.
- Checks: 271 contract tests on Python 3.14 and 3.10, 52 release tests and 12 validator tests, all OK. `validate.py` exits 0. `verify_release.py` ran after the commit.
- Lint: `ruff check` reports 6 findings (SIM102, ISC004 ×3, SIM117 ×2), all present at `2eaa406` and in lines this rework did not touch. They are left as they are, and reported here.
