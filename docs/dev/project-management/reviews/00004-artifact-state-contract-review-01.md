---
prd: docs/dev/project-management/specs/00004-artifact-state-contract/requirements.md
review: 1
date: 2026-10-11
head_sha: 4d000aa9c292b87c494f532c27d53b876d07f793
codex_thread_id: 01a1271a-f8fd-7493-b7f1-3b1c2b446e2c
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00004-artifact-state-contract

Diff range: `1f9f341bf42f4961a9b51681cc74fc7fb569e1b6..4d000aa9c292b87c494f532c27d53b876d07f793`

codex_rung_guard: not fired

## Review Summary

Standalone run (no autopilot `state.json`, no wip PRD). As in 00003, the review target was spec 00004's `requirements.md`, with `design.md` attached as the design doc and `tasks.md` as the task source. The reviewed tasks were T-020 to T-026, T-028 and T-029, all checked. T-027 is a known open item: its capture is partial. Findings are written here as walkthrough packets for the developer. None was applied, and no tasks were created.

Known open items, which are accounted for and not counted as new defects:

- T-027 is partial. The public Kiro captures are in, but the Kiro IDE Bug Fix display trial and the link trial are still pending (F32).
- The design was corrected after approval (see `kiro-captures.md`, "Against the design") and is waiting for re-approval.
- The contract-test CI step is missing from `.github/workflows/validate.yml` because the push token lacks the `workflow` scope. The full version is on the local branch `feature/specflow-00004-with-ci` (F31).

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one format retry on his resumed thread, see his section)
- Carl: ✅ Available (gemini via copilot; the session restarted while he ran, so his exit code and stderr were lost, but his output file is complete: findings plus all R verdicts)
- Eve: ⏸️ Disabled (doubt_reviewer resolved to codex; no codex-implemented tasks recorded)

### Run notes

- pack: ok.
- Gate: `review-stage` ran the gate (exit 0) but could not parse unittest counts. The counts below come from suite runs this cycle at HEAD: contract 230 OK, release 52 OK, `scripts` 12 OK. `validate.py` and `verify_release.py` exited 0. Alice also ran the contract tests under Python 3.10.22 (OK).
- Fail-first replay: `review-stage` skipped it because pytest was not installed. The lead re-ran it with `uv run --no-project --with pytest python -m pytest`. Result: 22 touched tests ran; 18 failed against base and 4 passed, all in `test_templates.py`; 13 files could not be collected at base. See F22.
- Bob's first output again put a `- ` bullet before each issue line, under FIX/VERIFY/KNOWN headers. This is the same defect as in 00002 and 00003. One format retry on his resumed thread fixed it, and the substance did not change. The first output is kept at `docs/dev/tmp/bob-output-00004c1-first.txt`. The defect recurs, so `agents/bob.md` (autopilot plugin) should be fixed at the source.
- Consolidation corrections (by hand):
  - The script merged Blake's three `checks.py` findings (placeholders, bugfix task order, hash validation) into Alice's dotted-ID row, because their citations matched after line-suffix stripping. They are split out again as F2, F23 and F24.
  - Carl's `workspace_config` finding and the matching part of Alice's style item are merged into F20.
  - Bob's and Carl's CI-step findings are merged into F31, and their T-027 findings into F32. Both are known open items.
  - Bob's replay VERIFY item is merged with the mech-check into F22.
- Lead's checks:
  - F1 confirmed by reading `status.py`. Each gate is closed only by blockers that name it. `marker_blockers` gives a design-approval marker blocker the `tasks` gate. `nextTask` reads only the `implementation` gate, so it stays available.
  - F2 confirmed. The design's check table (design.md:227-241) maps VAL-001.1 only to `required-files` and `state-valid`. No `validate` check compares a hash outside `gates`, which runs in the implementation phase only.
  - F3 (raised 🟠, lead downgraded to 🟡). The state schema's `path` pattern `[^/\\]+\.md` is matched against the whole string. That confines a redirect to a `.md` file inside the spec folder, so this is a strictness gap, not an escape.
  - F6 confirmed by reading `checks.py:253`. `required-files` uses the derived phase, not the requested one. For an empty spec the derived phase is `requirements`, so nothing is required.
  - F12 confirmed. `stale_causes` is called only from `test_invalidation.py`. No command and no `status` field exposes it.
  - F23 (raised 🟠 twice, lead downgraded to ⚪). The design says 00005 (T-071) adds the placeholder checks and 00006 adds the bugfix checks (design.md:223). That is a recorded deferral, not a gap in 00004.
- Carl's raw output includes his copilot tool transcript above his findings; consolidation reads only the `[CARL]` lines.
- No verification-check queue was written (standalone run).
- Workspace note: the shared-checkout edit guard blocked writes under `docs/dev/tmp/`. So Alice's and Blake's outputs and this file were drafted in the job scratch directory, and this file was copied into place.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [1/4] | 🟠 | An upstream marker not accepted on the design approval closes only the `tasks` gate; `implementation` stays open and `nextTask` is offered (confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:97 | T-026 | BOB |
| F2 | [1/4] | 🟠 | `validate` never compares recorded approval hashes with current content outside the implementation-phase `gates` check; VAL-001.1 and WF-005.1 ("next validation SHALL detect") are only half met. The design's check table has no such row (confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:653 | T-026 | BLAKE |
| F3 | [1/4] | 🟡 | State `path` can point a canonical slot at another `.md` in the spec folder, so hashing and checks read that file while phase derivation reads `tasks.md` (lead: confined to the spec folder; downgraded from 🟠) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:119 | T-021 | BOB |
| F4 | [3/4] | 🟡 | `checks.py` is 802 lines, over the 800-line limit | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:802 | T-026 | ALICE, BOB, CARL |
| F5 | [3/4] | 🟡 | `parse_depends_on` (56 lines) and `dependency_blockers` (52 lines) exceed the 50-line limit | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/deps.py:35 | T-026 | ALICE, BOB, CARL |
| F6 | [1/4] | 🟡 | `required-files` uses the derived phase, not the requested one; an empty spec passes `validate --phase tasks` (confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:253 | T-026 | BOB |
| F7 | [1/4] | 🟡 | `BAD_CHECKBOX` errors on any list item with 0-3 bracket characters anywhere in `tasks.md` (`- [Q1] note`, `- [RFC] y`, `- [] x` confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:60 | T-026 | ALICE |
| F8 | [1/4] | 🟡 | `next_number` scans only the configured `specsDir`; specs left in a real `.kiro/specs/` beside it are not counted (INT-001.4 names `.kiro/specs/`) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:35 | T-029 | BLAKE |
| F9 | [1/4] | 🟡 | `hash --json` emits a ready approval record; STATE-003.4 says the helper offers no way to record an approval, while a non-functional line says recording needs Python 3. Spec ambiguity | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:130 | T-026 | BLAKE |
| F10 | [1/4] | 🟡 | `code_baseline` is all-or-nothing: one refused path makes the whole baseline `not_checked`; WF-004.8 implies per-file capture | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/drift.py:54 | T-022 | BLAKE |
| F11 | [1/4] | 🟡 | One non-UTF-8 artifact aborts the whole `status` run with exit 2, hiding every healthy spec | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:132 | T-026 | BLAKE |
| F12 | [1/4] | 🟡 | WF-005.4: `stale_causes` is reachable only from tests; no command or status field tells the agent why an approval is stale (confirmed) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:185 | T-023 | BLAKE |
| F13 | [1/4] | 🟡 | Baseline containment accepts a drive-qualified path such as `C:/outside/file.py` (`PurePosixPath` reads it as relative) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/drift.py:13 | T-022 | BOB |
| F14 | [1/4] | 🟡 | Unexpected Git failures silently become "no repository" or a missing `approvedCommit`, not exit 2 | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:55 | T-026 | BOB |
| F15 | [1/4] | 🟡 | Intake clash procedure re-runs `next-number`, whose max-plus-one output cannot show a duplicate claim; `validate <item> --phase intake` would | plugins/specflow/skills/spec-workflow/references/artifact-contract.md:202 | T-029 | BOB |
| F16 | [1/4] | 🟡 | The `found(message, fix)` closure is written four times; `functools.partial(error, ctx, path, rule)` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:324 | T-026 | ALICE |
| F17 | [1/4] | 🟡 | The finding dict is built by hand in `deps.finding`, `numbers.number_clashes`, `progress_fields` beside `checks.error` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:72 | T-029 | ALICE |
| F18 | [1/4] | 🟡 | `drift.py` hashes raw bytes twice by hand; `canonical.sha256_raw` already does it | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/drift.py:49 | T-022 | ALICE |
| F19 | [1/4] | 🟡 | State cloned by a JSON round trip; `copy.deepcopy` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:103 | T-024 | CARL |
| F20 | [2/4] | 🟡 | `workspace_config` is a one-line pass-through to `load_config`, kept for the design's interface name | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:107 | T-028 | ALICE, CARL |
| F21 | [2/4] | 🟡 | `status` runs `validate` per spec, repeating repository checks (a `git check-ignore` subprocess, number scans) and `dependency_blockers` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:157 | T-026 | ALICE, BLAKE |
| F22 | [1/4] | 🟡 | Four `test_templates.py` tests pass against the pre-change code. `test_placement_keeps_headings_and_ids_in_every_capture` checks `insert_depends_on`, a helper defined in the test file, so it pins no shipped behavior. The other three use `subTest` and may be a pytest replay artifact (suspected) | tests/specflow/contract/test_templates.py:260 | T-020 | BOB, mech-check |
| F23 | [1/4] | ⚪ | Placeholder checks (VAL-001.8, ART-001.10, VAL-001.3) and bugfix task-order checks (VAL-001.4) are absent; the design defers them to 00005 T-071 and 00006 (lead: downgraded from 🟠 ×2) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:542 | T-026 | BLAKE |
| F24 | [1/4] | ⚪ | `traced_ids` misses a dotted ID (`REQ-001.2`) on a `Requirements:` line | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:532 | T-026 | ALICE |
| F25 | [1/4] | ⚪ | `git check-ignore` gets the configured path without `--`; a `specsDir` starting with `-` is read as an option | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:116 | T-028 | ALICE |
| F26 | [1/4] | ⚪ | `own_status` keeps a stored `stale` even when content matches `approvedSha256` again (STATE-002.4: content wins); no test pins either reading | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:128 | T-023 | ALICE |
| F27 | [1/4] | ⚪ | Literal invisible BOM character in `canonical.py:66`; import order in `checks.py:14-15` | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/canonical.py:66 | T-022 | ALICE |
| F28 | [1/4] | ⚪ | Extras beyond the spec (`hash --raw`, `reconcile --dry-run`, text modes); a hold forces `nextTask: null` though the spec ties that to a closed gate | plugins/specflow/skills/spec-workflow/scripts/validate_spec.py:185 | T-026 | BLAKE |
| F29 | [1/4] | ⚪ | An approved `tasks.md` with zero tasks derives `complete`; `write_guarded` leaves `.specflow.json.tmp` behind if the write fails | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/reconcile.py:36 | T-024 | BLAKE |
| F30 | [1/4] | ⚪ | VERIFY: tests and release checks pass. Resolved: lead ran all suites at HEAD (294 tests OK, both checks exit 0) | N/A | general | BOB |
| F31 | [2/4] | ⚪ | KNOWN: contract-test step missing from CI (token lacks `workflow` scope; full version on `feature/specflow-00004-with-ci`) | .github/workflows/validate.yml:33 | T-020 | BOB, CARL |
| F32 | [2/4] | ⚪ | KNOWN: T-027 Kiro IDE Bug Fix display and link trials pending | docs/dev/project-management/specs/00004-artifact-state-contract/tasks.md:21 | T-027 | BOB, CARL |

Overlap: F4, F16, F17 and F20 are all `checks.py` restructuring and fit one refactor pass. F5 is its sibling in `deps.py`. F2, F6 and F23 all concern which checks `validate` runs in each phase. F10, F13, F14 and F18 all touch `drift.py`/git evidence.

## Walkthrough packets (for the developer)

Agenda: 32 findings: 2 🟠, 20 🟡, 10 ⚪. F30 is resolved, and F31 and F32 are known open items with an owner already. That leaves 29 to decide: 2 full 🟠 packets, 9 short 🟡 packets, and two bundles of low-impact items. Nothing has been applied.

### 1 of 13: 🟠 F1, implementation opens while the design approval skips a marker

- **What:** WF-002.7 says design and tasks may not be approved while an upstream artifact holds an open question, a `(guess)`, or a deferred decision, unless the developer accepts each one by name. `status` checks this in `marker_blockers` (`status.py:78-104`). A marker not accepted on the design approval blocks only the gate after the design, which is `tasks`. Bob's doubt lens found it, and the lead confirmed it by reading the code.
- **Evidence:** Each gate closes only on blockers that name it (`status.py:168-171`), and `nextTask` checks only `implementation` (`status.py:173`). Take a spec whose tasks approval accepts a requirements marker but whose design approval does not: `implementation` is open and a next task is offered. This follows the T-026 Verify wording ("a blocker of the gate after the dependent artifact"), so the code matches the plan, and the question is whether the plan is right.
- **If unchanged:** An agent can start building on a design approval that was never valid under WF-002.7. This happens only when the developer approved the design without accepting a marker. The risk stays the same over time, but it bypasses a gate silently.
- **Options:**
  1. **(Recommended)** Make gates cumulative: a closed gate also closes every later gate. Add a test in both workflow orders. Benefit: fixes the whole class, covering artifact, marker and state blockers alike. Drawback: `blockers` stays per gate, so a reader sees the cause on an earlier gate only. Effort S. Could break: status fixtures that expect `implementation: open` beside a closed `tasks` gate. Strongest reason against: it changes the published status meaning, so the status schema docs need a line.
  2. Add an `implementation` blocker for each design-approval marker blocker. Benefit: the smallest diff, and blockers name the gate they close. Drawback: it fixes only this path, so a future blocker type can repeat the bug. Effort S. Could break: little.
  3. Have `validate --phase implementation` (the `gates` check) also fail on unaccepted markers. Benefit: the agent's pre-implementation gate catches it. Drawback: `status` still shows `nextTask`. Effort S-M. Could break: the gates tests.
  4. Accept: rely on the agent never recording such an approval (WF-002.7 is agent behaviour). Benefit: no change. Drawback: no tool backstop.

### 2 of 13: 🟠 F2, `validate` does not detect a stale approval

- **What:** VAL-001.1 asks validation to check artifact hashes, and WF-005.1 says the next resume *or validation* detects a changed hash. The design's check table (design.md:227-241) gives VAL-001.1 only `required-files` and `state-valid`. A hash comparison runs only inside `gates`, which runs in the implementation phase only. Blake's blind lens found it, and the lead confirmed the table.
- **Evidence:** Hand-edit an approved `requirements.md`, then run `validate <spec>` (no phase) or `--phase tasks`. Neither reports a stale approval. `status` and `reconcile` do detect it (`state.py:132`).
- **If unchanged:** A developer who runs only `validate`, say in CI, gets a pass on a spec whose approvals are stale. The agent's resume path still catches it through `status`. The risk stays the same over time.
- **Options:**
  1. **(Recommended)** Register a `stale-approvals` check (all phases, error level) that reports each artifact whose `artifact_status` is `stale`, naming the cause from `stale_causes`. Add it to the design table under VAL-001.1. Benefit: it closes VAL-001.1 and WF-005.1 and gives `stale_causes` a caller (F12). Drawback: it edits the design, which is already waiting for re-approval. Effort S. Could break: `validate` on repos with stale specs now fails, which is intended.
  2. Make it a warning, not an error. Benefit: it is visible without failing CI on in-progress specs. Drawback: a warning is easy to ignore. Effort S.
  3. Amend VAL-001.1 so `status` alone is the hash check. Benefit: no code. Drawback: it narrows a requirement to fit the code, and WF-005.1 still says "validation". Effort S.
  4. Defer it to 00005 with an intake item. Benefit: keeps 00004 closed. Drawback: the gap ships in the first release.

### 3 of 13: 🟡 F6, `required-files` ignores the requested phase

- **What/evidence:** `checks.py:253` uses `spec_phase(...)`, the derived phase. For an empty spec that is `requirements`, so `validate --phase tasks` requires nothing (lead confirmed by reading). VAL-001.1 asks for "required paths".
- **If unchanged:** a phase-scoped validation can pass with artifacts missing. It is likely only for hand runs.
- **Options:** (1, **Recommended**) Require the artifacts before the requested phase when one is given, else before the derived phase. Add one test. S. Against: it touches the `Context` signature. (2) Document that `--phase` filters only which checks run. S; it leaves the gap. (3) Accept.

### 4 of 13: 🟡 F7, `BAD_CHECKBOX` false errors

- **What/evidence:** Alice confirmed that `- [Q1] note`, `- [RFC] y` and `- [] x` fail `task-structure` at error level, even under `## Unresolved questions`.
- **If unchanged:** valid Markdown blocks the tasks phase, and the agent may "fix" correct text.
- **Options:** (1, **Recommended**) Apply the pattern only to task items above `## Completion criteria` (`scan_lines`' `in_task`). Add one test per sample. S. Against: a malformed box outside a task item goes unreported. (2) Flag only empty or one-character brackets. S; `[RFC]` still passes, but `[-x]` may slip. (3) Downgrade it to a warning. S. (4) Accept.

### 5 of 13: 🟡 F3, state `path` can retarget a canonical slot

- **What/evidence:** `artifact_paths` (`state.py:119`) takes `path` from the state. The schema allows any single-segment `.md`, so `"tasks": {"path": "notes.md"}` makes hashing read `notes.md`. Bob raised it 🟠; the lead downgraded it because the path cannot leave the spec folder.
- **If unchanged:** a hand-edited or buggy state makes approvals refer to the wrong file. ART-001.9 says files specflow does not own are never hashed.
- **Options:** (1, **Recommended**) Narrow the schema: requirements `requirements.md|bugfix.md`, design `design.md`, tasks `tasks.md`. Add one schema test. S. Against: the schema change may need a version note. (2) Ignore the state `path` and always use the defaults. S; then the field is dead weight. (3) Accept.

### 6 of 13: 🟡 F8, number scan skips `.kiro/specs/` leftovers

- **What/evidence:** `numbers.py:35` scans `config["specsDir"]`. INT-001.4 names `.kiro/specs/`, and `specs-folder` already reports leftovers there.
- **If unchanged:** a reused number is possible only while leftovers exist, which `specs-folder` already flags as an error.
- **Options:** (1, **Recommended**) Also scan a real `.kiro/specs/` when it differs from `specsDir`. Add one test. S. Against: one more folder read. (2) Amend INT-001.4 to say "the specs folder". S. (3) Accept, relying on `specs-folder`.

### 7 of 13: 🟡 F9, `hash --json` vs STATE-003.4

- **What/evidence:** STATE-003.4 says neither status nor the helper offers a way to record an approval. `hash --json` prints the record fields, but the agent writes them. Blake flags a spec ambiguity, not a bug.
- **Options:** (1, **Recommended**) Reword STATE-003.4 to "the helper writes no approval; it may compute the values the agent records". S. Against: it touches approved requirements. (2) Drop `approvedAt` and `workflowVersion` from `hash --json`. S; the agent then assembles more. (3) Accept as is.

### 8 of 13: 🟡 F10, all-or-nothing code baseline

- **What/evidence:** One refused path in `code_baseline` (`drift.py:54`) makes the whole baseline `not_checked`. WF-004.8 says re-approval clears drift "for successfully captured files". The design chose "never a partial" (T-022 Details), so the plan and the requirement disagree.
- **Options:** (1, **Recommended**) Amend WF-004.8's wording to match all-or-nothing. S. Against: one bad path loses all drift checks. (2) Add a per-file `not_checked` entry to the schema. M; a schema change. (3) Accept.

### 9 of 13: 🟡 F11, one bad artifact aborts `status`

- **What/evidence:** A `UnicodeDecodeError` in `sha256_canonical` (`state.py:132`) escapes `spec_status` as exit 2 for the whole run.
- **Options:** (1, **Recommended**) Catch it per spec, mark that spec `state: invalid` with a blocker, and keep going. Add a test. S. Against: one more error path. (2) Map it to a `problems` entry. S. (3) Accept.

### 10 of 13: 🟡 F12, nothing explains why an approval is stale

- **What/evidence:** `stale_causes` has no caller outside `test_invalidation.py`. The agent can reach the helper only through `validate_spec.py`, which never prints causes. WF-005.4 asks the agent to explain them.
- **Options:** (1, **Recommended**) Add the cause to each stale artifact in `status` (a `staleCause` field, a schema minor bump), or fold it into F2's check. S. Against: a status schema change. (2) Print causes in `reconcile` output. S. (3) Accept; the agent reasons from the graph in `artifact-contract.md`.

### 11 of 13: 🟡 F22, template tests that pin nothing shipped

- **What/evidence:** The replay found 4 `test_templates.py` tests passing at base. `test_placement_keeps_headings_and_ids_in_every_capture` exercises `insert_depends_on` from the test file itself (`test_templates.py:151`). The other three are suspected artifacts of pytest's `subTest` handling, not confirmed.
- **Options:** (1, **Recommended**) Point the placement test at the templates and fixtures (assert where `Depends on:` sits in the shipped files), and re-run the replay under unittest. S. Against: the placement rule itself is agent text, so a test may only be able to check examples. (2) Rename it to make clear it checks the documented rule's example. S. (3) Accept.

### 12 of 13: 🟡 bundle, small correctness and robustness items (one fix each)

- F13 drive-qualified paths: reject `^[A-Za-z]:` in `drift.py` containment. S. Recommended: fix.
- F14 Git failures: treat only "not a repository" and unborn HEAD as absence; raise `GitError` on anything else. S. Recommended: fix.
- F15 intake clash: change the procedure step to `validate <item> --phase intake`. S. Recommended: fix (doc only).
- F21 `status` repeats repository checks per spec: skip `NOT_PER_SPEC` checks inside the per-spec `validate`. S. Recommended: fix with F4.

### 13 of 13: 🟡/⚪ bundle, structure and style (one fix each)

- F4 + F16 + F17 + F20: split `checks.py` (the intake item for this already exists). Use `functools.partial` for `found`, add one finding constructor in a leaf module, and drop or keep `workspace_config` (it is kept for the design's name, so recommend keeping it). M. Recommended: one refactor pass.
- F5: split the two `deps.py` functions. S. Recommended: with the refactor.
- F18: use `sha256_raw` in `drift.py`. S. F19: `copy.deepcopy`. S. F27: write the BOM as `"\ufeff"` and fix the import order. S.
- F23: deferred by design to 00005 T-071 and 00006. Recommended: no action; confirm 00005 and 00006 carry them.
- F24 dotted IDs, F25 `--` before the path, F26 sticky `stale` (decide it, add a test), F28 extras and the hold rule (accept), F29 zero-task complete and the stray tmp file (add `finally` unlink). All S.

## Alice

[ALICE] 🟡 checks.py over 800 lines (F4). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:802 | Task: T-026
[ALICE] 🟡 Two deps.py functions over 50 lines (F5). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/deps.py:35 | Task: T-026
[ALICE] 🟡 `found` closure written four times (F16). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:324 | Task: T-026
[ALICE] 🟡 Finding dict built by hand in three modules (F17). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/numbers.py:72 | Task: T-029
[ALICE] 🟡 drift.py repeats `sha256_raw` (F18). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/drift.py:49 | Task: T-022
[ALICE] 🟡 BAD_CHECKBOX false errors (F7). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:60 | Task: T-026
[ALICE] ⚪ Dotted IDs not traced (F24). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:532 | Task: T-026
[ALICE] ⚪ `git check-ignore` without `--` (F25). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py:116 | Task: T-028
[ALICE] ⚪ status repeats repository checks per spec (F21). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/status.py:157 | Task: T-026
[ALICE] ⚪ Sticky stored `stale` (F26). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/state.py:128 | Task: T-023
[ALICE] ⚪ BOM literal, import order, `workspace_config` pass-through (F27, F20). | File: plugins/specflow/skills/spec-workflow/scripts/specflow_helper/canonical.py:66 | Task: T-022

Alice found no correctness defects against the spec. She ran the contract tests (230 OK, also on Python 3.10.22), the release tests (52 OK), and `validate.py`.

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
R13: fail

## Blake

Blind lens (spec only). He found the code himself and ran the contract tests (230 OK), the release tests (52 OK), and `validate.py`. He judged these conforming: canonical hashing, the state and status schemas, preservation of unknown fields, spec-type precedence, config path refusal, the `Depends on:` grammar and cycles, cross-spec references, `Sources:` and number clashes, the `.kiro/specs` and ignored-folder checks, advisory drift, and read-only `status` with its exit codes. His findings are F2, F8, F9, F10, F11, F12, F21 (merged), F23 (two 🟠, downgraded by the lead), F28, and F29.

B1: fail
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: fail
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

Codex, exit 0. (format warning) His first run's issue lines carried a leading `- ` under FIX/VERIFY/KNOWN headers. He then made one format retry, on his resumed thread and not inlined, which also gave him the replay result and the test counts. He re-emitted the same findings in the correct shape. FIX: F1, F3, F6, F13, F14, F15, F31 (known), F5 and F4 (merged). VERIFY: F30 (resolved), F22 (merged), F32 (known). Standalone run, so no verification-check queue was written.

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
R12: fail
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Gemini via copilot. The session restarted while he ran, so the exit code and stderr (backend and model line) were not captured. His output file is complete. Findings: F4, F5 (merged), F19, F20 (merged), F31 and F32 (known).

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
R13: fail

Verdict: 32 findings

Tests: 294 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-11)

- F1: cumulative gates (a closed gate closes every later gate), tests in both workflow orders, status schema doc line. Queued.
- F2: new `stale-approvals` check, error level, all phases, names the cause from `stale_causes`; design table row under VAL-001.1. Queued.
- F3: narrow state schema `path` to canonical names per slot, plus a schema test. Queued.
- F4, F5, F16, F17: one refactor pass (split `checks.py`, `functools.partial` for `found`, one finding constructor in a leaf module, split the two `deps.py` functions). Queued.
- F6: `required-files` uses the requested phase when given, plus a test. Queued.
- F7: scope `BAD_CHECKBOX` to task items, one test per sample. Queued.
- F8: `next_number` also scans a real `.kiro/specs/` that differs from `specsDir`, plus a test. Queued.
- F9: reword STATE-003.4 (the helper writes no approval; it may compute the values the agent records). Queued.
- F10: amend WF-004.8 to the design's all-or-nothing baseline. Queued.
- F11: catch decode errors per spec, mark the spec `state: invalid` with a blocker, plus a test. Queued.
- F12: closed by F2's check; no `status` field. Rejected as separate work.
- F13, F14, F15, F21: apply all four bundle fixes. Queued.
- F18, F19, F27: apply the small cleanups. Queued.
- F20: keep `workspace_config` for the design's interface name. Rejected.
- F22: point the placement test at shipped templates and fixtures; re-run the replay under unittest for the other three. Queued.
- F23: deferred by design to 00005 T-071 and 00006. Accepted.
- F24, F25: trace dotted IDs; pass `--` to `git check-ignore`. Queued.
- F26: content matching `approvedSha256` clears a stored `stale` (STATE-002.4), pinned by a test. Queued.
- F28: extras and the hold rule accepted.
- F29: zero-task `tasks.md` does not derive `complete`; `write_guarded` unlinks its tmp file in `finally`. Queued.
- F30: resolved. F31, F32: known open items, already owned.
