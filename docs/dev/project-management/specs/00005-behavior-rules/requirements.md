# Requirements: specflow behavior rules

Sources: docs/dev/project-management/intake/processed/specflow/00005-behavior-rules/

Depends on: 00002, 00004

## Purpose

Make parity measurable: every behavior ported from a personal skill, and every reviewed decision criterion, is a numbered rule with exactly one check, and maintainer CI fails when a rule, a mapping, or a check is missing.

## Scope

The first three tasks of phase 4 of the source plan (T-070, T-071, T-069): the rule inventory and the required-criterion list under `tools/specflow/rules/`, `check_rules.py`, the validator checks for structural rules with their text in `validation-rules.md`, and the session and eval formats. The rule texts in the phase and review references belong to 00006 and 00007; running the evals on hosts belongs to 00009.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Requirements

### RULE-001: Behavior rules and parity

Source: decision 2026-09-27 #4-6; Plan A and Plan B port plans.

**User story:** As a maintainer, I want every ported skill behavior numbered and checked, so that retiring a personal skill never loses behavior silently.

#### Acceptance criteria

1. Every approved port or redesign row in a port plan SHALL map to one or more numbered behavior rules, and every drop SHALL keep its approved ruling. The 33 decision-derived criteria (the 31 listed in design §5.4, plus ART-004.16 and VAL-001.13 by decision 2026-10-04 #12) SHALL also each map to one or more rules and their checks, through a separate explicit required-criterion list. Shared rules and structural/behavioral splits are allowed; a decision citation alone SHALL NOT count as criterion coverage. Rows not yet approved SHALL NOT enter the rules.
2. Behavior rules SHALL live in local files separate from the AWS references, which a catch-up never edits; each rule's text SHALL appear, with its ID, in exactly one distributed runtime file (the skill or one of its references).
3. Each structural rule SHALL be enforced by a validator check, and each behavioral rule SHALL have one scenario eval.

Criterion 4: see 00009.

5. Maintainer CI SHALL fail when an approved row or required decision criterion maps to no rule, the required-criterion list is missing or malformed, a mapping names an unknown criterion, a rule has no check, a check is missing, or a rule's ID is missing from its file or appears in two. These conditions SHALL cover every accepted rule before the first release; no release-slice exemption applies (§9).

Criterion 6: see 00009.

### VAL-001: Workflow validation

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want validation before implementation and handoff so that incomplete or inconsistent specs are caught early.

#### Acceptance criteria

Criteria 1-8: see 00004.

9. Validation SHALL list each marker in an upstream artifact (a `(guess)` outside inline code and fenced blocks, a list item under `## Unresolved questions`, or a list item under `## Open decisions`) that no recorded acceptance covers, so the gate in WF-002.7 can enforce it (decision 2026-10-04 #10).
10. Validation SHALL warn, without failing, on absolute or home-directory paths and on `[[...]]` wiki links in artifacts.
11. Validation SHALL fail an artifact whose code fence is never closed, because fence tracking decides what the hash and the placeholder scan leave out (WF-002.4, VAL-001.8); THE AGENT SHALL NOT record an approval of such an artifact.
12. Validation SHALL warn, without failing, on a requirement in `requirements.md` that has no `Source:` line; a Kiro-made document has none, so the warning never blocks.

Criterion 13: see 00004.

## Risks

- A rule maps to a check whose assertions do not cover its whole obligation: impact h, likelihood m; mitigation: reference authors check every obligation of each criterion against its assertions; fallback: the release review of the 33 required criteria (T-063) rejects the mapping.
