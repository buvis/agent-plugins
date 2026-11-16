---
eligibility: engram nudge --help
default_model: sonnet
model_tier_rationale: transcription - every shipped file's content is given here; tests are additive and fail loudly
---

# Engram plugin: recall skill, MCP server, and per-host nudge hooks

Source: graduated spike in `buvis/engram`,
`docs/dev/project-management/spikes/engram-plugin/SPEC.md` (2026-11-10).
Spike code never merges; this PRD rebuilds from the contract below.
Companions: Engram PRD 00012 (`engram mcp`, `engram nudge`; this PRD's
eligibility check waits for it to be installed) and intake 00066
(orchestrator injection, which shares the two environment guards).

## Overview

### Problem Statement

Agents do not ask Engram on their own: 14 of 364 Claude sessions since
2026-11-01 called it, all through the catch-up skill. A host loads only what a
plugin gives it. Engram needs one package that puts a skill and a tool in front
of every host, and adds a push path on the hosts whose hooks can inject context.

### Target Users

The maintainer's agents on Claude Code, Codex, Copilot CLI, and Pi.

### Success Metrics

- `python3 scripts/validate.py plugins/engram` exits 0.
- `python3 -m unittest discover -s tests/engram` passes.
- No shipped file names a path inside the plugin: every hook and the MCP
  server call the bare `engram` command, so no host placeholder is needed.

Non-goals for v1: a Kiro hook adapter (its hook file schema is unread), a
Gemini CLI adapter (the CLI cannot authenticate on the maintainer's machine),
and a hook shipped through the Codex plugin manifest (only config-level Codex
hooks were verified).

## Functional Decomposition

### Capability: Portable pull path

Works on every host that reads Agent Plugins v1.

#### Feature: Recall skill

- **Description**: Tell the agent when and how to ask Engram.
- **Inputs**: None.
- **Outputs**: `plugins/engram/skills/recall-prior-work/SKILL.md`.
- **Behavior**: Frontmatter `name: recall-prior-work` and `description: Use
  before a broad search for prior decisions, past sessions, history, or
  cross-repo "where/why" questions. Triggers on "have we done this before",
  "why did we", "where else", "which repo".` Body, in this order: one line
  "Ask engram before you sweep repositories with `rg`, `grep`, or `git log`.";
  a bash block with `engram query --scope repo "<question in plain words>" -k 5`
  and the same line with `--scope portfolio`; four bullets: when to use each
  scope; each hit is `rank score path:start-end heading`, read the cited lines
  before relying on them; Engram indexes code, PRDs, memory, and past agent
  sessions and does not replace `rg` inside a known file; a nonzero
  `engram status --scope portfolio` means the index is stale, say so when
  citing a hit.

#### Feature: MCP configuration

- **Description**: Register Engram's own MCP server.
- **Inputs**: None.
- **Outputs**: `plugins/engram/mcp.json`.
- **Behavior**: Exact content: `$schema` is
  `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`; `mcpServers` has
  one server `engram` with `"type": "stdio"`, `"command": "engram"`,
  `"args": ["mcp"]`.

### Capability: Per-host push path

After a shell tool call, the host runs `engram nudge <host>`; Engram decides
whether the search was broad and prints the host's context-injection output.

#### Feature: Claude Code adapter

- **Description**: PostToolUse hook for the Bash tool.
- **Inputs**: None.
- **Outputs**: `plugins/engram/com.anthropic.claude-code/hooks.json`,
  `plugins/engram/.claude-plugin/plugin.json`.
- **Behavior**: `hooks.json` holds `hooks.PostToolUse` with one entry:
  `matcher` `Bash`, one hook `{"type": "command", "command": "engram nudge
  claude", "timeout": 12}`. The Claude manifest repeats the root manifest's
  `name`, `version`, `description`, `author`, and `license`, and adds
  `"hooks": "./com.anthropic.claude-code/hooks.json"` (guess: path-valued
  `hooks` field; every installed buvis plugin uses the default
  `hooks/hooks.json` instead) and an inline
  `"mcpServers": {"engram": {"command": "engram", "args": ["mcp"]}}`, because
  Claude Code does not read the portable `mcp.json`. Verified live in the
  spike: the same hook in project settings injected the recall lines.

#### Feature: Codex adapter

- **Description**: PostToolUse hook for the Bash tool, installed at user level.
- **Inputs**: None.
- **Outputs**: `plugins/engram/com.openai.codex/hooks.json`.
- **Behavior**: Same shape as the Claude file with command
  `engram nudge codex`. The README tells the user to merge it into
  `~/.codex/hooks.json`. Verified live in the spike on Codex 0.167.0 through a
  config-level hook; a repository `.codex/hooks.json` did not fire.

#### Feature: Copilot CLI adapter

- **Description**: `postToolUse` hook.
- **Inputs**: None.
- **Outputs**: `plugins/engram/com.github.copilot/hooks.json`.
- **Behavior**: `{"version": 1, "hooks": {"postToolUse": [{"type": "command",
  "bash": "engram nudge copilot", "timeoutSec": 12}]}}`. The README tells the
  user to copy it to `~/.copilot/hooks/engram.json`. Verified live in the
  spike on Copilot CLI 1.0.108 from a repository `.github/hooks/` file.

#### Feature: Pi adapter

- **Description**: Extension that appends the nudge text to a bash result.
- **Inputs**: None.
- **Outputs**: `plugins/engram/works.earendil.pi/engram-nudge.ts`.
- **Behavior**: Default-export a function taking `pi`. On `tool_result`,
  return unless `isBashToolResult(event)`; run `engram nudge plain` with stdin
  `JSON.stringify({tool_input: event.input, cwd: ctx.cwd})` and a 12 s
  timeout; when stdout is non-empty, return
  `{content: [...event.content, {type: "text", text}]}`. Not run in the spike;
  the README marks it untested.

### Capability: Package and documentation

#### Feature: Manifest and README

- **Description**: Root manifest, changelog, and honest per-host status.
- **Inputs**: None.
- **Outputs**: `plugins/engram/plugin.json`, `plugins/engram/README.md`,
  `plugins/engram/CHANGELOG.md`, `README.md`, `.claude-plugin/marketplace.json`.
- **Behavior**: `plugin.json`: name `engram`, version `0.1.0`, description
  "Recall prior decisions, sessions, and code across the portfolio through the
  engram CLI.", author `buvis`, license `MIT`, and an `extensions` object with
  keys `com.anthropic.claude-code`, `com.openai.codex`, `com.github.copilot`,
  `works.earendil.pi`, each `{"hooks": "<directory>/<file>"}`. The README
  states: the `engram` CLI must be on PATH; install steps per host; the guards
  `ENGRAM_NUDGE=off` (silence) and `ENGRAM_PACK_FILE=<path>` (drop hits a pack
  already holds); and a table with one row per host and a `Status` column
  reading `verified 2026-11-10` for Claude Code, Codex, and Copilot CLI,
  `untested` for Pi, and `skill and MCP only` for Kiro. Add the plugin row to
  the root `README.md` table and regenerate the marketplace file.

## Structural Decomposition

### Repository Structure

```
plugins/engram/
├── plugin.json                              # Manifest and README
├── .claude-plugin/plugin.json               # Claude Code adapter
├── README.md                                # Manifest and README
├── CHANGELOG.md                             # Manifest and README
├── mcp.json                                 # MCP configuration
├── skills/recall-prior-work/SKILL.md        # Recall skill
├── com.anthropic.claude-code/hooks.json     # Claude Code adapter
├── com.openai.codex/hooks.json              # Codex adapter
├── com.github.copilot/hooks.json            # Copilot CLI adapter
└── works.earendil.pi/engram-nudge.ts        # Pi adapter
tests/engram/test_package.py                 # Package assertions
README.md                                    # Plugin table row
.claude-plugin/marketplace.json              # Generated
.github/workflows/validate.yml               # Run tests/engram
```

### Module: plugin package

- **Maps to capability**: Portable pull path, Per-host push path, Package and
  documentation
- **Responsibility**: Configuration and one skill; no executable logic.
- **Location**: `plugins/engram/plugin.json`, `plugins/engram/.claude-plugin/plugin.json`,
  `plugins/engram/README.md`, `plugins/engram/CHANGELOG.md`, `plugins/engram/mcp.json`,
  `plugins/engram/skills/recall-prior-work/SKILL.md`,
  `plugins/engram/com.anthropic.claude-code/hooks.json`,
  `plugins/engram/com.openai.codex/hooks.json`,
  `plugins/engram/com.github.copilot/hooks.json`,
  `plugins/engram/works.earendil.pi/engram-nudge.ts`

New symbols: `recall-prior-work`, `engram-nudge.ts`, `works.earendil.pi`, `isBashToolResult`, `tool_result`, `postToolUse`, `ENGRAM_NUDGE`, `ENGRAM_PACK_FILE`

### Module: package tests

- **Maps to capability**: Package and documentation
- **Responsibility**: Assert the contract the hosts depend on.
- **Location**: `tests/engram/test_package.py`, `.github/workflows/validate.yml`,
  `README.md`, `.claude-plugin/marketplace.json`

New symbols: `test_every_hook_command_is_bare_engram_nudge`, `test_mcp_server_command_is_engram_mcp`, `test_claude_manifest_repeats_root_metadata`, `test_readme_states_status_for_each_host`, `test_no_shipped_file_names_a_plugin_root_placeholder`

## Dependency Graph

### Foundation Layer (Phase 0)

No dependencies - built first.

- **plugin package**: all shipped files.

### Core Layer (Phase 1)

- **package tests**: Depends on [plugin package]

### Integration Layer (Phase 2)

- **root README, marketplace, CI step**: Depend on [plugin package, package tests]

## Implementation Phases

### Phase 0: Foundation

**Goal**: A valid plugin directory.

**Tasks**:
- [ ] Create every file under `plugins/engram/` listed in the tree with the
  content the Features give (no deps) - Acceptance:
  `python3 scripts/validate.py plugins/engram` exits 0.

**Exit Criteria**: The validator accepts the package.

### Phase 1: Core

**Goal**: The host-facing contract is pinned by tests.

**Tasks**:
- [ ] Write `tests/engram/test_package.py` with the five tests named in the
  package tests module (depends on: Phase 0) - Acceptance:
  `python3 -m unittest discover -s tests/engram` passes; the placeholder test
  fails if any shipped file contains `PLUGIN_ROOT`.

**Exit Criteria**: All five tests pass.

### Phase 2: Integration

**Goal**: Listed, generated, and checked in CI.

**Tasks**:
- [ ] Add the plugin row to `README.md`, run
  `python3 scripts/generate_marketplace.py`, and add a
  `python3 -m unittest discover -s tests/engram` step to
  `.github/workflows/validate.yml` (depends on: Phase 1) - Acceptance:
  `python3 scripts/generate_marketplace.py --check` exits 0 and
  `rg -c "tests/engram" .github/workflows/validate.yml` prints at least 1.

**Exit Criteria**: `python3 scripts/validate.py`,
`python3 -m unittest discover -s scripts`, and
`python3 -m unittest discover -s tests/engram` all pass.

## Test Strategy

### Critical Scenarios

- **Happy path**: every hook file parses and its command starts with
  `engram nudge ` → Expected: test passes.
- **Edge case**: a hook command is changed to a plugin-relative path →
  Expected: `test_every_hook_command_is_bare_engram_nudge` fails.
- **Error case**: the README drops a host's status row → Expected:
  `test_readme_states_status_for_each_host` fails.

## Risks

- **The path-valued Claude `hooks` field is a guess**: if Claude Code ignores
  it, move the file to the plugin's `hooks/hooks.json` (the location every
  installed buvis plugin uses) and record the deviation from the
  extension-directory invariant in the README.
- **User-level install steps are manual on Codex, Copilot, and Pi**: the
  README states them; the status table says what was verified and how.
- **Double injection**: the orchestrator (intake 00066) sets
  `ENGRAM_PACK_FILE` or `ENGRAM_NUDGE=off` for workers it already served.
