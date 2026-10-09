# Specflow preparation docs review — Codex — 2026-10-03

Reviewed commit: `d0887aa5879c874838dc3095f8bc9efdc8dda9ac`.
Scope: requirements, design, tasks, intake README, decisions, prior review
minutes, and selected discovery sections. Repository package boundaries,
validator, contribution docs, and CI were also inspected. No plugin exists
yet, so findings concern the specification, not demonstrated runtime bugs.

**Verdict: revise before development.** The primary-inspiration shift is
captured, but the docs explicitly retire the original source, contrary to
the maintainer's current instruction. The first delivery also couples a
useful portable workflow to substantial maintenance and migration machinery.
Several contract and task-order defects need correction independently of
any scope reduction.

Report only, for consolidation with the other agent's review. Proposed
source edits and a maintainer skill drafted during this review were rolled
back; none of the recommendations below has been applied. The other agent's
report is preserved separately. Findings reference the reviewed commit.

Severity: P1 = resolve before implementing the affected behavior; P2 =
correct or make an explicit tradeoff. Scope recommendations are proposals,
not claims that an earlier approved decision is invalid.

## 1. P1 — A2 was retired, rather than retained as complementary inspiration

Evidence: [upstream decision](../meta/decisions.md)
#1 and #8; [requirements](../intake/processed/specflow/00001-initial-delivery/requirements.md)
AWS-001.7; [design](../intake/processed/specflow/00001-initial-delivery/design.md)
§9.4, §17 “Keep the aws-samples upstream, or pin it beside A1”, and §18;
[tasks](../intake/processed/specflow/00001-initial-delivery/tasks.md) T-010.

These say A2 is retired, replaced, or provenance-only. The maintainer now
requires A1 (`awslabs/aidlc-workflows`) as primary method inspiration and A2
(`aws-samples/sample-ai-powered-sdlc-patterns-with-aws`) as an ongoing,
complementary patterns source. This is a substantive decision correction.

Propose a dated superseding decision and update the normative docs together.
Keep historical discovery/minutes intact, with a superseded notice. Retaining
both inspirations does **not** require vendoring both repositories or
maintaining two ingestion parsers. Distinguish ongoing observation from
adoption into the shipped workflow.

External verification: the [A2 pattern README](https://github.com/aws-samples/sample-ai-powered-sdlc-patterns-with-aws/tree/main/all-phases/all-phases-aidlc-mcp)
explicitly presents the approaches as complementary. The [A1 README](https://github.com/awslabs/aidlc-workflows)
describes a methodology with an engine and harness integrations. These
support different inspiration roles; they do not require Specflow to adopt
either implementation's runtime. Historical inactivity claims in discovery
were not reverified as current commit-history facts and should not determine
source retention.

## 2. P1 — The maintainer skill lacks a plugin-local, cross-tool convention

Evidence: design §3 and §11.1, UPD-001, T-001/T-018. The skill is proposed at
repo-root `.agents/skills/update-aws-prompts/`, with other host launchers
deferred. Root `AGENTS.md` and `CONTRIBUTING.md` do not define the convention.
The package boundary is sound, but placement alone does not establish
discoverability or invocation across maintainer tools.

Smallest recommendation: reuse the existing per-plugin `tools/` project:

```text
plugins/specflow/                               # Complete shipped package
tools/specflow/                                # Maintainer project
  skills/specflow-catchup/SKILL.md               # One canonical portable skill
  upstream/sources.md                           # Source roles and review cursors
tools/README.md                                 # Maintainer skill index
```

Standardize `tools/<plugin>/skills/<plugin>-<purpose>/SKILL.md` for every
plugin-local maintainer skill. Link the index from repository instructions
and contribution docs. “Read this SKILL.md and follow it” is the portable
invocation fallback; do not promise universal slash syntax or automatic
discovery. Tested client-native links or thin pointers can expose the same
source later, outside `plugins/`, without copying workflow text. Confirm
symlink behavior on the actual host/OS before calling a discovery path
supported. Shared personal skills still belong in `buvis/agent-skills`.

Keep runtime manifests and references free of dependencies on maintainer
files. Release verification should assert that maintainer content did not
enter the package. Existing `scripts/validate.py` does not validate these
proposed maintainer skills; add an explicit skill validation command when
the convention is implemented.

## 3. P1 — Regular catch-up is missing and is blocked behind updater development

Evidence: UPD-001/002, design §11 and §17 “Manual upstream refresh”,
T-018 depends on T-017. The plan creates an A1 release updater, not an
immediately usable two-source catch-up skill. Reports are ignored under
`docs/dev/tmp/specflow/upstream-reports/` (T-019); no durable two-source
decision record or independent review cursors are specified.

Specify a lightweight catch-up contract now:

- Keep A1 primary and A2 complementary, each with its own immutable
  reviewed-through commit, evidence date, and review scope.
- Check both on a regular maintainer cadence and before releases. Monthly is
  a proposed default, not an instruction already agreed with the maintainer.
- A1 review includes relevant method changes and release notes; A2 starts
  with the original `all-phases/all-phases-aidlc-mcp/` pattern and checks the
  wider catalog for useful developments. Do not silently freeze A2 to one file.
- Save tracked adopt/adapt/defer/reject rulings, with exact source evidence,
  local impact, and maintenance cost. Record no-change outcomes explicitly;
  revisit deferred decisions on the next run.
- Advance only fully assessed source cursors. A partial or inaccessible
  source retains its cursor and makes coverage incomplete.
- Separate review cursors from the runtime `SOURCE.lock.json`. Catch-up can
  inspect unreleased commits; A1 runtime adoption can remain release-tag-only.
  A2 need not have release tags or a parser to remain under review.
- Default to review/report; runtime adoption remains an explicit maintainer
  instruction. No scheduler, commit, publication, or upstream execution is
  implied. Preserve applicable licenses/provenance when copying guidance.

Let the skill work through ordinary source inspection before T-017 exists.
Later it can orchestrate the deterministic updater if that tool is retained.

## 4. P1 — The updater is a large prerequisite for trying the core workflow

Evidence: AWS-002.1, UPD-002/003, design §10–11, T-010–019, and T-030's
dependency on T-014. This includes a bespoke YAML-subset parser, heading-tree
diff, mapping DSL, normalization, exhaustive heading rulings, and staged
multi-file application. Even a harmless upstream YAML representation change
can block ingestion. The runtime skill cannot complete its planned build
before normalization exists.

The spec itself says the full pipeline is the largest initial build cost and
that the cost was accepted (§17). Therefore this is a recommendation to
reconsider sequencing, not an unapproved removal of the requirement.

Deliver a cited, manually adapted phase reference and the catch-up skill
first; prove create → approve → resume → invalidate → implement with them.
Keep immutable source identities, license preservation, offline runtime, and
human review. Build a synchronizer after real refreshes demonstrate which
parts are repetitive and what useful change classes look like. That staged
alternative requires explicit revisions to AWS-002, UPD-002/003 and the
reproducibility promises; it cannot honestly be called compliant as written.

If automation remains in release one, prefer JSON for local mappings rather
than designing another YAML dialect. Retain only upstream sections the
runtime actually uses, unless the full allowlist has a stated benefit.

## 5. P1 — Marker exceptions cannot be recorded at the point drafting is blocked

Evidence: WF-002.7 blocks **recording approval**; design §7.1 stores
`acceptedMarkers` on the dependent approval. But T-033 says to refuse to
**start** design while upstream markers are unaccepted, and §7.6 says a gate
is open when its phase may start while listing missing dependent acceptance
as a gate blocker.

Example: approved requirements contain one `(guess)` the developer wants
the design to investigate. No design approval exists yet to carry acceptance,
so one reading blocks drafting; the requirements allow drafting and only
block approval. No defined operation records an earlier acceptance.

Choose one meaning for a gate. The smaller correction is to let approved
upstream content permit drafting, then require named marker acceptance at
the dependent artifact's approval. Align T-033 and status accordingly. If
pre-draft acceptance is intended, specify its record and lifetime explicitly
instead of depending on an approval that does not yet exist.

## 6. P1 — Hash normalization can hide edits to approved task instructions

Evidence: design §7.3 steps 5–6 normalize **every** `[x]`/`[X]` marker and
drop list lines beginning `Outcome:` or `Exception:`. T-022 requires those
changes to preserve approval without limiting their syntactic location.

Example: a fenced verification command changes from
`rg -F '[x]' tasks.md` to `rg -F '[ ]' tasks.md`. The approved hash stays the
same under the specified transformation, although the command now checks
different behavior. A similarly shaped list line inside quoted or fenced
material can disappear from the hash.

Define exclusions only for parsed task/completion checkbox state and actual
progress-field records owned by those tasks. Literal examples, commands,
contracts, and fenced text must remain content-bound. Add a fixture proving
a literal checkbox edit invalidates approval while real progress does not.
This is a necessary boundary for the existing hash contract, not an argument
for stronger authentication machinery.

## 7. P1 — Retirement parity accidentally remains a release gate

Evidence: prior 2026-10-02 review finding #8 explicitly decoupled release
from T-058, and T-060 now depends on T-056. However T-064 requires **all**
requirements success measures; measure 7 is every retiring skill's parity
gate. The tasks definition of done also requires a parity report for each
retiring skill. T-065 depends on T-064.

Release can therefore still wait on retirement work despite the documented
decision to separate it. Identify release success measures explicitly and
keep T-058's parity evidence as a prerequisite for T-067 retirement, not
T-065 publication. Preserve the required parity standard itself.

## 8. P2 — T-012 cannot pass its own verification before T-013

Evidence: tasks lines 72–85. T-012's verification requires its adapter file
to parse with T-013's parser. T-013 depends on completing T-012. Execution
rules prohibit checking a task before its verification succeeds.

Move parser-integration verification to T-013, leaving T-012 verified with
mapping/schema fixtures, or revise the task boundaries. Do not implement a
later task secretly to satisfy an earlier task's acceptance.

## 9. P2 — Quick bugfix requirements contradict the bugfix artifact contract

Evidence: WF-003.4 prohibits omitting `requirements.md`; ART-005.1 prohibits
creating it for a bugfix, which must use `bugfix.md`. WF-003.7 applies quick
to bugfix specs.

Refer to “the requirements artifact (`requirements.md` for features,
`bugfix.md` for bugfixes), design.md, and tasks.md” in WF-003.4. This is a
wording correction, not a profile or artifact change.

## 10. P2 — Concurrency and atomic update promises exceed the described mechanism

Evidence: WF-006.1–2, design §7.5 and T-025/T-053; UPD-002.8, design §11.3
steps 14–15 and T-017.

Compare-immediately-before-write detects a change already observed. It does
not prevent two writers from both passing the comparison and then replacing
the same file. The current T-053 promise that the second writer cannot lose
work needs either serialized writes or a narrower contract. For a solo
developer, documenting one active writer and detecting intervening edits
may be preferable to adding distributed locking.

Likewise, “replace atomically” followed by “update source lock, hashes,
provenance” leaves the transaction boundary unclear. A crash or later write
failure could produce a mixed snapshot. Specify whether all outputs belong
to one validated replacement unit or application is recoverable through a
backup/rollback procedure. Test an interruption during application, rather
than only failure before it. Avoid inventing a generic transaction engine
when a smaller recoverable maintainer operation would suffice.

## 11. P2 — Compatibility feasibility is discovered after expensive commitments

Evidence: PKG-003 promises five hosts; design §12 retains unverified
installation/import behavior. T-040–044 arrive in Phase 6, after the updater,
state model, port inventory, references, and review machinery. T-027 probes
Kiro artifact/link behavior but does not establish all plugin loading paths.

Move minimal host-loading probes ahead of feature implementation: load one
skill, read one bundled reference, write a fixture artifact, and resume it
in another host. Establish supported installation paths and limitations
before promising the whole matrix. This can retain all five target hosts;
removing a host is a separate scope decision. Likewise, run the Kiro link
probe before investing in Windows junction machinery, as the existing
fallback already anticipates abandoning `specsDir` if Kiro cannot follow it.

## 12. P2 — Whole-source migration makes the first release harder to validate

Evidence: RULE-001, design §5.4/§15, T-069–079 and T-056–058. The project
imports two large approved port plans, adds rule/check inventory machinery,
and requires behavioral coverage on every supported host, including manual
IDE/Crew sessions. This is materially broader than proving portable files
and approval semantics.

Per-rule coverage and host parity were explicitly accepted in the scope
decision. The current design already shares sessions across rule evals;
do not misread it as requiring one full agent session per rule. Nor should
the old skills' original host be used as a reason to weaken a new plugin's
claimed cross-host behavior.

Recommended sequencing: separate a runnable portable core from the complete
personal-skill migration. Keep old skills until their agreed parity gate
passes. For any released slice, retain all its mandated review lenses and
checks; defer whole capabilities explicitly rather than silently thinning
their behavior. Optional advisory scan ports and additional review intents
are candidates for later slices. Source skill retirement and the autopilot
consumer migration can remain separate deliverables.

## Consolidation recommendations

1. Apply the clarified two-source policy and standardize one canonical,
   unshipped maintainer skill under the existing per-plugin tools project.
2. Make two-source catch-up usable immediately and preserve durable review
   evidence; do not tie it to completion of a synchronizer.
3. Correct marker/gate semantics, hashing exclusions, task verification order,
   quick bugfix wording, and the accidental retirement release prerequisite.
4. Establish host-loading feasibility early. Then reconsider the upfront
   synchronization and migration workload against a demonstrable core.

Keep the strong parts: one distributable root, offline runtime, canonical
Kiro-compatible Markdown, explicit human approvals, strict downstream
invalidation, preservation of native edits, and rule-backed retirement.
State hashing and a stable status interface have concrete users; they are
not speculative merely because the runtime is skills-based.

Avoid a second implementation of hash canonicalization unless needed:
design §5.3's shell `sed`/`tr` fallback duplicates Python behavior and its
cross-platform checks. Requiring Python for deterministic approval/status
operations is a reasonable simplification to consider, with the prerequisite
stated honestly. This changes a supported fallback and needs a decision.

Unresolved for consolidation: maintainer skill placement/native discovery;
catch-up cadence; whether the full updater remains a first-release gate;
delivery slices and their host support; draft-versus-approval gate semantics;
and the exact concurrency/update recovery guarantees. None was decided by
this review. No implementation or release was attempted.

Verification: the repository validator and its nine existing unit tests
pass. These check the current scaffold/example package, not the proposed
Specflow behavior or host integrations.
