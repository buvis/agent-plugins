---
prd: docs/dev/project-management/specs/00007-reviews-and-conversion/requirements.md
review: 1
date: 2026-10-19
head_sha: e735c9bbeb7bd77eac82c6c52714bcb7f188b24d
codex_thread_id: 01a152e7-76ed-73d2-ab7d-5b6587be96da
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00007-reviews-and-conversion

Diff range: `15ce4fdfe713..e735c9bbeb7bd77eac82c6c52714bcb7f188b24d`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 1, a full review of branch `feature/specflow-00007` since `15ce4fd` (the 00006 completion tick), as the developer asked: eight commits, 440 files. There is no autopilot `state.json` and no wip PRD. The target is spec 00007's `requirements.md`, with `design.md` as the design doc. All seven tasks (T-073 to T-077, T-079, T-080) are complete. Findings are reported here, not written as tasks.

No reviewer found a 🔴. One 🟠 stands: the requirements review accepts `bugfix.md` as its target but its lenses demand feature-only shapes, so every bugfix review raises false blockers (F3). The other confirmed defects are rule-text and test gaps. The receipt check accepts the unfilled template verdict (F1). `check_links.py` has three probed path-handling defects: an outside group link still feeds the citation index (F10), an unreadable intake folder crashes the scan (F11), and a numbered wiki link is resolved instead of only warned about (F12). The design-review tier is stated two ways (F8, F15). Unwalked pre-pass findings never reach the minutes (F9). The cross-spec apply pass batches edits against the core's immediate-apply rule (F14). The workflow skill has no `convert` routing row (F4).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, first run, on the inlined 631 KB prompt; no refusal this cycle). His `[BOB]` lines carry a `- ` bullet, so consolidation read a stripped copy (`docs/dev/tmp/bob-output-00007c1-lines.txt`).
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, after one retry). His first run, also exit 0, published only a tool transcript, with no `[CARL]` line and no verdicts. That is format-invalid, so the one retry re-sent his prompt with the format correction appended. The first output is kept at `docs/dev/tmp/carl-output-00007c1-first.txt`. The retry returned the all-clear with every verdict.
- Eve: ⏸️ Disabled. `doubt_reviewer` resolved to codex, since the spec has no frontmatter. With no state file there is no record of codex-implemented tasks, so the guard cannot fire.

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). The review is degraded, not invalid.
- Dirty tree: the first staging skipped the gate because seven session-fixture files held uncommitted `ruff format` output (line wrapping only). The lead set them aside in a tagged stash entry, staged again on a clean tree, and restored them after the review. They are not part of the reviewed range.
- Gate: `review-stage` ran the eight CI steps of `validate.yml` through the worktree-local `docs/dev/tmp/review-tools/gate.sh` (exit 0). It could not parse the unittest counts, so the lead composed the `Tests:` line from the logs: `scripts` 12, release 54, contract 369, rules 58, review 32, all OK. `validate.py` ("Validated 2 plugin package(s) and 4 skill(s)"), `check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER,RVC,RVR,RVD,RVX,CNV` and `verify_release.py` exited 0. The corrected line was written into the staged context and Blake's prompt before dispatch.
- Python 3.10, the version CI pins: the lead ran contract (369 OK), review (32 OK) and rules (58 OK).
- Lint: `ruff check` on the changed project Python files reports only the three pre-existing ISC004 hits in `test_checks.py`; `ruff format --check` is clean on them. The seven stashed fixture files are the only ones it would reformat.
- Fail-first replay: `python3 -m pytest` reported 5 of 42 touched tests passing at base. The lead redid the replay with unittest in a worktree at `15ce4fd` with HEAD's `tests/specflow` copied in. `test_id_tokens_are_not_measurements` errors in all six subtests at base, since the script does not exist there; pytest swallowed the subtest errors. The receipt class ran 7 tests at base: the three seeded defects fail and the four passing-direction cases pass. No tautological test shapes were reported.
- Probes (scratchpad tree, `check_links.py --json`): a `[[00009-missing]]` link gives both a finding and a warning, exit 1 (F12). An intake group folder linked outside the root is reported as a scan error, but a citation to a folder inside it resolves, so no finding (F10). An unreadable intake item folder ends the run with a `PermissionError` traceback from `resolvable_numbers` (F11).
- Carl's first run executed the suites without `PYTHONDONTWRITEBYTECODE` and left `__pycache__` under `tests/` and `tools/`. The lead removed only those ignored folders (`git clean -X -d -f -- plugins tools tests`). Afterwards the tree held no ignored files there.
- Consolidation corrections (by hand): the script merged Alice's and Bob's rows on `test_id_tokens_are_not_measurements`, which make opposite claims; the row is kept as F2 with the lead's replay as its verdict. The two `[MECH]` replay lines became `mech-check` finders on F2 and F16. The lead downgraded four rows with the evidence below: F2 (🟡 to ⚪), F5, F7 and F13 (🟡 to ⚪). Refs were renamed from the script's `R1`..`R18` to `F1`..`F18`.
- Lead's checks:
  - F1: `conversion_receipt` tests `(verdicts[-1][:1] or [""])[0]`, the first token only (`checks.py:753`). The template line of `conversion.md:60`, `Verdict: COMPLETE | AWAITING_DECISION | INCOMPLETE`, passes as written. Confirmed.
  - F2: refuted as a defect. Under unittest the test fails at base in all six subtests, so it pins the ID-token fix; the T-077 outcome also records 9 failures against the installed sources. Alice is right, Bob's row is a replay artifact.
  - F3: SR-RVR-002 names `bugfix.md` as a target "whose clauses stand for the criteria". SR-RVR-012 still requires `## Purpose`, a user story and `## Out of scope` at every profile, and SR-RVR-020 requires `THE SYSTEM SHALL` in every criterion. A bugfix artifact has neither the headings nor SHALL in its Current Behavior clauses, and SR-RVR-037 makes an unverifiable criterion blocking. A conforming review of any bugfix spec therefore raises false blockers. No session reviews a bugfix. The T-074 outcome records the SR-RVR-002 choice but not this conflict. Kept at 🟠.
  - F4: `SKILL.md:33-44` has no `convert` row and no mention of `convert-prd`; `design.md:154` says "the `convert` row of the workflow skill's intent table sends the agent to it". Confirmed as code versus design.
  - F5: the test checks rule `file` and `check` prefixes only, confirmed. `verify_release.py:51-56` forbids `tools/specflow` and `tests/specflow` in every package file and runs in CI, so the property holds on the shipped text; only the test's name over-promises. Downgraded to ⚪.
  - F6: the seven receipt tests (`test_checks.py:641-676`) have no `..` or absolute `Sources:` path and no missing log. Confirmed.
  - F7: the T-077 outcome records "`blank_fences` is repeated in each scan, since each runs standalone". Each scan runs by `python3 <path>`, and `check_links.py:28` shows a sibling import works the same way, so a shared module is possible; the copy is a recorded choice. Downgraded to ⚪.
  - F8 and F15: REV-001.6 says "a quick spec gets ... design Tier 1; a standard spec ... the design tier rises when Tier 2 or Tier 3 conditions hold". `design.md:99` and SR-RVD-006 let a quick design rise. The `design-review-quick` fixture writes the `notes` column of the `orders` table, a persistent store, which SR-RVD-020 puts in Tier 2, yet SR-RVD-019's eval asserts Tier 1. The eval agrees with the requirement and disagrees with the rule. Confirmed as a requirement-versus-design question that needs one reading.
  - F9: SR-RVD-117 minutes the author's fixes only; SR-RVD-118 sends the rest into the walkthrough; SR-RVD-012 lets non-blockers and questions stay unwalked, and SR-RVC-064 writes a line only when a finding is decided. ART-003.11 requires remaining findings in the log. Confirmed.
  - F10, F11, F12: confirmed by the probes above. F10 still exits 1 through the scan error, so the effect is a missing finding, not a false clean run.
  - F13: SR-RVC-013 opens with "Every file a review loads is named by its path relative to the skill folder, as the routing table in `SKILL.md` gives it", which scopes it to the review's own guidance; only the last clause reads wider. Downgraded to ⚪: a one-word scope fix.
  - F14: the defect is in the rule as well as the eval. SR-RVC-054 (`core.md:85`) applies "the accepted edits and the approved reshapes" in a pass after the walkthrough, while SR-RVC-016, 026 and 053 in the same file apply each edit before the next card. Confirmed.
  - F16: the four passing-direction receipt tests pass at base by construction; the T-080 outcome records the fail-first (7 run, 3 failed with the check unregistered). A fact, as 00006 F15; kept 🟡 per the mechanical-check rule.
  - F17: `phases/requirements.md` holds no hand-off to the requirements review; `phases/design.md:38` hands the draft to its review. SR-RVR-006 calls the review "the review step of the requirements phase". Confirmed.
  - F18: `sources()` adds every folder it meets to `seen` but not the two base folders, so a link back to a base is walked once more. Confirmed by reading.
- No verification-check queue was written (Bob's VERIFY bucket is empty, and there is no `state.cycle`), no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/4] | 🟡 | The receipt `Verdict:` check reads only the first token. The template line `Verdict: COMPLETE / AWAITING_DECISION / INCOMPLETE` (pipes in the source), copied unfilled from `conversion.md`, therefore passes, and so does `COMPLETE, but ...`. Compare the whole value after the label against the three verdicts, allowing only the parenthetical note the test uses | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:753 | T-080 | ALICE, BLAKE |
| F2 | [2/4] | ⚪ | The pytest replay lists `test_id_tokens_are_not_measurements` as passing at base. Refuted by the lead's unittest replay: it errors in all six subtests at base, since its assertions sit in `subTest` and the script did not exist. It pins the ID-token fix. Downgraded from 🟡 by the lead | tests/specflow/review/test_claim_ladder_scan.py:49 | T-077 | ALICE, BOB, mech-check |
| F3 | [1/4] | 🟠 | The requirements review accepts `bugfix.md` (SR-RVR-002) but its lenses mandate feature shapes: `## Purpose`, a user story and `## Out of scope` (SR-RVR-012) and `THE SYSTEM SHALL` in every criterion (SR-RVR-020). Kiro's Current Behavior clauses hold no SHALL, so a conforming review flags valid bugfix artifacts, and SR-RVR-037 makes an unverifiable criterion blocking. Branch the completeness and integrity checks by artifact type and add a bugfix review session | plugins/specflow/skills/spec-workflow/references/review/requirements.md:25 | T-074 | BOB |
| F4 | [1/4] | 🟡 | `design.md:154` says the `convert` row of the workflow skill's intent table sends the agent to `convert-prd`. No such row exists, and `SKILL.md` never mentions convert-prd, convert, adopt or graduate. Routing depends only on convert-prd's own description. Add a `convert` row and a one-line routing rule, or correct the design text | plugins/specflow/skills/spec-workflow/SKILL.md:33 | T-080 | ALICE |
| F5 | [1/4] | ⚪ | `test_convert_prd_ships_and_no_cnv_rule_names_a_maintainer_path` checks only the CNV rules' `file` and `check` prefixes; it never scans the shipped convert-prd text for maintainer paths. `verify_release.py:51-56` already forbids `tools/specflow` and `tests/specflow` in every package file in CI, so only the test's name over-promises. Rename it or add the scan. Downgraded from 🟡 by the lead | tests/specflow/release/test_boundary.py:32 | T-080 | ALICE |
| F6 | [1/4] | 🟡 | Two branches of `conversion_receipt` have no test: the guard that returns no finding for an absolute or `..` `Sources:` path (`checks.py:728`), and a named `qa-log.md` that does not exist (`checks.py:732`). Add one test for each | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:728 | T-080 | ALICE |
| F7 | [1/4] | ⚪ | `blank_fences` is copied in the three scans (`claim_ladder_scan.py:87`, `adversarial_signal_scan.py:74`, `section_weight_audit.py:53`), and only the first carries the SR-RVD-103 tag. A fence fix must be kept in sync three times. The T-077 outcome records the copy as a choice; a sibling module imported as `check_links.py:28` does would remove it. Downgraded from 🟡 by the lead | plugins/specflow/skills/spec-workflow/scripts/review/claim_ladder_scan.py:87 | T-077 | ALICE |
| F8 | [1/4] | 🟡 | REV-001.6 gives a quick spec design Tier 1 and lets only a standard spec's tier rise, but SR-RVD-006 (and `design.md:99`) review a quick design at Tier 2 or 3 when those conditions hold. The requirement and the rule read two ways; settle one. See F15 | plugins/specflow/skills/spec-workflow/references/review/design/triage.md:15 | T-075 | BLAKE |
| F9 | [1/4] | 🟡 | ART-003.11 requires the design review to record applied fixes and remaining findings in the intake Q&A log. SR-RVD-117 logs only the author's fixes; remaining pre-pass findings are minuted only when the walkthrough decides them (SR-RVC-064), and SR-RVD-012 lets non-blockers and questions stay unwalked, so those are never recorded | plugins/specflow/skills/spec-workflow/references/review/design/pre-pass.md:8 | T-075 | BLAKE |
| F10 | [1/4] | 🟡 | `resolvable_numbers()` indexes intake group folders through links that `sources()` rejected as leaving the repository, so a citation to a folder outside the root resolves and draws no finding (probed; the scan error still makes the exit 1). Apply the same containment check before indexing | plugins/specflow/skills/spec-workflow/scripts/check_links.py:80 | T-076 | BOB |
| F11 | [1/4] | 🟡 | Directory errors are not reported consistently: `os.walk()` skips an unreadable subfolder silently, and `iterdir()` in `resolvable_numbers` raises, so an unreadable intake item ends the run with a `PermissionError` traceback (probed) instead of a scan error. Collect traversal errors into `scan_errors` and test both cases | plugins/specflow/skills/spec-workflow/scripts/check_links.py:64 | T-076 | BOB |
| F12 | [1/4] | 🟡 | A numbered wiki link such as `[[00009-missing]]` is resolved as a citation and draws a dangling finding beside its warning, so the run exits 1 (probed). SR-RVX-078 says such a link is a warning, never resolved. Exclude wiki-link spans from citation matching and add the regression case | plugins/specflow/skills/spec-workflow/scripts/check_links.py:111 | T-076 | BOB |
| F13 | [1/4] | ⚪ | SR-RVC-013's last clause, "no review reads ... a file outside the package", reads wider than the rule's own opening ("Every file a review loads", the routing table's files), against the required reads of artifacts, intake logs and code. Scope the clause to the review's guidance and its eval with it. Downgraded from 🟡 by the lead | plugins/specflow/skills/spec-workflow/references/review/core.md:8 | T-073 | BOB |
| F14 | [1/4] | 🟡 | SR-RVC-054 (`core.md:85`) and its eval apply the accepted edits and reshapes in a pass after the walkthrough, contradicting REV-001.4 and SR-RVC-016, 026 and 053 in the same file, which apply each edit before the next card. Keep only the validation and the report reconciliation after the walkthrough | tests/specflow/evals/SR-RVC-054.json:8 | T-076 | BOB |
| F15 | [1/4] | 🟡 | SR-RVD-019's eval asserts Tier 1 on `design-review-quick`, whose design writes the `notes` column of the `orders` table, a persistent store that SR-RVD-020 places in Tier 2. Use a Tier 1 fixture with no store change, or assert the upgrade. Settled together with F8 | tests/specflow/evals/SR-RVD-019.json:12 | T-075 | BOB |
| F16 | [1/4] | 🟡 | Four touched receipt tests pass against the pre-change code: `test_a_spec_with_no_receipt_block_draws_no_finding`, `test_a_receipt_with_every_label_and_a_known_verdict_passes`, `test_a_complete_receipt_after_a_broken_one_passes`, `test_a_receipt_inside_a_fence_is_not_read`. They are passing-direction cases; the three seeded defects fail at base (T-080 outcome). A seeded control in each would make them fail if the check went silent | tests/specflow/contract/test_checks.py:641 | T-080 | BOB, mech-check |
| F17 | [1/4] | ⚪ | REV-001.1 says the workflow offers the requirements review, but it is reachable only on request (`SKILL.md:39`); the requirements phase never hands its draft to the review, unlike `phases/design.md:38`, although SR-RVR-006 calls it the review step of that phase | plugins/specflow/skills/spec-workflow/references/phases/requirements.md:74 | T-074 | BLAKE |
| F18 | [1/4] | ⚪ | `sources()` does not add the two base folders to `seen`, so a link inside the scanned tree back to a base folder is walked again and its files are scanned and reported twice | plugins/specflow/skills/spec-workflow/scripts/check_links.py:64 | T-076 | BLAKE |

Overlap: F10, F11, F12 and F18 are `check_links.py` path handling and can be fixed together with one test each. F1, F6 and F16 are the receipt check and its tests. F8 and F15 need one decision on the quick-spec tier: changing REV-001.6 or the design edits an approved artifact. F9, F13, F14 and F17 are rule-text fixes in the review references. F3 needs a bugfix branch in the requirements review lenses and a session.

## Alice

Implementation-aware review on the legacy consensus engine. Findings: F4, F5, F6, F7, and F1 with Blake; F2 with Bob, where she reads the replay row as an artifact, which the lead's replay confirms.

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Blind lens (spec only). Findings: F8, F9, F17, F18, and F1 with Alice.

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
B17: pass
B18: pass
B19: pass

## Bob

Codex, exit 0, first run. FIX holds nine items (F3, F10, F11, F12, F13, F14, F15, F16, and F2 with Alice); VERIFY and KNOWN are empty.

R1: fail
R2: fail
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0, after one retry (format-invalid first run, see Agent Status). Carl: ✅ No issues found.

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

Verdict: 18 findings

Tests: 525 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-25)

The lead ruled on each finding under the developer's standing authorization (review findings are the agent's to adjudicate; no ruling edits an approved artifact). The developer may overturn any ruling before cycle 2. The cycle's one 🟠 (F3) is fixed, so the rework is followed by an incremental cycle 2 under the autopilot bar. Before the rework, `master` (the PR 5 fix `583829c`) was merged into the branch: its SR-VAL-019 to 025 collided with T-079's SR-VAL-019 and 020, so `placement-drift` is folded into SR-VAL-020 with both sources and `design-sections` is renumbered SR-VAL-026.

- F1: fix. The verdict check compares the whole value after `Verdict:` with the three verdicts, allowing only the parenthetical note the passing test uses; the unfilled template line and `COMPLETE, but ...` are reported. Queued.
- F2: refuted (ledger entry added). The unittest replay errors in all six subtests at base; the pytest row is a `subTest` artifact.
- F3: fix. The requirements review branches by artifact type: for `bugfix.md` the completeness lens reads Kiro's shape (`## Introduction`, `## Bug Analysis` with its three behavior sections, each with a clause, the `Sources:` line) and the integrity lens applies the clause patterns (no `SHALL` in Current Behavior, `WHEN ... THEN THE SYSTEM SHALL` in Expected, `SHALL CONTINUE TO` in Unchanged) in place of the feature shapes of SR-RVR-012 and the EARS test of SR-RVR-020; SR-RVR-037 then blocks on an unverifiable clause as written. A bugfix review session with its eval records is added. No design edit: `design.md:89` already names `bugfix.md` as the target and `design.md:129` leaves the lens calibration to the reference. Queued.
- F4: fix. The intent table gains a `convert` row ("Convert PRD X", "Adopt PRD X", "Graduate PRD X") that names the `convert-prd` skill of this package, with a one-line routing rule and its eval record on a conversion session. Queued.
- F5: fix. The test is renamed to what it checks (the CNV rules' file and check prefixes); the shipped-text scan is `verify_release.py`'s. Queued.
- F6: fix. One test for the absolute or `..` `Sources:` path and one for a named `qa-log.md` that does not exist, each expecting no finding. Queued.
- F7: accepted (ledger entry added). The T-077 outcome records the copy as a choice: each scan runs standalone by `python3 <path>`.
- F8 and F15: fix by rule text, one reading. SR-RVD-006 follows `design.md:99` literally: a `quick` design starts at Tier 1 and rises only when a WF-003.6 trigger holds (security, architecture, a data migration, a public API, cross-component work, concurrency, an equivalence obligation, an invented algorithm, a destructive change), which also draws the profile proposal of WF-003.14; the Tier 2 and Tier 3 conditions of SR-RVD-020 and 021 decide a `standard` spec's tier. REV-001.6 then holds as written. The `design-review-quick` design writes an existing unused column (its README), no migration and no trigger, so SR-RVD-019's Tier 1 assertion stands. Neither approved artifact is edited. Queued.
- F9: fix. SR-RVD-012 writes one minutes line (severity, title, "not walked", open) for each non-blocker or question left unwalked when the developer stops, so ART-003.11's remaining findings reach the log; the eval rubric follows. Queued.
- F10, F11, F12, F18: fix, one test each. The containment check runs before an intake folder is indexed; traversal errors from `os.walk()` and `iterdir()` become scan errors instead of a traceback or silence; `[[...]]` spans are excluded from citation matching; the two base folders enter `seen`. Queued.
- F13: fix. SR-RVC-013's last clause is scoped to the review's own guidance files; the artifacts, intake logs, and code a review must read are not in it. Queued.
- F14: fix. SR-RVC-054 and its eval keep only the validation re-run on every touched spec, the report update, and the final verdict after the walkthrough; each accepted edit and approved reshape lands before the next card, as SR-RVC-016, 026, and 053 say. The same wording in `cross-spec.md`, where present, follows. Queued.
- F16: accepted as a fact (ledger entry added). The four tests are passing-direction cases; the three seeded defects fail at base (T-080 outcome), as 00006 F15.
- F17: fix. `phases/requirements.md` hands the validated draft to the requirements review before the approval summary, as `phases/design.md:38` does for the design. Queued.

### Outcome (2026-10-25)

Fixture formatting `4cb02f5`; merge of `master` `0207afb`; decisions and ledger `7ff65ed`; fix commits `0783028` (F1, F5, F6), `6786e67` (F10, F11, F12, F18), `6585043` (F3), `f7a93b4` (F4, F8, F9, F13, F14, F15, F17), `3ed1576` (a defect of the F1 fix); this record in the commit after it. The rework ran as four sub-agents on disjoint files, each with its tests written first; the lead committed each cluster after reading its diff.

- F1: `RECEIPT_VERDICT` matches the whole value after `Verdict:`: one of the three verdicts, an optional parenthetical note, an optional full stop. The template line and `COMPLETE, but ...` are errors. Fail-first at `7ff65ed`: the template-line test failed; the free-text test is a guard only, since the old first-token check already saw `COMPLETE,`. The first regex had no full stop, so every real receipt in this repository (nine intake logs end `COMPLETE (... not started).`) drew the error and `status` closed 00007's implementation gate; `3ed1576` adds the full stop with `test_a_verdict_with_a_note_and_a_full_stop_passes`, which failed at `f7a93b4`. Lesson recorded: after a check changes, run `validate` on this repository's own specs before committing.
- F3: SR-RVR-043 (completeness in Kiro's shape), SR-RVR-044 (each clause by its section's pattern; the shape stays the helper's; an unverifiable clause is blocking), SR-RVR-045 (`## Introduction` stands for `## Purpose`; an Expected clause against an Unchanged clause is a blocking pair), SR-RVR-046 (a guessed Current Behavior clause is blocking and never replaced by an invented observation). SR-RVR-012, 013, and 020 are scoped to a feature spec with a pointer; the SR-RVR-013 scoping goes beyond the ruling, since its `standard` sections would raise the same false blockers on a standard bugfix. Session `requirements-review-bugfix`: a standard bugfix spec `00001-discount-total`, `bugfix.md` valid to the helper, seeded with 1.2 "sometimes seems slow", 2.3 "SHALL work correctly", and 3.3 contradicting 2.1; the four records assert each defect and the absence of any feature-heading finding. `review/requirements.md` is 107 lines.
- F4: the `convert` row and SR-SKL-017 (sources `R:CNV-001.2`, `R:CNV-001.6`; eval on `convert-prd-new`). The row names the skill, not a path, since a host installs skills one by one. `SKILL.md` is 103 lines.
- F5: `test_convert_prd_ships_and_every_cnv_rule_points_inside_it`; no inventory binding named the old name.
- F6: `test_a_sources_path_outside_the_repo_draws_no_receipt_finding` (an absolute path and `../outside`, each pointing at a real broken receipt, so the test fails if the guard goes) and `test_a_sources_item_with_no_qa_log_draws_no_finding`; both pass before and after, as coverage of existing branches.
- F8 and F15: SR-RVD-006 as ruled, with the WF-003.6 trigger list spelled out and "a write to an existing store leaves a `quick` design at Tier 1"; its rubric says the same; SR-RVD-019 and 020 untouched. The agent found SR-RVD-025 (mid-review upgrades) in conflict with the new text; the lead scoped it: a finding always, a tier rise as SR-RVD-006 allows the profile.
- F9: SR-RVD-012 writes a minutes line (severity, title, "not walked", open) for each finding left unwalked; rubric extended.
- F10, F11, F12, F18: `resolvable_numbers()` walks one list of folders and skips one that resolves outside the root; `os.walk`'s `onerror` and a `try/except OSError` around `iterdir` turn an unreadable folder into one scan error (`run()` drops a duplicate message); wiki-link spans are blanked before citation matching; the base folders enter `seen`. Five tests, each failing at `0783028` as the finding described (the F18 test needed a file directly in a base folder: `seen` already pruned subfolders, so only base-level files were scanned twice). Review suite 37. SR-RVX-006 and 073 say "unreadable files"; unreadable folders are scan errors too now; the wording is incomplete, not false, and left for cycle 2 to judge.
- F13: SR-RVC-013 reads "no review loads its guidance from a home path, an absolute path, or a file outside the package"; rubric follows.
- F14: SR-RVC-054 keeps validation, the decisions-applied section ("completes", since SR-RVX-068 fills it during the walkthrough), the report update, and the verdict after the walkthrough; rubric rewritten. `cross-spec.md` needed no change.
- F17: untagged prose after SR-REQ-042 and before SR-REQ-014, mirroring the untagged hand-off of `phases/design.md:38`; no new rule.
- F2, F7, F16: ledger entries; no change.
- Gates after the rework, Python 3.14 and 3.10: scripts 12, release 54, contract 383, rules 58, review 37, all OK; `validate.py` 2 packages, 4 skills; `check_rules.py` passes with the CI areas and with none; `verify_release.py` passes; ruff reports only the three pre-existing ISC004 hits; `status` reports 00007 at `verification` with `stale` empty and every gate open.
- Open for cycle 2: the merge of `master` renumbered T-079's SR-VAL-019 and 020 (placement-drift folded into SR-VAL-020 with both sources, design-sections now SR-VAL-026); reviewers should read `0207afb` with the fixes.
