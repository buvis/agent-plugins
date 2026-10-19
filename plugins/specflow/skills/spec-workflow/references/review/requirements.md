# Requirements review

The `review requirements` intent. Load `references/review/core.md` first; this file adds the target, the context, the five lenses with their profile calibration, the no-HOW check, the severities, and the resolution shapes. The walkthrough, the card, the picker, the minutes, and the recap are the core's.

## Target and context

- [SR-RVR-001] The target is the requirements artifact of one spec, resolved from the spec the developer names (number or title) or the current spec of the conversation; never a free file path.
- [SR-RVR-002] The reviewed artifact is `requirements.md`, or `bugfix.md` for a bugfix spec, whose clauses stand for the criteria in the lenses below. The raw input lives in the intake item and is context, not the target.
- [SR-RVR-003] When the request names one spec, confirm it in the first message: "Reviewing `<spec folder>`. Wrong spec? Say so now." and go on without waiting for an answer.
- [SR-RVR-004] When no spec is named and the conversation holds no current spec, ask which spec, by number or title, as one question; never ask for a path, and never pick a spec yourself.
- [SR-RVR-005] Check that the spec folder and its requirements artifact exist before reading; when either is missing, ask again and quote the error.
- [SR-RVR-042] Read first, and do not review: the intake item (`idea.md` and the other inputs), its `qa-log.md` with the earlier minutes, and, in a Design-First spec, the approved `design.md` the requirements were drafted from. A problem seen in the design is reported as a note for a design review, never as a finding of the requirements.
- [SR-RVR-006] The review is the review step of the requirements phase: it runs on a draft before the requirements approval, or on an approved artifact when asked (the first edit then stales the approval). Its recap enters the approval summary; it records no approval itself.
- [SR-RVR-007] Review the WHAT only. Architecture, interfaces, and failure modes belong to the design review; a requirement-level decision that would corner the future design (a one-way door written as a requirement) is flagged here, at its origin, while the deep reversibility analysis stays with the design.
- [SR-RVR-008] Never invent a requirement the intake item, the answers, or the developer did not surface. A gap becomes a finding whose options the developer chooses; the artifact grows only by the developer's choice.
- [SR-RVR-009] Calibrate every completeness check to the profile: a `quick` artifact is not defective for leaving out a section only `standard` needs.
- [SR-RVR-010] The first move is to read `profile` from `.specflow.json`; when there is no state file, take the profile the intake entry of `qa-log.md` records, and say which you used.

## Lenses

- [SR-RVR-011] Five lenses: completeness, coherence, integrity (inward: the artifact against itself and the template), feasibility and evolvability (outward: against the problem, the repository, and the future). Under `quick`, run the three inward lenses as full passes and not the two outward ones, with the safety valve: a glaring impossibility or lock-in that shows on a single line is still raised. Under `standard`, run all five as full passes.

### Completeness

- [SR-RVR-012] At every profile: `## Purpose` states a concrete problem; at least one requirement has a user story and a numbered acceptance criterion; `## Scope` says where the work stops, and `## Out of scope` is populated (empty negative space is where scope creep enters); the `Sources:` line names the intake item; what the developer confirmed or the agent assumed sits under `## Assumptions` or `## Unresolved questions`.
- [SR-RVR-013] Under `standard`, also: `## Non-functional requirements` for the constraints, `## Assumptions` naming each source (a file path or a Q&A entry, not a vague description), `## Risks` with at least one line, and `## Unresolved questions` present, even when it holds nothing.
- [SR-RVR-014] Do not flag a section the profile does not require; under `quick`, a missing non-functional, risks, or assumptions section is not a finding.

### Coherence

- [SR-RVR-015] Any two requirements or criteria that contradict each other are a blocking finding, cited as the pair.
- [SR-RVR-016] `## Purpose` motivates each requirement: a requirement with no traceable pain in the purpose is scope creep or an unstated assumption, and the finding asks which.
- [SR-RVR-017] Every acceptance criterion belongs to the requirement it sits under and tests that requirement; a success measure that no requirement delivers is orphaned, and a requirement no criterion covers is untested.
- [SR-RVR-018] Nothing under a requirement belongs in `## Out of scope`, and nothing excluded there is needed by a requirement; a misplaced item is a finding that moves it.
- [SR-RVR-019] Check each requirement against the intake item named in `Sources:` and the answers in `qa-log.md`: a requirement that drifted from what the developer wrote or answered is a finding that quotes both.

### Integrity

- [SR-RVR-020] Each acceptance criterion is a testable EARS statement: a trigger or condition, `THE SYSTEM SHALL`, and an observable result. A vague qualifier with no metric or threshold ("fast", "robust", "intuitive") makes it unverifiable; the structural shape is the helper's check, the testability is this review's.
- [SR-RVR-021] Each requirement is testable: a test could fail when it is unmet. A requirement no test could fail is a blocking finding.
- [SR-RVR-022] A constraint under `## Non-functional requirements` is externally imposed and non-negotiable, with its source; a preference smuggled in as a constraint (a language, a library, a style) is a finding that moves it to `## Assumptions` or drops it.
- [SR-RVR-023] An open question that blocks the build is listed under `## Unresolved questions`, not buried in an assumption or a parenthesis; a buried one is a finding that moves it there, where the design approval must accept it by name.
- [SR-RVR-024] Each requirement is singular: a requirement that bundles several needs ("X and Y and Z") is split, since it cannot be traced, cited, or tested as a unit.
- [SR-RVR-025] A requirement that states HOW instead of WHAT (a technology, a storage, a mechanism posing as a requirement) is a finding: the behaviour stays as the requirement, and the choice goes to the design phase through the Q&A log, or stays as a constraint when the developer confirms it is one, with its source. When the smuggled choice is also a one-way door, it is an evolvability finding too.
- [SR-RVR-026] When coherence and integrity both claim a defect, route by the fix: an edit to a single element (a criterion with no number) is integrity; an added or repaired link between two elements (a requirement no criterion covers) is coherence.

### Feasibility

- [SR-RVR-027] Judge the requirement count against the purpose: when a small convenience draws a long list of requirements, the finding demotes the inessential ones to `## Out of scope` or a later spec, and the recap may recommend the `quick` profile for what remains.
- [SR-RVR-028] A single requirement that is really a separate feature is a finding whose resolution is its own spec, with its own number and intake item.
- [SR-RVR-029] A requirement that assumes something that does not exist (a service, a dataset, a capability nobody has built) is a finding; check the repository before raising it, and cite the search.
- [SR-RVR-030] Ask whether the problem is big enough for the requirement count at all; an artifact over-built for the pain it describes is a finding on the set, not on one requirement.
- [SR-RVR-031] When the set is too large for one spec (loosely coupled parts, or a draft past about 200 lines), recommend splitting it into separate specs, each with its own number and intake item; the split itself needs the developer's approval.

### Evolvability

- [SR-RVR-032] A requirement or constraint that encodes a one-way door (a fixed data model, a single-tenant assumption, a vendor, a format, or a protocol stated as a hard requirement instead of an extension point) is a finding at its origin.
- [SR-RVR-033] A closed, fixed list where the purpose or the domain implies growth (an enumeration where a registry is needed, with no extension seam) is a finding.
- [SR-RVR-034] An exclusion under `## Out of scope` that removes a seam a foreseeable later requirement will need (one the intake item, the answers, or the unresolved questions name) is a finding, since reintroducing the seam later costs a redesign.
- [SR-RVR-035] Flag a lock-in only when a named, foreseeable evolution is blocked at redesign cost, with the evidence (the purpose, the domain, the intake item, an unresolved question), never a hypothetical "what if". This lens pulls against feasibility on purpose: the resolution is almost always a cheap seam now, not a built-out feature now.

## Severity

- [SR-RVR-037] Blocking means the finding must be fixed, or disputed with a reason, before the requirements approval: a missing requirement the purpose needs, a contradiction, an unverifiable criterion, a scope that contradicts the purpose, a requirement that is really a separate feature, or a one-way door that walls out a foreseeable evolution.
- [SR-RVR-038] Non-blocking means the artifact is weaker but the design can proceed: a thin `## Risks`, a vague constraint, an exclusion left implicit, a requirement set larger than the purpose warrants but internally sound.
- [SR-RVR-039] A question is a genuine ambiguity that needs the author's intent, mostly from the confusion notes of the comprehension pass.

## Resolution shapes

- [SR-RVR-036] The options of a card take the shape of its lens, keyed to the sections of `requirements.md` and to the phases of this skill: an unmeasurable criterion (rewrite it with a metric or threshold; split it into a measurable criterion and an assumption; add an unresolved question that the design must settle); two requirements that contradict (reword or drop A; reword or drop B; add a constraint that reconciles them); an empty `## Out of scope` (list the exclusions the purpose and the requirements imply; add the one riskiest exclusion and an unresolved question for the rest; add an assumption that the scope is bounded to the requirements listed); an over-scoped set (move the inessential requirements to `## Out of scope`; move the ones that are a separate feature to their own spec; keep a first slice and list the rest under `## Unresolved questions`); a set too big for one spec (split into separate specs; keep one spec and name the slices under `## Unresolved questions`; trim to a first slice and move the rest to a later spec); a one-way door (turn the choice into an extension point; keep it as a default with a documented extension path; add a constraint or an unresolved question that makes the design address the seam), with No edit accepting the lock-in and recording why.
- [SR-RVR-041] The card below is the output anchor for this review; every card follows it, with the lens, the severity, the location, a body of about three sentences, the impact line, the options, and No edit.

```text
Finding 2 of 6: Nightly digest contradicts the one-minute alert
Lens: Coherence
Severity: Blocking
Location: requirements.md, REQ-001 criterion 2 and REQ-003 criterion 1

REQ-001.2 commits to an alert within one minute of the stock change. REQ-003.1
commits to one email at 22:00 holding the day's alerts. A design cannot satisfy
both for the same alert.

Impact if unresolved: the design picks one silently, and the other criterion
fails at verification.

Options:
1. (Recommended) Immediate alert, nightly summary
   Why: keeps both needs by separating them.
   Edit: in REQ-003, replace criterion 1 with "THE SYSTEM SHALL send a summary
   of the day's alerts at 22:00, in addition to each alert."
2. Nightly only
   Why: the developer asked not to be interrupted.
   Edit: delete REQ-001 criterion 2.
3. Immediate only
   Why: the purpose is to reorder before the shelf is empty.
   Edit: delete REQ-003.
4. No edit (dispute, defer, or accept as is)
   When: the two criteria describe two different alert kinds the artifact should name.
```

## Recap

- [SR-RVR-040] The recap of the core (raised, resolved, disputed, deferred, open; lenses skipped) feeds the requirements approval summary; it names each unresolved question the review added and each blocking finding still open, since the approval is refused while one is open and not disputed.
