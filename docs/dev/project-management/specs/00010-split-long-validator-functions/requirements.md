# Requirements: Split long validator functions

Sources: docs/dev/project-management/intake/processed/00010-split-long-validator-functions

## Purpose

`validate_manifest` and `validate_mcp` in `scripts/validate.py` exceed the 50-line function limit identified by review R9. Split their responsibilities into smaller checks while preserving behavior, because every plugin's validation and specflow's release checks depend on them.

## Scope

Refactor these two validators and add characterization coverage for their existing behavior. Preserve the public API used by current callers and the marketplace generator planned in spec 00008. Success means smaller cohesive functions, unchanged validation results and diagnostics, and passing existing and added tests.

## Assumptions

- A1: The 50-line limit counts physical lines from the `def` line through the final statement, including intervening comments and blank lines. This reproduces R9's measured lengths of 96 and 130 lines (qa-log.md D1).
- A2: The behavior at base commit `6c16d03d7f5e878a3033de747866c931edcf12bf` is the preservation baseline. Comparisons use the same inputs, filesystem conditions, and Python version (qa-log.md D1, D4).
- A3: This refactor has no implementation prerequisite on 00008; its planned caller uses the existing API. No other spec must be recovered or changed (qa-log.md D3 and supplied scope).

## Requirements

### REQ-001: Bounded, cohesive validation checks

Source: idea.md; qa-log.md supplied scope and D1; originating review R9.

**User story:** As a maintainer, I want short checks with identifiable responsibilities, so that I can review validation rules without following an oversized function.

#### Acceptance criteria

1. WHEN the refactor is complete THE SYSTEM SHALL have `validate_manifest`, `validate_mcp`, and every helper introduced or expanded to perform their extracted checks measure at most 50 lines under A1.
2. WHEN the resulting functions are reviewed THE SYSTEM SHALL expose one identifiable validation responsibility per extracted check, with the public validators retaining an explicit validation sequence.

### REQ-002: Manifest compatibility

Source: qa-log.md supplied scope and D1-D3.

**User story:** As a caller of `validate_manifest`, I want the same result and failures, so that release checks and the planned marketplace generator continue to work.

#### Acceptance criteria

1. WHEN a caller imports and calls `scripts/validate.py`'s `validate_manifest(plugin: Path) -> dict[str, object]` THE SYSTEM SHALL retain that interface and return the complete parsed manifest without filtering, normalization, or added fields for an accepted input.
2. WHEN a manifest is checked under the baseline conditions THE SYSTEM SHALL preserve accepted and rejected inputs across file presence and containment, JSON loading, top-level fields and schema, name, metadata strings, version, required metadata, author, keywords, and extensions.
3. IF a manifest encounters a failure THEN THE SYSTEM SHALL preserve the exception type and diagnostic text, including its path; for multiple invalid fields it SHALL preserve validation order and the first reported failure.

### REQ-003: MCP compatibility

Source: qa-log.md supplied scope and D1-D2.

**User story:** As a plugin author, I want MCP configuration validation to remain unchanged, so that the refactor neither rejects valid packages nor admits invalid ones.

#### Acceptance criteria

1. WHEN a caller imports and calls `scripts/validate.py`'s `validate_mcp(plugin: Path) -> None` THE SYSTEM SHALL retain that interface and return `None` for both an absent MCP file and an accepted configuration.
2. WHEN an MCP configuration is checked under the baseline conditions THE SYSTEM SHALL preserve accepted and rejected inputs across file checks, JSON loading, top-level fields and schema, empty and populated server mappings, server names and objects, transport selection, stdio command/args/env/cwd, and remote URL/headers for both `streamable-http` and `sse`.
3. IF an MCP configuration encounters a failure THEN THE SYSTEM SHALL preserve the exception type and diagnostic text, including its file and server path; for multiple invalid fields or servers it SHALL preserve validation and server iteration order and the first reported failure.

### REQ-004: CLI and caller compatibility

Source: qa-log.md supplied scope and D2-D3.

**User story:** As a repository maintainer, I want existing commands and callers to behave identically, so that internal decomposition does not change CI results.

#### Acceptance criteria

1. WHEN the validator CLI runs with default discovery or explicit plugin paths THE SYSTEM SHALL preserve argument handling, package and skill selection, validation order, success output, error output and ordering, and exit codes for the same inputs.
2. WHEN existing release checks call the two validators THE SYSTEM SHALL preserve manifest data consumed by `check_manifests` and collectable `ValidationError` failures without requiring caller changes.
3. WHEN either validator runs THE SYSTEM SHALL preserve its read-only effect on input files.

### REQ-005: Evidence of behavior preservation

Source: idea.md; qa-log.md supplied scope and D4-D5.

**User story:** As a reviewer, I want tests grounded in the original behavior, so that a passing refactor demonstrates compatibility rather than merely testing its new structure.

#### Acceptance criteria

1. WHEN regression checks run THE SYSTEM SHALL keep every pre-existing test unchanged and passing, including all of `scripts/test_validate.py`.
2. WHEN characterization tests are added THE SYSTEM SHALL establish and record their passing result against the original validators before any refactoring, then pass those same tests after refactoring.
3. WHEN preservation evidence is reviewed THE SYSTEM SHALL cover accepted and rejected cases for both validators, boundary and malformed inputs, public return values, exact diagnostics, competing failures that expose ordering, and CLI output and exit behavior wherever existing tests do not already establish them.
4. WHEN implementation is verified THE SYSTEM SHALL pass this worktree's repository validation and CI checks, including release-check callers, on the supported Python 3.10 baseline.

## Non-functional requirements

- Preserve dependency-free Python 3.10 compatibility; add no dependencies (AGENTS.md, `.github/workflows/validate.yml`, `ruff.toml`, supplied scope).
- Limit production changes to decomposing the two validators; avoid unrelated cleanup, formatting churn, new validation rules, or repairs to existing behavior (supplied scope; R9).
- Preserve existing security checks, including containment, command/cwd traversal checks, reserved environment variables, and remote URL rules; compatibility does not authorize strengthening or weakening them (supplied scope; D1).
- Run Python with `-B` or `PYTHONDONTWRITEBYTECODE=1`; prepare the worktree-local gate from this checkout's CI before implementation commits (supplied execution constraints; D4).

## Risks

- Reordering checks changes the first diagnostic: impact h, likelihood m; mitigation: characterize competing failures before extraction; fallback: retain the original sequence and revise the split.
- Tightening edge-case behavior accidentally changes accepted inputs: impact h, likelihood m; mitigation: compare both passing and failing boundary cases against the original code; fallback: preserve the original predicate and defer any behavior change.
- A regression blocks every plugin's CI or breaks release callers: impact h, likelihood m; mitigation: unchanged existing tests, characterization evidence, and this worktree's full CI gate; fallback: withhold the refactor until compatibility is restored.

## Out of scope

- New validation policies, diagnostic improvements, and bug fixes: this spec preserves behavior.
- Refactoring other validator functions or unrelated files: R9 names only these two functions.
- Implementing the 00008 marketplace generator or changing its host-test workspace: only its existing API dependency is protected here.
- Recovery or modification of other specs, new dependencies, and workflow redesign: excluded by the supplied scope.

## Unresolved questions

None.
