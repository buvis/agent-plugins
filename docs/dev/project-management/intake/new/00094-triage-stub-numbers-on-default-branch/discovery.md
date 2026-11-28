# Discovery: Publish Autopilot triage stubs on the default branch

## Classification

Depth: comprehensive | Date: 2026-11-28
Source: `idea.md` beside this file.

Git publication, concurrent allocation, and batch synchronization affect multiple parts of the port.

## Problem

Autopilot creates hold PRDs for severe deferred findings that have no PRD owner. The frozen writer allocates a number from the current checkout and misses intake reservations. A linked worktree can claim a number that another branch already used. A stub kept on that work branch is absent from the default branch until synchronization. Intake 00094 records collisions in gems and agent-plugins.

## Requirements

### Must have

- Make the default branch the registry for new triage stubs. Apply this requirement in the port of CLI-121 and preserve the documented meanings of CLI-122 through CLI-125.
- Resolve the default branch from `origin/HEAD`. For a repository without a remote, use local `master` when it exists, then local `main`.
- Fetch before allocation when a remote exists. Scan the worktree, all available refs, and relevant history for five-digit reservations under the PRD lifecycle buckets, intake item directories, and legacy discovery.
- Commit the stub on the default branch and publish it with a normal fast-forward push when a remote exists. Use an isolated detached worktree based on the fetched default tip when the default checkout cannot safely host the commit. For a repository without a remote, defer and report if the local default branch cannot safely receive the commit.
- On a competing advance of the remote default branch, fetch again and recheck ownership and numbering before retrying publication.
- If a configured remote cannot be reached, defer minting and report the failure. Keep the ledger entry available for retry. A repository with no remote uses its local default branch as the registry.
- Keep the running loop free of default-branch merges. After the loop exits, merge the current default tip into the work branch so the published stubs arrive with their original commits. Report a blocked merge and preserve both the published stubs and local work.
- Preserve the deferred ledger, the hold disposition, and the existing severity and ownership rules.
- Check ownership in the calling worktree and at the current default tip. With a remote, use the fetched tip. Recheck after a remote race so a published owner suppresses a second stub. Recognize both `ledger_key` and folded `ledger_keys` under the existing ownership rules.

### Out of scope

- Editing the frozen `buvis/claude-autopilot` repository.
- Repairing historical sequence collisions or automatically promoting hold stubs.
- Editing the PRD authoring and elicitation skills.

## Constraints

- Preserve unrelated worktree and index changes.
- Respect Git hooks and use normal fast-forward publication.
- Use local Git repositories for headless remote and worktree tests.

## Codebase Context

- [Autopilot source inventory](../../../discovery/00011-autopilot-agent-plugins-inventory.md) assigns CLI-121 through CLI-125 to the owned port. The shipped package retains historical mint call sites in `plugins/autopilot/skills/run-autopilot/references/phase-review.md` and `plugins/autopilot/skills/run-autopilot/references/phase-done.md`. The batch count is documented in `plugins/autopilot/skills/run-autopilot/references/state-schema.md`.
- The frozen reference at `buvis/claude-autopilot:skills/run-autopilot/cli/triage.py` checks each lifecycle bucket for owners, folds related findings, and emits one hold stub per unowned group. Its allocator takes the highest visible PRD or discovery number and adds one.
- The frozen CLI in `buvis/claude-autopilot:skills/run-autopilot/cli/__main__.py` accepts `--state`, `--batch`, and `--prds`, emits the minted basenames and skipped count, and tracks minted basenames for the batch.
- The create-prd and elicit-requirements skills supply the all-ref scan, default checkout selection, and push retry pattern.

## Approach

Publish each new hold stub to the default branch while the loop runs. Synchronize the work branch with a merge after the loop exits. The merge preserves the published commit and brings in other default-branch changes. A cherry-pick would create a second commit for the stub. Waiting for a normal update would delay visibility.

Defer minting if a configured remote is unreachable. A local default-branch commit could require renumbering when the remote returns. A provisional stub on the work branch could expose a duplicate number.

## Success Criteria

- A stale linked worktree mints above reservations held by intake items, the latest default tip, and an unmerged local ref.
- The default branch receives the hold stub and its number. Tests inspect the actual commits and confirm that unrelated files remain untouched.
- A remote advance that claims the same number triggers a rescan before retry. A remote advance that claims the same ledger key produces one canonical stub.
- Repeat calls preserve the existing hold ownership contract.
- A retry from a stale worktree recognizes a stub already published for the same ledger key, even when the worktree has yet to receive that commit. An earlier commit in an unrelated ref reserves its number. Ownership comes from the current worktree and default tip.
- A linked-worktree test verifies that minting leaves the work branch tip unchanged and that post-loop synchronization brings in the published stub commit.
- An unreachable configured remote yields a visible failure and leaves the ledger available for a successful retry. A repository with no remote commits to its local default branch.

## Risks

- **Concurrent writers**. The default branch can advance between scan and push. Verify the final number and ledger ownership against the new tip before retry.
- **Interrupted publication**. A commit can land before bookkeeping. Recover from the published artifact and its ledger key.
- **Post-loop merge conflict**. Preserve the published stub and report that the work branch still needs synchronization. Preserve the user's changes.

## Discovery Log

### Reused evidence

- The idea records the trigger, the reserved paths, the frozen-repo boundary, and the requirement to land the behavior with the minter port.
- The inventory supplies the historical command and option scope. The frozen writer supplies the output shape, qualification rules, and ownership behavior.
- The frozen writer recognizes owners in the caller's lifecycle buckets. The default-branch registry adds the current default tip to that check. Historical and unrelated refs reserve numbers. They can contain retired or abandoned owners, so their content is insufficient to establish current ownership.

### Q1. How should the work branch receive published stubs?

The user agreed to merge the default branch into the work branch after the loop exits. This imports the published commit and other default-branch changes. A cherry-pick would create another commit for the stub. Waiting for a normal branch update would delay visibility.

### Q2. What happens when a configured remote is unreachable?

The user agreed to defer minting, retain the ledger entry, and report the failure. A repository with no configured remote still uses its local default branch.
