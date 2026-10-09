# specflow bugfix workflow - discovery

Date: 2026-09-28. Purpose: capture how bugfix specs work in Kiro and AWS
AI-DLC so the specflow spec can create and run one end to end, not just
detect it.

Source keys (fetched or cloned 2026-09-28):

- **K1** https://kiro.dev/docs/specs/bugfix-specs.md (page dated Aug 4, 2026)
- **K2** https://kiro.dev/docs/specs.md
- **K3** https://kiro.dev/docs/specs/best-practices.md
- **K4** https://kiro.dev/blog/bug-fix-paradox/ (Feb 19, 2026)
- **U1** user capture, `calcard-mcp/.kiro/specs/harden-cross-account-url-check/`
  (Kiro, 2026-09-28; `.config.kiro`, `bugfix.md`, `design.md`; no `tasks.md` yet)
- **G1** github.com/sbenstewart/kiro-spark-challenge
  `.kiro/specs/llm-session-load-error/` (public Kiro capture, all 4 files)
- **G2** github.com/docktermj/senzing-bootcamp-kiro-powers
  `.kiro/specs/power-version-display/`
- **G3** github.com/ssatguru/BabylonJS-CharacterController
  `.kiro/specs/springback-ellipsoid-clearance/`
- **A1** awslabs/aidlc-workflows @ `589bf38` (2026-09-28)
- **A2** aws-samples/sample-ai-powered-sdlc-patterns-with-aws @ `3e7c0f0`
  (2026-08-07), subtree `all-phases/all-phases-aidlc-mcp/`

Verification: I read U1 in full, G1 `tasks.md` in full, the K1 and K4 quotes
below, `A1 core/scopes/aidlc-bugfix.md` in full, and the A1/A2 lines quoted
with a line number. Claims about G2/G3 and K2/K3 come from a research agent
and are marked (agent).

## 1. Kiro native bugfix spec

### 1.1 Creation and type marker

- IDE: "Select Bug Fix from workflow options"; CLI: `/spec new <name>`,
  choose "Fix a Bug", run with `/spec run <name>` (K1).
- Feature specs ask Requirements-First or Design-First; bug specs do not
  (K2, agent).
- The spec type lives only in `.config.kiro`:
  `{"specId": "<uuid>", "workflowType": "requirements-first", "specType": "bugfix"}`
  (U1 `.config.kiro:1`; same in G1-G3, agent). No Markdown file carries
  frontmatter (U1 `bugfix.md:1` is a plain `#` heading).
- Kiro's docs never mention `.config.kiro` (agent; inferred undocumented).
- A bugfix spec cannot be converted into a feature spec (K3, agent).

### 1.2 Phase order and gates

- "Bugfix Specs follow the same three-phase workflow as Feature Specs
  (Requirements → Design → Tasks), but with content tailored specifically
  for bug fixes" (K1).
- The user approves `bugfix.md`, then `design.md`, then tasks, as in feature
  specs (K1 flow diagram, agent).
- Review point: "Before writing any code or tests, Kiro presents C, P, and
  the hypothesis for your review." (K4)
- Quick Spec (no gates) is feature-only; no gate-free bugfix mode exists
  (K2, agent; inferred from absence).

### 1.3 `bugfix.md` (requirements slot)

Headings (U1 `bugfix.md:1-58`; G1 identical, agent):

```text
# Bugfix Requirements Document
## Introduction
## Bug Analysis
### Current Behavior (Defect)
### Expected Behavior (Correct)
### Unchanged Behavior (Regression Prevention)
## Bug Condition and Properties        (U1, G3 only; others put it in design.md)
### Bug Condition                      (pascal-style isBugCondition(X))
### Property: Fix Checking
### Property: Preservation Checking
### Counterexamples
```

Clause patterns (K1, verbatim):

- Current: "WHEN [condition] THEN the system [incorrect behavior]" (no SHALL)
- Expected: "WHEN [condition] THEN the system SHALL [correct behavior]"
- Unchanged: "WHEN [condition] THEN the system SHALL CONTINUE TO [existing behavior]"

Numbering is `section.item`: 1.x defect, 2.x expected, 3.x unchanged
(U1 `bugfix.md:29-50`). There is no user story and no `REQ-` ID.
The Introduction may already state the root cause (U1 `bugfix.md:5-16`).

### 1.4 `design.md`

K1: design.md holds "root cause analysis, proposed fix approach, and
properties to test for". Headings (U1 `design.md`; G1 same skeleton, agent):

```text
# <Title> Bugfix Design
## Overview
## Glossary                     Bug_Condition (C), Property (P), Preservation, F, F'
## Bug Details
### Bug Condition               **Formal Specification:** isBugCondition pseudocode
### Examples
## Expected Behavior
### Preservation Requirements
## Hypothesized Root Cause      numbered list of causes
## Correctness Properties       Property 1: Bug Condition, Property 2: Preservation,
                                each "_For any_ ... SHALL ...", "**Validates: Requirements 2.x**"
## Fix Implementation
### Changes Required            "Assuming our root cause analysis is correct:"
## Testing Strategy
### Validation Approach
### Exploratory Bug Condition Checking
### Fix Checking                FOR ALL X WHERE isBugCondition(X) ...
### Preservation Checking       FOR ALL X WHERE NOT isBugCondition(X) ASSERT F(X) = F'(X)
### Unit Tests
### Property-Based Tests
### Integration Tests
```

U1 adds a free-form `### Design Tension` and `### Optional: ...` under Fix
Implementation (U1 `design.md:197-240`), so the skeleton is a floor, not a cage.

The method (K4, verbatim):

- "The _**bug condition**_ C identifies when the bug triggers."
- "**Fix property (C ⟹ P):** When C holds, the patched code satisfies P."
- "**Preservation property (not C ⟹ unchanged):** When C doesn't hold, the
  patched code behaves identically to the original."
- The root cause is a hypothesis: "If they fail for a different reason, or
  don't fail at all, the hypothesis is refuted and Kiro re-analyzes before
  writing any fix."
- "If a preservation test flips, the fix has side effects and Kiro narrows
  the scope of the patch."

### 1.5 `tasks.md`

"Implementation tasks are generated with property-based tests (PBTs) that
validate: The bug is reproducible, The bug is fixed, No regressions are
introduced" (K1). Fixed four-task shape (G1 `tasks.md:1-65`, read in full;
G2, G3 and two more public samples match, agent):

```text
# Implementation Plan
- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - ...
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **EXPECTED OUTCOME**: Tests FAIL ...
  - Document counterexamples found
  - _Requirements: 1.x_
- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - ...
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: ... on unfixed code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - _Requirements: 3.x_
- [ ] 3. Fix ...
  - [ ] 3.1 <change>   _Bug_Condition:_ _Expected_Behavior:_ _Preservation:_ _Requirements:_
  - [ ] 3.2 Verify bug condition exploration test now passes
        **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
  - [ ] 3.3 Verify preservation tests still pass
- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
```

IDs are plain `N.` / `N.M`, trace tags are italic `_Requirements: x.y_`.
No sampled bugfix task list marks tasks optional with `*` (agent).
G3 adds a `## Task Dependency Graph` JSON block (agent).

## 2. AWS AI-DLC

### 2.1 aws-samples MCP prompts (A2, the current specflow upstream)

- Bugfixes use an opt-in abbreviated flow:
  `prompts.py:127` "# --- Abbreviated Brownfield Prompts (bug fixes / minor enhancements) ---";
  `server.py:39` `PHASE_SEQUENCE_ABBREVIATED`
  (discovery-0.1-lite, inception-1.1-lite, construction-2.2-lite,
  operations-3.1, deployment-2.3-lite, agent); `server.py:438`
  "Abbreviated (lite) is only used when explicitly requested".
- Acceptance criteria include "Regression criteria (what existing behavior
  must NOT change)" (`prompts.py:163`), the same idea as Kiro's Unchanged
  Behavior.
- No reproduction step, no root-cause section, no failing-test-first rule
  (agent, searched `reproduc|root.cause`).
- Artifacts go to `.aidlc/` files such as `targeted_analysis.md`,
  `changes_summary.md`, `validation_report.md` (agent), none Kiro-shaped.

### 2.2 awslabs/aidlc-workflows (A1, new candidate upstream)

- A named `bugfix` scope: `core/scopes/aidlc-bugfix.md:2-3` `name: bugfix`,
  `depth: Minimal`; keywords `fix`, `bug`, `broken` (`:4-7`);
  `guard_policy: relaxed` (`:12`): "changed inputs are recorded and
  announced rather than reopening approval" (`:25`).
- Stages: "Initialization, reverse-engineering, requirements-analysis,
  code-generation, build-and-test, deployment-pipeline, and
  deployment-execution execute; the rest is SKIP." (`:42-44`)
- Reverse engineering is forced: `docs/reference/04-stages/inception.md:72`
  "2.1 (always -- find the bug), 2.3 (minimal -- bug description)".
- Regression test mandated: `core/aidlc-common/stages/construction/code-generation.md:138`
  "a targeted regression for the bug/vulnerability at the narrowest level
  that reproduces it ... the existing suite remains green"; enforced in
  code at `core/tools/aidlc-testing-posture.ts:899`.
- Test-before-fix is only an agent principle, not a gate:
  `core/agents/aidlc-quality-agent.md:63` "write a test that reproduces it
  before fixing".
- No root-cause stage for the reported bug (agent; "root cause" appears only
  in build-and-test loop-back and post-rollback analysis).
- Kiro coexistence, no mapping: `docs/guide/harnesses/kiro-ide.md:216`
  "Kiro's welcome panel (Spec, Plan, Bug Fix, Quick Spec) lists Kiro's own
  workflows; AI-DLC does not appear there" (continuation per agent).

## 3. Comparison

| Concern | Kiro | A2 samples | A1 aidlc-workflows |
|---|---|---|---|
| Distinct bugfix flow | yes, spec type | opt-in "abbreviated" | `bugfix` scope |
| Requirements shape | Current / Expected / Unchanged, 1.x/2.x/3.x | stories + regression criteria | minimal requirements.md |
| Root cause | design.md, hypothesis, falsified by task 1 | none | none for the bug |
| Failing test first | task 1, MUST FAIL | no | principle only |
| Preservation | property tests on unfixed code, task 2 | "regression criteria" | "existing suite remains green" |
| Gates | same 3 as feature | 2 per phase | every domain stage |
| Artifact home | `.kiro/specs/` | `.aidlc/` | own tree (see study) |

Kiro is the richest and the only one that fits the canonical layout. Both AWS
sources contribute depth rules, not artifact shape.

## 4. Gaps in the specflow spec (as of `6f7502b`)

1. **Create path missing.** ART-001.2 and design §6.5 only detect `bugfix.md`;
   nothing creates one. No bugfix template in design §3 `templates/`.
2. **Type marker.** The spec infers the shape from files present (§6.5).
   Kiro marks it in `.config.kiro` `specType`. specflow neither reads nor
   writes `.config.kiro`, so a specflow-created bugfix spec may not show
   as a Bug Fix spec in Kiro (unverified: whether Kiro needs the file).
3. **Requirements rules clash.** ART-002 demands user stories, `REQ-` IDs and
   EARS "THE SYSTEM SHALL"; Kiro bugfix uses Current/Expected/Unchanged,
   `1.x/2.x/3.x`, and a Current clause without SHALL.
4. **Design rules clash.** ART-003.2's section list (architecture,
   components, data model, rollout ...) does not match the bugfix design
   skeleton (bug condition, hypothesized root cause, properties, fix,
   fix/preservation checking).
5. **Task shape.** ART-004 and §6.4 use `T-001` with `Requirements:` lines;
   Kiro bugfix uses the fixed 4-task shape with `_Requirements:_` tags and a
   MUST FAIL first task. The user's testing rule (fail-first regression
   test) is met by Kiro task 1.
6. **Hypothesis loop.** No rule for "exploration test did not fail as
   predicted -> re-analyze root cause", which reopens design (invalidation
   graph §7.4 has no path for it).
7. **Profile.** WF-003 quick/standard is orthogonal; Kiro has no quick
   bugfix. AI-DLC runs bugfix at Minimal depth.
8. **Intake.** Kiro's prompt asks for reproduction steps, expected result,
   and constraints (K1); specflow intake has no bugfix question set.
9. **Validation.** VAL-001.2 checks `REQ-` IDs; no bugfix rule set (three
   sections present, clause patterns, every 2.x has a fix check, every 3.x
   a preservation check).
10. **Fixtures.** T-027 already plans a bugfix capture; U1 plus G1 exist now.

## 5. Decision minutes (2026-09-28, user)

| # | Finding | Decision | Status |
|---|---|---|---|
| 1 | aidlc-workflows relation (§6) | Separate discovery session; prompt in `docs/dev/tmp/prompt-specflow-aidlc-workflows-discovery.md` | queued -> `discovery/00001-specflow-aidlc-workflows.md` |
| 2 | Gaps 1, 3, 4, 5, 9: bugfix contract | Mirror Kiro exactly | applied: ART-005, ART-002/003/004 scoped to feature, VAL-001.2/.4, design §3, §6.6 |
| 3 | Gap 2: type marker | Write `.config.kiro` + `.specflow.json`, read either | applied: ART-001.6-7, STATE-001.2, design §6.1, §6.5, §7.1 |
| 4 | Gap 6: refuted hypothesis | Stop and reopen design; never edit tests to fit | applied: ART-005.9-10, design §6.6, §7.4, §8 |
| 5 | Gaps 7, 8: profile and intake | Profiles apply; spec type + four bug inputs at intake | applied: WF-003.7-9, design §9.3 |
| 6 | Gap 10: fixtures | Fresh synthetic capture; public specs cited, not copied | applied: T-027, T-020, T-038, T-039, T-050, design §15 |

## 6. aidlc-workflows as a wider redesign input

The user flagged A1 as a likely strong complement and a major redesign
(2026-09-28). First-pass fit, from one agent study; lines I re-read myself
are marked (read), the rest (agent):

- **Same goal, different artifacts.** "One harness-neutral core runs
  natively in Claude Code, Kiro CLI, Kiro IDE, Codex CLI, Cursor, opencode,
  and GitHub Copilot" (`README.md:3-6`, read). Artifacts live in
  `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/` (`docs/guide/10-state-and-audit.md:9`,
  read), never `.kiro/specs`. Our non-goal "make `.aidlc/` canonical"
  (requirements §3.7) names the wrong dir: `.aidlc/` is only an engine dir
  for opencode/Copilot (`docs/guide/15-troubleshooting.md:60`, read).
- **Resume anywhere.** "Session resume works on every harness"
  (`docs/guide/11-session-management.md:5`, read). But the `active-intent`
  cursor is gitignored (`docs/guide/12-cli-commands.md:296`, read) and
  approvals must come from the invoking session (agent, `10-state-and-audit.md:48-50`).
- **Invalidation is policy-gated.** "`strict` reopens the approval";
  "`relaxed` and `off` keep going" (`docs/guide/13-customization.md:249-250`,
  read). Downstream staleness is "read-only and advisory"
  (`docs/reference/12-state-machine.md:1479`, read). specflow's WF-002.5-6 is
  stricter.
- **Needs a runtime.** Native `aidlc` binary or Bun (`README.md:29-45`, read);
  deterministic TypeScript engine, 78 tools, 17 hooks (agent). specflow's
  core is Markdown + JSON with no required runtime (requirements §7).
- **Extensible without forking.** Third-party AIDLC plugins add stages,
  scopes, agents, knowledge; "A plugin never edits `core/`" (agent,
  `docs/harness-engineering/10-authoring-a-plugin.md:8-14`).
- **Richer method.** 11 scopes (classic, express, feature, enterprise, mvp,
  poc, bugfix, refactor, infra, security-patch, workshop), 33 stages, depth
  levels (agent, `docs/guide/workflow-profiles.md:22-34`). specflow has two
  profiles.
- **Provenance.** MIT-0 (`README.md:9`, read). A1 never mentions A2: no hit
  for `sample-ai-powered|aidlc_mcp|aws-samples` (control `awslabs/aidlc-workflows`
  hits `README.md` 3 times). A2 was last touched 2026-08-07; A1 ships
  v2.10.0 and committed 2026-09-28.

Takeaway (inferred): A1 is the maintained AWS source of method (scopes,
depth, stage rules); Kiro stays the source of artifact shape. Whether A1
replaces A2 as the pinned upstream, sits beside it, or becomes the runtime
is the redesign question. It touches AWS-001/002, UPD-001-003, design §9-§11,
and Plan B.

**Decision (user, 2026-09-28):** study it in a separate discovery session
(`discovery/00001-specflow-aidlc-workflows.md`, to be written). Bugfix spec
edits here follow Kiro's shape and cite no AWS upstream for depth rules.
