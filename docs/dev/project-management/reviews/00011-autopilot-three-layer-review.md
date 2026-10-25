# Three-layer architecture planning review — 2026-10-25

Scope: documentation/PRD redesign only. Applied create-prd standard template/grounding, manage-agents-md ownership guidance and review-with-doubt. No implementation PRD was executed; the fresh-session work-completion gate is not claimed.

## Result

Autopilot carries one canonical controller for standalone and managed workflow truth. OVCAQ owns agent/session/process orchestration and public operations. Lantern is the provisional independent TUI. The [design](../designs/00011-autopilot-standalone-design.md) is authoritative.

Updated six existing AP PRDs and added00018–00021 (ten total). Respecified OV00057–00061, added00064/00065, preserved00062/00063 byte-for-byte. Added Lantern00001–00003 in a local planning-only directory. Reconciled five held OV PRDs, accepted-plan/coverage digest, feasibility/inventory interpretation, historical-review notes and current/target ownership instructions. No Git repository/remote or published package was created for Lantern.

## Skeptical pass one

| Question / doubt | Classification | Action and evidence |
| --- | --- | --- |
| Least confident: request identity was specified without credential transport/bootstrap | FIX | Contract A/AP00018 now define absent-store bootstrap, restricted credential files, --actor-file and actor/scope binding; no secrets in output |
| Assumptions: architecture-document path was guessed incorrectly | FIX | Used actual OV docs/dev/architecture/README.md; removed the accidental wrong-path file; corrected PRD/AGENTS references |
| Complete request: do all three products have independent acceptance? | VERIFY | AP00017 tests no upper layers; OV00060 mixed-driver same-controller lifecycle; OV00065 headless install; Lantern00003 installed API/detach parity |
| Failure: stale controller revision could block emergency stop | FIX | Contract C/OV00064 require current execution identity/CAS but allow stop without fresh workflow revision; pending reconciliation explicit |
| Failure: UI extraction might form a dependency cycle | VERIFY | 22-node DAG checked; Lantern00003 requires OV00064/00060/00061, OV00065 consumes Lantern evidence, never reverse |
| Approach: old host PRD still sounded like nested cross-driver launch | FIX | AP00014 now describes native identity/delegation/job intent; managed headless processes belong to OV00059 |
| Missing check: extraction file allowlist omitted existing state consumers | FIX | Enumerated actual import consumers and source/test retirement paths in OV00058; every retired test requires mapped passing evidence |

## Slop pass

- Bloat: generated Module Location lists duplicated complete file trees. FIX: removed redundant lists; retained explicit additional source/test locations and the existing reference roster where needed.
- Boilerplate: identical success metrics obscured each PRD's purpose. FIX: generated PRDs now lead with their own concrete acceptance outcome.
- Defensive impossibility: checked credential/bootstrap, stale-control and crash cases; these are reachable process/file boundaries, not imaginary branches.
- Single-caller abstraction: two subprocess protocols serve actual independent distributions and test fixtures; no daemon/broker/general workflow framework was introduced.
- Comment paraphrasing/framework tests: no production code/comments/tests were added. Future tests assert state/process/render outcomes, not only mocked calls.

## Pass two and limitations

Rechecked the fixes, source references, headings, capability gates and dependency direction. The final held-PRD check found two inherited grounding issues: a literal capability identifier parsed as a code symbol, and placeholder migration/acceptance IDs. Corrected their wording and replaced the obsolete workflow version-range assumption with the tested portable-package/controller pins. Rechecked the affected held PRDs.

KNOWN: implementation and actual host probes are future work. Fake process/fixture acceptance is explicitly separate from real native isolation/interception certification. Documentation checks cannot prove runtime behavior.

KNOWN: Lantern is a provisional working name; an optional preference was requested and has not been answered. Planning is reversible; no namespace availability or publication is claimed.

Total: 13 doubts; 9 fixed, 2 verified/dismissed, 2 known limitations above.

## Validation evidence

- 20 revised/new backlog PRDs and five amended held PRDs passed create-prd grounding with no failing rows.
- Standard-template heading order, no unresolved guess markers, and <=200 physical lines checked for all20.
- Changed planning-document local links resolve; backlog IDs are unique.
- Dependency graph checked acyclic (22 nodes including unchanged robustness work).
- All119 original P00–P12 task IDs preserved; accepted-plan SHA-256 matches coverage.
- Expanded source inventory unchanged below its ownership introduction.
- OV00062/00063 hashes match the pre-task snapshot.
- agent-plugins validator: validated2 plugin packages and3 skills (existing packages; Autopilot is not implemented yet).
- Documentation whitespace checked. Source claude-autopilot remains unchanged.
- No runtime test suite is claimed; this task changes planning/instructions only.

## Unresolved questions

No blocking architecture question. Provisional TUI naming remains optional.
