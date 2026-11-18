# Cross-host handoff

Status: failed collection. T-051 remains unchecked. No successful handoff or
host-order independence is claimed.

## Observed run

The latest batch at `96bb5b2`, inspected on 2026-11-18, captured requirements
on kiro-cli 2.35.1 / KAS 0.66.70 with `claude-haiku-5.5`, followed by design
on Codex 0.169.0 with `gpt-6.1-sol`. Both instruction inventories are clean.
The canonical requirements hash is unchanged across those steps:
`3e3d048b24b07d8cc84318c4fd0603c34a0e3c89696dcecf38d768f76de75948`.

Claude rejected its boundary proof before the tasks step. The generic error
does not identify the mismatching proof field. No tasks, approval/edit cycle,
implementation, verification or coexistence step completed. The supervisor's
later missing-state findings are consequences of that stop, not observations
of those hosts executing the remaining steps.

The trace is preserved at
`docs/dev/tmp/specflow/batch-20261118T170622Z/proofs/handoff.json`.
This diagnostic evidence does not close T-051. A successful live trace and
the checks below remain required.

The earlier `f511ceb` trace stopped at the first Kiro step on a denied read;
it remains preserved under `batch-20261117T130520Z/proofs/handoff.json`.

## Required evidence

The batch writes `docs/dev/tmp/specflow/proofs/handoff.json`. Its first eight
steps belong to this record: requirements (kiro-cli), design (Codex), tasks,
task approval, requirements edit and reapproval (Claude Code), implementation
(Codex), and verification (kiro-cli).

Each step retains the actual host/model, boundary digest, measured instruction
classification, developer prompt, final reply, validator status, artifact file
list and bytes, and canonical artifact hashes. The supervisor checks stale
requirements/design/tasks after the Claude edit, reapproved state before
implementation, stable upstream hashes across host changes, and final completion
with no next task. Review the stored state and paths for additional canonical
files or relocation before accepting this evidence.

After the developer run, inspect the trace for privacy, preserve its observed
results, and record findings here. A failed or incomplete trace does not close
T-051; a mocked test is not live evidence.
