# Implementation phase

Load this reference to build an approved task plan, with `references/aws/implementation.md`, reading only the AWS passages marked with the active profile or `[both]`. Questions follow the shared dialogue rules in `references/artifact-contract.md`.

- [SR-IMP-001] Build only from an approved task plan whose implementation gate is open: `status` shows no stale approval and no dependency blocker, and `validate_spec.py validate <spec-dir> --phase implementation` reports no error. Report any code-drift warning first. Otherwise build nothing, and name what blocks.
- [SR-IMP-003] Work one coherent task at a time: the next task `status` names, inside its `Location:` and contract, finished and verified before the next one starts.
- [SR-IMP-002] Before a task with a `Premise:` runs, check that premise against the repository as it is now. When it no longer holds, skip the task, leave it unchecked, and report what you found; never adapt the task to make it fit.
- [SR-IMP-004] Preserve every change in the working tree that the task did not make: never revert, overwrite, stage, or commit it, and stop to ask when it overlaps the task's files.
- [SR-IMP-005] Check a task only after its own `Verify:` succeeds, and write the observed result in its `Outcome:` line. A failed or unrunnable check leaves the task unchecked; report the evidence and the requirement it touches. Only the developer can accept an exception, recorded in an `Exception:` line with its rationale.
- [SR-IMP-006] When building shows that a requirement or the design is wrong or incomplete, stop and say so. With the developer's agreement, correct that upstream artifact; its change stales what depends on it, and implementation waits until the plan is approved again. Never widen or narrow the scope silently in code.
