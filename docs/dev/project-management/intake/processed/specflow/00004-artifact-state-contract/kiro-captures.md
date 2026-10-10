# Kiro captures (T-027)

Status: provisional, 2026-10-10. The developer was away from the machine that runs Kiro IDE and asked for progress without oversight. Instead of three specs generated in Kiro IDE, three Kiro-made specs from public repositories were captured. All three are Apache-2.0, and each is stored unchanged with its LICENSE, NOTICE, and source commit. The two IDE trials (open a specflow-written bugfix spec, and list specs through a `.kiro/specs` link) have not been run, so T-027 stays unchecked.

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

## Still open (needs Kiro IDE)

- Open a specflow-written bugfix spec (with `.config.kiro`) in Kiro IDE and record whether it shows as a Bug Fix spec.
- Link trial: point `.kiro/specs` at a folder elsewhere in the repository with a symbolic link (macOS), and record whether Kiro IDE lists, opens, and watches those specs, and whether it ignores `.kiro/specflow/`. Until then, the requirements' unresolved question stands, and so does the documented fallback (a configured specs folder may be invisible to Kiro's spec panel).
- A Requirements-First and a Design-First capture generated in this repository's own Kiro IDE, to compare with the public ones. Run sheet: `docs/dev/tmp/specflow/kiro-capture/RUNBOOK.md`.
