# T-053 provisional eval

Run `concurrent-edit` with `--evals tests/specflow/evals/provisional/concurrent-edit`.
The fixture copies status-summary's synthetic spec tree. The runner applies the
second writer's replacement before turn 2; no helper concurrency tests are copied.
SR-IMP-004 exercises preservation of an intervening writer's work. This provisional
record supplements, rather than replaces, its inventory eval. Review the rubric
against the host's calls, not only its final claims. No live run is recorded yet.
