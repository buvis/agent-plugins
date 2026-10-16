---
prd: docs/dev/project-management/specs/00005-behavior-rules/requirements.md
review: 1
date: 2026-10-16
head_sha: 641d325de8eac75ecfb03eed26ade435db984ea5
codex_thread_id: 01a1462c-40e0-7d20-bc7a-ba2cd6e77f9d
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00005-behavior-rules

Diff range: `392098d9f6a154dfa8e6f4a0daa64d4c0b734900..641d325de8eac75ecfb03eed26ade435db984ea5`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 1, a full review of branch `feature/specflow-00005` against `master` (`392098d..641d325`). There is no autopilot `state.json` and no wip PRD. The target is spec 00005's `requirements.md`, with `design.md` as the design doc. All three tasks (T-070, T-071, T-069) are complete. Findings are reported here, not written as tasks.

No reviewer found a 🔴 or 🟠. All 18 findings are 🟡 or ⚪. Three themes have 3/4 agreement: the new guard tests that pass at base (F1), and `checks.py` and `test_checks.py` now over the 800-line limit (F2, F3). The defects the lead confirmed are: `status` lists each open marker twice (F6), `test_eval_formats.py` fails when run alone (F7), a duplicate tag in the same file is not caught (F9), plan values in the inventory are untyped (F11), and `portable-links` misses root-level paths (F4). Blake's F8 and F10 are coverage gaps that the design defers to later specs on purpose. They need a ruling, not a code fix in this spec.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run refused for lack of input, as in every 00004 cycle: the sandbox blocked his read-only `cat` (`sandbox initialization rejected`). The output had one `[BOB] ⚪ Review unverified` line and every `R{n}` set to fail. That is the refusal shape in substance, though not the literal `Cannot statically verify` pattern, so the one retry used the inlined prompt (253 KB: context, diff, and the persona with the two edits). The first output is kept at `docs/dev/tmp/bob-output-00005c1-first.txt`. His retry put a `- ` bullet before each `[BOB]` line, so consolidation read a stripped copy (`bob-output-00005c1-lines.txt`). The `codex_thread_id` above belongs to the retry.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run)
- Eve: ⏸️ Disabled. `doubt_reviewer` resolved to codex, since the spec has no frontmatter. With no state file there is no record of codex-implemented tasks, so the guard cannot fire.

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). The review is degraded, not invalid.
- Gate: `review-stage` ran the seven CI steps of `validate.yml` through a worktree-local `docs/dev/tmp/review-tools/gate.sh` (exit 0). It could not parse the unittest counts, so the counts come from the logs: `scripts` 12 OK, release 52 OK, contract 321 OK, rules 53 OK. `validate.py`, `check_rules.py --area VAL` and `verify_release.py` all exited 0.
- Python 3.10.22, the version CI pins: the lead ran rules (53 OK) and contract (321 OK).
- Fail-first replay: `python3 -m pytest` reported 4 touched tests passing at base. The lead redid the replay with unittest, in a worktree at `392098d` with HEAD's contract tests copied in. Three tests pass at base: `test_closed_fences_accept_a_longer_closing_fence`, `test_portable_links_skip_urls_relative_paths_and_slashed_words` and `test_requirement_source_skips_bugfix_and_withdrawn_requirements`. `test_placeholders_skip_inline_code_and_fences_and_a_design_reason` fails at base in all four seeded subTests, which pytest hides. So F1 covers three tests, not four. No tautological test shapes were reported.
- Consolidation corrections (by hand): the script merged nothing across the 800-line findings. Bob's single finding covering both files was folded into F2 and F3, which makes each [3/4]. Bob's and Blake's root-path findings became F4, and their `check_exists` findings became F5. The `[MECH]` replay row was absorbed into F1, with `mech-check` added as a finder. The lead downgraded Carl's `check[6:]` row from 🟡 to ⚪ (F13): `"evals/"` is six characters, so the slice is correct, and the change is style only. Refs were renumbered from the script's `R1`..`R21`.
- Carl's shell ran the suites without `PYTHONDONTWRITEBYTECODE` and left `__pycache__` folders under `plugins/`, `tools/` and `tests/`. The lead removed only those ignored folders (`git clean -X -d -f -- plugins tools tests`). Afterwards the tree is clean.
- Lead's checks:
  - F2 and F3: `wc -l` gives 909 and 850.
  - F4: read `MACHINE_PATH` (`checks.py:89-92`). The `/` branch requires at least one `segment/`, so `/tmp` and `/config.json` never match, and `$HOME` has no branch.
  - F5: read `check_exists` (`check_rules.py:187`). A multiline `^\s*def name\(` search also matches a line inside a docstring. A `# def` comment does not match, so Blake's commented-out case is refuted.
  - F6: read `status.py:31,194` and `checks.py:778-813`. `open-markers` reports at error level and is not in `NOT_PER_SPEC`, so `spec_status` adds a `validation failed: open-markers` blocker to the implementation gate for each marker that `marker_blockers` already reports. Alice reproduced it. Gate states do not change, since the gate is already closed. Only the blocker list repeats.
  - F7: `python3 -B -m unittest discover -s tests/specflow/rules -p test_eval_formats.py` fails with `ModuleNotFoundError: No module named 'check_rules'`.
  - F9: read `package_tags` and `presence_errors` (`check_rules.py:167-174,284-286`). A second tag in the rule's own file is appended under the same path and then filtered out by `other != shown`.
  - F11: read `inventory.schema.json:9`. `plans` is `{"type": "object"}` with no constraint on values, so a non-string value reaches `root / rel` and raises a `TypeError` instead of producing an error line.
  - F12: read `plan_rows` (`check_rules.py:141`). An empty matrix produces no error of its own. Any rule that cites `A:<row>` would then report an unknown row, so the problem only goes unnoticed when nothing cites the plan.
  - F17: `PLAN_SOURCE` captures exactly one letter, so `match[1] in "DR"` behaves like set membership. That half is refuted. The single-letter key limit stands.
- No verification-check queue was written, no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [3/4] | 🟡 | Three new guard tests only assert that nothing is reported, so they pass at base, where the check does not exist: `test_closed_fences_accept_a_longer_closing_fence`, `test_portable_links_skip_urls_relative_paths_and_slashed_words`, `test_requirement_source_skips_bugfix_and_withdrawn_requirements`. Add a seeded positive control to each, in the file the sample edit touches, so each test fails if its check goes silent. The fourth test the replay flagged (`..._placeholders_skip_...`) fails at base under unittest. Confirmed by the lead's unittest replay | tests/specflow/contract/test_checks.py:759 | T-071 | ALICE, BOB, CARL, mech-check |
| F2 | [3/4] | 🟡 | `checks.py` is 909 lines, over the 800-line limit (T-071 added 156). Move the five structural checks (`placeholders`, `open-markers`, `portable-links`, `closed-fences`, `requirement-source`) to a sibling module, keeping their `CHECKS` registration | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:909 | T-071 | ALICE, BOB, CARL |
| F3 | [3/4] | 🟡 | `test_checks.py` is 850 lines, over the 800-line limit (T-071 added 197). Move `StructuralRuleTest` to its own test file | tests/specflow/contract/test_checks.py:850 | T-071 | ALICE, BOB, CARL |
| F4 | [2/4] | 🟡 | `portable-links` misses absolute paths at the root level, such as `/tmp`, `/etc`, `/config.json` and `/foo.md`, because `MACHINE_PATH` requires a `segment/` after the first slash. `$HOME/x` is not caught either. VAL-001.10 asks for a warning on absolute and home-directory paths. Cover them, and add regression cases next to the existing skip cases (a bare `/` word must still pass) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:90 | T-071 | BOB, BLAKE |
| F5 | [2/4] | 🟡 | `check_exists` treats a `test:` check as present when `def <name>(` starts any line, including a line inside a docstring, so a missing test can pass CI. Parse the file with `ast` and look for a function definition of that name | tools/specflow/check_rules.py:187 | T-070 | BOB, BLAKE |
| F6 | [1/4] | 🟡 | `open-markers` is not in `NOT_PER_SPEC`, so `status` reports every unaccepted upstream marker twice: once as the `marker_blockers` gate blocker, and again as `validation failed: open-markers: ...` on the implementation gate. The comment at `status.py:30` says checks that blockers already cover are skipped. Add `open-markers` to that set, with a test | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:31 | T-071 | ALICE |
| F7 | [1/4] | 🟡 | `test_eval_formats.py` cannot run alone: line 10 does `import check_rules` before anything puts `tools/specflow` on `sys.path`, and only the later `from test_check_rules import ...` does that, as a side effect. It passes in CI only because discovery imports `test_check_rules` first. Confirmed by the lead's run | tests/specflow/rules/test_eval_formats.py:10 | T-069 | ALICE |
| F8 | [1/4] | 🟡 | VAL-001.11's second sentence ("THE AGENT SHALL NOT record an approval of such an artifact") maps only to the structural SR-VAL-004 (`validator:closed-fences`). No rule or eval covers the approval ban, and `hash --json` still emits an approval record for an artifact with an unclosed fence. T-071's Verify defers the ban to 00006's approval procedure, but the PRD's own risk is a rule whose check does not cover its whole obligation | tools/specflow/rules/inventory.json:157 | T-071 | BLAKE |
| F9 | [1/4] | 🟡 | A rule tag repeated inside its own file is not caught: `presence_errors` drops entries where `other == shown`, so two `[SR-VAL-001]` items in `validation-rules.md` pass. RULE-001.2 asks for "exactly one" file, and RULE-001.5 fails a tag that "appears in two". Design §5.4 says "a second file", so the code follows the design. Confirmed by the lead's reading and Blake's probe | tools/specflow/check_rules.py:284 | T-070 | BLAKE |
| F10 | [1/4] | 🟡 | CI runs `check_rules.py --area VAL` only. The unfiltered run still fails for about 400 rules in the other areas, which is expected at this stage, but nothing in the repo yet makes CI or `verify_release.py` run unfiltered before a release. RULE-001.5 says no release-slice exemption applies. The design stages this on purpose. The risk is that the switch to an unfiltered run is never made | .github/workflows/validate.yml:43 | T-070 | BLAKE |
| F11 | [1/4] | 🟡 | `inventory.schema.json` types `plans` only as an object, so `{"A": 42}` passes the schema and then crashes `plan_rows` at `root / rel` with a traceback, which breaks the collect-then-exit pattern. Constrain the keys and require non-empty string values | tools/specflow/rules/inventory.schema.json:9 | T-070 | BOB |
| F12 | [1/4] | 🟡 | A matrix with only its header and separator rows is accepted, because `plan_rows` counts tables but never requires a data row. Rules that cite the plan would still fail with unknown-row errors, so this only goes unnoticed when no rule cites the plan. Reject an empty matrix with a targeted message | tools/specflow/check_rules.py:141 | T-070 | BOB |
| F13 | [1/4] | ⚪ | `check[6:]` could be `check.removeprefix("evals/")`, to match `check_exists`. The slice is correct; this is style only (the lead downgraded it from 🟡) | tools/specflow/check_rules.py:293 | T-069 | CARL |
| F14 | [1/4] | ⚪ | `closed_fences` re-implements the fence open/close logic of `scan_lines` (`canonical.py:44-47`). The two can drift, and fence tracking decides what the hash and the scans leave out. Consider having `scan_lines` expose the fence that is still open and its start line | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:847 | T-071 | ALICE |
| F15 | [1/4] | ⚪ | `open_markers` rebuilds the `acceptedMarkers` set and the per-artifact marker loop that `status.marker_blockers` already has (`status.py:92-107`). One shared helper would serve both, and it fits with F6 | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:792 | T-071 | ALICE |
| F16 | [1/4] | ⚪ | `test_every_approved_plan_a_row_has_a_rule` hard-codes `469 rows read` from the live Plan A file, so adding any approved row breaks the test even though the checker is correct | tests/specflow/rules/test_check_rules.py:135 | T-070 | ALICE |
| F17 | [1/4] | ⚪ | `PLAN_SOURCE` accepts only single-letter plan keys, while the design lets the `plans` map take any key. The claim that `match[1] in "DR"` is a loose substring test is refuted: the group is exactly one letter | tools/specflow/check_rules.py:49 | T-070 | ALICE |
| F18 | [1/4] | ⚪ | Plan B is not in the inventory yet, so RULE-001.1 is met for Plan A only. This is intended: the T-070 contract says T-079 (00007) adds key `B` | tools/specflow/rules/inventory.json:3 | T-070 | BLAKE |

Overlap: F6 and F15 touch the same marker logic and can be fixed together. F2 and F3 are one split. F1's positive controls go into the moved test file from F3. F8 and F10 are scope questions for later specs (00006, and 00006/00007/00009). Fixing them here would change the approved design.

## Alice

Implementation-aware review on the legacy consensus engine. She ran `check_rules.py --area VAL` (33 criteria covered), the rules suite (53 OK) and the contract suite (321 OK). She also reproduced the `status` double report on a scratch spec. Findings: F1, F2, F3, F6, F7, F14, F15, F16, F17.

R1: pass
R2: fail
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: fail

## Blake

Blind lens (spec only). He ran both suites and `check_rules.py --area VAL`, and checked `criteria.json` against design §5.4 (33 IDs; missing, empty, malformed, duplicate and unknown IDs are all rejected, and a decision-only source is refused). He found the five checks registered, `open-markers` reading only upstream artifacts, and the session and eval formats enforced. He also probed same-file duplicate tags and the path regex on a scratch copy. Findings: F4, F5, F8, F9, F10, F18.

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
B15: fail
B16: pass
B17: pass
B18: pass
B19: pass

## Bob

Codex, exit 0, after one retry (inlined). His first run refused for lack of input (see Agent Status). In the retry, FIX holds six 🟡 items (F1, F2/F3, F4, F5, F11, F12), and VERIFY and KNOWN are empty.

R1: fail
R2: fail
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0, first run. He read the context and diff and ran the suites. Findings: F1, F2, F3, F13.

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: fail

Verdict: 18 findings

Tests: 438 passed, 0 failed, 0 skipped (suite run this cycle)
