# Port Plan: specflow (from autopilot design/tasks phase behavior)

_Freshness: generated 2026-09-27 from buvis/claude-autopilot master - regenerate if the source has moved on since._

Status: approved. Port/redesign table approved with corrections on 2026-09-30; all 68 drop candidates ruled under the user's delegated judgment on 2026-09-30.

Sources (`buvis/claude-autopilot/skills/`): design-solution, plan-tasks - phase
behavior only. **No retirement**: run-autopilot, its CLI, fast-track fixtures,
and the release check call both skills directly, so they stay in autopilot;
specflow copies their phase behavior.
Sibling plan: `00001-specflow-port-agent-skills.md` (its rulings on host-capability
fan-out, sizing from this plan, and the autopilot ripple apply here too).
Decisions: `meta/decisions.md` (2026-09-27).

Totals: 131 rows - 28 port, 37 redesign, 66 drop. PLT-41 and PLT-61 moved from drop to redesign.

Judgment calls resolved: DSN-53 drops the old dispatch loop; PLT-41 keeps
per-task risk evidence without model flags; PLT-55 drops fixed task-count
thresholds while PLT-56 keeps module-drift advice. See Drop Rulings.
Upstream bug spotted (not specflow's): classify_tier.py:128-134 matches cheap-tier
phrases as raw substrings ("port" hits "support", "report", "import").

## Port/redesign approval

Approved by the user on 2026-09-30: "approve with corrections" (all 63 rows).
Corrections follow settled decisions:

- DSN-35 and DSN-47 use the intake item's `qa-log.md` for review minutes, per Plan A RDS-04 and design §5.5. No `Review log` section is added to `design.md`.
- DSN-36 joins the existing design review as its autonomous pre-pass. There is no second design review.
- DSN-27 uses the design section set in §6.3 and the per-artifact rule from Q6: keep design headings with `Not applicable: <reason>` when needed, even for `quick`.
- DSN-33 extends the existing `## Risks and edge cases`, per Q4, rather than adding another risk section.
- PLT-19 joins Plan A PRD-17 and ART-004.8: copy a stated premise verbatim, re-check before acting, and skip and report the task if it fails.
- DSN-54's write scope includes review minutes in `qa-log.md`, consistent with DSN-35 and DSN-47.

The table approval did not rule drops. After the first packet, the user
delegated the remaining calls: "I'm tired of these decisions, don;t you know
hte best what to do?" The rulings below are assistant judgments under that
authority, not separately selected user answers. The user was told once that
68 drops exceed a screen and that splitting sessions was their call.
Task sizing is settled by the contract below.

## Inventory Matrix

### Port and redesign (single approval)

| id | source skill | phase | row | classification | reason | code-only | evidence |
|---|---|---|---|---|---|---|---|
| DSN-01 | design-solution | design | Invocation arg `<prd-path>`; input is a PRD | redesign | Input becomes the approved `requirements.md` in the spec dir (ART-003.1); no PRD path arg | no | DS:4,39 |
| DSN-02 | design-solution | design | Auto-select the single PRD in `prds/wip/`; error on 0 or 2+ ("ambiguous - pass the PRD path explicitly") | redesign | Keep "resolve target, stop on ambiguity"; resolve against `.kiro/specs/NNNNN-*/` instead of `prds/wip` | no | DS:39-41 |
| DSN-12 | design-solution | design | Runs unattended; never asks the user anything | redesign | Drafting and self-review can run without prompts, but the phase must end at an explicit developer approval (WF-002.1-3); no unattended pass-through | no | DS:14-15 |
| DSN-13 | design-solution | design | State-agnostic: prints doc path; FAILED report is the observable signal; caller records path | redesign | Outcome is recorded as artifact status/hash in `.specflow.json` and shown in the status summary; no external caller | no | DS:15-18 |
| DSN-14 | design-solution | design | Never edits the PRD; acceptance criteria stay PRD-owned | port | Same rule for `requirements.md` (editing it would also stale approvals, WF-002.5-6) | no | DS:20-21 |
| DSN-15 | design-solution | design | Own `references/cardinal-sins.md`, duplicated in `review-design-doc`; "edit the two together" | redesign | One design-phase reference in specflow; review-design-doc folds in (decision 4), so no duplicate copy | no | DS:25-27 |
| DSN-20 | design-solution | design | Load `AGENTS.md` / `agent_docs/` when present | redesign | Generalize to "relevant repository context" (ART-003.1): host steering files such as AGENTS.md, `.kiro/steering/` | no | DS:49 |
| DSN-21 | design-solution | design | Output `docs/dev/project-management/designs/<prd-stem>-design.md`; create dir | redesign | Output is `.kiro/specs/NNNNN-<title>/design.md` (ART-001) | no | DS:53-55 |
| DSN-22 | design-solution | design | Step 1: read PRD in full, load context, identify capabilities to drive sweep and interfaces | redesign | Read approved `requirements.md`; capabilities = requirement IDs, which design elements must trace to (ART-003.3) | no | DS:118-120 |
| DSN-23 | design-solution | design | Reuse sweep before designing new code; search both verb and noun synonyms per capability | port | Host-neutral discipline; supports ART-003.5 (quick profile documents reused pattern) | no | DS:124-133 |
| DSN-24 | design-solution | design | Empty search -> re-run with a known-present term before concluding absent | port | Host-neutral search hygiene | no | DS:131-132 |
| DSN-25 | design-solution | design | `## Reuse inventory`: (path + how to use) per helper, else `nothing found, greps tried: ...` | port | Section content moves unchanged into design.md | no | DS:134-136 |
| DSN-27 | design-solution | design | Design doc has exactly nine sections, fixed headings, fixed order | redesign | Use the existing design §6.3 section set plus reuse and module placement; merge overlapping content into its existing sections. Keep every design heading with Not applicable: <reason> where needed (Q6), including quick; no Review log section | no | DS:140-159 |
| DSN-28 | design-solution | design | `## Architecture fit`: target layers/modules, drawn from atlas/capsule | redesign | Same section, sourced from repo context instead of atlas/capsule | no | DS:143-144 |
| DSN-29 | design-solution | design | `## Module placement`: new files vs edits, with paths | port | Feeds task Location in tasks phase | no | DS:145-146 |
| DSN-30 | design-solution | design | `## Interfaces & contracts` verbatim-ready (exact signatures, types, enums, field names, thresholds) so a planner who never reads the PRD can copy them | port | Tasks phase copies contracts byte-for-byte (PLT-20) | no | DS:147-150, 161-162 |
| DSN-31 | design-solution | design | `## Data flow` | port | Required by ART-003.2 | no | DS:151 |
| DSN-32 | design-solution | design | `## Alternatives considered`: 2-3 options, chosen + why; one is smallest-diff; say what extra size buys | port | Matches ART-003.4 (rejected options with reasons) | no | DS:153-155 |
| DSN-33 | design-solution | design | `## Risks & edge cases` incl. 2-3 likely next changes and what boxes them in | port | Extend the existing design ## Risks and edge cases (Q4), retaining impact, likelihood, mitigation, and fallback; no duplicate risk section | no | DS:156-157 |
| DSN-34 | design-solution | design | `## Test strategy outline` | port | Required by ART-003.2 (testing strategy) | no | DS:158 |
| DSN-35 | design-solution | design | `## Review log` starts empty; review loop fills it | redesign | Record review minutes in the intake item's qa-log.md under a review heading (Plan A RDS-04, design §5.5); no Review log section in design.md | no | DS:159 |
| DSN-36 | design-solution | design | Autonomous adversarial review, up to 3 dispatches, cross-model loop | redesign | Merged into Plan A's ported design review (no second design review): its autonomous pre-pass fixes cardinal sins/blockers before the interactive walkthrough; fresh-context reviewer where the host supports isolated sub-tasks, inline otherwise; cross-model optional, never required | no | DS:164-170 |
| DSN-37 | design-solution | design | Each dispatch gets one self-contained prompt: draft + PRD summary + severity taxonomy | port | Review package content is host-neutral (requirements summary in place of PRD) | no | DS:172-189 |
| DSN-38 | design-solution | design | Severity taxonomy: cardinal-sin, blocker, non-blocker, question, with definitions | port | Host-neutral classification | no | DS:176-187 |
| DSN-39 | design-solution | design | Calibration: not everything is a blocker; overflagging dilutes signal | port | Host-neutral rule | no | DS:188-189 |
| DSN-40 | design-solution | design | Reviewer returns findings only, never edits; shape `{severity, title, evidence, suggested_fix}` | port | Host-neutral finding contract | no | DS:191-196 |
| DSN-41 | design-solution | design | Dispatch 1: fresh Claude subagent; fix every cardinal sin/blocker | redesign | "Fresh-context reviewer" is host-optional (Agent subagents are Claude-only); fallback inline pass | no | DS:200-201 |
| DSN-44 | design-solution | design | Dispatch 3: conditional verification pass, only if dispatch 2 found cardinal sins/blockers | redesign | Keep "re-review once after fixing blockers", host-neutral, not codex | no | DS:216-218 |
| DSN-46 | design-solution | design | After each dispatch fix every cardinal sin and blocker by editing the doc | port | Host-neutral | no | DS:231-232 |
| DSN-47 | design-solution | design | Append non-blockers and questions to Review log; do not fix them | redesign | Record them in qa-log.md review minutes and carry them into the interactive walkthrough; apply each chosen edit there and surface unresolved concerns in the approval summary (WF-002.1) | no | DS:233 |
| DSN-49 | design-solution | design | Minimum-engagement check: <3 findings or none anchored to a section/`file:symbol` -> re-dispatch once with sharper prompt; still unanchored -> WEAK (advisory) | redesign | Keep "every finding cites a doc section or file:symbol" as a review rule; drop re-dispatch count and WEAK token | no | DS:248 |
| DSN-51 | design-solution | design | Terminate: resolved -> print path + report, exit 0; open blocker after dispatch 3 -> list, exit non-zero, caller PAUSEs | redesign | Open blockers block approval of design.md and are shown to the developer; no exit code or PAUSE | no | DS:263-269 |
| DSN-52 | design-solution | design | Exit report (doc, dispatches n/3, per-severity counts, open list, weak list, result) always printed | redesign | Becomes the design-phase status/approval summary (NFR status summaries, WF-002.1) | no | DS:273-284 |
| DSN-54 | design-solution | design | Writes only the design doc; never edits PRD, task list, autopilot state | redesign | Writes design.md, its hash/status in .specflow.json, and review minutes in the intake item's qa-log.md (DSN-35/47); requirements.md and tasks.md stay owned by their phases | no | DS:291-292 |
| DSN-56 | design-solution | design | Cardinal sins are blockers regardless of justification (asymmetric, irreversible cost) | port | Host-neutral review rule | no | CS:4 |
| DSN-57 | design-solution | design | 15-item cardinal-sin list (rollback, secrets, SPOF, owner, observability, "later" on load-bearing concern, unbounded resources, schema migration, lock-in, deferred authn/z, data deletion/export, backup/restore, API versioning, hardcoded creds, decisions by acclamation) | port | Content moves unchanged; maps onto ART-003.2 security/migration/failure sections | no | CS:6-20 |
| PLT-06 | plan-tasks | tasks | No PRDs found -> inform user and stop | redesign | Refuse tasks phase when design is not approved (WF-001.4, VAL-001.5) | no | PT:31 |
| PLT-07 | plan-tasks | tasks | Select PRD: 1 in wip auto; 0 -> ask from backlog; 2+ -> ask | redesign | Resolve active spec dir; ask developer only when ambiguous | no | PT:35-37 |
| PLT-10 | plan-tasks | tasks | Read full PRD + architecture context; identify reusable code before tasks | redesign | Read approved requirements.md and design.md (ART-004.1); reuse comes from design's Reuse inventory | no | PT:54 |
| PLT-11 | plan-tasks | tasks | Design doc detection via `state.design_doc` or glob; plan from PRD alone when absent | redesign | design.md is always present and approved in the spec dir; no detection or fallback | no | PT:56 |
| PLT-12 | plan-tasks | tasks | Extract capabilities, module structure, dependency graph, phases, reusable patterns | port | Host-neutral analysis | no | PT:58-63 |
| PLT-13 | plan-tasks | tasks | No decomposition/dependency section -> derive from Requirements (each R = unit; order from depends-on wording and data flow; default none); note derivation | port | Maps to REQ IDs in requirements.md | no | PT:65 |
| PLT-14 | plan-tasks | tasks | Persist each task via `statectl.py task-add <json>`; capture printed id | redesign | Tasks are ordered checkboxes with stable IDs in tasks.md (ART-004.2, 7); no state tracker | no | PT:69-75 |
| PLT-16 | plan-tasks | tasks | Task qualities: atomic, self-contained, sequenced, unambiguous | port | Host-neutral; matches ART-004.5 | no | PT:81-85 |
| PLT-17 | plan-tasks | tasks | Task description format: What / Location / Reuse / Premise / Contract / Details / Acceptance criteria / Verify | redesign | Keep fields inside each tasks.md item; add REQ refs (ART-004.3) and dependencies (ART-004.4) | no | PT:87-109 |
| PLT-18 | plan-tasks | tasks | Contract and Acceptance mandatory, verbatim, never paraphrased (Tess test-author rationale); vague contract -> report ambiguity | redesign | Contract names copied verbatim from design; acceptance referenced by REQ ID/EARS criteria; drop Tess rationale | no | PT:111-123 |
| PLT-19 | plan-tasks | tasks | Optional `Premise:` copied verbatim; implementor re-verifies, false premise = stop | port | Merge with Plan A PRD-17 and ART-004.8: copy stated premises verbatim, re-check before acting, skip and report the task if false; no stall-path link | no | PT:125-133 |
| PLT-20 | plan-tasks | tasks | Contract from design `## Interfaces & contracts` byte-identical; design wins on conflict (log it); acceptance always from requirements; Location/Reuse seeded from design | port | Same precedence with requirements.md/design.md | no | PT:135-146 |
| PLT-23 | plan-tasks | tasks | Per-task context estimate: sum(file_bytes/4)+prd_slice/4+plan_text/4+55000 | redesign | Replace with host-neutral sizing guidance ("one coherent work unit", ART-004.5); constants are Claude work-tier specific | no | PT:154-168 |
| PLT-27 | plan-tasks | tasks | Context-budget split trigger when estimate > threshold | redesign | Split tasks too large for one work unit, judged by sizing guidance not token math | no | PT:196 |
| PLT-29 | plan-tasks | tasks | Separability: split only if each piece compiles and has own passing tests; trait not split from impls; correlated impl/test, interface/impl, impl/caller stay together | redesign | Keep as general split guidance (each task independently verifiable); strip qwen motive | no | PT:197-199 |
| PLT-33 | plan-tasks | tasks | Split mechanics: file boundary first, capability boundary second | port | Host-neutral decomposition order | no | PT:218-219 |
| PLT-34 | plan-tasks | tasks | One split attempt; still oversized -> stall PRD | redesign | Report the unsplittable task to the developer before tasks approval, no state stall | no | PT:220 |
| PLT-36 | plan-tasks | tasks | Estimator caveats: bytes/4 +-20%, round up for markdown, within 10% of threshold prefer splitting | redesign | Keep "when in doubt, split" in sizing guidance; drop bytes/4 math | no | PT:238 |
| PLT-53 | plan-tasks | tasks | Dependencies set inline at creation (`blocked_by` ints), phase order: Phase 0 none, Phase 1 blocked by Phase 0 | redesign | Express deps as task-ID refs inside tasks.md items (ART-004.4), ordered by phase | no | PT:353-358 |
| PLT-54 | plan-tasks | tasks | Blocker must exist before being referenced; never guess ids; late deps added after | port | Same rule for task IDs; validator enforces resolvable deps (VAL-001.4) | no | PT:360 |
| PLT-56 | plan-tasks | tasks | Drift rule: 2+ planned modules missing from PRD `### Repository Structure` | redesign | Validator advisory: task Location paths vs design.md Module placement | no | PT:370 |
| PLT-59 | plan-tasks | tasks | Summary: total tasks, execution order, PRD ambiguities | redesign | Becomes the tasks-phase approval summary (WF-002.1) | no | PT:394-397 |
| PLT-60 | plan-tasks | tasks | Summary: derived-structure note | port | Host-neutral transparency | no | PT:398 |
| PLT-62 | plan-tasks | tasks | Summary: requirements-vs-design contract conflicts listed | port | Same with requirements.md vs design.md | no | PT:400 |
| PLT-63 | plan-tasks | tasks | Granularity guide (too coarse vs properly granular) | port | Host-neutral | no | PT:402-410 |
| PLT-64 | plan-tasks | tasks | Good vs bad examples: model, endpoint, refactor, bug fix | port | Host-neutral reference | no | TE:5-98 |
| PLT-65 | plan-tasks | tasks | Example 5 separable vs coupled splits (qwen_eligible) | redesign | Keep separability lesson, strip qwen/tier fields | no | TE:100-130 |
| PLT-41 | plan-tasks | tasks | Facts `contract_edit` / `algorithmic_risk` with evidence rules | redesign | Keep a task Risk note only on evidence of an exported contract, persisted format, hook shape, new algorithm, shared mutable state, or migration change; name the change and its design mitigation. No model booleans or tiers | no | PT:250-253, 267 |
| PLT-61 | plan-tasks | tasks | Summary: irreducible-coupling reports (routing above Qwen) | redesign | Explain each coupled multi-file task in the planning summary and why a split would break its build, contract, or tests; omit model-routing consequences | no | PT:399 |

### Drops (final rulings below)

| id | source skill | phase | row | classification | reason | code-only | evidence |
|---|---|---|---|---|---|---|---|
| DSN-03 | design-solution | design | `--rework <review-file>` mode: design one review cycle's CRITICAL fixes | drop | Autopilot review-rework loop plumbing; specflow has no review-cycle phase. "`/autopilot:run-autopilot` Phase 6 invokes it once per cycle" | no | DS:62-64 |
| DSN-04 | design-solution | design | Rework inputs: parse `## Consolidated Findings` rows with `🔴 Critical`, `review:` cycle, cycle-1 `Diff range:` -> `work_start_sha`, `git diff --stat` ranges | drop | Depends on autopilot review-file format and work range. "under autopilot that range is `work_start_sha..HEAD`" | no | DS:67-78 |
| DSN-05 | design-solution | design | Rework usage error `design-solution: --rework needs a 🔴 Critical row and a cycle-1 Diff range`, stop without writing | drop | Part of rework mode (DSN-03) | no | DS:78-81 |
| DSN-06 | design-solution | design | Rework output `<prd-stem>-rework-<cycle>-design.md`, `Source review: ... (head_sha ...)` line, overwrite existing | drop | Phase 6 reuse check; "Phase 6 compares that line before reusing a doc" | no | DS:82-88 |
| DSN-07 | design-solution | design | Rework `## Architecture fit` opens with `Prior fix:` paragraph (cycle 1: exact "none" text) | drop | Rework-only; ties to prior autopilot fix commits | no | DS:89-93 |
| DSN-08 | design-solution | design | Rework `## Interfaces & contracts` is sole contract for `[D{cycle}]` tasks; entries open `Closes: <row>` | drop | Autopilot `[D]` fix-task convention. "Phase 6 copies it verbatim into each CRITICAL `[D{cycle}]` task" | no | DS:94-98 |
| DSN-09 | design-solution | design | Rework review prompt carries CRITICAL rows verbatim | drop | Rework-only | no | DS:99-102 |
| DSN-10 | design-solution | design | Rework terminal `result: ok` / `result: failed (...)` as last line of Review log (pass gate) | drop | Phase 6 gate signal. "Phase 6 reads it as the pass gate" | no | DS:103-107 |
| DSN-11 | design-solution | design | Rework exit report first line `(rework cycle <n>)` | drop | Rework-only | no | DS:108-112, 286 |
| DSN-16 | design-solution | design | Dependency: `use-codex` `codex-run.sh` and `codex` CLI for review | drop | Claude-only/external CLI dependency forbidden by target. "CLI: `codex` (review dispatch)" | no | DS:28-30 |
| DSN-17 | design-solution | design | Optional `~/.claude/rules-library/rationalizations.md` synonym sets; absent -> own synonyms, say so | drop | User-global rules file; the sweep itself ports (DSN-23) with agent-chosen synonyms. "`~/.claude/rules-library/rationalizations.md` (host-local...)" | no | DS:31-33 |
| DSN-18 | design-solution | design | Optional cartographer atlas `~/.local/share/agents/cartographer/projects/<hash>/atlas.md` | drop | buvis-personal tool path. "cartographer atlas `~/.local/share/agents/cartographer/...`" | no | DS:34-35, 46-47 |
| DSN-19 | design-solution | design | Load `docs/dev/project-management/meta/project-capsule.md` when present | drop | buvis project-management convention. "`docs/dev/project-management/meta/project-capsule.md`" | no | DS:48 |
| DSN-26 | design-solution | design | Use Bash `rg`; native Grep tool absent in this build | drop | Claude Code build-specific tooling note. "the native Grep tool is absent in this build" | no | DS:124-126 |
| DSN-42 | design-solution | design | Dispatch 2: mandatory codex, always runs even when dispatch 1 is clean | drop | Requires codex CLI, forbidden by target. "Dispatch 2 - codex (mandatory, cross-model)" | no | DS:202-205 |
| DSN-43 | design-solution | design | codex as direct background Bash (`codex-run.sh -f ... -o ...`), read-only sandbox, never a Task subagent | drop | codex CLI + Claude Bash/background semantics. "Run codex as a direct background Bash command" | no | DS:206-215 |
| DSN-45 | design-solution | design | Claude fallback on codex outage; loud `dispatch <n>: codex unavailable, Claude fallback`; never PAUSE | drop | Moot without codex; PAUSE is autopilot. "Never PAUSE on a codex outage" | no | DS:220-227 |
| DSN-48 | design-solution | design | Pinned dispatch line `dispatch <n> (<claude\|codex\|claude-fallback>): cardinal-sin <c>, ...` (+ ` weak`) | drop | Exists for run-autopilot Phase 1.5 regex gate; model-specific tokens. "so the run-autopilot Phase 1.5 execution gate can match it" | no | DS:234-246 |
| DSN-50 | design-solution | design | Codex deadline ~10 min x2 via task-notification; timeout = outage -> fallback | drop | Claude background-task mechanics + codex. "`<task-notification>` carrying the codex `-o` output path" | no | DS:250-259 |
| DSN-53 | design-solution | design | One reviewer dispatch per iteration; never two in flight | drop | Dispatch orchestration moot once multi-dispatch cross-model loop is gone. "never two in flight at once" | no | DS:290 |
| DSN-55 | design-solution | design | Downstream blind/doubt review stay PRD-only; design feeds plan-tasks and work-completion review | drop | Autopilot review lenses not in specflow. "Downstream blind review and doubt review stay PRD-only" | no | DS:293-295 |
| PLT-01 | plan-tasks | tasks | `compatibility:` requires Bob personal Claude/autoclaude env | drop | Personal-env coupling forbidden. "Requires Bob personal Claude/autoclaude environment" | no | PT:4 |
| PLT-02 | plan-tasks | tasks | Depends on `work` skill "Gemini-first tasks" list and `qwen-integration.md` | drop | Model-lane routing. "sets `qwen_eligible`" | no | PT:13 |
| PLT-03 | plan-tasks | tasks | State contract with run-autopilot: `autopilot/state.json`, `replan-context.md` | drop | Autopilot state/handoff. "State contract with `run-autopilot`" | no | PT:14 |
| PLT-04 | plan-tasks | tasks | Optional `pi` + llama.cpp endpoint | drop | qwen lane infra. "`pi` binary plus a reachable llama.cpp endpoint" | no | PT:15 |
| PLT-05 | plan-tasks | tasks | List PRDs via `list-prds.sh` or `ls prds/wip`, `prds/backlog` | drop | buvis PRD layout. "`ls docs/dev/project-management/prds/wip`" | no | PT:21-29 |
| PLT-08 | plan-tasks | tasks | Replan mode when `replan-context.md` exists (Phase 0 abort handler) | drop | Autopilot abort/replan loop. "triggered by `/autopilot:run-autopilot` Phase 0's abort handler" | no | PT:41 |
| PLT-09 | plan-tasks | tasks | Replan: read `Budget:` (default 75 000), skip completed work, delete file after success, keep on stall | drop | Replan-only (PLT-08) | no | PT:43-50 |
| PLT-15 | plan-tasks | tasks | Post-create fixes via `task-set-body` / `task-set-meta` | drop | statectl-only. "`task-set-meta <task-id> <meta-json-file>`" | no | PT:77 |
| PLT-21 | plan-tasks | tasks | `task-add` failure -> `tasks-clear` rollback, `stall_reason taskcreate_failed` | drop | statectl/autopilot Phase 2 recovery. "`set stall_reason '{\"stalled\": \"taskcreate_failed\"...`" | no | PT:148 |
| PLT-22 | plan-tasks | tasks | On success clear stale `taskcreate_failed` marker (no blind del) | drop | statectl-only | no | PT:150 |
| PLT-24 | plan-tasks | tasks | Threshold 150K (replan budget); `est_context_peak` = +20K | drop | Model-window constants. "under the work-tier model's standard context ceiling (200K...)" | no | PT:154, 170 |
| PLT-25 | plan-tasks | tasks | Persist `estimated_tokens`, `est_context_peak` on task | drop | state.json fields | no | PT:172-176 |
| PLT-26 | plan-tasks | tasks | Worked estimate example (97 000 / 117 000) | drop | Follows PLT-23/24 constants | no | PT:178-190 |
| PLT-28 | plan-tasks | tasks | Eligibility split trigger: backend >=2 files -> one-file pieces for qwen | drop | qwen lane routing. "so each subtask can route to qwen" | no | PT:197 |
| PLT-30 | plan-tasks | tasks | Both triggers -> single split pass; re-estimate and re-classify subtasks | drop | Couples to tier/qwen classification | no | PT:201 |
| PLT-31 | plan-tasks | tasks | Qwen infra preflight gates eligibility trigger | drop | qwen infra. "`pi` on PATH, the llama.cpp endpoint reachable" | no | PT:203-210 |
| PLT-32 | plan-tasks | tasks | Risk exemption: `contract_edit`/`algorithmic_risk` tasks not split for eligibility | drop | Eligibility-only | no | PT:212-214 |
| PLT-35 | plan-tasks | tasks | Stall: `stall_reason oversized_task`, `tasks-clear`, Phase 2 moves PRD to `prds/hold/` | drop | Autopilot loop + PRD layout. "moves the PRD from `.../prds/wip/` to `.../prds/hold/`" | no | PT:222-234 |
| PLT-37 | plan-tasks | tasks | Overhead constant re-derivation from `~/.claude/projects/.../*.jsonl` usage | drop | Claude transcript mechanics. "read the first usage line from `~/.claude/projects/<hash>/<session>.jsonl`" | no | PT:240 |
| PLT-38 | plan-tasks | tasks | Pending re-derivation on Sonnet build transcripts | drop | Model-routing (`build_model`, `_AUTOPILOT_MODEL_BUILD`) | no | PT:242 |
| PLT-39 | plan-tasks | tasks | Per-task model tier via `classify_tier.py`; persist `model`, `tier_reason` | drop | Model-tier routing forbidden. "`model: \"haiku\"\|\"sonnet\"\|\"opus\"`" | no | PT:246 |
| PLT-40 | plan-tasks | tasks | Classifier inputs: file slice, title+description, lines-changed, two facts | drop | Tiering-only | no | PT:248 |
| PLT-42 | plan-tasks | tasks | Run classifier per task via `docs/dev/tmp/plan-<n>-files.txt` / `-text.txt` | drop | Tiering + buvis tmp path | no | PT:255-263 |
| PLT-43 | plan-tasks | tasks | Legal `tier_reason` set (test_port, packaging, contract, algorithmic_risk, mechanical, default, floor) | drop | Tiering-only | no | PT:265 |
| PLT-44 | plan-tasks | tasks | Classifier precedence order | drop | Tiering-only | no | PT:267 |
| PLT-45 | plan-tasks | tasks | Mechanical signal widening withdrawn (PRD 00075) | drop | Tiering history | no | PT:269-270 |
| PLT-46 | plan-tasks | tasks | `_PLAN_TASKS_FLOOR` env knob (`legacy`/`sonnet`/other), deliberate no-op kill-switch | drop | Tiering knob. "The knob is currently a no-op, deliberately" | no | PT:272-280 |
| PLT-47 | plan-tasks | tasks | Tier examples (rename -> haiku, wire format -> opus, endpoint -> sonnet) | drop | Tiering-only | no | PT:282-286 |
| PLT-48 | plan-tasks | tasks | PRD frontmatter `default_model` floor; `fable` rejected; `session_model` note; `max()` clamp | drop | Model routing + PRD frontmatter. "`final_tier = max(classifier_tier, default_model)`" | no | PT:288-307 |
| PLT-49 | plan-tasks | tasks | `qwen_eligible` = backend AND haiku/sonnet AND 1 file AND no contract | drop | qwen lane routing | no | PT:309-320 |
| PLT-50 | plan-tasks | tasks | `qwen_excluded_reason` (ui/tier/contract/files, first-fail order) and unreachability note | drop | qwen/codex fence audit | no | PT:322-333 |
| PLT-51 | plan-tasks | tasks | Persist model/tier/qwen fields; work reconciles FILE_PATHS | drop | state.json routing fields | no | PT:335-347 |
| PLT-52 | plan-tasks | tasks | Legacy plans missing model/qwen/tier fields read as fallbacks | drop | state.json back-compat | no | PT:349 |
| PLT-55 | plan-tasks | tasks | Plan-expansion gate `check-plan`: >15 tasks, expansion >3.0 with >8 tasks; split note in `autopilot/split-notes/` | drop | run-autopilot CLI + loop ceiling tuned on autopilot incidents. "`run-autopilot/cli/__main__.py check-plan`" | no | PT:366-370, 387-390 |
| PLT-57 | plan-tasks | tasks | Gate exit codes 0/3/2; loop-mode stall vs interactive advice; `unfiled`/`drift` stderr diagnostic | drop | Autopilot loop semantics. "loop mode (`$_AUTOPILOT_LOOP` set)" | no | PT:372-374 |
| PLT-58 | plan-tasks | tasks | `plan_expansion: allow` + `rework_cap: 3` frontmatter override; `--ceiling N` | drop | PRD frontmatter + autopilot rework cap | no | PT:376-385, 390 |
| PLT-66 | plan-tasks | tasks | Rationale: mechanical widening withdrawn | drop | Tiering history; cites local gitignored audit file | no | DR:8-39 |
| PLT-67 | plan-tasks | tasks | Rationale: keyword opus triggers retired (PRD 00160) | drop | Tiering history. "`classify_tier.py` decides the tier now" | no | DR:41-67 |
| PLT-68 | plan-tasks | tasks | `list-prds.sh` also lists `prds/done/` (docs say wip + backlog only) | drop | PRD layout | yes | LP:19-25 |
| PLT-69 | plan-tasks | tasks | `classify_tier.py` imports `is_test_path` from `work/scripts/work_routing.py` by relative path | drop | Cross-skill coupling for tiering | yes | CT:19-28 |
| PLT-70 | plan-tasks | tasks | Packaging paths: fixed basename set, `requirements*.txt` glob, any `.claude-plugin` segment | drop | Tiering-only; Claude-specific dir | yes | CT:32-60, 82-90 |
| PLT-71 | plan-tasks | tasks | Mechanical phrases matched as raw lowercased substrings (`port` hits `support`/`report`/`import`) | drop | Tiering-only; latent over-match bug worth noting upstream | yes | CT:62-74, 128-134 |
| PLT-72 | plan-tasks | tasks | Empty file slice skips test/packaging rows | drop | Tiering-only | yes | CT:120-122 |
| PLT-73 | plan-tasks | tasks | CLI errors: missing args, negative `--lines`, unreadable input -> exit 1; unknown `--default-model` warns and is ignored | drop | Tiering CLI | yes | CT:156-175 |
| PLT-74 | plan-tasks | tasks | Code never reads `_PLAN_TASKS_FLOOR` (confirms prose-only knob) | drop | Tiering knob | yes | CT:1-191 (no env read) |

## Drop Rulings

All source locations below were read. DS and PT mean the respective source
`SKILL.md`; CT means `plan-tasks/scripts/classify_tier.py`, LP means
`plan-tasks/scripts/list-prds.sh`, and DR means
`plan-tasks/references/design-rationale.md`. Rows sharing a reason are
recorded together. All rulings were made under the user's delegation above.

### DSN-03, DSN-04, DSN-05, DSN-06, DSN-07, DSN-08, DSN-09, DSN-10, DSN-11 - repair-cycle protocol

- **Evidence presented**: DS:62-112 defines --rework, parses critical rows and commit ranges, checks inputs, writes cycle-specific designs with source lines, explains prior fixes, links contracts to findings, sends findings to reviewers, and emits runner result/report tokens; DS:286 changes the report title. All nine serve autopilot Phase 6.
- **Ruling**: drop all nine. Fixes use the existing design, review, and approval gates, with finding minutes in the intake Q&A log. This loses separate fix-cycle design records and a dedicated prior-fix analysis rule, but avoids a second artifact and repair protocol. The first packet offered this approach, separate portable repair designs, or selected checks; the user then delegated the choice.

### DSN-16, DSN-42, DSN-43, DSN-45, DSN-48, DSN-50 - external reviewer plumbing

- **Evidence presented**: DS:28-30 requires a Codex helper/CLI; :202-227 defines mandatory/background dispatch and fallback; :234-246 pins model/count tokens for the runner regex; :250-259 uses host task notifications and a helper deadline.
- **Ruling**: drop all six. DSN-36/41/44 keep the pre-pass, isolated reviewer where available, inline fallback, and one verification pass after blocker fixes. DSN-49 keeps anchored evidence; DSN-52 keeps a summary. Mandatory rival-model review is lost; cross-model review stays optional through host capabilities, with no CLI dependency.

### DSN-17, DSN-18, DSN-19 - personal context paths

- **Evidence presented**: DS:31-35 and :46-48 name a global synonym file, a personal cartographer atlas, and a fixed project-capsule path. Synonyms already have an agent-chosen fallback; atlas and capsule are optional.
- **Ruling**: drop all three fixed integrations. DSN-20 still reads relevant repository context, and DSN-23 keeps verb/noun synonym searches. A repository may supply equivalent steering without requiring personal stores.

### DSN-26 - source host search-tool note

- **Evidence presented**: DS:124-126 chooses Bash rg because the native Grep tool is absent in that build.
- **Ruling**: drop the host tool note. DSN-23/24 keep the searches and known-hit control using available host tools.

### DSN-53 - serial dispatch loop

- **Evidence presented**: DS:290 allows one reviewer per loop iteration; :164-218 defines the old three-dispatch model loop.
- **Ruling**: drop the loop rule. DSN-36/44 replace it with a pre-pass and one verification pass after fixes in the existing review. Each pass reads the current design; findings-only reviewers do not edit it (DSN-40). No separate scheduler is added.

### DSN-55 - downstream reviewer exclusions

- **Evidence presented**: DS:293-295 keeps autopilot blind/doubt reviewers PRD-only and names the design's callers.
- **Ruling**: drop. Specflow defines review context by intent in design §5.5; autopilot retains its reviewer boundaries.

### PLT-03, PLT-08, PLT-09, PLT-15, PLT-21, PLT-22, PLT-35 - runner state and recovery

- **Evidence presented**: PT:14 names runner state/replan context; :41-50 consumes an abort file and budget, excluding completed work; :77 uses statectl edit operations; :148-150 clears task arrays and failure markers; :222-234 records an oversized stall, clears tasks, and lets the runner move a PRD to hold.
- **Ruling**: drop all seven runner protocols. Stable checkboxes retain completed work (ART-004.7); re-planning does not reset checked tasks. PLT-34 reports an unsplittable task before approval. Invalid draft tasks have no approval, and writes follow existing hash/write checks. No abort-file budget, tracker rollback, or automatic hold move.

### PLT-05, PLT-68 - PRD listing

- **Evidence presented**: PT:21-29 lists wip/backlog folders; LP:19-25 also lists completed PRDs. LP was read in full, confirming the code-only row.
- **Ruling**: drop both. Selection and status use the existing spec directory and state rather than a PRD queue.

### PLT-24, PLT-25, PLT-26, PLT-37, PLT-38 - token math and measurement

- **Evidence presented**: PT:154-190 sets a 150K threshold, 20K headroom, persisted estimates, and a 97K/117K example; :240-242 measures overhead in personal transcripts and calls for model-specific remeasurement.
- **Ruling**: drop all five. PLT-23/27/29/33/34/36 use the concrete sizing contract below. Cross-spec review uses that same contract, preserving the oversize check without claiming portable model capacity.

### PLT-01, PLT-02, PLT-04, PLT-28, PLT-30, PLT-31, PLT-32, PLT-39, PLT-40, PLT-42, PLT-43, PLT-44, PLT-45, PLT-46, PLT-47, PLT-48, PLT-49, PLT-50, PLT-51, PLT-52, PLT-66, PLT-67, PLT-69, PLT-70, PLT-71, PLT-72, PLT-73, PLT-74 - model routing

- **Evidence presented**: PT:4, :13-15 binds the personal host, work skill, and inference infrastructure. :197-214 defines eligibility splits, shared split/reclassification, preflight, and exemptions. :246-349 defines tiers, inputs, calls, reason values, precedence, history, env knob, examples, floors, eligibility/exclusions, state, and legacy fallbacks. DR:8-67 explains retired routing policies. CT:19-28 imports a sibling predicate; :32-90 defines packaging/mechanical signals; :120-134 handles empty slices and substring matching; :156-175 checks CLI arguments. The full CT file has no environment read, confirming PLT-74.
- **Ruling**: drop all 28 routing rows. Task boundaries follow verification and coupling rather than model eligibility. Split pieces are re-checked against sizing (PLT-27/29), preserving the useful part of PLT-30. PLT-41 separately keeps risk evidence. CT substring matching can mistake support/report/import for port (PLT-71); report it as an autopilot follow-up, without changing specflow or the source.

### PLT-41 - task risk evidence

- **Evidence presented**: PT:250-253 defines actual exported API/schema/wire/hook changes and actual new algorithms/shared mutable state/migrations from a task's Contract, Location, Details, and file slice. Calling/documenting a contract or using risk words does not qualify. :267 uses the facts for model selection, but they also identify the task needing care.
- **Ruling**: redesign, not drop. An optional Risk note names the evidenced change and its mitigation from design. No classifier booleans or tiers. Standard-profile triggers stay as settled; risk is visible at the task boundary with no new gate.

### PLT-55, PLT-57, PLT-58 - numeric plan-expansion gate

- **Evidence presented**: PT:366-390 defines >15 tasks, expansion >3.0 with >8 tasks, module drift, split notes, exit codes, loop stalls, interactive advice, and overrides. Incidents motivate the constants; interactive use is advisory. The unfiled diagnostic finds tasks without file paths.
- **Ruling**: drop all three runner/count protocols. Count ratios are lost; PLT-59 still reports totals/order, concrete sizing catches bundled outcomes, and cross-spec sizing weighs three artifacts/gates. PLT-56 keeps advice for two or more task modules outside design's Module placement. Required Location fields cover missing file paths. No numeric task ceiling.

### PLT-61 - coupled-task explanation

- **Evidence presented**: PT:399 requires a summary of each coupled multi-file backend task and its routing. The explanation is useful without routing; PLT-34 covers only tasks that remain oversized.
- **Ruling**: redesign, not drop. The summary names each coupled multi-file task and why splitting would break its build, contract, or tests. Omit model routing and the backend-only scope.

## Task sizing contract

PLT-23, PLT-27, PLT-29, PLT-33, PLT-34, PLT-36, PLT-63, and PLT-65
share these checks; Plan A RPB-09 uses them in cross-spec review:

1. A task has one named outcome, a bounded file slice, exact applicable contracts, and its own verification. An unresolved design choice is a planning defect.
2. Split when the description bundles independent outcomes or verification needs changes outside its slice that are not already satisfied by listed dependencies. Look for file boundaries first, capability boundaries second. File count alone is no split trigger.
3. Each piece must build or pass its applicable file check and own verification after its listed dependencies, without an unfinished sibling. Keep coupled interface/implementation/caller and implementation/test edits together.
4. Re-check each piece's scope, contracts, dependencies, and verification after a split. Prefer splitting independently verifiable outcomes; keep inseparable edits together and explain their coupling.
5. If a task still has no bounded, verifiable outcome and no safe split, report an unresolved planning blocker before approval. Name the attempted boundary and why it fails; never silently approve it as oversized.
6. Show model, endpoint, refactor, bug-fix, and separable/coupled contrasts. The summary explains what a coupled split would break and counts tasks without a numeric ceiling.

## Port acceptance criteria

Each port row gets one criterion. Redesign rows use the approved reasons and
rulings above when their numbered rules and checks are built.

| Row | Acceptance criterion |
|---|---|
| DSN-14 | Design drafting leaves the requirements artifact unchanged. |
| DSN-23 | Search verb and noun synonyms per capability before new design. |
| DSN-24 | Check empty searches with a known-present term before concluding absence. |
| DSN-25 | Reuse inventory names each helper path and use, or no match with actual searches. |
| DSN-29 | Module placement gives paths and distinguishes new files from edits. |
| DSN-30 | Interfaces give exact signatures, types, enums, fields, kinds, and thresholds ready to copy. |
| DSN-31 | Design shows data and control flow. |
| DSN-32 | Two or three alternatives include the smallest diff, choice, rationale, and what added size buys. |
| DSN-33 | Existing risks cover two or three likely next changes and constraints on them. |
| DSN-34 | Design carries a test strategy traced to requirements. |
| DSN-37 | Reviewers receive the current draft, requirements summary, and severity taxonomy. |
| DSN-38 | Findings use cardinal-sin, blocker, non-blocker, or question with defined meanings. |
| DSN-39 | Review distinguishes concerns from defects making a design wrong or unbuildable. |
| DSN-40 | Reviewers return severity, title, evidence, and suggested_fix; they never edit artifacts. |
| DSN-46 | Fix each cardinal sin/blocker before verification; open blockers prevent approval. |
| DSN-56 | Cardinal sins are blockers regardless of justification. |
| DSN-57 | The shared review reference retains all fifteen source cardinal sins. |
| PLT-12 | Extract capabilities, modules, dependencies, phases, and reuse. |
| PLT-13 | Derive missing decomposition from requirement IDs and dependencies from stated order/data flow; otherwise none. |
| PLT-16 | Each task has one focused outcome, enough context, explicit dependencies, and no guessed design choice. |
| PLT-19 | Copy a stated premise verbatim; re-check it; skip and report the task if false. |
| PLT-20 | Contracts match design byte for byte; acceptance comes from requirements; location/reuse comes from design. |
| PLT-33 | Consider safe file splits before capability splits. |
| PLT-54 | Dependencies name existing earlier IDs; late discoveries update references without guessed IDs. |
| PLT-60 | Summary states derived decomposition or ordering. |
| PLT-62 | Summary lists both sides of contract conflicts and the affected task. |
| PLT-63 | Guidance contrasts vague whole-feature tasks with bounded, verifiable outcomes. |
| PLT-64 | Model, endpoint, refactor, and bug-fix examples give location, contracts, and verification. |

## Consumer Cutover

Not applicable while no source retires. Portfolio consumer scan (2026-09-27) kept for reference:

## claude-autopilot (heaviest)
- skills/run-autopilot/SKILL.md, references/phase-build.md (+ phase-review, recovery, state-schema, model-ladder, design-rationale, lane-solo, phase-done): invokes design-solution, plan-tasks, create-prd. Retire -> loop cannot plan.
- run-autopilot/cli/{lane.py:87, routing.py, frontmatter.py, triage.py}, scripts/tune_routing.py: hardcode plan-tasks/scripts/classify_tier.py; copy create-prd frontmatter.
- run-autopilot tests + goldens; fast-track test_card.py fixtures; work skill docs; dev/bin/release-checks:62 runs plan-tasks prose test.
- README/CHANGELOG.

## agent-skills
- brush SKILL.md:29,70 invokes review-prd-backlog (phase 4).
- capture-experiment hands off to /spike, create-prd.
- plan-port hands off to create-prd, design-solution (+ template:60).
- convene-council routes to autopilot:plan-tasks; use-qwen mentions plan-tasks.
- create-skill validate_skill.py:327 comment re create-prd.
- AGENTS.md:91-98, README.md:45, docs/plugin-skills/{design-solution,plan-tasks,run-autopilot,work} mirror.

## Other
- claude-agoge run-agoge allocate_prd_number.py:10 copies create-prd numbering; prd-emission.md scans discovery/.
- doogat/ddb, calcard-mcp settings.local.json Skill(plan-tasks) allow entries (harmless).
- ovcaq characterization string; buvis/home stale copies (not live).

## ~/.claude, ~/.agents
- rules/coding-style.md:39 spikes/ exemption cites spike skill.
- dirmap.md:39 design-solution pointer (already stale).
- hooks/tests/test_write_scope_parity.py:292 review-prd-backlog script path; test_track_skills.py sample ids.
- skill symlinks + .braid-state.json.

## Path conventions
- prds/{backlog,wip,hold,done}: enforce_prd_location.py:62-139, rules/working-documents.md:12, aegis gateguard_fact_force.py:133, agoge.
- discovery/: enforce_prd_location.py:45, agoge prd-emission.md:35.
- designs/<prd-stem>-design.md: enforce_prd_location.py:40, autopilot phase-build.md:217, state-schema.md:173.
- spikes/: enforce_prd_location.py:50, coding-style.md:39.
- audit-results/backlog-review-*; autopilot/{state.json,...}.
- intake/ is NOT on enforce_prd_location allowed list (check).

## Phases (dependency order)

1. Fold approved behavior and rulings into the existing requirements, design, tasks, README, and Q&A log. Exit: no pending marker, concrete sizing, one design review, and T-079 contains only build work. No phase dependencies.
2. Add Plan B mappings and numbered rules to the maintainer inventory; reuse shared rules and give each rule one check. Exit: all 65 approved port/redesign rows map to rules, including PLT-41/61; drops map to none. Depends on Phase 1 and the existing Plan A inventory task T-070.
3. Build design/tasks references and the existing design review's pre-pass from the rules, including risk notes, sizing, summaries, and structural checks. Exit: DSN/TSK/RVD checks pass; no personal paths, model routing, runner state, or second review. Depends on Phase 2 and baseline T-033/T-034/T-075; T-079 integrates the additions.
4. Run per-rule scenarios on every supported host and source comparison fixtures for the copied behavior. Exit: reuse, contracts, blockers, inline/isolated review, sizing, coupling, risk, and summary cases pass, with full rule coverage. Depends on Phase 3 and eval tasks T-056/T-057.

Shared Plan A/Plan B behavior may use one rule with both sources; every approved
row must still map to it. No consumer cutover or source removal follows.
Unresolved questions: none.

## Retirement

None planned; see Sources.
