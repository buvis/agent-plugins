# Project Capsule: buvis agent-plugins

Generated: 2026-10-30

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
- [ ] 00013-autopilot-session-helpers-v2.md (wip: v1 held as exhausted cap-regression history; v2 corrective T1-T4, design doc not yet written)
- [ ] 00014-autopilot-host-execution-v1.md
- [ ] 00015-autopilot-workflow-parity-v1.md
- [ ] 00016-autopilot-controller-integration-v1.md
- [ ] 00017-autopilot-profile-conformance-v1.md
- [ ] 00018-autopilot-controller-kernel-v1.md (hold: replan budget 40K below 55K estimator overhead; tasks 1-6 + task 7 tests committed; do not resume this batch)
- [ ] 00019-autopilot-controller-lifecycle-v1.md
- [ ] 00020-autopilot-controller-review-v1.md
- [ ] 00021-autopilot-controller-records-v1.md

Observations: AP00012 completion and host provenance gates pass. Original review receipts and companion Tail sweep audit remain intact. Final Tail sweep suite: 104 passed; validator: 3 packages/15 skills. Next: fresh build session selects AP00013. The pytest count parser limitation remains documented; no new verification receipt is claimed.

## Related context

- `meta/decisions.md:291` — 0.016, discovery-additions doubt review (drift baseline, spec-dependency contract, both built in 00004).
- `meta/decisions.md:372` — 0.016, the nine-spec split and cite-upstream rule.
- `discovery/00001-specflow-bugfix-workflow.md:252` — 0.016, bugfix shape decisions T-027 compares captures against.
- `discovery/00001-specflow-aidlc-workflows.md:136` — 0.015, A1 state/approvals/invalidation notes.
- Portfolio: only cellar transcript hits, not relevant.
- Topic: `specflow 00004 artifact state contract`. Portfolio stamp: memory stale=23 dead=1, code stale=105 dead=805, prd dead=5259 (exit 1). Harvest: 12 of 14 review files lack frontmatter (`parse_failed`).

## GitHub State

- 0 open issues, no releases. PR #4 (00005) merged 2026-10-16; the 00006 PR follows.

## Project Health

- CI green, PRs flowing one per spec. Review files predating 00002 have no frontmatter, so engram cannot harvest them.

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
