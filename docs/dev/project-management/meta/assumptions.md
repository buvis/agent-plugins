# Assumption ledger - AP 00014 (autopilot host execution v1)

Per-plan ledger: replaced at the first completed task of this plan, per the work
skill's assumption-ledger rule.

## 1: Build contracts/hosts.json and scripts/hosts.py capability model

Tess (strengthen after Devon):
- `hosts._ADAPTERS` is a module attribute `probe_host` reads on every call; a
  "fill if empty" lazy import inside `probe_host` would break the empty-table
  test, so the table is assumed to be built once at import/call-site setup.
- The `ValueError` message contains `repr(host_id)` (not a plain `f"...{host_id}"`)
  so empty-string and trailing-space ids stay distinguishable in the text.
- `KeyboardInterrupt` raised by an adapter must reach the caller unchanged, same
  as any other exception.
- `HostCapability.statuses` keeps keys in `CAPABILITY_NAMES` order.

Ivan:
- Adapters (`claude`, `codex`, `gemini`) are imported as top-level sibling
  modules under `plugins/autopilot/scripts/`, the same way the test imports
  `hosts` (via `sys.path` insertion), since they do not exist yet.
- `contracts/hosts.json` did not exist yet; created with the exact content
  given in the design doc excerpt, since no test reads it.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed twice on this
host (`OAuth session expired and could not be refreshed`, then `Session ID ...
is already in use` once the first attempt had consumed the id) — the same
known host quirk recorded in project memory. The attempt record carries
`review: "failed:runner_unavailable"` as the fail-loud marker; the PRD-level
review lenses cover what the per-task reviewer missed.

## 2: Build scripts/claude.py host adapter

Ivan:
- `hosts.py` lives in the same `plugins/autopilot/scripts/` directory and
  exports `CAPABILITY_NAMES`, `CapabilityStatus`, `HostCapability`,
  `ProbeResult`, `UNAVAILABLE_NO_AUTH` exactly as shown in the architecture
  excerpt, importable as `from hosts import ...`.
- `identity`/`delegation`/`isolation` capability status is gated on presence
  of `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` env vars as the "real
  signal" for auth presence (task gave no concrete signal for these three;
  only guided `interception` explicitly). No test exercises these exact
  values, so this doesn't affect pass/fail, only honesty of the static check.
- `session_identity()` uses `CLAUDE_SESSION_ID` env var as the native
  session-id signal (not specified in the given contract; no test exercises
  it).
- `build_job_argv`'s `intent` parameter keeps the literal `"JobIntent"`
  string annotation from the design excerpt without importing/defining
  `JobIntent` (it doesn't exist yet; safe because
  `from __future__ import annotations` defers evaluation).

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk as task 1: `OAuth session expired`,
then `Session ID ... is already in use`). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 3: Build scripts/codex.py host adapter

Ivan:
- Auth detection convention is not specified beyond "env var or config file
  existence check only"; chose `CODEX_API_KEY` env var or `~/.codex/auth.json`
  file existence as the simplest plausible convention. No failing test
  exercises this choice.
- `probe()` does not attempt to read/parse a Codex version string even when
  the binary is found, because getting a real version string without
  `subprocess` isn't possible and the task forbids calling `subprocess`
  anywhere; version info is omitted rather than guessed.
- `build_job_argv()` always returns `None` — `JobIntent` (task 5) isn't
  landed yet and wasn't in the file allowlist, so no role-to-argv mapping
  could be inspected; returning `None` universally is the conservative,
  honest placeholder.
- `identity`/`delegation`/`isolation` capability status for Codex are gated
  together on the same auth check (all available together, or all
  unavailable/no_auth together) since the architecture excerpt gave no
  per-capability distinction for Codex.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 4: Build scripts/gemini.py host adapter and cross-host test_sessions.py

Tess:
- `build_job_argv`'s return contract for gemini is unspecified beyond "same
  four-function surface" as claude/codex; only asserted it doesn't raise and
  returns either `None` or a list.
- `gemini.probe()`'s "identity" capability status itself is unconstrained
  (only delegation/isolation/interception are pinned to never-"available");
  asserted it is one of the three known status strings.
- The resolver helper's candidate pool is restricted to ("codex", "gemini")
  per the task's literal wording; the "claude is never the ONLY host"
  assertion is a logical corollary rather than a resolver that includes
  claude in its own candidate list.
- Per-job_id capability requirements (exactly which capabilities "alice" or
  "carl" need) are not given anywhere in the two contract files, so no such
  mapping was invented; tested the two literal capability subsets the task
  specifies plus the mandatory-job-union check.

Ivan:
- Gemini's auth check uses the `GEMINI_API_KEY` environment variable
  (claude.py/codex.py's exact auth convention were outside the file
  allowlist, so the most common Gemini CLI auth convention was used instead
  of guessing a config-file path).

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 5: Build scripts/jobs.py job-request builder and ControllerSeam protocol

Tess:
- `FakeSeam.submitted_intents` is a public list of the `JobIntent` objects
  passed to `submit_job`, in call order, empty at construction, one per
  instance (not shared across instances).
- `FakeSeam`'s constructor takes one keyword argument, `guard_rules`, shaped
  `{duty: (allowed, reason)}`.
- `FakeSeam.evaluate_guard` returns `{"allowed": True, "reason": None}` for
  a duty with no rule; key matching is exact (no prefix/suffix/case fallback).
- After Devon's strengthen round: `FakeSeam.submit_job` must accept every
  job (`accepted is True`, non-empty string `job_ref`, distinct refs per
  submission on one instance).
- The standalone-mode `intent` in the response is a deep copy — mutating it
  must never change the frozen `JobIntent`.

Ivan:
- `FakeSeam.submit_job`'s `job_ref` format is `"fake-job-<n>"`, counted per
  instance.
- The `RecursionError` message text is free-form; only the exception type
  is pinned by the tests.

Devon (adversarial validation, opus tier): broke the original 27 tests with
8 stacked exploits in one deliberately wrong `jobs.py` (always-rejecting
FakeSeam, first/last-only ancestry scan, host-id guessed from module
`__name__` instead of `HOST_ID`, fabricated argv for codex/gemini ignoring
the real adapter, dropped non-`accepted`/`job_ref` seam-response keys,
class-level shared `submitted_intents`, case-sensitive effort substring
check, shared (non-deep-copied) `inputs`/`policy_constraints` dicts in the
standalone response). Tess strengthened all 8; the real implementation
(Ivan) passes the strengthened 30-test suite cleanly with none of the
exploited shortcuts.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 6: Build scripts/guards.py nine-duty guard library

Orchestrator (this task's own simplification, since the design doc leaves
the exact artifact check unspecified for each pure duty): each pure
`_guard_<duty>` function decides `allowed` from one caller-supplied key,
`context.get("ok", True)` (`is False` check) - deny with reason
`f"{duty.value}_check_failed"`, else allow with reason `None`. This is
deliberately not real artifact probing (reading a file, checking git
state); the PRD ships the guard library only, not real interception wiring.

Tess / Ivan:
- A pure guard denies only when `ok` is exactly `False` (`is False`); a
  missing `ok` key or any other value allows.
- The seam is called with `duty.value` (a plain str), matching
  `jobs.ControllerSeam.evaluate_guard(duty: str, ...)`.
- `run_guard` must never mutate the caller's context dict (not stated by
  the contract, but implied by "thin wrapper that forwards context
  verbatim").
- A member's name string (e.g. "CUSTODY_PUSH") counts as "not a GuardDuty
  member" - duties are identified by their StrEnum VALUE, not their name.
- Unknown-duty rejection raises one of `(ValueError, KeyError)` - the
  contract does not pin the exact type.

Devon (adversarial validation, opus tier): broke the original 25 tests with
8 stacked exploits (hardcoded per-duty denial reasons ignoring the seam's
actual reason, dropped non-prd/branch context keys, mutated the caller's
context after the call, a stateful duty that let `context["ok"]` override
the seam's allow verdict, a pure guard that accepted a `seam` under the
name `controller=None` and called `submit_job` on it without detection,
StrEnum/str identity confusion in outcome comparisons, and case-insensitive
duty-name lookup). Tess strengthened all 8; the real implementation (Ivan)
passes the strengthened 27-test suite cleanly with none of the exploited
shortcuts.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 7: Build scripts/doctor.py and wire hosts/guards/diagnose modes into autopilot.py

Ivan:
- `profile` is `"claude-free"` whenever the union of codex's and gemini's
  declared capabilities (from `contracts/hosts.json`) is non-empty (always
  true today), else `"mixed"` - a live comparison against the contract
  file, never a hardcoded string.
- `diagnose()` passes an empty `{}` context to every guard duty.
- The two new CLI modes beyond `--diagnose` (`--probe-host HOST_ID
  --project-root PATH`, `--run-guard DUTY --context PATH`) have no pinned
  exact invocation form in the task contract; kept as small as the
  existing `_catchup_probe` shape, with `--context` reusing the existing
  `_read_json`/`_INPUTS` live-state-path refusal.
- `--run-guard` passes `seam=None` (no CLI flag exists for binding a real
  `ControllerSeam` - AP00016's job); a stateful duty therefore always
  refuses with `"missing_controller_seam"` through this CLI path today,
  which is correct per the guard contract, not a shortcut.

Orchestrator: this task's three new `_CAPABILITIES` entries changed
`--list-capabilities`' output, which a pre-existing test
(`tests/autopilot/test_facade.py::test_capabilities_are_exact_contract_formats_without_runtime_side_effects`)
hardcoded as an exact list. Fixed by adding `"hosts-v1"`, `"guards-v1"`,
`"diagnose-v1"` to that test's `HELPER_OPERATIONS` constant - a minimal,
in-scope fix for a regression this task's own change caused, even though
`test_facade.py` was not in this task's `files` list.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 8: Build tools/autopilot/probe-host.py maintainer CLI

Ivan:
- `sys.path` insertion resolves `plugins/autopilot/scripts` via
  `Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot" / "scripts"`
  from `tools/autopilot/probe-host.py`'s own location, matching the
  `tests/autopilot/*.py` pattern.
- The evidence write uses `O_TRUNC` (review_stage.py `_write`'s flags)
  rather than `O_EXCL`, so a probe re-run at the same host_id within the
  same UTC second does not crash.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.

## 9: Build tools/autopilot/build-compatibility.py and generate compatibility bundles

Tess: the bundle JSON schema (field names) is unpinned by the task; tested
via a schema-agnostic recursive scan over the parsed JSON (collects every
leaf string matching a known capability name) rather than asserting a key
name, so the test checks the substantive claim without inventing a
contract.

Ivan: bundle schema is `{"host_id": str, "capabilities": [str, ...]}` -
the simplest shape satisfying the schema-agnostic test. Dispatch goes
through `hosts.probe_host(host_id, ...)` generically rather than importing
each adapter module directly.

Orchestrator: added a `probe_result.capability is None` guard before
`.statuses` in the implementor's draft - without it, any declared host
whose probe returns `available=False` (binary missing - a real,
documented `ProbeResult` shape) would crash the ENTIRE build, not just
skip that one host. None of this environment's adapters trigger it today,
but it is real documented behavior worth guarding defensively at a real
system boundary (external probe result), not speculative.

Orchestrator: the `sonnet-run.sh` reviewer lane (step 5.7) failed again on
this host (same known runner/auth quirk). `review: "failed:runner_unavailable"`
recorded on the attempt; PRD-level review lenses cover it.
