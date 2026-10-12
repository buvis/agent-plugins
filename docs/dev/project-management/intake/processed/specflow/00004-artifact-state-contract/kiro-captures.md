# Kiro captures (T-027)

Status: complete, 2026-10-12. On 2026-10-10 the developer was away from the machine that runs Kiro IDE and asked for progress without oversight. Instead of three specs generated in Kiro IDE, three Kiro-made specs from public repositories were captured. All three are Apache-2.0, and each is stored unchanged with its LICENSE, NOTICE, and source commit. The developer ran the two IDE trials in Kiro IDE on 2026-10-12; both passed (see "IDE trials").

## Captures

| Fixture under `tests/specflow/fixtures/kiro/` | Source | `.config.kiro` |
|---|---|---|
| `requirements-first/` | `awslabs/sra-verify` `.kiro/specs/iam-user-detection` | `workflowType` `requirements-first`, `specType` `feature` |
| `design-first/` | `sebsto/swift-bedrock-library` `.kiro/specs/structured-output` | `design-first`, `feature` |
| `bugfix/` | `awslabs/DefectDetectionApplication` `.kiro/specs/triton-inference-runtimes-missing-fix` | `requirements-first`, `bugfix` |

The exact commit is in each fixture's `SOURCE.txt`. Two local Kiro specs were read for comparison but not copied, because one repository is private and the other has no clear license: `doogat/ddb` `.kiro/specs/collapse-actor-plumbing` (Design-First, run in Kiro) and `calcard-mcp` spec 00031 (bugfix, run in Kiro). Their observations are marked "local" below.

## File sets

- Every spec has `.config.kiro` as one line of JSON with `specId` (a UUID), `workflowType`, and `specType`. A bugfix spec records `workflowType` `requirements-first`. Not every file ends with a newline.
- Feature: `requirements.md`, `design.md`, `tasks.md`. Bugfix: `bugfix.md`, `design.md`, `tasks.md`.
- Kiro writes a sidecar `tasks.meta.json` with its task run history, keyed by task title (local, both specs). Other public specs carry extra files such as `status.md`, `plan.md`, or `PIVOT-FINDINGS.md`. These are files specflow does not own (ART-001.9).

## Headings and IDs

- Feature `requirements.md`: `# Requirements Document`, `## Introduction`, `## Glossary`, `## Requirements`, then one `### Requirement N: <title>` per requirement with `**User Story:**` and `#### Acceptance Criteria`, which holds numbered EARS clauses. A trace cites `N.M`, as in `_Requirements: 1.6, 1.7_`.
- Feature `design.md` has no fixed skeleton. Both captures open with `# Design Document` (with or without `: <title>`) and `## Overview`, then vary: `## Architecture`, `## Components and Interfaces`, `## Data Models`, `## Algorithmic Pseudocode`, `## Key Functions with Formal Specifications`, `## Correctness Properties`, `## Error Handling`, `## Testing Strategy`, `## Performance Considerations`, `## Security Considerations`, `## Dependencies`.
- `bugfix.md` matches the shape of design §6.6 (`# Bugfix Requirements Document`, `## Introduction`, `## Bug Analysis` with the three behavior sections, clauses numbered `1.x`, `2.x`, `3.x`). It adds `## Bug Condition and Property Specification` (this capture) or `## Bug Condition and Properties` (local), both variants that the discovery document already reported.
- Bugfix `design.md` matches the skeleton of design §6.6 and adds a free-form `### Deployment Path` under `## Fix Implementation`, as the discovery document reported for its own sample.

## Task syntax

- `# Implementation Plan` or `# Implementation Plan: <title>`, `## Overview`, `## Tasks`, and often `## Notes` and `## Task Dependency Graph` (a fenced JSON block). No capture has `## Completion criteria`.
- Top-level tasks are `- [ ] N. <title>`, sub-tasks `  - [ ] N.M <title>`, traced by `_Requirements: x.y_`.
- Checkbox states seen: `[ ]`, `[x]`, `[-]` (in progress: bugfix task 4, requirements-first task 13), and `[~]` (queued: bugfix tasks 5 and 6; local Design-First spec, most sub-tasks).
- `[ ]*` marks an optional task (requirements-first tasks 2.2, 3.2, 4.2, 8 to 12).
- The bugfix plan has six top-level tasks, and so does the local bugfix spec. The checkpoint is the last task, not task 4.

## Against the design

Corrections applied to `design.md` on 2026-10-10. Each one stales the design approval and the task plan, which the developer re-approves (T-027 Risk):

1. Canonical step 5 and the checkbox pin now accept `[-]` and `[~]` as well as `[x]`, and keep a trailing `*`. Without this, starting a task in Kiro would stale the approved plan.
2. Only `[x]` or `[X]` counts as checked. An optional (`*`) task left unchecked does not hold a spec out of `verification` or `complete`, and is never `nextTask`. This is a design choice the captures prompted, not something they show.
3. A bugfix plan is in `verification` while its last top-level task alone is unchecked, not "task 4".
4. The validator accepts any `## Bug Condition...` section in `bugfix.md`.
5. `design-sections` checks the template section list only in a design written from the specflow template (`# Design: `). A Kiro-native design keeps its own headings.

Matches without change: the `.config.kiro` keys and values, the `bugfix.md` and bugfix `design.md` skeletons, the IDs and traces in Kiro's own numbering, and the requirements-slot path `bugfix.md`.

## IDE trials (2026-10-12)

Run by the developer in Kiro IDE on macOS, each in its own workspace under the ignored `docs/dev/tmp/specflow/kiro-capture/`. Inputs were copies of the specflow-written fixtures `tests/specflow/fixtures/specs/00101-feature-sample` and `00102-bugfix-sample`.

- Bug Fix display (`trial-bugfix/`, the spec in a real `.kiro/specs/`): Kiro's spec panel lists `00102-bugfix-sample` with the documents Bugfix, Design, Tasks, so it reads the spec as a Bug Fix spec. All three open, and Kiro offers to run the tasks.
- Link trial (`trial-link/`, `.kiro/specs` a relative symbolic link to `../specs-elsewhere`):
  - Lists: both specs appear in the spec panel.
  - Opens: all six documents open; 00101 shows Requirements, 00102 shows Bugfix, so each keeps its type through the link.
  - Watches: with 00101's Tasks open, `T-001` was checked by an edit to the real file under `specs-elsewhere/` from outside Kiro; Kiro showed it done without a reload.
  - Ignores `.kiro/specflow/`: a spec-shaped folder there (`.config.kiro` and all three documents) did not appear in the panel.

Result: the design's assumption holds. A configured specs folder is visible to Kiro's spec panel when `.kiro/specs` links to it, so the fallback (documenting it as invisible) is not needed. T-045 (00008) can state that the link works.

## Optional follow-up

- A Requirements-First and a Design-First capture generated in this repository's own Kiro IDE, to compare with the public ones. Not needed to close T-027.
