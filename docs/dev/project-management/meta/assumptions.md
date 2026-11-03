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

## 2: Repair containment-before-read, pre-spawn sink validation, controlled sink failure and policy-output platform/nonblocking behavior

Only the bounded cleanup-containment round is recorded here; the earlier Tess,
Devon, Ivan and de-slop rounds of this task recorded theirs in the reports under
`autopilot/reports/00013-v2-task2-*`.

Test author (Tess), bounded regression round:

- The cleanup path is reached only via a run-log sink write failure, proven empirically: arming a result-artifact write failure reports `sink-write-failed` but the created leaf survives, because a record did reach the writer. The brief's "result-artifact sink" wording is therefore treated as naming the failure slug, not the handle that must raise.
- Children print a chatty summary line in a loop and sleep, so the second log write (the one that raises) lands after the mutation; the gate kills them and `reap` covers every exit path.
- Each case's artifact lives in its own fresh subdirectory under `docs/dev/tmp/` with the parent pre-created by the test, so the parent can be renamed; the leaf never exists before the run.
- "Outside the repository" for the control sentinel means a sibling of the project root inside the pytest temp tree.
- The verification argv may not name the artifact path (doing so is refused pre-spawn as `unsafe-artifact-path` and the child never runs), so fixture paths reach the child out of band through a plan file.
- Devon's full weak-point matrix was not re-applied beyond the four cases: the bounded scope governs, with distinct sentinel bytes, a one-byte near miss, an accept/reject pair, an escaping-error case and a cwd plumbing assertion.

Implementor (Ivan), bounded cleanup fix:

- The per-function limit is 50 lines and the gate to trust is the installed `autopilot/0.10.0` copy, since the repository contains no `check_style_limits.py`.
- `_open_log_sink` must keep returning a bare file object, because the spec's own `break_artifact_sink` wraps its return value; cleanup data is handed back by a separate helper rather than by widening that return.
- An artifact leaf that already existed before the run is owned by nobody, so cleanup removes nothing (preserves the committed prior-bytes behaviour).
- When the pin cannot be taken at all, cleanup removes nothing rather than falling back to a pathname unlink.
- Inode numbers are not recycled within a single run, so `(st_dev, st_ino)` is a sound ownership test on the hosts in scope.

Orchestrator:

- Pat's two mandated review inputs were supplied as two sequential messages in the same resumed conversation rather than one combined render: measured, the combination is 50528 bytes of diff alone against a 50000-byte cap, and excluding a file is forbidden by the same instruction. Rationale and measurements in `autopilot/reports/00013-v2-task2-pat-scope-completion.md`.
- The attempt record's `self_deslop` is stamped `committed:c5ab4ea` because de-slop did run and commit there; its unsupported pipe-close removal was reverted at `43789d8` and the pass was not repeated, per the recovery report.

## 3: Replace implementation-shaped allocation evidence with a behavioral bound

Implementor (Ivan), test-only rewrite:

- The measuring child locates fixtures via `Path(__file__).resolve().parent` (the tests directory) and `SCRIPTS` imported from `test_review_evidence_helpers`, because the task named no path constant to reuse.
- The child runs without `-I`/`-E` on purpose, so an inherited `PYTHONTRACEMALLOC` really does pre-enable tracing and exercise the stop/start requirement.
- `report.get("defects", [])` is used in the child because `defects` exists only on a not-ok report.
- The sensitivity test's ceiling comparison is `>= 1_000_000`, the exact complement of the normal test's strict `<`.

Orchestrator:

- The two failing `test_spawn_failure_is_controlled_and_preserves_outputs[*-False]` nodes in the same file are pre-existing at HEAD `bc1627a` (proven by a stash control run, 2 failed / 2 passed on the pristine file), so task 3's gate is judged on its own two tests. The residue they report (an empty `docs/dev/tmp/run.log` left behind when the spawn fails) is a production defect in the verify path, recorded for the step-7 regression loop and the completion review, not fixed by this test-only task.
