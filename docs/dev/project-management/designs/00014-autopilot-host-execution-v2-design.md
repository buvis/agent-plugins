# Design: Autopilot host execution and enforcement, v2 (AP 00014)

PRD: `docs/dev/project-management/prds/wip/00014-autopilot-host-execution-v2.md`.
Source design: `designs/00011-autopilot-standalone-design.md`. Retained v1
records: `designs/00014-autopilot-host-execution-v1-design.md`,
`designs/00014-autopilot-host-execution-v1-rework-1-design.md`,
`reviews/00014-autopilot-host-execution-v1-review-1.md` (rows `v1c1-R1`..`R43`),
`reviews/00014-autopilot-host-execution-v1-review-2.md` (rows `v1c2-R1`..`R32`),
and triage stubs 00038-00064 (`git show e6f9f31:docs/dev/project-management/prds/hold/<file>`).

## Architecture fit

Three layers, per `designs/00011` § Ownership. This PRD lands only in the first.

1. **Plugin package** (`plugins/autopilot/`, self-contained, AGENTS.md:39
   containment). Host adapters, native identity, hook-input translation, guard
   decisions, job-request construction, policy-driven role resolution, doctor,
   and generated client assets. Python stdlib only. It never launches a provider
   CLI, never supervises, schedules or relaunches anything.
2. **Controller** (`plugins/autopilot/controller/`, AP00018 v2, done). Owns
   workflow state. Its contract (`contracts/controller-v1.json`,
   `contracts/controller/workflow-v1.json`) implements `workflow.open` and
   `owner.*` only; `job.plan`, `job.claim`, `job.record_exit` are reserved
   under the **unavailable** capability `workflow.jobs.v1`. This design does
   not touch the controller. It defines the plugin-side job-intent payload that
   a future `job.plan` will accept, and a `ControllerSeam` Protocol the real
   client (AP 00016) will implement. Until then the package holds no seam
   implementation; tests use fakes in `tests/autopilot/host_fakes.py`.
3. **OVCAQ** (external). Consumes controller job intents, maps tiers to models,
   launches and cancels processes. Nothing here imitates it.

Maintainer tools (`tools/autopilot/build-compatibility.py`,
`tools/autopilot/probe-host.py`, `tools/autopilot/update_helper_map.py`,
`tools/autopilot/helper_map_successor.py`) stay outside the package. Only
`probe-host.py` ever starts a provider CLI, and only as a manual real-host
probe in an isolated directory under `docs/dev/tmp/autopilot/probes/`. That is
not "plugin scripts spawning headless children": the PRD's Phase 0 and Phase 2
text requires such probes, in isolated plugin/project locations.

### Verified state of master (2026-11-15)

- The AP00014 v1 code is on master: `scripts/{hosts,claude,codex,gemini,jobs,guards,doctor}.py`,
  `contracts/hosts.json`, `compatibility/{claude,codex,gemini}.json`,
  `tools/autopilot/{build-compatibility,probe-host}.py`, and the autopilot.py
  modes `--probe-host`, `--run-guard`, `--diagnose`.
- **Cycle-2 R1 is resolved on master.** The AP00018 v2 close-out added the
  successor receipt
  `docs/dev/project-management/autopilot/reports/00018-v2-controller-delivery-receipts.json`
  (`package_revision` `1d83b8950a8cbd7cfe4e3916f600d807cdd2645d`, paths
  include README.md and CHANGELOG.md), and
  `tests/autopilot/test_helper_provenance_real.py::assert_refreshed_evidence`
  now pins those two files to the successor revision. I ran
  `test_helper_provenance_real.py test_jobs.py test_guards.py test_guards_pure_duties.py test_sessions.py test_host_argv.py test_compatibility.py test_package.py test_facade.py`:
  **203 passed, 0 failed, 0 skipped**. Consequence for this PRD: any AP00014 v2
  edit to README.md or CHANGELOG.md re-breaks that test unless this PRD mints
  its own successor receipt (§12). The fix is a receipt chain, not an exemption.
- **New defect found during design.** `claude.session_identity()` reads
  `CLAUDE_SESSION_ID`. Claude Code does not export that name. The running
  Claude Code session that wrote this doc exports `CLAUDE_CODE_SESSION_ID`
  (observed with `os.environ` on 2026-11-15, together with `CLAUDECODE`,
  `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_PID`). So Claude identity is `None` in
  every real Claude session today, and the v1 tests pass only because they set
  the wrong variable themselves. §2 fixes the name and a test binds to it.
- **Source characterization facts** (pinned source `e960ef1c`, read-only from
  the frozen `buvis/claude-autopilot` checkout):
  - `hooks/hooks.json` registers PreToolUse `Edit|Write|MultiEdit`
    (`enforce_prd_location.py`), PreToolUse `Bash`
    (`enforce_prd_location.py`, `guard_push_on_critical.py`), PreToolUse
    `Skill` (`guard_skill_after_leave.py`), PreToolUse `Agent`
    (`guard_phase_delegation.py`), PostToolUse (`autopilot_context_cap_hook.py`,
    `validate_state_json_hook.py`, `note_session_leave.py`), and Stop
    (`review_coverage_hook.py`, `guard_stop_on_live_lanes.py`).
  - **Known effort mismatch.** `skills/review-work-completion/SKILL.md:17`
    says "External Claude reviewers pass `--effort high`", but
    `skills/use-sonnet/scripts/sonnet-run.sh` has no `--effort` option: its
    `*)` branch takes `--effort` and then `high` as the positional prompt, so
    the effort is dropped and, without `-f`, the prompt becomes `high`. The
    corrected target (§5) requires `effort` in job metadata and never puts it
    in argv; argv forwarding is OV 00059.
- **Host registration surfaces** (documentation read 2026-11-15):
  - Claude Code: plugin hooks file, `${CLAUDE_PLUGIN_ROOT}` substituted in
    hook commands, PreToolUse deny via
    `hookSpecificOutput.permissionDecision = "deny"`, stdin carries
    `session_id`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`.
  - Codex CLI (0.167.2 installed): hooks on by default; plugin hooks default
    to `hooks/hooks.json` in the plugin root, overridable by a `hooks` field in
    `.codex-plugin/plugin.json`; same event schema as Claude
    (`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, ...); stdin carries
    `session_id`, `cwd`, `tool_name`, `tool_input`; deny with the same
    `hookSpecificOutput.permissionDecision` shape or exit 2; plugin hook
    processes get `PLUGIN_ROOT` and, for compatibility, `CLAUDE_PLUGIN_ROOT`;
    non-managed hooks need trust or `--dangerously-bypass-hook-trust`.
    `CODEX_SESSION_ID` is set in Codex child shells
    (`skills/use-codex/references/host-markers.md`).
  - Gemini CLI (0.68.0 installed): hooks in `settings.json` layers or an
    extension's fixed `hooks/hooks.json` beside a root `gemini-extension.json`;
    `BeforeTool` event; `GEMINI_SESSION_ID` env for the session. The CLI is
    documented as superseded (2026-06-18), and native auth failed with
    `IneligibleTierError` when last probed (host-markers.md).

## Module placement

New files (all paths exact):

| Path | Purpose |
|---|---|
| `plugins/autopilot/scripts/roles.py` | Policy-driven role resolution (§6) |
| `plugins/autopilot/scripts/interception.py` | Hook entry: translate, evaluate, render, trace (§8) |
| `plugins/autopilot/compatibility/claude/hooks.json` | Generated Claude hook registration asset (§9) |
| `plugins/autopilot/compatibility/codex/hooks.json` | Generated Codex hook registration asset (§9) |
| `docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json` | AP00014 successor receipt (§12), minted last |
| `tests/autopilot/host_fakes.py` | `FakeSeam`, `TripwireSeam` moved out of the package |
| `tests/autopilot/hook_characterization.json` | Source hook decision fixtures (§13) |
| `tests/autopilot/test_roles.py` | Role resolution and Claude-free profile tests |
| `tests/autopilot/test_interception.py` | Hook entry tests per host |

Edited files:

| Path | Change |
|---|---|
| `plugins/autopilot/scripts/hosts.py` | `ADAPTERS` table, `adapter()`, `NativeSession`, `current_session()`, provider/adapter-kind tables, `CapabilityStatus` validation (§1) |
| `plugins/autopilot/scripts/{claude,codex,gemini}.py` | Uniform adapter surface; real session env names; argv; hook registration and rendering for Claude and Codex (§2) |
| `plugins/autopilot/scripts/jobs.py` | Validated `JobRequest`, `request_job`, `bind_job_session`, `close_native_child`, strict seam replies; `FakeSeam` removed (§4, §5) |
| `plugins/autopilot/scripts/guards.py` | Strict verdict relay; project-root path normalization; Bash command mode; `is_git_push` (§7) |
| `plugins/autopilot/scripts/doctor.py` | Observed vs simulated split; profile from `roles.resolve_profile` (§10) |
| `plugins/autopilot/scripts/autopilot.py` | Five new modes and capability IDs (§11) |
| `plugins/autopilot/contracts/hosts.json` | `schema_version` 2 shape (§3) |
| `plugins/autopilot/compatibility/{claude,codex,gemini}.json` | Regenerated, `schema_version` 2 (§9) |
| `plugins/autopilot/CHANGELOG.md`, `plugins/autopilot/README.md` | Supported and still-unavailable duties per client; new modes (§14) |
| `tools/autopilot/build-compatibility.py` | `hosts.adapter()` gate, hooks assets, `--check` (§9) |
| `tools/autopilot/probe-host.py` | Real isolated probe plus static record (§10) |
| `tools/autopilot/helper_map_successor.py`, `tools/autopilot/update_helper_map.py`, `tools/autopilot/source-map.json` | Receipt chain and AP00014 asset registration (§12) |
| `tests/autopilot/test_{jobs,sessions,host_argv,guards,guards_pure_duties,compatibility,facade,package,local_boundary,helper_provenance_real}.py` | Re-specified per § Test strategy outline |

Untouched: `plugins/autopilot/controller/**`, the controller contracts,
`plugins/autopilot/plugin.json` (closed portable schema), every `skills/**`
file (AP 00015 adapts skill prose), and no client manifest
(`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
`gemini-extension.json`) is added to the package: a `.claude-plugin/plugin.json`
would make `scripts/generate_marketplace.py` emit a catalog entry, which is
publication, and any manifest pointer activates hooks on install, which is
live installation. Both are out of scope (PRD Overview).

## Interfaces & contracts

Every symbol below is exact. "Refuse" means: raise or return the named error
code, perform no side effect.

### §1 `plugins/autopilot/scripts/hosts.py`

Kept unchanged: `CAPABILITY_NAMES`, `UNAVAILABLE_NO_BINARY`,
`UNAVAILABLE_NO_AUTH`, `CAPABILITY_STATUSES`, `HostCapability`, `ProbeResult`
(all invariants, `probe_kind == "static"`, `certified is False`),
`unavailable()`, `statuses_from()`, `probe_host()`.

Changed and added:

```python
ADAPTERS: dict[str, str] = {"claude": "claude", "codex": "codex", "gemini": "gemini"}
PROVIDER_HOSTS: dict[str, str] = {"anthropic": "claude", "openai": "codex", "google": "gemini"}
# review-policy-v1 adapter id -> (host_id, execution)
ADAPTER_KINDS: dict[str, tuple[str, str]] = {
    "native-subagent": ("claude", "in-session"),
    "native-fallback": ("claude", "in-session"),
    "review-fanout-workflow": ("claude", "in-session"),
    "codex-cli": ("codex", "cross-session"),
    "gemini-cli": ("gemini", "cross-session"),
}
SESSION_SOURCES = ("environment", "hook_input")

@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    status: str
    reason: str | None
    def __post_init__(self) -> None:
        # name in CAPABILITY_NAMES; status in CAPABILITY_STATUSES;
        # status == "unavailable" -> reason in (UNAVAILABLE_NO_BINARY, UNAVAILABLE_NO_AUTH);
        # otherwise reason is None. Violation -> ValueError naming the field.

@dataclass(frozen=True)
class NativeSession:
    host_id: str      # key of ADAPTERS
    session_id: str   # 1..256 UTF-8 bytes, no ASCII control characters
    source: str       # one of SESSION_SOURCES
    def __post_init__(self) -> None: ...  # ValueError on any violation

def adapter(host_id: str) -> ModuleType:
    """Imports ADAPTERS[host_id] only after the membership check. A host_id
    outside ADAPTERS raises ValueError(f"unknown host_id: {host_id!r}") before
    importlib runs, so no foreign module's import-time code executes."""

def current_session(host_id: str, env: Mapping[str, str]) -> NativeSession | None:
    return adapter(host_id).session_from_environment(env)
```

`probe_host` and `_ADAPTERS` dispatch through `adapter()`; the lazy-probe
table is removed.

### §2 Adapter surface (`claude.py`, `codex.py`, `gemini.py`)

Every adapter exports exactly:

```python
HOST_ID: str
IMPLEMENTED_CAPABILITIES: frozenset[str]
SESSION_ENV_VAR: str
HOOK_REGISTRATIONS: tuple[HookRegistration, ...]   # empty when interception is not implemented
def probe(*, project_root: Path) -> ProbeResult                  # unchanged static probe
def session_from_environment(env: Mapping[str, str]) -> NativeSession | None
def can_delegate() -> bool
def build_job_argv(request: "JobRequest") -> list[str]
```

Adapters with `"interception"` in `IMPLEMENTED_CAPABILITIES` also export:

```python
def session_from_hook_input(payload: Mapping[str, object]) -> NativeSession | None
def translate_hook(event: str, payload: Mapping[str, object], *, project_root: Path) -> tuple[DutyCall, ...]
def render_hook_reply(event: str, decision: "HookDecision", *, stop_active: bool) -> HookReply
```

`session_identity()` is removed (replaced by `session_from_environment`).
`HookRegistration`, `DutyCall`, `HookReply` are defined in `interception.py`
(§8); adapters import them from there.

| | claude | codex | gemini |
|---|---|---|---|
| `IMPLEMENTED_CAPABILITIES` | `{"identity","delegation","isolation","interception"}` | `{"identity","isolation","interception"}` | `{"identity","isolation"}` |
| `SESSION_ENV_VAR` | `"CLAUDE_CODE_SESSION_ID"` | `"CODEX_SESSION_ID"` | `"GEMINI_SESSION_ID"` |
| `session_from_hook_input` | `payload["session_id"]`, source `"hook_input"` | same | not exported |
| `can_delegate()` | `True` (Agent tool, in-session) | `False` | `False` |
| `build_job_argv(request)` | `["claude", "-p"]` | `["codex", "exec", "-"]` | `["gemini", "-p", "Follow the instructions on standard input."]` |

`session_from_environment(env)` returns `NativeSession(HOST_ID, env[SESSION_ENV_VAR], "environment")`
when the variable is set and valid, `None` when absent, and `None` when
`NativeSession` validation fails (never raises on host data).

`build_job_argv` returns argv only; the prompt travels on stdin (§5) and the
argv never carries model, tier or effort (OVCAQ maps tiers; OV 00059 forwards
effort).

Capability meaning, each bound to a behavior test (closes v1c2-R9):

- `identity`: `session_from_environment` (and `session_from_hook_input` where
  exported) returns the native id from the documented source.
- `delegation`: `can_delegate()` is True; only an in-session primitive counts.
- `isolation`: the adapter has `identity`, and `jobs.bind_job_session` refuses
  a child session equal to the requester session (§5). Cross-session jobs are
  the isolation mechanism for codex and gemini.
- `interception`: `HOOK_REGISTRATIONS` is non-empty, `translate_hook` and
  `render_hook_reply` exist, and the generated `compatibility/<host>/hooks.json`
  exists (§9).

Gemini declares no `interception`. Its blocker constant is
`gemini.INTERCEPTION_BLOCKER = "no_package_local_registration_surface"`: the
only extension surface is a fixed root `hooks/hooks.json` beside a root
`gemini-extension.json`, which collides with the Claude/Codex default hooks
path and is an install surface; the CLI is documented superseded. Gemini's
mandatory role in the Claude-free profile (doubt reviewer) needs no
interception (§6).

Hook registrations (derived from the source `hooks/hooks.json`; `timeout` in seconds):

```python
# claude.HOOK_REGISTRATIONS
(HookRegistration("PreToolUse", "Edit|Write|MultiEdit", 5),
 HookRegistration("PreToolUse", "Bash", 10),
 HookRegistration("PreToolUse", "Skill", 5),
 HookRegistration("PreToolUse", "Agent", 5),
 HookRegistration("PostToolUse", "Edit|Write|MultiEdit", 5),
 HookRegistration("Stop", None, 10),
 HookRegistration("SessionStart", "compact|resume", 5))
# codex.HOOK_REGISTRATIONS
(HookRegistration("PreToolUse", "Bash", 10),
 HookRegistration("PreToolUse", "apply_patch", 5),
 HookRegistration("PostToolUse", "apply_patch", 5),
 HookRegistration("Stop", None, 10),
 HookRegistration("SessionStart", None, 5))
```

`translate_hook` maps a native event plus tool to duty calls:

| Host event / tool | Duty calls (context keys) |
|---|---|
| claude PreToolUse `Edit`/`Write`/`MultiEdit` | `document_location` (`document_path`=`tool_input.file_path`, `project_root`) |
| claude, codex PreToolUse `Bash` | `document_location` (`command`, `project_root`); `custody_push` (`command`) only when `guards.is_git_push(command)` |
| codex PreToolUse `apply_patch` | one `document_location` per path in the patch's `*** Add File: `, `*** Update File: `, `*** Move to: ` lines |
| claude PreToolUse `Skill` | `post_handoff` (`requested_skill`=`tool_input.skill`) |
| claude PreToolUse `Agent` | always one `delegation` call: `dispatch_skill` = first match of `(?<![\w:])/?(autopilot:[a-z-]+\|git-ferry:catchup)\b` in `tool_input.prompt`, or `""` when none; `child_depth` = `1` when the payload carries a non-empty `agent_id` or the hook environment has a non-empty `CLAUDE_CODE_CHILD_SESSION`, else `0` |
| claude PostToolUse `Edit`/`Write`/`MultiEdit`, codex PostToolUse `apply_patch` | `state_integrity` (`document_path`s) |
| Stop (both) | `review_completeness`, `live_job`, `departure` |
| SessionStart (both) | `context_reinjection` |

Codex coverage of `delegation` and `post_handoff` is `not_applicable_on_host`
(no in-session delegation primitive, no interceptable skill tool); this is
recorded in the bundle's `duty_coverage` (§9), never inferred as supported.

`render_hook_reply` for claude and codex (identical shapes, documented by both
hosts):

- PreToolUse refused: stdout
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "<reasons joined by '; '>"}}`, exit 0.
- PostToolUse refused: `{"decision": "block", "reason": "<reasons>"}`, exit 0.
- Stop refused and `stop_active is False`: `{"decision": "block", "reason": "<reasons>"}`, exit 0.
- Stop refused and `stop_active is True` (payload `stop_hook_active` true):
  `{"systemMessage": "autopilot: <reasons>"}`, exit 0. This bounds a Stop
  refusal to one block per stop chain, so a refusing guard can never loop a
  session.
- SessionStart refused: `{"systemMessage": "autopilot: <reasons>"}`, exit 0.
- SessionStart allowed with `decision.additional_context` set (the
  reinjection duty's delivery):
  `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<contract card body>"}}`, exit 0.
  The card body comes only from the validated `seam.read_facts` reply
  (`contract_card_body`, at most 65536 UTF-8 bytes, else
  `malformed_controller_facts`). `test_interception.py::test_session_start_reinjects_the_contract_card`
  asserts the returned `additionalContext` text, not only the verdict.
- Any other allowed decision: empty stdout, exit 0.

### §3 `plugins/autopilot/contracts/hosts.json` (schema_version 2)

```json
{
  "schema_version": 2,
  "hosts": {
    "claude": {"capabilities": ["delegation", "identity", "interception", "isolation"],
               "session_env_var": "CLAUDE_CODE_SESSION_ID",
               "registration": {"asset": "compatibility/claude/hooks.json", "activation": "client-manifest-hooks-field"}},
    "codex":  {"capabilities": ["identity", "interception", "isolation"],
               "session_env_var": "CODEX_SESSION_ID",
               "registration": {"asset": "compatibility/codex/hooks.json", "activation": "client-manifest-hooks-field"}},
    "gemini": {"capabilities": ["identity", "isolation"],
               "session_env_var": "GEMINI_SESSION_ID",
               "registration": null,
               "blockers": {"interception": "no_package_local_registration_surface"}}
  },
  "role_requirements": {
    "implementor": ["identity", "interception", "isolation"],
    "reviewer-cross-session": ["identity", "isolation"],
    "reviewer-in-session": ["delegation", "identity", "isolation"]
  },
  "implementor_duties": ["custody_push", "document_location", "state_integrity"]
}
```

Invariants (tested): each host's `capabilities` equals sorted
`IMPLEMENTED_CAPABILITIES`; `session_env_var` equals `SESSION_ENV_VAR`;
`registration` is non-null iff `"interception"` is declared; every
undeclared capability that has a `blockers` key names a non-empty reason.
Migration from schema 1: regenerated in the same commit; its consumers are
`build-compatibility.py`, `doctor.py` and tests, all in this repository; the
package is unpublished, so no external reader exists.

### §4 Controller seam (`jobs.py`)

```python
class ControllerSeam(Protocol):
    def submit_job(self, intent: dict) -> dict: ...
    def evaluate_guard(self, duty: str, context: dict) -> dict: ...
    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict: ...
```

The package ships no implementation. `FakeSeam` moves to
`tests/autopilot/host_fakes.py` with the same constructor
(`FakeSeam(*, guard_rules: dict, facts: dict | None = None)`).

Reply validation, applied by the caller to every seam return value:

- `submit_job` -> exactly `{"accepted": bool, "job_ref": str | None, "error": str | None}`;
  accepted True needs a non-empty `job_ref` and `error is None`; accepted
  False needs `job_ref is None` and `error` in the controller `error_codes`
  (`invalid_request`, `incompatible_contract`, `revision_conflict`,
  `wrong_binding`, `missing_capability`, `rejected_evidence`,
  `recovery_required`). Anything else becomes
  `{"accepted": False, "job_ref": None, "error": "malformed_controller_reply"}`.
- `evaluate_guard` -> exactly `{"allowed": bool, "reason": str | None}`;
  allowed False needs a non-empty str reason. Anything else becomes
  `GuardOutcome(allowed=False, reason="malformed_controller_verdict", stateful=True)`.
- `read_facts` -> a dict holding exactly the duty's controller-bound keys
  (§7 table) with their types; anything else refuses the duty with
  `"malformed_controller_facts"`. A raised exception from any seam method is
  caught and treated the same as a malformed reply.

### §5 Job requests, bindings, native children (`jobs.py`)

```python
TIERS = ("haiku", "sonnet", "opus", "fable")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
MAX_JOB_DEPTH = 1          # a job session may not request another cross-session job
MAX_CHILD_DEPTH = 1        # in-session children of a session, one level
MAX_INPUT_BYTES = 33554432 # per input file
INTENT_SCHEMA = "autopilot.job-intent.v1"

class JobRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None: ...
    code: str  # invalid_request | recursion_depth | recursive_job | input_digest_mismatch
               # | same_session | host_mismatch | missing_native_session | foreign_child

@dataclass(frozen=True)
class InputRef:
    kind: str     # member of review-policy-v1 input_kinds
    path: str     # project-relative POSIX path, no "..", not absolute, not under docs/dev/project-management/autopilot/
    sha256: str   # 64 lowercase hex, computed from the file bytes

@dataclass(frozen=True)
class AncestryEntry:
    host_id: str
    job_id: str
    session_id: str

@dataclass(frozen=True)
class JobRequest:
    request_id: str                 # sha256 of the canonical payload without request_id
    job_id: str
    role_id: str
    host_id: str
    tier: str
    effort: str                     # required; never forwarded in argv
    inputs: tuple[InputRef, ...]
    excluded_input_kinds: tuple[str, ...]
    requester: NativeSession
    ancestry: tuple[AncestryEntry, ...]
    def to_payload(self) -> dict: ...
    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "JobRequest": ...  # re-validates, recomputes request_id

def build_job_request(*, job_id: str, role_id: str, host_id: str, tier: str, effort: str,
                      inputs: Sequence[Mapping[str, str]], excluded_input_kinds: Sequence[str],
                      requester: NativeSession, ancestry: tuple[AncestryEntry, ...],
                      project_root: Path) -> JobRequest: ...   # ancestry from derive_ancestry only
def request_job(request: JobRequest, *, seam: ControllerSeam | None, project_root: Path,
                request_file: Path | None) -> dict: ...
def bind_job_session(payload: Mapping[str, object], *, child: NativeSession,
                     project_root: Path) -> dict: ...
def close_native_child(*, parent: NativeSession, child: Mapping[str, object], outcome: str,
                       raw_output: bytes, artifact_path: Path, project_root: Path) -> dict: ...
```

`build_job_request` validation, in order, each failure `JobRefused("invalid_request", ...)` unless named:

1. `job_id`, `role_id`: identity strings (1..256 UTF-8 bytes); neither may
   equal a key of `PROVIDER_HOSTS`, `ADAPTERS`, or a member of `TIERS`
   (role IDs stay independent of provider/model names).
2. `host_id` in `ADAPTERS`; `tier` in `TIERS`; `effort` in `EFFORTS`
   (an empty or missing effort is refused).
3. Each input mapping has exactly `kind`, `path`; `kind` in the policy's
   `input_kinds`; `path` satisfies `InputRef.path` rules, resolves (realpath)
   inside `project_root`, is a regular file of at most `MAX_INPUT_BYTES`;
   `sha256` is computed here from its bytes. Inputs are sorted by `(kind, path)`.
4. `excluded_input_kinds` members are in `input_kinds`; no input has an
   excluded kind.
5. Ancestry is never caller input. `build_job_request` takes the
   `ancestry` argument only from `derive_ancestry(env, project_root)` (below);
   the `--request-job` request file has no `ancestry` key, and a request file
   that carries one is refused `invalid_request`. Entries have exactly
   `host_id`, `job_id`, `session_id`.
   `len(ancestry) >= MAX_JOB_DEPTH` -> `JobRefused("recursion_depth", ...)`;
   an entry equal to `(host_id, job_id)` of this request ->
   `JobRefused("recursive_job", ...)`.

```python
JOB_ENV = "AUTOPILOT_JOB_REQUEST"
def derive_ancestry(env: Mapping[str, str], project_root: Path) -> tuple[AncestryEntry, ...]:
    """No JOB_ENV -> (). JOB_ENV set -> read that job file (regular file,
    <= 2097152 bytes, JobRequest.from_payload) and return its ancestry plus
    AncestryEntry(its host_id, its job_id, the current session id from
    hosts.current_session(its host_id, env)). An unreadable or invalid job
    file refuses JobRefused("invalid_request", ...), never returns ()."""
```

   A job session therefore always reaches depth 1 and is refused
   `recursion_depth`. Three independent lineage signals feed the check, and
   any one of them sets depth 1:
   - `JOB_ENV`, set by the standalone instruction (§5 `request_job`);
   - `AUTOPILOT_DISPATCH_DEPTH` (the source runners' backstop, kept with the
     same meaning): the instruction env sets it to the requester's value + 1;
     a value that is not a non-negative integer refuses `invalid_request`;
     `>= MAX_JOB_DEPTH` refuses `recursion_depth`;
   - a lineage record: `bind_job_session`'s CLI caller (`--bind-job`) writes
     `docs/dev/tmp/autopilot/jobs/<host_id>-<sha256(session_id)>.json`
     (`O_EXCL|O_NOFOLLOW` under `_pinned_parent_fd`; content = the binding
     record), and `--request-job` refuses `recursion_depth` when a record for
     the current native session exists. The native session id comes from the
     host (§2) and the requester must have one (`missing_native_session`
     otherwise), so removing the env variables does not remove the record.

   **Residue, stated as open, not fixed:** a child that strips both env
   variables *and* never runs `--bind-job` still escapes the package-local
   bound in standalone mode. The plugin cannot prevent a cooperating host
   process from skipping its own instructions; the source had the same limit
   (`AUTOPILOT_DISPATCH_DEPTH` only). The enforcing bound for managed mode is
   the controller's `job.plan` lineage check (AP 00016 seam, AP 00019 jobs);
   §13 records this finding as fixed for cooperating sessions and deferred
   for adversarial ones, and the README calls the standalone bound
   cooperative.
6. All nested values are copied into tuples and frozen dataclasses, so later
   caller mutation cannot change the request (closes v1c1-R32).

Canonical payload (`to_payload`), also the `job.plan` intent body:

```json
{"intent_schema": "autopilot.job-intent.v1",
 "operation": "job.plan",
 "required_capability": "workflow.jobs.v1",
 "request_id": "<64 hex>",
 "job_id": "...", "role_id": "...", "host_id": "...",
 "execution": "cross-session", "isolation": "fresh-session",
 "tier": "...", "effort": "...",
 "inputs": [{"kind": "...", "path": "...", "sha256": "..."}],
 "excluded_input_kinds": ["..."],
 "requester": {"host_id": "...", "session_id": "...", "source": "..."},
 "ancestry": [{"host_id": "...", "job_id": "...", "session_id": "..."}]}
```

`request_id` = `sha256(json.dumps(payload_without_request_id, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))`.

`request_job` returns:

- seam given: `{"schema_version": 1, "mode": "controller", "request": <payload>, "reply": <validated reply, §4>}`.
  `mode` is fixed by this function; the reply is nested, so a seam cannot
  override it. A rejected reply (including `missing_capability`, which the
  AP00018 controller returns today) is reported as is; there is **no**
  fallback to standalone mode.
- seam None: `{"schema_version": 1, "mode": "standalone", "request": <payload>, "instruction": {...}}`
  with instruction exactly:
  `{"host_id", "argv": adapter.build_job_argv(request), "stdin": <text>, "env": {"AUTOPILOT_JOB_REQUEST": str(request_file), "AUTOPILOT_DISPATCH_DEPTH": str(len(request.ancestry) + 1)}, "manual_settings": {"tier", "effort"}, "steps": [<str>, ...]}`.
  `stdin` tells the new session to run
  `python3 <plugin>/scripts/autopilot.py --bind-job "$AUTOPILOT_JOB_REQUEST" --project-root <project_root>`
  first and to read only the listed inputs. `steps` are the human launch
  steps in order: write nothing else, start the argv in `project_root` with
  the env and stdin, set the tier's model and the effort by hand. `request_file`
  None -> `JobRefused("invalid_request", "standalone mode needs a request file")`.

`bind_job_session(payload, child, project_root)`:
`JobRequest.from_payload(payload)` (a changed `request_id` refuses
`invalid_request`); `child.host_id != host_id` -> `host_mismatch`;
`child.session_id == requester.session_id` -> `same_session`; any input's
current digest differs -> `input_digest_mismatch`; the CLI caller then
writes the lineage record (above) and refuses `recursion_depth` if one
already exists for that child session. Returns
`{"schema_version": 1, "request_id", "job_id", "host_id", "child_session": {...}, "requester_session": {...}, "verified_inputs": [<InputRef dicts>], "ancestry": <request ancestry + requester entry>}`.
It writes nothing; the caller records it as controller evidence.

`close_native_child(...)`: for in-session children only (Claude Agent). The
`child` mapping has exactly `child_id` (str), `kind` (`"in-session"`),
`parent_session_id` (str), `depth` (int). `kind != "in-session"` or
`parent_session_id != parent.session_id` -> `foreign_child`;
`depth > MAX_CHILD_DEPTH` -> `recursion_depth`; `outcome` in
`("completed", "cancelled", "failed")`. It writes `raw_output` to
`artifact_path` with `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW` under a
`log_sink_refusal._pinned_parent_fd` descriptor rooted at `project_root`, and
refuses paths inside `docs/dev/project-management/autopilot/`. Returns
`{"schema_version": 1, "child_id", "outcome", "artifact": {"path", "sha256", "bytes"}, "cleanup": "completed"}`.
It never sends a signal, never calls `subprocess`, and never references a
cross-session `request_id`, so it cannot touch an OVCAQ process. Cancellation
itself stays with the host (for example the host's own stop control).

### §6 Role resolution (`roles.py`)

```python
@dataclass(frozen=True)
class ProfileFacts:
    gemini_cli_available: bool
    doubt_reviewer: str | None
    implementor_codex_present: bool

@dataclass(frozen=True)
class RoleResolution:
    role: str                         # "implementor:<provider>" or a reviewer job_id
    role_id: str                      # "implementor" or the policy role_id
    host_id: str | None
    adapter: str | None
    execution: str | None             # "in-session" | "cross-session"
    required_capabilities: tuple[str, ...]
    missing: tuple[str, ...]          # sorted "<host>:<capability>", "unknown_adapter:<id>", "claude_excluded"
    unobserved: tuple[str, ...]       # sorted "<host>:<capability>" not proven by probe evidence
    status: str                       # "resolved" | "blocked"

@dataclass(frozen=True)
class ProfileResolution:
    profile_id: str
    lane: str
    claude_free: bool
    roles: tuple[RoleResolution, ...]
    status: str                       # "resolvable" | "blocked"
    certifiable: bool                 # resolvable and no role has unobserved capabilities
    certified: bool                   # always False (AP 00017)

PREDICATES = {"gemini_cli_available": "gemini_cli_available",
              "doubt_reviewer_fable": "doubt_reviewer",
              "implementor_codex_present": "implementor_codex_present"}

def resolve_profile(policy: Mapping[str, object], *, profile_id: str, lane: str,
                    facts: ProfileFacts, implemented: Mapping[str, frozenset[str]],
                    observed: Mapping[str, frozenset[str]] | None) -> ProfileResolution: ...
```

Rules:

- Mandatory reviewer jobs = `procedure.lanes[lane].required_reviewer_jobs`
  plus each `conditional_reviewer_jobs` job whose predicate holds:
  `gemini_cli_available` -> `facts.gemini_cli_available is True`;
  `doubt_reviewer_fable` -> `facts.doubt_reviewer == "fable"`;
  `implementor_codex_present` -> `facts.implementor_codex_present is True`.
  An unknown predicate id, profile id or lane raises `ValueError`.
- Each reviewer job takes `execution_profiles[profile_id].role_bindings[job].adapters[0]`;
  `ADAPTER_KINDS` gives host and execution. Requirement key:
  `reviewer-in-session` or `reviewer-cross-session` from `contracts/hosts.json`.
- One implementor row per `implementor_providers` entry, host via
  `PROVIDER_HOSTS`, requirement `implementor`, execution `cross-session`.
- `claude_free` is True iff no provider in `implementor_providers`, no
  binding provider and no fallback provider is `anthropic`. In a
  `claude_free` profile any row resolving to `claude` gets
  `missing=("claude_excluded",)`; fallbacks are never used.
- `missing` = required minus `implemented[host]`; `unobserved` = required
  minus `observed[host]` (all required when `observed` is None).
- `status` "resolved" iff `missing` is empty; profile "resolvable" iff every
  row is resolved.

Expected results (pinned by `tests/autopilot/test_roles.py`) for
`profile_id="codex-gemini", lane="full"`, facts
`(gemini_cli_available=True, doubt_reviewer=None, implementor_codex_present=True)`,
`implemented` from the adapters: rows `alice`, `blake`, `bob` -> codex,
`carl`, `eve` -> gemini, `implementor:openai` -> codex; all resolved;
`claude_free` True; profile resolvable; `certifiable` False with no observed
evidence. With `gemini_cli_available=False`, `carl` is not mandatory and
`eve` still is.

### §7 Guards (`guards.py`)

Kept: `GuardDuty`, `GuardOutcome` (four fields), `run_guard` signature, the
pure/stateful partition.

Changes:

- `_relay` validates the verdict per §4.
- `delegation` checks depth **before** the child starts:
  `child_depth >= jobs.MAX_CHILD_DEPTH` denies with
  `delegation: recursion_depth` whatever the skill; otherwise a non-empty
  phase `dispatch_skill` denies as today; `""` allows. This is the native-child
  recursion bound; `close_native_child` only records results.
  `CLAUDE_CODE_CHILD_SESSION` was observed set inside a Claude Code subagent
  on 2026-11-15; `agent_id` in hook input is a second signal. The §10 Claude
  probe adds one observation, `child_lineage`, from a bound run whose prompt
  asks for one Agent dispatch that itself tries an Agent dispatch.
  `child_lineage` is observed only if the trace shows the top-level Agent
  call allowed (`child_depth` 0, so the signal is absent in the parent
  session) **and** the nested call denied with `recursion_depth`. Any other
  pattern is `not_observed` (`no_child_lineage` when the nested call was not
  denied, `parent_marked_as_child` when the top-level call was denied), and
  `delegation` is then not observed, so the Claude in-session reviewer rows
  stay uncertifiable. The second outcome would also mean every activated
  session denies all Agent calls; Risks names it.
- Context keys per duty (pure duties deny on a missing or mistyped key, as now):

| Duty | Kind | Local keys | Controller-bound keys (via `seam.read_facts`) |
|---|---|---|---|
| `document_location` | pure | exactly one of `document_path: str`, `command: str`; optional `project_root: str` (absolute) | none |
| `delegation` | pure | `dispatch_skill: str` (`""` = no skill named), `child_depth: int` | none |
| `post_handoff` | pure | `requested_skill: str`, `session: str` | `leave_recorded: bool`, `leave_session: str` |
| `departure` | pure | none | `leave_row_written: bool`, `last_store_write_at: int`, `leave_row_at: int` |
| `context_reinjection` | pure | none | `contract_card_present: bool`, `contract_card_body: str` |
| `custody_push`, `state_integrity`, `review_completeness`, `live_job` | stateful | as passed | verdict from `seam.evaluate_guard` |

- `document_location` normalization (closes v1c2-R17): with `project_root`,
  an absolute `document_path` under the root becomes root-relative; a
  relative path stays relative; both then use the existing store and
  lifecycle checks. `/repo/backlog/x.md` with `project_root="/repo"` and
  `backlog/x.md` give the same deny. An absolute path outside the root keeps
  the current whole-path store check.
- `document_location` `command` mode (source Bash mode): tokens from
  `shlex.split(command, posix=True)` with `punctuation_chars=True` via
  `shlex.shlex` (so `>`, `>>`, `<`, `|`, `;`, `&`, `(`, `)` become separate
  tokens; on `ValueError`, whitespace split). Each token is then cleaned:
  a leading run of redirection characters `[0-9]*[<>&]+` is stripped
  (`>backlog/x.md` -> `backlog/x.md`, `2>>done/y` -> `done/y`), and a token
  of the form `NAME=value` or `--opt=value` is replaced by `value`. Every
  cleaned token containing `/` is normalized like `document_path`; deny when
  its first relative part is in `("backlog", "wip", "hold", "done")` outside
  the store.
- `def is_git_push(command: str) -> bool` (conservative superset; a false
  positive only costs a seam consultation):
  1. Split `command` into segments on newlines, `;`, `&&`, `||`, `|`, `&`.
  2. True if any segment, after leading `NAME=value` assignments and any
     run of `command`/`exec`/`env`/`sudo`/`nice`/`time`/`nohup` prefixes,
     has an executable token whose `PurePosixPath(token).name == "git"`
     (so `/usr/bin/git` and `./git` count) and the token `push` appears
     anywhere after it in that segment. Git option spellings are not parsed
     at all (`git --git-dir .git push`, `git -c a=b push` match), which makes
     this a superset of the push grammar; `git log --grep push` is a
     tolerated false positive.
  3. True if the command contains `$(`, a backtick, `eval`, `sh -c`,
     `bash -c`, `zsh -c`, `xargs` or `<<` and the words `git` and `push`
     both appear anywhere in it (`\bgit\b`, `\bpush\b`): forms the grammar
     cannot classify fail closed.
  4. Otherwise False.
  Fixtures: the source `hooks/test_guard_push_grammar.py` cases at pin
  `e960ef1c` (§13), plus denial cases `"git status\ngit push origin HEAD"`,
  `"FOO=1 git -C x push"`, `"sh -c 'git push'"`, `"echo $(git push)"`, and
  `"/usr/bin/git push origin HEAD"`, `"git --git-dir .git push origin HEAD"`,
  `"nohup env A=1 git push"`, and allow cases `"git pushd-notes"` (no `push`
  token), `"echo git push"` (executable is `echo`). Each denial fixture
  asserts that `custody_push` was passed to the seam (or refused with
  `missing_controller_seam`), not only that `is_git_push` returned True.
  Command-mode denial fixtures: `"echo text >backlog/x.md"`,
  `"cp a.md --target-directory=wip/"`, `"mv x.md\ndone/x.md"`.

### §8 Hook entry (`interception.py`)

```python
NEUTRAL_EVENTS = {"PreToolUse": "pre_tool", "PostToolUse": "post_tool",
                  "Stop": "stop", "SessionStart": "session_start"}
MAX_HOOK_INPUT_BYTES = 1048576
MAX_TRACE_BYTES = 1048576
TRACE_ENV = "AUTOPILOT_HOOK_TRACE"
BINDING_MARKER = (".autopilot", "controller")

@dataclass(frozen=True)
class HookRegistration:
    event: str
    matcher: str | None
    timeout: int

@dataclass(frozen=True)
class DutyCall:
    duty: GuardDuty
    context: Mapping[str, object]

@dataclass(frozen=True)
class HookDecision:
    host_id: str
    event: str
    session: NativeSession | None
    project_root: str
    bound: bool
    outcomes: tuple[GuardOutcome, ...]
    skipped: tuple[tuple[str, str], ...]   # (duty, "unbound" | "not_applicable_on_host")
    allowed: bool                          # all(outcome.allowed)
    additional_context: str | None         # validated contract_card_body when context_reinjection allowed, else None

@dataclass(frozen=True)
class HookReply:
    stdout: str
    exit_code: int

def find_binding(cwd: Path) -> Path | None: ...
def evaluate_hook(host_id: str, event: str, payload: Mapping[str, object], *,
                  env: Mapping[str, str], seam: ControllerSeam | None) -> HookDecision: ...
def run_hook(host_id: str, event: str, stdin: bytes, *, env: Mapping[str, str]) -> HookReply: ...
```

- `find_binding(cwd)`: walks `cwd` and its parents; returns the first
  directory `D` where `D/.autopilot/controller` is a real directory
  (`os.lstat`, `S_ISDIR`, not a symlink). It stops after checking the first
  directory that contains a `.git` entry (the repository top), so a binding
  never leaks from an enclosing repository into a nested one. It reads no
  file inside.
- `evaluate_hook`: `project_root` = binding directory when bound, else the
  payload `cwd`. Duty calls come from `adapter(host_id).translate_hook`.
  Unbound: stateful duties and duties with controller-bound keys are skipped
  with `"unbound"`; local pure duties run. Bound: every call runs; controller
  facts come from `seam.read_facts`; with `seam is None` each such duty
  returns `GuardOutcome(allowed=False, reason="missing_controller_seam", ...)`.
- `run_hook` (CLI path) always passes `seam=None` in this PRD. It reads at
  most `MAX_HOOK_INPUT_BYTES`; oversized, non-JSON, non-object input or a
  missing `cwd` produce, for `PreToolUse`, a deny with reason
  `hook_input_invalid`, and for other events a `systemMessage` warning; exit 0
  either way. Event names outside the host's `HOOK_REGISTRATIONS` are a usage
  error (exit 2) before stdin is read.
- Trace (observability, opt-in): when `TRACE_ENV` is set, `run_hook` appends
  one JSON line to that path only if it resolves inside
  `<project_root>/docs/dev/tmp/autopilot/`, opened through
  `_pinned_parent_fd` with `O_WRONLY|O_APPEND|O_CREAT|O_NOFOLLOW`, single
  regular file with one link, and only while its size is below
  `MAX_TRACE_BYTES`. A line holds `ts`, `host_id`, `event`, `session_id`,
  `session_source`, `plugin_root` (`Path(__file__).resolve().parents[1]`),
  `bound`, and per outcome `duty`, `allowed`, `reason`. It never records
  `tool_input`, commands or contexts. A refused trace write prints one stderr
  line and does not change the decision.

### §9 Generated client assets (`tools/autopilot/build-compatibility.py`)

CLI: `build-compatibility.py [--project-root PATH] [--check]`.

- Host IDs come from `contracts/hosts.json` and pass through `hosts.adapter()`
  before any import (closes v1c2-R7).
- Declared capabilities must equal `IMPLEMENTED_CAPABILITIES`, and §3's
  invariants must hold; else stderr names the first violation, exit 1, no
  file written.
- Writes `compatibility/<host>.json`:

```json
{"schema_version": 2, "host_id": "...", "capabilities": ["sorted"],
 "probe_kind": "static", "certified": false,
 "registration": {"asset": "...", "activation": "client-manifest-hooks-field"} ,
 "duty_coverage": {"<duty>": "intercepted" | "not_applicable_on_host" | "blocked:<reason>"},
 "blockers": {"<capability>": "<reason>"}}
```

  `duty_coverage` lists all nine duties: `intercepted` when some registration
  of that host maps to the duty (§2 table), `not_applicable_on_host` for codex
  `delegation`/`post_handoff`, `blocked:no_package_local_registration_surface`
  for every gemini duty.
- For hosts with registrations writes `compatibility/<host>/hooks.json`:
  `{"hooks": {"<Event>": [{"matcher": "<m>" (omitted when None), "hooks": [{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py\" --hook <host> --event <Event>", "timeout": <t>}]}]}}`,
  events in registration order. Claude substitutes `${CLAUDE_PLUGIN_ROOT}`
  textually; Codex sets `CLAUDE_PLUGIN_ROOT` in plugin hook processes and the
  shell expands it.
- Output bytes: `json.dumps(obj, indent=2) + "\n"`, no environment input, so
  identical on every machine. Writes each file to a temp sibling and
  `os.replace`s it; removes a `compatibility/<host>.json` or
  `compatibility/<host>/hooks.json` whose host or registration is no longer
  declared (closes v1c1-R22).
- `--check`: builds in memory, exits 1 naming the first differing or extra
  file, writes nothing.

No manifest pointer is generated. Activation (a `hooks` field in a client
manifest pointing at the asset) is a gated install step outside this PRD.

### §10 Probes and doctor

`tools/autopilot/probe-host.py HOST [--project-root PATH] [--static-only] [--timeout SECONDS]`
(default timeout 120, max 600; at most three host invocations per run: two
bound runs and one unbound control run):

1. Static record: `hosts.probe_host` as today.
2. Unless `--static-only`, the host is available and has a probe plan: create
   `docs/dev/tmp/autopilot/probes/<host>-<ts>/` (pinned descriptor, `O_EXCL`
   naming with the existing 10-attempt retry) holding `plugin/` (a copy of
   `plugins/autopilot`), `project/` (bound: `.autopilot/controller/` and
   `docs/dev/tmp/autopilot/`), `control/` (unbound: `docs/dev/tmp/autopilot/`
   only) and `remote.git` (a local bare repository). `project/` and
   `control/` are `git init` repositories with one commit and a remote named
   `probe-remote` pointing at `remote.git` (local path, no network); the
   tool runs these `git` commands itself. Resource check: every symlink in `plugin/`
   must resolve inside `plugin/`, and every asset named in
   `compatibility/<host>.json` must exist inside `plugin/`; else outcome
   `resource_escape`, no invocation.
3. Invocations (cwd `project/`, environment = caller environment plus
   `AUTOPILOT_HOOK_TRACE=<project>/docs/dev/tmp/autopilot/hook-trace.jsonl`;
   HOME and host config untouched; stdin =
   `PROBE_PROMPT = "Use your shell tool to run exactly: git push probe-remote HEAD:refs/heads/probe-<run>"`,
   where `<run>` is `bound-1`, `bound-2` or `control`). Because `project/`
   and `control/` are each their own git repository, §8 `find_binding` stops
   at them and never sees a marker in the enclosing source repository, so
   `control/` is unbound even when the source repository is bound
   (`test_host_argv.py::test_probe_control_is_unbound_inside_a_bound_source_repo`).
   Per invocation:

   | Run | cwd | Registration | argv target | Trace path |
   |---|---|---|---|---|
   | bound-1, bound-2 | `project/` | claude: `--plugin-dir <plugin>`; codex: `project/.codex/hooks.json` | codex `-C <project>` | `project/docs/dev/tmp/autopilot/hook-trace.jsonl` |
   | control | `control/` | claude: same `--plugin-dir <plugin>`; codex: `control/.codex/hooks.json` (same rendered bytes) | codex `-C <control>` | `control/docs/dev/tmp/autopilot/hook-trace.jsonl` |

   Gemini has no control run (no interception to prove). Host plans:
   - claude: writes `plugin/.claude-plugin/plugin.json`
     `{"name": "autopilot", "hooks": "./compatibility/claude/hooks.json"}`
     inside the copy only; argv
     `["claude", "-p", "--plugin-dir", <plugin>, "--output-format", "json"]`,
     once per run in the table.
   - codex: writes `project/.codex/hooks.json` and `control/.codex/hooks.json`
     from `compatibility/codex/hooks.json` with `${CLAUDE_PLUGIN_ROOT}`
     replaced by the copy's absolute path; argv
     `["codex", "exec", "--dangerously-bypass-hook-trust", "-C", <run cwd>, "-"]`,
     once per run in the table. Evidence marks `registration_surface: "project-layer"`: plugin-layer
     loading stays unobserved until installation is authorized.
   - gemini (hook-free plan): argv
     `["gemini", "-p", GEMINI_PROBE_PROMPT]`, twice, where
     `GEMINI_PROBE_PROMPT = "Use your shell tool to run exactly: python3 <plugin>/scripts/autopilot.py --record-session gemini --project-root <project>"`
     with both paths absolute. `registration_surface` is `"none"` and
     `interception` is recorded `{"status": "unavailable", "reason": "no_package_local_registration_surface"}`.
     An auth refusal (non-zero exit, for example `IneligibleTierError`) makes
     every capability `unavailable` with the first stderr line's error class
     as reason.
   Every host's invocations are thus traced either by hooks (claude, codex)
   or by `--record-session` (gemini); claude and codex prompts also append
   the same `--record-session <host>` command after the push command, so
   identity is observable even if a hook does not load.
4. Observations from the trace: `identity` observed iff a line for the host
   has a `session_id`; `isolation` iff the two bound invocations show two
   distinct session ids; `interception` iff **all** of: a bound-run
   `PreToolUse` trace line has duty `custody_push` refused with
   `missing_controller_seam`, `remote.git` has no `refs/heads/probe-bound-1`
   or `refs/heads/probe-bound-2` after the bound runs (the host honored the
   deny), and `remote.git` has `refs/heads/probe-control` after the control
   run (the command does execute when not guarded). A trace refusal without
   the missing ref, or a missing control ref, is `not_observed` with reason
   `host_did_not_enforce` or `control_did_not_execute`. `resources` iff every
   trace line's `plugin_root` equals the copy's realpath. **Resource escape
   invalidates the run:** if the pre-launch resource check fails, or any
   trace line names another `plugin_root`, every capability of that run is
   recorded `not_observed` with reason `resource_escape`, and
   `"resource_check": "failed"`. Each capability gets
   `{"status": "observed" | "not_observed" | "unavailable", "reason": str | null}`.
   A non-zero exit, timeout or missing trace is `not_observed` with that
   reason; it is never turned into success.
5. Evidence file `docs/dev/tmp/autopilot/probes/<host>-<ts>.json` (`O_EXCL`):
   `{"schema_version": 2, "static": <ProbeResult>, "run_dir", "registration_surface", "invocations": [{"argv", "exit_code", "timed_out", "duration_seconds", "stdout_sha256", "stderr_sha256", "stdout_path", "stderr_path"}], "trace_lines", "observed": {...}, "resource_check", "certified": false}`.
   Raw stdout/stderr stay as files in the run directory; the evidence file
   carries only digests and paths, so no host output lands in a tracked file.
   Exit 0 for any completed probe, 2 for usage errors.

`doctor.diagnose(*, project_root: Path) -> DoctorReport`:

```python
@dataclass(frozen=True)
class DoctorReport:
    schema_version: int                 # 2
    hosts: list[ProbeResult]            # static
    observed: dict[str, dict]           # host -> latest evidence summary or {"status": "not_probed"}
    profiles: list[ProfileResolution]   # "source-parity" and "codex-gemini", lane "full"
    simulation: dict                    # {"simulated": True, "guards": [GuardOutcome, ...]}
    certified: bool                     # always False
    generated_at: str
```

- `observed` reads the newest `docs/dev/tmp/autopilot/probes/<host>-*.json`
  per host by name, validates `schema_version == 2`, and maps
  `observed[cap].status == "observed"` to the observed set. Evidence with
  `resource_check != "passed"` contributes an empty observed set, so a run
  with a resource escape can never make a role `certifiable`.
- Profile facts: `gemini_cli_available` = the newest gemini evidence has at
  least one invocation with exit 0 (the §10 gemini plan always invokes
  gemini when the binary exists, so this is a host fact, not a design
  constant); `implementor_codex_present` = `"openai"` in the
  profile's `implementor_providers`; `doubt_reviewer` = None.
- `simulation` runs each duty once with a representative valid context
  (`DOCTOR_CONTEXTS` constant, one per duty, all allow-path) and, for stateful
  duties, a private `_SimulationSeam` that allows. It is labelled
  `simulated: True` and is never merged into `observed` (closes v1c2-R2,
  R16, v1c1-R30).

### §11 `autopilot.py` CLI

`_CAPABILITIES` appends, in order: `"hook-v1"`, `"request-job-v1"`,
`"bind-job-v1"`, `"close-child-v1"`, `"resolve-roles-v1"`,
`"record-session-v1"`.

| Mode | Companions | Exit |
|---|---|---|
| `--hook HOST` | `--event EVENT` (required); stdin JSON | the `HookReply.exit_code` (0); 2 for unknown host, a host without interception, or an unregistered event |
| `--request-job REQUEST.json` | `--project-root` (required), `--out PATH` (required in standalone) | 0 report; 1 `{"ok": false, "error": <JobRefused.code>}`; 2 usage |
| `--bind-job JOB.json` | `--project-root` (required) | 0; 1 refusal (child from `hosts.current_session(request host, os.environ)`, None -> `missing_native_session`); 2 usage |
| `--close-child REQUEST.json` | `--project-root` (required) | 0; 1 refusal; 2 usage |
| `--resolve-roles` | `--profile ID`, `--lane LANE` (required), `--facts FACTS.json` (optional, default all False/None) | 0 resolvable; 1 blocked; 2 usage |
| `--record-session HOST` | `--project-root` (required) | 0 and prints `{"schema_version": 1, "host_id", "session": {...} or null, "plugin_root", "traced": bool}`; appends the same record as one trace line through §8's trace writer when `AUTOPILOT_HOOK_TRACE` is set (event `"record_session"`, no outcomes); 2 usage. It is the hook-free identity observation used by the gemini probe plan (§10) and works for every host. |

`REQUEST.json` for `--request-job` is
`{"schema_version": 1, "job_id", "role_id", "host_id", "tier", "effort", "inputs", "excluded_input_kinds"}`
(exactly these keys; ancestry comes from `jobs.derive_ancestry(os.environ, project_root)`);
the requester comes from `hosts.current_session(<calling host>, os.environ)`
where the calling host is the first adapter whose `SESSION_ENV_VAR` is set
(none -> `missing_native_session`). The `--out` file is created with
`O_EXCL|O_NOFOLLOW` through `_pinned_parent_fd`. All new request flags join
`_INPUTS`, so live-state paths are refused. `--run-guard` keeps `seam=None`
and the README states that stateful duties therefore always refuse there
(v1c1-R27).

### §12 Provenance receipt chain

Receipt `docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json`:

```json
{"schema_version": 1, "prd": "00014",
 "supersedes": {"artifact_id": "docs/dev/project-management/autopilot/reports/00018-v2-controller-delivery-receipts.json",
                "artifact_sha256": "<sha256 of that file>"},
 "package_revision": "<40 hex commit holding the final bytes of every listed path>",
 "paths": ["plugins/autopilot/README.md", "plugins/autopilot/CHANGELOG.md",
           "plugins/autopilot/scripts/autopilot.py", "<every AP00014 asset path>"],
 "tasks": [{"task", "tests", "command", "passed", "failed", "skipped", "exit_code", "duration_seconds"}],
 "real_host": {"status": "unavailable", "reason": "<probe outcome summary per host; no certification>"}}
```

`helper_map_successor.py` additions:

```python
HOST_RECEIPT_PRD = "00014"
AP00014_ASSET_PATHS = (
    "plugins/autopilot/compatibility/claude.json",
    "plugins/autopilot/compatibility/claude/hooks.json",
    "plugins/autopilot/compatibility/codex.json",
    "plugins/autopilot/compatibility/codex/hooks.json",
    "plugins/autopilot/compatibility/gemini.json",
    "plugins/autopilot/contracts/hosts.json",
    "plugins/autopilot/scripts/claude.py",
    "plugins/autopilot/scripts/codex.py",
    "plugins/autopilot/scripts/doctor.py",
    "plugins/autopilot/scripts/gemini.py",
    "plugins/autopilot/scripts/guards.py",
    "plugins/autopilot/scripts/hosts.py",
    "plugins/autopilot/scripts/interception.py",
    "plugins/autopilot/scripts/jobs.py",
    "plugins/autopilot/scripts/roles.py",
)
def validate_host_receipts(receipts: dict, supersedes_artifact: dict | None) -> None: ...
# validate_receipts(receipts, prd="00014"); package_revision required;
# supersedes must equal the loaded AP00018 artifact; every path in
# (*SHARED_PATHS, "plugins/autopilot/scripts/autopilot.py", *AP00014_ASSET_PATHS); unique.
def refresh_listed_row(row: dict, path: str, cited: dict, prd: str = "00018") -> None: ...
# the landed sentence and expected_outcome text name f"AP{prd}"
```

`update_helper_map.py`:

- `DEFAULT_HOST_RECEIPTS = "docs/dev/project-management/autopilot/reports/00014-v2-host-delivery-receipts.json"`,
  flag `--host-receipts`, loaded like the successor when the default exists.
- `AP00014_DIGESTED = AP00014_ASSET_PATHS`.
- `register_ap00014_assets(result, root)` runs on every generator run,
  receipt or not: for each path in `AP00014_ASSET_PATHS` that exists under
  `root` and has no asset row, it upserts an asset row (digest from bytes,
  evidence `{"status": "planned", "artifact_id": null, "artifact_sha256": null, "tested_package_revision": null}`,
  adaptation reason "Newly authored AP00014 host-execution file; no pinned
  source asset or source sections. The digest records current packaged
  bytes.", acceptance case status `"planned"`, the same text v1 rows carry)
  and an owner row with `delivery_prd "00014"`. So every task that adds a
  packaged file regenerates the map in the same commit and the package roster
  test stays green at every commit; only evidence waits for the receipt.
- Order in `apply`: AP00013 rows, then the AP00018 successor, whose
  `verify_listed_paths_match_revision` runs only over its paths **not** listed
  by a valid host receipt, then `apply_host_receipt(result, root, receipts, artifact)`:
  verify all host receipt paths against its revision; register missing
  AP00014 asset rows and owner rows (`delivery_prd "00014"`, adaptation
  reason "Newly authored AP00014 host-execution file; ..."); refresh every
  listed row with `refresh_listed_row(..., prd="00014")`; README and
  CHANGELOG evidence becomes self-referential at the host revision, as the
  successor does today; `autopilot.py` cites the host receipt.
- Without a host receipt, evidence is unchanged from today; only
  `register_ap00014_assets` and `refresh_ap00014_digests` act.

Test edits that must land with the first task that adds a packaged file
(each named so no task leaves the suite red):

- `tests/autopilot/test_helper_provenance_real.py`: `AP00014_TARGETS =
  frozenset(AP00014_ASSET_PATHS)` (15 paths, imported values written out
  literally); `AP00014_OWNED = AP00014_TARGETS | {"tools/autopilot/probe-host.py", "tools/autopilot/build-compatibility.py"}`.
- `tests/autopilot/test_package.py`: `AP00014_OWNED` gains
  `compatibility/claude/hooks.json`, `compatibility/codex/hooks.json`,
  `scripts/interception.py`, `scripts/roles.py`.
- `assert_refreshed_evidence` becomes a chain rule, written as:
  `latest = host receipt if it exists and lists path, else AP00018 successor if it lists path, else AP00013 receipts`.
  For README.md and CHANGELOG.md: evidence equals
  `{"status": "passed", "artifact_id": path, "artifact_sha256": <current sha>, "tested_package_revision": latest["package_revision"]}`
  and `git show <that revision>:<path>` equals current bytes. For
  `scripts/autopilot.py`: evidence equals the AP00013 receipts evidence
  while no host receipt lists it, and
  `{"status": "passed", "artifact_id": <host receipt path>, "artifact_sha256": <its sha>, "tested_package_revision": <its revision>}`
  once one does. `load_successor_receipt` keeps validating the AP00018 file;
  its `path in REFRESHED[1:]` membership check stays.
- `test_ap00014_rows_are_owned_and_digested_from_current_bytes` is renamed
  `test_ap00014_rows_cite_the_host_receipt_and_digest_current_bytes` and
  asserts, per `AP00014_TARGETS` row, current digest, owner `00014`, and
  evidence `planned` without a host receipt or equal to the host receipt
  citation with it.

Original receipts stay byte-identical: AP00013 and AP00018 files are never
rewritten; the chain is "supersedes by digest".

### §13 Finding dispositions (input for plan-tasks)

`F` = fixed by the named contract and test; `R` = rejected with evidence;
`D` = deferred to the named owner. Stubs 00042-00064 are cycle-1 rows
R1-R24 in order (00042 = v1c1-R1 ... 00064 = v1c1-R24).

| Finding (stub) | Disp. | Contract | Repair or evidence test |
|---|---|---|---|
| v1c2-R1, 00039, 00041 | F (on master) | §12 keeps it fixed | `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes` stays green after AP00014 edits, through §12's chain rule and its named test edits |
| v1c1-R1 (00042) | F (v1 rework, verified) | §1 | `test_sessions.py::GeminiCapabilityContractTest::test_missing_binary_yields_no_capability_and_a_recorded_reason` |
| v1c1-R2, R20 (00060) | F (v1 rework) + §7 normalization | §7 | `test_guards_pure_duties.py` path and command cases |
| v1c1-R3, R10, R11, R16 (00049-00051, 00056); v1c2-R6, R9 | F | §2 capability-behavior binding, §9 | `test_sessions.py::test_each_implemented_capability_has_its_behavior` |
| v1c1-R4-R8, R24 (00043-00047, 00064) | F (v1 rework, verified 203 passed) | §12 | full gate |
| v1c1-R9 (00048), v1c2-R5, R21 | F | §10 real probe | `test_host_argv.py::test_relocated_host_probe_*` with fake host binaries; Phase 2 real run evidence |
| v1c1-R12 (00052) | F | §12 | `test_ap00014_rows_cite_the_host_receipt_and_digest_current_bytes` |
| v1c1-R13, R35 (00053) | F | §10, §11 | `test_facade.py` CLI cases for `--diagnose`, `--hook`, `--request-job`; `test_host_argv.py` probe CLI |
| v1c1-R14, R15, R21, R33 (00054, 00055, 00061); v1c2-R8, R22 | F | §6, §10 | `test_roles.py` |
| v1c1-R17 (00057), v1c2-R12 | F (isolation, cleanup, digests, sessions; recursion for cooperating sessions) + D (adversarial standalone recursion: controller `job.plan` lineage, AP 00016/00019) | §5 | `test_jobs.py::ReviewerIsolationTest`, `ChildCleanupTest`, `RecursionBoundTest` (env, depth variable and lineage record each refuse alone; stripped env with a lineage record still refuses) |
| v1c1-R18 (00058), v1c2-R13 | F | §5 standalone instruction | `test_jobs.py::StandaloneInstructionTest` |
| v1c1-R19 (00059), v1c2-R4 | F (package assets) + D (activation: publication/install PRD) | §9 | `test_compatibility.py::test_hooks_assets_*`, `test_interception.py` |
| v1c1-R22 (00062) | F | §9 stale removal | `test_compatibility.py::test_undeclared_host_bundle_is_removed` |
| v1c1-R23 (00063) | F (v1 rework, `O_EXCL`) | §10 | existing `test_probe_host_never_writes_through_an_existing_evidence_name` |
| v1c1-R25, R34, R37, R43 | F (v1 rework, verify) | - | re-run; R37/R43 must read `SCRIPTS / "autopilot.py"` directly |
| v1c1-R26, R36 | F | §10 | evidence-path test |
| v1c1-R27 | F (documented) | §11 | README text test |
| v1c1-R28, R31, R32; v1c2 auto-dismissed rows (effort, digests) | F | §5 | `test_jobs.py::BuildJobRequestValidationTest`, mutation test |
| v1c1-R29; v1c2 auto-dismissed relay row | F | §4 | `test_guards.py::test_malformed_verdict_refuses`, `test_jobs.py::test_seam_cannot_override_mode` |
| v1c1-R30, v1c2-R25 | F | §2 `CLAUDE_CODE_SESSION_ID` | `test_sessions.py::test_claude_identity_reads_claude_code_session_id` |
| v1c1-R38, R39, R42 | F | §4 (FakeSeam out), §9 | `test_package` roster has no `FakeSeam` in `scripts/jobs.py` |
| v1c1-R40, R41 | R | - | R40 is a passing preservation invariant; R41 belongs to AP00018 and is fixed there (stub 00040: full suite 1615 passed at `c988f45`) |
| 00038, 00040 | R (meta) | - | 00038 is the cycle-1 cap summary (content mapped above); 00040 is the controller-suite failure set, fixed by AP00018 v2 |
| v1c2-R2, R16 | F | §10 simulation | `test_facade.py::test_diagnose_reports_simulation_apart_from_observation` |
| v1c2-R3 | F | §2, §6 | `test_roles.py::test_codex_gemini_full_lane_resolves_without_claude` |
| v1c2-R7 | F | §1 `adapter()`, §9 | `test_compatibility.py::test_unknown_host_executes_no_module` |
| v1c2-R10 | R | §10 | static auth is a hint only; authority is the real probe. Evidence: `ProbeResult.certified` is False and doctor exposes `observed` separately |
| v1c2-R11 | F | §1 `CapabilityStatus.__post_init__` | `test_host_argv.py::test_capability_status_rejects_unknown_status` |
| v1c2-R14 | F | §13 characterization | `test_host_argv.py::test_effort_mismatch_is_a_corrected_target`, `test_interception.py::test_hook_behavior_equivalence` |
| v1c2-R15 | F | §14 | README/CHANGELOG tests |
| v1c2-R17 | F | §7 | `test_guards_pure_duties.py::test_absolute_and_relative_spellings_decide_alike` |
| v1c2-R18 | F | - | `while 10` asserted as a violation; scanner checks literal truthiness via `ast` |
| v1c2-R19 | F | - | collision test seeds via a frozen clock (`PROBE_HOST_NOW` env read only by the tool's timestamp function) |
| v1c2-R20 | F | - | redundant token collector removed |
| v1c2-R23 | F/D | as above | live certification D to AP 00017 |
| v1c2-R24 | F | §10 | named retry constant `EVIDENCE_NAME_ATTEMPTS = 10` |
| v1c2-R26 | R | - | cause recorded: the 19 controller failures, fixed by AP00018 v2 |
| v1c2-R27-R32 | F | - | each touched test file gains at least one fail-first test per behavior it covers (§ Test strategy) |

Hook characterization fixture `tests/autopilot/hook_characterization.json`:
`{"schema_version": 1, "source_commit": "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48", "cases": [{"case_id", "source_ref", "host": "claude", "event", "payload", "bound", "facts", "expected": "allow" | "deny", "divergence": null | "<reason>"}]}`.
`source_ref` is `<path>:<line>` at the pin. Cases cover each source hook's
own test cases for document location (file and Bash modes), push grammar,
skill-after-leave, phase delegation (one allowed and one denied fixture from
`hooks/fixtures/phase_delegation/`), and Stop coverage. A case whose target
behavior differs from the source (for example the lexicon-based delegation
detection narrowed to explicit `autopilot:` skill names, or
`missing_controller_seam` in bound sessions) carries a non-null `divergence`.
The effort characterization lives in the same file as cases with
`"host": "runner"`, recording that source `sonnet-run.sh` drops `--effort`.

### §14 Documentation

CHANGELOG `[Unreleased]` bullets: host adapters with the real session
variables; job requests and bindings; generated Claude and Codex hook assets
(not activated); role resolution and doctor; per client, the duties still
unavailable: Codex `delegation`, `post_handoff` not applicable; Gemini every
duty blocked (`no_package_local_registration_surface`); every stateful duty
refuses in a bound session until the controller seam lands (AP 00016); no
host certified. README gains a `## Host adapters and guards` section covering
the five new modes, `--probe-host`, `--run-guard`, `--diagnose`, and the same
unavailable list.

## Data flow

1. **Hook path.** Host fires an event -> generated `hooks.json` runs
   `autopilot.py --hook <host> --event <Event>` -> `interception.run_hook`
   reads bounded stdin -> `find_binding(cwd)` -> adapter `translate_hook` ->
   `guards.run_guard` per duty (seam None) -> `HookDecision` -> optional trace
   line -> adapter `render_hook_reply` -> stdout to the host.
2. **Cross-session job.** Requesting session: `--request-job` ->
   `build_job_request` (digests read from files) -> `request_job` ->
   controller mode: intent payload to `seam.submit_job` (none in the package
   until AP 00016) / standalone: job file written with `O_EXCL` plus
   instruction -> human or OVCAQ launches the argv -> child session:
   `--bind-job` -> `bind_job_session` verifies host, distinct session, input
   digests -> binding record returned as evidence.
3. **In-session child.** Claude Agent subagent ends or is cancelled by the host
   -> parent runs `--close-child` -> raw output stored, record returned.
4. **Assets.** `contracts/hosts.json` + adapter constants ->
   `build-compatibility.py` -> `compatibility/*.json` and
   `compatibility/{claude,codex}/hooks.json` (deterministic, `--check` in CI
   tests).
5. **Evidence.** `probe-host.py` -> isolated copy and project -> host runs ->
   hook trace -> evidence file -> `doctor.diagnose` reads newest evidence ->
   `roles.resolve_profile` -> report (`certified` False).
6. **Provenance.** Final code commit -> host receipt pinned to that commit ->
   `update_helper_map.py` -> `source-map.json` -> provenance tests.

No component writes workflow state. Writers are limited to: the `--out` job
file, the `--bind-job` lineage record under `docs/dev/tmp/autopilot/jobs/`,
the `--close-child` artifact, the opt-in trace, and maintainer tools
under `docs/dev/tmp/autopilot/` and `plugins/autopilot/compatibility/`.

## Reuse inventory

- `plugins/autopilot/scripts/log_sink_refusal.py:_pinned_parent_fd` (line 192)
  and `_descend` (line 215): symlink-safe directory descent. Use for the
  `--out` job file, `--close-child` artifact, the hook trace and probe run
  directories.
- `tools/autopilot/probe-host.py` `O_EXCL` 10-attempt naming loop: reuse for
  evidence and run directory names (name the bound `EVIDENCE_NAME_ATTEMPTS`).
- `plugins/autopilot/scripts/autopilot.py:_in_live_state` (line 98),
  `_request` (line 124), `_call` (line 135), `_helper` (line 109): reuse for
  every new mode; do not add a second parser.
- `plugins/autopilot/scripts/review_evidence.py:load_policy` (used by
  `autopilot.py:_check_evidence`): load `review-policy-v1.json` for
  `roles.resolve_profile` and the `input_kinds` check.
- `plugins/autopilot/scripts/hosts.py:unavailable`, `statuses_from`,
  `ProbeResult`: unchanged static probe core.
- `plugins/autopilot/scripts/guards.py:_missing_input`, `_store_rel`,
  `_store_rel_allowed`: extended, not duplicated.
- `tools/autopilot/helper_map_successor.py:validate_receipts`,
  `verify_listed_paths_match_revision`, `refresh_listed_row`;
  `tools/autopilot/update_helper_map.py:register_controller_asset`,
  `owner_row`, `asset_row`, `upsert`: the receipt chain reuses them with a
  `prd` parameter instead of copies.
- `tests/autopilot/test_helper_provenance_real.py:pinned_source_root`
  (line 486): gate for checking `hook_characterization.json` `source_ref`s
  against the pinned source when reachable.
- `tests/autopilot/test_package.py:GUARD` (line 51): audit hook denying process
  launch and network; reuse to prove `--hook`, `--request-job`, `--bind-job`
  never spawn a process.
- Controller error codes: `contracts/controller/workflow-v1.json`
  `x-controller.error_codes`; read, never copied by hand in tests.
- Nothing found for hook stdin translation, job binding or role resolution.
  Greps tried: `rg -n "hook_input|translate_hook|permissionDecision|session_id" plugins/ tools/`
  (only controller `native_session_id` schema hits), `rg -n "role_bindings|implementor_providers" plugins/autopilot/scripts tools/`
  (no resolver; data only in the policy and `export-policy.py`),
  `rg -n "bind|binding" plugins/autopilot/scripts` (only staging `_bind`-free
  text); control search `rg -n "def _pinned_parent_fd" plugins/` hit, proving
  the pattern works. `~/.claude/rules-library/rationalizations.md` synonyms
  were not loaded; synonyms used: probe/detect/observe, bind/attach/claim,
  resolve/route/map, hook/intercept/guard.

## Alternatives considered

1. **Smallest diff: test-and-label repair.** Keep v1's capability lists,
   static probes and `FakeSeam`; fix only the doctor contexts, path
   normalization, verdict validation and build-compatibility import gate.
   About 300 changed lines. Rejected: it leaves cycle-2 R3, R4, R5 and v1c1
   R17-R19 open, which the PRD's Phase 1 and 2 acceptance names directly
   (generated client assets, real probes, Claude-free role resolution,
   job bindings). The extra size of the chosen design buys exactly those
   acceptance scenarios and nothing beyond them.
2. **Activate hooks on install** (package `hooks/hooks.json` at the default
   path, plus `.claude-plugin/plugin.json`). Rejected: both Claude and Codex
   load that same default path, so the file could not name its host; the
   Claude manifest makes `generate_marketplace.py` publish the plugin; and
   activation is live installation. All three are outside this PRD.
3. **Gemini extension packaging** (`gemini-extension.json` plus root
   `hooks/hooks.json`). Rejected: collides with alternative 2's path, is an
   install surface, and the CLI is documented superseded with failing native
   auth. Gemini stays a cross-session reviewer host with identity and
   isolation, which the Claude-free profile needs; its interception gap is a
   named blocker.
4. **Chosen:** per-host generated assets under `compatibility/<host>/`,
   activated only by a gated manifest pointer; a probe that proves
   registration in an isolated copy; job requests as versioned
   `job.plan` intent payloads behind a Protocol seam; role resolution read
   from the packaged policy.

## Risks & edge cases

- **Hooks are packaged, not active.** No session is intercepted until a
  later, authorized install adds the manifest pointer. The bundle's
  `registration.activation` and the README state this; a reader must not
  treat the asset as live enforcement. Rollback: every change is files in the
  package and maintainer tools; reverting the commits restores v1 bytes, and
  no live configuration is ever written.
- **Bound sessions refuse every stateful duty until AP 00016.** In a project
  with `.autopilot/controller/`, an activated hook denies `git push` and
  blocks Stop once per chain with `missing_controller_seam`. This is the
  PRD's `missing_controller_seam_refused` behavior. Unbound projects see only
  the local pure duties.
- **Stop loop.** Bounded by `stop_hook_active` (§2): one block per chain.
- **Child-lineage signal unverified in a parent session.**
  `CLAUDE_CODE_CHILD_SESSION` was observed inside a subagent only. If a host
  version also sets it in top-level sessions, the §7 depth rule denies every
  Agent call in an activated session. The §10 `child_lineage` observation
  detects this (`parent_marked_as_child`) before any activation; hooks are not
  active until then.
- **Hook failure mode.** Invalid input fails closed only for PreToolUse; other
  events warn. A buggy hook therefore blocks tool calls in an activated
  session; the user disables it by removing the manifest pointer.
- **Real probes cost model calls.** At most two invocations per host per run,
  each bounded by `--timeout` (max 600 s), manual only, never run by tests.
- **Codex project-layer substitute.** The Codex probe proves event, identity
  and decision semantics through the project hook layer, not plugin-layer
  loading; evidence says so in `registration_surface`. Plugin-layer proof
  waits for install authorization.
- **Session variables can change between host versions.** `SESSION_ENV_VAR`
  values are code facts pinned by tests; the probe's `identity` observation
  is the live check. A rename shows up as `identity: not_observed`.
- **Receipt ordering.** The host receipt must pin a commit that already holds
  the final bytes of every listed path, including CHANGELOG and README; mint
  it last, then regenerate the map (the AP00018 close-out pattern,
  `01fd160`). Editing a listed path after minting re-breaks the provenance
  tests by design. README.md and CHANGELOG.md are listed by the AP00018
  successor, so the generator refuses them once changed until the host
  receipt exists. Therefore no task before Phase 2 task 2 edits either file,
  and Phase 2 tasks 2 and 3 run as one sequence: commit the doc edits, mint
  the receipt pinned to that commit, regenerate the map, commit. Only the
  first of those two commits may show the provenance tests red, and the
  gate runs after the second.
- **Frozen hash skip set.** `test_unrelated_arrays_and_original_owners_stay_byte_semantic`
  keeps skipping `AP00014_TARGETS` from `OTHER_ASSETS_SHA`, exactly as it
  skips controller rows; every skipped row is positively asserted by
  `test_ap00014_rows_cite_the_host_receipt_and_digest_current_bytes`. This is
  scoping, not a blanket exemption: no AP00014 row is unasserted.
- **Delegation detection narrows the source lexicon.** Recorded as a
  `divergence` in the characterization fixture, not hidden.
- **Next likely changes and what this design leaves open.**
  1. AP 00016 implements `ControllerSeam` against the controller; the
     Protocol and reply validation are its contract, and `run_hook` gains a
     seam argument without changing guards.
  2. AP 00017 certifies hosts from probe evidence; the evidence schema
     (`schema_version` 2) and `ProfileResolution.certifiable` are its inputs.
  3. OV 00059 forwards effort and launches Gemini; `JobRequest.effort` is
     already required, `build_job_argv` deliberately excludes it, and the
     `intent_schema` version lets the controller-side `job.plan` schema
     evolve.

## Test strategy outline

Gate (Phase 2 exit):
`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`
and `python3 scripts/validate.py`, with zero AP00014 exclusions beyond §12's
scoped skip set.

Named scenarios:

| Scenario | File::test |
|---|---|
| `hook_behavior_equivalence` | `test_interception.py::test_hook_behavior_equivalence` (every fixture case; divergences asserted as the target value) |
| `effort_forwarding` | `test_jobs.py::test_effort_is_required_and_never_in_argv`; `test_host_argv.py::test_effort_mismatch_is_a_corrected_target` |
| `recursive_child_denied` | `test_jobs.py::RecursionBoundTest` (cycle, depth, lineage record); `test_interception.py::test_nested_agent_dispatch_is_denied_before_it_starts` (`agent_id` and `CLAUDE_CODE_CHILD_SESSION` each deny alone) |
| `no_nested_driver_cli` | `test_jobs.py::test_request_bind_close_never_spawn` (`GUARD` audit hook) |
| `reviewer_isolation` | `test_jobs.py::ReviewerIsolationTest` (same session refused, distinct reviewers bind, request ids differ, no shared mutable state) |
| `child_cleanup` | `test_jobs.py::ChildCleanupTest` (cancel keeps raw bytes, foreign child refused, no signal or subprocess) |
| `custody_push_denied` | `test_interception.py::test_bound_git_push_is_denied_for_claude_and_codex` |
| `missing_controller_seam_refused` | `test_guards.py::MissingControllerSeamRefusedTest`; `test_interception.py::test_bound_stateful_duties_refuse_without_seam` |
| `missing_guard_refused` | `test_roles.py::test_implementor_on_gemini_is_blocked_by_interception`; `test_interception.py::test_gemini_hook_is_a_usage_error` |
| `relocated_host_probe` | `test_host_argv.py::test_relocated_host_probe_observes_identity_isolation_interception` with fake `claude`/`codex` scripts on `PATH` that run the generated hook command |
| `shared_core_without_claude` | `test_sessions.py::SharedCoreWithoutClaudeTest` extended to `roles`, `jobs`, `interception` with `claude` unimportable |
| `codex_gemini_role_capabilities` | `test_roles.py::test_codex_gemini_full_lane_resolves_without_claude` |
| `no_coordinator_runtime_in_plugin` | `test_compatibility.py::NoCoordinatorRuntimeInPluginTest` extended to `roles.py`, `interception.py` |

Bug-fix tests that must be seen failing first on current master:
`test_claude_identity_reads_claude_code_session_id`,
`test_absolute_and_relative_spellings_decide_alike`,
`test_malformed_verdict_refuses`, `test_unknown_host_executes_no_module`,
`test_capability_status_rejects_unknown_status`,
`test_undeclared_host_bundle_is_removed`,
`test_diagnose_reports_simulation_apart_from_observation`.
New-behavior tests need not fail first; the provenance chain test is shown
binding by mutating a temp copy of the map (the rework-1 method).

Fakes live in `tests/autopilot/host_fakes.py`; a test asserts
`plugins/autopilot/scripts/jobs.py` defines no `FakeSeam`.

## Review log

Dispatch 1 blockers, fixed in the doc:

- §12 left the package roster and provenance tests red at every commit before
  the receipt, and the test edits were unnamed. Fixed: `register_ap00014_assets`
  registers new AP00014 rows with planned evidence on every generator run;
  §12 now names the `AP00014_TARGETS`, `AP00014_OWNED` (both test files),
  `assert_refreshed_evidence` chain rule and renamed row test; Risks orders
  the README/CHANGELOG edits with receipt minting.
- Recursion bound read caller-written ancestry. Fixed: §5
  `derive_ancestry(env, project_root)` reads the job file named by
  `AUTOPILOT_JOB_REQUEST`; request files carrying `ancestry` are refused;
  managed-mode re-check assigned to the controller's `job.plan`.
- Gemini identity and isolation were unobservable by construction. Fixed:
  §11 `--record-session HOST` (hook-free identity trace) and a §10 gemini
  probe plan that invokes `gemini -p` twice; doctor's `gemini_cli_available`
  is now a host fact.

Dispatch 1 non-blockers and questions, recorded, not fixed:

- Non-blocker: in a bound project with no seam, every Claude `Skill` call is
  denied (post_handoff needs controller facts even for non-autopilot skills)
  and every Edit/Write gets a PostToolUse block (state_integrity); `session`
  for post_handoff has no stated source. Suggested: fetch facts only for
  guarded skills, inject `session` from `HookDecision.session`, list in Risks.
- Non-blocker: uncaught exceptions, hook timeouts or a missing `python3` fail
  open on PreToolUse; exit 2 for usage errors on Stop bypasses the
  `stop_hook_active` bound. Suggested: catch-all rendering a deny/systemMessage
  with exit 0.
- Non-blocker: §11 picks the calling host by the first set session variable;
  a codex or gemini process launched from Claude Code inherits
  `CLAUDE_CODE_SESSION_ID`. Suggested: explicit `--host` or innermost marker.
- Non-blocker: Claude in-session isolation is not shown by `bind_job_session`
  (Agent subagents likely share the parent session id); one child binding two
  jobs is not refused by the stateless binder.
- Non-blocker: SessionStart is a new interception point, not derived from the
  source; `autopilot_context_cap_hook.py`, `note_session_leave.py` and
  `guard_stop_on_live_lanes.py` lack named dispositions in the fixture.
- Non-blocker: codex `apply_patch` and PostToolUse coverage is declared
  `intercepted` but never probed; the codex `tool_input` keys for Bash and
  `apply_patch` are not named.
- Non-blocker: §6 hard-codes `PREDICATES` instead of reading
  `procedure.conditional_predicates`; `eve` can appear twice when both its
  predicates hold; `--resolve-roles` default facts differ from doctor's.
- Non-blocker: §13 sentence "stubs 00042-00064 are cycle-1 rows R1-R24 in
  order" is wrong (R2 has no stub; 00051 = R3, 00060 = R20); the table rows are
  correct.
- Non-blocker: second half of v1c2-R25 (`codex._AUTH_FILE` evaluates
  `Path.home()` at import) has no disposition.
- Question: how `--hook` bypasses `_run_operation`'s JSON printing, and the
  exact `_COMPANIONS`/`_REQUIRED` edits for the new flags.
- Question: `--close-child` request schema (raw bytes cannot ride in JSON;
  parent session source unstated).
- Question: the §2 delegation regex is written with a Markdown-escaped `\|`;
  whether command-mode tokens also get the full store decision.

dispatch 1 (claude): cardinal-sin 0, blocker 3, non-blocker 9, question 3

Dispatch 2 (codex, gpt-6-astra, read-only sandbox) could not read the
repository (`sandbox_apply: Operation not permitted`); its findings judge the
inlined doc and PRD summary. Blockers, fixed in the doc:

- Shell classification let `git status\ngit push` and `echo >backlog/x.md`
  through. Fixed: §7 `is_git_push` splits on newlines and `&`, strips command
  prefixes, fails closed on substitution/`sh -c`/`eval`/heredoc forms that
  mention git and push; command mode tokenizes shell punctuation, strips
  redirection prefixes and `=` values; denial fixtures named.
- Context reinjection never delivered the card. Fixed: §8
  `HookDecision.additional_context`, §2 SessionStart `additionalContext`
  rendering, bounded card size, a test asserting the returned text.
- The interception probe proved a hook decision, not host enforcement.
  Fixed: §10 pushes to a local bare remote; interception counts only when
  the refusal is traced, the bound refs are absent, and an unbound control
  run's ref is present.
- Runtime resource escape did not invalidate a run. Fixed: §10 escape marks
  every capability of the run `not_observed` (`resource_escape`), and doctor
  ignores evidence whose `resource_check` is not `passed`.
- Recursion repair was advisory but counted as fixed. Fixed in scope: §5 adds
  `AUTOPILOT_DISPATCH_DEPTH` and a session-keyed lineage record written at
  `--bind-job`, either of which refuses alone; the remaining adversarial
  standalone residue (strip both variables and never bind) is stated as open
  and deferred in §13 to the controller's `job.plan` lineage check
  (AP 00016/00019), not counted as fixed.

Dispatch 2 non-blockers, recorded, not fixed:

- Non-blocker: doctor accepts probe evidence regardless of the package bytes
  it tested; record tested package and asset digests in evidence and treat a
  mismatch as stale.
- Non-blocker: standalone `steps` set model and effort after launch; for
  `codex exec -` and `claude -p` the settings must precede launch, or the
  instruction must say they cannot be applied yet.

dispatch 2 (codex): cardinal-sin 0, blocker 5, non-blocker 2, question 0

Dispatch 3 (codex verification; repository reads refused again). It judged
resolved, with section citations: dispatch 1's provenance, ancestry and
Gemini-observability blockers, and dispatch 2's reinjection and
resource-escape blockers; dispatch 2's recursion blocker resolved within the
stated cooperative scope with the adversarial residue deferred; dispatch 2's
shell and probe blockers only partly. New and remaining blockers, fixed in
the doc after dispatch 3:

- `is_git_push` still missed `/usr/bin/git push` and
  `git --git-dir .git push`. Fixed: §7 step 2 matches any executable whose
  basename is `git` with a later `push` token and parses no git options;
  fixtures assert `custody_push` reaches the seam.
- The control run could inherit a binding from the enclosing repository, and
  Codex had no control registration. Fixed: §8 `find_binding` stops at the
  first directory holding `.git`; §10 gives a per-invocation table (cwd,
  registration, argv target, trace path) and a bound-source-repo test.
- Native-child depth was checked only after the child ran. Fixed: §2 always
  emits a `delegation` call for `Agent` with `child_depth` from `agent_id` or
  `CLAUDE_CODE_CHILD_SESSION`; §7 denies `recursion_depth` before dispatch;
  §10 adds a `child_lineage` probe observation; Risks names the
  parent-marked-as-child failure.

These three fixes were made after the last permitted dispatch and have not
been re-reviewed (3-dispatch ceiling).

Dispatch 3 non-blocker, recorded, not fixed:

- Non-blocker: the invocation budget is inconsistent: §10 says at most three
  host invocations (two bound plus control), while Risks ("Real probes cost
  model calls") still says two. Planned wording: three for Claude and Codex,
  two for Gemini.

dispatch 3 (codex): cardinal-sin 0, blocker 3, non-blocker 1, question 0
