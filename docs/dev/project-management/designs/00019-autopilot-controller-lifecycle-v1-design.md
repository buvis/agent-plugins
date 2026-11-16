# Design: Autopilot controller lifecycle, tasks and job plans (AP00019)

## Architecture fit

Targets `plugins/autopilot/controller/autopilot_state/` — the AP00018 kernel
package (done, pinned `1d83b89`). AP00018 shipped `schema.py` (bounded
decode/validate), `store.py` (`StateStore`, locked `transaction`),
`actors.py` (`PrivateLayout`, credential/intent primitives), `owner.py`
(lease acquire/release/recover saga), `protocol.py` (request envelope,
`validate_payload`, `apply_locked` dispatcher, `public_contract`), `paths.py`
(symlink-proof root resolution) and `main.py` (CLI). The contract
(`plugins/autopilot/contracts/controller/workflow-v1.json`) already reserves
every operation this PRD implements under `x-controller.reserved_operations`,
mapped to capabilities `workflow.lifecycle.v1`, `workflow.tasks.v1`,
`workflow.policy.v1` and `workflow.jobs.v1` — all four currently listed in
`unavailable_capabilities`. This PRD's job is to implement those four
capabilities and move them from unavailable to available; it does not touch
`workflow.reviews.v1`/`workflow.custody.v1`/`workflow.verification.v1`/
`workflow.records.v1` (AP00020/00021).

The extraction source is **OVCAQ** (`~/git/src/github.com/buvis/ovcaq`,
`src/ovcaq/workflow/`), per `designs/00011-autopilot-standalone-design.md`
line 44 ("OVCAQ at cf8be72 has tested atomic state, locking, lifecycle
intents/recovery, policy and records. Extract workflow portions"). OVCAQ's
`records.py` saga (`SagaBoundary` crash-point enum, intent→verified-move→
append→commit→cleanup) is the one correct shape for file-intent recovery —
not the legacy `claude-autopilot` CLI pack's `shutil.move`-based `_select`,
which lacks crash-point granularity and (per its own `transitions.py`) omits
the running-batch/active-PRD preconditions OVCAQ's `transitions.apply`
enforces. Those preconditions and the `SagaBoundary` crash points are the
"cf8be72 guards" the PRD (line 32, line 87) says to preserve.

Discovery `00003-workflow-entry-and-lifecycle-ownership.md` (OVCAQ, open,
2026-10-19) is the requirements source behind the PRD's wording: one verb
enters a PRD (wip-first-then-backlog, verified move, atomic commit, replay-
safe), one verb closes it (wip→done, recorded in `batch.completed_prds`),
`select` never re-offers a completed PRD, `phase-complete` refuses without a
running batch and active PRD, `stall`/`park` verify the file's actual bucket
before stamping intent, and no operation is an arbitrary state setter. This
design adopts discovery 00003's two open questions explicitly (§ Risks).

## Module placement

New files (all under `plugins/autopilot/controller/autopilot_state/`, ported
from OVCAQ's pure/saga functions, re-expressed as closed operations over
`StateStore.transaction`, never as a parallel engine):

- `lifecycle.py` — ports OVCAQ `transitions.py` (`TRANSITIONS` table,
  `apply`, `phase_complete`), `selection.py` (`sequence`, `selectable`,
  `select`), `resume.py` (`resume_target`), and the entry/exit half of
  `records.py` (`require_recovery_idle`, `reset_prd_fields`,
  `completed_prd_summary`). Implements `prd.enter`, `phase.handoff`,
  `prd.complete`.
- `files.py` — ports OVCAQ `records.py`'s saga machinery: `SagaBoundary`,
  `_execute_operation`/`_begin_operation`/`_move_operation`/
  `_record_and_commit`, and the public `stall()`/`park()` entry points.
  `lifecycle.py` and `tasks.py` call into `files.py` for every operation that
  moves a PRD file or appends a defer/audit record; no other module touches
  the filesystem directly. Implements the file-move half of `prd.stall`,
  `prd.park`, `prd.defer`.
- `tasks.py` — new (no direct OVCAQ analog: OVCAQ has no task-list concept
  yet). Implements `task.replace`, `task.start`, `task.finish`,
  `task.attempt` as pure reducers over `workflow.tasks`, validated by
  `policy.validate_plan_shape`.
  `tests/autopilot/test_controller_tasks.py` is added to the PRD's own test
  list (the PRD names `test_controller_lifecycle.py`/`test_controller_jobs.py`
  /`test_controller_recovery.py` but every `task.*` operation needs its own
  file; grouping task tests into `test_controller_lifecycle.py` would bury
  them under lifecycle's own lease/saga tests).
- `frontmatter.py` — ports OVCAQ `frontmatter.py` verbatim (`parse`,
  `defaults`, `_block`/`_pairs`, `overwrite_warnings`): pure parsing, no
  store write of its own. `lifecycle.py`'s `prd.enter` calls `parse` and
  writes the resulting fields as part of the entry transaction (closing
  discovery 00003's first open question: frontmatter is stamped **inside**
  `prd.enter`, not a separate verb — see § Risks).
- `policy.py` — ports OVCAQ `policy.py`'s **algorithms**, not its code
  verbatim: `InvalidPlan` and `plan_over_ceiling` port unchanged, but
  `validate_plan_shape`'s DFS cycle check must be rewritten against this
  PRD's own id/dependency fields. OVCAQ's real `validate_plan_shape`
  (`ovcaq/src/ovcaq/workflow/policy.py:25-32`) requires integer task ids
  and reads dependencies from a `blocked_by: list[int]` key — incompatible
  with this design's `TaskRecord.id: str` / `depends_on: list[str]` and
  `JobSpec.job_id: str` / `depends_on: list[str]` (§ Interfaces). The
  rewritten `validate_plan_shape(items, *, id_key="id",
  depends_key="depends_on")` keeps the same DFS cycle-detection algorithm
  over string ids and a `depends_on` key, parameterized so `task.replace`
  and `job.plan` both call it. Implements `policy.bind` (binds a lane
  decision to `workflow.work.lane*`) and `lane.route` (the lane
  classification call `tasks.py`/`lifecycle.py` consult before admitting a
  plan). Pure; no saga, no file I/O.
- `jobs.py` — new (net-new build against the reserved `workflow.jobs.v1`
  contract surface; no legacy code to port — confirmed by the Explore survey
  above, nothing elsewhere implements job IDs, claim exclusivity or exit
  facts). Implements `job.plan`, `job.claim`, `job.record_exit`.

Edited files:

- `schema.py` — `_WORKFLOW`'s five reserve keys (`batch`, `work`, `tasks`,
  `recovery`, `jobs`) stop being frozen at their initial values for the
  operations this PRD defines. `validate_state` currently hard-fails any
  write that changes `workflow` from `_WORKFLOW` (line 253); this PRD adds
  per-key shape validators (`_batch`, `_work`, `_task`, `_recovery_op`,
  `_job`) called from a revised `validate_state` that checks each key's
  *shape* instead of its *identity-equals-default*, while every key AP00020/
  AP00021 still own (`review`) keeps the exact frozen-default check.
- `protocol.py` — `public_contract()`'s `operations`/`capabilities` lists
  grow to include the twelve ops below and `workflow.lifecycle.v1`/
  `workflow.tasks.v1`/`workflow.policy.v1`/`workflow.jobs.v1`.
  `validate_payload` grows one `elif` branch per operation (payload shape
  below). `apply_locked` grows a dispatch branch per operation, inserted
  **before** the `workflow.open` fallback at line 199 and **after** the
  existing intent/owner-operation checks at lines 187-198 — a pending
  lifecycle/task/job intent must resolve through the same
  `actors.read_intent`/`finish_bootstrap`-shaped path owner operations use
  today, not a second intent mechanism.
- `plugins/autopilot/contracts/controller/workflow-v1.json` —
  `implemented_operations` gains the twelve names below;
  `unavailable_capabilities` drops `workflow.lifecycle.v1`,
  `workflow.tasks.v1`, `workflow.policy.v1`, `workflow.jobs.v1`.
  `fixtures-v1.json` gains one fixture per new operation.
- `plugins/autopilot/contracts/controller-v1.json`,
  `plugins/autopilot/README.md`, `plugins/autopilot/CHANGELOG.md` —
  regenerated by `tools/autopilot/export-controller-contract.py` and hand
  edits, per the AP00018-closeout pattern (design's own Phase 2 task 2: mint
  last, pinned to the README/CHANGELOG commit).
- `tools/autopilot/source-map.json` — regenerated by
  `tools/autopilot/update_helper_map.py` in the same closing commit.

## Interfaces & contracts

### Operations and payload shapes (`protocol.validate_payload` branches)

All twelve operations require `workflow_id`/`actor_id`/`lease_epoch` bound
(i.e. they run through the same `actor_binding` check as `owner.release`
today — a lifecycle/task/job mutation always requires an authenticated actor,
never an unbound `workflow.open`-style request).

- `prd.enter` → `workflow.lifecycle.v1`.
  Payload: `{"prds": list[str]}` — candidate basenames already confirmed
  present in `wip/` or `backlog/` by the caller; the controller does not scan
  the filesystem itself (that stays the plugin skill's job per the PRD's "no
  arbitrary state setters" line — the controller only records which file was
  entered and the saga intent that moved it, it does not decide eligibility
  or discover candidates).
  Reducer: `lifecycle.select(workflow_tasks=[], prds=payload["prds"])` (ports
  OVCAQ `selection.select`) picks wip-first-then-backlog-lowest-sequence
  from `payload["prds"]`, skipping any basename already in
  `workflow.batch.completed_prds` (discovery 00003's drain-distinction
  requirement). Result `{"prd": <basename>, "source": "wip"|"backlog"}`; a
  `"backlog"` source routes through `files.begin_move(... boundary=
  SagaBoundary.PRD_MOVE_STAGED)` before the transaction commits
  `workflow.work = {"prd": <basename>, "source": ..., "entered_at": <iso>}`
  and `lifecycle.reset_prd_fields(workflow)` (ports OVCAQ `records.py:105`).
  Replay-safe: **there is no shared receipt helper to extend** — verified
  by reading `protocol.py` in full, the lines 138-149 check lives inside
  `existing_open()`, called only for `operation == "workflow.open"`;
  `owner.py`'s `apply_locked` (owner.py:256-264) writes its own separate
  receipt-cache check for `OWNER_OPERATIONS`, duplicating the pattern
  rather than sharing code. This design follows that same precedent
  explicitly: `prd.enter` (and every other new operation below) implements
  its own receipt lookup/cache — check `current["receipts"].get(
  request["request_id"])` first and return the cached response verbatim
  on a digest match, exactly as `owner.py`'s branch does — rather than
  assuming a generic mechanism absorbs it. `test_controller_lifecycle.py`
  covers this per operation (§ Test strategy outline).
  Error: `rejected_evidence` when every candidate in `payload["prds"]` is
  already in `completed_prds` (empty-eligible-queue drain, PRD line 32).

- `phase.handoff` → `workflow.lifecycle.v1`.
  Payload: `{"phase": str, "next_phase": str, "outcome": str}`.
  Reducer: `lifecycle.phase_complete(workflow, outcome)` (ports OVCAQ
  `transitions.phase_complete`) looks up `TRANSITIONS[(workflow.work.phase,
  outcome)]`, applies its `effect` (a pure `(workflow) -> workflow` function
  per OVCAQ's `TransitionRow`), and requires
  `require_recovery_idle(workflow)` first (ports OVCAQ `records.py:69`) —
  this is the "`phase-complete` refuses without a running batch and active
  PRD" guard the legacy CLI's own `transitions.apply` does **not** enforce
  (Explore finding §1), so this port closes that gap rather than
  reproducing it.
  Error: `rejected_evidence` on an unknown `(phase, outcome)` pair or a
  non-idle `workflow.recovery`.

- `prd.stall` / `prd.park` → `workflow.lifecycle.v1`.
  Payload: `{"reason": str, "site": str}` (`site` matches the existing
  `pause_reason.site` vocabulary the plugin skill already writes, e.g.
  `"cap_regression"`, `"design_gate"` — the controller stores it verbatim,
  it does not validate against a closed enum, since that vocabulary is owned
  by the skill layer, not the kernel).
  Reducer: `files.park(...)` (ported from OVCAQ `records.py:777`) stages a
  move-intent `wip/` → `hold/`, verifies the file's actual current bucket
  before staging (discovery 00003's "validate the file is actually in
  `wip/` (or proven in `hold/`) before stamping intent" requirement),
  commits the move and a `defer_record` (ports OVCAQ `records.py:225`) in
  one saga, and clears the intent marker last. `files.stall(...)` (ported
  from OVCAQ `records.py:753`) is the no-move case: it performs **no file
  move at all** — the PRD stays in `wip/` — and only commits
  `workflow.recovery` plus the same `defer_record`, so it needs no intent
  stage/clear at all (there is nothing to recover if it crashes mid-write,
  since `store.transaction` is already atomic). The "saga with intent
  staging" description applies to `park` only; `stall` is a plain
  transaction. A replay of a null-artifact park intent re-verifies the
  destination and either resumes the same saga step or raises
  `recovery_required` — it never silently re-runs from the top (discovery
  00003's "rebind or abort cleanly").
  Error: `recovery_required` when the saga was interrupted and the on-disk
  bucket no longer matches any resumable step; `rejected_evidence` when the
  named PRD is not in `wip/`.

- `prd.defer` → `workflow.lifecycle.v1`.
  Payload: `{"record": dict}` — the deferred-decision JSON object the skill
  already builds (`{"type", ...}` shape, unchanged from the existing
  `batch.skips[]`/deferred-JSON format). Reducer: `files.defer_record(...)`
  appends to the batch deferred JSON through the same saga, no bucket move.

- `prd.complete` → `workflow.lifecycle.v1`.
  Payload: `{}`. Reducer: `lifecycle.complete_prd(workflow)` ports OVCAQ's
  `completed_prd_summary` (`records.py:156-175`) and `complete_prd`/
  `complete_prd_in_store` (`records.py:178-222`) for the pure bookkeeping
  half only — verified by direct read, those three functions never touch
  the filesystem; they append a `CompletedPrd` summary to
  `workflow.batch.completed_prds` and reset `parks_consecutive`. **The
  wip/→done/ file move itself has no OVCAQ source to port** (confirmed: no
  move call appears anywhere in OVCAQ's `records.py` or `workflow_cli.py`).
  This design therefore specifies the move as **net-new**, built the same
  way as `files.py`'s stall/park saga (stage intent, verified
  `Path.rename`, commit, clear intent) but under its own
  `SagaBoundary.PRD_COMPLETE_MOVE_STAGED`/`_COMMITTED` pair, not a reuse of
  stall/park's existing boundaries — it is a third move shape alongside
  stall's (no move) and park's (wip→hold), not a variant of either.
  `lifecycle.complete_prd` ports OVCAQ's precondition too (`records.py:
  178-193`, verified by read): it calls `require_recovery_idle`, then
  requires `workflow.work.phase == "done"` **and** `"review" in
  workflow.work.completed_phases` before calling the move saga — this is
  the one check that makes `false_success_no_advance` (PRD's own named
  error scenario: "prose or exit zero cannot bypass review") actually
  hold for `prd.complete`; dropping it would let a caller complete a PRD
  whose review phase never ran. `lifecycle.complete_prd` calls this new
  `files.py` saga only after that precondition passes, then commits the
  bookkeeping above in the same transaction, then resets per-PRD fields
  (`lifecycle.reset_prd_fields`) while preserving `batch`. Error:
  `rejected_evidence` without an active `workflow.work.prd`, or when
  `phase != "done"` or `"review"` is missing from `completed_phases`.

- `task.replace` → `workflow.tasks.v1`. Payload: `{"tasks": list[TaskRecord]}`
  where `TaskRecord = {"id": str, "subject": str, "status":
  "pending"|"in_progress"|"completed"|"aborted", "depends_on": list[str]}`
  (matching the `_task` schema validator's four-value enum exactly —
  `"aborted"` is a legal `task.replace` input, not only a `task.finish`
  output, so a plan can be submitted with a pre-aborted task). Reducer:
  `policy.validate_plan_shape(tasks, id_key="id", depends_key="depends_on")`
  (the rewritten DFS dependency-cycle check, § Module placement) then
  `policy.plan_over_ceiling(tasks, ceiling=15)`
  unless the PRD frontmatter set `plan_expansion: allow` (payload carries
  `allow_expansion: bool`, mirrored from that frontmatter field); on pass,
  replaces `workflow.tasks` wholesale (planning is a full replace, not an
  incremental merge — matches `/autopilot:plan-tasks`'s own `task-add`-then-
  snapshot pattern). Error: `rejected_evidence` (`InvalidPlan`) on a cycle,
  an unknown `depends_on` id, or an over-ceiling plan without the allow flag.

- `task.start` / `task.finish` → `workflow.tasks.v1`. Payload:
  `{"id": str}` (`finish` adds `"outcome": "completed"|"aborted"`). No
  per-task claim field is needed beyond the blanket actor/lease-epoch
  binding every operation already requires (§ Interfaces intro): only one
  actor can ever be bound to a given `workflow_id`/`lease_epoch` at a time
  (the single controller-held execution lease, `designs/00011...md` line
  62), so two concurrent implementors cannot both hold a valid binding to
  issue competing `task.start` calls — unlike jobs, which are plural and
  concurrent by design (§ Alternatives, option 2) and therefore need their
  own per-job claim field. Reducer: flips the named task's `status`,
  rejecting a `start` whose `depends_on` are not all `"completed"` and a
  `finish` on a task not `"in_progress"`.
  Error: `rejected_evidence` on an out-of-order transition (mirrors the
  false-success guard: a `finish` cannot be issued without a prior `start`
  receipt for the same task in the same lease epoch).

- `task.attempt` → `workflow.tasks.v1`. Payload: `{"id": str, "implementor":
  str, "outcome": "completed"|"aborted"|"stalled"}`. Reducer: appends to the
  named task's `attempts` list (new field on `TaskRecord`, default `[]`);
  purely additive bookkeeping, never a status transition on its own.

- `lane.route` → `workflow.policy.v1`. Payload: `{"prd_frontmatter": dict}`
  (the already-parsed frontmatter fields `lane`, `plan_cards`, etc., not raw
  text — `frontmatter.parse` runs once at `prd.enter` time and the result is
  threaded through, never re-parsed here). Reducer: a pure classification
  function returning `{"lane": "solo"|"fast-track"|"full", "reason": str}`,
  written against the same `cli/lane.py` decision table the plugin skill
  uses today — this PRD ports the table's *result shape* into the
  controller contract; the skill-side `cli/lane.py` itself is untouched
  (out of scope: this PRD does not migrate the skill onto the controller,
  only gives the controller the capability).

- `policy.bind` → `workflow.policy.v1`. Payload: `{"lane": str, "reason":
  str}`. Reducer: writes `workflow.work.lane`/`lane_reason` from a prior
  `lane.route` result. Error: `rejected_evidence` when `lane` is not one of
  the three known values.

- `job.plan` → `workflow.jobs.v1`. Payload: `{"jobs": list[JobSpec]}` where
  `JobSpec = {"job_id": str, "role": str, "depends_on": list[str],
  "input_digests": list[str], "isolation": str, "tier": str, "effort": str}`.
  Reducer: validates `job_id` uniqueness and `depends_on` closure by
  calling the same rewritten `policy.validate_plan_shape(jobs,
  id_key="job_id", depends_key="depends_on")` the Tasks capability uses
  (not a second cycle checker) and appends to `workflow.jobs` as
  `{"spec": JobSpec,
  "claimed_by": null, "claim_epoch": null, "exit_fact": null}`. Deterministic:
  the same `JobSpec` list committed twice (same `expected_revision`) produces
  byte-identical `workflow.jobs` rows — no server-generated field varies
  between replays, matching the PRD's "Plan generation is deterministic"
  line.

- `job.claim` → `workflow.jobs.v1`. Payload: `{"job_id": str}`. Reducer: the
  claim-exclusivity mechanism parallels `owner.py`'s lease-epoch pattern
  (Explore finding §3) rather than reusing `owner.py` itself (different
  domain: a job claim is per-job, an owner lease is per-controller-instance):
  sets `claimed_by = request["actor_id"]`, `claim_epoch =
  request["lease_epoch"]` on the named job **only if** `claimed_by is None`.
  Error: `rejected_evidence` ("already claimed") if not — "only one valid
  claim per job/epoch" (PRD line 39) is enforced by this null-check, not by
  a separate lock.

- `job.record_exit` → `workflow.jobs.v1`. Payload: `{"job_id": str,
  "exit_fact": {"outcome": str, "native_session_id": str | None}}`. Reducer:
  requires the caller's `(actor_id, lease_epoch)` to match the job's
  `claimed_by`/`claim_epoch` (replay-safe idempotent: a second identical
  `record_exit` for the same job returns the stored receipt, never
  re-applies) and sets `exit_fact`. This never spawns, launches, or reports
  on a process directly — the controller only records what the caller (the
  OVCAQ-side execution layer, per `designs/00011...md` line 78: "OVCAQ maps
  neutral roles/tiers to drivers/models... launches processes and records
  normalized execution facts") tells it happened. "Controller never launches
  processes" (PRD line 40) holds structurally: no code path in `jobs.py`
  shells out, forks, or imports `subprocess`.

### Schema additions (`schema.py`)

```python
def _task(value: object) -> None:
    _object(value, {"id", "subject", "status", "depends_on", "attempts"})
    _identity(value["id"])
    if value["status"] not in ("pending", "in_progress", "completed", "aborted"):
        raise SchemaError("invalid task status")
    for dep in value["depends_on"]:
        _identity(dep)

def _job(value: object) -> None:
    _object(value, {"spec", "claimed_by", "claim_epoch", "exit_fact"})
    _object(value["spec"], {"job_id", "role", "depends_on", "input_digests",
                             "isolation", "tier", "effort"})
    _identity(value["spec"]["job_id"])
```

`validate_state`'s workflow check (currently `if workflow != _WORKFLOW`)
becomes per-key: `batch`/`work`/`recovery` accept `None` or a shape-checked
dict; `tasks` accepts a list validated item-by-item with `_task`; `jobs`
accepts a list validated item-by-item with `_job`; `review` keeps the exact
`{"cap": 2}`-or-frozen check since AP00020 still owns it untouched.

## Data flow

1. The plugin skill (unchanged by this PRD) resolves PRD candidates and
   bucket state from the filesystem, same as today.
2. The skill builds a request envelope and calls
   `protocol.execute("apply", root, request_file, actor_file)` — the
   existing CLI entrypoint (`main.py`), unchanged surface.
3. `apply_locked` resolves any pending intent first (owner-operation or
   bootstrap, unchanged), then dispatches on `request["operation"]`: the
   twelve new branches call into `lifecycle.py`/`tasks.py`/`policy.py`/
   `jobs.py`, which either return a pure `(workflow) -> workflow` reducer
   result committed via `store.transaction` directly, or — for the three
   PRD-bucket-moving operations (`prd.enter` from backlog, `prd.stall`,
   `prd.park`, `prd.complete`) — first drive `files.py`'s saga (stage
   intent, perform the verified `Path.rename`, append the defer/audit
   record, commit workflow state, clear the intent marker) before returning.
4. The response shape (`protocol.response`) is unchanged infrastructure.
   Receipt caching is **not** shared infrastructure: each of the twelve new
   dispatch branches implements its own receipt-cache check following
   `owner.py`'s precedent (no generic helper exists today — see § Interfaces,
   `prd.enter`), so replay-safety is a per-operation obligation, not a free
   side effect of adding a branch to `apply_locked`.
5. `job.plan`/`job.claim`/`job.record_exit` never touch the filesystem
   outside `workflow.jobs`; the actual process launch stays entirely outside
   the controller, in OVCAQ's execution layer (out of this PRD's scope, per
   `designs/00011...md` line 78 and the PRD's own "Controller never launches
   processes" line).

## Reuse inventory

- `ovcaq/src/ovcaq/workflow/transitions.py` (`TRANSITIONS`, `apply`,
  `phase_complete`) → ported into `lifecycle.py`, preconditions intact.
- `ovcaq/src/ovcaq/workflow/selection.py` (`sequence`, `selectable`,
  `select`) → ported into `lifecycle.py`'s `prd.enter` reducer.
- `ovcaq/src/ovcaq/workflow/resume.py` (`resume_target`) → ported into
  `lifecycle.py`, backs a later read-only `snapshot` projection addition (not
  required by this PRD's operations but kept alongside its sibling ports so
  a future PRD does not re-port it from scratch).
- `ovcaq/src/ovcaq/workflow/records.py` (`SagaBoundary`,
  `require_recovery_idle`, `reset_prd_fields`, `completed_prd_summary`,
  `complete_prd`/`complete_prd_in_store`, `defer_record`,
  `_execute_operation`/`_begin_operation`/`_move_operation`/
  `_record_and_commit`, `stall`, `park`) → split across `lifecycle.py` (the
  pure reducers, including `complete_prd`'s bookkeeping) and `files.py`
  (the saga/move machinery for `prd.stall`/`prd.park`), per § Module
  placement. **`prd.complete`'s wip/→done/ move is the one exception: no
  OVCAQ source exists for it** (verified by reading `records.py` in full —
  `complete_prd`/`complete_prd_in_store` never call a move), so `files.py`
  adds it net-new, under its own `SagaBoundary.PRD_COMPLETE_MOVE_*` pair
  (§ Interfaces, `prd.complete`).
- `ovcaq/src/ovcaq/workflow/policy.py` (`InvalidPlan`, `plan_over_ceiling`
  ported verbatim; `validate_plan_shape`'s DFS **algorithm** ported, its
  signature rewritten for string ids/`depends_on` — see § Module placement)
  → `policy.py`, reused by both `task.replace` and `job.plan`'s
  dependency-cycle check.
- `ovcaq/src/ovcaq/workflow/frontmatter.py` (`parse`, `defaults`, `_block`/
  `_pairs`, `overwrite_warnings`) → ported verbatim into `frontmatter.py`.
- AP00018 `owner.py`'s lease-epoch acquire/null-check pattern (Explore
  finding §3) → reused as the *pattern* for `job.claim`'s exclusivity check,
  not imported as code (different domain: per-job claim vs. per-instance
  lease).
- AP00018 `paths.py` `resolve_project_root` → reused as-is by any new path
  resolution `files.py` needs; not re-derived.
- `tools/autopilot/export-controller-contract.py` / `update_helper_map.py` →
  reused unmodified to regenerate `controller-v1.json`/the source map in
  Phase 2, same invocation as AP00018's closeout.

Nothing found for job-claim/exit-fact machinery: greps tried
`job_id`/`job.claim`/`job.plan`/`exit_fact`/`claim_epoch` across
`plugins/autopilot/` and the legacy CLI pack (Explore §2) — only the
contract's reserved names and `designs/00011...md`'s prose exist; no prior
Python implementation to port.

## Alternatives considered

1. **Smallest-diff option: implement only `prd.enter`/`phase.handoff`/
   `prd.complete` now, defer `tasks.py`/`jobs.py` to a later PRD.** Rejected:
   the PRD's own Phase 1 scope and acceptance criteria (`job_claim_exclusive`,
   `job_plan_stable`, `no_controller_spawn`) explicitly require Jobs in this
   PRD; splitting would leave `workflow.tasks.v1`/`workflow.jobs.v1`
   unavailable past this PRD's own exit criteria check in Phase 2.
2. **Reuse `owner.py` itself for job claims** (treat a job claim as a
   second kind of lease on the same `owner` field). Rejected: `owner` is
   singular (one controller-held execution lease, per
   `designs/00011...md` line 62); jobs are plural and concurrent by design
   (multiple claimed-but-unfinished jobs coexist). Forcing job claims through
   the single-owner field would serialize work the PRD's own Jobs capability
   exists to parallelize. The pattern is reused; the field is not shared.
3. **Chosen: port OVCAQ's existing pure/saga functions module-for-module
   into the kernel's operation-dispatch shape, and build Jobs net-new against
   the already-reserved contract surface.** This is the design doc's
   baseline (not the smallest diff, larger than option 1) because the extra
   size buys the full Phase 1 scope the PRD requires in one pass, reusing
   OVCAQ's already-tested saga/policy logic rather than re-deriving it, and
   leaves no `workflow.*.v1` capability half-finished at this PRD's own exit
   gate.

## Risks & edge cases

- **Discovery 00003's open question 1** (does `prd.enter` also stamp
  `work_start_sha`/frontmatter, or does a separate verb?): resolved here —
  `prd.enter` calls `frontmatter.parse` and commits the resulting fields in
  the same transaction as the bucket move (§ Interfaces, `prd.enter`). A
  later PRD needing a frontmatter *re*-read (e.g. a `catchup: force` re-run)
  gets its own operation; `prd.enter` itself never re-parses.
- **Discovery 00003's open question 2** (does `build→drained` stay legal?):
  resolved here as **not this PRD's to decide** — `TRANSITIONS` is ported
  verbatim from OVCAQ, including whichever `(phase, outcome)` rows it
  currently defines; this PRD does not add or remove transition rows beyond
  what OVCAQ already has at the pinned extraction commit. A future PRD that
  wants a new transition edits the table explicitly, with its own review.
- **Next likely change 1 (AP00020, Reviews):** `review.record_stage`/
  `review.close` land against `workflow.review` (today frozen at
  `{"cap": 2}`). This design's `validate_state` split (per-key shape checks)
  is what lets AP00020 extend `review`'s shape without touching this PRD's
  `_task`/`_job` validators — the boxing-in risk is contained to one
  function already built for per-key extension.
- **Next likely change 2 (AP00021, Records):** `artifact.record`/
  `records.commit` land against `files.py`'s saga. This design keeps
  `files.py`'s saga generic over *what* is being recorded (an intent +
  verified effect + append + commit), not specific to PRD-bucket moves, so
  AP00021 extends it rather than forking a parallel saga.
- **Job claim without a reconciliation path:** `owner.recover`'s payload
  already carries `reconciled_job_ids` (Explore §4) but `owner.py` today
  only checks `workflow.jobs` truthiness, since `jobs.py` doesn't exist yet.
  This PRD does not wire `owner.recover` to cross-check claimed-but-unexited
  jobs against `reconciled_job_ids` — that wiring is this PRD's natural
  Phase-2-adjacent follow-up, explicitly deferred (not silently dropped):
  `owner.recover` keeps its current truthiness check, which is conservative
  (refuses recovery whenever any job is outstanding, claimed or not) and
  therefore safe to leave as-is until a later PRD tightens it.
- **Deterministic `job.plan` replay vs. its own receipt cache:** since
  `job.plan`'s dispatch branch implements its own receipt-cache check
  (§ Interfaces, `prd.enter`), a replayed `job.plan` with the same
  `request_id` returns the cached receipt rather than re-validating the
  job graph — this is correct (replay-idempotent) but means a caller must
  mint a fresh `request_id` to submit a genuinely different plan, never
  reuse one to "retry with a fix." Existing callers already follow this
  convention for `owner.*`; no new caller behavior is introduced.

## Test strategy outline

- `tests/autopilot/test_controller_lifecycle.py`: `entry_wip_first`,
  `completion_moves_once`, `manual_session_handoff`, `false_success_no_advance`,
  `drained_vs_ineligible`, `require_recovery_idle` precondition refusal,
  `reset_prd_fields` preserves `batch`.
- `tests/autopilot/test_controller_recovery.py`: `interrupted_move_recovery`
  (crash at each `SagaBoundary` point, replay resumes or cleanly aborts, never
  double-moves or double-appends), stall/park bucket-verification refusal.
- `tests/autopilot/test_controller_tasks.py`: `task_attempt_replay`,
  dependency-cycle rejection (`InvalidPlan`), ceiling rejection without
  `allow_expansion`, out-of-order `start`/`finish` rejection.
- `tests/autopilot/test_controller_jobs.py`: `job_claim_exclusive` (second
  claim on an already-claimed job is `rejected_evidence`), `job_plan_stable`
  (identical `JobSpec` list replayed twice yields byte-identical
  `workflow.jobs` rows), `no_controller_spawn` (static check: no
  `subprocess`/`os.exec*`/`os.fork` import anywhere under `jobs.py`),
  `record_exit` idempotent replay.
- All tests build state through temporary `StateStore` roots, never the
  implementation batch's own `state.json` (PRD line 87, AP00018 convention
  already in force for `test_controller_*`).
- Integration: `tests/autopilot/test_package.py` and
  `test_helper_provenance_real.py` must pass against the regenerated
  `controller-v1.json`/README/source-map (PRD Phase 2 task 2's own acceptance
  line) — no path exemption, no test exclusion.

## Review log

- Non-blocker: `job.record_exit`'s `exit_fact` carries no digest of actual produced/consumed resources despite `job.plan`'s `input_digests` emphasis; acceptable for Phase 1 scaffolding since exit facts "never substitute for review acceptance" (PRD). Not fixed; flagged for AP00020/21 if exit-time digest verification is later needed.
dispatch 1 (claude): cardinal-sin 0, blocker 1, non-blocker 2, question 2
- Question (dispatch 2): does `job.claim`'s exclusivity hold across genuinely concurrent actors given the kernel's single owner lease/`lease_epoch`, or does `claimed_by` only disambiguate jobs within one shared binding? Not resolved here — Jobs' execution/claiming model against multiple concurrent actors is this PRD's Phase 1 build-out detail, to be settled when `jobs.py` is actually written and tested against `test_controller_jobs.py::job_claim_exclusive`.
- Question (dispatch 2): `_batch`/`_work`/`_recovery_op` schema validators are named in prose but not sketched as code (only `_task`/`_job` are shown). Deliberate: their field sets (`completed_prds`, `prd`/`source`/`entered_at`, saga-in-flight shape) are exactly what `lifecycle.py`/`files.py`'s implementation pins down; sketching them here would duplicate, not guide, that work.
dispatch 2 (claude-fallback): cardinal-sin 0, blocker 3, non-blocker 1, question 2
- Dispatch 3 (verification): confirmed all three dispatch-2 blocker fixes correct and complete against OVCAQ/AP00018 source — validate_plan_shape's rewritten signature is consistent across all four doc locations, the receipt-cache fix is consistent across all three replay-safety mentions, and prd.complete's precondition is stated both in reducer logic and as an error condition.
dispatch 3 (claude-fallback): cardinal-sin 0, blocker 0, non-blocker 0, question 0
