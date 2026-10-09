# Tasks gates: specflow specs 00001 to 00009

Date: 2026-10-05
Status: closed on 2026-10-06. Every decision is answered and applied, and the
nine designs and nine task plans are approved (see Decisions at the end).

Agenda: one decision on how to treat 27 findings against the approved
designs and six late fixes in the plans, six smaller decisions, then the
nine task-plan approvals.

## Where things stand

| Spec | Tasks | Review | Recheck | Late fixes, unread | Design findings |
|---|---|---|---|---|---|
| 00002 package boundary | 6 | no blocker | not needed | none | 2 |
| 00003 AWS sources | 4 | no blocker | not needed | none | 2 |
| 00004 artifact and state | 10 | 2 blockers | both confirmed fixed | 1 | 5 |
| 00005 behavior rules | 3 | no blocker | not needed | none | 3 |
| 00006 runtime skill | 11 | 2 blockers | both confirmed fixed | 4 | 4 |
| 00007 reviews and conversion | 7 | 2 blockers | both confirmed fixed | none | 3 |
| 00008 host integration | 5 | no blocker | not needed | none | 2 |
| 00009 cross-host validation | 10 | 1 blocker | confirmed fixed | none | 4 |
| 00001 initial delivery | 8 | 1 blocker | confirmed fixed | 1 | 5 |

"Late fixes, unread": the recheck confirmed every original blocker, but in
three plans it found new problems that my own fixes had introduced. I fixed
each as the reviewer proposed. specflow allows one recheck, so nobody has
read these six fixes:

- 00004: a sentence of T-026 said the helper records an approval's values;
  it now says the helper gives the values and the agent writes them.
- 00006: T-036 now depends on T-072; the bugfix rules of T-038 are
  behavioral, and T-039 enters no inventory rule; three texts of T-030 carry
  no rule tag until the task whose session proves them; the re-entry of one
  rule moved from T-035 to T-034.
- 00001: T-065 no longer changes the changelog date after the package is
  verified; T-062 writes the date.

How the plans were made: each `tasks.md` is assembled by script from the
source plan in intake item 00001. Source bullets are carried word for word,
and the fields the approved task shape adds (Location, Contract, Acceptance
criteria, and so on) come from the approved designs. The script checks that
every source line is placed once (427 carried, 52 reworded or retired, each
with a reason), that every criterion a spec holds is cited by a task, that
every dependency names an earlier task, and that every quoted contract
appears word for word in its design. One criterion has no task by the
developer's earlier ruling: PKG-002 criterion 6 (the dormant distribution
branch).

Seven isolated reviewers then read the plans against their designs and
requirements. They raised 8 blockers, about 90 smaller points, and 16
questions; every one is applied in the plans, and the five plans that had a
blocker were rechecked once. Detail is in each spec's `qa-log.md`.

## T1 · The approved designs contradict themselves in 27 small places

- What: writing the task plans, and then reviewing them, exposed places
  where an approved design says two things, or names a file for no task.
  None changes what specflow does. The task plans already state the right
  thing in each case, so the plans and the designs now disagree in wording.
  Beside them stand the six late plan fixes above, which nobody has read.
- Evidence (confirmed by the reviewers, one by a run): the list below.
- If unchanged: an implementer who reads the design first is misled in
  those places, and the planned `placement-drift` check would warn on four
  plans.
- Options:
  1. (Recommended) I edit the designs to say what the task plans say, the
     27 edits below and nothing else. Reviewers then make one last pass over
     those edits and over the six late plan fixes. After that you approve
     the corrected designs and the task plans together. Benefit: designs and
     plans agree, and everything changed late has been read. Drawback: nine
     approved designs change again, and the one-recheck rule is bent a
     second time. Effort M.
  2. I edit the designs, with no further review, and you approve. Benefit:
     fastest way to agreeing documents. Drawback: 27 design edits and six
     plan fixes go unread. Effort M.
  3. Leave the designs; reviewers recheck only the six late plan fixes.
     Benefit: no approved artifact changes. Drawback: known contradictions
     stay in approved designs. Effort S.
  4. Leave everything and go to the approvals. Benefit: no more rounds.
     Drawback: contradictions stay, and six fixes stay unread.
- Strongest reason against option 1: it reopens designs you approved a few
  hours ago, and it is one more review round.

### The 27 findings and the edit each would get

00002 package boundary:

1. Rollout says the boundary is enforced "from the first commit that has a
   package", but the CI steps arrive with T-005, after T-002. Edit: say it
   holds from T-005 on.
2. The placement table gives T-006 no row for the 00008 design it corrects.
   Edit: add the row.

00003 AWS sources:

3. T-011 extends the test fixture `make_package` with files under a skill
   folder, and a skill folder with no `SKILL.md` fails the validator that
   the release check calls (confirmed by a run). Edit: the fixture also
   gets a minimal `SKILL.md`.
4. The placement table gives T-018 no row for the cursor file its first
   catch-up advances. Edit: add the row.

00004 artifact and state:

5. `templates/specflow.json` is given to T-020 in one sentence and to T-028
   in the placement table. Edit: T-028, in both places.
6. T-028 and T-029 must edit `validate_spec.py` and `checks.py`, which the
   placement table gives only to T-026 and T-029. Edit: add the rows, and
   say `status` fills `problems` from the check registry.
7. The number scan is called "recursive" in one place and limited to two
   levels in another. Edit: keep the limit.
8. Two drift test cases ("native placement", "missing placement") name
   something the helper never reads. Edit: say they reach the helper as
   paths or as a stored value.
9. T-023 (invalidation) has no function in the helper layout, so nothing
   carries "which change made this stale". Edit: name one function,
   `stale_causes(spec_dir, state)`, in `state.py`.

00005 behavior rules:

10. The placement table gives the CI file to T-070 only, while the rollout
    has T-071 change it. Edit: add the row.
11. The table names a fixtures folder; the testing section says fixtures
    are built in temporary folders. Edit: drop the folder.
12. "One coverage row per required criterion" ignores that a criterion may
    have several rules. Edit: one row per criterion and rule.

00006 runtime skill:

13. Two rules that act after intake are placed in `SKILL.md`, which only
    T-030 and T-037 may edit, but the sessions that prove them are T-031's,
    so T-030 could not pass its own check. Edit: T-031 writes them.
14. The session `resume-after-intake` is said to continue "on another
    host"; the session format and the runners have no way to say that.
    Edit: "in a new conversation"; resuming on another host is proven by
    the handoff of T-051.
15. T-039 registers five bugfix checks and lists four seeded defects. Edit:
    add the fifth.
16. The 00004 design hands two agent cases (a group folder kept on a move,
    a file name that matches two files) to "sessions of 00006", and this
    design names no session for them. Edit: name them under T-031.

00007 reviews and conversion:

17. The design review's pre-pass has rules only in the second port plan,
    which arrives with a later task, and the design does not say how T-075
    tags them. Edit: they are rules sourced from the requirements until
    T-079 adds the plan rows. It also lacks the sentence that scenario
    checks are scored later, in 00009. Edit: add it.
18. "The only failures left are the eight script rules" may miss three
    more script-like rows. Edit: "the script rules, whose checks are tests
    of T-077".
19. The placement table lists no row for the routing test, the inventory,
    the eval records, or the CI file that its review tasks edit. Edit: add
    the rows.

00008 host integration:

20. A record holds the status document "at its end", yet two later tasks
    append to the records; and "every to-be-verified line is gone" cannot
    hold while five prose lines use the phrase. Edit: reword both.
21. The traceability table has no row for the marketplace generator. Edit:
    add one that names the Claude Code install line it serves.

00009 cross-host validation:

22. The scenario table puts "modify requirements in Claude Code" into the
    handoff record, but the five handoff steps hold no such edit, and "a
    task completed in Kiro shows elsewhere" is never shown. Edit: add the
    step, and a second host order in which Kiro implements.
23. Parity inputs are "the skill's own examples plus the fixtures", but
    specflow's results exist only for session fixtures. Edit: the inputs
    are the fixture and turns of each session that carries the skill's
    rules.
24. A note is wanted "in the manual record", and a run that stops early is
    to be "recorded as not run, with the reason"; the run record has no
    field for either. Edit: an optional `notes` field and an optional
    `notRun` field holding the reason.
25. The folder tree lists the concurrent-edit test under the wrong folder.
    Edit: correct the comment.

00001 initial delivery:

26. Four placement and listing gaps: a test named under T-066 that T-061
    must write; no rows for the catch-up report and cursors that T-064
    produces; the third procedure linked from nowhere; the tested tree id
    missing from the report's contents. Edit: fix each.
27. Security says every push to another repository waits for your
    instruction, while Open decisions names only T-065. Edit: name T-066
    and T-067 too.

## T2 to T7 · Smaller decisions

Each has a choice already made in the plans; say if you want another.

| # | Decision | Chosen in the plans | Main drawback |
|---|---|---|---|
| T2 | Where does the merge of `feature/specflow` fall relative to the release candidate and the tag (00001)? | not chosen; proposed: merge first, so the candidate and the tag are on the default branch | the public marketplace route cannot be tried before the merge |
| T3 | 00001 may cite only specs on its `Depends on:` line, and 00004 is not there, so T-061's check of the one-writer contract cites no criterion | leave it uncited; the test exists | one check with no criterion behind it |
| T4 | Some rules of `phases/implementation.md` have no criterion to name as their source ("one coherent task at a time") | the task reports such a rule in its `Outcome:` line; it needs your ruling before T-035 starts | a rule with no source cannot be entered in the inventory |
| T5 | The 46 guessed risk ratings in eight designs, not yet confirmed | open; they must be confirmed or accepted by name before a task plan is approved | confirming means vouching for estimates |
| T6 | PKG-002 criterion 6 (the distribution branch) has no task | stays dormant, by decision 2026-10-04 #10 | one criterion with nothing built |
| T7 | Which date the 0.1.0 changelog heading carries | the day T-062 writes it; changing it later makes a new release candidate | the heading may show a day before the tag's |

Choices the plans make that no approved design states, named here so that an
approval covers them knowingly:

- 00001: the release checklist asks that a change to the artifact contract,
  the state schema, the phase gates, or an upstream reference came with its
  fixtures and tests (a rule of the source plan that no design held).
- 00007: the `conversion-receipt` check runs in every phase from
  `requirements` on; T-076 adds no rule of area `SKL`.
- 00009: the scorer's entry function takes the folder of evals as a
  parameter, so a deliberately broken test eval never sits among the real
  ones.
- 00004: T-023 adds one function beside `artifact_status` and records its
  name in its `Outcome:` line (finding 9 would name it in the design).

## The nine approvals

After the decisions above: the task plans of 00002, 00003, 00004, 00005,
00006, 00007, 00008, 00009, and 00001, in that order.

## Decisions (filled in during the walkthrough)

- T1, 2026-10-05: option 1, "Fix designs, one last check (Recommended)".
  The 27 listed edits go into the designs and nothing else; reviewers make
  one last pass over those edits and over the six late plan fixes; the
  corrected designs and the task plans are then approved together.
- Last check, 2026-10-05: all 27 design edits confirmed right, and all six
  late plan fixes confirmed. The check found two more faults in the plans,
  each from a reviewer's own earlier suggestion: a check command in T-018
  that cannot run (00003), and the check kind `test:` left out of T-070 and
  T-071 (00005). Both are corrected as the reviewers worded them and have
  not been read again. A dozen wording leftovers were applied; one is left
  as it is (00007: "each task" against T-077). Minutes in each `qa-log.md`.
- T2, T3, T4, T7, 2026-10-05: all four choices accepted. The feature branch
  is merged before the release candidate is verified (a `Premise:` of
  T-063). T-061's check of the one-writer contract stays uncited. In
  `phases/implementation.md`, "one coherent task at a time" is sourced
  `R:ART-004.5` and routing an upstream error through invalidation
  `R:WF-002.5` (T-035). The 0.1.0 changelog heading carries the day T-062
  writes it. T6 stands by decision 2026-10-04 #10. T5 is asked with the
  approvals.
- Approvals, 2026-10-06: "Approve all, confirm ratings (Recommended)". The
  nine corrected designs are approved again and the nine task plans are
  approved, the three open upstream questions accepted by name, and the 46
  guessed risk ratings confirmed (their marks are gone). The two unread
  corrections of the last check (00003, 00005) were named in the question
  and are accepted with it. A receipt with each file's git blob is in each
  `qa-log.md`.
