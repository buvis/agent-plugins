# AP 00012 post-pin source drift

Measured 2026-11-01 against `~/git/src/github.com/buvis/claude-autopilot`.
Pin: `e960ef1c` (`tools/autopilot/source-pin.json`). Source HEAD: `7e17947b`.

## Why a ledger, not a repin now

The AP 00012 design treats source changes after the pin as a deliberate repin:
regenerate `source-inventory.json` at the new commit, re-map rows, update
`PIN` in `tools/autopilot/check-source.py`, and pass the explicit audit
(design "Reuse and alternatives" and "Risks"). A repin moves every changed
source blob hash, the inventory digest and the preserved destination assets
(`waves.md` is byte-identical today). AP 00013 is mid-build (task 10 of 11,
uncommitted), so a repin now would churn its bindings under it.

Decision: record every post-pin change here with its planned row. Run the
repin as the first step of AP 00015 Phase 0, which already must "recheck
ownership/pin before edits". Repin to the source HEAD at that time. If the
source owner has committed the `subagent-dispatch.md` fix by then (see
below), it comes in with the repin. Until the repin, these rows are open
obligations, not passed evidence.

## Post-pin commits

| Commit | Change | Disposition | Owner (per existing map rows) | Planned rows at repin |
| --- | --- | --- | --- | --- |
| `692d772c` | `loop_act.py`: a batch whose every pick failed `eligibility:` closes "Backlog blocked." and names the gated PRDs; a drain lists skipped PRDs after the count. | port, controller loop | `buvis/ovcaq#00060` (owns the other `test_loop_act.py` cases) | behavior row for the batch-close headline; regression rows `skills/run-autopilot/cli/test_loop_act.py::test_every_pick_gated_says_blocked_and_names_the_prds`, `::test_a_drain_with_some_picks_gated_still_lists_them`, `::test_gated_prds_ignores_malformed_entries_and_keeps_odd_names`, all `replaced`, OVCAQ 00060 |
| `52fb6755` | Spec only: source PRD 00371 (hold pushes until an agoge run leaves the repo unchanged). No code. | informational, no row | `buvis/ovcaq#00060` if it ships (drain-time agoge run lives there) | none at repin unless 00371 is implemented in source first; then its tests get rows like any other change |
| `9dba4206` | `gather-context.sh` takes `PROJECT_ROOT` from `git rev-parse --show-toplevel`, falling back to `pwd`. | **ported now** | `buvis/agent-plugins#00016` (owns the other `test_gather_context_*.sh` cases) | regression row `skills/review-work-completion/scripts/test_gather_context_root.sh::script-or-module`, `replaced` by `tests/autopilot/test_review_helpers.py::test_subdirectory_project_root_stages_under_the_repo_toplevel` |
| `7e17947b` | `AUTOPILOT_WORKTREE_ROOT` puts wave lane and assembly worktrees under `$AUTOPILOT_WORKTREE_ROOT/<repo>/`; the `wave.json` path check accepts both layouts. `cli/conftest.py` clears the variable for the suite. | port, wave behavior (waves not ported yet) | `buvis/ovcaq#00061` (owns `waves.md` rows and the other `test_wave_assemble.py` cases) | configuration row `environment:AUTOPILOT_WORKTREE_ROOT`; behavior row for the dual-layout path check; regression rows `skills/run-autopilot/cli/test_wave_assemble.py::test_worktree_root_setting_moves_lane_and_assembly_worktrees_under_it` and `::test_wave_planned_beside_the_repo_stays_valid_once_the_root_is_set`, `replaced`, OVCAQ 00061; `waves.md` asset re-copied (stays `preserved`) |

Port of `9dba4206`: the ported gatherer is `plugins/autopilot/scripts/review_stage.py`.
It takes `project_root` from the request and joins a relative `artifact_root`
onto it, so a subdirectory root reproduced the bug. `stage_review` now swaps a
subdirectory root for its git toplevel. The new test failed before the fix.

## Uncommitted claude-autopilot edits (2026-10-27/28)

Not committed, not changed. Read only.

| Path | What it is | Owner work | Disposition |
| --- | --- | --- | --- |
| `skills/work/references/subagent-dispatch.md` | Oversized-dispatch recovery sets `phase` and `next_phase` to `build` and drops the signal file. The old text sets `next_phase` to `planning`, which `statectl` rejects. | AP 00012 recovery, session `cdd23c1a` (`docs/dev/project-management/autopilot/reports/00012-state-write-recovery.md`): it fixed source and the installed 0.10.0 copy, and never committed source. | Real fix. The source owner should commit it with its CHANGELOG line. The ported copy `plugins/autopilot/skills/work/references/subagent-dispatch.md` still has the `planning` text (byte-identical to the pin). It is not live: the package refuses execution until certified. Planned row: asset becomes `adapted` for that step, owner `buvis/agent-plugins#00015` (owns the file's behavior rows `OPT-015`, `OPT-141`, `BEH-535`, `BEH-536`), and comes in through the repin or a section adaptation in AP 00015. |
| `CHANGELOG.md` | The fix's "oversized dispatch recovery uses the valid `build` phase" line, plus two stray blank lines. | Same as above. | Commit with the fix and drop the blank lines. |
| `skills/run-autopilot/cli/loop_act.py`, `cli/test_loop_act.py` | Formatter reflow only (lines joined past 88 columns, imports merged). No change in behavior. Made by the edit-time autofixer, which falls back to `~/.config/ruff` because that repo has no ruff config. | None. | Discard (`git checkout` by the source owner). No port row. |
| `docs/dev/project-management/prds/hold/00370-retire-source-package-v1.md` (untracked) | Source-side retirement PRD, sourced from discovery 00011 and the port completeness review here. | Port retirement plan (discovery 00011). | Keep in source; the source owner should commit it. Its readiness gate needs "the complete AP source inventory/map", so it also needs the repin above. No port row. |

## Ruff target

`ruff.toml` here sets `target-version = "py310"`, which matches the Python
3.10 `plugins` job. Ruff picks this project file over `~/.config/ruff`, so the
autofixer will not rewrite code to 3.11+ idioms. The one 3.11+ name in tree,
`StrEnum` in `plugins/autopilot/controller/autopilot_state/store.py`, is
hand-written and matches AP 00018's stated Python 3.12 controller target. Only
the 3.12 `autopilot` job imports it. No change needed.
