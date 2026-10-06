# specflow and awslabs/aidlc-workflows - discovery

Date: 2026-09-28. Purpose: decide how specflow relates to AWS's maintained
AI-DLC implementation before any spec edit. The user's hypothesis
(2026-09-28): it "seems to try to achieve the same as we do and actually
should be a strong complement to the repository we started from".

## 0. Sources and verification

Clones read-only in the session scratchpad, never in this repo:

- **A1** `awslabs/aidlc-workflows` @ `fbb7f1c923991da91ca64136fddc9db854ecdbe6`
  (2026-09-28 08:48 UTC, "fix(plan-approval): ...", #1473). Latest release
  v2.10.0, 2026-09-24 (`CHANGELOG.md:4`; tag `v2.10.0` = `b1854bad`,
  `v2.9.0` = `22f5d1b1`, from `git ls-remote`). The bugfix discovery doc read
  A1 at `589bf38`; every A1 line it cites was re-read here at `fbb7f1c` and
  still matches (§10).
- **A2** `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` @
  `3e7c0f0aa2a1a084c94631edb709deae5fe0ae4f` (2026-08-07), the repository
  head. The subtree `all-phases/all-phases-aidlc-mcp/` has one commit ever,
  `d7b2d9b` (2026-05-05), so the current specflow upstream has not changed
  since it was added. (Corrected 2026-09-30 from the GitHub commits API; the
  first reading took `3e7c0f0` as the subtree's last commit.)
- **S** the specflow spec under `intake/processed/specflow/00001-initial-delivery/`
  (requirements 0.1, design 0.1, tasks 0.1) as of `776c07e`.

Every line number below was read by me in this session; no agent was used.
`rg` no-hit claims were control-checked (§8.3).

## 1. What A1 is, in one screen

- Method: 5 phases, 33 stages, 14 agents, 11 workflow profiles, human
  approval gates, a 105-event audit trail, "the same deterministic engine
  across every supported harness" (`README.md:107-113`).
- Harnesses: Claude Code, Kiro CLI >= 2.6, Kiro IDE 1.x / Kiro CLI v3, Codex
  CLI >= 0.145.0, Cursor, opencode >= 1.17, GitHub Copilot (`README.md:79-87`).
  No Kiro Crew (`rg -w crew` over `README.md` and `docs/guide/harnesses/`: no
  hit; the harness guide list is `codex-cli, copilot, cursor, kiro-cli,
  kiro-ide, opencode`).
- Shape: hand-authored `core/` (7.7 MB; stage, scope, protocol and conductor
  Markdown alone is 10,275 lines) projected per harness by `bun
  scripts/package.ts` (`AGENTS.md:10-13`). 78 TypeScript tools
  (`README.md:139`), 17 hooks (`AGENTS.md:32`). The orchestrator is a
  "forwarding loop": every move is a JSON directive from `aidlc engine
  orchestrate next`, every gate is reported back to the engine
  (`harness/kiro-ide/skills/aidlc/SKILL.md:44-57`; `stage-protocol.md:132`
  "Use the engine for every lifecycle transition").
- Install: native `aidlc` binary, "Bun and Node.js are not required"
  (`README.md:29-30`), or the copy channel which needs Bun >= 1.3.8
  (`docs/guide/18-install-and-lifecycle.md:1251-1258`). Both put an engine
  dir in the project (`.claude/`, `.kiro/`, `.codex/`, `.aidlc/`) plus a
  neutral `aidlc/` tree (`docs/guide/03-spaces-and-intents.md:19-25`).
- License MIT-0 (`LICENSE:1-3`; `package.json:13`). Same license as A2
  (`aws-samples-sdlc/LICENSE:1-3`).
- Design intent (v2 spec PDF, 6 pages): "Version 2 keeps the methodology and
  rebuilds the workflow layer to march progressively towards autonomous
  software delivery" (p.1 l.4-6); Skills per agentskills.io are the building
  block (p.3 l.112-117); extensibility must allow additive, replacement and
  composed stages (p.4 l.143-154); a package manager emits tool-specific
  artifacts from one canonical stage file (p.6 l.258-264); guidelines:
  deterministic routing, tool-owned state, explicit approval for every
  non-bootstrap stage, no hidden delegation (p.6 l.279-288).

## 2. Relation between A1 and A2

- A2 names A1 as its sibling: "This is a **complementary approach** to the
  rules-based awslabs/aidlc-workflows. Both can be used independently or
  together" and tabulates the difference: agent reads Markdown vs agent calls
  MCP tools; agent interprets rules vs server validates transitions;
  `current_phase.json` persistence; "Edit scattered markdown files" vs
  "Single `prompts.py` module"; dependencies "None (copy files)" vs
  "Python 3.10+, `mcp` package" (`all-phases-aidlc-mcp/README.md:7-15`).
- A1 never names A2: `rg -i "sample-ai-powered|aidlc_mcp|aws-samples"` over
  A1 hits only a test fixture env var `AIDLC_MCP_FIXTURE_KEY`
  (`tests/e2e/t-acp-kiro-mcp-headers.serial.test.ts:33`), unrelated.
  Control: `rg -c "awslabs/aidlc-workflows" README.md` = 3.
- A2's own comparison row "Dependencies: None (copy files)" for A1 predates
  A1 v2's engine; today A1 needs the `aidlc` binary or Bun (§1). The
  "rules-based" label is also stale: A1 routes off a compiled stage graph,
  not steering rules alone (`SKILL.md:50-57`).
- Cadence: A1 shipped 2.8.1 (09-08), 2.8.2 (09-10), 2.9.0 (09-15), 2.10.0
  (09-24) (`CHANGELOG.md:4,17,34,55`), roughly one release a week. A2 has not
  moved since 2026-08-07.

## 3. Comparison by concern

Legend: **S** = specflow spec; IDs are S requirement IDs.

### 3.1 Method and stages

| | A1 | A2 | S |
|---|---|---|---|
| Phases | initialization, ideation, inception, construction, operation; 33 stages (`docs/guide/05-scopes-and-depth.md:171-205`) | `PHASE_SEQUENCE_FULL` = discovery-0.1, inception-1.1/1.2, construction-2.1/2.2/2.3; abbreviated = discovery-0.1-lite, inception-1.1-lite, construction-2.2-lite, operations-3.1, deployment-2.3-lite (`server.py:30-45`) | intake, requirements, design, tasks, implementation, verification, complete (WF-001.1) |
| Requirements stage | `requirements-analysis`: intent analysis, FR{n}/FR{n}.{m} and NFR{n} IDs, constraints, assumptions, out of scope, open questions (`requirements-analysis.md:191-198`); IDs are "permanent traceability keys" (`:200-201`) | user stories in `INCEPTION_1_1` (`prompts.py:53`) | purpose, scope, user stories, `REQ-001`, EARS criteria (ART-002) |
| Design | `domain-design` (components.md, decisions.md ADR log), `units-generation`, `contract-design`, per-unit `functional-design`/`nfr-*`/`infrastructure-design` (`14-artifacts-reference.md:217-235`) | `CONSTRUCTION_2_1` DDD domain model per unit (`prompts.py:81`) | one `design.md` with fixed section list (ART-003.2, design §6.3) |
| Tasks | `delivery-planning` bolt-plan + Code Generation `code-generation-plan.md` per unit (`14-artifacts-reference.md:220,236`) | `CONSTRUCTION_2_2` plan with checkboxes (`prompts.py:94`; README:51) | one `tasks.md` with `T-001` checkboxes (ART-004) |
| Test floor | Minimal = 1 test per requirement + happy-path floor; `bugfix`/`security-patch` add "a targeted regression ... at the narrowest level that reproduces it ... the existing suite remains green" (`code-generation.md:131-141`; `05-scopes-and-depth.md:426-430`) | "Regression criteria" in lite stories (`prompts.py:163`, per bugfix doc) | VAL-002 proportionate tests; bugfix fail-first task 1 (ART-005.5) |
| Question protocol | questions file with `[Answer]:` tags, A-E + `X. Other`; three modes Guide me / I'll edit the file / Chat; batches up to 4 on Claude (`stage-protocol.md:347-356,394-406`; `14-artifacts-reference.md:262`); depth sets volume: Minimal ~2-4, Standard ~5-8, Comprehensive ~8-12+ per stage (`stage-protocol.md:370-374`); mandatory contradiction detection and overconfidence prevention (`:556-579`) | prompt text asks the agent to "ask clarifying questions" (README:51) | one question at a time (ART-002.6, WF-003.9, NFR usability) |
| Voice | "narrate the work, not the plumbing", reserved internal vocabulary (`stage-protocol.md:5-33`) | none | none stated |

A1 is the richer method by an order of magnitude and the only one still
moving. Its text is deeply engine-coupled: the requirements stage alone has
12 steps, five of which are `bun .../aidlc-utility.ts` or `engine orchestrate
report` calls (`requirements-analysis.md:59-99,209-213`).

### 3.2 Profiles vs scopes

| | A1 | A2 | S |
|---|---|---|---|
| Selector | 11 scopes: classic 18/33, express 10, feature 33, enterprise 33, mvp 23, poc 8, bugfix 9, refactor 10, infra 13, security-patch 10, workshop 26 (`docs/guide/workflow-profiles.md:22-34`) | `flowType: "full" \| "abbreviated"`; abbreviated "only used when explicitly requested" (README:19) | `standard` / `quick` (WF-003.1) |
| Orthogonal knobs | depth Minimal/Standard/Comprehensive (`05-scopes-and-depth.md:334-338`); test strategy; review cap; guard policy; three ceremony switches (`13-customization.md:201-213`) | none | profile only; spec type feature/bugfix (WF-003.8) |
| Scope file shape | YAML frontmatter `name, depth, keywords, description, skeleton, runner, review_cap, guard_policy, sensors, learnings, summary_confirmation` + prose "why these stages" (`core/scopes/aidlc-bugfix.md:1-44`); membership lives in each stage's `scopes:` list (`requirements-analysis.md:39-50`) | list constants in `server.py` | prose in `profiles/{standard,quick}.md` (design §3) |
| Auto-detect | keyword match (`fix, bug, broken` -> bugfix) plus an adaptive composer for long descriptions (`05-scopes-and-depth.md:221-235,248-278`) | project-type detection only | agent recommends, developer overrides (WF-003.5) |

S's two profiles map onto A1's depth axis, not onto its scopes: A1 `bugfix`
runs 9 stages at Minimal, `express` runs 10 with no design pass. S keeps all
three artifacts in every profile (WF-003.4), which A1 does not (express skips
design; `aidlc-express.md:19-21`).

### 3.3 Artifacts

| | A1 | A2 | S |
|---|---|---|---|
| Home | `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/<phase>/<stage>/<artifact>.md` (`10-state-and-audit.md:9`; `14-artifacts-reference.md:25-98`); path is engine-derived from canonical name + stage (`16-artifact-vocabulary.md:166-175,191-194`) | `.aidlc/` (README:42) | `.kiro/specs/NNNNN-<title>/{requirements\|bugfix,design,tasks}.md` (ART-001, decision 2026-09-27 #2) |
| Identity | UUIDv7 in `intents.json`; dir name is a label (`03-spaces-and-intents.md:82-86,100-104`) | feature dir name | `NNNNN` shared with intake and PRD |
| Shape control | team template override `aidlc/spaces/<space>/memory/templates/X.md`, whole-doc, "none ship at GA" (`stage-protocol.md:955-961`) | edit `prompts.py` | S templates in `templates/` (design §3) |
| Kiro spec awareness | none: `rg -i "\.kiro/specs\|kiro spec\|specType\|bugfix\.md"` over `core/ docs/ harness/` hits nothing relevant; Kiro's welcome panel "lists Kiro's own workflows; AI-DLC does not appear there" (`harnesses/kiro-ide.md:216-217`) | none | canonical |
| Where code goes | sibling repos / project dir, never the record dir (`14-artifacts-reference.md:143-151`) | `aidlc_integrate_code` copies from `.aidlc/` (README:54) | project |

The template override changes a file's headings but never its location, so
A1 cannot be configured to write `.kiro/specs/`. The `.aidlc/` non-goal in S
requirements §3.7 is correct for A2 and wrong for A1: A1's neutral tree is
`aidlc/` (no dot) and `.aidlc/` is the engine dir shared by opencode and
Copilot (`15-troubleshooting.md:60`).

### 3.4 State, approvals, invalidation

| | A1 | A2 | S |
|---|---|---|---|
| State | `aidlc-state.md` per intent, six-state checkboxes `[ ] [-] [?] [R] [x] [S]` (`10-state-and-audit.md:55-65`); append-only `audit/<host>-<clone>.md` shards (`:105-111,235`); state "can be reconstructed from the audit trail" (`:243`) | `current_phase.json` (README:13) | `.specflow.json` sidecar; phase derived (STATE-001.2) |
| Approval record | `GATE_APPROVED` audit row carrying the exact user label, emitted only by `aidlc-orchestrate.ts report` (`stage-protocol.md:276-279`); human-presence fence: an approval needs a real human turn, no in-band switch (`13-customization.md:305-311`); a Construction verification command needs "a matching current-workflow human approval receipt" from the invoking session (`10-state-and-audit.md:44-50`) | `aidlc_request_phase_approval` tool (`prompts.py:146`) | SHA-256 of canonical text + timestamp in sidecar (WF-002.4) |
| Content binding | review receipts bind digests (`16-artifact-vocabulary.md:196-202`); schema-3 `STAGE_COMPLETED` receipts carry a structure hash and a content hash (`12-state-machine.md:1453-1456`) | none | approval := status approved AND hash matches (design §7.3) |
| Invalidation | mismatch "projects the completed stage as `stale`" (`12-state-machine.md:1458-1459`); "The projection remains read-only and advisory ... suggested recovery is `/aidlc --stage <earliest-affected-stage>`, but this release does not enforce it" (`:1479-1484`); Guard Policy `strict` reopens approval on changed inputs, `relaxed`/`off` record `CHANGE_ACCEPTED` and continue (`13-customization.md:245-250`); defaults: strict for enterprise/security-patch/infra, relaxed for bugfix/feature/classic/..., off for express (`:264-270`) | none | any change stales the approval and all downstream approvals; gate closed (WF-002.5-6, VAL-001.5) |
| Resume | "Session resume works on every harness" (`11-session-management.md:5-6`); four options: resume, redo, jump, start fresh (`:73-78`); per-user `active-intent` cursor is gitignored so a teammate must `/aidlc intent <name>` first (`12-cli-commands.md:296`) | resume via `.aidlc/` (README:23) | recompute hashes, resume at first stale phase (WF-004) |
| Concurrency | per-clone audit shards, "no merge conflicts" (`10-state-and-audit.md:235`); workspace lock | none | compare-before-write (WF-006) |

S is stricter than A1's defaults on invalidation and simpler on state (one
JSON file vs state + shards + engine dir). A1's approvals are enforced by
hooks; S's are instructions plus an optional validator (design §5.3).

### 3.5 Runtime needs

| | A1 | A2 | S |
|---|---|---|---|
| Required | `aidlc` binary (native) or Bun >= 1.3.8 (copy channel) (§1); engine dir + `aidlc/` shell in every project (`harnesses/kiro-ide.md:127-131`) | Python 3.10+, `mcp` (A2 README:15) | none; Markdown + JSON; optional stdlib Python helper; `shasum` fallback (requirements §7; design §5.3) |
| Hooks | 17, incl. hard blocks while a gate is open (`harnesses/kiro-ide.md:264-276`) | MCP server validates transitions | none |

S's "no runtime" (requirements §7, PKG-001.3) and A1's engine are the
central incompatibility. A1 cannot be "just text" for S: its prose assumes
the engine on every step.

### 3.6 Harness coverage

| Surface | A1 | S target |
|---|---|---|
| Kiro IDE 1.x / Kiro CLI v3 | folder-drop into `.kiro/` (`skills/aidlc/SKILL.md`, `agents/aidlc.md`, 14 persona `.md`, `settings/cli.json`, `steering/`, `hooks/*.json`) (`harnesses/kiro-ide.md:150-171`); numbered-prose questions, no widget (`:308-311`); persona `fs_write` denied under `.kiro/**` (`harness/kiro-ide/manifest.ts:70-73`); conductor's filesystem allow covers only `aidlc/spaces/**`, `.kiro/sensors/**` and one marker (`harness/kiro-ide/agents/aidlc.md:38-43`) | Kiro Power via Agent Plugins v1 (PKG-003.1) |
| Kiro Powers / Agent Plugins v1 | zero mentions: `rg -w -i "agent-plugins\.org\|Agent Plugins\|POWER\.md\|Kiro Power"` over `core/ docs/ harness/ scripts/ plugins/` = no hit (control `rg -w -c "Kiro IDE" harnesses/kiro-ide.md` = 31). A1's own plugin projection uses a `.kiro-plugin/` manifest dir (`harness/kiro-ide/manifest.ts:200`; `18-plugin-mechanism.md:602`), not Kiro's Powers format | PKG-001, PKG-003 |
| Kiro Crew | not supported (§1) | PKG-003.4 |
| Codex | `.codex/` engine dir, `$aidlc` (`README.md:69,84`) | root Agent Plugins manifest (PKG-003.2) |
| Claude Code | `.claude/` engine dir, `.mcp.json` with 5 servers (`harness/claude/manifest.ts:44-68`) | `.claude-plugin/plugin.json` (PKG-003.3) |
| Cross-harness | `aidlc/` is harness-neutral; moving a project between harnesses is "supported-but-untested" (`harnesses/kiro-ide.md:324-327`); two harnesses sharing one engine dir "cannot coexist" (`15-troubleshooting.md:60`) | success measure 1: Kiro -> Codex -> Claude -> Kiro with no relocation |

Neither AWS source covers S's packaging goals (Agent Plugins v1, Kiro Powers,
Crew). That layer stays S's own under every option below.

### 3.7 Extensibility

A1 plugins: a directory with `.aidlc-plugin/plugin.json` and core-shaped
subtrees (`stages/`, `contributions/`, `agents/`, `scopes/`, `knowledge/`,
`sensors/`, `tools/`) (`10-authoring-a-plugin.md:33-82`). Rules: "A plugin
never edits `core/`" (`:8-14`); contributions are "additive only ... cannot
override or remove a core stage's fields, agent, or prose" (`:656-661`);
produced artifacts must be `<plugin>-` prefixed (`:117-118`); number ranges
are not claimed (`:109`). Distribution: the packager "emits a real host
plugin" per harness (`.claude-plugin/`, `.codex-plugin/`, `.kiro-plugin/`
...), trust is host-native, Kiro is a folder-drop with "no install-time trust
gate" (`18-plugin-mechanism.md:34-40,602`). Deferred today: `memory/`
projection, `when:` evaluation, `dependencies`, machine-enforced
`required_sections` (`18-plugin-mechanism.md:594`; `10-authoring-a-plugin.md:153-156,193-211`).

A2: edit `prompts.py` (`PROMPTS_CUSTOMIZATION.md`, README:14). S: local
adapter files the updater never overwrites (decision 2026-09-27 #5).

### 3.8 Updater fit

| | A2 (current UPD-002) | A1 |
|---|---|---|
| Source form | one Python module, 257 lines, 11 string constants + `PROMPTS` dict (`prompts.py:40-256`) | Markdown with YAML frontmatter: 11 scope files (35-59 lines each), 33 stage files (86-581 lines), 9 protocol files (32-1131 lines) (`wc -l`, §1) |
| Parse | `ast`, literal-only (UPD-002.4, design §10.2) | frontmatter keys + heading tree; no code to avoid executing; YAML is simple block/flow lists (`requirements-analysis.md:1-53`) |
| Semantic diff targets | prompt keys, template variables, phase order, tool names, artifact paths, gates, license (UPD-002.5) | scope membership (`scopes:` lists), `produces`/`consumes`, `required_sections`, depth table, gate wording, `{{HARNESS_DIR}}`/`{{INVOKE}}` tokens, license |
| Pin | `main` -> commit (design §10.1) | release tag `vX.Y.Z` (`19-supply-chain-security.md:16-22`), which also has a CHANGELOG entry per release (`AGENTS.md:57-61`) |
| Churn | none since 2026-08-07 | weekly; `CHANGELOG.md` is 634 KB |
| Adaptation load | strip `.aidlc/` paths and MCP tool names (design §9.4) | strip engine calls, `[Answer]:` file protocol, audit events, sensors, `{{INVOKE}}`; keep method content. Most of a stage file is plumbing (§3.1), so "verbatim upstream vs local adaptation" (AWS-002.4) inverts: the adaptation would outweigh the verbatim text |

An A1 allowlist that carries method and little plumbing: `core/scopes/*.md`,
`stages/inception/requirements-analysis.md`, `stages/inception/domain-design.md`,
`stages/inception/units-generation.md`, `stages/construction/code-generation.md`
(test floor, `:131-141`), `stages/construction/build-and-test.md`,
`protocols/stage-protocol.md` §3 (questions, depth, contradiction) and its
§8 test strategy, `docs/guide/05-scopes-and-depth.md` matrix (`:171-205`,
kept in sync by a test), `LICENSE`. Roughly 2,500 lines, all Markdown.

### 3.9 Provenance and license

Both MIT-0 (§1). A1 is an `awslabs` repo with signed release attestation
(`18-install-and-lifecycle.md:1267-1276`); A2 is an `aws-samples` pattern.
AWS-001.1 names A2 by repository; AWS-001.4 (MIT-0) holds for either.

### 3.10 Bugfix (already decided; recheck only)

Lines the bugfix doc cites were re-read at `fbb7f1c` and are unchanged:
`core/scopes/aidlc-bugfix.md:2-3,4-7,12,25,41-44`;
`docs/reference/04-stages/inception.md:72`; `code-generation.md:138`;
`harnesses/kiro-ide.md:216-217`. The bugfix contract mirrors Kiro and cites
no AWS upstream for depth (bugfix doc §5-6); nothing here reopens it.

## 4. Hard facts that bound the options

1. A1's artifact location is engine-derived and not configurable
   (`16-artifact-vocabulary.md:166-175`); template overrides change headings
   only (`stage-protocol.md:955-961`). Canonical `.kiro/specs/` (settled)
   cannot be produced by A1 itself.
2. On Kiro IDE, A1 personas are denied writes under `.kiro/**`
   (`manifest.ts:70-73`) and the conductor's auto-approved writes cover only
   `aidlc/spaces/**` (`agents/aidlc.md:38-43`). A "Kiro exporter" stage would
   prompt or be refused on the one harness that matters most.
3. A1 requires the `aidlc` binary or Bun (§3.5). S requires no runtime
   (requirements §7). These cannot both hold in one package.
4. A1 plugins are additive only (§3.7): S could add stages and scopes to A1
   but could not shrink A1 to Kiro's three documents.
5. A1 has zero awareness of Kiro specs, Kiro Powers, Agent Plugins v1 or Kiro
   Crew (§3.3, §3.6). Packaging and artifact contract stay S's own work.
6. A2 is idle (7 weeks) and A1 ships weekly (§2). A2 says A1 is complementary;
   A1 does not say so back.
7. A1's method text is engine-coupled; an A1-based reference is mostly
   adaptation (§3.8). A2's prompts are self-contained but thin (257 lines).

## 5. Options for the upstream question (A1 vs A2)

Each option names what it changes in S. IDs are S requirement IDs.

### A. A1 replaces A2 as the pinned upstream (recommended)

Pin an A1 release tag; allowlist the Markdown in §3.8; updater parses
frontmatter + headings (no Python `ast`); A2 retires to a "prior source" note
in `adaptation.md`.

- Benefit: the method source is maintained, richer (scopes, depth, test
  floors, contradiction rules, FR/NFR IDs) and versioned by tags with a
  changelog, so UPD-002's semantic diff has real releases to diff.
- Drawback: A1 text is engine-coupled, so normalization strips more than it
  keeps and the "verbatim vs adaptation" rule (AWS-002.4) flips; weekly
  upstream releases mean more updater runs (mitigated by pinning tags and
  updating on demand).
- Strongest reason against: S's `standard`/`quick` profiles and three
  documents are a deliberate simplification; grounding them in an 11-scope,
  33-stage method invites scope creep back toward A1's ceremony.
- S changes: AWS-001.1-2 (repo, subtree = allowlist), UPD-002.4 (parser),
  UPD-002.5 (diff targets), design §3 `aws/raw/` (Markdown files, not
  `prompts.py`), §9.1-9.2 (guidance-source column), §10.1-10.3, §11.3 step
  8, §17 "Manual upstream refresh" rationale, requirements §3.7 wording;
  tasks T-010, T-012-T-015. Plan B: untouched (its rows key on ART/WF IDs).

### B. A1 beside A2 (two pins)

A2 keeps supplying compact phase prompts; A1 supplies scopes, depth and test
floors.

- Benefit: matches both A2's "complementary" claim and the user's hypothesis;
  A2's prompts are already the closest analog to S's phase references.
- Drawback: two parsers (`ast` and Markdown), two pins, two vocabularies to
  reconcile (`.aidlc/` vs `aidlc/`; 6 phases vs 33 stages), and one source
  is idle, so half the updater guards nothing.
- S changes: as A plus a second `SOURCE.lock.json` entry and adapter
  namespace; tasks T-010-T-015 roughly double.

### C. specflow as an A1 plugin plus a Kiro exporter

Ship S as an AIDLC plugin (`.aidlc-plugin/plugin.json`, own stages/scopes)
and add a stage that mirrors the record dir into `.kiro/specs/`.

- Benefit: inherits A1's engine, hooks, audit trail and seven harnesses for
  free; no updater at all (the plugin composes over the installed core).
- Drawback: violates §4.1-4 (location not configurable, `.kiro/**` writes
  denied on Kiro IDE, runtime required, additive-only), so `.kiro/specs/`
  becomes a derived copy, not canonical, and "no runtime" is dropped.
  Reopens two settled decisions (canonical Kiro artifacts; no runtime).
- S changes: a rewrite, not an edit. Plan B invalidated: A1's own stages
  replace the design/tasks phase behavior it ports.

### D. Keep A2 only

- Benefit: zero spec churn; the `ast` updater design is already written.
- Drawback: the upstream is idle and thin; the updater guards a source that
  does not change; the richer method stays out of reach except by hand.
- S changes: none. Plan B untouched.

### E. No vendored upstream; cite A1 and Kiro as references only

Author S's phase references directly (a few hundred lines), keep a `SOURCES.md`
with A1/A2/Kiro URLs and commits, drop UPD-001-003 and the updater.

- Benefit: removes the largest first-release cost (design §17 calls the
  pipeline "the largest build cost in the first release"); no parser, no
  adapter schema, no semantic diff, no release-boundary scanning for updater
  markers.
- Drawback: gives up goal 5 (inspectable prompt provenance) and success
  measure 5; upstream improvements arrive only when a human re-reads A1.
- S changes: delete AWS-002, UPD-001-003, SEC-001 (updater half), design
  §9.4, §10, §11, §17 "Manual upstream refresh"; tasks T-010-T-019, T-060;
  PKG-002.3-5 shrink to release tooling only. Plan B untouched.

## 6. Follow-on decisions (only if A or B is chosen)

1. Allowlist: the §3.8 set, or scopes + protocol only.
2. Pin policy: release tags only (recommended) vs any commit.
3. Parser: frontmatter + headings in stdlib Python vs vendoring verbatim and
   diffing by section hash.
4. Profile model: keep `standard`/`quick` (recommended, WF-003 settled shape)
   and map them to A1 depth Standard/Minimal in `adaptation.md`, or adopt A1
   scope names as profiles.
5. Question protocol: keep one-at-a-time (recommended; user rule) and cite
   A1's depth table for volume only.
6. Invalidation: keep S strict (recommended); record A1's guard policy as a
   rejected alternative in design §17.
7. IDs: keep `REQ-`/`T-` for feature specs (settled 2026-09-27) or adopt A1's
   `FR{n}`/`NFR{n}`; Kiro bugfix numbering is already settled.

## 7. Ripple

- Requirements §3.7 names `.aidlc/`; under A/B it should name A1's
  `aidlc/spaces/.../intents/` tree as well. Not edited in this session.
- Design §9.3 says bugfix depth rules "cite Kiro only until the
  aidlc-workflows discovery settles the AWS upstream"; A or B lets A1's
  regression floor (`code-generation.md:138`) be cited as supporting text,
  never as the shape.
- Plan B (`discovery/00001-specflow-port-autopilot-phases.md`): only option
  C invalidates it. A, B, D, E leave every row valid; A/B change design §9
  tables that Plan B does not cite.
- Bugfix doc §2.2 and §6 line numbers hold at `fbb7f1c` (§3.10); §6's "A1
  never mentions A2" holds, and A2's mention of A1 (§2) is new information
  that §6 lacked.

## 8. Method notes

1. Clones live in the session scratchpad and are deleted with it; nothing
   from either clone was copied into this repo.
2. PDF read: pages 1-6 of `assets/AI-DLC-Workflows-2.0-Specification.pdf`
   (the whole file).
3. `rg` controls: `awslabs/aidlc-workflows` in A1 `README.md` = 3 hits;
   `-w "Kiro IDE"` in `harnesses/kiro-ide.md` = 31 hits. A first
   `powers` search without `-w` drowned in `PowerShell` (34 KB) and was
   redone word-bounded.
4. `du -sh` on `core/` = 7.7 MB; line counts from `wc -l` (§1, §3.8).

## 9. Decision minutes (2026-09-28, user)

Full text: `meta/decisions.md` (2026-09-28; #1, #3, #7, #8 since superseded). Spec files
were not edited in this session.

| # | Question | Decision | Status |
|---|---|---|---|
| 1 | Upstream (§5) | A: A1 replaces A2 | queued -> spec rewrite |
| 2 | Allowlist (§3.8, §6.1-2) | phase-fit set; pin release tags only | queued |
| 3 | Parser (§6.3) | structural: frontmatter subset + heading tree, fail-closed | queued |
| 4 | Profiles (§6.4) | keep standard/quick, map to A1 depth Standard/Minimal | queued |
| 5 | Invalidation (§6.6) | stays strict; A1 guard policy -> design §17 rejected | queued |
| 6 | Requirements §3.7 wording (§7) | name AWS record tree `aidlc/` or `.aidlc/` | queued |
| 7 | Adapter file format | same YAML subset or JSON, stdlib-only tooling | queued |
| 8 | A2 retirement | provenance note in `adaptation.md`; AWS-001.1 renamed | queued |
| - | Question protocol (§6.5), IDs (§6.7) | settled by standing rule / 2026-09-27 decision | not asked |
