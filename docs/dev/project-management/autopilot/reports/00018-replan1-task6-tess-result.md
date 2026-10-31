Created 20 task6 tests across:

- `tests/autopilot/test_controller_bootstrap.py`
- `tests/autopilot/test_controller_bootstrap_recovery.py`
- `tests/autopilot/controller_cli_support.py`

Covers bootstrap, snapshots, strict parsing, authentication/replay, concurrency, private credentials/ignores, and all five bootstrap crash boundaries.

Python 3.12 run: **19 failed, 1 passed; exit 1**, because `controller/main.py` is absent. Fixed the argument-misuse test’s missing-runtime false positive afterward; no rerun. Syntax verified; functions remain below 50 lines. No production reads, commits, or controller-state writes.

ASSUMPTIONS:
Crash labels correspond to observable credential-file and directory fsync boundaries.
Snapshot assertions cover only explicitly named public fields and redaction.
Corrected task6 error mappings: well-typed revision mismatches expect `revision_conflict`; bootstrap actor mismatches expect `wrong_binding`. Malformed fields remain `invalid_request`.

Preserved all sound tests and the CLI-presence guard. Per latest steering, added no interim owner-handler assertions. Only `tests/autopilot/test_controller_bootstrap.py` changed.

All three test files pass syntax and size checks. No pytest rerun, production reads, state writes, or commits.

ASSUMPTIONS: none
1. strengthened: `test_bootstrap_publishes_one_private_operator_state_and_receipt` — independent secrets differ.
2. strengthened: `test_archiving_controller_allows_new_identities_at_the_same_project_path`
3. strengthened: `test_credentials_reject_wrong_permissions_symlinks_hardlinks_and_secrets` — all credential bindings.
4. strengthened: `test_request_byte_and_utf8_identity_limits_accept_the_exact_boundary` — five oversized lengths.
5. strengthened: `test_request_identity_utf8_limit_applies_to_varied_ascii_and_multibyte_values`
6. strengthened: `test_unknown_operation_names_never_alias_workflow_open`
7. strengthened: `test_bootstrap_fsyncs_final_state_inode_and_contents_before_publication`
8. strengthened: `test_contract_without_project_root_matches_public_metadata_and_current_scope`

Touched:

- `/Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/controller_cli_support.py`
- `/Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_controller_bootstrap.py`
- `/Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_controller_bootstrap_recovery.py`

Static checks pass: 25 tests; functions <50 lines; files <800 lines. Runtime remains unavailable. No pytest/Devon rerun, production reads, commits, or controller-state writes.

ASSUMPTIONS: none