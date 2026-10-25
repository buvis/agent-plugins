# Autopilot port planning corrections — 2026-10-25

Scope: repair the planning defects from the completeness audit. Implementation, real-host certification, publishing and retirement are not performed here. The user authorized supported corrections and requested material decisions one at a time with at least three options.

## Disposition

| Finding | Status | Correction |
| --- | --- | --- |
| F1 weakened review policy | Fixed in planning | AP 00012 declares full/fast-track mandatory and conditional roles, solo's real review, source retries/escalations and rubric namespaces; AP 00015/00020 enforce the same rules. |
| F2 findings mistaken for review completion | Fixed in planning | Explicit clean/failed reviewer results, source/input bindings and caller-supplied expected context; AP 00020 verifies actual controller jobs and native identity. Clean reviews need no invented findings. |
| F3 source-dependent CI | Fixed in planning | Commit source-derived provenance and fixtures; ordinary target CI has no source/home/network dependency. A separate explicit maintainer command verifies the source capture at its pin. |
| F4 incomplete coverage mechanism | Fixed in planning | Independent expected source inventory plus destination behavior/regression mappings, actual delivery owners/scenarios and profile-specific evidence. Headings or unavailable status cannot prove parity. |
| F5 Claude-free completion evidence | Partly addressed; one decision pending | Separate implementation readiness from real-host certification and require passed receipts at cutover. The required non-Claude provider configuration still needs the user's ruling. |
| F6 escaped package dependencies | Fixed in planning | Classify resource edges and reject escaped runtime resources; test archive closure with source/home inaccessible. Informational citations and declared external capabilities are distinct. |

The [corrected foundation design](../designs/00012-autopilot-package-contract-v1-design.md) supersedes its historical approval. Its terminal result now refuses approval until the amended contract passes a new design review. AP 00012 moved from wip to hold in another session during this work; its edited content was verified intact and no hold was activated here.

Added [source retirement PRD 00370](../../../../../claude-autopilot/docs/dev/project-management/prds/hold/00370-retire-source-package-v1.md) in hold, with exact source/consumer/evidence checks and an already-authorized target-ledger prerequisite. It does not authorize remote archival or publication. Updated the target port plan and OVCAQ's architecture/cutover/release requirements to name this owner and the stronger evidence gate.

## Pending decision

Which execution configuration must earn the Claude-free certificate: Codex-only, Codex plus Gemini, or both? All retain the required review lenses and isolated contexts. Source review-work-completion explicitly adds another provider's doubt voice when Codex implemented the work, so Codex-only needs an explicit provider-policy redesign. That guard remains preserved while the question is pending. No implementation PRD asks an unattended agent to make this choice.

## Skeptical review

Applied review-with-doubt, two passes. Nine doubts: six FIX, one VERIFY dismissed, two KNOWN. The second pass checked the corrections themselves.

| Lens / doubt | Disposition | Evidence or action |
| --- | --- | --- |
| Least confident: source roles and rubric names could be simplified incorrectly | FIX | Re-read pinned full/fast-track/solo procedures and rubrics; retained conditional roles and mapped historical doubt labels to source D1–D5 by namespace. |
| Assumption: source checkout can be required by ordinary target CI | FIX | Source capture is a maintainer operation; target checks consume committed inventories/fixtures. |
| Complete request: Claude independence still has a product-policy choice | KNOWN | Provider diversity is material; asked one three-option question and preserved the source guard pending the answer. |
| Practical failure: the PRD changed lifecycle buckets during edits | VERIFY, dismissed | Located held AP 00012, compared its full content with the edited snapshot, confirmed equality and repaired the audit link. |
| Approach: copied headings and a destination-generated roster cannot detect missing behavior | FIX | Separate source-derived expected IDs from destination mappings and require observable scenario evidence. |
| Missing validation: plans and fixtures cannot prove live host enforcement | KNOWN | Actual implementation/certification is future work; unavailable stays distinct from passed evidence. |
| Slop: original design repeated prior reviewer conversations and CI layout assertions | FIX | Replaced the active contract text with concrete interfaces, source rules and behavioral tests; retained prior review comments as explicitly historical. |
| Slop: proposed CI tests snapshot unrelated workflow steps and merely confirm mocks | FIX | Test the actual declared command and target-only behavior; preserve existing CI without a byte-level formatting snapshot. |
| Second-pass failure: stale terminal approval and readiness checker used before creation | FIX | Historical result no longer satisfies the design gate; source retirement creates/tests its checker before applying removal. |

## Validation

- Grounding passed for all eight changed local PRDs, both amended held OVCAQ PRDs and the new source retirement PRD: no blocking or unverified rows.
- All ten local PRDs retain standard-template heading order, stay below 200 lines and contain no unresolved contract markers. Their dependency graph is acyclic; AP 00012 remains held.
- Local planning links resolve. Source PRD 00370 has no sequence collision. Whitespace checks pass in all three repositories.
- Validator unit tests: 12 passed. Existing Specflow and template packages validate.
- Full repository validation currently fails on the concurrently created partial plugins/autopilot directory because plugin.json is absent. This review changed planning documents only and leaves that implementation intact; it does not claim a green full-repository gate.

## Unresolved questions

Which non-Claude provider configuration must pass certification before the port is declared complete?
