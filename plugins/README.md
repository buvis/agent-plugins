# Published plugins

Each immediate child directory is one independently installable Agent Plugin.
It must contain a root `plugin.json` and may contain portable `skills/`, a root
`mcp.json`, and documented client extension directories.

Plugin packages must be self-contained. Shared development tooling belongs at
the repository root, but runtime files required by a plugin must be bundled
inside that plugin.
