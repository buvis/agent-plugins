# Contributing

This repository publishes self-contained Agent Plugins from buvis. Each plugin
is versioned independently and must keep its portable core usable without the
rest of the monorepo.

## Add or update a plugin

1. Copy `templates/example-plugin` into `plugins/<plugin-name>` or edit an
   existing plugin in place.
2. Keep the directory name and `plugin.json` `name` identical.
3. Include `version`, `description`, `author.name`, and `license`; use SemVer
   for the version and bump only the plugins that changed.
4. Put portable skills in immediate child directories of `skills/`.
5. Put portable MCP configuration only in root `mcp.json`.
6. Put client-specific behavior in a namespace or compatibility format that
   the target client documents. Do not invent extension semantics.
7. Keep every packaged path inside the plugin root. Do not depend on a sibling
   plugin or a repository-level virtual environment, `node_modules`, or cache.
8. Add every user-visible change to the plugin's `CHANGELOG.md` under
   `[Unreleased]` in the same commit.
9. Update the plugin table in the root README.
10. Run `python3 -m unittest discover -s scripts` and
    `python3 scripts/validate.py`.

## Maintainer skills

A skill for maintaining a plugin, never for its users, lives at
`.agents/skills/<verb>-<plugin>-<object>/SKILL.md`, for example
`.agents/skills/catchup-specflow-upstream/`. That folder holds its only
committed copy; its support files live under `tools/<plugin>/`. Do not commit
an agent-private folder (`.claude/`, `.kiro/`, `.codex/`) or a symlink to one:
a local copy of a skill for your own tool stays uncommitted. A maintainer skill
is never copied into or named inside a plugin package.

## Plugin documentation

Each plugin README should state:

- what the plugin does and which clients have actually been tested;
- its skills, MCP servers, and client extensions;
- prerequisites, installation, and authentication requirements;
- commands, endpoints, files, or user data it can access;
- a credential-free or read-only first test;
- expected failure behavior and uninstall steps.

## Security and generated files

Never commit secrets. MCP environment values and headers are package data, not
a credential store. Prefer generated client catalogs over hand-maintained
duplicates, but commit generated files when clients install them directly from
the repository. Lockfiles and distributable plugin assets are intentional
source artifacts and should normally remain tracked.
