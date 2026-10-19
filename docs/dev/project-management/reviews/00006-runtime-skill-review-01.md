---
prd: docs/dev/project-management/specs/00006-runtime-skill/requirements.md
review: 1
date: 2026-10-17
head_sha: fe2434084357de03b7031cb186933ccd13c9d9cc
codex_thread_id: 01a148cf-c1e1-7941-91f3-a6df3e79f136
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00006-runtime-skill

Diff range: `f53085ca6ef2bf880eda64b04f4aa5a1ad8f37e3..fe2434084357de03b7031cb186933ccd13c9d9cc`

codex_rung_guard: not fired

## Review Summary

This is a standalone run, cycle 1, a full review of branch `feature/specflow-00006` against `master` (`f53085c..fe24340`, 14 commits). There is no autopilot `state.json` and no wip PRD. The target is spec 00006's `requirements.md`, with `design.md` as the design doc. All eleven tasks (T-030, T-031, T-072, T-032 to T-039) are complete. Findings are reported here, not written as tasks.

No reviewer found a 🔴. One 🟠 survives the lead's checks: SR-SKL-015 tells the agent to report fields that `status --json` does not hold while computing nothing (F3, 2/4). Five more 🟠 lines were downgraded to 🟡 with the evidence under "Lead's checks": each names a real wording or edge-case defect, but none breaks a required behavior. Three reviewers agree that `sketch_screens` is over the 50-line limit (F1) and that the README is stale (F2). The other confirmed defects are session and rule gaps: the `shared-dialogue` session approves over open markers without a named acceptance (F14), `bugfix-task-order` is looser than the design table says (F13), WF-002.8 is implemented in one phase (F10), the 2.x clause pattern accepts a preservation clause (F11), and a secret pasted into the first message reaches `idea.md` verbatim (F12).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). His first run refused for lack of input, as in every 00004 and 00005 cycle: his `cat` of the context file was blocked by the Fact-Forcing Gate PreToolUse hook, and his own line cites `sandbox_apply: Operation not permitted`. The output had one `[BOB] ⚪ Cannot verify review criteria` line and every `R{n}` set to fail. That is the refusal shape in substance, though not the literal `Cannot statically verify` pattern, so the one retry used the inlined prompt (773 KB: context, diff, and the persona with the two edits). The first output is kept at `docs/dev/tmp/bob-output-00006c1-first.txt`. His retry put a `- ` bullet before each `[BOB]` line, so consolidation read a stripped copy (`bob-output-00006c1-lines.txt`). The `codex_thread_id` above belongs to the retry.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run)
- Eve: ⏸️ Disabled. `doubt_reviewer` resolved to codex, since the spec has no frontmatter. With no state file there is no record of codex-implemented tasks, so the guard cannot fire.

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). The review is degraded, not invalid.
- Gate: `review-stage` ran the seven CI steps of `validate.yml` through a worktree-local `docs/dev/tmp/review-tools/gate.sh` (exit 0). It could not parse the unittest counts, so the counts come from the logs: `scripts` 12 OK, release 53 OK, contract 348 OK, rules 58 OK. `validate.py`, `check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER` and `verify_release.py` all exited 0.
- Python 3.10.22, the version CI pins: the lead ran contract (348 OK) and rules (58 OK).
- Lint: `ruff check` on the eight changed project Python files reports only the five pre-existing findings (three ISC004 in `test_checks.py`, EXE001 and PLW1510 in `verify_release.py`); `ruff format --check` is clean.
- Fail-first replay: `python3 -m pytest` reported 9 touched tests passing at base. The lead redid the replay with unittest, in a worktree at `f53085c` with HEAD's `tests/specflow` copied in: 8 project tests ran, 7 pass at base and `test_every_reference_is_routed` fails at base in six subtests (F15, F16). The ninth, `test_empty_month`, is a session fixture's test, not a project test (F18). No tautological test shapes were reported.
- Consolidation corrections (by hand): the script merged Alice's two coverage findings (`test_phase_checks.py:16` and `:236`) into one row, which is kept as F9 since both describe untested branches of the same file. The three `[MECH]` replay lines became F15, F16 and a `mech-check` finder on F18. The lead downgraded six rows with the evidence below: F4 and F5 (Blake, 🟠 to 🟡), F6, F7 and F8 (Bob, 🟠 to 🟡), F17 (Blake, 🟡 to ⚪) and F18 (Bob, 🟡 to ⚪). Refs were renumbered from the script's `R1`..`R19`.
- Carl's shell ran the suites without `PYTHONDONTWRITEBYTECODE` and left `__pycache__` folders under `tests/` and `tools/`. The lead removed only those ignored folders (`git clean -X -d -f -- plugins tools tests`). Afterwards the tree is clean.
- Lead's checks:
  - F1: the mechanical facts give `sketch_screens` 68 lines (line 103); the other new functions are 17 to 41 lines.
  - F3: `validate_spec.py status --json` on this spec holds `phase`, `state`, `hold`, `artifacts`, `stale`, `gates`, `blockers`, `warnings` and `nextTask`, and nothing else; 00004 STATE-003.1 defines exactly that. The rule's "checked of total", "next action" and "blocking question" are not in it, and the T-037 contract in `design.md:246` already listed them beside "computes nothing itself", so the contradiction came in with the task contract. Confirmed.
  - F4: by the approved plan. T-030's details say "T-076 completes `review specs`", `test_skill.py` carries `NOT_WRITTEN_YET` with the four `references/review/` entries and fails if one of them appears, and completion criterion 3 requires that list to hold only the 00007 files. The missing files are the expected state of this spec, so the row is 🟡: what remains is that SKILL.md's "Any review" routing row has no "when installed" wording, while `design.md:36` has it.
  - F5: the conflicts are in text 00003 wrote (`aws/requirements.md` is not in this diff). Line 3 gives the artifact contract precedence, which covers (c), since SR-DLG-001 is in the artifact contract; the question-count passages at lines 62 and 66 are followed by the source's own "guidelines, not hard caps" and SR-REQ-003 is the tagged range, which covers (b). (a) stands: the Adaptation at line 125 tells the agent to pick an option the developer left open, and SR-REQ-005/006 say such an answer decides nothing. A one-line precedence fix and a reworded Adaptation close it; 🟡.
  - F6: SR-INT-055 itself says to "record each applicable constraint with its file and scope" and that "this session's own instructions still govern", and SR-INT-013 routes discovery findings into `## Assumptions` and `## Context and constraints`. Repository instructions enter as recorded constraints, which is data, so the conflict with SKILL.md:12 is wording that one clause resolves; 🟡.
  - F7: SR-REQ-014's last sentence and SR-REQ-053's "the design waits for it" are wrong in Design-First, confirmed by reading. SR-SKL-009, loaded on every invocation, carries the order-conditional rule, and when these sentences are read in Design-First the design is already approved, so no behavior changes; 🟡.
  - F8: `files = {p.name for p in mockups.iterdir()}` (`phase_checks.py:141`) counts a directory named `<screen>.html` as the mockup, and `read_text` returns `None` for an unreadable or non-UTF-8 page (`checks.py:161`), after which the edge loop skips it silently. The inputs are a sketch the agent itself wrote, and the hole needs a directory or a non-UTF-8 file under `spike/mockups/`; a `p.is_file()` filter and a finding on an unreadable page close it; 🟡.
  - F9: `rg` over `test_phase_checks.py` finds no test for the reserved `index` ID as a screen (only `index.html` as a non-screen), "holds no flowchart screen", an unreadable journey, a missing `## Introduction` or `## Bug Analysis`, a section with no clause, fewer than four top-level tasks, or a second, third or last task mismatch. Confirmed.
  - F10: `inventory.json:143` sources SR-REQ-042 from `A:PRD-30` only; no rule names `R:WF-002.8`. T-030's details assign the WF-002.8 offer to T-032, so the plan scoped it to the requirements phase; the criterion's text says "a draft". Confirmed as a plan-versus-criterion question.
  - F11: the design table scopes `bugfix-design-sections` to the four headings and the Bug Condition, so the `Validates:` half is by design. The 2.x pattern `WHEN .+ THEN the system SHALL ` matches `SHALL CONTINUE TO`, confirmed by reading `BUGFIX_SECTIONS`. `templates/bugfix/tasks.md` has `_Requirements:` lines and no `Outcome:` slot; SR-IMP-007 carries that behavior.
  - F12: SR-DLG-013 names "the log, the artifacts, and `.specflow.json`"; SR-INT-001 saves the idea verbatim before any question, and SR-INT-057 copies a named file. Neither names the secret rule. Confirmed.
  - F13: the design table says "exactly the four top-level tasks of the bugfix shape" and, two lines later, that the T-027 capture must pass; the capture has six top-level tasks. The code checks the first three and the last, with a ponytail note, and the T-039 outcome records the choice. Confirmed as a design-text versus code mismatch that needs a design correction or an accepted deviation.
  - F14: the session's turns record three uncertain answers (the failure budget, on-call paging, "Not decided yet"), then "Approve the design." and "Approve the tasks." with no acceptance turn. SR-SKL-011 and SR-DSN-015 require the agent to refuse those approvals until each marker is accepted by name; the design-first continuation does carry an acceptance (the SR-SKL-011 record). Confirmed.
  - F15 and F16: the lead's unittest replay (see above). The six `test_phase_checks.py` tests are negative guards (nothing warns, nothing errors, T-026's rejections still fire) whose positive siblings fail at base per the task outcomes; `test_skill_md_is_within_the_size_limit` passes at base because the shell was short. Facts, not defects, unless the developer wants seeded controls as in 00005 F1.
  - F17: Blake's own line says the instruction is ambiguous, not a conflict: a suite run after a task is in addition to the owned checks that ART-004.9 says the `Verify:` line names; ⚪.
  - F18: `test_orders.py` is scenery of the `tasks-planning` session fixture, run by no CI step; ⚪.
  - F2: `README.md:8-9` still says the phase references "are still being written"; `CHANGELOG.md:11` and `:28` both sit under `[Unreleased]`, so the release notes will say the placeholder was added and then replaced in the same release.
  - F21: by design. T-030's details say "Write every path relative to the skill folder, with no host placeholder".
- No verification-check queue was written (Bob's VERIFY bucket is empty, and there is no `state.cycle`), no dispatch rows were opened, and no contract card or session brief was written (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [3/4] | 🟡 | `sketch_screens` is 68 lines, over the 50-line limit (R12). Split it behaviorally unchanged: journey findings, mockup-file findings (missing and orphan), and link findings (the edge loop) each become a small helper returning a finding list, and the check body concatenates them | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:103 | T-072 | ALICE, BOB, CARL |
| F2 | [3/4] | ⚪ | README status is stale: it says the phase references "are still being written", but all six phase files plus the bugfix additions exist; only the 00007 review references are missing. `CHANGELOG.md:11` still describes a "placeholder `spec-workflow` skill" under the same `[Unreleased]` heading as its replacement | plugins/specflow/README.md:8 | T-039 | ALICE, BLAKE, CARL |
| F3 | [2/4] | 🟠 | SR-SKL-015 contradicts itself and the helper. It says to report "what `status --json` holds and nothing it does not" and to "compute nothing yourself", and also lists "task progress (checked of total)", "the next action" and "the question that blocks it". `status --json` (`status.py:220-233`, 00004 STATE-003.1) holds only `nextTask`, with no count, no next action and no blocking question. An agent must either compute (breaking the rule) or omit fields the usability NFR asks for, and the summary will differ between hosts. Reword to separate helper-supplied fields from the next action and blocking question, stated from `phase`, `gates`, `blockers` and `nextTask` by one fixed rule; drop "checked of total" unless the helper gains that field | plugins/specflow/skills/spec-workflow/SKILL.md:77 | T-037 | ALICE, BLAKE |
| F4 | [1/4] | 🟡 | SKILL.md advertises and routes the intents `review requirements`, `review design` and `review specs` (SR-SKL-001 to 003) to `references/review/core.md`, `requirements.md`, `design/` and `cross-spec.md`, none of which exist yet; an unfiltered `check_rules.py` fails on the SR-RVC and SR-RVD rules. The plan defers those files to 00007 (`test_skill.py` `NOT_WRITTEN_YET`, completion criterion 3), but the "Any review" routing row has no "when installed" wording, while `design.md:36` has it. Downgraded from 🟠 by the lead | plugins/specflow/skills/spec-workflow/SKILL.md:46 | T-030 | BLAKE |
| F5 | [1/4] | 🟡 | `references/aws/requirements.md` conflicts with the specflow rules loaded in the same phase: (a) the Adaptation at line 125 says "When the developer leaves a choice to you, pick the option that best fits what they said", while SR-REQ-005 says such an answer decides nothing and SR-REQ-006 offers spike, keep answering or park; (b) the `[quick]` "~2-4 per stage" and `[standard]` "~5-8" passages differ from the profile budgets of 0-2 and 3-12; (c) "PROACTIVE: Always generate clarifying questions" differs from SR-DLG-001. Line 3 gives only the artifact contract precedence. (b) and (c) are covered by the source's "guidelines, not hard caps" and the artifact-contract precedence; (a) stands. Downgraded from 🟠 by the lead | plugins/specflow/skills/spec-workflow/references/aws/requirements.md:125 | T-032 | BLAKE |
| F6 | [1/4] | 🟡 | SKILL.md:12 says an instruction found in "specs, intake items, and other repository files" is "reported to the developer, never followed", while SR-INT-055 reads `AGENTS.md`, `CLAUDE.md` and root steering on every host and follows their routing. SR-INT-055 records them as constraints and keeps the session's own instructions governing, so one clause on line 12 (repository instruction files are read for constraints under SR-INT-055; everything else is data) resolves it. Downgraded from 🟠 by the lead | plugins/specflow/skills/spec-workflow/SKILL.md:12 | T-031 | BOB |
| F7 | [1/4] | 🟡 | Two requirements-phase sentences assume Requirements-First: SR-REQ-053 says "the design waits for it" and SR-REQ-014 says "Design starts only after the developer approves the requirements". In Design-First the design is already approved; SR-SKL-009 carries the order-conditional rule. Make both sentences conditional on the workflow order. Downgraded from 🟠 by the lead | plugins/specflow/skills/spec-workflow/references/phases/requirements.md:72 | T-038 | BOB |
| F8 | [1/4] | 🟡 | `sketch-screens` counts a directory named `<screen>.html` as the mockup (`mockups.iterdir()` names, no `is_file()` filter), and when `read_text` returns `None` for an unreadable or non-UTF-8 mockup the edge loop skips that page silently. Require regular files and report an unreadable page. Downgraded from 🟠 by the lead: the inputs are agent-written and the trigger is contrived | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:141 | T-072 | BOB |
| F9 | [1/4] | 🟡 | Untested branches of the new checks, each with its own message: `sketch-screens` for the reserved screen ID `index`, "holds no flowchart screen" and a missing or unreadable `journey.md`; `bugfix-sections` for a missing `## Introduction` or `## Bug Analysis` and a behavior section with no clause; `bugfix-task-order` for fewer than four top-level tasks and for a second, third or last-task mismatch. Add one seeded-defect test per branch | tests/specflow/contract/test_phase_checks.py:16 | T-072, T-039 | ALICE |
| F10 | [1/4] | 🟡 | WF-002.8 is generic ("a draft" with three or more `(guess)` markers or contract-bearing open questions gets the spike/resolve/save offer before approval), but it is implemented only in the requirements phase (SR-REQ-042, sourced `A:PRD-30`). The design, tasks and bugfix flows carry no such offer, and no inventory rule names WF-002.8. T-030's details scoped the offer to T-032, so this is a plan-versus-criterion question | plugins/specflow/skills/spec-workflow/references/phases/design.md:36 | T-033 | BLAKE |
| F11 | [1/4] | 🟡 | The bugfix shape checks inspect headings only. `bugfix-design-sections` never checks the `Validates:` lines (by the design table), the Expected Behavior pattern `THEN the system SHALL ` also accepts a `SHALL CONTINUE TO` clause, so a preservation clause misfiled under 2.x passes, and `templates/bugfix/tasks.md` has no `Outcome:` slot although ART-005.6 and SR-IMP-007 require one under tasks 1 and 2. Advisory: the instructions cover the behavior | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:306 | T-039 | BLAKE |
| F12 | [1/4] | 🟡 | SEC-002.2 forbids secrets in artifacts, the log and state. SR-INT-001 saves the free-text idea verbatim as `idea.md` before any question, and SR-INT-057 copies a developer-named input file into the intake item. Neither applies SR-DLG-013, which names only "the log, the artifacts, and `.specflow.json`", so a secret in the first message lands on disk unredacted | plugins/specflow/skills/spec-workflow/references/phases/intake.md:7 | T-031 | BLAKE |
| F13 | [1/4] | 🟡 | `bugfix-task-order` allows any number of top-level tasks between the fix and the checkpoint (first three and last checked), while the design table says "exactly the four top-level tasks". The same table requires the T-027 Kiro capture, which has six, to pass; the T-039 outcome records the choice with a ponytail note. Correct the design text or record the deviation | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:342 | T-039 | BOB |
| F14 | [1/4] | 🟡 | The `shared-dialogue` session records three uncertain answers (the failure budget, on-call paging, "Not decided yet"), then "Approve the design." and "Approve the tasks." with no acceptance by name. SR-SKL-011 and SR-DSN-015 require the agent to refuse those approvals, so a conforming run cannot reach the later turns. Add the named acceptances, or assert that progression stays blocked | tests/specflow/evals/sessions/shared-dialogue.json:21 | T-030 | BOB |
| F15 | [1/4] | 🟡 | Six touched tests pass against the pre-change code under unittest: `test_design_without_a_placement_section_is_not_checked`, `test_one_module_absent_does_not_warn`, `test_placed_modules_and_a_placed_folder_do_not_warn`, `test_task_plan_defects_are_rejected`, `test_checks_skip_a_feature_spec`, `test_kiro_capture_and_template_sample_pass`. They are negative guards and a re-run of T-026's rejections; their positive siblings fail at base per the task outcomes. A seeded control in each (as 00005 F1) would make them fail if a check goes silent | tests/specflow/contract/test_phase_checks.py:113 | T-034, T-039 | mech-check |
| F16 | [1/4] | 🟡 | `test_skill_md_is_within_the_size_limit` passes against the pre-change code, where `SKILL.md` was a two-line shell. `test_every_reference_is_routed`, which the pytest replay also listed, fails at base in six subtests under unittest, so it does pin this change | tests/specflow/contract/test_skill.py:33 | T-030 | mech-check |
| F17 | [1/4] | ⚪ | `references/aws/implementation.md:87` says "The full suite runs when the task is done, before it is checked", while ART-004.9 and SR-TSK-005 say a task's `Verify:` names the checks it owns. For a quick bugfix that adds a full-suite step per task beyond the checkpoint. Ambiguous, not a conflict: the suite run is in addition to the owned checks. Downgraded from 🟡 by the lead | plugins/specflow/skills/spec-workflow/references/aws/implementation.md:87 | T-035 | BLAKE |
| F18 | [1/4] | ⚪ | `test_empty_month` asserts `[] == []` and cannot detect a defect; the pytest replay flagged it as passing at base. It is scenery of the `tasks-planning` session fixture, run by no CI step. Downgraded from 🟡 by the lead | tests/specflow/fixtures/sessions/tasks-planning/tests/test_orders.py:5 | T-034 | BOB, mech-check |
| F19 | [1/4] | ⚪ | `requirements.md` line 3 says a bugfix spec's rules "are added to this file with the bugfix instructions", but the `## Bugfix specs` section (SR-REQ-053 and 054) is now in this file. Point to that section | plugins/specflow/skills/spec-workflow/references/phases/requirements.md:3 | T-038 | ALICE |
| F20 | [1/4] | ⚪ | Over-long single-line strings in new code (the `fix` message in `bugfix_task_order` and the `fix` string in `bugfix_clause_patterns`); the file otherwise wraps near 88 columns. `ruff format --check` is clean, so this is style only | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:340 | T-039 | ALICE |
| F21 | [1/4] | ⚪ | SKILL.md:10 says the helper path is relative to the skill folder, yet to "run it with Python 3 from the repository root"; no rule says how the agent finds the skill folder on a host that installs the skill outside the repository. By design: T-030 forbids host placeholders | plugins/specflow/skills/spec-workflow/SKILL.md:10 | T-030 | BLAKE |

Overlap: F1, F8 and F9 touch `sketch_screens` and its tests and can be fixed together. F3, F6 and F7 are wording fixes in rule text. F4, F10, F13 and F21 are plan or design decisions, not code defects: fixing F10 or F13 changes an approved artifact. F5 and F17 are in 00003's AWS references, outside this diff.

## Alice

Implementation-aware review on the legacy consensus engine. She ran the four unittest suites (12, 348, 58, 53, all OK), `validate.py`, `check_rules.py` for the nine areas and `verify_release.py`, and read the replay rows as negative or preservation tests. Findings: F1, F2, F3, F9, F19, F20.

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
R12: fail
R13: pass

## Blake

Blind lens (spec only). He ran the three specflow suites and `validate.py`, `verify_release.py`, `check_rules.py` for the eight 00006 areas, and `validate` on the `00102` bugfix fixture, all passing; the unfiltered `check_rules.py` fails only on the 00007 review files. Findings: F2, F4, F5, F10, F11, F12, F17, F21, and F3 with Alice.

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
B16: fail
B17: fail
B18: pass
B19: pass

## Bob

Codex, exit 0, after one retry (inlined). His first run refused for lack of input (see Agent Status). In the retry, FIX holds seven items (F6, F7, F8, F13, F14, F18, and F1 with Alice and Carl), and VERIFY and KNOWN are empty.

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
R12: fail
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0, first run. He read the context and diff, ran the suites and diffed the changed test files. Findings: F1, F2.

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

Verdict: 21 findings

Tests: 471 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-18)

The developer ruled on each finding in turn and took the lead's proposed ruling on every row. The cycle's one 🟠 (F3) is fixed, so the rework is followed by an incremental cycle 2 under the autopilot bar.

- F1: fix. `sketch_screens` splits into three helpers (journey findings, mockup-file findings, link findings), behavior unchanged. Queued.
- F2: fix. The README status and the placeholder CHANGELOG line. Queued.
- F3: fix. SR-SKL-015 is reworded: the helper's status document stays the only source of the derived facts, and the rule names where the rest comes from (the task count from `tasks.md`; the next action and the blocking question from `phase`, `gates`, `blockers` and `nextTask` by one fixed mapping written into the rule). No design edit: `design.md:246` lists the fields only, and the "computes nothing itself" sentence is T-037's Reuse note in `tasks.md`, which stays as written. The SR-SKL-015 eval rubric follows the wording. Queued.
- F4: accepted by plan (ledger entry added). The routing names 00007's files on purpose, and `test_skill.py` fails when its NOT_WRITTEN_YET list goes stale. Correction to the row above: `design.md` has no "when installed" wording either (its routing row at line 118 reads as SKILL.md's), so there was nothing in the design to copy. The entry lapses when 00007 lands.
- F5: fix. `aws/requirements.md:125`: a choice the developer leaves to the agent is a non-answer under SR-REQ-005 and 006. Line 3: where the two differ, the specflow rules (artifact contract and phase references) win. 00003's file, recorded here. Queued.
- F6: fix. One clause on SKILL.md:12: the repository's own instruction files are read for constraints as the intake reference says. Queued.
- F7: fix. SR-REQ-014 and SR-REQ-053 are qualified with the workflow order. Queued.
- F8: fix with F1. Regular files only, and an existing mockup that cannot be read is reported. Queued.
- F9: fix. One seeded-defect test per untested branch. Queued.
- F10: trace it, accept the scope (ledger entry added). SR-REQ-042 gains the source `R:WF-002.8`; the approved design places the offer in the requirements phase, where `(guess)` markers live. Queued (the source line).
- F11: fix (ii) only. The Expected Behavior pattern excludes `SHALL CONTINUE TO`. (i) is by the design table and (iii) by SR-IMP-007, with the template kept in Kiro's shape (one ledger entry for both). Queued.
- F12: fix. SR-DLG-013 also names the intake item; SR-INT-001's verbatim save and SR-INT-057's copy leave a secret out as SR-DLG-013 says. Queued.
- F13: fix by design edit. `design.md:259` now says the first three and the last of the fixed tasks, in order, with tasks Kiro adds between the fix and the checkpoint allowed, as the T-027 capture shows. The code stays. Recorded in the 00006 qa-log ("Review 00006-01 design edits"); the edit stales the design and tasks approvals, which are asked again after the fix.
- F14: fix. Turns 23 and 25 of `shared-dialogue` accept the three open questions by name before each approval. Queued.
- F15: accepted as facts. The positive siblings pin the change, and a negative guard exists to catch over-firing. No seeded controls this time: 00005 F1 had three reviewers behind it, this row only the replay.
- F16: accepted as a fact.
- F17: accepted (ledger entry added). 00003's text, ambiguity only.
- F18: accepted. Fixture scenery.
- F19: fix. Line 3 of `requirements.md` points at `## Bugfix specs`. Queued.
- F20: fix with F1. The two strings are wrapped. Queued.
- F21: accepted by design (ledger entry added). No host placeholder by T-030; 00008 proves the install on real hosts.

### Outcome (2026-10-18)

Decisions and ledger `93139f4` (with the F13 design edit and its qa-log entry); fix commit `de90b0e`; the re-approvals and this record in the commit after it.

- F1 + F8 + F20: `sketch_screens` is 24 lines and calls `journey_findings` (27), `mockup_findings` (27) and `link_findings` (27). `files` holds regular files only, so a directory named `<screen>.html` leaves its screen without a mockup; a source page that exists but is not UTF-8 is reported once (`spike/mockups/<source>.html cannot be read as UTF-8`) and its edges are skipped. The two long `fix` strings are wrapped.
- F11 (ii): the Expected Behavior pattern is `WHEN .+ THEN (?i:the system) SHALL (?!CONTINUE TO)`.
- F9: eight tests, one per branch (the reserved `index`, no flowchart screen, a missing and an unreadable journey, a missing `## Introduction`, a missing `## Bug Analysis` with its three sections, a section with no clause, three top-level tasks, and the second, third and last-task mismatches). `test_phase_checks.py` is 390 lines.
- Fail-first, tests written before the code: against `93139f4`, the two classes ran 29 tests with 2 failures and 1 error (the directory mockup, the unreadable page, the `SHALL CONTINUE TO` clause under 2.x); the eight F9 tests pass there, as coverage of branches that already existed. At `de90b0e` all 29 pass.
- F3: SR-SKL-015 names the fields taken from `status --json` as they are, the count from the task list of `tasks.md`, and the mapping for the next action and the blocking question (a hold, then a blocker, then the phase's own step). The SR-SKL-015 eval rubric says the same. `SKILL.md` stays at 101 lines.
- F6, F7, F12, F19: one clause on SKILL.md:12; SR-REQ-014 and SR-REQ-053 qualified for Design-First; SR-DLG-013 names the intake item, and SR-INT-001 and 057 point at it; `requirements.md` line 3 points at `## Bugfix specs`.
- F5: `aws/requirements.md` line 3 gives the specflow rules precedence (the artifact contract and the phase reference), and the Adaptation at line 125 treats a choice left to the agent as a non-answer under SR-REQ-005 and 006.
- F10: SR-REQ-042's sources are `A:PRD-30` and `R:WF-002.8`.
- F2: the README says the phase references are in place and the review references are next; the CHANGELOG's first line no longer mentions the placeholder skill.
- F14: turns 23 and 25 of `shared-dialogue` accept the three open questions by name before each approval.
- F13: the design row was corrected in `93139f4`; the code is unchanged.
- `CHANGELOG.md` gains two lines under Fixed: the `sketch-screens` and `bugfix-clauses` fixes, and the rule-text corrections.
- Gate at `de90b0e`, Python 3.14: `scripts` 12, release 53, contract 359, rules 58, all OK; `validate.py`, `check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER` and `verify_release.py` exit 0. Python 3.10.22: contract 359 OK, rules 58 OK. Lint: `ruff check` is clean on the two changed Python files, and `ruff format --check` passes.
- Re-approvals: design at blob `cc2badd` (canonical `8a6e8f7d…`) and tasks at blob `8fc762b` (canonical `d839553c…`), approved by the developer ("Approve both (Recommended)") and recorded in `.specflow.json` with a fresh code baseline over the 19 placement files at `de90b0e`; `reconcile` reports phase `verification`, and `status` shows no stale artifact, no blocker and no warning (qa-log "Re-approvals, review 00006-01").
- Next: cycle 2, incremental since `fe24340`, with the ledger and this file's findings handed to the reviewers.
