# buvis agent plugins

Monorepo for self-contained, portable Agent Plugins published by buvis. The
repository targets Agent Plugins v1.0.0; the repository root is not itself a
plugin package.

## Stack

- Package format: Agent Plugins v1.0.0 and Agent Skills.
- Tooling: dependency-free Python validator.
- Automation: GitHub Actions.
- License: MIT unless an individual plugin explicitly says otherwise.

## Structure

- `plugins/` — published packages; each immediate child is one plugin root.
- `templates/example-plugin/` — valid copyable starter, not a published plugin.
- `scripts/validate.py` — repository and portable-format validation.
- `.github/workflows/validate.yml` — CI entry point.

## Invariants

- Keep every `plugins/<name>` package independently distributable.
- Keep the directory name and root `plugin.json` `name` identical.
- Keep runtime files and resolved symlinks inside their plugin root.
- Put portable skills only at `skills/<name>/SKILL.md` and portable MCP
  configuration only at root `mcp.json`.
- Keep custom agents, commands, hooks, rules, and other client behavior in a
  client-documented extension or compatibility package.
- Treat portable plugin manifests as source-of-truth metadata. Do not invent a
  universal marketplace format or hand-maintain drifting client catalogs.
- Never commit credentials in manifests, MCP configuration, fixtures, or
  examples.
- Keep lockfiles and distributable plugin assets tracked unless their plugin
  documents that they are reproducible output.

## Commands

- Test validator: `python3 -m unittest discover -s scripts`
- Validate repository: `python3 scripts/validate.py`

## Verification

Run the validator before completing changes. When publishing or removing a
plugin, also update the plugin table in `README.md`.

## Documentation

- `README.md` — architecture, portable scope, and repository workflow.
- `CONTRIBUTING.md` — publishing and documentation checklist.
- `SECURITY.md` — trust boundaries and vulnerability reporting.
