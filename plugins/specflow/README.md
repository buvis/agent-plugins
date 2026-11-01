# specflow

A portable requirements, design, tasks, and implementation workflow that
writes Kiro-compatible spec artifacts.

## Status

Unreleased. The `spec-workflow` skill holds the workflow's entry point, gates,
shared contracts, phase references, and review references; the `convert-prd`
skill adopts an existing PRD or legacy intake item into them.

## Package

This folder is the whole distributable package. Maintainer tools, tests, and
skills live outside it and never ship.

## Hosts

Kiro IDE, Codex, and Claude Code are the supported hosts of this release.
Each has loaded this package, run the workflow, and taken over a spec another
host wrote; the repository keeps one record per host. Kiro CLI and Kiro Crew
are expected to load the same package but are untested, so they are not
listed as supported.

Two rules hold on every host:

- Recording an approval needs Python 3: the helper
  `skills/spec-workflow/scripts/validate_spec.py` writes `.specflow.json`.
  Without Python 3 the skill is read-only and says so.
- Sessions do not transfer between hosts. Only the repository's files do:
  the next host reads the spec folder and `.specflow.json`, reconciles the
  hashes, and continues at the phase they show.

The marketplace that lists this plugin is `buvis-agent-plugins`, the
repository's generated `.claude-plugin/marketplace.json`; Codex and Claude
Code both read it.

### Kiro IDE

- Install: open the Powers panel, choose **Add Custom Power**, then
  **Import power from GitHub**, and enter
  `https://github.com/buvis/agent-plugins/tree/master/plugins/specflow`.
  From a local clone, choose **Import power from a folder** instead and
  select this package folder. Either way Kiro copies the package to
  `~/.kiro/powers/installed/specflow/` and asks for approval before it
  activates the Power.
- Invoke: ask in your own words ("Create a spec for X", "Continue spec X",
  "What's the status of X?"). The skill appears as `spec-workflow`, with no
  plugin prefix, and Kiro does not tell the agent the Power's folder, so the
  first run may search for it.
- Known differences: the agent runs the helper in Kiro's terminal, so check
  that a trivial command such as `echo ok` returns there before the first
  approval; a prompt framework that redraws the prompt (Bash-it, for one)
  can keep Kiro from reading command results. Kiro's Specs panel reads
  `.kiro/specs/`; with a specs folder configured in `.agents/specflow.json`
  it lists, opens, and watches those specs only through a `.kiro/specs` link
  that the repository sets up, and it ignores `.kiro/specflow/`.
- Handoff example: create a spec in Kiro and approve its requirements, then
  close the chat. In Codex, say "Continue spec 00001-hello-world": Codex
  reads the same files, reports no reconciliation change, and drafts the
  design.

### Codex

- Install: Codex installs plugins from a marketplace, never from a bare
  folder. Add the repository, then the plugin:

  ```text
  codex plugin marketplace add buvis/agent-plugins
  codex plugin add specflow@buvis-agent-plugins
  ```

  The first command also takes a local checkout path, or a Git ref
  (`--ref <branch-or-tag>`). Codex copies the plugin into
  `$CODEX_HOME/plugins/cache/buvis-agent-plugins/specflow/<version>/` and
  runs it from there.
- Invoke: the skill appears as `specflow:spec-workflow`; ask in your own
  words.
- Known differences: `codex exec` runs one headless turn, so an approval is a
  run of its own whose prompt states the artifact and its exact canonical
  hash; the skill records nothing without that explicit yes.
- Handoff example: after Codex approves the design and the task plan, open
  Claude Code in the same repository and say "Continue spec
  00001-hello-world": it resumes at the implementation phase with every
  approval intact.

### Claude Code

- Install: inside Claude Code, one step:

  ```text
  /plugin install specflow --marketplace buvis/agent-plugins
  ```

  or from a shell, `claude plugin marketplace add buvis/agent-plugins` and
  then `claude plugin install specflow@buvis-agent-plugins`. From a local
  checkout, give `claude plugin marketplace add` the checkout path instead;
  for development without installing, start
  `claude --plugin-dir <checkout>/plugins/specflow`, which loads the folder
  in place.
- Invoke: the skill appears as `specflow:spec-workflow`, also as the slash
  command `/specflow:spec-workflow`.
- Known differences: Claude Code reads `.claude-plugin/plugin.json`, which
  repeats the root manifest's metadata. In print mode (`claude -p`) no one
  answers a permission prompt, so allow the edit tools and
  `Bash(python3 *)` up front, or the helper cannot run.
- Handoff example: in Claude Code, edit an approved `requirements.md`; the
  skill reconciles and reports requirements, design, and tasks as stale. In
  Codex, say "What's the status of 00001-hello-world?": it reports the same
  stale artifacts and the closed gates, and nothing but the files carried
  that state across.

## Provenance

specflow's method is adapted by hand from three public AWS AI-DLC
repositories, all MIT-0:

- AWS AI-DLC workflows, `awslabs/aidlc-workflows` (the primary method source)
- AI-powered SDLC patterns with AWS,
  `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (the original source)
- AI-DLC discovery, `aws-samples/sample-aidlc-discovery`

`skills/spec-workflow/references/aws/adaptation.md` records the commit each
is adopted from, and `references/aws/LICENSE` carries the license of every
source that text is copied from.

## Security

The package ships one optional helper,
`skills/spec-workflow/scripts/validate_spec.py`, a Python 3 standard-library
script. It reads the repository's spec artifacts and runs read-only local
`git` commands (`rev-parse`, `check-ignore`). Its only write is
`.specflow.json` inside a spec folder, through `reconcile`. It refuses paths
outside the repository. The package has no network access, MCP servers, or
authentication.
