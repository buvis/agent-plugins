# AP00018 v2 Task 2 reuse verification

Date: 2026-11-09. Verdict: **blocked: publication-guard equivalence fails**.
No runtime, state, receipt, custody, source-map, or historical delivery evidence
was changed. No extraction was replayed and no historical completion flag was
imported.

## Pinned comparison

Compared bounded AST/symbol sections from OVCAQ commit
`cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7`, using `git show`, with the current
`plugins/autopilot/controller/autopilot_state/` implementation. The source
checkout's HEAD was not used. Raw source digests match the independently recorded
Task 9 characterization:

| Pinned source | Observed raw SHA-256 |
| --- | --- |
| `src/ovcaq/state/schema.py` | `1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b` |
| `src/ovcaq/state/store.py` | `b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7` |
| `src/ovcaq/paths.py` | `3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990` |

| Source symbols/invariant | Target comparison and existing evidence |
| --- | --- |
| `StateStore.transaction`, `_commit_pair`, `_publish_bytes` | Lock-scoped decoding/CAS, copied candidate, current revision +1, validation and state/backup publication remain recognizable. Publication guard propagation differs incorrectly, as detailed below. |
| Source exception classes, `DurabilityBoundary` | All eight store exception class ASTs and all six durability-boundary values are identical. Existing tests cover all six injected boundaries, ordinary exceptions and interrupts, pair repair, file fsync failures and explicit unsupported directory fsync. |
| `_read_backup`, `_snapshot`, `_replace_without_hook` | AST-identical. Existing tests cover bounded reads, corrupt current state and aliased artifacts without replacing evidence. |
| `StateStore.restore` | Deliberately tightened in target `_restore_locked`: backup must decode, current/backup `lease_epoch`, `owner`, `actors` and `receipts` must match, and credential intent must be absent. Source did not impose these security restrictions. Existing tests explicitly preserve credential/pair bytes on refusal, allow a security-identical restore at current revision +1, and cover repair boundaries. This is a declared divergence, not full restore equivalence. |
| Source `decode_json`, `validate_state`, `new_state` | Target decoder retains duplicate-key, integer and nonfinite rejection with explicit document/string/depth bounds. Target validation is a closed kernel schema, not the complete source workflow schema. Existing tests cover bool counters, unknown/process fields, immutable workflow reserves, byte limits independent of receipt count, and rejection before copying. Task 9 retains the source-field/deferred-owner inventory. |
| Source path-resolver family → `resolve_project_root` | Target resolves an explicit existing root without ancestor workflow inference; `_inspect_path` and final descriptor/inode checks remain explicit. The six existing path tests cover relative roots, missing/nondirectory roots, symlinked private components and symlinked/hardlinked fixed artifacts. This verifies the named path-test scope, not uninspected `PrivateLayout` creation internals. |
| CAS/process contention | Existing `test_real_process_cas_allows_exactly_one_writer_for_the_same_revision` and `test_real_process_writers_serialize_all_revision_increments_without_lost_updates` passed in the authorized suite. |

## Blocking characterized edge

Pinned `src/ovcaq/state/store.py:126-159` forwards `publication_guard` from
`transaction` into `_commit_pair`. `_commit_pair:313-346` forwards it to both
publications. `_publish_bytes:348-392` invokes the guard after every boundary
hook, including `STATE_TEMP_FSYNCED`, before replacing the state file.

Current `plugins/autopilot/controller/autopilot_state/store.py:158-180` invokes
the guard once before `_commit_pair` and does not pass it through. The target's
`_commit_pair:346-380` and `_publish_bytes:382-426` still contain the guard
plumbing, but this transaction path never supplies it.

Added exactly one focused test,
`StoreTest.test_publication_guard_rechecks_changed_evidence_before_state_replace`,
which invalidates external evidence at `STATE_TEMP_FSYNCED`. The pinned source
would recheck the guard and repair the exact previous pair; the target commits
without raising. The focused test fails with `RuntimeError not raised`.

All existing assertions were preserved. The existing
`test_validation_conflict_mutator_and_publication_failures_preserve_exact_pair`
also expects a successful guard to run exactly once. That assertion needs
explicit reconciliation with the pinned repeated-guard invariant in subsequent
authorized repair. No runtime repair or assertion weakening was attempted here.

## Executed verification

Each command ran once through a subprocess with a 300-second timeout.

Initial authorized suite:

```sh
mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_kernel.py tests/autopilot/test_controller_kernel_adversarial.py tests/autopilot/test_controller_paths.py tests/autopilot/test_controller_schema.py -q --tb=line
```

Exit: **0**. Exact summary: **51 passed in 0.65s**.

Focused characterization after the coordinator explicitly requested one test:

```sh
mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_kernel.py::StoreTest::test_publication_guard_rechecks_changed_evidence_before_state_replace -q --tb=line
```

Exit: **1**. Exact summary: **1 failed in 0.07s**.

No full suite or repository validator was run in this narrowly scoped task;
the coordinator owns the final repository checks. Passing the original suite
does not establish reuse equivalence while the new characterization fails.

ASSUMPTIONS: none

FILES_TOUCHED:
tests/autopilot/test_controller_kernel.py
docs/dev/project-management/autopilot/reports/00018-v2-task2-reuse.md
