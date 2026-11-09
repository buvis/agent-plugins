# specflow release 0.1: fast path through 00009 and 00001

Written 2026-11-09 at master `956eab5`. Measured with
`validate_spec.py status --json`, the task files, the eval inventory, and the
installed host CLIs. Executed plans leave this folder when the work is done.

## 1. What is left

| Spec | Phase | State file | Tasks open |
|---|---|---|---|
| 00009 cross-host validation | requirements (receipts only) | missing | 10 of 10 |
| 00001 initial delivery (release) | requirements (receipts only) | missing | 8 of 8 |

00001 depends on 00009. Specs 00002 to 00008 and 00010 are complete.
`check_rules.py` already passes unfiltered from the repository root, so every
behavioral rule has an eval record; nothing has ever run on a host.

## 2. Where the time goes

| Measure | Value |
|---|---|
| Sessions written / still to write | 51 / 8 (`concurrent-edit`, `conversion-calcard`, `comparison-design`, `comparison-tasks`, `recover-native-kiro`, `resume-kiro-bugfix`, `resume-kiro-design-first`, `configured-specs-folder`) |
| Developer turns across the 51 sessions | 219 (about 245 with the 8 new ones) |
| Eval records / rubric assertions | 470 / 464 (design-review 102, review-specs 77, review-walkthrough 56, requirements-review 38) |
| Rules mapped from the six retiring skills (parity rows) | 431 |
| Supported hosts | 3 (Kiro IDE, Codex, Claude Code) |

As approved, three multipliers are manual: every Kiro IDE session by hand
with per-turn capture (about 245 turns), every rubric judged by the
developer (464 x 3 hosts, about 1,400 verdicts, ruling D10), and the parity
gate (six source skills run by hand, 431 rules judged per host). Agents
cannot shorten any of these. A fourth multiplier is structural: a package
fix after a run stales every session on every host (T-057, T-064).

## 3. Rulings that remove the multipliers

All four were ruled by the developer on 2026-11-09 in the planning session
(section 7). Each is a small edit to an approved artifact; phase 0 applies
the edits, and the artifact is re-approved at the same gate when its
`.specflow.json` is recovered (section 4).

| ID | Ruling (recommended) | Edits | Fallback |
|---|---|---|---|
| R1 | Kiro host runs go through `kiro-cli` engine v3 headless (`--no-interactive --output-format stream-json`, or ACP as `acp_review.py` of intake 00022 already does). It is the same Kiro Agent Server the IDE runs; the Power is installed at `~/.kiro/powers/installed/specflow`; `kiro-cli` has `powers` and `--mode spec`. Kiro IDE stays manual only where IDE behavior is asserted: the three Kiro steps of T-051, T-052, and the "opens as its own spec type" notes for `intake-bugfix` and `shared-dialogue-design-first`. Records keep `host: kiro-ide`, `mode: automated`, and `hostVersion` names kiro-cli and the agent server. Kiro CLI stays "untested, not listed as supported" in the docs (PKG-003.4 unchanged). | 00009 design: Context bullet 4, Eval runners bullet 1, run environment; tasks T-056 adds `run_kiro.py`, T-057 Details. | Power does not load in kiro-cli: the approved plan, all Kiro sessions by hand. |
| R2 | A model judge scores every `rubric` assertion (`claude -p`, fixed judge prompt, a model other than the one under test where the host is Claude Code). The record stores `judge: model:<id>`. The developer judges by hand every FAIL and a random 10% of PASS per host and session; if more than 1 of 10 sampled verdicts is wrong, that session's rubrics are judged by hand. Amends D10. | 00009 design: Scoring, last bullet; tasks T-056 Details. | D10 as approved: every verdict by hand. |
| R3 | Parity source runs are headless: the source skill runs on Claude Code through `claude -p` in the developer's normal profile (`--setting-sources user`), invoked by name, on the same fixture and turns. The same judge scores the 431 rules; the developer reviews each per-skill report, not each row. | 00009 design: Parity gate step 2, Data model "run by hand"; tasks T-058 Contract. | Six skills by hand, 431 rows by hand. |
| R4 | T-066's target `buvis/claude-autopilot` is frozen since 2026-11-01. The repoint item goes to this repository's `docs/dev/project-management/intake/new/` for `plugins/autopilot`. | 00001 tasks T-066 Location, Details, Verify. | None workable; the frozen repo refuses commits. |

Not a ruling, only ordering (section 4): the package is frozen before the
second and third hosts run, so a fix never stales three hosts at once.

## 4. Sequence

Critical path: T-056 runners -> Claude Code shakedown -> package freeze ->
Codex and Kiro runs -> T-058 parity -> 00009 review and merge -> T-063,
T-064 -> tag.

### Phase 0: gate and state (one session; developer about 20 minutes)

1. Branch `feature/specflow-00009`, worktree
   `~/git/src/worktrees/agent-plugins/feature-specflow-00009`.
2. Apply R1 to R4 to the 00009 design and tasks and the 00001 tasks.
3. Recover `.specflow.json` for 00009 and 00001 (spec-workflow recovery
   mode on the receipts in each `qa-log.md`); the developer confirms the
   requirements approvals as they stand and approves the amended design and
   tasks in the same answer. Hashes from `validate_spec.py hash --json`.
4. Commit. `status --json` shows both specs with every gate open.

### Phase 1: instruments (parallel agent sessions, no host runs yet)

| Lane | Tasks | Notes |
|---|---|---|
| A | T-050 fixtures + `test_fixtures.py` | Reuse the fixture specs under `tests/specflow/fixtures/sessions/` where one already is the named shape; add only what is missing. |
| B | T-056 runners, scorer, judge, `result.schema.json`, `test_score.py` | Probes first, in this order: (1) Codex sign-in from a temporary `CODEX_HOME` holding a copy of `~/.codex/auth.json` and the plugin installed by the 00008 route (`codex plugin marketplace add <checkout>`, `codex plugin add specflow@buvis-agent-plugins`); (2) kiro-cli v3 loads the installed Power and answers one spec-workflow turn; (3) `claude -p --plugin-dir plugins/specflow` with user settings left out (`--setting-sources` without `user`, or `--bare` if it accepts `CLAUDE_CODE_OAUTH_TOKEN`), and the instruction files it still reports. A probe that fails stops the lane and is reported; nothing is worked around silently. Codex exposes no read events, so `filesRead` for Codex is recorded as not measured (design fallback). |
| C | T-054 security review + `tests/specflow/security/` + CI step | Independent of A and B. |
| D | T-081 fixture copy from `buvis/calcard-mcp` 00032 + `test_conversion_fixture.py` + CI step; the 8 missing sessions and their eval records (T-053, T-057 authoring half) | Read the copy for anything non-public before committing. |
| E | 00001 T-060, T-061, T-062 drafts on `feature/specflow-00001`, branched from the 00009 branch once lane A lands | All three stay inside the safe paths (`README.md`, `CHANGELOG.md`, `docs/`), so they stale no evidence. Final text waits for T-058's two maintainer guides. |

### Phase 2: shakedown on Claude Code only

1. Run all 59 sessions on `claude-code`, four at a time, with a per-session
   `--max-budget-usd` cap. Score. Judge rubrics (R2).
2. Developer: hand-judge every FAIL and the 10% sample.
3. Fix in one batch: rule text, SKILL.md or reference wording, or the eval
   when the eval is wrong (say so in the `Outcome:` line). Rerun only
   Claude Code. Repeat until green. Each rerun is a new `<n>.json`.

### Phase 3: freeze and fan out

1. Record the package tree id (`git rev-parse HEAD:plugins/specflow`) as the
   frozen revision. No edit under `plugins/specflow/skills/` or to a
   manifest after this point without returning to phase 2.
2. In parallel: Codex batch (temporary home, removed at batch end), kiro-cli
   batch, and the developer's Kiro IDE subset (T-051 Kiro steps, T-052, the
   two type notes). T-053 and T-081 sessions ride in the batches.
3. Score and judge as in phase 2. A failure that needs a package fix sends
   all three hosts back to phase 2; an eval or judge error is fixed in
   place and that session is rerun on the affected hosts only.
4. T-055 from the stored records (sizes measured by script; loading compared
   per phase and profile; Codex marked not measured).
5. T-058: six source skills headless (R3), judge, six reports, the two
   maintainer guides.

### Phase 4: close 00009

1. Tick completion criteria; every task carries its `Outcome:` line; CI
   green with the two new steps; no temporary Codex home left under
   `docs/dev/tmp/specflow/evals/`.
2. Fresh session: `/autopilot:review-work-completion` per the recipe in
   project memory (standalone flags, roster alice, blake, bob as in 00008).
   Rework, PR, merge to master.

### Phase 5: close 00001 and release

1. Rebase `feature/specflow-00001`; finish T-060 (trial on a throwaway
   branch), T-061 (`test_docs.py`), T-062 (policy, 0.1.0 entry, pinned
   install lines with the tag name).
2. T-063 on a clean checkout of the candidate: `verify_release.py`,
   unfiltered `check_rules.py`, `generate_marketplace.py --check`, the CI
   test commands with `PYTHONDONTWRITEBYTECODE=1`; report with commit and
   package tree id.
3. T-064: catch-up over the three sources (report plus cursor moves), install
   the candidate on the three hosts by the recorded local routes (Kiro IDE
   by the developer), handoff from the candidate. The 00009 records stay
   valid when the package diff since the frozen revision touches only
   `README.md`, `CHANGELOG.md`, and `docs/`. Eight measures with evidence.
4. Review (fresh session), rework, PR, merge.
5. T-065 only on the developer's explicit instruction: tag
   `specflow-v0.1.0` on the master commit that holds the report, the
   catch-up outputs, and the README row; release notes; fetch the three
   schema addresses; `git rev-parse specflow-v0.1.0:plugins/specflow` equals
   the tested tree id.
6. T-066 (this repository's intake, R4) and T-067 (`buvis/agent-skills`,
   on the developer's instruction).

## 5. Developer time, in order

| Step | When | Time |
|---|---|---|
| Answer R1 to R4; confirm recovered approvals | Phase 0 | 20 min |
| Hand-judge FAILs and the 10% sample, Claude Code | Phase 2, per round | 1 to 2 h |
| Kiro IDE subset: T-051 three steps, T-052, two type notes | Phase 3 | 2 to 3 h |
| Hand-judge FAILs and samples, Codex and Kiro | Phase 3 | 1 to 2 h |
| Read six parity reports | Phase 3 | 1 h |
| Two review walkthroughs (only if a finding needs a ruling) | Phases 4, 5 | 0 to 1 h |
| T-064 Kiro IDE install and handoff step | Phase 5 | 30 min |
| Say "tag" for T-065; file T-067 | Phase 5 | 15 min |

Everything else is agent work. Agent wall-clock, assuming the probes pass
and two shakedown rounds: phase 0 and 1 about three days, phase 2 and 3
about four, phase 4 and 5 about three.

## 6. Risks

- Codex temporary home: `auth.json` may not be readable from the sandbox,
  or the copied sign-in may be refused. Probe first; on failure the
  developer picks the design's fallback (instruction file moved aside,
  taint recorded, waiver).
- kiro-cli may not load Powers in headless mode, or may refuse `--trust-tools`
  for the file tools the skill needs. Probe first; fallback is R1's.
- Judge variance: the sample rule in R2 catches a judge that drifts; failing
  runs are kept, reruns are recorded as reruns.
- `filesRead` on Codex and possibly kiro-cli is unavailable; T-055 records
  those hosts as not measured, as the design allows.
- Stored records: 59 sessions x 3 hosts, each with messages and changed
  files. Expect tens of megabytes in `tests/specflow/evals/results/`.
- Flaky model output: a session breaks at an `expects` turn and fails every
  eval on it; rerun once before investigating.

## 7. Unresolved questions

Asked one at a time, in this order.

1. R1: ruled 2026-11-09, yes: kiro-cli v3 headless, Kiro IDE by hand only
   for the IDE-asserted steps.
2. R2: ruled 2026-11-09, yes: model judge, developer judges FAILs and a 10%
   sample; D10 amended.
3. R3: ruled 2026-11-09, yes: source skills headless through `claude -p`,
   judged the same way, six reports reviewed.
4. R4: ruled 2026-11-09, yes: T-066's item goes to this repository's intake
   for `plugins/autopilot`.
5. Reviewer roster: ruled 2026-11-09: alice, blake, bob, as in 00008.

No question is open. Phase 0 can start.
