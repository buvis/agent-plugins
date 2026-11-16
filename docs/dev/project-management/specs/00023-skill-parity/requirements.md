# Requirements: source-skill parity

Sources: docs/dev/project-management/intake/processed/specflow/00009-cross-host-validation/qa-log.md

## Purpose

Backlog, not approved for execution. Deferred from spec 00009 by the developer's
2026-11-16 option A decision. No personal skill may retire until this gate passes.
This is not a gate for completion of 00009 or the first specflow release.

## Requirements

### PAR-001: Preserve behavior before retirement

Source: 00009 RULE-001.6 and REL-002.7, approved scope decision 2026-11-16.

1. Compare elicit-requirements, review-discovery-doc, review-design-doc, spike,
   create-prd, and review-prd-backlog against specflow on identical fixture inputs
   and developer turns for every mapped behavioral rule.
2. Run source skills in their normal Claude Code profile; keep source evidence
   separate from specflow's isolated, revision-bound evidence on all supported hosts.
3. Judge every mapped rule with the same model judge and require developer review
   of every model failure and the approved PASS sample, including disagreement escalation.
4. Write six reports under tests/specflow/parity, listing each mapped rule, source
   result, specflow result per host, evidence revisions, and readiness verdict.
5. The developer reviews all six reports. A skill may retire only when every
   mapped rule passes on specflow on every supported host, even if the source fails.
6. create-prd and review-prd-backlog also require the autopilot repoint before retirement.
7. Document run procedures in tests/specflow/evals/README.md and tests/specflow/parity/README.md.

## Carried gate procedure

Carried intact into the new backlog spec; required before any skill retirement, not before completing 00009 or release 0.1: per source skill covered by RULE-001.6:

1. Collect the inputs: the fixture and the developer turns of each session whose evals carry the skill's rules.

2. Run the source skill by name on Claude Code with `claude -p --setting-sources user` in the normal profile (R3). Use source-skill paths rather than specflow assertion paths.
3. Run specflow on every supported host with the same inputs and its isolated profile.
4. Score each mapped rule with the same model judge. Apply R2 human review to failures and sampled passes.
5. Record, per rule, the source result and specflow's result per host in `tests/specflow/parity/<skill>.md`.
6. Have the developer review each of the six per-skill reports. The skill may retire only when every rule mapped from it passes on specflow on every host. A rule the source skill fails still has to pass on specflow: the rule is the contract, not the old behavior.

The retirement PRD in `buvis/agent-skills` cites these reports (Plan A "Retirement"). create-prd and review-prd-backlog also wait for the autopilot repoint (`qa-log.md` Q2).

