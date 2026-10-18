---
prd: docs/dev/project-management/specs/00006-runtime-skill/requirements.md
review: 2
date: 2026-10-18
head_sha: c98fe5b0bbe9a35c69d252f66a07ab10c9fc72e4
codex_thread_id: 01a15087-f247-7902-b533-149773cf1a68
reviewers: alice,blake,bob,carl
agents:
  alice: available
  blake: available
  bob: available
  carl: available
  eve: disabled
---

# Review: 00006-runtime-skill

Diff range: `fe2434084357de03b7031cb186933ccd13c9d9cc..c98fe5b0bbe9a35c69d252f66a07ab10c9fc72e4`

codex_rung_guard: not fired

## Review Summary

Cycle 2, an incremental review of the cycle-1 rework (`1450b6e`, `93139f4`, `de90b0e`, `c98fe5b`) against the same standalone inputs. The ledger (five accepted rows) and the cycle-1 findings with their dispositions were handed to Alice and Bob; Blake stayed blind and his three re-raises of ledger rows (F4, F10, F17) were absorbed by the ledger.

Alice verified every cycle-1 fix in the code and found two follow-ups: the reworded SR-SKL-015 names a blocker "fix" and "question" that the status document does not hold (F1, with Blake, 2/4), and the F12 wording change has no eval that would catch its regression (F4). Bob found one gap left by F8 (F6): only edge-source mockups are read, so an unreadable terminal-screen page passes. Carl found nothing. Blake raised two 🟠 lines, both downgraded to 🟡 by the lead with the evidence under "Lead's checks": SR-INT-052 names no `path` for the three state records (F2), and `placement-drift` reads only inline-code paths (F3). Each is a real gap with a one-clause or one-function fix, and neither breaks a required behavior: the state contract, loaded on every invocation, defines the record with its path, and the drift warning is advisory by ART-004.15. After the lead's checks the cycle holds no 🔴 and no 🟠, so it converges under the autopilot bar; the rework is a Medium/Low sweep.

### Agent Status

- Alice: ✅ Available (legacy consensus engine)
- Blake: ✅ Available
- Bob: ✅ Available (codex, after one retry (inlined)). The resumed-thread run (`--resume-thread 01a148cf-…`) refused for lack of input: both reads failed with `sandbox_apply: Operation not permitted`, one `[BOB] ⚪ Cycle 2 review remains unverified` line under VERIFY and every `R{n}` set to fail. That output is kept at `docs/dev/tmp/bob-output-00006c2-first.txt`. The one retry used the inlined prompt (201 KB: context, diff and the persona) without `--resume-thread`; the `codex_thread_id` above belongs to the retry.
- Carl: ✅ Available (copilot backend, `gemini-3.8-flash`, exit 0, first run)
- Eve: ⏸️ Disabled (`doubt_reviewer` resolved to codex; no state file, so no record of codex-implemented tasks)

### Run notes

- pack: failed (`engram pack exit 1: not inside a registered repo` for this worktree). Degraded, not invalid.
- Gate: `review-stage` ran the seven CI steps through the worktree-local `gate.sh` (exit 0; counts from the logs): `scripts` 12, release 53, contract 359, rules 58, all OK; `validate.py`, `check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER` and `verify_release.py` exit 0. Python 3.10.22: contract 359 OK at `c98fe5b`, rules 58 OK at `de90b0e` (the two commits after it touch no Python).
- Fail-first replay: `python3 -m pytest` listed eight touched tests passing at base, all of them the F9 coverage tests (F11 below). The lead's unittest runs before the fix commit (recorded in the cycle-1 outcome) showed the three defect tests failing at the pre-fix tree and those eight passing, as coverage of branches that already existed.
- Consolidation: `consolidate_findings.py --ledger … --ledger-dismiss blake` gave ten rows and dismissed Blake's three ledger re-raises (F10 WF-002.8, F17 `aws/implementation.md:87`, F4 review routing), each with the ledger reason. No merge warning. Refs renumbered from the script's `R1`..`R10`; the `[MECH]` line is F11.
- Carl's shell left `tests/specflow/contract/__pycache__/`, removed with `git clean -X -d -f -- tests`; an older `scripts/__pycache__/` from 2026-10-17 was removed the same way. The tree is clean.
- Lead's checks:
  - F1: `status.py:76-80` and `:115-119` build each blocker from `gate`, `reason` and `reference` only; the dependency and validation blockers (`:183`, `:205`) have the same keys. Confirmed; the rule's "its fix" and "that blocker's question" name fields that do not exist, and with several blockers it does not say which one. The fix names the first blocker in `blockers` order and its `reason` and `reference`.
  - F2: SR-INT-052 says "the three artifact records with status `missing`" and nothing about `path`; the state schema requires `path`, so Blake's literal state fails `state-valid`. Downgraded to 🟡: `references/state-contract.md:10`, loaded on every invocation (SKILL.md step 1, design.md:316), defines each record as `path`, `status`, `sha256`, so the record shape is in the agent's context whenever SR-INT-052 runs, and the T-031 detail that produced the sentence (tasks.md:52) had the same wording, so the gap came in with the plan. The fix names the three paths, with `bugfix.md` for a bugfix, and the SR-INT-052 eval asserts the `path` field.
  - F3: `placement_drift` collects `Location:` paths with `CODE_SPAN` only (`phase_checks.py:246`), and Blake's plain-path plan draws no warning. Downgraded to 🟡: ART-004.15 makes the warning advisory and `placement-drift` never closes a gate; the T-034 outcome recorded the inline-code choice (tasks.md:145); the design's own placement table and every plan in this repository write paths in inline code. Still a gap against ART-004.15's "task Locations", fixed by reading plain comma-separated paths as well.
  - F4: `SR-DLG-013.json` checks the qa-log, the three artifacts and `.specflow.json`; `SR-INT-001.json` checks that `idea.md` exists and holds the idea; `SR-INT-057.json` checks the copied `notes.md`. No session puts a secret in the first message or in an input file. Confirmed. The sweep adds a synthetic key to the first turn of `intake-two-unknowns` with `file_lacks` and omission-note assertions on `idea.md`, and a `file_lacks` on the intake item's `idea.md` to SR-DLG-013; the input-file case needs a session of its own and is deferred (ledger).
  - F5: SEC-002.4 is general ("Destructive cleanup or migration SHALL identify exact targets and require explicit authorization when recovery is uncertain"), and the approved design maps it to the spike path and spike cleanup only (`design.md:402`: SR-INT-043, SR-VER-002), with SEC-002.1 on SR-SKL-012 and SEC-002.3 on SR-IMP-004. A general rule would be a new `R:SEC-002.4` rule in `phases/implementation.md` with an eval record, and a design-mapping edit. A design-scope question for the developer.
  - F6: `link_findings` reads `pages` for edge sources only (`phase_checks.py:197`); a terminal screen's mockup is never opened, so a non-UTF-8 `done.html` passes. Confirmed; the readability pass now covers every screen's mockup once.
  - F7: the spike time-boxes are design text (`design.md:193-194`: "about ten minutes", "about twenty minutes", "about an hour"), the three-level search is design text (`design.md:172`), and SR-TSK-006's count pin is Plan A row PRD-32 (`inventory.json:182`), an adopted source passage. Rejected.
  - F8: the every-invocation path is the design's (`design.md:316`), and `design.md:141` says `status` "is all a status request runs". Rejected: by design.
  - F9: the check table (`design.md:254`) defines `sketch-screens` as the screen-to-file mapping, orphan mockups and edge links; the other sketch rules are behavioral SR-INT rules by design. Rejected.
  - F10: the `[quick]` "~2-4 per stage" passage is F5 (b) of cycle 1, accepted in the minutes as covered by the source's "guidelines, not hard caps" and the precedence line, now widened to the phase rules. Accepted; ledger entry added with the sweep.
  - F11: the eight tests are the F9 coverage tests of cycle 1; their branches existed at base, so passing there is expected. A fact.
- No verification-check queue, dispatch rows, contract card or session brief (standalone run, no autopilot state).

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| F1 | [2/4] | 🟡 | SR-SKL-015's next-action and blocking-question mapping names helper fields that do not exist: "a blocker, then its fix, and that blocker's question". Each `status --json` blocker holds only `gate`, `reason` and `reference`, and a spec with an unapproved first artifact carries several blockers, one per gate, with no rule for which to pick. Say that both come from the first blocker in `blockers` order, built from its `reason` and `reference` | plugins/specflow/skills/spec-workflow/SKILL.md:77 | T-037 | ALICE, BLAKE |
| F2 | [1/4] | 🟡 | SR-INT-052 tells the agent to write `.specflow.json` with "the three artifact records with status `missing`" and names no `path`; the state schema requires `path`, and a state written literally fails `state-valid` (`missing required field path`, exit 2), which SKILL.md says is left as it is. The instruction does not say `bugfix.md` is the requirements path for a bugfix. Downgraded from 🟠 by the lead: `state-contract.md:10` defines the record shape and is loaded on every invocation | plugins/specflow/skills/spec-workflow/references/phases/intake.md:33 | T-031 | BLAKE |
| F3 | [1/4] | 🟡 | `placement-drift` is blind to `Location:` paths not in inline code: `phase_checks.py` counts backticked paths only, nothing tells the agent to backtick them (the template placeholder is `<bounded repository-relative paths>`, SR-TSK-010 says nothing), and a plan with three plain unplaced paths validates with no warning. Downgraded from 🟠 by the lead: an advisory warning that closes no gate, and the recorded T-034 choice | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:241 | T-034 | BLAKE |
| F4 | [1/4] | 🟡 | The F12 fix has no eval that would catch its regression: SR-DLG-013, SR-INT-001 and SR-INT-057 changed, their eval records did not. SR-DLG-013 never checks the intake item's `idea.md`; the one synthetic secret arrives as a mid-dialogue answer; no session puts a secret in the first message or in a copied input file | tests/specflow/evals/SR-DLG-013.json:1 | T-031 | ALICE |
| F5 | [1/4] | 🟡 | SEC-002.4 ("destructive cleanup or migration SHALL identify exact targets and require explicit authorization when recovery is uncertain") is carried only by spike deletion (SR-INT-043, SR-VER-002) and the existing-spec-folder rule (SR-SKL-012); no general rule covers a cleanup or migration task. The approved design maps SEC-002.4 to the spike path only (`design.md:402`), so this is a design-scope question | plugins/specflow/skills/spec-workflow/SKILL.md:60 | T-030 | BLAKE |
| F6 | [1/4] | 🟡 | F8 left a gap: `link_findings` reads only edge-source pages, so an unreadable terminal-screen mockup passes because it has no outgoing edge. Read every screen's mockup once and add a terminal-screen test | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:193 | T-072 | BOB |
| F7 | [1/4] | ⚪ | Parameters not in the requirements: the spike time-boxes, the three-level nested-repository search, and SR-TSK-006's test-count pin. Rejected by the lead: the first two are design text (`design.md:172`, `:193-194`) and the pin is Plan A row PRD-32 | plugins/specflow/skills/spec-workflow/references/phases/intake.md:85 | T-031 | BLAKE |
| F8 | [1/4] | ⚪ | The Performance NFR says only current-phase references enter context, yet step 1 loads `artifact-contract.md` and `state-contract.md` on every invocation, a status request included. Rejected by the lead: the design's every-invocation path (`design.md:316`) | plugins/specflow/skills/spec-workflow/SKILL.md:18 | T-030 | BLAKE |
| F9 | [1/4] | ⚪ | The sketch rules for mockups (not functional, accessibility note, no invented action, no feature missing from the rough spec) are instructions only; `sketch-screens` checks the mapping, orphans and links. Rejected by the lead: the check's scope is the design's (`design.md:254`) | plugins/specflow/skills/spec-workflow/scripts/specflow_helper/phase_checks.py:106 | T-072 | BLAKE |
| F10 | [1/4] | ⚪ | The `[quick]` passage of `aws/requirements.md` says "~2-4 per stage" with no adaptation line, while quick's range is 0-2; the precedence line covers it, but the text is mixed. Cycle-1 F5 (b), accepted | plugins/specflow/skills/spec-workflow/references/aws/requirements.md:62 | T-032 | BLAKE |
| F11 | [1/4] | ⚪ | Eight touched tests pass against the pre-change code: the F9 coverage tests of cycle 1, which exercise branches that already existed. A fact | tests/specflow/contract/test_phase_checks.py:92 | T-072, T-039 | mech-check |

Overlap: F1 and F2 are one-clause wording fixes in rule text; F3 and F6 are small `phase_checks.py` changes with a fail-first test each; F4's partial fix touches one session and two eval records; F5 is a design-scope decision.

## Alice

Legacy consensus engine; she read the staged files, re-ran `test_phase_checks.py` (34 OK), `scripts/validate.py` and `check_rules.py` over the nine areas, and checked `status` on 00006 (all approved, nothing stale, no blocker, no warning). She verified F1, F2, F5 to F11, F13, F14, F19 and F20 of cycle 1 as resolved and F3 and F12 as partly resolved. Findings: F1, F4.

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Blind lens: the PRD only, no diff, no history. He ran the contract suite (359 OK) and `scripts/validate.py`, wrote the SR-INT-052 state and the plain-path plan under the scratchpad to reproduce F2 and F3, and confirmed that Outcome and checkbox edits leave the bugfix `tasks.md` canonical hash unchanged. Findings: F2, F3, F5, F7, F8, F9, F10, plus F1 as ⚪ and three ledger re-raises (absorbed).

B1: fail
B2: fail
B3: pass
B4: pass
B5: pass
B6: fail
B7: fail
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: fail
B17: fail
B18: fail
B19: fail

## Bob

Codex, doubt lens, inlined retry after the resumed-thread refusal. He verified the cycle-1 fixes against the inlined diff and raised one gap. FIX: the unreadable terminal mockup (F6). VERIFY: none. KNOWN: none.

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: fail
R11: pass
R12: pass
R13: pass

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Carl

Copilot backend, `gemini-3.8-flash`, exit 0, first run. He read the context and diff and ran the suites. `[CARL] ✅ No issues found`.

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

Verdict: 11 findings

Tests: 482 passed, 0 failed, 0 skipped (suite run this cycle)

## Walkthrough minutes (2026-10-18)

The cycle converges under the autopilot bar (no 🔴, and no 🟠 after the lead's checks). The developer confirmed the two downgrades ("Downgrades stand, converge (Recommended)") and ruled F5 "Accept by design (Recommended)"; the other rows take the lead's dispositions. The rework is the Medium/Low sweep, and no cycle 3 runs.

- F1: fix. SR-SKL-015 takes the next action and the blocking question from the first blocker in `blockers` order, built from its `reason` and `reference`. Queued.
- F2: fix. SR-INT-052 names the three records' paths, `bugfix.md` for a bugfix, and points at the state contract's record shape; the SR-INT-052 eval asserts the `path` field. Queued.
- F3: fix. `placement-drift` reads plain comma-separated `Location:` paths as well as inline code; fail-first test with Blake's plan. Queued.
- F4: fix in part. The first turn of `intake-two-unknowns` carries a synthetic key; SR-INT-001's eval asserts that `idea.md` lacks it and notes the omission; SR-DLG-013's eval asserts that the intake item's `idea.md` lacks the mid-dialogue secret. The input-file case (SR-INT-057) needs a session of its own: deferred (ledger entry).
- F5: accepted by design (ledger entry). The approved design maps SEC-002.4 to the spike path; the skill itself deletes only spikes and, with approval, spec folders (SR-SKL-012); a developer's destructive task carries its premise (SR-TSK-004, SR-TSK-006) and runs under the premise re-check of `phases/implementation.md`.
- F6: fix. The readability pass reads every screen's mockup once; fail-first test with a non-UTF-8 terminal page. Queued.
- F7, F8, F9: rejected with the evidence above.
- F10: accepted (ledger entry), cycle-1 F5 (b).
- F11: a fact.
