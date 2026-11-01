# Claude Code compatibility (T-043)

Status: passed. The real CLI loads `plugins/specflow` by its absolute path
through `--plugin-dir`, exposes the skill as `specflow:spec-workflow`, resumes
the spec Codex left, edits its requirements, and reconciles the three approvals
to stale with every gate closed. Codex then resumes the same files and reports
the same stale design and tasks, which closes the hand-back. Both runs were
launched on 2026-11-01 from inside a Claude Code agent session, after the
developer's deferral of 2026-10-30. The launcher limitation that forced the
deferral is kept below.

## Environment and installation

- Run: 2026-11-01, Europe/Prague. Claude Code 10:20 to 10:24 CET; Codex
  hand-back 10:37 to 10:38 CET.
- CLI: `2.1.312 (Claude Code)`, model `claude-fable-5-1`, session
  `4a653a43-2d79-4660-9377-a27beb7c4ee5`, 50 turns, 252 seconds, exit 0.
- Plugin source: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/plugins/specflow`.
- Loading route: `claude --plugin-dir <plugin source> --print <prompt>
  --output-format stream-json --verbose --permission-mode acceptEdits
  --allowedTools "Read,Glob,Grep,Skill,Edit,Write,Bash(python3 -B *),Bash(git rev-parse *)"`,
  run by the prepared `docs/dev/tmp/specflow/hosts/capture-claude.py` with the
  workspace as its current directory.
- Compatibility manifest: `<plugin source>/.claude-plugin/plugin.json`.
- Workspace: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/docs/dev/tmp/specflow/hosts/workspace`,
  the repository Kiro and Codex used, as T-042 left it: all three artifacts
  approved, implementation gate open, T-001 unchecked, both implementation
  files absent. Its full starting snapshot is in `codex.md`; no reconstruction
  was needed.
- Existing Claude profile: `claude plugin list` before the run showed no
  installed plugin containing `specflow`. The session's init event lists the
  plugin as `specflow@inline`, version `0.1.0`, with the plugin source as its
  path, beside the profile's installed plugins. Its skill list holds
  `specflow:spec-workflow` and `specflow:convert-prd`, and
  `specflow:spec-workflow` appears among the slash commands.
- Skill name exposed by the host: `specflow:spec-workflow`. The Skill tool
  call was `specflow:spec-workflow` with the argument `resume 00001-hello-world`;
  the tool result reads `Launching skill: specflow:spec-workflow`.

## Launcher limitation and the in-session launch

The user's `run-agent` launcher supplies the long-lived Claude setup token
and applies the macOS Seatbelt profile. On 2026-10-29 and 2026-10-30, a
token-availability preflight through that launcher, started from inside a
Codex agent session, failed before starting Claude:

```text
sandbox-exec: sandbox_apply: Operation not permitted
```

The same preflight with tool-level escalation also exited 71. An agent session
cannot create the launcher's nested sandbox, so the prepared
`claude-start.bash` was left for the developer's regular Terminal and the
developer deferred the test to 2026-11-01.

On 2026-11-01 the test ran from inside a Claude Code agent session instead.
`docs/dev/tmp/specflow/hosts/claude-start-insession.bash` reads the same
setup-token file the launcher reads, exports it without printing it, and runs
the unchanged `capture-claude.py` without a nested Seatbelt; the session's own
Seatbelt still confined the child process. The Keychain login was not used, and
no login or security configuration changed.

The prompt is `docs/dev/tmp/specflow/hosts/claude-stale.txt`. It pins the
three starting hashes, invokes the loaded `specflow:spec-workflow` skill, reads
its contracts, and resumes from files. It then changes the three
`Hello, world!` occurrences in the throwaway requirements to
`Hello from Claude Code!`, reconciles, and stops with the approvals stale. It
authorizes no design or task edit, reapproval, implementation, or commit. The
captured event stream is `claude-stale-events.jsonl` and the final response is
`claude-stale-output.txt`, both under the ignored host scratch directory.

## Claude Code run

| Required step | Result |
|---|---|
| Load the compatibility manifest with `--plugin-dir` and the absolute path | Pass: init event plugin `specflow@inline` 0.1.0 at the plugin source; the model reported the compatibility manifest at `<plugin source>/.claude-plugin/plugin.json` |
| The skill appears as `specflow:spec-workflow` | Pass: Skill tool invocation and `Launching skill: specflow:spec-workflow`; it then read `artifact-contract.md`, `state-contract.md`, `profiles/standard.md`, and `phases/requirements.md` from the plugin source |
| Resume the spec Codex left | Pass: status phase `implementation`, all three approved, no stale files; `reconcile --dry-run` with no changes; `hash --json` matched the three pinned values |
| Edit the requirements | Pass: three lines of `requirements.md` changed; reason logged as Q2 in the intake `qa-log.md`; raw pre-write hashes checked |
| See design and tasks go stale | Pass: `reconcile` moved requirements, design, and tasks to `stale`; phase `requirements`; every gate closed; `validate --phase requirements` exits 1 with three `stale-approvals` errors |
| Codex resumes the spec and reports the same stale design and tasks | Pass: see the hand-back section below |

Initial state, from the child session's own helper runs and confirmed by the
orchestrating session before the launch: phase `implementation`, state
`valid`, requirements, design, and tasks `approved`, `stale: []`, every gate
`open`, no hold, blockers, or warnings, next task T-001. `reconcile --dry-run`
returned `changes: []` and `ambiguous: []`. Canonical hashes from
`hash --json`:

| Artifact | Canonical SHA-256 before the edit |
|---|---|
| `requirements.md` | `1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0` |
| `design.md` | `f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f` |
| `tasks.md` | `bddc3cd7eab681f89e6cf2a8aedffe07ded0f9d17034a89a5635a398cd70e4ab` |

The child took `hash --raw` of `requirements.md`, `.specflow.json`, and the
intake `qa-log.md` before writing and checked them again right before each
write; none had moved. It then changed exactly three lines of
`requirements.md` with one `Edit` call (`Hello, world!` to
`Hello from Claude Code!`, replace all): REQ-001 criterion 1 (line 28),
REQ-003 criterion 1 (line 49), and the first out-of-scope bullet (line 62).
The single LF, exit 0, and standard-library test requirements are untouched.
A second `Edit` appended entry Q2 to the intake `qa-log.md` with the
developer's words on the `Answer:` line and the expected staling on the
`Reading:` line.

`reconcile --dry-run --json` then proposed, and `reconcile --json` wrote, the
derived changes: the requirements `sha256` moved from `1eceb5ba...` to
`efe6f1a66bf6f7cb3c7596a922103fa95beca3e4d79ff8b5ef94a482227c6a98` and its
status from `approved` to `stale`; design and tasks keep their hashes but each
records the old requirements hash as upstream, so both went from `approved` to
`stale`; the phase derived to `requirements`; nothing was ambiguous. Approval
fields, approved hashes, upstream hashes, and the design's code baseline are
unchanged, which is all `reconcile` may leave alone.

`validate .kiro/specs/00001-hello-world --phase requirements --json` exits 1
with exactly three findings, all `stale-approvals` errors:

```text
requirements.md: the requirements.md approval is stale: it is recorded stale
design.md: the design.md approval is stale: upstream requirements.md changed since its approval
tasks.md: the tasks.md approval is stale: upstream requirements.md changed since its approval
```

Each carries the fix "Review <artifact> with the developer and record its
approval again." The edited requirements draw no structural finding. Before
`reconcile` wrote, the same validation named the requirements cause as "its
content changed since the approval".

The final response ends with `specflow-claude-stale-ready`. The orchestrating
session confirmed the end state independently: `status --json` and
`reconcile --dry-run --json` as shown under Final status below, the three
changed lines in `requirements.md`, the `.specflow.json` below, and the
workspace repository still at its single commit with all spec files untracked.
The parent checkout was not modified by the child; its working tree held only
the uncommitted deferral edits of 2026-10-30 and this record.

One observation from the child session, for the maintainers: `hash --json`
prints `approvedAt` as the current time on every call. That is the helper
offering the values a would-be approval would record, as the state contract
says; no approval was recorded here.

## Codex hand-back

- CLI: `codex-cli 0.166.0` (`0.165.0` at T-042), the profile's default model,
  shown as `gpt-6.1-sol` by a probe run in the same profile.
- Isolated profile: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/docs/dev/tmp/specflow/hosts/codex-home`,
  with the plugin still installed from T-042 as `specflow@specflow-host-test`
  0.1.0 at
  `<profile>/plugins/cache/specflow-host-test/specflow/0.1.0`. No plugin file
  changed between that install (2026-10-29) and this run; the last commit that
  touched `plugins/specflow/` is `76a3ee6` of 2026-10-25.
- Launch: `docs/dev/tmp/specflow/hosts/codex-handback.bash`, the `use-codex`
  wrapper with the prompt `codex-handback.txt`, the output
  `codex-handback-output.txt`, and the thread id
  `01a19678-e62b-7270-8ba1-6e8c4847039e` in `codex-handback-thread.txt`.
- Sandbox: Codex's own sandbox cannot apply inside the agent session's
  Seatbelt. A probe run in the same profile under `--sandbox read-only` asked
  Codex to run `echo codex-sandbox-ok`; the command failed with exit 71 and
  `sandbox-exec: sandbox_apply: Operation not permitted`. The hand-back
  therefore ran with the wrapper's `-y` flag, which bypasses Codex's sandbox
  and approvals; the session's Seatbelt still confined the run, and the prompt
  forbids every write, git mutation, approval, and `reconcile` without
  `--dry-run`. The raw SHA-256 of all seven workspace files was taken before
  and after the run and is identical:

```text
efe6f1a66bf6f7cb3c7596a922103fa95beca3e4d79ff8b5ef94a482227c6a98  .kiro/specs/00001-hello-world/requirements.md
f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f  .kiro/specs/00001-hello-world/design.md
bddc3cd7eab681f89e6cf2a8aedffe07ded0f9d17034a89a5635a398cd70e4ab  .kiro/specs/00001-hello-world/tasks.md
0b3e7429f5a3bab336ca4e7d002510144cea8d79008d8496516c00d9d3cd314e  .kiro/specs/00001-hello-world/.specflow.json
422ee58eac8b9cf8d6b76ad4d95dee82dc71918dd4785477ec4f2c0d24324bae  .kiro/specs/00001-hello-world/.config.kiro
3e8b0ae5bc5bcab357c030bac359f3460b56e4feaa158266190f30c9fbe9c56b  .kiro/specflow/intake/processed/00001-hello-world/idea.md
93ad03afcb67e9651ea91bc5311a58644e84604015d2f27406d8a6c28092afd7  .kiro/specflow/intake/processed/00001-hello-world/qa-log.md
```

Codex read the artifact contract, the state contract, the standard profile,
all canonical artifacts, the state, and the intake records, and ran
`status --json`, `reconcile --dry-run --json`, and `hash --json` for the three
artifacts with `python3 -B` from the workspace. Its report: host skill
`specflow:spec-workflow`; installed plugin path as above; "root manifest"
`<installed path>/.claude-plugin/plugin.json` (the T-042 run reported
`<installed path>/plugin.json`; Codex installs from the Agent Plugins v1 root
manifest, as the probe of 00002 showed, and the two self-reports name the two
manifests the cached copy holds). It confirmed requirements.md at
`efe6f1a6...` against the recorded `approvedSha256` `1eceb5ba...`, design.md
and tasks.md unchanged at `f2f0541e...` and `bddc3cd7...` yet stale because
their recorded upstream requirements hash no longer matches, statuses
requirements, design, and tasks `stale`, phase `requirements`, every gate
closed, no hold, `nextTask` null, task progress 0/1, `reconcile --dry-run`
with `changes: []` and `ambiguous: []`, `.agents/specflow.json` absent, and
"Files changed: none". Its status JSON, reconcile JSON, and `.specflow.json`
match the ones below byte for byte. It ended with
`specflow-codex-handback-complete`.

## Final status

```json
{
  "statusVersion": 1,
  "specs": [
    {
      "spec": "00001-hello-world",
      "specType": "feature",
      "profile": "standard",
      "phase": "requirements",
      "state": "valid",
      "hold": null,
      "artifacts": {
        "requirements": "stale",
        "design": "stale",
        "tasks": "stale"
      },
      "stale": [
        "requirements",
        "design",
        "tasks"
      ],
      "gates": {
        "design": "closed",
        "tasks": "closed",
        "implementation": "closed"
      },
      "blockers": [
        {
          "gate": "design",
          "reason": "requirements is stale",
          "reference": "requirements.md"
        },
        {
          "gate": "tasks",
          "reason": "requirements is stale",
          "reference": "requirements.md"
        },
        {
          "gate": "tasks",
          "reason": "design is stale",
          "reference": "design.md"
        },
        {
          "gate": "implementation",
          "reason": "requirements is stale",
          "reference": "requirements.md"
        },
        {
          "gate": "implementation",
          "reason": "design is stale",
          "reference": "design.md"
        },
        {
          "gate": "implementation",
          "reason": "tasks is stale",
          "reference": "tasks.md"
        }
      ],
      "warnings": [
        {
          "kind": "not-checked",
          "message": "the design approval is stale; code is checked again after reapproval"
        }
      ],
      "nextTask": null
    }
  ],
  "problems": [],
  "intake": []
}
```

## Final reconciliation (dry run)

```json
{
  "spec": "00001-hello-world",
  "statuses": {
    "requirements": "stale",
    "design": "stale",
    "tasks": "stale"
  },
  "phase": "requirements",
  "changes": [],
  "ambiguous": []
}
```

## Artifact snapshot

The files as Claude Code left them and Codex read them. `design.md`,
`tasks.md`, `.config.kiro`, and `idea.md` are byte-identical to the snapshot
in `codex.md` (raw SHA-256 above), so they are not repeated. The Q&A log
gains entry Q2 at its end; the rest of it is the `codex.md` snapshot.

### `.kiro/specs/00001-hello-world/.specflow.json`

~~~~json
{
  "schemaVersion": 1,
  "specId": "00001-hello-world",
  "specType": "feature",
  "profile": "standard",
  "workflowOrder": "requirements-first",
  "workflowVersion": "0.1.0",
  "artifacts": {
    "requirements": {
      "path": "requirements.md",
      "status": "stale",
      "sha256": "efe6f1a66bf6f7cb3c7596a922103fa95beca3e4d79ff8b5ef94a482227c6a98",
      "approvedSha256": "1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0",
      "approvedAt": "2026-10-27T21:47:41Z",
      "approvedCommit": "5a88b2f07c7ac123932c91a43533f4e67b0820b4"
    },
    "design": {
      "path": "design.md",
      "status": "stale",
      "sha256": "f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f",
      "approvedAt": "2026-10-29T09:58:27Z",
      "approvedCommit": "5a88b2f07c7ac123932c91a43533f4e67b0820b4",
      "upstreamSha256": {
        "requirements": "1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0"
      },
      "approvedSha256": "f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f",
      "approvedCode": {
        "status": "captured",
        "files": [
          {
            "path": "hello.py",
            "missing": true
          },
          {
            "path": "test_hello.py",
            "missing": true
          }
        ]
      }
    },
    "tasks": {
      "path": "tasks.md",
      "status": "stale",
      "sha256": "bddc3cd7eab681f89e6cf2a8aedffe07ded0f9d17034a89a5635a398cd70e4ab",
      "approvedAt": "2026-10-29T21:14:05Z",
      "approvedCommit": "5a88b2f07c7ac123932c91a43533f4e67b0820b4",
      "upstreamSha256": {
        "requirements": "1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0",
        "design": "f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f"
      },
      "approvedSha256": "bddc3cd7eab681f89e6cf2a8aedffe07ded0f9d17034a89a5635a398cd70e4ab"
    }
  }
}
~~~~

### `.kiro/specs/00001-hello-world/requirements.md`

~~~~markdown
# Requirements: Hello World

Sources: .kiro/specflow/intake/processed/00001-hello-world

## Purpose

Provide a minimal program that greets the user on standard output and reports success through its exit status. It serves as a first, verifiable end-to-end slice for the specflow workflow.

## Scope

A single command-line program that writes a fixed greeting and terminates successfully, plus an automated test that confirms both the output and the exit status. Nothing else is covered.

## Assumptions

- The program is implemented in Python and named `hello.py`. Source: idea.md.
- The automated test uses the Python standard-library `unittest` framework. Source: idea.md.

## Requirements

### REQ-001: Greeting on standard output

Source: idea.md

**User story:** As a user running the program, I want it to print a greeting, so that I can confirm the program runs and produces visible output.

#### Acceptance criteria

1. WHEN the program is run THE SYSTEM SHALL write the text `Hello from Claude Code!` to standard output.
2. WHEN the program writes the greeting THE SYSTEM SHALL terminate the output with exactly one line feed character (`\n`) and write nothing after it.

### REQ-002: Success exit status

Source: idea.md

**User story:** As a user or an automated caller, I want the program to signal success through its exit status, so that I can detect that it completed without error.

#### Acceptance criteria

1. WHEN the program finishes writing the greeting THE SYSTEM SHALL exit with status code 0.

### REQ-003: Automated verification of output and exit status

Source: idea.md

**User story:** As a developer, I want an automated test of the program's output and exit status, so that the behavior stays verifiable without manual inspection.

#### Acceptance criteria

1. WHEN the test suite runs THE SYSTEM SHALL assert that the program's standard output equals `Hello from Claude Code!` followed by exactly one line feed character (`\n`).
2. WHEN the test suite runs THE SYSTEM SHALL assert that the program exits with status code 0.

## Non-functional requirements

- The program and its test rely only on the Python standard library; no third-party dependency is introduced. Source: idea.md (standard-library unittest).

## Risks

- Trailing-whitespace or newline mismatch: impact l, likelihood l; mitigation: the test asserts the exact output including the single trailing newline; fallback: adjust the program's output to match the asserted string.

## Out of scope

- Command-line arguments, configuration, or any greeting other than the fixed `Hello from Claude Code!`.
- Internationalization or localization of the greeting.
- Packaging, distribution, or installation of the program.
~~~~

### `.kiro/specflow/intake/processed/00001-hello-world/qa-log.md`, appended entry

~~~~markdown
## Q2 - Greeting text, replaces the fixed greeting of idea.md (2026-11-01)

- Question: none asked; the developer directed the change as host compatibility test T-043 of parent spec 00008 on Claude Code.
- Answer: "In requirements.md replace each of the three occurrences of "Hello, world!" with "Hello from Claude Code!". This deliberately invalidates the prior approval. Keep the single LF, exit 0, standard-library test, and all other requirements. Do not change design.md or tasks.md."
- Reading: REQ-001.1, REQ-003.1, and the out-of-scope bullet now name `Hello from Claude Code!`; nothing else in requirements.md changes. design.md and tasks.md stay as approved, so the requirements, design, and tasks approvals go stale and the implementation gate closes until the developer re-approves each artifact. No approval is recorded by this change.
~~~~

## Marketplace install check (T-046)

- Run: 2026-11-01, Europe/Prague, 11:20 to 11:30 CET, from the same agent
  session, with CLI `2.1.312 (Claude Code)`.
- Catalog: `.claude-plugin/marketplace.json` at the checkout root, written by
  `python3 scripts/generate_marketplace.py` from `plugins/specflow/plugin.json`
  (one entry: `specflow`, `./plugins/specflow`, version `0.1.0`).
  `claude plugin validate --strict .` printed
  `Validating marketplace manifest: <checkout>/.claude-plugin/marketplace.json`
  and `✔ Validation passed`, with one piece of advice that does not change
  the verdict: the plugin README has no line that installs `specflow` from a
  marketplace (`/plugin install specflow --marketplace <owner>/<repo>`,
  one step on Claude Code 2.1.275 or later). T-045 adds that line.
- Before the check, `claude plugin list` held no plugin containing `specflow`
  and `claude plugin marketplace list` held no `buvis-agent-plugins`.

| Step | Command | Result |
|---|---|---|
| Add the marketplace from the local checkout | `claude plugin marketplace add <checkout> --json` | `outcome: ok`, `marketplace: buvis-agent-plugins`, "declared in user settings"; `marketplace list` shows `buvis-agent-plugins` with `Source: Folder (<checkout>)`; `~/.claude/plugins/known_marketplaces.json` records `source.source` `directory` with the checkout as `path` and `installLocation` |
| Install specflow through it | `claude plugin install specflow@buvis-agent-plugins --json` | `outcome: ok`, `pluginId: specflow@buvis-agent-plugins`, `scope: user`; `plugin list` shows `specflow@buvis-agent-plugins`, version 0.1.0, `Read from: <checkout>/plugins/specflow`, enabled; `installed_plugins.json` records `installPath` `~/.claude/plugins/cache/buvis-agent-plugins/specflow/0.1.0` (that folder existed) and `gitCommitSha` `654b1be` |
| `specflow:spec-workflow` is listed | `claude plugin details specflow@buvis-agent-plugins`, then a headless `claude --print` run without `--plugin-dir` (`docs/dev/tmp/specflow/hosts/claude-marketplace-check.bash`) | details: `Skills (2)  convert-prd, spec-workflow`, source `specflow@buvis-agent-plugins`; the headless session's init event lists plugin `specflow` with source `specflow@buvis-agent-plugins`, version `0.1.0`, path `<checkout>/plugins/specflow`, and the skills `specflow:convert-prd` and `specflow:spec-workflow`, both also as slash commands; the one-turn session answered `ok` |
| Remove the plugin and the marketplace again | `claude plugin uninstall specflow@buvis-agent-plugins --json`, then `claude plugin marketplace remove buvis-agent-plugins` | `outcome: ok`, `keptData: false`; `✔ Successfully removed marketplace: buvis-agent-plugins`; afterwards `plugin list` holds no `specflow` and `marketplace list` no `buvis-agent-plugins`, so a later `--plugin-dir` run sees one copy of the plugin |

The folder route takes no ref: the marketplace reads the checkout as it is on
disk, and the registry only records the commit it saw. The public route
through GitHub is left to the release, as the design says.
