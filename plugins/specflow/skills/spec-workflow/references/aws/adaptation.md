# AWS AI-DLC adaptation record

specflow adapts the method of three public AWS AI-DLC repositories by hand. Nothing upstream is vendored, and nothing is fetched at runtime: the four phase references beside this file hold the adopted passages, each under a source line, and this file records where they came from.

## Source record

| Source | Role | Adopted from | License |
|---|---|---|---|
| A1 `awslabs/aidlc-workflows` | primary method | `v2.11.0` `6a378b53c0a4fe0641ed7d8de8dfff94264d5b6a` | MIT-0 |
| A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` | complementary patterns; the original source | `3e7c0f0aa2a1a084c94631edb709deae5fe0ae4f` | MIT-0 |
| A3 `aws-samples/sample-aidlc-discovery` | complementary discovery | `a84b2899d0dd518081a4764b42fde4c6dbf3cc9a` | MIT-0 |

A1 is adopted from release tags only, never a preview tag or a branch head; the cell names the tag and the commit it points to. A2 and A3 are recorded by commit. Nothing is adopted from A2 yet, so its cell records the commit that was read.

## Profile mapping

A1 runs 11 scopes over 33 stages at three depths. specflow keeps two profiles and Kiro's three documents, and maps the profiles onto A1's depth axis, not its scopes:

| specflow profile | A1 depth |
|---|---|
| `standard` | Standard |
| `quick` | Minimal |

A1 scope names never become profiles: some skip artifacts specflow always writes (`express` has no design pass), and `bugfix` is already a spec type. Stage paths below are under `core/aidlc-common/stages/`; `stage-protocol.md` is at `core/aidlc-common/protocols/stage-protocol.md`.

### Standard profile

| Portable phase | AWS guidance source (depth Standard) | Portable output |
|---|---|---|
| Intake | No A1 stage; A3 discovery rules adapted as local rules (below); local `phases/intake.md` (repository discovery) | Context feeding requirements and design |
| Requirements | `inception/requirements-analysis.md`; `stage-protocol.md` `## 3. Question Format` | `requirements.md` |
| Design | `inception/domain-design.md`, `inception/units-generation.md` | `design.md` |
| Tasks | None; local `phases/tasks.md` (contracts, sizing, and verification) | `tasks.md` |
| Implementation | `construction/code-generation.md` (test floor) | Source changes plus task updates |
| Verification | `construction/build-and-test.md`; `stage-protocol.md` `## 8. Depth Guidance` (test strategy) | Test evidence and task completion |
| Deployment | Not in the adoption set | Design/tasks sections when in scope, not a fourth artifact |

### Quick profile

| Portable phase | AWS guidance source (depth Minimal) | Portable output |
|---|---|---|
| Intake | No A1 stage; the same adapted A3 rules; local `phases/intake.md` (targeted discovery) | Concise impact assessment |
| Requirements | `inception/requirements-analysis.md`, Minimal passages | `requirements.md` |
| Design | `inception/domain-design.md`, Minimal passages; existing-pattern assessment (ART-003.5) | Minimal `design.md` |
| Tasks | None; local `phases/tasks.md` (same checks, concise task text) | `tasks.md` |
| Implementation | `construction/code-generation.md` Minimal floor (one test per requirement plus a happy-path floor) | Source changes |
| Verification | `construction/build-and-test.md`, Minimal passages | Regression evidence |
| Deployment | Not in the adoption set | Conditional design/task entries |

## A1 `awslabs/aidlc-workflows`

### Adopted

Text is taken only from the adoption set: `core/scopes/*.md`; the stages `inception/requirements-analysis.md`, `inception/domain-design.md`, `inception/units-generation.md`, `construction/code-generation.md`, and `construction/build-and-test.md`; `stage-protocol.md` (`3. Question Format` and `8. Depth Guidance`); and the stage-by-scope matrix in `docs/guide/05-scopes-and-depth.md`. Each passage sits verbatim under its source line in a phase reference; cuts are shown as `[...]`.

### Adapted

A1's stage files wrap the method in engine plumbing. Adaptation keeps the method and leaves the plumbing out. Reworded upstream method goes on `Adaptation:` lines under the source line it came from, and the local artifact contract wins where the two differ. Because the plumbing outweighs the method, most reference text is adapted, with short verbatim passages.

A full read of twelve stages outside the adoption set (the seven `ideation` stages, the three `initialization` stages, `practices-discovery`, and `reverse-engineering`) gave these local rules. No text is taken from those stages:

- one fixed rule for "existing code or empty", and a coverage statement for every discovery (WF-003.15, WF-003.16; from `workspace-detection` and the scope block of `reverse-engineering`);
- a source for every requirement, nothing unpicked turned into scope, and assumptions named at approval (ART-002.15, WF-002.1; from the grounding contract of `intent-capture`);
- applicable repository instructions read on every host, with their scope preserved (WF-003.17; from the guardrail files each A1 stage loads);
- an existing library, tool, or service among the design alternatives (ART-003.12; from `market-research`);
- a commit recorded at approval and a drift warning (WF-004.8; from the freshness guard of `reverse-engineering`);
- a "not decided yet" choice, plain words with terms defined, and a playback before drafting (ART-002.16-18; from `intent-capture`, `practices-discovery`, and the summary checkpoint in `stage-protocol.md`);
- working practices asked when nothing shows them (WF-003.18; from `practices-discovery`), and a `Depends on:` line between specs (ART-002.11, WF-001.9; from the dependency register of `feasibility`);
- design-system/accessibility context and an accessibility note for sketches (INT-002.8; from `rough-mockups`, with known-answer reuse and the spike budget of the spike rules), and one explicit path for an input file (INT-001.8; from `intent-capture`).

### Not adopted

- Engine plumbing: engine calls (`aidlc engine ...`, `bun .../aidlc-utility.ts`), the `[Answer]:` question-file protocol, audit events, sensors, harness tokens (`{{HARNESS_DIR}}`, `{{INVOKE}}`), and `aidlc/` record paths. None of these is copied into normative runtime instructions.
- Question batching (up to four per turn) and the three answer modes: one question at a time stays.
- `FR{n}`/`NFR{n}` IDs: feature specs keep `REQ-`/`T-`.
- Scope names as profiles.
- Guard Policy `relaxed`/`off` with advisory staleness: an approval goes stale on any change, as the artifact contract says.
- From the twelve stages read in full: stakeholder maps and team formation, market sizing and competitor analysis, the go/no-go brief, backlog scoring, multi-repo work, the shared code knowledge base with its locks and fingerprints, and saving confirmed practices into the repository's own files.
- The other sixteen stages (four inception, five construction, seven operation) have not been read against specflow.

## A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws`

A2 was the original source and calls itself complementary to A1.

### Adopted

Nothing yet.

### Adapted

Nothing yet. Its `all-phases/all-phases-aidlc-mcp/` pattern stays under review.

### Not adopted

The rest of its pattern catalog has not been read against specflow.

## A3 `aws-samples/sample-aidlc-discovery`

A3 covers the discovery that comes before a spec.

### Adopted

No text is taken from A3.

### Adapted

These are adapted as local rules (decisions 2026-10-03 #10 and #11):

- what must not change, in the repository and in systems outside it, and how to learn about those systems (WF-003.11);
- binding technical constraints when the repository gives nothing to infer, each ban with its reason and alternative, plus one example to imitate (WF-003.12);
- intake choices saved to disk as soon as they are confirmed (WF-003.13), and a profile that can be raised later (WF-003.14);
- genuine uncertainty in hedged answers recorded as unresolved questions, with definite current choices and later follow-ups kept distinct (decision 2026-10-04 #2); a source for every inferred answer, and a progress line while asking (ART-002.12-14);
- answers logged in the developer's own words, in an append-only log (INT-001.5);
- English structure whatever the developer's language (ART-001.11), and a validation failure for an unclosed code fence (VAL-001.11);
- a sketch form of the spike: a user journey and static mockups (INT-002.8).

### Not adopted

A3's product-level documents, parallel roles, batch answer files, the audit log of every interaction, and automatic language detection.
