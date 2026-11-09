
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: Recheck exact pinned source hashes and ownership map

Description:
Recheck pinned kernel ownership and protocol characterization

Location: plugins/autopilot/contracts/controller/provenance.json, docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md

Reuse: Existing StateStore, PrivateLayout, bootstrap protocol, controller test support and map generator.

Contract (verbatim):

### Recovery and delivery

Preserve held v1 PRD, receipts, reviews and attempt counters. Re-characterize existing behavior against pinned OVCAQ source before reuse. Do not import old completion flags. All v2 tasks use normal planner budgets and retain independent test writers and patch review. Owner/capacity/recovery tests are mandatory acceptance, never baseline exemptions. Keep package unavailable entry gates and pending custody unchanged.

Refresh tools/autopilot/source-map.json through its generator. Historical AP00013 delivery receipts remain immutable. If shared README/CHANGELOG bytes require later ownership, introduce an explicit tested successor receipt bound to the current revision and raw file digest; do not repin historical receipts or exempt paths. tests/autopilot/test_helper_provenance_real.py and test_package.py must verify successor evidence against current package bytes and actual test results. Final full implementation suite and repository validator must pass. No publication/install/source retirement/push.

### Kernel

Python floor is 3.12; stdlib only. `autopilot_state.schema` exports `SCHEMA_VERSION = 1`, `MAX_STATE_BYTES = 16777216`, `MAX_COMMAND_PAYLOAD_BYTES = 2097152`, `MAX_STRING_BYTES = 1048576`, `MAX_JSON_DEPTH = 32`, `MAX_JSON_INTEGER_DIGITS = 640`, `SchemaError`, `ResourceLimitError`, `decode_json(text: str, *, source: str)`, `validate_state(value: object) -> dict`, and `new_state(*, repo_root: Path, project_id: str, workflow_id: str) -> dict`. Reject duplicate JSON keys, nonfinite numbers, bool integers, unknown owned fields and unsupported durable versions; validate before deep copying. Default review cap is 2. Reject process identity, PID, launcher, heartbeat, resource usage and TUI state as workflow fields. Model/session observations later arrive only as explicitly bounded workflow evidence, never execution authority.

Retain source `StateStore(path: Path, *, boundary_hook=None)`, `read()`, `initialize(initial)`, `transaction(mutator, *, expected_revision=None, publication_guard=None)`, `restore(*, expected_revision=None, precondition=None)`, source exception names and six `DurabilityBoundary` values. Preserve source lock/read/publication guards, single-link regular-file checks, bounded reads, CAS under exclusive flock, deep-copy mutation, revision increment, fsync-before-replace, backup/state pair repair and create-only initialization. Keep one last-good `.bak` and `.lock`; failed validation/conflict/publication cannot change the pair. Restore is an offline forensic library primitive, never a CLI operation or a protocol recovery path. It requires readable valid current state and valid backup and refuses with BackupError unless backup lease_epoch, owner, actors and receipts exactly equal current and no credential-intent.json exists. Check these invariants under the same exclusive lock after decoding backup and before any pair publication; precondition(current) alone is insufficient. Only security-identical backups may be restored, with current revision +1. This deliberate tightening of source restore prevents epoch rollback, credential resurrection and receipt loss; characterize it explicitly. Test acquire followed by restore refuses with exact state/backup/credential bytes preserved, and a security-identical backup restore retains source revision and repair outcomes. Corrupt current state refuses with recovery_required and preserves bytes for operator forensic recovery. Never silently overwrite corruption. Test backup/restore and each injected boundary. Unsupported directory fsync refuses explicitly.

`resolve_project_root(path: Path) -> Path` resolves an existing directory without ancestor workflow inference. The private controller store is `<project-root>/.autopilot/controller/`, directory 0700, with `state.json`, `state.json.bak`, `state.json.lock`, and `actors/`. Before creating any credential, create regular private `.gitignore` files containing `*\n` in both `.autopilot/` and the private controller directory (parent 0700, files 0600; sibling archives are ignored too), refuse an existing incompatible or aliased ignore file, and verify a temporary Git repository ignores state and actor files. This is separate from the implementation batch's legacy state. Reject symlink components below the resolved project root, escapes, nonregular/multiply-linked artifacts and payload-selected state paths. Preserve directory descriptor/no-follow creation and ancestor inode identity rechecks from the pinned root resolver; Path.resolve containment alone is insufficient. Project identity is SHA-256 of the resolved root's UTF-8 path. Relocating the installed package preserves functionality; relocating an existing project requires explicit future migration, not identity rewriting.

Durable state has closed top-level keys `schema_version`, `revision`, `project_id`, `workflow_id`, `repo_root`, `lease_epoch`, `owner`, `actors`, `receipts`, `workflow`. `workflow` is exactly `{batch: null, work: null, tasks: [], review: {cap: 2}, recovery: null, jobs: []}` in this kernel; no operation may mutate these reserves. Later producer PRDs define their expanded schemas and migration. Characterization records each source workflow field and its deferred owner; it does not import process fields or claim full legacy schema equivalence. No generic JSON setter is exported. `owner` is null or `{actor_id, mode, native_session_id, lease_epoch}`; `mode` is `manual|supervised`. `actors` contains descriptors, never credential secrets. `receipts` maps request IDs to canonical request digests, actor binding and complete original responses. `jobs` is empty and cannot be mutated in AP00018. Actor registry retains only the current operator and current owner descriptors (at most two); historical authorizing digests are receipt-owned, never actor rows. Normal receipt admission stops at 4094 entries. Before writing durable intent or any final credential, serialize and validate the complete candidate and complete response. Normal operation candidates may occupy at most 14680064 bytes (14 MiB), leaving 2097152 bytes for the two emergency operations below the 16777216-byte state ceiling. Each stored core response is bounded to 65536 UTF-8 bytes, including all absolute paths; refuse a root/response that cannot meet this bound before bootstrap. Emergency release/recover may use the reserved bytes only when clearing an active owner; their complete candidate must still validate under the state ceiling. A no-owner call cannot consume reserve capacity. Maximum response/descriptor growth for both emergency operations fits within 2 MiB under these explicit core bounds; test byte saturation independently of receipt-count saturation and reject oversized candidates before preparing intent. This prepublication check is part of the transaction admission, not a later _canonical_bytes failure after credentials changed. Reserve two further slots exclusively for owner.release/owner.recover; these may clear an active owner at saturation, never acquire a new one. At 4096 entries the workflow is sealed against all new mutations; exact receipt retrieval and snapshot remain available. Capacity is an explicit terminal boundary, not an unspecified future repair. Operator exit procedure: finish/reconcile jobs (none supported here), release/recover ownership using reserve capacity, verify an owner-null snapshot, copy the entire private controller directory to a private offline archive and verify every file hash, then rename the original private directory into a sibling private archive named by workflow ID, and open a new workflow at the fixed empty controller path. Never delete the archive. Archived state, credentials, receipts and schema remain replayable by placing the original directory back at its original project binding while the new workflow is offline; never merge identities. README documents the ordered manual procedure; tests saturate normal capacity, clear the owner through reserved capacity, validate the archive/hash/restore roundtrip and open a distinct workflow. No archival or state removal runs automatically. If an active owner reaches hard capacity through externally corrupted state, return recovery_required and retain all evidence rather than overriding it. Top-level `lease_epoch` starts at 0 and increases on acquire/recover/release, retained even while owner is null.

### Protocol

CLI argv is `["python3", "<installed-plugin-root>/controller/main.py"]`. Commands are `--json contract`, `--json snapshot --project-root PATH`, `--json apply --project-root PATH --request FILE`; apply accepts `--actor-file PATH`. No shell invocation or process launch. Request file limit is 2097152 bytes; snapshot/response output limit is 16777216 bytes. Use strict bounded JSON parsing. Exit 0 for success, 1 for structured rejection, 2 for argument misuse; never print credentials or untrusted request values in diagnostics. CLI callers must bound execution time; tests use a 30-second subprocess deadline.

Envelope is exactly `{protocol_major, operation, request_id, expected_revision, project_id, workflow_id, actor_id, job_id, lease_epoch, payload}`. `protocol_major` is integer 1; request_id and nonnull identities are nonempty strings of at most 256 UTF-8 bytes; expected_revision and nonnull lease_epoch are nonnegative integers, never bool. Operator job_id is null. Response is exactly `{ok, revision, result, error_code, retryable}`; success has error_code null and retryable false; failure has result null. Error codes are exactly `invalid_request`, `incompatible_contract`, `revision_conflict`, `wrong_binding`, `missing_capability`, `rejected_evidence`, `recovery_required`. Only revision_conflict is retryable. Rejections retain current revision, or 0 before initialization. Reject malformed envelopes before touching state. Redact diagnostics.

AP00018 implements `workflow.open`, `owner.acquire`, `owner.release`, `owner.recover` and advertises only `workflow.core.v1`. Closed later names are `policy.bind`, `prd.enter`, `task.replace`, `task.start`, `task.finish`, `task.attempt`, `lane.route`, `job.plan`, `job.claim`, `job.record_exit`, `review.record_stage`, `review.close`, `custody.record`, `custody.discharge`, `verification.record`, `phase.handoff`, `prd.stall`, `prd.park`, `prd.defer`, `prd.complete`, `artifact.record`, `records.commit`; these return missing_capability without writes. Unknown operation returns invalid_request. Jobs/reviews/records/waves capabilities are declared unavailable, never advertised or returned as successful stubs.

Payload schemas are closed objects: workflow.open `{}`; owner.acquire `{mode: "manual"|"supervised", native_session_id: nonempty string}`; owner.release `{}`; owner.recover `{reason: nonempty string, reconciled_job_ids: unique string[]}`. Strings obey the identity bound except reason, bounded to 4096 bytes. Freeze schemas and positive/negative fixtures for all four implemented operations. Reserved operation names and their unavailable capability mappings are explicit contract declarations, not implemented payload schemas.

Fresh workflow.open on an absent store alone accepts null workflow_id/actor_id/lease_epoch, null job_id, expected_revision 0 and matching project_id. Assign workflow ID once, create operator credential, state and receipt recoverably under one bootstrap lock. Result contains `workflow_id`, `actor_id`, `actor_file`, `lease_epoch`; only credential path is returned. Initialize receipt and revision 0 together. Identical fresh-open replay after lost acknowledgement returns that exact result without creating credentials or workflows; conflicting ID returns revision_conflict. Existing workflow.open requires a valid actor and all existing bindings; it cannot reset or acquire ownership.

Other apply calls authenticate actor-file against its stored current descriptor or a receipt-retained historical descriptor before any mutation. Check project/workflow binding, scope and job first. For an identical recorded request, either a credential matching the receipt's historical authorizing digest or the authenticated current credential of that same actor_id and role at an epoch not earlier than the authorizing epoch may retrieve only that receipt even if its epoch was revoked; this never grants mutation authority. For any new request, require current descriptor and exact current envelope/credential epoch, then CAS and operation preconditions, then persist state plus receipt atomically. Current-credential receipt retrieval uses the historical envelope unchanged and does not require its lease_epoch to equal the current epoch. Historical credentials cannot submit new operations, altered envelopes or recover ownership. Thus in-place operator-file rotation does not prevent the caller reopening that path and retrieving its original receipt after lost acknowledgement; a caller retaining the old bytes may also retrieve that receipt only. Same canonical complete envelope (including expected_revision) under an authenticated binding returns the original response even after revision changes; changed request ID payload/envelope conflicts. Historical receipt retrieval is the sole exception to execution-epoch revocation and returns no credential contents; it cannot replay effects into new ownership. Retain each receipt's original authorizing digest and response until explicit future migration; capacity refusal never evicts them. Unsupported operation and rejected requests never create receipts or change revisions. Contract/snapshot do not acquire execution ownership; snapshot excludes all credential material.

### Actors and lease

Credential files are strict JSON with closed keys `{actor_id, project_id, workflow_id, role, lease_epoch, native_session_id, secret}`. Generate secrets using `secrets.token_urlsafe(32)`, store only SHA-256 digests in durable actor descriptors, compare with `hmac.compare_digest`. Credential root 0700/file 0600; reject symlinks, hardlinks, wrong permissions and bindings. File contents never enter logs, responses, bundle fixtures or public snapshot. Bootstrap operator is role operator at epoch 0. Execution credential role is owner; its scope allows release and future permitted lifecycle actions, never operator recovery. Future job role is declared but no job credential issuance occurs here.

owner.acquire requires current operator authority and no owner; increment epoch, rotate the operator credential to that epoch, and issue one owner credential bound to mode/native_session_id. Operator actor ID remains stable, its new secret replaces the old secret; every epoch-changing operation rotates it in the same recoverable publication. owner.acquire returns `actor_file`/`actor_id`/`lease_epoch` for the owner and `operator_actor_file` for the refreshed operator. Return its path, actor ID and epoch. Concurrent acquires have exactly one winner; an existing owner blocks even when mode differs. owner.release requires the current owner credential; increment epoch and revoke owner credentials. Preserve operator recovery authority across every acquire/release/recover by rotating its descriptor and credential through recoverable intent; do not make an old execution credential an operator. owner.recover requires operator authority plus reason and reconciliation of the durable active/unreconciled jobs; never timeout alone. AP00018 has no jobs and requires both durable jobs and reconciled_job_ids empty. Increment epoch, revoke prior execution actors and clear owner; acquiring again is explicit. Return current operator credential path/epoch where rotation is required. Lost acknowledgements at every credential publication boundary must leave either the old consistent pair or a recoverable intent; never a committed receipt pointing at missing credential bytes. Recovery retries reconcile intent before new work. Failure to reconcile returns recovery_required without accepting another owner. Intent records contain paths/digests/IDs, never plaintext secrets; staged credential bytes remain private 0600. Use one fixed private `credential-intent.json` and private staged/rollback files under actors. Before changing final credentials, stage+fsync all new bytes and rollback copies, then persist+directory-fsync intent containing the canonical request digest, old revision/state digest, candidate state, response/receipt and old/new credential descriptors/paths/digests. Candidate state contains no secrets. Publish final credential files with fsync/replace/directory-fsync, then publish state+receipt through StateStore, then remove intent and private stages with directory fsync. Bootstrap uses the state sidecar lock without recursively locking; factor a locked initialization entry internally. Never acquire a second flock for the same operation. A crash before durable intent leaves only unreferenced private stages; it changes no final credential or state. Bound all controller-owned staging/rollback/temp artifacts to 64 files and 16777216 aggregate bytes. Under the exclusive store lock, descriptor-check and count the existing owned stage/temp files and budget the full proposed set before creating any; refuse with recovery_required without modifying evidence if the new set would exceed either limit, or an owned artifact is unsafe/unreadable. This budget covers bootstrap and owner intent temp files as well as credential stages/rollback files. Never delete an orphan automatically. Document private offline archive/hash verification and attended orphan recovery; archive-based recovery requires the operator to take the workflow offline, retain all bytes, and restore the verified consistent state/credentials before retry. Tests repeatedly crash before durable intent and prove bounded file/byte growth and fail-closed admission at the limit. A crash after intent is reconciled forward exactly once from validated old/candidate state and verified staged/final hashes, or returns recovery_required retaining evidence. A successful receipt is never emitted until final files match its descriptors. Reconciliation admission: strict envelope and project/workflow binding validation precede reconciliation; only the identical intent request authenticated by its recorded old/new authorizing descriptor (or the identical null-bootstrap request) may finish it. All unrelated/invalid requests return recovery_required/wrong_binding without changing bytes. Snapshot never reconciles; it reports recovery_required while an intent exists. A changed bootstrap request ID cannot reconcile another bootstrap. Frozen fixtures enumerate crashes at stage, intent, each credential publication, state publication and cleanup; after recovery the original caller can retrieve the exact receipt using its historical credential. Rejection byte preservation is measured after admitted intent reconciliation only for that successful matching recovery request; rejected calls never reconcile.

### Export and installed evidence

`contracts/controller/workflow-v1.json` is canonical JSON Schema for durable state and protocol/payload/response definitions. `fixtures-v1.json` freezes named positive/negative scenarios with explicit expected errors and no real secrets. `provenance.json` records OVCAQ repository, exact pin, source-to-target symbol and test maps, hashes, preserved invariants and deliberate exclusions/divergences; preserve MIT attribution in extracted files. Exporter computes SHA-256 of raw schema/fixture bytes and produces `contracts/controller-v1.json`, strict JSON with exactly `{protocol_major, package_version, schema_digest, fixture_digest, operations, capabilities}`. protocol_major is integer 1; package_version equals plugin manifest version; digests are lowercase SHA-256 hex; operations/capabilities are unique string lists containing only implemented items. No symlink path components, regular file, under 16777216 bytes. Runtime contract reads installed assets and matches digests/identities; package version may add `+<build>` only. Export is deterministic and cannot read live workflow state. README documents raw bundle SHA-256 and the single installed argv above. No package version bump/publication or installation is authorized.


Details:
Source/config characterization only. Stream git show blobs directly into SHA256; never print full source. Inspect only provenance source hash and ownership sections with a bounded JSON query. Check exact pinned source and source-to-target maps. Do not read fixture bodies. Write raw hash comparisons and any divergence to the durable report; no production edits. Verify existing schema ownership tests only.

Acceptance criteria:
kernel_field_ownership and contract_examples reject unowned fields; recheck source pin and preserve existing fixes.

Verify: mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_schema.py -q --tb=short


Acceptance criteria:
Recheck pinned source hashes and ownership map; preserve existing behavior and evidence.

## Diff under review

```diff
diff --git a/docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md b/docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md
new file mode 100644
index 0000000..8eed1ce
--- /dev/null
+++ b/docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md
@@ -0,0 +1,84 @@
+# AP00018 v2 pinned-source characterization
+
+Rechecked 2026-11-09 against OVCAQ `cf8be72214a515c84ee42f0d8b30e65cc2a4ebb7`
+from `https://github.com/buvis/ovcaq`. Each raw blob was read using
+`git show <exact-pin>:<path>` and streamed into SHA-256. No checkout HEAD
+source or fixture bodies were inspected.
+
+All 15 observed hashes equal the recorded provenance hashes. No provenance
+correction is needed.
+
+| Pinned source path | Recorded SHA-256 | Observed SHA-256 |
+| --- | --- | --- |
+| `src/ovcaq/state/schema.py` | `1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b` | `1aa218e2b435866c96ca490bc499aaa2fc3e49d640ddde84dd947b00812bd60b` |
+| `src/ovcaq/state/store.py` | `b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7` | `b7ade1f13f7c4ef8cb65ce07ac5c228e235ab293ae9e82562e7d449e721307e7` |
+| `src/ovcaq/state/commands.py` | `30d51f28eb04a3a00ecae2aa3d3966435add4e804311468c1b6ea1bb7614fbd0` | `30d51f28eb04a3a00ecae2aa3d3966435add4e804311468c1b6ea1bb7614fbd0` |
+| `src/ovcaq/paths.py` | `3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990` | `3bb2bdd7da9dc838e19751fb95c79aa072961849624978f9ab91bfb3a5cfb990` |
+| `tests/state/test_schema.py` | `91e46ef82e027e9b9f30769e012170e105c6c6cef9e065276f9abdbd37248e27` | `91e46ef82e027e9b9f30769e012170e105c6c6cef9e065276f9abdbd37248e27` |
+| `tests/state/test_schema_constraints.py` | `60bd69c7aaf5f3297d51095506e1618a7cd373886879879d311d07f24d417174` | `60bd69c7aaf5f3297d51095506e1618a7cd373886879879d311d07f24d417174` |
+| `tests/state/test_schema_invariants.py` | `93826703d0452919d2b16bb040b11a70f2ac4e166e94e913b25cedef7476382f` | `93826703d0452919d2b16bb040b11a70f2ac4e166e94e913b25cedef7476382f` |
+| `tests/state/test_schema_limits.py` | `f92ff6c294850837675a2bea85aff774ce888c66466cc0fdc3d16b1008445cb1` | `f92ff6c294850837675a2bea85aff774ce888c66466cc0fdc3d16b1008445cb1` |
+| `tests/state/test_store.py` | `5bebdd57e7b027889c18de3e18f006702d4017a1f7e1e9abd2bd22befd6e9992` | `5bebdd57e7b027889c18de3e18f006702d4017a1f7e1e9abd2bd22befd6e9992` |
+| `tests/state/test_store_transactions.py` | `59863830378a6ffe7c2cef4df0f383e5937541345347f8c36f952e0eb36fa4f3` | `59863830378a6ffe7c2cef4df0f383e5937541345347f8c36f952e0eb36fa4f3` |
+| `tests/state/test_store_concurrency.py` | `791b17d686b9dc4bb5cb4b9f770690d1bf580988c286f91b1dba55a6f0761fb9` | `791b17d686b9dc4bb5cb4b9f770690d1bf580988c286f91b1dba55a6f0761fb9` |
+| `tests/state/test_durability.py` | `fafcd253e9ebdf05d0ed9b4aa5f7a0619f602ae36349ab387e0ffe88477dbc32` | `fafcd253e9ebdf05d0ed9b4aa5f7a0619f602ae36349ab387e0ffe88477dbc32` |
+| `tests/state/test_guarded_service.py` | `7e7c8bae2ecd23c21fbb58f8fb4fa5f744b03fb9aa94c810f28b75655002111f` | `7e7c8bae2ecd23c21fbb58f8fb4fa5f744b03fb9aa94c810f28b75655002111f` |
+| `tests/runtime/test_paths.py` | `aa10c8c06740bf6ea4eb29c11d06affac0f17c0e605d7fb3d6a10fe2da3b3fdd` | `aa10c8c06740bf6ea4eb29c11d06affac0f17c0e605d7fb3d6a10fe2da3b3fdd` |
+| `LICENSE` | `cf48d74443ef10a4521c1413fc331ceca76a2c791ea913c60df6d0cbf1440e46` | `cf48d74443ef10a4521c1413fc331ceca76a2c791ea913c60df6d0cbf1440e46` |
+
+The four source-to-target declarations reference existing pinned source symbols:
+
+| Source | Declared target | Symbols checked | Missing |
+| --- | --- | ---: | ---: |
+| `src/ovcaq/state/schema.py` | `autopilot_state.schema` | 11 | 0 |
+| `src/ovcaq/state/store.py` | `autopilot_state.store` | 14 | 0 |
+| `src/ovcaq/paths.py` | `autopilot_state.paths.resolve_project_root` and private layout | 6 | 0 |
+| `src/ovcaq/state/commands.py` | none; excluded generic mutation service | 6 | 0 |
+
+The allowed target schema contains its 11 mapped exports, including the two
+exception classes and three public functions. Its six published constants
+retain the required values: schema version 1; state 16777216 bytes; command
+payload 2097152 bytes; string 1048576 bytes; depth 32; integer digits 640.
+Other target modules were outside this task's read allowlist; source symbol
+presence does not establish their behavioral equivalence.
+
+The pinned schema declares 144 class fields. The ownership section has 144
+distinct matching source fields, with no missing or extra entries: 137
+deferred, three excluded, two redesigned and two preserved. Its four core
+mappings are `WorkState.repo_root -> repo_root`,
+`ReviewState.cap -> workflow.review.cap`,
+`State.schema_version -> schema_version`, and
+`State.revision -> revision`. This is field ownership characterization,
+not a claim that the kernel implements the legacy workflow schema.
+
+The existing schema tests explicitly check rejection of missing and unknown
+fields, process identity/PID/launcher/heartbeat/resource/TUI fields at both
+top level and under workflow, populated or extended workflow reserves,
+and invalid values before deep copying. They also check revision-zero
+initialization with explicit project/workflow identity and fresh reserves.
+No source-hash or ownership-map drift was observed. Runtime restore,
+credential recovery, protocol examples and delivery behavior were not
+re-executed by this schema-only gate.
+
+Executed once, with a 300-second subprocess timeout:
+
+```text
+mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_schema.py -q --tb=line
+22 passed in 0.33s
+exit code: 0
+```
+
+Scope: report only. Production, tests, provenance, held/custody records and
+controller state were not modified. No commit, push or installation ran.
+
+Reading deviation: the initial provenance query selected invariant and
+divergence sections in addition to the intended source/symbol/ownership
+sections. Its output exceeded the 15 KB query cap and was truncated by
+the tool. The orchestrator was informed; subsequent outputs were bounded.
+No fixture body or full pinned source was printed.
+
+ASSUMPTIONS: none
+
+FILES_TOUCHED:
+docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md
+
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Recorded task 9 command: mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot/test_controller_schema.py -q --tb=line
exit code: 0
22 passed in 0.33s
Evidence: docs/dev/project-management/autopilot/reports/00018-v2-source-characterization.md


Judge only from this prompt: the diff above, the task text, and this recorded
result. Do not read other files, run commands, or re-run the tests. What is not
in this prompt is not evidence, and a finding you cannot ground in what is here
is one you should not report.

# Simplification Mandate (step 5.7 reviewer-prompt appendix)

Append this block **verbatim** to every per-task code-reviewer prompt (see
`SKILL.md` step 5.7). It ships inside the prompt, so it must stay
self-contained.

> Beyond bugs, actively hunt for simplification in the diff under review. For
> every added or changed file, ask "what would make this simpler to read
> without changing what it does?" and flag concrete behavior-preserving
> opportunities to: reduce complexity (needless indirection, dead branches,
> single-caller abstractions, nesting deeper than 4 levels, functions over 50
> lines); eliminate redundancy (logic duplicated within the diff or against
> existing code, a helper that reimplements a stdlib or existing utility);
> improve naming (names that state intent, no opaque abbreviations); and
> remove dead code. Follow CLAUDE.md / AGENTS.md conventions and the
> surrounding code's style.
>
> Report each concrete behavior-preserving simplification as a LOW finding,
> with file:line, the current shape, and the simpler replacement. LOW findings
> are carried to the PRD-level review, never retried here.
>
> Do not over-simplify: never propose a change that trades clarity for
> brevity, drops error handling, collapses a deliberate boundary, or removes a
> documented invariant. Simpler means easier to read and maintain, not shorter
> at any cost. If a change would alter behavior, it is out of scope — do not
> flag it.


## Reporting contract

Report one finding per line, in exactly this shape:

SEVERITY | file:line | issue | fix

Severities are CRITICAL, HIGH, MEDIUM, LOW.

Severity has a fixed meaning here, and it decides what happens next. MEDIUM is
reserved for a correctness or security defect this diff introduces that its own
tests do not catch: a wrong result, an unhandled error path, data loss,
injection, secret exposure, or a missing authorization check. Style, naming,
duplication, structure and maintainability are LOW, and so is every
behavior-preserving simplification, whatever its size. A LOW is noted and
carried to the PRD-level review; it is never retried in this loop.

If the diff has no findings, emit the literal line:

NO FINDINGS

## Closure verdicts (only when the description carries a findings block)

When the Description above contains a `### Findings (verbatim)` block, this is
a rework task and each quoted finding is a claim to check. Before your findings
lines, emit one verdict per quoted finding, in this shape:

CLOSURE | resolved|unresolved | <the finding, quoted> | <one line of evidence from the diff>

Judge each finding against the diff, not against the commit message and not
against how clean the code reads. A diff that improves the file while leaving
the quoted defect reachable is `unresolved`. Quote the line that resolves it,
or say what still reaches the defect. Emit a verdict for every quoted finding,
including ones you judge already fixed elsewhere.


