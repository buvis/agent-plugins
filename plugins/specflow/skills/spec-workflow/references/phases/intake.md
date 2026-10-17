# Intake

Load this reference for a new idea or a bug, before the spec folder exists. Questions follow the shared dialogue rules in `references/artifact-contract.md` (`## Shared dialogue`), loaded before the first question; this file adds what intake asks and discovers. The intake procedure in `references/artifact-contract.md` (create, scan again, move, file input) is how the item is written.

## The input

- [SR-INT-001] When the developer starts from a free-text idea, save it first, verbatim, as `idea.md` of a new intake item under `<root>/intake/new/`, before any question or discovery. The item claims the spec number.
- [SR-INT-002] Look for the input in this order: what the developer names in the request, then an intake item under `<root>/intake/new/`, then an existing spec folder, then the conversation. Use the first that holds it, and say which one you used. An item in a group folder keeps that group when it moves to `processed/`.
- [SR-INT-057] Take an input file only from one explicit path. When the path is missing, or the name matches more than one file, ask which one; never pick a match. Copy the file into the intake item; for one that is binary, too large to read, or outside the repository, record its location in `idea.md` and say what could not be read.
- [SR-INT-003] Pull the problem, the requirements, the constraints, the success criteria, and the open questions out of the input, and skip every question the input already answers.
- [SR-INT-014] A new item's number is one more than the highest five-digit prefix in use; get it from `validate_spec.py next-number`, never by counting yourself.
- [SR-INT-019] The number scan covers `<root>/intake/new/`, `<root>/intake/processed/`, the specs folder, and the `numberScan` folders of `.agents/specflow.json`, and nothing else.
- [SR-INT-020] Right after writing a new item, run `validate_spec.py validate <item> --phase intake`. On a `number-clashes` error that names your item, rename your own new item to the number `next-number` now prints, before anything cites it. Never rename an item someone else made.

## Spec type, workflow order, and profile

- [SR-INT-060] Recommend a spec type, `feature` or `bugfix`, and a workflow order, `requirements-first` by default and `design-first` only when the input is itself a design or architecture decision, each with its basis. The developer may override either until the first artifact exists; after that the order is fixed.
- [SR-INT-004] Rate four dimensions low, medium, or high from the input and the discovery: requirement clarity, scope breadth, codebase impact, and problem complexity.
- [SR-INT-005] Recommend `quick` only when all four are low; otherwise `standard`. A change that is security-sensitive, architectural, a data migration, a public API, cross-component, about concurrency or timing, must match an existing implementation, invents an algorithm or a predicate, or is destructive is `standard` unless the developer explicitly decides otherwise.
- [SR-INT-017] Explain each rating with this repository's facts, for example "codebase impact low: one function in `src/export.py`", never with examples from another project.
- [SR-INT-006] Give the recommended profile with a one-line basis, and let the developer override it; the choice goes into `.specflow.json` as `profile`. Going along with a recommended profile may settle the profile; it never counts as an approval.
- [SR-INT-015] The profile sets the depth: how much you discover and how many questions you ask grow with what the work needs, not with a fixed list.
- [SR-INT-007] In every phase, hold the work to the active profile's expectations in `references/profiles/standard.md` or `references/profiles/quick.md`: its question range, its discovery depth, and the size of what it writes.

Raising `quick` to `standard` later, and proposing it when a trigger appears after intake, are rules of `SKILL.md` (SR-SKL-005 and SR-SKL-013); they apply here too.

### The intake budget

- [SR-INT-059] All intake topics share one question budget: what must not change, outside systems, constraints, examples, working practices, conflicts, and the input itself. Read the input and the applicable instructions first, reuse every answer already given, and ask only unknowns that materially affect this spec, the most consequential first. Each independent answer you ask for counts as one question, even when several would fit in one sentence, and the count never restarts per topic; the progress line counts the whole remaining queue. Before `quick` needs more than about two questions, explain what remains and propose `standard`; raise it only when the developer agrees. If the developer keeps `quick`, agree with them on the extra questions, a narrower scope, or the questions deferred as unresolved. Confirmations are not counted, and never carry a hidden content question.

### Creating the spec

- [SR-INT-052] When the developer confirms the spec type, the workflow order, and the profile, create the spec folder before the first question of the first artifact: `.config.kiro` with a new UUID as `specId`, `workflowType`, and `specType`, and `.specflow.json` with `schemaVersion` 1, `specId` equal to the folder's name, `specType`, `profile`, `workflowOrder`, `workflowVersion` (the value of `WORKFLOW_VERSION` in `scripts/specflow_helper/__init__.py`), and the three artifact records with status `missing`. A resume in another tool then finds the three choices. Without Python 3, write the folder and `.config.kiro` only, and log the three choices in the intake item's `qa-log.md`.

The folder name is the intake item's number and a kebab-case title. The intake item stays in `new/` until the requirements artifact is first written (procedure step 3). The spec is then in its first artifact's phase, with that artifact missing.

## Repository discovery

- [SR-INT-053] Classify the repository by one fixed rule. Existing code means a source file, an application framework configuration, a package manifest with application dependencies, an application source folder, or a declared submodule. Agent and tool folders (`.kiro/`, `.claude/`, `.codex/`, `.agents/`), the workspace root and the specs folder, dependency folders, and build output never count. With no signal at the root, search nested project folders, three levels down at most, before you call the repository empty. State the result and its basis; the developer may override it.
- [SR-INT-008] Under `standard`, run the full discovery below; under `quick`, a targeted one over the files and conventions the change touches. An empty repository has no code to scan.
- [SR-INT-009] Pattern scan: look for existing implementations similar to what the input asks for.
- [SR-INT-010] Dependency map: name the existing modules the work touches.
- [SR-INT-011] Conventions: note naming, file layout, and the testing approach in use.
- [SR-INT-012] Integration surface: name the files and functions that would change.
- [SR-INT-016] Never ask what the code can answer. State the finding and its source instead.
- [SR-INT-018] On existing code, when the scan leaves the integration points open, ask about them in one multi-select question whose choices come from the scan.
- [SR-INT-013] Findings feed the artifacts: each one a requirement relies on goes under `## Assumptions` with its source, and the design takes them into `## Context and constraints`. There is no separate discovery document.
- [SR-INT-054] Append one `## Discovery <YYYY-MM-DD>` block to the intake item's `qa-log.md`: the classification and its basis; the coverage, as the paths read in full, the paths skimmed, and the paths not looked at; and numbered findings (`D1`, `D2`, ...) that requirements can cite as their source. Tell the developer when a submodule is declared but not checked out, and never fetch it.
- [SR-INT-055] Read the root instruction files present (such as `AGENTS.md`, `CLAUDE.md`, and root steering) on every host, whether or not the host loads them itself. Resolve their explicit imports and pointers once per file, and follow their declared routing and the nested instructions for the affected paths. Keep each rule's scope: a rule for one path, condition, or explicit request is not repository-wide, and a rule you can discover is not therefore active. Use the precedence the files declare, including scoped overrides, and invent no ranking between differently named files; this session's own instructions still govern. Record each applicable constraint with its file and scope. Ask only when two rules that apply at the same time still conflict after their declared precedence. While the affected paths are unknown, start with the root-wide rules and note scoped coverage as incomplete. Log skipped, unreadable, and not-yet-applicable sources in the discovery coverage; an unreadable rule that applies is unknown, not satisfied. Do not read unrelated subtrees to claim full coverage.

Revisiting instruction scope when the affected paths become known or change is a rule of `SKILL.md` (SR-SKL-014).

## What intake establishes

- [SR-INT-050] For a feature that changes existing code, establish what must not change (behavior, schemas, contracts, configuration), asking only for what the repository and the input do not show. For work that depends on a system outside the repository, establish how to learn about it (a path, documents, or a description) and what must not change there.
- [SR-INT-051] When discovery finds no code or conventions to infer them from, establish the binding technical constraints: required and prohibited languages, frameworks, and services; security or compliance rules; and the test standard. Each prohibition carries its reason and the allowed alternative; an unknown one becomes an unresolved question. Record them as constraints in the requirements artifact. Reuse an example file or snippet that is available, or ask for one when it would materially guide the work.
- [SR-INT-056] When the input, the repository, and its instruction files do not already show them and they materially affect the work, ask whether tests are written before or after the code and whether to build a thin end-to-end slice first. Record the answers as constraints; supplied ones are reused, never asked again.
- [SR-INT-061] For a bugfix, collect the reproduction steps, the current behavior, the expected behavior, and the constraints (behavior or code that must not change), asking one question at a time and only for an item the developer has not given. Under either profile, read the code around the defect before the design is drafted.

Each of these questions draws on the intake budget above.

## Spike path

A spike answers a fuzzy idea with a throwaway build instead of more questions. It lives in the intake item, before any spec exists.

### Entry and rough spec

- [SR-INT-021] Offer a spike at intake when the idea is too unclear to specify, or during requirements after the developer's second non-answer to a contract-level question: spike it, keep answering, or park the item with its open questions under unresolved questions. The developer may also ask for one directly ("spike this", "prototype this idea", "a throwaway prototype"). The spike path is part of this skill, chosen before requirements.
- [SR-INT-022] A spike needs only Git and a host where the developer attends the build; it holds the same way on every host.
- [SR-INT-024] The rough spec is a guess and the build is how the guess gets tested: iterate with the developer until the contract is real, then graduate. Nothing built in a spike ships.
- [SR-INT-025] Write the rough spec as `spike/SPEC.md` in the intake item, from `templates/intake/SPEC.md`; it moves with the item.
- [SR-INT-026] `SPEC.md` records the developer's idea verbatim.
- [SR-INT-027] `SPEC.md` states the smallest outcome that demonstrates the idea end to end.
- [SR-INT-028] `SPEC.md` lists the guessed contract (inputs, outputs, interfaces), each guess marked `(guess)`.
- [SR-INT-029] When the developer gave only a phrase, ask at most one question, the most consequential, and guess the rest.
- [SR-INT-030] Spend about ten minutes on the rough spec, with no polish.

### Build

- [SR-INT-031] Build the smallest end-to-end demonstration directly. The task, test, and approval gates of specflow do not apply to a spike.
- [SR-INT-032] A standalone idea builds inside the intake item's `spike/` folder.
- [SR-INT-033] A change to existing code builds on a branch `spike/NNNNN-<title>`, in a separate worktree when the working tree has changes, and never on the current branch.
- [SR-INT-034] Never touch production data, live services, or anything irreversible from a spike.
- [SR-INT-035] Keep input validation at real trust boundaries; only specflow's own verification and approval gates are skipped.
- [SR-INT-036] Aim for about twenty minutes of building. When it will not demonstrate within about an hour, stop, report what you have, and carry the open questions into the requirements phase.

### Sketch form

- [SR-INT-058] For a user-facing feature the build may be a sketch instead of running code. `spike/journey.md` holds one Mermaid flowchart per user type: each node a screen the user sees, each edge a user action. Use the same screen ID wherever a screen recurs, across user types too; a distinct visible state may have its own ID. `spike/mockups/` holds exactly one `<screen-id>.html` per unique screen ID, and `index.html` for navigation only (`index` is never a screen ID); no mockup belongs to no screen. Every mockup is self-contained, with no script and no network resource, says "mockup, not functional" at the top, and carries a one-line accessibility note (its heading level, landmark regions, and keyboard entry point; an unknown target level stays open, and the note claims no conformance). Each declared action links, in the edge's words, to its target's file; a terminal screen gets no invented action, and no screen shows a feature the rough spec lacks. Reuse the design-system, UI-pattern, and accessibility requirements the input and the instructions already give; ask only material unknowns, from the same question budget. For phrase-only entry the one question covers the rough spec and the sketch together; record the remaining choices as `(guess)` or open questions in `SPEC.md` and in the report. After writing or changing the mockups, and before showing them, run `validate_spec.py validate <intake item> --phase intake` and fix every `sketch-screens` error.

### Report and the three choices

- [SR-INT-037] After each build, report first what was built and how to run it, in two or three lines with the run command.
- [SR-INT-038] Then `ASSUMPTIONS:`, one line per choice you made where `SPEC.md` was silent.
- [SR-INT-039] Then `OPEN QUESTIONS:`, what the build surfaced.
- [SR-INT-040] Then ask one question with exactly three choices: refine, graduate, or discard.
- [SR-INT-041] Refine: fold the answers into `SPEC.md` and rebuild in place, back to the build.
- [SR-INT-042] Never start another build, or chain refine cycles, without the developer; their look at each build is the point.
- [SR-INT-043] Discard: delete the spike folder or branch after the developer confirms the exact target. The intake item stays in `new/` unless the developer asks to remove it.

### Graduate

- [SR-INT-023] Graduating hands the spike to the requirements phase of this same skill.
- [SR-INT-044] Graduate: enter the requirements phase for the spec `NNNNN-<title>`; the intake item, with `spike/`, moves to `processed/` when the requirements artifact is first written.
- [SR-INT-045] The requirements record the behavior the spike showed, not the original guesses.
- [SR-INT-046] The requirements' `Sources:` line names the intake item and the spike folder or branch.
- [SR-INT-047] The real implementation goes through the design, tasks, implementation, and verification phases, built anew; nothing is copied over from the spike.

Spike code never merges. At verification, `references/phases/verification.md` checks that no spike path or branch is part of the change and, at `complete`, offers to delete the spike; it is not repeated here.
