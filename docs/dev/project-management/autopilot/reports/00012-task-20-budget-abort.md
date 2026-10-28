# Task 20 dispatch-budget abort

AP 00012, cycle 1, rework cap 3. The session resumed Phase 6 because cycle 1's complete independent review was already consolidated and tasks 20 and 21 were queued. No review lens was rerun. No finding was closed by this attempt.

Task base: `491ebd7f506d5926a45c7c470eeab7a515d09b02`.
PRD review base remains `b1e05c75d6f0dad01db35258baf565ecaf5a77ad`.

## Dispatch and observed model

Source routing selected row 7. The mandatory Codex hook doctor exited 1: 4 OK, 7 stale, 5 broken. Its first broken target was `/Users/bob/.codex/codex-hook`. The external implementor lane therefore did not dispatch; source rules use the native task tier on this infrastructure failure. Host mapping: logical sonnet, actual OpenAI `gpt-6.1-sol`, medium effort. Anthropic is a supported independent review route for this provider. No unsupported provider contribution was substituted or relabeled.

Native implementation session `01a1807a-09da-7c92-9388-c961bd677fbd`, agent path `/root/ivan20`, dispatch `0a9dd932`. Exact session metadata and first turn-context rows are preserved in `00012-task-20-ivan-native-metadata.jsonl`; line 2 records the observed model and effort. The complete raw worker session is `00012-task-20-ivan-raw.jsonl`. This is an implementation/test-edit attempt, not a reviewer model or coordinator fallback claim.

The rendered Ivan prompt measured 13,278 bytes. Together with its resulting own test file, the worker measured 44,331 bytes. Tess and red-check skipped for a configuration/test task; Devon skipped at sonnet tier. The worker made only the two task-allowlisted file changes and committed nothing.

## Candidate and verification limits

The candidate adds 508 source-line resource edges, corrects 25 existing active-script classifications, and adds independently derived script-closure checks. It retains the original 202 frozen edge identities. The worker reported three focused working-tree checks passing under Python 3.12 (3 tests, 0.296 seconds, exit 0). This does not establish committed-archive verification or complete closure. Candidate assumptions and classification choices still need review.

Complete candidate diff: 320,312 bytes. Complete rendered Pat prompt: 329,263 bytes. One trim removed unchanged diff context (`git diff -U0`): diff 313,401 bytes, rendered prompt 322,352 bytes. Both exceed the mandatory 50,000-byte ceiling. Neither Pat prompt was dispatched. No review coverage was thinned, no cap raised, and no completed task was reopened.

The installed `skills/work/references/subagent-dispatch.md` requires abort and replan after one unsuccessful trim. The attempt is recorded as `aborted`, cause `subagent_prompt_overrun`; task 20 is pending, task 21 remains pending and dependent on task 20. The cycle remains 1 and the cap remains 3.

The entire candidate is preserved in `00012-task-20-oversized-candidate.patch`. Only task 20's files, which were clean at claim, were restored to task-base bytes. The patch is a reversible artifact, not reviewed or accepted product code. The existing implementation-model audit and reviewed snapshot remain untouched. Replan must retain this attempt provenance and all 19 completed tasks' work/history, and must not infer successful closure from this candidate.

## Replan inputs

Split only the remaining repair scope into tasks whose complete persona, task, own tests, and full review diff each fit 50,000 bytes. The resource map's repeated source-line rows dominate the diff; splitting only by its two writable filenames does not solve the problem. Use bounded source-file groups or a contract-preserving equivalent with explicit coverage. Preserve all source identities, owner/profile assignments, gates, previous review receipts, work_start_sha, cycle and cap. Do not apply the entire candidate as a supposedly completed task. Task 21 still follows completed dependency-map repair.

Candidate assumptions reported by Ivan:

- Every concrete script reference outside explicitly identified illustrative filenames requires an unavailable external capability.
- Existing active helper edge identities permit corrected classification without changing frozen identity coverage.

No product changes from this attempt remain in the worktree. Fresh-session recovery owns the prescribed replan; this session does not enter planning or cycle 2 review.

## Recovery transition failed: wrapper must halt

The source-required command `statectl.py docs/dev/project-management/autopilot/state.json set next_phase '"planning"'` failed with exact stderr `rejected: next_phase: invalid value 'planning'` and exit 1. The exact retry failed identically. Canonical `autopilot restore` succeeded, and the final required retry failed identically. The installed prose and installed schema disagree. No source schema or tool installation was modified to bypass validation.

The source's state-write failure procedure now requires `autopilot/state-write-failed`, with `site: statectl_fail` and the raw diagnostic. That marker is the halt signal; the replan transition did not land. State remains phase/next_phase `review`, cycle 1, 19/21 completed, both rework IDs pending, with the aborted attempt and budget stall trigger preserved. The backup restore removed only the newly loaded abort contract card; the durable card file and this report explain the current boundary. The previous cycle's state card therefore must not be mistaken for successful rework.

Repair the installed prose/schema transition mismatch before allowing automatic recovery to relaunch. Use the existing state CLI for any subsequent transition. Preserve this report, candidate, model metadata, attempt history and reviewed snapshot. Do not clear the failure marker without resolving the mismatch. Repository validator passed: 3 plugin packages and 15 skills. No archive verification or new review receipt is claimed.
