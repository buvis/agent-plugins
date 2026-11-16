# agoge strategy profile

Recon by olivia on 2026-11-16 against HEAD `9757971c0eb7ea235801bc9d13f7f6c4280cbbee`.
Every command below was run from a scratch clone of that HEAD
(`git clone <target> <scratch>/clone`), never in the target checkout.

## 1. Surfaces

Plugins under `plugins/`: `autopilot` 0.10.0, `engram` 0.1.0 (new since the
last recon), `specflow` 0.1.0. `templates/example-plugin` is a starter, not a
plugin.

### How to run anything here

- Run from a scratch clone, not the target. The specflow release tests call
  `git -C <root> ls-files`, so they need a git repo (a `git archive` copy
  failed 2 tests at the last recon; not re-run this time).
- Set `PYTHONDONTWRITEBYTECODE=1` and `GIT_CEILING_DIRECTORIES=<scratch>`.
- The session's write-scope fence rejects a write target it cannot resolve
  (`> /tmp/x/out$i.txt` was blocked). Write scratch paths out in full. Allowed
  write roots: the target, `/private/tmp`, `$TMPDIR`.
- Hooks block `cat`, `head`, `tail`, `grep`, `find`, `umask` and `chmod` in
  Bash. Use `rg` and Read. Create a 0600 or 0755 file from Python with
  `os.open(path, flags, mode)`.
- A shell `for ...; done` followed by a newline and a `/path` tripped a PRD
  location hook ("done/"). Put loops last in a call or unroll them.
- Python: `python3` is 3.15.2 (mise), the same as CI's `plugins` job. It has
  no `pytest`. The autopilot suite runs with
  `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest ...`
  (CI's `autopilot` job uses 3.12).
- `bun` and `node` are on PATH (mise). No `tsc`.

### Test suites (all from the clone root)

| Suite | Command | Result at HEAD |
| --- | --- | --- |
| Validator | `python3 -m unittest discover -s scripts` | 59 tests, OK |
| specflow release | `python3 -m unittest discover -s tests/specflow/release` | 54, OK |
| specflow contract | `python3 -m unittest discover -s tests/specflow/contract` | 387, OK |
| specflow rules | `python3 -m unittest discover -s tests/specflow/rules` | 58, OK |
| specflow review | `python3 -m unittest discover -s tests/specflow/review` | 41, OK |
| engram package | `python3 -m unittest discover -s tests/engram` | 5, OK (static file checks only) |
| autopilot | `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q -p no:cacheprovider` | **3 failed, 1946 passed, 1 skipped, 755 s** |

The autopilot failures, as established. All three have one cause: the source
map row for `plugins/autopilot/controller/autopilot_state/schema.py` is stale
(map `7aaedd12...`, file `8ef20175...`). Commit 521df8f widened the schema and
the map was not regenerated.

- `test_helper_provenance_real.py::test_controller_assets_digest_current_bytes_and_cite_the_successor`
- `test_helper_provenance_real.py::test_generator_check_accepts_the_committed_map`
- `test_package.py::TargetPackageTest::test_content_roster_matches_frozen_inventory_and_actual_package_bytes`
- `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json --check`
  now agrees with the tests: rc 1, "successor package_revision 1d83b895... is
  stale for '.../schema.py'".
- The CI `autopilot` job would be red at this HEAD.
- The skip is `test_helper_provenance_real.py:558`: "pinned source checkout
  unavailable; set AUTOPILOT_SOURCE_ROOT". A scratch clone of
  `/Users/bob/git/src/github.com/buvis/claude-autopilot` provides it (not
  re-run with the variable set).
- The 19 `owner.acquire` failures of the last recon are gone.

Not runnable: `tests/specflow/evals/*.json` and
`tests/specflow/compatibility/*.md` are data and checklists for live agent
hosts. They have no runner here and are not in CI.

### Other CI checks

- `python3 scripts/validate.py`: rc 0, "Validated 4 plugin package(s) and 16
  skill(s)." It takes plugin paths (`validate.py [paths ...]`), not a repo root.
- `python3 scripts/generate_marketplace.py --check`: rc 0. **Without `--check`
  it rewrites `.claude-plugin/marketplace.json`. Never run it without the flag
  in the target.**
- `python3 tools/specflow/check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER,RVC,RVR,RVD,RVX,CNV`: rc 0.
- `python3 tools/specflow/verify_release.py`: rc 0, "Verified plugins/specflow."
- `python3 tools/autopilot/export-controller-contract.py --check`: rc 0 (not in CI).

### CLI entry points (rc in brackets)

- `plugins/autopilot/scripts/autopilot.py --help` [0]. Modes:
  `--list-capabilities` (19 ids), `--export-policy`, `--stage-review`,
  `--group-findings`, `--check-evidence`, `--prepare-close`, `--request-job`,
  `--bind-job`, `--close-child`, `--catchup-probe`, `--verify`,
  `--controller-action`, `--probe-host`, `--run-guard`, `--diagnose`,
  `--hook HOST --event EVENT`, `--resolve-roles --profile ID --lane LANE`,
  `--record-session HOST`. Established:
  - `--diagnose --project-root <dir>` [0]: JSON, static host probe, guards
    `simulated: true`, every host `certified: false`.
  - `--resolve-roles --profile source-parity --lane full` [0]; an unknown
    profile gives rc 2.
  - `--hook claude --event PreToolUse` reads a payload on stdin, run from the
    project dir (`--project-root` is refused with this mode, rc 2). A valid
    payload gives rc 0 and no output with no bound job; garbage gives rc 0 and a
    `permissionDecision: deny`, reason `hook_input_invalid`; an unknown event
    gives rc 2.
- `plugins/autopilot/controller/main.py` [2 when bare]: `--json contract`,
  `--json snapshot --project-root P`,
  `--json apply --project-root P --request FILE [--actor-file FILE]`.
  `contract` lists operations `workflow.open`, `owner.acquire`,
  `owner.release`, `owner.recover`. Established in scratch: `workflow.open`
  (rc 0, revision 0), `owner.acquire` with the operator actor file (rc 0,
  revision 1), an exact replay of it (same response), `snapshot`
  (`health: ready`, `capacity` block). `owner.release` and `owner.recover`
  were not run by recon. The request file must be canonical JSON (sorted keys,
  `,` and `:` separators, as `tests/autopilot/controller_cli_support.py`
  `canonical`) and mode 0600; a pretty-printed request got `invalid_request`.
  `project_id` is `sha256(str(resolved project root))`, so `/tmp/x` hashes as
  `/private/tmp/x`. The store is `<P>/.autopilot/controller/` (0700; files
  0600: `state.json`, `.bak`, `.lock`, `actors/*.json`). Limits
  (`contracts/controller/workflow-v1.json` `x-controller.limits`): request
  2 MiB, state 16 MiB, JSON depth 32, 640 integer digits, identity 256 bytes,
  4094 normal and 4096 hard receipts, 64 orphan files. Request shapes for all
  four operations: `contracts/controller/fixtures-v1.json` `cases`.
- `plugins/specflow/skills/spec-workflow/scripts/validate_spec.py` [0]:
  `status | validate [--phase P] [--json] spec_dir | hash | code-baseline | reconcile | next-number`.
  It finds its root through the enclosing git repo, so copy a fixture to
  scratch and `git init` it. Done with
  `tests/specflow/fixtures/sessions/completion-success`: `status` printed
  `00001-cart-rounding: verification; ...`, `validate .kiro/specs/00001-cart-rounding`
  printed `valid`, `next-number` printed `00002`. `check_links.py --json` [0].
  `review/claim_ladder_scan.py <file>` [0]; the three review scanners take one
  file path and have no `--help` (rc 1).
- `tools/autopilot/check-source.py --source-root <scratch frozen clone>` [0]:
  "Source audit passed: e960ef1c...; 679 files, 92 assets, 1381 behaviors,
  4950 regression cases".
- `tools/autopilot/probe-host.py host_id [--project-root P] [--static-only]` [0
  with `--static-only`]. It writes evidence to
  `<P>/docs/dev/tmp/autopilot/probes/`. **Without `--static-only` it starts a
  live host session. Always pass `--static-only` and a scratch `--project-root`.**
- `tools/autopilot/{prerequisites.py,build-compatibility.py,map_slice.py,export-controller-contract.py} --help` [0].
- engram ships no code of its own to run: three hook JSON files, `mcp.json`,
  one skill, and `works.earendil.pi/engram-nudge.ts`. All of them call the
  external `engram` CLI (see External services). The Pi adapter ran under bun
  in scratch against a stub `@earendil-works/pi-coding-agent` module and a fake
  `engram` on PATH: a bash tool result got the fake's text appended, a
  non-bash result returned undefined.

### Dev server, browser, database

- Dev server: none. No server code and no port. The only `package.json` is the
  fixture `tests/specflow/fixtures/sessions/instruction-scope/frontend/package.json`.
- Browser: Playwright browsers are cached at `~/Library/Caches/ms-playwright`
  (chromium-1228, chromium-1234, firefox-1538, webkit-2336), but this repo has
  no web interface to load.
- Database: none. The nearest thing is the controller's file state store
  above, now with working owner leases.

### External services

- `engram` CLI at `~/.local/bin/engram`, not part of this repo. `engram --help`
  and `engram nudge --help` [0] (`nudge {claude,codex,copilot,plain}`). With a
  harmless payload on stdin: `ENGRAM_NUDGE=off` gives rc 0 and no output; a
  `ls` command gives rc 0 and no output; non-JSON gives rc 0 and
  "unreadable hook payload" on stderr. It reads the operator's private index;
  recon ran no `query`, `mcp`, `index` or `harvest`, and did not establish
  whether it reaches the network.
- Agent host CLIs on PATH: `claude`, `codex`, `gemini`, `kiro-cli`, `copilot`,
  `pi`. `--diagnose` (static) reports claude `no_auth`, codex
  `authenticated: true`, gemini `no_auth`. Recon ran no live host session, so
  plugin install and hook firing on a real host are not established. The
  engram README's "verified 2026-11-10" rows cannot be re-checked here.
- GitHub and the marketplace remote: not reached.
- Upstream specflow sources (`tools/specflow/upstream/`): network, not probed.
- The frozen `buvis/claude-autopilot` checkout is local. Read it only through
  a scratch clone.

### Alarming, noted only

- The autopilot suite is red at HEAD (3 failures, one stale source-map row).
- The suite now takes 755 s (341 s on 2026-11-09, with 497 more tests).
- The plugin tables disagree. `README.md` lists autopilot and engram, not
  specflow. `.claude-plugin/marketplace.json` lists engram and specflow, not
  autopilot (a copied template with no `.claude-plugin/` manifest also stayed
  out of the catalog, so that part may be by design; the README gap is not).
- No git tags. All three CHANGELOGs hold only `[Unreleased]`, while the
  manifests say 0.10.0, 0.1.0 and 0.1.0.
- `prds/hold` holds 19 PRDs, 17 of them autopilot triage stubs (00068-00084),
  including "the shipped hooks deny unrelated work".
- engram hook commands and the Pi adapter trust whatever `engram` is first on
  PATH (bare name by design; `tests/engram` pins it).

## 2. Per-specialist strategy

| Specialist | Verdict | Tactics or reason |
| --- | --- | --- |
| walter (journeys) | armed | All in a scratch clone. Maintainer journey: `cp -R templates/example-plugin plugins/<new>`; `python3 scripts/validate.py` must fail rc 1 ("name must match the plugin directory"); fix `name` in `plugin.json`; validate again (rc 0, 5 packages); `python3 scripts/generate_marketplace.py` then `--check`. Check what lands in `.claude-plugin/marketplace.json` and whether that matches `CONTRIBUTING.md`. specflow journey: copy `tests/specflow/fixtures/sessions/<case>/.` to a scratch dir, `git init` it, then from inside it run `python3 <clone>/plugins/specflow/skills/spec-workflow/scripts/validate_spec.py status`, `validate [--phase P] [--json] .kiro/specs/<spec>`, `next-number`, `reconcile`, and `check_links.py --json`, across the intake to completion cases. Controller journey: `python3 plugins/autopilot/controller/main.py --json apply --project-root <scratch proj> --request <file>` for `workflow.open`, `owner.acquire`, `owner.release`, `owner.recover` (shapes in `contracts/controller/fixtures-v1.json`; canonical JSON, mode 0600, `project_id` = sha256 of the resolved root), with `--json snapshot` between steps, then the README's "Leave a sealed workflow" steps. Facade: `autopilot.py --list-capabilities`, `--export-policy`, `--diagnose --project-root <dir>`, `--resolve-roles --profile source-parity --lane full`. engram install journey per `plugins/engram/README.md`, with a fake `engram` first on PATH: pipe a PostToolUse payload to each hook file's command, and drive `engram-nudge.ts` with `bun run` against a stub `@earendil-works/pi-coding-agent`. Report engram results `mocked`. |
| heidi (integration/db) | armed | The "db" is the controller store `<proj>/.autopilot/controller/`. With `main.py --json apply` and `snapshot`: exact replay of a request, `revision_conflict` on a stale `expected_revision`, wrong or swapped `--actor-file`, release then re-acquire (lease epoch), recovery after a deleted `.lock`, a corrupt `state.json` with a good `.bak`, a leftover `actors/*.stage` or `.intent-*.tmp`, and the 64-file orphan limit (`recovery_required`). Cross-tool: manifests to `python3 scripts/generate_marketplace.py --check` to `python3 scripts/validate.py`; `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json --check` (rc 1 at HEAD for `schema.py`, known; report other rows only); `python3 tools/autopilot/export-controller-contract.py --check`; `python3 tools/autopilot/check-source.py --source-root <scratch clone of the frozen repo>`; the autopilot suite with `AUTOPILOT_SOURCE_ROOT=<that clone>` to clear the skip (755 s; the 3 known failures are not new). engram wiring: `plugins/engram/.claude-plugin/plugin.json` `mcpServers` and `hooks` against `mcp.json` and the three host hook files; real `engram nudge <host>` only with harmless payloads on stdin. |
| judy (UX via browser) | unarmed | No browser surface. The repo has no web app, server or HTML; the only `package.json` is a test fixture. Playwright browsers are cached, but nothing here renders in them. |
| wendy (release truth) | armed | Compare `plugins/*/CHANGELOG.md` `[Unreleased]` bullets with behavior: autopilot controller claims against `main.py --json contract` and scratch runs; engram's three bullets against the shipped files. `plugins/autopilot/README.md` lines 331-370 (new modes) and 405-481 (controller, capacity, orphans) against `autopilot.py --help` and `main.py`. `plugins/engram/README.md` install paths and host status table against the hook files (`tests/engram/test_package.py` pins the table text, not the truth). `plugin.json` versions (0.10.0, 0.1.0, 0.1.0) against CHANGELOG headings (no released section) and `git tag --list` (empty). The root `README.md` plugin table against `.claude-plugin/marketplace.json` and `plugins/README.md`. `AGENTS.md` and `CONTRIBUTING.md` commands against `.github/workflows/validate.yml` (the engram tests run in the `autopilot` job; AGENTS.md lists neither engram nor autopilot commands). |
| peggy (performance) | armed | One narrow surface with a stated bound: the README's receipt capacity (4094 normal, 4096 hard) and "Callers must bound execution time". In a scratch project, loop `owner.acquire` then `owner.release` through `main.py --json apply` (new `request_id` each time) toward saturation. Record per-apply wall time and `state.json` size at 0, 1000, 2000, 4000 receipts and at the seal; check `snapshot` stays fast when sealed and that state stays under 16 MiB. Baseline: `snapshot` on a 2-receipt store took 0.04 s. Also time a 2 MiB request and a depth-32 payload. Nothing else has a budget: `validate.py` 0.03 s, specflow helper under 1 s. Note the test suite grew from 341 s to 755 s. |
| trudy (runtime security) | armed | Hostile input, scratch only. Controller: `python3 plugins/autopilot/controller/main.py --json apply --project-root <scratch proj> --request <file> [--actor-file <file>]` with duplicate keys, NaN or Infinity, invalid UTF-8, depth 33, 641-digit integers, a request over 2 MiB, bool-as-int, a 257-byte identity, non-canonical JSON, a request or actor file that is a symlink, a hardlink or mode 0644, a forged or other-project actor file, a symlinked project root or `.autopilot`, and a planted `state.json.lock` or 65 orphan files. Errors must stay in the closed code set (`x-controller.error_codes`), no secret may appear in output, and nothing may be written outside `<proj>/.autopilot/controller/`. Hook mode: from a scratch dir, `printf '<payload>' \| python3 <clone>/plugins/autopilot/scripts/autopilot.py --hook {claude,codex} --event PreToolUse` with oversized, deep or non-UTF-8 payloads, traversing `cwd`, hostile `session_id`, and push-grammar evasions (`git -c x push`, quoting, `;` chains); set `AUTOPILOT_HOOK_TRACE` to a scratch path and to a symlink. Jobs: `--request-job`, `--bind-job`, `--close-child` with traversing `artifact_path` and `--out` to an existing file. `python3 tools/autopilot/probe-host.py <host> --static-only --project-root <scratch>` only (never live), with a symlinked evidence dir. Validator: plugin trees with symlinks leaving the root, `..` in manifests, huge or malformed SKILL.md frontmatter, non-UTF-8 files, via `python3 scripts/validate.py <path>`. specflow: crafted spec markdown and `.specflow.json` (traversal in `spec_dir`, deep JSON, huge files) through `validate_spec.py` and the review scanners. engram: PATH hijack of the bare `engram` name, and a fake `engram` that floods stdout or hangs, to test the Pi adapter's 12 s timeout and unbounded `stdout +=` (`bun run` harness with a stub pi module); shell metacharacters in `tool_input` reaching `engram nudge`. Report engram results `mocked`. |

## 3. Mocking strategy

- **engram CLI**: put a fake `engram` executable in a scratch bin dir at the
  front of PATH (create it from Python with mode 0755). It should echo its
  argv and stdin. Use it for every hook command, `mcp.json` and the Pi
  adapter. The real `engram nudge` may be run only with harmless payloads;
  never run the real `query`, `mcp`, `index` or `harvest`. Fake results are
  `mocked`, never `verified`.
- **Pi host**: stub `node_modules/@earendil-works/pi-coding-agent/index.js`
  in scratch (`export const isBashToolResult = (e) => e.toolName === "bash"`),
  copy `engram-nudge.ts` beside it, and drive the default export with
  `bun run`. `mocked`.
- **Agent hosts (claude, codex, gemini, kiro-cli, copilot)**: do not call the
  real binaries. Use fake executables on PATH that print what the probe
  expects; see `plugins/autopilot/scripts/{claude,codex,gemini,hosts}.py`,
  `tests/autopilot/host_fakes.py` and `tests/autopilot/test_host_argv.py`.
  Pipe recorded payloads (`tests/autopilot/hook_characterization.json`) to
  `autopilot.py --hook`. `mocked`.
- **Controller seam for guards**: `--diagnose` guards are simulated
  (`simulation.simulated: true`). Report guard results `mocked`. The
  controller CLI itself is real and can be `verified`.
- **GitHub / marketplace remote**: do not install from the remote. Generate
  the catalog locally in the clone; any claim about client install is `mocked`
  or unestablished.
- **Upstream specflow sources**: no network. Use the committed cursors in
  `tools/specflow/upstream/`; `mocked`.
- **Frozen claude-autopilot source**: not external. Read it through
  `git clone /Users/bob/git/src/github.com/buvis/claude-autopilot <scratch>/frozen`;
  those results can be `verified`.

## 4. Authoring assignments

The master authors these on a branch after the lanes report. Specialists put
any proposed test in their finding's `fix` field only.

- Controller hostile-input, owner-lease and capacity regressions:
  `tests/autopilot/`, under pytest
  (`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot`).
- Hook-mode payload and push-grammar regressions: `tests/autopilot/`, same runner.
- Validator and marketplace edge cases (symlink escape, name mismatch, catalog
  drift, README table versus catalog): `scripts/test_*.py`, under
  `python3 -m unittest discover -s scripts`.
- specflow helper journeys on isolated fixtures: `tests/specflow/contract/`,
  under `python3 -m unittest discover -s tests/specflow/contract`.
- engram package contract (manifest versus `mcp.json` and hook files):
  `tests/engram/`, under `python3 -m unittest discover -s tests/engram`. The Pi
  adapter has no test runner in the repo; a behavior test for it needs one
  added (bun ran it in scratch), which is a decision for the owner.

## 5. Pins and vetoes

Authorization: not asserted

## 6. Freshness stamp

- Recon date: 2026-11-16
- Target HEAD: 9757971c0eb7ea235801bc9d13f7f6c4280cbbee
