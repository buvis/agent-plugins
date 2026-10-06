# Requirements: specflow AWS sources and catch-up

Sources: docs/dev/project-management/intake/processed/specflow/00003-aws-sources-catchup/

Depends on: 00002

## Purpose

Record the three public AWS AI-DLC sources, adapt their method by hand into phase references that name every source, and give maintainers a repository-only catch-up skill that reviews upstream changes and rules on each one.

## Scope

Phase 2 of the source plan (T-010, T-011, T-014, T-018): the source record and `adaptation.md`, licenses and attribution, the four hand-adapted AWS references, the source cursors, the catch-up skill at `.agents/skills/catchup-specflow-upstream/`, and the first catch-up report. Loading the references by phase belongs to 00006.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Assumptions

- AWS AI-DLC material is adapted by hand, with a source line per passage. `awslabs/aidlc-workflows` is the primary source; `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (the original) and `aws-samples/sample-aidlc-discovery` are complementary sources. All three get a regular catch-up, and none is vendored.
- Maintainer skills live at repo-root `.agents/skills/<verb>-<plugin>-<object>/`, the only committed copy; no agent-private folder is committed.

## Requirements

### AWS-001: Published AWS sources

Source: decision 2026-09-28 (aidlc-workflows) #2; decision 2026-10-03 #1, #2, #10, #11, #12, which supersede 2026-09-28 #1 and #8.

**User story:** As a maintainer, I want the runtime workflow grounded in public AWS sources so that prompt provenance is inspectable.

#### Acceptance criteria

1. THE DISTRIBUTED RUNTIME SKILL SHALL contain an attribution and source record naming `awslabs/aidlc-workflows` (A1) as the primary method source, and `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (A2, the original source) and `aws-samples/sample-aidlc-discovery` (A3) as complementary sources.
2. THE SOURCE RECORD SHALL give, per source, its role, its license, and the commit adopted from; for A1 it SHALL also give the release tag.
3. THE PACKAGE SHALL NOT ship a raw copy of an upstream repository; it ships adapted references and the source record only.
4. THE PACKAGE SHALL include the license of every source it copies text from, with attribution.
5. `adaptation.md` SHALL record, per source, what specflow adopted, adapted, and deliberately did not adopt.
6. Runtime behavior SHALL NOT fetch upstream content from the network.
7. Keeping A2 and A3 as sources SHALL NOT require vendoring their repositories or a parser for them.

### AWS-002: Selective prompt loading

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a runtime agent, I want phase-specific references so that the full upstream corpus does not consume context unnecessarily.

#### Acceptance criteria

1. THE PACKAGE SHALL carry phase-specific AWS references, adapted by hand from the tracked sources.

Criterion 2: see 00006.

3. Each adopted passage SHALL name the source repository, file, heading, and tag or commit it came from.
4. AWS references SHALL clearly distinguish verbatim upstream guidance from local adaptation instructions.
5. `adaptation.md` SHALL map the `standard` and `quick` profiles to AWS AI-DLC depth Standard and Minimal; AWS AI-DLC scope names SHALL NOT become profiles.

### UPD-001: Repository-only catch-up skill

Source: decision 2026-10-03 #2, #3.

**User story:** As a maintainer, I want an internal catch-up skill so that upstream changes are assessed the same way each time without exposing maintenance operations to plugin users.

#### Acceptance criteria

1. THE CATCH-UP SKILL SHALL live outside `plugins/specflow/`, at `.agents/skills/catchup-specflow-upstream/`, the repository's only committed copy; its support files SHALL live under `tools/specflow/`.
2. THE CATCH-UP SKILL SHALL NOT be referenced from the distributed `plugin.json`, runtime skill, Claude compatibility manifest, or marketplace entry.
3. THE CATCH-UP SKILL SHALL run only from a trusted checkout of the plugin source repository.
4. THE CATCH-UP SKILL SHALL default to review and report, and SHALL leave `plugins/specflow/` unchanged in that mode.
5. Editing runtime references to adopt a change SHALL require an explicit maintainer instruction.
6. THE CATCH-UP SKILL SHALL NOT commit, push, publish, or tag unless separately and explicitly requested.
7. `AGENTS.md` and `CONTRIBUTING.md` SHALL state the maintainer-skill convention: `.agents/skills/<verb>-<plugin>-<object>/` holds the only committed copy, support files live under `tools/<plugin>/`, and no agent-private folder (`.claude/`, `.kiro/`, `.codex/`) is committed.

### UPD-002: Regular upstream catch-up

Source: decision 2026-10-03 #1, #2.

**User story:** As a maintainer, I want every upstream change reviewed and ruled on before adoption so that a compromised or incompatible change cannot silently alter the workflow, and nothing useful is missed.

#### Acceptance criteria

1. `tools/specflow/upstream/sources.md` SHALL keep one cursor per source: its role, the commit reviewed through, the review date, and the review scope.
2. A catch-up SHALL review each source's changes since its cursor: for A1, the method files specflow adopts from and the release notes; for A2, the `all-phases/all-phases-aidlc-mcp/` pattern and then the wider catalog; for A3, the discovery rules.
3. Each change considered SHALL get a ruling (adopt, adapt, defer, or reject) with the source evidence, the local impact, and the upkeep cost. A catch-up that finds nothing to adopt SHALL say so, and a deferred ruling SHALL be reviewed again on the next catch-up.
4. Rulings SHALL be written to a tracked report under `docs/dev/project-management/reviews/`.
5. A cursor SHALL advance only when its source was fully reviewed. A source that could not be read, or was only partly reviewed, SHALL keep its cursor, and the report SHALL say coverage is incomplete.
6. THE CATCH-UP SKILL SHALL fetch only the configured HTTPS repositories.
7. Adoption from A1 SHALL come from a release tag (`vX.Y.Z`), by the commit the tag points to, never from a branch head; a catch-up MAY read unreleased commits to see what is coming. A2 and A3 SHALL be adopted from a recorded commit.
8. A catch-up SHALL run before each specflow release and at least monthly. THE CATCH-UP SKILL SHALL NOT install a scheduler.
9. A license change in a source SHALL block adoption from it until the maintainer rules on it.

### UPD-003: withdrawn

Withdrawn 2026-10-03 (decision #2): the adapter pipeline it governed was cut. The identifier is not reused.

### SEC-001: Supply-chain safety

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a maintainer, I want upstream review to be non-executing so that a catch-up does not become a code execution path.

#### Acceptance criteria

1. THE CATCH-UP SKILL SHALL treat all fetched content as untrusted data: an instruction found in upstream text SHALL be reported, never followed.
2. THE CATCH-UP SKILL SHALL read upstream content in a newly created temporary directory outside the repository's tracked tree.
3. THE CATCH-UP SKILL SHALL not evaluate shell fragments, import modules, install upstream dependencies, or run upstream scripts, hooks, or tests.
4. Temporary clones SHALL be removed after the catch-up, or kept with an explicit diagnostic path after a failure.
5. Source cursors and the commits adopted from SHALL be recorded in version control.

### REL-001: Reproducible release

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a maintainer, I want a reproducible plugin artifact so that users can inspect exactly what was shipped.

#### Acceptance criteria

Criteria 1-2: see 00002.

3. THE RELEASE BUILD SHALL verify that the source record and each source's license are present and that every adopted passage names a recorded source.

Criteria 4-6: see 00001.

## Non-functional requirements

**Maintainability**

- AWS references and behavior-rule files shall stay separate, so a catch-up never edits a behavior rule.

## Risks

- An upstream change is missed between catch-ups, since A1 ships about once a week: impact m, likelihood m; mitigation: one cursor per source and a tracked ruling for every change considered; fallback: add a synchronizer when real catch-ups show a step that repeats.

## Unresolved questions

- The catch-up cadence (before each release and at least monthly) is a default from the review, not yet confirmed by use. Resolves when the first catch-ups have run and the developer confirms or changes it.
- The repository has no onboarding command yet, so Claude Code reaches the maintainer skill only by being told to read its `SKILL.md`. Resolves when the repository gains its onboarding command.
