# specflow docs commit review - 2026-10-03

Target: `d0887aa` (docs(specflow): initial delivery spec), 14 files, 5,001
lines. Read in full: both decisions, `README.md`, `requirements.md`,
`design.md`, the 2026-10-02 spec review. Skimmed: `tasks.md` (65 tasks, 8
phases), aidlc discovery §2, §5.

Lenses asked for: (1) upstream change A2 -> A1 captured right, (2) a
maintainer-only skill pattern for this repo, (3) over-engineering and
premature optimization.

Result: 2 high (settled by the user or needs one call), 4 high
over-engineering, 4 medium, 4 low.

## F1 - HIGH - A2 is recorded as dropped; the user keeps both upstreams

Settled by the user (2026-10-03): A1 `awslabs/aidlc-workflows` is now the main
source of method, A2 `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` was
the original and stays tracked. Both get regular catch-up.

The commit says the opposite in six places:

- decision 2026-09-28 #1 "A2 is retired", #8 "Retire A2 with a provenance note"
- requirements AWS-001.7 (provenance note "why it was replaced")
- design §9.4 last paragraph, §17 "Keep the aws-samples upstream, or pin it
  beside A1" (rejected), §18 "Prior upstream, retired"
- README working assumptions name only A1

Also missing: any cadence or trigger for "regularly". Design §17 says
"updating on demand"; nothing reminds anyone.

Fix shape (after F2/F3 decisions): amend decision 2026-09-28 #1/#8 with a
dated reversal; AWS-001 names A1 as primary and A2 as secondary tracked
source; §17 drops the "Keep A2" rejection; each upstream gets a catch-up
skill and a `last-reviewed` pin. A2's "two parsers" objection dies if F3 is
taken (no parser at all).

## F2 - HIGH - No repo convention for maintainer-only skills; Claude Code cannot see the planned one

Design §3/§11.1 puts one updater at repo-root `.agents/skills/update-aws-prompts/`
and defers `.claude/skills/` and `.kiro/skills/` launchers "later". Claude Code
reads project skills from `.claude/skills/` only, so a maintainer on Claude
Code (this repo's main tool) cannot invoke it. Codex reads `.agents/skills/`.
Kiro's project skill path is unverified (guess: `.kiro/skills/`).

Maintainer material for specflow is spread over four roots: `.agents/skills/`,
`tools/specflow/`, `tests/specflow/`, `docs/dev/tmp/specflow/`. Nothing in
`AGENTS.md`, `CONTRIBUTING.md`, or `scripts/validate.py` names the pattern, so
the next plugin will invent its own.

Decision needed: where maintainer skills live and how every tool finds them.
Hosts install `plugins/<name>/` as-is, so anything inside it ships.

Options:

1. **(Recommended) `maintain/<plugin>/{skills,tools,tests}` + links.** One
   repo-only source folder per plugin; committed relative symlinks
   `.agents/skills/<plugin>-<skill>` and `.claude/skills/<plugin>-<skill>`
   (`.kiro/skills/` once verified); `validate.py` fails on a broken link or a
   maintainer skill under `plugins/`. Benefit: one folder per plugin, every
   tool discovers it, `plugins/<name>` stays the release. Drawback: new
   top-level dir, symlinks awkward on Windows checkouts. Effort M.
2. **Root `.agents/skills/` + `.claude/skills/` links.** Spec layout plus
   links and an AGENTS.md rule. Benefit: smallest change. Drawback: material
   stays split over `.agents`, `tools/<plugin>`, `tests/<plugin>`; not "part
   of the plugin's project folder". Effort S.
3. **`plugins/<name>/{plugin,maintain}`.** Plugin dir becomes the project
   folder, `plugin/` ships. Benefit: matches "within its project folder"
   literally. Drawback: install path `plugins/specflow/plugin`; repo
   invariant (dir name = manifest name), validator, AGENTS.md, template all
   change. Effort M-L.
4. **Inside plugin, stripped at release.** Benefit: literally inside the
   plugin. Drawback: ships unless a distribution branch is built (deferred in
   §17); breaks the physical boundary. Effort L.

Whichever wins: document it in `AGENTS.md` and `CONTRIBUTING.md`, add a
validator check, and add a maintainer-skill example to `templates/`.

## F3 - HIGH (over-engineering) - The upstream updater pipeline is a compiler for a reading task

Design §10-§11, UPD-002, UPD-003, SEC-001, REL-001.3/.5, the determinism NFR,
tasks Phase 2 (T-010..T-019, 10 tasks). It builds: a stdlib YAML-subset
parser, a heading-tree differ with 7 tracked frontmatter keys, an adapter
YAML DSL (`extract`/`ignore`/`drops`), a deterministic normalizer, staged
atomic apply, a 19-file / 3,705-line raw snapshot shipped in the plugin, and
byte-reproducible regeneration. §17 admits "the largest build cost in the
first release".

What the job actually is: read what changed upstream since the last reviewed
ref, decide what to adopt, edit specflow's own references by hand, record the
new ref. That is a catch-up skill (the user already runs this pattern:
`catchup-ecc`, `git-ferry:catchup-upstream`). The runtime never reads `raw/`
("provenance only", §5.2); a URL + SHA in `adaptation.md` is the provenance.
MIT-0 does not even require attribution.

Lazy version: per-upstream maintainer skill + `upstream.lock.json`
(`repo`, `ref`, `reviewedAt`), `git diff <old>..<new> -- <paths>` read by the
agent, edits to hand-written `references/*.md` with a "Source: A1 <path> @
<tag>" line per adopted passage. Cuts ~10 tasks, AWS-002.1/.3, UPD-002.3-8,
UPD-003 entirely, SEC-001.1-4, REL-001.3/.5, "byte-for-byte reproducible".
Cost: no machine-checked mapping completeness; drift is caught by a human
reading a diff, which is what happens anyway at review time.

## F4 - HIGH (over-engineering) - Parity gate: one eval per rule, on every host

RULE-001.3-6, §5.4, §15 "Scenario evals" and "Parity gate", T-030, T-056-058,
T-069, T-079. Plan A + Plan B approve hundreds of rows (Plan B alone: 65),
each becomes a rule with its own eval, scored on 5 hosts, with recorded manual
runs for Kiro IDE and Crew, an `inventory.json`, and `check_rules.py --area`.

The parity gate exists to retire the user's personal skills, which only run on
Claude Code. Running them "on every supported host" measures something the old
skill never did. Lazy version: inline rule IDs stay (cheap, good); evals are
per session, not per rule; parity runs on Claude Code only; other hosts get
the compatibility fixtures that already exist (§15). Drop `inventory.json` +
`check_rules.py` or shrink it to "every ID in plan matrix appears in exactly
one runtime file" (one grep).

## F5 - HIGH (premature) - Five hosts in release one

PKG-003, §12, Phase 6 (T-040..T-046), success measure 6, release steps 4-6.
Kiro IDE, Kiro CLI, Kiro Crew, Codex, Claude Code, with Crew install path and
Kiro CLI headless "to be verified". Ship Claude Code + Codex + Kiro IDE
(the artifact-compat target); add Kiro CLI and Crew when someone uses them.
The portable package already lets an unknown Agent Skills host try it (§7
Compatibility), so nothing is lost.

## F6 - HIGH (premature) - `.kiro/specs` relink machinery

INT-001.7, ART-001.8, SEC-002.5-6, §6.7 "The specs link", T-027/T-028, a new
`windows-latest` CI job. Symlink on POSIX, junction via `cmd.exe` on Windows,
path character whitelist to make `cmd.exe` safe, `.gitignore` editing, refusal
cases, "real ignored folder" detection. All of it exists so buvis repos can
keep specs under `docs/dev/project-management/specs`, and it already carries
an unverified premise (does Kiro follow the link? T-027) with a written
fallback that deletes it all.

Lazy version: specs live in `.kiro/specs/`, full stop. `root` still moves
intake and reviews. buvis repos accept `.kiro/specs/` (or autopilot reads it).
Add `specsDir` when a real user cannot live with `.kiro/specs/`.

## F7 - MEDIUM - Design-First creation path

Added by the 2026-10-02 review #5: workflow order chosen at intake, reversed
traceability, mirrored invalidation graph, compatibility fixtures per host.
Kiro supports it, but creating Design-First specs is a second state machine.
Lazy version: create Requirements-First only; resume a Kiro-made Design-First
spec without breaking it (gates by upstream, already generic). Add creation
when someone asks.

## F8 - MEDIUM - Advisory review scripts ported in release one

`scripts/review/*.py` (3 scans) + `check_links.py`, with three defect fixes,
§5.5 "Scripts". Advisory and optional by the spec's own words. Defer to the
release that retires review-design-doc.

## F9 - MEDIUM - Shell hashing fallback

§5.3, Portability NFR: `shasum`/`sha256sum` + a pinned `sed`/`tr` pipeline,
contract-tested against the helper. Python 3 is already a stated prerequisite
for relink and Windows. Require Python 3 for approvals, drop the shell path.

## F10 - MEDIUM - Status JSON as a versioned public schema

STATE-003, §7.6, `specflow-status.schema.json`, `statusVersion`. Built for the
autopilot repoint, which is autopilot's own future PRD. Keep `status --json`;
drop the shipped schema and versioning promise until a second consumer exists.

## F11 - LOW - `acceptedMarkers` exact-line ledger

WF-002.7, §7.1. Simpler: refuse approval while upstream markers exist; the
developer resolves or deletes them. Keeps state smaller.

## F12 - LOW - `numberScan` extra folders

INT-001.4, §6.7. Only needed while buvis PRDs share the number space. Fine to
keep if cheap; it is one list.

## F13 - LOW - Decision docs still say "not yet applied"

Both decision files open with "Status: decided, not yet applied to the
specflow spec" though the 0.2 rewrite applied them.

## F14 - LOW - README "Working assumptions" omits A2 and the maintainer pattern

Follows from F1/F2.

## Not findings

Kept on purpose: hash-bound approvals and invalidation (core value), Kiro
bugfix shape, `.config.kiro` writing, physical `plugins/<name>/` release
boundary, one-question-at-a-time.

## Summary for consolidation

No spec edits applied; this report is input to a merge with a parallel
review. Order below is the suggested decision order (upstream first).

| # | Sev | Lens | Finding | Recommendation | Status |
|---|-----|------|---------|----------------|--------|
| F1 | High | upstream | A2 recorded as retired in 6 places; no catch-up cadence | Keep A1 primary, A2 secondary, both caught up regularly | settled by user 2026-10-03; edits wait on F2/F3 |
| F2 | High | maintainer skill | No convention; planned `.agents/skills` updater invisible to Claude Code | Option 1: `maintain/<plugin>/` + links, codified in AGENTS.md, validator, template | open |
| F3 | High | over-eng | Updater pipeline (parser, adapters DSL, normalizer, raw snapshot) | Replace with per-upstream catch-up skill + `upstream.lock.json` + hand-edited references | open |
| F4 | High | over-eng | One eval per rule on every host; inventory + `check_rules.py` | Evals per session; parity on Claude Code only; grep-level ID check | open |
| F5 | High | premature | Five hosts in release one | Claude Code, Codex, Kiro IDE; defer Kiro CLI, Crew | open |
| F6 | High | premature | `.kiro/specs` relink (symlink/junction, Windows CI) | Specs always in `.kiro/specs/`; `root` still moves intake/reviews | open |
| F7 | Medium | premature | Design-First creation path | Create Requirements-First only; resume Kiro-made Design-First | open |
| F8 | Medium | premature | Advisory review scripts ported now | Defer to review-design-doc retirement release | open |
| F9 | Medium | over-eng | Shell `sed`/`tr` hashing fallback | Require Python 3 for approvals | open |
| F10 | Medium | premature | Versioned public status schema | Keep `status --json`, drop schema/version promise | open |
| F11 | Low | over-eng | `acceptedMarkers` exact-line ledger | Block approval while markers exist | open |
| F12 | Low | over-eng | `numberScan` extra folders | Keep if cheap; drop after autopilot repoint | open |
| F13 | Low | hygiene | Decision docs say "not yet applied" | Update status lines | open |
| F14 | Low | hygiene | README assumptions omit A2 and maintainer pattern | Update with F1/F2 | open |

Rough effect if F3-F10 are taken (guess, from task titles): about 25 of 65
tasks drop or shrink, mostly Phases 2, 6, 7.
