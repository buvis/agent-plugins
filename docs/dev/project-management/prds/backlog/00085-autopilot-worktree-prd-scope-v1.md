---
default_model: sonnet
model_tier_rationale: the scope file format, refusal predicate and messages are given verbatim; tests on temporary git worktrees fail loudly on a wrong pick
eligibility: ls docs/dev/project-management/prds/done/00019-* # link-ok: lifecycle output
---
# Autopilot worktree PRD scope

Source: user decision 2026-11-24 in a herdr-app session (Runway PRD 00005 review finding R1, `~/.config/herdr-app/docs/dev/project-management/reviews/00005-runway-lanes-housekeeping-v1-review-01.md`). Requirements were settled in that conversation; no discovery doc. link-ok: the review file lives in the herdr-app repo.

## Overview

### Problem Statement
PRD selection takes the lowest `00XXX-` number in `wip/`, else in `backlog/`. A linked git worktree inherits every committed `wip/` PRD of the branch it starts from. Opening a worktree for one PRD while `master` has other PRDs in `wip/` is allowed, but then every loop in that worktree (autoclaude, autocodex, and any later host) starts the lowest-numbered PRD, not the one the worktree exists for. Nothing tells a worktree which PRDs it owns, and one worktree may need several PRDs, so the branch name cannot carry the scope.

Rejected alternatives (user, 2026-11-24): scope from the branch name (cannot hold several PRDs); a `branch:` claim in PRD frontmatter (a committed claim goes stale on every merge).

### Target Users
Users who run several autopilot loops in parallel, one per worktree, from Runway (herdr-app) or by hand; and every host that selects PRDs through the controller.

### Success Metrics
- `test_scoped_worktree_picks_only_scoped_prd`, `test_unscoped_worktree_refuses_two_wip`, `test_main_checkout_selection_unchanged` and the other tests in `tests/autopilot/test_controller_scope.py` pass.
- No host carries its own selection rule: every loop gets the scope through the controller's selection operation.

## Functional Decomposition

### Capability: Worktree scope

#### Feature: Scope file
- **Description**: A per-worktree list of the PRDs that worktree may run, kept out of git history.
- **Inputs**: The project root.
- **Outputs**: `frozenset[str]` of PRD basenames, or `None` when the file is absent.
- **Behavior**:
  - Path: the output of `git rev-parse --git-path autopilot-scope`, run in the project root. In a linked worktree that is `<common-dir>/worktrees/<name>/autopilot-scope`; in the main checkout it is `.git/autopilot-scope`. Git never tracks it, and each worktree has its own.
  - Format: UTF-8 text, one PRD basename per line (`00005-runway-lanes-housekeeping-v1.md`, a herdr-app PRD; link-ok: example). Surrounding whitespace is stripped. Empty lines and lines starting with `#` are ignored.
  - A line that is not a basename matching `^[0-9]{5}-[A-Za-z0-9._-]+\.md$` makes the whole file invalid. Reading it raises `ScopeError` naming the path and the 1-based line number: `autopilot scope file <path> line <n> is not a PRD file name: <line>`.
  - An existing file with no entries is a valid empty scope, so selection finds nothing and reports drained.
  - Other tools may write this file directly. herdr-app Runway will write it when it opens a lane. The format above is the public contract.

#### Feature: Scoped selection
- **Description**: Selection honours the scope, and refuses to guess in an unscoped linked worktree.
- **Inputs**: `wip/` and `backlog/` names, the scope (`frozenset[str] | None`), and `linked` (true when `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir`).
- **Integration point**: `lifecycle.select_eligible(project_root)` from PRD 00019 (design `designs/00019-autopilot-controller-lifecycle-v1-design.md`, "Candidate selection"). It returns `{"prd", "source", "skipped"}` with `source` in `wip | backlog | drained`, moves no file and writes no state. This PRD calls `filter_candidates` inside it, after listing `wip/` and `backlog/` and before the wip-first rule, so an out-of-scope backlog PRD never runs its `eligibility:` command and never appears in `skipped`.
- **Outputs**: the `select_eligible` result plus `scope`, or a raised `ScopeRefusal`.
- **Behavior**:
  - Scope present (main checkout or linked worktree): keep only the `wip/` and `backlog/` names that are in the scope, then apply the unchanged wip-first, lowest-number rule. Scope entries that match no file in `wip/` or `backlog/` (for example a PRD already in `done/`) are ignored. No scoped candidate means `drained`.
  - Scope absent, main checkout: selection is unchanged, byte for byte.
  - Scope absent, linked worktree:
    - `wip/` holds two or more selectable PRDs: refuse with `ScopeRefusal` and the message `worktree <root> has <n> PRDs in wip/ and no autopilot scope; run: autopilot scope add <basename>`.
    - `wip/` holds exactly one: select it. This keeps today's behaviour for a worktree that has only its own PRD.
    - `wip/` is empty: report `drained`. Never pull from `backlog/` in an unscoped linked worktree, or that worktree would start the lowest backlog PRD, which is the same defect.
  - A refusal starts nothing: `select_eligible` raises `ScopeRefusal` before any eligibility command runs, no PRD moves and no state is written. How a host loop reports the refusal is host wiring (PRD 00016) and out of scope here.
  - The `eligibility:` gate still runs only on the backlog candidate that survives the scope filter.
  - The selection result carries `scope`: the sorted list of scope entries, or `null` when no file exists, so every host and status view can show the active scope.

#### Feature: Scope command
- **Description**: One command to read and edit the scope file, so nobody needs to know the git path.
- **Inputs**: `scope show`, `scope add <basename>...`, `scope remove <basename>...`, run in the project root.
- **Outputs**: one JSON line on stdout, `{"path": <scope file path>, "scope": [<sorted basenames>] | null}`, and exit 0. Invalid input prints the error on stderr and exits 2.
- **Behavior**: `add` creates the file when absent, rejects a basename that fails the format rule above, and adds each name once. `remove` drops names, and keeps the file even when it becomes empty (an empty scope stays a deliberate "nothing to run"). `show` never creates the file. Writes replace the file atomically (write a sibling temp file, then `os.replace`). `add` does not require the PRD to exist yet, because a lane may scope a PRD before it moves into `wip/`.

## Structural Decomposition

### Repository Structure

```
plugins/autopilot/
├── controller/
│   ├── main.py                          # Maps to: Scope command (new `scope` subcommand)
│   └── autopilot_state/
│       ├── scope.py                     # Maps to: Scope file, Scoped selection
│       └── lifecycle.py                 # Maps to: Scoped selection (wire into the selection operation)
├── contracts/controller-v1.json         # Re-sealed delivery evidence
├── README.md                            # Scope file contract and command; digest re-sealed
└── CHANGELOG.md                         # Added entry
tools/autopilot/
├── source-map.json                      # Regenerated by update_helper_map.py
├── update_helper_map.py                 # Run, not edited
└── export-controller-contract.py        # Run, not edited
tests/autopilot/
├── test_controller_scope.py             # All scenarios below, on temporary git repositories
├── test_package.py                      # Must pass against the re-sealed bytes
└── test_helper_provenance_real.py       # Must pass against the re-sealed bytes
```

### Module: Scope
- **Maps to capability**: Worktree scope
- **Responsibility**: Locate, parse and write the scope file; apply the scope and the refusal rule to selection candidates.
- **Location**: `plugins/autopilot/controller/autopilot_state/scope.py`
- **Exports**:
  - `scope_path(root: Path) -> Path` - the `git rev-parse --git-path autopilot-scope` result, made absolute against `root`
  - `is_linked_worktree(root: Path) -> bool` - `--git-dir` differs from `--git-common-dir` after both are resolved
  - `read_scope(root: Path) -> frozenset[str] | None` - parse per the format; raises `ScopeError`
  - `write_scope(root: Path, names: Iterable[str]) -> Path` - atomic write, sorted, one name per line
  - `filter_candidates(wip, backlog, scope, linked) -> tuple[list[str], list[str]]` - apply the scope, or raise `ScopeRefusal` per the rule
  - `ScopeError`, `ScopeRefusal` - exception classes
New symbols: `plugins/autopilot/controller/autopilot_state/scope.py`, `scope_path`, `is_linked_worktree`, `read_scope`, `write_scope`, `filter_candidates`, `ScopeError`, `ScopeRefusal`, `tests/autopilot/test_controller_scope.py`, `test_scoped_worktree_picks_only_scoped_prd`, `test_scope_with_two_prds_runs_lowest_scoped_first`, `test_main_checkout_selection_unchanged`, `test_main_checkout_honours_scope`, `test_unscoped_worktree_refuses_two_wip`, `test_unscoped_worktree_single_wip_selected`, `test_unscoped_worktree_never_pulls_backlog`, `test_scope_entry_in_done_is_ignored`, `test_empty_scope_file_drains`, `test_scope_file_invalid_line_errors`, `test_scope_file_is_per_worktree`, `test_scope_command_add_remove_show`

### Module: Lifecycle selection
- **Maps to capability**: Worktree scope
- **Responsibility**: Inside `select_eligible`, call `filter_candidates` before the existing wip-first rule and the eligibility gate, and add `scope` to its result.
- **Location**: `plugins/autopilot/controller/autopilot_state/lifecycle.py` (created by PRD 00019)
New symbols: `plugins/autopilot/controller/autopilot_state/lifecycle.py`

### Module: Controller CLI
- **Maps to capability**: Worktree scope
- **Responsibility**: The `scope show|add|remove` subcommand.
- **Location**: `plugins/autopilot/controller/main.py`

## Dependency Graph

### Foundation Layer (Phase 0)
PRD 00019 is done (the `eligibility:` line checks this): the controller owns PRD selection in `plugins/autopilot/controller/autopilot_state/lifecycle.py`.
- **Scope**: no dependency inside this PRD; built first.

### Core Layer (Phase 1)
- **Lifecycle selection**: Depends on [Scope].
- **Controller CLI**: Depends on [Scope].

### Integration Layer (Phase 2)
- **README.md, CHANGELOG.md**: Depend on [Lifecycle selection, Controller CLI].

## Implementation Phases

### Phase 0: Foundation
**Goal**: The scope file and the refusal rule exist as tested pure logic plus git lookups.

**Tasks**:
- [ ] Create `plugins/autopilot/controller/autopilot_state/scope.py` with the exports above, and `tests/autopilot/test_controller_scope.py` covering the file and filter scenarios. Premise: `plugins/autopilot/controller/autopilot_state/lifecycle.py` exists (PRD 00019); if it does not, stop and report. (no deps) - Acceptance: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_scope.py -k "scope_file or filter"` passes.

**Exit Criteria**: Scope parsing, writing, linked-worktree detection and the filter rule pass their tests on temporary repositories with a real `git worktree add`.

### Phase 1: Core
**Goal**: Every selection goes through the scope, and the command edits it.

**Tasks**:
- [ ] Wire `filter_candidates` into `select_eligible` in `plugins/autopilot/controller/autopilot_state/lifecycle.py`, before the eligibility gate, and add `scope` to its result. (depends on: Phase 0) - Acceptance: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_scope.py -k "selection or scoped or unscoped or main_checkout or drains or ignored"` passes, including `test_main_checkout_selection_unchanged`.
- [ ] Add the `scope` subcommand to `plugins/autopilot/controller/main.py`. (depends on: Phase 0) - Acceptance: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_scope.py -k command` passes.

**Exit Criteria**: A loop in a scoped worktree can only pick a scoped PRD; an unscoped linked worktree with two `wip/` PRDs stops with the refusal message.

### Phase 2: Integration
**Goal**: The contract is documented for other tools.

**Tasks**:
- [ ] Document the scope file path, format, refusal rule and command in `plugins/autopilot/README.md`; add an `Added` entry in `plugins/autopilot/CHANGELOG.md`. (depends on: Phase 1) - Acceptance: `rg -n "autopilot-scope" plugins/autopilot/README.md` and `rg -n -i "scope" plugins/autopilot/CHANGELOG.md` both find a match.
- [ ] Refresh delivery evidence for final package bytes: the controller, README and CHANGELOG edits change the controller bundle digest, so regenerate `plugins/autopilot/contracts/controller-v1.json` with `tools/autopilot/export-controller-contract.py`, its README digest, the successor receipt and `tools/autopilot/source-map.json` with `tools/autopilot/update_helper_map.py`, without changing historical receipts, as PRD 00019 Phase 2 task 2 does. (depends on: Phase 2 task 1) - Acceptance: `tests/autopilot/test_helper_provenance_real.py` and `tests/autopilot/test_package.py` pass against current bytes; no path exemption or test exclusion is introduced.

**Exit Criteria**: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` and `python3 scripts/validate.py` pass once, after the last task.

## Test Strategy

### Critical Scenarios
All run on a temporary repository with a real `git worktree add`; never on the batch's own checkout. PRD names below are fixture names inside that temporary repository (link-ok: fixtures).
- **Happy path** (`test_scoped_worktree_picks_only_scoped_prd`): worktree with `00003-a`, `00005-b` in `wip/`, scope `00005-b-v1.md` → selects `00005-b-v1.md`, source `wip`. (link-ok: fixtures)
- **Several PRDs** (`test_scope_with_two_prds_runs_lowest_scoped_first`): scope holds `00007` and `00009`, `wip/` holds `00003`, `00007`, `backlog/` holds `00009` → `00007` from `wip`; after `00007` leaves `wip/`, `00009` from `backlog`.
- **Main checkout** (`test_main_checkout_selection_unchanged`): no scope file, two `wip/` PRDs in the main checkout → the lowest, as today.
- **Main checkout scoped** (`test_main_checkout_honours_scope`): scope file present in `.git/autopilot-scope` → only scoped PRDs.
- **Refusal** (`test_unscoped_worktree_refuses_two_wip`): linked worktree, no scope, two `wip/` PRDs → `ScopeRefusal` with the exact message, and no file moves.
- **Single wip** (`test_unscoped_worktree_single_wip_selected`): linked worktree, no scope, one `wip/` PRD → selected.
- **No backlog pull** (`test_unscoped_worktree_never_pulls_backlog`): linked worktree, no scope, empty `wip/`, one `backlog/` PRD → `drained`.
- **Stale entry** (`test_scope_entry_in_done_is_ignored`): scoped PRD only in `done/` → `drained`.
- **Empty scope** (`test_empty_scope_file_drains`): file with only comments → `drained`.
- **Invalid line** (`test_scope_file_invalid_line_errors`): line `../x.md` → `ScopeError` naming the line number.
- **Isolation** (`test_scope_file_is_per_worktree`): scope written in one worktree is not seen by the main checkout or a second worktree.
- **Command** (`test_scope_command_add_remove_show`): `add` twice keeps one entry, `remove` to empty keeps an empty file, `show` on no file prints `"scope": null` and creates nothing; an invalid name exits 2.

## Risks

- **The loops running today do not use the controller.** autoclaude and autocodex still run the frozen buvis/claude-autopilot 0.10.0 `cli/selection.py`, which this PRD does not change (that repo is frozen). The scope takes effect at cutover to the controller. Until then, the safe practice stays: run a loop only in a worktree whose `wip/` holds that worktree's PRDs alone.
- **A tool that makes worktrees does not write the scope.** The refusal rule turns that into a loud stop with the fix command, never a wrong pick.
- **The scope file is hidden.** The `scope` field in every selection result and `autopilot scope show` make it visible.
