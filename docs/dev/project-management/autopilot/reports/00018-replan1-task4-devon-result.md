Task 4 broken: eight cumulative exploits passed eight required test runs, each reporting:

```text
....................                                                     [100%]
20 passed
```

Deliberately wrong implementation excerpts:

```python
# 1. Duplicate JSON keys accepted.
value = json.loads(raw.decode("utf-8"))

# 2. Sensitive state made world readable and writable.
self.path.chmod(0o666)

# 3. Invalid revision token types accepted.
if expected is not None:
    expected = int(expected)

# 4. Mutator changes silently discarded.
candidate["repo_root"] = current["repo_root"]

# 5. Successful publication guard invoked twice.
publication_guard()
publication_guard()

# 6. Valid nonfixture workflows rejected.
if value["workflow_id"] != "workflow-synthetic":
    raise StateError("only synthetic workflows supported")

# 7. Receipt removal silently undone.
if not candidate["receipts"]:
    candidate["receipts"] = current["receipts"]

# 8. Restore ignores decoded backup content.
candidate = copy.deepcopy(current)
```

Weak points:

1. `test_corrupt_current_is_never_replaced_by_backup_or_restore` — duplicate keys are accepted — inject duplicate keys into an otherwise valid state and require rejection without mutation.
2. `test_initialization_is_create_only_and_returned_states_are_isolated` — initialization publishes mode `0666` — assert state permissions exclude group and other access.
3. `test_real_process_cas_allows_exactly_one_writer_for_the_same_revision` — booleans and numeric strings become revision tokens — require rejection of `False`, `True`, and `"0"` with the pair unchanged.
4. `test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup` — requested root changes disappear silently — verify changed bindings are explicitly rejected or preserved according to contract.
5. `test_validation_conflict_mutator_and_publication_failures_preserve_exact_pair` — successful guards run twice — assert a successful guard runs exactly once.
6. `test_initialization_is_create_only_and_returned_states_are_isolated` — only `"workflow-synthetic"` initializes — initialize and read a second schema-valid workflow identity.
7. `test_transactions_copy_mutations_assign_revisions_and_preserve_last_good_backup` — clearing receipts does nothing — verify schema-valid receipt removal persists, or explicitly fails if forbidden.
8. `test_security_identical_restore_advances_current_revision_and_preserves_security` — restore substitutes current state for backup — test a distinguishable schema-valid backup and assert its required restoration or rejection.

Cleanup complete: experimental implementation overwritten with:

```python
# adversarial placeholder - overwritten by implementor
```

Touched source path: `/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/autopilot/controller/autopilot_state/store.py`

No test edits, commits, or controller state writes. No abort; input remained below 100K tokens.