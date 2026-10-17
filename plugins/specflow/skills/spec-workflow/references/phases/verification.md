# Verification phase

Load this reference once every task is checked, with `references/validation-rules.md` and `references/aws/verification.md`, reading only the AWS passages marked with the active profile or `[both]`. Questions follow the shared dialogue rules in `references/artifact-contract.md`.

## Checks

- [SR-VER-008] Run the checks under `## Completion criteria` and `validate_spec.py validate <spec-dir> --phase verification`, plus the tests and checks the changed behavior calls for: proportionate to the change, never a ritual over unrelated code.
- [SR-VER-003] The evidence for each task is its `Outcome:` line. Map every failed check to the tasks and the requirement criteria it touches, and report it that way.
- [SR-VER-005] When a final check fails for a task already checked, uncheck that task and write the reason in its `Outcome:` line; the spec goes back to implementation.
- [SR-VER-006] A check that cannot be run, or fails for a reason outside the spec, stays a failure unless the developer accepts an exception. Record an accepted one in an `Exception:` line under its task, with the rationale.
- [SR-VER-001] Spike code never merges. Confirm that no spike folder, no spike branch, and no file copied or imported from either is part of the change; report any you find with its path.
- [SR-VER-007] A requirements error found here is corrected in the requirements, with the developer; that change stales the design and the tasks, and the spec goes back through their approvals.

## Completion

- [SR-VER-004] Completion is ticking the boxes under `## Completion criteria`. Tick none while a required task is unchecked, a check fails, or an approval is stale; ticking the last box is what makes the spec complete. A Kiro-native plan without that section goes straight from implementation to complete, and this phase does not run.
- [SR-VER-009] A bugfix plan has no `## Completion criteria`: the spec is in verification while task 4, the checkpoint, is its only unchecked task. Run the full test suite and `validate`; check task 4, with the result in its `Outcome:` line, only when both pass, and that makes the spec complete. A failure maps to the task and the clause it touches, as above.
- [SR-VER-002] When the spec reaches `complete`, offer to delete its spike folder or branch, naming each exact target; delete only after the developer confirms.
