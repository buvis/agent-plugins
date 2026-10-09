# Requirements: specflow host integration

Sources: docs/dev/project-management/intake/processed/specflow/00008-host-integration/

Depends on: 00002, 00006

## Purpose

Prove on the real package what the probe showed on a throwaway one: Kiro IDE, Codex, and Claude Code each load specflow, run the workflow, and hand a spec to another host. Document how to install it on each host and what is untested.

## Scope

Phase 6 of the source plan (T-040, T-042, T-043, T-045, T-046): the three host loading tests, the host compatibility documentation, and the monorepo Claude Code marketplace entry. These tasks prove criteria that 00002 owns; this spec owns only the supported-host statement.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Requirements

### PKG-003: Host compatibility

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a developer, I want the same workflow available in my supported tools so that switching tools changes the interface, not the process.

#### Acceptance criteria

Criteria 1-3: see 00002.

4. Kiro IDE, Codex, and Claude Code SHALL be the supported hosts of the first release. Kiro CLI and Kiro Crew are expected to load the same package but are untested; THE DOCUMENTATION SHALL say so and SHALL NOT list them as supported.

Criteria 5-7: see 00002.

## Risks

- An install path the source design marks "to be verified" does not work on a host: impact m, likelihood m; mitigation: T-045 resolves every such line into a confirmed path; fallback: the limit is documented for that host.
