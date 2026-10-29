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

## Cycle 2 audit
Prior cycle snapshot preserved in 00012-cycle1-reviewed-models.json. Recovery task IDs correlate through attempts model_evidence, worker_session, task_base_sha and implementation_sha, as documented in 00012-recovery/rework-completion.md. Task20 includes the Astra mapper/test helper and independent Sol test author and correction. Task21 cites only the micro implementation turn; other coordinator activity and all Pat reviews are excluded. Aborted task24 and task44 histories remain accurately recorded. Every attempt already has observed actual_model/provider; no history was rewritten.

{"task": "22", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task22-raw-model-metadata.jsonl", "line": 2, "sha256": "5d6e30776b21027f65a5fedab7f80c0374e19ec0b506ef66aac6cd1e67ac31c8"}
{"task": "23", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task23-raw-model-metadata.jsonl", "line": 2, "sha256": "39f15523668432fdeafda5a6c21c586c7fc1a7cb71731b1b698161baf5f061da"}
{"task": "24", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task24-raw-model-metadata.jsonl", "line": 2, "sha256": "5fb4f59315acd380a6d56d46c5057a033341f9743284ade2af56512485c7c5e1"}
{"task": "25", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task25-raw-model-metadata.jsonl", "line": 2, "sha256": "8a06977c148bf5893516f92310bfe98c16cc8e3b65d39da6486ef85e9f96a5a1"}
{"task": "26", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task26-raw-model-metadata.jsonl", "line": 2, "sha256": "073c4ad38240089bd35b7bf4758367ce34714e11561fb048b810df5012b4c4a6"}
{"task": "27", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task27-raw-model-metadata.jsonl", "line": 2, "sha256": "558d6008fde6cda6e23b5ea2c098de363440d16eb1bb5182049e447261b2db58"}
{"task": "28", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task28-raw-model-metadata.jsonl", "line": 2, "sha256": "7f043d10008f57709defa814a5e02b1e823b7ee59bcc91bc0b01d1b8710906b8"}
{"task": "29", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task29-raw-model-metadata.jsonl", "line": 2, "sha256": "68896c9bb695656c67660c291383110abe2b7be3db3d688e8539c998908167f3"}
{"task": "30", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task30-raw-model-metadata.jsonl", "line": 2, "sha256": "0392c01445cdcb2fee83dbbb09e9ee43a8d2be6b391dd5099a2b34ad92e8f7ea"}
{"task": "31", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task31-raw-model-metadata.jsonl", "line": 2, "sha256": "b5439c8b4cfa631ead0495905f6680f0732871fc253eca21dfac75c165ad3f06"}
{"task": "32", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task32-raw-model-metadata.jsonl", "line": 2, "sha256": "61722872a90c3546f1c06827faadd7a8bedbfdeb702abbf20d16b7e79aae6ad3"}
{"task": "33", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task33-raw-model-metadata.jsonl", "line": 2, "sha256": "1f74216129ebdb58674bfcc068f1c48f2ee97885533474c1444abf930ffabb76"}
{"task": "34", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task34-raw-model-metadata.jsonl", "line": 2, "sha256": "2ee34511e0ededec5f2f26211eb9eabe4b80d21654b9a20cbc032e8b786f3083"}
{"task": "35", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task35-raw-model-metadata.jsonl", "line": 2, "sha256": "f29528d9ac10cf972f777b3bae4c6e5f2b3be85c8057bfe822b3ec1b5533c5fb"}
{"task": "36", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task36-raw-model-metadata.jsonl", "line": 2, "sha256": "66477355dd7fa2b107eadd09cb671d26bb491f0446cefd86285fa299df639de6"}
{"task": "37", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task37-raw-model-metadata.jsonl", "line": 2, "sha256": "c7b8b8055df2bd0062e7da7083afe5ed7702c2a162872e09d37b70279da5f0bf"}
{"task": "38", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task38-raw-model-metadata.jsonl", "line": 2, "sha256": "b86684b5d338d325c030895d9e9633a42dea07cfcaffd98f773fd204222f0d91"}
{"task": "39", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task39-raw-model-metadata.jsonl", "line": 2, "sha256": "4b2e3ce88ff6da90b2434f833786bfcb5d850fb60f7b3374a7f3d62614d56d50"}
{"task": "40", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task40-raw-model-metadata.jsonl", "line": 2, "sha256": "31418484564da7719b45fe55c724ddd7d43c5788e0e3fbecd0803538aba54eaf"}
{"task": "41", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task41-raw-model-metadata.jsonl", "line": 2, "sha256": "2cbbe0ccfc1aa1c9c82a6907fbe2d4f7eb53b77b572e3ed5f3671d10e4729298"}
{"task": "42", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task42-raw-model-metadata.jsonl", "line": 2, "sha256": "8589cb73b30ef6cd7397c5b807b301e8e8fa6a7c341482156412733bbfcaf1bb"}
{"task": "43", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task43-raw-model-metadata.jsonl", "line": 2, "sha256": "6e0162b8e5f400ab412cc19722448a184f533f618706ce59e210062554f6fcec"}
{"task": "20", "role": "implementation", "model": "gpt-6-astra", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/native-metadata.jsonl", "line": 2, "sha256": "e66fde6940ce1ed5bc6bd7f45d5f7b25d44a79afa2d5675f1a84a5f049194711"}
{"task": "20", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task20-pat-fix-raw-model-metadata.jsonl", "line": 2, "sha256": "164b5243093b793ac14a68264e6e006001fbe0f242afc06ecbe4804117dc93ad"}
{"task": "20", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task20-raw-model-metadata.jsonl", "line": 2, "sha256": "6a6a06fb75e05c8909bb5870c72027ea467a77d8da5ba0939c69e38e6f1a73f8"}
{"task": "20", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-task-20-ivan-native-metadata.jsonl", "line": 2, "sha256": "38844d85088a4b18f30ca1cd923a80abba091223df9a7dba1ff357b2e556b492"}
{"task": "21", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task21-raw-model-metadata.jsonl", "line": 2, "sha256": "beef5ba7693b39e1071c6da8d89809e80e229649f40ab187ba9725554bbcab36"}
{"task": "44", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task44-raw-model-metadata.jsonl", "line": 2, "sha256": "52222b7eb5d75a271add7038461e6c15d02b9072c10f68b9bd8b408db24ad6b2"}
{"task": "45", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task45-raw-model-metadata.jsonl", "line": 2, "sha256": "57888cef3ca1a893bfade03f27d4fd2471b00e6b13fd4c581e8b9ddf54c57a29"}
{"task": "46", "role": "implementation", "model": "gpt-6.1-sol", "path": "docs/dev/project-management/autopilot/reports/00012-recovery/task46-raw-model-metadata.jsonl", "line": 2, "sha256": "b70fcbfbba85b8778658f5d76ea82ff23d47c0c207665129f49eeaaf926340a4"}
