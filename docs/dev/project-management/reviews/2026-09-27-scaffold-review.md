# Scaffold review - 2026-09-27

Scope: repo scaffold, README, `.gitignore`, validator, CI. Checked against the
Agent Plugins 1.0.0 schemas (plugin + mcp, fetched 2026-09-27) and against
peer repos: github/awesome-copilot, anthropics/claude-plugins-official,
openai/plugins, openai/skills, anthropics/skills, vercel-labs/agent-skills.

## Verdict

The design is sound. The validator's manifest and MCP rules match the official
1.0.0 schemas field for field. The README explains portable scope clearly, and
no peer does it better. awesome-copilot is the closest match in layout
(`plugins/<name>/plugin.json` using the 1.0.0 `$schema`).

## Applied

| # | Finding | Fix |
|---|---------|-----|
| 1 | `.gitignore` silently dropped skills named `coverage`, `tmp`, `target` (proved with `git check-ignore`) | `!**/skills/*/` negation, re-verified |
| 2 | Branch `main` and CI trigger `main`; the standing rule is `master` | branch renamed (no commits yet), CI trigger updated |
| 3 | CI used `checkout@v4` / `setup-python@v5`; the current majors are v7 | SHA-pinned v7.0.1 / v7.0.0, `persist-credentials: false`, Dependabot keeps the pins fresh |
| 4 | Validator (480 lines of security-relevant rules) had no tests | `scripts/test_validate.py`, 9 stdlib unittest cases, run in CI |
| 5 | No changelog convention; plugins version independently | per-plugin `CHANGELOG.md` in the template, README, and CONTRIBUTING |

## Open

| # | Sev | Finding |
|---|-----|---------|
| 6 | HIGH | `plugins/specflow/` failed validation (no `plugin.json`), and its spec assumed a single-plugin repo. **Decided: split by role.** Specs moved to `docs/dev/project-management/specs/specflow/` on branch `feature/specflow`. Spec paths rewritten: `plugins/specflow/` ships; `tools/specflow/`, `tests/specflow/`, `.agents/skills/`, and `docs/dev/tmp/specflow/` do not. Applied. |
| 7 | LOW | The validator hand-mirrors the schemas. It will drift when 1.1.0 (now a working draft) lands. Fix then: vendor the schema files and diff against them. |
| 8 | LOW | No ban on credential-like MCP header names (awesome-copilot bans `authorization` and `x-api-key`). Add it with the first remote MCP plugin. |
| 9 | LOW | No client catalog yet. The README already defers this until a client is tested. When it is time, awesome-copilot generates `.github/plugin/marketplace.json` from the manifests. |

Skipped on purpose: CODEOWNERS and issue/PR templates (solo repo), and
`skills-ref validate` (its README calls it demo-only).
