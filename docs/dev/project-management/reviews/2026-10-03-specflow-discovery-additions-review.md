# Specflow discovery additions: doubt review — 2026-10-03

Status: report and walkthrough complete. All eight user rulings applied:
F1/F2/F3/F5/F6/F7/F8 option 1 and F4's full-feature ruling.
The user has superseded the two-slice plan: all accepted features and planned
checks gate 0.1. Earlier deferral recommendations below are historical and no
longer proposed. The original review describes baseline `1ee379c`;
subsequent changes are recorded in the minutes.

Reviewed baseline: `feature/specflow` at `1ee379c`, version 0.3. Working tree
was clean, no upstream, no stashes. Scope is exactly the supplied 31 criteria:
23 new and 8 changed. Decisions 2026-10-03 #1–9 were the settled review
constraints; the user subsequently superseded #4 in the walkthrough. The
initial proposals below are historical; the minutes record the binding rulings.

## Result

All 31 criteria remain in the initial release. Their eight interaction and
verification defects are corrected in the specification, with tasks and checks
assigned. No feature or planned proof is deferred. Fourteen initial doubts
resolved as eight fixes, five verified dismissals, and one remaining live-Kiro
verification limitation: host capture/evals require the future implementation
and remain release gates, not evidence claimed by this documentation review.

### Initial review result (baseline, before user rulings)

The additions mostly earn their place, but the set is not ready to implement
unchanged. Eight findings concern their interaction, implementation contracts,
or verification. The strongest problems are cross-phase dialogue rules loaded
only in requirements, an incomplete cross-spec dependency contract, and intake
questions that compete for the same small budget. Neither a new upstream
pipeline nor link machinery is justified by these additions.

Keep the inexpensive discovery, provenance, language, logging, and fence rules.
Keep the user's progress line, working practices, and sketch capability; the
findings propose making their behavior coherent, not reversing those choices.
Consider moving the complete **code-drift advisory capability** to slice two.
The dependency capability is another possible whole-capability deferral, but
retaining it with a small explicit contract protects the named external runner.
No removal or deferral has been applied.

## Evidence and coverage

Local citation keys (line numbers refer to `1ee379c`, before any rulings):

- **R**: [requirements.md](../intake/processed/specflow/00001-initial-delivery/requirements.md).
- **D**: [design.md](../intake/processed/specflow/00001-initial-delivery/design.md).
- **T**: [tasks.md](../intake/processed/specflow/00001-initial-delivery/tasks.md).
- **M**: [meta/decisions.md](../meta/decisions.md).
- **C**: [consolidated prior review](2026-10-03-specflow-docs-review-consolidated.md).

Read in full: R, D, T, the spec's `qa-log.md`, M, C, root `AGENTS.md`, and
`/Users/bob/.agents/skills/review-with-doubt/SKILL.md`. Read the complete
`974eff6..1ee379c` diff of the spec directory, in file-sized chunks; inspected
the four #10 additions in `38f6a71` separately. Machine enumeration confirms
31 criteria, 1,483 words in their current complete text (including the unchanged
parts of the eight changed criteria).

Upstream clones were read only; no upstream code, install, hooks, or tests ran.
Verified A1 `v2.10.0` peels to `2a883858f5483bce3b48f43b8f6d3ca2c042d6ae`;
A3 HEAD is `a84b2899d0dd518081a4764b42fde4c6dbf3cc9a`. Full files read for
attribution checking:

- A1: `core/aidlc-common/stages/ideation/{intent-capture,market-research,feasibility,rough-mockups}.md`,
  `stages/initialization/workspace-detection.md`,
  `stages/inception/{practices-discovery,reverse-engineering}.md`, and
  `core/aidlc-common/protocols/stage-protocol.md` (all 1,190 lines).
- A3: `README.md`; under `aidlc-discovery-rules/aidlc-discovery-rule-details/`,
  `technical/tech-env-interview.md`, `common/{question-format-guide,audit-format,content-validation,language-handling,session-continuity}.md`,
  and `shared/{greenfield-vs-brownfield,open-questions-collector,visual-sketch}.md`.

Search-only, not read in full: A3's other rule files and `src/`; the local
scratch cross-reference checker. The repo-structure plan
`~/.kiro/crew/workspace/ai-age-repo-structure.md` was partially read (tool output
was truncated); no new skill/config/link location is recommended here.
Not read: A2, the sixteen unexamined A1 stages, the other five previously read
initialization/ideation stages, and the five previously adopted A1 stages.
This is an attribution check of existing decisions, not another discovery pass.

Kiro's public [Specs](https://kiro.dev/docs/specs/) and
[Bugfix Specs](https://kiro.dev/docs/specs/bugfix-specs/) pages were read for
the document contract. They establish the three artifacts and bugfix behavior
sections; they do not prove acceptance of specflow's extensions. No live Kiro
capture or host run was performed. T-027 remains the existing verification step.

## 1. Overlap and contradictions

| Pair or group | Judgment and evidence |
|---|---|
| ART-002.12 / ART-002.16 | Complementary: free-text uncertainty versus an explicit undecided choice (R:142,146). One answer must produce one unresolved item, not two. The problem is over-broad treatment of an otherwise settled “for now” answer: F2. |
| ART-002.13 / ART-002.15 | Complementary links in a chain: evidence → inferred answer → requirement (R:143,145; D:609–612). A requirement can cite D1 without copying the discovery record. No reason to delete either. |
| WF-003.12 / .17 / .18 | Constraints from missing context, constraints already stated by the repository, and missing process preferences (R:311,316,317). Read applicable instructions first, reuse their answers, then ask only the remainder. Without that ordering and applicability rule they duplicate questions: F1/F7. |
| INT-001.5 / SEC-002.2 | Verbatim logging has an explicit secret-redaction exception (R:222,527; D:619). They do not conflict. A synthetic-secret fixture is missing from the named logging checks. |
| ART-002.10 / .15 | A sourced requirement can still contain a guessed contract detail; an entirely invented requirement cannot be legitimized by a `(guess)` tag (R:140,145; T:245). This is a coherent reading, worth showing in an eval. Source presence alone cannot prove the source supports the claim. |
| WF-002.1 / marker gate | Listing assumptions is disclosure, not confirmation or marker acceptance (R:284,290). Keep the named-acceptance contract; do not turn summary confirmation or artifact approval into automatic fact promotion. |
| WF-003.14 / strict invalidation | Compatible: raising review depth changes workflow metadata, not approved artifact bytes (R:287–290,313; D:688). A later content edit still stales approvals normally. |
| WF-003.18 / bugfix task order | Compatible under D:440–442: practices order only independent tasks; Kiro bugfix test-first dependencies still win (R:203–207). Add the mixed case to T-034 verification. |
| WF-003.13 / intake move | Compatible: persist choices before the first artifact question; move the intake item only when requirements are written (R:219,312; D:466). Design-First can therefore have a spec while its intake item remains in `new/`. |
| ART-002.18 / short intake / spike | Mandatory playback adds a stop before drafting, and the scope of that stop is unclear for spike `SPEC.md` (R:148; D:619,642). F1/F8. |

## 2. Settled decisions and release scope

| Settled decision | Effect of the additions |
|---|---|
| #2: pipeline cut | No contradiction. Local source lines and a discovery log do not require an upstream parser, normalizer, snapshots, or staged apply (M:158–163; D:245,951). F6 must be solved with explicit local criterion mappings, not by parsing all upstream prose. |
| #4: two slices | All 31 currently belong to slice one: R:597 excludes only the named slice-two items. They add authored behavior, eval records, and deterministic checks to 0.1; full per-host eval execution still belongs to slice two (D:1141–1146). Tasks saying “scenario tests” need this distinction made explicit, not a new release-wide host-eval gate. |
| #5: three hosts | No new supported host is added (M:174–176). Instruction discovery and questioning must work on all three. The no-HTML fallback in D:644 serves unnamed hosts and has no matching T-072 check: F8. |
| #6: no link machinery | No conflict. Nothing here warrants creating or repairing `.kiro/specs` links (M:177–180; R:120). Dependency lookups must use the configured specs folder. |
| #9: small fixes | Fence rejection reinforces the parsed-progress hash rule (M:186–189; D:720–723). Drift warnings must remain advisory and must not become locks, code snapshots, or a clean-tree approval requirement: F4. |

Largest 0.1 increments: cross-spec dependency lookup/gating (ART-002.11,
WF-001.9, STATE-003.1, VAL-001.5/.8); Git drift handling (WF-004.8,
STATE-001.2, the warning part of STATE-003.1); sketch generation and checks
(INT-002.8). The remaining additions predominantly extend existing references
and scenario assertions, although discovery classification needs precise cases.

Recommended slice-two candidate: **the whole drift capability**, including
`approvedCommit`, its schema/tests, warning generation, and documentation.
It is useful, but a commit-only approximation is not necessary to preserve the
already-decided artifact approval gates. Keep the generic `warnings` channel
for existing advisories. F4 offers keeping a deliberately limited version now.

Optional alternative, not the primary recommendation: defer the **whole new
spec-dependency capability**, including its Markdown line and helper behavior,
alongside cross-spec review. Do not ship a hard-gate-looking line that is silently
ignored. Retain existing `Blocks:` and `Supersedes:` behavior. F3 explains the
small contract needed if it stays in 0.1. Sketches are useful at intake and were
expressly chosen; F8 recommends simplifying their contract, not deferring them.

## 3. Question and confirmation load

There is no finite worst-case count in the current text. Bans, external systems,
instruction conflicts, ambiguous paths, and correction rounds can each multiply
questions. “About 0–2” is guidance, not a hard cap (D:892), but “within the
profile's question budget” in R:311,317 leaves no rule for competing mandatory
topics. Counting each independent requested answer as a question:

| Trigger | Added intake questions | Evidence |
|---|---:|---|
| Missing preservation boundary for existing feature code | 0 or 1 initial question | R:310 |
| One outside system: how to inspect it; what must stay unchanged | 2 if neither known; text does not explicitly waive already supplied answers | R:310 |
| Empty repository: binding constraints | At least 1 broad question; more if split into stack/security/test decisions | R:311 |
| Ban lacks reason and allowed alternative | Up to 2 follow-ups per ban if asked separately | R:311 |
| No example pattern | 1 | R:311 |
| Neither test order nor thin-slice preference known | 2 | R:317 |
| Applicable instruction conflict | 1 per unresolved conflict | R:316 |
| File path absent or ambiguous | At least 1 clarification round | R:225 |
| Sketch: design system and accessibility level | 2 before sketching, currently unconditional | R:242; D:644 |

Examples, not guaranteed bounds:

- Well-described existing change, all rules known: **0 new content questions**.
- Existing change missing preservation and the two practices: **3**, already
  above quick's usual 0–2 without any exceptional technical complexity.
- Empty repository, one outside system, unclear input path: **7 initial
  questions** even grouping technical constraints into one; add missing reasons,
  alternatives and conflicts. A sketch adds **2 more**. Such work may merit
  standard, but a quick override is expressly allowed (R:305,313).

Stops are separate from content questions. WF-003.13 makes confirmation of the
three intake choices explicit (one combined confirmation is sufficient; it need
not be three questions). ART-002.18 adds **one playback confirmation per
questioned drafting round**, more after corrections. The three artifact approval
gates remain. WF-002.1 adds summary content, not a new approval. Progress lines,
source lines, coverage, and undecided options add no turn by themselves. An
undecided answer can cause a later named marker acceptance on design and tasks;
K unchanged markers can require up to **2K named acceptances**, which may be
included in the two existing approval responses rather than 2K new turns
(R:290; D:692). Deduplicate ART-002.12/.16 for the same answer.

This can fit quick only after resolving F1, with F2 preventing unnecessary
marker work. It currently conflicts with the literal one-question spike limit
in D:642 unless sketch questions are treated as a separate, unbounded interview.

## 4. Kiro shape and state compatibility

| Addition | Compatibility judgment |
|---|---|
| `Source:` | Ordinary Markdown beneath a feature requirement (D:365–367), not proprietary frontmatter. Warning-only for existing Kiro requirements (R:494). No demonstrated break; no live proof either. Do not auto-rewrite or fabricate sources in native documents. ART-002.15 explicitly names `requirements.md`; do not insert per-clause source fields into `bugfix.md`. |
| `Depends on:` | Feature header is specified (D:359), but bugfix placement and references to unnumbered native specs are not. This is a contract gap, not evidence that Kiro rejects the text: F3. |
| `approvedCommit` | Belongs to recorded approval metadata, so it fits STATE-002.3's authority for approvals (R:379); it does not replace Markdown. D:725's “Only the fact, timestamp, and approved hash” is now incomplete and should include the commit and already-existing accepted markers. The substantive issue is what that commit proves: F4. |
| status `warnings` | Derived output, not stored state. It closes no gate and therefore does not alter §7.5 phase derivation (D:774–785,814–816). Git history is additional input beyond the three documents; define absent history explicitly. `statusVersion: 1` can include the field before first release; compatibility/version policy applies once published (D:817; T:485). |
| English structure | Sensible for newly authored specflow templates (R:123; D:349). The existing no-conversion/no-renumbering promise still controls native resumes (D:462,470). Test a native document without forcing translation; the assertion that Kiro matches all these English tokens is not established by the public docs. |

The public Kiro pages describe the artifact skeleton, not a closed grammar for
extra plain-text fields. T-027/T-052 should explicitly exercise opening,
continuing, and editing an extended spec, retaining extra lines or reporting
their change through normal hash invalidation (T:100–108,414–419). Until that
capture, actual IDE behavior is a **KNOWN verification limitation**, not a reason
to claim either compatibility or breakage.

## 5. Criterion-by-criterion task, check, and deletion test

Every criterion has a plausible task owner. That is weaker than full acceptance
coverage: existing task references are mostly requirement-level, and the scratch
checker proves only ID resolution. **B** means scenario behavior; **S** means a
deterministic file/helper check. Checks below are proposed acceptance assertions,
not claims that specflow is implemented. “Add” identifies a missing or insufficient
named verification in the present tasks. F5/F6 cover these omissions together.

| Criterion (R line) | Task/check evidence | If deleted; recommendation |
|---|---|---|
| WF-003.11 (310) | T-031, T:226,231; B: known preservation facts cause no question; unknown outside-system context is requested. Add already-supplied outside-context case. | Existing integrations regress; keep, apply F1. |
| WF-003.12 (311) | T-031, T:226,231; B: empty repo asks relevant constraints, bans have reason/alternative. Add unknown alternative and example-absent cases. | New projects inherit arbitrary stack rules; keep, apply F1. |
| WF-003.13 (312) | T-031, T:227,231; B/S: interrupt immediately after choices; other host reads both sidecars with missing first artifact. | Tool switch loses choices; keep. |
| WF-003.14 (313) | T-031, T:227,231; B/S: late trigger proposes raise, confirmed raise updates profile/log without staling unchanged artifacts. | Quick discovery can stay too shallow; keep. |
| WF-003.15 (314) | T-031, T:228,231; B or deterministic classifier fixture: agent-only repo versus nested application. Add excluded dependency/build trees, root source, submodule and depth-limit cases. | Empty-repo questioning fires inconsistently; keep, avoid claiming exhaustive absence after a bounded scan. |
| WF-003.16 (315) | T-031, T:228,231; B: compare declared coverage against fixture read trace; empty submodule reported without fetch. Add explicit no-fetch assertion. | A skim passes as a full read; keep. |
| WF-003.17 (316) | T-031, T:228,231; B: applicable rule from a file not auto-loaded by the host reaches constraints with citation. Add scoped rules and genuine conflict. | Host switches lose standing rules; keep, F7. |
| WF-003.18 (317) | T-031/T-034, T:228,264; B: missing preferences asked, known preferences not re-asked; resulting independent tasks honor answer. Neither T:231 nor T:269 names this end-to-end assertion. | User's chosen implementation order is lost; keep, F1/F5. |
| ART-002.12 (142) | T-032, T:244,248; B: actual uncertainty becomes one unresolved item with resolution path. Current “for now” positive fixture lacks a settled-release negative case. | Hedged intent can become false certainty; keep, narrow per F2. |
| ART-002.13 (143) | T-032, T:244,248; B: inferred answer cites the actual intake/repository evidence. | Inference becomes untraceable; keep. |
| ART-002.14 (144) | T-032, T:243,248; B: each elicitation question includes a truthful progress estimate, with no extra response required. | Long interviews lose orientation; keep, shared routing F5. |
| ART-002.15 (145) | T-020/T-032, T:114,245,248; B/S: source present and supports requirement; unsourced whole requirement stays out; unpicked option is neither requirement nor exclusion. Add sourced requirement with guessed detail. | Scope can be invented; keep. One source chain, no duplicate evidence store. |
| ART-002.16 (146) | T-032, T:245,248; B: undecided answer logged once; later gate accepts the named marker only on explicit response. | Forced choices invent intent; keep, F5. |
| ART-002.17 (147) | T-032, T:245; B/rubric: user terminology and first-use definition. Not named in T:248 verification. | Process jargon returns; keep, add rubric and cross-phase routing. |
| ART-002.18 (148) | T-032, T:245,248; B: drafting follows playback confirmation. Add quick, Design-First, and spike scope cases after F1/F8 ruling. | Misread answers survive to draft; retain playback, revise stop policy via F1. |
| ART-001.11 (123) | T-030, T:216,218; B/S: non-English conversation generates English structural tokens; preserve existing native shape. | Validators can miss translated control fields; keep, add native-resume case. |
| ART-003.12 (167) | T-033, T:255,258; B/rubric: plausible existing solution considered; unavailable search disclosed, not falsely claimed. | Needless custom code; keep within existing 2–3 alternatives, not a market survey. |
| INT-001.8 (225) | T-029, T:181,183; B/S: ambiguous input prompts once. Add valid copy, missing/unreadable path, non-text/large/outside fallback, and collision-safe destination. | Agent guesses wrong input; keep. One explicit path per supplied file; multi-input interpretation should be explicit. |
| INT-002.8 (242) | T-072, T:236–237; B/S: screen coverage, disclaimer, no scripts/network, accessibility note. Add question scope, shared screen and terminal-screen cases. | Cheap UI exploration needs executable code; keep, F8. |
| WF-001.9 (276) | T-026, T:164–165; S: incomplete prerequisite closes implementation and nulls nextTask; complete prerequisite opens it. Add malformed/native/multiple/self/cyclic cases per F3. | Runner starts work before its prerequisite; keep with F3 or defer whole capability. |
| WF-004.8 (332) | T-026, T:164–165; S: tracked placement path changed, no-git case. Add dirty tree, missing commit, missing placement, and reapproval cases after F4. | Stale code assumptions get no advisory; useful but defer whole capability to slice two, or narrow now. |
| VAL-001.11 (493) | T-071, T:199–201; S: unterminated fence refuses approval; valid fenced literal content remains hash-bound. Include both backtick/tilde and longer outer fences. | Placeholder masking goes undiagnosed; keep. |
| VAL-001.12 (494) | T-071, T:199–201; S: missing Source warns, exit/gates unchanged. | Provenance omissions invisible or native files blocked; keep. |
| INT-001.5 (222) | T-032, T:243,248; B: exact answer/caveats, separate interpretation, replacing entry; earlier bytes preserved. | A later host sees agent paraphrase as user intent; keep. |
| SEC-002.2 (527) | T-054 generic secret handling, T:430; B: synthetic credential omitted from log/state, omission recorded. No explicit new logging fixture. | Verbatim logging copies credentials; keep, add fixture. Apply same rule before copying an input file. |
| ART-002.11 (141) | T-020/T-029, T:114,182–183; S: dependency metadata distinguished from task-level Depends on and fenced examples. | Explicit prerequisite declaration lost; keep with F3, no change to Supersedes/Blocks. |
| WF-002.1 (284) | T-032, T:245,248; B: assumptions named, retained as assumptions after approval. Add design/tasks approval summaries, not just requirements. | Approval masks unasked assumptions; keep, F5. |
| STATE-001.2 (364) | T-021, T:122–125; S: optional approval commit round-trips without phase storage; older state remains readable. Recording it also needs an approval-path check. | Drift lacks baseline; move only new commit field with F4 if deferred. |
| STATE-003.1 (391) | T-026, T:162–165; S: blockers close gate, warnings do not, nextTask null when blocked; same inputs produce same JSON. | Runner cannot distinguish blocked work from advisory notes; keep, dependency/drift portions follow F3/F4. |
| VAL-001.5 (487) | T-026, T:165; S: gate rejection for unfinished prerequisite; stale artifact behavior unchanged. | Helper and agent disagree on readiness; keep with dependency capability. |
| VAL-001.8 (490) | T-029, T:182–183; S: missing referenced spec named as error; existing path/number checks preserved. | Typo causes opaque waiting; keep with dependency capability. |

### Eval load

By the table's proposed classification, **22 criteria have behavioral assertions**
and **9 can be covered by structural/helper assertions alone**. Some of the 22
also have structural parts. This is not 31 new eval files: D:273 requires
splitting mixed rules and D:300 allows shared rules; the final inventory does not
exist yet. Conversely, “one eval per criterion” would miss compound behavior.

A practical proposed grouping is eight reusable session families: (1) quick
existing change with supplied facts, (2) empty repo with unknown constraints and
practices, (3) outside-system/file-input ambiguity, (4) correction/undecided/hedged
answers, (5) non-English native and Design-First handoff, (6) late profile raise
and instruction scope/conflict, (7) sketch spike, (8) reuse alternatives plus
task ordering. They need positive/negative turns, not eight happy paths. Metadata,
fences and dependency graphs mostly use cheap deterministic fixture tests.

If eight sessions are additional, slice two adds **24 host-session runs per
pass**: 16 headless runs and 8 recorded Kiro runs; roughly 22 × 3 = **66
criterion-level behavioral scoring groups**, with more atomic assertions inside.
These are planning estimates, not measured tokens, minutes, or final inventory
counts. Reusing already-planned sessions can reduce additional runs. Slice one
adds record/fixture authoring and deterministic tests, **zero newly mandated
full-matrix eval runs** (D:1141–1146). F6 prevents a misleading green inventory
check from hiding omitted decision-derived rules.

## 6. Findings for the walkthrough

Each is classified **FIX, pending user ruling**. This report intentionally does
not follow the skill's automatic-edit instruction: the user's explicit
report-first/no-spec-edits rule controls. Walk highest severity first: F3, F5,
then F1, F2, F4, F6, F7, F8. Options include their benefit and drawback.

### F1 — Mandatory intake questions have no shared budget policy (medium)

Evidence: R:310–317, R:148; D:619,892. Several individually reasonable “SHALL
ask” rules now consume the same 0–2-question allowance. The two practice
questions alone exhaust it. Playback adds a further confirmation even after one
unambiguous answer. A profile raise is possible but no rule says when competing
question obligations trigger it. This is interaction cost, not a reason to cut
the accepted topics.

1. **Recommended:** ask only material unknowns across all intake topics, reuse
   supplied facts, explain when more than about two are needed and propose
   standard without silently changing it. Combine playback with the existing
   intake-choice confirmation when timing permits; require a separate playback
   confirmation only for a material interpretation or unresolved conflict.
   Benefit: quick remains quick; drawback: narrows ART-002.18's universal stop.
2. Keep every stop; state explicitly that 0–2 counts substantive questions only
   and is a usual range, and enumerate mandatory exceptions. Benefit: strongest
   confirmation discipline; drawback: quick may still require many turns.
3. No edit. Benefit: preserves all accepted wording; drawback: agents must
   improvise priority and counting, producing different intake experiences.

Apply to R:148,310–317, D §6.7/§9.2, T-031/T-032 and combined intake evals.

### F2 — “For now” can turn a settled release boundary into a blocker (medium)

Evidence: R:142,290; D:602–603; T:248. “Use 0.1% for this release; revisit after
the pilot” defines the current contract. The example nevertheless records the
whole answer as unresolved. The strict marker gate then asks for named
acceptance again. Genuine uncertainty must survive; future review does not
necessarily make today's answer unknown.

1. **Recommended:** preserve the exact caveat, but record only the unresolved
   part; a definite current boundary stays a requirement, with the later review
   noted outside gate-bearing unresolved items unless it affects this spec.
   Benefit: avoids false blockers; drawback: requires semantic judgment.
2. Keep all temporal caveats as markers and accept them by name at existing
   gates. Benefit: maximally visible uncertainty; drawback: repetitive acceptance
   of decisions already explicit in the answer.
3. No edit. Benefit: no contract change; drawback: keeps the false-positive example.

Apply to ART-002.12, D §6.7 example, T-032 positive and negative evals. Do not
change decision #7's gate or ART-002.16's undecided choice.

### F3 — The new cross-spec gate lacks a complete input contract (high)

Evidence: R:141,276,487,490; D:345,359,478–500,813–815; T:164–165,182–183.
The feature header names one five-digit spec, while native folders may have no
number and bugfix documents have no placement for the field. Multiple
prerequisites, self-reference and cycles have no defined syntax or diagnosis.
A → B → A can leave both blocked forever with only “not complete” as the
message. A bugfix depending on a feature has no specified header location.
T-026 checks an unfinished prerequisite, not these cases. The performance
promise also needs to allow reading prerequisite specs outside the selected
directory (R:560).

1. **Recommended:** retain in 0.1; define one metadata location per supported
   shape, a small explicit list syntax and identifier resolution (including a
   native-folder form, or an explicit unsupported-reference error), direct
   prerequisite completion from existing reconciliation, and diagnostics for
   missing/ambiguous/self/cyclic dependencies. Gate only implementation and set
   nextTask null; exclude fenced examples and task-local fields. Benefit:
   external runners have a dependable gate; drawback: more resolver fixtures.
2. Defer this entire new capability to slice two, including its field, gate,
   status and validation additions. Benefit: smaller 0.1 aligned with cross-spec
   review; drawback: external runners have no enforced prerequisite gate yet.
3. No edit. Benefit: smallest immediate spec diff; drawback: implementations
   will choose incompatible input and error behavior.

Apply to ART-002.11, WF-001.9, STATE-003.1, VAL-001.5/.8, D §6.2/§6.6/§7.5/§7.6,
R performance and possibly §9, T-020/T-026/T-029 plus fixtures. The `Blocks:`
and `Supersedes:` contracts remain settled. No scheduling engine is proposed.

### F4 — A commit is not the code snapshot at approval (medium)

Evidence: R:332,364; D:690,725,1056; T:165. A dirty tree can be approved without
committing. If comparison is against working bytes, immediate reapproval at the
same HEAD cannot clear the warning. If comparison is commit-to-commit, dirty
changes are invisible. An unborn Git repository has no commit; a shallow clone
may lack the recorded one. Native bugfix designs also lack `Module placement`.
Neither comparison nor unavailable-data behavior is specified. This is a
deduction from the stated contract, not an observed specflow implementation bug.

1. **Recommended:** defer the whole code-drift capability to slice two. Benefit:
   avoids adding an incomplete Git contract to 0.1; drawback: no automatic code
   freshness advisory in the first release. Retain generic status warnings.
2. Keep a deliberately limited committed-change advisory: compare approved
   commit to HEAD for explicit placement paths (native matching section where
   available), state that dirty edits are outside this check, and report
   “not checked” without blocking when the baseline/history/paths are unavailable.
   Omit approvedCommit when HEAD does not exist. Reapproval resets the committed
   baseline. Benefit: small, testable check now; drawback: does not detect every
   code change. Update D:725's metadata list too.
3. No edit. Benefit: no scope change; drawback: dirty approval and reapproval
   have mutually incompatible readings.

Apply to WF-004.8, new part of STATE-001.2 and STATE-003.1, D §7/§13/§15,
T-021/T-026/T-030 approval path, and §9 if deferred. Do not add source fingerprints,
locks, automatic commits, or a clean-tree approval prerequisite.

### F5 — Global dialogue behavior is authored in a requirements-only file (high)

Evidence: D:187,212–219,253; T:239–248. Verbatim logging, progress, undecided
choices, plain language and playback are assigned to `phases/requirements.md`
and REQ checks. Intake loads `phases/intake.md`; Design-First initially loads
`phases/design.md`. It is therefore possible to obey phase-selective loading
and never load those rules before intake or Design-First questions. The changed
approval summary is similarly tested only in requirements. Eventual requirements
loading cannot repair an earlier missing answer or confirmation.

1. **Recommended:** place shared dialogue and approval-summary rules once in
   an existing always-loaded core reference or the compact skill; phase references
   link to them. Route their inventory areas accordingly and check intake,
   Design-First and later approval behavior. Add missing concrete assertions from
   §5, particularly practices-to-task order and synthetic-secret redaction.
   Benefit: one rule behaves the same in every phase; drawback: modest always-loaded
   text and broader session fixtures.
2. Explicitly load the shared subsection of the requirements reference for all
   questioning/approval phases. Benefit: fewer moves; drawback: a requirements
   file becomes an implicit cross-phase dependency.
3. No edit. Benefit: no routing change; drawback: behavior depends on retained
   context and workflow order, violating the portability purpose.

Apply to D §5.2/§5.4, T-030/T-031/T-032/T-033/T-034 and eval records; clarify
cross-phase scope in the affected R criteria without duplicating their text.

### F6 — The inventory cannot detect an entirely omitted decision rule (medium)

Evidence: D:245,255–273,296; T:190–194,355–358; R:470–474.
`D:<date>#<n>` is accepted as provenance, but the coverage algorithm enumerates
port-plan rows only. If ART-002.17 or WF-003.18 is never entered in the inventory,
neither a missing check nor a missing runtime ID exists for the checker to catch.
Even a single mapped rule for decision #12 cannot prove all its criteria covered.
The current scratch check likewise passes without criterion-level assertions.

1. **Recommended:** add an explicit local coverage list for these 31 criterion
   IDs and require each to map to rule/check IDs, allowing shared rules and
   structural/behavioral splits. Seed a missing decision-criterion mapping.
   Benefit: the promised slice-one gate covers the additions; drawback: a small
   maintained manifest. No decision-prose or upstream parser.
2. Require a signed-off manual criterion/check table at release alongside the
   existing machine inventory. Benefit: less checker code; drawback: omissions
   remain human-detected, so document the weaker guarantee.
3. No edit. Benefit: current checker stays smallest; drawback: the additions can
   silently miss the inventory while release coverage appears green.

Apply to RULE-001 coverage wording, D §5.4/§15, T-070/T-069/T-063 and reference
task assertions. Preserve per-rule evals and the two delivery slices.

### F7 — “All instruction files” needs applicability, not just discovery (medium)

Evidence: R:316; D:621; T:228,231. Repository instructions can be root-wide,
directory-scoped, conditional, or explicit-only. Flattening every hard rule
into spec constraints can make unrelated rules look contradictory and force an
unnecessary question. A backend-only and frontend-only language mandate can both
be valid. Reading every instruction body also works against targeted discovery
if the repository is large (R:302).

1. **Recommended:** read root instructions and instructions applicable to the
   spec's affected paths, follow repository-declared routing, retain their scope
   and precedence, and ask only about conflicts that remain applicable together.
   Record relevant constraints with their file and scope. Benefit: consistent
   cross-host behavior without globalizing local rules; drawback: one scoped-rule
   fixture and explicit handling when affected paths are still unknown.
2. Keep the broad read, but record applicability beside every extracted rule and
   resolve only genuine conflicts. Benefit: broader early visibility; drawback:
   larger context/read cost for quick specs.
3. No edit. Benefit: shortest prose; drawback: leaves conditional loading and
   conflict interpretation to each host.

Apply to WF-003.17, D §6.7, T-031; preserve #5's hosts and #6's folder ownership.
This does not recommend new rule directories, projections or configuration.

### F8 — The sketch adaptation has contradictory counts and excess machinery (medium)

Evidence: R:242; D:642–644; T:237. One file per journey node *plus* `index.html`
does not satisfy “each mockup matches exactly one step” unless the index is
explicitly excluded. Shared screens across personas need deduplication; terminal
screens have no outgoing edge for the mandated main action. The two compulsory
questions compete with the spike's one-question limit. The no-HTML branch has no
named supported host or acceptance case. These are copied structural details,
not reasons to discard the user's sketch choice.

1. **Recommended:** keep the sketch as a minimal happy-path prototype; one
   mockup per unique visible screen, index excluded, links only for actual edges,
   no invented outgoing action on terminal screens. Reuse known style/accessibility
   facts; fit missing questions into the spike budget, explicitly record remaining
   assumptions. Drop the unneeded no-HTML branch for the three supported hosts.
   Benefit: smaller coherent build/check contract; drawback: less coverage of
   alternative paths and hypothetical restricted hosts.
2. Keep all variants, define the index/unique-screen/terminal exceptions, give
   sketches an explicit question-budget exception, and test the text fallback.
   Benefit: preserves broader sketch support; drawback: higher intake and eval cost.
3. No edit. Benefit: no contract change; drawback: a correct index or shared
   screen can fail the stated bijection test.

Apply to INT-002.8, D §6.8, T-072, and coordinate playback scope with F1.

## 7. Upstream attribution audit

All checked groups have identifiable support. Several are deliberate local
adaptations, not requirements imposed by AWS. Pinned links below survive clone
cleanup. A1 paths are under `core/aidlc-common/`; A3 rule-detail paths are under
`aidlc-discovery-rules/aidlc-discovery-rule-details/`.

| Design §9.4 attribution | Checked evidence and verdict |
|---|---|
| A3 preservation/outside context, D:908 | [Project type:72–100](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/shared/greenfield-vs-brownfield.md#L72) and [technical interview:659–670](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/technical/tech-env-interview.md#L659). Supported; narrowed from product to spec. |
| A3 constraints/bans/example, D:909 | [Technical interview:211,307–325,568–615,702–704](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/technical/tech-env-interview.md#L307). Supported adaptation. Reason **and alternative for every ban** is broader than A3's rule for prohibited libraries; languages/services list reasons. One per-spec example is local simplification. |
| A3 immediate persistence/profile raise, D:910 | [Project type:60–68](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/shared/greenfield-vs-brownfield.md#L60), [depth:24,45–56](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/technical/tech-env-interview.md#L24). Supported; Kiro folder timing and non-staling semantics are local. |
| A3 hedges, D:911 | [Open-question collector:15–20,38–42](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/shared/open-questions-collector.md#L15). Supported. Specflow's strict marker gate amplifies its effect; F2. |
| A3 inferred-answer source, D:911 | [README:80–102](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/README.md#L80). Supported as a documented invocation pattern, **not an implemented universal extraction validator** (README:113). Local promotion to a mandatory rule is legitimate but should be labeled. |
| A3 progress, D:911 | [Question format:11–25](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/common/question-format-guide.md#L11). Supported adaptation from per-batch counts/time to a per-question line. No scheduler or progress state is needed. |
| A3 own words/append-only, D:912 | [Question format:124,156–171](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/common/question-format-guide.md#L156), [audit:64–68](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/common/audit-format.md#L64). Supported; replacing-entry IDs are local. Redaction has direct support. |
| A3 English structure, D:913 | [Language handling:11–16,72–85,138](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/common/language-handling.md#L11). **Partial analogue**: A3 keeps control tokens English but permits translated visible headings. All artifact headings English is specflow's stronger local rule, not A3's exact rule or proof of Kiro syntax. |
| A3 fence validation, D:913 | [Content validation:9–20,58–65](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/common/content-validation.md#L9). Supported; blocking approval and linking to hash parsing are local. Do not copy its loose “matching language tags” wording as a Markdown parser rule. |
| A3 sketches, D:914 | [Visual sketch:111–190,214–223,278–287](https://github.com/aws-samples/sample-aidlc-discovery/blob/a84b2899d0dd518081a4764b42fde4c6dbf3cc9a/aidlc-discovery-rules/aidlc-discovery-rule-details/shared/visual-sketch.md#L111). Supported. A3 permits CDN Tailwind; specflow intentionally forbids network/scripts. A3 explicitly derives unique screens; specflow should retain that clarity (F8). |
| A1 classification/coverage, D:920 | [Workspace detection:43–81,101–108](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/initialization/workspace-detection.md#L43); [reverse engineering:212–216,271–295](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/inception/reverse-engineering.md#L212). Supported, including the three-level fallback as an upstream implementation choice; local override and Q&A storage are adaptations. |
| A1 grounding/assumptions, D:921 | [Intent capture:141–159,179–204](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/intent-capture.md#L141). Supported. Per-requirement Source is weaker than per-claim source tags; accept assumptions does not make them facts. No need to import sensors. |
| A1 instruction files, D:922 | [Intent capture:81–83](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/intent-capture.md#L81), [stage protocol:810–848](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/protocols/stage-protocol.md#L810). Supported method analogue; A1 loads its scoped memory, not a universal union of AGENTS/CLAUDE/Kiro files. F7 is a local responsibility. |
| A1 existing solutions, D:923 | [Market research:39–58](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/market-research.md#L39). Supported adaptation to per-capability alternatives. Does not justify a mandatory market study for a small fix. |
| A1 freshness, D:924 | [Reverse engineering:90–108,161–182,271](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/inception/reverse-engineering.md#L90). Supported inspiration, **not equivalent assurance**: A1 tracks scan scope and source fingerprints. Specflow's approval-commit advisory deliberately omits that machinery (F4). |
| A1 undecided/plain words/playback, D:925 | [Intent capture:121–128](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/intent-capture.md#L121), [practices:139–155](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/inception/practices-discovery.md#L139), [protocol:421–480](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/protocols/stage-protocol.md#L421). Supported, but A1 offers none/not-applicable variants and playback is conditional on summary_confirmation. Specflow's universal stop is a stronger local choice (F1). |
| A1 practices/dependencies, D:926 | [Practices:125–177](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/inception/practices-discovery.md#L125), [feasibility:68–72](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/feasibility.md#L68). Practices supported directly. The latter is a RAID log including dependencies; the precise cross-spec line, completion semantics and hard gate are **local**, not specified in feasibility. |
| A1 sketches/file path, D:927 | [Rough mockups:49–68](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/rough-mockups.md#L49), [intent capture:54–80](https://github.com/awslabs/aidlc-workflows/blob/2a883858f5483bce3b48f43b8f6d3ca2c042d6ae/core/aidlc-common/stages/ideation/intent-capture.md#L54). Supported. Copying into intake and recording unreadable/outside input locations are local fallbacks; A1 instead stops and requests supported input. |

Attribution disposition: no invented source found among the checked additions.
When implementing T-010/T-014, carry the pinned file/heading citations and local
strengthenings above into `adaptation.md`; do not claim AWS requires the local
gates. The prior “full read of twelve” is historical session evidence (C:158–165),
not a claim that this review re-read all twelve. A2's older complementary-source
claim at D:906 was not independently rechecked, as directed by the scope boundary.

## Initial doubt protocol record

All six required questions were considered:

1. Least certain: runtime Kiro acceptance and drift semantics. Kiro remains
   KNOWN until T-027; drift is F4.
2. Assumptions checked: distinct provenance levels, metadata ownership,
   phase-relative creation, profile raising, three-host scope, and source
   attribution. Evidence above dismisses broad incompatibility claims.
3. Completion: all 31 criteria are in the matrix, all seven requested questions
   answered. Walkthrough/application remain pending by explicit user instruction.
4. Practical failures: too many intake stops, false open markers, native/bugfix
   dependencies, dirty approval, phase routing, omitted rules, scoped instructions,
   sketch index/shared/terminal screens. F1–F8.
5. Different approach: specify a combined intake transcript and helper edge-case
   fixtures before adding rules from another source. Keep rules that passed the
   deletion test; upstream similarity alone is not sufficient justification.
6. Missing checks: criterion coverage and negative/cross-phase cases in §5;
   live Kiro extension acceptance; no runtime/eval passes can be claimed yet.

Slop checks:

- **Bloat ratio:** #11/#12 diff adds 152 and removes 40 lines, net +112 across
  four files. This is not a 5–10× implementation expansion over 1,483 criterion
  words; units differ, so this is a size sanity check only. Restating contract,
  design and owned verification has a purpose. No blanket prose deletion.
- **Defensive impossibility / speculative support:** D:644's no-HTML fallback has
  no named supported-host need and no task check; F8 proposes dropping it.
- **Single-caller abstraction:** no new implementation helpers exist to inspect.
  No factories, wrappers or runtime services are required by these edits. Checked
  D §3/§5/§7; no separate finding.
- **Paraphrase / ritual duplication:** unconditional answer playback before
  drafting duplicates already explicit answers plus artifact approval on simple
  quick work; F1. This is a second substantive slop item, not a quota-driven code
  criticism.
- **Framework-verification tests:** missing-source warnings, fence refusal and
  dependency gates test local contracts. Do not count a Markdown render or JSON
  field-existence test as proof of semantic provenance or host behavior; F5/F6.

Initial tally: **14 distinct doubts** — eight FIX proposals awaiting rulings at report delivery (F1–F8),
five VERIFY concerns dismissed (provenance overlap; redaction versus verbatim;
profile raise versus hash invalidation; early state versus intake move; added
metadata versus state authority), one KNOWN live-Kiro verification limitation.
Fixed spec defects at report delivery: **0**, as requested. The subsequent
second-pass review of applied rulings is recorded in the minutes below.

## Checks performed

- `python3 -m unittest discover -s scripts`: 9 passed.
- `python3 scripts/validate.py`: `Validated 1 plugin package(s) and 1 skill(s).`
- `python3 docs/dev/tmp/specflow/check_refs.py docs/dev/project-management/intake/new/specflow/00001-initial-delivery`:
  62 tasks, 30 requirements, no cross-reference problems. This scratch checker
  has hardcoded withdrawn IDs and proves no criterion, behavior, or eval coverage.
- Git state and pinned upstream commits verified as described above.
- No runtime implementation tests or host evals run; this is a specification review.

## Minutes

Each user choice was recorded and applied before the next finding. All eight
findings are now ruled and applied; nothing awaits a walkthrough response.

| Finding | User ruling | Applied changes / verification | Status |
|---|---|---|---|
| F3 | Option 1: keep in 0.1 and define the contract | Requirements, design §6.2/§6.6/§7.5/§7.6/§13/§15, T-020/T-026/T-029; decision #13. Verification below. | Applied |
| F5 | Option 1: move shared rules into an always-loaded core reference | ART-002 scope; design §5.1/§5.2/§5.4/§15; T-030 through T-034 and T-079; decision #14. Verification below. | Applied |
| F1 | Option 1: one shared intake budget and conditional playback confirmation | ART-002.18, WF-003 intake policy and .11/.12/.17/.18; design §5.2/§6.7/§9.2/§15; T-030/T-031; decision 2026-10-04 #1. Verification below. | Applied |
| F2 | Option 1: mark only genuine uncertainty | ART-002.12; design §6.7/§9.4/§15; T-030/T-032; decision 2026-10-04 #2. Verification below. | Applied |
| F4 | Custom: full features in 0.1; no deferral or committed-only approximation | Working-file approval baseline and tests; all slice-two capabilities/checks moved into release; decision 2026-10-04 #3. Verification below. | Applied |
| F6 | Option 1: explicit criterion-to-rule/check mapping | RULE-001.1/.5; design §5.4/§15; T-070/T-069/T-063 and reference-authoring rule; decision 2026-10-04 #4. Verification below. | Applied |
| F7 | Option 1: read and apply instructions by scope | WF-003.17; design §6.2/§6.7/§9.4/§13/§15; T-031; decision 2026-10-04 #5. Verification below. | Applied |
| F8 | Option 1: correct sketch correspondence and share the spike budget | INT-002.8; design §6.8/§9.4/§15; T-072; decision 2026-10-04 #6. Verification below. | Applied |

### F3 ruling and application

User: “option 1”. Retained the spec-dependency capability in slice one. Defined
one comma-separated declaration, feature and bugfix placements, numbered and
exact native-folder references, missing/ambiguous/unsupported/unreadable target
errors, duplicate handling, self-reference, and reachable-cycle diagnostics.
Direct prerequisites use existing read-only reconciliation; blockers close only
implementation and null `nextTask`. A prerequisite's later edits do not rewrite
the dependent phase or approvals. The performance exception permits only the
folder listing and reachable prerequisite reads. Tasks own the matching
deterministic fixtures; no runtime feature or extra host-eval gate was added.

Second-pass doubts on this edit: (1) recursive gate evaluation could redefine
completion or loop — resolved by local phase derivation plus graph validation;
(2) bugfix metadata could change Kiro's section shape — placement preserves
headings and clauses, with live capture still owned by T-027; (3) dependency
failures could accidentally block drafting or stale approvals — requirements,
status contract, and fixtures explicitly restrict them to implementation.
Slop checks kept one shared grammar rather than repeating it in each artifact
section, and assigned exhaustive resolver cases to T-026 rather than duplicating
them in T-029. No scheduler, extra state, or implementation was introduced.

Verification: repository validator passes (1 plugin, 1 skill); the cross-reference
check still resolves 62 tasks and 30 requirements with no problems; `git diff
--check` passes. These verify the specification edit, not an implemented resolver.
New decisions are appended only after the corresponding user ruling; #13
records this one. Other findings remain proposals.

### F5 ruling and application

User: “option 1”. The existing `artifact-contract.md` now owns shared dialogue
and approval summaries, with `DLG` rule IDs and source mappings; it loads before
questioning on every invocation, including fresh intake, Design-First and direct
review entry. T-030 authors the section and its eval records. Phase references
point to it, and T-032 no longer owns duplicate copies. T-079's Plan B integration
uses the same shared-rule precedence. Requirements clarify the cross-phase scope
without changing the pending question-budget, hedge, or playback decisions.

Added owned checks for intake and fresh-context Design-First, direct review
entry, all artifact approval summaries preserving assumptions, plain language
and definitions, synthetic-secret redaction, and working preferences reaching
task ordering while preserving bugfix dependencies. Sessions are reused across
rule evals; full host execution stays in slice two.

Coverage update: read `~/.kiro/crew/workspace/ai-age-repo-structure.md` in full
(669 lines) before selecting the shared reference. This uses an existing
distributed plugin file and introduces no project skill/config/link location.

Second-pass doubts on this edit: (1) direct review entry could bypass the shared
load — the routing row now covers every invocation; (2) old phase-based mappings
could recreate duplicate rules — shared-rule routing has explicit precedence,
including Plan B; (3) moving checks could lose secret handling or later approval
coverage — both have named assertions and an owner. Slop fixes remove the repeated
T-032 rule text and reuse session transcripts instead of requiring one host run
per rule or another core file. No change to other pending findings was applied.

Verification: repository validator passes (1 plugin, 1 skill); cross-reference
check resolves 62 tasks and 30 requirements with no problems; `git diff --check`
passes. The first cross-reference run mistook the proposed `SR-ART-007` example
for requirement `ART-007`; the final dialogue namespace is `DLG`. No checker was
changed. Runtime routing and behavioral eval execution remain implementation
work, not results claimed by this specification edit.

### F1 ruling and application — 2026-10-04

User: “option 1”. All intake topics now share one budget: read first, reuse
known answers, ask material unknowns, and explain/propose standard before quick
exceeds its usual 0-2 questions. The developer can explicitly keep quick with
extra questions, narrower scope, or deferred items under the existing marker
gates. The range remains guidance, not a cap; confirmations cannot hide new
content questions, and progress estimates cover the combined topics.

Playback remains a short recap. It can accompany the existing intake-choice
confirmation; clear answers need no extra response, while a material
interpretation or unresolved conflict requires confirmation/correction before
drafting from it. Later interpretations are not covered by an earlier yes.
Artifact approvals and named marker acceptance remain distinct. T-030/T-031
own shared-session assertions for these branches, with full host runs still
in slice two. The separate sketch/spike issues remain for F8.

Second-pass doubts: (1) the usual range could become an unintended hard cap —
explicitly retained agreed extra questions; (2) fewer stops could silently
accept guesses — marker and artifact gates remain explicit; (3) supplied
preferences or outside-system facts could still be re-asked — the shared policy
and affected criteria now require reuse. Slop checks avoid another budget state
field or counter service, and reuse the existing session cases rather than add
per-topic eval runs. No other pending ruling was applied.

Verification: repository validator passes (1 plugin, 1 skill); cross-reference
check resolves 62 tasks and 30 requirements with no problems; `git diff --check`
passes. Checks cover the specification edit; runtime transcripts remain future
eval work. The pre-existing untracked `graduate/` directory was left untouched.

### F2 ruling and application — 2026-10-04

User: “option 1”. ART-002.12 now preserves caveats verbatim and marks only the
undecided content affecting this spec. Definite current choices remain sourced
requirements; later revisits outside this spec stay in the log as follow-ups.
Replaced the design's keyword-triggered example with a clear current-release
decision and a later review, and added a mixed settled/uncertain example.
T-030/T-032 own the matching positive and negative assertions in shared sessions.

Second-pass doubts: (1) an ambiguous "for now" could be promoted to a decision —
clarify or retain uncertainty; (2) a future decision needed by this spec could
evade the gate — it remains unresolved; (3) splitting the answer could erase
the caveat — keep the original wording and separate the interpretation. The
existing "not decided yet" and named-acceptance rules remain unchanged. Slop
checks keep this semantic distinction in the existing dialogue rule and log;
no keyword classifier, new artifact, or per-case host run was introduced.

Verification: repository validator passes (1 plugin, 1 skill); cross-reference
check resolves 62 tasks and 30 requirements with no problems; `git diff --check`
passes. Runtime evals remain future implementation work. Other session changes
in the spec README and `graduate/` were left untouched.

### F4 ruling and full-release scope — 2026-10-04

User: “initial release must ship full features”. Asked whether this also moves
the already-planned slice-two features into 0.1, the user confirmed: “yes, we
don't defer, it makes no sense to defer”. The deferral recommendation and the
limited committed-only alternative are withdrawn. This ruling supersedes the
earlier settled two-slice decision; it is an explicit user change of scope.

Requirements §9, design, tasks, and the README now promise all accepted features
and planned checks in 0.1. Cross-spec review, advisory scripts, all-host evals
and parity evidence join the initial release gate. Removed slice exemptions and
the definition-of-done escape allowing deferred acceptance criteria. T-063 now
waits for T-058's full eval/parity chain and T-054's complete security review.
Area checks still support incremental construction; T-079 does not require
the later T-076 output, avoiding a circular dependency. External migration and
actual skill retirement keep their original repository ownership.

F4's design now captures per-file content hashes/absence at design approval,
alongside optional commit provenance. This preserves uncommitted and untracked
content, handles added/deleted files, and resets correctly on reapproval at the
same HEAD. It reads only explicit placement files; no source copies, recursive
repo snapshot, forced commit, clean-tree requirement, or lock. Missing baseline,
stale design, ambiguous/native placement, unreadable/unsupported paths, and old
state produce not-checked advisories rather than false clean results. The
existing Git-scoped behavior remains; historical Git objects are unnecessary.
T-021/T-022/T-026 and security review own the schema/capture/comparison checks.

Second-pass doubts: (1) removing slices could create a T-079/T-076 dependency
cycle — keep area construction checks and gate the full inventory later;
(2) hashes could imply a new source authority or broad snapshot — scope stays
in design, with explicit file-only evidence and no copied content; (3) missing
evidence or stale approvals could look clean — require not-checked reasons;
(4) ordinary commit metadata changes could warn despite identical code — compare
working bytes, not commits. Slop checks remove the slice-filter mechanism and
avoid directories/globs/history reconstruction for drift. Live Kiro behavior
remains a build-time check; no runtime implementation was claimed here.

Eval-load update: the earlier estimate of eight additional sessions / 24 host
runs per pass now belongs to the initial-release workload, along with the
already-planned complete suite. These remain estimates, not measured results.

Verification: repository validator passes (1 plugin, 1 skill); cross-reference
check resolves 62 tasks and 30 requirements with no problems; `git diff --check`
passes. A separate in-memory task-graph check expanded the declared task ranges:
62 nodes, no missing dependencies, no cycles. Scope search found no remaining
slice-one/slice-two exemptions in the current README, requirements, design, or
tasks; the remaining references to slices concern task sizing or thin end-to-end
work. The README's delivery sentence was updated while preserving the other
session's conversion-skill content and untouched `graduate/` files.

### F6 ruling and application — 2026-10-04

User: “option 1”. Added the full 31-ID required set to design §5.4 and specified
its independent maintainer manifest, `criteria.json`. Rules carry `criteria`
mappings and retain decision provenance; existing rule checks complete the chain.
Shared rules and split structural/behavioral rules are allowed. Missing whole
mappings fail even if a decision source remains, and construction-area filtering
cannot hide them. Missing/malformed lists, duplicate/unknown IDs and missing
checks have named failure fixtures. T-063 reviews the printed coverage rows
against substantive assertions; an existing but irrelevant check is insufficient.

Second-pass doubts: (1) generating the required set from the inventory would
recreate the original omission hole — the set is independent, reviewed scope;
(2) one mapping could conceal a compound criterion's missing behavior — author
and release checks must cover every obligation, with mixed-kind splits;
(3) area filtering could conceal a missing mapping — global mapping checks
remain active. Slop checks reuse existing check references instead of a parallel
check catalog and retain shared sessions rather than add one run per criterion.
Semantic completeness cannot be established by links alone; eval assertions
and results remain the evidence. No upstream/decision-prose parser was added.

Verification: parsed the design's required-criterion JSON and compared it with
the user's original set: 31 unique IDs, none missing or extra. Repository
validator passes (1 plugin, 1 skill); cross-reference check resolves 62 tasks
and 30 requirements with no problems; `git diff --check` passes. The mapping
checker and runtime rule files are implementation tasks, not built by this edit.

### F7 ruling and application — 2026-10-04

User: “option 1”. Instruction discovery now reads root entry points and follows
declared routing for affected paths/conditions, preserving source, scope, and
precedence. Disjoint local rules do not conflict; unresolved simultaneous
material conflicts use the existing question budget. Unknown paths mean scoped
coverage is incomplete, not that every instruction should be loaded or ignored.
Revisit applicability as paths become known and before work expands. The code
classifier's three-level scan does not cap instruction routing. T-031 owns the
scoped fixtures, including imports, overrides, inactive conditions, real
conflicts, changed scope, and unreadable applicable files.

Second-pass doubts: (1) a narrow initial scan could permanently miss rules —
revisit on scope discovery/expansion; (2) file names could imply invented
precedence — use declared routing/precedence and retain the session hierarchy;
(3) unreadable or inactive files could be treated as satisfied — record coverage
limits and preserve conditions. Slop checks avoid a new rule loader/config and
reuse discovery coverage rather than add a separate instruction registry. The
previously fully read repo-structure plan is respected; no locations change.

Verification: repository validator passes (1 plugin, 1 skill); cross-reference
check resolves 62 tasks and 30 requirements with no problems; `git diff --check`
passes. The scoped runtime behavior remains covered by the specified future
evals; no host behavior is claimed as tested in this documentation edit.

### F8 ruling and application — 2026-10-04

User: “option 1”. Applied the final walkthrough wording: one mockup per unique
visible screen across journeys, navigation index excluded, links for actual
user-action edges, and no invented outgoing action on terminal screens. Shared
screens reuse IDs/files; distinct visible states remain representable. All HTML
stays offline, script-free, and visibly nonfunctional. Removed the unsupported
text-layout fallback. The final option preserved full sketch capability and the
rough spec's scope; the initial report's happy-path-only restriction was not
carried into the ruling.

Known UI/accessibility context is reused. Phrase-only entry gets at most one
content question across rough-spec and sketch setup, with remaining choices
explicitly guessed or open in the rough spec and report. Every screen retains
its accessibility note without claiming unverified conformance. The existing
refine/graduate/discard choice remains. INT-002.8, design §6.8/§9.4/§15, and
T-072 now agree; decision 2026-10-04 #6 records the ruling. T-072 owns both the
structural fixtures and dialogue assertions, reusing the sketch session.

Second-pass doubts: (1) deduplication could merge distinct visible states —
distinct states may have separate IDs; (2) the index could collide with a screen
or escape output checks — its ID is reserved and all generated HTML still has
the offline/disclaimer requirements; (3) fewer questions could silently invent
accessibility requirements — unasked choices remain marked guesses/open and
the note describes structure, not certified conformance. These VERIFY concerns
are dismissed by the revised contract and its named fixtures. Slop fixes remove
the speculative fallback and reuse the existing session instead of adding a
separate interview or test suite.

### Final verification and second-pass disposition — 2026-10-04

All six doubt questions were revisited across the applied rulings:

1. **Least certain:** live Kiro handling remains KNOWN until T-027 and the host
   evals run against the implementation. Document shapes and metadata authority
   are specified, but a documentation review cannot execute an unbuilt runtime.
2. **Assumptions:** checked shared budgets, scoped instructions, dependency
   completion, dirty-file baselines, criterion coverage, and screen identity
   against the edited contracts and owned checks. Their specific second-pass
   doubts and resolutions are recorded under each ruling.
3. **Completion:** all seven requested questions have cited evidence, all 31
   criteria remain, all eight findings have user rulings, and requirements,
   design, tasks, and decisions reflect them. The full-feature ruling supersedes
   the earlier two-slice plan. No review finding awaits a user response.
4. **Practical failures:** missing evidence never becomes a clean drift result;
   dependency cycles have explicit outcomes; scope expansion triggers instruction
   reads; cross-phase entry loads dialogue rules; shared/terminal screens and
   unknown sketch context have checks. The task graph has no missing dependency
   or cycle. These are specified runtime behaviors, not executed host results.
5. **Approach:** combined dialogue sessions and small explicit contracts resolve
   the interaction problems while retaining the accepted features. No further
   upstream discovery or source-driven scope expansion was needed.
6. **Missing validation:** repository checks pass below. Implementation tests,
   criterion-mapping checks, and all-host eval/parity runs remain assigned release
   work; this review neither implements them nor substitutes for their evidence.

All five slop lenses were revisited. The tracked diff currently adds 412 and
removes 179 lines, including concurrent conversion work; this is not an isolated
review-size measurement. The report is an audit record, not runtime material.
The substantive reductions are removal of duplicate phase dialogue, speculative
HTML fallback, repeated known-answer questions, and delivery-slice machinery.
No new single-caller runtime abstraction or impossible-state guard was introduced.
Cross-document restatement is limited to requirement, contract, and owned check;
task checks target local behavior, not framework mechanics. Coverage links remain
traceability evidence only, never a substitute for substantive assertions.

Final disposition of the **14 initial doubts: eight fixed in the specification,
five verified and dismissed, one KNOWN live-host verification limitation**.
The second pass found no additional unresolved specification defect.

Final checks:

- `python3 -m unittest discover -s scripts`: **9 passed**.
- `python3 scripts/validate.py`: **1 plugin package and 1 skill validated**.
- Scratch reference check: **62 tasks, 30 requirements, no reference problems**.
  Its requirement-level scope and hardcoded withdrawn IDs remain limitations.
- Independent in-memory checks: **all 31 reviewed criteria still present**;
  the design's required-criterion JSON has **31 unique IDs, no omissions/extras**;
  the **62-task graph has no missing dependencies or cycles**.
- `git diff --check`: passed. Search found no old per-node/step sketch contract
  or delivery-slice exemption in the current spec files.

Concurrent conversion-skill edits and `graduate/` were preserved. No runtime
implementation, commit, push, or host-eval result is claimed by this review.
