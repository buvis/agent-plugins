# Autopilot port planning corrections — 2026-10-25

Scope: repair the planning defects from the completeness audit. Implementation, real-host certification, publishing and retirement are not performed here. The user authorized supported corrections and requested material decisions one at a time with at least three options.

## Disposition

| Finding | Status | Correction |
| --- | --- | --- |
| F1 weakened review policy | Fixed in planning | AP 00012 declares full/fast-track mandatory and conditional roles, solo's real review, source retries/escalations and rubric namespaces; AP 00015/00020 enforce the same rules. |
| F2 findings mistaken for review completion | Fixed in planning | Explicit clean/failed reviewer results, source/input bindings and caller-supplied expected context; AP 00020 verifies actual controller jobs and native identity. Clean reviews need no invented findings. |
| F3 source-dependent CI | Fixed in planning | Commit source-derived provenance and fixtures; ordinary target CI has no source/home/network dependency. A separate explicit maintainer command verifies the source capture at its pin. |
| F4 incomplete coverage mechanism | Fixed in planning | Independent expected source inventory plus destination behavior/regression mappings, actual delivery owners/scenarios and profile-specific evidence. Headings or unavailable status cannot prove parity. |
| F5 Claude-free completion evidence | Fixed in planning | User selected Codex + Gemini. AP 00014 owns native host support, OV 00059 the Gemini driver/provider attribution, OV 00060 real supervision evidence and AP 00017 standalone/managed certificates; cutover and retirement require both receipts. |
| F6 escaped package dependencies | Fixed in planning | Classify resource edges and reject escaped runtime resources; test archive closure with source/home inaccessible. Informational citations and declared external capabilities are distinct. |

The [corrected foundation design](../designs/00012-autopilot-package-contract-v1-design.md) supersedes its historical approval. Its terminal result now refuses approval until the amended contract passes a new design review. AP 00012 moved from wip to hold in another session during this work; its edited content was verified intact and no hold was activated here.

Added [source retirement PRD 00370](../../../../../claude-autopilot/docs/dev/project-management/prds/hold/00370-retire-source-package-v1.md) in hold, with exact source/consumer/evidence checks and an already-authorized target-ledger prerequisite. It does not authorize remote archival or publication. Updated the target port plan and OVCAQ's architecture/cutover/release requirements to name this owner and the stronger evidence gate.

## Accepted decision

The user's “ok” accepts the recommended Codex + Gemini profile. Codex implements and Gemini supplies the independent provider's doubt voice, including Eve when required. Every resolved role retains its rubric, input restrictions and fresh context; Carl's source availability predicate still applies. This preserves the source diversity guard without requiring Claude. Codex-only is not the required completion profile; the mixed Claude canary remains compatibility coverage. Real standalone and managed certification must exclude Claude runtime/configuration/credentials and source/author-home runtime dependencies, and record exact artifact and execution identities. Missing capabilities prevent certification but do not block unrelated implementation. The dependent local, OVCAQ and source-retirement plans now state this choice.

## Skeptical review

Applied review-with-doubt, two passes. Nine doubts: six FIX, one VERIFY dismissed, two KNOWN. The second pass checked the corrections themselves.

| Lens / doubt | Disposition | Evidence or action |
| --- | --- | --- |
| Least confident: source roles and rubric names could be simplified incorrectly | FIX | Re-read pinned full/fast-track/solo procedures and rubrics; retained conditional roles and mapped historical doubt labels to source D1–D5 by namespace. |
| Assumption: source checkout can be required by ordinary target CI | FIX | Source capture is a maintainer operation; target checks consume committed inventories/fixtures. |
| Complete request: Claude independence still has a product-policy choice | KNOWN at review; resolved afterward | User accepted Codex + Gemini; preserved source provider diversity and assigned the driver, native support and real certification work explicitly. |
| Practical failure: the PRD changed lifecycle buckets during edits | VERIFY, dismissed | Located held AP 00012, compared its full content with the edited snapshot, confirmed equality and repaired the audit link. |
| Approach: copied headings and a destination-generated roster cannot detect missing behavior | FIX | Separate source-derived expected IDs from destination mappings and require observable scenario evidence. |
| Missing validation: plans and fixtures cannot prove live host enforcement | KNOWN | Actual implementation/certification is future work; unavailable stays distinct from passed evidence. |
| Slop: original design repeated prior reviewer conversations and CI layout assertions | FIX | Replaced the active contract text with concrete interfaces, source rules and behavioral tests; retained prior review comments as explicitly historical. |
| Slop: proposed CI tests snapshot unrelated workflow steps and merely confirm mocks | FIX | Test the actual declared command and target-only behavior; preserve existing CI without a byte-level formatting snapshot. |
| Second-pass failure: stale terminal approval and readiness checker used before creation | FIX | Historical result no longer satisfies the design gate; source retirement creates/tests its checker before applying removal. |

## Validation

- Grounding passed for all eight changed local PRDs, both amended held OVCAQ PRDs and the new source retirement PRD: no blocking or unverified rows.
- After the provider decision, grounding passed again for all seven affected PRDs, including OV 00059/00060. All 25 local links across the 12 amended planning documents resolve; whitespace checks pass. The two pre-existing held OVCAQ PRDs remain approximately 200 lines (213 and 208); this amendment preserves their task structure.
- All ten local PRDs retain standard-template heading order, stay below 200 lines and contain no unresolved contract markers. Their dependency graph is acyclic; AP 00012 remains held.
- Local planning links resolve. Source PRD 00370 has no sequence collision. Whitespace checks pass in all three repositories.
- Validator unit tests: 12 passed. Existing Specflow and template packages validate.
- Full repository validation currently fails on the concurrently created partial plugins/autopilot directory because plugin.json is absent. This review changed planning documents only and leaves that implementation intact; it does not claim a green full-repository gate.

## Unresolved questions

None requiring a user decision. Implementation, renewed review of the amended AP 00012 design, actual host certification and the already-defined cutover/retirement gates remain. Planning coverage does not guarantee a host capability exists or that future implementation passes its checks.
