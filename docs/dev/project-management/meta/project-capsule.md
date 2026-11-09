# Project Capsule: buvis agent-plugins

Generated: 2026-11-05

## Current AP 00012 handoff

Completed and moved to done: 47/47 tasks, two review cycles and the completed Tail sweep. Model provenance and independent review receipts passed the host completion gate. AP00013 starts in a fresh build session. Earlier build and recovery notes below are historical.

## 2026-10-27 AP 00012 normal planning

The operator restored AP 00012 to normal planning (150,000-token estimates),
retaining completed inventory/map commits and review base `b1e05c7`. No replan
context applies. Each task copies only its own contract entries and must keep
persona, body and tests below 50,000 bytes. Review policy, evidence schema and
fixtures are separate tasks. Existing contract tests retain their intent.

GitHub: no open issues, PRs or releases; latest master Validate succeeded.
Related context: repo query hits AP 00012 (0.0328), port discovery (0.0161);
portfolio adds historical cellar transcripts. Topic: Autopilot package and
review artifact contracts. Repository indexing succeeded; portfolio still
reports memory stale=24/dead=1, code stale=61/dead=1466 and PRD dead=3079.
Review harvest completed; task restoration reports `no_tasks_dir`.

## Key Invariants

- specflow is dogfooded on itself: nine specs (00001-00009) under `docs/dev/project-management/specs/`, the folder `.agents/specflow.json` names. Since 2026-10-16, 00002-00006 record approvals in `.specflow.json`, written by recovery mode from the `qa-log.md` receipts after the developer confirmed them, with values copied from `validate_spec.py hash --json`. 00001 and 00007-00009 still hold receipts only; recover each before its work starts.
- A criterion has one home spec; other specs cite it as `00004 WF-004 criterion 8` (decision 2026-10-04 #9). Pointer lines ("Criterion 6: see 00006.") are not gaps.
- Editing an approved `requirements.md`/`design.md` stales its approval: needs a new receipt in `qa-log.md` (precedent: 2026-10-09 #2, #3). `tasks.md` gaining only `Outcome:` lines does not.
- Shipped code under `plugins/specflow/` is stdlib-only Python 3.10 and cannot import repo code (`scripts/validate.py`); copy patterns as ideas. Tests live in `tests/specflow/`, never in the package; the release check forbids it.
- Maintainer skills only in `.agents/skills/`, support files in `tools/<plugin>/`; no committed `.claude/`, `.kiro/`, `.codex/`.

## Architecture Decisions

- Spec work runs one branch per spec (`feature/specflow-0000N`), merged by PR; each closes with a completion review file `reviews/0000N-<slug>-review-01.md` and a decisions.md section.
- The helper (00004) is an optimization, not the source of meaning: an agent without Python reads files but records no approval.

## Component Boundaries

- 00004 builds `plugins/specflow/skills/spec-workflow/{templates,schemas,scripts,references}`; 00005 (T-071) and 00006 (T-039) register more checks into its `CHECKS` registry.
- 00005 builds the maintainer-only rule inventory (`tools/specflow/rules/`, `tools/specflow/check_rules.py`) and the eval formats (`tests/specflow/evals/`). Each reference task of 00006 and 00007 writes its tagged rule texts and evals and adds its area to the CI step `check_rules.py --area VAL,...`.

## Active Work

### Batch 202610250001
- [x] 00012-autopilot-package-contract-v1.md (2 cycles; 47/47 tasks)
- [x] 00013-autopilot-session-helpers-v3.md (2 cycles; 11/11 tasks; the one user-authorized bounded recovery; T1 R1 root-anchored symlink refusal, T2 R3 descriptor-bound failed-artifact invalidation, T3 git-probe timeout fail-closed, T4 delivery evidence. Dispositions: `reports/00013-v3-admission.md`; audit: `reviews/00013-autopilot-session-helpers-v3-audit.md`)
- [ ] 00013 v1 and v2: hold (exhausted caps, cap_regression); superseded by v3's completed fresh full review. v2 cycle-2 review `reviews/00013-autopilot-session-helpers-v2-review-2.md`, stubs 00034-00037.
- [ ] 00014-autopilot-host-execution-v1.md
- [ ] 00015-autopilot-workflow-parity-v1.md
- [ ] 00016-autopilot-controller-integration-v1.md
- [ ] 00017-autopilot-profile-conformance-v1.md
- [ ] 00018-autopilot-controller-kernel-v1.md (hold: replan budget 40K below 55K estimator overhead; tasks 1-6 + task 7 tests committed; do not resume this batch)
- [ ] 00019-autopilot-controller-lifecycle-v1.md
- [ ] 00020-autopilot-controller-review-v1.md
- [ ] 00021-autopilot-controller-records-v1.md

Observations (2026-11-08T16:36Z done gate): AP00013 v3 closed at cycle 2 after a tail sweep of tasks 9-11 (R1 receipt re-pin, R3 CHANGELOG conjunction, R4 artifact-parent-swap coverage check); full suite re-verified at 19 known AP00018 controller failures only. 35 autonomous decisions and 1 deferred decision (dirty_tree.py sibling git-probe timeout, out of T3 scope) projected to `decisions.md`. Next: fresh build session selects the next PRD (00014) from wip/backlog.

## 2026-11-08T16:39Z AP00014 build catchup

AP00014 (autopilot host execution and enforcement) selected into wip, no design doc yet. GitHub: 1 open issue (#12 Renovate dashboard, routine), 3 open Renovate PRs (#13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9 — all routine dependency bumps). **Master Validate stays RED** (latest run 42124079804, 2026-11-05: 22 failed, 1167 passed, 11 skipped) — the known AP00018 controller suite (`test_controller_capacity.py`, `test_controller_owner.py`, `test_controller_owner_recovery.py`) plus two newly-failing package-provenance tests (`test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes` — a blob-hash mismatch on a packaged asset, `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes` and `test_generator_check_accepts_the_committed_map` — `log_sink_refusal.py` digest drift and an unregenerated `tools/autopilot/source-map.json`). These three are new since the 2026-11-02/05 entries above and are NOT part of AP00014's scope (host execution/enforcement adapters) — flag for the next source-map/provenance-owning PRD rather than fix here. Local master is 141+ commits ahead of origin; nothing pushed.

Related context: topic "autopilot host execution enforcement" not yet queried this session (engram query deferred; no new hits recorded). Task restore: not re-run.

## 2026-11-03T00:45Z AP00013 v2 task-2 Devon-gate build catchup

Full catchup again (cache 29m old, but two commits past `catchup_head_sha` carry committer `Agent ran by Tomáš Bouška`, so the delta condition failed). Only two content commits are new since the 00:15Z entry: `1c6212f` (the committed sink/artifact-byte test file `tests/autopilot/test_helper_recovery_v2_sinks.py`) and `f0b2e04` (the task-2 scope-recovery report plus the preserved incomplete-Devon patch); `03d4e47` and `c00f784` are state/metrics commits. No project fact changed.

Standing position for task 2: the accepted Tess correction is committed and gated; the immediate gate is ONE complete fresh Opus Devon pass using the prepared prompt at `docs/dev/tmp/ap00013-v2/task2c/devon-complete-prompt.md`. No valid Devon verdict exists yet (rows `ef85cc76` and `af622d15` were interrupted). Selection must span BOTH `test_helper_recovery_v2.py` and `test_helper_recovery_v2_sinks.py` (21 cases). Neither `00013-v2-invalid-work-attempt.patch`, the lower-tier Tess draft, nor `00013-v2-task2-incomplete-devon.patch` may reach a worker.

GitHub unchanged: 1 open issue (#12 Renovate dashboard), 3 routine renovate PRs (#13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9), no releases, remote branch `docs/ap00015-verification-counts` still present. **Master Validate stays RED** (latest run 41516085734: 20 failed, 898 passed, 1 skipped) - the known AP00018 controller suite plus the `test_helper_provenance_real.py` README pin. Both pre-existing and separately tracked; the provenance node belongs to task 4.

Related context: repo query re-run this session on topic `autopilot session helpers v2 host-neutral session helpers` - top five hits are all v1 review history (`reviews/00013-autopilot-session-helpers-v1-review-0{2,1,3}.md` at 0.0164/0.0161/0.0159, `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` at 0.0156), which must stay away from Blake's blind lens. Repo index refreshed clean. Portfolio query not re-run (identical topic); fresh portfolio stamp: memory stale=5/dead=0, transcripts stale=6/dead=1513, prd dead=105, code stale=34/dead=1232, 6098 code rows skipped (exit 1, unchanged shape). Review harvest re-run: 23 frontmatted review files upserted, 25 pre-00002/scratch files still `parse_failed` (missing frontmatter). Native task restore: `no_tasks_dir`; the authoritative autopilot task list is intact at 1/4.

## 2026-11-03T01:40Z AP00013 v2 task-2 verification-correction build catchup

Full catchup again (cache 1h 4m old, under the 4h window, but commits past `catchup_head_sha` `c00f784` include committer `Agent ran by Tomáš Bouška`, so the delta condition failed). New content commits since the 00:45Z entry: `964faee` (Tess strengthening), `4a93821` (initial Ivan sink-openable implementation), `c5ab4ea` (de-slop, later reverted), `8262193` (partial Pat review preserved), `43789d8` (revert of the de-slop pipe-close removal), `60eb370` (controlled result-artifact sink errors), `d00e130` (the task-2 scope-recovery report); `f8e810a` is a state commit.

Standing position for task 2 (authoritative: `autopilot/reports/00013-v2-task2-review-scope-recovery.md`): Devon `103d2c13`, one Tess strengthening pass, initial Ivan and a partial Pat review all ran and must NOT be repeated. The remaining work is (a) one isolated Opus Tess verification correction - replace the denied-`ps` observation with a real owned-child handle, arm cleanup before `run_gate`, add the missing result-artifact preflight and controlled-failure regressions - then (b) continue the single interrupted MEDIUM fix with isolated Opus Ivan so both verification sinks and their parent descent are validated before spawning, and (c) complete Pat's omitted scope by resuming session `29c0b516-5d37-4c52-939e-289e4bf0523c` with `-R` (cycle 2), supplying `docs/dev/tmp/ap00013-v2/task2d/previously-omitted-tests.diff` first. De-slop is not rerun; its pipe-close removal was refuted against CPython source. Last actual full six-file Verify result: **145 passed, 1 failed** (the denied `ps` call) - no all-green claim applies.

GitHub unchanged: 1 open issue (#12 Renovate dashboard), 3 routine renovate PRs (#13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9), no releases, remote branch `docs/ap00015-verification-counts` still present. **Master Validate stays RED** (latest run 41516085734: 20 failed, 898 passed, 1 skipped) - the known AP00018 controller suite plus the `test_helper_provenance_real.py` README pin. Both pre-existing and separately tracked; the provenance node belongs to task 4. No push until those and required checks pass.

Related context: repo index refreshed clean; repo query on the unchanged topic `autopilot session helpers v2 host-neutral session helpers` returned the same five v1 review-history hits (`reviews/00013-autopilot-session-helpers-v1-review-0{2,1,3}.md` at 0.0164/0.0161/0.0159, `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` at 0.0156, review-01:24 at 0.0154) - keep all of it away from Blake's blind lens. Portfolio query not re-run (identical topic); fresh portfolio stamp (exit 1, unchanged shape): memory stale=5/dead=0, transcripts stale=6/dead=1578, prd dead=105, code stale=34/dead=1232, 6109 code rows skipped. Review harvest not re-run this refresh (last run 00:45Z upserted 23 frontmatted files; 25 pre-00002/scratch files stay `parse_failed`). Native task restore: `no_tasks_dir`; the authoritative autopilot task list is intact at 1/4.

## 2026-11-03T02:2xZ AP00013 v2 task-2 cleanup-containment build catchup

Full catchup again (cache 42m old, inside the 4h window, but four commits past `catchup_head_sha` `f8e810a` carry committer `Agent ran by Tomáš Bouška`, so the delta condition failed). New content commits since the 01:40Z entry: `2e3dba5` (observe owned children by handle, pin artifact pre-spawn validation), `71fb60d` (prove the result-artifact sink openable before the spawn), `7c031f7` (preserved interrupted style correction), `42a9172` (the cleanup-containment recovery report); `eb6494a` and `6c9b230` are state commits. No project fact changed.

Standing position for task 2 (authoritative: `autopilot/reports/00013-v2-task2-cleanup-recovery.md`): the process-list test correction and the artifact preflight are committed and the complete six-file Verify passed 151 tests twice; neither is redone. The open defect is the new preflight cleanup, which follows a re-resolved parent pathname (deleting an outside sentinel) and lets its unlink `OSError` mask the original controlled failure. Remaining work: bounded regression coverage from an isolated Opus Tess (parent-symlink swap, leaf-directory replacement, same-parent replacement-file preservation, no-swap control) in the existing sibling recovery test file, then an isolated Opus Ivan fix in `verification.py`/the sink helpers, then the mandatory Pat follow-up that completes its omitted scope by resuming session `29c0b516-5d37-4c52-939e-289e4bf0523c` with `-R`. No Devon rerun, no repeated de-slop, no replan, no v3.

GitHub unchanged: 1 open issue (#12 Renovate dashboard), 3 routine renovate PRs (#13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9), no releases, remote branch `docs/ap00015-verification-counts` still present. **Master Validate stays RED** (latest run 41516085734: 20 failed, 898 passed, 1 skipped) - the known AP00018 controller suite plus the `test_helper_provenance_real.py` README pin. Both pre-existing and separately tracked; the provenance node belongs to task 4. No push until all 19 controller tests and required checks pass.

Related context: repo index refreshed clean; repo query on topic `autopilot session helpers v2` returned the PRD itself (0.0307), its Risks section (0.0161) and the three v1 review-history files (`reviews/00013-autopilot-session-helpers-v1-review-0{1,2}.md` 0.0164/0.0161, `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` 0.0159) - keep all v1 review history away from Blake's blind lens. Portfolio query returned the same four plus one cellar transcript; portfolio stamp (exit 1, unchanged shape): memory stale=5/dead=0, transcripts stale=6/dead=1618, prd dead=105, code stale=34/dead=1232, 6101 code rows skipped. Review harvest re-run: 23 frontmatted review files upserted, 25 pre-00002/scratch files still `parse_failed`. Native task restore: `no_tasks_dir`; the authoritative autopilot task list is intact at 1/4.

## 2026-11-03T21:0xZ AP00013 v2 task-3 build catchup

Full catchup (cache 18h 45m old, past the 4h window, so the delta condition failed outright). New content commits since the 02:2xZ entry: `0239445` (cleanup-containment tests), `30e5c5e` (the bounded cleanup fix), `cea8fa9` (Pat scope completion report), `2c3b21e` (task-2 assumptions + catchup refresh), `b7c5124` (retained task-2 findings for completion rework); `ee342b8`, `ac05426` and `bc1627a` are state commits. Task 2 is COMPLETE; this session starts task 3.

Standing position: tasks 3 and 4 run through the normal work loop at opus (`tier_reason: floor`, `qwen_eligible: false`), full lane, `work_start_sha` `316557e` preserved. Nothing from task 2 is re-run (no Tess, Devon, Ivan, de-slop or Pat; no cycle or counter reset). Task 2's three deferred findings (the `_open_result_sink` ownership window, the `drop = art is None` partial-artifact case, the missing `reason` key on the unsafe-path refusal) are in scope for the fresh completion review, not for a per-task redo. Closeout goes to a fresh completion-review session (Alice, Blake, Bob, Carl, Eve) with all v1 review history and the 6d duplicate kept away from Blake.

GitHub unchanged: 1 open issue (#12 Renovate dashboard), 3 routine renovate PRs (#13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9), no releases; remote branches now also include `docs/codex-force-copilot-backend`. **Master Validate stays RED** (latest run 41516085734: 20 failed, 898 passed, 1 skipped) - the 19 known AP00018 controller tests plus the `test_helper_provenance_real.py` README pin, whose cause was corrected locally in `cce5dad` and is not re-verified here. No push until all 19 controller tests and required checks pass.

Related context: repo index refreshed clean; repo query on topic `autopilot session helpers v2` returned the same five hits as the prior refresh (PRD 0.0307, v1 review-01 0.0164, PRD Risks 0.0161, v1 review-02 0.0161, `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` 0.0159) - all v1 review history stays away from Blake's blind lens. Portfolio query and `engram status` not re-run this refresh (identical topic), so no fresh staleness stamp is claimed; the prior stamp stands. Review harvest not re-run. Native task restore not run; the authoritative autopilot task list is intact at 2/4.

## Related context

- `meta/decisions.md:291` — 0.016, discovery-additions doubt review (drift baseline, spec-dependency contract, both built in 00004).
- `meta/decisions.md:372` — 0.016, the nine-spec split and cite-upstream rule.
- `discovery/00001-specflow-bugfix-workflow.md:252` — 0.016, bugfix shape decisions T-027 compares captures against.
- `discovery/00001-specflow-aidlc-workflows.md:136` — 0.015, A1 state/approvals/invalidation notes.
- Portfolio: only cellar transcript hits, not relevant.
- 2026-11-03 topic `autopilot session helpers v2 host-neutral session helpers` (repo scope): top hits are the three `reviews/00013-autopilot-session-helpers-v1-review-0{1,2,3}.md` files and `docs/dev/tmp/00013-review-01-by-agent-plugins-6d.md` (~0.016). That is v1 cap-regression review history: keep it away from Blake's blind lens. Portfolio scope not re-queried this run (no new portfolio topic); stamp below is the prior run's.
- Topic: `specflow 00004 artifact state contract`. Portfolio stamp: memory stale=23 dead=1, code stale=105 dead=805, prd dead=5259 (exit 1). Harvest: 12 of 14 review files lack frontmatter (`parse_failed`).

## GitHub State

- Refreshed 2026-11-05 (unchanged since 2026-11-03; local master 141 commits ahead of origin, nothing pushed). 1 open issue (#12 Renovate dashboard). 3 open Renovate PRs: #13 setup-python v7.1.0, #14 python 3.15, #15 pytest v9. No releases. Remote branches: master, three renovate branches, `docs/ap00015-verification-counts`, `docs/codex-force-copilot-backend`.
- `Validate` is red on master (runs 41516085734, 41511458941): 20 failures - 19 `tests/autopilot/test_controller_*` (AP00018 kernel, known/expected) plus `test_helper_provenance_real.py` README pin, which was already fixed locally after that run.

## Project Health

- CI red on master for the known AP00018 controller tests; no push until those and required checks pass (closeout constraint). Renovate PRs are stacked and also red on the same failures. Review files predating 00002 have no frontmatter, so engram cannot harvest them.

## Project Memories

- Fix misfiring buvis guard hooks at their source repo with a test, never bypass.
- Check `~/.kiro/crew/workspace/ai-age-repo-structure.md` before recommending homes for skills, links, or agent-private dirs.

## Historical Autopilot foundation context (superseded)

Active work: AP 00012 package and review contracts on master; seven ordered tasks. Pinned source exists; no package is present. Superseded test_contract.py needs reconciliation against amended design; scratch-v1 is quarantined. Source inventory must precede destination mapping.

GitHub: no issues or PRs; latest master Validate succeeded.

Related context: engram repo hits AP 00012 and discovery inventory; portfolio adds historical session evidence. Topic: Autopilot package and review artifact contracts. Existing specflow memory loaded.

Catchup gap: engram index failed with read-only SQLite; existing query results may be stale. Portfolio status reports stale/dead rows (including 61 stale code rows); no fresh index is claimed.

## 2026-10-26 build resume

AP 00012 Task 1 committed source inventory and map. Normative wire shapes were reviewed and committed in 199b00a. Task 2 replaces superseded schema tests before defining the three review contracts. Review base b1e05c7 remains unchanged.

GitHub: no open issues, PRs or releases; latest master Validate succeeded. PR #6 is merged. Related context: repo/portfolio query returned AP 00012 and inventory/port discovery. Engram index failed (read-only SQLite); portfolio reports memory stale=24/dead=1 and code stale=61/dead=1466. Native Claude task restore has no task directory; authoritative autopilot tasks remain intact.

## 2026-10-26 replan budget check

AP 00012's 75,000-token replan budget cannot admit the required 110,179-byte
state-schema reference under the installed estimator (82,545 tokens before
task prose). File/capability splitting cannot retain its single-file byte-copy
acceptance criterion. See `autopilot/reports/00012-replan-1-budget.md` for the
measurement and mandatory oversized-task recovery. Existing inventory, partial
tests and archived attempt provenance remain available.

GitHub refresh: no issues, PRs or releases; latest master Validate succeeded.
Engram repository index succeeded this session. Repo query hits: AP 00012
`prds/wip/00012-autopilot-package-contract-v1.md:8` (0.0328), inventory discovery
`discovery/00011-autopilot-agent-plugins-port.md:96` (0.0161), and AP 00013
`prds/backlog/00013-autopilot-session-helpers-v1.md:42` (0.0161). Portfolio
adds historical cellar transcripts. Topic: Autopilot package and review
artifact contracts. Portfolio stamp: memory stale=24/dead=1, code
stale=61/dead=1466, PRD stale=9/dead=3079. Review harvest partially succeeded;
older reviews without frontmatter remain parse failures. Task restore reports
no_tasks_dir; no native task restoration was needed.

## 2026-10-27 task 4 build resume

AP 00012 resumes at 3/16 completed, task 4 golden fixtures in progress.
The package stays gated; inventory/map and original review base remain fixed.
GitHub refresh: zero open issues/PRs, no releases, latest master Validate passed.
Related context: repository AP 00012 (0.0328), port retirement/inventory
(0.0161/0.0159); portfolio additionally returns historical cellar transcripts.
Topic: Autopilot package and review artifact contracts. Repository index refreshed.
Portfolio staleness: memory 24/dead 1, code 66/dead 1466, PRD 1/dead 3079.
Review harvest partially succeeded; older files lack frontmatter.
Native task restoration returned no_tasks_dir; canonical workflow tasks stay intact.

## 2026-10-29 AP 00013 build catchup

AP00013 is active on master; AP00012 remains complete. Session helpers accept explicit inputs and emit reports/proposals; the future controller alone owns persistent workflow effects. Existing facade exposes policy only, so helper APIs require a reviewed design before implementation. No publication or installation is authorized.

GitHub refresh: zero open issues or PRs, no releases, latest master Validate succeeded; no failed master runs. Related-context topic: Autopilot session-local helpers. Repo hits: current PRD (0.0328), Helpers module (0.0161), resource closure tests (0.0156), AP00014 adapters (0.0154). Portfolio adds legacy wrappers and transcripts. Portfolio stamp: memory stale24/dead1, PRD stale1/dead3133, code stale73/dead1466. Review harvest is best effort. Task restore: no_tasks_dir; no native tasks restored.

## AP00013 planning stall handoff

AP00013 is in hold after the mandatory check-plan exited 3 for module_drift. The 11-task plan is below the count ceiling and has expansion 2.20; four module groups contain paths not explicitly listed in the PRD. File-only tree entries grant exact paths, not their implicit parent directories. No implementation started and no package code changed. The completed three-dispatch design, raw failed external dispatch, native fallback findings, final external findings and complete task snapshot remain durable. No gate override or cap increase occurred. The canonical stall leaves phase/next_phase build, allowing a fresh session to select the next eligible backlog PRD.

Repository validation passed: 3 plugin packages and 15 skills. Recovery evidence: reviews/00013-plan-gate-stall.md; autopilot/reports/00013-plan-before-stall.json; autopilot/split-notes/00013-autopilot-session-helpers-v1.md.

## 2026-10-30 AP00018 build catchup

AP00018 is selected in wip on master; no implementation tasks exist. AP00013 remains held. The kernel must extract pinned OVCAQ workflow transactions without process/TUI dependencies; later lifecycle/review/records families stay unavailable until implemented. Contract A and the immutable bundle are producer-owned. All canaries use temporary roots.

GitHub: zero open issues/PRs, no releases; latest recorded master Validate succeeded, no failed master runs. Related-context topic: Autopilot canonical controller kernel and protocol. Repo/portfolio hits point to AP00018 overview (0.0328), integration (0.0304/0.0311), Kernel (0.0161), Protocol (0.0159). Index refresh failed with database locked; queries may be stale. Portfolio memory stale24/dead1, code stale80/dead1466, PRD dead3115. Review harvest partially succeeded; older/scratch files lack frontmatter. Task restore: no_tasks_dir.

## 2026-10-30 AP00018 replan build

Preserve completed characterization and 44 retained kernel tests. Remaining work is split into API-isolated test files, schema, store, paths, bootstrap, owner lease, export, provenance registration and docs. No cap changes or completion review. GitHub has no open issues/PRs/releases; latest master Validate passed. Engram repository index succeeded; related topic returns AP00018 overview/kernel/protocol. Portfolio: memory stale24/dead1, code stale82/dead1466, PRD dead3151. Review harvest partially failed on old frontmatter; task restore no_tasks_dir.

## 2026-10-30 AP00018 task 3 recovery build

Task 3 resumes after an operator-scoped Claude Devon round proved eight schema test gaps. Exactly one GPT Tess strengthen pass precedes standard GPT Ivan implementation; no Devon rerun is authorized for task 3. Later tasks retain their original gates. The original work start and prior attempt evidence remain intact.

GitHub refresh: zero open issues/PRs/releases; latest master Validate succeeded and no failed master runs. Related-context topic: Autopilot canonical controller kernel and protocol. Repo/portfolio hits: AP00018 overview (0.0328), integration (0.0311/0.0304), protocol (0.0290/0.0159), kernel (0.0161). Engram indexing failed; queries may be stale. Portfolio stamp: memory stale24/dead1, code stale57/dead21, PRD dead3115. Task restoration returned no_tasks_dir; authoritative workflow tasks remain intact.

Review harvest completed with parse failures on old files without frontmatter.

## 2026-11-01 AP00013 resume build catchup

AP00013 back in wip after AP00018 hold. Two autocodex sessions made no progress on a stale `--scope` (AP00018 task 3, already done); that directive is obsolete. AP00018 task-3 exception stays historical only. GitHub: 0 issues; open PRs #7 (specflow-00010 validator refactor, green) and #8 (dependabot setup-python 7.1.0); no master failures. Related topic: Autopilot session-local helpers; repo hits AP00013 PRD (0.0328), resource-closure helpers test (0.0156), AP00014 adapters (0.0154). Engram index succeeded; portfolio stamp: memory stale24/dead1, code stale52/dead21, PRD dead3031 (exit 1).

## 2026-11-01 AP00013 mid-build catchup (tasks 1-4 done)

AP00013 resumes at task 5 (review_stage.py) of 11; tasks 1-4 committed (characterization, finding groups, evidence checker, dirty-tree/log-sink). work_start_sha 843e6e7. AP00018 stays on hold. GitHub: 0 issues; open PRs #9 (specflow-00008 host integration) and #8 (dependabot setup-python 7.1.0); latest Validate runs green, no master failures, no releases. Related context: engram queries skipped this refresh (cache expired mid-build; topic unchanged: Autopilot session-local helpers), so no new hits are claimed. Review harvest and task restore not re-run.

## 2026-11-02 AP00013 v2 full catchup

AP00013 v1 is now held (cap_regression) with review-03 settled; v2 selected explicitly to correct only T1-T4 (staging/sink/evidence/delivery), no design doc yet. GitHub: 1 open issue (#12, Renovate dashboard), 2 open renovate PRs (#13 setup-python 7.1.0, #14 python 3.15 — both routine dependency bumps, not blocking). **Master Validate is currently RED** (runs 41516085734, 41511458941, both 2026-11-02): `tests/autopilot/test_helper_provenance_real.py` fails because `plugins/autopilot/README.md` is missing from the tested package revision tree (git show 128), and `tests/autopilot/test_controller_capacity.py` / `test_controller_owner.py` / `test_controller_owner_recovery.py` (the AP00018 controller suite) show 19-20 failures — consistent with the session-brief's "known 19 AP00018 controller tests" deferred-failure note. 20 failed, 898 passed, 1 skipped on the latest run. Treat this as the pre-existing red gate the PRD already flags (Success Metrics: "the known AP18 controller failures remain separate... never mask/relabel") — v2's T4 exit criteria explicitly require recording red controller nodes rather than fixing them. The provenance/README failure is new since the last green run (2026-11-01) and needs checking at T4 (source-map/receipt refresh) since it concerns `plugins/autopilot/README.md`, one of T4's own writable paths.

Related context: repo hits are the PRD itself (0.0328), the hold-30 cap stall stub (0.0161), `test_cap_custody_helpers.py` (0.0159), the v1 PRD (0.0156), `test_local_paths.py` (0.0154); portfolio adds historical claude-autopilot park-cap-regressions review and cellar transcripts, nothing new actionable. Topic: "Autopilot session-local helpers v2 cap regression recovery". Portfolio stamp: memory stale=5/dead=0, code stale=34/dead=1232, prd stale=0/dead=105 (exit 1, same as always — stale/dead rows exist, not a new problem). Review harvest upserted the repo's frontmatted review files; everything under `docs/dev/tmp/` and the pre-00002 review files remain `parse_failed` (no frontmatter), as before — no regression there.

## 2026-11-02 AP00013 v2 task-1 recovery build catchup

Full catchup re-run (cache 20m old, but HEAD moved past `944f900` with a non-loop committer, so the delta condition failed). Only three content commits are new since the 22:00 refresh: `18ca409` (v2 design preserved), `f5bfc2e` (interrupted-workflow violation evidence), `7ff920e` (rejected abort provenance), plus two state commits. The invalid direct-edit attempt by a Sonnet coordinator is reverted; its patch is kept as evidence in `autopilot/reports/00013-v2-invalid-work-attempt.patch` and must never reach Tess. Task 1 is pending with no valid worker attempt; `tasks[0].attempts` is deliberately absent because the installed attempt writer rejects an `orchestrator` implementor, and no stamp was forged.

GitHub unchanged from the 22:00 entry: 1 open issue (#12 Renovate dashboard), 2 routine renovate PRs (#13 setup-python 7.1.0, #14 python 3.15), no releases, plus one extra remote branch `docs/ap00015-verification-counts`. **Master Validate stays RED** — latest run 41516085734: 20 failed, 898 passed, 1 skipped. The failures are the known AP00018 controller suite (`test_controller_capacity.py`, `test_controller_owner.py`, `test_controller_owner_recovery.py`) plus `test_helper_provenance_real.py`, which still fails because `plugins/autopilot/README.md` is absent from the tested package revision `527d880c`. Both are pre-existing and separately tracked; neither is this task's to mask or relabel. The provenance failure touches `plugins/autopilot/README.md`, one of T4's own writable paths, so T4 is where it gets checked.

Related context: engram queries were NOT re-run this refresh (identical topic, hits recorded three hours earlier in the entry above: PRD 0.0328, hold-30 cap stall stub 0.0161, `test_cap_custody_helpers.py` 0.0159). No new hits and no fresh staleness stamp are claimed for this session. Review harvest and native task restore were not re-run either (historically `no_tasks_dir`); the authoritative autopilot task list is intact at 0/4.

## 2026-11-02T22:45Z AP00013 v2 task-1 build catchup

Full catchup again (cache 20m old, HEAD moved past `381b1bd` with a non-loop committer, so the delta condition failed). Exactly one content commit is new since the entry above: `24a08a7`, which added `autopilot/reports/00013-v2-self-debug.md` plus the preserved lower-tier Tess draft `00013-v2-lower-tier-tests.py.txt` and wrote that entry itself; `372ef47` is a state commit. So no project fact changed in this refresh.

Standing position for task 1: all four tasks are pending with `model: opus`, `tier_reason: floor`, `qwen_eligible: false`, `qwen_excluded_reason: tier`, verified directly from `state.json` this session. The self-debug report records the root cause (the planner omitted `--default-model opus`, so all four task records compiled to Sonnet) and the bounded recovery. Neither the invalid patch (`00013-v2-invalid-work-attempt.patch`) nor the lower-tier draft may reach Tess.

GitHub unchanged: 1 open issue (#12 Renovate dashboard), 2 routine renovate PRs (#13 setup-python 7.1.0, #14 python 3.15), no releases; remote branch `docs/ap00015-verification-counts` still present. **Master Validate stays RED** (latest run 41516085734, 2026-11-02: 20 failed, 898 passed, 1 skipped): the known AP00018 controller suite (`test_controller_capacity.py`, `test_controller_owner.py`, `test_controller_owner_recovery.py`) plus `test_helper_provenance_real.py`, whose failure is the historical README pin (`git cat-file -e` at the current receipt pin `cce5dad` returns 0), not a new defect. Both are pre-existing and separately tracked; task 4 checks the provenance node, nothing masks or relabels either.

Related context: engram not re-run (identical topic, hits unchanged from the two entries above); no new hits or staleness stamp claimed. Review harvest not re-run. Native task restore: `no_tasks_dir`; the authoritative autopilot task list is intact at 0/4.

## 2026-11-09 AP00018 v2 recovery catchup

Batch 202611090642 selects AP00018 v2 first; AP00014 v2 remains dependency-blocked. Held v1 records and pending critical custody remain intact. Master local HEAD dacba71 includes authorized recovery admission and measured baseline: 20 failed, 1433 passed (19 controller owner/capacity/recovery; one shared CHANGELOG provenance mismatch). No baseline exemption. Current protocol only executes workflow.open; owner payload/schema/test scaffolding exists but the owner dispatcher is absent. Existing store/bootstrap must be characterized and reused. Final suite and successor evidence must cover current bytes. All changes remain local.

GitHub refresh: issue 12 dependency dashboard; Renovate PRs 13/14/15 remain open. Latest master Validate 42124079804 failed with 22 failures, including controller and provenance/roster mismatches at historical 584c42c2. No releases.

Related context: repo and portfolio query Autopilot canonical controller kernel and protocol return held 00018 v1 and current v2 (scores 0.0328 and 0.0323); remaining hits include integration requirements and AP00014 v2 dependency. Portfolio stamp: memory stale=7; transcripts stale=6/dead=4894; code stale=91/dead=1232; PRD dead=140. Review harvest partly succeeded; unstructured historical review files report missing frontmatter. Task restoration no_tasks_dir.

AP00018 v2 build paused at host_per_task_review_transport. Required Pat review cannot currently combine explicit high effort, disabled tools and print-session resume in either available Sonnet wrapper. Gap report and hashes: reports/00018-v2-review-transport-gap.{md,json}. Source characterization task 9 completed (22 schema tests passed, 15 hashes/37 symbols/144 ownership fields verified); task 1 abort retained, split task 10 pending; 1/10 complete. No production edits or PRD completion. Validator 3 packages/15 skills passed. Custody unchanged.
