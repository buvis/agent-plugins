# Tasks phase

Load this reference to plan or re-plan `tasks.md`. Questions follow the shared dialogue rules in `references/artifact-contract.md` (`## Shared dialogue`); the approval summary is the one defined there, and the task shape is the one in its `## Tasks` section. Record an approval by the procedure in `references/state-contract.md`.

## Inputs

- [SR-TSK-009] Resolve the active spec, and ask only when more than one could be meant. Plan only from approved requirements and an approved design, never from the requirements alone; the design is always there in the spec folder, so nothing is detected or planned around. Read both in full. Refuse the tasks approval while an upstream marker (a `(guess)`, an unresolved question, an open decision) has no acceptance by name, or while a contract a task needs is still vague; report each before asking.
- [SR-TSK-007] Requirements say what, the design says how, and the tasks say in which order. Dependencies are explicit, the order is topological, and detail is refined task by task from the design, never invented.
- [SR-TSK-020] Before the first task, extract from the two approved artifacts: the capabilities (one per requirement ID), the module structure (the placement rows, new or edited), the dependency graph among them, the phases the design or its rollout names, and the patterns the reuse inventory says to follow. The tasks come from that extraction, not from the requirements' prose alone.
- [SR-TSK-021] When the design gives no decomposition or no order, derive them: each requirement is one unit of work, a unit depends on another when the design's data flow or its wording says so, and on nothing otherwise; the planning summary says that the decomposition or the order was derived, and from what.

## Writing the tasks

- [SR-TSK-018] Each task has a stable checkbox and a stable `T-NNN` ID, and names the requirement IDs and numbered criteria it satisfies (or the bugfix clauses).
- [SR-TSK-002] List the tasks in topological order; each has its `Requirements:`, `Depends on:`, and `Verify:` lines, and `Depends on:` names only earlier tasks that exist. A dependency found late goes onto the later task's line, never a guessed ID.
- [SR-TSK-001] State each task's dependencies in its own `Depends on:` line. Grouping tasks into layers is optional.
- [SR-TSK-010] Each task names its `Location:`, and its `Reuse:`, `Contract:`, `Details:`, and `Acceptance criteria:` where they apply; leave out a field that does not apply. Seed `Location:` and `Reuse:` from the design's placement and reuse inventory, and copy each contract from the approved design byte for byte. A task has one named outcome, a bounded file slice, and no design choice left for the implementer to guess.
- [SR-TSK-008] A task may cite a criterion of a spec its own spec names in `Depends on:`, written as that spec's reference, the requirement ID, and the criterion number: `00004 WF-004 criterion 8`. Never cite a criterion of any other spec, and never restate a criterion in this spec to make it citable.
- [SR-TSK-004] A task that deletes or rewrites based on what the repository looks like now states that observed state in a `Premise:` line, verbatim. Whoever runs the task checks it again first (`references/phases/implementation.md`).
- [SR-TSK-006] Write the premise so a skip is unambiguous: what to look at and what must be true. A task that edits an existing test pins the test's expected count in its premise with a count check, so a changed count stops it.
- [SR-TSK-003] Verification is a command, a test, or a file check; anything else needs an exception the developer accepts.
- [SR-TSK-005] `Verify:` names the tests or checks the task owns, never a suite-wide total.
- [SR-TSK-012] Add a `Risk:` note only when the task's contract, paths, or details show an exported API, persisted schema, or wire format change, a hook registration, a new algorithm, a change to shared mutable state, or a migration of persisted data. Name the change and the design's mitigation. Calling an interface, risk words, or the number of files never earn a note.
- [SR-TSK-017] Among tasks with no dependency between them, follow the working practices the requirements record: a thin end-to-end slice first when the developer chose one, and each test before or after its code as chosen. A bugfix plan keeps its fixed test order whatever the practices say.
- [SR-TSK-015] The last tasks cover end-to-end verification, documentation, compatibility, and cleanup. End the plan with `## Completion criteria` (checkboxes), then `## Unresolved questions` when any are left. The checkboxes in `tasks.md` are the one record of progress; `.specflow.json` never stands in for them.

## Bugfix plans

- [SR-TSK-019] A bugfix plan is the four top-level tasks of `templates/bugfix/tasks.md`, in this order, under Kiro numbering (`1.`, `3.1`): 1, the bug condition exploration test, which MUST FAIL on the unfixed code; 2, the preservation tests, written by observing the unfixed code, which MUST PASS on it; 3, the fix, whose subtasks make the change and then re-run the same task 1 and task 2 tests; 4, the checkpoint that runs the full test suite. Only the subtasks of task 3 vary. Each task traces its clauses in a `_Requirements: <clause numbers>_` line, and every `2.x` and `3.x` clause is traced by task 1, task 2, or a subtask of task 3. Working practices do not change this order (SR-TSK-017).

## Sizing

- [SR-TSK-011] Check every task with the five sizing checks:
  1. one named outcome, a bounded file slice, exact applicable contracts, and owned verification after its listed dependencies, with no design choice handed to the implementer;
  2. split independent outcomes, or a verification path that needs edits outside the slice; try safe file boundaries first, then capability boundaries; the number of files alone is no reason;
  3. each piece builds, or passes its file check and verification, after its dependencies, without an unfinished sibling; coupled interface, implementation, caller, and test edits stay together;
  4. re-check each split piece's scope, contracts, dependencies, and verification; when size is uncertain, prefer a safe split that can be checked on its own, and say why inseparable changes stay together;
  5. when no bounded task or safe split exists, report a planning blocker with the boundary you tried and why it fails, before the tasks approval.

Good splits: two independent cache changes, each with its own check. Not splits: a new module and the export that makes it reachable, or a signature and the callers that must change with it; each pair stays one task.

- [SR-TSK-022] A task that says "implement the feature", "wire everything up", or names a whole module as its outcome is too coarse: it bundles outcomes nobody can verify apart. A granular task names one outcome a reader can check with its own `Verify:` line, in a bounded file slice, with its contracts copied in; the sizing checks above decide the boundary.
- [SR-TSK-023] Shape each task like these contrasts: a model task names the file, the fields and types of the record it adds, and the test that reads one back; an endpoint task names the route, the request and response shapes with their status codes, and the request its test sends; a refactor task names the functions moved or renamed, every caller it touches, and the suite that must still pass; a bug-fix task names the failing test written first, the function fixed, and the preservation test that must still pass. A separable pair (two independent cache changes, each with its own check) is two tasks; a coupled pair (a signature and the callers that must change with it, a module and the export that makes it reachable) is one task, and the planning summary says what a split would break.

## Re-planning

- [SR-TSK-014] Re-planning keeps every checked task and its ID; it never resets completed work silently, and a new task takes a new ID.

## Before approval

- [SR-TSK-016] Run `validate_spec.py validate <spec-dir> --phase tasks`. Fix every error; report a `placement-drift` warning (two or more planned modules the design does not place) in the summary, as an advisory, not a blocker.
- [SR-TSK-013] The planning summary gives the number of tasks, the execution order, the ambiguities, any decomposition or order you derived and how, both sides of each conflict between the requirements and the design with the task it touches, and each coupled multi-file task with what would break if it were split. The design owns implementation contracts and the requirements own acceptance; a conflict that breaks required behavior stays a blocker until the upstream artifact is corrected or the developer accepts a named exception. Then show the shared approval summary.
