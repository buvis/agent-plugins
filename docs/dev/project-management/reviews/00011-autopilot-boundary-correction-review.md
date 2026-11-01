# Plugin/runtime boundary correction review

> Historical assessment. The 2026-10-25 three-layer redesign supersedes earlier ownership conclusions: Autopilot/controller owns workflow truth, OVCAQ owns execution, Lantern owns presentation. Preserve the source observations; use the current design and PRDs for implementation.

Reviewed 2026-10-25 using the review-with-doubt protocol. Two passes; documentation changes only.
Scope: corrected design, six plugin PRDs, five OVCAQ PRDs, discovery/coverage/cutover reconciliation and prior audit dispositions.

Result: 10 doubts — 6 fixed, 2 verified/dismissed, 2 implementation/storage limitations documented.

## Doubts and actions

| ID | Category | Finding | Resolution/evidence |
| --- | --- | --- | --- |
| D1 | FIX | The 00057 prerequisite paragraph still required a plugin contract bundle after a literal text replacement missed reviewed wording. | Replaced the complete condition, retained predecessor/exit semantics, asserted only 00061 needs an external plugin artifact. 00058 is independently executable after 00057. |
| D2 | FIX | A managed probe created by 00016 could become its own eligibility prerequisite. | 00012 supplies the initial direct runtime probe with exact command/major/capability/exit behavior; 00016 creates the later full compatibility tool. |
| D3 | FIX | Runtime record-store commits change HEAD and could invalidate every successful verification. | 00060 preserves code and record identities separately, requires allowed-path/tree/command proof and tests both safe reuse and hidden-code-change rejection. |
| D4 | FIX | A generic review API could accidentally absorb plugin staging, grouping or policy content. | 00013/00015 own semantics; 00059 only validates and persists prepared proposals. OVCAQ owns its API; external plugin policy is data supplied at run binding, not bundled content. |
| S1 | FIX | The second backend and shared mode-owner protocol added machinery contrary to the original extraction. | Removed backend/writer/lifecycle/owner-marker/effort-router files from plugin PRDs and reused OVCAQ’s existing runtime locks and identity. |
| S2 | FIX | Five consolidated reference documents encouraged an unnecessary rewrite of 59 source files. | Preserved all 59 skill-relative paths with explicit locations/provenance and per-file/section assertions; retained the eighteen persona files. |
| V1 | VERIFY | Correcting the plan might invalidate the accepted coverage authority or leave a dependency cycle. | Recomputed the accepted-plan hash, checked its coverage reference and verified the graph is acyclic with independent plugin and OVCAQ lanes until 00016. |
| V2 | VERIFY | Rewriting PRDs might overwrite recent review fixes. | Compared snapshots before publication. Kept OVCAQ frontmatter tuning, cf8be72 provenance, exact CLI spelling, ordered tasks, row ownership and prerequisite exit behavior; removed only superseded architecture. |
| K1 | KNOWN | Actual host interception/session identity and runtime implementation are not proved by authoring checks. | Future PRDs contain real installed-host and public-runtime gates; no implementation or compatibility success is claimed here. |
| K2 | KNOWN | OVCAQ planning is local and ignored by git. | Preserved the existing policy; did not force-add planning or publish it. Worktree instructions explicitly require copying those documents. |

## Six-question check

1. Least confidence: real native host capability remains K1; refusal is explicit for unavailable enforcement.
2. Assumptions: checked source reference/persona inventories, current config readers, the authoritative state-store seam and prerequisite bootstrap. D1–D4 resolve discovered mismatches.
3. Completeness: both repositories now agree that OVCAQ replaces the runtime only; plugin local use produces artifacts and cannot complete a durable PRD lifecycle. Record-store ownership and held cutover acceptance are explicit.
4. Practical failures: scoped tests use temporary roots; replay, state/identity errors, interrupted record commits, ignored files and unrelated index changes have named future tests. No local backend fallback remains.
5. Retrospective: the simpler boundary removes a second runtime and cross-mode lock. File-for-file references reduce unnecessary content rewriting.
6. Missing checks: all authored PRDs pass grounding with existing code/policy citations, template/size/task checks, links and dependency checks. Runtime/host tests belong to implementation, not this documentation change.

## Slop check

- Bloat: removed the two-backend protocol and five-file content consolidation rather than adding another compatibility layer (S1/S2).
- Defensive impossibility: deleted cross-mode ownership guards once only one runtime remained; retained CAS/identity/crash checks for reachable multi-process failures.
- Single-caller abstraction: a thin CLI client is justified by the external-runtime boundary; there is no generic backend interface or RPC framework.
- Comment paraphrasing: no production comments were added. Modules now name concrete commands/data exports instead of claiming generic backend responsibility.
- Framework tests: planned assertions cover actual forbidden writes, artifact behavior, source-content preservation and git/process effects; schema checks cover real exchanged contracts.

## Second pass

Checked D1’s exact edited prerequisite line, D2’s bootstrap independence, the changed file allowlists, all new source/reference locations, canonical contract producer ownership and the accepted-plan digest. Each saved PRD remains below 200 lines and retains its standard template and required review gates. Prior audit text is preserved as historical evidence with correction dispositions, rather than silently rewritten as an implementation pass.

No runtime code, installation, publishing, source retirement or held PRD activation is part of this correction.
