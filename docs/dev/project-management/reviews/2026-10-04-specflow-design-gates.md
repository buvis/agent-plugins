# Design gates: specflow specs 00001 to 00009

Date: 2026-10-04
Status: the 14 decisions and the 12 leftovers were decided in the walkthrough
of 2026-10-04 and are applied to the designs (see Decisions at the end). The
nine design approvals are pending. The packets below are kept as they were
asked.

Agenda: 14 decisions (2 blocking, 12 non-blocking), then 12 small leftovers
in three bundles, then the nine design approvals. Each decision is written
for a walkthrough, one at a time, recommendation first.

Where things stand:

| Spec | Pre-pass | Recheck | Open blockers | Opens for you |
|---|---|---|---|---|
| 00002 package boundary | 1 blocker, 11 others | no open blocker | none | D1, D3, D4 |
| 00003 AWS sources | 1 blocker, 11 others | no open blocker | none | D1, D5, D6, D7 |
| 00004 artifact and state | 1 cardinal sin, 6 blockers, 7 others | 1 new blocker; closed after the extra recheck (D14) | none | D1, D2, D13 |
| 00005 behavior rules | 1 blocker, 11 others | no open blocker | none | D8, bundle B |
| 00006 runtime skill | 3 blockers, 9 others | 3 blockers left; closed after the extra recheck (D14) | none | D1, D3 |
| 00007 reviews and conversion | 1 blocker, 11 others | no open blocker | none | D9 |
| 00008 host integration | 1 blocker, 7 others | no open blocker | none | D12, bundle A |
| 00009 cross-host validation | 4 blockers, 6 others | no open blocker | none | D9, D10, D11 |
| 00001 initial delivery | 1 blocker, 9 others | no open blocker | none | D13, bundle C |

Every design was reviewed by an isolated reviewer that saw the draft, its
approved requirements, its source tasks, and the fifteen-item cardinal-sin
list, and then rechecked once after fixes. Findings and what was done with
each are in the `qa-log.md` of each spec's intake item. Fixes to my own draft
text were applied; anything that would change text carried from the source
design, or a contract you approved, was left for you below.

## D1 of 14 · Blocking · Which task first creates `SKILL.md`

- What: the repository validator fails any skill folder that has no
  `SKILL.md`. Tasks of 00003, 00004, and 00005 write files into
  `plugins/specflow/skills/spec-workflow/` long before T-030 (00006) writes
  the skill. My own design check found it (finding F12).
- Evidence (confirmed): `python3 scripts/validate.py` on a scratch package
  with `skills/spec-workflow/references/` and no `SKILL.md` exits 1 with
  "each skill directory must contain SKILL.md".
- If unchanged: CI is red from the first such task until T-030, across three
  specs. Certain, and it blocks every merge in between.
- Options:
  1. (Recommended) T-002 creates a truthful shell: valid frontmatter and one
     sentence saying the workflow is not written yet, and the release check
     forbids that sentence, so a shell can never ship. Benefit: CI stays
     green, and no validator change. Drawback: a file whose body is thrown
     away. Effort S. Could break: nothing found.
  2. The validator skips a skill folder with no `SKILL.md`. Benefit: no
     shell. Drawback: weakens a check every plugin relies on. Effort S.
     Could break: a real plugin shipping a broken skill unnoticed.
  3. Build everything outside the package and move it in at T-030. Benefit:
     the package is never half built. Drawback: every path in five designs
     changes twice. Effort L.
  4. Accept red CI until 00006. Drawback: three specs cannot land cleanly.
- Strongest reason against option 1: it is a stub, which your coding rules
  ban; the release check is what makes it safe.

## D14 of 14 moved up · Blocking · Four late fixes, in the 00006 and 00004 designs

- What: two rechecks left blockers. I fixed each afterwards, but specflow
  allows one recheck, so none was verified. In 00006, three: behavior from
  the requirements had no rule ID, so its sessions could not be scored; the
  sketch check was defined nowhere; two tests of T-030 failed by
  construction. In 00004, one: the design check as worded would fail every
  design that names a criterion another spec holds, so no design approval
  could be recorded in this repository.
- Evidence (confirmed by the reviewers, fixes unverified): the `qa-log.md`
  of 00006, entries V1 to V3, and of 00004, entry V1.
- If unchanged: neither design can be approved; the fixes stay guesses.
- Options:
  1. (Recommended) Allow one more recheck, of these four fixes only.
     Benefit: the fixes are verified by the reviewers that found the faults.
     Drawback: breaks the one-recheck rule once. Effort S.
  2. You read the four fixes and accept or dispute each. Benefit: keeps the
     rule. Drawback: your time on details of two long designs. Effort M.
  3. Approve as is and let the task review catch what is left. Benefit:
     fastest. Drawback: the two largest designs go forward unverified.
  4. Defer both. Drawback: every later spec waits behind 00004.
- Strongest reason against option 1: it sets a precedent for looping.

## D13 of 14 · Non-blocking, time-critical · The schema URLs

- What: the three JSON schemas need a public address. The source left that
  to T-062, the last spec. But T-062's edit lands after the host runs of
  00009, and any change under `skills/` voids their evidence.
- Evidence (confirmed by the 00001 reviewer): run records name the package
  tree they ran on; a schema edit changes it.
- If unchanged: every session runs again on three hosts, one by hand.
- Options:
  1. (Recommended) Settle it now: the raw file at the release tag,
     `https://raw.githubusercontent.com/buvis/agent-plugins/specflow-v<version>/plugins/specflow/skills/spec-workflow/schemas/<file>`,
     written by T-021 from the start. Benefit: no late edit, no rerun.
     Drawback: the address resolves only once the tag is pushed. Effort S.
  2. No address: schemas carry a relative path only. Benefit: nothing to
     decide. Drawback: a state file cannot point a tool at its schema.
  3. A separate site for schemas. Benefit: stable across versions. Drawback:
     one more thing to host. Effort M.
  4. Leave it to T-062 and accept the rerun.
- Strongest reason against option 1: the address carries the version, so it
  changes with every release.

## D9 of 14 · Non-blocking · The conversion fixture is not what the spec says

- What: the source says the calcard-mcp conversion produced an approved
  artifact set with a receipt, and T-081 tests against it. Two reviewers read
  the real folders: the task plan is drafted and not approved, there is no
  receipt and no completed work, and nothing there is committed.
- Evidence (confirmed): `.specflow.json` has tasks `"status": "draft"`; no
  hit for "receipt"; `git status` shows both folders untracked.
- If unchanged: T-081 cannot pass as written, and CNV-001's proof rests on a
  claim that is not true.
- Options:
  1. (Recommended) Correct the text to the true state; T-081 compares
     structure and tests completed work on a seeded variant, as the 00009
     design now says. Benefit: honest, buildable today. Drawback: the
     "proven" fixture proves less. Effort S.
  2. Finish the calcard-mcp spec first: approve its tasks, write a receipt,
     commit, then copy. Benefit: the fixture is what the spec says. Drawback:
     work in another repository first. Effort M.
  3. Drop T-081 and rely on T-080's scenario fixtures. Benefit: simplest.
     Drawback: loses the only real-world case.
  4. Defer to the 00009 task plan.
- Strongest reason against option 1: it weakens a claim you made the reason
  for shipping the skill.

## D10 of 14 · Non-blocking · Who judges a rubric assertion

- What: some evals need judgement ("plain language"). The scorer must store
  a verdict. Nothing said who gives it.
- Evidence (confirmed): the source names rubric assertions and no judge.
- If unchanged: T-057 cannot finish, since every eval must pass.
- Options:
  1. (Recommended) You judge, by hand; the scorer prints the rubric and
     stores verdict, judge, and reason. Benefit: no second model to trust.
     Drawback: hand work on every host run. Effort S.
  2. A named model with a fixed prompt judges; you spot-check. Benefit: runs
     unattended. Drawback: a model grading a model. Effort M.
  3. Cut rubric assertions; keep only deterministic ones. Benefit: no judge.
     Drawback: two source rules lose their check.
  4. Defer to the 00009 task plan.
- Strongest reason against option 1: with about 40 sessions on three hosts
  the hand work is real.

## D11 of 14 · Non-blocking · Codex cannot load a plugin per run

- What: Claude Code loads the plugin from a folder per run. `codex exec` has
  no such option, and no flag that leaves out your own instruction file,
  which holds rules the evals test.
- Evidence (confirmed from `codex exec --help` by the reviewer; not run).
- If unchanged: Codex results may show your settings, not specflow.
- Options:
  1. (Recommended) A temporary Codex home with only the sign-in and the
     plugin, set up by the runner. Benefit: clean runs. Drawback: must be
     proven to work with your sign-in. Effort M (guess).
  2. Reinstall before each batch and move your instruction file aside.
     Benefit: simple. Drawback: touches your real settings while it runs.
  3. Record what was loaded and accept the taint. Drawback: weak evidence.
  4. Defer until T-042 shows how Codex installs the plugin.
- Strongest reason against option 1: nobody has tried it yet.

## D2 to D8, D12: smaller decisions

Each has a proposal already written in the named design's Open decisions.

| # | Decision | Recommended | Main drawback |
|---|---|---|---|
| D2 | Who creates `references/artifact-contract.md` (no task does; T-030 calls it existing) | T-020 creates it, T-029 adds the intake steps | T-020 grows |
| D3 | Should the host probe also run one bundled script (approvals need the helper on every host) | yes, one line added to T-006 | the probe takes longer |
| D4 | The Claude manifest names no `skills` path, against T-003's wording | accept: Claude Code finds `skills/` by default (checked with `claude plugin validate --strict`) | relies on a host default |
| D5 | Catch-up steps 8 to 10 cannot run as carried (clones removed too early, the release check fails on uncommitted edits, no tag rule) | apply the reviewer's three edits | changes carried text |
| D6 | The license gate has no detection step | diff each source's license files in step 4 | a little more to read per catch-up |
| D7 | Is text under a source line verbatim | yes, with cuts shown as `[...]`; rewording goes on `Adaptation:` lines | more markup in references |
| D8 | Do the two new criteria join the list of 31 | yes: 33, and RULE-001.1 says 33 | edits an approved requirement |
| D12 | The marketplace name | `buvis-agent-plugins` (others offered: `quiver`, `satchel`, `foundry`) | plain, not evocative |

## Leftover bundles

Findings a reviewer raised that I did not apply. Each line gives the gap and
one proposed fix. A fix marked (author) is my proposal, not the reviewer's.

Bundle A, 00008 host integration:

- A1. No task tries the install routes that T-045 documents. Fix: T-045
  tries each open install route once in a fresh host profile and appends
  the result to that host's record.
- A2. The catalog generator's contract leaves gaps. Fix: it calls
  `validate_manifest`, builds its output in `build_manifest(root)`, which
  returns the exact text, and skips a plugin with no Claude manifest.
- A3. The catalog and its CI check appear in none of the root docs. Fix:
  T-046 adds rows for `README.md`, `AGENTS.md`, and `CONTRIBUTING.md`.
- A4. Nothing says where a pre-release install comes from. Fix (author):
  T-046's install check adds the marketplace from the local checkout; the
  public route is first exercised at release. This rests on a recalled
  Claude Code feature, which T-046 confirms.

Bundle B, 00005 behavior rules:

- B1. The design says the inventory and the criteria list are checked with
  `check_schema`, and places no schema file for them. Fix (author):
  `tools/specflow/rules/inventory.schema.json` and `criteria.schema.json`,
  beside the files they describe, written by T-070.
- B2. A drop ruling may add behavior, and a rule may not cite a `drop` row.
  Fix (author): no new source form. Such a rule cites the decision (`D:`)
  or the criterion (`R:`) behind it, and the checker keeps rejecting a rule
  that cites a `drop` row.
- B3. The carried text describes rule area `SKL` as intent and trigger rows
  only, while 00006 also tags the language rule, the gates, and the status
  summary there. Fix (author): reword the sentence to name them; the source
  line is dropped with that reason.

Bundle C, 00001 initial delivery:

- C1. The schema-address work names no keyword, no instance side, and no
  check that the address resolves. Fix: the address is each schema's `$id`;
  the release task fetches the three addresses once the tag is pushed and
  records the result. No instance file carries a `$schema` key in the first
  release (author: nothing reads one yet).
- C2. The documentation tests cannot be built as named. Fix: package paths
  are marked in the guide, the test holds the map from each example to its
  fixture, and the host list is a constant.
- C3. The policy understates where the version lives and does not say
  whether install lines pin the tag. Fix (author): the release procedure
  lists the version-bearing files (the manifests, `WORKFLOW_VERSION`, the
  schema addresses, the changelog heading, the marketplace entry), the
  release check compares them, and install lines pin the release tag where
  a host's install route takes a ref.
- C4. The plugin README row covers four of the six items `CONTRIBUTING.md`
  requires. Fix: add skills and adapter, files and data accessed,
  authentication, and failure behavior; remove the unreleased line.
- C5. Principle 6 says every adopted passage names its source and commit,
  while an A1 source line needs only the release tag. Fix (author):
  principle 6 says "source and ref"; the source record maps each tag to its
  commit, and the source check enforces it.

## The nine approvals

After the decisions above, each design is ready for its approval summary.
Order: 00002, 00003, 00004, 00005, 00006, 00007, 00008, 00009, 00001. Each
design ends with the list of choices I made where the source was silent;
those are what you would be approving beyond the carried text.

## Decisions (filled in during the walkthrough)

- D1, 2026-10-04: option 1. T-002 writes a truthful shell `SKILL.md`, and the
  release check forbids its sentence, so a shell cannot ship. Queued: the
  designs of 00002, 00003, 00004, and 00006 take it in before their approval.
- D14, 2026-10-04: option 1. One more recheck, of the four late fixes only
  (00006 V1 to V3, 00004 V1), by the reviewers that found the faults. The
  one-recheck rule is bent once, by the developer's ruling. Done: two fixes
  confirmed (00006 V2, V3). The other two were each one edit short; the
  reviewers named the edits and they are applied as worded. For 00004 the
  reviewer's script now passes all nine designs; no reviewer read the
  closing edits. Minutes in the `qa-log.md` of 00004 and 00006.
- D13, 2026-10-04: option 1. The schema address is the raw file at the
  release tag, written by T-021 from the start. Queued: the designs of
  00004 and 00001 take it in before their approval.
- D9, 2026-10-04: option 1. The text states the fixture's true condition
  (task plan drafted, no receipt, nothing committed); T-081 compares
  structure and tests completed work on a seeded variant. Queued: the
  designs of 00007 and 00009 are checked against it before their approval.
- D10, 2026-10-04: option 1. The developer judges each rubric assertion by
  hand; the scorer prints the rubric and stores verdict, judge, and reason.
  Queued: the 00009 design is checked against it before its approval.
- D11, 2026-10-04: option 1. The runner uses a temporary Codex home with
  only the sign-in and the plugin; it must be proven with the developer's
  sign-in. Queued: the 00009 design is checked against it before its
  approval.
- D2, D3, D4, 2026-10-04: all three recommended fixes accepted. T-020
  creates `references/artifact-contract.md` and T-029 adds the intake
  steps; the host probe of T-006 also runs one bundled script; the Claude
  manifest names no `skills` path and T-003's wording follows. Queued: the
  designs of 00002, 00004, and 00006 close these open decisions before
  their approval; the T-003 and T-006 wording goes to the 00002 task plan.
- D5, D6, D7, 2026-10-04: all three recommended fixes accepted. Catch-up
  steps 8 to 10 take the reviewer's three edits; step 4 diffs each source's
  license files; text under a source line is verbatim, with cuts shown as
  `[...]` and rewording on `Adaptation:` lines. Queued: the 00003 design
  closes these open decisions before its approval.
- D8, 2026-10-04: option 1. ART-004.16 and VAL-001.13 join the required
  list, which holds 33, and RULE-001 criterion 1 says 33. Queued: the edit
  to the approved 00005 requirements, which then need the developer's
  approval again for that change; the 00005 design follows.
- D12, 2026-10-04: the marketplace is named `buvis-agent-plugins`. Queued:
  the 00008 design closes this open decision before its approval.
- Bundles A, B, and C, 2026-10-04: "Accept all 12 (Recommended)". Every
  proposed fix under Leftover bundles is accepted as written there,
  including the two that reword carried text (B3 and C5). Queued: the
  designs of 00008, 00005, and 00001 take them in before their approval.
- Applied, 2026-10-04: every ruling above is in the designs (commit
  `a4c09b3`); D8 and D9 also changed the requirements of 00005 and 00009,
  which the developer approved again ("Approve both (Recommended)").
- Checked, 2026-10-04: an isolated checker read that commit against the
  rulings. 20 rulings applied as ruled; 2 blockers (00004 still described
  the schema URL as before D13 and C1; 00005 still said a model judges a
  rubric) and 10 non-blockers, all applied by the author and not read
  again. Detail in each spec's `qa-log.md`.
- Approved, 2026-10-05: the developer chose to approve one design at a
  time, approved 00002 with its risk ratings confirmed, and at the question
  for 00003 said "I trust you, approving all designs". That is recorded as
  the approval of the other eight, with the three open upstream questions
  accepted by name (they had been shown by name). Their guessed risk
  ratings were not confirmed by that statement and stay marked, open for
  the tasks gate. A receipt with the file's git blob is in each `qa-log.md`.
