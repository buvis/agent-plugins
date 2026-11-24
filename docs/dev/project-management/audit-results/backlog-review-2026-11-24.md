# Backlog review - agent-plugins - 2026-11-24

Scope: 00019 and 00085 only (user request). The other backlog PRDs were not reviewed.

Verdict: GO for 00019 and 00085 (0 Blocking open after the apply pass).

## Map

| # | PRD | template | lines | subsystems | depends on | verdict |
|---|---|---|---:|---|---|---|
| 00019 | autopilot-controller-lifecycle-v1 | standard | 136 | `plugins/autopilot/controller`, contracts, delivery pins | 00018 (done) | READY |
| 00085 | autopilot-worktree-prd-scope-v1 | standard | 173 | `plugins/autopilot/controller`, delivery pins | 00019 | READY (after FIX) |

## Findings

### Blocking (all fixed)

- [00085 x 00019 design] D/E grounding: 00085 hooked into "the controller's selection operation" that reads `wip/` and `backlog/`, runs `eligibility:` and returns `source: drained`. The 00019 design had no such operation. Its `prd.enter` took a caller-supplied list, said "the controller does not scan the filesystem ... does not decide eligibility", and returned drain as a `rejected_evidence` error. This contradicted PRD 00019 line 32 ("Controller owns eligibility"). No later PRD (00015, 00016, 00020, 00021) ports the legacy `autopilot select` (claude-autopilot `skills/run-autopilot/cli/selection.py:100`). -> fails as: stall at the 00085 premise check (the same failure that parked 00019 on 2026-11-16), and a producer/consumer gap for 00016. Fix applied: the 00019 design now specifies read-only `lifecycle.select_eligible(project_root)`, ported from the legacy `select_eligible` and `eligibility.py` (pinned `f40004a`), with result `{"prd", "source": wip|backlog|drained, "skipped"}`. 00085 names it as its integration point.
- [00085] B executability: the refusal path said "guess: the exact stop-reason field follows PRD 00019's drain/stop result shape". -> fails as: wrong-TDD lock-in. Fix applied: `select_eligible` raises `ScopeRefusal` before any eligibility command runs. Host reporting is out of scope (PRD 00016).
- [00085] B executability: every Acceptance line used `python3 -m pytest`. The system python has no pytest (`No module named pytest`, measured 2026-11-24). -> fails as: rework thrash, because every task gate fails. Fix applied: the same `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest` command that 00019 uses.
- [00085] C/G pin churn: 00085 edits `README.md`, `CHANGELOG.md` and controller code, which stales `contracts/controller-v1.json`, the README digest, the successor receipt and `tools/autopilot/source-map.json`. It had no re-seal task. -> fails as: the full gate goes red after the last task (`test_package.py`, `test_helper_provenance_real.py`), which caused rework in 00014 v1 and 00018 v2. Fix applied: added Phase 2 task 2 (re-seal, as in 00019 Phase 2 task 2) and the pin files to the tree.
- [00085] step 1 citations: 7 dangling citations (an eligibility path that is a lifecycle output, a herdr-app review path, fixture PRD names). Fix applied: `link-ok` tokens. Re-run: 0 findings for both PRDs.

### Non-blocking (recorded, not changed)

- [00019] A/C: the `Lifecycle` and `Jobs` Module blocks have no `Location`. A stray `- **Location**: schema.py` line sits after `Jobs` with no module. Tree files `protocol.py`, contracts, README, CHANGELOG and tools appear in no Module block. The design adds `tests/autopilot/test_controller_tasks.py`, which is not in the PRD tree. The full lane survives this.
- [00019] D: Phase 0 task 1 already landed (`42819fd`, `521df8f`). The PRD's "preserve already-satisfied behavior" rule covers the replan.
- [00085] C: the success metric "No host carries its own selection rule" is not measurable by a command.
- [00085] C: the Phase 0 Acceptance `-k "scope_file or filter"` matches no test named `filter`. It still selects the two `scope_file` tests.
- [00020] E: 00020 is now gated on 00085 for ordering (commit `0f18b50`), not for code. The gate makes the loop run 00085 before 00020, because selection skips an ineligible PRD and takes the next one.

### Questions

None.

## Reshapes

None.

## Gaps

- Host wiring: who calls `select_eligible` and reports `ScopeRefusal` is PRD 00016's work. Until the loops move to the controller, the scope file has no effect on running loops (00085 Risks).

## End state after this batch

The controller owns PRD selection, eligibility and lifecycle moves, and each worktree can scope its PRDs through a per-worktree file and `autopilot scope`. The legacy CLI still runs the loops until 00016/00017 move them to the controller.

## Frontmatter tuning

| PRD | suggestion | why |
|---|---|---|
| 00085 | none | `default_model: sonnet` fits: the contracts are verbatim and the tests fail loudly. |

## Decisions applied

Decided by the agent under standing authorization (reversible doc edits). Nothing was walked interactively.

1. 00019 design: added "Candidate selection" (`lifecycle.select_eligible`) and updated the source map line.
2. 00085: integration point, refusal contract, test command, re-seal task, exit criteria, tree, `link-ok` tokens.
3. Lens A re-run on both PRDs: headings unchanged. Grounding re-run: 0 blocking, 0 unverified. Citations re-run: 0 findings.
