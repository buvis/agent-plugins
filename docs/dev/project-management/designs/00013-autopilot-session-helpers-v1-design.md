# AP00013 — Session-local helpers design

Source: PRD `docs/dev/project-management/prds/wip/00013-autopilot-session-helpers-v1.md`; pinned source `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48`, verified as an existing commit. Source was read with `git show`, never assumed from the working tree. Design pending adversarial review; no implementation.

## Architecture fit

The distributable plugin prepares artifacts, parses findings, classifies supplied evidence and proposes effects. The separate controller owns persistent state, queues, attempts, review acceptance, custody registration, lifecycle transitions and dispatch. Helpers never infer reviewer completion from finding count.

AP00012 supplies normative policy/schema/fixtures and an independent test oracle, not a runtime validator. `tests/autopilot/test_contract_semantics.py:validate_review` imports jsonschema and unittest policy assertions. Production must not import it or move it into the package unnoticed. The local production evaluator checks AP00012 semantics using stdlib, while its independent oracle remains test-only. Its output is advisory, never controller acceptance. It must clearly distinguish semantic checks from complete Draft 2020-12 schema validation; no partial schema interpreter claims full conformance.

Existing source-map assignments conflict with a blanket helper port: 185 selected exact helper regression rows are assigned to AP00019, AP00020 or AP00021. Preserve those controller commitments and append helper-specific dispositions. Never mark controller acceptance passed merely because a helper test passes. No publication, installation, migration or source retirement occurs.

## Module placement

New PRD-listed modules under `plugins/autopilot/scripts/`: `review_stage.py`, `findings.py`, `rework_groups.py`, `gate_lead.py`, `custody.py`, `catchup.py`, `verification.py`. Add `review_evidence.py` for local evidence checks, `review_close.py` for pure classified proposals, `cap_check.py` for regression classification, and `dirty_tree.py`/`log_sink_refusal.py` for pinned verification checks. This keeps source functions visible instead of burying approximately 900 lines of read-only checks in unrelated files.

Edit existing `scripts/autopilot.py`, `contracts/review-fixtures-v1.json`, package README/CHANGELOG, and maintainer `tools/autopilot/source-map.json`. New tests follow PRD paths, adding focused evidence/cap tests if needed. Package imports stay inside the plugin. No fallback to source checkout, author home or runtime modules.

## Interfaces & contracts

Each subsection is a task-scoped contract. Python uses explicit `Path` inputs; JSON objects have the named fields. Invalid caller shapes raise ValueError; unreadable explicit inputs raise OSError unless specified otherwise. Public functions reject unknown request fields. Helpers support Python 3.10+ stdlib; verification can use platform facilities already used by the pinned Unix source. Tests run under the mandated Python 3.12 command.

### Common boundary

The helper protocol is version 1. Every new facade JSON request file is an object with schema_version: 1 (a real integer, never bool/float). Stage/prepare-close requests put their keyword fields beside it; the facade strips only this envelope field before calling the library. --group-findings reads {schema_version: 1, findings: [...]} and returns {schema_version: 1, ok: true, groups: [...]}. --check-evidence reads {schema_version: 1, evidence: <AP00012 evidence>}; --expected-context reads {schema_version: 1, expected_context: <AP00012 context>}. --policy consumes the already-versioned AP00012 policy unchanged. Nested AP00012 objects retain their exact original schema, with no added fields. Missing, unknown or higher helper versions are usage errors (exit 2) before effects. All new report/error dictionaries from public report functions and the facade include schema_version: 1; pure Row/list/string utility returns remain Python API values versioned by package semver and are enveloped at the facade boundary. Python API breaking changes require a package major version and a new facade protocol major; version-1 wire changes stay additive only where the schema explicitly allows them. No preexisting durable helper state exists to migrate.

--list-capabilities retains its existing JSON array format and three original versioned capability IDs. Add versioned operation IDs stage-review-v1, group-findings-v1, check-evidence-v1, prepare-close-v1, catchup-probe-v1, verification-artifact-v1 and controller-required-v1 only when implemented. --export-policy keeps the exact AP00012 schema_version=1 canonical policy format. Neither legacy operation is rewrapped.


Lifecycle refusal is `{"schema_version": 1, "ok": false, "error": "controller-required", "operation": <string>}` before request-file reads or writes. Helpers never discover OVCAQ, import runtime modules, read/write the executing project's live `docs/dev/project-management/autopilot/`, create markers, move PRDs, persist tasks/attempts, commit the store, dispatch reviewers or invoke supervisors.

All artifact destinations are explicit. Relative paths resolve against explicit project_root. Validate planned output paths before writing. Refuse live state, Git internals, tracked outputs, nested repositories, symlink components below the supplied root, executable/nonregular/multiply linked existing files, or escape from the explicit artifact root. Preserve unresolved paths for symlink checks. Explicit optional snapshots are in-memory JSON or report files outside live state; they never authorize discovery. Verification log paths additionally preserve the pinned descriptor-relative no-follow protections.

### findings.py / gate_lead.py

```python
class Row(NamedTuple):
    ref: str
    severity: str
    file: str
    issue: str

def reviewed_rows(text: str) -> tuple[list[Row], str | None]: ...
def finding_key(severity: str, file: str, issue: str) -> tuple[str, str, str]: ...
def strip_lead(line: str) -> str: ...
```

Preserve pinned `findings_section._reviewed_keys`. Problems are None, `no-section`, `unreadable-table`. Parse first Consolidated Findings H2 through next H2, bullet and named-column tables, optional Ref/Task columns, uppercase normalized R-digits refs, bracketed consensus, emoji/word severity. Right-split issue pipes. Malformed/truncated table rows, duplicate refs or missing terminal pipes make the table unreadable instead of hiding findings. Normalize escaped pipes/whitespace/severity prefixes consistently; display issue keeps case, finding key lowercases it.

`strip_lead` preserves source `_strip_lead`: repeat ordinal, checkbox, comment/details, inline-code/link and Unicode P/S/Z/C/M leads; exclude bare Ps/Pe brackets; include Hangul filler U+3164; stop before severity emoji. It is lexical classification, not review acceptance.

### rework_groups.py

```python
NON_CRITICAL_CAP = 4
def file_key(file: str) -> str: ...
def group(findings: list[dict]) -> list[dict]: ...
```

Input requires file string and severity emoji from 🔴/🟠/🟡/⚪, retaining all other fields. The AP00012 adapter converts severity words without mutating evidence. Output groups contain name_hint, critical, findings. Critical singleton groups retain input order and do not count toward cap. Strip repeated source citation suffixes; only full N/A maps to general; markdown shares prose. Above four noncritical groups: general merges into smallest code group, then deepest shared directory, smallest combined pair, lexical keys; absent shared directory becomes mixed. Preserve within-group finding order. Sort noncritical groups by worst severity, descending size, key. Never mutate input.

### review_evidence.py

```python
def load_policy() -> dict: ...
def check_evidence(policy: dict, expected_context: dict, evidence: dict) -> dict: ...
```

Load policy/schema only from packaged contracts. A supplied policy must satisfy the complete AP00012 normative policy shape/invariants and its own canonical digest; it need not byte-equal the packaged policy. In particular the existing v1-alt execution-profile fixture remains a valid policy and earns policy_digest_mismatch for stale submitted binding, not invalid-policy. load_policy returns the packaged default; explicit policy input is independently checked. Implement exact field-specific input shape checks for the AP00012 fields consumed below; reject booleans where integers are required, invalid enums, unknown/missing object fields and duplicate IDs before indexing. This is a contract-specific checker, not a generic JSON Schema implementation. Differential schema tests use test-only jsonschema to expose holes.

Implement all AP00012 semantic checks: independent source bindings/digests; lane/roster/activation/exclusion correctness; result attempts and provider/adapter/fallback history; finding/group/result/artifact attribution; complete required results and rubric namespaces/rules; allowed per-job inputs; reviewer-context independence from builders; verification/source compatibility. Expected context is supplied independently from current inputs, never derived from submitted evidence. Clean completed results satisfy completion with no findings. Missing/failed/unavailable results do not. Forbidden blind inputs stay forbidden even when other jobs may receive them.

Return `{"schema_version": 1, "ok": true, "checks": "local-contract-v1", "evidence_valid": true, "controller_required": true}` or `{"schema_version": 1, "ok": false, "error": "invalid-evidence", "defects": <sorted AP00012 defect strings>}`. Match the AP00012 oracle defect set on every existing fixture. Do not return its authoritative-sounding `accepted` token. Validation does not certify host execution or advance phase.

### review_stage.py

```python
def render_tasks(tasks: list[dict]) -> str: ...
def findings_precedent(pack_text: str | None) -> str: ...
def stage_review(*, project_root: Path, artifact_root: Path, cycle_id: str,
                 tasks: list[dict], prd_text: str, design_text: str | None,
                 context_text: str, diff_text: str | None,
                 expected_context: dict, input_texts: dict[str, str],
                 pack_text: str | None = None, settled_text: str | None = None,
                 prior_findings_text: str | None = None,
                 test_gate_text: str | None = None) -> dict: ...
```

cycle_id matches `[A-Za-z0-9][A-Za-z0-9._-]*`. Validate expected context before output. Encode prd_text exactly as UTF-8 without trimming, newline insertion or normalization, and require SHA-256 equality with expected_context.source_bindings.prd_sha256 before any write. The staged raw PRD preserves these exact bytes. The PRD input_texts ref must carry exactly that same content. Supplied repo-tree refs must name expected_context.source_bindings.tree_sha; these are explicit identities, not permission to query workflow state. All non-PRD input_texts are explicit caller-provided content under the validated per-job manifest; this helper does not certify their external origin. Mismatched PRD content or repo identity refuses invalid-input before output. input_texts keys are AP00012 refs; every required per-job ref needs supplied content or a declared explicit reference. Never select a lane/roster or discover CLI availability. Use the independently resolved expected context.

Write review-tasks-ID.md, review-prd-raw-ID.md, review-prd-ID.md, review-context-ID.md, optional review-diff-ID.diff and JOB-prompt-ID.md beneath artifact_root. Raw PRD remains authoritative for blind input, including literal Design Doc headings inside the actual PRD. Only merged nonblind PRD appends design. Task rendering escapes pipes/newlines and retains each folded task/shared commit/companions. Missing optional pack uses pinned fallback text; precedent section stops at same-or-higher heading.

Reuse packaged personas/rubrics/checklist/output formats. Adapt preflight to packaged metadata, not omitted host tools registration. Preserve source Alice/Carl normal inputs, Bob's Eve doubt appendix and citation rule, and Eve's five run inputs. Apply policy allowed refs before rendering. Blake gets raw PRD, blind rubric/output and only explicitly allowed test-results; never design, diff, file list, task table, history, pack, mechanical facts, sibling findings or broad context path. Isolation includes references/paths as well as text. Substitute known template tokens once; injected text containing tokens is not reprocessed.

Return `{"schema_version": 1, "ok": true, "artifacts": [{"kind": <local helper kind>, "path": <absolute string>, "sha256": <hex>}], "prompts": {<job>: <absolute path>}, "input_manifest": {<job>: <refs>}}`. Do not extend AP00012 evidence artifact enums to describe these local reports. No dispatch rows, state stamps or completion claims.

### review_close.py

```python
class CarryTaskSnapshot(TypedDict):
    id: str
    name: str
    carry_refs: list[str]
    carry_cycle: int
    escalation_reason: Literal["review_flag", "fable_rescue"]
    status: str

class CloseReadSnapshot(TypedDict):
    cycle: int
    tasks: list[CarryTaskSnapshot]
    rework_task_ids: list[str]
    decision_gate_review_ref: str | None
    deferred_decisions: list[dict]

def prepare_close(*, policy: dict, expected_context: dict, evidence: dict,
                  review_ref: str, review_text: str,
                  chosen_findings: list[dict], cycle: int,
                  batch_id: str, default_tier: str,
                  read_snapshot: CloseReadSnapshot | None = None) -> dict: ...
```

First require local evidence validity. Require exactly one evidence artifact of kind review-file with path equal to review_ref; hash review_text encoded as exact UTF-8 with no normalization and require its sha256 to match that artifact. Every chosen consolidated row carries finding_ids: list[str], nonempty and unique. AP00012 findings project to parser rows as follows: severity maps critical/high/medium/low to 🔴/🟠/🟡/⚪ for source grouping; issue is finding.title, not finding.evidence; file is finding.file or N/A when null. Normalize severity/file/title through finding_key. The finding.evidence body, task_ref and result_id remain unchanged in the proposal's linked source findings. Each linked finding must match the consolidated row's normalized severity/file/issue. Several independently attributed findings may link to one row when these keys agree. Different normalized titles remain separate rows; speculative semantic title merging is not certified by this deterministic helper. Every evidence finding appears in exactly one row's links, with no missing, unknown or multiply linked finding ID; clean evidence therefore requires zero consolidated rows. Derive found_by as distinct reviewer job_ref values reached through each linked finding.result_id in validated reviewer_results. If caller found_by is present, its distinct values must exactly match that derived set. Duplicate reports from one reviewer count once. Reject conflicting or duplicate chosen refs before proposals rather than creating duplicate tasks. Verify/discard bookkeeping rows that the source permits outside the consolidated table have no finding_ids and cannot contribute tasks or consensus. A ref selects its matched consolidated row and cannot introduce a new finding. Refuse artifact/content/attribution mismatches before proposals. Then cross-check chosen findings against consolidated rows by normalized severity/file/issue or unambiguous ref, never merely their count. Classifications preserve pinned gate.KNOWN_CLASSIFICATIONS exactly: verify/discard/fix/defer/carry. Preserve source exceptions for verify/discard, duplicate-ref conflicting classifications, full coverage, and ref-required checks; do not invent unconditional critical classification. Malformed/mismatch/uncovered/ref-required refuse before proposal generation. Do not inherit source legacy no-section application escape hatch for new AP00012 evidence.

Port pure `_mutation_context`, `_findings_block` and `_add_decisions` transformations from pinned review_close without its mutator. Fixes are grouped through rework_groups; proposed task fields are name=`[D<cycle>] <prefix><name_hint>`, description=`### Findings (verbatim)` followed by source-format rows, model=default_tier; prefix is `Tail sweep: ` only for batch_id tail-sweep. Output has `schema_version: 1`, `ok`, `controller_required: true`, `task_proposals`, `decision_proposals`, `rubric_verdicts`, `reviewer_results`. Task proposals have no durable IDs. Deferred proposal preserves cycle/issue/emoji severity/file/action=deferred/reason. Fix proposal preserves cycle/issue/word severity and action=fix-proposed, avoiding source's premature auto-fixed claim. Verify/discard/carry proposals retain their supplied classification/reason without new task creation. Extract rubric/result completion from validated evidence, not source agents frontmatter or finding count.

Preserve `_single_voice_refusal`: decision-gate medium/low fix needs two distinct list-valued found_by entries; missing/nonlist is zero. Tail sweep needs two distinct finders for every row. A carry row needs supplied read_snapshot tasks/rework_task_ids/current cycle proving one unfinished task with matching carry_refs, carry_cycle, rework membership and review_flag/fable_rescue escalation. Missing snapshot refuses controller-required; never discover it. Tail sweep preserves ordered refusals: carry, missing current-review decision-gate receipt, empty, above medium, single voice, duplicate open deferral by normalized severity/file. Supply receipt/open deferrals explicitly in read_snapshot; never infer them. Tail sweep proposes no lens close-out. No applied-review-batch stamp, dispatch end call, statectl import, task persistence or authoritative lens state is emitted.

The snapshot is read-only caller data, never a discovered file. Require snapshot.cycle == cycle. For tail sweep, require snapshot.decision_gate_review_ref == review_ref exactly; a receipt from another review is insufficient. Only actual list entries that are validated reviewer job IDs count for found_by; caller labels cannot invent a second reviewer. Missing snapshot required by carry/tail-sweep returns controller-required; malformed supplied snapshot returns invalid-input. Carry matching normalizes refs uppercase and requires one task satisfy all conditions; completed tasks cannot satisfy it. Distinct finder count uses unique list entries, not raw list length. Deferred matching normalizes both emoji and word severity and strips file whitespace. None of these checks writes, reapplies or manufactures the supplied controller receipt.

### cap_check.py / custody.py

```python
class CapCheckError(RuntimeError): ...
def classify_findings(*, repo_root: Path, review_text: str,
                      previous_head: str | None, head: str) -> list[dict]: ...
def capture_range(repo_root: str, git_dir: str | None, base: str) -> tuple[str, int, str]: ...
def upsert_entry(entries: list[dict], entry: dict) -> tuple[list[dict], bool]: ...
def marker_entry(prd: str, batch: str, op_id: str, detail: str, capture: dict) -> dict: ...
def refresh_hold_prd(text: str, entry: dict) -> str: ...
def migration_records(snapshot: dict, op_id: str, prd: str) -> list[dict]: ...
```

Cap takes heads explicitly instead of inferring current truth from evidence/frontmatter. Missing previous head returns []; medium/low-only makes no Git calls. Require full 40-hex commits, distinct range, previous ancestor of head, head reachable from HEAD; normalize to Git toplevel. Preserve multipath/backtick/annotation/absolute/unambiguous casefold and every-line parsing. Any unresolved path/cell returns regression=null, never false; introduced rework line or first file/subtree touch yields true with abbreviated commit; otherwise false. Missing-path detection reads Git stderr only; unrelated corruption raises. Output source fields ref/severity/file/line/regression/commit and optional reason.

capture_range uses explicit repo/git-dir/base, captures HEAD once, preserves empty-tree/detached/bare-backed support, 30-second timeout, and returns range/count/branch. Pure constructors/upsert/hold-text/migration retain source semantics, original deferred index/type/cycle, 20-line closed-frontmatter rule, same-batch notice replacement, insertion fallback and idempotence. Any notice instructing custody resolve must identify controller requirement. No disk writes, marker/journal loading, locks, pending discovery, implicit project root, configuration locator, branch pin, revert/reset, record_critical, mirror mutation, cleanup or resolve implementation.

### catchup.py

```python
def probe(project_root: Path, *, run=subprocess.run, which=shutil.which) -> dict: ...
```

Only gh auth status and engram status --scope repo, explicit cwd, captured text, timeout 15 seconds each. Missing binary/OSError/timeout => absent. gh zero=>ok, otherwise unauthenticated. Engram exact stderr marker `not inside a registered repo`=>unregistered, otherwise ok even nonzero, preserving source fallback. Return schema_version=1, gh token, engram token, skip list; github-state first when gh not ok, engram second when engram not ok. No batch cache/state discovery/persistence. Probe success never narrows required review.

### verification.py / dirty_tree.py / log_sink_refusal.py

```python
GATE_TIMEOUT_S = 1800
GATE_OUTPUT_CAP = 2_000_000
GATE_LOG_CAP = 20_000_000
def run_verification(*, argv: list[str], project_root: Path, head_sha: str,
                     artifact_path: Path, log_path: Path,
                     timeout: float = GATE_TIMEOUT_S) -> dict: ...
def reuse_verdict(*, prior: dict | None, argv: list[str],
                  project_root: Path, head_sha: str) -> tuple[str, dict]: ...
```

Require timeout to be a finite number greater than zero and no greater than GATE_TIMEOUT_S; booleans are invalid. Require nonempty argv/executable; shell=False, preserve token bytes, process-group isolation and deadline-bounded drain/exit. Stream real stdout/stderr to explicit safe log; retain final 2MB stdout. Bound combined on-disk stdout/stderr log bytes to GATE_LOG_CAP. Before a chunk would exceed the cap, write only the remaining permitted bytes, terminate/reap the process group, and return output_limit_exceeded=true with reusable=false. Output overflow is a failed verification result, never a green run; the facade exits 1. The hard timeout includes drain and child exit. Last PASS n FAIL n SKIP n EXIT n wins; preserve actual process exit separately from summary EXIT. A command without this summary still returns actual output/exit but is not reusable as a source gate. Close/reap pipes/children; kill group on deadline or log-write error. No default workflow lock/last-verification lookup/deletion/write.

Artifact exact fields: schema_version=1, kind=verification-artifact-v1, argv, head_sha, exit_code (int/null), summary ({passed,failed,skipped,exit_code} integer fields/null), timed_out boolean, output_limit_exceeded boolean, dirty_paths string list, head_moved boolean, log ({path,sha256}), reusable boolean. Return `{"schema_version": 1, "ok": true, "artifact": <object>, "controller_required": true}` after an attempted run, even a failing command; facade exit reflects failure. Pre-spawn refusal returns ok=false with error dirty-tree/head-moved/unsafe-artifact-path and writes no reports. Refuse overlapping output/input or equal log/artifact paths.

Preserve pinned NUL porcelain, rename/copy both paths, toplevel prefixes, forced untracked status, hidden index flags, Git error refusal, changed-store targets through product symlinks, endpoint diff for merge resolution, exact self-log exclusion and tracked-log refusal. Dirty-run exclusions retain source store/scratch roots; committed reuse tolerates management-store changes only. Preserve Git main/common-dir inode identity, linked-worktree .git pointer, nested repo, symlink/hardlink/executable/nonregular checks, descriptor-relative O_NOFOLLOW parent descent and exclusive leaf creation. Validate both artifacts before spawning. Post-run dirt/head movement invalidates reusable evidence.

reuse_verdict yields (stale,{}) or (reused,prior). Strict artifact shape/types, full lowercase SHA, identical argv, reusable=true, output_limit_exceeded=false, actual exit zero, summary counts present with failed=0 and EXIT=0, then ancestor/clean/unchanged-product checks. Missing/failed/changed/dirty/nonancestor/Git-error evidence is stale. No whitespace normalization within argv arguments.

### autopilot.py facade

Preserve existing --list-capabilities and --export-policy [--out PATH]. New mutually exclusive operations:

```
--stage-review REQUEST_JSON
--group-findings FINDINGS_JSON
--check-evidence EVIDENCE_JSON --expected-context CONTEXT_JSON [--policy POLICY_JSON]
--prepare-close REQUEST_JSON
--catchup-probe --project-root ROOT
--verify --project-root ROOT --head-sha SHA --artifact PATH --log PATH [--timeout SECONDS] -- ARGV...
--controller-action OPERATION
```

Requests map exactly to function keyword names; paths explicit. --check-evidence uses load_policy() when --policy is absent and otherwise reads that explicit policy JSON; alternate valid policies are available to both library and facade. prepare-close request carries expected_context separately from evidence within named sibling fields and explicit cycle/batch/tier. It only emits proposals. Cap/custody pure library APIs are not advertised as complete workflow operations. Exit 0 successful preparation/probe/check; 1 invalid evidence or real verification failure; 2 usage/input/path errors; 3 controller-required. One JSON value stdout; diagnostics stderr. Lifecycle refusal happens before request reads, adapter import, output writes or runtime lookup. Capabilities advertise implemented helpers only; existing skill execution gates stay intact.

## Data flow

Explicit PRD/tasks/source identity/current expected context enter staging, which validates destinations and isolates per-job prompts. Reviewer evidence later enters local checks against policy/current expected bindings. Findings feed normalized cross-check, grouping, regression classification and custody/task/decision proposals. Verification executes explicit argv and emits explicit reports. A later controller may submit/apply results; this PRD does neither.

## Reuse inventory

Sweep used rationalizations verb/noun synonyms. Verbs: render/format/serialize, parse/read/load/decode, validate/check/verify/assert, group/merge/classify, probe/capture/reuse. Nouns: review/persona/prompt/findings, evidence/binding/roster/rubric, verification/dirty/log/artifact, catchup/engram/custody/state. Search roots: packaged scripts, tests/autopilot, tools/autopilot. Positive controls reviewer_results and review-policy confirm search shape. No installed helper implementation found.

- Existing facade: extend argparse and contained canonical policy loading.
- AP00012 policy/evidence/fixtures: normative source; do not weaken enums/semantics.
- AP00012 semantic/schema tests: independent differential oracle only; never production import.
- Packaged personas/rubrics/checklist/output format: prompt resources, adapted metadata preflight.
- `tools/autopilot/map_slice.py`: existing bounded stale-snapshot/diff pattern for assets/resource_edges; it does not support behaviors/regression_cases.
- Pinned pure helper functions: semantic extraction with explicit inputs, no runtime imports or wholesale mixed-module copies.

## Alternatives considered

1. Smallest textual diff: copy mixed source files and disable writers. Reject: implicit roots/runtime imports/record deletion remain.
2. Extract pure functions and read-only probes with explicit artifact I/O and advisory evidence checks. Choose: additional focused modules expose ownership and keep task prompts small.
3. Generic workflow/schema engine/artifact database. Reject: duplicate controller ownership and unnecessary abstraction. A complete field-specific AP00012 checker is bounded by one contract, not a claimed general schema engine.

## Risks & edge cases

Evidence checking is substantial work. All closed field shapes must match AP00012 schema on consumed inputs; differential tests retain independent schema validation. Never equate zero findings, valid local evidence or a clean verification report with accepted runtime review.

Mapping conflicts must be reported and retained. Add top-level helper_dispositions keyed by source module:function and source_regression_id with target scenario, owner scope, controller exclusion and evidence reference; preserve all existing identity/digest/owner fields and controller evidence. Test validator acceptance and byte-semantic equality of unrelated arrays. Use bounded projections rather than opening the 13.66MB map in task prompts.

Likely next changes are controller submission, adapters and host certification. Explicit proposals and per-job refs leave room for these without creating state today. Source historical test names can contradict newer null/stall assertions; characterize actual pinned assertions. Do not inherit legacy review-close permissiveness for new evidence.

## Test strategy outline

Every helper uses temporary project repos/explicit roots. Poison state/ledger/marker paths; guard opens and subprocesses to detect reads as well as mutations. Assert no queue/branch/session effect, no runtime lookup and unchanged poison bytes. No helper invocation against this batch's own live state.

Named scenarios: helper_source_parity; review_preparation_no_state; finding_group_equivalence; catchup_optional_absent; verification_artifact_reuse; local_helpers_without_ovcaq; no_hidden_workflow_state; controller_action_not_yet_wired; source_inventory_mapping. Cover clean versus missing reviewer results, stale PRD/code, blind references/paths, malformed table rows, citation/group ordering and immutability, cap missing/corrupt Git paths, pure custody text/capture/migration, optional probe timeouts and peculiar engram fallback, real command exits/stdout/stderr, summary disagreement, output timeout/child cleanup, dirty/hidden flags, rename directions, product/store symlinks, merge resolution and safe sink races.

Run all AP00012 golden/adversarial fixtures through production and independent oracle; compare exact defect sets after outer-token mapping. Preserve test-only schema validation and add malformed/boolean/unknown fields. Review-close tests cover normalized/ref cross-check, complete classification, grouped task proposals, no premature auto-fixed claims and tail-sweep restrictions. Stateful source writer/lock/record tests are explicit controller exclusions, not successful helper equivalents.

Practical task split: (1) source characterization/dispositions/fixtures; (2) finding parser/lead/groups; (3) production evidence checker; (4) staging/blind isolation; (5) review-close proposals; (6) cap/custody pure extraction; (7) catchup; (8) dirty/log primitives; (9) verification runner/reuse; (10) facade/public boundaries; (11) source-map receipts/docs/changelog. Roughly 150–400 production lines per normal task; verification up to 600 from existing logic. Use each task's module contract/relevant source extracts, never the entire map/design. Complete task prompts remain <=50KB. Recheck source and ownership before each edit.

Completion gates: targeted tests, full `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`, validator unit suite and `python3 scripts/validate.py`. Record real-host execution unavailable. Preserve required fresh-session full-lane completion review after build handoff.

## Review log

Dispatch 3 completed through the real guarded external wrapper, requested Anthropic Sonnet/high with no tools; the wrapper text does not expose the exact served model. Raw output is retained in the sibling review artifact.

dispatch 3 (codex): cardinal-sin 0, blocker 1, non-blocker 9, question 3

- Resolved blocker: every new wire request/report now has a version-1 envelope and unknown-version refusal, while legacy capabilities/policy formats and nested AP00012 schemas remain intact. Pure Python values use package semver. No new workflow state or migration is introduced.
- Count note: the reviewer header said eight non-blockers but emitted nine non-blocker finding objects; the summary records the actual objects.
- Retained non-blockers: exact-title consensus is intentionally conservative; title normalization needs table-equivalent fixtures; refusal tokens/exits need explicit task treatment; input-reference/root spelling needs explicit task treatment; staging write races/partial sets remain a concern; boundary guards must cover os.open/subprocess reads; nonverification input/Git bounds need task treatment; missing previous-head [] preserves source but requires caller awareness; verification needs a POSIX availability guard.
- Retained questions: carry matching/status/table bookkeeping linkage; whole-map digest/concurrency implications; stdout/stderr log versus retained summary tail.
- Earlier mandatory fixes were independently rechecked as holding. The sole final mandatory finding is resolved in this design; no cardinal sin or blocker remains open. No fourth design dispatch runs.


Dispatch 2 external output was unparseable; source outage fallback completed with isolated native gpt-6.1-sol/high (OpenAI). No successful independent-provider review is claimed.

dispatch 2: codex unavailable, Claude fallback
dispatch 2 (claude-fallback): cardinal-sin 0, blocker 2, non-blocker 1, question 1

- Resolved blocker: AP00012 finding.title projects to issue, null file to N/A, evidence body and result attribution remain intact.
- Resolved blocker: explicit finding_ids supports many-to-one matching of identical normalized finding keys; derived distinct validated reviewer jobs supply consensus counts, never caller labels.
- Non-blocker checked correct: verification resource and failure bounds are explicit.
- Question addressed as an interface omission found by the coordinator: optional --policy supplies the library policy input; packaged policy remains the default.


Dispatch 1 used the host-mapped native reviewer gpt-6.1-sol/high (OpenAI), isolated from coordinator history. Complete taxonomy and draft were supplied in docs/dev/tmp/ap00013/design-review-1-prompt.md.

dispatch 1 (claude): cardinal-sin 1, blocker 2, non-blocker 1, question 1

- Resolved cardinal sin: verification now caps disk logs at 20,000,000 bytes, kills/reaps on overflow, and rejects nonfinite or excessive timeouts.
- Resolved blockers: stage PRD bytes must match the independent digest; review-close binds exact review artifact bytes and attributed evidence findings before producing proposals.
- Coordinator consistency correction: explicit valid alternate policy inputs remain supported, preserving the existing v1-alt golden defect expectation.
- Non-blocker retained: staging path checks and writes may race a concurrent parent-directory replacement; only verification explicitly mandates descriptor-relative writes. Reviewer's suggested shared safe writer is not adopted in this design pass.
- Question retained: declared input reference representation and verification artifact-root spelling need clarification in task contracts; input_texts currently carries strings and verification has project_root only.

External dispatch 2 attempted Anthropic Sonnet/high through the installed guarded wrapper with tools disabled. It exited 0 but returned only unexecuted Read/Bash invoke tags, not findings; raw output is preserved in docs/dev/tmp/ap00013/design-review-2-output.md. Per the source outage rule, dispatch 2 falls back to a fresh isolated host-mapped native reviewer. No successful cross-provider design review is claimed.

Unresolved questions: retained advisory questions above require explicit task contracts, not an operator decision. No open cardinal sin or blocker remains.
