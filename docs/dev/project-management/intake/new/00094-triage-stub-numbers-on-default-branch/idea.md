# Idea: triage hold stubs must take their number from the default branch

Status: new. Recorded 2026-11-26 by an agent working on the gems Engram port.

Developer's words, 2026-11-26:

> I think we discovered a big issue when working with worktrees. So we must enhance create PRD skill to store PRDs to main/master branch and before doing that they must take main/master branch current state into the worktree branch if it isn't on main/master

> apply the same rule to the autopilot triage writer

This is an intake item and not a code change on purpose. The live writer is `skills/run-autopilot/cli/triage.py` in `buvis/claude-autopilot`, which is frozen (2026-11-01). The port inventory row `CLI-121` (`autopilot mint-stubs`, in `docs/dev/project-management/discovery/00011-autopilot-agent-plugins-inventory.md`) has no target yet. Spec this with the PRD that ports `mint-stubs`, and make it part of that command's contract.

## Problem

`mint-stubs` numbers a stub from the files in its own working tree: `next_sequence` takes the highest `NNNNN` in `prds/{backlog,wip,hold,done}` and `discovery/`, plus one (`_allocate`, `_claimed_by_other`). A loop that runs on a worktree branch cannot see numbers that the default branch or other branches took after the branch was cut. The stub also stays on that branch until it merges.

Observed collisions:

- gems, 2026-11-25: branch `feature/engram-port` held PRDs 00163-00173. `master` gained its own 00163-00169 through a merged PR. Both sets now sit on `master`.
- agent-plugins, this repo: `intake/new/00086-fast-track-dispatch-defects` and `prds/hold/00086-triage-review-acceptance-is-not-enforced-a-phas-v1.md` share 00086.
- The frozen scan also skips `intake/*/`, so an intake item never reserves its number against a stub.

## Rule to apply (same as create-prd step 6 and elicit-requirements step 5, agent-skills e466b08 and 4ec88c0)

1. Find the default branch from `origin/HEAD`, else local `master`, else `main`.
2. Fetch. Scan for the next number in the working tree AND on every ref: `git log --all --name-only --format= -- docs/dev/project-management/prds docs/dev/project-management/intake docs/dev/project-management/discovery`. Include `intake/*/` item directories.
3. Commit each stub on the default branch, not only on the loop's branch. Use the checkout that has the default branch when it is clean under `docs/dev/project-management/`; otherwise use a temporary detached worktree from `origin/<default>`. Push. On a rejected push: pull with rebase, re-scan, renumber on a collision, push again.
4. Bring the stub into the loop's branch.

Difference from the skills: the skills merge the default branch into the working branch BEFORE the scan. `mint-stubs` runs inside a loop, and the skill rule forbids a merge under a running loop. So for the minter, step 2 replaces the merge (scan all refs without merging), and step 4 must be a safe point the loop owns (for example, at batch end, or by committing the same stub file on the loop branch). The PRD decides which.

## Open questions for the porting PRD

- Where the loop brings the stub in (step 4): a merge at batch end, or a second commit of the same file on the loop branch.
- Behavior with no network: stub on the local default branch only, or stub on the loop branch plus a warning.
- Whether `ledger_key` idempotency still holds when the same stub exists on two branches before they merge.
