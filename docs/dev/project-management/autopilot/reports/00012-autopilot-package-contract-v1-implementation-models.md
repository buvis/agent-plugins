# AP00012 implementation model audit

PRD: 00012-autopilot-package-contract-v1.md; cycle: 1; work_start_sha: b1e05c75d6f0dad01db35258baf565ecaf5a77ad.
Fingerprint: `aca7b85369e1924a6b5fc597c03d575cd5571be014af4d4a9eea00d595790bc9`. The JSON preserves the driver's exact snapshot.
All cited lines are immutable copied native `turn_context` records; SHA-256 excludes LF.
`session_meta` in each source file identifies the native worker session and parent spawn.
Dispatch-ledger task/role records and per-task build evidence correlate those sessions
with the TDD/implementation/repair commits in the whole work range. Requested aliases
and provider/launcher brands were not used as actual-model fallback.

Observed contributing models are OpenAI gpt-6.1-sol and gpt-6-astra. Native logical
tiers remain Opus in schema; launcher stays codex. Both task3 contributors, test writers,
earlier contributing attempts, split tasks, actual copy workers and later repairs count.
Historical shared test writer session01a17745-1278-7e71-8abb-a5e25bb8e9e3 authored
commit044dfdd; its retained contract specification contributes to tasks2,3,4.
Task4 is the completed partial parent: its delivered test and golden-fixture work is
correlated to child17 tests063be41 and child18 fixtures33aaae4, rather than relabeling
the read-only Devon or discarded aborted partial files as implementation.

Task14 Sol test contribution c71a4c7 survives Astra strengthening6de9dfb,
implementatione9404d0 and style repairc1c3458. Task15 Sol067b52c survives
Astra f79c5ef/bb5b61d/afacf9d. Task19 Sol5755217 and Astra0669cd58 both
contribute to current delivery metadata. Task16 Sol2a28871 and Astra0e2aef9
test contributions survive final integration; its implementation worker is cited below.
Only actual changed cleanup/repair contributions need model rows; no-op cleanup is
excluded. All Pat sessions are tool-less read-only Anthropic review, not implementation.
Devon private mutants were discarded; task16 proved main HEAD/index/tracked bytes
unchanged. Planning/coordinator and review model mentions are excluded.

One explicit exception to coordinator-role exclusion is the concrete one-line PyYAML
test-dependency implementation patch, not a coordinator-model fallback: original native
transcript line3501 (SHA256 a03f1dc78ce8440deeeedb1f730d14f720d33bc43c8f0d0a3b1cce416954160d)
is paired with preceding observed turn metadata line2405. Both raw lines
are retained in task16-dependency-edit metadata. Actual model is gpt-6.1-sol, matching
the contributing test-author group. No other coordinator activity establishes provenance.

Required opposite-company completion review is Anthropic Claude Opus/xhigh for all
three fresh isolated lenses Alice, Blake and Bob. This audit makes no review verdict
or provider_review_guard claim. The next fresh review session must run review-route
and obtain every required successful helper receipt. No Eve invocation is claimed.

| Task | Observed model | Native session | Raw metadata file | Line |
| --- | --- | --- | --- | --- |
| 1 | gpt-6.1-sol | 01a1753b-0434-7e41-8f50-a4775f21dc1e | 00012-worker-1-native-metadata.jsonl | 2 |
| 2 | gpt-6.1-sol | 01a17745-1278-7e71-8abb-a5e25bb8e9e3 | 00012-tess-2-native-metadata.jsonl | 2 |
| 2 | gpt-6.1-sol | 01a17f29-7fb3-72e3-9b68-83afa9435ecd | 00012-task-2-tess-native-metadata.jsonl | 2 |
| 2 | gpt-6.1-sol | 01a17f30-ecfb-7f20-b25a-53654750861e | 00012-task-2-ivan-native-metadata.jsonl | 2 |
| 3 | gpt-6.1-sol | 01a17745-1278-7e71-8abb-a5e25bb8e9e3 | 00012-tess-2-native-metadata.jsonl | 2 |
| 3 | gpt-6.1-sol | 01a17f3d-487a-7282-a513-ac05ef2d5cc7 | 00012-task-3-tess-native-metadata.jsonl | 2 |
| 3 | gpt-6.1-sol | 01a17f42-6c88-7272-b049-c3217356bf89 | 00012-task-3-tess-quality-native-metadata.jsonl | 2 |
| 3 | gpt-6-astra | 01a17f51-eb95-73a3-9ce8-8d70ca481b85 | 00012-task-3-tess-astra-native-metadata.jsonl | 2 |
| 3 | gpt-6-astra | 01a17f57-4e12-7e93-9104-951c55a17766 | 00012-task-3-ivan-astra-native-metadata.jsonl | 2 |
| 4 | gpt-6.1-sol | 01a17745-1278-7e71-8abb-a5e25bb8e9e3 | 00012-tess-2-native-metadata.jsonl | 2 |
| 4 | gpt-6.1-sol | 01a17f8f-9825-7503-8241-261f13edfbac | 00012-task-17-tess-native-metadata.jsonl | 2 |
| 4 | gpt-6.1-sol | 01a17f92-75f1-7db2-8a31-b35b752037c9 | 00012-task-18-ivan-native-metadata.jsonl | 2 |
| 5 | gpt-6.1-sol | 01a17f98-e9c6-7391-a6b2-59b32f3fa479 | 00012-task-5-tess-native-metadata.jsonl | 2 |
| 5 | gpt-6.1-sol | 01a17fa1-0f16-7f00-b01e-9c151febf7ab | 00012-task-5-tess-strengthen-native-metadata.jsonl | 2 |
| 5 | gpt-6.1-sol | 01a17fa3-9c30-7d20-8c36-28a8500a4fb1 | 00012-task-5-ivan-native-metadata.jsonl | 2 |
| 6 | gpt-6.1-sol | 01a17fb2-fc57-77c0-a80f-a5bf34401bc9 | 00012-task-6-ivan-native-metadata.jsonl | 2 |
| 7 | gpt-6.1-sol | 01a17fba-d158-7ee3-aa96-22fc46a19d21 | 00012-task-7-ivan-native-metadata.jsonl | 2 |
| 8 | gpt-6.1-sol | 01a17fbf-3afc-7c30-b36e-c7ac9a08c3eb | 00012-task-8-ivan-native-metadata.jsonl | 2 |
| 9 | gpt-6.1-sol | 01a17fc3-985b-7833-b830-bf8725c83a7d | 00012-task-9-ivan-native-metadata.jsonl | 2 |
| 10 | gpt-6.1-sol | 01a17fca-9482-7b30-91c5-7cca4a9cc031 | 00012-task-10-ivan-native-metadata.jsonl | 2 |
| 11 | gpt-6.1-sol | 01a17fd0-a60a-7fd3-a28c-15a526ee3337 | 00012-task-11-ivan-native-metadata.jsonl | 2 |
| 12 | gpt-6.1-sol | 01a17fd7-dbab-7963-98f2-db60921c4c25 | 00012-task-12-ivan-native-metadata.jsonl | 2 |
| 13 | gpt-6.1-sol | 01a17fdc-1241-7883-b92d-5be91f8dad79 | 00012-task-13-ivan-native-metadata.jsonl | 2 |
| 14 | gpt-6.1-sol | 01a17fe3-4fb8-7ba0-a844-0fbfbd5e3ea0 | 00012-task-14-tess-native-metadata.jsonl | 2 |
| 14 | gpt-6-astra | 01a17fed-fd85-7a13-9c51-8c80c1bf75fc | 00012-task-14-tess-astra-native-metadata.jsonl | 2 |
| 14 | gpt-6-astra | 01a17ff2-f5c3-7821-9f67-01d9a248210e | 00012-task-14-ivan-astra-native-metadata.jsonl | 2 |
| 14 | gpt-6-astra | 01a17ff9-2130-7a11-aa68-329fe95d9a87 | 00012-task-14-style-astra-native-metadata.jsonl | 2 |
| 15 | gpt-6.1-sol | 01a17ffc-d62e-7073-b990-67217c0fdb78 | 00012-task-15-tess-native-metadata.jsonl | 2 |
| 15 | gpt-6-astra | 01a18002-93e7-70a1-82d8-bcd9c0d7ad0a | 00012-task-15-tess-astra-native-metadata.jsonl | 2 |
| 15 | gpt-6-astra | 01a18004-b69d-7171-ac3f-d9036ccd3761 | 00012-task-15-ivan-astra-native-metadata.jsonl | 2 |
| 15 | gpt-6-astra | 01a18008-913c-74b3-9e71-999e21e7a7f9 | 00012-task-15-newline-astra-native-metadata.jsonl | 2 |
| 16 | gpt-6.1-sol | 01a18011-04d8-7ea3-88d6-34e2367632db | 00012-task-16-tess-native-metadata.jsonl | 2 |
| 16 | gpt-6.1-sol | 01a18018-4236-7f11-b21c-fd5c4fafc73e | 00012-task-16-tess-quality-native-metadata.jsonl | 2 |
| 16 | gpt-6-astra | 01a1802d-e1a5-7600-8cba-6d620dcf4169 | 00012-task-16-tess-astra-native-metadata.jsonl | 2 |
| 16 | gpt-6-astra | 01a18037-c2ac-7752-9909-412410a2cd2c | 00012-task-16-ivan-astra-native-metadata.jsonl | 2 |
| 16 | gpt-6-astra | 01a18047-71bb-7192-9c55-78059c33605c | 00012-task-16-tess-pat-native-metadata.jsonl | 2 |
| 16 | gpt-6.1-sol | root dependency patch only | 00012-task-16-dependency-edit-native-metadata.jsonl | 1 |
| 17 | gpt-6.1-sol | 01a17f8f-9825-7503-8241-261f13edfbac | 00012-task-17-tess-native-metadata.jsonl | 2 |
| 18 | gpt-6.1-sol | 01a17f92-75f1-7db2-8a31-b35b752037c9 | 00012-task-18-ivan-native-metadata.jsonl | 2 |
| 19 | gpt-6.1-sol | 01a1800c-7d8c-7272-b913-f0c5edf5ad02 | 00012-task-19-ivan-native-metadata.jsonl | 2 |
| 19 | gpt-6-astra | 01a1801f-fed5-7322-a39f-af1633c11661 | 00012-task-19-repair-astra-native-metadata.jsonl | 2 |
