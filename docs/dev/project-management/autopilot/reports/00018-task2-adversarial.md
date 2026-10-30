# Task2 adversarial proof

Your tests can be passed by a wrong implementation:
1. parse_float=_wrong_float where finite float values return0.0.
2. duplicate-key guard: if key in result and result[key] != value: fail; result[key]=value.
3. integer guard applies only if value>=0, exempting negative integers.
4. object recursion checks key type but not UTF-8 byte length.
5. actor validator omits identity(actor_id).
6. receipt response validator omits counter(revision).
7. if candidate.owner==current.owner, replace candidate.actors with deepcopy(current.actors).
8. write/flush file then announce TEMP_FSYNCED without os.fsync.

Test output (all passing):
Each cumulative exploit1..8 ran the exact named narrow command once and returned35 passed, exit0; durations0.46,0.44,0.44,0.39,0.43,0.40,0.40,0.43s.

Weak points:
1. `test_decodes_complete_json_and_preserves_distinct_nested_values` — finite decimals become `0.0` — assert exact decoding of distinct positive, negative, and exponent-form finite decimals.
2. `test_rejects_duplicate_keys_nonfinite_numbers_and_malformed_json` — identical-value duplicate keys are accepted — reject `{"same":1,"same":1}` and nested equivalents.
3. `test_decoder_rejects_byte_depth_and_integer_resource_overflow` — negative integers bypass the 640-digit limit — reject `"-" + "9" * 641` and accept the negative 640-digit boundary.
4. `test_decoder_rejects_byte_depth_and_integer_resource_overflow` — oversized object keys bypass string limits — reject an object containing a key exceeding `MAX_STRING_BYTES`, including UTF-8 multibyte cases.
5. `test_actor_owner_and_receipt_objects_have_closed_fields_and_bounded_identities` — actor descriptor IDs accept arbitrary JSON types and oversized strings — reject invalid `actor_id` values in active actors and receipt authorizing actors.
6. `test_receipts_retain_complete_success_responses_and_reject_oversized_responses` — receipt response revisions accept booleans, strings, and negative numbers — reject malformed response revision values explicitly.
7. `test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup` — actor updates disappear when the owner stays unchanged — rotate a valid actor digest without changing ownership; assert returned state, persisted state, and previous backup.
8. `test_successful_publication_reports_all_six_boundaries_and_commits_only_its_path` — durability hooks report successful file synchronization without file `fsync` calls — verify regular-file `fsync` precedes each corresponding boundary and inject file synchronization failures.

Address every numbered weak point. Answer each in your reply as
`N. strengthened: <test name>` or `N. in-contract: <why the behavior is allowed>`.
Do not change tests that Devon could NOT break.

Run only the test files this task names (the tests you wrote, or the
failing tests in your prompt), with `-q --tb=line`. Never run a whole test
directory or `dev/bin/release-checks`: the orchestrator runs the full suite
once, after every task. Read the pass count and exit code from that one
run; never re-run a suite to recover a number.

Scope: existing /Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_controller_kernel.py and optional new /Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_controller_kernel_adversarial.py. Keep every file<800 lines/functions<50; create additional assertions in the sibling file rather than refactor unbroken tests. You may import public test helpers from the original test file, but avoid imported TestCase duplication. Runtime files are currently Devon placeholders; do not read them or implementation/source. No runtime changes or commits. Use PYTHONDONTWRITEBYTECODE=1. One narrow run may report collection failure until Ivan implements; report honestly.

All four wrong implementations were overwritten with prescribed placeholders; no tests changed or commits made by Devon.
