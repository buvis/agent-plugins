# Suite failures that predate AP 00013 task 11

Measured 2026-11-01 at HEAD `d20093d` (clean worktree): `pytest tests/autopilot`
gives 21 failed, 753 passed. Local master is 187 commits ahead of
`origin/master`. None of the failing commits are pushed, so GitHub CI is still
green. The first push turns the `autopilot` job red unless the failures below
are fixed first.

No test was skipped or marked xfail to hide them.

## 19 controller tests: AP 00018 task 7 never built

- Tests: `test_controller_owner.py` (7), `test_controller_capacity.py` (8),
  `test_controller_owner_recovery.py` (4).
- They are task 7's red-first tests, committed at `b4655fe` on 2026-10-31.
  They have never passed.
- Cause: `plugins/autopilot/controller/autopilot_state/protocol.py:174-175`
  (and 219-220) refuse every operation except `workflow.open` with
  `missing_capability`. No handler exists for `owner.acquire`,
  `owner.release` or `owner.recover`. The CLI prints the error on stdout, and
  the test helper only shows stderr, so the failures read as a bare `1 != 0`.
  The recovery tests fail before the crash hook fires, not because of fsync.
- Not a sandbox effect: the other 96 controller tests use the same flock,
  fsync and crash machinery and pass in the sandbox.
- Owner: AP 00018 (on hold). Replan 2 stalled because its 55000-token task
  floor is above the 40000 cap (`autopilot/reports/00018-replan2-budget-stall.md`).
  The fix is to implement task 7, not to change a test.

## 2 package tests: map and pins not updated

`test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes`:

- 13 AP 00013 helper scripts have no `assets` rows. AP 00013 task 11 adds them
  (generator `tools/autopilot/update_helper_map.py`; checked by the untracked
  `tests/autopilot/test_helper_provenance.py`).
- 10 AP 00018 files have no rows: `contracts/controller/{fixtures-v1,workflow-v1,provenance}.json`,
  `controller/main.py`, `controller/autopilot_state/{__init__,schema,store,paths,protocol,actors}.py`.
  AP 00018's own registration task (replan-2 task 9) never ran. AP 00013
  deliberately excludes them (`test_helper_provenance.py:716`). No one owns
  this now.
- The test pins the AP 00012 owners: count 21 and `OWNER_SHA` (lines 28,
  192-194), and only `delivery_prd == "00012"` (line 199). Task 11's 13 new
  owner rows with `delivery_prd` "00013" fail it at line 267. No task
  schedules this pin update.

`test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy`:

- `FORMATS` (line 23) still lists the 3 `review-*` IDs. AP 00013 task 10 added
  7 operation IDs, and `--list-capabilities` returns 10. Line 242 also needs
  each ID named in `plugins/autopilot/README.md`, which names none of the 7 new
  ones. No task schedules the `FORMATS` change. Task 11's README edit has to
  name all 7.

## Required before AP 00013 can close or master can be pushed

1. Done in AP 00013 task 11 (`fbbdc3f` and before): helper rows, the
   `test_package.py` owner pin, the capability list and the README IDs.
2. Done in `4cb0ff7`: asset and owner rows for the 10 AP 00018 files
   (`delivery_prd` 00018, evidence `planned`). Task 11 had added
   `test_helper_provenance_real.py` assertions that banned every controller
   row from the committed map, so no one could satisfy the package roster
   test. They now check that AP 00013 never claims a controller row.
   Each AP 00018 task that changes one of these files must refresh its digest.
3. Open: AP 00018 tasks 7a-7d (`plans/00018-replan-3.md`) make the 19
   controller tests pass. Until then they stay red on purpose, and pushing
   master publishes a red CI job.

Measured after `4cb0ff7` (2026-11-02): 19 failed, 801 passed. All 19 are the
controller tests above.
