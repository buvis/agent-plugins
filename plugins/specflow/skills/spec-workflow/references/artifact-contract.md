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

- The specs folder is `.kiro/specs/` by default, or the folder `specsDir` names in `.agents/specflow.json`. Read and write it directly. Never create, repair, or depend on a `.kiro/specs` link; making that link so Kiro IDE lists the specs is the repository's own setup, and it must be a link, never a copy. Kiro IDE's spec panel reads `.kiro/specs/`; through a `.kiro/specs` link to another specs folder it lists, opens, and watches those specs, and it ignores `.kiro/specflow/`.
- `NNNNN` is the spec number of the intake item. The title is lowercase kebab-case, stable, and filesystem-safe. A number is never reused.
- The folder name is chosen once. Renaming needs an explicit migration. A Kiro-native folder without a number is valid and is never renamed to add one.
- The three canonical artifacts keep these names on every host. Other files in the folder (another tool's sidecar, Kiro's `tasks.meta.json`) belong to their owners: never edit, hash, or approve them.
- `.specflow.json` is written by a check and then a replace, as WF-006.4 allows: a write stops when the file changed since it was read, and a state file that is a symbolic link is replaced by a regular file. The new file is flushed to disk before it replaces the old one, so a crash leaves one of the two whole.
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
- A withdrawn requirement keeps its heading as `### <ID>: withdrawn`, followed by one line giving the reason. It needs no criteria and no task, its ID stays taken, and nothing may cite it.
- Each requirement names its source. Anything without one is a `(guess)` or an assumption. A contract detail the developer did not give stays marked `(guess)` until confirmed.
- `## Risks` holds risks known at requirements time; technical risks found later go to the design.
- A spec that reworks a complete spec names it in `Supersedes:` and leaves the complete spec unchanged.

### Spec dependencies

`Depends on:` lists implementation prerequisites. It is separate from task dependencies, `Blocks:`, and `Supersedes:`.

- At most one unindented `Depends on:` line, before the first level-two heading of `requirements.md`, or at the end of `## Introduction` in `bugfix.md`, just before `Sources:`. No line means no prerequisite. An empty or repeated line is invalid. A list-item field, a fenced example, and a field in `tasks.md` declare nothing. An unindented `Depends on:` line elsewhere in the requirements artifact is a misplaced declaration, and so is a bugfix one with any text but `Sources:` after it in `## Introduction`. A bare indented line, or one spelled in another letter case, declares nothing and is reported as malformed.
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
- Each progress field is one line. Only that line is left out of the hash: a wrapped or indented line under it is hashed, so writing one stales the approved plan, and validation warns about it.
- `Depends on:` names earlier task IDs. Re-planning keeps checked tasks and their IDs.
- `## Completion criteria` holds checkboxes; ticking the last one marks the spec complete.
- Ticking a task or completion-criteria box never stales the approved plan. A checkbox in any other section, such as `## Risks` or `## Unresolved questions`, is hashed like other text, wherever that section sits. The task list is the part before the first `## ` heading, or the `## Tasks` section of a Kiro plan.
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

Without it, the root is `.kiro/specflow` and the specs folder `.kiro/specs`. `schemaVersion` is optional and must be `1` when present. Paths are repository-relative with forward slashes. A path that is absolute, holds a `..` segment, or resolves outside the repository is refused before any use. `numberScan` lists extra folders whose five-digit prefixes count when a new number is claimed.

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

### Intake procedure

The agent performs these steps; `validate_spec.py next-number` only reads.

1. **Create an item.** Run `validate_spec.py next-number`. Create `<root>/intake/new/[<group>/]NNNNN-<title>/` with the number, save the developer's first input verbatim as `idea.md`, and start `qa-log.md` from `templates/intake/qa-log.md`.
2. **Scan again.** Run `validate_spec.py validate <your item> --phase intake` after writing. If it reports a `number-clashes` error naming your item, rename your own new item to the number `next-number` now prints, before anything cites it. Never rename an item someone else made.
3. **Move the item.** When the requirements artifact is first written, move the item to `<root>/intake/processed/`, keeping its group folder, first. Then write the artifact with a `Sources:` line naming the `processed/` path, and any spike folder inside it.
4. **Write the fallback log.** A spec with no intake item, such as one Kiro created, gets `<root>/intake/processed/<spec-folder>/qa-log.md` on its first question.
5. **Take a file input.** Take an input file only from one explicit path. When the path is missing or matches more than one file, ask; never pick a match. Copy the file into the intake item. When it is binary, too large to read, or outside the repository, record its location in `idea.md` and say what could not be read.

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

- [SR-DLG-008] `Answer:` holds the developer's own words, caveats included; the agent's interpretation goes on a `Reading:` line. Classify a caveat by its meaning, never by words such as "for now": a definite choice for this release stays a requirement, a later revisit that does not affect this spec is a `Follow-up:` line in the entry, and only the part still undecided for this spec goes under `## Unresolved questions`, with what would resolve it. When it is unclear whether a caveat affects this spec, ask, or keep it marked uncertain; never guess a settled choice, and never hide a current dependency in a follow-up.
- [SR-DLG-005] The log is append-only, each entry written right after its answer, so it survives a lost conversation: a changed answer is a new entry that names the one it replaces, and the earlier entry stays as it was.
- [SR-DLG-013] A secret in an answer (a key, a password, a token, a copied environment value) is left out of the log, the artifacts, and `.specflow.json`, and the omission noted where it was left out.

## Shared dialogue

These rules hold in every phase and every review, at intake and in Design-First too. Load them before the first question or approval summary of any conversation; phase and review references point here and add only their own question banks and summaries. The Q&A log rules above are part of this section.

- [SR-DLG-001] Ask a clarifying question only when the missing answer would materially change scope or behavior, and ask one question per message.
- [SR-DLG-002] Offer the choices of a question as a numbered list in plain text, or through the host's structured-question tool when it has one. Never depend on one host's tool.
- [SR-DLG-003] Put the recommended choice first, marked `(Recommended)`, with a one-line reason. When the choices are a toss-up, say so and recommend none.
- [SR-DLG-007] Every multiple-choice question also offers "Other", for an answer in the developer's own words.
- [SR-DLG-010] Every clarifying question also offers "Not decided yet". That choice records an unresolved question in the artifact, which a dependent approval needs accepted by name.
- [SR-DLG-009] Say where the questioning stands in each question, for example "question 3 of about 8", counting what is left across every topic, so the developer can judge whether to stop early.
- [SR-DLG-011] Use the developer's words in questions. Define a term of art in plain words the first time it appears.
- [SR-DLG-004] Do not ask what the intake item, the repository, or an earlier answer already shows. Use that answer, name its source (the file, or the Q&A entry), and list it under `## Assumptions` until the developer confirms it.
- [SR-DLG-012] After asking questions, play back your reading of the answers as a short list before drafting from them. Clear, unambiguous answers need no further confirmation: recap and draft. A material interpretation or an unresolved conflict needs the developer's confirmation or correction before you draft from it; ask it with a confirmation you already need, such as the intake choices, and stop separately only when no such confirmation is left. A playback never stands in for an artifact approval or a marker accepted by name.
- [SR-DLG-006] When an artifact is ready for approval, summarize its material decisions, the risks left open, what you assumed without asking, the recap of any review (raised, resolved, disputed), and the phase that follows. Then ask for approval and stop: never start the next phase on your own. Approval leaves an assumption an assumption; it stays listed as one.
