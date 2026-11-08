# Design: Autopilot host execution and enforcement (AP 00014)

## Architecture fit

Per `designs/00011-autopilot-standalone-design.md` § Ownership: "Process identity,
launch/cancel/retry, driver/model placement, isolation" is OVCAQ's authority;
the plugin only "supplies role requirements and resource references." This PRD
builds the plugin-side half of that seam — the **Adapters** module (native
session identity, in-session delegation, cross-session job *requests*) and the
**Compatibility** module (client-native guards, generated compatibility
bundles, host probes) — with no coordinator runtime, no headless CLI
supervision, and no controller implementation (that is AP 00018-00021).

Both modules sit directly under `plugins/autopilot/scripts/` and
`plugins/autopilot/compatibility/` /`plugins/autopilot/contracts/`, beside the
AP 00012/00013 helpers already there (`review_stage.py`, `dirty_tree.py`,
`log_sink_refusal.py`, `verification.py`, …). They import only stdlib plus
those sibling helpers — no controller package import (`controller/` is a
separate distribution unit per the source design's "no sibling-checkout
imports").

Two execution modes, both real at design time:

- **Standalone** (no OVCAQ): `jobs.py` emits a structured next-session
  instruction (role, inputs, resources, binding) for the user to act on by
  hand. No controller-bound request exists yet because there is no controller
  client to send it to.
- **Controller-bound** (OVCAQ present, simulated here with a fake seam): a
  cross-session/cross-driver job becomes a `JobIntent` payload handed to a
  `ControllerSeam.submit_job()` call. AP 00014 defines the seam's shape and a
  fake implementation for tests; AP 00016 wires the real controller client.

Native session identity and in-session delegation (same-session subagent
dispatch) are real in both modes — they never touch the controller seam, since
nothing cross-session is happening. **Neither is ever executed by this PRD's
Python code.** `can_delegate()` only *reports* whether the running host
exposes a true in-session dispatch primitive: one that runs inside the
current process/session with no new OS process spawned for the dispatched
work, and no separate provider-CLI invocation anywhere in the chain. **Only
Claude has one today** — the `Agent` tool, which the calling skill's own
prompt invokes directly; it is a tool call inside the running session, not a
subprocess. `codex.can_delegate()` and `gemini.can_delegate()` both return
`False`: `codex exec` *spawns a new OS process* running a new Codex instance,
which is cross-session execution by this design's own definition (it needs a
`JobIntent`/`request_cross_session_job`, OVCAQ, or a human to launch it — it
is not something "in-session" at all, and the earlier draft's framing of it
as in-session delegation was the defect this fix removes), and Gemini has no
primitive of either kind. This resolves the PRD's distinction cleanly:
"explicitly permitted in-session delegation" is Claude's `Agent` tool only;
every other cross-driver execution path, including `codex exec`, is a
cross-session job request — "spawn headless provider CLI children inside
plugin scripts" stays a rule this design's Python code never has an occasion
to violate, because it never has an in-session primitive to invoke for a
non-Claude host in the first place. (§ Risks & edge cases)

## Module placement

New files, all under `plugins/autopilot/`:

- `scripts/hosts.py` — host capability model: `HostCapability`,
  `ProbeResult`, `probe_host(host_id)` dispatch, `UNAVAILABLE` sentinel.
- `scripts/claude.py`, `scripts/codex.py`, `scripts/gemini.py` — one adapter
  module per host, each exporting the same four functions (§ Interfaces).
- `scripts/jobs.py` — `JobIntent`, `build_job_intent(...)`,
  `request_cross_session_job(...)`, `ControllerSeam` protocol + `FakeSeam`.
- `scripts/guards.py` — `GuardDuty` enum (the nine duties), `run_guard(duty,
  context, seam)`, nine `_guard_<duty>` functions, `GuardOutcome`.
- `scripts/doctor.py` — `diagnose() -> DoctorReport`; a pure library module
  with no CLI of its own (invoked via `autopilot.py --diagnose`, § `doctor.py`
  below).
- `contracts/hosts.json` — schema for `hosts.py`'s probe/capability records
  (parallel to `contracts/review-policy-v1.json`'s shape).
- `compatibility/claude.json`, `compatibility/codex.json` — generated
  capability/guard-binding bundles (never hand-edited; `build-compatibility.py`
  is their only writer).

New files under `tools/autopilot/`:

- `build-compatibility.py` — reads `contracts/hosts.json` + each adapter
  module's declared capabilities, writes `compatibility/<host>.json`.
- `probe-host.py` — CLI wrapper around `hosts.probe_host`, writing real probe
  evidence under `docs/dev/tmp/autopilot/probes/<host>-<ts>.json` (never
  `~/.claude` or any live user config).

New tests under `tests/autopilot/`: `test_jobs.py`, `test_host_argv.py`,
`test_sessions.py`, `test_guards.py`, `test_compatibility.py` — one file per
module above, plus adversarial/refusal cases per the PRD's named scenarios
(§ Test strategy outline).

**Two existing files ARE edited**, both already on disk and both named by the
PRD's own Structural Decomposition as carrying this work's symbols:

- `plugins/autopilot/scripts/autopilot.py` — the repo's single CLI dispatcher
  (verified: every other script under `scripts/` is a pure library module with
  no `argparse`/`__main__`; `autopilot.py` alone owns `_CAPABILITIES`,
  `_MODES`, and the `_helper()` → `importlib.import_module` registration
  pattern). This PRD's new capabilities register the same way the existing
  ones do — new `_CAPABILITIES` entries `"hosts-v1"`, `"guards-v1"` and
  `"diagnose-v1"`, new `_MODES` entries `"probe_host"`, `"run_guard"` and
  `"diagnose"`, each dispatching via `_helper("hosts")` / `_helper("guards")` /
  `_helper("doctor")` exactly as `"catchup_probe"`
  dispatches via `_helper("catchup")` today. `doctor.py` and
  `build-compatibility.py`/`probe-host.py` are **not** given their own
  `argparse` entry points — that would fork the one-CLI-front-door
  convention this file already establishes with no justification for
  diverging. `doctor.diagnose()` and the `tools/autopilot/*.py` scripts are
  plain library functions / thin scripts that call `autopilot.py`'s new modes
  (or the underlying `hosts.py`/`guards.py` functions directly, for the
  `tools/` scripts which are maintainer-only and already outside the
  packaged-CLI convention — `build-compatibility.py` and `probe-host.py` sit
  beside `tools/autopilot/probe-host.py`'s sibling `requirements-test.txt`,
  not inside the shipped plugin surface).
- `plugins/autopilot/CHANGELOG.md` — the PRD's own Phase 2 task 2 ("Update
  the source map and changelog for supported and still-unavailable client
  duties") edits this file directly; there is no other place that duty could
  land. One entry per host whose capability set this PRD newly establishes
  (e.g. "Codex: identity, delegation, isolation supported; Gemini: identity
  only, delegation unavailable pending OV 00059").

No other existing file is touched: `controller/` (AP 00018-00021's exclusive
surface), the already-shipped AP 00012/00013 helpers (`review_stage.py`,
`dirty_tree.py`, `log_sink_refusal.py`, …, read-only reused per § Reuse
inventory), and every `skills/*/SKILL.md` (preserved source prose under AP
00012's freeze; AP 00015/00016 are where skill prose gets adapted to call
these new adapters) stay untouched by this PRD.

## Interfaces & contracts

### `hosts.py`

```python
CAPABILITY_NAMES = ("identity", "delegation", "isolation", "interception")

@dataclass(frozen=True)
class CapabilityStatus:
    name: str                 # one of CAPABILITY_NAMES
    status: str               # "available" | "unavailable" | "unimplemented"
    reason: str | None        # set when status != "available":
                               # UNAVAILABLE_NO_BINARY / UNAVAILABLE_NO_AUTH
                               # for "unavailable"; None for "unimplemented"
                               # (the adapter has no check for this name at all)

@dataclass(frozen=True)
class HostCapability:
    host_id: str                              # "claude" | "codex" | "gemini"
    statuses: dict[str, CapabilityStatus]      # keyed by CAPABILITY_NAMES

@dataclass(frozen=True)
class ProbeResult:
    host_id: str
    available: bool              # True iff the host binary/auth itself is
                                   # reachable at all; independent of any
                                   # single capability's status
    capability: HostCapability | None  # None when available is False
    probed_at: str                     # ISO 8601
    evidence_path: str | None          # path under docs/dev/tmp/autopilot/probes

UNAVAILABLE_NO_BINARY = "no_binary"
UNAVAILABLE_NO_AUTH = "no_auth"

def probe_host(host_id: str, *, project_root: Path) -> ProbeResult: ...
```

`CapabilityStatus.status` is exactly the two cases § `contracts/hosts.json`
below distinguishes: `"unavailable"` is a fact about today's environment
(no binary, no auth — `reason` names which); `"unimplemented"` is a
build-time defect (the adapter has no code path for that capability name at
all — the case `build-compatibility.py` treats as a build failure, never a
per-environment fact). `probe_host` always returns a `CapabilityStatus` for
every name in `CAPABILITY_NAMES` the adapter *could* check; an adapter that
has genuinely never implemented a check for one of them returns
`"unimplemented"` rather than omitting the entry, so `build-compatibility.py`
never has to infer unimplemented-vs-silently-absent from a missing key.

`probe_host` dispatches to `claude.probe()` / `codex.probe()` / `gemini.probe()`
by `host_id` — a plain dict lookup, no plugin discovery, no dynamic import.
Unknown `host_id` raises `ValueError("unknown host_id: ...")`; this is a
programming error (the caller always passes a literal), not a runtime
refusal, so it is not encoded as an `UNAVAILABLE_*` reason.

### Per-host adapter module (`claude.py`, `codex.py`, `gemini.py`)

Each exports the identical four-function surface so `hosts.py` and `jobs.py`
never branch on which module they hold:

```python
def probe(*, project_root: Path) -> ProbeResult:
    """STATIC checks only — binary-on-PATH, auth-file/env-var present,
    version string parses — never a live dispatch, never a real
    `codex exec`/Agent-tool round-trip. Probing a capability and
    EXECUTING it are different operations by design: `probe()` answers
    "would this work", `can_delegate()`/`build_job_argv()` are what a
    caller invokes to actually use a capability, and this PRD's own
    rule that its Python code never executes delegation (§ Architecture
    fit) applies to `probe()` too — a probe that actually ran a dispatch
    would violate that rule on every `doctor.py`/`build-compatibility.py`
    invocation, which is why it does not."""
def session_identity() -> dict | None:
    """Native session id + process identity for the CURRENT session, or
    None when this host exposes none (e.g. running outside that host)."""
def can_delegate() -> bool:
    """True iff this host supports a TRUE in-session subagent dispatch
    primitive: no new OS process, no provider-CLI invocation anywhere in
    the chain. Claude: True (the Agent tool). Codex: False (`codex exec`
    spawns a new process, which is cross-session by this design's own
    definition — see § Architecture fit). Gemini: False (no primitive of
    either kind) until OV 00059 lands a conforming driver — recorded
    honestly, never assumed. A host returning False here is not
    "unavailable" for review work; it simply routes that work through
    `jobs.request_cross_session_job` instead of in-session dispatch."""
def build_job_argv(intent: "JobIntent") -> list[str] | None:
    """The argv this host's native CLI would need to RUN a job matching
    `intent`, for the standalone next-session instruction. Returns None
    when `intent.role` has no native entry point on this host (the
    caller reports that role as unsupported-on-host, it does not guess
    a substitute)."""
```

No adapter module ever calls `subprocess.run`/`Popen` on another provider's
CLI. `build_job_argv` only *constructs* the argv string for the human (or the
real OVCAQ client in managed mode) to launch — this is the line the PRD draws
("never spawn headless provider CLI children inside plugin scripts").

**Claude-free profile.** `claude.py` exists for completeness and for the
"mixed Claude scenario kept as compatibility coverage" the source design
names, but the profile this PRD must certify is Codex-builds /
Gemini-doubts: every mandatory role in AP 00012's policy
(`contracts/review-policy-v1.json`) must resolve to a `request_cross_session_job`
call naming `codex` or `gemini` as `host` — never `claude` — with no silent
substitution. Since neither `codex.can_delegate()` nor `gemini.can_delegate()`
is `True` (§ per-host adapter module above), this profile runs entirely
through the cross-session job path, never in-session delegation; that is
expected, not a degraded mode — in-session delegation was never this
profile's mechanism. A role whose `build_job_argv` returns `None` on the
required host (§ Risks & edge cases, "a role with no entry point") is this
profile's actual unsupported-capability signal, distinct from a `GuardOutcome`
(§ `guards.py` below settles that naming once).

### `jobs.py`

```python
@dataclass(frozen=True)
class JobIntent:
    job_id: str                 # matches review-policy job_id ("alice", "bob", "carl", ...);
                                 # a job_id outside that file's current persona
                                 # set is a new reviewer/role being added to
                                 # policy, not a provider-named ad hoc value
    role: str                   # neutral role name, never a provider/model name
    inputs: dict                # artifact references + digests, not raw content
    isolation: str               # "fresh-context" | "fresh-session"
    tier: str                    # "haiku" | "sonnet" | "opus" | "fable"
    effort: str                  # characterized only; CLI forwarding is OV 00059
    policy_constraints: dict     # e.g. blindness, allowed-input identities

class ControllerSeam(Protocol):
    def submit_job(self, intent: JobIntent) -> dict: ...   # -> {"accepted": bool, "job_ref": str | None}
    def evaluate_guard(self, duty: "GuardDuty", context: dict) -> dict: ...
        # -> {"allowed": bool, "reason": str | None} — the authoritative
        # answer for a STATEFUL guard duty (custody, state integrity, live
        # job, review completeness). guards.py never re-implements this
        # logic locally; it only shapes `context` and relays the seam's
        # verdict into a GuardOutcome (§ guards.py below).

class FakeSeam:
    """Records submitted intents (`submit_job`) and answers
    `evaluate_guard` from caller-supplied fixture rules (a dict of
    `{duty: (allowed, reason)}` passed to its constructor) — it never
    launches anything and never implements real custody/state/review
    policy. The only seam implementation this PRD ships. A real seam
    (backed by the actual controller, once AP 00018-00021 exist) is
    AP 00016's job; it must implement both methods identically."""

def build_job_intent(*, job_id: str, role: str, inputs: dict,
                      isolation: str, tier: str, effort: str,
                      policy_constraints: dict) -> JobIntent: ...

def request_cross_session_job(intent: JobIntent, *, seam: ControllerSeam | None,
                                host: ModuleType, ancestry: list[dict]) -> dict:
    """Calls recursive_child_denied(intent, host=host, ancestry=ancestry)
       first and raises RecursionError if it returns True.
       seam is None  -> standalone mode: returns
         {"mode": "standalone",
          "instruction": {"argv", "intent": asdict(intent)}}
       where argv = host.build_job_argv(intent) (None if unsupported) and
       `intent` is the COMPLETE validated JobIntent — job_id, role, inputs,
       isolation, tier, effort, policy_constraints — carried verbatim so the
       human (or a future standalone-aware launcher) can see and honor every
       constraint the intent declared, not just the ones that fit into argv.
       A host whose `build_job_argv` cannot express `isolation` or
       `policy_constraints` as CLI flags (e.g. no blindness flag exists)
       MUST still return the full `intent` dict with those fields intact;
       it is the human operator's responsibility to honor them manually,
       and this function never silently drops them to produce a
       cleaner-looking argv.
       seam given -> controller-bound mode: returns
         {"mode": "controller", **seam.submit_job(intent)}.
    Never starts a process either way."""

def recursive_child_denied(intent: JobIntent, *, host: ModuleType,
                             ancestry: list[dict]) -> bool:
    """True when `ancestry` (the chain of {host_id, job_id} records this
    process inherited from its own launch — read from an environment
    variable or marker file the launching session set, never from `ps`
    or a live process-tree walk) already contains an entry whose
    `host_id == host.HOST_ID` AND `job_id == intent.job_id` — i.e. THIS
    intent is trying to re-launch the job that is already running it.
    `request_cross_session_job` calls this UNCONDITIONALLY as its first
    step (not an optional caller step) and raises `RecursionError` when
    it returns True, before building any argv or calling `seam`; a test
    drives it by passing a synthetic `ancestry` list, no real process
    tree required."""
```

`request_cross_session_job` never shells out — it only builds the instruction
or forwards to the fake seam. This is the one function `test_jobs.py`'s
`no_nested_driver_cli` scenario asserts never touches `subprocess`, and its
first line is always the `recursive_child_denied` check above — a caller
cannot reach argv-building or `seam.submit_job` without passing it.

### `guards.py`

```python
class GuardDuty(StrEnum):
    DOCUMENT_LOCATION = "document_location"
    CUSTODY_PUSH = "custody_push"
    DELEGATION = "delegation"
    POST_HANDOFF = "post_handoff"
    DEPARTURE = "departure"
    CONTEXT_REINJECTION = "context_reinjection"
    STATE_INTEGRITY = "state_integrity"
    REVIEW_COMPLETENESS = "review_completeness"
    LIVE_JOB = "live_job"

@dataclass(frozen=True)
class GuardOutcome:
    duty: GuardDuty
    allowed: bool
    reason: str | None       # set when allowed is False
    stateful: bool           # True -> this call hit `seam`; False -> pure/artifact-only

def run_guard(duty: GuardDuty, context: dict, *,
               seam: ControllerSeam | None) -> GuardOutcome: ...
```

`run_guard` dispatches to nine `_guard_<duty>` functions. Each is classified
**stateful** (calls `seam.evaluate_guard(duty, context)` and relays its
`{allowed, reason}` verbatim into `GuardOutcome` — `CUSTODY_PUSH`,
`STATE_INTEGRITY`, `LIVE_JOB`, `REVIEW_COMPLETENESS`) or **pure/artifact-only**
(`DOCUMENT_LOCATION`, `DELEGATION`, `POST_HANDOFF`, `DEPARTURE`,
`CONTEXT_REINJECTION` — these check local artifacts/markers only and decide
`allowed` themselves, matching the source hooks' own split between
state-mutating guards and read-only checks). A pure guard never receives
`seam` at all (its function signature has no `seam` parameter), so a caller
cannot accidentally make it stateful. A stateful `_guard_<duty>` function is
a thin wrapper — build `context`, call `seam.evaluate_guard`, wrap the result
— it holds no custody/state/review policy of its own; that policy lives in
whatever implements `ControllerSeam` (`FakeSeam`'s fixture rules here, the
real controller client at AP 00016).

**`missing_guard_refused` (the PRD's name) is the single outcome this module
produces for every refusal; `reason` is the one field that distinguishes the
cause** — there is no second, separately-named refusal path:

- A stateful duty called with `seam=None` →
  `GuardOutcome(allowed=False, reason="missing_controller_seam", stateful=True)`.
- A host-capability gap (e.g. a mandatory role resolving to Gemini with
  `can_delegate() is False`) is caught by `jobs.py`/`hosts.py` before it ever
  reaches a guard, and surfaces as `missing_capability` on the `ProbeResult`/
  `JobIntent` path, not as a `GuardOutcome` — guards and host-capability checks
  are two different refusal sites, and `missing_guard_refused` names only the
  guard one. The PRD's `missing_guard_refused` acceptance scenario (Phase 2
  task 1) and this design's `missing_controller_seam_refused` test case
  (`test_guards.py`, § Test strategy outline) are the same code path under one
  name; the latter is this design doc's more specific internal label for the
  one `reason` value a stateful guard ever produces today. A later duty could
  add a second stateful-refusal `reason` string without changing
  `GuardOutcome`'s shape.

### `doctor.py`

```python
@dataclass(frozen=True)
class DoctorReport:
    hosts: list[ProbeResult]
    guards: list[GuardOutcome]       # one per duty, evaluated with a
                                      # FakeSeam whose fixture always
                                      # returns allowed=True — this proves
                                      # only that the LIBRARY CALL succeeds
                                      # end-to-end, never that a real
                                      # controller is reachable
    guards_simulated: bool           # always True until AP 00016 ships a
                                      # real ControllerSeam; doctor.py has
                                      # no way to probe real controller
                                      # reachability, so it never claims to
    profile: str                     # "claude-free" | "mixed" — derived, not asserted
    generated_at: str

def diagnose(*, project_root: Path) -> DoctorReport: ...
```

`doctor.py` has **no CLI of its own** — it is a pure library module, same as
`hosts.py`/`guards.py`. `autopilot.py` gets a third new mode, `--diagnose`
(`_CAPABILITIES` entry `"diagnose-v1"`, `_MODES` entry `"diagnose"`,
dispatching via `_helper("doctor").diagnose(...)`), so the invocation is
`python3 scripts/autopilot.py --diagnose --project-root PATH`, printing
`asdict(diagnose(...))` as JSON — consistent with every other mode's shape
and with § Module placement's "no second CLI entry point" rule. No flag
writes anything outside `docs/dev/tmp/autopilot/`.

### `contracts/hosts.json`

```json
{
  "schema_version": 1,
  "hosts": {
    "claude": {"capabilities": ["identity", "delegation", "isolation", "interception"]},
    "codex":  {"capabilities": ["identity", "delegation", "isolation"]},
    "gemini": {"capabilities": ["identity"]}
  }
}
```

`build-compatibility.py` reads this (the declared/advertised surface) and
cross-checks it, per capability name, against the matching
`CapabilityStatus` in the adapter's fresh `probe()` result:

- `status == "available"` → included in the written `compatibility/<host>.json`.
- `status == "unavailable"` (no binary, no auth — e.g. Gemini has no CI
  credential in this environment) → excluded from the written bundle
  silently; this is the normal, expected shape of a bundle generated on a
  host that is not fully provisioned, and it is exactly what
  `test_compatibility.py`'s round-trip case checks ("generated bundle
  matches the contract minus any capability the live probe reported
  unavailable").
- `status == "unimplemented"` (the adapter has no check for a capability
  name `contracts/hosts.json` declares — a build-time/contract mismatch,
  not a runtime-environment fact) → `build-compatibility.py` exits
  non-zero. This is the "build failure, not a warning" case: a capability
  no adapter can ever evidence is a defect in `contracts/hosts.json` or the
  adapter, not a fact about today's environment.

`build-compatibility.py` never needs to guess which case it is in — `status`
is an explicit three-way enum per capability, not an inferred distinction
over exceptions or a bare boolean.

## Data flow

1. `doctor.py` / `probe-host.py` call `hosts.probe_host(host_id)` →
   dispatches to the adapter's `probe()` → adapter runs static, read-only
   checks only (binary on PATH, auth file/env var present, version string
   parses — never a live dispatch; § `probe()`'s docstring above) → returns
   a `ProbeResult` with one `CapabilityStatus` per `CAPABILITY_NAMES` entry.
   Any evidence written under `docs/dev/tmp/autopilot/probes/` is the static
   check's inputs/outputs (e.g. the binary path found, the version string
   read), never a dispatch transcript — nothing this PRD's code runs ever
   executes a real in-session or cross-session job.
2. `build-compatibility.py` reads `contracts/hosts.json` + fresh `ProbeResult`s
   → writes `compatibility/<host>.json` (the frozen, shippable capability
   bundle other skills/doctor read without re-probing).
3. A job request: caller builds a `JobIntent` (`jobs.build_job_intent`) →
   `jobs.request_cross_session_job(intent, seam=None_or_FakeSeam, host=<module>)`
   → standalone: adapter's `build_job_argv` produces the next-session
   instruction string; controller-bound: `FakeSeam.submit_job` records the
   intent and returns an acceptance stub. No process is spawned either path.
4. A guard check: caller (a skill, at the point the source hooks fired) calls
   `guards.run_guard(duty, context, seam=...)` → pure duties check local
   artifacts (e.g. `DOCUMENT_LOCATION` checks a path against the PRD-location
   keeper list, mirroring `enforce_prd_location.py`'s rule, re-implemented
   here rather than imported — that script lives in the installed consumer
   plugin, a separate distribution this repo does not import); stateful
   duties call `seam.evaluate_guard` and refuse outright when `seam is None`.
   **This PRD ships the guard *library* only — `run_guard` is a callable a
   skill's own prompt invokes explicitly.** This matches the PRD's own Phase
   2 acceptance criterion verbatim: `missing_guard_refused` must "report
   denied mandatory capabilities" — report, not retrofit a new enforcement
   mechanism — and the PRD's Overview explicitly excludes "live installation"
   from this PRD's scope. Native, un-bypassable interception (a Claude
   `PreToolUse` hook registration, a Codex equivalent, or an explicit refusal
   on a host whose `interception` capability status is not `"available"`) is AP 00015
   (workflow parity, adapting the preserved `SKILL.md` prose to call these
   functions) and AP 00016 (standalone, native hook registration) — the PRD's
   own Delivery graph orders AP 00014 before both. What IS mandatory here,
   and what `missing_guard_refused`/`missing_controller_seam_refused` certify:
   every `_guard_<duty>` function, when called, decides correctly and never
   silently passes when it should refuse (`seam=None` → refuse, not allow).
   `statuses["interception"].status != "available"` is itself the honest "report denied
   mandatory capabilities" signal the PRD asks for on a host with no native
   hook surface — it is not a gap this PRD leaves silently unaddressed, it is
   the exact shape of evidence Phase 2 asks this PRD to produce. A reviewer
   should read a green `missing_guard_refused` test as "the library decides
   correctly when invoked" and read a host's `interception` capability status as "whether
   invocation can be made unbypassable" — two different, both honestly
   reported, facts.

No new persistent state. `FakeSeam` holds its recorded intents in memory for
the test process only; nothing here writes `state.json` or any controller
file — that remains AP 00018's exclusive write surface.

## Reuse inventory

- `scripts/dirty_tree.py:_git` (`subprocess.CompletedProcess` wrapper around a
  scoped `git` invocation) — reuse directly for any git-derived identity/probe
  check an adapter needs (e.g. confirming a clean isolated probe root); do not
  write a second git-subprocess wrapper.
- `scripts/log_sink_refusal.py` (`_pinned_parent_fd`, `_descend`,
  `_root_anchor`) — the root-anchored, symlink-safe descent pattern this repo
  already uses to open a log sink safely. `probe-host.py` reuses the same
  pattern when creating `docs/dev/tmp/autopilot/probes/` so a probe write
  cannot be redirected outside that root by a planted symlink.
- `scripts/review_stage.py:_write` / `_read` (atomic-ish write-then-read
  helpers with explicit encoding) — reuse for `compatibility/<host>.json` and
  probe-evidence writes instead of a third ad hoc `Path.write_text`.
- `scripts/review_stage.py:_precheck` / `_manifest` (declared-vs-actual
  capability cross-check shape) — the closest existing precedent for
  `build-compatibility.py`'s "claimed capability needs probe evidence" check;
  same shape, new domain.
- `controller/autopilot_state/actors.py:PrivateLayout`,
  `credential_descriptor`, `authenticate` — **not reused**. These implement
  the *controller's* operator-credential admission (directory/file mode
  0700/0600, bound to the controller's own private state root) for AP 00018's
  owner-lease protocol. AP 00014's `ControllerSeam`/`FakeSeam` is a plugin-side
  stub that never holds a real credential; importing `actors.py` here would
  cross the "no sibling-checkout imports" boundary the source design draws
  between the plugin and the controller. Noted so a future reviewer does not
  flag the non-reuse as a miss.
- Greps tried for an existing host/provider-probe abstraction before
  concluding none exists: `rg -i "probe_host|host_capab|session_identity|can_delegate|job_intent" plugins/ tools/` —
  no hits outside this PRD's own new-symbol list; `rg -l "subprocess" plugins/autopilot/scripts/`
  (cap_check.py, verification.py, review_stage.py, catchup.py, dirty_tree.py) —
  all task-specific git/process wrappers already covered above, no generic
  "run another CLI" helper exists to reuse or avoid duplicating.

## Alternatives considered

1. **One `hosts.py` god-module** holding all three providers' logic in one
   file with `if host_id == "claude": ...` branches, instead of
   `claude.py`/`codex.py`/`gemini.py`. Smallest-diff option. Rejected: the PRD's
   own Structural Decomposition names the three per-host files explicitly, and
   a single branching module is exactly the "provider-named modules" boundary
   the PRD asks to avoid collapsing — adding a fourth host later would mean
   editing a shared file instead of adding one, and `can_delegate()`
   honestly differing per host (Gemini: False today) reads better as separate
   small modules than as a branch table.
2. **Real controller seam now** (build an HTTP/socket/subprocess client against
   `controller/main.py`) instead of `FakeSeam`. Rejected: `controller/main.py`
   is still a two-function stub (confirmed by reading it) and the source
   design assigns the real seam to AP 00016 ("00016 after 00015 + 00020 +
   00021"); building a real client against an unfinished protocol now would
   need rework at 00016 regardless, and the PRD's own Phase 0 note says
   "expose a controller-binding seam tested with fakes until 00016."
3. **Chosen: three thin per-host adapter modules + one `FakeSeam`**, as
   specified above. Costs more files than option 1, but keeps each host's
   honestly-different capability set (especially Gemini's current
   `can_delegate() == False`) visible at the module boundary instead of
   buried in a conditional, and the `ControllerSeam` Protocol means AP 00016
   swaps `FakeSeam` for a real client with no call-site change.

## Risks & edge cases

- **This PRD ships callable guards, not installed interception.** `missing_guard_refused`
  proves a called `run_guard` refuses correctly; native un-bypassable
  registration of each duty into a host's own hook surface is AP 00015/00016's
  scope (§ Data flow point 4). A reviewer must not read this PRD's green
  tests as "an operation cannot skip a guard" — only as "a guard, when
  invoked, decides correctly."
- **Neither Codex nor Gemini has an in-session delegation primitive today.**
  `can_delegate()` returning `False` for both is a real, expected finding,
  not a bug — recording it honestly (rather than forcing a review role onto
  a host that cannot execute it in-session) is what `codex_gemini_role_capabilities`
  exists to prove. This is distinct from `missing_guard_refused`, which names
  only a `GuardOutcome` refusal (§ `guards.py`); a capability gap here surfaces
  as `build_job_argv` returning `None` (the next bullet), never as a
  `GuardOutcome`. OV 00059 is tracked as the PRD that may change Gemini's
  cross-session execution story; it does not bear on in-session delegation,
  which stays Claude-only by the chain-of-processes definition above.
- **A role with no entry point on the selected host.** `build_job_argv`
  returning `None` must propagate as an explicit "role unsupported on this
  host" result, never a guessed substitute host or a silently-skipped role —
  this is the same discipline as the Gemini delegation case above, applied to
  argv construction instead of capability probing.
- **Next 2-3 likely follow-on changes**, and what this design keeps open for
  them:
  1. AP 00015 (workflow parity) will adapt the preserved `SKILL.md` prose to
     call these new adapters/guards instead of the source hooks it currently
     narrates — `guards.py`'s duty names are chosen to match the PRD's nine
     duty names 1:1 so that mapping is a rename, not a redesign.
  2. AP 00016 (standalone) swaps `FakeSeam` for a real controller client —
     the `ControllerSeam` Protocol is the only seam `jobs.py`/`guards.py`
     touch, so that swap is a constructor-argument change at call sites, not
     a signature change.
  3. OV 00059 (managed Gemini driver) is a cross-session capability change,
     not an in-session one — it may make `gemini`'s `request_cross_session_job`
     path reach more roles, but `gemini.can_delegate()` stays `False` under
     this design's chain-of-processes definition regardless; nothing in
     `jobs.py` assumes a host's capability set is fixed at import time,
     `hosts.probe_host` always re-probes rather than reading a cached
     constant, so any such flip needs no code change here, only a fresh
     probe.
- This design does not implement the controller, does not publish or install
  anything, and does not retire any source hook — all explicitly out of scope
  per the PRD's Overview line.

## Test strategy outline

One test file per new module, covering exactly the PRD's named scenarios:

- `test_host_argv.py`: `relocated_host_probe` (probe writes only under
  `docs/dev/tmp/autopilot/`, never `~/.claude` or installed config — assert by
  pointing `project_root` at a temp dir and checking no path outside it is
  touched), `missing_guard_refused`-adjacent argv cases (`build_job_argv`
  returns `None` for an unsupported role).
- `test_sessions.py`: `shared_core_without_claude` (run the full `hosts.py` /
  `jobs.py` surface with `claude.py` import removed from the call graph —
  i.e. drive everything through `codex`/`gemini` only — and assert no code
  path requires `claude`), `codex_gemini_role_capabilities` (each mandatory
  review-policy role resolves to codex or gemini, never silently to claude).
- `test_jobs.py`: `recursive_child_denied` (a synthetic `ancestry` entry
  matching the requested intent's `host_id`/`job_id` raises `RecursionError`
  from `request_cross_session_job` before any argv is built or `seam` is
  called; a distinct `job_id` in `ancestry` does not), `no_nested_driver_cli`
  (assert `request_cross_session_job` and every adapter's `build_job_argv`
  never call `subprocess`/`os.exec*` — patch them to raise if called).
  `reviewer_isolation` is explicitly scoped to **record independence only**
  (two intents for different `job_id`s produce independent `FakeSeam`
  records with no shared mutable state) — it does NOT, and is not claimed to,
  prove fresh execution contexts or blindness enforcement; that evidence
  does not exist until a host actually executes a delegated job, which is
  outside this PRD (§ Risks & edge cases notes this explicitly).
- `test_guards.py`: `custody_push_denied` (a `CUSTODY_PUSH` guard call with a
  `FakeSeam` constructed with a fixture rule `{CUSTODY_PUSH: (False,
  "pending_critical")}` returns `allowed=False`, relayed verbatim from
  `seam.evaluate_guard`), `missing_controller_seam_refused` (any stateful
  duty called with `seam=None` refuses without calling anything), one case
  per remaining duty exercising its pure/artifact-only path.
- `test_compatibility.py`: `build-compatibility.py` round-trip (generated
  `compatibility/<host>.json` matches `contracts/hosts.json` minus any
  capability the live probe could not evidence), `no_coordinator_runtime_in_plugin`
  (static scan of `scripts/*.py` added by this PRD for `while True`, a
  scheduler loop, or a bound TUI import — none of this PRD's modules may
  contain one).

`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`
must pass for every new test above; the PRD's Phase 2 exit criteria already
require this plus `python3 scripts/validate.py`. The pre-existing AP00018
controller-suite failures (`test_controller_capacity.py`,
`test_controller_owner.py`, `test_controller_owner_recovery.py`, 19 cases) and
the two provenance/package drift failures newly observed on master this
session (`test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes`,
`test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes`
and `test_generator_check_accepts_the_committed_map`) are **pre-existing and
out of this PRD's scope** — none of this PRD's new files are among the
drifted ones (`log_sink_refusal.py` is already present and owned by AP 00013;
the drift is in its *existing* digest, not a change this PRD makes). This PRD
must not mask, relabel, or incidentally fix them; it must also not add new
failures to that count. The next session's full-suite run should confirm the
same known-red set, not a larger one, before Phase 2 closes.

## Review log

- Blocker: "no edits to existing files" contradicted the PRD's own file list (`autopilot.py`, `CHANGELOG.md` already exist and are named as this work's symbols) and left `doctor.py` with an unjustified standalone CLI diverging from the repo's one-entry-point convention. Fixed (§ Module placement, § Architecture fit now scope and justify the two edited files; `doctor.py`/`tools/` scripts route through `autopilot.py`'s new modes or stay maintainer-only, no new CLI entry point).
- Non-blocking: `JobIntent.job_id` example used a provider-named value not present in `review-policy-v1.json`. Fixed (corrected example + clarifying comment).
- Question: relationship between `missing_guard_refused` and `missing_controller_seam_refused` was unstated. Recorded resolution inline (§ Interfaces & contracts, `guards.py`): same code path, one `reason` value; host-capability gaps are a separate, earlier refusal site in `jobs.py`/`hosts.py`.
dispatch 1 (claude): cardinal-sin 0, blocker 1, non-blocker 1, question 1
- Blocker: `ControllerSeam`/`FakeSeam` had no method a stateful guard could call to get a real allowed/denied verdict (only `submit_job` existed). Fixed: added `evaluate_guard(duty, context) -> {allowed, reason}`; stateful `_guard_<duty>` functions are now thin relays onto it; `FakeSeam` takes caller-supplied fixture rules.
- Blocker: in-session delegation's actual execution path (who calls it, on which host) was unstated, reading as a contradiction with the never-spawn-headless-CLI rule. Fixed (§ Architecture fit): clarified the calling skill's own prompt invokes the host-native primitive directly (Claude's `Agent` tool, Codex's own `codex exec` sub-session tool); this PRD's Python code never executes delegation, only reports `can_delegate()`.
- Blocker: the standalone-mode job-request response dropped `job_id`/isolation/tier/effort/policy_constraints, keeping only role/argv/inputs. Fixed (§ `jobs.py`): the standalone instruction now always carries the complete `JobIntent` verbatim alongside argv, never only the fields that happened to fit into a CLI flag.
- Blocker: guard functions had no stated path into a host's actual, un-bypassable interception point, so passing tests here could be misread as "nothing can skip a guard." Fixed (§ Data flow point 4, § Risks & edge cases): explicitly scoped — this PRD ships the callable guard library only; native hook/interception wiring is AP 00015/00016.
- Blocker: `recursive_child_denied(host)` had no intent/job-id/ancestry input, so it could not evaluate the condition it claims to check, and was an optional caller step. Fixed (§ `jobs.py`): takes `intent` and `ancestry` explicitly, and `request_cross_session_job` calls it unconditionally as its first step, raising `RecursionError` rather than leaving enforcement optional.
- Blocker: `build-compatibility.py`'s "unavailable capability is a build failure" contradicted the round-trip test's "generated bundle excludes unavailable capabilities." Fixed (§ `contracts/hosts.json`): split into two distinct cases with different exceptions — a probed-unavailable capability (no binary/auth) is silently excluded (the round-trip test's case); a capability no adapter even has code to probe is the actual build failure.
- Non-blocking: `reviewer_isolation` only proved record independence, not execution-boundary/blindness isolation. Recorded the narrower scope explicitly in § Test strategy outline rather than fixing (no execution-boundary evidence exists until a host actually executes a delegated job, which is out of this PRD's scope).
- Non-blocking: `DoctorReport.guards` evaluated against a simulated `FakeSeam` could be misread as proof of real controller reachability. Fixed: added `guards_simulated: bool` (always `True` until AP 00016), and the field comment states what the simulated check does and does not prove.
- Question: `doctor.py`'s CLI line (`python3 scripts/doctor.py --json`) contradicted Module placement's "no second CLI entry point" rule. Fixed: `doctor.py` is now a pure library module with no CLI of its own; `autopilot.py` gains a third mode, `--diagnose`.
dispatch 2 (codex): cardinal-sin 0, blocker 6, non-blocker 2, question 1
- Blocker (verification found dispatch-2's fix incomplete): calling Codex delegation a "`codex exec` sub-session the skill issues" still conflated an in-session primitive with a CLI process spawn, keeping the contradiction with the cross-session-only rule for provider CLI children. Fixed (§ Architecture fit, § per-host adapter module): redefined in-session delegation as "no new OS process, no provider-CLI invocation anywhere in the chain" — only Claude's `Agent` tool qualifies; `codex.can_delegate()` now returns `False` (codex exec is a process spawn, i.e. cross-session by this design's own definition), matching Gemini. Propagated to § `jobs.py`'s Claude-free profile paragraph and § Risks & edge cases.
- Blocker (verification found dispatch-2's fix insufficient): deferring native interception wiring to AP 00015/00016 was read as leaving the enforcement gap open rather than closing it. Fixed (§ Data flow point 4): grounded the scope boundary in the PRD's own Phase 2 acceptance text verbatim ("report denied mandatory capabilities", not install hooks) and the PRD Overview's explicit "no live installation" exclusion, so the boundary is the PRD's own scope, not an unaddressed gap this design introduced.
- Blocker: `probe()` took no capability name and `ProbeResult.capability` had no per-field reason, so the unavailable-vs-unimplemented distinction from the earlier fix had no representable interface. Fixed (§ `hosts.py`): replaced the single `HostCapability` bool set with `CapabilityStatus` (name, status ∈ {available, unavailable, unimplemented}, reason) keyed by `CAPABILITY_NAMES`; `build-compatibility.py`'s two-case logic now dispatches on an explicit per-capability `status` field instead of an exception/boolean distinction.
- Blocker (new, exposed by the dispatch-2 fix): Data flow point 1 described `probe()` performing "a throwaway isolated-context dispatch," which is itself an execution this design's own Architecture-fit rule forbids. Fixed: `probe()` is now explicitly static/read-only only (binary-on-PATH, auth-file/env-var presence, version-string parse) — it never dispatches anything, live or throwaway.
- Non-blocking: the Claude-free profile paragraph and the Gemini-delegation Risks bullet both still named `missing_guard_refused` for a host-capability gap, contradicting `guards.py`'s own "capability gaps never reach guards" rule. Fixed: both now point at `build_job_argv` returning `None` / `codex_gemini_role_capabilities` instead, reserving `missing_guard_refused`/`missing_controller_seam_refused` for actual `GuardOutcome` refusals.
- Question: Module placement still listed the obsolete `python3 scripts/doctor.py --json` invocation after `doctor.py`'s CLI was removed. Fixed: Module placement's `doctor.py` bullet now points at `autopilot.py --diagnose` with no CLI line of its own.
dispatch 3 (codex): cardinal-sin 0, blocker 4, non-blocker 1, question 1
result: ok
