# AWS guidance: design

Adaptation: Read this file in the design phase. Each passage under a source line is AWS AI-DLC text, copied verbatim with cuts shown as `[...]`; each `Adaptation:` line is specflow's own. Where the two differ, the specflow artifact contract wins. Read only the passages marked with the active profile or `[both]`.

## Find the building blocks

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Domain Design @ v2.11.0 (6a378b5) [both]

Identify and detail the **logical building blocks** of the system — the components you will write code for. A component is a bounded piece of software with its own business logic, entities, and lifecycle: **code you write, not infrastructure you deploy.** Databases, caches, queues, and third-party services are dependencies OF components, not components themselves.

This stage does NOT decide deployment topology (monolith, microservices, serverless, etc.) — that is Units Generation's job. Domain Design produces the building blocks so the team can then decide how to group them into deployable units. It also does not choose the tech stack or NFR patterns — those belong to the NFR and infrastructure stages.

Adaptation: specflow has one design pass. The building blocks go under Components and interfaces in `design.md`; how they are grouped and deployed, the stack, and the non-functional patterns go in the same document, under Architecture and the sections the artifact contract names.

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 2: Create Design Plan with Questions @ v2.11.0 (6a378b5) [both]

[...]
- Component boundary decisions (what is a distinct building block, and why)
- Entity ownership (each entity has exactly one owning component — ambiguity is a design smell)
- Component responsibilities (what business logic each block owns)
- Interaction between components (which component calls which, and why)
- Integration approach with existing components (brownfield)
- UI component structure (if user-facing, informed by UX designer perspective)

Adaptation: These are topics to settle, not a list to ask through. Ask only what the requirements and the repository leave open, one question at a time, as the requirements phase does.

## Entities and well-formedness

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 4: Generate the Component Catalogue @ v2.11.0 (6a378b5) [both]

**Entity capture depth.** Capture entities at the **ownership + shape** level only — which component owns each entity, its identifier, its attribute names, and any cross-component references. Do NOT specify data types, validation constraints, allowed values, or relationship cardinality here — that full schema belongs to Functional Design (`entities.md`). Every entity has **exactly one** owning component; ambiguous ownership is a design smell to resolve before the gate.

Adaptation: specflow has no separate functional design. Under `standard`, the full schema goes under Data models in `design.md`; under `quick`, ownership and shape are enough unless the change depends on a type or constraint.

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 4: Generate the Component Catalogue @ v2.11.0 (6a378b5) [both]

Well-formedness rules (all must hold): each component name is unique; every `component:`/`owned_by` named anywhere is a declared component; no component depends on itself; `depends_on`/`dependents` are symmetric (if A depends_on B, B lists A in dependents); every entity is owned by exactly one component and has an identifier; every `references.entity` is declared under its `owned_by` component; the dependency graph is acyclic (call out any deliberate cycle in the Rationale). Infrastructure, databases, caches, queues, and third-party services are `external_dependencies` — never components.

Adaptation: specflow writes no machine-readable catalogue. Apply the same rules to the components and dependencies `design.md` names.

## Weigh the options

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 4: Generate the Component Catalogue > Component-boundary options (when >1 viable decomposition) @ v2.11.0 (6a378b5) [both]

When a decomposition choice has more than one viable approach, present the
trade-off before recording the decision:

- Option A — <name>: pros / cons / reversibility
- Option B — <name>: pros / cons / reversibility
- Recommendation: <option> because <trade-off tied to responsibilities/change rate>

The team chooses at the gate (ownership stays with the team), then record the
chosen decomposition plus an **Alternatives Rejected** note in the Rationale
section of components.md.

When only one decomposition is viable, state why and skip the block.

Adaptation: The options and the rejected alternatives go under Alternatives considered in `design.md`. Among the alternatives, name an existing library, tool, or service that would do the job, when one exists.

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 5: Record Architecture Decisions (ADRs) @ v2.11.0 (6a378b5) [standard]

Each ADR MUST follow this structure (per the Inception phase guardrails):

- **ADR-NNN: <short title>**
  - **Context** — the forces and constraints that made a decision necessary
  - **Decision** — what was chosen
  - **Consequences** — the resulting trade-offs, both positive and negative
  - **Alternatives Rejected** — the other viable options considered and why they were not chosen

Adaptation: specflow writes no separate decisions file. Each significant decision is recorded in `design.md` with these four parts, beside the element it decides.

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Depth-Level Examples @ v2.11.0 (6a378b5) [quick]

- Domain Design: Single component diagram, basic data model, minimal ADR log (a one-line "no significant decisions" note is fine)

> Source: A1 `core/aidlc-common/protocols/stage-protocol.md` > 8. Depth Guidance > Depth-Level Examples @ v2.11.0 (6a378b5) [standard]

- Domain Design: Component diagrams with interactions, data model with relationships, 2-3 ADRs in the decisions log

## Parts that ship separately

> Source: A1 `core/aidlc-common/stages/inception/units-generation.md` > Steps > Step 2: Create Decomposition Plan with Questions @ v2.11.0 (6a378b5) [standard]

[...]
- Unit boundary strategy (by service, by feature, by domain, by deployment target)
- Unit granularity preference (coarse-grained vs. fine-grained)
- Dependency ordering preferences (strict topological only, or allow parallelism between independent units)
- Integration points and contracts between units (APIs, shared data, events)
- Deployment model (monolithic deploy, independent deploy, hybrid)

> Source: A1 `core/aidlc-common/stages/inception/units-generation.md` > Steps > Step 5: Execute Plan — Generate Unit Artifacts @ v2.11.0 (6a378b5) [standard]

- Dependency DAG between units (directed edges: "A depends on B"). Must be cycle-free.
- Integration points between units (APIs, shared data, events)
- Parallel development opportunities (sets of units with no dependency between them — multiple valid topological orderings exist)

Adaptation: Apply this only when the design has parts that build or deploy separately. specflow writes no unit files: `design.md` names the parts and the dependencies between them under Architecture, and `tasks.md` orders the work with `Depends on:` lines.

## Trace the requirements

> Source: A1 `core/aidlc-common/stages/inception/domain-design.md` > Steps > Step 6: Record Traceability @ v2.11.0 (6a378b5) [both]

[...] When
`stories.md` exists, enumerate every `USx.y`; otherwise enumerate every `FR`
from `requirements.md`. Map each upstream ID to the **component or entity**
in `components.md` that realizes it [...]

Adaptation: The requirement traceability table in `design.md` maps every acceptance criterion of `requirements.md` to the design element that realizes it. A criterion with no element is a gap to close before approval.
