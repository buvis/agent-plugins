# AP00014 rework design, cycle 1

Source review: docs/dev/project-management/reviews/00014-autopilot-host-execution-v1-review-1.md (head_sha 68418c5a3c8951abfbac494ddc9cdae0d6408a06)

## Architecture fit

Prior fix: none - there was no prior rework fix.

Cycle 1 of AP00014's review raised nine 🔴 CRITICAL rows. They fall into two
independent clusters.

**Cluster A - the PRD's own work left five tests failing** (R4, R5, R6, R7, R8).
Alice re-ran `tests/autopilot/test_package.py`,
`tests/autopilot/test_helper_provenance_real.py` and
`tests/autopilot/test_local_boundary.py` in a worktree at the PRD base commit
`635e3764` (47 passed, 1 skipped) and at `68418c5a` (5 failed). The build session
and task 10 recorded those five as pre-existing. They are not: they are this
PRD's own regressions, and the PRD's Phase 2 exit criteria name
`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`
as a gate. This cluster lands entirely in existing test files and in the
committed `tools/autopilot/source-map.json`; no production module changes for it.

**Cluster B - capability claims are not backed by capability** (R1, R9, R10, R11).
The adapters live at `plugins/autopilot/scripts/{hosts,claude,codex,gemini}.py`,
their declaration at `plugins/autopilot/contracts/hosts.json`, their generated
bundles at `plugins/autopilot/compatibility/*.json`, and the generator at
`tools/autopilot/build-compatibility.py`. The PRD's success metric is "No
unsupported capability is advertised"; its Phase 0 line is "only successful real
probes enable host execution claims". Today a probe reports `identity`,
`delegation` and `isolation` as `available` for codex on nothing but a binary on
`PATH` plus `~/.codex/auth.json`, while `codex.session_identity()` returns `None`
and `codex.can_delegate()` returns `False` in the same module.

**The root cause of cluster B is that one artifact mixes two different kinds of
fact.** "Codex implements in-session delegation" is a property of the code and is
the same on every machine. "Codex is authenticated here" is a property of the
machine. The committed `compatibility/*.json` is currently derived from both, so
its bytes change with the builder's `~/.codex/auth.json`. Cluster B is fixed by
separating them: each adapter declares `IMPLEMENTED_CAPABILITIES` as a code fact,
the declaration and the committed bundle are derived from that alone, and auth
presence survives only in per-run probe evidence, which is never committed.

Both clusters stay in the layers AP00014 already owns. Nothing here adds a
process launch, a supervisor, a scheduler or a controller runtime: the PRD's
Risks section forbids all four and `no_coordinator_runtime_in_plugin`
(`test_compatibility.py:216-256`) tests for it.

## Module placement

Edits to existing files only. No new module, no new package file.

| File | Change | Closes |
|---|---|---|
| `plugins/autopilot/scripts/hosts.py` | `unavailable()` constructor; `unavailable_reason`, `probe_kind`, `authenticated`, `certified` fields; `__post_init__` invariant; `statuses_from()` emitting `supported`, never `available` | R1, R10 |
| `plugins/autopilot/scripts/claude.py` | `IMPLEMENTED_CAPABILITIES`; probe rebuilt on `statuses_from()` | R10 |
| `plugins/autopilot/scripts/codex.py` | `IMPLEMENTED_CAPABILITIES = frozenset({"isolation"})`; probe rebuilt | R10 |
| `plugins/autopilot/scripts/gemini.py` | `IMPLEMENTED_CAPABILITIES = frozenset()`; module docstring; probe rebuilt, invariant obeyed | R1, R10 |
| `plugins/autopilot/contracts/hosts.json` | Declaration reduced to each adapter's `IMPLEMENTED_CAPABILITIES` | R10, R11 |
| `tools/autopilot/build-compatibility.py` | Bundle derived from declaration ∩ implemented, never from auth; unavailable host still gets a bundle | R11 |
| `plugins/autopilot/compatibility/{claude,codex,gemini}.json` | Regenerated; bytes are now machine-independent | R11 |
| `plugins/autopilot/CHANGELOG.md` | Capability sentence restated to match the declaration | R11 |
| `tools/autopilot/probe-host.py` | Evidence names its own path and the resolved binary; `O_EXCL`; auth state recorded here and only here | R9 |
| `tools/autopilot/update_helper_map.py` | New `AP00014_DIGESTED` tuple so the generator owns the 13 AP00014 digests | R7, R8 |
| `tools/autopilot/source-map.json` | Regenerated, as the last step of the rework | R7, R8 |
| `tests/autopilot/test_package.py` | `AP00014_OWNED` owner expectation; `--list-capabilities` expectation extended | R5, R6 |
| `tests/autopilot/test_local_boundary.py` | `OPERATIONS` extended with the three new operation ids | R6 |
| `tests/autopilot/test_helper_provenance_real.py` | New AP00014 row-integrity test beside the existing `AP00014_TARGETS` exclusion | R4, R8 |
| `tests/autopilot/test_sessions.py` | `GeminiCapabilityContractTest` and `CodexGeminiRoleCapabilitiesTest` re-specified; new declared-equals-implemented test; new `ProbeResult`-invariant test; hedged assertions replaced | R1, R10 |
| `tests/autopilot/test_compatibility.py` | `REAL_CONTRACT` and the inline contract updated; `_expected_available` replaced; scrubbed-env regeneration case | R11 |
| `tests/autopilot/test_host_argv.py` | Unavailable fakes pass `unavailable_reason`; probe-evidence case for `probe-host.py` | R1, R9 |

**R9 is closed IN PART, and the residue is recorded, not quietly dropped.**
R9 reads "Phase 2 task 1 (real headless probes) is not done ... nothing invokes
a host, proves identity, isolation or interception, or records unavailable
hosts." It has two halves and they have different owners:

- **The half this rework closes** is the last clause and the dishonesty around
  it: nothing recorded unavailability, nothing labelled the observation as
  static, the evidence file could not name itself, and the probe advertised
  capabilities the code did not implement. §10 and §2 close all of that.
- **The half this rework must NOT close** is "invokes a host". The PRD forbids
  it here twice - "never spawn headless provider CLI children inside plugin
  scripts", and "AP 00017 owns real certification, OV 00059 owns managed Gemini
  process launch" - so a subprocess launch added by this cycle would be a
  PRD violation, not a fix.

A static observation does not become a real probe by being labelled one, and
this design does not claim otherwise. Instead the residue is made **explicit and
machine-readable**: `ProbeResult.certified` is False and `__post_init__` refuses
any other value (§1), `probe_kind` is `"static"`, and §15(b)'s test name states
in words that the Claude-free profile is not certifiable. No consumer can read a
record from this package as host-execution certification. The open dependency on
AP 00017 is recorded in `## Risks & edge cases`, and R9 is also in
`state.deferred_decisions` as a CRITICAL raised this cycle, which is the batch-end
audit trail. A later session reading this doc must not treat R9 as fully
resolved.

## Interfaces & contracts

Every signature below is verbatim-ready. Name each symbol exactly as written.
Import lines are given where a snippet needs a symbol its file does not already
import. The call style for the new constructor is always `hosts.unavailable(...)`
in `tools/`-level code and bare `unavailable(...)` inside an adapter that imports
it by name; each snippet below shows the style for its own file.

### 1. `plugins/autopilot/scripts/hosts.py`

Closes: R1 - "The gemini probe returns available=False together with a non-None capability, contradicting the ProbeResult contract ("None when available is False"). Claude and codex return None in the same state, so build-compatibility.py skips them while writing a gemini bundle."
Closes: R10 - "Availability is claimed without proof, and the claim contradicts the adapter's own code."

```python
CAPABILITY_NAMES = ("identity", "delegation", "isolation", "interception")

UNAVAILABLE_NO_BINARY = "no_binary"
UNAVAILABLE_NO_AUTH = "no_auth"


@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    status: str
    reason: str | None


@dataclass(frozen=True)
class HostCapability:
    host_id: str
    statuses: dict[str, CapabilityStatus]


CAPABILITY_STATUSES = ("supported", "unavailable", "unimplemented")


@dataclass(frozen=True)
class ProbeResult:
    """`capability` is None exactly when `available` is False.

    `probe_kind` is always "static" in this package: every adapter probe is a
    binary-on-PATH plus auth-presence observation. A live invocation is AP 00017's
    certification work and OV 00059's managed launch, never this package's, so
    `certified` is always False here and no field of this record may be read as
    evidence that a host executed anything.

    `unavailable_reason` is non-None exactly when `available` is False.
    `authenticated` records auth presence for an available host (None when the
    host is unavailable, so auth was never checked).
    """

    host_id: str
    available: bool
    capability: HostCapability | None
    probed_at: str
    evidence_path: str | None
    probe_kind: str = "static"
    unavailable_reason: str | None = None
    authenticated: bool | None = None
    certified: bool = False

    def __post_init__(self) -> None:
        """Enforces EVERY invariant this record documents, so a defaulted
        construction site cannot serialise a contradictory state. A documented
        guarantee that construction can violate is not a guarantee."""
        if self.available:
            if self.capability is None or self.unavailable_reason is not None:
                raise ValueError(f"{self.host_id}: available result must carry a capability and no reason")
            if not isinstance(self.authenticated, bool):
                raise ValueError(f"{self.host_id}: available result must record auth presence")
        else:
            if self.capability is not None or self.unavailable_reason is None:
                raise ValueError(f"{self.host_id}: unavailable result must carry a reason and no capability")
            if self.authenticated is not None:
                raise ValueError(f"{self.host_id}: unavailable result never checked auth")
        if self.probe_kind != "static":
            raise ValueError(f"{self.host_id}: this package performs only static probes")
        if self.certified is not False:
            raise ValueError(f"{self.host_id}: this package never certifies a host")


def unavailable(host_id: str, *, probed_at: str, reason: str) -> ProbeResult:
    """The single construction site for an unavailable host: `capability` is
    always None and `reason` is always recorded, so no adapter can break the
    ProbeResult invariant or drop the no_binary/no_auth distinction."""
    return ProbeResult(
        host_id=host_id,
        available=False,
        capability=None,
        probed_at=probed_at,
        evidence_path=None,
        unavailable_reason=reason,
        authenticated=None,
    )


def statuses_from(
    implemented: frozenset[str], *, authenticated: bool
) -> dict[str, CapabilityStatus]:
    """Capability statuses for an available host, derived from the adapter's
    own `IMPLEMENTED_CAPABILITIES`.

    A name the adapter does not implement is "unimplemented" with reason None
    (the status already says why). A name it does implement is "supported" when
    the host is authenticated, else "unavailable" with reason `no_auth`. The
    returned mapping always has exactly `CAPABILITY_NAMES` as its keys, in that
    order.

    "supported" is deliberately NOT "available". This package performs only
    static probes, so the strongest honest claim is "this adapter implements
    this capability and the host is authenticated" - never "this capability was
    observed working". A reader wanting the latter needs AP 00017's
    certification, and `ProbeResult.certified` is False precisely to say so.
    """
    statuses: dict[str, CapabilityStatus] = {}
    for name in CAPABILITY_NAMES:
        if name not in implemented:
            statuses[name] = CapabilityStatus(
                name=name, status="unimplemented", reason=None
            )
        elif authenticated:
            statuses[name] = CapabilityStatus(name=name, status="supported", reason=None)
        else:
            statuses[name] = CapabilityStatus(
                name=name, status="unavailable", reason=UNAVAILABLE_NO_AUTH
            )
    return statuses
```

`probe_kind`, `unavailable_reason`, `authenticated` and `certified` are new
fields **with defaults**, so no construction site needs new arguments - but
`__post_init__` rejects a contradictory one, so two existing fixtures must be
updated: the unavailable fakes at `test_host_argv.py:73-80` must pass
`unavailable_reason=hosts.UNAVAILABLE_NO_BINARY`, and the available fake at
`:62-70` must pass `authenticated=True`. Add one direct test beside them
asserting each invalid construction raises `ValueError` - a validator with no
test for its own rejections is the next thing to rot.

**There is no `"available"` status value anywhere after this change.**
`CAPABILITY_STATUSES` exists so the three-value domain has one written home and
`statuses_from` can be checked against it; it is read by §15(c)'s test, so it is
not an unused constant.

One thing deliberately NOT added: there is no new reason constant for
"unimplemented". The status string already carries that fact and a reason
repeating it adds nothing (current code already uses `reason=None` there -
`codex.py:51-53`, `gemini.py:37-39`).

### 2. Per-adapter `IMPLEMENTED_CAPABILITIES` (the code fact)

Closes: R10 - "`codex.probe` reports identity, delegation and isolation "available" whenever a binary and an auth file exist. But `codex.session_identity()` always returns None (codex.py:64) and `codex.can_delegate()` always returns False (codex.py:68)."
Closes: R11 - "The shipped compatibility bundles and changelog advertise capabilities from the builder's environment, not from verified behavior."

Each adapter module gains one module-level constant, immediately after its
`HOST_ID`:

```python
IMPLEMENTED_CAPABILITIES: frozenset[str]
```

**The rule that decides its contents, stated once and applied to every adapter:
a capability name belongs in `IMPLEMENTED_CAPABILITIES` only when this module has
code that can make it true. A name whose backing function is unconditionally
inert does not belong, whatever the host could do in principle.**

| Adapter | `IMPLEMENTED_CAPABILITIES` | Why each exclusion |
|---|---|---|
| `claude.py` | `frozenset({"identity", "delegation", "isolation", "interception"})` | nothing excluded: `session_identity()` returns a record when `CLAUDE_SESSION_ID` is set, `can_delegate()` returns `True`, and `interception` is the documented client-native hook registration |
| `codex.py` | `frozenset({"isolation"})` | `identity` excluded - `session_identity()` is `return None` (codex.py:64-65). `delegation` excluded - `can_delegate()` is `return False` (codex.py:68-69). `interception` excluded - already `unimplemented` today |
| `gemini.py` | `frozenset()` | all four excluded - `session_identity()` is `return None` (gemini.py:51-52), `can_delegate()` is `return False` (gemini.py:55-56), and `delegation`/`isolation`/`interception` are already `unimplemented` today |

`session_identity() -> dict | None` and `can_delegate() -> bool` keep their
current bodies and signatures in all three adapters. They were never the defect;
the claim made about them was.

### 3. `plugins/autopilot/scripts/codex.py`

The no-binary branch and the status block become:

```python
from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    ProbeResult,
    statuses_from,
    unavailable,
)

HOST_ID = "codex"
IMPLEMENTED_CAPABILITIES = frozenset({"isolation"})


def probe(*, project_root: Path) -> ProbeResult:
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("codex") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    return ProbeResult(
        host_id=HOST_ID,
        available=True,
        capability=HostCapability(
            host_id=HOST_ID,
            statuses=statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=_has_auth()),
        ),
        probed_at=probed_at,
        evidence_path=None,
        authenticated=_has_auth(),
    )
```

Compute `_has_auth()` once into a local and pass it to both call sites, rather
than calling it twice as the snippet reads for clarity.

`_has_auth()`, `_AUTH_ENV_VAR` and `_AUTH_FILE` are unchanged. The module's
existing static-only docstring is unchanged. `UNAVAILABLE_NO_AUTH` and
`CapabilityStatus` are no longer referenced here and come out of the import list.

A deliberate behaviour change: a codex binary present with no auth now reports
`available=True` with `isolation: unavailable (no_auth)`, as today - the host is
there, its capability is not usable. Only a missing binary is `available=False`.
This keeps the existing semantics; it is stated because the `unavailable()`
helper makes it easy to over-apply.

### 4. `plugins/autopilot/scripts/gemini.py`

Closes: R1 - "The gemini probe returns available=False together with a non-None capability ... Claude and codex return None in the same state, so build-compatibility.py skips them while writing a gemini bundle."

```python
"""Gemini host adapter - native host seam for the Gemini CLI.

STATIC checks only: binary-on-PATH and GEMINI_API_KEY presence. Never invokes
`gemini` as a subprocess and never performs a live dispatch. Implements no
capability yet: session identity and in-session delegation are both inert, so
IMPLEMENTED_CAPABILITIES is empty and the declared contract is empty with it.
"""

from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    ProbeResult,
    statuses_from,
    unavailable,
)

HOST_ID = "gemini"
IMPLEMENTED_CAPABILITIES: frozenset[str] = frozenset()


def probe(*, project_root: Path) -> ProbeResult:
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("gemini") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    return ProbeResult(
        host_id=HOST_ID,
        available=True,
        capability=HostCapability(
            host_id=HOST_ID,
            statuses=statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=authenticated),
        ),
        probed_at=probed_at,
        evidence_path=None,
        authenticated=authenticated,
    )
```

with `authenticated = bool(os.environ.get("GEMINI_API_KEY"))` computed once
before the return.

**The no-auth branch is deliberately gone.** Today a gemini binary with no
`GEMINI_API_KEY` returns `available=False` *with* a capability object - the exact
R1 contract violation. After this change a present binary is always
`available=True`. `UNAVAILABLE_NO_AUTH` and `CapabilityStatus` come out of the
import list; `os` stays.

**`GEMINI_API_KEY` presence stays observable, through the `authenticated`
field.** With `IMPLEMENTED_CAPABILITIES` empty, every capability status is
`unimplemented` whatever the auth state, so the statuses alone cannot record it -
and the PRD requires "Missing binary/auth/capability records unavailable". The
`ProbeResult.authenticated` field added in §1 is what carries it: an
authenticated and an unauthenticated gemini host now serialise differently
(`authenticated: true` against `authenticated: false`), and §15(a) asserts both.
The field records presence only; no key, token or file content is ever stored.

Gemini declaring zero capabilities **is the explicit blocker** the PRD's
Claude-free profile paragraph demands - "A missing mandatory host capability
remains an explicit blocker to this profile's certification" - and it must be
visible in the declaration and the bundle, not only in the code.

### 5. `plugins/autopilot/scripts/claude.py`

Closes: R10 - "`claude.probe` hardcodes interception "available" (claude.py:50) with no hook registration or interception test."

```python
from hosts import (
    UNAVAILABLE_NO_BINARY,
    HostCapability,
    ProbeResult,
    statuses_from,
    unavailable,
)

HOST_ID = "claude"
IMPLEMENTED_CAPABILITIES = frozenset({"identity", "delegation", "isolation", "interception"})


def probe(*, project_root: Path) -> ProbeResult:
    """STATIC checks only: binary-on-PATH and auth presence. Never a live
    dispatch, never a real Agent-tool round-trip."""
    probed_at = datetime.now(timezone.utc).isoformat()
    if shutil.which("claude") is None:
        return unavailable(HOST_ID, probed_at=probed_at, reason=UNAVAILABLE_NO_BINARY)
    authenticated = bool(
        os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    )
    return ProbeResult(
        host_id=HOST_ID,
        available=True,
        capability=HostCapability(
            host_id=HOST_ID,
            statuses=statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=authenticated),
        ),
        probed_at=probed_at,
        evidence_path=None,
        authenticated=authenticated,
    )
```

**Two deliberate losses, both acceptable.** `interception` becomes auth-gated
and reports `"supported"` rather than unconditionally `"available"`: the old
hardcode plus its comment go away, because `statuses_from` has one rule and a
per-name exception would put the R10 class of defect straight back. Hook
registration genuinely does not need auth, so an unauthenticated Claude host now
under-reports `interception` by one status - the conservative direction, and the
committed bundle is unaffected because it is derived from the declaration (§7),
not from this status.

`claude.session_identity()` keeps its body. Its docstring gains one sentence:
`CLAUDE_SESSION_ID is the Claude Code session-id environment variable; absent, this host exposes no native session identity.`
`identity` stays in `IMPLEMENTED_CAPABILITIES` and is reported `"supported"` when
authenticated: the module *has* identity code, and whether a given process is
inside a Claude session is a per-run fact that belongs in probe evidence, not in
a capability claim. `"supported"` is exactly the strength of that claim - the
adapter supports identity; this probe did not watch it work.

### 6. `plugins/autopilot/contracts/hosts.json`

The declaration is each adapter's `IMPLEMENTED_CAPABILITIES`, sorted, and is
therefore identical on every machine:

```json
{
  "schema_version": 1,
  "hosts": {
    "claude": {"capabilities": ["delegation", "identity", "interception", "isolation"]},
    "codex": {"capabilities": ["isolation"]},
    "gemini": {"capabilities": []}
  }
}
```

`schema_version` stays `1`: the shape did not change, only the values.

### 7. `tools/autopilot/build-compatibility.py`

Closes: R11 - "`tools/autopilot/build-compatibility.py` derives bundle content from live auth presence, so output varies by machine."

**The committed bundle holds the declared-and-implemented set, never the live
available set.** This is the whole of R11: an artifact in git must not change
with the builder's `~/.codex/auth.json`. Replace the body of the per-host loop:

```python
import importlib

def _implemented(host_id: str) -> frozenset[str]:
    """The adapter's own IMPLEMENTED_CAPABILITIES - a code fact, read without
    probing, so the generated bundle cannot depend on this machine."""
    return importlib.import_module(host_id).IMPLEMENTED_CAPABILITIES


def write_bundle(compatibility_dir: Path, host_id: str, bundle: dict) -> None:
    compatibility_dir.mkdir(parents=True, exist_ok=True)
    path = compatibility_dir / f"{host_id}.json"
    path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")


for host_id, declaration in contract["hosts"].items():
    declared = set(declaration["capabilities"])
    implemented = _implemented(host_id)
    overclaimed = sorted(declared - implemented)
    if overclaimed:
        print(
            f"host {host_id!r}: declared capability {overclaimed[0]!r} is unimplemented",
            file=sys.stderr,
        )
        sys.exit(1)
    write_bundle(
        compatibility_dir,
        host_id,
        {
            "host_id": host_id,
            "capabilities": sorted(declared),
            "probe_kind": "static",
        },
    )
```

Three consequences, all intended:

- `hosts.probe_host` is **no longer called** by this tool. Auth presence cannot
  reach a committed file, and a host with no binary installed no longer makes the
  tool skip a bundle, so a stale positive bundle can no longer survive a lost
  binary. The `probe_result.capability is None: continue` branch is deleted.
- The existing abort on a declared-but-unimplemented capability survives, with
  the same stderr wording, and is now machine-independent. It is the check that
  keeps the declaration honest if someone widens it again.
- Every bundle gains `"probe_kind": "static"` and a trailing newline. The
  trailing newline also closes the ⚪ Carl finding R42 at no extra cost.

### 8. `plugins/autopilot/compatibility/*.json`

Closes: R11 - "`plugins/autopilot/compatibility/codex.json:3` lists delegation, identity and isolation as supported."

The exact committed bytes, reproducible on any machine by running the tool above
against the §6 declaration (two-space indent, trailing newline):

`claude.json`:

```json
{
  "host_id": "claude",
  "capabilities": [
    "delegation",
    "identity",
    "interception",
    "isolation"
  ],
  "probe_kind": "static"
}
```

`codex.json`:

```json
{
  "host_id": "codex",
  "capabilities": [
    "isolation"
  ],
  "probe_kind": "static"
}
```

`gemini.json`:

```json
{
  "host_id": "gemini",
  "capabilities": [],
  "probe_kind": "static"
}
```

Never hand-edit a bundle; run the tool and commit what it emits. These bytes are
stated so the result is verifiable rather than machine-dependent.

### 9. `plugins/autopilot/CHANGELOG.md`

Replace the capability sentence with one that matches the declaration and says
what the probe is:

`Add static host adapters for Claude, Codex and Gemini with a declared-capability contract and generated compatibility bundles. A declared capability is one the adapter implements, so the contract and the bundles are identical on every machine; auth presence appears only in per-run probe evidence, never in a committed artifact. Claude declares identity, delegation, isolation and interception; Codex declares isolation only; Gemini declares none, because neither host implements native session identity or in-session delegation yet. Capability status is a static observation (binary on PATH plus auth presence), never a live invocation. No host execution or certification is claimed.`

### 10. `tools/autopilot/probe-host.py`

Closes in part: R9 - "All adapter probes are static (`shutil.which` plus an env var or auth-file existence check). Nothing invokes a host, proves identity, isolation or interception, or records unavailable hosts." (the recording and labelling half; see `## Module placement` for what stays open and why)

The record must identify itself and must state plainly that nothing was
certified. Add `import shutil` to the import block, then:

- Resolve the winning filename FIRST, inside the pinned-fd block, so the record
  can name the path it is actually written to. `O_EXCL` replaces `O_TRUNC`:
  `O_NOFOLLOW` guards symlinks only, so `O_TRUNC` would still truncate an
  external file through a pre-existing hard link.

  ```python
  parent_fd = _pinned_parent_fd(probes_dir, project_root)
  try:
      flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
      for attempt in range(1, 11):
          filename = (
              f"{args.host_id}-{timestamp}.json"
              if attempt == 1
              else f"{args.host_id}-{timestamp}-{attempt}.json"
          )
          try:
              fd = os.open(filename, flags, 0o666, dir_fd=parent_fd)
              break
          except FileExistsError:
              if attempt == 10:
                  raise
  finally:
      os.close(parent_fd)
  ```

  The retry loop lives inside the `try`, so `parent_fd` stays open across
  attempts and is still closed exactly once.

- Build the payload AFTER the filename is decided, from the name that won:

  ```python
  relative = Path("docs/dev/tmp/autopilot/probes") / filename
  record = dataclasses.asdict(result) | {
      "evidence_path": relative.as_posix(),
      "binary_path": shutil.which(args.host_id),
  }
  payload = json.dumps(record, indent=2)
  ```

  `binary_path` is **an independent second lookup**, not the adapter's own
  resolution: the adapter already called `shutil.which` inside `probe()`, and a
  `PATH` target changing between the two calls can yield `available=True` beside
  `binary_path: None`. Do not describe it as identifying the probed executable;
  it is a non-secret observation recorded alongside the result, and a mismatch
  between the two is itself useful evidence. **No auth value, token, or file
  content is ever recorded**;
  auth presence reaches the record only as the boolean `authenticated` field and
  the `status`/`unavailable_reason` values the probe already computed. The record
  also carries `probe_kind: "static"` and `certified: false` straight from the
  dataclass, so the artifact itself says no host was invoked.

Everything else stays: the tool writes only under
`docs/dev/tmp/autopilot/probes/`, pins the parent directory fd through
`_pinned_parent_fd`, and never touches live user configuration.

### 11. `tools/autopilot/update_helper_map.py` and `tools/autopilot/source-map.json`

Closes: R7 - "Stale source-map digests. The `plugins/autopilot/scripts/autopilot.py` and `plugins/autopilot/CHANGELOG.md` rows have `destination_blob_sha256` values that no longer match the files on disk."
Closes: R8 - "test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map fails with "source-map.json is not the generated helper map"."

**R7 and R8 are one defect today, and this rework would create a second one.**

*Today.* `plugins/autopilot/scripts/autopilot.py` and
`plugins/autopilot/CHANGELOG.md` are both in `update_helper_map.REFRESHED`
(`update_helper_map.py:274-278`), and `apply()` recomputes
`destination_blob_sha256` for exactly those rows. The two digests went stale when
tasks 7 and 10 edited those files without rerunning the generator; that same
staleness is why `--check` reports "not the generated helper map". **Verified
empirically at `68418c5a`**: copy the map aside, run the generator with
`--root .`, and `--check` then exits 0; the only changed values are those two
digests plus the `evidence.artifact_sha256` of the CHANGELOG row, which is derived
from the same bytes. Every AP00014 and AP00018 row is byte-identical afterwards,
because `apply()` deep-copies the document (`:488`) and upserts only
`HELPER_PATHS` (`:499-506`). Alice's claim that "the generator does not produce
them, so the committed map drifts from the tool that owns it" is refuted by that
code path: the generator never owned those rows.

*The second defect this rework would create.* All 13 paths in
`test_helper_provenance_real.AP00014_TARGETS` currently digest their real bytes,
and this rework edits nine of them. `REFRESHED` does not list them, so after the
fixes their digests go stale and §14's new row-integrity test fails - with no
permitted repair, because hand-editing a digest is forbidden. **Resolve it by
giving the generator ownership**, which is the only option that leaves one writer:

```python
AP00014_DIGESTED = (
    "plugins/autopilot/compatibility/claude.json",
    "plugins/autopilot/compatibility/codex.json",
    "plugins/autopilot/compatibility/gemini.json",
    "plugins/autopilot/contracts/hosts.json",
    "plugins/autopilot/scripts/claude.py",
    "plugins/autopilot/scripts/codex.py",
    "plugins/autopilot/scripts/doctor.py",
    "plugins/autopilot/scripts/gemini.py",
    "plugins/autopilot/scripts/guards.py",
    "plugins/autopilot/scripts/hosts.py",
    "plugins/autopilot/scripts/jobs.py",
    "tools/autopilot/build-compatibility.py",
    "tools/autopilot/probe-host.py",
)
```

In `apply()`, after the existing `REFRESHED` loop, refresh **only the digest** of
these rows - never their `evidence`, which is AP00014's own and not this
generator's to rewrite:

```python
ap00014 = set(AP00014_DIGESTED)
for row in result["assets"]:
    if row["destination_path"] in ap00014:
        row["destination_blob_sha256"] = hashlib.sha256(
            (root / row["destination_path"]).read_bytes()
        ).hexdigest()
```

The 13 paths are exactly `AP00014_TARGETS` in
`test_helper_provenance_real.py:48-62`; keep the two lists equal. The rows stay
excluded from the frozen `OTHER_ASSETS_SHA` (that exclusion is why changing their
digests is safe), and `authored_file_owners` is untouched, so the `delivery_prd`
values stay `"00014"`.

**Then, as the LAST step of the whole rework**, after every other file edit:

```
python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json
```

**Never hand-edit a `destination_blob_sha256`.** Running the generator before a
later edit re-stales the map and re-breaks R7 and R8; see
`## Risks & edge cases`.

### 12. `tests/autopilot/test_package.py`

Closes: R5 - "test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes fails with AssertionError '00014' != '00013'. The test hardcodes `later = "00018" if "/controller/" in row["path"] else "00013"`."
Closes: R6 - "test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy ... fail. The `_CAPABILITIES` list grew by hosts-v1, guards-v1 and diagnose-v1."

Three edits.

- A module-level path set mirroring the existing `CONTROLLER_PREFIXES`
  precedent, holding the same 13 paths as `AP00014_DIGESTED` above:

  ```python
  AP00014_OWNED = frozenset({
      "plugins/autopilot/compatibility/claude.json",
      "plugins/autopilot/compatibility/codex.json",
      "plugins/autopilot/compatibility/gemini.json",
      "plugins/autopilot/contracts/hosts.json",
      "plugins/autopilot/scripts/claude.py",
      "plugins/autopilot/scripts/codex.py",
      "plugins/autopilot/scripts/doctor.py",
      "plugins/autopilot/scripts/gemini.py",
      "plugins/autopilot/scripts/guards.py",
      "plugins/autopilot/scripts/hosts.py",
      "plugins/autopilot/scripts/jobs.py",
      "tools/autopilot/build-compatibility.py",
      "tools/autopilot/probe-host.py",
  })
  ```

- In `assert_authored_owners_and_history`, replace the two-way `later`
  (`test_package.py:202`) with a three-way owner expectation:

  ```python
  if "/controller/" in row["path"]:
      expected_owner = "00018"
  elif row["path"] in AP00014_OWNED:
      expected_owner = "00014"
  else:
      expected_owner = "00013"
  self.assertEqual(row["delivery_prd"], "00012" if index < 21 else expected_owner)
  self.assertTrue((self.target / row["path"]).is_file())
  ```

  The `is_file()` line at `:204` is **unchanged, and must stay unchanged**.
  `self.target` is a repo-wide `git archive` of HEAD, not a package root
  (`:109` reads `self.target / "scripts/validate.py"`, `:267` reads
  `self.target / "tools/autopilot/source-inventory.json"`), and seven
  `tools/autopilot/*` owner rows delivered by 00012/00013 already satisfy it. The
  two new `tools/autopilot/*` rows need no exemption, and adding one would hide a
  real packaging regression.

- In `test_target_only_checkout_denies_source_home_and_network_but_exports_policy`,
  extend the `listed[3:]` expectation at `:404-406` to the ten operation ids
  `plugins/autopilot/scripts/autopilot.py:24-29` now publishes, in `_CAPABILITIES`
  order:

  ```python
  self.assertEqual(listed[3:], [
      "stage-review-v1", "group-findings-v1", "check-evidence-v1", "prepare-close-v1",
      "catchup-probe-v1", "verification-artifact-v1", "controller-required-v1",
      "hosts-v1", "guards-v1", "diagnose-v1"])
  ```

### 13. `tests/autopilot/test_local_boundary.py`

Closes: R6 - "test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations fails. The `_CAPABILITIES` list grew by hosts-v1, guards-v1 and diagnose-v1, so the list now has 13 entries where the tests expect 3+7."

```python
OPERATIONS = {
    "stage-review-v1", "group-findings-v1", "check-evidence-v1", "prepare-close-v1",
    "catchup-probe-v1", "verification-artifact-v1", "controller-required-v1",
    "hosts-v1", "guards-v1", "diagnose-v1",
}
```

The test body is unchanged: `:242-243` already derive the count from
`len(LEGACY) + len(OPERATIONS)` and membership from `set(ids[3:]) == OPERATIONS`,
so widening the constant is the whole fix. Its
`assert not [i for i in ids if "cap" in i.split("-") or "custody" in i]` still
holds for all three new ids. `tests/autopilot/test_facade.py:26` already carries
the same ten and needs no edit.

### 14. `tests/autopilot/test_helper_provenance_real.py`

Closes: R4 - "Five tests fail that pass at the PRD base commit 635e376, so they are regressions from this PRD, not pre-existing."
Closes: R8 - the replacement check that makes the `AP00014_TARGETS` exclusion safe.

The existing `AP00014_TARGETS` exclusion at `:241` stays: it correctly keeps a
later PRD's rows out of the frozen `OTHER_ASSETS_SHA`, exactly as
`CONTROLLER_PREFIXES` does for AP00018. What is missing is the replacement check
AP00018 has (`:319-328`). Add one test:

```python
def test_ap00014_rows_are_owned_and_digested_from_current_bytes(mapping: dict) -> None:
    """Every AP00014 row is owned by 00014 and digests its current bytes."""
    assets = single_assets(mapping, sorted(AP00014_TARGETS))
    owners = by_key(mapping["authored_file_owners"], "path")
    for path in sorted(AP00014_TARGETS):
        assert assets[path]["destination_blob_sha256"] == digest(
            (ROOT / path).read_bytes()
        ), path
        assert owners[path]["delivery_prd"] == "00014", path
        assert owners[path]["owner_repository"] == "buvis/agent-plugins", path
        assert owners[path]["source_asset_id"] is None, path
        assert owners[path]["source_blob_sha256"] is None, path
        assert owners[path]["acceptance_cases"], path
```

This is the AP00014 analogue of the controller block at `:319-328`, and §11's
`AP00014_DIGESTED` is what keeps it satisfiable without hand-editing a digest.

### 15. `tests/autopilot/test_sessions.py`

Closes: R1 and R10 - the invariants, pinned deterministically, so the next widening of a declaration fails a test rather than shipping a false bundle.

Four edits. **Every assertion below is independent of the developer's installed
binaries and environment variables** - a test whose outcome varies by machine is
the R11 defect, not a check on it. Add to the imports:

```python
import os
import shutil
from unittest import mock

claude = importlib.import_module("claude")
codex = importlib.import_module("codex")
```

**(a) `GeminiCapabilityContractTest` is re-specified.** Three of its four tests
(`:33-43`, and `:45-51` via the same dereference) assert
`assertIsNotNone(result.capability)` against a probe of the real machine, which
breaks the moment §4 returns `capability=None` for a missing binary. Replace the
machine-dependent probe with both branches, driven explicitly:

```python
class GeminiCapabilityContractTest(unittest.TestCase):
    """gemini.py implements no capability yet; its probe must say so, and must
    obey the ProbeResult invariant in both branches."""

    def test_missing_binary_yields_no_capability_and_a_recorded_reason(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            result = gemini.probe(project_root=ROOT)
        self.assertFalse(result.available)
        self.assertIsNone(result.capability)
        self.assertEqual(result.unavailable_reason, hosts.UNAVAILABLE_NO_BINARY)
        self.assertIsNone(result.authenticated)

    def test_present_binary_reports_every_capability_unimplemented(self) -> None:
        with mock.patch.object(shutil, "which", return_value="/usr/bin/gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                result = gemini.probe(project_root=ROOT)
        self.assertTrue(result.available)
        self.assertIsNone(result.unavailable_reason)
        self.assertEqual(tuple(result.capability.statuses), hosts.CAPABILITY_NAMES)
        for name in hosts.CAPABILITY_NAMES:
            with self.subTest(capability=name):
                self.assertEqual(result.capability.statuses[name].status, "unimplemented")

    def test_auth_presence_stays_observable_even_with_no_capability_implemented(
        self,
    ) -> None:
        """Every status is "unimplemented" either way, so `authenticated` is the
        only field that records auth presence - and the PRD requires it be
        recorded."""
        with mock.patch.object(shutil, "which", return_value="/usr/bin/gemini"):
            with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k"}, clear=True):
                with_auth = gemini.probe(project_root=ROOT)
            with mock.patch.dict(os.environ, {}, clear=True):
                without_auth = gemini.probe(project_root=ROOT)
        self.assertIs(with_auth.authenticated, True)
        self.assertIs(without_auth.authenticated, False)

    def test_can_delegate_is_unconditionally_false(self) -> None:
        self.assertIs(gemini.can_delegate(), False)
```

`mock.patch.object(shutil, "which", ...)` patches the module object the adapter
imported, so it reaches `gemini.probe` in-process. The retired
`test_identity_status_is_one_of_the_known_values` is subsumed: an exact status
assertion is strictly stronger than membership in a three-value tuple.

**(b) `CodexGeminiRoleCapabilitiesTest` is re-specified.** `:138-153` assert that
codex and gemini declare `identity`, which §6 makes false - and *deliberately*
false, because neither implements it. Rewriting them to the new truth is the
point of the cycle, not collateral damage. Keep `_resolve_candidate_hosts`,
`test_mandatory_reviewer_job_union_matches_the_policy_data` (`:128-136`),
`test_resolver_rejects_a_capability_subset_neither_host_declares` (`:155-157`)
and `test_empty_required_capabilities_resolves_to_both_hosts` (`:159`) as they
are. Replace the two identity tests with one that records the blocker:

```python
    def test_identity_jobs_resolve_to_no_non_claude_host_which_blocks_the_claude_free_profile(
        self,
    ) -> None:
        """AP00014 implements native session identity on no non-Claude host, so
        the PRD's Claude-free profile is not certifiable yet. This is the
        explicit blocker the PRD requires, recorded rather than papered over;
        AP 00017 owns the certification that would change it."""
        self.assertEqual(_resolve_candidate_hosts(("identity",), self.hosts_declared), [])
        self.assertEqual(
            _resolve_candidate_hosts(("identity", "delegation", "isolation"), self.hosts_declared),
            [],
        )
        self.assertEqual(_resolve_candidate_hosts(("isolation",), self.hosts_declared), ["codex"])
```

The last line keeps a positive case, so the test cannot pass by the resolver
always returning `[]`. The retired `assertNotEqual(set(resolved), {"claude"})`
assertions are dropped outright: `_resolve_candidate_hosts` only ever returns
members of `("codex", "gemini")` (`:112`), so comparing its result to `{"claude"}`
could never fail - Alice's R14 called this vacuous and she was right.

**(c) New test: the declaration equals what the adapters implement.** This is the
single assertion that keeps R10 and R11 closed:

```python
class DeclaredCapabilitiesMatchImplementationTest(unittest.TestCase):
    def test_contract_declares_exactly_what_each_adapter_implements(self) -> None:
        declared = json.loads((CONTRACTS / "hosts.json").read_text())["hosts"]
        for host_id, module in (("claude", claude), ("codex", codex), ("gemini", gemini)):
            with self.subTest(host=host_id):
                self.assertEqual(
                    set(declared[host_id]["capabilities"]),
                    set(module.IMPLEMENTED_CAPABILITIES),
                )

    def test_an_inert_backing_function_keeps_its_capability_unimplemented(self) -> None:
        """A capability whose backing function cannot succeed is never declared."""
        with mock.patch.dict(os.environ, {}, clear=True):
            for host_id, module in (("codex", codex), ("gemini", gemini)):
                with self.subTest(host=host_id):
                    self.assertIsNone(module.session_identity())
                    self.assertIs(module.can_delegate(), False)
                    self.assertNotIn("identity", module.IMPLEMENTED_CAPABILITIES)
                    self.assertNotIn("delegation", module.IMPLEMENTED_CAPABILITIES)

    def test_claude_identity_is_implemented_because_it_returns_a_record(self) -> None:
        with mock.patch.dict(os.environ, {"CLAUDE_SESSION_ID": "s-1"}, clear=True):
            identity = claude.session_identity()
        self.assertEqual(identity["host"], "claude")
        self.assertEqual(identity["session_id"], "s-1")
        self.assertIn("identity", claude.IMPLEMENTED_CAPABILITIES)
        self.assertIs(claude.can_delegate(), True)

    def test_no_static_probe_ever_claims_availability_or_certification(self) -> None:
        """"supported" is the strongest claim a static probe may make."""
        self.assertNotIn("available", hosts.CAPABILITY_STATUSES)
        for host_id, module in (("claude", claude), ("codex", codex), ("gemini", gemini)):
            for authenticated in (True, False):
                with self.subTest(host=host_id, authenticated=authenticated):
                    statuses = hosts.statuses_from(
                        module.IMPLEMENTED_CAPABILITIES, authenticated=authenticated
                    )
                    for status in statuses.values():
                        self.assertIn(status.status, hosts.CAPABILITY_STATUSES)
        with mock.patch.object(shutil, "which", return_value="/usr/bin/claude"):
            result = claude.probe(project_root=ROOT)
        self.assertEqual(result.probe_kind, "static")
        self.assertIs(result.certified, False)
```

`mock.patch.dict(os.environ, {}, clear=True)` is what makes the codex/gemini
assertions machine-independent. The claude case asserts the capability is
implemented by exhibiting the record it produces, which is why claude keeps
`identity` while codex and gemini do not. The last test is what pins the
answer to "a static probe must not say available": it drives `statuses_from`
directly over both auth states, so it needs no binary at all.

**(d) Replace the hedged assertions.** `assertIn(codex.can_delegate(), (True, False))`,
`assertIn(gemini.can_delegate(), (True, False))` (`:95` and nearby) and
`assertTrue(result is None or isinstance(result, list))` (`:102`) cannot fail as
written. Replace with `assertIs(codex.can_delegate(), False)`,
`assertIs(gemini.can_delegate(), False)` and
`self.assertIsNone(adapter.build_job_argv(None))` - all three adapters return
`None` there today, so the exact assertion is correct and binding. The same
either-or shape at `test_jobs.py:306` is a 🟡 finding deferred this cycle and is
not touched here.

### 16. `tests/autopilot/test_compatibility.py`

Closes: R11 - the generator's output must not depend on the developer's installed hosts.

**`REAL_CONTRACT` (`:36-43`) must be updated to the §6 declaration**, or the
generator aborts on it and `RoundTripTest` (`:123`, `:152`) and
`CliInvocationShapeTest` (`:209`) start asserting `returncode == 0` against an
exit 1:

```python
REAL_CONTRACT = {
    "schema_version": 1,
    "hosts": {
        "claude": {"capabilities": ["delegation", "identity", "interception", "isolation"]},
        "codex": {"capabilities": ["isolation"]},
        "gemini": {"capabilities": []},
    },
}
```

The inline contract at `:160-163` becomes
`{"schema_version": 1, "hosts": {"codex": {"capabilities": ["isolation"]}}}`.

`_expected_available` (`:89-100`) is **deleted**, along with its two call sites
(`:140-147`, `:169-171`). It probes the live adapter to predict the bundle, which
is precisely the machine dependence R11 names; after §7 the prediction is the
declaration itself:

```python
    def test_bundle_capabilities_equal_exactly_the_declared_implemented_set(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td)
            _write_contract(tmp_root, REAL_CONTRACT)
            proc = _run_build(tmp_root)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertEqual(proc.stderr, "")
            for host_id, declared in REAL_CONTRACT["hosts"].items():
                with self.subTest(host=host_id):
                    path = tmp_root / "plugins/autopilot/compatibility" / f"{host_id}.json"
                    self.assertTrue(path.exists())
                    bundle = json.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        _collect_capability_tokens(bundle), set(declared["capabilities"])
                    )
                    self.assertEqual(bundle["probe_kind"], "static")
```

`gemini.json` is now asserted to exist with an empty list - under the old
`capability is None: continue` branch no gemini bundle was written at all on a
machine without the binary.

**The machine-independence test must scrub the child's environment, not
monkeypatch.** `_run_build` (`:80-86`) launches the generator with
`subprocess.run`, so patching `shutil.which` in the test process cannot reach it.
Add a `env` parameter to `_run_build` and one new test:

```python
def _scrubbed_env(tmp_home: Path) -> dict:
    """An env in which no host binary resolves and no host is authenticated:
    empty PATH, HOME at a temp dir (so codex's ~/.codex/auth.json is absent),
    and every auth variable cleared."""
    env = {k: v for k, v in os.environ.items() if k not in _AUTH_VARS}
    env["PATH"] = ""
    env["HOME"] = str(tmp_home)
    return env


_AUTH_VARS = (
    "CODEX_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
)


    def test_bundle_bytes_are_identical_with_no_binary_and_no_auth(self) -> None:
        """Two builds into two FRESH roots, each with a controlled environment,
        and every expected bundle must EXIST in both before any comparison."""
        bundles = {}
        for label, scrub in (("rich", False), ("bare", True)):
            with tempfile.TemporaryDirectory() as td:
                tmp_root = Path(td)
                _write_contract(tmp_root, REAL_CONTRACT)
                env = _scrubbed_env(tmp_root) if scrub else _authenticated_env(tmp_root)
                self.assertEqual(_run_build(tmp_root, env=env).returncode, 0)
                bundles[label] = {}
                for host_id in REAL_CONTRACT["hosts"]:
                    path = tmp_root / "plugins/autopilot/compatibility" / f"{host_id}.json"
                    self.assertTrue(path.exists(), f"{label}: {host_id} bundle missing")
                    bundles[label][host_id] = path.read_bytes()
        for host_id in REAL_CONTRACT["hosts"]:
            with self.subTest(host=host_id):
                self.assertEqual(bundles["bare"][host_id], bundles["rich"][host_id])
```

with `_authenticated_env(tmp_home)` returning a copy of `_scrubbed_env(tmp_home)`
with every `_AUTH_VARS` name set to a dummy value and `PATH` left as the real
one, so the two runs genuinely differ in auth and binary presence.

**Two fresh roots and the existence assertions are load-bearing.** An earlier
draft ran both builds into the SAME root, where a generator that skipped a host
would leave the first run's file in place and the byte comparison would pass -
the exact stale-bundle behaviour §7 exists to remove, surviving as a green test.
It also left the first environment uncontrolled, so the test's baseline failure
was not guaranteed. In the shape above the test fails at `68418c5a` for a
definite reason: today's generator skips a host whose `capability is None`, so
the `bare` run writes no bundle at all and `path.exists()` fails.

`HOME` scrubbing is required, or `codex._AUTH_FILE` (`codex.py:24`,
`Path.home() / ".codex" / "auth.json"`) leaks the developer's real auth into the
child.

`BuildFailureTest` (`:179-188`) keeps its purpose but drops its live-probe
premise (`:183-184`): assert the abort directly by declaring a capability the
adapter does not implement, e.g.
`{"schema_version": 1, "hosts": {"gemini": {"capabilities": ["identity"]}}}`,
and assert exit 1 with `is unimplemented` in stderr.

### 17. `tests/autopilot/test_host_argv.py`

Closes: R9 - the evidence record must be checkable, not just written.

One new test, in this file because it already owns the probe-dispatch surface:

```python
def test_probe_host_evidence_names_its_own_path_and_binary(self) -> None:
    """The written record identifies its own artifact, labels the probe static,
    and carries no auth value."""
```

It runs `tools/autopilot/probe-host.py claude --project-root <tmp>` with
`subprocess.run`, reads the single file under
`<tmp>/docs/dev/tmp/autopilot/probes/`, and asserts: `record["evidence_path"]`
equals that file's path relative to `<tmp>`, `record["probe_kind"] == "static"`,
`record["certified"] is False`, `record["binary_path"]` is `None` or an existing
path, and the record leaks no secret.

**Leak check, stated exactly** (an earlier draft used the real environment's auth
values as substrings, which is both machine-dependent and unsound - an empty
value matches every string and a short one matches ordinary text). Define the
variable list locally in this module, do not import it from
`test_compatibility.py`:

```python
_AUTH_VARS = (
    "CODEX_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
)
_SENTINEL = "ap00014-secret-sentinel-4f1c8e"
```

Run the subprocess with every `_AUTH_VARS` name set to `_SENTINEL`, then assert
`_SENTINEL not in evidence_file.read_text()`. A long distinctive value cannot
match by accident and the assertion holds on any machine.

## Data flow

```
IMPLEMENTED_CAPABILITIES (per adapter: a code fact, machine-independent)
  -> plugins/autopilot/contracts/hosts.json          declaration, committed
  -> tools/autopilot/build-compatibility.py          declared - implemented != {} -> exit 1
  -> plugins/autopilot/compatibility/<host>.json     committed, byte-identical everywhere

hosts.probe_host(host_id)                            per-run observation, never committed
  -> <adapter>.probe(project_root)                   static only
       binary on PATH?  no -> unavailable(...)       capability=None, unavailable_reason set
       yes              -> statuses_from(IMPLEMENTED_CAPABILITIES, authenticated=...)
                             name not implemented -> "unimplemented", reason None
                             implemented + auth    -> "supported"  (never "available")
                             implemented, no auth  -> "unavailable", reason no_auth
  -> tools/autopilot/probe-host.py
       -> docs/dev/tmp/autopilot/probes/<host>-<ts>.json
          evidence_path, binary_path, probe_kind="static"
          created O_CREAT|O_EXCL|O_NOFOLLOW inside a pinned parent fd
```

The declaration is the contract; the probe is the observation. Only the
declaration reaches a committed file. No step in this flow starts a process.

## Reuse inventory

- `hosts.CapabilityStatus` / `HostCapability` / `ProbeResult`
  (`plugins/autopilot/scripts/hosts.py:15-34`) - the existing capability types.
  Reused as-is; `ProbeResult` gains two defaulted fields and the module gains two
  functions. No parallel type is introduced.
- `hosts.UNAVAILABLE_NO_BINARY` / `UNAVAILABLE_NO_AUTH` (`hosts.py:11-12`) -
  existing reason constants, reused unchanged. No new reason constant is added.
- `update_helper_map.apply` / `REFRESHED` / `--check`
  (`tools/autopilot/update_helper_map.py:478,558`) - the committed map's own
  generator. Extended with one tuple and one loop rather than replaced; it
  already owns the two stale digests, so R7 and R8 need no new tool.
- `log_sink_refusal._pinned_parent_fd` - the existing write-containment
  primitive `probe-host.py` already uses. Reused unchanged; only the open flags
  and the retry loop change.
- `tests/autopilot/test_helper_provenance_real.CONTROLLER_PREFIXES` and the
  controller assertion block at `:319-328` - the AP00018 precedent for "exclude a
  later PRD's rows from a frozen hash, then assert them separately". §14 is
  modelled on it directly.
- `tests/autopilot/test_compatibility._collect_capability_tokens` (`:103-119`) -
  the schema-agnostic bundle reader. Reused in §16's rewritten assertions.
  `_write_contract` (`:74-77`) and `_run_build` (`:80-86`) are reused; only
  `_run_build` gains an `env` parameter.
- `tests/autopilot/test_local_boundary.LEGACY` / `OPERATIONS` (`:32-36`) - the
  operation-id constants. Widened, not replaced; the assertions already read them.
- `tests/autopilot/test_sessions._resolve_candidate_hosts` (`:105-116`) - the
  test-local declaration resolver. Kept; only its expectations change.
- Greps run before adding the §15 declared-equals-implemented test, to check no
  such assertion already exists:
  `rg -n 'unimplemented|session_identity|can_delegate' plugins/autopilot/scripts tests/autopilot`,
  `rg -n 'declared|advertise|capabilit' tests/autopilot`. Nothing asserts the
  implication; the control term `can_delegate` returns hits in `codex.py`,
  `gemini.py`, `claude.py` and `test_sessions.py`, which proves the pattern works.
  `~/.claude/rules-library/rationalizations.md` was not read for synonym sets;
  the verb/noun pairs used are this design's own (declare / advertise / report ×
  capability / status / probe).

## Alternatives considered

**Option A - smallest diff: fix only the five failing tests.** Regenerate the
source map, widen two constants, extend one expectation. Roughly 30 changed lines,
and the PRD's own exit-criteria gate stops reporting these five. Rejected as the
whole answer: it closes R4-R8 and leaves R1, R9, R10 and R11 open, and those four
are the ones that break the PRD's stated success metric ("No unsupported
capability is advertised"). A cycle shipping only option A would converge with
four CRITICAL rows unresolved.

**Option B - option A, plus demoting the dishonest statuses in each probe.**
Mark codex `identity`/`delegation` and all four gemini names `"unimplemented"`,
fix the `ProbeResult` invariant, shrink the declaration. This was the first draft
of this design. Rejected after review: the committed `compatibility/*.json` would
still be built from the live *available* subset, so its bytes would still change
with the builder's `~/.codex/auth.json` - R11's actual complaint, left open.

**Option C (chosen) - option B, plus `IMPLEMENTED_CAPABILITIES` as the single
source of the declaration and the bundle.** One constant per adapter states what
the code can do; the declaration equals it, the committed bundle equals the
declaration, and auth presence survives only in uncommitted probe evidence. What
the extra size buys over option B: R11 genuinely closes (§16 tests the bytes are
identical with and without auth), `statuses_from` removes the per-name special
cases where R10's defect lived, and `build-compatibility.py` stops calling
`probe_host` entirely - a tool that generates a committed artifact no longer
reads the machine. Cost: three existing test classes are re-specified (§15, §16),
and `claude`'s unconditional `interception: "available"` becomes auth-gated.

**Option D - implement real headless probes now.** Invoke each host CLI, capture
identity, record live evidence. Rejected on PRD authority, twice over: "never
spawn headless provider CLI children inside plugin scripts", and "AP 00017 owns
real certification, OV 00059 owns managed Gemini process launch". Option C's
`probe_kind: "static"` label plus the recorded `unavailable_reason` is the honest
alternative: it stops a static probe reading as a live one, which is what R9
complains about.

## Risks & edge cases

- **Regenerating `source-map.json` is order-dependent, and this is the most
  likely way the rework re-breaks itself.** §11's generator run must be the LAST
  step: it digests `plugins/autopilot/scripts/autopilot.py`,
  `plugins/autopilot/CHANGELOG.md` and the 13 AP00014 paths, and this cycle edits
  the CHANGELOG (§9) and nine of the 13. Run it earlier and R7, R8 and §14's new
  test all come back.
- **The PRD's Phase 2 exit gate stays blocked after this rework, and not on this
  PRD.** 24 failures remain, all in AP00018's controller suites (recorded KNOWN by
  the doubt lens as R41). The PRD names a clean `pytest tests/autopilot -q` as
  Phase 2 exit criteria, so **Phase 2 exit is not met by this rework** and no
  later session should read §Test strategy's acceptance line as the PRD gate
  being satisfied. The acceptance test for *this rework* is that the five named
  failures are gone and the new tests pass.
- **Host-execution certification is still unmet, and R9 is only partly closed.**
  Every probe stays static; "invokes a host" is AP 00017's work and is forbidden
  here (`## Module placement`). The open dependency is therefore **AP 00017**,
  named here so it is not lost: until it lands, no capability this package
  reports may be read as proven. `ProbeResult.certified is False`,
  `__post_init__` refuses any other value, and `probe_kind: "static"` rides in
  every evidence file, so the artifact states this itself rather than relying on
  a reader finding this doc. R9 also stays in `state.deferred_decisions` as a
  CRITICAL raised in cycle 1, which is the batch-end audit trail.
- **Gemini declaring zero capabilities blocks the Claude-free profile, and that
  is the recorded answer, not an accident.** §15(b)'s test name says so in words.
  The adjacent consequence: `doctor.py:40` derives `profile="claude-free"` from
  `"identity" in covered`, so after §6 `--diagnose` starts reporting `"mixed"`.
  No existing test asserts `"claude-free"` (searched `tests/` for the literal), so
  the flip would otherwise land unobserved. The fix task should add one assertion
  pinning the post-rework value; deriving the profile properly is R15/R21,
  deferred this cycle.
- **`ProbeResult` gains four defaulted fields and a `__post_init__`, while
  `schema_version` stays 1.** The defaults keep every construction site valid as
  a call, but `__post_init__` makes the documented invariant real, so the two
  unavailable fakes at `test_host_argv.py:73-80` must start passing
  `unavailable_reason` - that is a required edit, not an optional one, and
  `test_host_argv.py` is in `## Module placement` for it. The frozen-instance test
  at `:258-273` is unaffected (`__post_init__` runs at construction, not on
  assignment). The `--probe-host` CLI output (`autopilot.py:177-179`, `asdict`)
  and the probe evidence file gain four keys; no test pins either key set
  (searched `test_facade.py`, `test_local_boundary.py`), and the package publishes
  no bundle or probe schema. A future external consumer is out of scope.
- **The `"available"` status value disappears from the vocabulary.** Any consumer
  matching on that string sees no capability as available. Inside this repo the
  matches are the adapters and the tests this design respecifies, plus
  `test_host_argv.py`'s self-defined fakes, which supply their own strings and are
  unaffected. `build-compatibility.py` no longer reads statuses at all (§7), and
  `doctor.py` passes `ProbeResult` objects through without inspecting status
  strings. Nothing outside the repo consumes them.
- **`claude`'s `interception` becomes auth-gated**, under-reporting by one status
  on an unauthenticated host. Accepted: `statuses_from` having exactly one rule is
  what keeps R10 shut, the committed bundle is unaffected because §7 reads the
  declaration, and the direction of the error is conservative.
- **Do not exempt `tools/` paths from `test_package.py`'s `is_file()` assertion.**
  An earlier draft proposed that; it was wrong (`self.target` is a repo-wide
  `git archive`, and seven `tools/autopilot/*` rows already pass), and it would
  have hidden a real packaging regression.
- **`O_EXCL` changes `probe-host.py` behaviour on a name collision.** Two probes
  of the same host within one second now produce two files rather than one
  overwritten file, and ten collisions raise. Intended trade: an extra evidence
  artifact is cheap; truncating an external file through a hard link is not.
- **Likely next changes after this PRD.** AP 00017 adds real certification and
  will want a second `probe_kind` value (`"live"`) - which is why the field is a
  string, not a bool - and will move names into `IMPLEMENTED_CAPABILITIES` as it
  implements them, where §15(c) forces the declaration and bundle to follow. OV
  00059 adds managed process launch and consumes `build_job_argv`; this design
  does not touch it. A fourth host adapter copies `gemini.py`'s post-rework shape,
  which is why `unavailable` and `statuses_from` live in `hosts.py` rather than in
  each adapter.

## Test strategy outline

**Two kinds of test here, and only one of them can fail-first. Do not conflate
them**, and do not fake a failure for the second kind.

**(1) Regression tests - MUST be seen failing at `68418c5a` before the fix
lands.** Each one fails today for the reason given.

| What | Test | Fails at `68418c5a` because |
|---|---|---|
| Source map digests | `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes` | two `REFRESHED` digests are stale |
| Generator agreement | `test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map` | same staleness, surfaced by `--check` |
| Owner expectations | `test_package.py::test_content_roster_matches_frozen_inventory_and_actual_package_bytes` | `later` has no `"00014"` branch |
| Capability list | `test_package.py::test_target_only_checkout_denies_source_home_and_network_but_exports_policy` | expectation lists 7 of 10 operations |
| Capability list | `test_local_boundary.py::test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations` | `OPERATIONS` lists 7 of 10 |
| ProbeResult invariant | `test_sessions.py::GeminiCapabilityContractTest::test_missing_binary_yields_no_capability_and_a_recorded_reason` (new) | gemini returns a capability object while `available is False`, and records no reason |
| Auth observability | `test_sessions.py::GeminiCapabilityContractTest::test_auth_presence_stays_observable_even_with_no_capability_implemented` (new) | `ProbeResult` has no `authenticated` field |
| Declaration honesty | `test_sessions.py::DeclaredCapabilitiesMatchImplementationTest::test_contract_declares_exactly_what_each_adapter_implements` (new) | `IMPLEMENTED_CAPABILITIES` does not exist; the contract declares codex identity/delegation |
| Inert backing functions | `test_sessions.py::DeclaredCapabilitiesMatchImplementationTest::test_an_inert_backing_function_keeps_its_capability_unimplemented` (new) | same |
| No false availability | `test_sessions.py::DeclaredCapabilitiesMatchImplementationTest::test_no_static_probe_ever_claims_availability_or_certification` (new) | `statuses_from` does not exist and today's probes emit `"available"` |
| Machine independence | `test_compatibility.py::test_bundle_bytes_are_identical_with_no_binary_and_no_auth` (new) | bundle content is derived from live auth, and a binary-less host writes no bundle at all |
| Declared bundle | `test_compatibility.py::test_bundle_capabilities_equal_exactly_the_declared_implemented_set` (rewritten) | the bundle equals the live available subset, not the declaration |
| Build abort | `test_compatibility.py::BuildFailureTest` (re-specified) | asserts the abort via a live probe premise |
| Probe evidence | `test_host_argv.py::test_probe_host_evidence_names_its_own_path_and_binary` (new) | the record serialises `evidence_path: null`, no `binary_path`, no `certified` |

**(2) Preventive check - PASSES at `68418c5a`, and that is correct.**
`test_helper_provenance_real.py::test_ap00014_rows_are_owned_and_digested_from_current_bytes`
(new, §14) asserts the 13 AP00014 rows are owned by `"00014"` and digest their
current bytes. All 13 already do at the base commit, so **requiring it to
fail-first would be requiring a false failure.** It is the replacement check that
makes §14's `AP00014_TARGETS` exclusion safe, not a regression test.

Demonstrate it binds, instead of demonstrating it fails, in two ways - both are
required evidence for this test:

- **Mid-rework**: run it after the nine adapter/tool files are edited and
  *before* §11's generator run. It must fail there (nine digests stale). That
  failure is the proof it is wired to real bytes, and §11's `AP00014_DIGESTED`
  is what resolves it.
- **Mutation**: with the rework complete, flip one character of one
  `destination_blob_sha256` in a temp copy of the map and confirm the test
  fails against that copy. Never mutate the committed map.

`rules/testing.md`'s fail-first mandate is written for bug fixes; this is a
coverage gap, and the mid-rework failure above is the honest equivalent.

Gate for the cycle, run once at the end, after §11's generator run:

```
uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q
python3 scripts/validate.py
```

Acceptance for this rework: the five named failures are gone, every new and
re-specified test passes, `validate.py` exits 0, and the only remaining failures
are AP00018's controller suites. Phase 2 exit criteria remain unmet for the
reason recorded in `## Risks & edge cases`.

## Review log

dispatch 1 (claude): cardinal-sin 0, blocker 9, non-blocker 5, question 2

Blockers fixed in this revision:

- Shrinking `contracts/hosts.json` breaks `test_sessions.py:138,148` role-resolver tests the design never mentioned - now §15(b), with the replacement assertions verbatim, and a `test_sessions.py` row in `## Module placement`.
- The status demotion makes `test_compatibility.py`'s `REAL_CONTRACT` (`:36-43`) and inline contract (`:160-163`) abort the generator, breaking `RoundTripTest` and `CliInvocationShapeTest` - now §16, which updates both and re-specifies `BuildFailureTest`.
- Returning `capability=None` from `gemini.probe` breaks `GeminiCapabilityContractTest` (`:37,38,42`) - now §15(a), both branches driven by `mock.patch.object(shutil, "which", ...)`.
- The rework stales the 13 hand-added AP00014 digests, which §14's new test asserts and §11 forbids hand-fixing - resolved in §11 by giving the generator ownership through `AP00014_DIGESTED`.
- §14's invariant test contradicted claude's auth-gated `identity` and depended on the developer's env - replaced by §15(c)'s three deterministic tests built on `IMPLEMENTED_CAPABILITIES`, with `mock.patch.dict(os.environ, ..., clear=True)`.
- R11 was not closed: the committed bundles still encoded the builder's auth state - the design was restructured around `IMPLEMENTED_CAPABILITIES` (§2, §7), the exact committed bytes are stated (§8), and §16 tests byte-identity with and without auth. This is now option C against the rejected option B.
- §15's monkeypatch could not reach the generator, which runs in a subprocess - now §16's `_scrubbed_env`, with `PATH=""`, a temp `HOME` (so `codex._AUTH_FILE` is absent) and every auth variable cleared.
- `hosts.unavailable()` silently dropped `reason` - `ProbeResult.unavailable_reason` added (§1) and asserted (§15(a)).
- §12's `tools/` exemption rested on a false claim about the packaged target - the exemption, its justification and its Risks bullet are gone; the Risks section now records not to reintroduce it.

Non-blockers and questions recorded, not fixed:

- `CAPABILITY_STATUSES` would have landed unused - dispatch 2's status rename made it load-bearing instead, so it IS in §1 and §15(c) reads it. The dispatch-1 finding is superseded, not deferred.
- `reason=UNAVAILABLE_UNIMPLEMENTED` duplicated the status string - the constant is not in this revision; `statuses_from` uses `reason=None` for unimplemented (§1).
- §10's `O_EXCL` retry conflicted with the self-identifying evidence path and the single-`os.open` fd handling - addressed in §10 by resolving the filename inside the pinned-fd block before building the payload.
- Snippets omitted needed imports and mixed two call styles for `unavailable()` - import lines are now given per snippet and the call-style rule is stated at the top of `## Interfaces & contracts`.
- The probe-evidence test had no named home - it is now §17, in `test_host_argv.py`, with a `## Module placement` row.
- `doctor`'s user-visible profile flips to `"mixed"` with no test pinning it - recorded in `## Risks & edge cases` with an instruction to add the assertion; deriving the profile properly stays R15/R21, deferred this cycle.
- The PRD's Phase 2 exit gate still fails after this rework - now stated explicitly in `## Risks & edge cases` and in the acceptance line, so no later session reads it as met.

dispatch 2 (codex): cardinal-sin 0, blocker 4, non-blocker 2, question 0

Codex's sandbox refused repository reads (`sandbox_apply: Operation not
permitted`), so its findings judge the doc's internal consistency and its
reasoning against the PRD text, not the real files. Recorded because it changes
what its "checked, correct" silence is worth: it verified nothing against source.
Its four blockers were substantive anyway, and all four are fixed:

- **R9 was overclaimed as closed.** Correct, and the most important finding of
  the cycle. `## Module placement` now splits R9 into the half this rework closes
  (recording and labelling) and the half it must not touch (invoking a host,
  which the PRD forbids here and assigns to AP 00017). §10's line reads
  `Closes in part`, the open dependency on AP 00017 is named in
  `## Risks & edge cases`, and `ProbeResult.certified` plus `probe_kind` put the
  residue in the artifact rather than only in prose.
- **R10 stayed partly open: implemented + authenticated still became
  `"available"`.** Correct - a static probe cannot honestly report availability.
  The status vocabulary is now `supported | unavailable | unimplemented`
  (`CAPABILITY_STATUSES`, §1); `"available"` no longer exists anywhere, claude's
  `interception` included, and §15(c)'s
  `test_no_static_probe_ever_claims_availability_or_certification` pins it over
  both auth states without needing a binary.
- **Gemini's auth state became unobservable.** Correct, and it followed directly
  from the empty `IMPLEMENTED_CAPABILITIES`: both auth states serialised
  identically. `ProbeResult.authenticated` (§1) now records presence for every
  adapter, §4 says so explicitly, and §15(a)'s
  `test_auth_presence_stays_observable_even_with_no_capability_implemented`
  asserts the two states differ.
- **Fail-first was impossible for §14's new integrity test.** Correct: the 13
  rows already digest correctly at the base commit, so demanding a failure there
  demanded a false one. `## Test strategy outline` is now split into regression
  tests (must fail at `68418c5a`) and one preventive check, with two required
  demonstrations for the latter - a mid-rework failure before §11's generator
  run, and a mutated temp copy of the map.

Both non-blockers were fixed rather than deferred, because each left a contract
block unbuildable as written and that block is copied verbatim into the fix
tasks: `_AUTH_VARS` is now defined locally in §17 with a `_SENTINEL` leak check
instead of unsound substring matching against the real environment, and §1's
`__post_init__` makes the `unavailable_reason` guarantee real instead of merely
documented (with the consequent required edit to `test_host_argv.py`'s
unavailable fakes recorded in `## Module placement` and `## Risks & edge cases`).

dispatch 3 (codex): cardinal-sin 0, blocker 2, non-blocker 2, question 0

Verification pass over the revision. It judged all four of dispatch 2's blockers
**resolved**, each with a section citation, and raised two new ones - both
introduced by the revision itself, and both fixed:

- **The contract source gave contradictory status instructions.** Real, and the
  worst kind of defect in a block copied verbatim into fix tasks: §1 both defined
  `CAPABILITY_STATUSES` and carried a leftover paragraph saying no such tuple
  exists, while `## Data flow` still showed `implemented + auth -> "available"`.
  Following the stale half would have made §15(c) raise `AttributeError`. The
  stale paragraph is gone, `## Data flow` reads `"supported"`, and the
  superseded dispatch-1 entry above is corrected.
- **The machine-independence test could pass vacuously.** Real: both builds wrote
  into one root, so a generator that skipped a host left the first run's file in
  place and the byte comparison passed - the exact stale-bundle behaviour §7
  removes. §16 now builds into two fresh roots with controlled environments
  (`_scrubbed_env` and a new `_authenticated_env`) and asserts every bundle
  exists in both before comparing, which also gives the test a definite baseline
  failure.

Both non-blockers were fixed, again because each left a verbatim-copied contract
wrong rather than merely improvable: `__post_init__` now validates `probe_kind`,
`authenticated` and `certified` as the docstring claims (with a required test for
its own rejections, and the available fake at `test_host_argv.py:62-70` updated),
and §10 now describes `binary_path` as an independent second lookup instead of
claiming it identifies the probed executable.

No dispatch 4 was run: the 3-dispatch ceiling is spent. Every cardinal sin and
blocker raised across the three dispatches is fixed in the doc above.

result: ok
