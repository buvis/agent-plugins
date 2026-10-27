# AP 00012 build evidence

Task 1: source routing row 2, logical opus. Host maps native Claude worker to OpenAI gpt-6.1-sol/high, with supported independent Anthropic completion-review route. Native agent /root/ivan_inventory/session 01a1753b-0434-7e41-8f50-a4775f21dc1e. Exact native session_meta/turn_context bytes are extracted into 00012-worker-1-native-metadata.jsonl. Initial read-only blocked attempt contributed no files; corrected evidence scope completed capture and map. Inventory f55c98bba2b4b3c94ce588b6c616258186dd0bb2164800b2d34271acc25dfb5d committed f39d95e before map a8a7e4c. First commit also retained pre-staged lifecycle rename; content was untouched.

Config-only snapshot task skipped Tess/red-check/Pat per source. Last map commit touches one file, so self-deslop skipped:trivial. Style clean (no Python), split skipped:no-tests. Coordinator exact ID set/digest checks passed: 92 assets, 1381 behaviors, 4950 regressions. No future behavior marked passed. Source commit roster independently verified 11 skills/18 agents/59 refs.

Catchup: GitHub state green, no open issues/PRs; engram query succeeded, index/harvest failed read-only SQLite.

Seven task plan uses amended design verbatim; classifier floor opus, estimates ~75K/95K peak, coupled multi-file/risk work excludes Qwen eligibility split. Existing test_contract.py is superseded and will be reconciled.

Task 2: Tess /root/tess_contracts stopped before edits because nested public schemas are not declared. No implementation contribution, no production/test files changed, no tests run by Tess. Exact blocker recorded in 00012-contract-clarification.md. Task remains pending; no implementation attempt/model is fabricated.

Pause verification: repository validator passed (2 packages/4 skills); validator unit tests passed (12). Whole-state schema and task counts passed: 1/7 completed; phase/next_phase paused. Empty package scaffold directories created for dispatch preflight were removed. No completion-review invocation.

## 2026-10-26 Task 2 interrupted build

Tess initial dispatch f23c6fc9 (45464 bytes), then rendered quality retry 8720a52e (43498 bytes), ran in isolated native /root/tess_2, thread 01a17745-1278-7e71-8abb-a5e25bb8e9e3, actual model gpt-6.1-sol/high, provider openai. Exact session_meta/turn_context bytes are retained in 00012-tess-2-native-metadata.jsonl. Both dispatches contributed tests. Logical tier opus. Source worker route is native task-tier; the host maps it to OpenAI with an independently supported Anthropic completion-review route. No Ivan model is claimed.

Replaced superseded test_contract.py and added test_contract_fixtures.py and test_contract_semantics.py. 29 test functions cover exact policy tables, closed Draft202012 wire shapes, all 55 golden cases, and an independent contract-specific semantic checker with stop order and exact defect sets. Quality retry corrected the initial omission of that semantic checker. Mechanical tautology check found no flagged shapes; main-session behavior/output/edge/anti-tautology/contract exploit checks passed; test style gate passed. Source-inventory equality and packaged rubric provenance remain integration obligations, not claimed by this test-only work.

Tess narrow verification: UV_CACHE_DIR=/private/tmp/tess-2-uv-cache uv run --with pytest --with jsonschema pytest -q --tb=line tests/autopilot/test_contract.py tests/autopilot/test_contract_fixtures.py tests/autopilot/test_contract_semantics.py. Exit 1: 29 setup errors because the three contract JSON files are absent. This is expected missing-feature evidence, not passing implementation verification. Coordinator did not repeat this run.

Test commit failed with exit 128 twice, including approved require_escalated retry: error: 1Password: agent returned an error; fatal: failed to write commit object. Signing remained enabled. Tests are staged and uncommitted; HEAD remains 199b00a8c5e149686063679371e49ab41dbd12bb. Warrant request 876c58d526e695eacf7f429f8d829287 awaits host approval for the exact signed test commit with --only on these three paths.

Devon prompt budget measured 69445 bytes (b5ff75a8); one trim removed redundant public-interface context and still measured 69163 (b01fd68e), above the mandatory 50000-byte cap. Both rows closed error/blocked; NO Devon process launched. Remaining context is mandatory tests and persona. Recorded subagent_prompt_overrun for Task 2, requiring the source replan procedure after signing recovery; no prompt-cap increase or test-coverage reduction. The signing pause takes precedence until resolved. Preserve the tests and split remaining Task 2 contract work so downstream prompts fit. No Ivan, self-deslop, Pat, full-suite verification or completion review ran.

Pause checks: repository validator passed (2 packages/4 skills); validator unit tests passed (12). Empty package scaffolding removed. Workflow remains 1/7 completed; Task 2 in progress with one aborted attempt attributed to its actual test-author model. Full verification still belongs after all implementation tasks.

## 2026-10-26 Signing recovery (interactive, Claude under run-agent)

Cause: the `autocodex` shell function ran the driver bare, so codex inherited `~/.gitconfig`'s 1Password `op-ssh-sign`; `autoclaude` runs under `~/bin/run-agent`, which switches signing to `ssh-keygen` with the agent key. Fix: `autocodex` now wraps the driver in `run-agent` (dotfiles commit via warrant). The staged Task 2 tests were committed unchanged as 044dfdd (`test(autopilot): reconcile task 2 with normative review contracts`, agent key, signature good), so warrant 876c58d526e695eacf7f429f8d829287 is obsolete and must not be approved. `stall_reason.stalled = subagent_prompt_overrun` and `task_aborts[-1]` stay in state for the next build session's Phase 0 replan; `phase`/`next_phase` reset to `build`, `pause_reason` cleared via statectl.

## 2026-10-27 Un-park after the replan budget stall (interactive, Claude under run-agent)

Three sessions ran after the signing recovery: eefb14ce replanned (c25d9af), df17222a parked the PRD in `hold/` as `oversized_task` because the 110 179-byte `state-schema.md` copy estimates 82 545 tokens against the 75 000-token replan budget (e6ae4c9, `reports/00012-replan-1-budget.md`), and 0ec5287e found no selectable PRD (every backlog PRD requires 00012 in `done/`) and drained the batch (939aefb). The wrapper then paused with `build skipped the fresh review handoff`: a false positive in `~/.config/autocodex/adapter.py`, whose guard had no exemption for the source's `("build", "drained")` transition after a park; fixed with a test (dotfiles patch via warrant).

Root cause of the task 2 overrun: every pre-replan task body (54-55 KB each, `reports/00012-pre-replan-1-state.json`) embedded the design doc's whole `## Interfaces & contracts` section (lines 54-781, about 55 KB) instead of the task's own entries, and task 2's three test files total 66 KB, so no Devon prompt for that scope can fit 50 000 bytes. Recovery: PRD moved `hold/` -> `backlog/` (SKILL.md "Un-park a sidelined PRD"); `phase`/`next_phase` reset to `build`, `pause_reason` cleared, `work_start_sha` restored to `b1e05c75d6f0dad01db35258baf565ecaf5a77ad` (the original review base named in `00012-replan-1-budget.md`); planning constraints for the next session in `docs/dev/project-management/plans/00012-replan-scope.md`, to be passed with `autocodex --scope`. `resume-target` prints `build: catchup then planning`; normal mode, 150 000-token budget, no replan-context.md.

## 2026-10-27 normal plan and task 2 policy

Normal planning created fifteen remaining tasks and restored the original
completed inventory/map task, including its unchanged actual-model attempt.
The original test-author abort is retained once on task 2; its test contribution
also supplies the current schema/fixture/integration tasks. This is a split of
remaining work, not a recapture of completed provenance. The exact plan is in
`00012-normal-plan.json`; `plan_expansion: allow` passed the executable gate.
The design amendment has its three required review dispatches and no open
blocker. Planning/lifecycle artifacts committed as `468adca`.

Task 2 acquired one extra writable file, package `CHANGELOG.md`, to satisfy
the source's feature-commit rule. Other contract tasks remain separately
scoped. Native source route is backend Opus, row 2; actual host mapping is
`gpt-6.1-sol` / high. Driver `model_provider` and `review_providers` support
its independent Anthropic completion-review route. No unsupported-provider
fallback or model escalation fired.

Tess `c85ce0c1`, native `/root/tess_policy`, session
`01a17f29-7fb3-72e3-9b68-83afa9435ecd`, wrote the split tests. Observed model
and effort are preserved verbatim in `00012-task-2-tess-native-metadata.jsonl`.
Prompt: 42,577 bytes. Policy-owned tests: 14,989 bytes before cleanup, within
the 15,000-byte planned test budget; task body plus 8,000-byte persona reserve
and own tests stays below 50,000. Schema tests moved unchanged to
`test_contract_schema.py`; all original methods/assertions passed an AST
comparison to commit `044dfdd`. New assertions compare all 29 source bindings
to exact committed inventory digests. Tautology gate found no flagged shapes;
main-session output/edge/contract checks and style gate passed. Initial test
run: six setup errors because policy JSON was absent. Tests committed in
`13918a3` before Devon or Ivan.

Devon `ea635d07`, session `01a17f2d-8b45-7d03-ac20-bae5029ac474`, received a
26,482-byte prompt. Two candidates each passed six tests: duplicate root
members with the same parsed last value, and contradictory free descriptions
with unchanged machine fields. Tess `22334558` (29,253-byte prompt) adjudicated
both explicitly in-contract: duplicate-member rejection and canonical
description prose are not specified. No assertion was weakened or changed.
Devon cleaned its sole temporary target to the prescribed placeholder.
The coordinator red-check then produced six JSON-decode setup errors, exit 1.
The stray `f8c693a5` row measured an old scratch prompt after a failed render;
it was closed error and no agent was dispatched from it. It did not change
the plan or prompt cap.

Ivan `27dbd8af`, native `/root/ivan_policy`, session
`01a17f30-ecfb-7f20-b25a-53654750861e`, received a 31,306-byte prompt and wrote
only policy JSON, test requirements and changelog. Actual observed model is
`gpt-6.1-sol` / high, preserved in `00012-task-2-ivan-native-metadata.jsonl`.
Commit `b5364fa` contains the implementation and changelog. Policy digest:
`cfd9fd5aa477a211973cc6449fb31f901ad3fa06e534132a5d141c00295f5afc`.
Post-commit narrow gate: the PRD's Python 3.12 uv/requirements command targeting
`test_contract.py`, exit 0, six passed in 0.05 seconds.

Fresh self-deslop `8c8bc8e3` (30,352 bytes) returned `no slop found`. Style
limits passed. Split hygiene found two dead imports, removed by bounded native
cleanup `c8adb3c1` (7,459 bytes), session
`01a17f35-427b-7551-bfe8-067f4273c691`, observed `gpt-6.1-sol` / high in
`00012-task-2-cleanup-native-metadata.jsonl`. Commit `ea95077` deletes exactly
those imports, no assertions. Same narrow test command: six passed in 0.02
seconds. Final style gate passed. The checker still reports EVIDENCE_FILE and
FIXTURES_FILE as locally unused; these are required exports imported by
schema/fixture/semantic sibling tests. Retained the raw failed-check marker
with that false-positive disposition rather than breaking preserved tests.

Pat `fe87c42c` ran via real use-sonnet, tool-less, high effort, on the whole
task range `468adca..ea95077`. Its external CLI prompt is 77,763 bytes because
it includes the committed diff; the source's 50,000-byte Agent-tool dispatch
cap is unchanged and every native dispatch above satisfies it. Parsed output
is preserved in `00012-task-2-pat-review.txt`. MEDIUM rubric-pair ordering is
rejected: the normative field requires one entry per (job, namespace), while
only required_reviewer_jobs is explicitly ordered. User-owned specification
test `test_contract.py:172` deliberately uses assertCountEqual for rubric
pairs; each rule_ids array remains exact and source-ordered. A different
serialization changes its own checked digest, not contract validity. No
stricter ordered assertion is invented. The LOW blank-line observation is
retained for completion review, per the source's LOW-only no-retry rule.

All current task-2 contributors have OpenAI actual-model evidence. Devon's
temporary discarded candidates, self-deslop's no-op, design reviewers and
read-only Pat are not additional implementation contributions. All worker
ASSUMPTIONS footers are none. No full-suite, schema/fixture completion or
completion-review claim is made by this policy task.

## 2026-10-27 task 3 closed evidence schema

Task base: `01e4077625cd62055c6f33a7409cd7021c8a20b0`. Source route is
backend logical Opus. Initial test authors used native `gpt-6.1-sol` / high:
Tess `2586d0f9` (22,617 bytes), session
`01a17f3d-487a-7282-a513-ac05ef2d5cc7`, then quality retry `55bcd7aa`
(16,987 bytes), session `01a17f42-6c88-7272-b049-c3217356bf89`.
Observed metadata is retained in `00012-task-3-tess-native-metadata.jsonl`
and `00012-task-3-tess-quality-native-metadata.jsonl`. The source object was
rechecked in the actual `claude-autopilot` repository: `git -C ... cat-file -t
e960ef1...` returned commit. Its absence from the target repository's separate
object database was not a failed premise or a repin.

New standalone tests cover the wire contract before golden fixtures exist.
The older golden-dependent test file stayed byte-identical, SHA-256
`f4466e359a936aa27873f2fd04e35064733a51406cae57b7f756fbddf5030cfa`.
Initial quality review required scalar/enum/path/array boundary assertions;
the strengthened 17-test suite committed in `b4db9df`. Mechanical tautology
and style gates passed. Initial runs were expected red because schema JSON
did not exist; no golden-dependent test was skipped as a claimed pass.

Devon `e3351427` (27,511 bytes), session
`01a17f48-b7f5-7571-99b6-a2c5bde4b763`, proved eight independently passing
wrong schemas: uppercase B-F digests, unvalidated first reviewer fields,
an unauthorized two-reviewer maximum, unvalidated fresh per_job keys,
an incomplete custom-lane escape, carriage-return/Unicode whitespace in
input references, missing not-applicable fields, and deep path traversal.
Each returned 17 passed (0.66–1.20 seconds). Devon overwrote its sole schema
target with the required placeholder. No second Devon dispatch ran.

This concrete failed Opus test-author check triggered the host-authorized
next bounded `gpt-6-astra` / high attempt. The contributing Sol test attempt
is retained as escalated in state, not rewritten as Astra. Logical tier
remains Opus; the task-local effective native model override dies with this
task. No Fable, cap increase or unsupported-provider fallback was used.
Both models are OpenAI and have a supported independent Anthropic review
route in the host driver.

Astra Tess `47ce7af6` (19,528 bytes), session
`01a17f51-eb95-73a3-9ce8-8d70ca481b85`, returned all eight numbered
strengthened dispositions. Tests now cover every reviewer position, 0/1/2/3/7
rows, generated lane variants including custom-lane and Unicode, all uppercase
hex letters and mixed case, new per_job keys, whitespace variants, missing
alternative fields, and traversal at depths 2/3/7/16. Commit `ec4e26e`
contains this single allowed adversarial strengthening. Standalone file:
19,671 bytes; both test files: 30,008 bytes; retry prompt plus both files:
49,536 bytes, below the unchanged 50,000-byte limit. All 17 prior methods and
old golden-test assertions remain. Shape/style gates passed. Red-check:
17 JSON-decode setup errors from the cleaned placeholder, exit 1.

Astra Ivan `fa738a46` (33,285 bytes), session
`01a17f57-4e12-7e93-9104-951c55a17766`, wrote only
`review-evidence-v1.json` and package changelog. Actual observed model/effort
for both Astra contributors are preserved in
`00012-task-3-tess-astra-native-metadata.jsonl` and
`00012-task-3-ivan-astra-native-metadata.jsonl`. The first self-run had 16
passed, 1 failed: an extra delta-roster restriction was removed because
roster policy is semantic, not this structural schema. No test changed.
Final self-run: 17 passed in 1.97 seconds. Implementation/changelog commit:
`86e4932`. Post-commit Python 3.12 uv gate targeting only
`test_contract_schema_wire.py`: exit 0, 17 passed in 1.75 seconds.

Fresh Astra self-deslop `ed402089` (18,182 bytes) returned no slop found.
Final style and split-hygiene gates are clean. Pat `7d731f1e` ran a real
tool-less Claude Sonnet/high review over `01e4077..86e4932`; full prompt
48,905 bytes. Parsed output has two LOW observations only: duplicate prior
digest condition data, and the test mutation helper's nested comprehension.
Retained in `00012-task-3-pat-review.txt` for completion review; source policy
does not retry LOW-only findings. Every ASSUMPTIONS footer is none.

The complete task received Devon exactly once; the Astra repair group reuses
that adversarial evidence and therefore records lean for the second attempt
rather than claiming another full Devon run. Completion review must include
both contributing actual models, Sol and Astra, including all test writers.
Discarded Devon schema candidates, no-op self-deslop and read-only Pat are
not additional implementation providers.

The native task-boundary headroom check fired after task 3. Its calculation
uses the observed Codex 475,000-token window, actual context growth from this
task's start, and the source's 1.25 margin; it does not copy Claude's 500K cap
or change any setting. Exact measurements are in `00012-native-headroom.json`.
The clean same-build handoff leaves 3/16 tasks complete and 13 pending, with
fixtures next. No full-suite or completion-review claim is made. The build
continues in a fresh process; source inventory/map work stays completed and
the review base remains `b1e05c75d6f0dad01db35258baf565ecaf5a77ad`.
