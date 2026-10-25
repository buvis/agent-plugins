# Autopilot split design: doubt review

> Historical assessment. The 2026-10-25 three-layer redesign supersedes earlier ownership conclusions: Autopilot/controller owns workflow truth, OVCAQ owns execution, Lantern owns presentation. Preserve the source observations; use the current design and PRDs for implementation.

Historical review of the superseded two-backend design. The user’s later boundary correction replaces its standalone-state assumptions. See the [boundary correction review](00011-autopilot-boundary-correction-review.md); prior runtime/ownership findings are not approval for a second backend.

Reviewed 2026-10-25 with the review-with-doubt skill. Two passes; documentation only.
Result: 11 doubts — 7 fixed, 2 verified/dismissed, 2 explicit limitations.

## Findings and actions

| ID | Category | Doubt | Resolution |
| --- | --- | --- | --- |
| F1 | FIX | Wave implementation could require an unowned later plugin contract edit, creating a circular dependency. | Contract PRD 00012 defines optional wave request shapes; plugin 00016 implements translation; OVCAQ 00061 implements the already-defined capability. |
| F2 | FIX | Amending the accepted OVCAQ plan invalidates its pinned coverage digest. | Reconciled plan/held provisioning/coverage ownership and regenerated the digest. Reconstructing the pre-amendment plan matched the original accepted hash exactly. |
| F3 | FIX | Concurrent OVCAQ fixes already implement some lifecycle preconditions. | PRD 00057 explicitly preserves those fixes and scopes new work to remaining gaps; no concurrent code was edited. |
| F4 | FIX | Proposed JSON flag placement differed from the live OVCAQ parser. | Design commands use the existing global flag form: `ovcaq --json workflow ...`. |
| F5 | FIX | File allowlists omitted generated command documentation and TUI integration files. | Added the actual CLI, documentation and app/model/panel paths to relevant PRDs; command docs derive from the live parser. |
| F6 | FIX | Generated test sections repeated vague expectations and assigned arbitrary scenario labels. | Replaced them with concrete happy/edge/error scenarios, observable state/artifact outcomes and named tests. |
| F7 | FIX | Module exports were generic and prerequisite-owned files were repeatedly declared new. | Named actual command/data exports and declared new files only at their first owning PRD. |
| V1 | VERIFY | The port could silently omit or invent persona/skill identities. | Read the source file lists: the planned eleven skills and eighteen persona names match. |
| V2 | VERIFY | Managed dependencies could still block standalone delivery or leave the user’s request incomplete. | Saved six plugin and five OVCAQ PRDs, checked an acyclic dependency graph, and proved the standalone conformance dependency closure contains no OVCAQ node. |
| K1 | KNOWN | Current host APIs might not supply every required session/interception guarantee. | This is a design task, not runtime implementation. Headless installed-host probes are mandatory implementation gates; unsupported execution profiles refuse instead of weakening reviews. |
| K2 | KNOWN | OVCAQ planning artifacts are not durable in git. | The repository deliberately ignores all project-management documents. Files are written locally as requested; no force-add or unrelated policy change was made. |

## Six-question check

1. Least confidence: actual host enforcement and native session identity remain K1; no live compatibility claim is made.
2. Assumptions: checked source identities, parser flag placement, schema/service paths and the accepted-plan digest; F1–F5 resolve unsupported assumptions.
3. Completeness: the accepted standalone/optional split, contracts, synchronization and both backlogs are present; source retirement and held OVCAQ work remain separate.
4. Practical failures: the design covers wrong-mode ownership, crash/replay, stale revision/evidence, lost acknowledgement, ended sessions and missing capabilities; F1/F3/F5 remove concrete integration gaps.
5. Retrospective: reduced vague generated prose and made module ownership explicit through F6/F7; retained the existing algorithms instead of specifying an unrelated generic engine.
6. Missing validation: runtime and installed-host tests belong to implementation (K1); all authored PRDs passed grounding, structure and link/dependency checks now.

## Slop check

- Bloat: standard-template sections are required, but repetitive test prose was unnecessary and removed (F6). Each PRD remains below 200 lines.
- Defensive impossibility: mode collisions, stale receipts and interrupted renames are reachable because independent processes and durable state outlive a session; their guards are justified.
- Single-caller abstraction: a common facade serves two concrete backends and keeps shared skills independent of state storage; no additional RPC framework is specified.
- Comment paraphrasing: generic export descriptions repeated responsibility fields; replaced with concrete exports (F7). No production comments were added.
- Framework tests: schema/manifest shape is an actual cross-repository contract; conformance tests additionally assert mutations, artifacts and rejected actions, rather than only mocks or file existence.

## Second pass and evidence

All eleven saved PRDs pass the create-prd grounding gate, standard-template ordering, bounded length and no-unresolved-marker checks. Task lines contain dependencies and acceptance criteria. Sequence scans found no collisions. Design/PRD links resolve. The delivery graph is acyclic and standalone release has no OVCAQ prerequisite. OVCAQ’s accepted-plan digest matches its amended plan, and provisioning remains held. The target validator passes. Source claude-autopilot is unchanged.

The second pass checked the fixes themselves, including optional wave schemas and consumer order, generated-doc path coverage and the original pre-amendment plan hash. No further actionable doubt remains within this authoring scope.
