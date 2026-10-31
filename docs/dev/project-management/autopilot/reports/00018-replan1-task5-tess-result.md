1. strengthened: `test_refuses_missing_and_nondirectory_roots_without_creating_state` — additional missing names.
2. strengthened: same test — differently named regular files.
3. strengthened: `test_resolves_existing_directory_without_inferring_an_ancestor_workflow` — another alias and chained alias.
4. strengthened: same test — independently named nested projects.
5. strengthened: `test_refuses_symlinked_private_components_and_aliased_fixed_artifacts` — every component under unrelated basename.
6. strengthened: `test_refuses_hardlinked_fixed_artifacts_under_any_project_name` — every fixed artifact under unrelated basename.
7. strengthened: `test_refuses_symlinked_fixed_artifacts_and_preserves_their_targets` — every artifact symlink; target bytes preserved.
8. strengthened: `test_resolves_relative_directories_and_refuses_relative_missing_or_file_roots` — canonical absolute results and relative rejection.

Touched: `tests/autopilot/test_controller_paths.py` only.

Static syntax and size checks passed: 160 lines; every function under 50 lines. Pytest not run: target absent per dispatch. No production reads, commits, or state writes.

ASSUMPTIONS: none