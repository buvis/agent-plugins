# AP00013 v2 helper recovery report

Tested package revision: `0ed4c17ff964b04104b3961a83a0c8e5563b0f3a` (branch
`master`). The previous receipt pinned
`3c7e2183a194c86d10390a3f2eda5524516ba50a`; that record stays in the receipt
history.

The 21-file helper regression run was taken at the tree of commit
`016b6b3a2ec9d3282cf58c523ecfae69163d1d21`, with the README and CHANGELOG
edit of task 8 still uncommitted. The tested revision differs from that commit
only in `plugins/autopilot/README.md` and `plugins/autopilot/CHANGELOG.md`. No
test file and no product script differs, so the measurement applies to the
product bytes of the tested revision.

Served backend, model and effort (not the `opus` and `sonnet` aliases):

- Build phase, v2 corrective tasks T1-T4: Claude Code subagent
  `autopilot:worker-opus`, model `claude-opus-5`, transcript effort `high`.
- Cycle-1 rework implementor, tasks 7 and 8: Claude Code subagent
  `autopilot:worker-sonnet`, model `claude-sonnet-5-5`, agent-frontmatter effort
  `medium`.
- Cycle-1 rework implementor, task 6: the same `autopilot:worker-sonnet` lane.
  Its transcript belongs to an earlier session, so the served model id was not
  probed. Not captured.
- Per-task reviewer (Pat), tasks 6 to 8: native `claude` CLI through
  `use-sonnet/scripts/sonnet-run.sh` (`claude --print --model sonnet`, no tools,
  no `--effort` flag), model `claude-sonnet-5-5`. Effort was not passed and not
  captured.
- Coordinator session for the rework: model `claude-opus-5`, effort `high` as
  recorded in the loop session brief.

Every number below was measured by the coordinator or in the session that is
named beside it; nothing is copied from an earlier receipt unless it is marked
as history.

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

Cycle-1 rework:

| Task | Resolution | Evidence |
| --- | --- | --- |
| 5 | Verification sink ownership, cleanup containment, and below-root symlink and root-spelling refusals. | `fbeeb50`, `8d5c325`, `fe0cb96`, `eb770e3`, `0463059`, `e6827b2`, `ce23348`. |
| 6 | Staging git-probe locale pin, empty context union, and the `detail` refusal shape. | `699d0f0` (tests), `3ea5ded` (fix). |
| 7 | Test-only: FIFO reader readiness sync, dead sink hooks dropped, committed framework-selftest removed. | `1f3f911`. |
| 8 | Package docs, then this evidence refresh. | `0ed4c17`. |

T2 is also the source of the four red nodes recorded below. Its pre-spawn sink
proof changed the observable filesystem contract of the verify path. Cleanup's
creation/identity window remains open, as recorded in
`00013-v2-task2-followup-ruling.md`; the table does not certify that boundary.

## Measured verification

### Helper regression set (21 files)

The set is the earlier 19 files plus the two modules the cycle-1 rework added,
`tests/autopilot/test_helper_rework_sinks.py` and
`tests/autopilot/test_helper_rework_stage.py`.

Command:

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_cap_recovery_helpers.py tests/autopilot/test_cycle1_boundaries_verify.py tests/autopilot/test_cycle1_boundaries_stage.py tests/autopilot/test_cycle1_boundaries_context.py tests/autopilot/test_review_helpers.py tests/autopilot/test_review_helpers_contract.py tests/autopilot/test_review_close_helpers.py tests/autopilot/test_review_close_helpers_gates.py tests/autopilot/test_cycle1_hardening_sinks.py tests/autopilot/test_verification.py tests/autopilot/test_review_evidence_helpers.py tests/autopilot/test_verification_reuse.py tests/autopilot/test_local_paths.py tests/autopilot/test_local_boundary.py tests/autopilot/test_local_boundary_verify.py tests/autopilot/test_local_boundary_state.py tests/autopilot/test_facade.py tests/autopilot/test_helper_recovery_v2.py tests/autopilot/test_helper_recovery_v2_sinks.py tests/autopilot/test_helper_rework_sinks.py tests/autopilot/test_helper_rework_stage.py -q
```

Result: **668 passed, 0 failed, 0 skipped in 219.29s, exit code 0.** No helper
failure remains in this set.

The earlier T1-T4 run of the 19-file set gave 4 failed, 544 passed, 0 skipped in
188.29s, exit code 1. That result stays recorded as history in the "Four red nodes" section below.

### Repository validator

`python3 scripts/validate.py` printed `Validated 3 plugin package(s) and 15
skill(s).` and exited `0`.

### Source map regeneration (T1-T4 delivery, revision 3c7e218)

This section and the final gate below describe the T1-T4 delivery only.

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

### Provenance tests (T1-T4 delivery)

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_helper_provenance.py tests/autopilot/test_provenance.py -q
```

Result: **19 passed in 1.07s, exit code 0.** No receipt field was adjusted to
obtain that result.

## Four red nodes in the helper regression set, owned by v2 task 2

Status now: all four nodes are GREEN in the 21-file run above (668 passed, 0
failed). Cycle-1 rework task 5 resolved the contract conflict on the product
side. The v2 sink test that used to assert an empty leftover log is now
`tests/autopilot/test_helper_recovery_v2_sinks.py::test_verification_preserves_its_outputs_on_a_spawn_failure_and_an_absent_log_stays_absent`.
An absent log stays absent after a failed spawn, so the two contracts no longer
disagree. The failures below were real and stay
recorded as history, exactly as measured in the T1-T4 delivery (revision
`3c7e2183a194c86d10390a3f2eda5524516ba50a`, 4 failed, 544 passed, 188.29s).

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
roughly 19 failing nodes there. The sub-task that wrote this section did not run
those files. The orchestrator's final integration gate, below, did: exactly 19
AP00018 controller nodes failed. They are recorded as remaining red, not fixed,
not masked and not relabelled.

## Final integration gate, T1-T4 delivery (run once, by the orchestrator)

Run on the evidence commit `9e89a5913f26e7d062347362a3cad773ccd09396`, whose
bytes under `plugins/` and `tests/` are identical to the tested package revision
`3c7e2183a194c86d10390a3f2eda5524516ba50a`. Under `tools/`, the generated
`tools/autopilot/source-map.json` differs as described above.

| command | exit | result |
|---|---|---|
| `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` | 1 | 23 failed, 967 passed in 254.02s |
| `python3 -m unittest discover -s scripts` | 0 | 59 tests, OK |
| `python3 scripts/validate.py` | 0 | 3 packages, 15 skills |
| `python3 scripts/generate_marketplace.py --check` | 0 | `marketplace.json` is up to date |

The 23 failures are exactly the 19 AP00018 controller nodes plus the four v2
task-2 contract-conflict nodes named above. Every other AP00013 helper node is
green, including `test_helper_recovery_v2.py`,
`test_helper_recovery_v2_sinks.py`, and — after the receipt and map were
refreshed — `test_helper_provenance.py`, `test_provenance.py` and
`test_helper_provenance_real.py` (31 passed).

One repair attempt for the two spawn-failure nodes was written during this round
and **reverted before this gate**: reusing `_open_result_sink` /
`_close_result_sink` for the log leaf in `verification._execute` made those two
nodes green and immediately broke the two task-2 nodes
`test_verification_preserves_its_outputs_on_a_spawn_failure_but_leaves_an_empty_log[absent-program|unexecutable-program]`,
which assert the opposite contract. No product byte changed, and the contract
choice is recorded as a deferred item for the completion review.

## Pin confirmation and the historical CI failure

`git cat-file -e 3c7e2183a194c86d10390a3f2eda5524516ba50a:plugins/autopilot/README.md`
exited `0`, so the pinned revision contains the packaged README.

The remote CI failure at the old pin `527d880c` is historical. The previous
receipt pin `cce5dadcfe5c951e541ef8e395ffd930b1d56b0e` already contained
`plugins/autopilot/README.md` (`git cat-file -e` also exits `0` there), so the
new pin repairs nothing about that missing-file failure. It was already repaired
before this delivery.

## Attempt-validation allocation peak (measured)

The previous report had no measured allocation number. This one replaces the
committed framework-selftest that cycle-1 rework task 7 deleted.

Provenance: a scratch-only probe at `docs/dev/tmp/ap13-allocation-probe.py`. It
is untracked and not shipped. The coordinator wrote and ran it once; no
implementor ran it.

Command:

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -I docs/dev/tmp/ap13-allocation-probe.py
```

Exit code `0`. Output, verbatim:

```
ceiling: 1000000
parent_tracing_enabled: true
parent_prior_peak: 12000040
plain: {"peak": 95314, "ok": false, "defects": ["attempt_sequence_invalid"]}
inject: {"peak": 1695370, "ok": false, "defects": ["attempt_sequence_invalid"]}
plain_under_ceiling: true
inject_over_ceiling: true
python: 3.12.16
```

What it proves:

- For attempt 200000, `check_evidence` peaked at 95,314 bytes against a
  1,000,000-byte ceiling.
- An injected `[0] * 200000` allocation in the same child peaked at 1,695,370
  bytes, above the ceiling. The bound has power.
- The parent process already had tracemalloc enabled with a prior peak of
  12,000,040 bytes (above 8 MB). The child still reported its own absolute
  peak, so the measurement is absolute and not a delta.

The committed test keeps only the plain measurement and its ceiling. The
injected demonstration is scratch evidence only.

## Unresolved finding: helper parent-alias

Source: `00013-v2-parent-alias-helper-audit.md`.

A read-only, helper-only probe at pinned source commit
`eb770e31348df5c4b669e3f8ba391ca25526d901` CONFIRMED that `_pinned_parent_fd`
resolves the whole parent when the supplied root uses another spelling. That
removes a below-root symlink component before the `O_NOFOLLOW` descent.

Limits:

1. The larger hypothesis (a full `run_verification` bypass, a tracked-file
   overwrite, an outside-root write) remains UNVERIFIED. The attempted
   full-runtime disposable Git clone failed at `.git/hooks` with an OS
   permission denial, including the required escalated retry. No further clone
   was attempted.
2. At the later HEAD, the diff against the pinned source changes only
   `_symlinked_component`. The finding still applies by source inspection.
3. No new runtime execution against that HEAD is claimed.

Consequence: the green scoped tests do not authorize a clean-delivery claim or a
defect-closure claim. The cycle-2 review gate adjudicates this finding.

## Real-host evidence

Unavailable. No Claude Code, Codex or Kiro host execution of the packaged
helpers was run for AP00013. Delivery rests on local test evidence only. No host
profile is certified, and nothing is published or installed. The receipt keeps
`real_host.status: "unavailable"` with that reason.

## What this report does not claim

It does not claim the full `tests/autopilot` suite is green. The 21-file helper
set is green; the separately owned AP00018 controller suite is not. It does not
claim the completion review passed. It does not claim any real-host
certification. It does not claim a clean delivery. It does not claim the
parent-alias finding is closed: the helper-level defect is confirmed, its
runtime consequences are unverified, and the cycle-2 review gate adjudicates it.
