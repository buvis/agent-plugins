---
prd: docs/dev/project-management/specs/00002-package-boundary/requirements.md
review: 1
date: 2026-10-07
head_sha: 5135c987295a93b69160c8d60693b3345a489580
codex_thread_id: 01a1173f-3ccf-7a73-93a2-4f8e148e929c
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00002-package-boundary

Diff range: `accde1dc1a62d9f0b9212938e9aa137001467357..5135c987295a93b69160c8d60693b3345a489580`

codex_rung_guard: not fired

## Review Summary

Standalone run (no autopilot `state.json`). Spec 00002 is a specflow spec, not a wip PRD, so `requirements.md` was the review target, with `design.md` attached as the design doc and `tasks.md` as the task source. Reviewed: 6 completed tasks (T-001 to T-006). Findings are reported here, not written as tasks.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, first run; format warning, see his section)
- Carl: ✅ Available (backend=copilot model=gemini-3.8-flash)
- Eve: ⏸️ Disabled (doubt_reviewer resolved to codex; no codex-implemented tasks recorded)

### Run notes

- pack: failed (engram pack exit 1: repo not registered with gita). The review ran without it, so it is degraded but valid.
- Gate: `review-stage` ran the gate (exit 0) but could not parse unittest counts, so the counts below come from a suite run this cycle (9 + 23 tests).
- Final-commit check: in a fresh clone of 5135c98 with `-B` (no bytecode): `scripts` tests 9 OK, the validator printed `Validated 2 plugin package(s) and 2 skill(s).`, release tests 23 OK, and `verify_release.py` printed `Verified plugins/specflow.`. This settles Bob's VERIFY item (R19) and the evidence half of R14.
- Consolidation correction (by hand): `consolidate_findings.py` merged Bob's "empty compat manifest passes" (verify_release.py:135) into Blake's "no release packaging step" (verify_release.py:186). These are different defects. Bob's finding belongs with Blake's "compat manifest need not carry name/version" (same line, same defect). Rows R1 and R6 below reflect the corrected merge.
- Alice cited `tasks.md:299`, but that file has 106 lines. Her finding is about completion criterion 2, which is `tasks.md:105`, so the citation was corrected.
- Carl wrote `plugins/specflow/dummy.txt` while probing `check_clean`. It was gone when the run ended (`git status --ignored -- plugins` is clean).
- Lead's checks: R1 is confirmed (`compat.items()` only checks the keys that are present; design.md:185 asks for no more, so this is a gap in the design rather than an implementation bug). R3 is confirmed (3 of the 6 markers contain `/` and can never match a single name). R4 is confirmed (the test covers 1 of 6 markers; design.md:270 asks for a `subTest` loop). Carl's two 🟠 are high for what they are: R3 is a dead check on a branch the content scan still covers, and R4 is a test gap.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟠 | Compat manifest check only compares present keys: an empty `{}` or one missing `name`/`version` passes, leaving REL-001.2 unenforced. Require the root metadata fields; add empty-object and deleted-field regression tests. | tools/specflow/verify_release.py:135 | T-004 | BLAKE, BOB |
| R2 | [3/4] | 🟡 | Guard test `test_no_specflow_manifest_outside_the_package` passes against pre-change code (by design per T-001); also brittle on a deleted tracked file or unparseable tracked `plugin.json` | tests/specflow/release/test_boundary.py:23 | T-001 | ALICE, BOB, mech-check |
| R3 | [1/4] | 🟠 | Multi-segment markers in FORBIDDEN_MARKERS (`tools/specflow`, ...) can never match a single path component in `check_name`, so that branch is dead for them | tools/specflow/verify_release.py:149 | T-005 | CARL |
| R4 | [1/4] | 🟠 | `test_rejects_marker_in_a_folder_name` tests one marker instead of a `subTest` loop over FORBIDDEN_MARKERS as design.md:270 specifies | tests/specflow/release/test_verify_release.py:274 | T-005 | CARL |
| R5 | [1/4] | 🟡 | REL-001.1 / PKG-002.2 have no packaging step or release-process statement; only the verifier exists | tools/specflow/verify_release.py:186 | T-004 | BLAKE |
| R6 | [1/4] | 🟡 | PKG-002.4 enforced only by exact names: `parity-report.md`, `evals.json`, maintainer prompts, or host launchers pass unless they hit a marker/name/pattern | tools/specflow/verify_release.py:40 | T-005 | BLAKE |
| R7 | [1/4] | 🟡 | `os.walk` silently skips directory enumeration errors, so the forbidden scan can pass without inspecting a subtree; add `onerror` collecting failures plus a test | tools/specflow/verify_release.py:157 | T-005 | BOB |
| R8 | [1/4] | 🟡 | Forbidden-content tests derive fixtures from production constants; deleting an entry from a denylist also deletes its test case | tests/specflow/release/test_verify_release.py:247 | T-005 | BOB |
| R9 | [1/4] | 🟡 | `line.split(chr(9), 1)` instead of `'\t'` | tools/specflow/verify_release.py:104 | T-004 | CARL |
| R10 | [1/4] | 🟡 | `check_manifests` builds `[*errors, ...]` copies on early returns | tools/specflow/verify_release.py:131 | T-004 | CARL |
| R11 | [1/4] | ⚪ | Error paths inconsistent: `check_clean` prints repo-relative, `check_forbidden`/`check_manifests` print absolute | tools/specflow/verify_release.py:122 | T-004 | ALICE |
| R12 | [1/4] | ⚪ | `test_reports_unreadable_file` relies on `chmod(0)`; fails when run as root | tests/specflow/release/test_verify_release.py:763 | T-005 | ALICE |
| R13 | [1/4] | ⚪ | Probe record claims Codex reads both marketplace paths; only `.agents/plugins/marketplace.json` was exercised | docs/dev/project-management/intake/processed/specflow/00002-package-boundary/host-loading-probe.md:94 | T-006 | ALICE |
| R14 | [1/4] | ⚪ | Completion criterion 2 checked on evidence from the T-005 commit, not the final commit (the lead's fresh-clone run at 5135c98 now backs it; the record in tasks.md still cites T-005) | docs/dev/project-management/specs/00002-package-boundary/tasks.md:105 | general | ALICE |
| R15 | [1/4] | ⚪ | Symlinked files skipped in the content scan; escapes still caught by `validate_containment` | tools/specflow/verify_release.py:171 | T-005 | BLAKE |
| R16 | [1/4] | ⚪ | No CI run yet (no PR); "CI SHALL fail" unproven on a real runner | .github/workflows/validate.yml:33 | T-005 | BLAKE |
| R17 | [1/4] | ⚪ | Probe evidence is a manual record; Kiro passed on a second attempt after an unrecorded terminal fix | docs/dev/project-management/intake/processed/specflow/00002-package-boundary/host-loading-probe.md:45 | T-006 | BLAKE |
| R18 | [1/4] | ⚪ | Content-marker scan is case-sensitive substring; variants like `catch-up` not caught | tools/specflow/verify_release.py:49 | T-005 | BLAKE |
| R19 | [1/4] | ⚪ | VERIFY: final-commit tests and release verification pass in a fresh checkout (run by the lead at 5135c98: all four pass) | N/A | general | BOB |
| R20 | [1/4] | ⚪ | KNOWN: shell workflow skill remains a placeholder, deferred to 00006 by ruling D1 | plugins/specflow/skills/spec-workflow/SKILL.md:6 | T-002 | BOB |

Overlap: R3, R6, and R18 are all about how the forbidden-name matching works and can be fixed in one pass.

## Decisions (walkthrough 2026-10-09)

- R1: applied. Require `name` and `version` in the Claude manifest, add empty-manifest and missing-field tests, and update design.md:185.
- R3: applied. Check slash markers against the path inside the package, and add a test.
- R4 + R8: applied. Tests keep their own copy of the required entries and check that each code list contains every one (and refuses it); the folder-name test loops over all six markers; update design.md:270.
- R7: applied. Add an `os.walk` `onerror` handler that records each failure, plus a test.
- R5: applied. In requirements.md, mark REL-001.1 and PKG-002.2 as "verified here, built by T-065 (00001)".
- R2: applied. Guard test skips a deleted tracked file and reports a broken tracked `plugin.json` as a named failure.
- R9: applied. Write `'\t'` instead of `chr(9)`.
- R11: applied. Print every verifier error path relative to the repository root.
- R13: applied. Change "(Codex reads both)" to say only `.agents/plugins/marketplace.json` was tested.
- R14: applied. Record this review's fresh-clone run at 5135c98 under completion criterion 2.
- R16: applied. Pushed `feature/specflow` (and `master` as the PR base), opened draft PR https://github.com/buvis/agent-plugins/pull/1; CI `plugins` job passed (run 37981347770).
- R6: deferred. Broader forbidden-name patterns risk refusing innocent files. Home: this file, with a pointer in the 00001 qa-log (Deferred to T-065).
- R10: rejected. The early-return copies don't mutate anything, which matches the immutability rule.
- R12: deferred. Only fails when the suite runs as root; CI is not root. Home: this file.
- R15: rejected. Escaping links are already caught by `validate_containment`.
- R17: deferred. Needs the developer to say what the Kiro terminal fix was. Home: this file, with a pointer in the 00008 qa-log (Deferred to the host tests).
- R18: deferred. Case-insensitive matching risks refusing innocent files. Home: this file, with R6 in the 00001 qa-log pointer.
- R19: resolved. The lead's fresh-clone run at 5135c98 passed all four commands.
- R20: settled. The placeholder skill belongs to 00006 (ruling D1).

## Alice

[ALICE] ⚪ Guard test `test_no_specflow_manifest_outside_the_package` passes against the pre-change code (the mech replay flag); by design, but brittle on a deleted tracked file or unparseable tracked `plugin.json`. | File: tests/specflow/release/test_boundary.py:23 | Task: 1
[ALICE] ⚪ Error paths are inconsistent: repo-relative in `check_clean`, absolute in `check_forbidden` and `check_manifests`. | File: tools/specflow/verify_release.py:122 | Task: 4
[ALICE] ⚪ `test_reports_unreadable_file` relies on `chmod(0)`; fails as root. | File: tests/specflow/release/test_verify_release.py:763 | Task: 5
[ALICE] ⚪ Probe record's "(Codex reads both)" is only half evidenced. | File: docs/dev/project-management/intake/processed/specflow/00002-package-boundary/host-loading-probe.md:94 | Task: 6
[ALICE] ⚪ Completion criterion 2 evidence is from the T-005 commit, not the final commit. | File: docs/dev/project-management/specs/00002-package-boundary/tasks.md:105 | Task: general

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

Blind lens (spec only). Blake ran the release tests (23 OK), `scripts/validate.py` and `verify_release.py` himself. He did not run `claude plugin validate --strict` and did not re-run any host probe. His findings are R1 (merged), R5, R6, R15, R16, R17, and R18 above.

B1 to B19: pass (all 19).

## Bob

Codex, first run, exit 0, no retry. (format warning) His issue lines carried a leading `- ` list marker, so `consolidate_findings.py` dropped them. A copy with that prefix stripped (`docs/dev/tmp/bob-output-00002-c1-normalized.txt`) was consolidated instead; no words changed. FIX: R1 (merged), R7, R8. VERIFY: R19 (resolved by the lead's fresh-clone run). KNOWN: R2 (merged), R20. Standalone run, so no verification-check queue was written.

R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: fail
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Gemini via copilot (model gemini-3.8-flash), exit 0. Findings: R3, R4, R9, R10. Carl wrote a temporary `plugins/specflow/dummy.txt` while probing and removed it.

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

Verdict: 20 findings

Tests: 32 passed, 0 failed, 0 skipped (suite run this cycle)
