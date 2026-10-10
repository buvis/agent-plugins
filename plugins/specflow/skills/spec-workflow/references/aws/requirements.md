# AWS guidance: requirements

Adaptation: Read this file in the requirements phase. Each passage under a source line is AWS AI-DLC text, copied verbatim with cuts shown as `[...]`; each `Adaptation:` line is specflow's own. Where the two differ, the specflow artifact contract wins. Read only the passages marked with the active profile or `[both]`.

## Analyze the request

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 2: Analyze User Request @ v2.11.0 (6a378b5) [both]

Assess the user's request for:
- **Clarity**: How well-defined is the request?
- **Type**: New feature, enhancement, refactoring, bug fix, migration
- **Scope**: Single component, multi-component, system-wide
- **Complexity**: Simple, standard, complex

Adaptation: A bug fix is the `bugfix` spec type; every other type is a `feature` spec.

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 3: Determine Depth @ v2.11.0 (6a378b5) [both]

Based on complexity assessment:
- **Minimal**: Clear request, narrow scope, well-understood domain
- **Standard**: Moderate scope, some unknowns, multiple stakeholders
- **Comprehensive**: Large scope, significant unknowns, complex domain

Adaptation: The profile chosen at intake sets the depth: `standard` is Standard and `quick` is Minimal. specflow has no Comprehensive profile; a request that would need it uses `standard`.

## Assess what is known

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 4: Assess Current Requirements @ v2.11.0 (6a378b5) [both]

Extract and organize what is already known from the user's input:
- Explicit functional requirements
- Implied non-functional requirements
- Constraints and assumptions
- Business context and goals

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 5: Completeness Analysis @ v2.11.0 (6a378b5) [both]

Evaluate coverage across six dimensions:
1. **Functional requirements** — Core behaviors, features, use cases
2. **Non-functional requirements** - Performance, security, scalability, reliability, observability
3. **User scenarios** — User workflows, edge cases, error scenarios
4. **Business context** — Goals, success metrics, stakeholders, constraints
5. **Technical context** — Integration points, platform requirements, technology constraints
6. **Quality attributes** — Maintainability, testability, accessibility, usability

Identify gaps in each dimension.

Adaptation: Under `standard`, also cross each component the request names with the conditions it touches (empty input, failure, concurrency, limits). Carry each condition that applies into `requirements.md` as an acceptance criterion, an assumption with its reason, or an exclusion. Ask about one only when it depends on a fact about the developer's world that the repository cannot show.

## Ask clarifying questions

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 6: Generate Clarifying Questions @ v2.11.0 (6a378b5) [both]

PROACTIVE: Always generate clarifying questions unless requirements are exceptionally clear and complete across all six dimensions.

[...]

Adaptation: specflow asks one question at a time, in chat, and writes no questions file. Each answer goes into the intake log in the developer's own words. A question offers its likely answers and always leaves room for a free answer.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Depth-aware question generation @ v2.11.0 (6a378b5) [quick]

| Minimal | ~2-4 per stage | Ask only what's essential to proceed. Skip questions where the answer can be reasonably inferred from context, prior stages, or codebase analysis. Minimal follow-ups unless answers are contradictory or dangerously vague. |

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Depth-aware question generation @ v2.11.0 (6a378b5) [standard]

| Standard | ~5-8 per stage | Cover the stage's topic areas. Follow up on ambiguities. Probe for missing details when answers are incomplete. |

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Depth-aware question generation @ v2.11.0 (6a378b5) [both]

**These are guidelines, not hard caps.** The agent MUST use judgment:
- A Minimal bugfix with a vague one-line description warrants more questions — don't blindly cap at 2.
- A Comprehensive enterprise feature with crystal-clear requirements warrants fewer — don't pad with noise.
- Prior stage outputs reduce what needs asking. If requirements-analysis already captured NFR targets, construction stages shouldn't re-ask.
[...]
- Follow-up questions are always justified regardless of depth — ambiguity must be resolved.
- Contradiction detection and resolution remains MANDATORY at all depth levels.

Adaptation: Before asking, read the intake log. A question it already answers is not asked again; when the answer leaves a real gap, ask a narrow follow-up that names the earlier answer.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Depth-aware question generation @ v2.11.0 (6a378b5) [both]

**Questions must be self-explanatory.** A question the user cannot answer without asking you to rephrase it is a defect, not a saved token. Every question MUST stand on its own:
- **Expand every identifier in each question that uses it.** Never present a bare reference like `FR3`, `url1`, `NFR-2`, or `unit-4` as if the user carries the mapping. Write the thing it names, then the tag once in parentheses — "the requirement that the export must finish within 5 minutes (FR3)" — not "Is FR3 still correct?".
- **Give each question one line of context** — why it is being asked or what depends on the answer — when the reason is not obvious from the prompt itself. "We found two conflicting retention values in the requirements (30 days vs 90 days); which governs?" beats "What is the retention period?".
- **Prefer a concrete phrasing over an abstract one.** Ask about the actual decision in the user's domain terms, not the framework's internal vocabulary. If you would need to explain the question when asked to rephrase it, phrase it that clear way the first time.

## Analyze the answers

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Answer analysis (MANDATORY) @ v2.11.0 (6a378b5) [both]

After collecting answers, analyze ALL responses for:
- Vague answers: "mix of", "not sure", "depends", "probably"
- Contradictions between answers
- Missing details needed for the next step

If ANY ambiguity found: create follow-up questions and resolve before proceeding.
**When in doubt, ask.** Incomplete answers lead to poor designs.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Contradiction detection (MANDATORY) @ v2.11.0 (6a378b5) [both]

After all answers are collected, cross-check the full answer set for:
- **Scope mismatch**: e.g., user says "keep it simple" but also requests enterprise-grade features
- **Risk mismatch**: e.g., user says "security is not a concern" but describes handling sensitive data
- **Technology conflicts**: e.g., user requests offline-first but also requires real-time collaboration
- **Timeline vs. scope conflicts**: e.g., user wants MVP timeline but full-feature scope

When contradictions are detected:
1. Present the specific contradictory answers side by side
2. Explain why they conflict
3. Ask a targeted follow-up question to resolve the contradiction
4. Do NOT proceed until contradictions are resolved

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Overconfidence prevention @ v2.11.0 (6a378b5) [both]

- Default to asking, not assuming. Never proceed with ambiguity.
- If an answer seems incomplete, probe deeper.
- Red flags that require follow-up:
  - Single-word answers to open-ended questions
  - Contradictory signals between different answers
  - Answers that dodge the question or change the subject
  - Relaxing, lowering, or disabling a previously defined quality target (e.g.
    a test coverage threshold) instead of meeting it
[...]

Adaptation: When the developer's answer is itself uncertain, record it as an unresolved question with what would resolve it, and keep a definite current choice apart from a later follow-up. When the developer leaves a choice to you, pick the option that best fits what they said, and say in one line what you chose.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 3. Question Format > Consuming grounded artifacts @ v2.11.0 (6a378b5) [both]

When an upstream artifact carries inline source tags or an
`Assumptions & Open Questions` section, preserve that epistemic status:

- A source tag records provenance; it does not grant permission to strengthen
  or broaden the claim.
- Content tagged `[assumption]` remains an assumption in every downstream
  artifact until the user confirms it through that downstream stage's
  questions file.
- Never silently promote an assumption, open question, unselected option, or
  workflow metadata into a confirmed requirement, scope boundary, stakeholder,
  metric, or constraint.
- When downstream work needs an unresolved item, ask a follow-up and record the
  answer in the current stage's questions file.

Adaptation: specflow's questions file is the intake log.

## Write the requirements

> Source: A1 `core/aidlc-common/stages/inception/requirements-analysis.md` > Steps > Step 10: Generate Requirements @ v2.11.0 (6a378b5) [both]

[...]
- **Intent analysis** — What the user is trying to achieve (goals, not just features)
- **Functional requirements** — Organized by feature area or domain. [...]
- **Non-functional requirements** — Performance, security, scalability, reliability, and observability targets. [...]
- **Constraints** — Technical, business, and organizational constraints
- **Assumptions** — Documented assumptions with rationale
- **Out of scope** — Explicitly excluded items
- **Open questions** — Any remaining uncertainties for later stages

Adaptation: These contents land in the `requirements.md` layout of the artifact contract. A requirement keeps its `REQ-` ID, a user story, and numbered acceptance criteria; open questions go under Unresolved questions. IDs are never renumbered once written.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Depth-Level Examples @ v2.11.0 (6a378b5) [quick]

- Requirements Analysis: 5-10 requirements, brief descriptions, minimal NFR coverage

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Depth-Level Examples @ v2.11.0 (6a378b5) [standard]

- Requirements Analysis: 15-30 requirements with acceptance criteria, moderate NFR coverage

Adaptation: The counts are a guide, not a target. A small `standard` spec with five requirements is fine; never pad.
