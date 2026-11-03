# AP00013 v2 helper recovery report

Tested package revision: `3c7e2183a194c86d10390a3f2eda5524516ba50a` (branch
`master`). Backend: Claude Code subagent (`autopilot:worker-opus`), model
`opus`. Every number below was measured in this session; nothing is copied from
an earlier receipt.

Working tree at the start: `git status --porcelain` listed only three autopilot
store files as dirty
(`docs/dev/project-management/autopilot/dispatch-metrics.jsonl`,
`docs/dev/project-management/autopilot/ledger/dispatch-metrics.jsonl`,
`docs/dev/project-management/autopilot/state.json`). No file under `plugins/`,
`tests/` or `tools/` was dirty, so the measurements apply to the committed
product bytes.

## What the v2 corrective tasks resolved

| Task | Resolution | Evidence |
| --- | --- | --- |
| T1 | Review staging fails closed on an unanswerable git probe, and the staging grant is scoped. | `c9e8a3f` (`plugins/autopilot/scripts/review_stage.py`, `tests/autopilot/test_review_helpers.py`), tests added in `bfb9da3` and strengthened in `3e259bc`. |
| T2 | Output sinks are proven openable before the verification child spawns, and cleanup drops only the pinned result-artifact leaf the run created. | `4a93821` and `71fb60d` (pre-spawn sink proof), `30e5c5e` (containment of artifact cleanup), tests in `eccf5c6`, `1c6212f`, `964faee`, `2e3dba5`, `0239445`. |
| T3 | Attempt validation allocation is bounded behaviorally, not by an implementation detail. | `c67250b` (`tests/autopilot/test_cap_recovery_helpers.py`). |
| T4 | The plan grant is corrected and the v2 refusals are recorded in the package docs. | `3c7e218` (`plugins/autopilot/README.md`, `plugins/autopilot/CHANGELOG.md`). |

T2 is also the source of the four red nodes recorded below. Its pre-spawn sink
proof changed the observable filesystem contract of the verify path.

## Measured verification

### Helper regression set (19 files)

Command:

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_cap_recovery_helpers.py tests/autopilot/test_cycle1_boundaries_verify.py tests/autopilot/test_cycle1_boundaries_stage.py tests/autopilot/test_cycle1_boundaries_context.py tests/autopilot/test_review_helpers.py tests/autopilot/test_review_helpers_contract.py tests/autopilot/test_review_close_helpers.py tests/autopilot/test_review_close_helpers_gates.py tests/autopilot/test_cycle1_hardening_sinks.py tests/autopilot/test_verification.py tests/autopilot/test_review_evidence_helpers.py tests/autopilot/test_verification_reuse.py tests/autopilot/test_local_paths.py tests/autopilot/test_local_boundary.py tests/autopilot/test_local_boundary_verify.py tests/autopilot/test_local_boundary_state.py tests/autopilot/test_facade.py tests/autopilot/test_helper_recovery_v2.py tests/autopilot/test_helper_recovery_v2_sinks.py -q
```

Result: **4 failed, 544 passed, 0 skipped in 188.29s, exit code 1.** Both v2
recovery files (`test_helper_recovery_v2.py`,
`test_helper_recovery_v2_sinks.py`) are inside that run and are green.

### Repository validator

`python3 scripts/validate.py` printed `Validated 3 plugin package(s) and 15
skill(s).` and exited `0`.

### Source map regeneration

```
python3 tools/autopilot/update_helper_map.py --root . --map tools/autopilot/source-map.json --receipts docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json
```

Exit code `0`. The same command with `--check` appended also exited `0`.

Ownership was snapshotted before and after regeneration (601 helper regression
rows, 167 function rows, 44 authored-file owners, 4950 regression cases). The
two snapshots are byte-identical, so no source owner and no settled deferral
moved. `git diff --stat` on the map shows 24 insertions and 24 deletions, all of
them `destination_blob_sha256`, `artifact_sha256` or `tested_package_revision`
values; the tested revision advanced from
`cce5dadcfe5c951e541ef8e395ffd930b1d56b0e` to
`3c7e2183a194c86d10390a3f2eda5524516ba50a`.

### Provenance tests

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_helper_provenance.py tests/autopilot/test_provenance.py -q
```

Result: **19 passed in 1.07s, exit code 0.** No receipt field was adjusted to
obtain that result.

## Four red nodes in the helper regression set, owned by v2 task 2

The dispatch brief expected two failures and described them as pre-existing.
The measured result is four failures, and the control runs show that all four
are v2 task-2 regressions.

Failing nodes:

1. `tests/autopilot/test_cap_recovery_helpers.py::test_spawn_failure_is_controlled_and_preserves_outputs[missing-False]`
2. `tests/autopilot/test_cap_recovery_helpers.py::test_spawn_failure_is_controlled_and_preserves_outputs[not-executable-False]`
3. `tests/autopilot/test_local_paths.py::SafeSinkOpenerTest::test_sink_opener_creates_parents_and_a_fresh_unbuffered_binary_file`
4. `tests/autopilot/test_local_paths.py::SafeSinkOpenerTest::test_sink_opener_refuses_symlinked_parents_and_replaces_symlinked_leaf`

Assertions observed:

- Nodes 1 and 2: `assert tree(world.target) == before` reports one extra entry,
  an empty `docs/dev/tmp/run.log`, left behind when the spawn fails.
- Node 3: `AssertionError: b'newvious contents\n' != b'new'`. The reopened sink
  keeps its earlier bytes instead of being truncated.
- Node 4: `OSError: [Errno 62] Too many levels of symbolic links: 'leaf.log'`
  raised at `plugins/autopilot/scripts/log_sink_refusal.py:216`, where the test
  expects the symlinked leaf to be replaced.

Ownership evidence, measured in a detached control worktree:

- At `cce5dadcfe5c951e541ef8e395ffd930b1d56b0e` (the previous receipt pin), the
  two `SafeSinkOpenerTest` nodes gave `2 passed, 25 deselected in 0.08s`, and the
  spawn-failure parametrisation gave `4 passed, 13 deselected in 1.57s`.
- At `4a93821` (v2 task 2, "prove the log sink openable before spawning the
  verification child"), the same selection gave `4 failed, 2 passed, 38
  deselected in 1.69s`, with the identical four nodes and assertions.
- `tests/autopilot/test_local_paths.py` was last changed by `77bb783`, which
  precedes `cce5dad`. The test bytes did not move, so the change is on the
  product side: `plugins/autopilot/scripts/log_sink_refusal.py` was edited by
  `4a93821` and `30e5c5e`.

Conclusion: the four nodes are AP00013 v2 task-2 regressions in the verify-path
log-sink pre-open behaviour. They are not AP00018 controller tests. The earlier
"pre-existing" reading came from a control run at the parent of the task-3 edit,
which already contained task 2. None of the four is fixed in this report; the
product bytes at `3c7e2183a194c86d10390a3f2eda5524516ba50a` are unchanged, and a
fix needs its own task because it changes a product contract.

The control worktree was removed after the measurements
(`git worktree remove --force`), and `git worktree list` confirms it is gone.

## AP00018 controller suite: still red, separately owned

The AP00018 controller suites remain red and are owned by AP00018, not by
AP00013 v2. The affected files are `tests/autopilot/test_controller_capacity.py`,
`tests/autopilot/test_controller_owner.py` and
`tests/autopilot/test_controller_owner_recovery.py`. The dispatch brief records
roughly 19 failing nodes there. This session did not run those files, so this
report states no measured count for them. They are recorded as remaining red,
not fixed, not masked and not relabelled.

## Pin confirmation and the historical CI failure

`git cat-file -e 3c7e2183a194c86d10390a3f2eda5524516ba50a:plugins/autopilot/README.md`
exited `0`, so the pinned revision contains the packaged README.

The remote CI failure at the old pin `527d880c` is historical. The previous
receipt pin `cce5dadcfe5c951e541ef8e395ffd930b1d56b0e` already contained
`plugins/autopilot/README.md` (`git cat-file -e` also exits `0` there), so the
new pin repairs nothing about that missing-file failure. It was already repaired
before this delivery.

## Real-host evidence

Unavailable. No Claude Code, Codex or Kiro host execution of the packaged
helpers was run for AP00013. Delivery rests on local test evidence only. No host
profile is certified, and nothing is published or installed. The receipt keeps
`real_host.status: "unavailable"` with that reason.

## What this report does not claim

It does not claim the full `tests/autopilot` suite is green. It does not claim
the completion review passed. It does not claim any real-host certification.
