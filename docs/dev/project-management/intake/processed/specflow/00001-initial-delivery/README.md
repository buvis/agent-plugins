# Portable Spec Workflow Plugin

Status: Draft specification  
Date: 2026-10-03

This specification defines a portable Agent Plugins v1 package that gives Kiro IDE, Codex, and Claude Code a shared requirements → design → tasks → implementation workflow.

The package also ships a conversion skill that turns an existing PRD or legacy intake item into specflow requirements, design, and tasks without losing its decisions, implementation evidence, or approval boundaries. This is a distributed runtime capability, not a maintainer-only tool: a developer bringing specflow into a repository that already has PRDs needs it on the first day.

The canonical project artifacts remain compatible with Kiro:

```text
.kiro/specs/NNNNN-<title>/
├── requirements.md      # or bugfix.md for a bugfix spec
├── design.md
├── tasks.md
├── .config.kiro
└── .specflow.json
```

Raw inputs, Q&A logs, and review reports live under a configurable workspace root (default `.kiro/specflow/`; buvis repos use `docs/dev/project-management/`). The specs folder is `.kiro/specs/` unless `.agents/specflow.json` names another; specflow reads it directly and owns no link.

The repository-only catch-up skill, which reviews the AWS sources, is deliberately outside the distributable `plugins/specflow/` subtree. It must never be included in an installed or released plugin.

Documents:

- [requirements.md](requirements.md): product and behavioral requirements
- [design.md](design.md): architecture, state model, catch-up model, security, and host integration
- [tasks.md](tasks.md): dependency-ordered implementation plan
- [qa-log.md](qa-log.md): questions and answers from the 0.2 rewrite, Plan B integration, and the 2026-10-03 review
- [graduate/](graduate/): the proven PRD-to-specflow conversion reference skill (`SKILL.md`, `references/conversion.md`), adapted by hand into the shipped conversion skill

Working assumptions:

- The plugin is named `specflow` and lives at `plugins/specflow/` in the buvis agent-plugins monorepo.
- Agent Plugins v1 is the portable package baseline.
- The first release is skills-based and does not require an MCP server.
- Release 0.1 supports Kiro IDE, Codex, and Claude Code and ships the full accepted feature set, including cross-spec review and advisory scripts, with host evals and parity evidence. External migration and source-skill retirement remain owned by their repositories.
- AWS AI-DLC material is adapted by hand, with a source line per passage. `awslabs/aidlc-workflows` is the primary source; `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (the original) and `aws-samples/sample-aidlc-discovery` are complementary sources. All three get a regular catch-up, and none is vendored.
- Maintainer skills live at repo-root `.agents/skills/<verb>-<plugin>-<object>/`, the only committed copy; no agent-private folder is committed.
- Approved Plan B design/tasks behavior is folded into this spec. T-079 builds its rule mappings and runtime references; autopilot keeps both source phase skills.
- The conversion skill ships inside `plugins/specflow/` (it is runtime, not maintainer-only). A proven reference skill exists at [`graduate/`](graduate/) beside this specification — a `SKILL.md` plus [`references/conversion.md`](graduate/references/conversion.md) written by another agent that performed a real PRD-to-specflow conversion. It is adapted by hand into the shipped skill, not reused byte for byte: it predates this spec's naming, rule inventory (requirements RULE-001), and reference-routing conventions, so its text is a validated source, not a drop-in file.
- That reference skill's conversion was exercised against a real PRD and succeeded: the agent converted a calcard-mcp bugfix PRD into an approved specflow artifact set at `buvis/calcard-mcp` `docs/dev/project-management/specs/00032-add-if-match-preconditions-to-event-writes/` (`bugfix.md`, `design.md`, `tasks.md`, `.config.kiro`, `.specflow.json`). That spec is the acceptance fixture the shipped conversion skill is verified against.
