# specflow spec review - 2026-10-02

Docs: `requirements.md`, `design.md`, `tasks.md` (version 0.2) under
`docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/`.
Scope: all three documents and their cross-references, not design.md alone.
Tier: 2, same basis as the 2026-09-27 and 2026-09-29 reviews.
Scripts: section weight flagged §5.4 (3.2x median), §5.5 (4.3x), §11.3 (7.1x)
and the "Manual upstream refresh" alternative (3.1x) heavy, §6.1, §6.2, §11.2
and the record-tree alternative light; none became a finding (§5.5 grew with
the approved pre-pass). Claim ladder and adversarial scans clean on all three
files (one "configurable" hit in requirements §5, grounded by INT-001.1).
Traceability: every requirement ID maps to at least one task.
Evidence check: CI runner read from `.github/workflows/validate.yml`
(`ubuntu-latest` only); "safety valve" traced to Plan A RDD-17 and
review-discovery-doc `references/lenses.md:9`.

Result: 0 cardinal sins, 4 blocking, 5 non-blocking, 2 questions, 8 low (two
bundles). All 19 resolved by edits; none disputed.

## Minutes

| # | Sev | Finding | Decision | Status |
|---|-----|---------|----------|--------|
| 1 | Blocking | Phase derivation undefined for `intake`, `verification`, `complete`; STATE-001.5 unmeetable | Derivation table in §7.5 keyed on `## Completion criteria` checkboxes; bugfix = task 4; "mark complete" = last box | applied §7.5 |
| 2 | Blocking | Recording observed outcomes (ART-005.6) and exceptions (VAL-002.5) in tasks.md stales the approved plan | `Outcome:`/`Exception:` progress fields dropped from the tasks.md hash; validator warns on them in an unapproved plan | applied §6.4, §6.6, §7.3; WF-002.4, ART-005.6/.9, VAL-002.5; T-022 |
| 3 | Blocking | Accepted upstream markers and "deferred decision" had no machine shape; §7.6 blockers uncomputable | `acceptedMarkers` `[{artifact, line}]` on the design/tasks approval, exact-line match, lapses with the approval; markers = `(guess)`, `## Unresolved questions` items, `## Open decisions` items | applied §7.1, §7.2, §7.6, §13; WF-002.7, VAL-001.9, STATE-001.2, STATE-002.3; T-021 |
| 4 | Blocking | Eval format defined in T-056 (Phase 7) after Phase 4/5 tasks must write eval records for `check_rules.py --area` | New T-069 (session/eval schemas, Phase 4, after T-070); T-056 keeps the runners; T-030 depends on T-069 | applied execution rules, T-069, T-030, T-056 |
| 5 | Non-blocking | Design-First acknowledged (WF-001.7, §6.5, §8) but contradicted by WF-001.3, ART-003.1, §6.3, §5.5; create path undefined | Full support: order chosen at intake (WF-003.10), upstream-relative gates, reversed traceability (requirements name design elements), mirrored §7.4 graph | applied WF-001.3/.4/.7, WF-003.10, ART-003.1/.3, REV-001.2; §5.1, §5.5, §6.3, §6.5, §7.4, §15; T-023, T-031, T-032, T-033, T-050 |
| 6 | Non-blocking | T-035/T-036 instructions had no file; no rule area for implementation, verification, validation rules | `phases/implementation.md` (IMP), `phases/verification.md` (VER), `validation-rules.md` (VAL) | applied §3, §5.2, §5.4; T-035, T-036, T-071 |
| 7 | Non-blocking | Windows without Python is read-only and cannot relink; prerequisite unstated | Python 3 named as prerequisite in Portability, §5.3, §12, §13; status prints the hint | applied; T-037, T-045 |
| 8 | Non-blocking | First release waited on the parity gate (T-060 ← T-058) | T-060 depends on T-056; T-058 feeds only T-067 | applied T-060 |
| 9 | Non-blocking | INT-001.2 flat intake path vs §6.7 grouping and this spec's own path; group on move unstated | One optional group level, kept on the move; `Sources:` names the full `processed/` path | applied INT-001.2; §6.7; T-029 |
| 10 | Question | "safety valve" undefined (§5.5) | Defined inline from RDD-17 | applied §5.5 |
| 11 | Question | No fallback if Kiro IDE ignores the `.kiro/specs` link | Fallback named: drop `specsDir`, `relink`, link guards; specs in a real `.kiro/specs/`, `root` still moves intake and reviews | applied §6.7; T-027 |
| 12a | Low | UTF-8 BOM changes the hash | `canonical` drops a leading BOM | applied §7.3 |
| 12b | Low | Placeholder scan would fail requirements.md's own line naming the banned tokens | Placeholders count outside inline code and fences | applied VAL-001.8 |
| 12c | Low | `$schema` URL decision untracked | T-062 decides and sets the three URLs | applied §7.1; T-062 |
| 12d | Low | T-028 names a Windows CI runner the workflow lacks | T-028 adds a `windows-latest` job | applied T-028 |
| 13a | Low | T-001 "exactly one distributable root" breaks with a second plugin | Scoped to specflow | applied T-001 |
| 13b | Low | T-020 omits ART-005 | Added | applied T-020 |
| 13c | Low | `generatedAt` in the lock breaks byte-for-byte regeneration | Field dropped | applied §10.1 |
| 13d | Low | Helper exit codes unnamed | 0/1/2/3 enumerated | applied §5.3; T-026 |

## Outside this spec

- The autopilot plugin's `enforce_prd_location.py` blocked every edit under
  `intake/` (its vocabulary lacked `intake`). Fixed at source in
  claude-autopilot (9815f62 fix, 0fdfe71 style): fail-first test
  `hooks/test_enforce_prd_location.py`, wired into `dev/bin/release-checks`,
  changelog entry. Release 0.6.1 aborted inside release-checks on a
  pre-existing failure (`skills/run-autopilot/cli/test_loop_prose.py:37`,
  stand-down prose rewritten by c8bbe2b, PRD 00236); nothing was pushed,
  tagged or bumped. The installed 0.6.0 copy carries the same one-line change
  until the next plugin update. Plan A's cutover row for this hook and
  `working-documents.md` stands.
- The autopilot loop running in claude-autopilot stood down on the formatter
  edit between the two commits (observer session claude-autopilot-83); this
  session makes no further writes to that repo.
