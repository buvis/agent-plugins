# Requirements: specflow runtime skill

Sources: docs/dev/project-management/intake/processed/specflow/00006-runtime-skill/

Depends on: 00003, 00004, 00005

## Purpose

Ship the workflow itself: one compact skill and its phase references that take a developer from intake through requirements, design, tasks, implementation, and verification, with explicit approval gates, two profiles, feature and bugfix shapes, both workflow orders, and the spike path.

## Scope

The rest of phase 4 of the source plan (T-030 to T-039, T-072): `SKILL.md`, the shared dialogue contract, the six phase references, the bugfix instructions and validation, the status and handoff summaries, and the spike path. The files and the helper these instructions rely on belong to 00004; reviews and the conversion skill belong to 00007.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Requirements

### PKG-001: Portable package

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want one portable plugin package so that I do not maintain separate workflow implementations for every agent.

#### Acceptance criteria

Criterion 1: see 00002.

2. WHEN a compatible host discovers the plugin, THE PACKAGE SHALL expose the runtime workflow from `skills/<runtime-skill>/SKILL.md`.

Criteria 3-5: see 00002.

### ART-001: Canonical Kiro artifact layout

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want every tool to write Kiro-compatible specifications so that Kiro IDE can open and continue them naturally.

#### Acceptance criteria

Criteria 1-5: see 00004.

6. WHEN the workflow creates a spec, IT SHALL write Kiro's `.config.kiro` (`specId`, `workflowType`, `specType`) and record the spec type in `.specflow.json`.

Criteria 7-10: see 00004.

11. Headings, identifiers, field names, EARS keywords, markers, and file names in artifacts SHALL stay in English whatever language the developer writes in; prose MAY follow the developer's language.

### ART-002: Requirements artifact

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want testable requirements so that design and implementation can be reviewed against explicit behavior.

Scope: the dialogue criteria ART-002.6, .12-.14, and .16-.18 apply across workflow phases, including intake and Design-First, together with INT-001.5/SEC-002.2 logging and WF-002.1 approval summaries. They are loaded before questioning or approval, independently of whether a requirements phase has run; artifact-specific criteria retain their named scope (decision 2026-10-03 #14).

#### Acceptance criteria

1. WHEN requirements are generated for a feature spec, `requirements.md` SHALL contain a purpose, scope, user stories, numbered requirements, and acceptance criteria.
2. Acceptance criteria SHALL use testable EARS-style statements where the pattern is applicable.
3. Each requirement SHALL have a stable identifier such as `REQ-001`.
4. Functional and non-functional requirements SHALL be distinguishable.
5. Assumptions, exclusions, and unresolved questions SHALL be explicit.
6. The workflow SHALL ask clarifying questions one at a time when missing information would materially change scope or behavior.
7. `requirements.md` SHALL list the risks known at requirements time (scope, dependency, outside) under `## Risks`, one line each with impact, likelihood, mitigation, and fallback.
8. Every requirement SHALL be required. An optional item SHALL become a requirement, move to `## Out of scope` with a note, or become its own spec.
9. A requirement SHALL state needed behavior, not a solution; a named technology or mechanism SHALL appear only as a stated constraint.
10. A contract detail the developer did not give SHALL be marked `(guess)` until the developer confirms it.

Criterion 11: see 00004.

12. THE AGENT SHALL preserve an answer's caveats in the Q&A log and record only genuinely undecided content affecting this spec under `## Unresolved questions`, with what would resolve it. A definite choice for the current release SHALL remain a requirement; a later revisit that does not affect this spec SHALL remain a follow-up note in the log, outside gate-bearing unresolved items. Phrases such as "for now" SHALL NOT alone create an unresolved marker. WHEN the current decision is unclear, THE AGENT SHALL clarify under the shared question policy or retain the uncertainty, never infer a settled choice.
13. An answer taken from the intake item or the repository instead of asked SHALL name its source.
14. While asking, THE AGENT SHALL say where the questioning stands (for example "question 3 of about 8"), so the developer can judge whether to stop early.
15. Each requirement in `requirements.md` SHALL carry a `Source:` line naming where it came from: the idea, a Q&A entry, or a discovery finding. Content with no such source SHALL be marked `(guess)` or listed under `## Assumptions`, never written as a requirement. An option the developer did not choose SHALL NOT become a requirement or an exclusion.
16. Every clarifying question SHALL offer a "not decided yet" choice besides "Other"; choosing it SHALL record an unresolved question.
17. Questions SHALL use the developer's words, and a term of art SHALL be defined in the question the first time it appears.
18. WHEN questions were asked, THE AGENT SHALL play back its reading of the answers as a short list before drafting from them. Explicit, unambiguous answers SHALL NOT need another confirmation. WHEN the playback introduces a material interpretation or exposes an unresolved conflict, THE AGENT SHALL obtain confirmation or correction before drafting from that interpretation, combining it with an existing confirmation when possible and using a separate stop only when needed. Playback SHALL NOT replace artifact approval or named marker acceptance.

### ART-003: Design artifact

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want the design linked to requirements so that implementation choices are explainable and complete.

#### Acceptance criteria

1. WHEN design begins, THE WORKFLOW SHALL read the approved `requirements.md` (Requirements-First) or the intake item (Design-First) and relevant repository context.
2. For a feature spec, `design.md` SHALL describe architecture, components, data flow, interfaces, failure handling, security, testing strategy, technical risks and edge cases, and migration or rollout considerations when applicable.
3. Each material design element SHALL trace to one or more requirement identifiers. In a Design-First spec the trace SHALL run the other way: each requirement SHALL name the design elements that realize it, and the design's traceability section SHALL read `Not applicable: Design-First`, so approving requirements never edits the approved design.
4. Material alternatives SHALL include two or three options, including the smallest diff; the choice and rejected options SHALL record their reasons, and a larger choice SHALL say what its added size buys.
5. For a quick profile with no architecture change, `design.md` SHALL explicitly document the existing pattern being reused and why no broader design is required.
6. Before proposing new code, THE AGENT SHALL search verb and noun synonyms for each capability, check an empty search with a known-present term, and record helper paths and uses or the actual searches when none match.
7. Design SHALL name module and file placement, distinguishing new files from edits, and SHALL give exact applicable signatures, types, enums, field names, kinds, and thresholds ready to copy into tasks.
8. The existing technical-risk section SHALL include two or three likely next changes and what limits them, with impact, likelihood, mitigation, and fallback.

Criteria 9-11: see 00007.

12. Before proposing new code for a capability that an existing library, tool, or service could plausibly provide, THE AGENT SHALL include that option among the alternatives, with the reason it was chosen or rejected. WHEN the host cannot search for one, the design SHALL say it was not checked.

### ART-004: Tasks artifact

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want an executable task plan so that any supported agent can continue implementation safely.

#### Acceptance criteria

1. WHEN task planning begins, THE WORKFLOW SHALL read the approved requirements and design.
2. `tasks.md` SHALL contain ordered Markdown checkboxes with stable task identifiers (for bugfix specs, the shape in ART-005).
3. Each implementation task SHALL reference the requirements it satisfies.
4. Each task SHALL state its dependencies and verification method where those are not obvious, preferring a command, test, or file check.
5. Each task SHALL have one named outcome, a bounded file slice, enough context, exact applicable contracts, and its own verification after its listed dependencies, with no design choice left for the implementer to guess.
6. The final tasks SHALL cover end-to-end verification, documentation, compatibility, and cleanup.
7. Task completion SHALL be represented by checkbox state in `tasks.md`; `.specflow.json` SHALL not replace that source of truth.
8. A task that deletes or rewrites based on observed repository state SHALL state that premise; THE AGENT SHALL re-check it before running the task and, when it no longer holds, SHALL skip the task and report why.
9. A task's verification SHALL name the tests or checks the task owns, never a suite-wide total.
10. Each task SHALL name its Location and applicable Reuse, Contract, Details, and Acceptance criteria. Contracts SHALL be copied byte for byte from approved design; acceptance SHALL reference the approved requirements' IDs and numbered criteria, or bugfix clauses. A needed but vague contract SHALL be reported before approval.
11. WHEN a task changes an exported API, persisted schema or wire format, hook registration, implements a new algorithm, changes shared mutable state, or migrates persisted data, its Risk note SHALL name that actual change and its design mitigation. Calling or documenting an interface, risk words, and file count alone SHALL NOT trigger the note.
12. The planning summary SHALL give total tasks, execution order, ambiguities, any derived decomposition or dependencies, both sides of requirements/design contract conflicts, and the reason for each coupled multi-file task. Design owns implementation contracts; requirements own acceptance. A conflict that violates required behavior SHALL remain a blocker until the upstream artifact is corrected or a named exception is accepted.
13. THE AGENT SHALL split independent outcomes by safe file boundaries first and capability boundaries second, re-checking each piece's contracts, dependencies, and verification. A split piece SHALL build or pass its applicable check after its dependencies without an unfinished sibling. Coupled interface, implementation, caller, and test edits SHALL stay together. If no bounded task or safe split exists, THE AGENT SHALL report the attempted boundary and why it fails before tasks approval.
14. Re-planning SHALL preserve checked tasks and their IDs; it SHALL NOT silently reset completed work.
15. WHEN task Locations introduce two or more modules not named in design's Module placement, validation SHALL report an advisory drift warning.
16. A task MAY reference a criterion owned by a spec that its own spec names in its `Depends on:` line, written as that spec's reference, the requirement ID, and the criterion number, for example `00004 WF-004 criterion 8`. A task SHALL NOT reference a criterion of any other spec, and a criterion SHALL NOT be restated in a second spec to make it citable (decision 2026-10-04 #9).

### ART-005: Bugfix spec artifacts

Source: Kiro bugfix specs, captured in `discovery/00001-specflow-bugfix-workflow.md` §1.

**User story:** As a developer, I want to create and run a bugfix spec in any tool in the same shape Kiro uses, so that the fix is proven by a test that fails first and nothing else changes.

#### Acceptance criteria

1. WHEN a developer asks to fix a bug in a spec, THE WORKFLOW SHALL create a bugfix spec whose artifacts are `bugfix.md`, `design.md`, and `tasks.md`, and SHALL NOT create `requirements.md`.
2. `bugfix.md` SHALL contain `## Introduction` and `## Bug Analysis` with `### Current Behavior (Defect)`, `### Expected Behavior (Correct)`, and `### Unchanged Behavior (Regression Prevention)`.
3. Current Behavior clauses SHALL use `WHEN <condition> THEN the system <incorrect behavior>` numbered `1.x`; Expected Behavior clauses SHALL use `WHEN <condition> THEN the system SHALL <correct behavior>` numbered `2.x`; Unchanged Behavior clauses SHALL use `WHEN <condition> THEN the system SHALL CONTINUE TO <existing behavior>` numbered `3.x`.
4. The bugfix `design.md` SHALL contain a bug condition, a hypothesized root cause, a fix property tracing to the `2.x` clauses, a preservation property tracing to the `3.x` clauses, the fix implementation, and a testing strategy covering exploration, fix checking, and preservation checking.
5. The bugfix `tasks.md` SHALL order its tasks as: (1) a bug condition exploration test that MUST FAIL on the unfixed code, (2) preservation tests written by observing the unfixed code that MUST PASS on it, (3) the fix, followed by re-running the same task 1 and task 2 tests, and (4) a checkpoint running the full test suite.
6. Tasks 1 and 2 SHALL be completed, with their observed outcomes recorded in an `Outcome:` line under each task, before any task that changes production code starts.
7. Bugfix task identifiers SHALL use Kiro numbering (`1.`, `3.1`) and SHALL trace with `_Requirements: <clause numbers>_`.
8. Bugfix specs SHALL keep the requirements → design → tasks approval gates of WF-001 and WF-002.
9. WHEN the task 1 exploration test passes on unfixed code or fails for a reason other than the bug condition, THE AGENT SHALL record the observed outcome in task 1's `Outcome:` line, stop, and revise the hypothesized root cause in `design.md`, which makes `tasks.md` stale; it SHALL NOT change the test to force the predicted failure.
10. WHEN a preservation test fails after a fix change, THE AGENT SHALL narrow the fix and SHALL NOT edit the preservation test to pass; WHEN narrowing requires a design change, IT SHALL revise `design.md` under ART-005.9.

### INT-002: Spike path

Source: Plan A SPK rows, ELI-25, ELI-26.

**User story:** As a developer, I want to prototype a fuzzy idea before specifying it, so that the requirements record observed behavior instead of guesses.

#### Acceptance criteria

1. WHEN an idea is too unclear to specify, or the developer gives a second non-answer to a contract-level question, THE AGENT SHALL offer a spike before requirements continue.
2. A spike SHALL start from a rough spec, `<intake item>/spike/SPEC.md`, that records the idea verbatim, the smallest end-to-end outcome, and a guessed contract with each guess marked `(guess)`.
3. Spike code SHALL live in the intake item's `spike/` folder for a standalone idea, or on a branch `spike/NNNNN-<title>` for a change to existing code, in a separate worktree when the working tree has changes; it SHALL NOT be built on the current branch.
4. A spike SHALL skip specflow's task, test, and approval gates, SHALL keep input validation at real trust boundaries, and SHALL NOT touch production data, live services, or anything irreversible.
5. After each build, THE AGENT SHALL report what was built and how to run it, then `ASSUMPTIONS:` and `OPEN QUESTIONS:`, and SHALL offer exactly three choices: refine, graduate, or discard. IT SHALL NOT start another build without the developer.
6. Graduating SHALL enter the requirements phase with the observed behavior, not the original guesses. Spike code SHALL NOT be merged, and THE AGENT SHALL offer to delete the spike when the spec completes.
7. Discarding SHALL delete the spike folder or branch after the developer confirms, and SHALL keep the intake item unless the developer asks to remove it.
8. For a user-facing feature, a spike MAY be a sketch instead of running code: user-journey diagrams and static mockups. Each journey step SHALL identify a screen the user sees; each unique screen across the journeys SHALL have exactly one mockup, reused wherever that screen recurs. The navigation index is not a screen mockup. Mockups SHALL be marked as not functional, link the declared user-action edges, and invent no action for a terminal screen. A sketch SHALL follow the same report, choices, and cleanup rules as any spike. THE AGENT SHALL reuse known design-system/UI-pattern and accessibility requirements, ask only material unknowns within the existing spike question budget, and record unasked choices as guesses or open questions. Each mockup SHALL carry a one-line accessibility note (heading level, landmark regions, keyboard entry point).

### WF-001: Workflow phases

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want a predictable phase sequence so that every agent follows the same gates.

#### Acceptance criteria

1. THE WORKFLOW SHALL support the ordered phases `intake`, `requirements`, `design`, `tasks`, `implementation`, `verification`, and `complete`.
2. WHEN a workflow starts or resumes, THE AGENT SHALL determine the current phase from the canonical artifacts and `.specflow.json` before proposing work.
3. THE AGENT SHALL NOT begin the second artifact of the workflow order until the first is approved: design waits for requirements in Requirements-First, requirements wait for design in Design-First.
4. THE AGENT SHALL NOT begin task planning until requirements and design are both approved.
5. THE AGENT SHALL NOT begin implementation until tasks are approved.
6. THE AGENT SHALL NOT mark the spec complete until all required tasks and verification are complete.
7. THE WORKFLOW SHALL support both Kiro orders, Requirements-First and Design-First, chosen at intake (WF-003.10) and recorded once; the first artifact in the order SHALL be drafted from the intake item, the second from the approved first, and tasks from both.
8. A spec on hold or abandoned (STATE-001.7) SHALL keep its derived phase, and THE AGENT SHALL NOT offer it as next work until the developer clears the hold.

Criterion 9: see 00004.

### WF-002: Explicit approval gates

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want control at phase boundaries so that agents do not silently commit me to incorrect requirements or architecture.

#### Acceptance criteria

1. WHEN an artifact is ready for approval, THE AGENT SHALL summarize material decisions, unresolved risks, what it assumed without asking, the recap of any review (raised, resolved, disputed), and the proposed next phase. Approving SHALL NOT turn an assumption into a fact; it stays listed as an assumption.
2. THE AGENT SHALL require an explicit affirmative developer response before recording approval.

Criteria 3-7: see 00004.

8. WHEN a draft carries three or more `(guess)` markers or contract-bearing open questions, THE AGENT SHALL offer to spike, to resolve them now, or to save with them listed under unresolved questions, before asking for approval.
9. An open blocking review finding SHALL block approval of the reviewed artifact until it is fixed or the developer disputes it with a stated reason.

### WF-003: Standard and quick profiles

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want depth proportional to the change while retaining the same artifacts and gates.

Intake question policy (decision 2026-10-04 #1): all intake topics share one profile budget. THE AGENT SHALL read available input and applicable repository instructions first, reuse supplied answers, and ask only remaining unknowns that materially affect this spec. Each independent answer requested counts as one question, even when several could fit in one sentence. Before exceeding quick's usual 0-2 questions, THE AGENT SHALL explain the remaining need and propose standard; it SHALL NOT change the profile without the developer's agreement. If the developer keeps quick, explicitly agree to the extra questions, narrow scope, or defer remaining items under the existing unresolved-marker rules; do not silently omit required information or invent answers. Confirmations are separate from this content-question count and SHALL be combined where ART-002.18 permits.

#### Acceptance criteria

1. THE WORKFLOW SHALL support `standard` and `quick` profiles.
2. THE STANDARD PROFILE SHALL perform repository discovery, complete requirements analysis, technical design, task decomposition, implementation, and verification.
3. THE QUICK PROFILE SHALL perform targeted discovery, concise requirements, a minimal design, tasks, implementation, and regression verification.
4. THE QUICK PROFILE SHALL NOT omit the requirements artifact (`requirements.md` for a feature spec, `bugfix.md` for a bugfix spec), `design.md`, or `tasks.md`.
5. THE AGENT SHALL recommend a profile from requirement clarity, scope breadth, codebase impact, and problem complexity, recommending `quick` only when all four are low, and SHALL explain the basis; the developer MAY override it.
6. Security-sensitive, architectural, data migration, public API, cross-component, concurrency or timing, equivalence-obligation (behavior must match an existing implementation), invented algorithm or predicate, or destructive changes SHALL default to the standard profile.
7. Profiles SHALL apply to bugfix specs as to feature specs; in both profiles, a bugfix spec's discovery SHALL read the code around the defect before `design.md` is drafted.
8. At intake, THE AGENT SHALL recommend a spec type (`feature` or `bugfix`) and explain the basis; the developer MAY override it before the first artifact is created.
9. For a bugfix spec, intake SHALL collect reproduction steps, current behavior, expected behavior, and constraints (behavior or code that must not change), asking one question at a time for each item the developer has not already given.
10. At intake, THE AGENT SHALL recommend a workflow order, `requirements-first` by default and `design-first` only when the input is itself a design or architecture decision, and explain the basis; the developer MAY override it before the first artifact is created, after which the order is fixed.
11. For a feature spec that changes existing code, intake SHALL establish what must not change (behavior, schemas, contracts, configuration), asking only for what the repository and the input do not already show. For work that depends on a system outside the repository, intake SHALL establish how to learn about it (a path, documents, or a description) and what must not change there, asking only material unknowns under the shared intake budget.
12. WHEN repository discovery finds no code or conventions to infer them from, THE AGENT SHALL establish the binding technical constraints (required and prohibited languages, frameworks, and services; security or compliance rules; the test standard), asking only material unknowns under the shared intake budget, and SHALL record them as constraints in the requirements artifact. Each prohibition SHALL carry its reason and the allowed alternative; an unknown one follows the unresolved-marker rules. THE AGENT SHALL reuse an available example file or snippet, or ask for one when it would materially guide the work.
13. WHEN the developer confirms the spec type, workflow order, and profile at the end of intake, THE WORKFLOW SHALL create the spec folder with `.config.kiro` and `.specflow.json` holding those choices, before the first question of the first artifact, so a resume in another tool finds them.
14. The developer MAY raise the profile from `quick` to `standard` at any time, and THE AGENT SHALL propose it when a WF-003.6 trigger appears after intake. Raising the profile SHALL NOT stale an approval by itself; from then on questions and reviews SHALL follow the standard profile, and the change SHALL be recorded in the Q&A log.
15. Repository discovery SHALL classify the repository as holding existing code or as empty by one fixed rule. Existing code means a source file, an application framework configuration, a package manifest with application dependencies, an application source folder, or a declared submodule. Agent and tool folders, specflow's own folders, dependency folders, and build output SHALL NOT count, and a repository with no signal at its root SHALL be searched in nested project folders before it is called empty. THE AGENT SHALL state the result and its basis, and the developer MAY override it.
16. Discovery findings SHALL state their coverage: which paths were read in full, which were skimmed, and which were not looked at. THE AGENT SHALL tell the developer when a submodule is declared but not checked out, and SHALL NOT fetch it.
17. At intake on every host, THE AGENT SHALL read root repository instructions and follow their routing to instructions applicable to the spec's affected paths or conditions, preserving declared scope and precedence. Relevant constraints SHALL name their source file and scope in the requirements artifact; unrelated local rules SHALL NOT become repository-wide constraints. WHEN affected paths are not yet known, THE AGENT SHALL record that coverage limit and revisit applicability as paths become known or change, before drafting or editing the affected work. Only a material conflict between simultaneously applicable rules that declared precedence does not resolve SHALL prompt a question under the shared intake budget.
18. WHEN the input, repository, and its instruction files do not already show them and they materially affect the work, THE AGENT SHALL ask whether tests are written before or after the code and whether to build a thin end-to-end slice first, under the shared intake budget, and SHALL record the answers as constraints.

### WF-004: Resume and handoff

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want another agent to resume from disk so that I can change tools or sessions at any point.

#### Acceptance criteria

1. WHEN asked to continue a spec, THE AGENT SHALL read all canonical artifacts and `.specflow.json` before acting.

Criteria 2-5: see 00004.

6. THE WORKFLOW SHALL NOT require the previous host's transcript, memory store, or session identifier.
7. THE AGENT SHALL summarize the resumed state and intended next action before modifying files.

Criterion 8: see 00004.

### AWS-002: Selective prompt loading

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a runtime agent, I want phase-specific references so that the full upstream corpus does not consume context unnecessarily.

#### Acceptance criteria

Criterion 1: see 00003.

2. THE RUNTIME SKILL SHALL instruct the agent to read only the references relevant to the current phase and selected profile.

Criteria 3-5: see 00003.

### VAL-002: Completion verification

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want completion based on evidence so that checked tasks reflect working software.

#### Acceptance criteria

1. A task SHALL be checked only after its stated verification succeeds or the developer explicitly accepts an exception.
2. Verification SHALL include tests and checks proportionate to the changed behavior.
3. The workflow SHALL map failed verification to affected tasks and requirements.
4. The workflow SHALL not mark the spec complete while required tasks remain unchecked.

Criterion 5: see 00004.

### SEC-002: Project data safety

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want the workflow to preserve my work and secrets.

#### Acceptance criteria

1. THE RUNTIME SKILL SHALL not delete or replace an existing spec directory without explicit approval.
2. THE RUNTIME SKILL SHALL not store secrets or copied environment values in spec artifacts, the Q&A log, or state; a secret in a developer's answer SHALL be left out of the log and the omission noted.
3. THE RUNTIME SKILL SHALL preserve unrelated working-tree changes.
4. Destructive cleanup or migration SHALL identify exact targets and require explicit authorization when recovery is uncertain.

Criterion 5: see 00004.

## Non-functional requirements

**Performance**

- Only current-phase references should enter model context.

**Usability**

- A developer shall be able to start or resume using natural language, without remembering host-specific commands.
- Status summaries shall state the current phase, approval state, stale artifacts, next action, and blocking questions.
- Clarifying questions shall be asked one at a time.

**Compatibility**

- Unknown hosts may use the runtime skill if they implement Agent Skills, even if they do not install the full plugin manifest.
