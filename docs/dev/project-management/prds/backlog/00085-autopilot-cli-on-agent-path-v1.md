---
catchup: run
design: skip
default_model: sonnet
model_tier_rationale: one wrapper script, one test, and a prose check; no design unknowns
---

# Put the `autopilot` CLI on the agent's PATH

## Overview

### Problem Statement

The autopilot skills tell the agent to run bare `autopilot <verb>` (for
example `autopilot review-stage` in `review-work-completion/SKILL.md` step 3,
and many more in `run-autopilot` and `work`). In the installed plugin
(`buvis/claude-autopilot` 0.10.0, frozen) `autopilot` exists only as a bash
function in the user's interactive shell profile. The Bash tool runs
non-interactive shells, so the call fails with exit 127
(`autopilot: command not found`). Seen 2026-11-16 in a standalone
`/autopilot:review-work-completion` run: the agent had to find
`skills/run-autopilot/cli/__main__.py` and run it with `python3` by hand.

A user without that profile function has no `autopilot` command at all.

Claude Code puts a plugin's `bin/` directory on the Bash tool's PATH while the
plugin is enabled (https://code.claude.com/docs/en/plugins/components.md,
section "Executables").

### Target Users

Agents that run the autopilot skills, and any user who installs the plugin.

### Success Metrics

- `autopilot --help` works from the Bash tool in a fresh session with no shell
  profile.
- Every bare `autopilot <verb>` in the skills resolves to the plugin's own CLI.

## Functional Decomposition

### Capability: CLI on PATH

#### Feature: `bin/autopilot` wrapper

- **Description**: An executable `plugins/autopilot/bin/autopilot` that runs
  the plugin's CLI entry point with every argument passed through.
- **Inputs**: argv.
- **Outputs**: the CLI's stdout, stderr and exit code, unchanged.
- **Behavior**: Resolve the entry point relative to the script's own real
  path, never through `~/.claude/plugins/cache` and never through
  `${CLAUDE_PLUGIN_ROOT}` (unset outside hooks). Exec `python3` on it. Fail
  loud with a clear message when the entry point is missing.

## Implementation Phases

### Phase 0

**Tasks**:

- [ ] Add `plugins/autopilot/bin/autopilot` (executable bit set in git) - Acceptance: a test runs the script with `--help` through a symlink and from another cwd and gets exit 0; a test with the entry point removed gets a non-zero exit and a message that names the missing path.
- [ ] Check that each bare `autopilot <verb>` in `plugins/autopilot/skills/**` names a verb the CLI accepts - Acceptance: a test parses the skill prose and fails on an unknown verb.
- [ ] Add a CHANGELOG entry under Fixed.

**Exit Criteria**: `uv run pytest` passes; a fresh Claude Code session with the
plugin enabled runs `autopilot --help` from the Bash tool.

## Dependencies

- The successor CLI must be runnable: PRD 00015 / 00016 (stateful verbs refuse
  until controller integration). The wrapper can land first; it then prints
  that refusal, not exit 127.

## Risks

- Subagent shells: the docs confirm `bin/` on PATH for the main session's Bash
  tool only. Verify in a subagent before relying on it there.
- The user's profile function `autopilot` shadows the wrapper in interactive
  shells. It points at the same CLI today; retire it once the wrapper ships.

## Unresolved questions

- None.
