# Project Capsule: buvis agent-plugins

Generated: 2026-10-28

## Current AP 00012 handoff

Build complete: 19/19 tasks, including bounded split children17/18 and
delivery-metadata task19. The package has96 files:11 gated skills,
18 preserved persona documents,59 preserved references,3 review contracts,
the local facade and root metadata/documentation. No controller, host support,
certification or publication is claimed. All11 historical README bodies
reconstruct the pinned source exactly. Frozen92 source IDs,1381 behaviors,
4950 regression mappings and all future owners/profiles remain intact.

Full Python3.12 suite:89 passed in21.25s. Validator unit tests:12 passed;
repository validation:3 packages/15 skills. Explicit source audit passed679
files/92 assets/1381 behaviors/4950 cases. The source verifier returned3
because it could not parse pytest's summary; no canonical verification receipt
was written. Actual raw log and this limitation are durably retained.

Next: fresh full-lane review, cycle1, unchanged rework cap3 and review base
`b1e05c75d6f0dad01db35258baf565ecaf5a77ad`. Audited implementation models
are OpenAI Sol/Astra; driver validates41 raw-line evidence rows across19
tasks and requires Anthropic Opus/xhigh Alice, Blake and Bob. No completion
review ran in this build session. Follow `autopilot/reports/00012-build-handoff.md`.
Remote status below is historical; this build performed no new GitHub refresh.

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

- specflow track: 00002-00007 merged (PR #1-#6). Python target 3.10 (CI); `ruff check --fix` rewrites to 3.11+ APIs, re-run contract tests on `mise exec python@3.10.22` after any ruff fix.
- New autopilot-port track (00011/00012+): porting the `claude-autopilot` plugin content into `plugins/autopilot/` as a standalone, OVCAQ-independent package. Design doc `designs/00011-autopilot-standalone-design.md` plus three reviews (`boundary-correction`, `split-design`, `three-layer`) already landed; discovery docs `00011-autopilot-agent-plugins-{inventory,port}.md` map the source. PRD 00012 (this run) is Phase 0 of that port: pin the source commit (`e960ef1` in `claude-autopilot`), port assets 1:1, and define the plugin-owned review-evidence/policy contracts — no runtime wiring, no publishing. Later PRDs (00013-00021) build the controller/TUI on top.
- AP 00012 has19/19 tasks complete and all build gates passed. Delivery receipts and21 source-null authored-file owners are complete. Independent completion review remains pending in a fresh session. Review base stays `b1e05c7`.

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
