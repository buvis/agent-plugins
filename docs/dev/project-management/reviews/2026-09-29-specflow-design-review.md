# specflow design review - 2026-09-29

Doc: `docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/design.md`
(version 0.2, the rewrite that applied the 2026-09-27 and 2026-09-28
decisions; see `qa-log.md` beside it).
Tier: 2, same basis as the 2026-09-27 review (persistent state in user repos,
several host consumers, lifetime over 6 months). The new status output and
config file are new versioned contracts, not changes to existing ones, so no
Tier 3 condition applies.
Scripts: section weight flagged §6.7 (3.1x median), §11.3 (6.4x, a numbered
procedure), and the "Manual upstream refresh" alternative (3.1x) as heavy,
§11.2 (a code block) and the record-tree alternative as light; none became a
finding. Claim ladder and adversarial scans found nothing.
Evidence check: A1 facts re-read at `v2.10.0` in a scratchpad clone (see
`qa-log.md` "Checked at A1 v2.10.0"); this repo's `scripts/validate.py` puts
no limit on skill subfolders, so `schemas/` and `templates/` are allowed.

Result: 0 cardinal sins, 2 blocking, 4 non-blocking, 4 low (bundled). All 10
were resolved by edits; none disputed.

## Minutes

| # | Sev | Finding | Decision | Status |
|---|-----|---------|----------|--------|
| 1 | Blocking | One eval per rule per host, with Kiro IDE and Crew manual-only, makes the parity gate impractical (estimate: hundreds of hand-run sessions per pass, unmeasured) | Shared eval sessions: an eval is one rule's assertions over a named session; a host runs each session once | applied §15; T-056, T-057 |
| 2 | Blocking | `relink` passes a repo-controlled path through cmd.exe (`mklink /J`) on Windows; suspected injection, not demonstrated | Strict path characters `[A-Za-z0-9._/-]`, no `..`, checked on every OS before use | applied §6.7; SEC-002.6; T-028 |
| 3 | Non-blocking | Number-clash rule flagged any intake item and spec with different titles; split semantics conflicted (ELI-59 vs RPB-100) | Clash by kind plus the `Sources:` link; splits get their own intake items (ELI-59 wins) | applied §6.7, §5.5; VAL-001.8; T-029 |
| 4 | Non-blocking | `Sources:` path unspecified while the item moves `new/` to `processed/` in the same step | Move first, then write the `processed/` path | applied §6.7; T-029 |
| 5 | Non-blocking | Spec numbers could reuse buvis PRD numbers during the transition | `numberScan` config key; buvis lists `prds/`, the plugin names nothing | applied §6.7; INT-001.4, SEC-002.6; T-028, T-029 |
| 6 | Non-blocking | Committed `/.kiro/specs` ignore line outlives `specsDir`, so specs in a real folder go untracked | `status` and `validate` fail on a real `.kiro/specs` folder that git ignores | applied §6.7, §13; VAL-001.8; T-028 |
| 7a | Low | `nextTask` keyed on `Depends on:`, which bugfix and Kiro-numbered tasks lack | First unchecked task in document order whose listed dependencies are checked | applied §7.6 |
| 7b | Low | Inventory had no check kind for rules carried by script tests | Add `test:<path>::<test name>` | applied §5.4 |
| 7c | Low | Heading paths keyed two ways; adapters had no depth field | Full `H1 > H2 > H3` paths everywhere; `depth: standard\|quick\|both` on extract entries | applied §10.1, §10.2, §10.4 |
| 7d | Low | Principle 4 said JSON stores the phase, contradicting §7.1 | "JSON stores only approvals, hashes, the hold, and workflow metadata; the phase is derived" | applied §2 |

## Knock-on edits

- `requirements.md`: INT-001.4 (`numberScan`), VAL-001.8 (clash kinds, ignored
  real folder), SEC-002.6 (new: path character rule).
- `tasks.md`: T-028 (schema keys, character rule, ignored-folder check,
  fixtures), T-029 (clash kinds, move-then-write, `numberScan`), T-056 and
  T-057 (sessions).

## Outside this spec (not edited, fence)

- Plan A's Consumer Cutover table has no row for buvis's
  `enforce_prd_location.py` and `working-documents.md` allowing
  `docs/dev/project-management/specs/` (the buvis `specsDir`) next to the
  `intake/` row it already lists. Add it when Plan A is next edited.
