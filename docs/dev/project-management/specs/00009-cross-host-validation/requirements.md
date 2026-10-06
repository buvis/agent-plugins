# Requirements: specflow cross-host validation

Sources: docs/dev/project-management/intake/processed/specflow/00009-cross-host-validation/

Depends on: 00003, 00004, 00005, 00006, 00007, 00008

## Purpose

Produce the evidence the first release rests on: canonical fixtures, a full cross-host handoff, native-Kiro coexistence, concurrent-edit protection, a security review, context-efficiency measurements, every behavioral rule's eval on every supported host, the parity gate per retiring skill, and the conversion acceptance test.

## Scope

Phase 7 of the source plan plus T-081 (T-050 to T-058, T-081). These tasks prove again, on real hosts, criteria owned by the specs this one depends on. This spec owns the evidence obligations: the host runs of the evals, the parity gate, and six of the eight success measures.

The product's purpose, goals, actors, terms, and exclusions are in 00001. In `Source:` lines and criteria, `qa-log.md`, decisions, discovery documents, and `design §n` mean the documents of intake item 00001 and of `docs/dev/project-management/`.

## Assumptions

- That reference skill's conversion was exercised against a real PRD: the agent converted a calcard-mcp bugfix PRD into a specflow artifact set at `buvis/calcard-mcp` `docs/dev/project-management/specs/00032-add-if-match-preconditions-to-event-writes/` (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`). As read on 2026-10-04, its requirements and design are approved, its task plan is drafted and not approved, and it has no receipt and no completed work. That spec is the acceptance fixture the shipped conversion skill is verified against, by structure (decision 2026-10-04 #12).

## Requirements

### RULE-001: Behavior rules and parity

Source: decision 2026-09-27 #4-6; Plan A and Plan B port plans.

**User story:** As a maintainer, I want every ported skill behavior numbered and checked, so that retiring a personal skill never loses behavior silently.

#### Acceptance criteria

Criteria 1-3: see 00005.

4. Scenario evals SHALL run on each supported host; a host without a headless mode SHALL use a recorded manual run.

Criterion 5: see 00005.

6. A personal skill SHALL retire only after specflow passes every rule mapped from it, on every supported host, using the same inputs (parity gate).

### REL-002: Success measures

Source: the idea (`requirements.md` §8 in intake item 00001)

**User story:** As a maintainer, I want the first release judged against observable measures, so that it ships only when they hold.

#### Acceptance criteria

1. A spec created in Kiro IDE can be resumed in Codex, edited in Claude Code, and returned to Kiro without relocating files.
2. Editing approved requirements in any tool makes design and tasks stale on the next validation.
3. A fresh session can determine the correct next phase using only the repository.

Criteria 4-5: see 00001.

6. Compatibility tests pass for Kiro IDE, Codex, and Claude Code.
7. Each personal skill due to retire passes its parity gate: specflow meets every rule mapped from it on every supported host.
8. An external runner can read a spec's gates and next task from the status output alone.
