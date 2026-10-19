# Cross-spec readiness review

The `review specs` intent. Load `references/review/core.md` first; this file adds the target, the ground rules of a review across specs, the spec map, lenses A to H, the verdicts, the report, and the reshapes. The walkthrough, the card, the picker, and the recap are the core's.

## Target and position

- [SR-RVX-001] The target is every spec in the configured specs folder whose derived phase is not `complete`, together with every item under `<root>/intake/new/`. No other tree is read as a target.
- [SR-RVX-002] The review works at two levels: each spec as an artifact set an agent on any host can resume and implement from disk alone, and the set as a whole, whose sum should leave the project in the best shape to keep building.
- [SR-RVX-003] Its place is after the task plans are drafted and before their approval and implementation; it is the last look at the set before work starts.
- [SR-RVX-004] It is not a requirements review, a design review, or a code review: the requirements and design reviews are sibling intents of this skill, and this one stays with cross-spec fit and task readiness, never re-litigating the WHAT or the HOW of one spec.
- [SR-RVX-005] The law is this skill's `references/artifact-contract.md`, its `templates/`, and `references/validation-rules.md`; compliance is judged against them, never against another spec in the repository.
- [SR-RVX-008] When the specs folder holds no spec that is not complete and `<root>/intake/new/` is empty, say so and offer to create a spec; there is nothing to review.
- [SR-RVX-009] When the developer asks for a report only, write the report and skip the walkthrough; the report then holds the findings with no decisions applied.
- [SR-RVX-076] Grounding (lens D) runs one spec per isolated sub-task where the host can run them, each returning findings in the card's shape; where it cannot, ground the specs one at a time, writing a short summary of each before the next, so the later specs are judged as carefully as the first. The set lenses E to H need every spec in one context and never run in a sub-task.

## Ground rules of this review

- [SR-RVX-010] A blocking finding names the mechanism it prevents: a gate the set cannot pass (an approval refused by the validator or the markers), a resume that fails on another host (a task an agent cannot carry out from `tasks.md` alone), an implementation that cannot start (a prerequisite never built), or a goal reversed. A finding that names no mechanism is non-blocking.
- [SR-RVX-011] The law is live: read the templates and contracts of this skill at review time, never from memory and never from other specs, which drift.
- [SR-RVX-012] Fix the spec, not the gate: never weaken the validator, a check, an approval gate, or a marker rule to admit a spec that fails it.
- [SR-RVX-013] Verify grounding, do not trust prose: a claim about the repository (a file, a symbol, a behaviour) is checked against the repository before it is believed.
- [SR-RVX-007] The grounding check searches the repository with whatever the host offers (a search tool, a command runtime, reading files); no particular tool is required, and the recap says which was used.

## Inventory and map

- [SR-RVX-014] Inventory the specs with their derived phase and the approval state of each artifact, as `validate_spec.py status --json` holds them, and the intake items under `new/` and `processed/`.
- [SR-RVX-015] Hygiene: each spec folder is `NNNNN-<title>` (five digits, a lowercase kebab-case title, no version suffix) and holds the artifacts its phase needs; a stray file or a misnamed folder is a finding.
- [SR-RVX-016] Spec numbers are unique across the specs folder and the intake tree, and a spec and its intake item share one number; a clash is a blocking finding, since the number is the link between them.
- [SR-RVX-017] The citation check runs `scripts/check_links.py` and keeps the findings whose file belongs to a spec under review or an intake item: a dangling five-digit citation is blocking (a resume follows it and stops), unless the target is a spec the citing spec itself says it will create (a forward reference), or the citing line carries `link-ok:`, which waives it.
- [SR-RVX-006] `python3 scripts/check_links.py --root <repository> --json` resolves every five-digit citation in the specs folder and the intake tree against the spec folders and intake items, reports dangling ones as findings and unreadable files as scan errors, and warns on home paths, absolute paths, and `[[...]]` links without resolving them. A host with no command runtime skips it and says so.
- [SR-RVX-018] Load the templates (`templates/requirements.md`, `templates/design.md`, `templates/tasks.md`, and the bugfix ones) before lens A, since they are what the artifacts are checked against.
- [SR-RVX-019] The comprehension pass builds the spec map, one row per spec: number, title, profile, phase, the approval status of each artifact, the subsystems and files it touches, and its dependencies, stated and inferred; and keeps the confusion notes of the core.
- [SR-RVX-020] Lenses E to H run across the whole set in one context, after the per-spec lenses A to D.

## Lenses

### A. Compliance

- [SR-RVX-025] The spec folder is `NNNNN-<title>`, five digits, zero-padded, unique.
- [SR-RVX-026] Each artifact is checked against its template: the headings present, in order, worded as the template words them, with `design.md` keeping every section; the fit of the profile is judged too, since a multi-component change written under `quick` hides the structure the tasks need.
- [SR-RVX-027] Requirement and task IDs are stable and unique (`REQ-NNN`, `T-NNN`, or Kiro's numbering), since every trace keys on them.
- [SR-RVX-028] Every task names the requirement IDs it satisfies and states its own verification; a task without them makes the implementer invent both.
- [SR-RVX-029] The prose is plain engineering prose; narrative or role-play framing is a finding.
- [SR-RVX-030] A template stub or a placeholder left in an artifact is blocking: the implementer would guess.
- [SR-RVX-031] A spec whose task plan spans more than one subsystem, or more phases than it can verify one at a time, is a reshape candidate for lens F.

### B. Executability

- [SR-RVX-032] Every acceptance criterion, completion criterion, and `Verify:` line is checked by a command, a test, or a file check; a manual check is non-blocking when it is recorded as an exception the developer accepts, and blocking when it hides inside a criterion.
- [SR-RVX-033] Contracts are exact and final wherever a task names one: names, enum values, type shapes, signatures, thresholds, and file kinds. An agent implements from the task text alone and never sees this conversation; a contract that reads two ways becomes two implementations.
- [SR-RVX-034] A task that depends on a credential, an external account, an interactive login, or a service the host cannot reach is a verification risk, raised as a finding with the fallback the developer chooses.

### C. Coherence

- [SR-RVX-035] Every requirement traces to a design element and every design element back to a requirement (the `## Requirement traceability` table); a hole on either side is a finding.
- [SR-RVX-036] Every requirement is cited by a task and every task cites a requirement; a requirement no task builds fails late, and a task no requirement motivates is scope creep.
- [SR-RVX-037] The task dependency graph is acyclic and consistent with the order of the plan, and names only tasks of the plan or criteria of a spec the requirements name in `Depends on:`.
- [SR-RVX-038] Each requirement has its acceptance criteria in EARS form, and every success measure is a number or an observable behaviour, never an adjective.
- [SR-RVX-039] The scope boundary is crisp: exclusions stated under `## Out of scope`, and a nice-to-have phrased as a mandate tightened or moved. One value per name across the artifacts of a spec is the core's rule, applied here to the set.

### D. Grounding

- [SR-RVX-040] Every file, symbol, flag, and command a spec names exists in the repository now; a renamed function sends the implementer into invented locations.
- [SR-RVX-041] The placement in `design.md` matches the repository's real layout (the folders, the package names).
- [SR-RVX-042] The work is not already done: check the complete specs, the recent history, and the code for the spec's core surface.
- [SR-RVX-043] Spot-check the assumptions each spec states about current behaviour against the code.
- [SR-RVX-044] A spec that overlaps a spec in `implementation` is a finding: two agents would edit the same surface at once.

### E. Collisions

- [SR-RVX-045] Duplicate or overlapping scope under different names, across specs.
- [SR-RVX-046] Contradictory requirements across specs: one pins a behaviour, another pins its opposite.
- [SR-RVX-047] Same-file contention: two specs reshaping the same module with incompatible end shapes.
- [SR-RVX-048] Cross-invalidation: a spec that names code another spec deletes or renames is stale by construction when it runs; the finding fixes the text now, or merges the two. Terminology drift across the set is the core's rule, applied to every pair of specs.

### F. Sizing and regrouping

- [SR-RVX-077] Every spec costs three artifacts and three approval gates. Too small, and the gates cost more than the work: prefer the `quick` profile, or a merge with a neighbour of the same subsystem. Too big, and the review quality of each gate drops: split into new specs.
- [SR-RVX-049] Too big: a spec that spans more than one subsystem, more phases than it can verify one at a time, or a task plan the sizing checks cannot bound, is split at its loosely coupled seams into new specs, each self-contained with its own requirements, design, tasks, and verifiable end state.
- [SR-RVX-050] Too small: a single mechanical change with no test surface of its own first draws the `quick` profile; a merge into a cohesive neighbour of the same subsystem needs an explicit migration the developer approves, and unrelated scopes are never merged to save ceremony.
- [SR-RVX-051] Mixed concerns: a feature bundled with an unrelated fix is split, since the unrelated half draws findings forever.
- [SR-RVX-081] Task size follows the five sizing checks of `references/phases/tasks.md` (SR-TSK-011): the lens flags a task that bundles independent outcomes, a task whose verification needs an edit outside its file slice that no listed dependency covers, and a split piece that cannot build or pass its check without an unfinished sibling, each cited with the task ID and the failing check. A coupled task that builds and verifies as one outcome (a signature and its callers, a module and its export) is never flagged by its file count.

### G. Gaps

- [SR-RVX-052] Producer and consumer holes: a spec consumes an artifact, an API, or a file that neither the code nor any other spec produces, checked across every spec whatever its number.
- [SR-RVX-053] Missing enablers: infrastructure a spec assumes and nobody builds.
- [SR-RVX-054] Half-migrations: a spec introduces pattern B beside pattern A and nothing migrates the rest.
- [SR-RVX-055] A bugfix spec without the regression test that would catch the defect's return: its `tasks.md` must hold the exploration test.
- [SR-RVX-056] Cleanup debt: a spec deprecates something and no spec removes it.
- [SR-RVX-057] Strategic gaps: goal-level work no spec covers is noted in the report with the suggestion of a new intake item; the review invents no spec.

### H. Goal alignment and end state

- [SR-RVX-058] Read the goal sources first: the README, the repository's instruction files (`AGENTS.md` or the host's steering files), the recent history, and the complete specs.
- [SR-RVX-059] Per spec: does it move the goal? Flag the underminers: a spec that re-adds what the roadmap or another spec removes, one that instructs a violation of the repository's own rules, or speculative scope beyond its intake item.
- [SR-RVX-060] Traceability to the intake item named in `Sources:`: every must-have of the original carried over (a dropped one is blocking) and no scope invented beyond it.
- [SR-RVX-061] End-state simulation: with every spec complete, describe the repository. One pattern per problem, no orphaned deprecation, documentation current; what the set leaves half-finished is named in the report.

## Severities and verdicts

- [SR-RVX-021] Blocking mechanism, wrong contract lock-in: a vague contract that lets the next agent, implementing from `tasks.md` alone, invent a plausible but wrong shape that only a review of the whole spec would catch.
- [SR-RVX-022] Blocking mechanism, verification dispute: an ambiguous acceptance criterion that the implementer and the verifier read differently, so the completion checks of the verification phase cannot settle it.
- [SR-RVX-023] Blocking mechanism, goal reversal: a spec that undoes what the project or another spec is building toward.
- [SR-RVX-062] Each spec gets a verdict: READY (implement as is), FIX (blocking findings resolvable by edits, READY once applied), RESHAPE (a merge or split is needed), or NOT READY with its reason (stale, duplicate, dependent on work nobody has planned, or undermining the goal). The artifact statuses stay what `status` derives.
- [SR-RVX-063] The set verdict is GO only when every spec under review is READY after the apply pass, with no blocking finding open and no reshape pending; anything else is NO-GO with the shortest list of actions that reaches GO. A waiver is the developer's explicit acceptance of a blocking finding, recorded with its reason in the report's decisions-applied section; a waived finding no longer forces NO-GO, and the verdict then reads "GO (developer waived: ...)". A NO-GO is never softened.

## The report

- [SR-RVX-024] The report is written to `<root>/reviews/YYYY-MM-DD-cross-spec-review.md` from `templates/cross-spec-review.md`, before the walkthrough; it is never written inside a spec folder or an intake item.
- [SR-RVX-068] Its sections are the template's: the verdict, the spec map, the findings by severity with each spec, lens, location, and the mechanism of a blocking one, the reshapes, the gaps, the end state, and the decisions applied, filled during the walkthrough.
- [SR-RVX-080] The minutes of this review are the report's decisions-applied section, plus one line per finding in the intake log of each spec the finding touched, in the core's minutes shape under `## Review: specs <date>`, so a later review of that spec finds the dispute.

## Reshapes

- [SR-RVX-064] A reshape proposal (a merge, a split, a move between specs) is walked as a finding with the core's card: merge the specs; keep them separate with a cross-reference; split one into new specs.
- [SR-RVX-065] A merge needs the developer's explicit approval, lands in the lowest number of the specs merged, and keeps the absorbed specs' intake items; the absorbed spec folders are removed only when the developer chooses deletion.
- [SR-RVX-066] A split keeps the original number for the first part; each further part gets a new number from `next-number`, its own intake item under `<root>/intake/processed/` naming the original as its source, and its own artifacts.
- [SR-RVX-067] A reshape never touches a spec in `implementation` or `complete`, moves rather than copies, needs the developer's approval before any folder is created, renamed, or removed, and ends with `validate_spec.py validate` on every spec it touched.
