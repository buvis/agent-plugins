# Tasks: Split long validator functions

Run these tasks only after helper status opens the implementation gate. Use Python 3.10 for baseline and final verification, with `-B` or `PYTHONDONTWRITEBYTECODE=1`. Before every commit, run this worktree's gate and repository-wide helper status without reconciling other specs. Make one conventional commit per task, without Co-Authored-By; include the prepared spec/intake artifacts in the first task's commit. Keep approved requirements and design unchanged. Write progress only as task checkboxes and one-line Outcome fields under tasks.

- [x] T-001 Characterize manifest validation on the original code
  - Requirements: REQ-002, REQ-004, REQ-005
  - Depends on: none
  - Location: `scripts/test_validate_characterization.py` (new shared fixture and ManifestCharacterization tests); `docs/dev/tmp/review-tools/gate.sh` and logs (untracked verification support).
  - Reuse: `scripts/test_validate.py` unittest, temporary template-copy, and boundary-patching patterns; public `validate_manifest`; the eight commands in `.github/workflows/validate.yml` and worktree-gate precautions from the review recipe.
  - Contract: Characterization tests call public entry points, never the extracted helpers.
  - Contract: Record the baseline commit, Python version, command, and passing test count in the characterization task's Outcome before changing `validate.py`.
  - Details: Prepare the gate in this worktree from its own CI: validator tests, package validation, release/contract/rules/review tests, rule inventory with the current area list, and release boundary. Resolve its root to this worktree, disable bytecode, use managed Python 3.10, and record separate command logs and the interpreter version. Add tests for minimal/all-optional manifests, complete returned dictionary including nested extensions, unchanged input bytes, empty optional strings/collections, accepted whitespace strings, 64/65-character names, and supported version forms. Cover missing/directory/escaping-symlink files, malformed JSON/non-object roots, invalid values for every manifest check, sorted unknown fields, optional metadata type before version, author insertion order, and competing failures across schema/name/metadata/version/author/keywords/extensions. Include invalid UTF-8 and deterministic read failures with original exception class, full text, and cause where applicable. Keep `scripts/validate.py` and every existing test unchanged. Do not create the structural test yet.
  - Acceptance criteria: REQ-002 criteria 1, 2, 3; REQ-004 criterion 3; REQ-005 criteria 1, 2, 3, 4 (manifest preservation and baseline gate portions).
  - Verify: `python3 -B -m unittest discover -s scripts -p test_validate_characterization.py -k ManifestCharacterization` passes against original code; `git diff --exit-code 6c16d03d7f5e878a3033de747866c931edcf12bf -- scripts/validate.py scripts/test_validate.py` confirms the baseline; `sh -n docs/dev/tmp/review-tools/gate.sh` and its first complete run pass, with logs confirming this worktree and Python 3.10. Record that original-code evidence before committing `test: characterize manifest validation`.
  - Outcome: Added 13 ManifestCharacterization tests, passing on original validator at 6c16d03d7f5e878a3033de747866c931edcf12bf with Python 3.10.22 via unittest discover -s scripts -p test_validate_characterization.py -k ManifestCharacterization; existing tests unchanged, Ruff passes, worktree gate passes all eight CI checks (25 validator, 54 release, 387 contract, 58 rules, 41 review tests); logs retained under docs/dev/tmp/review-tools/t001-logs.

- [x] T-002 Characterize MCP validation on the original code
  - Requirements: REQ-003, REQ-004, REQ-005
  - Depends on: T-001
  - Location: `scripts/test_validate_characterization.py` (McpCharacterization tests and MCP fixture setup).
  - Reuse: T-001 temporary fixtures and exception assertions; public `validate_mcp`; synthetic JSON created explicitly because the template has no mcp.json.
  - Contract: Optional helpers run only under the original key-presence guards, never via truthiness or a default that merges absent and null values.
  - Contract: Record the baseline commit, Python version, command, and passing test count in the characterization task's Outcome before changing `validate.py`.
  - Details: Add accepted absent-file/empty-server cases, stdio bare/contained commands, empty args/env/headers, all permitted cwd root spellings, both remote transports, HTTPS and accepted HTTP loopback forms, None returns, and unchanged input bytes. Add rejection cases for files, JSON roots, schema, servers, names, server objects, transport, command separators/traversal, args/env/cwd/header types and values, reserved variables, and URL/userinfo/fragment/TLS rules. Pin first-failure order within a server and between servers. Characterize broken-symlink early return, invalid UTF-8, deterministic read failures, malformed URL parsing exceptions, and unhashable transport exceptions without adding runtime guards. Preserve existing tests and T-001's assertions; only additive cases and fixture support are in scope.
  - Acceptance criteria: REQ-003 criteria 1, 2, 3; REQ-004 criterion 3; REQ-005 criteria 1, 2, 3 (MCP preservation portions).
  - Verify: `python3 -B -m unittest discover -s scripts -p test_validate_characterization.py -k McpCharacterization` and the full characterization module pass against original `validate.py`; compare that file with commit `6c16d03d7f5e878a3033de747866c931edcf12bf`. Record the original-code evidence, then run the shared pre-commit checks and commit `test: characterize MCP validation`.
  - Outcome: Added 13 McpCharacterization tests, passing on original validator at 6c16d03d7f5e878a3033de747866c931edcf12bf with Python 3.10.22 via unittest discover -s scripts -p test_validate_characterization.py -k McpCharacterization; all 26 characterization and 12 existing validator tests pass, Ruff and the eight-command gate pass; original tests and validator unchanged; logs retained under docs/dev/tmp/review-tools/t002-logs.

- [x] T-003 Characterize CLI output and failure ordering on the original code
  - Requirements: REQ-004, REQ-005
  - Depends on: T-002
  - Location: `scripts/test_validate_characterization.py` (CliCharacterization tests and CLI fixture setup).
  - Reuse: Existing `ValidateMaintainerSkills.run_main` stream-capture and argv/ROOT boundary-patching pattern without editing or importing the test class; T-001/T-002 fixtures; `sys.executable -B` for subprocess checks.
  - Contract: Dynamic JSON-parser and OS wording is established on the same interpreter using deterministic inputs or injected exceptions, not frozen from another Python version.
  - Contract: Rerun the unchanged characterization tests after each extraction.
  - Details: Add direct-main tests for default discovery versus explicit paths, exact package/skill success output, empty success stderr, multiple plugin errors in order, manifest failure suppressing later checks, and maintainer-skill selection. Add subprocess success/failure smoke tests asserting actual exit codes and full stdout/stderr. Use no network or real credentials. Finish all preservation tests and run them together while both validators remain original; preserve those assertions during subsequent extraction. Existing release tests and the gate cover release callers; no caller edits or 00008 implementation are needed.
  - Acceptance criteria: REQ-004 criteria 1, 2; REQ-005 criteria 1, 2, 3 (CLI and completed baseline corpus portions).
  - Verify: `python3 -B -m unittest discover -s scripts -p test_validate_characterization.py -k CliCharacterization` and the full characterization module pass; verify `scripts/validate.py` still matches the baseline. Record the baseline commit, interpreter, command and full preservation test count in this task's Outcome, then run the shared pre-commit checks and commit `test: characterize validator CLI behavior`.
  - Outcome: Added 9 CliCharacterization tests; Python 3.10.22 unittest discover -s scripts -p test_validate_characterization.py passes all 35 characterization tests on original validate.py from 6c16d03d7f5e878a3033de747866c931edcf12bf, including exact CLI streams and exit codes; all 12 pre-existing validator tests remain unchanged, Ruff and eight CI checks pass; baseline logs preserved at docs/dev/tmp/review-tools/t003-logs.

- [ ] T-004 Split manifest validation into four ordered checks
  - Requirements: REQ-001, REQ-002, REQ-004, REQ-005
  - Depends on: T-003
  - Location: `scripts/validate.py` (validate_manifest and its four new private helpers only).
  - Reuse: Existing `require`, `load_object`, `is_string`, schema/name/version constants and predicates unchanged; the passing T-001 through T-003 preservation corpus.
  - Premise: `validate_manifest` is 96 physical lines and its source matches commit `6c16d03d7f5e878a3033de747866c931edcf12bf`; the full characterization corpus passes before extraction.
  - Contract: The manifest return value is the original object returned by `load_object`, not a filtered copy.
  - Contract: Manifest flow: construct `plugin / "plugin.json"`; check `is_file`; check resolved containment; load JSON once; call identity, metadata, author (with `manifest.get("author")`), and optional checks in that order; return the loaded dictionary.
  - Contract: Both validators and all extracted helpers remain at most 50 physical lines.
  - Details: Preserve `validate_manifest(plugin: Path) -> dict[str, object]`. Extract `_validate_manifest_identity(path: Path, manifest: dict[str, object], plugin_name: str) -> None`, `_validate_manifest_metadata(path: Path, manifest: dict[str, object]) -> None`, `_validate_manifest_author(path: Path, author: object) -> None`, and `_validate_manifest_optional(path: Path, manifest: dict[str, object]) -> None` with the exact responsibilities and check sequence in the approved design table. Keep each expression, short-circuit, cast, diagnostic literal, and iteration order unchanged. No other existing function, constant, caller, test, or package file changes. The still-original MCP function reaches its line limit in T-005.
  - Acceptance criteria: REQ-001 criteria 1, 2 (manifest portion); REQ-002 criteria 1, 2, 3; REQ-004 criteria 2, 3; REQ-005 criteria 1, 2.
  - Verify: Run all unchanged characterization tests and the existing validator/release tests through the shared gate. Measure the manifest wrapper and four helpers with AST `end_lineno - lineno + 1 <= 50`. Inspect the diff for identical predicate/message sequence, manifest return, and unchanged caller APIs; confirm existing tests remain unchanged. Run repository helper status and commit `refactor: split manifest validation checks`.

- [ ] T-005 Split MCP validation into five ordered checks
  - Requirements: REQ-001, REQ-003, REQ-004, REQ-005
  - Depends on: T-004
  - Location: `scripts/validate.py` (validate_mcp and its five new private helpers only).
  - Reuse: Existing `require`, `load_object`, `is_string`, `contained_suffix`, `validate_url`, and MCP schema constant unchanged; the same preservation tests established before either split.
  - Premise: `validate_mcp` is 130 physical lines and its source still matches commit `6c16d03d7f5e878a3033de747866c931edcf12bf`; only manifest validation has been split so far.
  - Contract: MCP flow: construct `plugin / "mcp.json"`; return on `not path.exists()`; check regular file and resolved containment; load JSON once; check exact root keys, schema, and servers object; iterate `servers.items()` without sorting; call `_validate_mcp_server(path, name, server)` for each entry.
  - Contract: No helper catches exceptions or accumulates findings.
  - Contract: Both validators and all extracted helpers remain at most 50 physical lines.
  - Details: Preserve `validate_mcp(plugin: Path) -> None`. Extract `_validate_mcp_server(path: Path, name: str, server: object) -> None`, `_validate_stdio_server(path: Path, server: dict[str, object]) -> None`, `_validate_mcp_env(path: Path, env: object) -> None`, `_validate_mcp_cwd(path: Path, cwd: object) -> None`, and `_validate_remote_server(path: Path, server: dict[str, object]) -> None` with the approved responsibility table. Construct the server diagnostic path before name/object checks; retain transport expressions, command/args/env/cwd order, remote fields/URL/headers order, and original key-presence guards. Preserve runtime exceptions, diagnostic text, and containment predicates. Do not revise T-004's manifest split, tests, other helpers, callers, or package files.
  - Acceptance criteria: REQ-001 criteria 1, 2 (MCP portion); REQ-003 criteria 1, 2, 3; REQ-004 criteria 1, 2, 3; REQ-005 criteria 1, 2.
  - Verify: Run all unchanged characterization tests and existing validator/release tests through the shared gate. Measure the MCP wrapper and five helpers with AST `end_lineno - lineno + 1 <= 50`. Inspect the diff for preserved ordering, presence checks, malformed-value exceptions and None returns; confirm all existing tests remain unchanged. Run repository helper status and commit `refactor: split MCP validation checks`.

- [ ] T-006 Enforce the line limit and verify the completed split
  - Requirements: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
  - Depends on: T-005
  - Location: `scripts/test_validate_structure.py` (new structural acceptance test); this spec's task progress and worktree-local verification logs.
  - Reuse: Standard-library `ast` and `unittest`; approved design's nine helper signatures; T-001's worktree gate and original-code evidence from T-001 through T-003.
  - Contract: The structural module parses `validate.py` with `ast` and verifies that both public functions and every helper named above exist and have `end_lineno - lineno + 1 <= 50`; it also checks any additional top-level function introduced relative to the baseline's function-name set.
  - Contract: No global 50-line rule is imposed on unrelated existing functions.
  - Details: Add the structural check after both splits exist; keep the baseline function-name set as test data so execution does not depend on Git history being available. Run the entire gate on Python 3.10, inspect helper cohesion and the final diff, verify original tests and unrelated functions/constants/callers remain unchanged, and record compatibility and verification evidence in the one-line task Outcome. Remove only task-created obsolete scratch files or executed plans; keep active gate support for fresh review and leave other worktrees/specs untouched. Any defect requiring production edits returns to its owning task and verification; it does not expand this task's file scope or authorize an approved-artifact edit.
  - Acceptance criteria: REQ-001 criteria 1, 2; REQ-002 criteria 1, 2, 3; REQ-003 criteria 1, 2, 3; REQ-004 criteria 1, 2, 3; REQ-005 criteria 1, 2, 3, 4 (final verification and preservation evidence).
  - Verify: `python3 -B -m unittest discover -s scripts -p test_validate_structure.py` and `sh docs/dev/tmp/review-tools/gate.sh` pass on Python 3.10. Compare all pre-existing tests and unrelated source definitions with baseline commit `6c16d03d7f5e878a3033de747866c931edcf12bf`; check `git diff --check`; confirm repository helper status shows no new blocking issue caused by this work. Record the AST lengths, gate result and baseline evidence, then commit `test: enforce validator function length limit`.

## Completion criteria

- [ ] Every task above is checked after its verification, with a one-line Outcome under that task and original-code characterization evidence preserved.
- [ ] All approved requirements are verified, every changed validation function is at most 50 physical lines, and existing tests and unrelated code remain unchanged.
- [ ] The worktree-local Python 3.10 gate passes, the branch is pushed, a PR to master is open, and CI is green on the final PR head.
- [ ] A separate fresh session completes autopilot's review-work-completion workflow and records its result before these completion criteria are checked.

## Unresolved questions

None. After all six task commits, push this branch, open the PR, await its CI, and hand off the fresh-session review. Leave every completion criterion unchecked in this work session. No rebase, force push, stash, master change, other-worktree change, or review execution in this session is authorized.
