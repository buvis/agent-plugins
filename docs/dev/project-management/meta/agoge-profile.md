# agoge strategy profile

Recon by olivia on 2026-11-09 against HEAD `0c5c47debc37cfeaa0f9010acbd072864f195f9e`.
Every command below was run from a scratch clone of that HEAD
(`git clone <target> <scratch>/clone`), never in the target checkout.

## 1. Surfaces

### How to run anything here

- Run from a scratch clone, not the target. The specflow release tests call
  `git -C <root> ls-files`, so a `git archive` copy fails 2 of 54 tests with
  git exit 128; a clone passes them all.
- Set `PYTHONDONTWRITEBYTECODE=1` and `GIT_CEILING_DIRECTORIES=<scratch>`.
- The session's autopilot write-scope fence rejects `$VAR` write targets
  (`mkdir "$SCRATCH/x"` was blocked). Write every scratch path out in full.
  Allowed write roots: the target, `/private/tmp`, `$TMPDIR`.
- Python: `python3` is 3.15.2 (mise), the same as CI's specflow job. It has no
  `pytest` and no `jsonschema`. The autopilot suite runs with
  `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest ...`.
  (uv: `mise which uv`; CI's autopilot job uses 3.12.)

### Test suites (all from the clone root)

| Suite | Command | Result at HEAD |
| --- | --- | --- |
| Validator | `python3 -m unittest discover -s scripts` | 59 tests, OK |
| specflow release | `python3 -m unittest discover -s tests/specflow/release` | 54, OK (needs a git repo) |
| specflow contract | `python3 -m unittest discover -s tests/specflow/contract` | 387, OK |
| specflow rules | `python3 -m unittest discover -s tests/specflow/rules` | 58, OK |
| specflow review | `python3 -m unittest discover -s tests/specflow/review` | 41, OK |
| autopilot | `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q -p no:cacheprovider` | **20 failed, 1432 passed, 1 skipped, 341 s** |

The autopilot failures, as established:

- 19 are in `test_controller_capacity.py` (8), `test_controller_owner.py` (7)
  and `test_controller_owner_recovery.py` (4). They all fail at
  `owner.acquire`. The controller returns
  `{"error_code":"missing_capability",...}` with rc 1, because
  `autopilot_state/protocol.py` accepts only `workflow.open`
  (`controller/main.py --json contract` lists `"operations":["workflow.open"]`).
  These tests are ahead of the implementation. That matches commit 169a520
  ("stall 00014 at the rework cap with an unresolved CRITICAL"). The CI
  `autopilot` job would be red at this HEAD.
- 1 is `test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes`.
  The source-map digest for `plugins/autopilot/CHANGELOG.md` is stale
  (map `a478a34b...`, file `35836377...`). But
  `python3 tools/autopilot/update_helper_map.py --map tools/autopilot/source-map.json --check`
  exits 0, so the two checks disagree.
- The skip is at `test_helper_provenance_real.py:378`: "pinned source checkout
  unavailable; set AUTOPILOT_SOURCE_ROOT". A scratch clone of
  `/Users/bob/git/src/github.com/buvis/claude-autopilot` provides that checkout.

Not runnable: `tests/specflow/evals/*.json` (SR-* eval cases) and
`tests/specflow/compatibility/*.md` are data and checklists for live agent
hosts. They have no runner in this repo and are not in CI.

### Other CI checks (all pass at HEAD)

- `python3 scripts/validate.py`: "Validated 3 plugin package(s) and 15 skill(s)." Takes paths (`validate.py [paths ...]`).
- `python3 scripts/generate_marketplace.py --check`: up to date. **Without
  `--check` it rewrites `.claude-plugin/marketplace.json`. Never run it
  without the flag in the target.**
- `python3 tools/specflow/check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER,RVC,RVR,RVD,RVX,CNV`: rc 0.
- `python3 tools/specflow/verify_release.py`: "Verified plugins/specflow."

### CLI entry points (`--help` or a bare run, rc in brackets)

- `plugins/autopilot/scripts/autopilot.py` [0]: facade with `--list-capabilities`,
  `--export-policy`, `--stage-review`, `--group-findings`, `--check-evidence`,
  `--prepare-close`, `--catchup-probe`, `--verify`, `--controller-action`,
  `--probe-host`, `--run-guard`, `--diagnose`. `--list-capabilities` lists 13
  capability ids. `--diagnose --project-root <clone>` prints JSON host and guard
  status. Its guards run on a FakeSeam (`guards_simulated: true`, stated in
  `doctor.py`). `tools/autopilot/export-policy.py` exposes the same parser.
- `plugins/autopilot/controller/main.py` [2 when bare: "invalid controller arguments"]:
  `--json contract`, `--json snapshot --project-root P`, and
  `--json apply --project-root P --request FILE [--actor-file FILE]`.
  `snapshot` on an empty scratch dir returns `health: absent`. Limits are in
  `contracts/controller/workflow-v1.json` `limits`: request 2 MiB, state
  16 MiB, JSON depth 32, 640 integer digits, 4096 receipts. It rejects
  duplicate keys and nonfinite numbers. It refuses Python < 3.12 with
  `incompatible_contract`.
- `plugins/autopilot/scripts/doctor.py` [0, no output with `--help`]: a
  library behind `--diagnose`, not a CLI.
- `plugins/specflow/skills/spec-workflow/scripts/validate_spec.py` [0]:
  `status | validate [--phase P] [--json] spec_dir | hash | code-baseline | reconcile | next-number`.
  It finds its root through the enclosing git repo. Run from a fixture
  directory inside the clone, `status` reported the clone's own
  `docs/dev/project-management/specs`, not the fixture's `.kiro/specs`.
  Copied to `<scratch>/fx` with its own `git init`, `status` reported the
  fixture's spec and `validate .kiro/specs/00001-cart-rounding` printed
  `valid`. Fixtures live in `tests/specflow/fixtures/{sessions,specs,state,cross-spec,kiro,recovery,sketch}`.
- `.../scripts/check_links.py [--root R] [--json]` [0].
- `.../scripts/review/{adversarial_signal_scan,claim_ladder_scan,section_weight_audit}.py` [1 with `--help`: "error: not a file: --help"]. They take a file path as the only argument and have no help.
- `tools/autopilot/check-source.py --source-root <frozen clone>` [0]:
  "Source audit passed: e960ef1c...; 679 files, 92 assets, 1381 behaviors,
  4950 regression cases" (run against a scratch clone of the frozen repo).
- `tools/autopilot/{prerequisites.py --prd P, probe-host.py host_id, build-compatibility.py, map_slice.py {show,apply}, update_helper_map.py}` [0 with `--help`].

### Dev server, browser, database

- Dev server: none. No server code, no port, no `package.json` except the
  test fixture `tests/specflow/fixtures/sessions/instruction-scope/frontend/package.json`.
- Browser: Playwright browsers are cached at `~/Library/Caches/ms-playwright`
  (chromium-1243 and others), but this repo has no web interface to load.
- Database: none. The nearest thing is the autopilot controller's file-backed
  state store (`<project>/.../state.json` with `.lock`, fsynced backup, and
  credential-intent files) behind `controller/main.py`. Only `workflow.open`
  and `snapshot` work at HEAD.

### External services

- Agent host CLIs are on PATH: `claude` (`~/.local/bin`), `codex` (mise),
  `gemini` (mise npm), `kiro-cli`. `--diagnose` (static probe, no network)
  reports claude `no_auth`, codex `authenticated: true`, gemini unauthenticated.
  Recon did **not** run any live host session. That costs money and needs
  auth, so live plugin install and execution on a host is not established.
- GitHub: consumers install through the marketplace and the remote. Recon did
  not reach it.
- Upstream specflow sources (`tools/specflow/upstream/sources.md`, used by the
  maintainer catch-up skill): network, not probed.
- The frozen `buvis/claude-autopilot` checkout exists locally. Read it only
  through a scratch clone (the repo is frozen).

### Alarming, noted only

- The autopilot suite is red at HEAD (20 failures, above).
- The provenance digest for `plugins/autopilot/CHANGELOG.md` is stale, while
  `update_helper_map.py --check` reports clean.
- The plugin tables disagree. `README.md` lists only autopilot 0.10.0;
  `.claude-plugin/marketplace.json` lists only specflow 0.1.0. AGENTS.md says
  to update the README table when a plugin is published.
- No git tags exist. Both plugin CHANGELOGs hold only `[Unreleased]`, while
  the manifests say 0.10.0 and 0.1.0.

## 2. Per-specialist strategy

| Specialist | Verdict | Tactics or reason |
| --- | --- | --- |
| walter (journeys) | armed | Maintainer journey in a scratch clone: copy `templates/example-plugin` to `plugins/<new>`, then run `python3 scripts/validate.py`, `python3 scripts/generate_marketplace.py` (in the clone only), and `--check`. Check that the new plugin lands in the catalog and that a broken manifest, a name/dir mismatch, or a symlink escaping the root fails the validator. specflow user journey: copy a fixture from `tests/specflow/fixtures/sessions/*` to an isolated scratch dir, `git init` it, and run `validate_spec.py status`, `validate --phase <p> --json`, `next-number`, `reconcile`, and `check_links.py --json` through intake to complete. autopilot facade journey: `autopilot.py --list-capabilities`, `--export-policy`, `--diagnose --project-root <dir>`, then `--stage-review`, `--check-evidence` and `--prepare-close` on artifacts built from the fixtures in `contracts/review-fixtures-v1.json`. |
| heidi (integration/db) | armed | The "db" is the controller's file state store. Run `controller/main.py --json apply` with `workflow.open`, then `snapshot`, then replay the same request. Check exact replay, revision_conflict, and recovery after a deleted `.lock` or a corrupt `state.json` or credential-intent file. Note that owner.* returns `missing_capability` at HEAD; report it, do not count it as a new defect. Cross-tool integrations: plugin manifests to `generate_marketplace.py --check` to `validate.py`. `tools/autopilot/update_helper_map.py --check` versus `test_helper_provenance_real.py` (they disagree at HEAD). `check-source.py --source-root <scratch frozen clone>`. The autopilot suite with `AUTOPILOT_SOURCE_ROOT=<scratch frozen clone>` to clear the one skip. |
| judy (UX via browser) | unarmed | No browser surface. The repo has no web app, server, or HTML; the only `package.json` is a test fixture. Playwright browsers are cached, but nothing here renders in them. |
| wendy (release truth) | armed | Compare `plugins/*/CHANGELOG.md` `[Unreleased]` bullets with the behavior: for example, the controller CHANGELOG claims (bounded CLI, exact replay, snapshots, credential-intent recovery) against `controller/main.py` runs. Compare `plugins/autopilot/README.md` CLI docs (line 263 `--verify ... -- ARGV...`) with `autopilot.py --help`. Compare plugin.json versions (0.10.0, 0.1.0) with the CHANGELOG headings (no released sections) and `git tag --list` (empty). Compare the README plugin table with `marketplace.json` (they disagree). Compare the specflow `.claude-plugin/plugin.json` with `plugin.json` (both 0.1.0). Compare `AGENTS.md`/`CONTRIBUTING.md` commands with what CI runs (`.github/workflows/validate.yml`). |
| peggy (performance) | unarmed | No stated latency or throughput budget in the READMEs. Every CLI finishes well under 1 s at real size (`validate.py` 0.03 s, `validate_spec.py status` 0.26 s, `--diagnose` 0.03 s). The capacity-bound controller paths (receipt counts, the 16 MiB state) need `owner.*`, which returns `missing_capability` at HEAD, so there is nothing to load. Parse cost of hostile input belongs to trudy. |
| trudy (runtime security) | armed (surface) | Hostile-input probing in scratch only. Controller: `controller/main.py --json apply --project-root <scratch proj> --request <file>` with duplicate keys, NaN or Infinity, invalid UTF-8, nesting at depth 33 and above, 641-digit integers, oversized requests (more than 2 MiB), bool-as-int, symlinked or hardlinked request, actor, or state files, a world-readable request file (tests chmod 0600), a project root that is itself a symlink, and a wrong `project_id`. Check that errors stay inside the closed error-code set and nothing writes outside the project. Validator: plugin trees with symlinks escaping the root, `..` paths in manifests, malformed or huge SKILL.md frontmatter, and non-UTF-8 files. specflow helper and review scanners: crafted spec markdown or state JSON (path traversal in spec_dir, huge files, deep JSON in `.specflow` state). `autopilot.py --verify ... -- ARGV`, `--stage-review` and `--check-evidence`: crafted artifact paths, relative or traversing `--project-root`, and argv injection. Needs the Authorization line (section 5) or `--authorized` at dispatch. |

## 3. Mocking strategy

- **Agent hosts (claude, codex, gemini, kiro-cli)**: do not call the real
  binaries. Put fake executables in a scratch bin dir at the front of PATH.
  They should print the version and marker output the host probe expects; see
  `plugins/autopilot/scripts/{claude,codex,gemini,hosts}.py` and
  `tests/autopilot/test_host_argv.py` for the expected argv. For guard paths,
  use the in-repo `jobs.FakeSeam`. Report all of these `mocked`, never `verified`.
- **Real controller seam**: does not exist at HEAD (doctor says "AP 00016 ships
  the real seam"). Guard results are simulated, so report them `mocked`.
- **GitHub / marketplace remote**: do not install from the remote. Exercise
  catalog generation locally in the clone; any claim about client install is
  `mocked` or unestablished.
- **Upstream specflow sources**: no network. Use the committed cursors in
  `tools/specflow/upstream/` as they are; results are `mocked`.
- **Frozen claude-autopilot source**: not external. Read it through a scratch
  clone (`git clone /Users/bob/git/src/github.com/buvis/claude-autopilot <scratch>/frozen`);
  those results can be `verified`.

## 4. Authoring assignments

The master authors these on a branch after the lanes report. Specialists put
any proposed test in their finding's `fix` field only.

- Controller hostile-input regressions: `tests/autopilot/`, under pytest
  (`uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot`).
- Validator and marketplace edge cases (symlink escape, name mismatch, catalog
  drift): `scripts/test_*.py`, under `python3 -m unittest discover -s scripts`.
- specflow helper journeys on isolated fixtures: `tests/specflow/contract/`,
  under `python3 -m unittest discover -s tests/specflow/contract`.
- Release-truth consistency (README table versus marketplace, CHANGELOG versus
  manifest version): `tests/specflow/release/` already holds boundary checks
  for specflow. An equivalent repo-wide check belongs in `scripts/` under
  unittest.

## 5. Pins and vetoes

Authorization: not asserted

## 6. Freshness stamp

- Recon date: 2026-11-09
- Target HEAD: 0c5c47debc37cfeaa0f9010acbd072864f195f9e
