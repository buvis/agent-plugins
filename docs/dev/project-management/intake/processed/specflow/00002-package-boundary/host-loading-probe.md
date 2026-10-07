# Host loading probe (T-006 of 00002)

Run on 2026-10-07, macOS, Python 3.14.6. Probe package: `docs/dev/tmp/specflow/probe/specflow-probe/`. Workspace: `docs/dev/tmp/specflow/probe/workspace/`. Both are ignored scratch; the probe files are reproduced below so the probe can be rebuilt.

Before the runs, `python3 scripts/validate.py docs/dev/tmp/specflow/probe/specflow-probe` printed `Validated 1 plugin package(s) and 1 skill(s).` and `claude plugin validate --strict` on the same folder printed `✔ Validation passed`.

## Codex

- Version: `codex-cli 0.160.1`, run headless with `codex exec --sandbox workspace-write -C <workspace>`, in a throwaway `CODEX_HOME` so the user's profile was untouched.
- Install surface: Codex has no install from a bare local folder. `codex plugin add` installs only from a marketplace, and `codex plugin marketplace add` accepts a local path. A local marketplace at `docs/dev/tmp/specflow/probe/.agents/plugins/marketplace.json` (below) pointed at `./specflow-probe`. Path that worked: `codex plugin marketplace add docs/dev/tmp/specflow/probe`, then `codex plugin add specflow-probe@specflow-probe-local`.
- Codex copies the plugin into its cache (`$CODEX_HOME/plugins/cache/specflow-probe-local/specflow-probe/0.0.1/`) and runs it from there.
- Required `plugin.json` at a repository root: no. It read the Agent Plugins v1 root `plugin.json` of the plugin folder; no `.codex-plugin/` was needed.
- Loaded the skill: yes, listed as `specflow-probe:probe-fixture`.
- Read the reference: yes.
- Ran the bundled script: yes. Output: `python 3.14.6 at <CODEX_HOME>/plugins/cache/specflow-probe-local/specflow-probe/0.0.1/skills/probe-fixture/scripts/probe.py`.
- Wrote the fixture: yes, it created `.kiro/specs/00000-probe/requirements.md` (it ran first).
- Resumed another host's fixture: not yet; Kiro IDE runs after it.
- Limit: a local install needs a marketplace file around the plugin. For specflow that is the monorepo's `.agents/plugins/marketplace.json` or `.claude-plugin/marketplace.json` (Codex reads both), so the 00008 Codex line "local folder" is wrong as written.

## Claude Code

- Version: `2.1.292 (Claude Code)`, run headless with `claude -p --plugin-dir docs/dev/tmp/specflow/probe/specflow-probe --add-dir <workspace>`.
- Install surface: local folder through `--plugin-dir`, which loads the plugin in place without copying it. The marketplace route is left to T-046 (00008).
- Required `plugin.json` at a repository root: no.
- Loaded the skill: yes, listed as `specflow-probe:probe-fixture`.
- Read the reference: yes.
- Ran the bundled script: yes. Output: `python 3.14.6 at /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/specflow/probe/specflow-probe/skills/probe-fixture/scripts/probe.py`.
- Wrote the fixture: yes, by appending its line.
- Resumed another host's fixture: yes, the one Codex wrote. Its line was kept and the Claude Code line added after it.
- Limit: none found.

## Kiro IDE

Open: this host runs by hand. It records the install surface used, whether it needed `plugin.json` at a repository root, the five checks, the name the skill appeared under, and any limit.

## Fixture after the runs

```text
- Codex: note="The probe reference was read."; script="python 3.14.6 at /private/tmp/claude-501/-Users-bob-git-src-github-com-buvis-agent-plugins/f1c3a2cf-12b9-4020-bd18-8ee28897670d/scratchpad/codex-home/plugins/cache/specflow-probe-local/specflow-probe/0.0.1/skills/probe-fixture/scripts/probe.py"
- Claude Code: note="The probe reference was read."; script="python 3.14.6 at /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/specflow/probe/specflow-probe/skills/probe-fixture/scripts/probe.py"
```

## Probe files

`specflow-probe/plugin.json`:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "specflow-probe",
  "version": "0.0.1",
  "description": "Throwaway probe that checks a host can load a specflow-shaped package.",
  "author": {
    "name": "buvis",
    "url": "https://github.com/buvis"
  },
  "license": "MIT",
  "keywords": [
    "probe"
  ]
}
```

`specflow-probe/.claude-plugin/plugin.json`: the same object without the `$schema` line.

`specflow-probe/skills/probe-fixture/SKILL.md`:

```markdown
---
name: probe-fixture
description: Probe skill for the specflow host loading check. Use when asked to run the specflow probe or probe-fixture.
---

Run these steps in order, in the current workspace.

1. Read `references/note.md` in this skill's folder.
2. Run `python3 scripts/probe.py`, resolving `scripts/probe.py` relative to this skill's folder. Keep its one line of output.
3. If `.kiro/specs/00000-probe/requirements.md` does not exist in the workspace, create it with one line. If it exists, keep its content and append one line. The line is:
   `- <host name>: note="<the note's sentence>"; script="<the script output>"`
   Name the host you run in (Kiro IDE, Codex, or Claude Code).
4. Report the full content of `.kiro/specs/00000-probe/requirements.md`.

If a step fails, stop and report which step failed and why.
```

`specflow-probe/skills/probe-fixture/references/note.md`:

```text
The probe reference was read.
```

`specflow-probe/skills/probe-fixture/scripts/probe.py`:

```python
"""Print the Python version and this script's resolved path (specflow host probe)."""

import platform
from pathlib import Path

print(f"python {platform.python_version()} at {Path(__file__).resolve()}")
```

Codex scaffolding, `.agents/plugins/marketplace.json` beside `specflow-probe/`:

```json
{
  "name": "specflow-probe-local",
  "plugins": [
    {
      "name": "specflow-probe",
      "source": {
        "source": "local",
        "path": "./specflow-probe"
      }
    }
  ]
}
```
