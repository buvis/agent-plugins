# Q&A log: 00010 split long validator functions

## Supplied choices and scope (2026-10-31)

- Source: developer's opening request for this worktree; no additional clarification was needed.
- Spec choices, verbatim: "Use the existing intake item to create a standard, requirements-first feature spec named 00010-split-long-validator-functions. Check for existing artifacts first."
- Scope, verbatim: "Split validate_manifest and validate_mcp into cohesive checks of at most 50 lines."
- Compatibility, verbatim: "Preserve their public interfaces, accepted/rejected inputs, validation order, diagnostics, and CLI behavior. Avoid unrelated cleanup or dependencies."
- Tests, verbatim: "Keep existing tests unchanged and passing. Add characterization tests where needed to prove behavior is preserved, running them against the original code first."
- Future caller, verbatim: "Preserve validate_manifest's API for the marketplace generator planned in 00008."
- Current stopping point, verbatim: "First prepare and review requirements, then ask for explicit approval and stop. Proceed through design and task approval in later turns. Do not implement before status opens the implementation gate. Never infer artifact approval from this prompt."
- Reading: feature refactoring, requirements-first, standard; no artifact is approved by the opening request. The existing intake item is the source and its idea.md stays byte-identical when moved to processed/.

## Execution constraints supplied for later phases (2026-10-31)

- Use Python `-B` or `PYTHONDONTWRITEBYTECODE=1`, the Python skills, and repository checks. Prepare `docs/dev/tmp/review-tools/gate.sh` from this worktree's CI and the review recipe, never another checkout's hardcoded gate. Run the gate and repository-wide helper status before every commit.
- Use conventional commits, one per task, without Co-Authored-By. Every feat/fix commit needs a `plugins/specflow/CHANGELOG.md` entry. New behavior or bug fixes need tests; a bug-fix test must fail against old code. This preservation spec does not authorize behavior fixes.
- Never rebase, force-push, or stash. Never edit approved hashed artifacts without reapproval. Write Outcome lines only under tasks; leave final completion criteria unchecked for fresh-session review.
- Claude is unavailable before Sunday, 2026-11-01, Europe/Prague. Keep 00008 and its host-test workspace untouched. Never modify master or another worktree.
- After implementation and green CI, push this branch and open a PR to master. Hand off `/autopilot:review-work-completion` to another fresh session; never run it in this work session.

## Discovery 2026-10-31

- Classification: existing-code repository, evidenced by `scripts/validate.py`, `scripts/test_validate.py`, and `tools/specflow/verify_release.py`.
- State: `feature/specflow-00010`, clean at entry, already at intended base `6c16d03d7f5e878a3033de747866c931edcf12bf`; no branch correction performed. Helper status found only the existing 00010 intake item, no matching spec, and no specs-folder problems. Other specs were read only through status; none were recovered or changed.
- Ratings: requirement clarity high (explicit preservation scope); scope breadth low (two functions); codebase impact medium (shared validator and release caller); problem complexity medium (order-sensitive equivalence). Standard is explicitly selected and warranted by behavior preservation and the public API.
- Read in full: root `AGENTS.md` and `CLAUDE.md` (imports AGENTS.md); `/Users/bob/.claude/AGENTS.md`; this intake's `idea.md`; `scripts/validate.py`; `scripts/test_validate.py`; `.agents/specflow.json`; `.github/workflows/validate.yml`; `ruff.toml`; `/Users/bob/.claude/projects/-Users-bob-git-src-github-com-buvis-agent-plugins/memory/review-work-completion-recipe.md`; `/Users/bob/.agents/skills/python-patterns/SKILL.md`.
- Workflow guidance read: `plugins/specflow/skills/spec-workflow/SKILL.md`, artifact/state contracts, standard profile, intake/requirements phases, AWS requirements guidance, review core and requirements lenses, requirements and intake-log templates, and state schema. These govern only this spec workflow.
- Skimmed: review `docs/dev/project-management/reviews/00003-aws-sources-catchup-review-01.md` (R9 and disposition); `tools/specflow/verify_release.py` (imports and full `check_manifests` caller); 00008 design/tasks API references found by repository search; remaining spec states via read-only helper status.
- Not examined: unrelated implementation subtrees and other worktrees, including the 00008 host-test workspace. No relevant nested instruction files or root steering were found for scripts or project-management docs. Fixture instruction files under tests are fixture data and outside the affected paths.
- Applicable constraints: root AGENTS.md requires independent packages, no dependencies for the validator, no credentials, and repository validation before completion. Global AGENTS.md authorizes routine reversible work but preserves explicit artifact gates and the fresh-session completion review. CLAUDE.md adds no rule beyond its root import. The supplied request bounds this turn to requirements and forbids changes to other specs.
- D1: At the intended base, AST source spans measure `validate_manifest` at 96 physical lines (61-156) and `validate_mcp` at 130 (303-432), matching R9. Both execute ordered checks through `require`, `load_object`, and related helpers. Manifest validation returns the parsed dictionary; MCP validation returns None. Errors are raised as encountered; some underlying exceptions can propagate and must not be silently normalized by extraction.
- D2: Current call sites found by `rg -n 'validate_manifest|validate_mcp' .` are `scripts/validate.py:main`, `scripts/test_validate.py:ValidatePlugin.check`, and `tools/specflow/verify_release.py:check_manifests`. The release caller imports both functions directly, catches ValidationError, and consumes the manifest return value. Main collects one ValidationError per plugin and reports errors in plugin order.
- D3: `docs/dev/project-management/specs/00008-host-integration/design.md` names `validate_manifest(plugin: Path) -> dict[str, object]`, ValidationError, and ROOT for a planned marketplace generator. No generator implementation exists in this checkout. Preserving the API needs no edit or prerequisite approval in 00008.
- D4: This worktree's CI uses Python 3.10, bytecode disabled, and eight checks: validator tests, package validation, release tests, contract tests, rule tests, review tests, rule inventory, release boundary. The review recipe warns about foreign-checkout gate paths, Python-version-dependent filesystem errors, bytecode pollution, and stale approvals after artifact edits. Those constraints apply when preparing implementation and its gate.
- D5: Baseline `python3 -B -m unittest discover -s scripts` passes 12 tests; `python3 -B scripts/validate.py` passes (2 packages, 4 skills). Tests use unittest, temporary template copies, and direct calls; existing coverage does not fully pin exact diagnostic order or both validators' return values. Characterization additions are deferred until the implementation gate opens and must run against original code before extraction.
- Pattern scan: existing small functions `require`, `load_object`, `is_string`, `contained_suffix`, and `validate_url` establish typed snake_case helpers and ordered direct checks. Their behavior is available for reuse; no framework or registry is needed by the request.
- Conditions checked: missing/empty/malformed files and objects, optional fields, limits, multiple errors, stdio and remote servers, path and URL boundaries, and default/explicit CLI use. Concurrency adds no requested capability; comparisons assume the same filesystem conditions. No performance, scalability, accessibility, or UI target is introduced by this internal refactor.
- Contradiction check: preserving tests permits additive characterization tests without modifying existing ones. Preserving the 00008 API does not require implementing 00008. A behavior-preserving refactor has no bug-fix fail-first obligation, but its characterization tests must pass before extraction. No material scope contradiction or unanswered domain question remains.

## Review: requirements.md 2026-10-31

- Target: `00010-split-long-validator-functions/requirements.md`; standard profile read from `.specflow.json`. Read the entire draft after reading the intake and this log as context. Comprehension pass found no material ambiguity beyond the explicitly sourced assumptions A1-A3.
- Completeness: full pass. Purpose, bounded scope, five sourced requirements, public contracts, error/order preservation, test evidence, constraints, risks, exclusions, and unresolved-question section cover the supplied request.
- Coherence: full pass. Every requirement serves the split or its compatibility proof; no conflict with unchanged tests, 00008 isolation, or the original behavior baseline. No contradiction or orphan criterion found.
- Integrity: full pass. Criteria are observable through source inspection or behavior tests; 50 physical lines is defined and matches R9. Function splitting, public signatures, Python 3.10, and test-before-refactor are supplied or repository constraints. No helper names, module architecture, or unsourced implementation mechanism is prescribed. A pre-review validation error was corrected by naming the intake directory rather than its idea.md file on Sources:.
- Feasibility: full pass. Five requirements remain one bounded refactor of two existing functions. Existing unittest fixtures, small validation helpers, and CI provide the required capability. No unavailable service or unbuilt 00008 implementation is assumed.
- Evolvability: full pass. The foreseeable marketplace caller is protected by REQ-002 and REQ-004; no registry or extension feature is invented. Extraction choices remain for design and are reversible.
- Confirmation of soundness: all five selected lenses ran in full and found no substantive finding. Raised/resolved/disputed/deferred/open: 0/0/0/0/0 at every severity. Skipped lenses: none. No open blocker; no clarification needed for actionability. This review records no artifact approval.
- Validation: requirements-phase helper validation passes. Repository validator and all 12 existing validator tests pass against unchanged production code. No characterization tests or implementation changes have been made in this phase.
- Approval remains pending. Next action: explicit developer approval of requirements; design and tasks remain missing, and implementation remains closed.

## Q1 - Requirements approval (2026-10-31)

- Question: Do you approve these requirements?
- Answer: "approved"
- Reading: explicit approval of requirements.md only; design and task approvals remain pending.
- Receipt: canonical SHA-256 `f278ac71bbbadce8013c197f1bc25f496efb154924017a751fc5fb3f8804f66b`, approved at `2026-10-31T10:22:53Z`, commit `6c16d03d7f5e878a3033de747866c931edcf12bf`, workflow `0.1.0`. Values copied from helper hash output.

## Design discovery 2026-10-31

- Re-read the approved requirements, intake, current state, root instructions, validator and existing tests, CI, and the release caller. Reuse searches covered check/validate plus manifest/mcp/author/stdio/remote, with known-present primitive names as controls. No alternate existing decomposition pattern was found.
- New affected paths are two proposed test modules under `scripts/`, already covered by root instructions. No new instruction scope applies; no upstream requirement changed. Python Testing guidance was read; the explicit no-dependency/unchanged-test constraints and repository unittest conventions take precedence over pytest-specific suggestions.
- Loaded design phase, AWS design, template, and the Tier 2 review references: triage, pre-pass, cardinal sins, checklist, techniques, stress tests, anti-patterns; review core was already loaded. A schema library is excluded by the dependency and exact-behavior constraints; no external technology choice or search is needed.
- The template plugin has no mcp.json; new MCP fixtures must create it explicitly. The full eight-command gate remains implementation preparation, not a claimed completed check in this design phase.

## Review: design.md 2026-10-31

- Target: 00010's design.md; domain: Python CLI/library validator; maturity: draft for approval. Tier 2 because there is more than one downstream consumer and this is maintained repository tooling. No Tier 3 trigger: public contracts are preserved, no cross-team coordination, new lock-in, or compliance scope. No tier upgrade occurred.
- Comprehension pass read the full draft and identified no material confusion. Signals: behavior-equivalence risk invokes premortem, hidden-coupling and asymmetric-risk checks; section imbalance invokes the section-weight audit. No isolated technique or required Tier 2 lens was skipped.
- Isolated pre-pass: one context-isolated reviewer received only the draft, approved-requirements summary, full cardinal-sins text, and severity instructions. It returned `[]`. Passes: 1; cardinal sins/blockers/non-blockers/questions: 0/0/0/0. No author fix or verification pass was needed. No Claude invocation occurred.
- Scripts: all three ran successfully with Python -B. Section-weight audit: Testing strategy 613 words, 4.8 times median, justified by the central preservation obligation and distinct case matrix; Open decisions 15 words, 0.12 times median, justified because none remain. Claim scan: one hit, "simple substitution" under Alternatives considered; it describes why a schema library cannot replace custom diagnostics, not an unmeasured quality commitment. Adversarial scan: zero signals or framing hits. No scan hit merits a finding.

### Checklist verdicts

| Item | Verdict | Evidence and reasoning |
|---|---|---|
| 027 Problem | Solid | Overview and Requirement traceability tie the split and tests to all approved criteria. |
| 028 Ownership | Solid | Context and constraints names Bob as the solo maintainer and operational owner. |
| 029 Constraints | Solid | Context states baseline assumptions, unchanged inputs/runtime, Python 3.10, and no dependencies; no new load or staffing commitment is introduced. |
| 030 Alternatives | Solid | Architecture and Alternatives considered compare in-place extraction, a new module/class, and a schema engine, including leaving code unchanged. |
| 031 Components | Solid | Architecture and Components specify one module, private responsibilities, and acyclic calls with explicit order. |
| 032 Data | Solid | Data model preserves JSON shapes and insertion order; no stored state or data lifecycle is introduced. |
| 033 Contracts | Solid | Components and Error handling preserve signatures, return values, exception semantics, CLI text/exit codes, and existing versioned schemas. No new API version is needed. |
| 034 Concurrency | Solid | Data and control flow preserves order; Error handling explicitly leaves filesystem races to existing operations rather than promising snapshots. |
| 035 Performance | Not applicable | Architecture adds bounded helper calls with no new traversal, storage, network, or throughput objective; existing file-size behavior is unchanged. |
| 036 Failure | Solid | Error handling covers load failures and propagated exceptions; Rollout gives concrete source/test backout with no data recovery. |
| 037 Observability | Solid | Context and Error handling retain CLI diagnostics and CI failures as signals for this local tool. No service telemetry is needed. |
| 038 Security | Solid | Security and privacy identifies plugin inputs and each preserved guard; no command execution or network access is added. |
| 039 Privacy | Not applicable | Security and privacy introduces no persistent personal data; all new fixtures are synthetic. |
| 040 Cost | Solid | Architecture and Context keep a dependency-free local process and existing owner; no recurring infrastructure cost is introduced. |
| 041 Deployment | Solid | Rollout retains the branch/PR and existing CI path; no topology or configuration migration exists. |
| 042 Migration | Solid | Rollout orders characterization before extraction and explains reverting the structural test with the implementation. |
| 043 Tests | Solid | Testing strategy distinguishes baseline-compatible behavior tests, structural checks, caller integration, and deterministic failure injection. |
| 044 Delivery | Solid | Rollout identifies the required intermediate states without drafting tasks or estimates before approval. |
| 045 Documentation | Solid | This design records interfaces and decisions; Module placement and Testing strategy specify workflow records, gate logs, and ownership. |
| 046 Risks | Solid | Risks and edge cases gives mitigations/fallbacks; Open decisions is explicit and approval remains pending. |
| 047 Consistency | Solid | Physical-line definition, paths, helper names and criteria agree throughout. Section outliers are justified above. |
| 048 Overengineering | Solid | Architecture rejects registries/state and keeps existing primitives; the new structural check proves an explicit requirement. |
| 049 Reversibility | Solid | Alternatives identifies reversible helper boundaries; public contracts and data are unchanged. |
| 050 Six-month reader | Solid | ADR-001/002 and the ordered flows explain why these boundaries and test phases were chosen. |
| 051 Reality | Solid | Read scripts/validate.py, scripts/test_validate.py, release check_manifests, template manifest, and CI; helpers, return consumption, ordering, and eight CI commands match. |

### Cardinal sins and additional techniques

- Cardinal sins checked: 053/055/060/063/064 are not applicable because no stateful write or schema migration is introduced; 054/066 pass because no credentials are present; 056 passes through named ownership; 057 through retained CLI/CI signals; 058 through explicit contracts without deferred concerns; 059 introduces no new consumption or processing loop beyond existing server iteration; 061 introduces no vendor; 062 introduces no authentication surface; 065 preserves the existing API and schema version; 067 has two ADRs with alternatives. None is raised.
- Premortem: eighteen months later, the refactor is blamed for rejecting a plugin that used a previously accepted optional value. The new helpers seemed equivalent, but a presence check became a truthiness check. Happy-path tests and broad exception assertions missed both the acceptance change and a changed first diagnostic. A Python-version difference then made the failure hard to reproduce. The design addresses this through explicit presence guards, complete-message tests, competing failures, original-code characterization, and same-interpreter comparison.
- Inverse problem/five-whys: the architecture optimizes reviewing ordered checks, matching the measured overlength problem and R9; it does not create an extension framework. Claim ladder/falsifiability: function length has an AST formula, and preservation is falsified by return, exception, output, ordering, or byte-difference tests. No performance number is asserted.
- Bias and anti-pattern scan: no appeal to authority, new stack, hidden store, deferred security/test concern, or analogy substitutes for evidence. The library alternative is rejected by explicit scope, not familiarity. The heavier testing section carries the primary risk mitigation.
- Negative space: missing files, null/empty values, Unicode/encoding, 64/65 limits, many servers, malformed containers, URL parsing, and filesystem errors are covered. Tenant quotas, clocks, retention, and vendor exit are not applicable to this unchanged local validator.
- Conway/bus factor: a single maintainer owns all pieces; no new coordination boundary appears. Helpers and this design reduce handoff dependence on the author's memory. Hidden coupling: diagnostic order, insertion order, return-object preservation, and interpreter behavior are explicit contracts, not accidental dependencies.
- Compression/surprise: the load-bearing core is the helper responsibility table, original ordered flow, and baseline-first test matrix. The less obvious decision is preserving uncaught malformed-value exceptions and separating structural tests from preservation tests; both are explained.
- Time horizon: day one uses gates and PR checks; day one hundred requires no daily service operation; day one thousand preserves the 00008 API and supports private extraction; retirement leaves no stranded state. Counterfactuals relevant to this Tier 2 change (less developer time, no new technology) favor the selected in-place extraction; infrastructure-region/vendor constraints do not apply.
- Assumption graph/asymmetric risk: baseline correctness is not asserted, only preservation of observed behavior; baseline identity and function lengths were verified. The shared CI blast radius is addressed by original-code evidence and the full gate, not by changing policy while refactoring. Decision quality rests on current code and constraints, not a claimed successful implementation.

### Stress scenarios

- Tenfold input: same JSON loading and server iteration; no new traversal or cache. Existing resource limitations are preserved.
- Dependency unavailable: no remote dependency; local read failures follow the existing exception path and diagnostics.
- Revert in three months: restore the validator and revert the structural check together; no data migration.
- Original author leaves: typed interfaces, responsibilities, ordered flow, and test matrix remain in the repository.
- Security incident: rule changes can target a private check in separate work; this spec does not authorize a policy change.
- Source of truth questioned: baseline code supplies behavior; requirements supply obligations; tasks will supply progress.
- Cost doubles: no introduced hosting or service expense; existing CI/local-run cost remains the relevant boundary.
- Auditor asks for evidence: characterization Outcomes and gate/CI logs provide behavior-preservation evidence; no regulated control claim is introduced.
- Future breaking schema: separate work and reapproval must define policy/version changes; no schema evolution is hidden in this split.
- Noisy neighbour: no multi-tenant service is introduced; inherited local-process resource limits are unchanged.

### Recap

- No findings raised, fixed, disputed, deferred, or open at any severity. All Tier 2 checklist items, cardinal sins, applicable techniques, ten stress scenarios, and three scripts were considered. Not-applicable subjects are explained above; no required review step was skipped.
- Explicit confirmation of soundness is limited to this document review: the design covers the approved requirements and the examined repository facts; it is not proof of implementation equivalence. Actionability has no unresolved blocker or missing domain input.
- Design-phase helper validation passes. Repository validator and all 12 existing validator tests pass against unchanged production code. No characterization tests, structural tests, gate script, or implementation changes have been made yet.
- Requirements approval remains unchanged. Design approval is pending; tasks remain missing and implementation closed.

## Q2 - Design approval (2026-10-31)

- Question: Do you approve the design?
- Answer: "yes"
- Reading: explicit design approval; task approval remains pending and implementation remains closed.
- Receipt: canonical SHA-256 `7b70d383092a743f99064b3dbf77f9512b960462c45459b4799b76475bb5da0d`, approved at `2026-10-31T11:06:31Z`, commit `6c16d03d7f5e878a3033de747866c931edcf12bf`, workflow `0.1.0`; upstream requirements hash `f278ac71bbbadce8013c197f1bc25f496efb154924017a751fc5fb3f8804f66b`. Copied from helper hash output.
- Code baseline: helper captured scripts/validate.py hash `2756144e5c5a6db44b4089bc206e67d36ed45ad3b11201f80b01cfa0acc2fbe6`; both planned test modules are missing. Recorded exactly in approvedCode, with no other spec changed.

## Task planning and review 2026-10-31

- Read requirements and design in full, the task-phase reference and template, this log, and current state. Helper status/reconcile dry-run matched the reviewed artifacts before recording design approval. The implementation gate remains closed until explicit task approval.
- Extraction from approved artifacts: REQ-001 requires bounded cohesive functions; REQ-002/003 preserve manifest/MCP behavior; REQ-004 preserves callers, CLI and read-only inputs; REQ-005 requires original-code characterization, unchanged tests and full verification. Implementation placement is one edited validator and two new test modules. Reuse is existing typed primitives, unittest fixtures, release checks and CI; no new instruction scope applies.
- Six tasks follow the design's rollout: T-001 manifest characterization and its gate support; T-002 MCP characterization; T-003 CLI characterization and the completed original-code corpus; T-004 manifest extraction; T-005 MCP extraction; T-006 structural acceptance and final verification. The three characterization units are a capability split derived from the design's test matrix. Their dependency chain reuses one fixture module and keeps all baseline evidence before either production edit. The design explicitly orders manifest before MCP and the structural check after both.
- Each task was checked against all five sizing rules: one named outcome, bounded file slice, exact contracts and owned verification; separable outcomes split by capability; each intermediate state passes without an unfinished sibling; split scopes and dependencies rechecked; no unsplittable planning blocker. T-001's untracked gate is verification support for its baseline evidence, not another production capability. There is no coupled multi-file production task: each extraction stays in validate.py, with caller interfaces unchanged. T-006 adds only structural tests and records final evidence, so production fixes cannot silently broaden its scope.
- Coverage review: all 15 numbered requirements criteria have task owners. Each design placement row is covered. T-004 owns the manifest portion of the final line-limit contract; MCP remains original until T-005, as the approved rollout permits. T-006 verifies the completed limit. Characterization assertions stay unchanged after T-003, and existing tests stay unchanged throughout.
- Contract check: all 14 Contract lines were programmatically confirmed as verbatim excerpts from approved design.md. Public and private signatures copied in task details match the design. AST inspection reconfirmed the original 96-line manifest and 130-line MCP premises; later task execution must recheck them at its dependency boundary.
- Validation cleanup: removed backticks around non-path names on Location lines so they cannot be mistaken for placement paths; named the fresh-session workflow without a leading slash so it cannot be mistaken for a filesystem link. These fix task formatting only; no approved upstream artifact was edited. Task validation now reports valid, with no placement-drift or portable-link warning.
- Working-practice review: no implementation or new tests before task approval; bytecode disabled; managed Python 3.10; worktree-local eight-command gate and repository helper status before every commit; one conventional commit per task. Planned test/refactor commits introduce no behavior changes requiring feat/fix changelog entries. The final task includes compatibility evidence and task-owned cleanup; push/PR/green CI and fresh-session review follow the six commits. Every completion box stays unchecked in this work session, and Outcome fields belong only to tasks.
- Requirements/design conflicts: none. No new material assumption, unresolved decision, or risk beyond the approved diagnostic-order and edge-case preservation risks. Review has no open finding or skipped sizing check. Task approval is pending; no task is checked and no implementation gate is open.

## Q3 - Task approval (2026-10-31)

- Question: Do you approve the task plan?
- Answer: "approved"
- Reading: explicit task-plan approval; implementation may start when helper status opens its gate.
- Receipt: canonical SHA-256 `35b839d8285e9e92ad0c9daea6109bd4812749c134c93997401318a3e5929bb7`, approved at `2026-10-31T11:11:37Z`, commit `6c16d03d7f5e878a3033de747866c931edcf12bf`, workflow `0.1.0`; upstream hashes copied from helper output into state.
