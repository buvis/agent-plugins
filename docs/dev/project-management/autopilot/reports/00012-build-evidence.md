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
