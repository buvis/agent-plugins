# AWS guidance: implementation

Adaptation: Read this file in the implementation phase. Each passage under a source line is AWS AI-DLC text, copied verbatim with cuts shown as `[...]`; each `Adaptation:` line is specflow's own. Where the two differ, the specflow artifact contract wins. Read only the passages marked with the active profile or `[both]`.

## Rules that always hold

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Critical Rules @ v2.11.0 (6a378b5) [both]

[...]
- Brownfield: modify files in-place. NEVER create duplicates like ClassName_modified.java
[...]
- Measurable quality targets from NFR Requirements, NFR Design, and the Testing
  Contract coverage floor are inputs, not suggestions. NEVER relax, lower, or
  disable a defined target, including threshold settings in test or build
  configuration, to make a step pass; surface the gap instead.

Adaptation: specflow's quality targets are the acceptance criteria of `requirements.md` and the targets `design.md` sets. A target that cannot be met is reported to the developer, never lowered.

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 1: Read All Unit Artifacts @ v2.11.0 (6a378b5) [both]

[...] Never invent the content of a
missing artifact.

Adaptation: Before a task starts, read its requirement, the design sections it names, and the files its Location line lists.

## Plan the work

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [standard]

Plan should cover (as applicable to the unit):
- [ ] Business logic implementation
- [ ] API/endpoint layer
- [ ] Repository/data access layer
- [ ] Database migrations/schema changes
- [ ] Unit tests
- [ ] Integration tests
- [ ] Configuration files
- [ ] Documentation (inline and API docs)
- [ ] Deployment artifacts (Dockerfiles, IaC)

Adaptation: specflow's plan is `tasks.md`, approved before implementation starts. Work one task at a time, in its order, and check the layers above against the task before calling it done.

## Tests belong to the task

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [quick]

- **Minimal strategy**: Requirement-driven tests (1 per requirement, happy-path unit floor per component); unit tests are the default, but a `bugfix` / `security-patch` targeted regression uses the narrowest level that reproduces the defect

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [standard]

- **Standard strategy**: Unit test files per component (5-8 tests each) + integration test stubs for key boundaries

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [both]

- `bugfix`, `security-patch`: the selected strategy plus a targeted regression for the bug/vulnerability at the narrowest level that reproduces it, even when that adds one integration/E2E test beyond Minimal's unit-test default; the existing suite remains green.

Adaptation: In specflow this floor belongs to the `bugfix` spec type, under either profile.

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [both]

If the plan presented to the user omits test file steps, add them before presenting. Tests are not deferred to Build and Test — that stage verifies and extends, not creates from scratch.

Adaptation: A task's tests ship in the same change as its code. A task whose Verify line names no test and no other check is not ready to start.

## Test order

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [both]

- **TDD**: for every applicable testable layer — data-model/database behavior, repository/data access, business logic, API/endpoint, and frontend behavior — plan Red (failing tests), Green (minimal implementation), then Refactor while green.
- **BDD**: define executable behavior/scenario examples before each observable feature slice, implement that slice across every required layer, run scenarios green, then refactor. Do not turn BDD into layer-local TDD.
- **ATDD**: write executable acceptance tests before the complete cross-layer feature implementation, implement against that acceptance contract, run acceptance green, then refactor. Do not split acceptance intent into unrelated per-layer Red steps.
- **Custom/mixed**: preserve the contract's exact `ordering` text, such as scenario-first BDD with lower-level unit tests after implementation. Never coerce a mixed posture into TDD.
- **Test-after**: for every applicable testable layer, implement the layer and then write/run that layer's tests.

Adaptation: The method comes from the repository's own instructions. When they name none and nothing in the repository shows one, ask the developer once, during intake, and keep the answer for every task.

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [both]

The contract always puts test-runner readiness before the first executable test step. On greenfield work, bootstrap the minimal runner/configuration and dependency needed to execute the exact unit-scoped command before the first TDD Red, BDD scenario, or ATDD acceptance step. On brownfield work, verify that command before the first test-first step. [...] a Red/Green step is invalid if no runnable command exists.

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 2: PART 1 — Planning @ v2.11.0 (6a378b5) [both]

Every run command in this file MUST be scoped to this unit only, using exact
test file paths or an exact unit filter. A bare project-wide command like
`npm test` is not acceptable. [...]

Adaptation: While a task is in progress, run its own tests by exact path or filter. The full suite runs when the task is done, before it is checked.

## Record what was done

> Source: A1 `core/aidlc-common/stages/construction/code-generation.md` > Steps > Step 5: Generate Code Summary @ v2.11.0 (6a378b5) [standard]

[...]
- Files created/modified
- Key implementation decisions
- Test coverage summary
- Any deviations from the plan

Adaptation: specflow writes no code summary file. These facts go in the task's `Outcome:` line in `tasks.md`, with the commands run and their results. A deviation from the task is named there, never left implicit.
