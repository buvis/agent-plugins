# engram

Recall prior decisions, sessions, and code across the portfolio through the
engram CLI.

## Requirements

The `engram` CLI must be on `PATH`.

## Install

### Claude Code

Install the plugin normally; `.claude-plugin/plugin.json` registers the
hooks and the MCP server.

### Codex

Merge `com.openai.codex/hooks.json` into `~/.codex/hooks.json`. A repository
`.codex/hooks.json` did not fire in the spike, so install at the home
location.

### Copilot CLI

Copy `com.github.copilot/hooks.json` to `~/.copilot/hooks/engram.json`.

### Pi

Install `works.earendil.pi/engram-nudge.ts` at
`~/.pi/agent/extensions/*.ts`, or register it through the `extensions` key
in `settings.json`.

## Environment guards

- `ENGRAM_NUDGE=off` — silence the nudge.
- `ENGRAM_PACK_FILE=<path>` — drop hits a pack already holds.

## Host status

| Host | Status |
|---|---|
| Claude Code | verified 2026-11-10 |
| Codex | verified 2026-11-10 |
| Copilot CLI | verified 2026-11-10 |
| Pi | untested |
| Kiro | skill and MCP only |
