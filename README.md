# buvis agent plugins

Portable agent plugins published by [buvis](https://github.com/buvis).

This monorepo targets the
[Agent Plugins specification](https://agent-plugins.org/) v1.0.0. Each
directory under [`plugins/`](plugins/) is an independent, self-contained
plugin package; the repository itself is not one large plugin.

## Status

The repository scaffold is ready. No plugins are published yet.

| Plugin | Purpose | Version |
| --- | --- | --- |
| _None yet_ | The first plugins will be added under `plugins/`. | — |

## Portable scope

Agent Plugins v1 standardizes two portable component types:

- Agent Skills at `skills/<skill-name>/SKILL.md`.
- MCP servers in an optional root `mcp.json`.

Custom agents, commands, hooks, rules, and LSP servers are not portable v1
components. Keep those in a client-documented reverse-domain extension such as
`com.github.copilot/`, or in that client's compatibility package. Never add
client-only fields directly to the closed portable `plugin.json` schema.

## Repository layout

```text
.
├── plugins/
│   └── <plugin-name>/
│       ├── plugin.json
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── skills/
│       │   └── <skill-name>/
│       │       ├── SKILL.md
│       │       ├── scripts/       # optional
│       │       ├── references/    # optional
│       │       └── assets/        # optional
│       ├── mcp.json               # optional
│       └── <reverse.domain.client>/ # optional client extension
├── templates/example-plugin/
├── scripts/
│   ├── validate.py
│   └── test_validate.py
├── tools/
│   └── <plugin-name>/             # maintainer tools, never shipped
├── tests/
│   └── <plugin-name>/             # maintainer tests, never shipped
├── .agents/skills/                # maintainer-only skills, never shipped
└── .github/
    ├── workflows/validate.yml
    └── dependabot.yml
```

Every plugin must be usable as though its directory were distributed alone.
Do not reference files above the plugin root or use symlinks that resolve
outside it.

`plugins/specflow/` is specflow's only distributable root. Its maintainer
tools, tests, skills, and scratch files stay outside it, in `tools/specflow/`,
`tests/specflow/`, `.agents/skills/`, and `docs/dev/tmp/specflow/`.

## Add a plugin

Start from the valid example package:

```bash
cp -R templates/example-plugin plugins/my-plugin
```

Then:

1. Rename the plugin and skill directories.
2. Update `plugin.json`, including `name`, `version`, and description.
3. Update each skill's `SKILL.md`; its `name` must match its directory.
4. Remove the example skill or replace it with real instructions.
5. Add `mcp.json` only when the plugin provides an MCP server.
6. Document setup, permissions, data access, and a safe first test in the
   plugin README.
7. Record user-visible changes in the plugin's `CHANGELOG.md`.
8. Validate the repository:

   ```bash
   python3 -m unittest discover -s scripts
   python3 scripts/validate.py
   ```

The repository validator enforces the pinned v1.0.0 manifest shape, names,
portable layout, basic Agent Skills metadata, MCP transport configuration, and
package path containment. The published
[Agent Plugins specification](https://agent-plugins.org/specification) and
[Agent Skills specification](https://agentskills.io/specification) remain
authoritative.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the publishing checklist.

## Distribution

Agent Plugins deliberately leaves installation and catalogs to clients. This
repository therefore has no invented "universal marketplace" manifest.
Client-specific catalogs will be added only after that client is tested; if
more than one catalog is needed, they should be generated from the portable
plugin manifests to prevent metadata drift.

The current list of implementations is maintained on the
[compatible clients](https://agent-plugins.org/compatible-clients) page.

## Security

Plugin instructions and MCP servers can cause tools or code to run with the
user's permissions. Review each plugin before installation. Never commit
credentials in `mcp.json`, environment values, headers, fixtures, or examples.
Use client-managed authentication and `${PLUGIN_DATA}` for writable runtime
state.

Report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). A plugin may carry a different license only when both its
manifest and bundled license file say so clearly.

## References

- [Agent Plugins v1.0.0 specification](https://agent-plugins.org/specification)
- [Canonical Agent Plugins example](https://github.com/agentplugins/agent-plugins-example)
- [Agent Skills specification](https://agentskills.io/specification)
- [Plugin and MCP JSON Schemas](https://agent-plugins.org/schemas)
