---
prd: docs/dev/project-management/specs/00007-reviews-and-conversion/requirements.md
review: 2
date: 2026-10-25
head_sha: 4d8609fa292cacc1f35c674fbac779dbb64f840b
codex_thread_id: 01a152e7-76ed-73d2-ab7d-5b6587be96da
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: unavailable
  eve: disabled
---

# Review: 00007-reviews-and-conversion

Diff range: `e735c9bbeb7bd77eac82c6c52714bcb7f188b24d..4d8609fa292cacc1f35c674fbac779dbb64f840b`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 2, an incremental review of `e735c9b..4d8609f`: the cycle-1 rework (fixture formatting, the merge of `master`, decisions, five fix commits, outcome). The range includes master's `583829c` (the PR 5 fix, reviewed in PR 5) through the merge `0207afb`, which renumbered T-079's SR-VAL rules. The target is spec 00007's `requirements.md`, with `design.md` as the design doc. Findings are reported here, not written as tasks.

No reviewer found a 🔴 or a 🟠, and the codex guard did not fire, so the loop converges under the autopilot bar; the walkthrough rework is the tail sweep and no cycle 3 runs. Alice verified every fixed cycle-1 finding (F1, F3 to F6, F8 to F15, F17, F18) and the SR-VAL renumbering. Bob found two of those fixes incomplete in reverse cases (F3 and F4 here: a numbered intake link leading outside, an intake base reached through a link from the specs tree) and one regression from `583829c` (F5: comma-separated plain paths). The rest is rule and template wording.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, first run, on the inlined 218 KB prompt with `--resume-thread 01a152e7-76ed-73d2-ab7d-5b6587be96da`; no refusal). His `[BOB]` lines carry no bullet.
- Carl: ❌ Unavailable. Copilot backend, `gemini-3.8-flash`: "You have exceeded your monthly quota", exit 1 on the first run and on the one unchanged retry. A runtime failure, not exit 4, so nothing is latched. The native gemini backend was not tried, since it bills a different account.
- Eve: ⏸️ Disabled. `doubt_reviewer` resolved to codex (the spec has no frontmatter); with no state file there is no record of codex-implemented tasks, so the guard cannot fire.

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). Degraded, not invalid.
- Gate: `review-stage` ran the eight CI steps through `docs/dev/tmp/review-tools/gate.sh` (exit 0). It could not parse unittest counts, so the lead composed the `Tests:` line from the logs: scripts 12, release 54, contract 383, rules 58, review 37, all OK; `validate.py`, `check_rules.py --area ...` and `verify_release.py` exit 0. The line was written into the staged context and Blake's prompt before dispatch.
- Fail-first replay (`python3 -m pytest` against `e735c9b`): eight touched tests pass at base, rows F13 to F16. Each has a known cause: the two F6 tests cover existing branches and the free-text test is a guard (cycle-1 outcome), the full-stop test fails at `f7a93b4`, the commit it guards, not at `e735c9b`; the two `test_phase_checks.py` tests come from `583829c`; `test_header_row` is a fixture touched only by `ruff format` (`4cb02f5`); the boundary test is the F5 rename.
- Consolidation corrections (by hand): the script merged Blake's two template rows (`cross-spec-review.md:5` and `:9`) after suffix stripping; they are split into F2 and F8. The four `[MECH]` lines are their own rows. Refs renamed from `R1`..`R11` to `F1`..`F16`.
- Lead's checks:
  - F1: SR-CNV-026 (`conversion.md:42`), the template line (`conversion.md:60`) and the fix text (`checks.py:759`) say only "one of the three"; `RECEIPT_VERDICT` (`checks.py:706`) also takes a parenthetical note and a full stop. Confirmed.
  - F2: REV-001.8 requires "a GO or NO-GO verdict and a verdict per spec"; the template's Verdict line names neither, and the spec map has no verdict column. Confirmed.
  - F3: `resolvable_numbers()` adds `p.name[:5]` for every entry of `new/` and `processed/` (`check_links.py:107`), so an item that is itself a link leading outside still resolves. The scan error from `sources()` keeps the exit at 1, as in cycle-1 F10. Confirmed by reading.
  - F4: `sources()` seeds `seen` with each base only when its own loop starts (`check_links.py:64`), so a link in the specs tree to the intake base walks it first and the second loop walks it again. Confirmed by reading.
  - F5: `583829c` changed `location_paths()` from comma splitting to `split()` (`phase_checks.py:257`), so `src/a.py,src/b.py` is one word. Confirmed by reading the diff.
  - F6: SR-RVD-012 says blockers "are walked before stopping", but its minutes line covers only unwalked non-blockers and questions; a blocker shown and not answered when the developer stops gets no line. Confirmed.
  - F7: SR-RVD-019, 020, 021 and 013 read without the profile limit SR-RVD-006 now sets. Confirmed as wording.
  - F8: SR-RVX-019 lists profile and approval status per spec; the template has neither column. Confirmed.
  - F9: `pre-pass.md` uses `blocker`/`non-blocker`, the core `blocking`/`non-blocking`; SR-RVD-116 defines the pre-pass terms without naming the core's. Confirmed as wording.
  - F10: the role-change pattern needs "a different" or "another" after "you are now"; SR-RVC-044 quotes "you are now …". Confirmed.
  - F11: `conversion_receipt` joins a relative `Sources:` path onto the repository without resolving it; `config.py:32` and `deps.py:112` check containment after `resolve()`. Confirmed, read-only.
  - F12: SR-RVX-006 and the SR-RVX-073 tag say "unreadable files"; since `6786e67` folders are scan errors too. Confirmed as wording.
- No verification-check queue, dispatch rows, contract card or session brief (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/3] | 🟡 | The verdict form `conversion-receipt` enforces (one of the three words, an optional parenthetical note, an optional full stop) is not stated in SR-CNV-026, the template line, or the check's fix text, so `COMPLETE - tasks drafted` is an error the guidance never warned about. Name the form, for example `COMPLETE (short note).` | plugins/specflow/skills/convert-prd/references/conversion.md:42 | T-080 | ALICE |
| F2 | [1/3] | 🟡 | REV-001.8 asks for a GO or NO-GO verdict and a verdict per spec, but the cross-spec report template has a free-text Verdict line and no per-spec verdict column (SR-RVX-062, 063) | plugins/specflow/skills/spec-workflow/templates/cross-spec-review.md:5 | general | BLAKE |
| F3 | [1/3] | 🟡 | F10 is incomplete: an intake item named `00042-elsewhere` that is itself a link leading outside still contributes `00042`, since the `entries` comprehension is not filtered by containment. Add a regression for a directly numbered external link | plugins/specflow/skills/spec-workflow/scripts/check_links.py:107 | T-076 | BOB |
| F4 | [1/3] | 🟡 | F18 is incomplete: a link in the specs tree to the intake base walks it before its own loop seeds `seen`, so its base-level files are scanned twice. Seed both resolved bases before either walk | plugins/specflow/skills/spec-workflow/scripts/check_links.py:64 | T-076 | BOB |
| F5 | [1/3] | 🟡 | Plain-path parsing regresses comma-separated paths without spaces (`583829c`): `src/a.py,src/b.py` is one path, which hides a two-unplaced-path warning. Split on commas and whitespace | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:257 | general | BOB |
| F6 | [1/3] | 🟡 | F9 is incomplete: a cardinal sin or blocker shown but not answered when the developer stops gets no minutes line; the fallback covers only unwalked non-blockers and questions | plugins/specflow/skills/spec-workflow/references/review/design/triage.md:38 | T-075 | BOB |
| F7 | [1/3] | ⚪ | The F8/F15 ruling is not carried into SR-RVD-019, 020, 021 and 013, which still read without the profile limit; SR-RVD-006's "since that spec is not `quick`" reads oddly, and it does not say which tier a triggered `quick` design takes | plugins/specflow/skills/spec-workflow/references/review/design/triage.md:15 | T-075 | ALICE |
| F8 | [1/3] | ⚪ | The template's spec map lacks the profile and per-artifact approval columns SR-RVX-019 lists | plugins/specflow/skills/spec-workflow/templates/cross-spec-review.md:9 | general | BLAKE |
| F9 | [1/3] | ⚪ | The pre-pass severities (`blocker`, `non-blocker`) are not mapped to the core's (`blocking`, `non-blocking`) | plugins/specflow/skills/spec-workflow/references/review/design/pre-pass.md:6 | general | BLAKE |
| F10 | [1/3] | ⚪ | The role-change pattern misses "You are now a friendly reviewer.", although SR-RVC-044 quotes "you are now …"; advisory only | plugins/specflow/skills/spec-workflow/scripts/review/adversarial_signal_scan.py:33 | general | BLAKE |
| F11 | [1/3] | ⚪ | `conversion-receipt` reads `qa-log.md` through a relative path without resolving symlinks, so a linked intake folder can make the validator read outside the repository; read-only | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:735 | general | BLAKE |
| F12 | [1/3] | ⚪ | SR-RVX-006 and the SR-RVX-073 tag say "unreadable files"; unreadable folders are scan errors too since `6786e67` | plugins/specflow/skills/spec-workflow/references/review/cross-spec.md:30 | T-076 | ALICE |
| F13 | [1/3] | 🟡 | 4 touched tests pass against the pre-change code: test_a_sources_item_with_no_qa_log_draws_no_finding, test_a_sources_path_outside_the_repo_draws_no_receipt_finding, test_a_verdict_followed_by_free_text_is_an_error, test_a_verdict_with_a_note_and_a_full_stop_passes | tests/specflow/contract/test_checks.py | general | mech-check |
| F14 | [1/3] | 🟡 | 2 touched tests pass against the pre-change code: test_every_fence_form_opens_a_flowchart, test_design_without_a_placement_section_is_not_checked | tests/specflow/contract/test_phase_checks.py | general | mech-check |
| F15 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_header_row | tests/specflow/fixtures/sessions/convert-prd-adopted/tests/test_export.py | general | mech-check |
| F16 | [1/3] | 🟡 | 1 touched test passes against the pre-change code: test_convert_prd_ships_and_every_cnv_rule_points_inside_it | tests/specflow/release/test_boundary.py | general | mech-check |

Overlap: F3 and F4 are `check_links.py` reverse cases of cycle-1 F10 and F18, with F12 the matching rule wording. F1 and F11 are the receipt check. F2 and F8 are the cross-spec template. F6, F7 and F9 are design-review rule text. F13 to F16 are replay facts.

## Alice

Implementation-aware review on the legacy consensus engine. Findings: F1, F7, F12. Verified every fixed cycle-1 finding and the SR-VAL renumbering of `0207afb`; did not re-raise the settled F2, F7, F16.

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

Blind lens (spec only). Findings: F2, F8, F9, F10, F11. Verified ART-003.9 to 11, REV-001.1 to 7 and 9, CNV-001.1 to 9 as compliant. No ledger re-raise was dismissed.

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

Codex, exit 0, first run. FIX holds four items (F3, F4, F5, F6); VERIFY and KNOWN are empty.

R1: fail
R2: pass
R3: pass
R4: fail
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

Tests: 544 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-25)

The lead ruled on each finding under the developer's standing authorization, as in cycle 1; no ruling edits an approved artifact. The cycle has no 🔴 or 🟠, so the rework below is the tail sweep and no cycle 3 runs.

- F1: fix. SR-CNV-026, the template line, and the fix text name the accepted form: one of the three verdicts, an optional parenthetical note, an optional full stop, as in `COMPLETE (short note).`
- F2 and F8: fix. The template's Verdict line reads GO or NO-GO per SR-RVX-063, and the spec map gains Profile, Approvals, and Verdict columns (READY, FIX, RESHAPE, NOT READY) per SR-RVX-019 and 062.
- F3 and F4: fix, one test each. `resolvable_numbers()` takes a number only from an entry that resolves inside the root; `sources()` seeds `seen` with both resolved bases before either walk.
- F5: fix. `location_paths()` splits plain text on commas and whitespace; a regression test with two unplaced paths and no space.
- F6: fix. SR-RVD-012 writes the open minutes line for every finding left without a decision, a cardinal sin or blocker shown but not answered included; the rubric follows.
- F7: fix by wording. SR-RVD-019, 020, and 021 decide a `standard` spec's tier, with a pointer to SR-RVD-006 for a `quick` one; SR-RVD-006 says a triggered `quick` design takes the tier its Tier 2 and Tier 3 conditions give, "since the spec should not stay `quick`". SR-RVD-013 is left as is: it settles a disagreement, not the profile.
- F9: fix. SR-RVD-116 maps the pre-pass terms to the core's four severities (SR-RVC-051).
- F10: fix. The role-change pattern also matches "you are now a/an/the ..."; a test with the quoted sentence.
- F11: fix. `conversion_receipt` skips a log whose resolved path leaves the repository, as `config.py` and `deps.py` do; one test.
- F12: fix. SR-RVX-006 and the SR-RVX-073 tag say "unreadable files or folders".
- F13 to F16: accepted as facts (ledger entries added), each with its cause in the run notes.

### Outcome (2026-10-25)

Decisions and ledger `89acab3`; sweep `e7bd417` (F1 to F12); loop fix `76a3ee6` (Pat's MEDIUM); this record in the commit after it. The loop converged at cycle 2: no 🔴 or 🟠 and the codex guard not fired, so no cycle 3 runs.

- Fail-first: the five code tests of the sweep each failed before the fix (`test_a_numbered_intake_link_outside_the_root_never_resolves`, `test_a_link_from_the_specs_tree_to_the_intake_base_scans_its_files_once`, `test_plain_paths_split_on_a_comma_without_a_space`, `test_any_you_are_now_role_is_a_role_change`, `test_a_sources_item_linked_outside_the_repo_is_not_read`).
- F1: the template line became a placeholder, `<COMPLETE, AWAITING_DECISION, or INCOMPLETE; an optional (note) and full stop>`; the template-line test asserts it is an error, and the old pipe form keeps its own test (`test_the_three_verdicts_as_alternatives_are_an_error`).
- F3: the number filter uses `os.path.realpath`, not `resolve()`, since a link loop raises `RuntimeError` on Python 3.10; a 3.10 probe with a self-looping intake item ran without a traceback.
- F7: the profile limit is written into SR-RVD-019, 020 and 021; SR-RVD-013 is unchanged, as ruled.
- Pat (patch review of `89acab3..e7bd417`, sonnet): CLOSURE resolved for all twelve findings. MEDIUM, confirmed and fixed in `76a3ee6`: the new `conversion-receipt` guard called `Path.resolve()`, which raises on a symlink loop under 3.10. The bug-fix sweep found the same call in `check_links.py`'s `outside()`, which crashed on a looped `.md` link. Both use `realpath` now, each with a test that errored on 3.10 before the fix. LOW, rejected: the widened role-change pattern also takes "you are a trusted reviewer", which is a role assignment in SR-RVC-044's sense, and the scan is advisory (SR-RVD-017).
- Gates at `76a3ee6`, Python 3.14 and 3.10: scripts 12, release 54, contract 387, rules 58, review 41, all OK; `validate.py`, `check_rules.py` with the CI areas and with none, and `verify_release.py` pass; ruff reports only the three pre-existing ISC004 hits; `status` reports 00007 at `verification`, `stale` empty, every gate open.
