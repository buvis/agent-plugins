# Incomplete task 5 Pat review — preserved, not accepted

Native Sonnet claude-sonnet-5-5/high, session 5f560368-70d2-459e-b9ec-257a789d8070.
The coordinator incorrectly excluded tests/autopilot/test_helper_rework_sinks.py
to fit the prompt cap. Root stopped the owning loop (exit 130); the reviewer
returned text in its native transcript. This is incomplete scope, not a passed
Pat gate. Complete the scope in the same isolated reviewer conversation.

CLOSURE | resolved | "The ownership-window defect ... `_open_result_sink` decides 'this run created the leaf' with a separate `artifact.exists()` ... identity from a later `os.lstat` by name ... also the artifact write/close failure leaving a reusable record, the spawn-failed empty-log residue, the unguarded `os.close(pin[0])`, the un-restorable truncated pre-existing artifact (out of scope)" | `_acquire_sink` takes creation from `os.open(... O_CREAT|O_EXCL)` and identity from `os.fstat` on the descriptor. `_close_result_sink(..., untrusted)` removes a created leaf or empties an existing one. `_execute` unlinks a created log on `spawn-failed`. `_close_pin` guards the parent-fd close. The restore case stays out of scope.

CLOSURE | resolved | "Two more v1 tests fail because _open_log_sink changed contract ... test_sink_opener_creates_parents_and_a_fresh_unbuffered_binary_file and ::test_sink_opener_refuses_symlinked_parents_and_replaces_symlinked_leaf" | The default `_open_log_sink` is back to unlink plus `O_CREAT|O_EXCL`, so it replaces the leaf and never touches a symlink's target. The non-destructive mode is the separate `preserve=True`. Both nodes are green in the recorded 223-passed run.

CLOSURE | resolved | "`_worktree_gitdir_pointer` reads any in-repo file that is the same inode as a sibling `.git` file, for example a nested repo's pointer" | `pointer = _worktree_gitdir_pointer(resolved) if resolved.parent == toplevel else None` limits the read to the supplied repository's own pointer.

CLOSURE | resolved | "Late sink failures do not terminate surviving process-group descendants" | `_run_against_sink` now carries `pgid`. `_execute` calls `_kill_group(result["pgid"])` on `sink-close-failed`, and `_run_and_record` calls it when `_write_artifact` fails. Whether `pgid` stays out of reports depends on `_artifact`, which is not in the diff.

CLOSURE | resolved | "`_open_log_sink`'s post-open validation checks `S_ISREG` and `st_nlink == 1` but not the executable bit" | `preserve=True` validation now includes `or info.st_mode & 0o111`, applied to the opened descriptor via `fstat`.

CLOSURE | resolved | "neither new test file drives `run_verification` with a symlinked `project_root` ... against a resolved-spelling `log_path`/`artifact_path`" | The new alias regression is in the excluded module, so I did not judge it. The recorded evidence is 14 red before and 223 green after. The production alias handling is fixed in `_symlinked_component` and `_pinned_parent_fd`, which now accept the resolved spelling.

MEDIUM | plugins/autopilot/scripts/log_sink_refusal.py:146 | The new alias escape in `_symlinked_component` (`not current.is_relative_to(repo_root) and current.resolve() in stops` then `break`) also stops the walk at a symlink below the root when the path uses the resolved spelling. Example: `repo_root=/tmp/repo`, log `/private/tmp/repo/sub/x.log`, with `sub` a symlink to the repo root. `/private/tmp/repo/sub` is not relative to `/tmp/repo`, and its `resolve()` equals `repo_root.resolve()`, so the walk breaks and does not refuse. The unresolved spelling `/tmp/repo/sub/x.log` is refused. The `_pinned_parent_fd` fallback then calls `parent.resolve()`, which follows the link and opens the root, so the sink is written through a symlinked component. This breaks criterion 8 (a symlink below the root is still refused, under either spelling). | Apply the escape only when `current` is outside both spellings: `not current.is_relative_to(repo_root) and not current.is_relative_to(repo_root.resolve()) and current.resolve() in stops`. Add a resolved-spelling test with a below-root symlink to the root.

LOW | plugins/autopilot/scripts/verification.py:326 | `_acquire_sink` closes the exclusive-create descriptor before `_open_log_sink(preserve=True)` reopens by name, then compares inode numbers. In that window the created inode can be freed and its number reused, so the identity check could match a different file. | Keep the first descriptor open until the reopened sink's `fstat` has been compared, then close it.

LOW | plugins/autopilot/scripts/log_sink_refusal.py:99 | `resolved.parent == toplevel` is a string comparison. On a case-insensitive volume a case-aliased parent spelling would skip the pointer read. | Compare with `os.path.samefile` or a normalized path if case aliases of the pointer matter here.

LOW | plugins/autopilot/scripts/verification.py:307 | `_Pin` is a 4-tuple accessed as `pin[0]` and `pin[3]`. `_unlink_pinned` and `_empty_pinned` repeat the same lstat-and-identity prologue. | Use a `NamedTuple` with `parent_fd`, `name`, `identity` and `created`, and share the identity check in one helper.

LOW | plugins/autopilot/scripts/log_sink_refusal.py:211 | `_open_log_sink` tests `if preserve:` twice, in two separate blocks. | Branch once, or move the validation into the first branch.
