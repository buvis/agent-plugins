# specflow security review — 2026-11-15

Scope: T-054 of 00009. Static review and local regressions; no live host
security claim. Fetched text and artifacts are attacker-controlled data;
the host's permissions remain the execution boundary.

| Surface and material read | Result |
|---|---|
| `.agents/skills/catchup-specflow-upstream/SKILL.md`, `tools/specflow/upstream/sources.md` | No finding. Only configured HTTPS sources; fresh external temporary clones; read-only inspection; upstream instructions reported rather than followed; no upstream hooks, scripts, imports, dependencies or tests run. Cleanup is mandatory, with an explicit diagnostic path for retained failed clones. These are agent instructions, not an OS enforcement mechanism. |
| `specflow_helper/config.py`, config schema, contract config tests | **S1, low, fixed:** a configured symlink loop raised RuntimeError on Python 3.10 instead of ConfigError. Resolve strictly first, allow missing destinations, and convert resolution failures to rejection. Regression: `test_config_paths.ConfigPathTests.test_symlink_loop_is_a_config_error`. All three configured fields also reject traversal and absolute paths in `test_all_configured_path_fields_refuse_escape`; existing `test_kiro_specs_link_resolving_outside_is_refused` covers escaping links. |
| `SKILL.md`, `references/artifact-contract.md`, `references/phases/implementation.md` | No finding. SR-SKL-012 protects existing specs; SR-DLG-013 excludes secrets and copied environment values from artifacts/state/logs and records omission; SR-IMP-004 preserves unrelated edits. No secret was used as a test target. |
| `references/phases/intake.md`, `references/phases/verification.md` | No finding. Spike builds prohibit live services/production data; discard identifies the exact folder or branch and requires confirmation; graduation retains provenance and rebuilds implementation. Cleanup authorization remains required where recovery is uncertain. |
| `references/review/core.md`, `references/review/design/pre-pass.md`, `scripts/review/*.py` | No new finding. Artifact imperatives remain data (SR-RVC-048/044); isolated review receives a bounded package and edits nothing. Advisory scanners only read supplied documents and report signals; English patterns and fence omission are explicitly limited heuristics, not an injection firewall. |
| `specflow_helper/drift.py`, `references/state-contract.md`, `tests/specflow/contract/test_drift.py` | No finding. Explicit baseline paths reject traversal, absolute paths, symlink components and nonregular files; baseline stores hashes, not copied content. `test_one_refused_path_leaves_no_partial_baseline` and `test_baseline_holds_hashes_not_source_content` cover the boundary. |
| `references/review/cross-spec.md` | No finding. Reshapes need approval before folder changes, exclude implementation/complete specs, retain intake provenance and validate all affected specs (SR-RVX-065/067). |
| `scripts/check_links.py`, `tests/specflow/review/test_check_links.py` | No new finding. T-077 regressions retained: `test_symlink_escaping_the_root_is_a_scan_error_and_not_read`, `test_a_linked_intake_folder_outside_the_root_is_never_indexed`, `test_a_numbered_intake_link_outside_the_root_never_resolves`, `test_a_looped_markdown_link_is_not_a_crash`. Home/absolute/wiki targets are warnings and never dereferenced, covered by `test_warns_on_home_and_absolute_paths_and_never_resolves_them` and `test_warns_on_wiki_links_and_never_resolves_them`. |
| T-076 advisory regressions in `tests/specflow/review/` | No new finding. Retain `test_any_you_are_now_role_is_a_role_change`, `test_reports_adversarial_and_framing_categories`, and each scanner's `test_unreadable_document_exits_1_without_a_traceback`; fence parsing and line-position regressions remain in their original suites rather than copied. |
| Python files in package, maintainer tools and eval runners | Required AST dependency test `test_shipped_and_maintainer_scripts_import_only_the_standard_library` checks every absolute import, skips relative imports, and permits stdlib and repository-local modules only. This checks declared imports, not dynamic execution or host binaries. |
| Runner changes `2e8816e`, `b207fc6` | No new finding in the changes: Codex compares instruction fingerprints and fails closed on differences; private-home normalization removes batch randomness. Kiro later-turn context inventory requires the proof's verified flag. Pending Codex field comparison and unnamed shell-read measurement remain unresolved release-evidence limitations; this review does not waive either. |

Verification: security suite (3 tests) passes on Python 3.10.22 and 3.15.2;
contract suite (390) and review suite (41) pass on Python 3.15.2.
CI runs the security suite including the dependency scan on Python 3.10 and
3.15. Remote CI execution is pending push. Rule tests require the shipped
package to be committed before their revision-bound checks can pass.
