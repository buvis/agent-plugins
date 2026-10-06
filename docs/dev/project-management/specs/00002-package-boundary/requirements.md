# Requirements: specflow package boundary

Sources: docs/dev/project-management/intake/processed/specflow/00002-package-boundary/

## Purpose

Give specflow one distributable folder, `plugins/specflow/`, with its portable manifest and its Claude Code compatibility manifest. Keep maintainer material out of that folder by release verification, and show with a throwaway probe that each supported host can load a package of this shape before feature work starts.

## Scope

Phase 1 of the source plan (T-001 to T-006): the repository skeleton, the two manifests, `tools/specflow/verify_release.py` with its forbidden-content checks, and the host loading probe. The runtime skill arrives in 00006, and the host tests on the real package in 00008.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Assumptions

- The plugin is named `specflow` and lives at `plugins/specflow/` in the buvis agent-plugins monorepo.
- Agent Plugins v1 is the portable package baseline.
- The first release is skills-based and does not require an MCP server.
- No supported host of release 0.1 needs `plugin.json` at a repository root, so PKG-002 criterion 6 is dormant and has no task in this release. The host loading probe (T-006) reopens it if it finds such a host (decision 2026-10-04 #10).

## Requirements

### PKG-001: Portable package

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want one portable plugin package so that I do not maintain separate workflow implementations for every agent.

#### Acceptance criteria

1. WHEN the plugin is packaged, THE PACKAGE SHALL contain a root `plugin.json` conforming to Agent Plugins v1.

Criterion 2: see 00006.

3. THE PACKAGE SHALL NOT require an MCP server for its core workflow.
4. THE PACKAGE MAY add `mcp.json` in a future compatible release without changing the canonical artifact contract.
5. THE PACKAGE SHALL keep host-specific metadata subordinate to the portable root manifest or in a compatibility manifest.

### PKG-002: Hard distribution boundary

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a maintainer, I want an unambiguous package boundary so that internal maintenance capabilities cannot leak into releases.

#### Acceptance criteria

1. THE REPOSITORY SHALL place the complete distributable package under the single `plugins/specflow/` directory.
2. THE RELEASE PROCESS SHALL treat the tagged `plugins/specflow/` subdirectory as the release; nothing outside it is installable.
3. THE REPOSITORY SHALL place the catch-up skill, the source cursors, catch-up reports, tests, and release tooling outside `plugins/specflow/`.
4. WHEN the released `plugins/specflow/` is inspected, IT SHALL NOT contain the catch-up skill or its name, source cursors, catch-up reports, maintainer prompts, upstream clones, the behavior rule inventory, scenario evals, parity reports, or repository-only host launchers.
5. CI SHALL fail if a forbidden maintainer-only path or marker appears in `plugins/specflow/`.
6. WHEN an installation surface requires `plugin.json` at a Git repository root, THE RELEASE PROCESS SHALL publish the contents of `plugins/specflow/` through a generated distribution branch or dedicated distribution repository that contains no maintainer-only files.

### PKG-003: Host compatibility

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want the same workflow available in my supported tools so that switching tools changes the interface, not the process.

#### Acceptance criteria

1. WHEN installed in Kiro IDE, THE PLUGIN SHALL load as an Agent Plugins v1 Power.
2. WHEN installed in Codex, THE PLUGIN SHALL load from its root Agent Plugins v1 manifest.
3. WHEN installed in Claude Code, THE PACKAGE SHALL expose the same runtime skill through a thin `.claude-plugin/plugin.json` compatibility manifest.

Criterion 4: see 00008.

5. Host adapters SHALL NOT duplicate the normative workflow instructions.
6. A host-specific adapter SHALL NOT introduce a host-specific artifact location.
7. Before feature work starts, a loading probe SHALL show for each supported host that it loads one skill from the package, reads one bundled reference, and writes a fixture artifact, and that another supported host resumes that artifact.

### REL-001: Reproducible release

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a maintainer, I want a reproducible plugin artifact so that users can inspect exactly what was shipped.

#### Acceptance criteria

1. THE RELEASE BUILD SHALL package only `plugins/specflow/`.
2. THE RELEASE BUILD SHALL validate root manifest schemas and compatibility manifests.

Criterion 3: see 00003.

Criteria 4-6: see 00001.

## Non-functional requirements

**Portability**

- Host adapters shall remain thin and replaceable.

## Risks

- A supported host fails the loading probe: impact h, likelihood m; mitigation: the probe (T-006) finishes before phase 3 work starts; fallback: the host is fixed or leaves the supported list first.
