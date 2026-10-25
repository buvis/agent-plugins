# Design: Autopilot package and review artifact contracts (PRD 00012)

Status: corrected 2026-10-25 after the port-completeness review. The earlier
review result applies to the previous text, not this amendment. Reconcile any
in-progress implementation and re-run the design gate before freezing these
contracts. No completed implementation review is claimed here.

## Architecture fit

Follow the three-layer design in designs/00011-autopilot-standalone-design.md.
Autopilot owns content, evidence policy and one later bundled controller;
OVCAQ owns supervision; Lantern owns presentation. AP 00012 supplies the
contracts and source evidence consumed by both the content and controller
workstreams. It does not implement either upper layer or the controller.

The existing repository validator remains dependency-free and unchanged.
Package metadata passing that validator is one check; resource closure,
behavior preservation and native-host execution require separate evidence.

## Module placement

Preserve the PRD's explicit eleven skill paths, all 59 skill-relative
references and eighteen persona destinations. Do not merge or rename source
references. New package files are plugin.json, README.md, CHANGELOG.md and
LICENSE; source attribution and the MIT license travel inside the package.

Other paths, all relative to this repository:

- plugins/autopilot/contracts/review-policy-v1.json: policy data.
- plugins/autopilot/contracts/review-evidence-v1.json: closed evidence schema.
- plugins/autopilot/contracts/review-fixtures-v1.json: policy/context/evidence cases.
- plugins/autopilot/scripts/autopilot.py: local capability and policy-export facade.
- tools/autopilot/source-pin.json: immutable source identity.
- tools/autopilot/source-inventory.json: frozen source assets, behavior IDs,
  configuration fields and regression-case inventory.
- tools/autopilot/source-map.json: destination mappings, ownership and evidence.
- tools/autopilot/check-source.py: explicit maintainer provenance verification.
- tools/autopilot/export-policy.py: deterministic export.
- tools/autopilot/prerequisites.py: read-only dependency diagnostics.
- tools/autopilot/requirements-test.txt: pytest>=8,<9 and jsonschema>=4.23,<5;
  jsonschema is a test-only reference validator, not a runtime dependency.
- tests/autopilot/test_contract.py, test_package.py, test_prerequisites.py:
  contracts, coverage/resource closure and prerequisite behavior.
- .github/workflows/validate.yml: add Python 3.12 tests alongside the existing
  Python 3.10 plugins job. Preserve its current steps and pinned actions.
- README.md: report the package's actual gated status.

Every newly authored file has an acceptance owner in the map, with source
identity explicitly null. Missing source provenance must never be fabricated.

## Interfaces & contracts

### Source identity and offline provenance

source-pin.json contains schema_version=1, source repository identity,
commit=e960ef1cc43e72bf92593b2f16c7a37c71ea7e48 and pinned_at=2026-10-24.
It contains no absolute checkout path. Maintainers explicitly supply
--source-root PATH to check-source.py; implementation may use the source
checkout named by the PRD to generate the initial snapshots.

Read source blobs with git show at that exact pin. Generate and commit
source-inventory.json before mapping destinations. It records source paths,
blob hashes, section anchors/hashes, required asset IDs, all P/R and expanded
inventory IDs, documented configuration/state fields, code-only discoveries
and source regression cases. Source docs and code inspection produce this
inventory; the destination map must not generate its own expected ID set.

Normal tests read these committed snapshots and fixture inputs. They never
require the old checkout, the author's home, network access or OVCAQ.
check-source.py re-enumerates the supplied pinned source and checks the
snapshot; missing objects or changed hashes fail that explicit audit.
A failed copying premise means skip/report the edit and leave its obligation
unresolved, never mark it preserved or waive the release gate.

### Source-to-destination mapping

source-map.json contains schema_version=1, the source-inventory digest and
separate assets, behaviors and regression_cases collections.

An asset row contains source_asset_id (null only for new files),
destination_path, source_blob_sha256, destination_blob_sha256,
adaptation_reason, disposition and acceptance_cases. Preserved means byte
equality, not just equal headings. Adapted rows retain source sections and
explain each changed section. Gated assets still exist and carry an explicit
entry-point refusal; gating a capability does not waive the promised files.

A behavior row contains source_behavior_id, source anchors, classification
(port or redesign), reason, owner_repository, delivery_prd, destination
procedure/operation, required_profiles, acceptance_cases and evidence.
Evidence carries status (planned, unavailable, failed, passed), artifact
identity/digest and tested package revision. One scenario may cover several
rows; each row must identify its observable expected outcome.

A regression-case row records its pinned source path/test identity and
retained, replaced or obsolete disposition. Replacements name the equivalent
target scenario. Obsolete requires evidence that the source case tests an
implementation detail or deliberately superseded behavior; it cannot waive a
retained capability. A proposed feature drop requires a recorded user ruling.

The expected set includes all 1,034 expanded rows observed at this pin plus
P01–P11/R01–R31, with separately enumerated field/configuration and code-only
rows. Counts describe this source snapshot, not future test-suite totals.
Reject duplicate, missing and unknown IDs by set comparison. Map external
owners to their actual repository/PRD; no "later" owner or implicit sibling
dependency. AP 00012 validates completeness of assignments, not completion of
future work. AP 00017 and retirement validate passed evidence for their
respective profiles. Unavailable is always incomplete for a promised profile.

Resource edges have a declared kind: packaged-resource, external-capability
or informational-provenance. Packaged references/scripts/personas resolve
inside the distributed root after symlink resolution. External tools have
explicit capability and failure/fallback rules. Historical/source citations
can remain informational but may not be read to supply missing runtime content.
Every runtime-bound instruction is either adapted or covered by an explicit
unavailable-entry-point gate.

### Portable metadata

plugin.json uses the canonical Agent Plugins v1.0.0 schema URL, name
autopilot, version 0.10.0, source author and MIT license. Package-only resources
and LICENSE ship with the directory. The root README must not advertise
execution support before real-host certification.

### Review policy

review-policy-v1.json is policy data with schema_version, procedure,
source_bindings, reviewer_jobs and policy_digest. Source bindings include
pinned path, section and content digest. Reviewer IDs describe roles; provider
and native agent names belong to adapters and explicit execution profiles.

The lane rules are normative:

| Lane | Mandatory roles | Conditional roles and engine | Evidence and boundary |
| --- | --- | --- | --- |
| full | alice consensus, blake blind, bob doubt plus de-slop | carl when the source availability rule activates him; eve when the source opt-in or implementor-diversity guard activates her; Alice can use legacy/workflow/shadow under source rules | Complete results/artifacts for the resolved roster, all required rubric verdicts, fresh coordinator review after build |
| fast-track | alice consensus, blake blind, eve doubt, bob independent review with doubt/de-slop | carl under the source Gemini availability rule; consensus can use its supported workflow/fallback | Complete per-card roster and delta evidence; mandatory fresh coordinator review boundary; no Alice-only shortcut |
| solo | alice consensus, or its policy-resolved workflow implementation | No discretionary choice to use solo; controller code selects and rechecks it | One zero-context complete review and artifact; invalid/missing review retries once then escalates; source production/security/severity/suite escalation remains |

The full-lane rework-cycle cap defaults to two, overridden only by the
validated source configuration. Do not invent a separate full-lane default
of three. Fast-track's bounded delta and solo's one pass/limited repair are
different policies, not three copies of the full-lane loop cap.

Policy declares exact required rubric sets, input exclusions, artifact kinds,
retry limits, escalation rules and conditional-roster predicates with source
anchors. Preserve source R/B/D namespaces. The standing rule's doubt R1–R5
labels map by rule meaning to source D1–D5 within the doubt namespace; they
are not consensus R1–R5. Preserve the de-slop instructions as well as binary
verdict coverage. Tests compare the mapped rules and their source text.

Resolve conditional roles from explicit context before dispatch. Absent
capability may skip only a source-optional role under its documented rule.
A required lens needs a supported replacement or refusal, never silent
omission. Preserve failed, retried and unavailable attempts in evidence.
Role identity, provider identity and independent-context identity are distinct.
The source-parity profile retains its implementor-diversity guard; a separate
certified execution profile must state any user-approved provider-policy
redesign explicitly.

Canonical digest: SHA-256 of UTF-8 json.dumps(policy_without_policy_digest,
sort_keys=True, separators=(",", ":")); remove only the top-level digest key.
The export and committed policy must agree. All policy-affecting content or
referenced content digests participate; relocation cannot change the result.

### Review evidence

review-evidence-v1.json is a JSON Schema for the following closed data model.
The schema describes structure; semantic validation checks the explicit
policy and expected input context. A valid evidence artifact does not itself
authorize a phase transition.

Required top-level fields:

| Field | Contract |
| --- | --- |
| schema_version | 1 |
| lane | full, fast-track or solo; must equal expected context |
| policy_binding | policy_digest and execution_profile; both match expected context |
| source_bindings | PRD digest, reviewed base/head/tree identity, task/card scope and allowed-input manifest digest |
| reviewer_results | One attributable terminal result for each required logical job, with attempt records retained |
| artifacts | ID, kind, path, SHA-256 and producing result ID |
| findings | Array, legitimately empty |
| groups | Array, legitimately empty |
| rubric_verdicts | Result ID, rubric namespace, rule ID, pass/fail and evidence |
| verification | Actual command argv, exit code, output artifact, code identity and outcome; or policy-permitted not-applicable with reason |

Each reviewer result records result_id, role_id, job_ref, attempt,
native_session_ref, source_binding_digest, artifact_ids, outcome
(clean, findings, failed, unavailable), finding_ids and failure/skip reason.
A clean result has zero finding_ids and a real output artifact. A findings
result references existing findings attributed to that result. Failed or
unavailable required roles do not satisfy coverage. Duplicate role/job/attempt
identities cannot fill another required slot. Each conditional exclusion has
its rule and observed capability evidence in the expected context.

Findings reference a result_id; groups reference existing finding IDs without
losing source provenance. Every required rubric rule has an explicit verdict
even on a clean review. Missing output is never an all-clear. A failed
rubric or a retained finding is represented honestly; acceptance remains the
controller's decision under the applicable severity/custody rules.

Validation takes (policy, expected_context, evidence). expected_context
contains resolved roster, source identities, permitted inputs and profile;
it must come from the caller's current authoritative job plan, never from
values merely copied out of the submitted evidence. AP 00012 golden cases
supply fixed expected contexts. AP 00020 binds result/job/session references
to actual controller records, checks artifact bytes and applies acceptance
atomically. Actor credentials, revision/CAS and authorization remain in AP
00018's separate envelope; caller-asserted native identity is not proof.

### Golden cases

review-fixtures-v1.json holds named policy/expected_context/input/expect cases.
Use JSON Schema validation plus contract-specific semantic checks in tests;
do not write a general JSON Schema interpreter. Required cases:

- Clean complete full, fast-track and solo rosters, with zero findings.
- Valid conditional activation, optional-provider absence and source fallback.
- Each missing mandatory role, Alice-only fast-track and review-free solo.
- Failed/malformed output, retry exhaustion and solo escalation.
- Duplicate/misattributed job result and a finding posing as reviewer completion.
- Missing required rubric verdict or required artifact.
- Unknown/duplicate finding or group reference.
- Changed policy binding, unknown lane and wrong execution profile.
- Changed PRD, code/tree, card scope or input manifest with unchanged policy.
- Blind reviewer receiving prohibited context, and reused builder-session identity.

Later controller fixtures additionally prove untrusted context, nonexistent
jobs, live jobs and forged native identity cannot authorize review.close.

### Local facade

Only these initial public commands are available:

~~~text
python3 <package>/scripts/autopilot.py --list-capabilities
python3 <package>/scripts/autopilot.py --export-policy [--out PATH]
~~~

Capabilities identify policy/evidence formats; they do not claim a controller,
executable skills or host support. Export recomputes/checks the policy digest
and returns an error on mismatch. No state mutation, fetch or supervisor.
Unimplemented skill entry points refuse before invoking old scripts.

### Prerequisites

python3 tools/autopilot/prerequisites.py --prd NNNNN reads local done-bucket
files only. Known ID with all predecessors present: exit 0 and JSON prd/missing.
Known ID with missing predecessors: exit 1 and JSON prd/missing.
Unknown ID: exit 1 and JSON unknown_prd diagnostic. Missing directory is empty.

| PRD | Predecessors |
| --- | --- |
| 00012 | none |
| 00013 | 00012 |
| 00014 | 00012, 00013 |
| 00015 | 00013, 00014 |
| 00018 | 00012 |
| 00019 | 00018 |
| 00020 | 00019 |
| 00021 | 00020 |
| 00016 | 00015, 00020, 00021 |
| 00017 | 00016 |

No fetch, write, subprocess or OVCAQ probe. Backlog selection still uses its
existing shell eligibility checks; this tool is the maintainer diagnostic
view, never a self-hosting dependency of selection.

## Data flow and CI

1. Maintainer reads the pinned source, freezes source inventory and fixtures,
   then maps every obligation to a delivery owner/scenario.
2. Copy assets and record byte-identical or documented section adaptations;
   preserve gates on unfinished entry points.
3. Target-only tests compare package content with committed provenance,
   validate policy/evidence and check local dependency behavior.
4. Export policy deterministically. Later producers extend the map with
   concrete passed evidence without deleting original obligations.

Add a Python 3.12 job running the PRD's uv/pytest command. Reuse existing
pinned checkout conventions with persist-credentials false, and pin any new
setup action to a verified commit. Preserve the current Python 3.10 plugins
job; do not assert the nonexistent job name "validate". No old-repository
checkout is needed by the ordinary CI job.

A clean-checkout test copies only committed target inputs into a temporary
root, removes source/upper-layer lookup paths and runs the public package
checks from another cwd. It must not skip when a source checkout is absent.
The explicit check-source maintainer audit remains a separate operation.

## Reuse and alternatives

Reuse scripts/validate.py for manifest, skill metadata, MCP and symlink
containment. Add the missing behavioral and resource checks alongside it.
Reuse pinned source fixtures and semantics rather than drafting new weaker
review rules. Fixtures cannot replace live host probes.

Committed provenance is chosen over source-dependent ordinary CI: it keeps
the independently maintained target testable after retirement. The separate
pinned-source audit checks the initial capture and deliberate future repins.
One controller remains the later authority; no generic workflow framework,
state setter or second backend is introduced.

## Risks and edge cases

- An in-progress build may have read the prior design. Reconcile generated
  contracts/tests with this amendment before its design/implementation gates.
- Source changes, missing objects or changed copying premises leave evidence
  unresolved. They never force an edit or silently certify a partial port.
- File hashes prove copying, not behavior. Behavioral rows and source-derived
  scenarios remain required after adaptation.
- Binding policy alone cannot detect stale work. Code/PRD/input and native-job
  checks are separate and required.
- Retained unavailable behavior cannot satisfy a promised release profile.
- Package-relative runtime references cannot escape through a valid symlink,
  a Markdown link, a shell placeholder or a source-home fallback.

## Test strategy outline

- content_roster: required asset ID set, byte equality for preserved rows and
  explicit section adaptations; all promised files exist even while gated.
- reference_tree_preserved: same skill-relative roster and required sections.
- source_inventory_mapping: exact expected behavior/field/configuration IDs,
  delivery owners, regression dispositions and evidence requirements.
- resource_closure: packaged dependency edges resolve inside the archive;
  a temporary external helper/reference and an escaping symlink are rejected.
- review_schema: all structural and semantic golden cases above; clean
  results pass without invented findings, while stale source identity fails.
- policy_export_reproducible: in-place and relocated facade export agree.
- target_only_checkout: tests succeed without source/author-home/network.
- prerequisites_missing: known, unknown, missing-directory and fulfilled cases.
- local_prerequisites_ignore_ovcaq: execute under unavailable external tools
  and confirm no runtime discovery or state changes.
- ci_autopilot_wired: run the declared test command; inspect the added job
  without snapshotting unrelated workflow formatting.

Run the full uv/pytest command and repository validator once after integration.
These prove the foundation only; real execution support is earned later.

## Review log

The entries below are historical reviews of the pre-correction design
(SHA-256 55a225858114a5c7da4ff48f8d1f6ce77f454507ce577412cd80d84e99afe735).
Their result does not approve the current contracts. The completeness review
and its resolution record govern this amendment.


- [question] `## Interfaces & contracts` → `autopilot.py --list-capabilities`'s hardcoded capability list (`["review-policy-v1", "review-evidence-v1"]`) omits `review-fixtures-v1`; is the fixtures contract internal-test-only (not advertised) or should it appear too? Left as an open question — not a blocker, since the facade's behavior is still fully specified either way.
- [non-blocker] `## Test strategy outline` → `tests/autopilot/test_prerequisites.py`'s `local_prerequisites_ignore_ovcaq` test is weakly motivated: it mocks `subprocess`/`socket` to prove an absence that already trivially holds (no such calls exist anywhere in the design). Consider rescoping it to "module imports and runs with no network/subprocess calls" as a static import-time assertion instead.
- [non-blocker] `## Interfaces & contracts` → `tools/autopilot/requirements-test.txt` contents are left unspecified beyond "pytest + any JSON-schema validation dependency pin"; name the exact pin (e.g. `pytest>=8`) so the CI job description in Data flow is fully concrete.
- [question] `## Module placement` lists `plugins/autopilot/README.md` as new but does not say whether it is a preserved-disposition copy of the source plugin's README or new portable-specific content; should get its own `source-map.json` row either way.

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 2, question 2

Dispatch 2 (codex) found 3 blockers, all fixed by editing the doc: (1) the
policy schema had no per-lane required-reviewer/artifact rules, so
`procedure.lanes` is now a map with `required_reviewer_jobs`/
`required_artifact_kinds` per lane; (2) evidence documents carried no lane or
policy binding, so `review-evidence-v1.json` now requires `lane` and
`policy_binding.policy_digest`; (3) the policy_digest canonicalization
instructions contradicted themselves ("minus this field" vs "set to empty
string") — resolved to "minus this field" alone, stated once, applied
everywhere. Non-blockers and questions fixed too: `requirements-test.txt` now
names `pytest>=8,<9` exactly; the prerequisites isolation test now runs the
tool under the mocks instead of only importing it; the prerequisite table now
gives 00012 an explicit `[]` row instead of leaving it ambiguous; and
`source-map.json`'s scope is now explicit about which PRD files have no row
by design.

dispatch 2 (codex): cardinal-sin 0, blocker 3, non-blocker 2, question 2

- [non-blocker] `## Interfaces & contracts` → the fixture cases exercised the
  `required_reviewer_jobs` enforcement but not `required_artifact_kinds`;
  added case 6 (`"missing-artifact"`) above.

dispatch 3 (codex): all 3 dispatch-2 blockers verified RESOLVED; cardinal-sin 0, blocker 0, non-blocker 1, question 0

result: ok
