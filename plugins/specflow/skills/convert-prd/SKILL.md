---
name: convert-prd
description: Converts an existing PRD or legacy intake item into specflow requirements, design, and tasks, or adopts an implemented PRD with its evidence kept. Use when the developer asks to convert, adopt, or graduate a PRD ("convert PRD", "adopt PRD", "graduate PRD"); needs a resolved source document or repository context.
---

# convert-prd

Take an authored PRD or a legacy intake item into specflow's artifacts and gates without losing its decisions, its implementation evidence, or its approval boundaries. Every path here is relative to this skill's folder. The workflow skill sits beside it at `../spec-workflow/`: its `SKILL.md`, its references, and its helper `../spec-workflow/scripts/validate_spec.py` (run from the repository root) own the gates, the state, the reviews, and the validation; nothing of them is repeated here.

Read `references/conversion.md` before writing anything.

## Activation

- [SR-CNV-001] Run on a request to convert, adopt, or graduate a PRD or a legacy intake item into specflow, given a source the request resolves to one document, or a repository ordering rule that names the next item. The spike path's graduate step belongs to the workflow skill; this skill takes an authored document, never a prototype.
- [SR-CNV-002] When the source is missing or matches more than one document, ask for its path as one question and wait; never pick a match. A repository rule that orders the items may name the next one; a missing roadmap is reported, never claimed followed.

## Steps

1. **Discover.** Read the source, the related specs, the repository's instruction files, the history, and the code and tests it names. Inspect hidden files too (`.config.kiro`, `.specflow.json`). Separate what the source asserts, what the code shows, what the history recorded, and what you verified now. Decide whether this is the adoption of completed work or new work.
2. **Preserve.** Keep the source text and its number, the native artifact shape, the task IDs, the recorded progress, and other tools' metadata, as `references/conversion.md` says. Create or reuse the intake item; it moves to `processed/` only when the requirements are first written.
3. **Requirements.** From here on, load `../spec-workflow/SKILL.md` and follow its `create` or `continue` path with its requirements phase: the obligation map, the review, and the approval come through it.
4. **Design.** The workflow skill's design phase and its design review with the pre-pass, grounded in the actual modules and dependencies.
5. **Tasks.** The workflow skill's tasks phase; a bugfix keeps its fixed order; nothing is executed.
6. **Handoff.** The receipt and the report of `references/conversion.md`.

- [SR-CNV-003] From the requirements step on, load `../spec-workflow/SKILL.md` and follow its create and continue path, every path resolved from the workflow skill's own folder; the phase gates, the state machine, the reference routing, and the approval procedure are the workflow skill's and are not restated or bypassed here. When the host installs skills one by one and the folder is absent, name the `spec-workflow` skill and ask the agent to load it.
- [SR-CNV-004] The installed runtime (`validate_spec.py`) owns the schema, the hashing, and the status derivation: use it for every hash, approval, invalidation, and validation. Never improvise a validator, approximate the canonical hash, invent a workflow version, or claim a portable approval the runtime did not record; without Python 3 the workflow skill's read-only mode applies and a receipt in `qa-log.md` is the most this skill records.
- [SR-CNV-005] Conversion authorizes artifact drafting and reversible organisation only: it starts no implementation, installs no plugin, commits nothing, pushes nothing, and edits no other project's specs. Evidence-only reads during discovery are allowed; a check that executes the task plan or changes production code is not.
- [SR-CNV-027] The handoff reports, as separate lines, the content completion, the implementation evidence, the approvals recorded, the questions still open, and the next action. When the work waits for an answer, say that it is paused, name the question, and name the gate that raised it, in the visible reply; never leave the only open question inside a picker the developer may not see.
