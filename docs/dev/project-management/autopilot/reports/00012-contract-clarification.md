# AP 00012 contract declaration blocker

Task 1 is committed (f39d95e independent source capture, a8a7e4c destination mapping). Task 2 Tess returned before edits; no tests or production changes contributed. Source skill plan-tasks requires exact contract names/types and forbids implementor guessing; Tess rule 10a likewise stops for unspecified data shapes.

The amended reviewed design names the following concepts but lacks a complete normative wire shape:

- expected_context: resolved roster/job bindings, permitted-input manifest, source identities, execution profile, builder/independent session identities.
- reviewer_jobs row structure and logical job IDs, required_rubric_sets and rework_policy nested fields/types.
- source_bindings nested fields; artifact, finding, group, rubric verdict and verification nested fields/types.
- Golden fixture outer container and expect result encoding. Case concepts/name/policy/expected_context/input/expect are named but do not close these models.

Existing tests/autopilot/test_contract.py embodies the superseded incompatible contract. docs/dev/tmp/autopilot/scratch-v1 is explicitly quarantined. Neither can supply normative declarations. The agreed design must be amended with exact nested JSON shapes and receive its required renewed design review before task 2 proceeds. No review cycle or completion is claimed.

Pause is not a cap, provider failure or permission denial. No repair, cap raise or pause clearance is authorized by the unattended host wording alone. Resume through installed run-autopilot recovery/state CLI after resolving this contract decision. Preserve work_start_sha and existing source capture. Remaining tasks stay uncompleted.

Resolved 2026-10-26 in an interactive take-over: the design gained a normative `### Wire shapes` section (exact policy, evidence, expected_context and fixture shapes, the closed defect-code enum and every required fixture case) and passed a fresh three-dispatch review plus two targeted codex re-verifications (its `## Review log` records every finding and the terminal `result: ok`). The pending task bodies were regenerated from the amended Interfaces section with `statectl task-set-body`, the pause was cleared and `phase`/`next_phase` set back to `build` through the state CLI. `work_start_sha` and the committed source capture are unchanged; Task 2 is still pending and no implementation attempt is recorded.
