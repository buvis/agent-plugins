# Design: Split long validator functions

## Overview

Extract contiguous checks from `validate_manifest` and `validate_mcp` into private functions in `scripts/validate.py`. Keep the public entry points, existing predicates, error strings, and evaluation order. Add behavior tests before extraction and a separate source-length check for the completed split. The result makes each validation responsibility reviewable without changing any plugin's validation outcome.

## Context and constraints

- The approved requirements define behavior at `6c16d03d7f5e878a3033de747866c931edcf12bf` as the baseline. A1 counts physical lines from `def` through the final statement; A2 compares identical runtime/filesystem conditions; A3 leaves 00008 independent.
- `scripts/validate.py` contains dependency-free, typed Python functions. `require`, `load_object`, `is_string`, `contained_suffix`, and `validate_url` already supply the needed primitives. No new framework or runtime dependency is needed.
- `main` calls manifest, containment, skill, and MCP checks in that order. `tools/specflow/verify_release.py:check_manifests` imports the validators, consumes the manifest dictionary, and collects `ValidationError` failures. The planned 00008 marketplace generator consumes the same public manifest API. All these callers stay unchanged.
- Root `AGENTS.md`, its `CLAUDE.md` pointer, global instructions, and the opening request govern the affected files. No nested instruction changes apply. Python 3.10 is the CI target; all local Python runs disable bytecode. Existing tests and unrelated production functions stay byte-identical.
- Bob, the repository's solo maintainer, owns approval and operation. CLI diagnostics and CI failures remain the operational signal; this refactor introduces no service, deployment topology, persistent state, schema version, or API version change.

## Architecture

**ADR-001: Extract private checks in place.** Context: two overlong functions implement a stable, ordered contract shared by multiple callers. Decision: preserve the module and public wrappers; extract contiguous responsibilities into private helpers. Consequences: a few extra calls and names, but no import migration, new state, or changed error collection. Alternatives rejected: a separate validation package adds an unnecessary import boundary; a schema engine changes validation semantics and violates the dependency constraint. Both validators and all extracted helpers remain at most 50 physical lines.

Dependencies remain acyclic: callers invoke public validators; validators invoke private checks; checks use the existing primitives. Helpers receive the original objects and paths, do not mutate them, and return `None`. There is no dispatch registry, result accumulator, generic validation framework, or module-level mutable state.

## Module placement

| Path | New or edit | Holds |
|---|---|---|
| `scripts/validate.py` | edit | Two shorter public validators and their private checks; no other function or constant changes |
| `scripts/test_validate_characterization.py` | new | Baseline-compatible public behavior and CLI tests |
| `scripts/test_validate_structure.py` | new | The 50-line structural acceptance check for the completed refactor |

The task plan will assign task IDs after design approval. Canonical spec artifacts and the intake log track workflow progress outside this implementation placement. `docs/dev/tmp/review-tools/gate.sh` and its logs are worktree-local, untracked verification support prepared before implementation commits. No package asset, existing test, CI configuration, release caller, or 00008 file needs editing. The planned commits are `test` and `refactor`, not behavior-changing `feat` or `fix` commits.

## Components and interfaces

### `scripts/validate.py`: validation component (REQ-001 through REQ-004)

Public contracts remain exactly `validate_manifest(plugin: Path) -> dict[str, object]` and `validate_mcp(plugin: Path) -> None`. `ValidationError`, `ROOT`, schema constants, regexes, `main`, and all other existing public helpers retain their current interfaces and behavior. The manifest return value is the original object returned by `load_object`, not a filtered copy.

Private helper signatures and responsibilities:

| Signature | Responsibility and exact check sequence |
|---|---|
| `_validate_manifest_identity(path: Path, manifest: dict[str, object], plugin_name: str) -> None` | Sorted unknown fields; schema; non-empty string name; length/regex; directory-name equality |
| `_validate_manifest_metadata(path: Path, manifest: dict[str, object]) -> None` | Present string fields in order description/homepage/repository/license; required version; version regex; required description; required license |
| `_validate_manifest_author(path: Path, author: object) -> None` | Object type; allowed fields; required name; string values in author insertion order |
| `_validate_manifest_optional(path: Path, manifest: dict[str, object]) -> None` | If present, keywords array then string elements; if present, extensions object then object values |
| `_validate_mcp_server(path: Path, name: str, server: object) -> None` | Construct server path; name check; server object check; transport dispatch |
| `_validate_stdio_server(path: Path, server: dict[str, object]) -> None` | Allowed fields; command; optional args; optional env helper; optional cwd helper |
| `_validate_mcp_env(path: Path, env: object) -> None` | Object type; reserved variables; string keys and values |
| `_validate_mcp_cwd(path: Path, cwd: object) -> None` | String type; allowed root spelling and suffix selection; suffix containment |
| `_validate_remote_server(path: Path, server: dict[str, object]) -> None` | Allowed fields; existing `validate_url`; optional headers object and string entries |

The type annotations describe existing JSON shapes, not extra runtime checks. Each moved expression, short-circuit, cast, literal diagnostic, and branch stays equivalent to the baseline. Stdio and remote helpers are called only after server object validation. Optional helpers run only under the original key-presence guards, never via truthiness or a default that merges absent and null values. No helper catches exceptions or accumulates findings.

### New test modules (REQ-001, REQ-005)

Both use standard-library `unittest` and are discovered by `python3 -B -m unittest discover -s scripts`. Characterization tests call public entry points, never the extracted helpers. The structural module parses `validate.py` with `ast` and verifies that both public functions and every helper named above exist and have `end_lineno - lineno + 1 <= 50`; it also checks any additional top-level function introduced relative to the baseline's function-name set. No global 50-line rule is imposed on unrelated existing functions.

## Data model

No new stored data or normalized representation. `load_object` returns `dict[str, object]` from JSON, and JSON objects retain insertion order. Nested values are checked before casts, using the original predicates. The baseline code remains authoritative for exact schema constants, regex spelling, and diagnostic literals.

Manifest fields remain `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, and `extensions`. Required values and optional-field semantics remain unchanged: author allows name/email/url, keywords contains strings, and extension values are objects. String validation does not trim whitespace or reinterpret an empty optional string.

MCP root fields remain exactly `$schema` and `mcpServers`. Each named server uses `stdio` with type/command/args/env/cwd, or `streamable-http` or `sse` with type/url/headers. The runtime check for a non-empty string name remains even though JSON object keys are strings. Transport membership tests retain their current behavior for malformed scalar and container values, including propagated exceptions.

## Data and control flow

Manifest flow: construct `plugin / "plugin.json"`; check `is_file`; check resolved containment; load JSON once; call identity, metadata, author (with `manifest.get("author")`), and optional checks in that order; return the loaded dictionary. These checks preserve the current interleaving: optional metadata string types precede version validation, and author validation precedes keywords and extensions.

MCP flow: construct `plugin / "mcp.json"`; return on `not path.exists()`; check regular file and resolved containment; load JSON once; check exact root keys, schema, and servers object; iterate `servers.items()` without sorting; call `_validate_mcp_server(path, name, server)` for each entry. That helper constructs `Path(f"{path}#{name}")` before checking name and server, then selects stdio, remote, or the original unknown-transport exception.

Stdio flow preserves command handling: a non-empty command beginning `./` checks `contained_suffix(command[2:])`; otherwise any slash or backslash is rejected. Args precede env, which precedes cwd. Cwd accepts `./`, `${PLUGIN_ROOT}`, `${PLUGIN_DATA}`, or a slash suffix under either variable, then applies the unchanged suffix check. Remote flow checks fields, URL, then headers. A failure immediately exits the current public call; `main` alone retains its existing per-plugin error collection and continuation.

## Error handling

| Condition | Required behavior |
|---|---|
| Missing manifest or non-file manifest | Original `ValidationError` with `missing required manifest` |
| Missing MCP file, including cases for which baseline `exists()` is false | Return `None`, preserving the original early return |
| Present non-file MCP path or escaping resolved file | Original file/containment diagnostic at its original position |
| JSON load failure or non-object root | Unchanged `load_object` behavior, including exception cause |
| Invalid fields or several simultaneous failures | Same first exception class and full message; preserve sorted manifest unknown-field names and insertion order elsewhere |
| Unknown transport | Original `unknown MCP transport {transport!r}` error when that branch is reached |
| Runtime/library exceptions not currently caught | Propagate unchanged; no new broad catches or conversion to `ValidationError` |
| CLI validation failures | Existing `error: {error}` lines on stderr in order, no success summary, exit 1 |
| CLI success | Existing package/skill-count summary on stdout, empty stderr, exit 0 |

Traceback frame locations necessarily move with extraction; exception type, text, cause handling, and CLI behavior remain preserved. No promise of atomic filesystem snapshots is added; race and permission behavior stays delegated to the same existing operations on the same Python version.

## Security and privacy

Plugin files are the input trust boundary. Containment, command and cwd traversal, reserved env variables (`PLUGIN_ROOT`, `PLUGIN_DATA`), URL scheme/loopback/userinfo/fragment rules, and field allowlists remain unchanged. Tests use synthetic values, never credentials or live servers. Validators neither execute a server command nor make a network request. No secrets, authentication mechanism, persistent personal data, or additional dependency is introduced; existing unusual behavior is characterized, not repaired by this refactor.

## Testing strategy

**ADR-002: Separate preservation from structure.** Context: behavior tests must pass before refactoring while the line limit does not. Decision: establish `test_validate_characterization.py` against the original code first; add `test_validate_structure.py` when implementing the split. Consequences: preservation evidence stays independent of helper names, and structural evidence measures the actual changed source. Alternatives rejected: editing existing tests violates scope; one before/after suite that expects short functions on the original code conflates the two obligations. Existing unittest conventions override optional pytest-specific practices; no test dependency or broad coverage project is introduced.

Use fresh temporary plugin copies and synthetic dictionaries serialized to JSON. Table cases may use `subTest`; run them through unittest so failures are not hidden by the known pytest replay issue. Patch only I/O boundaries for otherwise nondeterministic failures (for example `Path.read_text` raising a fixed `OSError`); do not mock validators or their private helpers. Compare exception classes and complete messages, with paths constructed from the fixture. Dynamic JSON-parser and OS wording is established on the same interpreter using deterministic inputs or injected exceptions, not frozen from another Python version.

| Test group | Required cases and evidence |
|---|---|
| Manifest accepted values | Minimal and all-optional manifests; original dictionary equality including nested extensions; empty optional strings/collections, whitespace-only required strings where currently accepted; 64-character name and supported version forms; input bytes unchanged |
| Manifest rejection and order | Missing/directory/escaping-symlink files; invalid JSON/non-object root; each moved check's invalid type or value; 65-character name; sorted multiple unknown fields; failures spanning schema/name/metadata/version/author/keywords/extensions, including optional metadata type before version and author insertion order |
| MCP accepted values | Absent file, empty servers, stdio bare and contained relative commands, optional empty args/env/headers, each cwd root spelling, both remote transports, HTTPS and allowed HTTP loopback forms; `None` return and unchanged input bytes |
| MCP rejection and order | Non-file/escaping-symlink path, broken link baseline early return, invalid JSON/root/schema/servers/name/server/transport; command path traversal or forbidden separator; args/env/cwd/header type/value errors; reserved env before bad values; URL/userinfo/fragment/TLS errors; field-to-field and server-to-server competing failures |
| Propagated failures | Invalid UTF-8; malformed URL that raises from parsing; unhashable transport such as a JSON array; deterministic read failure; preserve exception class/text and cause where the baseline supplies one |
| CLI integration | Public `main` with captured streams and argv/ROOT patched at the boundary: default versus explicit paths, exact success output, multiple plugin errors in order, manifest failure suppressing later checks, maintainer-skill handling. Subprocess smoke checks for actual success/failure exit and streams use `sys.executable -B` and temporary plugin paths |
| Release integration | Existing release-test suite plus release verifier exercise `check_manifests` without modifying the caller; manifest return tests protect the planned 00008 consumer without building it |
| Structure | AST physical-line assertion for the two validators and all newly introduced extraction helpers; manual review confirms each helper's responsibility and unaltered evaluation order |

Record the baseline commit, Python version, command, and passing test count in the characterization task's Outcome before changing `validate.py`. Rerun the unchanged characterization tests after each extraction. Check the final diff against the baseline to confirm all pre-existing tests and unrelated functions remain unchanged. Run the full worktree-local gate before every commit, plus helper status on this repository's own specs, without reconciling other specs.

The gate runs all eight commands from `.github/workflows/validate.yml`: validator tests; package validation; release, contract, rules, and review test suites; rule inventory with the checkout's area list; release boundary verification. It uses this worktree as its root, bytecode disabled, and logs each result separately. Verify on Python 3.10 as CI does; record the interpreter version. No full-gate success is claimed from the requirements baseline's 12-test run. No package edits are planned, so the release verifier's clean-package requirement is preserved.

## Rollout and migration

After task approval opens implementation, establish and record characterization success on original code, extract manifest checks, then extract MCP checks, with passing tests between changes. Add the structural check once both splits exist. Each intermediate refactor retains valid public entry points and needs no migration or feature flag. Delivery uses the requested branch and PR; fresh-session completion review precedes checking final completion criteria. Because CI triggers on pull requests or pushes to master, local gates precede branch push/PR creation, and remote CI is then awaited on that PR.

Backout restores `scripts/validate.py` from the approved baseline and reruns the original and characterization suites. The structural test must be reverted with the split if the entire change is backed out, since the old code intentionally exceeds 50 lines. No data or caller migration is needed, and no master, other worktree, stash, rebase, or force push is part of this procedure.

## Risks and edge cases

- Moving checks changes diagnostic precedence: impact h, likelihood m; mitigation: competing-failure cases and exact ordered extraction; fallback: keep original blocks until equivalence is demonstrated.
- Extracting server validation adds an early guard or catches an existing runtime exception: impact h, likelihood m; mitigation: preserve dispatch expressions and characterize malformed transport/URL/encoding cases; fallback: restore the original expressions without adding normalization.
- Python or filesystem differences invalidate comparisons: impact m, likelihood m; mitigation: baseline and refactor tests on the same interpreter and deterministic I/O failures, with Python 3.10 verification; fallback: treat mismatches as unresolved evidence, not permission to alter behavior.
- Readability regresses into arbitrary 50-line slices: impact m, likelihood l; mitigation: the responsibility table and source review, with the stdio block split only at env/cwd boundaries; fallback: revise the private boundaries before task approval or request design reapproval afterwards.

Likely next changes: 00008 can import the unchanged manifest API; a new validation rule must specify its order and new diagnostic in separate work; a future helper exceeding 50 lines can be decomposed privately while preserving the public contract. These are extension limits, not added features of this spec.

## Requirement traceability

| Design element | Criteria |
|---|---|
| In-place private extraction, responsibility table, AST check and manual cohesion review | REQ-001.1, REQ-001.2 |
| Manifest interface, ordered flow, accepted/rejected/precedence tests | REQ-002.1, REQ-002.2, REQ-002.3 |
| MCP interface, ordered flow, transport and failure tests | REQ-003.1, REQ-003.2, REQ-003.3 |
| Unchanged main and release callers, CLI/return-value/release integration tests | REQ-004.1, REQ-004.2 |
| Non-mutating helpers and input-byte assertions | REQ-004.3 |
| Additive test files, unchanged existing tests and baseline diff check | REQ-005.1 |
| Characterization-first delivery, recorded original-code run and reruns | REQ-005.2 |
| Accepted, rejected, boundary, malformed, return, diagnostic, precedence and CLI cases | REQ-005.3 |
| Worktree-local eight-command gate and Python 3.10 verification | REQ-005.4 |

## Alternatives considered

1. **Extract contiguous checks in the existing module (selected; smallest qualifying diff).** Preserves imports and keeps sequencing visible; the cost is private helper names. Internal helper boundaries remain reversible.
2. **Move validation into a new module or class.** Could group responsibilities, but adds imports or object state without a requirement and increases compatibility risk. Keeping the two functions unchanged is an even smaller diff but fails the approved line-limit requirement.
3. **Use a schema-validation library or generic rule engine.** Could replace repetitive shape checks, but brings new dependencies or machinery and cannot preserve this validator's custom ordering, predicates, and literal diagnostics by simple substitution. Rejected by scope; no external product search is needed to establish that conflict. Existing standard-library tools already cover JSON parsing and test execution.

## Reuse inventory

- Searches: `rg` for check/validate with manifest, mcp, author, stdio, and remote, plus known-present `require`, `load_object`, `is_string`, `contained_suffix`, and `validate_url`, across scripts/tools; caller search across the repository. No existing extracted author, env, cwd, or transport helpers were found.
- `scripts/validate.py`: reuse the five primitives unchanged; preserve `MANIFEST_FIELDS`, `PLUGIN_SCHEMA`, `MCP_SCHEMA`, `PLUGIN_NAME`, and `SEMVER` without duplicating their policy in a new module.
- `scripts/test_validate.py`: reuse its unittest, temporary template-copy, stream-capture, and boundary-patching patterns without importing its test classes or editing the file.
- `tools/specflow/verify_release.py:check_manifests` and existing release tests: run as integration evidence, not code to refactor.
- `.github/workflows/validate.yml` and the review-completion recipe: source the worktree-local gate and verification precautions; no foreign-checkout script is executed.

## Open decisions

None. Design approval is pending; no implementation is authorized until task approval opens the gate.
