# Requirements phase

Load this reference to draft or revise `requirements.md`, with `references/aws/requirements.md`, reading only the AWS passages marked with the active profile or `[both]`. Questions follow the shared dialogue rules in `references/artifact-contract.md` (`## Shared dialogue`); the approval summary is the one defined there. This file adds the question bank, the drafting rules, and the gates of this phase. A bugfix spec writes `bugfix.md` instead; its rules are added to this file with the bugfix instructions.

## Input

- [SR-REQ-030] `requirements.md` is the requirements artifact; a plan, a design note, a PRD, or a discovery document given as input is turned into it, never kept beside it as a second source.
- [SR-REQ-033] Read the input in this order: the intake item, then a file the developer names by one explicit path, then the conversation.
- [SR-REQ-031] When there is no intake item, say so and offer to save the input as one under `<root>/intake/new/`; the offer is advisory, and work goes on when the developer declines. The log then goes to `<root>/intake/processed/<spec-folder>/qa-log.md` on the first question.
- [SR-REQ-034] Pull out of the input the problem, the requirements, the constraints, the components it depends on, and the acceptance criteria, and ask nothing it already answers.
- [SR-REQ-032] A spike's `SPEC.md` and its report count as elicited input: start from what the build showed.
- [SR-REQ-007] When a spike started during requirements converges, fold its `ASSUMPTIONS:` into `## Assumptions` and the Q&A log, and resume these questions where they stopped; the spike's own graduate step is skipped, since requirements are already under way.
- [SR-REQ-012] The spike is the spike path of this skill (`references/phases/intake.md`), not another tool.

## Question bank

- [SR-REQ-001] Choose the questions from the bank below by profile: under `quick`, only the ones whose answer the input does not give and that change scope or behavior; under `standard`, every topic the input leaves open.
- [SR-REQ-003] Ask about 0 to 2 questions under `quick` and about 3 to 12 under `standard`, as the profile reference says; the range is guidance, never a target.
- [SR-REQ-013] When in doubt, ask. Never assume a requirement.

The bank, one topic per question:

- [SR-REQ-022] Problem: is this a repeated pain, a preventive change, an outside demand, or something else?
- [SR-REQ-023] Scope: where does it stop? Prompt with the adjacent features the input or the repository suggests; what falls outside goes under `## Out of scope`.
- [SR-REQ-024] Success: how will we know it works? Steer the answer to a measurable or behavioral test; a manual checklist needs an accepted exception at verification.
- [SR-REQ-025] Constraints, multi-select: stay backwards-compatible, no new dependency, a performance bound, or other.
- [SR-REQ-048] Under `standard`, when the input does not show it: does this block other work, and does it need another spec finished first? A yes goes into a `Blocks:` line, and a prerequisite spec into the `Depends on:` line, in the header.
- [SR-REQ-026] Decomposition: is this one spec or several? Parts that can ship apart become separate specs, each with its own number and intake item.
- [SR-REQ-027] Risks, open-ended, prompted by category: scope, dependency, and outside systems.
- [SR-REQ-028] Edge cases of the domain: what happens on empty input, failure, limits, or concurrent use? Each answer becomes an unwanted-behavior criterion (`IF ... THEN THE SYSTEM SHALL ...`).
- [SR-REQ-029] Contradiction: two answers that conflict get one question with the choices "X wins", "Y wins", and "they do not conflict".

### Answers that are not answers

- [SR-REQ-005] A non-answer is "I don't know", "whatever you think", "I'd need to see it", or the like. It decides nothing.
- [SR-REQ-006] After a second non-answer to a question that bears on the contract, offer three choices: spike it, keep answering, or park it as an open question under `## Unresolved questions`.
- [SR-REQ-004] When the developer says "that's enough", stop asking and draft from what exists; every unanswered topic goes under `## Unresolved questions`.
- [SR-REQ-002] Under `standard`, after the last question, check all answers against each other for contradictions, and ask one resolution question per contradiction found.

## Drafting

- [SR-REQ-008] Write `requirements.md` in the Kiro-compatible shape of `references/artifact-contract.md`: stable `REQ-` IDs, user stories, and EARS acceptance criteria.
- [SR-REQ-036] Read `templates/requirements.md` before drafting, and keep every section it has, in its order and under its headings.
- [SR-REQ-037] Never copy structure from another spec in the repository; the template is the one source of the shape. Keep the repository's own tone in the prose.
- [SR-REQ-035] One template serves every spec; the profile sets the depth, not the shape.
- [SR-REQ-045] Under `quick`, keep the requirements concise; the design and the tasks hold what the requirements need not say.
- [SR-REQ-009] Write into the spec folder intake created; create it first if it is missing, with `.config.kiro` and `.specflow.json` as intake does.
- [SR-REQ-043] The spec folder is `NNNNN-<title>` with the fixed artifact names; no version suffix, no other file name.
- [SR-REQ-044] A separate capability gets its own spec and a new number, never a version of this one.
- [SR-REQ-015] The header holds `Sources:`, and `Supersedes:`, `Blocks:`, and `Depends on:` when they apply. The profile and the date belong to `.specflow.json` and the Q&A log, not the header.
- [SR-REQ-016] `## Purpose` states the problem; its length follows the profile.
- [SR-REQ-046] The actors of the problem appear in the user stories, and the success measures in the acceptance criteria.
- [SR-REQ-038] Each capability becomes one `REQ-NNN` with a user story and EARS criteria.
- [SR-REQ-020] Success criteria become testable EARS acceptance criteria, measurable wherever a number exists.
- [SR-REQ-050] Each requirement carries a `Source:` line naming the idea, a Q&A entry, or a discovery finding. Content with no source is marked `(guess)` or listed under `## Assumptions`, never written as a requirement. An option the developer did not pick becomes neither a requirement nor an exclusion.
- [SR-REQ-051] A requirement states the behavior needed, not a solution. A named technology or mechanism appears only as a stated constraint, with its source; a design idea the developer offers goes to the design, noted in the Q&A log.
- [SR-REQ-017] Every requirement is required; there are no priority tiers. A nice-to-have becomes a requirement, moves to `## Out of scope` with a note, or becomes its own spec, as the developer chooses.
- [SR-REQ-018] `## Out of scope` lists what the spec leaves out, each with its reason.
- [SR-REQ-019] Constraints go to `## Non-functional requirements`, or to `## Assumptions` when they are taken rather than required.
- [SR-REQ-021] `## Risks` lists the risks known now (scope, dependency, outside), one line each with impact, likelihood, mitigation, and fallback.
- [SR-REQ-039] Mark every contract detail the developer did not give `(guess)` until they confirm it. Never resolve an ambiguity silently.
- [SR-REQ-011] Open questions go under `## Unresolved questions`, each with what would resolve it.
- [SR-REQ-047] A glossary goes into `## Purpose` or `## Scope`, references to outside material into the design, and open questions under `## Unresolved questions`; there are no appendix sections.
- [SR-REQ-010] Write no placeholder (`TBD`, `TODO`, `???`, bare `N/A`), and leave out a section that does not apply.
- [SR-REQ-040] When the draft passes about 200 lines or holds loosely coupled parts, propose splitting it into separate specs.
- [SR-REQ-049] While drafting, check each requirement against the triggers that force `standard`: security-sensitive, architectural, a data migration, a public API, cross-component, concurrency or timing, an equivalence obligation, an invented algorithm or predicate, or a destructive change. In a `quick` spec, a trigger draws the proposal of SR-SKL-013.
- [SR-REQ-052] In a Design-First spec, draft the requirements from the approved design and the intake item, and give each requirement a `Design:` line naming the design elements that realize it; the design is not edited.

## Bugfix specs

- [SR-REQ-053] A bugfix spec writes `bugfix.md` from `templates/bugfix/bugfix.md`, never `requirements.md`, and keeps Kiro's shape as it is: `## Introduction` (what breaks, where, the impact, then the `Sources:` line), and `## Bug Analysis` with `### Current Behavior (Defect)`, `### Expected Behavior (Correct)`, and `### Unchanged Behavior (Regression Prevention)`. Draft it from the four bug inputs intake collected; the constraints become the unchanged-behavior clauses. It passes through the same approval as `requirements.md`, and the design waits for it.
- [SR-REQ-054] Write each clause on one line in its section's pattern and numbering: `1.x WHEN <condition> THEN the system <incorrect behavior>`, with no `SHALL`; `2.x WHEN <condition> THEN the system SHALL <correct behavior>`; `3.x WHEN <condition> THEN the system SHALL CONTINUE TO <existing behavior>`. Number each section from `.1`, with no gap.

## Before approval

- [SR-REQ-041] Before saving, walk the template's headings against the draft, then run `validate_spec.py validate <spec-dir> --phase requirements` and fix what it reports.
- [SR-REQ-042] When the draft carries three or more `(guess)` markers or contract-bearing open questions, offer, before asking for approval: spike them, resolve them now, or save with them listed under `## Unresolved questions`.
- [SR-REQ-014] Then show the shared approval summary and ask for approval. Design starts only after the developer approves the requirements.
