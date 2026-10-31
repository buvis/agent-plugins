1. strengthened: `test_corrupt_current_is_never_replaced_by_backup_or_restore`
2. strengthened: `test_initialization_is_create_only_and_returned_states_are_isolated`
3. strengthened: `test_revision_tokens_reject_booleans_and_strings_without_changing_the_pair`
4. strengthened: `test_root_binding_change_is_preserved_or_explicitly_refused_without_publication`
5. strengthened: `test_validation_conflict_mutator_and_publication_failures_preserve_exact_pair`
6. strengthened: `test_initialization_is_create_only_and_returned_states_are_isolated`
7. strengthened: `test_schema_valid_receipt_removal_persists_and_keeps_the_previous_backup`
8. strengthened: `test_security_identical_restore_advances_current_revision_and_preserves_security`

Touched:
- `tests/autopilot/test_controller_kernel.py`
- `tests/autopilot/test_controller_kernel_adversarial.py`

Required pytest run: exit 2; two collection errors because `autopilot_state.store` is unavailable; zero tests executed. No rerun. Both files remain under 800 lines; every function is under 50 lines.

No production edits, commits, or controller state writes.

ASSUMPTIONS: none
8. strengthened: `test_security_identical_restore_advances_current_revision_and_preserves_security` now distinguishes backup through schema-valid `repo_root`, preserving frozen workflow and security fields.

Touched: `tests/autopilot/test_controller_kernel.py`. All other changes preserved. Size checks passed. Pytest not rerun because store is absent.

ASSUMPTIONS: none