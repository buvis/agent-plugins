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
