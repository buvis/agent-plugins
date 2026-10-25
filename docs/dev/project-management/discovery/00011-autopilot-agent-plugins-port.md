# Autopilot Agent Plugins feasibility and port plan

_Assessed 2026-10-24. Source: `claude-autopilot` at `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48`; target: `agent-plugins` at `c3906be2cbec5a08f3de87cd90d39ec0c85535cc`; supervisor: `ovcaq` at `cee9b9432e4cbd93dae936ca426ac97dfc105116`._

Status: assessed 2026-10-24; three-layer boundary revised at the user’s request on 2026-10-25. [Accepted design and PRD graph](../designs/00011-autopilot-standalone-design.md). No runtime, installation, marketplace, or consumer was changed by that planning assessment. The 2026-10-25 completeness corrections are recorded in [the corrective review](../reviews/00011-autopilot-port-completeness-review.md); AP 00012's revised design supersedes its earlier approval.

## Verdict

**Feasible. The package conversion can preserve Claude hooks and agents through a client-supported extension or compatibility layout. Equivalent execution on additional clients requires adapter work. The selected design bundles one workflow controller with Autopilot, keeps OVCAQ as optional supervision, and separates the TUI.**

The assessment considered three outcomes. The revised plan selects Autopilot/controller plus headless OVCAQ plus separate Lantern; the format-only alternative below is historical feasibility evidence, not the selected delivery:

| Outcome | Feasibility | What it delivers |
| --- | --- | --- |
| Valid Agent Plugins package that still requires Claude | High; small packaging change | Standard discovery plus retained Claude hooks, agents and runtime in supported compatibility locations |
| Portable workflow with equivalent enforcement on tested hosts | High in principle; significant integration and parity work | Shared skills/controller, optional OVCAQ orchestration, separate TUI and tested host adapters |
| Identical unattended behavior on every conforming client using only portable core components | Not provided by v1 | Shared hook and orchestration semantics are outside the portable core |

**Agent Plugins explicitly supports packaging hooks in client-specific extension folders.** Its own example is `com.example.client/hooks/hooks.json`. The client owns the folder's configuration and execution semantics; other clients may ignore it. Skills and MCP configuration form the shared portable core. Thus existing Claude hook logic can remain in the package, while another client's registration, event payloads and blocking behavior need an adapter. Use each client's documented namespace/layout rather than assuming the illustrative namespace works. [Specification](https://agent-plugins.org/specification), [client extensions](https://agent-plugins.org/plugin-authors/client-extensions).

The ownership and delivery plan below implement independent stateful plugin use plus optional orchestration and presentation. A format-only conversion can stop after packaging and Claude compatibility verification; it does not require migrating state, replacing hooks with MCP, or adopting OVCAQ.

The best initial execution targets are Claude Code and Codex, because OVCAQ already implements both drivers. Other clients may load the skills, but unattended execution must remain unavailable until their required capabilities pass the same tests. A host without reviewer isolation must not substitute an inline self-review.

## Evidence

| Check | Result | Limit |
| --- | --- | --- |
| Existing root manifest through the target validator | Exit 1: missing or unsupported `$schema` | Further checks stop at that error |
| Relocated scratch package, only root manifest normalized | `Validated 1 plugin package(s) and 11 skill(s).` | Valid metadata and layout do not prove runtime portability |
| Existing state, transitions, lane, and review-close tests in that relocated copy | 152 passed; 14 subtests passed | Selected reusable-core tests, not the complete release suite or live host execution |
| Target validator tests and repository validation | 12 tests passed; 2 packages and 3 skills validated, including the template | The target's baseline passes |
| Existing target host-loading experiment, 2026-10-07 | Claude, Codex, and Kiro loaded a fixture skill, read its reference, ran its script, and continued shared artifacts | A small Specflow fixture, not an Autopilot run |
| Runner `--help` from this Codex session | Codex and Gemini helpers refused with exit 3 before displaying help | Direct evidence that current parent-host guards obstruct these entry points |

The scratch manifest used the Claude manifest's version and metadata, adding the canonical schema identifier and MIT license. All runtime files stayed unchanged. The source root manifest says `0.9.0`; `.claude-plugin/plugin.json` says `0.10.0`. The root also advertises `org.anthropic.claude` agents/hooks settings without implementation evidence establishing those settings as a working client extension.

The source contains 11 skills, 18 agent files, and 9 distinct registered hook scripts. Its tracked Python files comprise 137 files not named as tests/conftest, approximately 39,274 lines, plus 303 test/conftest files, approximately 118,392 lines. These are size measurements, not an estimate of code requiring replacement; helper files can fall into the first count.

Reproduction of the selected relocation check: run `mise exec -- uv run --no-project --with pytest python -m pytest -q skills/run-autopilot/cli/test_state.py skills/run-autopilot/cli/test_transitions.py skills/run-autopilot/cli/test_lane.py skills/run-autopilot/cli/test_review_close.py` from the copied plugin root.

## Recommended ownership

| Owner | Responsibility |
| --- | --- |
| `agent-plugins/plugins/autopilot/` | Shared skills/review content, helpers, hooks and one bundled canonical workflow controller |
| OVCAQ | Headless sessions/processes, role-to-driver placement, collaboration/waves/worktrees, execution journal and operations API |
| Lantern (provisional) | Separate TUI consuming OVCAQ's public API |
| Specflow | Requirements/design/task authoring and approval artifacts; any future execution handoff needs an explicit artifact contract |
| Host adapters and enforcement plugins | Native delegation, tool-event interception, permission enforcement, and installation behavior |

All files supplied by Autopilot must ship inside its own package. OVCAQ is optional: durable standalone workflows use the same bundled controller with manually started sessions; the plugin must never import its sibling checkout or another plugin's files by repository-relative path. Maintainer tools and tests belong under `tools/autopilot/` and `tests/autopilot/`, following the target's existing layout.

Use skill-relative resource references and script-relative resolution. `${PLUGIN_ROOT}` is specified for designated MCP configuration fields; it is not a portable replacement for `${CLAUDE_PLUGIN_ROOT}` throughout Markdown. Keep repository workflow artifacts in the repository; use client data directories only for suitable caches and host-local state. [Agent Plugins specification](https://agent-plugins.org/specification), [Agent Skills references](https://agentskills.io/specification).

MCP is optional. A thin MCP facade could expose structured state and review operations later. It cannot, by itself, intercept an agent's separate terminal/editor tools, guarantee a new host session, or enforce the push guard. Start with the existing CLI boundary.

## Principal integration gaps

### Stateful execution uses one Autopilot controller

OVCAQ currently owns tested workflow services and bundled presentation. The revised [product boundary](../../../../../ovcaq/AGENTS.md) extracts those services into Autopilot's controller and presentation into Lantern. Its [driver contract](../../../../../ovcaq/docs/driver-protocol.md) still expects external skill content. The historical gaps below remain acceptance obligations, now assigned to their new owners.

The actual contracts differ:

- Old skills write `phase`, `next_phase`, `cycle`, and task `model` fields through `statectl`. OVCAQ uses a closed schema with `work.phase`, `work.next_phase`, `review.cycle`, and provider-neutral task tiers. Old mutations cannot be copied unchanged.
- The old default review cap is two; OVCAQ initializes three. Preserve the intended configured policy explicitly rather than inheriting a different default accidentally.
- OVCAQ's transition table has no `build + lane_reviewed` transition. Its generated public command reference exposes no counterparts named `lane-check`, `custody`, `wave`, `review-stage`, or `review-close`. Some underlying behavior may already exist under other APIs; exact parity remains unproven.
- OVCAQ's Codex prompt invokes `$run-autopilot`; the target's recorded plugin probe exposed a namespaced skill. Verify the installed invocation and configure a prompt override where necessary.
- OVCAQ provisioning, personal cutover, and public release remain held work. Its fixture-based driver verification does not prove the external Autopilot plugin works.

The OVCAQ migration policy requires a fresh batch/state tree and rejects permanent `autopilot`, `autoclaude`, `tracon`, or `statectl` aliases. Finish or park old batches under the old runtime. Do not build an importer or a second state writer as an incidental part of this port.

### Review guarantees need executable enforcement

Keep consensus, blind/spec-only, and doubt plus de-slop lenses, their rubrics, independent contexts, evidence requirements, retries, caps, and escalation behavior. The full and fast-track paths retain the required fresh-session review boundary. Solo-lane exceptions remain code-selected and retain their escalation rules; the model cannot choose a cheaper roster.

Keep staging, parsing, grouping and semantic review classification in plugin helpers; commit their outputs through the canonical controller's typed operations. Move state-owned acceptance checks into the authoritative transition path. An agent should not be able to mark a cycle complete merely by calling a lower-level mutation. Retain host enforcement for actions outside that path: a transition check after a forbidden push is too late.

The source's nine hooks cover document locations, critical-custody pushes, phase delegation, post-handoff skill calls, recording session departure, context caps, state integrity, review completeness, and outstanding reviewer processes. Preserve the existing implementations for Claude through its supported packaging. Each additional execution host needs verified registration and event adaptation, or an equivalent runtime check where that check can enforce the same boundary. Missing required enforcement must reject unattended execution before work starts.

### Dispatch is coupled to Claude

`runner.build_argv()` always emits Claude flags and stream-json expectations, even when `runner_bin` changes. Binary injection alone does not make it provider-neutral. Native worker names, model/effort tiers, `Agent`, `TaskOutput`, foreground/background behavior, and tool permission mappings also require adapters.

Both `codex-run.sh` and `gemini-run.sh` reject a parent carrying `CODEX_SESSION_ID` or `COPILOT_CLI`. Preserve recursion protection, but distinguish an authorized top-level coordinator from recursive reviewer dispatch. Do not solve this by simply removing the guard. OVCAQ owns managed cross-session and cross-driver launches. The plugin emits controller job intent/resources, with native host delegation only when explicitly permitted; standalone users start required fresh sessions manually.

There is also existing documentation/runtime drift: the skills request `sonnet-run.sh --effort high`, but that helper neither parses `--effort` nor forwards it to Claude. The port needs invocation-contract tests, not just copied prose. This finding is recorded here; the source runner was not changed.

### Specflow overlap is real, but its artifacts are different

The existing [Specflow port plan](00001-specflow-port-autopilot-phases.md) copies design/planning behavior and explicitly retires neither source skill. Specflow is still unreleased. Its spec bundles, approval hashes, and `.specflow.json` differ from Autopilot's PRD buckets, task state, and autonomous review cycle.

Keep PRD execution as the first port's input contract. Reuse established review/design principles, but do not merge the two state machines or make sibling-plugin file imports. Specflow-to-Autopilot execution is a later, explicitly versioned handoff; existing approvals must remain meaningful.

## Inventory Matrix

`port` preserves behavior and content; relocation alone does not count as redesign. `redesign` preserves the capability through a changed runtime or interface. No feature deletion is proposed. A retained feature without a proven equivalent blocks full retirement rather than silently disappearing.

The [surface inventory](00011-autopilot-agent-plugins-inventory.md) expands commands, options, helpers, and documented behavior sections. AP 00012 freezes that expected ID set plus principal rows, configuration/state fields, code-only discoveries and regression cases independently of destination mappings. Every row receives an owning repository/PRD, destination operation/procedure, observable acceptance scenario and profile-specific evidence. File/heading preservation alone is insufficient; unavailable rows cannot pass a promised profile. Source references below are relative to `claude-autopilot/` unless otherwise identified.

| ID | Row | Classification | Reason | Code-only |
| --- | --- | --- | --- | --- |
| P01 | Design reuse sweep, architecture fit, module placement, explicit interfaces, risks and test strategy | port | These design disciplines do not depend on host APIs | no |
| P02 | Task contracts, dependency ordering, sizing evidence, acceptance criteria and verification instructions | port | Preserve the planning rules independently of task storage | no |
| P03 | Reviewer personas, consensus/blind/doubt and dimension rubrics | port | Preserve prompt content and review criteria; registration is R05 | no |
| P04 | Blind reviewer receives the spec and rubric without implementation narrative | port | Context exclusion is a required invariant on every host | no |
| P05 | Review artifact sections, verdicts, evidence, tests and finding provenance | port | Preserve observable review outputs and completeness rules | no |
| P06 | Test-first discipline, adversarial test checks, red-check, per-task review and final verification | port | Preserve the pipeline's existing conditional rules and gates | no |
| P07 | Finding consolidation, severity, decisions, bounded rework and severe-issue custody intent | port | Preserve decision policy while storage changes under R12 | no |
| P08 | Fast-track card schema, explicit files/constraints/tests/gates, ordered cards | port | Its task contract is independent of host orchestration | no |
| P09 | Durable reports, audit history, attempts and explicit lifecycle cleanup | port | Historical evidence must survive runtime migration | no |
| P10 | Mechanical review facts, style/split checks and test-quality checks | port | Keep deterministic algorithms and their fixtures | no |
| P11 | PRD frontmatter behavior, eligibility checks and resume-by-artifact rules | port | Keep policy semantics; translate state and execution interfaces separately | no |
| R01 | Root manifest, versioning, installation and release catalogs | redesign | Generate client metadata from one portable source of truth | no |
| R02 | `run-autopilot`, status, explicit PRD, review-batch | redesign | Invoke the current phase and the local skill or OVCAQ runtime path through tested host entry points | no |
| R03 | `design-solution`, PRD selection and `--rework` | redesign | Replace path/dispatch assumptions while preserving reviewed-design behavior | no |
| R04 | `plan-tasks`, replanning, expansion gates and tier classification | redesign | Emit normalized task records with explicit provider-neutral tier policy | no |
| R05 | 18 native agents, worker wrappers and effort choices | redesign | Retain Claude definitions in supported compatibility assets; add registration and model mappings for other hosts | no |
| R06 | `work`, Tess/Devon/Ivan/Pat, checkpoints and per-task commits | redesign | Replace dispatch/wait/task-state APIs; preserve isolated roles and existing gates | no |
| R07 | `review-work-completion`, reviewer fan-out, retries and close | redesign | Require independent jobs and authoritative review-gated transitions | no |
| R08 | `review-blindly` standalone entry point | redesign | Replace its foreground-Claude/timeout mechanics without weakening blindness | no |
| R09 | `review-plan` and its question flow | redesign | Replace host plan-mode and question-tool assumptions | no |
| R10 | `fast-track`, `--push`, delta review, ledgers and bounded rework | redesign | Preserve explicit push intent and full review requirements through host/runtime contracts | no |
| R11 | Code-selected full, fast-track and solo lanes | redesign | Controller extraction must preserve source lane/escalation transitions; parity is a release blocker | no |
| R12 | State writer, atomic transitions, task/attempt APIs, recovery and backups | redesign | All durable workflow writes go through Autopilot's one controller; helpers prepare artifacts/proposals | no |
| R13 | Loop, fresh sessions, review-once, pause/resume, limits and notifications | redesign | Use OVCAQ supervision and provider adapters | no |
| R14 | Tracon fleet/task/agent views, controls and stream rendering | redesign | Map presentation to Lantern and normalized observations/controls to OVCAQ operations API | no |
| R15 | Waves, worktrees, review slots, assembly, abort and landing | redesign | Preserve this capability only after its supervisor contract is established | no |
| R16 | Critical custody, push refusal, stub minting and deferred follow-up | redesign | Requires both durable ownership and pre-action enforcement | no |
| R17 | PRD-location hook | redesign | Retain Claude hook logic; adapt registration and editor/terminal events for additional hosts | no |
| R18 | Phase-delegation and post-leave guards; departure recording | redesign | Retain Claude guards; map other hosts' events while preserving phase ownership and handoff | no |
| R19 | Context cap and contract-card reinjection | redesign | Retain Claude behavior; adapt other hosts' context measurements and compaction events without changing budget policy | no |
| R20 | State-write, review-completeness and live-lane Stop hooks | redesign | Retain Claude hooks; prove equivalent enforcement and feedback on each additional host | no |
| R21 | Codex, Gemini and Sonnet runner commands/options | redesign | Preserve backend semantics through permission, event, quota and job adapters | no |
| R22 | Runner recursion guard and host markers | redesign | Permit authorized coordinators while retaining bounded child dispatch | no |
| R23 | Hook doctor check/repair, dry-run and exit meanings | redesign | Keep host-scoped operator maintenance separate from unattended execution | no |
| R24 | Qwen optional lane, health checks and output guards | redesign | Keep an optional capability; absence must retain the documented fallback | no |
| R25 | Legacy/shadow/workflow consensus engines | redesign | Host-local workflow execution needs an explicit adapter; preserve legacy fallback | no |
| R26 | Catchup, engram context, agoge QA, rationalization synonyms and notification integrations | redesign | Declare capability dependencies and their existing failure/fallback contracts | no |
| R27 | Plugin roots, reference paths and cross-skill helpers | redesign | Resolve from the installed package without Claude text substitution | no |
| R28 | Python locking, process signals and OS probes | redesign | `fcntl`/process-group behavior requires a declared Unix baseline or OS adapters | yes |
| R29 | Anthropic connectivity probe, Claude plugin registry pins and home-directory registries | redesign | Move provider-specific runtime assumptions to their owners | yes |
| R30 | Release checks and test fixture locations | redesign | Separate shipped runtime from maintainer tooling without losing behavioral tests | no |
| R31 | Sonnet runner does not forward the effort requested by its callers | redesign | Make the documented effort contract executable and verify generated argv | yes |

No drop walkthrough is needed: this feasibility proposal retains all capabilities. Existing OVCAQ decisions to retire particular legacy *state fields* do not by themselves establish that the corresponding plugin behavior has been preserved.

## Consumer Cutover

The scan covered the local GitHub portfolio plus the live shell integration and global instructions. Historical transcripts, retired copies, caches, and completed management artifacts are evidence, not consumers to rewrite.

| Consumer | Current reference | New reference | Cutover step |
| --- | --- | --- | --- |
| Claude central marketplace | `claude-plugins/.claude-plugin/marketplace.json` points to `buvis/claude-autopilot.git` | Tested catalog entry for `agent-plugins/plugins/autopilot` | Publish only after package and runtime parity; preserve command identity or document changes |
| Source direct marketplace/install docs | `.claude-plugin/marketplace.json`, README installation commands | Tested target installation instructions | Update and deprecate the old distribution when users can install the replacement |
| Live dotfiles shell | `~/.config/bash/plugins/development.plugin.bash` resolves Claude cache; exposes `autopilot`, `autoclaude`, `tracon` | Local plugin skill invocations or OVCAQ runtime commands | Follow OVCAQ's existing personal-cutover sequence; finish old batches first |
| Global agent instructions | `~/.claude/AGENTS.md` names `/autopilot:*` and fresh-session rules | Same invariants plus tested per-host invocations | Edit the authoritative file, never its symlink pointers |
| OVCAQ drivers | Claude `/autopilot:run-autopilot`; Codex `$run-autopilot` | Installed skill name and canonical controller mutation contract | Verify both with real package loading and phase handoff |
| Agent-skills documentation copies | `agent-skills/docs/plugin-skills/` and README portability guidance | Target ownership and capability documentation | Refresh documentation copies; do not expose old runtime-bound prose as standalone skills |
| Agoge drain integration | Autopilot loop launches `/run-agoge` with drain authorization label | Required pinned agoge for OVCAQ personal cutover; optional only outside that configured profile | Preserve status/failure behavior; keep its runtime ownership external |
| Source tests, scripts and CI/release tooling | Root-relative `skills/`, `agents/`, `hooks/`; `dev/bin/release*` | Target package, `tools/autopilot`, `tests/autopilot`, target CI | Carry fixtures and gates across before source deletion |
| Existing project PRDs and runtime state | PRD lifecycle directories and legacy Autopilot state | Same PRD inputs; fresh controller workflow and OVCAQ execution state for new batches | Preserve historical artifacts; no silent in-flight migration |
| Specflow plans and provenance | Discovery plan says design/tasks stay in Autopilot | Portable Autopilot ownership, with Specflow's separate approvals intact | Update provenance at cutover; any new artifact bridge is separate work |

`buvis/home` contains older copies, and `cellar`/private baseline folders contain historical evidence. They do not justify changing active runtime behavior or rewriting history. Re-scan executable consumers immediately before retirement.

## Phases (dependency order)

[Canonical design](../designs/00011-autopilot-standalone-design.md) defines exact dependencies and contracts.

1. AP00012 freezes assets/review evidence and creates eligibility checks.
2. In parallel: AP00013–00015 port helpers/hosts/procedures; AP00018–00021 extract the canonical controller.
3. AP00016 wires standalone stateful sessions; AP00017 certifies independent distribution without OVCAQ.
4. OV00057 consumes controller contracts; OV00058 removes old workflow authority after installed equivalence and00062 robustness.
5. OV00059–00061 add mixed-driver jobs, supervision recovery and waves; OV00064 operations API can run beside this work after00058.
6. Lantern00001–00003 implement/test the separate client; OV00065 removes bundled UI after installed parity.

The plugin owns stateful lifecycle but never automatic cross-session spawning. OVCAQ owns execution but never another workflow writer. Lantern owns presentation only. Held provisioning/cutover/release remain separate; full retirement requires all inventory evidence.

## Retirement

The retirement PRD is [source PRD 00370, held](../../../../../claude-autopilot/docs/dev/project-management/prds/hold/00370-retire-source-package-v1.md). It removes the old package only after the complete matrix, expanded inventory, regression dispositions, real-host certificates and consumer cutover receipts are satisfied and its exact target ledger is authorized. Neither the earlier Specflow plan nor this assessment activates retirement.

- [ ] P01: the same design fixtures retain reuse, placement, interface, risk and test-strategy content.
- [ ] P02: task contracts retain dependency ordering, sizing evidence, acceptance criteria and verification instructions.
- [ ] P03: every persona and rubric is accounted for and produces the required verdict coverage.
- [ ] P04: blind-review prompts contain only allowed spec/rubric/context inputs, never implementation narrative.
- [ ] P05: accepted review artifacts retain required sections, provenance, verdicts and actual test evidence.
- [ ] P06: pipeline scenarios retain test-first, adversarial, red-check, per-task and final-verification rules.
- [ ] P07: equivalent findings yield equivalent severity, action, cap, deferral and custody outcomes.
- [ ] P08: valid/invalid fast-track card fixtures retain their results and card execution order.
- [ ] P09: completion and cleanup preserve durable reports, reviews, decisions and attempts.
- [ ] P10: deterministic fact/style/split/test-quality fixtures retain their outcomes.
- [ ] P11: eligibility, frontmatter and resume fixtures retain their behavior, including explicit cap defaults.
- [ ] Every principal/expanded behavior row, configuration/state-field mapping and source regression disposition has an implemented owner, current verification evidence and user-facing documentation; unavailable features do not satisfy retirement. The frozen expected ID set prevents omitted rows or renamed headings from hiding a drop.
- [ ] Fresh-session review, code-owned lane routing, reviewer isolation and mandatory lenses pass on every advertised execution host.
- [ ] The consumer table has no remaining active dependency on the source package; historical citations may remain explicitly historical.
- [ ] Each new batch uses Autopilot's controller as its only workflow writer; no legacy batch remains in flight and no unrequested importer has been added.
- [ ] Target release checks and the source-removal CI are green; the replacement has been installed and exercised through its actual distribution path.

## Unresolved questions

No blocking architecture question. Lantern is a provisional name. Host support requires capability evidence/refusal. Specflow handoff remains a separate future contract.
