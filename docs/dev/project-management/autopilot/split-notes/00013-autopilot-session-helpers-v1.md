# Split note: 00013-autopilot-session-helpers-v1.md
planned=11 prd_tasks=5 expansion=2.20 reasons=module_drift

## Recovery — 2026-10-30

Reconciled the PRD's exact file roster with the reviewed design and archived
eleven-task plan (`reports/00013-plan-before-stall.json`). Added the nine
previously unlisted paths without directory-wide grants or new capabilities.
The installed 0.10.0 `cli.policy.plan_expansion` now reports `stall: false`,
`drift: []`, `unfiled: 0`, `override: false`, with 11 tasks and expansion 2.20.
Returned the PRD from hold to backlog. The original gate evidence below is
retained. AP00018 remains paused separately; its unfinished runtime also leaves
the shared full test suite unable to import controller modules, so this repair
alone does not authorize or guarantee a successful backlog run.

## docs/dev/project-management/reviews (UNLISTED)

- 1 Characterize pinned helper semantics and ownership exclusions: docs/dev/project-management/reviews/00013-helper-source-characterization.md

## plugins/autopilot (UNLISTED)

- 2 Extract finding parsing, lead stripping and deterministic grouping: plugins/autopilot/CHANGELOG.md
- 3 Implement advisory AP00012 evidence consistency checking: plugins/autopilot/CHANGELOG.md
- 4 Port read-only dirty-tree and safe artifact path primitives: plugins/autopilot/CHANGELOG.md
- 5 Prepare isolated review artifacts and complete reviewer prompts: plugins/autopilot/CHANGELOG.md
- 6 Prepare authenticated classified review-close proposals: plugins/autopilot/CHANGELOG.md
- 7 Extract regression classification and pure custody proposals: plugins/autopilot/CHANGELOG.md
- 8 Expose stateless optional catchup probes: plugins/autopilot/CHANGELOG.md
- 9 Execute bounded verification and assess explicit artifact reuse: plugins/autopilot/CHANGELOG.md
- 10 Wire versioned local facade operations and controller refusals: plugins/autopilot/CHANGELOG.md
- 11 Record helper provenance and document delivered capability limits: plugins/autopilot/README.md, plugins/autopilot/CHANGELOG.md

## plugins/autopilot/scripts (UNLISTED)

- 2 Extract finding parsing, lead stripping and deterministic grouping: plugins/autopilot/scripts/findings.py, plugins/autopilot/scripts/gate_lead.py, plugins/autopilot/scripts/rework_groups.py
- 3 Implement advisory AP00012 evidence consistency checking: plugins/autopilot/scripts/review_evidence.py, plugins/autopilot/scripts/evidence_shapes.py
- 4 Port read-only dirty-tree and safe artifact path primitives: plugins/autopilot/scripts/dirty_tree.py, plugins/autopilot/scripts/log_sink_refusal.py
- 5 Prepare isolated review artifacts and complete reviewer prompts: plugins/autopilot/scripts/review_stage.py
- 6 Prepare authenticated classified review-close proposals: plugins/autopilot/scripts/review_close.py
- 7 Extract regression classification and pure custody proposals: plugins/autopilot/scripts/cap_check.py, plugins/autopilot/scripts/custody.py
- 8 Expose stateless optional catchup probes: plugins/autopilot/scripts/catchup.py
- 9 Execute bounded verification and assess explicit artifact reuse: plugins/autopilot/scripts/verification.py
- 10 Wire versioned local facade operations and controller refusals: plugins/autopilot/scripts/autopilot.py

## tools/autopilot (UNLISTED)

- 11 Record helper provenance and document delivered capability limits: tools/autopilot/update_helper_map.py
