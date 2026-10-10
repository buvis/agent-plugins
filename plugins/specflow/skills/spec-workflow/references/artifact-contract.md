# Artifact contract

The shapes every host reads and writes. The templates in `templates/` are filled copies of these shapes. Paths are the same on every host.

## Spec directory

```text
<specs folder>/NNNNN-<title>/
├── requirements.md     # or bugfix.md for a bugfix spec
├── design.md
├── tasks.md
├── .config.kiro        # Kiro's type marker
└── .specflow.json      # specflow state
```

- The specs folder is `.kiro/specs/` by default, or the folder `specsDir` names in `.agents/specflow.json`. Read and write it directly. Never create, repair, or depend on a `.kiro/specs` link; making that link so Kiro IDE lists the specs is the repository's own setup, and it must be a link, never a copy.
- `NNNNN` is the spec number of the intake item. The title is lowercase kebab-case, stable, and filesystem-safe. A number is never reused.
- The folder name is chosen once. Renaming needs an explicit migration. A Kiro-native folder without a number is valid and is never renamed to add one.
- The three canonical artifacts keep these names on every host. Other files in the folder (another tool's sidecar, Kiro's `tasks.meta.json`) belong to their owners: never edit, hash, or approve them.
- Structure stays English whatever language the prose uses: headings, IDs, field names, EARS keywords, markers such as `(guess)`, and file names.
- No placeholder in a written artifact: no `TBD`, `TODO`, `???`, or bare `N/A`. `requirements.md`, `bugfix.md`, and `tasks.md` leave out a section that does not apply. `design.md` keeps every section and marks one that does not apply `Not applicable: <reason>`.

## Requirements

```markdown
# Requirements: <Feature>

Sources: <intake item path>[, <spike folder or branch>]
Supersedes: NNNNN            (only when reworking a complete spec)
Blocks: <what waits on this> (only when it blocks other work)
Depends on: 00012, folder:login-fix

## Purpose
## Scope
## Assumptions
## Requirements

### REQ-001: <Title>
Source: <the idea | a Q&A entry such as Q3 | a discovery finding such as D1>
**User story:** As a ..., I want ..., so that ...

#### Acceptance criteria
1. WHEN ... THE SYSTEM SHALL ...

## Non-functional requirements
## Risks
- <risk>: impact <h/m/l>, likelihood <h/m/l>; mitigation: ...; fallback: ...
## Out of scope
## Unresolved questions
```

- IDs never change when sections are reordered, and a deleted ID is not reused. Every requirement is required; there are no priority tiers.
- Each requirement names its source. Anything without one is a `(guess)` or an assumption. A contract detail the developer did not give stays marked `(guess)` until confirmed.
- `## Risks` holds risks known at requirements time; technical risks found later go to the design.
- A spec that reworks a complete spec names it in `Supersedes:` and leaves the complete spec unchanged.

### Spec dependencies

`Depends on:` lists implementation prerequisites. It is separate from task dependencies, `Blocks:`, and `Supersedes:`.

- At most one unindented `Depends on:` line, before the first level-two heading of `requirements.md`, or at the end of `## Introduction` in `bugfix.md`, just before `Sources:`. No line means no prerequisite. An empty or repeated line is invalid. An indented or list-item field, a fenced example, and a field in `tasks.md` declare nothing. An unindented `Depends on:` line elsewhere in the requirements artifact is a misplaced declaration.
- The value is a comma-separated list; each item is trimmed. An item is five ASCII digits (the one spec folder with that number) or `folder:<name>` (the one spec folder with exactly that name). A name cannot be empty, `.` or `..`, or hold a comma, slash, or backslash. No other form is valid. Two items that resolve to the same folder count once.
- References resolve only in the configured specs folder. Each direct prerequisite must be complete before implementation starts. A missing, ambiguous, or unreadable target, a target whose state cannot be reconciled, a self-reference, or a cycle anywhere in the reachable graph closes the implementation gate, and only that gate. Phase and approvals stay as they are. Prerequisites are read, never written.

## Design

```markdown
# Design: <Feature>

## Overview
## Context and constraints
## Architecture
## Module placement
## Components and interfaces
## Data model
## Data and control flow
## Error handling
## Security and privacy
## Testing strategy
## Rollout and migration
## Risks and edge cases
## Requirement traceability
## Alternatives considered
## Reuse inventory
## Open decisions
```

Every section stays. One that does not apply reads `Not applicable: <reason>`, with a reason, so a review can tell "no security concern" from "forgot security". `## Risks and edge cases` uses the one-line risk shape of the requirements. `## Requirement traceability` has a column headed `Criteria` (or `Criterion`) that lists the criterion IDs each design element covers.

## Tasks

```markdown
# Tasks: <Feature>

- [ ] T-001 Implement ...
  - Requirements: REQ-001, REQ-003
  - Depends on: none
  - Location: <bounded repo-relative paths>
  - Reuse: <helpers and use, from design>           (when applicable)
  - Premise: <stated observed state, verbatim>      (when applicable; required for delete/rewrite based on state)
  - Contract: <applicable design contract, verbatim>
  - Details: <specific change and boundaries>
  - Acceptance criteria: REQ-001 criteria 1, 2; REQ-003 criterion 1
  - Risk: <actual risky change and design mitigation> (when evidenced)
  - Verify: <command, test, or file check this task owns>
  - Outcome: <observed result, written during implementation>   (progress field, not hashed)
  - Exception: <accepted verification exception and rationale> (progress field, not hashed)
  - [ ] T-001.1 ...

## Completion criteria
## Unresolved questions
```

- Top-level tasks have stable IDs. A checkbox records progress: a task is checked only after its verification succeeds or an exception is recorded.
- `Outcome:` and `Exception:` are progress fields, written during implementation and left out of the hash. Before the plan is approved, they draw a validation warning.
- `Depends on:` names earlier task IDs. Re-planning keeps checked tasks and their IDs.
- `## Completion criteria` holds checkboxes; ticking the last one marks the spec complete.
- A task may cite a criterion of a spec its own spec depends on. On a `Requirements:` or `Acceptance criteria:` line the form is `<spec reference> <requirement ID> criterion <n>` (or `criteria <n>, <m>`), the reference following the `Depends on:` grammar: `00004 WF-004 criterion 8`. An ID without a spec reference belongs to the task's own spec.

Checkbox forms: `[ ]` open, `[x]` or `[X]` checked, and Kiro's `[-]` (in progress) and `[~]` (queued), which count as open. A `*` right after the box (`- [ ]* 2.2 ...`) marks an optional task: left unchecked, it holds the spec in no phase and is never offered as the next task.

## Kiro-native specs

Kiro marks a spec's shape in `.config.kiro`:

```json
{"specId": "<uuid>", "workflowType": "requirements-first", "specType": "bugfix"}
```

- On create, write `.config.kiro` with a new UUID, `workflowType` `requirements-first` or `design-first`, and `specType` `feature` or `bugfix`, and mirror `specType` in `.specflow.json`. `.config.kiro` is not a canonical artifact: it is not hashed and carries no approval.
- On read, take the spec type from `.config.kiro`, else from `.specflow.json`, else from the files present (`bugfix.md` means bugfix). Report a disagreement; never fix it without the developer.
- Never convert one shape into another. Never renumber an existing document: validate IDs against the scheme it already uses (Kiro's `Requirement N` with criteria `N.M` and tasks `N.` / `N.M`, or `REQ-` and `T-` IDs). New specs use `REQ-` and `T-`.
- A Kiro-native design keeps its own headings; Kiro has no fixed design skeleton. A Kiro-native `tasks.md` without `## Completion criteria` goes from implementation straight to complete.
- Design-First specs put `design.md` first: the design is drafted from the intake item, requirements from the approved design, tasks from both.

## Bugfix specs

`bugfix.md` fills the requirements slot, in Kiro's shape:

```markdown
# Bugfix Requirements Document

## Introduction
<what breaks, where, impact; may name the suspected cause>

Depends on: <prerequisites, when there are any>
Sources: <intake item path>

## Bug Analysis

### Current Behavior (Defect)
1.1 WHEN <condition> THEN the system <incorrect behavior>

### Expected Behavior (Correct)
2.1 WHEN <condition> THEN the system SHALL <correct behavior>

### Unchanged Behavior (Regression Prevention)
3.1 WHEN <condition> THEN the system SHALL CONTINUE TO <existing behavior>
```

- Kiro sometimes adds a section whose heading starts `## Bug Condition`; it may sit in `bugfix.md` or in `design.md`.
- Never create `requirements.md` beside an existing `bugfix.md`.
- The bugfix `design.md` and `tasks.md` follow `templates/bugfix/`. Sections beyond the design skeleton are allowed. The task plan keeps Kiro's order: the exploration test that must fail, the preservation tests, the fix with its two re-runs, and the checkpoint last. Kiro plans may hold more tasks between the fix and the checkpoint; the spec is in verification while the checkpoint alone is unchecked.

## Workspace root and intake items

`.agents/specflow.json` (optional) sets the workspace root and the specs folder:

```json
{
  "schemaVersion": 1,
  "root": "docs/dev/project-management",
  "specsDir": "docs/dev/project-management/specs"
}
```

Without it, the root is `.kiro/specflow` and the specs folder `.kiro/specs`. Paths are repository-relative with forward slashes. A path that is absolute, holds a `..` segment, or resolves outside the repository is refused before any use. `numberScan` lists extra folders whose five-digit prefixes count when a new number is claimed.

```text
<root>/
├── intake/
│   ├── new/
│   │   └── [<group>/]NNNNN-<title>/
│   │       ├── idea.md          # first input, verbatim; claims the number
│   │       ├── qa-log.md        # questions, answers, review minutes
│   │       ├── <other inputs>
│   │       └── spike/           # spike path only
│   └── processed/
│       └── [<group>/]NNNNN-<title>/
└── reviews/
    └── YYYY-MM-DD-cross-spec-review.md
```

- An intake item may sit in at most one group folder, which it keeps when it moves to `processed/`. "Processed" means "has a spec", not "approved".
- An intake item and its spec share a number and may carry different titles.

### Q&A log

`qa-log.md` gets one entry per question, appended right after the answer, and one `## Review: <artifact> <date>` block per review:

```markdown
## Q3 - Error budget (2026-10-01)
- Question: What failure rate is acceptable for the nightly import?
- Answer: "Under 0.1% of rows for this release; failures go to a retry file."
- Reading: this release requires failures below 0.1% of rows and a retry file.

## Q7 - Error budget, replaces Q3 (2026-10-02)
- Question: Is 0.1% still the budget after the pilot numbers?
- Answer: "Make it 0.5%, the pilot showed 0.1 is not realistic."

## Review: design.md 2026-10-02
- 1 | Blocking | No rollback for the schema change | option 1 applied | resolved
```

- `Answer:` holds the developer's own words, caveats included; the agent's interpretation goes on a `Reading:` line.
- The log is append-only: a changed answer is a new entry that names the one it replaces. A secret in an answer is left out and the omission noted.
