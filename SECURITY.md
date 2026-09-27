# Security policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or exposed secret.
Use a private
[GitHub security advisory](https://github.com/buvis/agent-plugins/security/advisories/new)
and include the affected plugin, impact, reproduction steps, and any suggested
mitigation.

If a secret may have been exposed, revoke or rotate it before reporting the
repository issue.

## Scope

Reports are especially useful for:

- instructions that can trigger unintended destructive or privileged actions;
- bundled scripts or MCP servers with command, path, or injection flaws;
- credentials or private data included in package files;
- package paths or symlinks that escape the plugin root;
- misleading permission, authentication, or data-access documentation.
