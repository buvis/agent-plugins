# Canonical workflow fixtures (T-050)

`inventory.json` defines 27 workspaces and their expected status and validation
findings. All content is test data, including instruction files, approval
records, and task outcomes. No fixture claims a live host run.

Each `copies` entry copies a directory relative to `tests/specflow/fixtures/`
to a workspace-relative destination. Apply entries in order; later files
replace earlier files. This reuses session workspaces and the T-027 Kiro
captures without duplicating them. Directories here contain only missing
files or changed bytes. There are no generated hashes or approvals at test
time, and no symlinks or Git repositories to carry between hosts.

`test_fixtures.py` materializes each workspace outside the checkout, runs the
real `status --json` and `validate --json` commands, checks state and status
schemas, compares exact errors and warning counts, and verifies that nothing
was rewritten. The existing contract-test CI step discovers it.

| Cases | Purpose and reuse |
|---|---|
| `standard-feature`, `standard-bugfix` | Approved implementation states from `implementation-failed-check` and `bugfix-refuted`; the session names describe later dialogue, not fixture validation failures. |
| `partial-feature`, `partial-bugfix` | Existing `design-review-quick` and `bugfix-confirmed`: draft design and missing tasks, respectively. |
| `quick-feature`, `quick-bugfix` | The same complete artifact sets with a quick profile; quick does not remove canonical documents. |
| `stale-feature` | Existing `design-stale-upstream`: one changed requirements artifact, one stale approval. |
| `design-first-partial-*` | Approved design with draft requirements/tasks; requirements is the next phase for both types. |
| `design-first-stale-*` | One change to approved design stales design and both downstream approvals; the three errors are one cause and its propagation. |
| `verification-feature`, `completed-feature`, `completed-bugfix` | Reuse `completion-success` and `bugfix-refuted`; check completion criteria for features and the final checkpoint for Kiro bugfix plans. Added completion outcomes are synthetic. |
| `hold-and-intake` | Reuse `status-summary`, including both processed intake items and Q&A logs; hold suppresses the first spec's next task. |
| `recovered-*` | Original T-027 captures with recovered type/order/profile and draft state. No approval is inferred from their existence. Original canonical files, numbering, license and provenance remain byte-identical. |
| `configured-workspace` | Reuse `00101-feature-sample` under `planning/specs`, with intake under `planning/work`; no `.kiro/specs` link. |
| `intake-only` | Only an unprocessed idea and Q&A log; T-051's handoff starting point. No spec exists. |
| `spike-standalone`, `spike-branch`, `spike-sketch` | Built spike snapshots: standalone greeting output under the intake item, existing-code greeting output with a branch-name receipt, and a one-screen journey with mockups. Existing session fixtures are pre-spike inputs, so cannot supply these shapes. The branch case records a synthetic branch snapshot; it neither creates nor claims to run a Git branch. |

The recovered native captures deliberately retain their existing diagnostics:
requirements-first has one uncovered requirement (5) and seven source warnings;
Design-First has one uncovered requirement (8), four bare `N/A` placeholders,
and eleven source warnings; bugfix has 52 portability warnings for paths in
the original public capture. These are input evidence, not newly introduced
malformed cases or exceptions to production validation.

Each malformed case has exactly one error, specified in the inventory:

| Case | Isolated fault | Expected error |
|---|---|---|
| `missing-required-path` | Requirements file absent; validate at the tasks phase so implementation gate errors do not mask the path check. | `required-files` |
| `invalid-state` | Integer profile instead of string. | `state-valid` at `$.profile` |
| `unsupported-version` | State schema version 2. | `state-valid`, unsupported version |
| `recorded-hash-mismatch` | Tasks approval hash replaced by 64 zeroes; artifact bytes unchanged. | `stale-approvals` on tasks only |

Run from the repository root:

```sh
python3 -B -m unittest discover -s tests/specflow/contract -p test_fixtures.py
```

To prepare a later handoff workspace, apply the `intake-only` copy entry to an
empty directory. Host runners must establish and verify their own isolated
Git root under T-056; these deterministic checks do not prove host isolation.
