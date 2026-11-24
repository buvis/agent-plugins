# AP00019 Phase 0: Lifecycle/frontmatter/task characterization

Read 2026-11-24 against the live OVCAQ checkout (`~/git/src/github.com/buvis/ovcaq`,
no pinned commit given for OVCAQ by the PRD/design — read at current HEAD),
the AP00018 controller kernel (`plugins/autopilot/controller/autopilot_state/`,
current repo HEAD), and the frozen `claude-autopilot` repo at the design's
pinned commit `f40004a`.

## lifecycle_source_map

| OVCAQ source (function/class) | Destination module (this PRD) |
|---|---|
| `transitions.py`: `TRANSITIONS`, `TransitionRow`, `apply`, `next_phase`, `phase_complete`, `UnknownTransition` | `lifecycle.py` |
| `selection.py`: `sequence`, `selectable`, `select`, `select_from_paths` | `lifecycle.py` (`prd.enter`'s reducer and `lifecycle.select_eligible`) |
| `resume.py`: `resume_target` | `lifecycle.py` (read-only, kept for a future snapshot projection) |
| `records.py`: `require_recovery_idle`, `reset_prd_fields`, `completed_prd_summary`, `complete_prd`, `complete_prd_in_store` (pure bookkeeping half only) | `lifecycle.py` |
| `records.py`: `SagaBoundary`, `_begin_operation`, `_move_operation`, `_record_and_commit`, `_execute_operation`, `stall`, `park`, `defer_record` | `files.py` |
| `policy.py`: `InvalidPlan`, `plan_over_ceiling` (ported unchanged), `validate_plan_shape` (algorithm ported, signature rewritten for string ids / `depends_on`) | `policy.py` |
| `frontmatter.py`: `defaults`, `_block`, `_pairs`, `parse`, `overwrite_warnings`, `apply_to_store` | `frontmatter.py` (ported verbatim; `apply_to_store` is OVCAQ-store-specific and is adapted, not ported byte-for-byte, since this PRD's store transaction shape differs) |
| claude-autopilot (`f40004a`) `cli/selection.py`, `cli/eligibility.py` | `lifecycle.py`'s `select_eligible` (eligibility half) / `frontmatter.py` (`command_for`) |
| (no OVCAQ source) | `jobs.py` — net-new, confirmed nothing elsewhere implements job IDs/claims/exit facts (design's own Explore survey, re-confirmed by this characterization: no `job_id`/`claim_epoch`/`exit_fact` hit anywhere in `plugins/autopilot/` or the legacy CLI pack) |
| (no OVCAQ source) | `files.py`'s `prd.complete` wip/→done/ move saga — net-new; `records.py` and the legacy `workflow_cli.py` were both read in full and neither calls a wip→done move anywhere |

## transition_preconditions

Confirmed by direct read of current source (not from the design doc's prose alone):

- **OVCAQ `transitions.py::apply`** (lines 80-97) calls `require_recovery_idle(state)` first, then explicitly requires `state["batch"]["status"] == "running"` and (except for `("build", "drained")`) `state["work"]["prd"] is not None` — the running-batch/active-PRD precondition is intact in current OVCAQ source.
- **OVCAQ `records.py::require_recovery_idle`** (line 69) raises `RecoveryConflictError` whenever `state["recovery"]["operation"] is not None` — the pre-intent (recovery-in-flight) validation is intact.
- **OVCAQ `records.py::complete_prd`** (lines 178-193) calls `require_recovery_idle` then requires `phase == "done"` AND `"review" in completed_phases` before summarizing/appending — matches the design's citation exactly; this is the guard that makes `false_success_no_advance` hold.
- **Legacy `claude-autopilot` (`f40004a`) `skills/run-autopilot/cli/transitions.py::apply`** (lines 106-118, read via `git show f40004a:...`) derives `phase` from the state dict and looks up the `(phase, outcome)` row — it contains **no** recovery-idle check, **no** batch-status check, and **no** active-PRD check. The design's claim that the legacy CLI's own `transitions.apply` does NOT enforce these preconditions is confirmed by direct read, not assumed.

## Other characterization notes

- `ovcaq/src/ovcaq/workflow/policy.py::validate_plan_shape` (lines 32-80, with its `_task_id` helper at lines 25-29) confirmed to require integer task ids and a `blocked_by: list[int]` key, exactly as the design's Module placement section states — the rewritten signature this PRD needs (string ids, configurable `depends_on`-style key) is a genuine incompatibility, not a design assumption.
- No drift found between the design doc (written 2026-10-25, revised 2026-11-24) and the current OVCAQ/AP00018/legacy-CLI source read this session. Line numbers the design cites for OVCAQ `records.py` (69, 105, 156-175, 178-222, 225, 753, 777) all resolve to the functions the design names, confirmed against the read above.
- `records.py`'s saga helpers (`_prepare_operation`, `_begin_operation`, `_move_operation`, `_record_and_commit`, `_execute_operation`) exist as named; `stall` (line 753) and `park` (line 777) are present and share the same move-staging shape the design describes.
