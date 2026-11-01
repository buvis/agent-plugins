---
prd: docs/dev/project-management/specs/00010-split-long-validator-functions/requirements.md
review: 1
date: 2026-11-01
head_sha: 801f0d0c8e22ed565569ef90cd685bc916883e33
codex_thread_id: 01a1942e-a6e8-7110-bd5c-ecfc2b66add8
reviewers: alice,blake,bob,carl,eve
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: unavailable
---

# Review: 00010-split-long-validator-functions

Diff range: `6c16d03d7f5e878a3033de747866c931edcf12bf..801f0d0c8e22ed565569ef90cd685bc916883e33`

codex_rung_guard: fired (6 codex-implemented task(s)); eve unavailable, doubt lens fell back to claude

## Review Summary

This is a standalone run, cycle 1, a full review of `6c16d03..801f0d0`: the spec and intake artifacts plus the six task commits `c623e15` to `801f0d0`. The target is spec 00010's `requirements.md`, with `design.md` as the design doc. Reviewed: six completed tasks, T-001 to T-006. Findings are reported here, not written as tasks.

No reviewer found a 🔴 or a 🟠, and the doubt lens has a non-codex voice, so the loop converges under the autopilot bar; the walkthrough rework below is the tail sweep and no cycle 2 runs. Every reviewer confirmed the split itself: the nine helpers keep the baseline predicates, casts, key-presence guards, diagnostics and call order, and every changed function is at most 37 lines. The findings are test gaps and one portability defect: the characterization suite freezes Python 3.10's `TypeError` wording, so `python3 -m unittest discover -s scripts` fails two subtests on Python 3.14 (F1).

### Agent Status

- Alice: ✅ Available (legacy consensus engine). Claude `claude-opus-5.5`, effort `xhigh`, through Kiro ACP with the read-only `review-readonly` agent (read, grep, glob tools; no shell, no writes). Model and effort were set and confirmed before the prompt and again after the turn (receipt beside her output). The context and diff were inlined, since Kiro's tools cannot read the gitignored `docs/dev/tmp/`.
- Blake: ✅ Available. Same route and receipt check as Alice; PRD-only prompt plus the test-gate block. He compared the split against the main checkout's `scripts/validate.py` as a stand-in baseline; master has not merged 00010, so that copy is the base version.
- Bob: ✅ Available (codex, first run, inlined 177 KB prompt). His `[BOB]` line carries no bullet.
- Carl: ✅ Available on the retry. Copilot backend, `gemini-3.8-flash`. The first run failed with "You have exceeded your monthly quota", exit 1. The one unchanged retry ran after the Copilot quota reset at 2026-11-01 00:00 UTC and exited 0.
- Eve: ⚠️ Unavailable: no route serves Claude Fable 5 here (Kiro offers no Fable model; native Claude was held back until 2026-11-01 per the handoff). Her Claude substitute ran Bob's exact assembled doubt prompt on `claude-opus-5.5` `xhigh` through the same Kiro ACP route, as SKILL.md step 5 prescribes; its output is the `## Eve` section.

### Run notes

- Codex doubt-roster guard: there is no autopilot `state.json`, so the evidence is the handoff ("Codex build session") and the Codex session `rollout-2026-10-31T11-26-54-01a1917f` (`gpt-6-astra`, cwd this worktree), which precede the six task commits (12:13 to 12:20 CET). All six tasks count as codex-implemented, so the doubt lens needed a non-codex voice; the Eve substitute provided it.
- Kiro route: `kiro-cli chat --effort` is ignored headless in this build (every probe reported the model default, `medium` for Opus), so a first Eve-substitute run at `medium` was discarded unread for consolidation, and the first Alice and Blake runs were stopped before they finished. The reviewers then ran through `docs/dev/tmp/review-tools/acp_review.py`, which sets the effort option over ACP and refuses to send the prompt unless model and effort match. Bob's first codex run used a prompt whose repository-root line named `docs/` by mistake; he was re-dispatched with the corrected prompt, and both runs found nothing.
- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). Degraded, not invalid.
- Gate: `review-stage` ran `docs/dev/tmp/review-tools/gate.sh` (Python 3.10.22, exit 0). It could not parse unittest counts, so the lead composed the `Tests:` line from the logs: validator 49, release 54, contract 387, rules 58, review 41, all OK; `scripts/validate.py`, `check_rules.py --area VAL,...,CNV`, `verify_release.py` and `validate_spec.py status --json` exit 0. The line went into the staged context and Blake's prompt before dispatch.
- Fail-first replay (`python3 -m pytest` against `6c16d03`): all 35 characterization tests and the length test pass at base (F11, F12). The lead replayed with unittest in a detached worktree at `6c16d03` on Python 3.10.22: both structure tests fail there (nine helpers missing; 96 and 130 lines), and the 35 characterization tests pass, as REQ-005.2 requires.
- Consolidation corrections (by hand): the script merged Blake's two ordering gaps (`test_validate_characterization.py:194` for the manifest and `:449` for MCP) after suffix stripping; they are split into F4 and F5. Eve's replay row is folded into the replay row F11. Refs renamed from `R1`..`R10` to `F1`..`F12`.
- Lead's checks:
  - Diff scope: `git diff 6c16d03 HEAD` touches only the spec and intake artifacts, `scripts/validate.py` and the two new test files; `scripts/test_validate.py`, `tools/`, `tests/`, `plugins/` and `.github/` are unchanged, and `git diff --check` is clean.
  - Equivalence: an AST comparison of top-level definitions against `6c16d03` shows only `validate_manifest` and `validate_mcp` changed, nine helpers added, nothing removed, and the order of the baseline definitions kept. Reading the diff confirms the moved blocks are verbatim apart from `server_path` becoming the helpers' `path` parameter and the cwd message joined into one f-string with the same text.
  - F1: confirmed. Python 3.14.6 `python3 -B -m unittest discover -s scripts` fails both subtests of `test_uncaught_exception_types_and_messages` (`cannot use 'list' as a set element (unhashable type: 'list')`). The design's testing strategy says interpreter wording is established on the running interpreter, not frozen from another version. The severity stays at Carl's 🟡.
  - F4, F5: confirmed by reading. A `plugin.json` or `mcp.json` link to an outside directory would show the file-type check running before containment; no test has one.
  - F6: confirmed. `scripts/test_validate.py` calls `validate_mcp` directly, and no CLI test sends an MCP failure through `main`.
  - F7: refuted. PR 7's head is `801f0d0` and its `plugins` check passed (run 41196515864).
  - F8: confirmed. `{"a": 1} == {"a": True}` holds, so the current comparison does not pin value types or key order.
  - F9: `git grep '/Users/' master -- docs/dev/project-management` finds the same kind of path in dozens of tracked files.
- No verification-check queue, dispatch rows, contract card or session brief (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [3/5] | 🟡 | `test_uncaught_exception_types_and_messages` hardcodes the CPython 3.10 TypeError text (`"unhashable type: 'list'"` / `"unhashable type: 'dict'"`), while the invalid-UTF-8 case in the same test computes its expected exception at runtime; Python 3.14 rewords it, so the documented local run fails although behavior is unchanged. Derive the expected text on the running interpreter | scripts/test_validate_characterization.py:478 | T-002 | ALICE, CARL, EVE |
| F2 | [1/5] | 🟡 | Two subprocess tests repeat the same CLI call three times: the `[sys.executable, "-B", str(Path(validate.__file__).resolve()), ...]` command, `subprocess.run(..., capture_output=True, text=True, check=False)`, and the `(result.returncode, result.stdout, result.stderr)` tuple. Add a `run_cli(self, *args: str) -> tuple[int, str, str]` helper next to `run_main` | scripts/test_validate_characterization.py:602 | T-003 | ALICE |
| F3 | [1/5] | ⚪ | `_validate_manifest_identity` also performs the top-level field allowlist and `$schema` checks, not just the name checks, so its name understates its job (REQ-001.2 cohesion). Behavior is unaffected | scripts/validate.py:61 | T-004 | BLAKE |
| F4 | [1/5] | ⚪ | The escaping-symlink manifest test points at an outside file; no competing case, such as a link to an outside directory, pins that the regular-file check runs before the containment check (REQ-005.3 ordering evidence) | scripts/test_validate_characterization.py:194 | T-001 | BLAKE |
| F5 | [1/5] | ⚪ | Same gap for MCP: no test pins the regular-file check before the containment check | scripts/test_validate_characterization.py:449 | T-002 | BLAKE |
| F6 | [1/5] | ⚪ | The CLI tests never show a `validate_mcp` diagnostic (with its `#server` path) reaching stderr through `main`, and do not pin the per-plugin order of containment, skills and MCP. `main` is unchanged, so the risk is low, but REQ-005.3 asks for CLI coverage where existing tests lack it | scripts/test_validate_characterization.py:583 | T-003 | BLAKE |
| F7 | [1/5] | ⚪ | REQ-005.4 also asks for CI checks to pass. Only the local Python 3.10 gate is evidenced; the remote PR CI criterion is still unchecked | docs/dev/project-management/specs/00010-split-long-validator-functions/tasks.md:85 | T-006 | BLAKE |
| F8 | [1/5] | ⚪ | The accepted-manifest check compares with `assertEqual`. Python dict equality ignores key order and treats `1`, `1.0` and `True` as equal, so a validator that reordered or changed values in the returned manifest would still pass. REQ-002.1 forbids that kind of normalization | scripts/test_validate_characterization.py:60 | T-001 | EVE |
| F9 | [1/5] | ⚪ | The committed qa-log records the maintainer's absolute home paths (`/Users/bob/.claude/...`) in what looks like a published repo | docs/dev/project-management/intake/processed/00010-split-long-validator-functions/qa-log.md:27 | general | EVE |
| F10 | [1/5] | ⚪ | The structure test only checks the two wrappers and functions that are new compared with the baseline. A baseline helper grown with moved logic would not be checked, although REQ-001.1 covers helpers that are "introduced or expanded" | scripts/test_validate_structure.py:58 | T-006 | EVE |
| F11 | [1/5] | 🟡 | 35 touched tests pass against the pre-change code: test_accepted_manifest_is_returned_intact_without_writes, test_author_field_order_is_insertion_order, test_escaping_manifest_precedes_json_validation, test_field_rejections, test_first_failure_across_checks, test_invalid_utf8_propagates and 29 more | scripts/test_validate_characterization.py | general | mech-check, EVE |
| F12 | [1/5] | 🟡 | 1 touched test passes against the pre-change code: test_refactored_and_new_functions_fit_fifty_physical_lines | scripts/test_validate_structure.py | general | mech-check |

Overlap: F1 is the portability defect three lenses found. F4, F5 and F6 are ordering and CLI evidence gaps under REQ-005.3, and F8 is a REQ-002.1 evidence gap. F3, F7, F9 and F10 are design choices or already evidenced. F11 and F12 are replay facts.

## Alice

Implementation-aware review on the legacy consensus engine, Claude Opus 5.5 at `xhigh` through Kiro ACP, eight read-tool calls. Findings: F2, F1.

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

Blind lens (spec only), Claude Opus 5.5 at `xhigh` through Kiro ACP, 19 read-tool calls. Findings: F3, F4, F5, F6, F7. He reported no Critical, High or Medium issue and found the helpers' predicates, casts, guards, diagnostics and call order equal to the baseline.

B1: pass
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
B17: pass
B18: pass
B19: pass

## Bob

Codex, exit 0, on the inlined prompt; no issues found. FIX, VERIFY and KNOWN are empty.

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

Copilot `gemini-3.8-flash`, exit 0 on the one retry after the quota reset. Findings: F1. He ran the worktree gate and the validator suite on Python 3.14 and 3.10 himself; `git status --ignored` afterwards showed no new files under `scripts`, `plugins`, `tools` or `tests`.

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

## Eve

Claude substitute for Eve: Bob's exact assembled doubt prompt on Claude Opus 5.5 at `xhigh` through Kiro ACP, no tool calls (everything was inlined). Findings: F1, F8, F9, F10, F11. FIX holds F8. VERIFY holds F1, with the check to run it on Python 3.14, and F9, with a `git grep`; both were run by the lead (run notes). KNOWN holds F10 and the replay rows, each with its design or tooling reason.

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

Verdict: 12 findings

Tests: 589 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-11-01)

The lead ruled on each finding under the developer's standing authorization; no ruling edits an approved artifact. The cycle has no 🔴 or 🟠, so the rework below is the tail sweep and no cycle 2 runs. Every changed or added test must still pass on the original validators at `6c16d03` (REQ-005.2), on Python 3.10 and on 3.14.

- F1: fix. The test takes the expected `TypeError` from evaluating the validator's own membership test, `transport in {"streamable-http", "sse"}`, on the running interpreter, the same way the UTF-8 case derives its error.
- F2: fix. A `run_cli(*args)` helper beside `run_main` returns the exit code and both streams; the two subprocess tests use it.
- F3: accepted (ledger). The approved design's helper table names `_validate_manifest_identity` and gives it exactly this check sequence; a rename needs a design edit and reapproval for no behavior gain.
- F4 and F5: fix, one test each. A `plugin.json` link to an outside directory reports `missing required manifest`, and an `mcp.json` link to an outside directory reports `must be a regular file`, so the file-type check is pinned before containment.
- F6: fix. One CLI test with a valid manifest walks one plugin through its later failures: an escaping link is reported before a broken skill, a broken skill before an MCP failure, and the MCP failure reaches stderr with its `#server` path and exit 1.
- F7: refuted (ledger). PR 7's `801f0d0` head is green (run 41196515864); the completion box is ticked after this review records its result.
- F8: fix. The accepted-manifest test also compares `json.dumps` of the result with the written file text, and its nested case gains `1.0` and `true` values, so key order and value types are pinned.
- F9: accepted (ledger). Existing repository practice; not a credential; intake history is outside this spec.
- F10: accepted (ledger). The design limits the check to the two validators and new names; the AST comparison shows no baseline helper changed.
- F11: accepted as a fact (ledger), required by REQ-005.2.
- F12: refuted (ledger), a pytest `subTest` artifact; the unittest replay fails both structure tests at base.
