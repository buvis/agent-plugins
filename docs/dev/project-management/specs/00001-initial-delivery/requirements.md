# Requirements: specflow initial delivery

Sources: docs/dev/project-management/intake/processed/specflow/00001-initial-delivery/

Depends on: 00002, 00003, 00005, 00007, 00008, 00009

## Purpose

Create a portable Agent Plugins v1 package that makes AI coding tools follow one spec-driven development workflow and allows a developer to switch tools at any point without losing the authoritative requirements, design, task progress, or approval state.

The workflow shall preserve Kiro's conventional artifact locations while drawing its method from AWS's published AI-DLC material: `awslabs/aidlc-workflows` as the primary source, with `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` and `aws-samples/sample-aidlc-discovery` as complementary sources. The maintainer skill that reviews those sources shall exist only in the plugin source repository and shall not be shipped to plugin users.

The workflow also carries the spec discipline of the buvis personal SDLC skills (intake, elicitation, spike, requirements and design reviews, cross-spec readiness review) as numbered behavior rules, so each skill can retire once specflow matches it rule for rule.

The package shall also ship a conversion skill that adopts an existing PRD or legacy intake item into specflow's artifacts and gates without losing its decisions, implementation evidence, or approval boundaries, so a repository with prior PRDs can move onto the workflow on its first day.

**Goals**

1. Provide one distributable plugin usable by Agent Plugins v1-compatible clients.
2. Use `.kiro/specs/NNNNN-<title>/requirements.md`, `design.md`, and `tasks.md` as the human-readable source of truth.
3. Persist enough machine-readable state to resume safely in another tool or a new session.
4. Preserve explicit human approval gates between requirements, design, tasks, and implementation.
5. Track each public AWS AI-DLC source by an immutable commit, review the sources on a regular cadence, and record a ruling for every upstream change considered.
6. Keep all maintainer-only update machinery outside the distributable plugin.
7. Remain useful without a running service, network connection, or shared conversation history.
8. Replace the personal SDLC skills with measured parity: every ported behavior is a numbered rule with a check, and a skill retires only after specflow passes its rules.
9. Ship a conversion skill that turns an existing PRD or legacy intake item into approved specflow artifacts through the same contracts and gates as a natively created spec.

## Scope

This spec closes release 0.1. It covers phase 8 of the source plan (T-060 to T-067): the maintainer and user documentation, the changelog and versioning policy, verification of the release candidate, final acceptance, publishing `specflow-v0.1.0`, and the handoffs for the autopilot repoint and the skill retirement. It also holds the framing every other spec cites: purpose, goals, actors, terms, and what is out of scope. The capabilities themselves are specified in 00002 to 00009.

**Actors**

- **Developer**: creates, reviews, approves, and implements a feature specification.
- **Runtime agent**: Kiro IDE, Codex, Claude Code, or another compatible agent using the distributed workflow skill.
- **Plugin maintainer**: reviews the AWS sources, adapts the references, and maintains behavior rules, evals, tests, and plugin releases.
- **Upstream sources**: `awslabs/aidlc-workflows` (A1), the primary method source, adopted from release tags; `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (A2), the original source, kept as a complementary patterns source; `aws-samples/sample-aidlc-discovery` (A3), a complementary discovery source.
- **Host**: the AI coding product loading the plugin or its compatibility adapter.
- **External runner**: a tool without a chat session that reads the status output to pick up approved work. It never approves.

**Terms**

- **Artifact**: one of `requirements.md` (or `bugfix.md`), `design.md`, or `tasks.md`.
- **Spec type**: `feature` or `bugfix`, fixed when the spec is created; it selects the artifact templates and validation rules.
- **Spec number**: the five-digit `NNNNN` prefix one intake item and its spec share.
- **Approval**: an explicit developer decision recorded against the exact hash of an artifact.
- **Specs folder**: the repository folder that holds spec directories: `.kiro/specs/` by default, or the folder the configuration names (INT-001.1). A path written `.kiro/specs/...` in this document means the specs folder.
- **Canonical artifact**: a file under `.kiro/specs/NNNNN-<title>/` that all hosts read and write.
- **Workspace root**: the repository folder that holds intake items and review reports; configurable, default `.kiro/specflow/`.
- **Intake item**: the raw input for one spec (idea, notes, spike, Q&A log) under the workspace root, kept in `intake/new/` until its spec is written, then in `intake/processed/`.
- **Runtime skill**: the workflow skill included in the distributed plugin.
- **Conversion skill**: a distributed skill (CNV-001) that adopts an existing PRD or legacy intake item into specflow artifacts and gates. Distinct from spike *graduation* (INT-002.6), which carries a prototype's observed behavior into a fresh requirements phase; conversion takes an authored PRD, not a spike, as its source.
- **Catch-up skill**: the repository-only maintainer skill that reviews the AWS sources and records a ruling per upstream change.
- **AWS reference**: phase-specific Markdown in the plugin, adapted by hand from the AWS sources for selective runtime loading; each adopted passage names its source.
- **Source cursor**: the commit of an AWS source that a catch-up has fully reviewed, kept per source outside the plugin.
- **Behavior rule**: a numbered, host-neutral rule ported from a personal skill's port plan, enforced by a validator check or a scenario eval.
- **Parity gate**: the rule that a personal skill retires only after specflow passes every rule ported from it, on every supported host, using the same inputs.
- **Profile**: the workflow depth, `standard` or `quick`, mapped to AWS AI-DLC depth Standard and Minimal.

In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of this spec's intake item and of `docs/dev/project-management/`.

## Assumptions

- Release 0.1 supports Kiro IDE, Codex, and Claude Code and ships the full accepted feature set, including cross-spec review and advisory scripts, with host evals and parity evidence. External migration and source-skill retirement remain owned by their repositories.

## Requirements

### REL-001: Reproducible release

Source: the idea (`requirements.md` in intake item 00001)

**User story:** As a maintainer, I want a reproducible plugin artifact so that users can inspect exactly what was shipped.

#### Acceptance criteria

Criteria 1-2: see 00002.

Criterion 3: see 00003.

4. A RELEASE SHALL be a `specflow-vX.Y.Z` tag of the monorepo whose `plugins/specflow/` passed release verification.
5. A RELEASE SHALL follow a catch-up over every source (UPD-002.8).
6. THE PLUGIN version SHALL change whenever runtime instructions, distributed references, state schema, or compatibility behavior changes.

### REL-002: Success measures

Source: the idea (`requirements.md` §8 in intake item 00001)

**User story:** As a maintainer, I want the first release judged against observable measures, so that it ships only when they hold.

All eight measures gate the first release. Passing parity establishes readiness to retire a source skill; actual retirement still follows its external migration dependencies (§9).

#### Acceptance criteria

Criteria 1-3: see 00009.

4. The released `plugins/specflow/` contains no catch-up skill or maintainer tooling.
5. A catch-up over the three AWS sources produces a tracked report with a ruling per change considered and advances only the cursors of fully reviewed sources.

Criteria 6-8: see 00009.

### REL-003: Full initial delivery

Source: decision 2026-10-04 #3, superseding decision 2026-10-03 #4.

**User story:** As a developer, I want the first release to carry every accepted capability and its proof, so that nothing I was promised waits for a later version.

External migration remains separately owned: T-066 hands off the autopilot repoint, and T-067 hands off source-skill retirement after release. Those repositories perform their own changes; this does not defer any specflow capability or its proof.

#### Acceptance criteria

1. Release 0.1 SHALL deliver all accepted capabilities and checks in this specification, including cross-spec readiness review, advisory review scripts, full code-drift detection, every rule's check, scenario evals on all three supported hosts, and parity evidence.
2. No accepted capability or planned verification is deferred to a later release.
3. The release gate includes deterministic tests, the complete rule inventory check, cross-host handoff, host evals, and parity reports.

## Out of scope

1. Moving live chat history, hidden model context, pending tool calls, or host session identifiers between tools.
2. Reproducing Kiro IDE's private UI, buttons, or undocumented system prompts exactly.
3. Replacing Kiro's native Spec agent or preventing users from editing spec files manually.
4. Automatically merging concurrent edits from multiple agents.
5. Automatically executing newly downloaded upstream code.
6. Automatically pushing, publishing, committing, or releasing changes made during an upstream catch-up.
7. Making AWS AI-DLC's record tree (`aidlc/` or `.aidlc/`) the canonical project artifact format.
8. Depending on the AWS AI-DLC engine, its `aidlc` binary, or a Bun runtime.
9. Recording approvals without a developer. An external runner may read the status output (STATE-003) and implement approved tasks, but every gate still needs an explicit developer answer.
10. Project-level product discovery: a product vision or a technical-environment document. A developer may write those by hand or with another tool, such as `aws-samples/sample-aidlc-discovery`, and pass them to intake as input.
