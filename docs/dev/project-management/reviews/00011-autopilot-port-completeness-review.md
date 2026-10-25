# Autopilot port consistency and completeness review

Reviewed 2026-10-25. Verdict: **revise the foundation design before implementing its contracts; the planned work does not yet establish Claude independence or complete behavior coverage.**

Follow-up: the user authorized corrections. [Resolution record](00011-autopilot-port-corrections.md) tracks the amended plans and remaining provider-policy decision. Findings and line numbers below describe the audited revision, whose hash is recorded under Evidence; they are not claims that the amended text is unchanged.

The three-layer architecture is coherent. The immediate defects are in its translation into the active AP 00012 design and in the completion evidence. This is a planning audit, not a runtime certification or the fresh-session PRD work-completion review. No existing plan, implementation, installation or consumer was changed.

## Evidence and scope

- Read the port assessment, expanded inventory, authoritative three-layer design, AP 00012 design, all ten AP PRDs and prior planning/backlog reviews. Cross-checked the relevant OVCAQ extraction, mixed-driver, supervision and held cutover requirements, plus Lantern's installed-parity requirement.
- Compared the review rules with source commit `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48`; source HEAD still equals that pin. Verified the source roster: 11 skills, 59 skill references, 18 personas.
- Counted 1,034 expanded inventory rows: 212 CLI, 11 skill, 35 runner, 149 option, 16 state operation, 520 behavior-section and 91 helper rows. The separate P01–P11/R01–R31 matrix also remains required.
- Mechanically checked local eligibility dependencies. They are acyclic and select in this order: `00012, 00013, 00014, 00015, 00018, 00019, 00020, 00021, 00016, 00017`. Higher-numbered dependencies are handled by eligibility; renumbering is unnecessary.
- Rechecked the current [Agent Plugins specification](https://agent-plugins.org/specification), [client-extension contract](https://agent-plugins.org/plugin-authors/client-extensions) and [Agent Skills specification](https://agentskills.io/specification). Portable discovery covers skills and MCP; client hooks and native session enforcement need separate implementation evidence. Keeping an optional Claude adapter is compatible with removing Claude as a dependency.
- Spot-checked active consumers in the central marketplace, agent-skills documentation, shell launcher and authoritative global instructions. They still reference the source, as expected before cutover. This was not a new exhaustive portfolio retirement scan.
- AP 00012 design SHA-256 at review: `55a225858114a5c7da4ff48f8d1f6ce77f454507ce577412cd80d84e99afe735`. The planning tree was already uncommitted; findings refer to the inspected working files.

## Findings

### F1 — HIGH: the foundation policy removes required review lenses

Evidence: [AP 00012 design](../designs/00012-autopilot-package-contract-v1-design.md), lines 169–179, defines fast-track `required_reviewer_jobs: ["alice"]` and solo with no required reviewer or artifact.

That conflicts with the authoritative design, AP 00015/00020 and the standing review rule. At the pinned source, `skills/fast-track/SKILL.md` § Roster requires consensus, blind, doubt, Codex and conditionally available Gemini lanes. `skills/run-autopilot/references/lane-solo.md` § Review requires one zero-context consensus pass, validates all-clear output, and escalates failed review. Solo is a reduced review, not no review.

Consequence: the foundation can publish a policy and fixtures that certify Alice-only fast-track or completely unreviewed solo work. AP 00020 then has to contradict or revise the supposedly frozen contract.

Required correction: derive each lane's required and conditional roles, artifacts, rubric coverage, retries and escalation rules from the pinned procedures. Keep the user-required full/fast-track fresh-session boundary. Add negative fixtures for every missing mandatory lens and for solo with no review; retain a valid solo all-clear case. Preserve conditional source behavior rather than making optional providers universally mandatory.

### F2 — HIGH: review evidence confuses findings with completed reviews

Evidence: [AP 00012 design](../designs/00012-autopilot-package-contract-v1-design.md), lines 228–300. The complete-cycle fixture requires `findings` from every required reviewer; missing-lens is detected by a reviewer having no finding. The evidence shape contains no per-reviewer completion results or reviewed-input binding. Its stale-binding case only changes the policy digest.

A successful reviewer may find zero defects. The source solo runbook explicitly accepts an all-clear with zero finding rows. Under the planned fixture rules, a clean full review is indistinguishable from an absent lens. Conversely, a finding labeled with a reviewer name is not proof that the reviewer ran against the current input. Reusing evidence after changing the PRD/code leaves the policy digest unchanged.

Required correction: represent reviewer results separately from findings, including explicit clean outcomes, result/artifact references and reviewed-input identities. Bind those result references to controller job/session facts in AP 00020; keep actor/revision authorization in the controller envelope. Add fixtures for a clean complete roster, absent/failed reviewer, mislabeled result, stale PRD/code with unchanged policy, and missing required rubric verdicts. AP 00012's own PRD already requires stale-input rejection; implement that meaning rather than substituting policy-version mismatch.

### F3 — HIGH: the specified CI job cannot run its provenance tests

Evidence: [AP 00012 design](../designs/00012-autopilot-package-contract-v1-design.md), lines 63–75, 368–401 and 468–472. Tests run `git -C <source_path> show <pin>:<path>`, where the source path is `/Users/bob/git/src/github.com/buvis/claude-autopilot`. Missing source is explicitly a hard failure. The proposed Ubuntu job checks out only this repository and installs uv.

Consequence: a clean CI runner lacks both that path and the source repository. The specified test job fails even if the portable package is correct. Skipping those assertions would conceal the failure instead of proving the port.

Required correction: separate source-based provenance generation from ordinary target tests. Commit the necessary pinned inventories and characterization fixtures so target CI is self-contained. If independent source revalidation remains a mandatory CI gate, explicitly fetch/check out the exact pin into a configurable temporary path and supply that path to the audit. Prove the ordinary suite in a fresh target-only checkout.

### F4 — HIGH: the planned coverage mechanism does not cover the behavior inventory

Evidence at audit: [AP 00012 PRD](../prds/hold/00012-autopilot-package-contract-v1.md), then in wip at line 31, requires an acceptance owner for every asset/helper/behavior row. Its [design](../designs/00012-autopilot-package-contract-v1-design.md), then lines 78–129 and 502–511, instead defines a file-based map with three generic acceptance-test names. Preserved content is checked by heading equality; gated-unavailable rows are excluded from the content existence assertion. There is no binding from the 1,034 expanded IDs to destination operations, delivery PRDs and behavioral evidence.

AP 00015 and AP 00017 promise later source-behavior coverage, so the intent exists. The frozen foundation data model does not provide the ledger those checks need. A document can retain every heading while losing a default, failure rule, option or mandatory instruction. Likewise, an indefinitely unavailable capability can remain represented without ever being delivered.

Required correction: keep file provenance, and add an explicit behavior ledger covering the principal matrix, expanded IDs, configuration/state-field mappings and code-only discoveries. Each row needs a destination owner/repository, delivery PRD, interface or procedure, acceptance scenario and evidence status. Several rows may share a meaningful test. Freeze the expected source-ID set independently of the destination map so omissions fail. Temporary unavailability must stay incomplete for the release profile that promises the feature. Source regression tests need retained/replaced/justifiably obsolete dispositions, not just copied-document counts.

### F5 — HIGH for completion: no acceptance gate proves operation without Claude

Evidence: [AP 00016](../prds/backlog/00016-autopilot-controller-integration-v1.md), line 111, uses distinct fake native sessions. [AP 00017](../prds/backlog/00017-autopilot-profile-conformance-v1.md), lines 30–38, removes OVCAQ/Lantern and probes real hosts only where available. The three-layer design and OV 00059 explicitly require a Codex-build/Claude-review scenario.

These are useful tests, but none proves that the complete workflow works with Claude absent. The approved unavailable/refusal policy is honest and should remain: it lets implementation progress without inventing host support. It also means completing the implementation PRDs is not sufficient evidence that the user's portability objective has been achieved. A mixed-driver canary that still uses Claude cannot establish Claude independence.

Required correction: add a distinct completion/release gate for at least one real non-Claude host. Exercise an installed, relocated package through build, fresh isolated review with every required lens, rework, completion, records and refusal cases with Claude binaries, credentials, private configuration and the old source checkout unavailable. Bind the result to exact package/host versions and record actual invocations. Standalone must also work without OVCAQ/Lantern. Add the corresponding managed canary before claiming unattended parity. Missing prerequisites leave this gate unpassed without blocking unrelated implementation work.

Keep optional Claude compatibility assets. Detect accidental Claude dependencies in shared procedures, helpers and controller code; do not use a blanket ban on the word "Claude" that would reject valid adapter documentation or provenance.

### F6 — MEDIUM: the foundation's containment test accepts outside-package links

Evidence: [AP 00012 design](../designs/00012-autopilot-package-contract-v1-design.md), lines 507–514, allows a relative link to resolve to "a path outside this plugin" and calls the existing validator an archive-boundary check. The validator checks package filesystem containment and metadata; it does not follow Markdown instructions or determine their runtime resource dependencies.

Consequence: an installed package can pass those tests while a skill's required helper/reference still lives in the source checkout. Later AP 00017 relocation tests are stronger, but the foundational assertion currently permits the defect they must eliminate.

Required correction: classify links as required packaged resources, declared external capabilities, or informational provenance. Require all packaged resources to resolve within the distributed root, and test their closure from the archive with source/monorepo access removed. External citations may remain external; they must not substitute for shipped runtime resources.

## What the plan already gets right

- One workflow controller serves standalone and supervised sessions; helpers do not create another writer.
- Process supervision and TUI presentation have separate owners and distribution boundaries.
- Typed mutations, replay receipts, execution leases, crash recovery, custody and pre-action enforcement are explicit.
- Full/fast-track review requirements and code-selected solo escalation are preserved in the authoritative architecture and later PRDs. F1 is a contradiction in the foundation design, not a reason to redesign those boundaries.
- Fake-host evidence and real-host certification are explicitly distinguished. F5 strengthens the objective's completion gate without revoking the accepted record-and-refuse policy.
- Managed execution, waves, TUI parity and cutover are assigned beyond this repository. Completing AP 00012–00021 alone does not complete that larger migration.

## Completion boundary

Before freezing AP 00012 contracts, resolve F1–F4 and align its containment assertion with F6. Before calling the port Claude-independent, pass F5. Before retiring the source, require all promised inventory dispositions and the existing cross-repository/canary gates, refresh executable consumer discovery, and create/link the source retirement PRD promised by the port plan. No such retirement PRD was found in the source's current backlog/wip/hold scan. Publishing and source removal remain separate authorized actions.

No plan can guarantee future implementation correctness. A complete behavior ledger, passing source-derived tests, clean distribution tests and real non-Claude execution can make the claim auditable and substantially stronger than the current plan.

## Validation performed

- `python3 scripts/validate.py`: passed; 2 existing packages, 4 skills including maintainer skills.
- `python3 -m unittest discover -s scripts`: 12 tests passed.
- Local PRD dependency traversal: passed; order recorded above.

These are baseline repository checks. Autopilot runtime code is not implemented here, so they do not certify the port. No speculative tests or runtime code were added by this review.
