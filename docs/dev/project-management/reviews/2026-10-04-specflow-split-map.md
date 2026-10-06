# Split map: specflow 00001 into nine specs

Date: 2026-10-04
Status: approved by the developer on 2026-10-04 with one change ("Split 00005
in two"); rule 2 was amended afterwards and confirmed the same day ("Cite
upstream", decision 2026-10-04 #9)
Source: intake item `specflow/00001-initial-delivery` at commit `2456a76`
(requirements, design, and tasks at version 0.3)
Method: the manual conversion of `graduate/` (no runtime installed), after the
developer chose "Split by phase" on 2026-10-04.

## Why split

The source is one item: about 2,500 lines and 64 open tasks behind one set of
three gates. Any requirements fix during the build would stale design and
tasks for all 64. The task list already has eight phases, so the cut follows
them, with phase 4 cut once more at the developer's request. Each spec gets
its own three artifacts and gates, and `Depends on:` lines carry the build
order.

## The nine specs

All are feature specs, requirements-first, standard profile.

| Spec | Source phase | Tasks | Count | Depends on |
|---|---|---|---|---|
| `00002-package-boundary` | 1 | T-001 to T-006 | 6 | none |
| `00003-aws-sources-catchup` | 2 | T-010, T-011, T-014, T-018 | 4 | 00002 |
| `00004-artifact-state-contract` | 3 | T-027, T-020 to T-026, T-028, T-029 | 10 | 00002 |
| `00005-behavior-rules` | 4, first part | T-070, T-071, T-069 | 3 | 00002, 00004 |
| `00006-runtime-skill` | 4, the rest | T-030 to T-039, T-072 | 11 | 00003, 00004, 00005 |
| `00007-reviews-and-conversion` | 5 | T-073 to T-077, T-079, T-080 | 7 | 00004, 00005, 00006 |
| `00008-host-integration` | 6 | T-040, T-042, T-043, T-045, T-046 | 5 | 00002, 00006 |
| `00009-cross-host-validation` | 7 | T-050 to T-058, T-081 | 10 | 00003, 00004, 00005, 00006, 00007, 00008 |
| `00001-initial-delivery` | 8 | T-060 to T-067 | 8 | 00002, 00003, 00005, 00007, 00008, 00009 |

Total: 64 tasks, the same 64 as the source. Each `Depends on:` list is derived
from the task dependencies that cross a spec boundary; the graph has no cycle.
00003 and 00004 can run side by side after 00002, and so can 00007 and 00008
after 00006.

What each spec owns:

| Spec | Criteria | Source design sections |
|---|---|---|
| 00002 | PKG-001.1 and .3-5, PKG-002, PKG-003.1-3 and .5-7, REL-001.1-2 | §3, §4, §14 release, §15 release tests |
| 00003 | AWS-001, AWS-002.1 and .3-5, UPD-001, UPD-002, SEC-001, REL-001.3 | §9.4, §10, §11, §14 catch-up, §15 upstream checks |
| 00004 | ART-001.1-5 and .7-10, ART-002.11, INT-001, WF-001.9, WF-002.3-7, WF-004.2-5 and .8, WF-005, WF-006, STATE-001 to STATE-003, VAL-001.1-8, VAL-002.5, SEC-002.5 | §5.3, §6.1 to §6.7, §7, §13, §15 contract tests |
| 00005 | RULE-001.1-3 and .5, VAL-001.9-12 | §5.4, §15 eval formats |
| 00006 | PKG-001.2, ART-001.6 and .11, ART-002 (all but .11), ART-003.1-8 and .12, ART-004, ART-005, INT-002, WF-001.1-8, WF-002.1-2 and .8-9, WF-003, WF-004.1 and .6-7, AWS-002.2, VAL-002.1-4, SEC-002.1-4 | §5.1, §5.2, §6.8, §8, §9.1 to §9.3 |
| 00007 | ART-003.9-11, REV-001, CNV-001 | §5.5, §6.9 |
| 00008 | PKG-003.4 | §12 |
| 00009 | RULE-001.4 and .6, success measures 1-3 and 6-8 | §15 fixtures, scenario evals, parity gate |
| 00001 | REL-001.4-6, success measures 4-5, §9 full delivery, product purpose, goals, non-goals, actors, terms | §1, §2, §16, §18 |

Where each section of the source design went. The designs carry those passages
verbatim, assembled by line number; every line of the source design is in
exactly one design (1,203 carried, 3 header lines dropped, none missing, none
twice). Section numbers inside a carried passage are the source's own.

| Source design section | Now in |
|---|---|
| §1 Overview | 00001; the boundary paragraph in 00002 |
| §2 Design principles | 00001 |
| §3 Repository layout | 00001 (the tree); 00002 (installable root); 00003 (maintainer-skill convention) |
| §4 Distributed package | 00002 |
| §5.1 Normative runtime skill, §5.2 Reference routing | 00006 |
| §5.3 Optional validator | 00004 |
| §5.4 Behavior rules | 00005; its Plan B paragraph in 00007 |
| §5.5 Reviews | 00007 |
| §6.1 Directory, §6.2 Requirements structure | 00004 |
| §6.3 Design structure | 00004 (template); 00006 (drafting) |
| §6.4 Tasks structure | 00004 (template, progress fields); 00006 (planning, sizing, summary) |
| §6.5 Kiro-native compatibility | 00004; the intake-timing paragraph in 00006 |
| §6.6 Bugfix spec shape | 00004 (shape); 00006 (task order, refuted hypothesis) |
| §6.7 Workspace root, intake items, specs folder | 00004; caveats, intake budget, discovery record, and instruction applicability in 00006 |
| §6.8 Spike path | 00006 |
| §6.9 Conversion skill | 00007 |
| §7 State model | 00004 |
| §8 Workflow state machine | 00006 |
| §9 intro, §9.1, §9.2 | 00003 (profile mapping tables); the question-volume and budget paragraphs in 00006 |
| §9.3 Bugfix specs | 00006 |
| §9.4 Adaptation rule, §10 AWS source integration, §11 Catch-up skill | 00003 |
| §12 Host integration | 00008 |
| §13 Error handling | by table row: 00003, 00004, 00005, 00006 |
| §14 Security model | Runtime: 00004 and 00006; Catch-up: 00003; Release: 00002 |
| §15 Testing strategy | Contract tests: 00004 to 00007; Upstream checks: 00003; Compatibility fixtures, runners, parity gate: 00009; eval formats: 00005; sessions: 00006; Release tests: 00002, 00003, 00005 |
| §16 Release process | 00001 |
| §17 Alternatives considered | 00002 (distribution branch); 00003 (the six about upstream); 00004 (record tree, Guard Policy, specs link, state server, frontmatter approvals) |
| §18 References | 00001 |

## Rules of the split

1. **IDs survive.** Requirement IDs (`PKG-001`), criterion numbers
   (`ART-002.12`), and task IDs (`T-030`) keep their source values, with gaps
   where a spec holds only part of a requirement. Decisions, reviews, and the
   31-criterion list in design §5.4 cite these IDs.
2. **One home per criterion, never restated.** A criterion lives in the spec
   whose task builds it. When tasks in two specs build it, the home is the
   upstream one, so the later task can cite it. A task cites criteria of its
   own spec or of a spec it depends on, written `00004 WF-004 criterion 8`. A
   template or a test does not count as a builder. Each requirement block
   carries a pointer line for the criteria that live elsewhere.
   *Amended 2026-10-04 while assigning criteria.* The approved wording ("the
   spec whose task verifies it", with split criteria shown in both specs)
   would have restated dozens of criteria (my estimate) in 00009, whose tasks
   re-prove them on real hosts. The amended rule restates none.
3. **Shared framing lives once, in 00001.** Purpose, goals, non-goals, actors,
   and terms stay in `00001-initial-delivery`; the other specs cite it by
   number and restate nothing. Non-functional requirements go to the spec they
   bind.
4. **Text moves, it is not rewritten.** Criteria, contracts, and task details
   are carried verbatim into the shapes of design §6.2 to §6.4. Anything I add
   (a `Source:` line, a `Location:`, a new ID) is listed in that artifact's
   approval summary.
5. **Intake.** 00001 keeps its item, with `qa-log.md`, `graduate/`, and the
   source documents, and gains an `idea.md` that names them. Specs 00002 to
   00009 each get an intake item whose `idea.md` names 00001 and its slice
   (design §6.7). Each item moves to `intake/processed/specflow/` when its
   requirements artifact is first written.
6. **No runtime, so no sidecar.** Each spec folder gets `.config.kiro` and no
   `.specflow.json`. Approvals are dated receipts in the item's `qa-log.md`.
   Nothing is machine-validated until the helper (T-026) exists; specflow's
   recovery mode (WF-004.4) then records the real approvals.
7. **Paths.** `.agents/specflow.json` sets root `docs/dev/project-management`
   and specs folder `docs/dev/project-management/specs`, as in calcard-mcp.

## One deviation from the phases

T-081 (verify the conversion against the calcard-mcp fixture) moves from
phase 5 to `00009`. It needs T-050 from phase 7, while T-057 in phase 7 needs
T-080 from phase 5. Left in place, 00007 and 00009 would each wait for the
other.

## Findings so far

- **F1, confirmed.** The source phases are not a clean order at spec level:
  T-081 (phase 5) depends on T-050 (phase 7). Fixed by the deviation above.
- **F2, confirmed.** specflow has no rule for a task that serves a requirement
  owned by another spec. A layered product hits this at once: a template, a
  validator check, an instruction, and an eval all serve one criterion.
  Resolved by decision 2026-10-04 #9: rule 2 stands, and the contract gains
  ART-004.16 and VAL-001.13.
- **F3, suspected.** PKG-002.6 (publish through a distribution branch when a
  host needs `plugin.json` at a repository root) has no task; design §17
  defers it, while requirements §9 defers nothing.
- **F4, confirmed.** The success measures (§8) and the full-delivery clause
  (§9) carry no IDs, so no task can cite them. They become `REL-002` and
  `REL-003`.
- **F5, consequence.** A spec waits for its whole prerequisite, so T-070,
  which needs only T-001, waits for all of 00004.
- **F6, confirmed.** The requirements template in design §6.2 has no parent
  heading for the requirement blocks, so they nest under `## Assumptions`. The
  drafts add `## Requirements`, as Kiro's own documents do.
- **F7, suspected.** T-053 checks that the user documentation states the
  one-writer contract, but T-061 writes that documentation later, in a spec
  that depends on T-053's.
- **F8, confirmed.** No task writes `references/state-contract.md` or
  `references/profiles/{standard,quick}.md`, which the reference routing in
  design §5.2 loads on every invocation (no hit for either name in
  `tasks.md`).
- **F9, confirmed.** Requirement text cites design sections (`design §6.2`,
  `§7.1`, `§5.4`), although in requirements-first order the design is written
  after the requirements are approved.
- **F10, consequence.** 00008 owns a single criterion: its five tasks prove,
  on the real package, criteria that 00002 owns.
- **F11, suspected.** VAL-001.9 lists "a `(guess)`" as a marker without
  excluding inline code, as VAL-001.8 does for placeholders. specflow's own
  criteria name the token in inline code (WF-002.7, VAL-001.9, ART-002.10),
  so a plain scan would report them as open markers.

Found while the designs were drafted (2026-10-04). Each waits for a ruling in
`2026-10-04-specflow-design-gates.md`. The number F14 is not used.

- **F12, confirmed.** `scripts/validate.py` fails a skill folder with no
  `SKILL.md`, and tasks of 00003, 00004, and 00005 write into
  `plugins/specflow/skills/spec-workflow/` before T-030 (00006) writes the
  skill. Decision D1.
- **F13, confirmed.** No task creates `references/artifact-contract.md`;
  T-030 edits it as "the existing" file. The 00004 design gives it to T-020.
  Decision D2.
- **F15, confirmed.** The host loading probe of T-006 runs no bundled script,
  while recording an approval needs the helper on every host. Decision D3.

## Order of work

1. On approval: write the config, the intake items, and the spec folders, log
   the split in the 00001 `qa-log.md`, commit.
2. Draft the nine requirements artifacts, each with its pointer lines. Run the
   coverage check. Ask for approval.
3. Draft the designs in dependency order, each through the review pre-pass.
   Ask for approval.
4. Draft the task plans in the §6.4 shape. Ask for approval.
5. Close with a receipt per item: paths, coverage, gate states, limits.

## Rulings on the findings

Decision 2026-10-04 #9 resolved F2. Decision 2026-10-04 #10 took the
recommended fix for F3, F7, F8, and F11:

- F3: applied. PKG-002.6 is dormant; 00002 records the assumption.
- F11: applied. VAL-001.9 in 00005 lists a `(guess)` marker only outside
  inline code and fenced blocks. Design §7.1 of the source says "any
  `(guess)`", so the 00004 design must match when it is written.
- F7: queued. When the task plans are written, T-053 (00009) loses its check
  of the user documentation and T-061 (00001) gains it.
- F8: queued. When the 00006 design and task plan are written, T-030 names
  `references/state-contract.md`, `references/profiles/standard.md`, and
  `references/profiles/quick.md` among its outputs.
- F9: no edit. The `design §n` citations in criteria stay as pointers into
  the source design, which remains in intake item 00001.

## Gate status

| Gate | State | Evidence |
|---|---|---|
| Requirements, 00001 to 00009 | approved 2026-10-04 | text at commit `b6112ad`; a receipt in each item's `qa-log.md` |
| Design, 00001 to 00009 | approved 2026-10-05; corrected (27 findings) and approved again 2026-10-06, each with a receipt that names the file's git blob | every source design line carried once (`gen_design.py`); pre-pass minutes in each item's `qa-log.md`; the decisions waiting for the developer in `reviews/2026-10-04-specflow-design-gates.md` |
| Tasks, 00001 to 00009 | approved 2026-10-06, each with a receipt that names the file's git blob | every source task line placed once (`gen_tasks.py`); review minutes in each item's `qa-log.md`; the decisions in `reviews/2026-10-05-specflow-tasks-gates.md` |

Accepted by name at the design gate: two unresolved questions in 00003 and
one in 00004. The one in 00005 was answered by ruling D8. Rulings D8 and D9
changed the requirements of 00005 and 00009, approved again on 2026-10-04.
At the tasks gate (2026-10-06) the 46 guessed risk ratings of eight designs
were confirmed, and the three questions accepted by name once more. Checks kept for later stages, in the ignored scratch
folder `docs/dev/tmp/specflow/split/`: `check_split.py` (task and dependency
map) and `gen_requirements.py` (criterion coverage; check-only unless run
with `--write`).

## Unresolved questions

- One explicit answer approved the nine requirements artifacts (Q14). Whether
  the design and tasks gates may be batched the same way is the developer's
  call at each gate.
- Whether ART-004.16 and VAL-001.13 join the required-criterion list (open in
  00005 until its design gate).
