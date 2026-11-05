# AP00013 v3 helper recovery report

Tested package revision: `6888765da6b57ba44e464f9ccfca3e19c1ab1be5` (branch
`master`, HEAD when measured). The previous receipt pinned
`0ed4c17ff964b04104b3961a83a0c8e5563b0f3a`. That receipt now sits whole under
`historical_receipt` in `00013-helper-delivery-receipts.json`.

At the start, `git status --short` showed only three autopilot store files
dirty: `autopilot/dispatch-metrics.jsonl`,
`autopilot/ledger/dispatch-metrics.jsonl` and `autopilot/state.json`. Nothing
under `plugins/`, `tests/` or `tools/` was dirty.

## Scope

Admitted by `00013-v3-admission.md`:

- R1: root-anchored sink symlink refusal (T1).
- R3: descriptor-bound failed-artifact invalidation (T2).
- R4, R6, R9, R12 cluster: the staging git probe fails closed on a timeout or a
  start failure (T3).
- R15, R21 (docs), R20, R23 (receipt accuracy): T4.

## Tasks

| Task | Tests | Fix | Red at v2 | Green | Regression | Devon | Pat |
|---|---|---|---|---|---|---|---|
| T1 | `ebc644d`, `0f4ba03` | `27a16a3` | 48 failed, 42 passed | `test_helper_recovery_v3.py -k sink_alias ...`: 90 passed, exit 0 | 4 sink files: 164 passed in 83.52s, exit 0 | 7 weak points, tests strengthened | 3 LOW, no defect |
| T2 | `47e5f72`, `8efeafe` | `a1aa604` | 16 failed, 4 passed | `test_helper_recovery_v3_artifact.py`: 20 passed in 8.88s | 5 verify files: 226 passed in 152.49s | 5 weak points, tests strengthened and moved to their own file | 2 LOW (dup-failure branch untested; plan Verify line names the old file) |
| T3 | `34e5124`, `1769e8b` | `92e9ccd` | 12 failed, 4 passed | `test_helper_recovery_v3.py`: 106 passed in 10.95s | 4 staging files: 104 passed in 4.45s | 6 weak points, tests strengthened | 3 LOW |
| T4 | none | `6888765` (README, CHANGELOG) | n/a | full gate below | n/a | n/a | n/a |

The orchestrator recorded these task numbers. Tess ran in each task too, but
the record gives no separate outcome for her. The receipt lists the exact
commands. The T1 green command keeps an elision after `-k sink_alias`, because
the record holds it that way. T4 has no task-scoped run, so its receipt entry
holds the full-suite gate run at `6888765`.

Dispatch provenance (v3): Tess, Devon and Ivan ran as native Claude Code
subagents `autopilot:worker-opus`, model parameter `opus`, effort configured
`high` (agent frontmatter). Served model and served effort: not captured. Pat
ran through `use-sonnet/scripts/sonnet-run.sh --effort high`, on the session
setup token after the keychain OAuth route failed with "OAuth token revoked".
Effort configured `high`; served model and served effort: not captured.

V2 task 5 provenance, per v2 review R20: the v2 receipt left this out. Native
workers used `claude-sonnet-5-5` with `medium` effort, and Pat used
`claude-sonnet-5-5` with `high` effort. The receipt records those efforts as
configured. Served effort: not captured.

## Final gate (run at `6888765`, before map regeneration)

| command | exit | result |
|---|---|---|
| `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` | 1 | 24 failed, 1212 passed in 294.06s |
| `python3 -m unittest discover -s scripts` | 0 | 59 tests, OK |
| `python3 scripts/validate.py` | 0 | 3 packages, 15 skills |
| `python3 scripts/generate_marketplace.py --check` | 0 | `marketplace.json` is up to date |

Failing nodes:

- 19 AP 00018 controller nodes: 8 in `test_controller_capacity.py`, 7 in
  `test_controller_owner.py`, 4 in `test_controller_owner_recovery.py`. This is
  an external deferral owned by AP 00018 (admission row R7).
- 5 AP00013 v3 nodes, all digest checks against the committed pre-v3 source
  map. These are the 3 nodes in `test_helper_provenance_real.py`
  (`test_new_helper_files_are_owned_and_digested_from_current_bytes`,
  `test_source_audit_accepts_the_generated_map`,
  `test_generator_check_accepts_the_committed_map`) and 2 `TargetPackageTest`
  nodes in `test_package.py`
  (`test_content_roster_matches_frozen_inventory_and_actual_package_bytes`,
  `test_readme_retains_every_source_heading_with_completed_adaptation_receipts`).

## Source map regeneration

```
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
```

The first two attempts failed, and I fixed the receipt each time:

1. Exit 1: `receipts must be for PRD 00013 and list at least one task`. The
   dispatch asked for `prd: "00013-autopilot-session-helpers-v3.md"`. The
   generator accepts only `"00013"`, so the receipt uses `"00013"`, the same
   value as every historical entry.
2. Exit 1: `receipt task needs a positive integer passed count` for T4. T4 now
   holds the full-suite gate run.

The third run exited 0. `--check` then exited 0. The map diff has 23 insertions
and 23 deletions. All of them are `destination_blob_sha256`, `artifact_sha256`
or `tested_package_revision` values, including the README rows
(`b55c4e4e...` to `60ebfab1...`) and `log_sink_refusal.py`.

## Provenance tests (after regeneration)

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_helper_provenance.py tests/autopilot/test_provenance.py tests/autopilot/test_helper_provenance_real.py tests/autopilot/test_package.py -q
```

Exit 1: **3 failed, 36 passed in 3.91s.**

- `test_helper_provenance_real.py::test_source_audit_accepts_the_generated_map`:
  `Source audit failed: Inventory basis digest mismatch: expanded`.
- `test_package.py::TargetPackageTest::test_content_roster_matches_frozen_inventory_and_actual_package_bytes`
  and `...::test_readme_retains_every_source_heading_with_completed_adaptation_receipts`:
  README digest `60ebfab1...` (current bytes) != `b55c4e4e...` (expected).

The worktree map now holds `60ebfab1...` for the README. Only the committed
HEAD map still holds `b55c4e4e...`. So these tests appear to read the committed
tree, and they may pass once the receipt and map are committed. This is not
verified: the dispatch forbids commits, and the test files are outside my read
list. No receipt or map value was changed to get a result. The other two
stale-map nodes from the gate (`test_new_helper_files_are_owned_and_digested_from_current_bytes`
and `test_generator_check_accepts_the_committed_map`) now pass.

## Deferrals

These are unchanged, as recorded in `00013-v3-admission.md`: R7 (AP 00018
controller nodes), R2, R8, R10, R11, R17, and R14/R18/R22/R24-R27. Rejected
rows: R13/R28-R30, R16 and R19. R5 is resolved by the v3 grant.

## Real host evidence

Real host evidence: not run. No live install or publication was authorized.

## What this report does not claim

It does not claim the full suite is green, that the completion review passed,
that any real host is certified, or that the 3 post-regeneration provenance
failures are resolved.
