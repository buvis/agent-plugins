# AP00018 v2 Task 1 reconciliation

Reconciled 2026-11-09. Existing Task 9 and Task 10 evidence satisfies the
pinned ownership and closed protocol characterization gate. No remaining
defect required production, fixture, provenance or test changes.

Task 9's source characterization report is committed at
`1ded60f0fdee316576d240b8c095308b63dae99a`. It records the exact OVCAQ pin
`cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7`, all 15 raw source-blob SHA-256
checks, source-symbol checks and 144 source fields. All 15 recorded and
observed hash pairs in that report match current provenance. The current
ownership map retains 137 deferred, three excluded, two preserved and two
redesigned fields. Its four core mappings match `kernel_field_ownership`.
The completed pinned-source inspection was reused; no source inspection
was replayed and no legacy schema equivalence was inferred.

Task 10's build evidence records implementation commit `32aaa4a` and its
successful 33-test gate. Current fixtures were last changed by that commit.
The characterization test's current bytes also exactly match strengthening
commit `4dd90b07626e423020df54d90d0509e569c1defc`. Current provenance,
fixtures, characterization tests and schema tests match HEAD.

Current coverage retains both frozen kernel states and rejects all 16
declared unowned fields at top level and under workflow through both JSON
Schema and runtime validation. Nine positive protocol examples cover fresh
and existing open, acquire, release, recover and their four responses;
each rejects unowned envelope/payload or response/result fields. The eight
Task 10 strengthening cases remain present: required fields, invalid
revision text, negative revisions/epochs, owner process identity, three
otherwise-valid actor descriptors, populated tasks, changed review cap and
independent valid states. The schema suite retains its existing strict
decoding, closed-field, resource-limit and validation-before-copy checks.

Inspected current bytes:

| File | SHA-256 |
| --- | --- |
| `plugins/autopilot/contracts/controller/provenance.json` | `6172dff49c67a3eb1a6fc8056980b814023410aa1eaf5097efcd3ab22fff696c` |
| `plugins/autopilot/contracts/controller/fixtures-v1.json` | `50788e87e2a0a301d6f08a299e250f706cc64302263e5bf9e1b889b7abf8e077` |
| `tests/autopilot/test_controller_recovery_characterization.py` | `3d48c8e0e37f173a006c54d4660de2878b58d388452fe85416c9f1519ea05098` |
| `tests/autopilot/test_controller_schema.py` | `3979de5576c5c5168ccf107976dfc1348cb0b6e07d1327a3ff4441520144e7d3` |

Executed once with a 300-second subprocess timeout, using the task's
mandatory `--tb=line` reporting option:

```text
mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_recovery_characterization.py tests/autopilot/test_controller_schema.py -q --tb=line
33 passed in 0.36s
exit code: 0
```

Scope: reconciliation report only. No v1 completion flags were imported.
Historical receipts, reviews, attempt counters, custody, package entry
gates and controller state were untouched. No commit, publication,
installation, source retirement or push ran. Full-suite and repository
validation remain the orchestrator's final gates.

ASSUMPTIONS: none

FILES_TOUCHED:
docs/dev/project-management/autopilot/reports/00018-v2-task1-reconciliation.md
