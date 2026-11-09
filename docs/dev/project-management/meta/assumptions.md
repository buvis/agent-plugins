# Assumption ledger - AP 00018 v2 (autopilot controller kernel)

Per-plan ledger: replaced at the first task of this plan that records one, per
the work skill's assumption-ledger rule. The Codex host ran tasks 1, 2, 3, 9, 10
and 11 without writing here; their assumptions live in
`docs/dev/project-management/autopilot/reports/00018-v2-*`. The previous AP00014
ledger is in git history.

## 4: Bound pre-intent staging artifacts across bootstrap and owner mutations

Tess (strengthen after Devon):

- The full proposed file set equals what an `intent_replace` crash leaves (stages, rollback copies, intent temp), not the transient StateStore publication temps.
- A forged credential must be rejected by authentication before the staging budget runs, with any error code except `recovery_required`; no specific code is pinned.
- For a bad `expected_revision`, any rejection code is accepted; only the returned revision value is checked.
- Exempting `state.json.lock` from the ctime check is safe: a black-box probe showed it is the only entry whose ctime a read-only call changes.

Ivan:

- The proposed set is the credential stages, rollback copy and intent temp; the StateStore publication temporary is not pre-budgeted (tests require admission at exactly owned + proposal == 64). Pat LOW: a crash at a publication boundary can retain up to two state-size temps beyond the admitted budget; later mutations then refuse. Deferred to task 6's recovery docs.
- Owned artifacts are identified by exact generated-name patterns; other names in these directories do not count toward the budget.
- Only new bootstrap and owner mutations are budgeted; intent reconciliation, receipt replay, snapshots and `workflow.open` on an existing state are not (the last is untested).
- Removing the stale-temp cleanup applies to the whole StateStore library, not only the controller; a per-store option did not fit the harness's exact constructor signature.

## 5: Export canonical controller bundle and prove isolated relocation

Orchestrator:

- Exporter CLI pinned to the repo generator convention (no args writes, `--plugin-root`, `--check` exits 0/1, argparse misuse exits 2); the contract names no flags.
- Task 5 writes only the bundle sha256 pin and installed argv into the README, because its acceptance asserts the README digest; Task 6 writes the remaining docs.

Tess:

- The exporter is one self-contained stdlib script whose default plugin root comes from its own location (`../../plugins/autopilot`).
- The bundle's operations/capabilities equal the implemented sets (4 operations, `workflow.core.v1`); list order is not pinned.
- README holds the exact `sha256sum` line with two spaces and the literal argv; "affirmative" means the argv paragraph has no not/never/avoid/n't.
- Export over a symlink at the bundle path replaces it; missing inputs and an invalid version exit non-zero (not pinned to 1); the bundle mode may not exceed the sibling schema file's bits.
- An installed controller run with `-B` writes nothing inside its package folder; a `+<build>` suffix follows the semver build pattern.

Ivan:

- Bundle serialization is indent-2, sorted keys, trailing newline; mode is the schema file's bits masked to 0o666.
- Input errors exit 1, the same code as a stale `--check`; only `contracts/` between the plugin root and the bundle is checked for symlinks, the root itself is trusted; a small lstat-to-read window remains (no O_NOFOLLOW).
- Pat LOWs left open: the explicit parent check is redundant with the input walk; no test covers the input size cap.

## 6: Document supported kernel Python floor and sealed-workflow recovery

Ivan:

- "Verify an unchanged snapshot" in orphan recovery means run `snapshot` and confirm the state is unchanged after moving the orphans.
- The new content sits in `###` subsections under the Task 5 `## Controller contract bundle` heading; the sibling archive is "named by the workflow ID" with no invented path.

Orchestrator: Task 5's README text named the unshipped exporter as a `python3 tools/...` command, which the package resource-closure check rejects; it now names the tool without a command form (b56b106).

## 7: Add tested successor delivery receipts for current package ownership

Orchestrator: successor format pinned (path, fields, binding `paths`); Task 7's gate is the generator tests, the committed-map assertions go green at Task 8.

Tess:

- README.md/CHANGELOG.md in the successor `paths` rule mean the plugin's files; an unlisted shared doc keeps its whole AP00013-pinned row.
- A successor task's `tests` lists ", "-separated test files that exist and appear in its `command`; a string `passed` or a blank status is invalid.
- The new contract asset row uses the standard asset field set with source fields None.

Ivan:

- A listed controller path with no existing asset row (other than controller-v1.json) is ignored, not refused.
- A successor without loaded AP00013 receipts is refused; contract rows are upserted on every run that lists the path.
- Pat LOWs left open: the contract-row construction could move into a helper; the CHANGELOG entry describes an unshipped maintainer tool.
