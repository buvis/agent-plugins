---
prd: docs/dev/project-management/specs/00003-aws-sources-catchup/requirements.md
review: 1
date: 2026-10-10
head_sha: 907e2183bee78706ea23c3ed804b7456e25f4616
codex_thread_id: 01a1245e-c862-78c2-93f3-71354a2c0dd0
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00003-aws-sources-catchup

Diff range: `cce9a41da144a135ec6b075c845543f3ac97561a..907e2183bee78706ea23c3ed804b7456e25f4616`

codex_rung_guard: not fired

## Review Summary

Standalone run (no autopilot `state.json`). Spec 00003 is a specflow spec, not a wip PRD, so `requirements.md` was the review target, with `design.md` attached as the design doc and `tasks.md` as the task source. Reviewed: 4 completed tasks (T-010, T-011, T-014, T-018). Findings are reported here, not written as tasks.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one format retry, see his section)
- Carl: ✅ Available (backend=copilot model=gemini-3.8-flash)
- Eve: ⏸️ Disabled (doubt_reviewer resolved to codex; no codex-implemented tasks recorded)

### Run notes

- pack: ok.
- Gate: `review-stage` ran the gate (exit 0) but could not parse unittest counts. The counts below come from a suite run this cycle in the working tree at HEAD: `scripts` 12 OK, release 45 OK, `validate.py` printed `Validated 2 plugin package(s) and 3 skill(s).`, and `verify_release.py` printed `Verified plugins/specflow.`. CI on draft PR #2 (run 37994671759) is also green.
- Bob's first output put a `- ` bullet before each issue line, under FIX/VERIFY/KNOWN headers, so `consolidate_findings.py` dropped all of his findings. This is the same defect as in 00002. One format retry resumed his codex thread and he re-emitted the same findings in the correct shape. The first output is kept at `docs/dev/tmp/bob-output-00003c1-first.txt`. The defect recurs, so `agents/bob.md` (autopilot plugin) should be fixed at the source.
- Consolidation corrections (by hand):
  - The script merged Alice's "commit citations may be loose" note (report:11) into the A2-coverage row (R1). It is the same defect as Blake's evidence-rule finding (report:7), so it was moved to R11.
  - The script merged Carl's `cast("str", ...)` finding and Blake's churn finding into separate rows, though Alice and Bob raise the same thing. All four are now merged into R9.
  - Blake's "A3 scope includes `src/`" was split out of his churn line into R15.
  - The two assertion-free test rows (Bob KNOWN, Carl) were merged into R7.
- Mechanical checks absorbed: the two tautological-shape flags joined R7. Of the replay flag, `test_skips_maintainer_skills_when_paths_are_given` joined R5, and `test_rejects_env_overriding_reserved_variables` joined R9 (its only change is ruff's).
- Lead's checks:
  - R4 is confirmed: `RECORD_ROW`'s lazy `([^|]*?)` captures `"  "` for a blank cell, and `not role` lets it through.
  - R6 is confirmed: `SOURCE_LINE` already requires 7-40 hex characters, and a `v…` tag cannot prefix a hex commit, so `is_prefix`'s guards add nothing.
  - R8 fails closed: a padded adopted-from cell makes `A1_ADOPTED`/`COMMIT_ADOPTED` miss, the row is dropped, and the check reports "source record has no valid row". That matches T-010's fixed-form contract, so it is a strictness note, not a silent pass.
- Carl left no files behind (`git status --ignored` shows only `__pycache__`).
- No verification-check queue was written (standalone run).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/4] | 🟡 | A2 is reported as "Coverage: complete" and its cursor date moved to 2026-10-09, though its wider catalog (named in the cursor Scope) was never read; the seed read covered `all-phases/all-phases-aidlc-mcp/` only. UPD-002.2/.5 want a partly reviewed source to keep its cursor and be reported incomplete | docs/dev/project-management/reviews/2026-10-09-specflow-upstream-catchup.md:59 | T-018 | ALICE, BLAKE |
| R2 | [1/4] | 🟡 | Attribution check accepts the repository name anywhere in `LICENSE`; the design asks for an opening line per cited source. The `# ponytail:` marker documents the shortcut, but the design was not amended | tools/specflow/verify_release.py:333 | T-011 | ALICE |
| R3 | [1/4] | 🟡 | REL-001.3 ("every adopted passage names a recorded source") is enforced per file: one valid source line passes a file, and an unattributed passage or text after an `Adaptation:` line is never flagged | tools/specflow/verify_release.py:287 | T-014 | BLAKE |
| R4 | [1/4] | 🟡 | Whitespace-only role and license cells pass the record check; strip before testing and add rejection tests (confirmed) | tools/specflow/verify_release.py:248 | T-011 | BOB |
| R5 | [1/4] | 🟡 | `test_skips_maintainer_skills_when_paths_are_given` passes against the pre-change validator (expected per the T-018 Outcome); assert first that the same malformed skill fails default validation, so the test pins the mode distinction | scripts/test_validate.py:121 | T-018 | BOB, mech-check |
| R6 | [1/4] | 🟡 | `is_prefix` repeats null and length guards that `SOURCE_LINE` and its callers already guarantee; use `recorded.startswith(...)` (confirmed) | tools/specflow/verify_release.py:262 | T-014 | BOB |
| R7 | [2/4] | 🟡 | `test_template_is_valid` and `test_allows_plain_http_to_loopback` have no assertion. Both predate this spec, which only reformatted them | scripts/test_validate.py:41 | general | BOB, CARL, mech-check |
| R8 | [1/4] | 🟡 | Padded adopted-from cell fails `form.match(adopted)`; strip whitespace (lead: fails closed with "no valid row", consistent with the fixed-form contract) | tools/specflow/verify_release.py:246 | T-011 | CARL |
| R9 | [4/4] | 🟡 | Ruff-only churn in `scripts/validate.py` and `test_validate.py` (commit 4fd42f8): trailing commas, quoted `cast("str", ...)`, unrelated to the spec; `validate_manifest` (96 lines) and `validate_mcp` (130 lines) were already over 50 lines | scripts/validate.py:74 | T-018 | ALICE, BLAKE, BOB, CARL, mech-check |
| R10 | [1/4] | ⚪ | Two `check_sources` branches have no test: unreadable file in `read_text` (verify_release.py:237) and "source line names X, which the record lacks" (verify_release.py:274) | tests/specflow/release/test_verify_release.py:322 | T-011 | ALICE |
| R11 | [2/4] | ⚪ | The first report cites path and heading per ruling, not path and commit as the skill asks; it admits its commit citations "may be loose", and the delegated `v2.10.0..v2.11.0` read was spot-checked only | docs/dev/project-management/reviews/2026-10-09-specflow-upstream-catchup.md:7 | T-018 | ALICE, BLAKE |
| R12 | [1/4] | ⚪ | Skill says "the release process names it as its first step"; no release document does | .agents/skills/catchup-specflow-upstream/SKILL.md:72 | T-018 | BLAKE |
| R13 | [1/4] | ⚪ | "Trusted checkout" (UPD-001.3) is stated, not checked: step 1 checks two files exist; no `origin`/clean-tree check, no `mktemp -d`, no cleanup trap | .agents/skills/catchup-specflow-upstream/SKILL.md:28 | T-018 | BLAKE |
| R14 | [1/4] | ⚪ | Shipped `adaptation.md` cites internal IDs and decisions (WF-003.15, ART-002.16-18, INT-001.8, "decision 2026-10-04 #2") a package reader cannot resolve | plugins/specflow/skills/spec-workflow/references/aws/adaptation.md:62 | T-010 | BLAKE |
| R15 | [1/4] | ⚪ | A3 cursor Scope includes `src/`; UPD-002.2 names only the discovery rules | tools/specflow/upstream/sources.md:9 | T-018 | BLAKE |
| R16 | [1/4] | ⚪ | VERIFY: quotation provenance, including heading attribution, against A1 `6a378b5`. Blake checked 203 fragments with 0 mismatches and found all 28 headings upstream, so text and headings exist. Whether each passage sits under its true heading is still unchecked | docs/dev/project-management/specs/00003-aws-sources-catchup/tasks.md:61 | T-014 | BOB |
| R17 | [1/4] | ⚪ | VERIFY: tests and release checks pass. Resolved: the lead ran all four commands at HEAD and all passed, and CI run 37994671759 is green | N/A | general | BOB |

Overlap: R2, R3, R4, R6 and R8 all touch `check_sources` and can be fixed in one pass. R1, R11 and R15 are all fixes to the first catch-up report and its cursors.

## Alice

[ALICE] 🟡 A2 cursor date advanced and "Coverage: complete" though the wider catalog was never read (R1). | File: docs/dev/project-management/reviews/2026-10-09-specflow-upstream-catchup.md:59 | Task: T-018
[ALICE] 🟡 Attribution check weaker than the design; ponytail marker (R2). | File: tools/specflow/verify_release.py:333 | Task: T-011
[ALICE] ⚪ Two untested `check_sources` branches (R10). | File: tests/specflow/release/test_verify_release.py:322 | Task: T-011
[ALICE] ⚪ Formatter-only churn in the T-018 range (R9). | File: scripts/validate.py:74 | Task: T-018
[ALICE] ⚪ Report commit citations loose; delegated read spot-checked (R11). | File: docs/dev/project-management/reviews/2026-10-09-specflow-upstream-catchup.md:11 | Task: T-018

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

Blind lens (spec only). Blake cloned A1, A2 and A3 into scratch space. A1 `v2.11.0` peels to `6a378b5` as recorded, and the A2 and A3 HEADs equal their cursors. All three LICENSE files match the shipped MIT-0 text. He compared 203 verbatim fragments with upstream at `v2.11.0` and found 0 mismatches; all 28 headings exist upstream. The report's range stats and the `adaptation.md` counts are correct. He also ran the validator, the release check, and the release tests (45 OK). His findings are R1 (merged), R3, R9 (merged), R11 (merged), R12, R13, R14, and R15 above.

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
B16: fail
B17: pass
B18: pass
B19: pass

## Bob

Codex, exit 0. (format warning) In the first run his issue lines carried a leading `- ` under FIX/VERIFY/KNOWN headers and were dropped by consolidation. after one retry (format, resumed thread, not inlined), he re-emitted the same findings in the correct shape. FIX: R4, R5, R6. VERIFY: R16, R17 (R17 resolved). KNOWN: R7, R9 (both merged). Standalone run, so no verification-check queue was written.

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
R12: fail
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Gemini via copilot (model gemini-3.8-flash), exit 0. Findings: R7 (merged), R8, R9 (merged).

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

Verdict: 17 findings

Tests: 57 passed, 0 failed, 0 skipped (suite run this cycle)
