# PRD-to-specflow conversion contract

The obligations of a conversion, as rules. The artifact shapes, the state, the reviews, the approvals, and the validation are the workflow skill's (`../../spec-workflow/references/artifact-contract.md`, `state-contract.md`, `validation-rules.md`, and `review/`); this file adds only what a conversion does differently.

## Scope and authority

- [SR-CNV-006] Apply the conversion to the document the developer identified. Before creating a spec folder, look for an existing folder with the same number or name and resume it rather than create a second one. A related complete spec found on the way is context only: discovering it authorizes neither its adoption nor the recovery of its approvals.
- [SR-CNV-007] Use the workspace configuration (`.agents/specflow.json`, with absolute, traversal, and out-of-repository paths refused before use) and otherwise the defaults of the artifact contract. Never create a `.kiro/specs` link and never merge competing spec folders in silence; inspect the dotfiles `.config.kiro` and `.specflow.json`, which a plain listing misses.

## Layout and provenance

- [SR-CNV-008] Preserve the source verbatim as `idea.md`, with its existing edits and annotations. A flat legacy intake file moves into a numbered folder that claims no number already taken; a group folder is kept.
- [SR-CNV-009] Move the intake item to `processed/` right before the requirements artifact is first written, fixing the local links the move breaks, and put a `Sources:` line naming the processed source's repository-relative path in the requirements artifact (for a bugfix, at the end of `## Introduction`). "Processed" means specified, not implemented.
- [SR-CNV-010] When the source lives outside the intake tree, leave its native record where it is, copy its text verbatim into the numbered intake folder, and record both paths as provenance in `idea.md`; relocate the original only when the developer or an applicable repository rule authorizes it.
- [SR-CNV-011] Write `.config.kiro` with a new identifier only for a new spec. An existing type marker precedes any inference from file names, and a conflict between declared type or order and the files needs the developer's decision. Preserve native IDs (Kiro's `Requirement N`, `1.`, `3.1`) and unrelated metadata; never renumber a completed native plan to match the four-task bugfix skeleton of new specs.
- [SR-CNV-012] A preserved native shape that fails a runtime check is reported, with the check and the file, and the conversion stops at that gate; the shape is never changed to make the check pass.

## Completed-work adoption

- [SR-CNV-013] Recover the objective facts: the implementation commit, the checked tasks, the artifacts, and the verification records, with where each was read. A historical result implies no fresh run; say so instead of claiming one.
- [SR-CNV-014] Never uncheck verified completed work and never schedule its reimplementation because approvals are absent. Implementation completion and workflow approval are two facts, reported on two lines ("Implementation: complete, by commit X and the checked tasks. Specflow approvals: requirements recorded; design and tasks unresolved."), and the next action names the missing baseline with no code execution scheduled.
- [SR-CNV-015] Recover an approval only from the developer's explicit evidence: an approval to move a file or to continue with another item approves no artifact. Date each recovered approval when it is received; invent no earlier time. When the developer approves every identified artifact as a recovered baseline and the runtime supports it, record each against its current content without a redundant question per artifact; otherwise stop at the first ambiguous gate and ask.
- [SR-CNV-016] Keep Kiro's exact `Current Behavior (Defect)` heading in an adopted bugfix and say nearby that the description is historical and resolved; never rename the heading to express completion.

## Unimplemented conversion

- [SR-CNV-017] Recommend the spec type, the profile, and the workflow order with a one-line reason each: requirements-first unless the input is a design; `standard` for security, concurrency, a public contract, or data integrity. Both profiles keep every artifact and gate. An artifact the runtime already records as approved is resumed, never regenerated.
- [SR-CNV-018] Build the obligation map before drafting: every mandatory obligation of the source maps to a destination clause or to a change the developer approved, and every optional item is resolved one by one into a requirement, an exclusion under `## Out of scope` with its reason, or separately authorized work. A change to a public contract is surfaced in the map and the receipt, never hidden in implementation detail. Keep observations of the code, reproductions you ran, and suspected effects of dependencies apart.
- [SR-CNV-019] Ask one material question per turn, with distinct reasonable behaviours, the recommended one first, no padding, and the user-visible consequence of each in plain words; edit the artifact and the Q&A minutes right after the answer. A choice resolves that question only, never the artifact. At each gate show the document, its scope, the blockers, and the next action, and stop dependent drafting until the approval arrives.
- [SR-CNV-020] A converted bugfix keeps its stable clause numbers in Kiro's shape; converted feature requirements get stable IDs, testable criteria, scope, assumptions, and risks. A contract guess and a deferred answer stay marked as unresolved until settled.

## Design and plan

- [SR-CNV-021] Ground the converted design in the actual modules and the pinned dependencies: read the real transport signatures, version tokens, cache behaviour, and serialisation rather than a permissive mock, and trace a boundary constraint through the caller, the parser, the verifier, and the returned projection. The design phase and the design review of the workflow skill then apply unchanged, pre-pass included.
- [SR-CNV-022] Plan through the workflow skill's tasks phase: a bugfix keeps its four-task order, every slice names its location, dependencies, copied contracts, clause references, and owned check, and nothing is executed. Leave a new task's box unchecked until its own verification succeeds or an accepted exception is recorded, and never weaken a preservation expectation to let a fix pass.

## State, evidence, and done

- [SR-CNV-023] Use the installed helper for every hash, approval, invalidation, and validation; preserve unknown fields of an existing state file, compare the hash read before each write, and leave an existing state file as it is while reporting it unreconciled when an edit may have invalidated it.
- [SR-CNV-024] The conversion is complete when provenance and obligations are preserved, requirements and design are approved, and a reviewed task plan is approved or delivered as the draft the developer asked for. A delivered draft is not an approval; implementation, runtime validation, and cross-host compatibility stay distinct outcomes, each reported on its own.
- [SR-CNV-025] Record the obligation map and the receipt as blocks in the intake item's `qa-log.md`, in the shapes below; the log is append-only, so each stop writes a new receipt, and the last one counts. A pending gate is an honest deliverable: the receipt says what waits and why.
- [SR-CNV-026] `validate_spec.py validate` reads the last `## Conversion receipt` block of the intake log named by the spec's `Sources:` line, from the requirements phase on, and reports an error when one of the labels below is missing or the verdict is not `COMPLETE`, `AWAITING_DECISION`, or `INCOMPLETE`; a spec with no receipt block was not converted and draws no finding. (`conversion-receipt`, error)

```markdown
## Obligation map <date>
- <source obligation> -> <destination clause, or the approved change>

## Conversion receipt <date>
- Source: <repository-relative path>
- Destination: <spec folder>
- Number, type, folders: <...>
- Obligation coverage: <mapped of total; open ones named>
- Decisions and public-behavior changes: <...>
- Implementation evidence: <...>
- Gates: requirements <state>; design <state>; tasks <state>
- Review outcomes: <...>
- Checks run and limits: <...>
- Outstanding questions: <...>
- Next action: <...>
- Verdict: COMPLETE | AWAITING_DECISION | INCOMPLETE
```
