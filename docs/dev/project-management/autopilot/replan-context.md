# Replan Context

PRD: 00018-autopilot-controller-kernel-v1.md
Replan attempt: 2
Trigger: subagent_prompt_overrun on task 7
Budget: 40000 tokens per task

## Completed work (do NOT re-plan)

- Task 1: Freeze pinned controller ownership, schemas and fixtures
- Task 2: Split retained kernel tests by public API without changing assertions
- Task 3: Implement strict kernel schema and package namespace
- Task 4: Extract atomic store with guarded forensic restore
- Task 5: Extract explicit project root containment resolver
- Task 6: Implement bounded CLI bootstrap, snapshot and matching-intent recovery

## Aborted task

Implement epoch-fenced owner operations and receipt capacity

## Directive

Plan ONLY remaining PRD scope. Target ≤ 40000 tokens per task. Split fine-grained, with mandatory rendered Devon prompts below 50000 bytes. No cap increase.

Task 7 Tess tests are committed at b4655fe. Preserve all assertions and reuse them without duplicate test authoring. Devon was NOT dispatched; no verdict exists. Split owner acquire/release/recover, historical receipt replay, normal/reserved byte and count capacity, archive proof, export, registration and documentation into bounded tasks as appropriate. Preserve the response-size reachability limitation recorded in reports/00018-replan1-task7-build.md.

Task 3 is completed: its operator exception remains task-3-only. Never repeat its Devon or Tess rounds or reimplement completed tasks 1–6. Later security tasks retain all normal gates and need their own operator decision if a host filter blocks dispatch.

Preserve original work_start_sha 535e433cf83351bca3c12c9e87c5da08eed8d666. Full pre-clear tasks, attempts and provenance are archived in reports/00018-replan2-prior-state.json and committed history. Carry all contributing test/implementation model evidence into subsequent audits; the reset is not permission to omit earlier work.

Read reports/00018-replan1-task7-build.md and reports/00018-anthropic-route-recovery.md before planning/dispatch. Keep independent model-provider review routes verified. No completion review in the build session.
