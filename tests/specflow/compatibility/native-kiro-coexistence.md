# External-edit coexistence through kiro-cli

Status: not measured. T-052 remains unchecked. The latest batch at `96bb5b2`
stopped before the Claude tasks step, before either coexistence step launched.
The supervisor's missing-external-edit findings show missing evidence, not
an observed failure of edit preservation. This does not prove the Kiro IDE
native Spec workflow.

The incomplete trace is preserved at
`docs/dev/tmp/specflow/batch-20261118T170622Z/proofs/handoff.json`.

## Required evidence

The batch writes `docs/dev/tmp/specflow/proofs/handoff.json`. After its verified
handoff, kiro-cli receives an external-edit request that explicitly excludes
specflow and state updates. It appends a newline-related requirement. Codex then
resumes the spec without approval, implementation, or reversion.

Compare the state bytes before and after the external edit: `.specflow.json`
must be unchanged by that writer. Compare the edited requirements before and
after Codex resume: they must remain byte-identical. The next validator status
must mark requirements, design, and tasks stale. Both steps need clean measured
instructions and the matching boundary proof. Preserve the actual trace and
findings here after privacy inspection; do not substitute model prose for state.

IDE-only type checks remain separate in `kiro-type-checklist.md`.
