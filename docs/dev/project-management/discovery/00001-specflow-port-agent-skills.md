# Port Plan: specflow (from agent-skills SDLC skills)

_Freshness: generated 2026-09-27 from buvis/agent-skills master - regenerate if the source has moved on since._

Status: draft. Port/redesign table approved 2026-09-27; drop walkthrough complete 2026-09-28.

Sources (`buvis/agent-skills/skills/`): elicit-requirements, create-prd, spike,
review-discovery-doc, review-design-doc, review-prd-backlog.
Target: `plugins/specflow` runtime skill, per-phase references
(spec: `intake/processed/specflow/00001-initial-delivery/`).
Sibling plan: `00001-specflow-port-autopilot-phases.md` (design-solution,
plan-tasks phase behavior; no retirement).
Decisions: `meta/decisions.md` (2026-09-27).

Totals: 469 rows - 231 port, 179 redesign, 59 drop.

## Inventory Matrix

### Port and redesign (single approval)

| id | source skill | phase | row | classification | reason | code-only | evidence |
|---|---|---|---|---|---|---|---|
| ELI-01 | elicit-requirements | intake | Takes an optional argument: a rough idea or a file path | redesign | Input becomes an intake item under `intake/new/` (or a free-text idea that specflow saves there first) | no | E/SKILL.md:4,28 |
| ELI-02 | elicit-requirements | intake | Looks for input in order: argument, then prior work (plan-mode output, `spikes/`, `discovery/`), then the conversation | redesign | Order becomes argument, then `intake/new/`, then the existing `.kiro/specs/NNNNN-*`, then the conversation. The `discovery/` and `spikes/` lookups go | no | E/SKILL.md:26-30 |
| ELI-03 | elicit-requirements | intake | Reads the input file and pulls out the problem, requirements, constraints, success criteria and open questions. Skips questions the input already answers | port | Same extraction from the intake item | no | E/SKILL.md:29,32 |
| ELI-04 | elicit-requirements | intake | Scores depth on 4 dimensions: requirement clarity, scope breadth, codebase impact, problem complexity (low/med/high) | redesign | The rubric feeds the standard/quick profile recommendation (WF-003.5) instead of 3 depth levels | no | E/SKILL.md:36-41; E/references/classification-guide.md:5-45 |
| ELI-05 | elicit-requirements | intake | Rule: all low = minimal, any high = comprehensive, else standard | redesign | Three levels fold into two: all low = quick, else standard. Add the WF-003.6 forced-standard triggers (security, architecture, migration, public API, cross-component) | no | E/references/classification-guide.md:47-53 |
| ELI-06 | elicit-requirements | intake | Announces the depth with a 1-line rationale. "go deeper" / "keep it light" overrides it; silence accepts it | redesign | Becomes the profile recommendation with its basis plus a developer override, recorded as `profile` in `.specflow.json`. Silence may accept a profile but never an approval (WF-002.3) | no | E/SKILL.md:45-49 |
| ELI-07 | elicit-requirements | intake | Per-depth summaries: question counts, brownfield scope, doc size (~30 / 60-100 lines / full) | redesign | Moves to `profiles/{quick,standard}.md` as per-profile expectations | no | E/references/classification-guide.md:55-75 |
| ELI-08 | elicit-requirements | intake | Brownfield analysis only at standard+ depth | port | Matches WF-003.2/3: repository discovery in standard, targeted discovery in quick | no | E/SKILL.md:51-53 |
| ELI-09 | elicit-requirements | intake | Pattern scan for similar existing implementations in the project's source directories | port | Generic repo scan; host-neutral | no | E/SKILL.md:55 |
| ELI-11 | elicit-requirements | intake | Dependency map: existing modules the feature touches | port | Repo-agnostic | no | E/SKILL.md:56 |
| ELI-12 | elicit-requirements | intake | Convention extraction: naming, file layout, testing approach | port | Repo-agnostic | no | E/SKILL.md:57 |
| ELI-13 | elicit-requirements | intake | Integration surface: the files and functions that would change | port | Repo-agnostic; feeds design | no | E/SKILL.md:58 |
| ELI-14 | elicit-requirements | intake | Uses scan findings to fill in question options, skip obvious questions, and write the Codebase Context section | redesign | Findings go into requirements.md `Assumptions` and later design.md `Context and constraints`; there is no discovery doc | no | E/SKILL.md:60-63 |
| ELI-15 | elicit-requirements | requirements | Picks questions from the question bank by depth | redesign | The bank moves into the requirements-phase reference, keyed by profile | no | E/SKILL.md:67; E/references/question-bank.md:1-3 |
| ELI-16 | elicit-requirements | requirements | One question per message | port | Required by ART-002.6 and the usability NFR. Drop the pointer to the global CLAUDE.md rule; state the rule inline | no | E/SKILL.md:70 |
| ELI-17 | elicit-requirements | requirements | Uses the `AskUserQuestion` tool with multiple choice; open-ended for scope and risk | redesign | Host-neutral: numbered options in plain text, or the host's structured-question tool if it has one. No Claude-only tool dependency | no | E/SKILL.md:16,71 |
| ELI-18 | elicit-requirements | requirements | Puts the recommended option first, suffixed " (Recommended)" with a 1-line rationale; neutral when it is a toss-up | port | Host-neutral wording rule | no | E/SKILL.md:72; E/references/question-bank.md:139 |
| ELI-19 | elicit-requirements | requirements | Skips questions already answered and logs the inferred answer | redesign | Inferred answers land in requirements.md `Assumptions` (ART-002.5) instead of a Discovery Log | no | E/SKILL.md:73; E/references/question-bank.md:141 |
| ELI-20 | elicit-requirements | requirements | Appends each Q&A pair to the working file right after the answer (so it survives compaction) | redesign | Needs a Markdown home, because STATE-001.3 bans developer prompts in `.specflow.json`. Candidates: the intake item, or a clarifications section. Open decision | no | E/SKILL.md:74,120; E/references/question-bank.md:142 |
| ELI-21 | elicit-requirements | requirements | Comprehensive depth: after all questions, checks answers for contradictions and asks one resolution question | port | Applies in the standard profile | no | E/SKILL.md:75; E/references/question-bank.md:124-134 |
| ELI-22 | elicit-requirements | requirements | Question count by depth: 0-2 / 3-6 / 6-12 | redesign | Re-banded per profile (quick about 0-2, standard about 3-12) | no | E/SKILL.md:77-80 |
| ELI-23 | elicit-requirements | requirements | Early exit on "that's enough": stop asking and write with what exists | port | Unanswered items go to `Unresolved questions` | no | E/SKILL.md:82 |
| ELI-24 | elicit-requirements | requirements | Defines a non-answer: "don't know", "whatever you think", "I'd need to see it" | port | Host-neutral routing signal | no | E/SKILL.md:84 |
| ELI-25 | elicit-requirements | requirements | Spike fork: a 2nd non-answer on a contract-level question offers Spike it / Keep answering / Park as open questions | redesign | Spike folds into specflow (DEC #4). Park routes to `Unresolved questions`; the offer is host-neutral, not AskUserQuestion | no | E/SKILL.md:84 |
| ELI-26 | elicit-requirements | requirements | On spike convergence, folds its ASSUMPTIONS into the log, resumes, and skips spike's graduate step | redesign | Depends on how spike ports. Spike output feeds requirements.md `Assumptions` | no | E/SKILL.md:84 |
| ELI-27 | elicit-requirements | requirements | Writes the output from the discovery template at the classified depth | redesign | The output is requirements.md in the Kiro structure (REQ IDs, user stories, EARS), DES §6.2 | no | E/SKILL.md:88; DES:221-239 |
| ELI-29 | elicit-requirements | intake | Sequence number = max 5-digit prefix across `prds/**` and `discovery/`, plus 1 | redesign | Scans `intake/{new,processed}` and `.kiro/specs/` for the shared NNNNN (DEC #2). The `prds/` tree is not scanned | no | E/SKILL.md:90-93 |
| ELI-30 | elicit-requirements | requirements | Creates the output directory if it is missing | port | Same for `.kiro/specs/NNNNN-<title>/` | no | E/SKILL.md:97 |
| ELI-31 | elicit-requirements | requirements | Content rule: no stubs, "N/A" or "TBD"; leave out sections that do not apply | redesign | Keep no-placeholder (validator, VAL-001.3). But design.md marks omitted concerns "Not applicable" with a reason (DES:263), so the rule becomes per-artifact | no | E/SKILL.md:99-101; E/references/discovery-template.md:145 |
| ELI-32 | elicit-requirements | requirements | Discovery Log is mandatory at every depth (traceability to user decisions) | redesign | Traceability is kept, in the same home as ELI-20 | no | E/SKILL.md:102; E/references/discovery-template.md:141 |
| ELI-33 | elicit-requirements | requirements | Open Questions section, handed on to create-prd | port | Maps to requirements.md `Unresolved questions` (ART-002.5) | no | E/SKILL.md:103; E/references/discovery-template.md:142 |
| ELI-34 | elicit-requirements | requirements | Suggests `/review-discovery-doc` then `/create-prd`; never auto-invokes them | redesign | The next step is the requirements approval gate (WF-002.1 summary). The slash-command pointers go; the no-auto-progress rule stays | no | E/SKILL.md:105-112 |
| ELI-36 | elicit-requirements | requirements | Depends on the personal `spike` skill | redesign | Spike becomes a specflow reference (DEC #4), not an external skill | no | E/SKILL.md:15 |
| ELI-37 | elicit-requirements | requirements | Principle: when in doubt, ask; never assume requirements | port | Matches ART-002.6 | no | E/SKILL.md:118 |
| ELI-38 | elicit-requirements | intake | Principle: adaptive depth | port | Realized as profiles | no | E/SKILL.md:119 |
| ELI-39 | elicit-requirements | requirements | Principle: keep questions in files, not just chat | port | Same home as ELI-20 | no | E/SKILL.md:120 |
| ELI-40 | elicit-requirements | requirements | Principle: human approval gate before the doc becomes a PRD | port | Kept and made stronger by hash-bound approval (WF-002) | no | E/SKILL.md:121 |
| ELI-41 | elicit-requirements | intake | Principle: do not ask what code can answer; state the finding | port | Host-neutral | no | E/SKILL.md:122; E/references/question-bank.md:140 |
| ELI-42 | elicit-requirements | requirements | Template: `Classification` header (depth + date) | redesign | Profile goes to `.specflow.json`. requirements.md keeps a status/date header | no | E/references/discovery-template.md:10-11 |
| ELI-43 | elicit-requirements | requirements | Template: `Problem` (length scales by depth) | redesign | Maps to requirements.md `Purpose` | no | E/references/discovery-template.md:13,39,89 |
| ELI-44 | elicit-requirements | requirements | Template: Must have / Nice to have requirement lists | redesign | Become REQ-NNN items. Nice-to-have needs a priority marker or goes to Out of scope (Kiro has no MoSCoW) | no | E/references/discovery-template.md:18-19,44-48 |
| ELI-45 | elicit-requirements | requirements | Template: `Out of scope` | port | Same section in requirements.md | no | E/references/discovery-template.md:21,50 |
| ELI-46 | elicit-requirements | requirements | Template: `Constraints` (standard+) | redesign | Becomes the Non-functional requirements / Assumptions sections | no | E/references/discovery-template.md:53-54 |
| ELI-47 | elicit-requirements | design | Template: `Codebase Context` (relevant code, conventions, integration points, similar implementations) with file paths, standard+ only | redesign | Moves to design.md `Context and constraints` | no | E/references/discovery-template.md:56-59,106-110,143 |
| ELI-48 | elicit-requirements | design | Template: `Approach` (chosen, why, rejected alternatives with reasons), comprehensive only | redesign | Moves to design.md `Alternatives considered` (ART-003.4) | no | E/references/discovery-template.md:112-117,144 |
| ELI-49 | elicit-requirements | requirements | Template: `Success Criteria` (measurable) | redesign | Become EARS acceptance criteria per REQ (ART-002.2) | no | E/references/discovery-template.md:24-25,61-62 |
| ELI-50 | elicit-requirements | requirements | Template: `Risks` with mitigation | redesign | requirements.md has no Risks section. Route to design.md or the approval summary (WF-002.1). Open decision | no | E/references/discovery-template.md:64-65 |
| ELI-51 | elicit-requirements | intake | Classification-guide examples (`track-cost.sh`, "autopilot state file", `costs.jsonl`) | redesign | Keep the rubric; swap the buvis-specific examples for generic ones | no | E/references/classification-guide.md:15,23,34,44 |
| ELI-52 | elicit-requirements | requirements | Q1 Problem validation (repeated pain / preventive / external / other) | port | Generic | no | E/references/question-bank.md:7-15 |
| ELI-53 | elicit-requirements | requirements | Q2 Scope boundaries, open-ended, prompted with adjacent features | port | Generic; feeds Out of scope | no | E/references/question-bank.md:17-23 |
| ELI-54 | elicit-requirements | requirements | Q3 Success criteria (measurable / behavioral test / manual checklist / other) | redesign | Steer answers toward testable EARS criteria; a manual checklist needs a documented exception (VAL-002.1) | no | E/references/question-bank.md:25-33 |
| ELI-55 | elicit-requirements | intake | Q4 Integration points, multi-select, options from the scan, brownfield only | port | Generic | no | E/references/question-bank.md:35-45 |
| ELI-56 | elicit-requirements | requirements | Q5 Constraints, multi-select (backwards-compatible / no new deps / performance / other) | port | Generic; feeds NFRs | no | E/references/question-bank.md:47-57 |
| ELI-58 | elicit-requirements | design | Q7 Approach preference: 2-3 approaches with tradeoffs | redesign | Moves to the design phase; the answer lands in `Alternatives considered` | no | E/references/question-bank.md:71-81 |
| ELI-59 | elicit-requirements | requirements | Q8 Decomposition check: one PRD or a split | redesign | Split = separate specs, each with its own NNNNN and intake item | no | E/references/question-bank.md:83-91 |
| ELI-60 | elicit-requirements | requirements | Q9 Risk identification, open-ended, with category prompts | port | Generic; home per ELI-50 | no | E/references/question-bank.md:93-99 |
| ELI-61 | elicit-requirements | design | Q10 Pattern reuse: pick which found pattern to follow | redesign | Design phase; quick profile documents the reused pattern (ART-003.5) | no | E/references/question-bank.md:101-113 |
| ELI-62 | elicit-requirements | requirements | Q11 Domain-specific edge cases | port | Become EARS unwanted-behavior criteria | no | E/references/question-bank.md:115-122 |
| ELI-63 | elicit-requirements | requirements | Q12 Contradiction resolution (X wins / Y wins / not in conflict) | port | Generic | no | E/references/question-bank.md:124-134 |
| ELI-64 | elicit-requirements | requirements | Multiple choice always includes "Other" | port | Host-neutral | no | E/references/question-bank.md:138 |
| PRD-01 | create-prd | requirements | Turns a plan, design doc or discovery doc into a structured PRD | redesign | The output is requirements.md, which replaces the PRD (DEC); structure per DES §6.2 | no | P/SKILL.md:8 |
| PRD-04 | create-prd | requirements | Step 0 gate: warn when no discovery doc was given; "skip" goes ahead; the gate is advisory | redesign | Warn when there is no intake item and offer to save one under `intake/new/`; keep it advisory | no | P/SKILL.md:25-36 |
| PRD-05 | create-prd | requirements | Treats a converged spike `spikes/<slug>/SPEC.md` as elicited input | redesign | Spike folds in (DEC #4); spike output becomes an intake item or input to requirements | no | P/SKILL.md:29 |
| PRD-06 | create-prd | requirements | Source order: discovery doc, explicit file, conversation | redesign | Intake item, explicit file, conversation | no | P/SKILL.md:40-44 |
| PRD-07 | create-prd | requirements | Pulls out problem, requirements, constraints, component dependencies and acceptance criteria | port | Same extraction | no | P/SKILL.md:46-52 |
| PRD-08 | create-prd | requirements | Picks a template by complexity: minimal / standard / full RPG | redesign | One Kiro requirements template per artifact; depth set by quick/standard profile | no | P/SKILL.md:56-62 |
| PRD-09 | create-prd | requirements | Read the template before drafting; keep every section in the same order under the same headings | port | Template is the structure contract; the validator enforces it | no | P/SKILL.md:64 |
| PRD-10 | create-prd | requirements | Do not copy structure from existing repo PRDs; the template is the single source of truth; keep repo tone | port | Guards against drift in `.kiro/specs` too | no | P/SKILL.md:66 |
| PRD-11 | create-prd | requirements | Functional decomposition: Capability > Feature with Description/Inputs/Outputs/Behavior | redesign | Becomes REQ-NNN with a user story and EARS criteria | no | P/SKILL.md:72; P/assets/standard.md:14-32 |
| PRD-12 | create-prd | design | Structural decomposition: repo tree plus one Module block each (maps-to, responsibility, exports) | redesign | Moves to design.md `Components and interfaces`, traced to REQ IDs (ART-003.3) | no | P/SKILL.md:73-76 |
| PRD-13 | create-prd | tasks | Dependency graph: Foundation / Core / Integration layers, mandatory even when trivial | redesign | Per-task `Depends on:` in tasks.md (ART-004.4); layers are optional grouping | no | P/SKILL.md:77 |
| PRD-14 | create-prd | tasks | Implementation phases in topological order; each task has a dependency ref and an acceptance criterion | redesign | tasks.md T-NNN with Requirements / Depends on / Verify (DES §6.4) | no | P/SKILL.md:78 |
| PRD-15 | create-prd | requirements | Mark invented contract details `(guess)`; never resolve ambiguity silently | port | Feeds the placeholder check (VAL-001.3) and the ELI-25 / PRD-29 gate | no | P/SKILL.md:80 |
| PRD-16 | create-prd | tasks | Unattended rule: no human mid-run; criteria must be checkable headlessly by command, test or file | redesign | specflow has human gates, so the autopilot premise goes. Keep "verification is a command/test/file check" (VAL-002), with developer-accepted exceptions (VAL-002.1) | no | P/SKILL.md:82 |
| PRD-17 | create-prd | tasks | Premise rule: a destructive task based on observed state states the premise and re-checks it at run time (skip and report on failure) | port | Generic safety rule; fits SEC-002.4. Drop the buvis incident anecdote | no | P/SKILL.md:84 |
| PRD-18 | create-prd | tasks | Metric rule: name the owned tests, never suite-wide totals | port | Generic; drop the batch anecdote | no | P/SKILL.md:86 |
| PRD-28 | create-prd | requirements | Split when the draft is over ~200 lines or has loosely coupled parts; related PRDs share a slug prefix | redesign | Split into separate specs, each with its own NNNNN folder | no | P/SKILL.md:118-124 |
| PRD-29 | create-prd | requirements | Structure gate: walk the template headings before saving | port | The agent self-checks and the validator enforces | no | P/SKILL.md:126-128 |
| PRD-30 | create-prd | requirements | Guess-density gate: 3 or more `(guess)`/TBD/TODO/contract-bearing open questions offer Spike / Resolve now / Save anyway | redesign | Runs as a pre-approval check in requirements and design, with host-neutral options. Save anyway leaves items in `Unresolved questions` | no | P/SKILL.md:130-132 |
| PRD-32 | create-prd | tasks | Task-authoring warnings: premise-skip text must be explicit; an edit to an existing test pins its expected count with an `rg -c` premise | redesign | Keep as tasks-phase guidance, cut loose from the model tier; make `rg` a generic "count check" | no | P/SKILL.md:162-165 |
| PRD-35 | create-prd | intake | Sequence scan across `prds/{backlog,wip,done,hold}` and `discovery/` | redesign | Scan `intake/{new,processed}` and `.kiro/specs/` for the shared NNNNN | no | P/SKILL.md:185-186,209-214 |
| PRD-36 | create-prd | intake | Collision rule: re-scan after writing; on a clash, renumber, delete the original, re-scan; best-effort, `/review-prd-backlog` catches what is left | redesign | Keep the re-scan over the new dirs (fits WF-006). Replace the `/review-prd-backlog` fallback with a validator check for duplicate NNNNN | no | P/SKILL.md:192 |
| PRD-37 | create-prd | requirements | File name `{seq}-{slug}-v{version}.md` | redesign | Folder `.kiro/specs/NNNNN-<prd-like-title>/` with fixed artifact names; no version suffix | no | P/SKILL.md:196-207; DEC:10-13 |
| PRD-39 | create-prd | requirements | A separate capability gets a new sequence number, not a version bump | port | Same rule: new spec, new NNNNN | no | P/SKILL.md:222 |
| PRD-43 | create-prd | requirements | Minimal template: Problem, Solution, Must/Nice, Module, Dependencies, Task phases, Success Criteria | redesign | Split across quick-profile requirements.md, design.md and tasks.md | no | P/assets/minimal.md:1-44 |
| PRD-44 | create-prd | requirements | Standard template Overview: Problem Statement, Target Users, Success Metrics | redesign | Maps to Purpose, user-story actors, and acceptance criteria / success measures | no | P/assets/standard.md:3-12 |
| PRD-45 | create-prd | design | Standard template Test Strategy: happy, edge and error scenarios | redesign | Moves to design.md `Testing strategy` | no | P/assets/standard.md:93-98 |
| PRD-46 | create-prd | design | Standard template Risks with mitigation | redesign | Same home question as ELI-50 | no | P/assets/standard.md:100-102 |
| PRD-47 | create-prd | tasks | RPG core principles: dual semantics, explicit dependencies, topological order, progressive refinement | redesign | Explicit deps and topological order go to the tasks phase; WHAT vs HOW maps to the requirements/design split | no | P/assets/example_prd_rpg.md:6-11 |
| PRD-49 | create-prd | design | RPG test pyramid and coverage-percent targets | redesign | Test mix goes into design.md `Testing strategy`; coverage targets are optional, not mandated | no | P/assets/example_prd_rpg.md:359-375 |
| PRD-50 | create-prd | design | RPG critical test scenarios per module (happy, edge, error, integration) | redesign | design.md `Testing strategy`, traced to REQ | no | P/assets/example_prd_rpg.md:377-394 |
| PRD-51 | create-prd | design | RPG architecture: components, data models, tech stack decisions with rationale, trade-offs and alternatives | redesign | Maps to design.md Architecture / Data model / Alternatives considered | no | P/assets/example_prd_rpg.md:403-424 |
| PRD-52 | create-prd | design | RPG risks: technical, dependency, scope, each with impact, likelihood, mitigation, fallback | redesign | Same home question as ELI-50 | no | P/assets/example_prd_rpg.md:428-451 |
| PRD-53 | create-prd | requirements | RPG appendix: references, glossary, open questions | redesign | Open questions go to `Unresolved questions`; glossary to Purpose/Scope; references to design.md | no | P/assets/example_prd_rpg.md:455-464 |
| SPK-01 | spike | trigger | Activates when an idea is too fuzzy to spec and a throwaway build answers faster; runs before elicitation/PRD; triggers "spike", "spike this", "prototype this idea", "throwaway prototype" | redesign | Becomes an intake-phase option (spike path) of the single runtime skill, chosen before requirements; trigger phrases move to the intake reference, not a separate skill description | no | SKILL.md:3 |
| SPK-02 | spike | preconditions | Needs only git and a host that can run an attended build loop | port | Host-neutral; holds on Kiro, Codex, Claude Code | no | SKILL.md:4 |
| SPK-03 | spike | graduate | Depends on personal skill `create-prd` for the Graduate path | redesign | create-prd folds into specflow; graduation hands off to the requirements phase inside the same skill | no | SKILL.md:13 |
| SPK-05 | spike | all | Principle: spec is a guess, throwaway build is the elicitation device; iterate attended until contract is real, then graduate; nothing built ships | port | Core behavior, host- and layout-neutral | no | SKILL.md:9 |
| SPK-06 | spike | rough spec | Write rough spec at `docs/dev/project-management/spikes/<slug>/SPEC.md` | redesign | `spikes/<slug>` is a buvis layout; store the rough spec as the intake item under `intake/new/` sharing the NNNNN number (e.g. `NNNNN-<title>/spike/SPEC.md`), moved to `processed/` on graduation | no | SKILL.md:23 |
| SPK-08 | spike | rough spec | SPEC records the user's idea verbatim | port | Matches intake as raw, unedited input | no | SKILL.md:25 |
| SPK-09 | spike | rough spec | SPEC states the smallest outcome that demonstrates the idea end to end | port | Host-neutral content rule | no | SKILL.md:26 |
| SPK-10 | spike | rough spec | SPEC lists guessed contract (inputs, outputs, interfaces), each marked `(guess)` | port | Content rule; feeds later REQ drafting | no | SKILL.md:27 |
| SPK-11 | spike | rough spec | If user gave only a phrase, ask at most one question, then guess the rest | port | Consistent with specflow's one-question-at-a-time clarification | no | SKILL.md:29 |
| SPK-12 | spike | rough spec | Rough spec timeboxed to ~10 minutes, no polish | port | Pacing guidance, host-neutral | no | SKILL.md:21 |
| SPK-13 | spike | build | Build the smallest end-to-end demo directly in session: no implementor dispatch, no TDD ceremony | redesign | No subagent dispatch exists in specflow anyway; restate as an explicit spike exemption from the implementation phase's task/test gates | no | SKILL.md:33 |
| SPK-14 | spike | build | Standalone idea: build inside the spike directory | redesign | Directory moves with SPK-06 to the NNNNN intake/spike location | no | SKILL.md:35 |
| SPK-15 | spike | build | Change to existing code: work on branch `spike/<slug>`, worktree if tree is dirty, never the current branch | port | Plain git, portable; name becomes `spike/NNNNN-<title>` for shared numbering | no | SKILL.md:36 |
| SPK-16 | spike | build | Sandbox only: never touch production data, live services, or anything irreversible | port | Safety rule, host-neutral | no | SKILL.md:37 |
| SPK-17 | spike | build | Input validation at real trust boundaries stays; tests, changelog, review, production-ready rules suspended (disposable code) | redesign | Suspended rules are buvis user-global rule files; restate as specflow-owned: spike code skips specflow verification/approval gates, trust-boundary validation stays | no | SKILL.md:37 |
| SPK-18 | spike | build | Timebox ~20 min build; if it will not demonstrate in ~1 hour, stop, report, send open questions to elicit-requirements | redesign | Keep timebox and stop rule; route overflow to specflow's standard requirements phase clarification instead of the elicit-requirements skill | no | SKILL.md:31,38 |
| SPK-19 | spike | report | Report first: what got built and how to run it (2-3 lines plus run command) | port | Output contract, host-neutral | no | SKILL.md:44 |
| SPK-20 | spike | report | Report `ASSUMPTIONS:` one line per choice made where SPEC was silent | port | Output contract; seeds requirements assumptions | no | SKILL.md:45 |
| SPK-21 | spike | report | Report `OPEN QUESTIONS:` what the build surfaced | port | Output contract; seeds one-at-a-time clarification | no | SKILL.md:46 |
| SPK-22 | spike | decide | Ask via AskUserQuestion with exactly three options: Refine and re-spike, Graduate, Discard | redesign | AskUserQuestion is Claude-only; present the same three choices as a plain-text single question | no | SKILL.md:50 |
| SPK-23 | spike | decide | Refine: fold answers into SPEC, rebuild in place, back to build step | port | Loop semantics are host-neutral | no | SKILL.md:50 |
| SPK-24 | spike | decide | Never chain refine cycles without the user; attended examine step is the value | port | Matches specflow's user-gated flow | no | SKILL.md:50 |
| SPK-25 | spike | decide | Discard: delete spike dir or branch, done | port | Plain git/file ops; also decide intake item fate (stays in `new/` or removed) in intake reference | no | SKILL.md:50 |
| SPK-26 | spike | graduate | Graduate: invoke create-prd with SPEC plus final assumptions and answers | redesign | Enters requirements phase producing `.kiro/specs/NNNNN-<title>/requirements.md` (EARS, stable REQ IDs); intake item moves to `processed/` | no | SKILL.md:54 |
| SPK-27 | spike | graduate | Formal contract records observed prototype behavior, not the original guesses | port | Content rule applies unchanged to requirements.md | no | SKILL.md:54 |
| SPK-28 | spike | graduate | Note in PRD context where the spike lives (dir or branch) as reference | redesign | Becomes the `Sources` backlink line in requirements.md pointing at intake item and spike branch/dir (decision 3) | no | SKILL.md:54 |
| SPK-29 | spike | graduate | Real implementation goes through normal pipeline (plan-tasks, work, full review) | redesign | Pipeline is specflow's design, tasks, implementation, verification phases, not autopilot skills | no | SKILL.md:56 |
| SPK-30 | spike | graduate | Real implementation rebuilds from scratch; spike code never merges | port | Rule is host-neutral; can be a verification-phase check | no | SKILL.md:56 |
| SPK-31 | spike | complete | Delete the spike once the formal implementation lands | redesign | Trigger becomes specflow `complete` phase cleanup of spike branch/dir | no | SKILL.md:56 |
| RDD-01 | review-discovery-doc | requirements | Frontmatter trigger: "review discovery doc", runs before create-prd | redesign | Becomes a `review requirements` intent inside the single runtime skill; no separate skill, no create-prd | no | SKILL.md:3 |
| RDD-03 | review-discovery-doc | requirements | Argument: path to the discovery doc | redesign | Target is `.kiro/specs/NNNNN-<title>/requirements.md`, resolved from the spec, not a free path | no | SKILL.md:4 |
| RDD-04 | review-discovery-doc | requirements | Required input is a doc under `docs/dev/project-management/discovery/` | redesign | Discovery docs do not exist in specflow; the reviewed artifact is requirements.md, raw input lives in intake/ | no | SKILL.md:25 |
| RDD-05 | review-discovery-doc | requirements | Path solicitation: scan last message for one path, confirm "Wrong doc? Say so now" | redesign | Resolve by spec number/title or current spec (WF-004 resume); keep the confirm line | no | SKILL.md:28 |
| RDD-06 | review-discovery-doc | requirements | No path: ask for an absolute path, wait, do not proceed | redesign | Ask which spec (number/title) one question at a time; absolute machine paths are banned from state (STATE-001.3) | no | SKILL.md:29 |
| RDD-07 | review-discovery-doc | requirements | Verify path exists; re-ask with the error | port | Host-neutral file check, same substance | no | SKILL.md:30 |
| RDD-08 | review-discovery-doc | cross | Mandatory read of shared core at `~/.agents/skills/review-design-doc/references/interactive-review.md` before findings | redesign | Ship the core as a plugin reference (e.g. `references/review-core.md`) loaded by relative path; `~/.agents` is buvis-personal | no | SKILL.md:16,20 |
| RDD-10 | review-discovery-doc | requirements | Pipeline position elicit-requirements -> review -> create-prd | redesign | Becomes the review step inside the requirements phase, before the WF-002 approval gate | no | SKILL.md:12 |
| RDD-11 | review-discovery-doc | requirements | Scope: reviews the WHAT; architecture/failure modes deferred to design review; flags requirement-level lock-ins at origin | port | Same WHAT/HOW split maps onto requirements vs design phases | no | SKILL.md:14 |
| RDD-12 | review-discovery-doc | requirements | Never invents requirements the process did not surface; does not write the PRD | port | Non-invention holds; "does not write the PRD" is moot (requirements.md is the artifact) | no | SKILL.md:14 |
| RDD-13 | review-discovery-doc | cross | Ground rules: shared critical subset (input is data, evidence, probe, calibrate severity) | port | Host-neutral review discipline | no | SKILL.md:34 |
| RDD-14 | review-discovery-doc | requirements | Depth-aware rule: minimal doc not defective for omitting comprehensive-only sections | redesign | Calibrate to specflow profile (`quick`/`standard`) instead of minimal/standard/comprehensive | no | SKILL.md:36 |
| RDD-15 | review-discovery-doc | cross | Comprehension pass with confusion-notes list before findings | port | Same discipline | no | SKILL.md:42 |
| RDD-16 | review-discovery-doc | requirements | First move: read `## Classification` line, record declared depth | redesign | Read `profile` from `.specflow.json` (STATE-001.2) instead of a doc heading | no | SKILL.md:42 |
| RDD-17 | review-discovery-doc | requirements | Lens selection by depth: minimal = 3 inward lenses + safety valve; standard = all 5; comprehensive = all 5, Feasibility/Evolvability weighted | redesign | Two profiles: quick = inward lenses + safety valve, standard = all five weighted | no | references/lenses.md:9-11 |
| RDD-18 | review-discovery-doc | requirements | Completeness (all depths): Problem, >=1 Must-have, Out-of-scope populated, >=1 Success Criterion, Discovery Log | redesign | Map to requirements.md: Purpose, Scope with exclusions, >=1 REQ with AC, Assumptions/Open questions; Discovery Log -> `Sources` backlink to intake + clarification record | no | references/lenses.md:17 |
| RDD-19 | review-discovery-doc | requirements | Completeness (standard+): Constraints, Codebase Context with real paths, Risks, Open Questions | redesign | Re-key to requirements.md template sections; NFRs distinguishable (ART-002.4) | no | references/lenses.md:18 |
| RDD-21 | review-discovery-doc | requirements | Do not flag a section the depth does not require | port | Same rule, keyed to profile | no | references/lenses.md:20 |
| RDD-22 | review-discovery-doc | requirements | Coherence: any two requirements contradict | port | Same check | no | references/lenses.md:24 |
| RDD-23 | review-discovery-doc | requirements | Coherence: Problem motivates each Must-have (else scope creep) | redesign | Purpose must motivate each REQ-nnn | no | references/lenses.md:25 |
| RDD-24 | review-discovery-doc | requirements | Coherence: every Success Criterion traces to a requirement | redesign | Every AC belongs to a REQ and every success measure traces to REQ IDs | no | references/lenses.md:26 |
| RDD-25 | review-discovery-doc | requirements | Coherence: Must-have vs Out-of-scope misplacement | port | Same check against Scope/exclusions | no | references/lenses.md:27 |
| RDD-26 | review-discovery-doc | requirements | Coherence: Discovery Log answers support derived requirements (drift) | redesign | Check REQs against the intake original (via `Sources` line) and recorded clarification answers | no | references/lenses.md:28 |
| RDD-27 | review-discovery-doc | requirements | Integrity: each Success Criterion falsifiable; flag vague qualifiers | redesign | Becomes "each AC is a testable EARS statement" (ART-002.2); structural part enforced by validator | no | references/lenses.md:32 |
| RDD-28 | review-discovery-doc | requirements | Integrity: each Must-have testable | port | Same, applied per REQ | no | references/lenses.md:33 |
| RDD-29 | review-discovery-doc | requirements | Integrity: Constraints real vs smuggled preferences | port | Same | no | references/lenses.md:34 |
| RDD-30 | review-discovery-doc | requirements | Integrity: build-blocking Open Questions flagged, not buried | port | Matches ART-002.5 | no | references/lenses.md:35 |
| RDD-31 | review-discovery-doc | requirements | Integrity: each requirement singular (split bundled needs) | port | Same; supports stable REQ IDs | no | references/lenses.md:36 |
| RDD-32 | review-discovery-doc | requirements | Integrity: HOW posing as WHAT; solution belongs to design-solution | redesign | Hand off to specflow design phase, not autopilot:design-solution | no | references/lenses.md:37 |
| RDD-33 | review-discovery-doc | requirements | Coherence-vs-Integrity tie-breaker (one element vs a link) | port | Same routing rule | no | references/lenses.md:41 |
| RDD-34 | review-discovery-doc | requirements | Feasibility: Must-have set minimal for the Problem | redesign | EARS REQs have no MoSCoW tiers; judge REQ count vs Purpose and recommend quick/standard profile | no | references/lenses.md:47 |
| RDD-35 | review-discovery-doc | requirements | Feasibility: single Must-have really a separate feature | port | Same; resolution is a new spec number | no | references/lenses.md:48 |
| RDD-36 | review-discovery-doc | requirements | Feasibility: requirement assumes a nonexistent capability | port | Same | no | references/lenses.md:49 |
| RDD-37 | review-discovery-doc | requirements | Feasibility: Problem big enough for the requirement count | port | Same | no | references/lenses.md:50 |
| RDD-38 | review-discovery-doc | requirements | Feasibility: whole discovery -> one PRD; create-prd splits at ~200 lines; recommend splitting the discovery | redesign | Recommend splitting into separate specs (new NNNNN, shared with intake); no create-prd split rule | no | references/lenses.md:51 |
| RDD-39 | review-discovery-doc | requirements | Evolvability: one-way-door decision in a requirement/constraint | port | Same | no | references/lenses.md:57 |
| RDD-40 | review-discovery-doc | requirements | Evolvability: closed list where domain implies growth | port | Same | no | references/lenses.md:58 |
| RDD-41 | review-discovery-doc | requirements | Evolvability: Out-of-scope exclusion removes a needed seam | port | Same | no | references/lenses.md:59 |
| RDD-42 | review-discovery-doc | requirements | Evolvability discipline: flag only named, foreseeable evolutions; hold tension with right-sizing | port | Same | no | references/lenses.md:60 |
| RDD-43 | review-discovery-doc | requirements | Resolution shapes per dimension (unmeasurable SC, contradiction, empty out-of-scope, over-scope, too big, one-way door) | redesign | Re-key section names (Nice-to-have, Open Questions, create-prd, design-solution) to requirements.md sections and specflow phases | no | references/lenses.md:64-69 |
| RDD-44 | review-discovery-doc | requirements | Severity Blocking = would make create-prd produce a wrong/unbuildable spec | redesign | Blocking = must be fixed before requirements approval (WF-002) | no | SKILL.md:47 |
| RDD-45 | review-discovery-doc | requirements | Severity Non-blocking (thin risks, vague constraint...) | port | Same | no | SKILL.md:48 |
| RDD-46 | review-discovery-doc | requirements | Severity Question (from confusion notes) | port | Same | no | SKILL.md:49 |
| RDD-47 | review-discovery-doc | cross | Present one at a time, severity order, doc order within severity | port | Matches one-question-at-a-time | no | SKILL.md:51 |
| RDD-48 | review-discovery-doc | cross | Batch mode: record choice, do not edit until the end | redesign | Unify with RDS immediate apply; batch state lives only in chat and is lost on host switch (WF-004.6) | no | SKILL.md:10,51 |
| RDD-49 | review-discovery-doc | cross | Apply pass: print full decision summary first as the recovery record | redesign | With immediate apply the doc is the record; keep a final decision summary for the approval summary (WF-002.1) | no | SKILL.md:54 |
| RDD-50 | review-discovery-doc | cross | Apply accepted edits by exact text; reconcile overlapping edits; disputed/skipped = no edit | redesign | Add WF-006 pre-write hash compare; approvals go stale on edit (WF-002.5) | no | SKILL.md:55 |
| RDD-51 | review-discovery-doc | requirements | Recap: raised / resolved / disputed / Open Questions added for create-prd | redesign | Recap feeds the approval-gate summary; no create-prd | no | SKILL.md:57 |
| RDD-52 | review-discovery-doc | cross | Card format: title, Dimension, Severity, Location, exactly 3-sentence body, impact line, 3 options with Edit | port | Plain-text card, host-neutral | no | SKILL.md:59-80 |
| RDD-53 | review-discovery-doc | cross | Picker: AskUserQuestion, labels = approach names, `(Recommended)` on 1, no 4th option, dispute via automatic "Other" | redesign | Numbered plain-text question; hosts without an auto "Other" need an explicit dispute/skip option | no | SKILL.md:82 |
| RDD-54 | review-discovery-doc | requirements | Example session is the output-format anchor | redesign | Rewrite example against a requirements.md with REQ IDs and EARS AC; drop discovery headings and AskUserQuestion mapping | no | SKILL.md:86; examples/sample-session.md:1-165 |
| RDD-55 | review-discovery-doc | cross | Success criteria: surprise + actionability; name skipped lenses/deferred findings | port | Same | no | SKILL.md:90 |
| RDD-56 | review-discovery-doc | cross | Session safety: interrupt before apply -> re-walk; during apply -> use printed summary | redesign | Replaced by immediate apply + disk resume (WF-004) | no | SKILL.md:94 |
| RDS-01 | review-design-doc | design | Frontmatter trigger "review design doc"; edits applied directly | redesign | Becomes the `review design` intent (design.md 5.1 intent table) | no | SKILL.md:3 |
| RDS-02 | review-design-doc | design | Argument: design doc path + related-context path + codebase path | redesign | Target is the spec's design.md; context = approved requirements.md (ART-003.1); codebase = the repo | no | SKILL.md:4,18-23 |
| RDS-03 | review-design-doc | cross | Compatibility: needs one-question-at-a-time host and edit ability | port | Matches specflow host assumptions | no | SKILL.md:5 |
| RDS-06 | review-design-doc | cross | Shared core read before findings | redesign | Plugin-local reference file, relative path | no | SKILL.md:14 |
| RDS-07 | review-design-doc | design | Path solicitation: scan message, confirm; else ask absolute path; verify with Read or `ls` | redesign | Resolve spec by number/title or current spec; no absolute paths | no | SKILL.md:25-29 |
| RDS-08 | review-design-doc | design | Ask for optional inputs only if the doc references them | redesign | requirements.md is always loaded; intake sources only if cited | no | SKILL.md:30 |
| RDS-09 | review-design-doc | cross | Comprehension pass + confusion notes | port | Same | no | SKILL.md:36 |
| RDS-10 | review-design-doc | design | Absorb related context, do not review it | port | requirements.md is context, not re-reviewed | no | SKILL.md:37 |
| RDS-11 | review-design-doc | design | Identify domain and maturity | port | Same | no | SKILL.md:38 |
| RDS-12 | review-design-doc | design | Pick tier mechanically (T3 conditions first, then T2, else T1) | redesign | Tie to profile: quick = Tier 1 floor; WF-003.6 triggers (security, arch, migration, public API) overlap Tier 2/3 and force standard | no | SKILL.md:39; references/triage.md:5 |
| RDS-13 | review-design-doc | design | Scan for signals routing to extra techniques | port | Same | no | SKILL.md:40 |
| RDS-14 | review-design-doc | design | Run the three quantitative scripts and cite output | redesign | Ship scripts inside the plugin and call by relative path; optional when host has no command runtime (design.md 5.3 fallback) | no | SKILL.md:41,72-76 |
| RDS-15 | review-design-doc | design | Run tier content: checklist, cardinal sins, premortem, tier additions | port | Same | no | SKILL.md:42-46 |
| RDS-16 | review-design-doc | cross | Present one at a time with picker of 4 options (3 + No edit) in card order | redesign | Plain-text numbered picker, host-neutral; no AskUserQuestion | no | SKILL.md:48 |
| RDS-17 | review-design-doc | cross | Apply chosen edit immediately; Edit must finish before next card; never batch | port | Chosen as specflow's single apply timing (see header); add WF-006 hash compare | no | SKILL.md:49-52 |
| RDS-18 | review-design-doc | cross | No edit: record reasoning in chat; Other free-form -> custom edit or skip | port | Same | no | SKILL.md:49 |
| RDS-19 | review-design-doc | design | Session-end recap (edits, disputed, open questions) and success criteria | redesign | Feeds the design approval summary (WF-002.1) | no | SKILL.md:53 |
| RDS-20 | review-design-doc | design | Interaction order: cardinal sins -> blocking -> non-blocking -> questions | port | Same | no | SKILL.md:57-62 |
| RDS-21 | review-design-doc | design | User may stop; sins and blockers walked before stopping | port | Same; unresolved blockers should block design approval | no | SKILL.md:64 |
| RDS-22 | review-design-doc | design | Tier disagreement: default up; disagreement is itself a finding | port | Same | no | SKILL.md:68; references/triage.md:82 |
| RDS-23 | review-design-doc | design | Script: section_weight_audit (>3x / <1/3 median, containers, code blocks) | redesign | Bundle in plugin scripts, relative path, stdlib-only | no | SKILL.md:74 |
| RDS-24 | review-design-doc | design | Script: claim_ladder_scan (compressed qualifiers with locations) | redesign | Bundle in plugin; see RDS-S6 grounding fix | no | SKILL.md:75 |
| RDS-25 | review-design-doc | design | Script: adversarial_signal_scan (imperatives, role changes vs framing) | redesign | Bundle in plugin | no | SKILL.md:76 |
| RDS-26 | review-design-doc | design | Scripts are advisory; reviewer judges | port | Same | no | SKILL.md:78 |
| RDS-27 | review-design-doc | cross | Success criteria: surprise + actionability, assessed conversationally | port | Same | no | SKILL.md:86 |
| RDS-28 | review-design-doc | cross | Session safety: doc is the single source of truth; "stop and ask Claude to flush pending decisions" | redesign | Keep the rule, drop the Claude-specific wording | no | SKILL.md:90-92 |
| RDS-31 | review-design-doc | design | Limitations: findings are claims the discipline was applied, not validated truth | port | Honest caveat, host-neutral | no | SKILL.md:106-108 |
| RDS-33 | review-design-doc | cross | Ground rule: distinguish decisions from directions | port | Same | no | references/interactive-review.md:15 |
| RDS-34 | review-design-doc | cross | Confusion-note discipline: drop notes you cannot articulate; style is not a note | port | Same | no | references/interactive-review.md:27 |
| RDS-35 | review-design-doc | cross | Canonical card: title, severity, location, one-paragraph body, 3 options with Why+Edit, option 4 No edit | port | Plain text | no | references/interactive-review.md:31-61 |
| RDS-36 | review-design-doc | cross | No-edit path must always exist (explicit 4 or picker Other) | port | Keep explicit option in plain-text hosts | no | references/interactive-review.md:63 |
| RDS-37 | review-design-doc | cross | No concrete edit -> downgrade to Question; option 1 = answer in chat, written into doc | port | Same | no | references/interactive-review.md:65 |
| RDS-38 | review-design-doc | cross | Picker ordering: same labels/order as card, `(Recommended)` on 1, no A/B/C | redesign | Same ordering rule, but the "picker" is a numbered chat question on hosts without one | no | references/interactive-review.md:67-74 |
| RDS-39 | review-design-doc | cross | Apply timing is per-skill | redesign | specflow fixes one timing (immediate) for all review intents | no | references/interactive-review.md:76,133 |
| RDS-40 | review-design-doc | cross | Three options distinct/relevant/justified/concrete; fewer allowed with explicit note; never pad | port | Same | no | references/interactive-review.md:78-89 |
| RDS-41 | review-design-doc | cross | Resolution taxonomy per severity (blocking / non-blocking / question shapes) | port | Same | no | references/interactive-review.md:91-114 |
| RDS-42 | review-design-doc | cross | Question sources; option 1 = reviewer's best read of intent | port | Same | no | references/interactive-review.md:116 |
| RDS-43 | review-design-doc | cross | Pick Recommended by stakes vs reversibility, then simplicity | port | Same | no | references/interactive-review.md:118 |
| RDS-44 | review-design-doc | cross | Success: surprise test; actionability; disputed blockers need stated reasons | port | Same | no | references/interactive-review.md:120-127 |
| RDS-45 | review-design-doc | cross | Resume by re-invoking on same doc; disputed findings may reappear (no memory) | redesign | Resume through specflow `continue` (WF-004); disputes could be recorded in design.md so they do not reappear, since state may not hold prompts (STATE-001.3) | no | references/interactive-review.md:131 |
| RDS-46 | review-design-doc | cross | Long sessions (>=15 findings): split by severity across sessions | port | Same | no | references/interactive-review.md:132 |
| RDS-47 | review-design-doc | design | Tier 1 conditions (<5 pages, internal, reversible state, <6 months) and run list | port | Content moves; selection per RDS-12 | no | references/triage.md:9-22 |
| RDS-48 | review-design-doc | design | Tier 2 conditions (persistent store, >1 consumer, rollback, cross-team, >6 months) and run list | port | Content moves | no | references/triage.md:24-36 |
| RDS-49 | review-design-doc | design | Tier 3 conditions (>=3 teams, vendor >=12mo, compliance, public API, 10x failure cost) and run list | port | Content moves | no | references/triage.md:38-51 |
| RDS-50 | review-design-doc | design | Thresholds are calibrated defaults, tune per team | port | Same | no | references/triage.md:7 |
| RDS-51 | review-design-doc | design | Signal-driven additions (13 signal -> technique maps) | port | Same | no | references/triage.md:53-69 |
| RDS-52 | review-design-doc | design | Tier upgrade mid-review, logged in "resolution log Summary" | redesign | No resolution log; state the upgrade in chat and in the approval summary | no | references/triage.md:73 |
| RDS-53 | review-design-doc | design | Tier upgrade triggers (hidden persistent data, cross-team, lock-in, compliance, false reversibility) | port | Same | no | references/triage.md:75-80 |
| RDS-54 | review-design-doc | design | Checklist verdict scale (Solid/Concern/Missing/N/A) with cited evidence | port | Same | no | references/checklist.md:4 |
| RDS-55 | review-design-doc | design | Checklist 1 Problem framing (why now, outcome, non-goals, measurable metrics) | redesign | Problem lives in approved requirements.md; in design review check each element traces to REQ IDs (ART-003.3) instead of re-litigating | no | references/checklist.md:6-10 |
| RDS-56 | review-design-doc | design | Checklist 2 Stakeholders and ownership | port | Same | no | references/checklist.md:12-16 |
| RDS-57 | review-design-doc | design | Checklist 3 Assumptions and constraints | port | Same | no | references/checklist.md:18-23 |
| RDS-58 | review-design-doc | design | Checklist 4 Alternatives considered (do nothing, buy vs build, strawmen, bias) | port | Matches ART-003.4 | no | references/checklist.md:25-30 |
| RDS-59 | review-design-doc | design | Checklist 5 Architecture and component design | port | Same | no | references/checklist.md:32-37 |
| RDS-60 | review-design-doc | design | Checklist 6 Data model and lifecycle | port | Same | no | references/checklist.md:39-45 |
| RDS-61 | review-design-doc | design | Checklist 7 Interfaces and contracts | port | Same | no | references/checklist.md:47-53 |
| RDS-62 | review-design-doc | design | Checklist 8 Concurrency, consistency, semantics | port | Same | no | references/checklist.md:55-60 |
| RDS-63 | review-design-doc | design | Checklist 9 Scalability and performance | port | Same | no | references/checklist.md:62-68 |
| RDS-64 | review-design-doc | design | Checklist 10 Failure modes and resilience | port | Same (ART-003.2 failure handling) | no | references/checklist.md:70-76 |
| RDS-65 | review-design-doc | design | Checklist 11 Observability | port | Same | no | references/checklist.md:78-83 |
| RDS-66 | review-design-doc | design | Checklist 12 Security | port | Same (ART-003.2 security) | no | references/checklist.md:85-93 |
| RDS-67 | review-design-doc | design | Checklist 13 Privacy and compliance | port | Same | no | references/checklist.md:95-101 |
| RDS-68 | review-design-doc | design | Checklist 14 Cost and operational burden | port | Same | no | references/checklist.md:103-108 |
| RDS-69 | review-design-doc | design | Checklist 15 Deployment and topology | port | Same | no | references/checklist.md:110-115 |
| RDS-70 | review-design-doc | design | Checklist 16 Migration and rollout | port | Same (ART-003.2 migration/rollout) | no | references/checklist.md:117-123 |
| RDS-71 | review-design-doc | design | Checklist 17 Testability | port | Same (ART-003.2 testing strategy) | no | references/checklist.md:125-130 |
| RDS-72 | review-design-doc | design | Checklist 18 Timeline and delivery (estimates, milestones, critical path) | redesign | Milestones and ordering belong to tasks.md (ART-004); design review checks only phasing that constrains the design | no | references/checklist.md:132-136 |
| RDS-73 | review-design-doc | design | Checklist 19 Documentation and runbook | port | Same | no | references/checklist.md:138-141 |
| RDS-74 | review-design-doc | design | Checklist 20 Open questions and risks | port | Same | no | references/checklist.md:143-147 |
| RDS-75 | review-design-doc | design | Checklist 21 Internal consistency incl. word-count measurement anchor | port | Same | no | references/checklist.md:149-153 |
| RDS-76 | review-design-doc | design | Checklist 22 Overengineering check | port | Same | no | references/checklist.md:155-156 |
| RDS-77 | review-design-doc | design | Checklist 23 Reversibility check (one-way vs two-way doors) | port | Same | no | references/checklist.md:158-159 |
| RDS-78 | review-design-doc | design | Checklist 24 Six-months-later test | port | Same | no | references/checklist.md:161-162 |
| RDS-79 | review-design-doc | design | Checklist 25 Design vs reality, only if `$3` codebase path given | redesign | Always run: the spec lives in the repo, so claims are checkable; drop CLI-arg gating | no | references/checklist.md:164-165 |
| RDS-80 | review-design-doc | design | Cardinal sins flagged as blockers regardless of justification | port | Same | no | references/cardinal-sins.md:4 |
| RDS-81 | review-design-doc | design | Sin: no rollback plan for stateful changes | port | Same | no | references/cardinal-sins.md:6 |
| RDS-82 | review-design-doc | design | Sin: secrets in config/env/source | port | Same (SEC-002.2 spirit) | no | references/cardinal-sins.md:7 |
| RDS-83 | review-design-doc | design | Sin: SPOF on write path without acceptance | port | Same | no | references/cardinal-sins.md:8 |
| RDS-84 | review-design-doc | design | Sin: no human owner for production operation | port | Same | no | references/cardinal-sins.md:9 |
| RDS-85 | review-design-doc | design | Sin: no observability for user-visible ops | port | Same | no | references/cardinal-sins.md:10 |
| RDS-86 | review-design-doc | design | Sin: "figure it out later" on a load-bearing concern | port | Same | no | references/cardinal-sins.md:11 |
| RDS-87 | review-design-doc | design | Sin: unbounded resource use without limits | port | Same | no | references/cardinal-sins.md:12 |
| RDS-88 | review-design-doc | design | Sin: schema change without migration plan | port | Same | no | references/cardinal-sins.md:13 |
| RDS-89 | review-design-doc | design | Sin: vendor lock-in for critical infra without exit | port | Same | no | references/cardinal-sins.md:14 |
| RDS-90 | review-design-doc | design | Sin: authn/authz deferred | port | Same | no | references/cardinal-sins.md:15 |
| RDS-91 | review-design-doc | design | Sin: no data deletion/correction/export path | port | Same | no | references/cardinal-sins.md:16 |
| RDS-92 | review-design-doc | design | Sin: persistent data without backup and tested restore | port | Same | no | references/cardinal-sins.md:17 |
| RDS-93 | review-design-doc | design | Sin: public API without versioning | port | Same | no | references/cardinal-sins.md:18 |
| RDS-94 | review-design-doc | design | Sin: hardcoded credentials in doc or code | port | Same | no | references/cardinal-sins.md:19 |
| RDS-95 | review-design-doc | design | Sin: critical decisions by acclamation without alternatives | port | Same | no | references/cardinal-sins.md:20 |
| RDS-96 | review-design-doc | design | Anti-pattern list (15 patterns: vague qualifiers, name-dropping, deferred concerns, analogy, legend-less diagrams, ... disproportionate depth) | port | Same; note triage.md:36 says "all 14" but the file lists 15, fix the count in the port | no | references/anti-patterns.md:6-20; references/triage.md:36 |
| RDS-97 | review-design-doc | design | Stress tests (10 scenarios) | port | Same | no | references/stress-tests.md:6-15 |
| RDS-98 | review-design-doc | design | Probing reasoning: pick Socratic / five-whys / claim ladder by gap | port | Same | no | references/techniques.md:6-11 |
| RDS-99 | review-design-doc | design | Socratic questioning (6 question types; assertive vs Socratic) | port | Same | no | references/techniques.md:13-26 |
| RDS-100 | review-design-doc | design | Five-whys descent (bedrock / unvalidated / inherited / habit / authority) | port | Same | no | references/techniques.md:28-36 |
| RDS-101 | review-design-doc | design | Claim ladder | port | Same | no | references/techniques.md:38-44 |
| RDS-102 | review-design-doc | design | Premortem (18-month obituary; 6-month regret interview) | port | Same | no | references/techniques.md:46-49 |
| RDS-103 | review-design-doc | design | Inverse problem | port | Same | no | references/techniques.md:51-52 |
| RDS-104 | review-design-doc | design | Cognitive bias scan (9 biases) | port | Same | no | references/techniques.md:54-64 |
| RDS-105 | review-design-doc | design | Negative space audit | port | Same | no | references/techniques.md:66-67 |
| RDS-106 | review-design-doc | design | Conway's law check | port | Same | no | references/techniques.md:69-70 |
| RDS-107 | review-design-doc | design | Hidden coupling map | port | Same | no | references/techniques.md:72-73 |
| RDS-108 | review-design-doc | design | Falsifiability check | port | Same | no | references/techniques.md:75-76 |
| RDS-109 | review-design-doc | design | Compression test (load-bearing 10%, telephone variant) | port | Same | no | references/techniques.md:78-79 |
| RDS-110 | review-design-doc | design | Section weight audit procedure (containers, exclude code blocks) | port | Same | no | references/techniques.md:81-93 |
| RDS-111 | review-design-doc | design | Surprise check | port | Same | no | references/techniques.md:95-96 |
| RDS-112 | review-design-doc | design | Persona walkthrough (7 personas) | port | Same | no | references/techniques.md:98-106 |
| RDS-113 | review-design-doc | design | Time-horizon walkthrough (day 1/100/1000/EOL) | port | Same | no | references/techniques.md:108-113 |
| RDS-114 | review-design-doc | design | Counterfactual constraints | port | Same | no | references/techniques.md:115-123 |
| RDS-115 | review-design-doc | design | Load-bearing assumption graph | port | Same | no | references/techniques.md:125-126 |
| RDS-116 | review-design-doc | design | Bus factor per component | port | Same | no | references/techniques.md:128-129 |
| RDS-117 | review-design-doc | design | Asymmetric risk audit | port | Same | no | references/techniques.md:131-132 |
| RDS-118 | review-design-doc | design | Decision quality vs outcome quality | port | Same | no | references/techniques.md:134-135 |
| RDS-119 | review-design-doc | design | "What if we are wrong about the problem itself?" | port | Same; findings route back to requirements (explicit upstream edit per design.md invalidation rule) | no | references/techniques.md:137-138 |
| RDS-120 | review-design-doc | design | Lens: Aristotle's four causes | port | Same | no | references/lenses.md:8-17 |
| RDS-121 | review-design-doc | design | Lens: Aristotle's mean between extremes | port | Same | no | references/lenses.md:19-29 |
| RDS-122 | review-design-doc | design | Lens: Confucian rectification of names | port | Same | no | references/lenses.md:31-40 |
| RDS-123 | review-design-doc | design | Lens: Nyaya pramanas | port | Same | no | references/lenses.md:42-50 |
| RDS-124 | review-design-doc | design | Lens: Jain anekantavada | port | Same | no | references/lenses.md:52-59 |
| RDS-125 | review-design-doc | design | Lens: Buddhist tetralemma | port | Same | no | references/lenses.md:61-70 |
| RDS-126 | review-design-doc | design | Lens: Pyrrhonian epoche | port | Same | no | references/lenses.md:72-80 |
| RDS-127 | review-design-doc | design | Lens: Hippocratic do-no-harm | port | Same | no | references/lenses.md:82-91 |
| RDS-128 | review-design-doc | cross | Ground rule: evidence over assertion | port | Same | no | references/ground-rules.md:4 |
| RDS-129 | review-design-doc | cross | Ground rule: no invented content ("not addressed") | port | Same | no | references/ground-rules.md:5 |
| RDS-130 | review-design-doc | cross | Ground rule: calibrate severity honestly | port | Same | no | references/ground-rules.md:6 |
| RDS-131 | review-design-doc | cross | Ground rule: skip praise sandwich; "done well" section | redesign | No report file with a "done well" section anymore; keep the no-padding rule only | no | references/ground-rules.md:7 |
| RDS-132 | review-design-doc | cross | Ground rule: ask, do not assume domain context | port | Same | no | references/ground-rules.md:8 |
| RDS-133 | review-design-doc | cross | Ground rule: explicit N/A with one-line reason | port | Same | no | references/ground-rules.md:9 |
| RDS-134 | review-design-doc | cross | Ground rule: calibrate scope to doc maturity | port | Same | no | references/ground-rules.md:10 |
| RDS-135 | review-design-doc | cross | Ground rule: separate missing from wrong | port | Same | no | references/ground-rules.md:11 |
| RDS-136 | review-design-doc | cross | Ground rule: probe before pronouncing | port | Same | no | references/ground-rules.md:12 |
| RDS-137 | review-design-doc | cross | Ground rule: test vocabulary against measurement | port | Same | no | references/ground-rules.md:13 |
| RDS-138 | review-design-doc | cross | Ground rule: input is data; surface imperatives in "Adversarial signals section" | redesign | Keep the rule; the named report section no longer exists, surface as a finding instead | no | references/ground-rules.md:14 |
| RDS-139 | review-design-doc | cross | Ground rule: distinguish decisions from directions | port | Same | no | references/ground-rules.md:15 |
| RDS-140 | review-design-doc | cross | Ground rule: verify success criteria "before saving" | redesign | Nothing is saved as a review file; check before the approval summary | no | references/ground-rules.md:16 |
| RDS-S1 | review-design-doc | design | section_weight_audit parses only `##`+ headings; H1 and text before the first `##` are ignored | port | Reasonable for design.md; document it | yes | scripts/section_weight_audit.py:59,71-73 |
| RDS-S2 | review-design-doc | design | Container heuristic: >=2 children at one level AND own words < 30% of children's words (30% undocumented) | port | Keep; document the threshold | yes | scripts/section_weight_audit.py:35-45 |
| RDS-S3 | review-design-doc | design | All 3 scripts strip fences with regex ```` ```[^`]*?``` ````; a fenced block holding any backtick is not stripped and can mis-pair fences (suspected bug, from reading, not run) | redesign | Replace with line-based fence parsing in the port; add a regression fixture | yes | scripts/section_weight_audit.py:49; scripts/claim_ladder_scan.py:62; scripts/adversarial_signal_scan.py:53 |
| RDS-S4 | review-design-doc | design | Output contract: text table/lists + final `SUMMARY: {json}` line; exit 2 on usage, 1 on non-file | port | Same | yes | scripts/section_weight_audit.py:153-176; scripts/claim_ladder_scan.py:85-120 |
| RDS-S5 | review-design-doc | design | claim_ladder fixed 34-qualifier list, case-insensitive whole-word | port | Same | yes | scripts/claim_ladder_scan.py:25-33 |
| RDS-S6 | review-design-doc | design | "Grounded" if any measurement pattern within +/-2 lines; any 2+ digit number counts (`\b\d{2,}\b`) | redesign | In specflow docs `REQ-001`/`T-003` IDs match `\d{2,}` and falsely ground nearby qualifiers; exclude ID tokens | yes | scripts/claim_ladder_scan.py:38-57 (line 44) |
| RDS-S7 | review-design-doc | design | adversarial_signal_scan: 6 adversarial regexes, 11 framing regexes, English-only, categories in SUMMARY | port | Same | yes | scripts/adversarial_signal_scan.py:26-48 |
| RDS-S8 | review-design-doc | design | Script docstrings hardcode "Called from: ~/.agents/skills/review-design-doc/SKILL.md" | redesign | Point at plugin-relative skill path | yes | scripts/section_weight_audit.py:10; scripts/claim_ladder_scan.py:15; scripts/adversarial_signal_scan.py:16 |
| RPB-01 | review-prd-backlog | tasks | Trigger: review PRD backlog before /run-autopilot | redesign | Becomes a cross-spec readiness review (pending specs in `.kiro/specs/`) before implementation; no autopilot | no | SKILL.md:3 |
| RPB-03 | review-prd-backlog | tasks | Argument: backlog dir, default `docs/dev/project-management/prds/backlog` | redesign | Target = specs not yet `complete` under `.kiro/specs/` plus `intake/new/`; prds/ tree forbidden | no | SKILL.md:4,29 |
| RPB-04 | review-prd-backlog | tasks | Purpose: two levels, each PRD executable + set leaves project in best shape | redesign | Same two levels over specs; "executable" means an agent on any host can resume and implement from disk | no | SKILL.md:10 |
| RPB-05 | review-prd-backlog | tasks | Pipeline position elicit -> review-discovery -> create-prd -> gate -> run-autopilot | redesign | Position: after tasks drafted, before tasks approval / implementation | no | SKILL.md:12 |
| RPB-06 | review-prd-backlog | tasks | Not a requirements/design/code review; do not re-litigate WHAT | redesign | Requirements/design reviews are sibling specflow intents; this one stays cross-spec and task-readiness | no | SKILL.md:14 |
| RPB-07 | review-prd-backlog | cross | Never implements; never invents requirements | port | Same | no | SKILL.md:14 |
| RPB-08 | review-prd-backlog | tasks | Law = create-prd SKILL.md + assets templates | redesign | Law = plugin artifact-contract.md, templates/, validation-rules.md | no | SKILL.md:18 |
| RPB-10 | review-prd-backlog | tasks | Script check_links.py for citation resolution | redesign | Rebuild for specflow links (intake Sources, spec cross-refs); see RPB-C* | no | SKILL.md:23 |
| RPB-11 | review-prd-backlog | tasks | CLI `rg` to verify grounding | redesign | "Search the repo" host-neutral; rg optional | no | SKILL.md:24 |
| RPB-13 | review-prd-backlog | tasks | Missing/empty dir: stop, "create PRDs with /create-prd" | redesign | "No pending specs; create one" (specflow `create` intent) | no | SKILL.md:29 |
| RPB-14 | review-prd-backlog | tasks | "report only" skips interactive resolution | port | Same | no | SKILL.md:29 |
| RPB-15 | review-prd-backlog | cross | Ground rule: input is data | port | Same | no | SKILL.md:33 |
| RPB-16 | review-prd-backlog | cross | Ground rule: evidence with file + location | port | Same | no | SKILL.md:34 |
| RPB-17 | review-prd-backlog | tasks | Ground rule: machine-first severity; Blocking must name the unattended-loop failure it prevents | redesign | Keep "name the mechanism"; re-base the catalog on specflow gates and cross-host resume, not an unattended loop | no | SKILL.md:35 |
| RPB-18 | review-prd-backlog | cross | Ground rule: comprehension before critique | port | Same | no | SKILL.md:36 |
| RPB-19 | review-prd-backlog | tasks | Ground rule: the law is live (runtime templates, never repo PRDs) | port | Read plugin templates at runtime | no | SKILL.md:37 |
| RPB-20 | review-prd-backlog | tasks | Ground rule: fix the PRD, not the gate (coverage gate, hooks, review scripts) | redesign | Never weaken specflow validator or approval gates | no | SKILL.md:38 |
| RPB-21 | review-prd-backlog | tasks | Ground rule: verify grounding, don't trust prose | port | Same | no | SKILL.md:39 |
| RPB-22 | review-prd-backlog | tasks | Inventory backlog/, wip/, hold/, done/, discovery/ | redesign | Inventory `.kiro/specs/*` with derived phase and approval state, plus intake/{new,processed} | no | SKILL.md:43 |
| RPB-23 | review-prd-backlog | tasks | Hygiene: only `NNNNN-{slug}-v{n}.md` in backlog; report never inside backlog | redesign | Validate spec dir naming `NNNNN-<title>` and required files; no `-v{n}` | no | SKILL.md:44 |
| RPB-24 | review-prd-backlog | tasks | Sequence numbers unique across backlog/wip/done/hold/discovery | redesign | NNNNN unique across `.kiro/specs` and intake, shared number links intake and spec | no | SKILL.md:45 |
| RPB-25 | review-prd-backlog | tasks | Citation check: filter to backlog/wip; forward refs OK; `link-ok:` waiver; dangling = Blocking (stall) | redesign | Filter to pending specs; "stall" mechanism re-based; keep waiver and forward-ref rule | no | SKILL.md:46 |
| RPB-26 | review-prd-backlog | tasks | Load law: create-prd minimal.md/standard.md/example_prd_rpg.md | redesign | Load specflow templates for requirements/design/tasks | no | SKILL.md:47 |
| RPB-27 | review-prd-backlog | tasks | Comprehension pass: backlog map (number, title, template, lines, subsystems, deps, frontmatter) + confusion notes | redesign | Map columns: number, title, profile, phase, approval status, subsystems, deps | no | SKILL.md:48 |
| RPB-29 | review-prd-backlog | tasks | Set lenses E-H across the whole set in one context | port | Same | no | SKILL.md:50 |
| RPB-32 | review-prd-backlog | tasks | Blocking mechanism: wrong-TDD lock-in (vague contract -> invented tests) | redesign | Still real when another agent implements from tasks.md alone; re-word without autopilot TDD phases | no | SKILL.md:52 |
| RPB-33 | review-prd-backlog | verification | Blocking mechanism: rework thrash (ambiguous AC until rework cap) | redesign | Re-base on VAL-002 verification disputes; no rework cap | no | SKILL.md:52 |
| RPB-38 | review-prd-backlog | tasks | Blocking mechanism: goal reversal | port | Same | no | SKILL.md:52 |
| RPB-39 | review-prd-backlog | cross | Non-blocking and Question severities | port | Same | no | SKILL.md:53-54 |
| RPB-40 | review-prd-backlog | tasks | Write report via Write tool to `docs/dev/project-management/audit-results/backlog-review-DATE.md` (GC contract) | redesign | Pick a specflow-owned report location; drop the buvis GC contract and tool naming | no | SKILL.md:55 |
| RPB-41 | review-prd-backlog | cross | Chat output: three sentences + verdict | port | Same | no | SKILL.md:55 |
| RPB-42 | review-prd-backlog | cross | Resolve interactively: Blocking -> RESHAPE -> Question -> Non-blocking; AskUserQuestion; batch | redesign | Host-neutral picker; immediate apply per header decision | no | SKILL.md:56 |
| RPB-43 | review-prd-backlog | cross | Apply pass: summary first, edits + reshapes, re-run lens A, update report, final verdict | redesign | Re-run = validator; reshapes per RPB-98..102 | no | SKILL.md:57 |
| RPB-44 | review-prd-backlog | tasks | Lens A: filename `NNNNN-{slug}-v{n}.md`, 5-digit | redesign | Spec dir naming rule | no | SKILL.md:63 |
| RPB-45 | review-prd-backlog | tasks | Lens A: infer template; headings present/ordered/worded; RPG four sections; template-fit flag | redesign | Check against specflow templates; fit = profile choice (WF-003.5-6) | no | SKILL.md:64 |
| RPB-46 | review-prd-backlog | tasks | Lens A: `#### Feature:` headings unique (coverage files key on them) | redesign | Becomes unique stable REQ/T IDs (VAL-001.2/4) | no | SKILL.md:65 |
| RPB-47 | review-prd-backlog | tasks | Lens A: every task line has `Acceptance:` clause | redesign | Each task references REQ IDs and states verification (ART-004.3-4) | no | SKILL.md:66 |
| RPB-49 | review-prd-backlog | tasks | Lens A: plain engineering prose, no narrative framing | port | Same | no | SKILL.md:68 |
| RPB-50 | review-prd-backlog | tasks | Lens A: no template stubs/TBD/???/to-do markers -> Blocking | port | Matches VAL-001.3 placeholders | no | SKILL.md:69 |
| RPB-51 | review-prd-backlog | tasks | Lens A: >~200 lines -> RESHAPE (create-prd split rule) | redesign | Size by subsystem span / task count; no create-prd rule | no | SKILL.md:70 |
| RPB-52 | review-prd-backlog | verification | Lens B: every criterion headlessly verifiable; "user confirms" = Blocking | redesign | Prefer command/test evidence, but VAL-002.1 allows developer-accepted exceptions, so manual checks are Non-blocking if recorded | no | SKILL.md:76 |
| RPB-54 | review-prd-backlog | tasks | Lens B: contracts exact and final (test author sees only task text) | port | Critical for cross-host handoff | no | SKILL.md:78 |
| RPB-55 | review-prd-backlog | verification | Lens B: no dependence on credentials/external accounts/unreachable services | redesign | Flag as verification risk, not an unattended hang | no | SKILL.md:79 |
| RPB-61 | review-prd-backlog | design | Lens C: functional <-> structural mapping closed (Capability/Module/tree) | redesign | Becomes REQ <-> design element traceability (ART-003.3) | no | SKILL.md:88 |
| RPB-62 | review-prd-backlog | tasks | Lens C: features <-> tasks closed both ways | redesign | REQ <-> task traceability (ART-004.3, VAL-001.4) | no | SKILL.md:89 |
| RPB-63 | review-prd-backlog | tasks | Lens C: dependency graph acyclic, matches phase order | redesign | Task dependency graph in tasks.md (ART-004.4) | no | SKILL.md:90 |
| RPB-64 | review-prd-backlog | cross | Lens C: one value per name across sections | port | Same | no | SKILL.md:91 |
| RPB-65 | review-prd-backlog | requirements | Lens C: AC trace to features; metrics are numbers | redesign | AC per REQ in EARS form | no | SKILL.md:92 |
| RPB-66 | review-prd-backlog | requirements | Lens C: crisp scope boundary; Nice-to-have phrased as mandate | port | Same against Scope/exclusions | no | SKILL.md:93 |
| RPB-67 | review-prd-backlog | tasks | Lens D: referenced files/symbols/flags exist now | port | Same | no | SKILL.md:99 |
| RPB-68 | review-prd-backlog | tasks | Lens D: structural tree matches repo layout | port | Same, against design.md | no | SKILL.md:100 |
| RPB-69 | review-prd-backlog | tasks | Lens D: not already implemented (done/ PRDs, git log, code) | redesign | Check `complete` specs + git log + code | no | SKILL.md:101 |
| RPB-70 | review-prd-backlog | tasks | Lens D: spot-check stated current-behavior assumptions | port | Same | no | SKILL.md:102 |
| RPB-71 | review-prd-backlog | tasks | Lens D: no overlap with wip/, no dependence on hold/ | redesign | Overlap with specs in `implementation` phase; no hold concept | no | SKILL.md:103 |
| RPB-72 | review-prd-backlog | tasks | Lens E: duplicate/overlapping scope | port | Across specs | no | SKILL.md:107 |
| RPB-73 | review-prd-backlog | tasks | Lens E: contradictory requirements across PRDs | port | Across specs | no | SKILL.md:108 |
| RPB-74 | review-prd-backlog | tasks | Lens E: same-file contention | port | Same | no | SKILL.md:109 |
| RPB-76 | review-prd-backlog | tasks | Lens E: cross-invalidation; remedy fix text / `catchup: force` / merge | redesign | Keep detection and text fix; drop `catchup: force` | no | SKILL.md:111 |
| RPB-77 | review-prd-backlog | cross | Lens E: terminology drift | port | Same | no | SKILL.md:112 |
| RPB-79 | review-prd-backlog | tasks | Lens F: too big (>200 lines, >1 subsystem, >3 phases, >150K task); one split then hold/ | redesign | Keep subsystem/phase signals; drop 150K and hold/; split into new specs | no | SKILL.md:118 |
| RPB-80 | review-prd-backlog | tasks | Lens F: too small -> merge into same-subsystem neighbor; never merge unrelated | redesign | Recommend quick profile first; merge only with explicit migration | no | SKILL.md:119 |
| RPB-81 | review-prd-backlog | tasks | Lens F: mixed concerns -> split | port | Same | no | SKILL.md:120 |
| RPB-83 | review-prd-backlog | tasks | Lens G: producer/consumer holes (vs lower-numbered PRDs) | redesign | Check across all specs regardless of number | no | SKILL.md:125 |
| RPB-84 | review-prd-backlog | tasks | Lens G: missing enablers | port | Same | no | SKILL.md:126 |
| RPB-85 | review-prd-backlog | tasks | Lens G: half-migrations | port | Same | no | SKILL.md:127 |
| RPB-86 | review-prd-backlog | tasks | Lens G: fix without regression-test requirement | port | Same (bugfix specs) | no | SKILL.md:128 |
| RPB-87 | review-prd-backlog | tasks | Lens G: cleanup debt | port | Same | no | SKILL.md:129 |
| RPB-88 | review-prd-backlog | intake | Lens G: strategic gaps -> note + recommend /assess-evolution | redesign | Note gap, suggest a new intake item; no assess-evolution | no | SKILL.md:130 |
| RPB-89 | review-prd-backlog | tasks | Lens H: goal sources README, meta/project-capsule.md, CLAUDE.md, git log, done/ | redesign | README, AGENTS.md or host steering, git log, complete specs; project-capsule is buvis-only | no | SKILL.md:134 |
| RPB-90 | review-prd-backlog | tasks | Lens H: goal underminers incl. violating standing rules (hook language policy, branch naming, changelog) | redesign | Generic "project rules" from AGENTS.md/steering; no buvis hooks | no | SKILL.md:136 |
| RPB-91 | review-prd-backlog | requirements | Lens H: traceability to source discovery doc; dropped must-have = Blocking | redesign | Trace requirements.md to its intake original via `Sources` line | no | SKILL.md:137 |
| RPB-92 | review-prd-backlog | tasks | Lens H: end-state simulation | port | Same | no | SKILL.md:138 |
| RPB-93 | review-prd-backlog | tasks | Per-PRD verdicts READY / FIX / RESHAPE / HOLD | redesign | HOLD has no prds/hold dir; express as "not ready, reason" in report; statuses stay missing/draft/approved/stale | no | SKILL.md:144-147 |
| RPB-94 | review-prd-backlog | tasks | Set verdict GO/NO-GO; waiver "GO (user waived: ...)"; never soften NO-GO | port | Same | no | SKILL.md:149 |
| RPB-95 | review-prd-backlog | cross | Finding card (PRD, Lens A-H, severity, location, 3 sentences, impact, 3 options) | redesign | Field `PRD` -> `Spec`; lens list trimmed | no | SKILL.md:153-168 |
| RPB-96 | review-prd-backlog | cross | AskUserQuestion with same 3 options, `(Recommended)` on 1 | redesign | Host-neutral numbered question | no | SKILL.md:170 |
| RPB-97 | review-prd-backlog | tasks | RESHAPE proposals walked as findings (merge / keep + `catchup: force` / hold) | redesign | Options re-based: merge specs / keep separate + cross-ref / split | no | SKILL.md:170 |
| RPB-99 | review-prd-backlog | tasks | Reshape: merge into lowest number; absorbed originals to prds/hold | redesign | Merge specs with explicit approval (SEC-002.1, .4); no hold dir | no | SKILL.md:175 |
| RPB-100 | review-prd-backlog | tasks | Reshape: split, part 1 keeps number, parts get fresh tail numbers | redesign | New NNNNN specs; each links to the shared intake item | no | SKILL.md:176 |
| RPB-102 | review-prd-backlog | tasks | Reshape: always mv, never cp; never touch wip/done; re-run lens A | redesign | Never touch specs in implementation/complete; destructive moves need approval (SEC-002.4); re-run validator | no | SKILL.md:178 |
| RPB-103 | review-prd-backlog | tasks | Report format (Verdict, Map, Findings, Reshapes, Gaps, End state, Frontmatter tuning, Decisions applied) | redesign | Drop Frontmatter tuning section; map columns per RPB-27 | no | SKILL.md:182-208 |
| RPB-104 | review-prd-backlog | cross | Success: surprise test across all eight lenses | port | Same (lens count adjusted) | no | SKILL.md:212 |
| RPB-105 | review-prd-backlog | cross | Success: actionability (every Blocking applied or waived) | port | Same | no | SKILL.md:213 |
| RPB-106 | review-prd-backlog | cross | Success: gate honesty (skipped lens, unverified claim, subagent failure named) | port | Same; subagent clause moot | no | SKILL.md:214 |
| RPB-C1 | review-prd-backlog | tasks | check_links scans ALL `docs/dev/project-management/**/*.md`, not only backlog; filtering left to the agent | redesign | Scan `.kiro/specs/**` + intake; filter in code, not prose | yes | scripts/check_links.py:105-107 |
| RPB-C4 | review-prd-backlog | tasks | Five-digit citations resolved against prds/** (incl hold) and discovery/** | redesign | Resolve against `.kiro/specs/` and `intake/{new,processed}/` | yes | scripts/check_links.py:54-63 |
| RPB-C5 | review-prd-backlog | tasks | Placeholder skip (`* ? < > { } $ ... NNNNN XXXX YYYY`); trailing punctuation strip | port | Same | yes | scripts/check_links.py:30,85-86 |
| RPB-C7 | review-prd-backlog | tasks | Citation regex lookbehind skips digits after digit, `/`, `.`, `-` | port | Same | yes | scripts/check_links.py:26 |
| RPB-C8 | review-prd-backlog | tasks | Exit 0 clean / 1 findings or scan errors; `--json` {findings, scan_errors}; unreadable file = scan error | port | Same | yes | scripts/check_links.py:117-136 |
| RPB-C9 | review-prd-backlog | tasks | `resolve_path` memoized with functools.cache | port | Perf detail | yes | scripts/check_links.py:66 |
| RPB-C10 | review-prd-backlog | tasks | Tests use pytest and a `deny_access` fixture not defined in the skill dir (external conftest) | redesign | Target repo tests with stdlib unittest (AGENTS.md); fixture must be local | yes | scripts/test_check_links.py:7,102 |

### Walked drop candidates (final classification per Drop Rulings)

| id | source skill | phase | row | classification | reason | code-only | evidence |
|---|---|---|---|---|---|---|---|
| ELI-10 | elicit-requirements | intake | Pattern-scan targets `~/.agents/skills/` for skills and `~/.claude/hooks/` for hooks | drop | Personal buvis paths that do not exist on other machines or hosts | no | E/SKILL.md:55 "scan `~/.agents/skills/`... scan `~/.claude/hooks/`" |
| ELI-28 | elicit-requirements | requirements | Produces a separate discovery document as an intermediate artifact before the PRD | drop | specflow has only three canonical artifacts. Intake goes straight to requirements.md, which replaces both the discovery doc and the PRD | no | REQ ART-001.2 (requirements.md:100); DEC:16-19; E/SKILL.md:95 `discovery/{sequence}-{feature-slug}.md` |
| ELI-35 | elicit-requirements | intake | Pipeline and dependency pointers to review-discovery-doc, create-prd, autopilot:plan-tasks, autopilot:run-autopilot | drop | Personal skill and autopilot chain. specflow folds these into its own phases and must not depend on autopilot | no | E/SKILL.md:11,17-20 "Plugin skills (`autopilot` plugin)" |
| ELI-57 | elicit-requirements | requirements | Q6 Priority: "Next autopilot batch" / no rush / blocking; informs "ordering in backlog" | redesign | Tied to autopilot batches and the PRD backlog, neither of which exists in specflow (ruled redesign in walkthrough; see Drop Rulings) | no | E/references/question-bank.md:59-67 "a) Next autopilot batch" |
| PRD-02 | create-prd | requirements | RPG = Repository Planning Graph. Never add role-play framing. Literal headings (`#### Feature:`) are parsed by plan-tasks and the review coverage gate | drop | The heading contract serves autopilot parsers. specflow uses Kiro headings and REQ/T IDs checked by its own validator | no | P/SKILL.md:10 "downstream tooling (`/autopilot:plan-tasks`, the review coverage gate) parses the literal section headings" |
| PRD-03 | create-prd | requirements | Dependency note: the autopilot plugin consumes the PRD (plan-tasks, run-autopilot Phase 0, design-solution) | drop | specflow must not depend on autopilot hand-off | no | P/SKILL.md:14-19 |
| PRD-19 | create-prd | requirements | Frontmatter `catchup: run/skip/force` | drop | Controls autopilot Phase 1 | no | P/SKILL.md:92 |
| PRD-20 | create-prd | requirements | Frontmatter `rework_cap` | drop | Controls the autopilot review-rework loop | no | P/SKILL.md:93 |
| PRD-21 | create-prd | requirements | Frontmatter `design: run/skip` | drop | specflow always produces design.md, even on quick (WF-003.4) | no | P/SKILL.md:94; REQ WF-003.4 |
| PRD-22 | create-prd | requirements | Frontmatter `design_gate: user` | drop | specflow always gates design approval (WF-002); nothing to opt into | no | P/SKILL.md:95 |
| PRD-23 | create-prd | requirements | Frontmatter `doubt_reviewer: codex/fable` | drop | Picks autopilot reviewers backed by Claude/codex CLIs | no | P/SKILL.md:96 |
| PRD-24 | create-prd | requirements | Frontmatter `consensus_engine` | drop | autopilot review engine setting | no | P/SKILL.md:97 |
| PRD-25 | create-prd | requirements | Frontmatter `default_model` floor (haiku/sonnet/opus) | drop | Claude model-tier routing; specflow is host-neutral | no | P/SKILL.md:98 |
| PRD-26 | create-prd | requirements | Frontmatter `model_tier_rationale` | drop | Only means something alongside PRD-25 | no | P/SKILL.md:99 |
| PRD-27 | create-prd | requirements | An invalid frontmatter value falls back to the default with a warning | drop | Describes the autopilot parser | no | P/SKILL.md:116 |
| PRD-31 | create-prd | requirements | Model-tier gate: escalator table, then opus/sonnet/omit | redesign | Claude model-tier routing for autopilot plan-tasks (ruled redesign in walkthrough; see Drop Rulings) | no | P/SKILL.md:134-160 |
| PRD-33 | create-prd | requirements | No comment on the `default_model:` line (the Phase-0 parser is not PyYAML) | drop | Quirk of the autopilot parser | no | P/SKILL.md:174 |
| PRD-34 | create-prd | requirements | Saves to `prds/backlog/`, creating it if missing | drop | Banned buvis path; specflow writes `.kiro/specs/NNNNN-*/requirements.md` | no | P/SKILL.md:182 `mkdir -p docs/dev/project-management/prds/backlog` |
| PRD-38 | create-prd | requirements | `-vN` revision: edit backlog in place, `-v2` to keep a superseded spec, `-v2` under the same number for re-work of a done PRD | drop | specflow edits artifacts in place under hash-bound approvals, marks them stale on change, and never renames them (ART-001.4) | no | P/SKILL.md:216-224; DES:336-372 |
| PRD-40 | create-prd | requirements | Directory layout `backlog/ wip/ hold/ done/` | drop | Banned buvis PRD lifecycle tree | no | P/SKILL.md:228-234 |
| PRD-41 | create-prd | complete | Lifecycle by moving files: create, start, park, complete | drop | specflow derives the phase from state and never moves the spec (WF-001.2, ART-001.4) | no | P/SKILL.md:236-241; DES:325 |
| PRD-42 | create-prd | intake | A parked PRD keeps its number, so the scan must include `hold/` | drop | No hold/ folder; the specs dir holds every spec in place | no | P/SKILL.md:243 |
| PRD-48 | create-prd | requirements | RPG "Recommended tools" (Claude Code, Cursor, Gemini CLI, Codex) | drop | Vendor advice, irrelevant inside a host-neutral plugin | no | P/assets/example_prd_rpg.md:21-33 |
| PRD-54 | create-prd | tasks | Task Master integration: `parse-prd`, `expand`, `--research`, and the Surgical Test Generator guidelines | drop | Third-party tool contract; specflow writes tasks.md itself | no | P/assets/example_prd_rpg.md:396-397,468-511 |
| SPK-04 | spike | graduate | Names autopilot plugin (`plan-tasks`, `work`) as downstream pipeline; without it "you implement it by hand" | drop | Autopilot hand-off is a buvis-personal dependency that specflow must not carry; specflow's own tasks/implementation phases replace it (see SPK-29) | no | SKILL.md:15-17 "Plugin skills (`autopilot` plugin) ... `autopilot:plan-tasks`, `autopilot:work`" |
| SPK-07 | spike | rough spec | Use the Write tool, never shell redirects, for SPEC.md | drop | Claude Code harness/permission convention (buvis rules/tools.md), not workflow behavior; tool names differ per host | no | SKILL.md:23 "(Write tool, never shell redirects)" |
| RDD-02 | review-discovery-doc | n/a | Compatibility: needs the sibling review-design-doc skill for its shared core | drop | specflow has one runtime skill, so there is no sibling to depend on; the shared core becomes a local reference file (RDD-08) | no | SKILL.md:5 "requires ... the sibling review-design-doc skill" |
| RDD-09 | review-discovery-doc | n/a | Dependency: harness tool `AskUserQuestion` | drop | Claude-only tool, forbidden in target; the picker itself is redesigned in RDD-53 | no | SKILL.md:21 "Harness tool: `AskUserQuestion`" |
| RDD-20 | review-discovery-doc | n/a | Completeness (comprehensive): Approach section with chosen option and rejected alternatives | drop | In specflow alternatives and rejections belong to design.md (ART-003.4) and are checked by the design review (RDS-58); duplicating them in requirements review re-litigates the HOW | no | references/lenses.md:19 "Approach section with chosen option *and* rejected alternatives" |
| RDS-04 | review-design-doc | n/a | Session writes a resolution log to disk at the end | drop | Stale: contradicted by the same file's per-finding edits and the example's format note | no | SKILL.md:10 "writes a resolution log to disk at the end" vs SKILL.md:90; examples/self-review-v5.md:3 |
| RDS-05 | review-design-doc | n/a | "Replaces the older one-shot review-document approach" | drop | History, not behavior | no | SKILL.md:12 |
| RDS-29 | review-design-doc | n/a | Maintenance: regenerate examples/self-review-vN.md by self-review when skill changes | drop | Maintainer loop about the skill itself, not runtime behavior; belongs in repo evals (decision: one scenario eval per rule) | no | SKILL.md:96 "regenerate `examples/self-review-vN.md` by applying this skill to itself" |
| RDS-30 | review-design-doc | n/a | Convergence criterion for stopping self-iteration | drop | Same: skill-authoring process, not runtime | no | SKILL.md:98-104 |
| RDS-32 | review-design-doc | n/a | Example self-review-v5 (old resolution-log format) | drop | Self-declared stale artifact shape | no | examples/self-review-v5.md:3 "This example predates the direct-edit workflow" |
| RPB-02 | review-prd-backlog | n/a | Compatibility: sub-agents for grounding; full budget/tier coverage needs autopilot plugin | drop | Both are forbidden deps (Agent subagents, autopilot) | no | SKILL.md:5 "full budget/tier coverage needs the autopilot plugin" |
| RPB-09 | review-prd-backlog | n/a | Dependency on autopilot:plan-tasks budget/tier rules (steps 4-4.7); skip if plugin absent | drop | autopilot is a forbidden dependency; task sizing comes from ART-004.5 | no | SKILL.md:19-22 |
| RPB-12 | review-prd-backlog | n/a | Optional: recommend assess-evolution in report | drop | Personal skill not shipped in the plugin | no | SKILL.md:25 "Optional: `assess-evolution`" |
| RPB-28 | review-prd-backlog | n/a | >8 PRDs: dispatch lens D per PRD to parallel subagents | redesign | Agent subagents are Claude-only; run grounding inline (ruled redesign in walkthrough; see Drop Rulings) | no | SKILL.md:49 "dispatch lens D (grounding) per PRD to parallel subagents" |
| RPB-30 | review-prd-backlog | n/a | Blocking mechanism: selection break (Phase 0 picks wrong file) | drop | No autopilot Phase 0 selection in specflow | no | SKILL.md:52 "selection break (Phase 0 picks or moves the wrong file)" |
| RPB-31 | review-prd-backlog | n/a | Blocking mechanism: stall (task cannot split under 150K budget; parked in hold/) | drop | autopilot plan-tasks budget and hold/ dir | no | SKILL.md:52 "under the 150K budget; PRD parked in `hold/`" |
| RPB-34 | review-prd-backlog | n/a | Blocking mechanism: coverage-gate block (Feature headings keyed verbatim) | drop | autopilot review coverage files; specflow keys on REQ IDs | no | SKILL.md:52 "coverage-gate block (feature headings that reviewers cannot key verbatim)" |
| RPB-35 | review-prd-backlog | n/a | Blocking mechanism: unattended hang (needs approval/credential/human mid-loop) | drop | specflow is attended by design; gates require an explicit developer answer (WF-002.2) | no | SKILL.md:52 "unattended hang ... mid-loop" |
| RPB-36 | review-prd-backlog | n/a | Blocking mechanism: order break (depends on higher-numbered PRD) | drop | specflow does not drain specs in number order; cross-spec deps handled by RPB-83 | no | SKILL.md:52 "order break (dependency on a higher-numbered PRD)" |
| RPB-37 | review-prd-backlog | n/a | Blocking mechanism: loop self-harm (edits machinery running the batch) | drop | No batch loop to harm | no | SKILL.md:52 "loop self-harm (PRD edits the machinery executing the batch)" |
| RPB-48 | review-prd-backlog | n/a | Lens A: frontmatter fields catchup/rework_cap/design/design_gate/doubt_reviewer/consensus_engine/default_model; silent defaults | drop | autopilot Phase 0 knobs; specflow state lives in `.specflow.json` | no | SKILL.md:67 "parsed by run-autopilot Phase 0" |
| RPB-53 | review-prd-backlog | n/a | Lens B: unattended feasibility sweep; create-prd Unattended rule | redesign | specflow has a developer at every gate; no unattended phase (ruled redesign in walkthrough; see Drop Rulings) | no | SKILL.md:77 "create-prd's Unattended rule" |
| RPB-56 | review-prd-backlog | n/a | Lens B: unattended permission profile (chmod +x, force-push, warden ask) | drop | buvis warden / permission profile | no | SKILL.md:80 "A warden `ask` mid-loop has hung a batch" |
| RPB-57 | review-prd-backlog | n/a | Lens B: resource sanity (/work caps at 2 parallel; 48GB cargo incident) | drop | autopilot /work harness limits | no | SKILL.md:81 "`/work` caps at 2 parallel" |
| RPB-58 | review-prd-backlog | n/a | Lens B: self-referential hazard (edits autopilot/hook machinery) -> resequence last or HOLD | drop | No autopilot/hook machinery in target | no | SKILL.md:82 |
| RPB-59 | review-prd-backlog | n/a | Lens B: PRD prose tax against 150K per-task cap | redesign | plan-tasks context budget (ruled redesign in walkthrough; see Drop Rulings) | no | SKILL.md:83 "against the 150K cap" |
| RPB-60 | review-prd-backlog | n/a | Lens B: frontmatter tuning suggestions (catchup: skip, rework_cap: 5, design_gate, default_model: opus) | drop | autopilot knobs | no | SKILL.md:84 |
| RPB-75 | review-prd-backlog | n/a | Lens E: order breaks (autopilot drains ascending; remedy renumber) | drop | No ascending drain; renumbering breaks shared NNNNN links (design.md:219 rename needs migration) | no | SKILL.md:110 "autopilot drains ascending by sequence number" |
| RPB-78 | review-prd-backlog | n/a | Lens F: fixed per-PRD ceremony (catchup, design, planning, blind/doubt review, state churn) | redesign | autopilot ceremony cost model (ruled redesign in walkthrough; see Drop Rulings) | no | SKILL.md:116 |
| RPB-82 | review-prd-backlog | n/a | Lens F: adjacency (sequence same-subsystem PRDs for warm batch cache; renumber) | drop | Batch cache and numeric drain are autopilot-only | no | SKILL.md:121 "warm batch cache" |
| RPB-98 | review-prd-backlog | n/a | Reshape: renumber via `mv` in backlog/ | drop | Spec dir names are fixed once and share NNNNN with intake; rename needs explicit migration | no | SKILL.md:174 "Renumber: `mv` within `backlog/`"; target design.md:219 |
| RPB-101 | review-prd-backlog | n/a | Reshape: HOLD = `mv` to prds/hold, reason in report | drop | `prds/{backlog,wip,hold,done}` is a forbidden buvis convention | no | SKILL.md:177 "`mv` to `docs/dev/project-management/prds/hold/`" |
| RPB-C2 | review-prd-backlog | n/a | check_links scans Claude project auto-memory dir and resolves `[[memory]]` links | redesign | Claude-only memory store; WF-004.6 forbids needing host memory (ruled redesign in walkthrough; see Drop Rulings) | yes | scripts/check_links.py:33-34,93-95 |
| RPB-C3 | review-prd-backlog | n/a | Path refs matched for `~/.claude/` and `/Users/` absolute paths | redesign | Claude home and absolute machine paths are out of scope for portable specs (ruled redesign in walkthrough; see Drop Rulings) | yes | scripts/check_links.py:25 |
| RPB-C6 | review-prd-backlog | n/a | Skips `.trash` dirs | struck | `.trash` is the buvis GC convention, absent in target (INVALID: behavior does not exist; see Drop Rulings) | yes | scripts/check_links.py:107 |

Classification legend:

- **port** - ports unchanged.
- **redesign** - ports with modification; the `reason` column explains what changes and why.
- **drop** - does not port; the `reason` column explains why it stays behind.

`code-only` marks a row discovered only in code, absent from docs/SKILL.md/README, and therefore not yet judged by anyone.

## Drop Rulings

### ELI-28 - separate discovery document

- **Evidence presented**: elicit SKILL.md:95 writes `discovery/{seq}-{slug}.md`; specflow ART-001.2 and STATE-001.3 allow only the three artifacts plus `.specflow.json`, with no conversation content. Without a replacement, the Q&A log (why each requirement is shaped as it is) has no home.
- **Ruling**: drop, with the Q&A log kept as `qa-log.md` inside the intake item (moves to `processed/` with it). Every spec gets an intake item: a chat idea is first saved verbatim as `intake/new/NNNNN-<title>/idea.md` (this also claims the number, per ELI-01). Kiro-native specs with no intake item get `intake/processed/<spec-folder>/qa-log.md` created on the first Q&A.

### RDD-20 - Approach section check in requirements review

- **Evidence presented**: lenses.md:19 requires an Approach section with rejected alternatives; specflow puts alternatives in design.md (ART-003.4), checked by the design review (RDS-58). Risk: a solution written as a requirement gets approved before alternatives are weighed.
- **Ruling**: drop, and add a "no HOW" check: the requirements review flags requirements that name a solution (technology, mechanism) instead of needed behavior. Legitimate constraints may be kept when stated as constraints.

### RPB-C3 - `~/.claude/` and `/Users/` path matching (code-only)

- **Evidence presented**: check_links.py:25 resolves home and absolute paths; STATE-001.3 bans absolute paths only in `.specflow.json`, not in the Markdown artifacts, so machine-specific paths would slip into specs.
- **Ruling**: redesign, not drop. Do not resolve absolute or home paths; flag them in artifacts as an advisory portability warning ("use a repo-relative path"), with room for an allow list for legitimate system paths.

### RPB-36 - order break (dependency on a higher-numbered PRD)

- **Evidence presented**: SKILL.md:52; specflow has no numeric queue (WF-001.2). Cross-spec producer/consumer holes stay covered by RPB-83 (redesign, all specs regardless of number).
- **Ruling**: drop.

### PRD-38 - `-vN` revision scheme

- **Evidence presented**: create-prd SKILL.md:216-224; specflow's hash/stale model (design 336-372) covers edits to open specs. Gap: re-opening a complete spec in place erases what shipped.
- **Ruling**: drop. Re-working a complete spec creates a new NNNNN spec whose requirements.md carries `Supersedes: NNNNN`; the old spec stays complete and untouched.

### PRD-41 - lifecycle by moving files

- **Evidence presented**: create-prd SKILL.md:236-241; specflow computes phase (WF-001.2) and never moves specs (ART-001.4). Create/start/complete are covered; park has no equivalent, so paused and dead specs look active.
- **Ruling**: drop, and add an optional recorded hold status in `.specflow.json` (`on_hold` or `abandoned`, with reason and date), set and cleared only on explicit developer instruction. Needs a state-schema version bump and an eval.

### RPB-35 - unattended hang blocker

- **Evidence presented**: SKILL.md:52; specflow gates always need an explicit developer answer (WF-002.2). Matters only if a headless runner is later pointed at `.kiro/specs`.
- **Ruling**: drop. If autopilot is repointed, the check stays on autopilot's side.

### RPB-28 - parallel subagent grounding for >8 PRDs

- **Evidence presented**: SKILL.md:49; subagents are Claude-only, no portable equivalent. Inline-only grounding is slower and degrades late-run review quality on large spec sets.
- **Ruling**: redesign, not drop. Host-neutral rule: if the host can run isolated sub-tasks, ground each spec in its own; otherwise ground sequentially, summarizing each spec before the next. Parity evals cover both paths.

### RDS-29 - regenerate self-review example on skill change

- **Evidence presented**: SKILL.md:96; example already self-declared stale (self-review-v5.md:3). Maintainer loop, not runtime behavior; PKG-002 bars maintainer-only content from the package.
- **Ruling**: drop. Repo-side per-rule scenario evals are the regression net.

### RDS-30 - self-iteration convergence criterion

- **Evidence presented**: SKILL.md:98-104 - stop self-iterating at 0 cardinal sins, 0 blocking issues, <5 non-blocking concerns, and at least one real (non-self) application since the last self-review ("regression-by-polish"). Governs only the RDS-29 loop, now dropped. (The packet first paraphrased this incorrectly; corrected before recording.)
- **Ruling**: drop.

### RDS-04 - end-of-session resolution log

- **Evidence presented**: SKILL.md:10 promises a log; SKILL.md:90 and self-review-v5.md:3 say edits land per finding with no standalone file. Deferred/accepted findings would leave no trace and get re-raised.
- **Ruling**: drop the separate log; append review minutes (one line per finding: decision and status) to the intake item's `qa-log.md` under a review heading.

### RDS-05 - "replaces the older one-shot approach"

- **Evidence presented**: SKILL.md:12; history only. The "findings drive a workflow, not a report" intent is covered by ported walkthrough rows.
- **Ruling**: drop.

### RDS-32 - self-review-v5 example

- **Evidence presented**: self-review-v5.md:3 declares its format outdated (separate log file) while its reasoning stays illustrative.
- **Ruling**: drop. Finding format ports through the approved finding-card rows.

### RDD-02 - dependency on sibling review-design-doc

- **Evidence presented**: SKILL.md:5, :16 read the shared core from an absolute `~/.agents` path. The core itself ports as one local reference (RDD-08).
- **Ruling**: drop.
- **Note surfaced**: SKILL.md:10 records batch-apply as "by user preference"; the approved table uses per-choice edits everywhere. User told; flip on request.

### RDD-09 - AskUserQuestion dependency

- **Evidence presented**: SKILL.md:21. Behavior ports via RDD-53 (host picker if present, numbered plain text otherwise). The claim that Kiro and Codex lack an identical tool was not verified.
- **Ruling**: drop.

### ELI-10 - pattern scan of `~/.agents/skills/` and `~/.claude/hooks/`

- **Evidence presented**: elicit SKILL.md:55; personal out-of-repo paths. The general repo scan ports.
- **Ruling**: drop.

### ELI-35 - pipeline and dependency pointers

- **Evidence presented**: elicit SKILL.md:11, :17-20; specflow gates name the next phase (WF-002.1).
- **Ruling**: drop.

### ELI-57 - Q6 Priority question

- **Evidence presented**: question-bank.md:59-67 ("Next autopilot batch", "ordering in backlog"). The "blocking other work" signal is general and useful to RPB-83 and the hold/status view.
- **Ruling**: redesign, not drop. One optional standard-depth question, "Is this blocking other work? If so, what?", recorded as a `Blocks:` line in requirements.md next to Sources/Supersedes.

### SPK-04 - autopilot as downstream pipeline

- **Evidence presented**: spike SKILL.md:15-17; graduated spikes enter specflow's own phases (SPK-29). Same call as ELI-35.
- **Ruling**: drop.

### SPK-07 - "Write tool, never shell redirects"

- **Evidence presented**: spike SKILL.md:23; Claude harness hygiene (aegis enforces it locally regardless).
- **Ruling**: drop.

### RPB-02 - compatibility note (sub-agents, autopilot)

- **Evidence presented**: SKILL.md:5. Sub-agent half ruled in RPB-28; autopilot half is RPB-09.
- **Ruling**: drop.

### RPB-09 - dependency on autopilot:plan-tasks budget/tier rules

- **Evidence presented**: SKILL.md:19-22, :47; specflow sizes by ART-004.5 and has no tiers. (Packet misattributed "top measured waste driver" to oversize; SKILL.md:10 says it of review-rework cycles. Corrected before recording.)
- **Ruling**: drop. The cross-spec review checks task size against specflow's own tasks-reference sizing guidance, which Plan B settles.

### RPB-12 - recommend `/assess-evolution`

- **Evidence presented**: SKILL.md:25, :130; personal skill not shipped.
- **Ruling**: drop the skill name; strategic gaps are reported with "consider a new intake item" as the follow-up.

### RPB-30 - selection break blocker

- **Evidence presented**: SKILL.md:44, :52; specflow has no filename-sorted picker. Path hygiene is covered by VAL-001.1.
- **Ruling**: drop.

### RPB-31 - stall blocker (150K budget, hold/)

- **Evidence presented**: SKILL.md:52, :118. Oversize stays covered by the RPB-09 sizing check.
- **Ruling**: drop.

### RPB-34 - coverage-gate block (heading-keyed)

- **Evidence presented**: SKILL.md:52, :65; specflow keys on REQ/task IDs (ART-002.3, VAL-001.2/.4).
- **Ruling**: drop.

### RPB-37 - loop self-harm blocker

- **Evidence presented**: SKILL.md:52, :82; no batch loop. Consistent with RPB-35 (headless checks stay with the runner).
- **Ruling**: drop.

### RPB-58 - self-referential hazard (lens B)

- **Evidence presented**: SKILL.md:82; same check as RPB-37 from the lens side. Merged as a duplicate.
- **Ruling**: drop (follows RPB-37).

### RPB-75 - order breaks, remedy renumber (lens E)

- **Evidence presented**: SKILL.md:110; same check as RPB-36. Merged as a duplicate.
- **Ruling**: drop (follows RPB-36).

### RPB-53 - unattended feasibility sweep

- **Evidence presented**: SKILL.md:77. The unattended framing is autopilot-only, but "decision or Open Question deferred to implementation" is a defect in any spec; ART-002.5 makes questions explicit without blocking approval.
- **Ruling**: redesign, not drop. Design and tasks approval is refused while upstream artifacts carry unresolved questions or "decide later" markers, unless the developer explicitly accepts a named exception (recorded per VAL-002.5). The validator scans for the markers; the gate enforces it.

### RPB-56 - unattended permission profile

- **Evidence presented**: SKILL.md:80; warden is local tooling, and attended runs answer prompts live.
- **Ruling**: drop.

### RPB-57 - resource sanity (/work cap)

- **Evidence presented**: SKILL.md:81; the cap is autopilot's harness limit. Heavy-resource tasks are rare and visible to an attended developer.
- **Ruling**: drop.

### RPB-59 - PRD prose tax (150K cap)

- **Evidence presented**: SKILL.md:83; cap math is autopilot's, but verbose artifacts cost context on every implementation step on any host.
- **Ruling**: redesign, not drop. Non-blocking review finding across all three artifacts: trim restatement, never cut contracts or acceptance criteria.

### PRD-19, PRD-20, PRD-21, PRD-22, PRD-23, PRD-24, PRD-25, PRD-26, PRD-27, PRD-33, RPB-48, RPB-60 - autopilot frontmatter (merged)

- **Evidence presented**: create-prd SKILL.md:88-116, :174; review-prd-backlog SKILL.md:67, :84. Every field controls an autopilot phase, reviewer, or model tier. `design: skip` is covered by the quick profile (WF-003.4); `design_gate: user` is always on (WF-002). Merged as overlapping findings; the user could pull rows out and did not.
- **Ruling**: drop all twelve.

### PRD-31 - model-tier gate (escalator table)

- **Evidence presented**: create-prd SKILL.md:134-160. Model tiers are Claude-specific, but the escalators are a risk taxonomy wider than WF-003.6's standard-profile triggers.
- **Ruling**: redesign, not drop. Drop model tiers; add concurrency/timing, equivalence obligation, invented algorithm or predicate, and destructive blast radius to WF-003.6's triggers that force the standard profile (developer override per WF-003.5 still applies).

### PRD-34, PRD-40, PRD-42, RPB-101, PRD-03 - PRD folder tree and autopilot consumer note (merged)

- **Evidence presented**: create-prd SKILL.md:182, :228-234, :243, :14-19; review-prd-backlog SKILL.md:177 (create-prd line refs beyond :179 taken from the inventory, not re-read). All implied by ART-001.4, the PRD-41 hold flag, the approved numbering scan, and the ELI-35 ruling. Numbers are never reused because specs never move.
- **Ruling**: drop all five.

### PRD-02 - RPG literal heading contract

- **Evidence presented**: create-prd SKILL.md:10; headings serve autopilot parsers. Plain-prose rule ports as RPB-49; the WHAT/WHERE/dependency split maps onto the three artifacts via approved redesigns.
- **Ruling**: drop.

### PRD-48, PRD-54 - Task Master template material (merged)

- **Evidence presented**: example_prd_rpg.md:21-33, :396-397, :468-511; vendor advice and a third-party parser contract. Useful tips are covered by approved task rows.
- **Ruling**: drop both. The template's Risks shape (:428-451) is noted against the queued Risks item.

### RPB-78 - fixed per-PRD ceremony cost model

- **Evidence presented**: SKILL.md:116; autopilot phase list, but it is the stated reason for the too-big/too-small rules (RPB-79/80), which port.
- **Ruling**: redesign, not drop. Restate with specflow's overhead: each spec pays three artifacts and three approval gates; too small and gates dominate (prefer quick profile or merge), too big and review quality drops.

### RPB-82, RPB-98 - adjacency ordering and renumbering (merged)

- **Evidence presented**: SKILL.md:121, :174; both serve autopilot's numeric drain or batch cache. NNNNN is a permanent cross-artifact identity (design.md:219 rename-needs-migration ref taken from the inventory, not re-read).
- **Ruling**: drop both.

### RPB-C6 - skips `.trash` dirs (code-only) - INVALID ROW

- **Evidence presented**: none holds. check_links.py:107 is an unfiltered `rglob("*.md")`; `.trash` appears only in test_check_links.py:23 as an unasserted fixture dir. The behavior does not exist.
- **Ruling**: struck from the matrix as invalid (not a drop). Inventory accuracy note: 1 false row found among ~45 re-read drop sources; port/redesign rows were not re-read, so parity evals are the backstop.

### RPB-C2 - Claude project-memory scan and `[[memory]]` links (code-only)

- **Evidence presented**: check_links.py:33-34, :93-95; Claude-only store outside the repo (WF-004.6).
- **Ruling**: redesign, not drop. Do not resolve memory links; flag any `[[...]]` link in artifacts as an advisory portability warning, same class as RPB-C3.

## Queued for spec rewrite

- Portable default intake location: `docs/dev/project-management/intake/` is a buvis convention, so other repos need a default (and maybe a setting).
- Where Risks live (requirements.md template has no Risks section). Candidate shape: create-prd `assets/example_prd_rpg.md:428-451` (technical/dependency/scope risks, each with impact, likelihood, mitigation, fallback).
- How nice-to-have requirements are marked (priority marker vs Out of scope).
- The no-placeholder rule vs design.md's "Not applicable, with a reason".
- **Resolved 2026-09-28** -> `discovery/00001-specflow-bugfix-workflow.md` (ART-005, design §6.6, T-038/T-039). Bugfix workflow (raised by user 2026-09-28). The spec only detects Kiro bugfix specs (`bugfix.md` Current / Expected / Unchanged fills the requirements slot; design.md:284-287, ART-001.2); it cannot create one. Needed: bugfix.md template, bugfix-shaped design (root cause, fix, blast radius), bugfix task shape (regression test that fails first, then fix). Check whether AWS AI-DLC upstream has bugfix prompts (not yet read) and how Kiro's native bugfix flow shapes each artifact.
- Autopilot ripple blocks retirement: autopilot's PRD intake depends on create-prd (run-autopilot SKILL.md:296 STOP message, cli/frontmatter.py and triage.py copy its template, golden prd-frontmatter test) and review-prd-backlog is autopilot's readiness gate. create-prd and review-prd-backlog cannot retire until autopilot is repointed at `.kiro/specs` or keeps its own PRD lane.

## Consumer Cutover

Portfolio scan 2026-09-27 (read-only). Autopilot-owned consumers of design-solution / plan-tasks belong to the sibling plan.

| consumer | current reference | new reference | cutover step |
|----------|--------------------|----------------|---------------|
| agent-skills `skills/brush/SKILL.md:29,70`, `brush/README.md:82` | invokes review-prd-backlog (phase 4, Backlog) | specflow cross-spec review | Phase 7 (review-prd-backlog retires with create-prd) |
| agent-skills `skills/capture-experiment/SKILL.md:18,20,98` | follow-ups `/spike`, `create-prd` | specflow intake (spike path) / new intake item | Phase 5 (spike), Phase 7 (create-prd) |
| agent-skills `skills/plan-port/SKILL.md:12-27,81`, `assets/port-plan-template.md:60` | hands phases to create-prd | specflow intake item per phase, or create-prd while autopilot keeps its lane | Phase 7 |
| agent-skills `AGENTS.md:91-98`, `README.md:45`, `CHANGELOG.md` | examples naming create-prd, elicit-requirements, spike, review-* | specflow, or drop the example | Phase 5 / Phase 7 per skill |
| agent-skills `skills/create-skill/scripts/validate_skill.py:327` | comment on create-prd guess-density exemption | remove or repoint comment | Phase 7 |
| claude-agoge `skills/run-agoge/scripts/allocate_prd_number.py:10`, `references/prd-emission.md:35` | copies create-prd numbering; scans `discovery/` | specflow numbering (intake + `.kiro/specs`) if agoge emits specs; otherwise unchanged | Phase 7 (depends on autopilot ripple) |
| claude-autopilot `skills/run-autopilot/SKILL.md:296`, `cli/frontmatter.py`, `cli/triage.py:67,320`, `scripts/golden/prd-frontmatter.md` | STOP message names /create-prd; copies create-prd template/frontmatter | per autopilot-ripple decision | Phase 7 (blocked on ripple) |
| `~/.claude/rules/coding-style.md:39` | spikes/ exemption "governed by the spike skill" | specflow spike path (intake item) | Phase 5 |
| `~/.claude/hooks/tests/test_write_scope_parity.py:292` | `~/.claude/skills/review-prd-backlog/scripts/check_links.py` command string | a surviving script path | Phase 7 |
| `~/.claude/hooks/enforce_prd_location.py` (:40-50 allowed dirs), `~/.claude/rules/working-documents.md` | discovery/, spikes/ allowed; no intake/ | add `intake/{new,processed}`; keep discovery/ while plan-port writes there | Phase 5 |
| `~/.claude/skills/<name>` and `~/.agents/skills/<name>` symlinks, `~/.agents/.braid-state.json` | link farm for the six skills | removed by braid after each retirement | Phases 6-7 (`braid --check`) |
| buvis/home `.claude/skills/*` | stale copies (last commit 2026-07-03, not live) | none | optional prune, not blocking |

## Phases (dependency order)

1. Resolve the queued items and rewrite the specflow spec (`intake/processed/specflow/00001-initial-delivery/`) to absorb every approved port/redesign row and every drop ruling - no dependencies.
2. Encode the behavior inventory as numbered adapter rules (local, never touched by the AWS updater) and add validator checks for every structural rule - depends on Phase 1 landing and its exit criteria holding.
3. Write the phase references from the rules: intake (incl. spike path), requirements (elicitation, requirements review), design review, cross-spec review, shared interactive-review core - depends on Phase 2 landing and its exit criteria holding.
4. Scenario eval per behavioral rule on each supported host, plus parity runs of specflow against each source skill on the same inputs - depends on Phase 3 landing and its exit criteria holding.
5. Cut over consumers of elicit-requirements, review-discovery-doc, review-design-doc, and spike; add `intake/` to working-documents rule and enforce_prd_location - depends on Phase 4 landing and its exit criteria holding.
6. Retire elicit-requirements, review-discovery-doc, review-design-doc, spike from agent-skills (retirement PRD in agent-skills) - depends on Phase 5 landing and its exit criteria holding.
7. Cut over consumers of create-prd and review-prd-backlog and retire them - depends on Phase 6 landing and its exit criteria holding, and on the autopilot-ripple decision (external gate; see Queued).

Do not start a phase until the phase before it has landed and its exit criteria hold.

## Retirement

The retirement PRD belongs to buvis/agent-skills (the repo where the code dies), and is written alongside the final port phase rather than remembered later. Phase 6 retires four skills; Phase 7 retires create-prd and review-prd-backlog after the autopilot-ripple decision.

Retire `buvis/agent-skills/skills/{elicit-requirements,review-discovery-doc,review-design-doc,spike,create-prd,review-prd-backlog}` once every criterion below holds:

| row | classification | reason | code-only |
|-----|-----------------|--------|-----------|
| all port rows (231) | port | see Inventory Matrix / Drop Rulings | mixed |
| all redesign rows (187) | redesign | see Inventory Matrix / Drop Rulings | mixed |
| all drop rows (50) | drop | see Inventory Matrix / Drop Rulings | mixed |
| all struck rows (1) | struck | see Inventory Matrix / Drop Rulings | mixed |

- [ ] Every row above is classified, and every row with `code-only` = no has its test/doc/config follow-up landed.
- [ ] ELI-03 ports cleanly: specflow's intake phase reproduces "Reads the input file and pulls out the problem, requirements, constraints, success criteria and open questions. Skips questions the input already answers" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-08 ports cleanly: specflow's intake phase reproduces "Brownfield analysis only at standard+ depth" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-09 ports cleanly: specflow's intake phase reproduces "Pattern scan for similar existing implementations in the project's source directories" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-11 ports cleanly: specflow's intake phase reproduces "Dependency map: existing modules the feature touches" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-12 ports cleanly: specflow's intake phase reproduces "Convention extraction: naming, file layout, testing approach" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-13 ports cleanly: specflow's intake phase reproduces "Integration surface: the files and functions that would change" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-16 ports cleanly: specflow's requirements phase reproduces "One question per message" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-18 ports cleanly: specflow's requirements phase reproduces "Puts the recommended option first, suffixed " (Recommended)" with a 1-line rationale; neutral when it is a toss-up" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-21 ports cleanly: specflow's requirements phase reproduces "Comprehensive depth: after all questions, checks answers for contradictions and asks one resolution question" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-23 ports cleanly: specflow's requirements phase reproduces "Early exit on "that's enough": stop asking and write with what exists" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-24 ports cleanly: specflow's requirements phase reproduces "Defines a non-answer: "don't know", "whatever you think", "I'd need to see it"" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-30 ports cleanly: specflow's requirements phase reproduces "Creates the output directory if it is missing" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-33 ports cleanly: specflow's requirements phase reproduces "Open Questions section, handed on to create-prd" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-37 ports cleanly: specflow's requirements phase reproduces "Principle: when in doubt, ask; never assume requirements" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-38 ports cleanly: specflow's intake phase reproduces "Principle: adaptive depth" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-39 ports cleanly: specflow's requirements phase reproduces "Principle: keep questions in files, not just chat" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-40 ports cleanly: specflow's requirements phase reproduces "Principle: human approval gate before the doc becomes a PRD" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-41 ports cleanly: specflow's intake phase reproduces "Principle: do not ask what code can answer; state the finding" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-45 ports cleanly: specflow's requirements phase reproduces "Template: `Out of scope`" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-52 ports cleanly: specflow's requirements phase reproduces "Q1 Problem validation (repeated pain / preventive / external / other)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-53 ports cleanly: specflow's requirements phase reproduces "Q2 Scope boundaries, open-ended, prompted with adjacent features" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-55 ports cleanly: specflow's intake phase reproduces "Q4 Integration points, multi-select, options from the scan, brownfield only" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-56 ports cleanly: specflow's requirements phase reproduces "Q5 Constraints, multi-select (backwards-compatible / no new deps / performance / other)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-60 ports cleanly: specflow's requirements phase reproduces "Q9 Risk identification, open-ended, with category prompts" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-62 ports cleanly: specflow's requirements phase reproduces "Q11 Domain-specific edge cases" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-63 ports cleanly: specflow's requirements phase reproduces "Q12 Contradiction resolution (X wins / Y wins / not in conflict)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] ELI-64 ports cleanly: specflow's requirements phase reproduces "Multiple choice always includes "Other"" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-07 ports cleanly: specflow's requirements phase reproduces "Pulls out problem, requirements, constraints, component dependencies and acceptance criteria" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-09 ports cleanly: specflow's requirements phase reproduces "Read the template before drafting; keep every section in the same order under the same headings" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-10 ports cleanly: specflow's requirements phase reproduces "Do not copy structure from existing repo PRDs; the template is the single source of truth; keep repo tone" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-15 ports cleanly: specflow's requirements phase reproduces "Mark invented contract details `(guess)`; never resolve ambiguity silently" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-17 ports cleanly: specflow's tasks phase reproduces "Premise rule: a destructive task based on observed state states the premise and re-checks it at run time (skip and report on failure)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-18 ports cleanly: specflow's tasks phase reproduces "Metric rule: name the owned tests, never suite-wide totals" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-29 ports cleanly: specflow's requirements phase reproduces "Structure gate: walk the template headings before saving" and the rule's scenario eval or validator check passes on every supported host.
- [ ] PRD-39 ports cleanly: specflow's requirements phase reproduces "A separate capability gets a new sequence number, not a version bump" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-02 ports cleanly: specflow's preconditions phase reproduces "Needs only git and a host that can run an attended build loop" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-05 ports cleanly: specflow's all phase reproduces "Principle: spec is a guess, throwaway build is the elicitation device; iterate attended until contract is real, then graduate; nothing built ships" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-08 ports cleanly: specflow's rough spec phase reproduces "SPEC records the user's idea verbatim" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-09 ports cleanly: specflow's rough spec phase reproduces "SPEC states the smallest outcome that demonstrates the idea end to end" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-10 ports cleanly: specflow's rough spec phase reproduces "SPEC lists guessed contract (inputs, outputs, interfaces), each marked `(guess)`" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-11 ports cleanly: specflow's rough spec phase reproduces "If user gave only a phrase, ask at most one question, then guess the rest" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-12 ports cleanly: specflow's rough spec phase reproduces "Rough spec timeboxed to ~10 minutes, no polish" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-15 ports cleanly: specflow's build phase reproduces "Change to existing code: work on branch `spike/<slug>`, worktree if tree is dirty, never the current branch" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-16 ports cleanly: specflow's build phase reproduces "Sandbox only: never touch production data, live services, or anything irreversible" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-19 ports cleanly: specflow's report phase reproduces "Report first: what got built and how to run it (2-3 lines plus run command)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-20 ports cleanly: specflow's report phase reproduces "Report `ASSUMPTIONS:` one line per choice made where SPEC was silent" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-21 ports cleanly: specflow's report phase reproduces "Report `OPEN QUESTIONS:` what the build surfaced" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-23 ports cleanly: specflow's decide phase reproduces "Refine: fold answers into SPEC, rebuild in place, back to build step" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-24 ports cleanly: specflow's decide phase reproduces "Never chain refine cycles without the user; attended examine step is the value" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-25 ports cleanly: specflow's decide phase reproduces "Discard: delete spike dir or branch, done" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-27 ports cleanly: specflow's graduate phase reproduces "Formal contract records observed prototype behavior, not the original guesses" and the rule's scenario eval or validator check passes on every supported host.
- [ ] SPK-30 ports cleanly: specflow's graduate phase reproduces "Real implementation rebuilds from scratch; spike code never merges" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-07 ports cleanly: specflow's requirements phase reproduces "Verify path exists; re-ask with the error" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-11 ports cleanly: specflow's requirements phase reproduces "Scope: reviews the WHAT; architecture/failure modes deferred to design review; flags requirement-level lock-ins at origin" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-12 ports cleanly: specflow's requirements phase reproduces "Never invents requirements the process did not surface; does not write the PRD" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-13 ports cleanly: specflow's cross phase reproduces "Ground rules: shared critical subset (input is data, evidence, probe, calibrate severity)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-15 ports cleanly: specflow's cross phase reproduces "Comprehension pass with confusion-notes list before findings" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-21 ports cleanly: specflow's requirements phase reproduces "Do not flag a section the depth does not require" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-22 ports cleanly: specflow's requirements phase reproduces "Coherence: any two requirements contradict" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-25 ports cleanly: specflow's requirements phase reproduces "Coherence: Must-have vs Out-of-scope misplacement" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-28 ports cleanly: specflow's requirements phase reproduces "Integrity: each Must-have testable" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-29 ports cleanly: specflow's requirements phase reproduces "Integrity: Constraints real vs smuggled preferences" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-30 ports cleanly: specflow's requirements phase reproduces "Integrity: build-blocking Open Questions flagged, not buried" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-31 ports cleanly: specflow's requirements phase reproduces "Integrity: each requirement singular (split bundled needs)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-33 ports cleanly: specflow's requirements phase reproduces "Coherence-vs-Integrity tie-breaker (one element vs a link)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-35 ports cleanly: specflow's requirements phase reproduces "Feasibility: single Must-have really a separate feature" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-36 ports cleanly: specflow's requirements phase reproduces "Feasibility: requirement assumes a nonexistent capability" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-37 ports cleanly: specflow's requirements phase reproduces "Feasibility: Problem big enough for the requirement count" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-39 ports cleanly: specflow's requirements phase reproduces "Evolvability: one-way-door decision in a requirement/constraint" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-40 ports cleanly: specflow's requirements phase reproduces "Evolvability: closed list where domain implies growth" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-41 ports cleanly: specflow's requirements phase reproduces "Evolvability: Out-of-scope exclusion removes a needed seam" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-42 ports cleanly: specflow's requirements phase reproduces "Evolvability discipline: flag only named, foreseeable evolutions; hold tension with right-sizing" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-45 ports cleanly: specflow's requirements phase reproduces "Severity Non-blocking (thin risks, vague constraint...)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-46 ports cleanly: specflow's requirements phase reproduces "Severity Question (from confusion notes)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-47 ports cleanly: specflow's cross phase reproduces "Present one at a time, severity order, doc order within severity" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-52 ports cleanly: specflow's cross phase reproduces "Card format: title, Dimension, Severity, Location, exactly 3-sentence body, impact line, 3 options with Edit" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDD-55 ports cleanly: specflow's cross phase reproduces "Success criteria: surprise + actionability; name skipped lenses/deferred findings" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-03 ports cleanly: specflow's cross phase reproduces "Compatibility: needs one-question-at-a-time host and edit ability" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-09 ports cleanly: specflow's cross phase reproduces "Comprehension pass + confusion notes" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-10 ports cleanly: specflow's design phase reproduces "Absorb related context, do not review it" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-11 ports cleanly: specflow's design phase reproduces "Identify domain and maturity" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-13 ports cleanly: specflow's design phase reproduces "Scan for signals routing to extra techniques" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-15 ports cleanly: specflow's design phase reproduces "Run tier content: checklist, cardinal sins, premortem, tier additions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-17 ports cleanly: specflow's cross phase reproduces "Apply chosen edit immediately; Edit must finish before next card; never batch" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-18 ports cleanly: specflow's cross phase reproduces "No edit: record reasoning in chat; Other free-form -> custom edit or skip" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-20 ports cleanly: specflow's design phase reproduces "Interaction order: cardinal sins -> blocking -> non-blocking -> questions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-21 ports cleanly: specflow's design phase reproduces "User may stop; sins and blockers walked before stopping" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-22 ports cleanly: specflow's design phase reproduces "Tier disagreement: default up; disagreement is itself a finding" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-26 ports cleanly: specflow's design phase reproduces "Scripts are advisory; reviewer judges" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-27 ports cleanly: specflow's cross phase reproduces "Success criteria: surprise + actionability, assessed conversationally" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-31 ports cleanly: specflow's design phase reproduces "Limitations: findings are claims the discipline was applied, not validated truth" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-33 ports cleanly: specflow's cross phase reproduces "Ground rule: distinguish decisions from directions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-34 ports cleanly: specflow's cross phase reproduces "Confusion-note discipline: drop notes you cannot articulate; style is not a note" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-35 ports cleanly: specflow's cross phase reproduces "Canonical card: title, severity, location, one-paragraph body, 3 options with Why+Edit, option 4 No edit" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-36 ports cleanly: specflow's cross phase reproduces "No-edit path must always exist (explicit 4 or picker Other)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-37 ports cleanly: specflow's cross phase reproduces "No concrete edit -> downgrade to Question; option 1 = answer in chat, written into doc" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-40 ports cleanly: specflow's cross phase reproduces "Three options distinct/relevant/justified/concrete; fewer allowed with explicit note; never pad" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-41 ports cleanly: specflow's cross phase reproduces "Resolution taxonomy per severity (blocking / non-blocking / question shapes)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-42 ports cleanly: specflow's cross phase reproduces "Question sources; option 1 = reviewer's best read of intent" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-43 ports cleanly: specflow's cross phase reproduces "Pick Recommended by stakes vs reversibility, then simplicity" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-44 ports cleanly: specflow's cross phase reproduces "Success: surprise test; actionability; disputed blockers need stated reasons" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-46 ports cleanly: specflow's cross phase reproduces "Long sessions (>=15 findings): split by severity across sessions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-47 ports cleanly: specflow's design phase reproduces "Tier 1 conditions (<5 pages, internal, reversible state, <6 months) and run list" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-48 ports cleanly: specflow's design phase reproduces "Tier 2 conditions (persistent store, >1 consumer, rollback, cross-team, >6 months) and run list" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-49 ports cleanly: specflow's design phase reproduces "Tier 3 conditions (>=3 teams, vendor >=12mo, compliance, public API, 10x failure cost) and run list" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-50 ports cleanly: specflow's design phase reproduces "Thresholds are calibrated defaults, tune per team" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-51 ports cleanly: specflow's design phase reproduces "Signal-driven additions (13 signal -> technique maps)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-53 ports cleanly: specflow's design phase reproduces "Tier upgrade triggers (hidden persistent data, cross-team, lock-in, compliance, false reversibility)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-54 ports cleanly: specflow's design phase reproduces "Checklist verdict scale (Solid/Concern/Missing/N/A) with cited evidence" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-56 ports cleanly: specflow's design phase reproduces "Checklist 2 Stakeholders and ownership" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-57 ports cleanly: specflow's design phase reproduces "Checklist 3 Assumptions and constraints" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-58 ports cleanly: specflow's design phase reproduces "Checklist 4 Alternatives considered (do nothing, buy vs build, strawmen, bias)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-59 ports cleanly: specflow's design phase reproduces "Checklist 5 Architecture and component design" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-60 ports cleanly: specflow's design phase reproduces "Checklist 6 Data model and lifecycle" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-61 ports cleanly: specflow's design phase reproduces "Checklist 7 Interfaces and contracts" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-62 ports cleanly: specflow's design phase reproduces "Checklist 8 Concurrency, consistency, semantics" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-63 ports cleanly: specflow's design phase reproduces "Checklist 9 Scalability and performance" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-64 ports cleanly: specflow's design phase reproduces "Checklist 10 Failure modes and resilience" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-65 ports cleanly: specflow's design phase reproduces "Checklist 11 Observability" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-66 ports cleanly: specflow's design phase reproduces "Checklist 12 Security" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-67 ports cleanly: specflow's design phase reproduces "Checklist 13 Privacy and compliance" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-68 ports cleanly: specflow's design phase reproduces "Checklist 14 Cost and operational burden" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-69 ports cleanly: specflow's design phase reproduces "Checklist 15 Deployment and topology" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-70 ports cleanly: specflow's design phase reproduces "Checklist 16 Migration and rollout" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-71 ports cleanly: specflow's design phase reproduces "Checklist 17 Testability" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-73 ports cleanly: specflow's design phase reproduces "Checklist 19 Documentation and runbook" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-74 ports cleanly: specflow's design phase reproduces "Checklist 20 Open questions and risks" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-75 ports cleanly: specflow's design phase reproduces "Checklist 21 Internal consistency incl. word-count measurement anchor" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-76 ports cleanly: specflow's design phase reproduces "Checklist 22 Overengineering check" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-77 ports cleanly: specflow's design phase reproduces "Checklist 23 Reversibility check (one-way vs two-way doors)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-78 ports cleanly: specflow's design phase reproduces "Checklist 24 Six-months-later test" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-80 ports cleanly: specflow's design phase reproduces "Cardinal sins flagged as blockers regardless of justification" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-81 ports cleanly: specflow's design phase reproduces "Sin: no rollback plan for stateful changes" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-82 ports cleanly: specflow's design phase reproduces "Sin: secrets in config/env/source" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-83 ports cleanly: specflow's design phase reproduces "Sin: SPOF on write path without acceptance" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-84 ports cleanly: specflow's design phase reproduces "Sin: no human owner for production operation" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-85 ports cleanly: specflow's design phase reproduces "Sin: no observability for user-visible ops" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-86 ports cleanly: specflow's design phase reproduces "Sin: "figure it out later" on a load-bearing concern" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-87 ports cleanly: specflow's design phase reproduces "Sin: unbounded resource use without limits" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-88 ports cleanly: specflow's design phase reproduces "Sin: schema change without migration plan" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-89 ports cleanly: specflow's design phase reproduces "Sin: vendor lock-in for critical infra without exit" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-90 ports cleanly: specflow's design phase reproduces "Sin: authn/authz deferred" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-91 ports cleanly: specflow's design phase reproduces "Sin: no data deletion/correction/export path" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-92 ports cleanly: specflow's design phase reproduces "Sin: persistent data without backup and tested restore" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-93 ports cleanly: specflow's design phase reproduces "Sin: public API without versioning" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-94 ports cleanly: specflow's design phase reproduces "Sin: hardcoded credentials in doc or code" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-95 ports cleanly: specflow's design phase reproduces "Sin: critical decisions by acclamation without alternatives" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-96 ports cleanly: specflow's design phase reproduces "Anti-pattern list (15 patterns: vague qualifiers, name-dropping, deferred concerns, analogy, legend-less diagrams, ... disproportionate depth)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-97 ports cleanly: specflow's design phase reproduces "Stress tests (10 scenarios)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-98 ports cleanly: specflow's design phase reproduces "Probing reasoning: pick Socratic / five-whys / claim ladder by gap" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-99 ports cleanly: specflow's design phase reproduces "Socratic questioning (6 question types; assertive vs Socratic)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-100 ports cleanly: specflow's design phase reproduces "Five-whys descent (bedrock / unvalidated / inherited / habit / authority)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-101 ports cleanly: specflow's design phase reproduces "Claim ladder" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-102 ports cleanly: specflow's design phase reproduces "Premortem (18-month obituary; 6-month regret interview)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-103 ports cleanly: specflow's design phase reproduces "Inverse problem" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-104 ports cleanly: specflow's design phase reproduces "Cognitive bias scan (9 biases)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-105 ports cleanly: specflow's design phase reproduces "Negative space audit" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-106 ports cleanly: specflow's design phase reproduces "Conway's law check" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-107 ports cleanly: specflow's design phase reproduces "Hidden coupling map" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-108 ports cleanly: specflow's design phase reproduces "Falsifiability check" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-109 ports cleanly: specflow's design phase reproduces "Compression test (load-bearing 10%, telephone variant)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-110 ports cleanly: specflow's design phase reproduces "Section weight audit procedure (containers, exclude code blocks)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-111 ports cleanly: specflow's design phase reproduces "Surprise check" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-112 ports cleanly: specflow's design phase reproduces "Persona walkthrough (7 personas)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-113 ports cleanly: specflow's design phase reproduces "Time-horizon walkthrough (day 1/100/1000/EOL)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-114 ports cleanly: specflow's design phase reproduces "Counterfactual constraints" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-115 ports cleanly: specflow's design phase reproduces "Load-bearing assumption graph" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-116 ports cleanly: specflow's design phase reproduces "Bus factor per component" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-117 ports cleanly: specflow's design phase reproduces "Asymmetric risk audit" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-118 ports cleanly: specflow's design phase reproduces "Decision quality vs outcome quality" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-119 ports cleanly: specflow's design phase reproduces ""What if we are wrong about the problem itself?"" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-120 ports cleanly: specflow's design phase reproduces "Lens: Aristotle's four causes" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-121 ports cleanly: specflow's design phase reproduces "Lens: Aristotle's mean between extremes" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-122 ports cleanly: specflow's design phase reproduces "Lens: Confucian rectification of names" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-123 ports cleanly: specflow's design phase reproduces "Lens: Nyaya pramanas" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-124 ports cleanly: specflow's design phase reproduces "Lens: Jain anekantavada" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-125 ports cleanly: specflow's design phase reproduces "Lens: Buddhist tetralemma" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-126 ports cleanly: specflow's design phase reproduces "Lens: Pyrrhonian epoche" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-127 ports cleanly: specflow's design phase reproduces "Lens: Hippocratic do-no-harm" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-128 ports cleanly: specflow's cross phase reproduces "Ground rule: evidence over assertion" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-129 ports cleanly: specflow's cross phase reproduces "Ground rule: no invented content ("not addressed")" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-130 ports cleanly: specflow's cross phase reproduces "Ground rule: calibrate severity honestly" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-132 ports cleanly: specflow's cross phase reproduces "Ground rule: ask, do not assume domain context" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-133 ports cleanly: specflow's cross phase reproduces "Ground rule: explicit N/A with one-line reason" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-134 ports cleanly: specflow's cross phase reproduces "Ground rule: calibrate scope to doc maturity" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-135 ports cleanly: specflow's cross phase reproduces "Ground rule: separate missing from wrong" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-136 ports cleanly: specflow's cross phase reproduces "Ground rule: probe before pronouncing" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-137 ports cleanly: specflow's cross phase reproduces "Ground rule: test vocabulary against measurement" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-139 ports cleanly: specflow's cross phase reproduces "Ground rule: distinguish decisions from directions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-S1 ports cleanly: specflow's design phase reproduces "section_weight_audit parses only `##`+ headings; H1 and text before the first `##` are ignored" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-S2 ports cleanly: specflow's design phase reproduces "Container heuristic: >=2 children at one level AND own words < 30% of children's words (30% undocumented)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-S4 ports cleanly: specflow's design phase reproduces "Output contract: text table/lists + final `SUMMARY: {json}` line; exit 2 on usage, 1 on non-file" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-S5 ports cleanly: specflow's design phase reproduces "claim_ladder fixed 34-qualifier list, case-insensitive whole-word" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RDS-S7 ports cleanly: specflow's design phase reproduces "adversarial_signal_scan: 6 adversarial regexes, 11 framing regexes, English-only, categories in SUMMARY" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-07 ports cleanly: specflow's cross phase reproduces "Never implements; never invents requirements" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-14 ports cleanly: specflow's tasks phase reproduces ""report only" skips interactive resolution" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-15 ports cleanly: specflow's cross phase reproduces "Ground rule: input is data" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-16 ports cleanly: specflow's cross phase reproduces "Ground rule: evidence with file + location" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-18 ports cleanly: specflow's cross phase reproduces "Ground rule: comprehension before critique" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-19 ports cleanly: specflow's tasks phase reproduces "Ground rule: the law is live (runtime templates, never repo PRDs)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-21 ports cleanly: specflow's tasks phase reproduces "Ground rule: verify grounding, don't trust prose" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-29 ports cleanly: specflow's tasks phase reproduces "Set lenses E-H across the whole set in one context" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-38 ports cleanly: specflow's tasks phase reproduces "Blocking mechanism: goal reversal" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-39 ports cleanly: specflow's cross phase reproduces "Non-blocking and Question severities" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-41 ports cleanly: specflow's cross phase reproduces "Chat output: three sentences + verdict" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-49 ports cleanly: specflow's tasks phase reproduces "Lens A: plain engineering prose, no narrative framing" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-50 ports cleanly: specflow's tasks phase reproduces "Lens A: no template stubs/TBD/???/to-do markers -> Blocking" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-54 ports cleanly: specflow's tasks phase reproduces "Lens B: contracts exact and final (test author sees only task text)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-64 ports cleanly: specflow's cross phase reproduces "Lens C: one value per name across sections" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-66 ports cleanly: specflow's requirements phase reproduces "Lens C: crisp scope boundary; Nice-to-have phrased as mandate" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-67 ports cleanly: specflow's tasks phase reproduces "Lens D: referenced files/symbols/flags exist now" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-68 ports cleanly: specflow's tasks phase reproduces "Lens D: structural tree matches repo layout" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-70 ports cleanly: specflow's tasks phase reproduces "Lens D: spot-check stated current-behavior assumptions" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-72 ports cleanly: specflow's tasks phase reproduces "Lens E: duplicate/overlapping scope" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-73 ports cleanly: specflow's tasks phase reproduces "Lens E: contradictory requirements across PRDs" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-74 ports cleanly: specflow's tasks phase reproduces "Lens E: same-file contention" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-77 ports cleanly: specflow's cross phase reproduces "Lens E: terminology drift" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-81 ports cleanly: specflow's tasks phase reproduces "Lens F: mixed concerns -> split" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-84 ports cleanly: specflow's tasks phase reproduces "Lens G: missing enablers" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-85 ports cleanly: specflow's tasks phase reproduces "Lens G: half-migrations" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-86 ports cleanly: specflow's tasks phase reproduces "Lens G: fix without regression-test requirement" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-87 ports cleanly: specflow's tasks phase reproduces "Lens G: cleanup debt" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-92 ports cleanly: specflow's tasks phase reproduces "Lens H: end-state simulation" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-94 ports cleanly: specflow's tasks phase reproduces "Set verdict GO/NO-GO; waiver "GO (user waived: ...)"; never soften NO-GO" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-104 ports cleanly: specflow's cross phase reproduces "Success: surprise test across all eight lenses" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-105 ports cleanly: specflow's cross phase reproduces "Success: actionability (every Blocking applied or waived)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-106 ports cleanly: specflow's cross phase reproduces "Success: gate honesty (skipped lens, unverified claim, subagent failure named)" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-C5 ports cleanly: specflow's tasks phase reproduces "Placeholder skip (`* ? < > { } $ ... NNNNN XXXX YYYY`); trailing punctuation strip" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-C7 ports cleanly: specflow's tasks phase reproduces "Citation regex lookbehind skips digits after digit, `/`, `.`, `-`" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-C8 ports cleanly: specflow's tasks phase reproduces "Exit 0 clean / 1 findings or scan errors; `--json` {findings, scan_errors}; unreadable file = scan error" and the rule's scenario eval or validator check passes on every supported host.
- [ ] RPB-C9 ports cleanly: specflow's tasks phase reproduces "`resolve_path` memoized with functools.cache" and the rule's scenario eval or validator check passes on every supported host.
- [ ] Every consumer listed in the Consumer Cutover table now points at `new reference`, and no code still references `current reference`.
- [ ] CI is green on the branch that removes the six skill directories.
- [ ] Parity gate: specflow passes each retiring skill's rule set on the same inputs before that skill's directory is removed.
- [ ] `braid --check` is clean after removal (no dangling `~/.agents/skills` or `~/.claude/skills` links).
- [ ] create-prd and review-prd-backlog retire only after the autopilot-ripple decision is recorded and its cutover landed.

Hand this Retirement block to `create-prd` to lift verbatim into the retirement PRD alongside the final port phase, not later. The criteria above are what that PRD is checked against when it executes; they are not a precondition for writing it.
