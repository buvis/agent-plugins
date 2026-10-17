# Design phase

Load this reference to draft or revise `design.md`, with `references/aws/design.md`, reading only the AWS passages marked with the active profile or `[both]`. Questions follow the shared dialogue rules in `references/artifact-contract.md` (`## Shared dialogue`); the approval summary is the one defined there. Record an approval by the procedure in `references/state-contract.md`.

## Before drafting

- [SR-DSN-014] Resolve the active spec, and stop to ask when more than one could be meant. Draft only from an approved upstream: the approved `requirements.md` in Requirements-First, the intake item in Design-First. When the requirements are a draft or stale, say so and draft nothing. Read the upstream in full and the repository instructions that apply to the affected paths.
- [SR-DSN-015] An open marker in the approved upstream (a `(guess)`, an unresolved question, an open decision) never blocks drafting. It blocks the design approval until the developer accepts each one by name; the acceptance is recorded with the approval.

## Drafting

- [SR-DSN-018] A feature design keeps every heading of `templates/design.md`, under `quick` too; a section that does not apply reads `Not applicable: <reason>`. A bugfix design and an existing Kiro-native design keep their own shape and put reuse, placement, and contracts inside their matching sections. Drafting the design never changes the requirements or the tasks.
- [SR-DSN-001] `## Context and constraints` holds the relevant code, its conventions, the integration points, and similar implementations, each with its file path; under `quick`, only what the change touches.
- [SR-DSN-016] Before proposing new code, search for each capability under verb and noun synonyms, and check an empty search with a term you know is present. `## Reuse inventory` names each helper's path and how to use it, or, when nothing matches, the searches you tried.
- [SR-DSN-004] When the scan found more than one pattern the change could follow, ask which one. Under `quick`, the design names the existing pattern it reuses and why no broader design is needed.
- [SR-DSN-010] `## Architecture` fits the change to the existing layers and modules; `## Data model` holds the data shapes; each technology decision carries its rationale and trade-off.
- [SR-DSN-017] `## Module placement` names repository-relative file paths and marks each new or edited. `## Components and interfaces` gives the exact signatures, types, enums, field names, kinds, and thresholds that apply, ready to copy byte for byte into task contracts.
- [SR-DSN-005] `## Components and interfaces` holds one block per module: what it maps to, its responsibility, and its exports, each traced to requirement IDs.
- [SR-DSN-003] When the approach is a real choice, ask one question with two or three approaches and their trade-offs; the answer goes into `## Alternatives considered`.
- [SR-DSN-002] `## Alternatives considered` gives two or three options, the smallest diff among them, the choice, and the reason for each rejection; a larger choice says what its added size buys.
- [SR-DSN-012] When new code is proposed for something an existing library, tool, or service could plausibly do, that option is among the alternatives with the reason it was taken or rejected; when this host cannot search for one, the design says it was not checked.
- [SR-DSN-006] `## Testing strategy` covers the happy path, the edge cases, and the error cases.
- [SR-DSN-009] It names the critical test scenarios per module (happy, edge, error, integration), each traced to a requirement ID.
- [SR-DSN-008] It states the mix of test kinds. A coverage target is optional, never required.
- [SR-DSN-007] `## Risks and edge cases` lists each technical risk with its mitigation.
- [SR-DSN-011] Each risk line has impact, likelihood, mitigation, and fallback, and the section adds two or three likely next changes, with what limits each one.
- [SR-DSN-019] `## Requirement traceability` maps each material design element and test to the criterion IDs it covers, in a column headed `Criteria`. A Design-First design reads `Not applicable: Design-First` there, since its requirements name the design elements instead.

## Bugfix designs

- [SR-DSN-020] Before drafting a bugfix design, under either profile, read the code around the defect: the function the reproduction reaches, its callers, and its tests. Name what you read in `## Bug Details`.
- [SR-DSN-021] Write the bugfix design from `templates/bugfix/design.md`, in its shape: the bug condition (here, or already in `bugfix.md`), `## Hypothesized Root Cause` with the evidence for each cause, `## Correctness Properties` with a fix property whose `Validates:` line names the `2.x` clauses and a preservation property naming the `3.x` clauses, `## Fix Implementation`, and `## Testing Strategy` covering exploration, fix checking, and preservation checking. The root cause stays a hypothesis that task 1 tests. Under `quick`, trim the prose, never a section.

## Approval

Run `validate_spec.py validate <spec-dir> --phase design` and fix what it reports. When the review references are installed, hand the draft to the design pre-pass and the interactive design review before the approval summary; a repair edits this design and reopens its gate, and no copy of the design is made. Review minutes go to the intake item's `qa-log.md`.

- [SR-DSN-013] At the design approval in a Git repository, pass the explicit file paths of `## Module placement` (or the matching placement section of a native or bugfix design) to `code-baseline`, and record the result as `approvedCode`, by step 3 of the approval procedure. On resume and before implementation, report the code-drift warnings `status` gives, path by path; they close no gate. Never refresh the baseline without a new design approval.
