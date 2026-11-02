# Assumption ledger - AP 00013 v2 (autopilot session helpers, corrective plan T1-T4)

Per-plan ledger: replaced at the first completed task of this plan, per the work
skill's assumption-ledger rule. The v1 plan's ledger (tasks 1-15) remains in git
history at the commit before this one.

## 1: Repair staging metadata detection and missing/ungranted review inputs

Test author (Tess), initial authoring:

- The union of granted context kinds is taken over context-reading jobs (alice/bob), not over blake/eve; blake's and eve's granted kinds were kept a subset of alice's in every union test so both readings agree, and the fallback test relies on the "no context-reading jobs" wording of the task.
- A context kind may stay in `allowed_inputs.input_refs` while being granted to no job (the task phrases the rule as "no job was granted"), so `test-results:review` remains in `input_refs` in the union tests.
- The `context-pack` kind's recognisable section in the shared artifact is the pack's "Findings precedent" extract, so the assertion targets a marker placed inside that heading rather than raw pack text.
- The `test-results` kind's section carries the `test_gate_text` value verbatim.
- "A repository whose configuration refuses bare-repository access" is realised through the effective git configuration (a fake global `safe.bareRepository = explicit`), because git ignores that key in repo-local config.
- Refusal reports carry no `artifacts`/`prompts` keys; asserted with `report.get(..., default)` so an extra empty key would also pass.

Test author (Tess), adversarial strengthening:

- An `unsafe-output` refusal carries its message in `detail` (observed: `"artifact_root is inside git internals"`); the assertion accepts `reason` or `detail`, since the requirements name no message field for that behaviour.
- The cause prose for the unanswerable-probe refusal will name git internals/metadata/directory, a probe, or a bare repository; matched as that family case-insensitively after stripping fixture paths, rather than pinning one wording.
- Kind-to-section mapping is asserted only for kinds a caller can grant or ungrant through the fixture ref vocabulary. No `history:` ref kind exists in the fixtures, so `SETTLED` is pinned only in the no-context-reader fallback, where the full kind set is required.
- Blind jobs (blake) never get a per-job context override; the exact-set override assertion encodes that, matching current behaviour.
- The shared artifact is `review-context-<cycle>.md` and a per-job override is `<job>-review-context-<cycle>.md` (existing naming, unchanged by this task).
- `prd:00020` is a valid PRD ref for an otherwise unchanged context (verified by black-box probe).

Test author (Tess), pre-existing-test correction:

- Used `"context-pack:pk1"` as the pack ref literal (the value the new v2 test file already uses); the brief named the kind but not the id.
- Took "context-reading jobs" to mean every roster job except `blake` and `eve`, matching the split `context_for` itself already applies.
- Kept the pack ref literal local to the test rather than adding a module-level constant.

Implementor (Ivan):

- `_missing_prd_grant` is fed `{job: _manifest(expected_context, job) for job in jobs}`. The design contract wrote `context["manifest"]`, which does not exist at that point in `stage_review`; `_manifest` is the identical per-job view `_run_inputs` builds later.
- The precondition sits immediately after the roster job list is read and before the persona-availability check; no test in the verification set exercises both failures at once, so the relative order of those two refusals is unobserved.
- The CHANGELOG entry wording (one line, `**autopilot**:` prefix, effect-level) is the implementor's, placed first under the existing `### Fixed`.

Implementor (Ivan), style-limit fix:

- The style checker counts a function's length from its `def` line through its last body line (the reported 53 matched lines 591-643 of the pre-change file), so the 47-line result clears the limit.
- The choice of which cohesive block to extract was the implementor's: root resolution is the only self-contained, pure, refusal-free block in `stage_review`.
