# Backlog review - agent-plugins - 2026-11-28

Verdict: NO-GO for the complete backlog. AP 00014 is on hold. The independent chain can start with 00085.

## Map

| PRD | Title | Template | Lines before edits | Subsystem | Needs | Verdict |
|---|---|---|---:|---|---|---|
| 00015 | Workflow parity | Standard | 152 | Skills and runners | 00013, 00014 | Blocked on hold |
| 00016 | Controller integration | Standard | 127 | Host client and handoff | 00015, 00020, 00021 | Blocked transitively |
| 00017 | Profile conformance | Standard | 130 | Distribution and certification | 00016 | Blocked transitively |
| 00020 | Controller review | Standard | 137 | Review, custody and waves | 00019, 00085 | FIX |
| 00021 | Controller records | Standard | 131 | Git records and conformance | 00020 | FIX |
| 00085 | Worktree PRD scope | Standard | 171 | Selection and scope CLI | 00019 | FIX |

## Findings

### Blocking

- **00015, Foundation and eligibility (D/G).** Its host execution prerequisite 00014 is in hold. Selection skips 00015, then 00016 and 00017 cannot run. Closing this stall requires completing the held host work under its recovery procedure. Keep the prerequisite.
- **00085, Scoped selection and Phase 1 (B/C).** The current selector returns exactly three fields. Two lifecycle tests compare the entire dictionary. “Unchanged, byte for byte” conflicts with the promised fourth field. Preserve candidate choice and existing field values, and explicitly update the exact-result tests.
- **00085 and 00016, Scoped selection and One controller client (D/G).** The read-only picker checks eligibility. The mutating entry operation independently selects from supplied basenames. Calling it with an unfiltered list can start a different PRD. Require host wiring to pass only the selected basename and submit no entry on refusal or drain.
- **00020, Atomic review acceptance and Phase 1 (G/H).** The source map assigns CLI-121 to 00020. Its acceptance covers review rosters and custody but omits the new default-branch registry rules in intake 00094. Source-equivalence tests alone would preserve the old allocation bug. Carry the settled requirements and local Git acceptance cases into the port. Keep post-loop synchronization outside the controller.
- **00015, Phase 1 task 4 (A/D).** Grounding rejects the named dispatch regression because the PRD does not declare it as new.

### Non-blocking

- **00017, Capability-based profiles; 00021, One extraction artifact (D).** The two other grounding failures name external OVCAQ configuration keys. Verified both in the sibling repository's `docs/operations.md`. Qualify the external citations.
- **00085, Phase 0 acceptance (C).** The pytest expression does not select the named scoped and unscoped selection cases. Require filter coverage at the pure-function boundary.
- **00021, Phase 2 (C).** The tree lists export and provenance tools, but the acceptance allows generating the conformance artifact against yesterday's controller digest. Require the refreshed controller bundle before computing its digest.

### Questions

None requiring new product intent.

## Reshapes

Keep the stable PRD numbers. Both installed and ported selectors skip an ineligible backlog candidate and try the next. Gates deliberately order 00085 before 00020, then 00021 before 00016. No active WIP or duplicate active number. Historical discovery prefixes 00001 and 00011 group related documents and collide with no queued PRD. Each PRD has three phases and fewer than 200 lines. No task was shown to require more than the installed planner's 150K limit after splitting.

## Gaps

The controller cannot synchronize a work branch after the loop exits. The host handoff must carry that obligation. Live Codex/Gemini certification is opt-in and requires actual host credentials. Ordinary CI can record unavailable certification. Publication and cutover require separate work.

## End state after this batch

With the current hold, the reachable work delivers scoped selection, review enforcement and recoverable record commits. Wiring those capabilities into user workflows and certifying the package still depend on the host prerequisite.

## Frontmatter tuning

Keep the existing Opus choices for parity, integration and contracts, and Sonnet for the specified scope behavior. No change to gates, effort lanes or reviewer policy.

## Decisions applied

Applied the six PRD edits described above. In 00015, Phase 1 also now tests the D1-D3 replan defect already required by Foundation. The regression checks prompt-byte splitting and usable estimator capacity after repeated recovery.

Final disposition: 00085, 00020 and 00021 READY in that order. The text fixes for 00015, 00016 and 00017 are complete. One external prerequisite remains open for that chain. Leave all six in backlog so their existing eligibility gates resume work when the prerequisite lands.

Verification: rechecked standard section order, 14 unique-within-PRD feature headings and 31 acceptance-bearing tasks. Both mechanical checks returned zero active findings and zero unverified claims. The repository validator passed for four plugin packages and 16 skills. This check reviewed specifications only. No implementation or live certification ran.
