# Backlog review - agent-plugins - 2026-10-25

Verdict: GO

Target: `docs/dev/project-management/prds/backlog/` (ten PRDs, 00012-00021). No `wip/`, `hold/` or `done/` yet. The executing loop is the installed `autopilot` plugin 0.10.0; the PRDs port `claude-autopilot` at `e960ef1c` (checkout HEAD equals the pin) and extract the controller from `ovcaq` at `cf8be72` (requires Python 3.12).

History of this review: the first pass read a six-PRD backlog (two-backend design) and raised five Blocking findings; the user answered eight finding cards. While those cards were open, a parallel session rewrote the backlog twice (boundary correction, then the three-layer design with a bundled controller, adding 00018-00021 and renaming 00013 and 00016) and appended its own dispositions to this file. The second pass below re-read every current PRD in full, re-ran every lens, carried each user decision to its current counterpart, and corrected four edits the first pass had applied against stale text (00017's eligibility pointed at 00015 instead of 00016; 00014 carried a duplicate changelog line and a redundant build directory line).

Mechanical checks (after the apply pass):

- `check_links.py`: 0 findings under `prds/backlog/`. The `ls … prds/done/…` eligibility lines carry a `# link-ok: lifecycle output` shell comment (the done bucket is created by the lifecycle, not by any PRD); the comment is inert under the gate's `shell=True`.
- `ground_prd.py`: 11 citation rows, all `ok` (`AGENTS.md:39`, `scripts/validate.py:61`); 0 blocking, 0 unverified.
- Hygiene: only `NNNNN-slug-v1.md` files; 00012-00021 collide with nothing in `discovery/` or `intake/`; headings match `standard.md` in order; Feature headings unique; every task line carries `Acceptance:`; 119-151 physical lines each.
- Eligibility lines executed through the installed `cli.eligibility` code: every later PRD is unmet today (non-zero, skip-not-park); a control root with `done/00012-*` makes 00013 eligible (exit 0) and leaves 00014 unmet.
- Test command executed in the sandbox: `uv run --no-project --python 3.12 --with pytest` provisions Python 3.12.15 and pytest 9.1.1; the mise 3.12 interpreter has no pytest and its install target is read-only.

## Map

| # | PRD | template | lines | subsystems | depends on | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 00012 | Package and review artifact contracts | standard | 151 | 11 skills, 59 references, 18 personas, review evidence/policy contracts, `tools/autopilot/`, CI job | source pin only | READY |
| 00013 | Session-local helpers | standard | 126 | `plugins/autopilot/scripts/` pure helpers, verification artifacts | 00012 | READY |
| 00014 | Host execution and enforcement | standard | 130 | host adapters, guards, compatibility bundles, probes | 00012, 00013 | READY |
| 00015 | Skill procedures and runtime boundaries | standard | 150 | all 11 skill bodies, review policy, capabilities map | 00013, 00014 | READY |
| 00016 | Skills and standalone controller integration | standard | 126 | controller client, standalone handoff, compatibility diagnostics | 00015, 00020, 00021 | READY (waits by eligibility) |
| 00017 | Standalone and managed conformance | standard | 121 | profiles, release candidates, CI, README, AGENTS.md | 00016 | READY (waits by eligibility) |
| 00018 | Controller kernel and protocol | standard | 128 | `plugins/autopilot/controller/` store, schema, protocol, actors | 00012 | READY |
| 00019 | Controller lifecycle, tasks and job plans | standard | 127 | lifecycle, tasks, frontmatter, policy, files, jobs | 00018 | READY |
| 00020 | Controller review, lanes and evidence guards | standard | 129 | review, lane, custody, verification, waves | 00019 | READY |
| 00021 | Controller record commits and extraction conformance | standard | 120 | records, conformance bundle | 00020 | READY |

Drain order: 00012, 00013, 00014, 00015 run in sequence; 00016 and 00017 are skipped (unmet) until 00018-00021 complete, then picked on the next selections. Verified: `select_eligible` re-evaluates every backlog candidate on every pick.

## Findings

### Blocking (all resolved in the apply pass)

- [00013-00021] B Executability / E Collisions: eligibility lines were a mix of `python3 tools/autopilot/prerequisites.py --prd NNNNN` (a tool 00012 builds inside the batch) and two shell checks from the first pass, one of which (00017) named 00015 instead of its real predecessor 00016. -> fails as: selection break (a tool interface mismatch skips every later PRD silently) and order break (00017 before 00016). Fix applied: all nine lines are `ls docs/dev/project-management/prds/done/<dep>-*` per the design's prerequisite table (00013←00012; 00014←00012+00013; 00015←00013+00014; 00016←00015+00020+00021; 00017←00016; 00018←00012; 00019←00018; 00020←00019; 00021←00020); 00012 states that `prerequisites.py` is the maintainer view of the same table and never gates selection.
- [all] B Executability: exit criteria named `Python 3.12 python3 -m pytest tests/autopilot -q` or an unversioned `python3 -m pytest`, but the sandbox has no pytest on Python 3.12 and cannot install one (mise install targets are read-only); the default `python3` is 3.14. -> fails as: unattended hang (an install attempt escalates to warrant) or a false pass on the wrong interpreter. Fix applied: every exit criterion and 00012's Dependency Graph name `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q`, verified to run here; 00012's CI task installs `tools/autopilot/requirements-test.txt` on the 3.12 job.
- [00018] B Executability: Contract A (envelope, response, error codes, capability IDs, closed operations, CLI suffixes) lived only in the design doc; 00018 said "exact envelope/errors from Contract A". -> fails as: wrong-TDD lock-in (the test author invents the lists; 00016, 00019-00021 and OVCAQ 00057/00058 consume them). Fix applied: the lists are inlined in the Feature "Typed commands and actor fencing" Behavior (user decision 3 carried over).
- [00013, 00014, 00017] A Compliance: `check_links` flagged the `prds/done/` eligibility paths and 00013's prose path `docs/dev/project-management/autopilot`; 00014 carried a duplicate `CHANGELOG.md` tree line and a redundant `docs/dev/tmp/autopilot/compatibility/` line from the first pass. -> fails as: stall (premise checks trip on dangling pointers). Fix applied: `link-ok:` comments, rephrased prose, duplicates removed.

### Non-blocking (applied under standing authorization)

- [00017] H Goal / C Coherence: `AGENTS.md` ("only `plugins/specflow/` ships") was not in any tree; the release-candidate output directory was unnamed; "explicitly configured OVCAQ" named no configuration. Applied: `AGENTS.md` and `docs/dev/tmp/autopilot/` in the tree, the Phase 2 task names both documents and the boundary list, candidates go under `docs/dev/tmp/autopilot/dist/`, managed checks take `tools/autopilot/conformance.py --ovcaq-argv JSON` (absent means unavailable).
- [00018] D Grounding: the OVCAQ checkout path was absent (pin only). Applied: `/Users/bob/git/src/github.com/buvis/ovcaq`, read with `git show` at the pin.
- [00021] D Grounding: "source store_tree/verification behavior" named no repository; `store_tree` does not exist in OVCAQ, it is `claude-autopilot/skills/run-autopilot/cli/store_tree.py`. Applied: the path and pin are named.
- [00018-00020] F Sizing: 166 KB of OVCAQ state/workflow source plus its tests extracted across four-line task lists; the plan-expansion gate stalls at 13-16 planned tasks. Applied: `plan_expansion: allow` + `rework_cap: 3` on 00018, 00019, 00020 (extends user decision 8 from the first pass to the three extraction PRDs; 00012 and 00015 already carried it).
- [00012, 00014, 00015, 00018] A Compliance: numbers fused to words in contract text (`AP00018`, `OV00059`, `until00016`, `PRD00016`, `after00016`, `Exit0`/`exit1`, `Python3.12`, `directory0700/file0600`) and doubled periods in six Success Metrics lines. Applied: spaced and punctuated.

### Report-only

- All ten PRDs cite `AGENTS.md:39` as the containment rule; line 39 is "independently distributable" and line 41 is the containment line. Harmless (the grounding gate accepts it).
- `ruff.toml` targets py310 for the whole repo while the controller is Python 3.12 code; ruff will not fail on 3.12 syntax, but a `per-file-target-version` for `plugins/autopilot/controller/` and `tests/autopilot/` would stop loupe suggesting downgrades.
- OVCAQ 00057 (controller client) sits in that repo's `wip/` while the design says it consumes the AP 00018 bundle; cross-repo sequencing, outside this gate.
- Lantern PRDs live outside this repository; nothing here depends on them.
- Identical Target Users and Dependency Graph boilerplate across 00016-00021; prose tax is small.
- Real host probes (Claude Code, Codex) remain implementation risks; every PRD records a missing binary, auth or install path as `unavailable` and refuses the affected profile, never as success.

### Questions

None open. The three first-pass questions (test runner, host-probe semantics, plan-expansion gate) were answered by the user and are applied above.

## Reshapes

None. Sizes 120-151 lines, two capabilities each, producer-first order; the two higher-numbered dependencies (00016 on 00020/00021, 00017 on 00016) are gated by eligibility rather than renumbered, because the design, the OVCAQ PRDs and the held PRDs all cite these numbers.

## Gaps

- Source retirement, marketplace cutover, shell aliases and global instructions stay outside the batch by design (held OVCAQ 00010/00011/00014).
- OVCAQ 00058-00065 and Lantern 00001-00003 are driven from their own repositories; AP 00021's conformance bundle is their input.
- Specflow-to-autopilot artifact handoff: deferred by the design, no PRD.
- No strategic gap found that `/assess-evolution` should fill now.

## End state after this batch

`plugins/autopilot/` is a self-contained Agent Plugins package: eleven skills with their 59 references preserved file-for-file, eighteen personas, review evidence/policy contracts, pure session helpers, host adapters and guards for Claude Code and Codex (profiles earned only by recorded evidence), and one bundled Python 3.12 controller (kernel, lifecycle and jobs, review/lanes/evidence, record commits) that standalone sessions and OVCAQ both call. 00016 wires the skills to that controller and 00017 proves installed standalone use with every upper layer absent and produces unpublished candidates. `tests/autopilot/` runs in a new Python 3.12 CI job beside the Python 3.10 validator job; `README.md` and `AGENTS.md` describe the new package and its maintainer directories. Still lacking after the batch: OVCAQ's extraction (00058) and mixed-driver execution, waves, Lantern, source retirement and cutover.

## Frontmatter tuning

| PRD | suggestion | why |
| --- | --- | --- |
| 00012, 00015, 00018, 00019, 00020 | `plan_expansion: allow` + `rework_cap: 3` (applied) | four-to-six coarse task lines over 0.2-1 MB of source; the 15-task ceiling would stall |
| 00013-00021 | `eligibility` as shell `ls prds/done/<dep>-*` (applied) | the sequencing gate must not depend on code built inside the batch |
| all | keep `default_model: opus`, `lane: full` | equivalence obligations and invented contracts |

## Decisions applied

1. Eligibility (user: shell checks): nine `ls` lines on the done bucket, dependencies per the design table; 00012 marks `prerequisites.py` as non-gating.
2. References (user: port 1:1): already carried by the redesign; 00012 and 00015 list the nine `references/` directories and all 59 files; content_roster compares heading inventories against `git show` at the pin.
3. Contract enumerations (user: inline): applied to 00018 (the contract now lives there, not in 00012).
4. `tools/autopilot/compatibility.py` (user: drop from 00017): carried by the redesign; 00017 now depends on 00016 and lists only its own files.
5. Temporary project roots (user: one sentence per PRD): carried by the redesign in every PRD's Dependency Graph; 00013's prose rephrased.
6. Test runner (user: pytest): pinned to the uv command above in all ten exit criteria and 00012's CI task.
7. Host probes (user: record-and-refuse): carried by the redesign in 00014 and 00017; 00017's managed configuration pinned.
8. Plan-expansion gate (user: allow on the large ports): 00012 and 00015 carried by the redesign; extended to 00018-00020.
9. Standing-authorization edits: `AGENTS.md` and build root in 00017, OVCAQ path in 00018, `store_tree` grounding in 00021, typo and punctuation fixes.
