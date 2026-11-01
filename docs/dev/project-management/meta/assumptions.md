# AP00013 implementation assumptions

## 1: Characterize pinned helper semantics and ownership exclusions

- The "185 selected" controller-owned rows are the six exact-name test files test_{review_stage,rework_groups,custody,catchup_probe,verification,cap_check}.py, inferred from the exact count; the design does not define the selection.
- Helper-to-regression binding is by test-file name pattern; gate_lead has no own test file and maps to test_gate_findings_{shapes,unread_shapes,classification}, overlapping findings_section.
- "Pure" includes read-only Git and filesystem probes with explicit inputs (dirty_tree, log_sink_refusal, reuse_verdict, capture_range).

## 2: Extract finding parsing, lead stripping and deterministic grouping

- Tess: packaged table header is `| Ref | Consensus | Severity | Issue | File | Found By |`; other orders found by column name. Ref-less tables and bullets give `ref == ""`.
- Tess: modules import as top-level `findings`, `gate_lead`, `rework_groups` with `plugins/autopilot/scripts` on sys.path.
- Tess: `file_key("docs/x.md") == "prose"` (pinned folds markdown inside `group()`; packaged `file_key` folds it, grouping result unchanged).
- Tess: unknown severity label reads as `""` (pinned `_split_severity_cell`), not refused; bullet without "Found by:" keeps its last segment as the file.
- Tess: merged group `name_hint` is the shared directory with trailing `/`, or `mixed`; file groups use `file_key`.
- Tess: `group()` rejects non-emoji severity (`high`, `🔵`) per contract, diverging from pinned which accepted them.
- Ivan: critical group `name_hint` stays the citation-free path even for `.md` (private `_citation_free`); untested.
- Ivan: `N/A (reason)` also maps to general (pinned fullmatch regex kept).
- Ivan: invalid finding raises ValueError; table-row regex kept private.

## 3: Implement advisory AP00012 evidence consistency checking

- Tess: module imports as top-level `review_evidence`; mutated non-fixture inputs must match the oracle's defect set after outer outcome mapping.
- Tess: context shape failures report `schema_invalid`; `invalid_expected_context` is for well-formed but semantically wrong contexts.
- Tess: `check_evidence` reads only `.py`/`.pyc`/`.so` files and files under `plugins/autopilot/contracts`; reports survive a JSON round trip.
- Tess: float `schema_version: 1.0` inside AP00012 evidence left untested (oracle/jsonschema accepts it); duplicate-ID cases assert only `duplicate_id` membership.
- Ivan: JSON Schema "integer" follows jsonschema (bool never, integral float yes); policy `schema_version` and rework ints need a real int.
- Ivan: packaged policy is the source of normative values for policy checks; policy/schema checks return `schema_invalid` on KeyError/TypeError/AttributeError/IndexError.
- Pat LOW (not fixed): `policy_bindings_valid` uses `HEX64.search` without the `len==64` guard, so a policy digest with a trailing newline passes.

## 4: Port read-only dirty-tree and safe artifact path primitives

- Tess: `STORE_PREFIXES == {"docs/dev/project-management/", "docs/dev/tmp/"}`; `_store_roots` = show-prefix + each, in order.
- Tess: a committed `docs/dev/tmp/` change makes `_ancestor_and_clean` False (committed reuse tolerates management-store changes only).
- Tess: tests isolate git config (GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, XDG_CONFIG_HOME) after Devon found the user's global excludes hid docs/dev/tmp.
- Tess: hidden-flag paths are dirt even unmodified and are not excused by `extra_excluded` (pinned).
- Tess: `_open_log_sink(log_path, root)` returns an unbuffered binary file; unlinks then O_EXCL-creates the leaf.
- Ivan: `_log_rel_and_tracked` uses `git ls-files -z -- :(literal)rel` with exact match (pinned `--error-unmatch` matched a directory with tracked files); git failure returns None (fail closed).
- Ivan: `refuse` catches the Python 3.12 symlink-loop RuntimeError and returns "is a symlink"; `_untracked_log_exclusion` still raises on a loop.
- Pat LOWs (not fixed): `_ancestor_and_clean` lets `_GitProbeFailed` escape (callers must catch OSError); duplicated try/except in `_dirty_outside_store`/`_dirty_check`; repeated show-prefix in `_ancestor_and_clean`; `_log_rel_and_tracked` does not catch RuntimeError.
