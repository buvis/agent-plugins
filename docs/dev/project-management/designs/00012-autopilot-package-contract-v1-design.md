# Design: Autopilot package and review artifact contracts (PRD 00012)

Status: corrected 2026-10-25 after the port-completeness review, then amended
2026-10-26 with the normative wire shapes (Interfaces & contracts § Wire
shapes) after the Task 2 test author stopped on undeclared nested fields. The
earlier review results apply to the previous texts, not this amendment; its own
review is the last `## Review log` entry. Reconcile any in-progress
implementation with the current text. No completed implementation review is
claimed here.

## Architecture fit

Follow the three-layer design in designs/00011-autopilot-standalone-design.md.
Autopilot owns content, evidence policy and one later bundled controller;
OVCAQ owns supervision; Tower owns presentation. AP 00012 supplies the
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
- tools/autopilot/requirements-test.txt: pytest>=8,<9, jsonschema>=4.23,<5
  and PyYAML>=6,<7. The validators and YAML parser are test-only dependencies;
  the package facade and repository validator retain standard-library runtimes.
- tests/autopilot/test_contract.py, test_package.py, test_prerequisites.py:
  contracts, coverage/resource closure and prerequisite behavior.
- .github/workflows/validate.yml: add Python 3.12 tests alongside the existing
  Python 3.10 plugins job. Preserve its current steps and pinned actions.
- README.md: report the package's actual gated status.

Every newly authored file has an acceptance owner in the map, with source
identity explicitly null. Missing source provenance must never be fabricated.
The `authored_file_owners` collection assigns that source-null ownership to
foundation product files, including maintainer tools, tests and the map itself.
Package delivery hashes remain in `assets`; ownership records do not introduce
a recursive digest of the map. Workflow-store evidence is not a product asset.

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

`procedure.lanes` is a map keyed by lane name (`full`, `fast-track`, `solo`).
Each lane entry declares these fields:

| Field | Contract |
| --- | --- |
| `required_reviewer_jobs` | Ordered list of mandatory logical reviewer job IDs for the lane, resolved from the lane table below. Empty is never valid for full or fast-track; solo's single zero-context job is explicit, not absent. |
| `required_artifact_kinds` | Artifact kinds that must be present in evidence for the lane (e.g. `review-file`). |
| `required_rubric_sets` | Rubric namespaces and rule IDs each resolved job must return verdicts for (e.g. doubt D1-D5 for the doubt job), with source anchors. |
| `rework_policy` | Retry limits, escalation rules and the lane's cap policy as stated below. |

Golden fixtures and the evidence schema reference these exact field names;
evidence validation resolves the lane entry from the expected context's lane
and rejects evidence whose covered jobs, artifacts or rubric verdicts do not
satisfy the lane's required sets.

The lane rules are normative:

| Lane | Mandatory roles | Conditional roles and engine | Evidence and boundary |
| --- | --- | --- | --- |
| full | alice consensus, blake blind, bob doubt plus de-slop | carl when the source availability rule activates him; eve when the source opt-in or implementor-diversity guard activates her; Alice can use legacy/workflow/shadow under source rules | Complete results/artifacts for the resolved roster, all required rubric verdicts, fresh coordinator review after build |
| fast-track | alice consensus, blake blind, eve doubt, bob independent review with doubt/de-slop | carl under the source Gemini availability rule; consensus can use its supported workflow/fallback | Complete per-card roster and delta evidence; mandatory fresh coordinator review boundary; no Alice-only shortcut |
| solo | alice consensus, or its policy-resolved workflow implementation | No discretionary choice to use solo; controller code selects and rechecks it | One zero-context complete review and artifact; invalid/missing review retries once then escalates; source production/security/severity/suite escalation remains |

The full-lane rework-cycle cap defaults to two, overridden only by the
validated source configuration. Do not invent a separate full-lane default
of three. Note: the source `state-schema.md` example JSON shows
`"rework_cap": 3`; that value is illustrative (an explicit PRD frontmatter
override), not the default — the authoritative default of two comes from
`phase-review.md` and `frontmatter.py`. Fast-track's bounded delta and solo's one pass/limited repair are
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
The source-parity profile retains its implementor-diversity guard. The user
selected Codex + Gemini for Claude-free certification on 2026-10-25: Codex
implements; Gemini supplies the independent provider's doubt voice, including
Eve whenever required. All other resolved roles run in isolated Codex or Gemini
contexts. Carl's availability predicate still applies; no mandatory lens or
fresh-session boundary is removed. This changes provider bindings, not review
semantics. Codex-only is not a certified completion profile. AP 00014 owns
native host support; AP 00017 owns real standalone and managed certification;
OV 00059/00060 supply the managed driver and supervision evidence.

Canonical digest: SHA-256 of UTF-8 json.dumps(policy_without_policy_digest,
sort_keys=True, separators=(",", ":"), ensure_ascii=True); remove only the
top-level digest key. Policy JSON values are restricted to the finite JSON
domain: no NaN, Infinity or -Infinity, and non-integer numbers are not used
anywhere in the policy. The export and committed policy must agree. All
policy-affecting content or referenced content digests participate; relocation
cannot change the result. Two independent implementations serializing the same
policy content must produce the same digest.

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
native_session_ref, source_binding_digest, received_input_refs, artifact_ids,
outcome (clean, findings, failed, unavailable), finding_ids and failure/skip
reason.
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
  Both cases are expressed through the expected_context's permitted-inputs and
  the per-result input records: each reviewer result additionally records
  `received_input_refs` (the input identities actually supplied to that job).
  The blind-context case supplies a blind result whose `received_input_refs`
  contain an identity outside the allowed-input manifest and expects rejection;
  the reused-identity case supplies two results whose `native_session_ref`
  values are identical where the policy requires independent contexts and
  expects rejection. AP 00020 binds these references to actual launch facts.

Later controller fixtures additionally prove untrusted context, nonexistent
jobs, live jobs and forged native identity cannot authorize review.close.

The exact case names, inputs and expected results are fixed in § Wire shapes
below (Fixture cases). A case not listed there is not required; a listed case
missing from the committed fixture file fails review_schema.

### Wire shapes (normative)

These shapes close every model named above. Where an earlier paragraph names a
field and this section types it, this section governs. Notation: `string` is a
non-empty UTF-8 string; `int` a JSON integer; `bool`; `hex64` a lowercase
64-character SHA-256 hex digest; `hex40` a lowercase 40-character git object
id; `T?` is `T` or `null`; `[T]` an array of `T`, possibly empty unless stated;
`enum(a|b)` one of the literals. Every object is closed: a field outside its
table is a structural error (`additionalProperties: false`). An `anchor` is a
`string` equal to one `source_bindings[].binding_id` of the same policy.

Canonical JSON, used by every digest below: UTF-8 bytes of
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.

### review-policy-v1.json

| Field | Type and rule |
| --- | --- |
| `schema_version` | the integer `1` |
| `procedure` | object: `lanes` and `conditional_predicates` below |
| `reviewer_jobs` | `[reviewer_job]`, non-empty, unique `job_id`; exactly the five rows in the Reviewer jobs table |
| `rubric_sets` | object with exactly the keys `R`, `B`, `D`, each a `rubric_set` |
| `doubt_label_map` | exactly `{"R1":"D1","R2":"D2","R3":"D3","R4":"D4","R5":"D5"}`: the operator standing rule (the host's global `AGENTS.md` § Workflow, "doubt+de-slop with rubric R1-R5") mapped by rule meaning onto the pinned `D` set. That rule lives outside the pinned source, so it has no `source_bindings` row; the map is informational for this validator |
| `execution_profiles` | object keyed by `profile_id`; exactly the keys `source-parity` and `codex-gemini`, each an `execution_profile` |
| `artifact_kinds` | exactly `["review-file", "reviewer-output", "verification-log"]` |
| `input_kinds` | exactly `["prd", "card", "repo-tree", "rubric", "diff", "file-list", "plan", "history", "implementation-audit", "sibling-findings", "context-pack", "mech-facts", "test-results"]` |
| `source_bindings` | `[source_binding]`, non-empty, unique `binding_id` |
| `policy_digest` | `hex64`, the canonical digest of the document minus this key |

`procedure.lanes` is an object keyed by `lane_id`, exactly the keys `full`,
`fast-track` and `solo`. A lane:

| Field | Type and rule |
| --- | --- |
| `required_reviewer_jobs` | `[string]` of `job_id`, ordered, unique, non-empty |
| `conditional_reviewer_jobs` | `[{"job_id": string, "predicate_id": string}]`; `job_id` is not in `required_reviewer_jobs`; `predicate_id` is a key of `conditional_predicates`; the same `job_id` may appear with several predicates. The job is resolved when at least one of its predicates holds (the roster entry's `activation` names one holding pair, and the job appears in no `excluded_jobs` row); it is excluded only when every one of its (job, predicate) pairs appears in `excluded_jobs` with an observation that does not satisfy that predicate |
| `delta_reviewer_jobs` | `[string]` of `job_id` ⊆ `required_reviewer_jobs`, unique; the roster of a `delta` review pass (the one re-review of a rework commit). Empty means the lane has no delta pass and re-runs its whole roster every cycle |
| `required_artifact_kinds` | `[string]` ⊆ `artifact_kinds`, non-empty, contains `review-file` |
| `required_rubric_sets` | `[{"job_id": string, "namespace": enum(R\|B\|D), "rule_ids": [string], "anchor": anchor}]`; one entry per (job, namespace); `rule_ids` equals `rubric_sets.<namespace>.rule_ids` exactly; every required and conditional job of the lane has at least one entry |
| `input_exclusions` | `[{"job_id": string, "excluded_input_kinds": [string], "anchor": anchor}]`; kinds ⊆ `input_kinds`; at most one entry per job |
| `independent_contexts` | `bool` |
| `fresh_coordinator_review` | `bool`; informational for this validator, consumed by the controller (AP 00020) |
| `verification_not_applicable_reasons` | `[string]` |
| `rework_policy` | object below |

`rework_policy`:

| Field | Type and rule |
| --- | --- |
| `cycle_cap_default` | `int` ≥ 1 |
| `cap_override_source` | `enum(prd_frontmatter.rework_cap)?` |
| `reviewer_retry_limit` | `int` ≥ 0; the in-kind retries one job may spend per adapter. A fallback substitution (the profile's `fallback` binding) opens a new adapter group and spends no retry, as the source's unavailable-CLI substitution does |
| `escalation_rules` | `[{"signal": string, "action": action, "anchor": anchor}]`, unique `signal` |

`action` is `enum(escalate_full|branch_and_park|stall_or_pause|defer|treat_as_critical|mark_unavailable|retry_once|fallback_native_consensus)`.

`conditional_predicates` is an object keyed by `predicate_id`; a predicate is
`{"capability": string, "expected_value": string|bool, "description": string, "anchor": anchor}`.
A predicate holds for an observation `{"capability": c, "value": v}` when
`c` equals `capability` and `v` equals `expected_value`.

`reviewer_job`: `{"job_id": string, "role_id": enum(consensus|blind|doubt|ui), "lenses": [enum(consensus|blind|doubt|de-slop|ui)] non-empty, "anchor": anchor}`.
Which provider and adapter run a job is a profile fact (`execution_profiles`),
never a job fact.

`rubric_set`: `{"rule_ids": [string] non-empty in source order, "anchor": anchor}`;
the `D` set additionally carries `"de_slop_anchor": anchor` (the de-slop
instructions of `agents/eve.md` § 2. De-slop lens), the other two do not. Rule
prose stays outside the policy (PRD: "semantic rubric prose stays external"):
the package ships the three rubric files and `references/personas/eve.md` as
preserved assets, so tests parse the rule ids from the packaged
`skills/review-work-completion/references/rubric.md`,
`skills/review-blindly/references/rubric.md` and
`skills/run-autopilot/references/doubt-review-rubric.md` and require them to
equal `rule_ids`, and require the packaged `eve.md` to carry the de-slop
section the anchor names. `check-source.py` recomputes the anchors' digests
from the pinned blobs.

`execution_profile`: `{"description": string, "implementor_providers": [string] non-empty, "implementor_diversity_guard": bool, "role_bindings": {job_id: role_binding}}`
with one `role_bindings` key per `reviewer_jobs[].job_id`;
`role_binding` is `{"provider": string, "adapters": [string] non-empty, "fallback": {"provider": string, "adapters": [string] non-empty}?}`.
A result's (`provider`, `adapter`) pair must match the primary or the fallback
binding of its job under the bound profile (`profile_binding_mismatch`).
`implementor_providers` and `implementor_diversity_guard` are informational
for this validator; AP 00017 certification and the AP 00020 controller consume
them.

Adapter vocabulary: `native-subagent` (a native agent running its own
persona; also the legacy consensus engine), `review-fanout-workflow` (the
workflow consensus engine), `codex-cli`, `gemini-cli`, `native-fallback` (a
native agent running a CLI persona's prompt as its stand-in). The `shadow`
engine produces no adapter of its own: its gating result is the legacy
`native-subagent` run and its workflow run is an observation, never a
`reviewer_result`.

Consensus engine binding. `expected_context.consensus_engine` (the PRD's
`consensus_engine` frontmatter value as the controller resolved it) applies
only under a profile whose Alice binding lists the two engine adapters
(`source-parity`); there it selects Alice's permitted adapter: `legacy` and
`shadow` permit `native-subagent` only; `workflow` requires
`review-fanout-workflow`, and permits `native-subagent` only as a fallback
after a lower-numbered Alice attempt whose adapter is `review-fanout-workflow`
and whose outcome is `unavailable` (the engine itself absent: the Workflow
tool missing or the call refused). A workflow attempt that ended `failed`
(`INVALID_ARGS`, or `incomplete` after its one resume) never licenses a legacy
run; the source forbids that degradation (`rwc-dispatch`). Under a profile
whose Alice binding lists neither engine adapter (`codex-gemini`, Alice on
`codex-cli`), `consensus_engine` must be `legacy` and the binding's own
adapter is the permitted one; the engine rule adds nothing there.

`source_binding`: `{"binding_id": string, "source_path": string, "section": string?, "blob_sha256": hex64, "section_sha256": hex64?}`.
`source_path` and `blob_sha256` equal an `assets[]` or `source_files[]` row of
`tools/autopilot/source-inventory.json`; a non-null `section` is that asset's
`sections[].anchor` and `section_sha256` that section's `sha256`; a null
`section` means the whole blob and a null `section_sha256`. Normal tests check
this agreement against the committed inventory; `check-source.py` additionally
recomputes every digest from the supplied pinned checkout.

Normative policy data. The committed policy carries exactly these values; a
test that compares them to the tables below is the "weakened roster" check.

Reviewer jobs:

| job_id | role_id | lenses | anchor |
| --- | --- | --- | --- |
| `alice` | `consensus` | `consensus` | `rwc-reviewers` |
| `blake` | `blind` | `blind` | `blind-rubric` |
| `bob` | `doubt` | `consensus`, `doubt`, `de-slop` | `rwc-reviewers` |
| `carl` | `ui` | `consensus`, `ui` | `rwc-prereqs` |
| `eve` | `doubt` | `doubt`, `de-slop` | `eve-two-lenses` |

Rubric sets (`rule_ids`): `R` = `R1 R2 R3 R4 R6 R7 R8 R9 R10 R11 R12 R13`
(the pinned consensus rubric has no `R5`; twelve rules, anchor
`consensus-rubric`); `B` = `B1` … `B19` (anchor `blind-rubric`); `D` = `D1` …
`D5` (anchor `doubt-rubric`, `de_slop_anchor` `eve-de-slop`).

Conditional predicates:

| predicate_id | capability | expected_value | anchor |
| --- | --- | --- | --- |
| `gemini_cli_available` | `gemini_cli` | `true` | `rwc-prereqs` |
| `doubt_reviewer_fable` | `doubt_reviewer` | `"fable"` | `rwc-prereqs` |
| `implementor_codex_present` | `implementor_codex_present` | `true` | `rwc-prereqs` |

Lanes:

| Field | full | fast-track | solo |
| --- | --- | --- | --- |
| `required_reviewer_jobs` | `alice, blake, bob` | `alice, blake, eve, bob` | `alice` |
| `conditional_reviewer_jobs` | `carl:gemini_cli_available`, `eve:doubt_reviewer_fable`, `eve:implementor_codex_present` | `carl:gemini_cli_available` | none |
| `delta_reviewer_jobs` | none (every cycle re-runs the roster) | `eve` (`fast-track-delta`) | `alice` (`solo-disposition`) |
| `required_artifact_kinds` | `review-file, reviewer-output` | `review-file, reviewer-output` | `review-file, reviewer-output` |
| `required_rubric_sets` (job:ns, anchor) | `alice:R`, `bob:R`, `carl:R` (`consensus-rubric`); `blake:B` (`blind-rubric`); `bob:D`, `eve:D` (`doubt-rubric`) | `alice:R`, `bob:R`, `carl:R` (`consensus-rubric`); `blake:B` (`blind-rubric`); `eve:D`, `bob:D` (`doubt-rubric`) | `alice:R` (`consensus-rubric`) |
| `input_exclusions` | `blake`: `diff, file-list, plan, history, implementation-audit, sibling-findings, context-pack, mech-facts` (anchor `rwc-prompts`; `test-results` stays allowed, the source gives Blake the test gate block); `eve`: `plan` (anchor `rwc-context`; the doubt surface stays PRD-only) | same as full | none |
| `independent_contexts` | `true` | `true` | `true` |
| `fresh_coordinator_review` | `true` | `true` | `false` |
| `verification_not_applicable_reasons` | `docs-only` | `docs-only` | `docs-only` |
| `rework_policy.cycle_cap_default` | `2` | `1` | `1` |
| `rework_policy.cap_override_source` | `prd_frontmatter.rework_cap` | `null` | `null` |
| `rework_policy.reviewer_retry_limit` | `1` | `1` | `1` |
| `rework_policy.escalation_rules` (signal → action, anchor) | `critical_unresolved_at_cap → stall_or_pause` (`review-cap-check`: loop stalls `cap_critical`, interactive cap-pauses); `high_unresolved_at_cap_interactive → stall_or_pause` (`review-cap-pause`); `high_unresolved_at_cap_loop → defer` (`review-cap-check`: only after `cap-check` exit 0); `high_regression_at_cap_loop → stall_or_pause` (`review-cap-check`: `cap-check` exit 1, stall `cap_regression`); `cap_check_failed → retry_once` (`review-cap-check`: exit 2, re-invoke once then `sub_skill_fail`); `doubt_constraint_unmet → treat_as_critical` (`review-outcomes`); `reviewer_failed_after_retry → mark_unavailable` (`retry-policy`) | `critical_or_high_survives_delta → branch_and_park` (`fast-track-exit`); `consensus_workflow_unavailable → fallback_native_consensus` (`fast-track-roster`: the Workflow tool refuses the fanout call, an `unavailable` workflow attempt, so the consensus engine binding below permits the `native-subagent` fallback) | `unnamed_path`, `security_diff`, `check_failed → escalate_full` (`solo-escalation`); `critical_finding`, `high_unresolved`, `suite_red → escalate_full` (`solo-disposition`); `review_failed → escalate_full` (`solo-review`); `review_invalid → retry_once` (`solo-review`) |

Execution profiles (`implementor_diversity_guard` is `true` in both; cells are
`provider` / `adapters`, then the fallback binding when one exists):

| job | `source-parity` (implementors `anthropic`, `openai`) | `codex-gemini` (implementors `openai`) |
| --- | --- | --- |
| `alice` | `anthropic` / `native-subagent`, `review-fanout-workflow` (one of them, selected by `consensus_engine`) | `openai` / `codex-cli` |
| `blake` | `anthropic` / `native-subagent` | `openai` / `codex-cli` |
| `bob` | `openai` / `codex-cli`; fallback `anthropic` / `native-fallback` | `openai` / `codex-cli` |
| `carl` | `google` / `gemini-cli` | `google` / `gemini-cli` |
| `eve` | `anthropic` / `native-subagent`; fallback `anthropic` / `native-fallback` | `google` / `gemini-cli` |

Source bindings (`binding_id` → pinned `source_path` # `section`; a bare path
is a whole-blob binding):

`rwc-reviewers` → `skills/review-work-completion/SKILL.md` # `reviewers`;
`rwc-prereqs` → same file # `1-validate-prerequisites`;
`rwc-context` → same file # `3-gather-context`;
`rwc-prompts` → same file # `4-prepare-agent-prompts`;
`rwc-dispatch` → same file # `5-run-agent-review`;
`rwc-consolidate` → same file # `6-consolidate-findings`;
`consensus-rubric` → `skills/review-work-completion/references/rubric.md` # `rules`;
`blind-rubric` → `skills/review-blindly/references/rubric.md` # `rules`;
`doubt-rubric` → `skills/run-autopilot/references/doubt-review-rubric.md` # `rules`;
`eve-two-lenses` → `agents/eve.md` # `two-lenses-applied-to-every-changed-file`;
`eve-de-slop` → `agents/eve.md` # `2-de-slop-lens-quality`;
`eve-verdicts` → `agents/eve.md` # `rubric-verdicts-required--emit-verbatim-one-per-line`;
`bob-persona` → `agents/bob.md`;
`retry-policy` → `skills/review-work-completion/references/retry-policy.md` # `when-to-retry`;
`verdict-completeness` → same file # `per-rule-verdict-completeness`;
`review-cap-check` → `skills/run-autopilot/references/phase-review.md` # `cap-check--evaluate-after-reading-review-before-rework-dispatch`;
`review-cap-pause` → same file # `cap-pause-behavior`;
`review-outcomes` → same file # `outcomes`;
`review-de-slop` → same file # `de-slop-is-part-of-the-doubt-lens`;
`fast-track-roster` → `skills/fast-track/SKILL.md` # `roster`;
`fast-track-rework` → same file # `rework`;
`fast-track-delta` → same file # `delta`;
`fast-track-exit` → same file # `exit`;
`solo-escalation` → `skills/run-autopilot/references/lane-solo.md` # `4-escalation-checks`;
`solo-review` → same file # `5-review`;
`solo-disposition` → same file # `disposition`;
`review-file-format` → `skills/review-work-completion/references/review-coverage-format.md`;
`frontmatter-defaults` → `skills/run-autopilot/cli/frontmatter.py`;
`lane-routing` → `skills/run-autopilot/cli/lane.py`.

A binding no `anchor` field names (for example `frontmatter-defaults`, the
origin of the cap default of two) is provenance for `check-source.py`; it is
valid and stays in the digest.

### review-evidence-v1.json

A JSON Schema (draft 2020-12). Its root is the evidence document; `$defs`
holds `expected_context`, `source_bindings`, `reviewer_result`, `artifact`,
`finding`, `group`, `rubric_verdict` and `verification`, so tests validate an
expected context with `{"$ref": "<schema id>#/$defs/expected_context"}` and no
second schema file exists. Uniqueness and cross-reference rules below are
semantic checks, not schema keywords, except where `uniqueItems` applies to
arrays of strings.

Evidence (root):

| Field | Type and rule |
| --- | --- |
| `schema_version` | the integer `1` |
| `lane` | `string`; membership in `procedure.lanes` is the semantic check `unknown_lane`, not a schema enum |
| `review_pass` | `enum(initial\|delta)`: `initial` is a whole-roster review of the scope; `delta` is the lane's one re-review of a rework commit by its `delta_reviewer_jobs` |
| `policy_binding` | `{"policy_digest": hex64, "execution_profile": string}` |
| `source_bindings` | `source_bindings`; schema `if/then`: `prior_evidence_sha256` is a `hex64` when `review_pass` is `delta` and `null` when `initial` |
| `reviewer_results` | `[reviewer_result]`, unique `result_id` |
| `artifacts` | `[artifact]`, unique `artifact_id` |
| `findings` | `[finding]`, unique `finding_id` |
| `groups` | `[group]`, unique `group_id` |
| `rubric_verdicts` | `[rubric_verdict]`, unique (`result_id`, `namespace`, `rule_id`) |
| `verification` | `verification` |

`source_bindings`: `{"prd_sha256": hex64, "base_sha": hex40, "head_sha": hex40, "tree_sha": hex40, "scope": {"kind": enum(prd|task|card), "refs": [string] non-empty unique}, "allowed_input_manifest_sha256": hex64, "prior_evidence_sha256": hex64?}`.
For a `delta` pass, `base_sha` is the rework base, `head_sha`/`tree_sha` the
reworked revision, and `prior_evidence_sha256` the canonical digest of the
`initial` pass's evidence document; the two documents stay separate, each
bound to its own revision. AP 00020 binds that digest to the stored prior
document; this validator checks its shape only.

`reviewer_result`:

| Field | Type and rule |
| --- | --- |
| `result_id` | `string` |
| `job_ref` | `string`, a policy `job_id` |
| `role_id` | `enum(consensus\|blind\|doubt\|ui)` |
| `provider` | `string` |
| `adapter` | `string` |
| `attempt` | `int` ≥ 1 |
| `native_session_ref` | `string?`; schema `if/then`: a `string` when `outcome` is `clean` or `findings` (an attempt that never obtained a session, such as a missing CLI, records `null`) |
| `source_binding_digest` | `hex64` |
| `received_input_refs` | `[input_ref]` unique |
| `artifact_ids` | `[string]` unique |
| `outcome` | `enum(clean\|findings\|failed\|unavailable)` |
| `finding_ids` | `[string]` unique; schema `if/then`: empty when `outcome` is `clean`, non-empty when `findings` |
| `reason` | `string?`; schema `if/then`: a `string` when `outcome` is `failed` or `unavailable` |

`input_ref` is a `string` matching `^[a-z][a-z-]*:[^\s]+$`; the text before
the first `:` is its input kind.

`artifact`: `{"artifact_id": string, "kind": string, "path": string, "sha256": hex64, "result_id": string?}`.
`path` is repository-relative: no leading `/`, no `..` segment, no `\`, no
drive prefix. `result_id` is `null` for coordinator-written artifacts (the
`review-file`, the `verification-log`).

`finding`: `{"finding_id": string, "result_id": string, "severity": enum(critical|high|medium|low), "title": string, "file": string?, "task_ref": string?, "evidence": string}`.
No disposition field: acceptance belongs to the controller (AP 00020).

`group`: `{"group_id": string, "finding_ids": [string] non-empty unique, "rationale": string}`.

`rubric_verdict`: `{"result_id": string, "namespace": enum(R|B|D), "rule_id": string, "verdict": enum(pass|fail), "evidence": string}`;
`rule_id` matches `^[RBD][0-9]+$` and starts with `namespace`.

`verification` is one of
`{"status": "ran", "argv": [string] non-empty, "exit_code": int, "output_artifact_id": string, "code_identity": hex40, "outcome": enum(passed|failed)}`
or `{"status": "not-applicable", "reason": string}`.

`expected_context` (`$defs/expected_context`):

| Field | Type and rule |
| --- | --- |
| `lane` | `enum(full\|fast-track\|solo)` |
| `review_pass` | `enum(initial\|delta)` |
| `execution_profile` | `string` |
| `consensus_engine` | `enum(legacy\|workflow\|shadow)` |
| `policy_digest` | `hex64` |
| `source_bindings` | `source_bindings` (same shape as the evidence field) |
| `resolved_roster` | `[roster_entry]` non-empty, unique `job_id`; for a `delta` pass exactly the lane's `delta_reviewer_jobs`, all `required: true` |
| `excluded_jobs` | `[{"job_id": string, "predicate_id": string, "observed": observed}]` |
| `allowed_inputs` | `{"manifest_sha256": hex64, "input_refs": [input_ref] unique, "per_job": {job_id: [input_ref]}}` |
| `session_identities` | `{"builder_session_refs": [string], "independent_contexts_required": bool}` |

`roster_entry`: `{"job_id": string, "role_id": enum(consensus|blind|doubt|ui), "required": bool, "activation": {"predicate_id": string, "observed": observed}?}`;
`activation` is `null` exactly when `required` is `true`.
`observed`: `{"capability": string, "value": string|bool}`.

`allowed_inputs.manifest_sha256` is the canonical digest of
`{"input_refs": <input_refs sorted>, "per_job": <per_job with every value list sorted and deduplicated>}`.

### Validation result and defect codes

`validate_review(policy, expected_context, evidence)` returns
`{"outcome": "accepted"}` or `{"outcome": "rejected", "defects": [code, ...]}`
with `defects` sorted, unique and non-empty. The codes are a closed enum. The
checks run in the order below; a `(stop)` code ends validation with only the
codes found so far. Otherwise every applicable code is reported, so a fixture's
`expect.defects` is the complete set. Every lane-dependent check (required
jobs, rubric sets, artifact kinds, exclusions, rework policy, waivers) reads
the lane entry named by `expected_context.lane`, never by `evidence.lane`. On
a `delta` pass the "roster" below is the lane's `delta_reviewer_jobs`, with no
conditional jobs; `required_rubric_sets` apply to those jobs only, and
`required_artifact_kinds` apply unchanged.

| Code | Condition |
| --- | --- |
| `schema_invalid` (stop) | the evidence fails the root schema, the expected context fails `$defs/expected_context`, or the policy breaks a rule of its own table above |
| `invalid_expected_context` (stop) | `policy_digest` ≠ the policy's; `execution_profile` not in the policy; a lane required job is absent from `resolved_roster` or carries `required: false`; a `required: false` entry or an `excluded_jobs` entry names a (job, predicate) pair the lane does not declare, or its `observed` does not satisfy the predicate when activated or does satisfy it when excluded; a job is both resolved and excluded; a conditional job is neither resolved nor excluded under every one of its predicates; `per_job` keys ≠ roster job ids; a `per_job` ref is not in `input_refs`, has a kind outside `input_kinds`, or has a kind the lane excludes for that job; `manifest_sha256` ≠ its canonical digest or ≠ `source_bindings.allowed_input_manifest_sha256`; `session_identities.independent_contexts_required` ≠ the lane's `independent_contexts`; `review_pass` is `delta` in a lane whose `delta_reviewer_jobs` is empty, or its roster ≠ those jobs; `consensus_engine` is not `legacy` while the profile's `alice` binding lists no engine adapter |
| `lane_mismatch` | `evidence.lane` ≠ `expected_context.lane`, or `evidence.review_pass` ≠ `expected_context.review_pass` |
| `unknown_lane` (stop) | `evidence.lane` is not a key of `procedure.lanes` |
| `policy_digest_mismatch` | `policy_binding.policy_digest` ≠ `expected_context.policy_digest` |
| `execution_profile_mismatch` | `policy_binding.execution_profile` ≠ `expected_context.execution_profile` |
| `source_binding_mismatch` | `evidence.source_bindings` ≠ `expected_context.source_bindings` (deep equality); a result's `source_binding_digest` ≠ the canonical digest of `evidence.source_bindings`; or a `ran` verification's `code_identity` ≠ `source_bindings.head_sha` |
| `duplicate_id` | a repeated `result_id`, `artifact_id`, `finding_id` or `group_id`, or two rubric verdicts with the same (`result_id`, `namespace`, `rule_id`) |
| `duplicate_job_result` | two results share (`job_ref`, `attempt`), or a result that is not its job's highest attempt has outcome `clean` or `findings` |
| `attempt_sequence_invalid` | a job's distinct `attempt` values are not exactly `1..max(attempt)` (a lone attempt `2`, or a gap, hides history); duplicate values are covered only by `duplicate_job_result` |
| `result_misattributed` | a result's `job_ref` is not in `resolved_roster`; its `role_id` ≠ that job's policy `role_id`; or a rubric verdict's (`result_id` → job, `namespace`) is not one of the lane's `required_rubric_sets` for that job |
| `profile_binding_mismatch` | a result's (`provider`, `adapter`) is neither the primary nor the fallback binding of its job in `execution_profiles[expected_context.execution_profile]`; it is the fallback binding while no lower-numbered attempt of that job has outcome `failed` or `unavailable`; or, under a profile whose `alice` binding lists the engine adapters, it is an `alice` result whose adapter the consensus engine binding above does not permit (`review-fanout-workflow` under `legacy`/`shadow`, or `native-subagent` under `workflow` without a lower-numbered `unavailable` workflow attempt) |
| `retry_limit_exceeded` | a job has more than `reviewer_retry_limit + 1` results with the same `adapter` (in-kind retries); a fallback substitution starts its own count |
| `missing_required_job` | a roster job has no result |
| `required_job_failed` | a roster job's terminal result (its highest attempt) has outcome `failed` or `unavailable` |
| `result_without_output` | a terminal `clean` or `findings` result has no `artifact_ids` entry naming an artifact of kind `reviewer-output` whose `result_id` is that result (every completed review owns its raw output) |
| `outcome_findings_mismatch` | a finding's `result_id` names a result whose outcome is not `findings`, or a `findings` result's `finding_ids` ≠ the set of findings naming it |
| `finding_unattributed` | a finding's `result_id` names no result |
| `verdict_unattributed` | a rubric verdict's `result_id` names no result |
| `artifact_unattributed` | an artifact's non-null `result_id` names no result, or a result's `artifact_ids` names no artifact |
| `unknown_reference` | a group's `finding_ids` or the verification's `output_artifact_id` names nothing |
| `unknown_artifact_kind` | an artifact's `kind` is not in `artifact_kinds` |
| `unknown_rubric_rule` | a rubric verdict's `rule_id` is not in `rubric_sets[namespace].rule_ids` |
| `unknown_input_kind` | a result's `received_input_refs` entry has a kind outside `input_kinds` |
| `missing_rubric_verdict` | for a terminal `clean` or `findings` result, a `rule_id` of one of its job's `required_rubric_sets` has no verdict row |
| `missing_required_artifact` | a lane `required_artifact_kinds` entry with no artifact of that kind |
| `prohibited_input` | a result's `received_input_refs` holds a ref outside `allowed_inputs.per_job[job_ref]`, or one whose kind the lane excludes for that job |
| `shared_session_identity` | with the lane's `independent_contexts` true: two results of different `job_ref` share a non-null `native_session_ref`, or a non-null one equals a `builder_session_refs` entry. Attempts of one job may share a session (the source retries Alice in her own conversation) |
| `verification_mismatch` | `ran` with `exit_code` `0` and outcome `failed`, or non-zero and `passed`; `ran` whose `output_artifact_id` names an artifact of a kind other than `verification-log`; or `not-applicable` whose `reason` is not in the lane's `verification_not_applicable_reasons` |

Treating a failed or unavailable required job as incomplete evidence is a
deliberate redesign of the source's "mark unavailable, continue with partial
results" consolidation (`retry-policy` § When to Retry): the port-completeness
review (reviews/00011-autopilot-port-corrections.md, F1/F2) requires a
supported replacement or an explicit refusal for every required lens. The
`source-map.json` behavior row for that source section (`BEH-248`, When to
Retry) is already classified `redesign` under AP 00020; the next map update
(Task 7 touches `source-map.json`) adds this incomplete-evidence rule to its
`reason`. The full lane's `reviewer_failed_after_retry → mark_unavailable`
rule records the source's own response and is what the controller executes
before it submits evidence.

Severity, consensus and disposition never enter this result; a rejected
evidence is one that cannot be read as a complete review, an accepted one still
awaits the controller's decision.

### review-fixtures-v1.json

~~~text
{
  "schema_version": 1,
  "policies": {"<policy_key>": <policy document>},
  "cases": [
    {
      "name": <string, unique>,
      "policy": <policy_key>,
      "expected_context": <expected_context object>,
      "input": <complete evidence document>,
      "expect": {"outcome": "accepted"} | {"outcome": "rejected", "defects": [<code>, ...]}
    }
  ]
}
~~~

`policies` has exactly two keys: `v1`, byte-equal (after canonical JSON) to
the committed `review-policy-v1.json`, and `v1-alt`, the same policy with
`execution_profiles["source-parity"].description` changed and `policy_digest`
restamped: a different digest without touching any normative value, so the
"exactly these values" check holds for both. Every case `input` is
self-contained; cases never reference each other.

Fixture cases. Each `rejected` row lists the complete `expect.defects`. Unless
a row says otherwise, the default input is: lane `full`, `review_pass`
`initial` (`prior_evidence_sha256` null), profile
`source-parity`, `consensus_engine` `legacy`, policy `v1`; the roster is the lane's required jobs, `carl`
excluded by `gemini_cli_available` observed `false` and `eve` excluded by both
`doubt_reviewer_fable` observed `"codex"` and `implementor_codex_present`
observed `false` (two `excluded_jobs` rows); every result is attempt 1,
`clean`, carries the profile's primary `provider`/`adapter`, a distinct
`native_session_ref`, a `source_binding_digest` of the evidence's
`source_bindings`, received refs within its `per_job` allowance, its own
`reviewer-output` artifact and a `pass` verdict for every rule of its required
sets; a `review-file` artifact and a `verification-log` artifact (both
`result_id` null); a `ran` verification with exit `0`, outcome `passed`,
`code_identity` = `head_sha` and `output_artifact_id` naming the
`verification-log`; `findings` and `groups` empty; the expected context
consistent with the input. "No `<job>` result" removes that job's result,
artifacts and verdicts together. `full-clean` is also the optional-provider
absence case (`carl` observed unavailable).

| name | input deviation | expect |
| --- | --- | --- |
| `full-clean` | none | accepted |
| `fast-track-clean` | lane `fast-track`, scope kind `card`; `eve` is required there, so no `eve` exclusion rows | accepted |
| `solo-clean` | lane `solo`; no exclusion rows | accepted |
| `full-carl-activated` | `carl` resolved by `gemini_cli_available` observed `true` (`google`/`gemini-cli`), clean result and `R` verdicts | accepted |
| `full-bob-fallback` | `bob` attempt 1 `unavailable` (`openai`/`codex-cli`, `native_session_ref` null, reason given, no artifacts, no verdicts), attempt 2 `clean` (`anthropic`/`native-fallback`) | accepted |
| `full-bob-fallback-retry` | `bob` attempt 1 `unavailable` (`openai`/`codex-cli`), attempt 2 `failed` (`anthropic`/`native-fallback`, reason `format-invalid`), attempt 3 `clean` (`anthropic`/`native-fallback`): the substitution spent no retry, the fallback spent its one | accepted |
| `fast-track-delta-clean` | lane `fast-track`, `review_pass` `delta`, `prior_evidence_sha256` set, `base_sha` the rework base; roster exactly `eve` (`required: true`), clean result with `D` verdicts | accepted |
| `full-eve-guard` | profile `codex-gemini`, every result `openai`/`codex-cli`; `eve` resolved by `implementor_codex_present` observed `true` and therefore absent from `excluded_jobs`, clean `google`/`gemini-cli` result with `D` verdicts | accepted |
| `full-missing-alice` | no `alice` result | rejected: `missing_required_job` |
| `full-missing-blake` | no `blake` result | rejected: `missing_required_job` |
| `full-missing-bob` | no `bob` result | rejected: `missing_required_job` |
| `full-eve-guard-missing` | as `full-eve-guard` with no `eve` result | rejected: `missing_required_job` |
| `fast-track-alice-only` | lane `fast-track`, only an `alice` result | rejected: `missing_required_job` |
| `solo-review-free` | lane `solo`, no results, no `reviewer-output` artifact | rejected: `missing_required_artifact`, `missing_required_job` |
| `full-malformed-output` | `bob` terminal result `failed`, reason `format-invalid`, no verdicts | rejected: `required_job_failed` |
| `full-retry-exhausted` | `bob` attempts 1, 2 and 3 all `failed`, each with its own `native_session_ref` (fresh CLI dispatches) | rejected: `required_job_failed`, `retry_limit_exceeded` |
| `solo-escalation` | lane `solo`, `alice` attempts 1 and 2 `failed`, both carrying the same `native_session_ref` (the source retries Alice in her conversation) | rejected: `required_job_failed` |
| `fast-track-delta-missing-eve` | as `fast-track-delta-clean` with no `eve` result (so no `reviewer-output` artifact remains) | rejected: `missing_required_artifact`, `missing_required_job` |
| `full-delta-invalid` | `review_pass` `delta` in both documents, `prior_evidence_sha256` set; the full lane has no delta jobs | rejected: `invalid_expected_context` |
| `full-duplicate-result` | a second `alice` result, also attempt 1, with its own `reviewer-output` artifact, full verdicts and a distinct `native_session_ref` | rejected: `duplicate_job_result` |
| `full-attempt-gap` | the `alice` result numbered attempt 2 with no attempt 1 | rejected: `attempt_sequence_invalid` |
| `full-misattributed-result` | `alice` result with `role_id` `blind` | rejected: `result_misattributed` |
| `full-profile-binding-mismatch` | `alice` result with `openai`/`codex-cli` under `source-parity` | rejected: `profile_binding_mismatch` |
| `full-fallback-without-failure` | `bob` attempt 1 `clean` with `anthropic`/`native-fallback` and no failed primary attempt | rejected: `profile_binding_mismatch` |
| `full-alice-workflow-unavailable` | `consensus_engine` `workflow`; `alice` attempt 1 `unavailable` (`anthropic`/`review-fanout-workflow`, reason `engine_unavailable`, `native_session_ref` null), attempt 2 `clean` (`anthropic`/`native-subagent`) | accepted |
| `full-alice-workflow-failed-fallback` | `consensus_engine` `workflow`; `alice` attempt 1 `failed` (`anthropic`/`review-fanout-workflow`, reason `incomplete`), attempt 2 `clean` (`anthropic`/`native-subagent`) | rejected: `profile_binding_mismatch` |
| `full-alice-engine-mismatch` | `consensus_engine` `legacy`; `alice` attempt 1 `clean` with `anthropic`/`review-fanout-workflow` | rejected: `profile_binding_mismatch` |
| `full-retry-exceeded-in-kind` | `bob` attempts 1 and 2 `failed` (`openai`/`codex-cli`), attempt 3 `clean` (`openai`/`codex-cli`) | rejected: `retry_limit_exceeded` |
| `full-finding-as-completion` | no `bob` result; one finding whose `result_id` is the absent `bob` result id | rejected: `finding_unattributed`, `missing_required_job` |
| `full-findings-mismatch` | `alice` stays `clean` with empty `finding_ids` while one finding names her `result_id` | rejected: `outcome_findings_mismatch` |
| `full-missing-rubric-verdict` | `bob` lacks the `D5` verdict | rejected: `missing_rubric_verdict` |
| `full-duplicate-verdict` | `bob` carries two `D1` verdicts, one `pass` and one `fail` | rejected: `duplicate_id` |
| `full-unknown-rubric-rule` | `bob` carries an extra `D9` verdict | rejected: `unknown_rubric_rule` |
| `full-verdict-unattributed` | one extra `R1` verdict whose `result_id` names no result | rejected: `verdict_unattributed` |
| `full-missing-artifact` | no `review-file` artifact | rejected: `missing_required_artifact` |
| `full-unknown-artifact-kind` | the `review-file` artifact's kind is `review-files` | rejected: `missing_required_artifact`, `unknown_artifact_kind` |
| `full-artifact-unattributed` | one extra `reviewer-output` artifact whose `result_id` names no result | rejected: `artifact_unattributed` |
| `full-clean-without-output` | `blake` clean with empty `artifact_ids` (his artifact removed) | rejected: `result_without_output` |
| `full-findings-without-output` | `bob` is a `findings` result with one consistent finding and full verdicts, his `reviewer-output` artifact and its reference removed | rejected: `result_without_output` |
| `full-unknown-finding-reference` | `alice` is a `findings` result with finding `F1`; a group names `F1` and `F9` | rejected: `unknown_reference` |
| `full-duplicate-finding-id` | `alice` is a `findings` result with two findings both `F1` | rejected: `duplicate_id` |
| `full-stale-policy-binding` | policy and expected context `v1-alt`; `policy_binding.policy_digest` is `v1`'s | rejected: `policy_digest_mismatch` |
| `full-unknown-lane` | `evidence.lane` `canary`, expected context lane `full` | rejected: `lane_mismatch`, `unknown_lane` |
| `full-wrong-profile` | `policy_binding.execution_profile` `codex-gemini`, expected context `source-parity` | rejected: `execution_profile_mismatch` |
| `full-changed-prd` | `source_bindings.prd_sha256` differs from the expected context; results bound to the evidence value | rejected: `source_binding_mismatch` |
| `full-changed-tree` | `head_sha` and `tree_sha` differ from the expected context; results and verification bound to the evidence values | rejected: `source_binding_mismatch` |
| `fast-track-changed-scope` | lane `fast-track`; `scope.refs` names another card; results bound to the evidence value | rejected: `source_binding_mismatch` |
| `full-changed-input-manifest` | `source_bindings.allowed_input_manifest_sha256` differs from the expected context; results bound to the evidence value | rejected: `source_binding_mismatch` |
| `full-stale-result-binding` | one result's `source_binding_digest` is another digest | rejected: `source_binding_mismatch` |
| `full-blind-prohibited-input` | `blake` received a `diff:` ref | rejected: `prohibited_input` |
| `full-unknown-input-kind` | `alice` received a `wiki:` ref (kind outside `input_kinds`, also outside her allowance) | rejected: `prohibited_input`, `unknown_input_kind` |
| `full-reused-builder-session` | `alice.native_session_ref` equals a `builder_session_refs` entry | rejected: `shared_session_identity` |
| `full-verification-invalid` | verification `exit_code` `1`, outcome `passed` | rejected: `verification_mismatch` |
| `full-schema-invalid` | `verification` absent | rejected: `schema_invalid` |
| `full-invalid-context` | expected context roster omits `blake` | rejected: `invalid_expected_context` |

### Local facade

Only these initial public commands are available:

~~~text
python3 <package>/scripts/autopilot.py --list-capabilities
python3 <package>/scripts/autopilot.py --export-policy [--out PATH]
~~~

Capabilities identify the policy, evidence and fixtures contract formats
(`review-policy-v1`, `review-evidence-v1`, `review-fixtures-v1`); they do not
claim a controller, executable skills or host support. Export recomputes/checks the policy digest
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

Historical result: ok (pre-amendment only)

result: ok (2026-10-25 second amendment: N1 blocker resolved by normative
procedure.lanes field table; N2 digest determinism pinned with
ensure_ascii=True and the finite JSON domain; N3 blind-context/reused-identity
cases made expressible via received_input_refs; N4 facade advertises
review-fixtures-v1. Targeted N1 re-verification the same day: resolved, with
checks 1-3 passed against cited normative lines.)

### 2026-10-26 wire-shapes amendment review

Trigger: the Task 2 test author stopped before edits because the nested
shapes were not declared (reports/00012-contract-clarification.md). The
amendment added § Wire shapes; the three-dispatch loop below reviewed it.

Blockers, all fixed in the text: dispatch 1 found the fixture default left
`eve` neither resolved nor excluded, job `implementations` disconnected from
profile bindings, rubric prose embedded in the policy against the PRD,
same-job retries tripping `shared_session_identity`, and Blake barred from
`test-results`; dispatch 2 found an activated job still listed in
`excluded_jobs`, no way to express a fast-track/solo delta pass, fallback
substitution consuming the retry budget, attempt numbering able to hide
history, duplicate rubric verdicts without a code, and the full-lane HIGH cap
rule missing the source's interactive, regression and classifier-failure
branches; dispatch 3 found the delta fixture's defect set incomplete,
`findings` results accepted without their own output, and Alice's
workflow-to-legacy fallback unrestricted. Each has a rule and a fixture now.

- [non-blocker, fixed] open enums in the evidence model: `unknown_artifact_kind`, `unknown_rubric_rule`, `unknown_input_kind` added; a `ran` verification's artifact must be a `verification-log`.
- [non-blocker, fixed] a rubric verdict naming no result: `verdict_unattributed`; missing-job fixtures remove the job's verdicts and artifacts.
- [non-blocker, fixed] `independent_contexts_required` must equal the lane's `independent_contexts`; `fresh_coordinator_review`, `implementor_providers` and `implementor_diversity_guard` are informational here (AP 00017/00020 consume them).
- [non-blocker, fixed] the manifest digest sorts and deduplicates `per_job` values.
- [non-blocker, fixed] `eve: plan` exclusion (the doubt surface stays PRD-only, anchor `rwc-context`).
- [non-blocker, fixed] `native_session_ref` is nullable on attempts that obtained no session; null refs never trip `shared_session_identity`.
- [non-blocker, fixed] an anchor per `required_rubric_sets` entry; fixtures for `outcome_findings_mismatch` and `artifact_unattributed`; Eve's source-parity fallback adapter is `native-fallback`.
- [question, answered] the doubt R1–R5 "standing rule" is the host's global `AGENTS.md` § Workflow, outside the pinned source: `doubt_label_map` is informational and has no binding row.
- [question, answered] `lane_mismatch` precedes `unknown_lane`; every lane-dependent check reads `expected_context.lane`.
- [question, answered] fixture defaults now name the `verification-log` artifact and the duplicate result's own artifact, verdicts and session ref; `full-carl-absent` dropped (it was `full-clean`, which is the optional-provider-absence case).
- [question, answered] rejecting a failed or unavailable required lens is a deliberate redesign of the source's partial-consolidation rule (`BEH-248`, AP 00020), recorded in § Validation result.
- [question, answered] the alternate fixture policy is `v1-alt` (a description change), so its digest differs without contradicting the cap default of two.

dispatch 1 (claude): cardinal-sin 0, blocker 5, non-blocker 7, question 4
dispatch 2 (codex): cardinal-sin 0, blocker 6, non-blocker 0, question 1
dispatch 3 (codex): cardinal-sin 0, blocker 3, non-blocker 0, question 0

Two targeted codex re-verifications followed the dispatch-3 fixes. The first
found two contradictions the consensus-engine binding had introduced (the
fast-track fallback signal must be the engine-unavailable case; the engine
rule applies only to profiles exposing engine adapters), both fixed; the
second returned cardinal-sin 0, blocker 0, non-blocker 0, question 0.

result: ok (2026-10-26 wire-shapes amendment: every blocker from the three
dispatches and the first re-verification is fixed in § Wire shapes; the
second targeted re-verification found nothing open.)

### 2026-10-27 task-slice heading amendment

Promoted the four normative wire subsections from `####` to `###`, with no
contract-text changes in that amendment. Per-file tasks include the shared
Wire shapes definitions verbatim; policy/schema dependencies remain explicit.

Dispatch 1 used the host-native OpenAI worker (`gpt-6.1-sol`, high), not
Anthropic; the pinned `claude` summary token below is the source schema label.
It verified the exact four-line diff and found one non-blocking reminder to
carry shared definitions in every dependent task slice.

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 1, question 0

Dispatch 2 used the real use-sonnet wrapper (`sonnet`, high; external Claude,
tool-less). Raw output: `docs/dev/tmp/ap12-design-heading-review-claude.txt`.
It found two blockers, seven non-blockers and two questions. The attempt-number
wording is clarified above to match the existing committed oracle's distinct
set check; no assertion or fixture expectation changes. The missing inventory
wire-table blocker is rejected: those three artifacts were already completed
in `f39d95e`/`a8a7e4c`, and their committed exact shapes are inputs, not new
schemas for this amendment. Source bindings name existing keys, and raw blob
digests are already verified against pinned git blob bytes. Re-planning them
would violate the operator's completed-work constraint.

Non-blockers/questions are retained in that output: shared preamble scoping,
fixture dispatch size/generator placement, additional branch fixtures,
controller-owned provider enforcement, duplicate names/enums, v2 evolution,
amendment recording, doubt-label mapping and sort collation. The current plan
carries the preamble, measures all slices, consumes committed policy/schema
files and keeps the existing semantic oracle. Provider enforcement remains
explicitly owned by AP 00017/00020, as the prior review ruled. No semantic
expansion or test weakening is authorized by these advisory findings.

dispatch 2 (codex): cardinal-sin 0, blocker 2, non-blocker 7, question 2

Dispatch 3 used the same external Claude transport in a fresh process. It
confirmed the attempt-number clarification, inventory-blocker rejection and
heading amendment: no open cardinal sins or blockers. Four advisory notes
(preamble scoping, log labels, generated slice checks, inventory lookup) and
one pre-existing question (failed-attempt raw artifacts) remain recorded in
`reviews/00012-heading-amendment-verification-claude.txt`. Failed outcomes do
not prohibit raw artifacts; the existing `solo-escalation` fixture tests keep
them, so its expected defects are unchanged. Source `codex` labels for
dispatches 2/3 describe the logical slot; actual transport/provider is Claude
via use-sonnet, not Codex.

dispatch 3 (codex): cardinal-sin 0, blocker 0, non-blocker 4, question 1

result: ok (2026-10-27 task-slice amendment: no open blockers; prior committed
test intent and all normative case expectations retained.)

Dispatch 1 engagement quality retry was completed later in this build after
the coordinator noticed that the first slot's single finding triggered the
mandatory sharper retry despite its five anchored checks. The fresh isolated
native `gpt-6.1-sol` / high reviewer read the complete current draft and
taxonomy. It returned no findings and seven concrete section-anchored checks:
engagement PASS, not WEAK. This is the one permitted quality retry of slot 1,
not a fourth cross-model dispatch. It changed no interface or implementation.
Full result: `reviews/00012-heading-amendment-engagement-retry.txt`.

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 0, question 0

result: ok (2026-10-27 engagement retry complete; no open cardinal sins or
blockers, no weak dispatches.)
