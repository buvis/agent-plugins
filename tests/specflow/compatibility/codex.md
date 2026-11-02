# Codex compatibility (T-042)

Status: passed. Local marketplace registration, plugin installation,
skill discovery, Kiro-file resume, design approval, and task-plan approval
pass with the real CLI. The developer launched
the prepared commands outside the enclosing Codex session because the
dispatch wrapper refuses nested invocation.

## Environment and installation

- Date: 2026-10-29, Europe/Prague.
- CLI: `codex-cli 0.165.0`, resolved as `/opt/homebrew/bin/codex`.
- Plugin source: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/plugins/specflow`.
- Workspace: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/docs/dev/tmp/specflow/hosts/workspace`.
- Isolated profile: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/docs/dev/tmp/specflow/hosts/codex-home`.
- Installed plugin ID: `specflow@specflow-host-test`, version `0.1.0`.
- Installed path: `/Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008/docs/dev/tmp/specflow/hosts/codex-home/plugins/cache/specflow-host-test/specflow/0.1.0`.
- Skill name exposed by the agent session: `specflow:spec-workflow`.

The profile keeps authentication at its existing location through a local
symlink; no credential contents are copied into the record or fixture.
Its `AGENTS.md` links to the shared user-global instruction authority. The
spec began as the Kiro-created `00001-hello-world`, with approved requirements,
missing design/tasks, and no `.agents/specflow.json` in the workspace.

A temporary `.agents/plugins/marketplace.json` at the checkout root uses the
surface tested by T-006 of 00002 and points at the actual plugin folder:

```json
{
  "name": "specflow-host-test",
  "plugins": [
    {
      "name": "specflow",
      "source": {
        "source": "local",
        "path": "./plugins/specflow"
      }
    }
  ]
}
```

With `CODEX_HOME` set to that isolated profile, these real CLI operations
both returned exit 0:

```text
codex plugin marketplace add /Users/bob/git/src/worktrees/agent-plugins/feature-specflow-00008 --json
codex plugin add specflow@specflow-host-test --json
```

The first returned marketplace `specflow-host-test`, the checkout as its
installed root, and `alreadyAdded: false`. The second returned the plugin
ID, version, and installed cache path above, with `authPolicy: ON_INSTALL`.
The temporary catalog is test setup, not a distributable catalog; it must
be removed when the host sessions no longer need it and is not part of this
task's commit.

## Dispatch limitation

The `use-codex` skill requires its `codex-run.sh` wrapper for model dispatch.
The wrapper saw the enclosing session's `CODEX_SESSION_ID` and exited 3:

```text
refusing nested dispatch (already inside a CLI agent)
```

No model session was launched and no spec artifact changed in that attempt.
The prepared `docs/dev/tmp/specflow/hosts/codex-start.bash` runs the same
wrapper from a regular Terminal, with the isolated profile, the actual
workspace as its current directory, workspace-write permissions, a prompt
file, a captured final response, and a captured thread ID. It does not clear
or bypass the recursion guard. The prompt requests plugin-based skill
discovery, read-only reconciliation of Kiro's files, and a design draft,
then stops at the explicit approval gate. The completed runs are recorded below.

## Design draft run

The developer ran `codex-start.bash` from a regular Terminal and returned
its completed result. Codex discovered `specflow:spec-workflow` through the
installed plugin system and reported its loaded root manifest as
`<installed path>/plugin.json`. The cached skill path is
`<installed path>/skills/spec-workflow/SKILL.md`. An independent byte check
found all 69 package source files present and identical in the installed
cache. The isolated profile also reports `Logged in using ChatGPT`.

Codex read both contracts and the standard profile, resumed the Kiro spec
in phase `design`, and reported no initial reconciliation changes. The
requirements approval remains unchanged at
`1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0`.
It wrote only the design artifact, leaving requirements and their approval
intact. The draft names two new implementation paths, `hello.py` and
`test_hello.py`, and specifies a standard-library subprocess unittest with
byte-exact output and return-code assertions.

Codex reports a passing Tier 2 review with no findings from its isolated
pre-pass. Independent helper validation returns exit 0 with no findings.
The design's canonical hash is
`f2f0541e1d2be1cdd4d4b81abf78b7e336d73625d4f03ffcb1fce2dd8241d81f`.
The placement baseline contains exactly the two proposed files, both missing.
Status derives requirements approved, design draft, tasks missing, no stale
files, hold, warnings, or folder problems. Task and implementation gates
remain closed on the expected draft/missing artifacts; there is no task list
or next task. No design approval or implementation was performed.

The prepared approval command pins that exact design hash and stops if it
or the requirements hash changes. It records approval only when the developer
explicitly runs the command, then drafts the task plan and stops at its next
approval gate. The wrapper's resume path forces a read-only sandbox, so each
writing phase uses a fresh workspace-write CLI call in the same profile and
workspace. These calls are successive approval steps of this one recorded
host workflow test; no chat context is needed for file-based continuation.

## Design approval and task-plan draft

The developer explicitly ran the prepared design-approval command from a
regular Terminal. Codex verified both pinned hashes and recorded the design
approval at `2026-10-29T09:58:27Z`, against workspace commit
`5a88b2f07c7ac123932c91a43533f4e67b0820b4`. Its `approvedCode` contains
exactly `hello.py` and `test_hello.py`, both missing. Requirements remain
approved and unchanged.

Codex then drafted `tasks.md`, containing one coupled implementation-and-test
task, T-001, with all five acceptance criteria mapped. The process test checks
exact stdout bytes and exit status; it uses only the standard library.
Independent validation returns exit 0 with no findings. The task-plan hash is
`bddc3cd7eab681f89e6cf2a8aedffe07ded0f9d17034a89a5635a398cd70e4ab`.
The resulting state is phase `tasks`: requirements and design approved,
tasks draft, implementation blocked only by that draft, no stale artifacts,
hold, warnings, or spec-folder problems. Progress is 0/1; no implementation
exists. The only changed files in this step are state and the new task plan.

The final prepared command pins all three hashes, records only the explicit
task-plan approval when run by the developer, verifies the implementation
gate, and stops without implementing T-001 or ticking any checkbox.

## Task-plan approval and final result

The developer ran `codex-approve-tasks.bash` from a regular Terminal.
Codex checked all three pinned canonical hashes, validated the task plan,
and recorded its approval at `2026-10-29T21:14:05Z`, against the same
workspace commit. The design baseline and upstream approvals are unchanged.
The final marker was `specflow-codex-host-test-complete`.

An independent read of the workspace confirms the final state below.
Reconciliation proposes no changes and no ambiguities. Progress remains
0/1, with T-001 next. `hello.py`, `test_hello.py`, and
`.agents/specflow.json` are absent. No implementation or task checkbox
was changed. The workspace was retained throughout; no reconstruction
from the Kiro record was needed.

| Required step | Result |
|---|---|
| Load the root manifest | Pass: native marketplace installation and reported root `plugin.json` |
| Discover the shared skill | Pass: `specflow:spec-workflow` |
| Resume Kiro's files | Pass: requirements approved, phase design, initial reconciliation unchanged |
| Continue the correct phase | Pass: design drafted before tasks |
| Approve design | Pass: explicit developer command, matching hash and placement baseline |
| Draft and approve tasks | Pass: explicit developer command, matching upstream hashes, implementation gate open |

## Install trials in a fresh profile (T-045)

Run on 2026-11-01 with `codex-cli 0.166.0`, each in a fresh, empty
`CODEX_HOME` under the session scratchpad, through
`docs/dev/tmp/specflow/hosts/codex-fresh-trial.bash`. The temporary
`.agents/plugins/marketplace.json` of T-042 had been removed from the
checkout first, so the only marketplace file in the repository was the
generated `.claude-plugin/marketplace.json` of T-046. No model session ran;
the trials cover the install route only, and skill discovery from this cache
layout is the T-042 result above.

| Route | Commands | Result | Takes a ref |
|---|---|---|---|
| Local checkout, read through `.claude-plugin/marketplace.json` | `codex plugin marketplace add <checkout> --json`, then `codex plugin add specflow@buvis-agent-plugins --json` | Pass: marketplace `buvis-agent-plugins`, `installedRoot` = the checkout, `alreadyAdded: false`; `codex plugin list` names `<checkout>/.claude-plugin/marketplace.json` as the marketplace file and shows `specflow@buvis-agent-plugins` `installed, enabled` `0.1.0` with the source `<checkout>/plugins/specflow`; the plugin was copied to `$CODEX_HOME/plugins/cache/buvis-agent-plugins/specflow/0.1.0` with `authPolicy: ON_INSTALL` | No: a folder marketplace reads the checkout as it is on disk |
| Git marketplace from GitHub | `codex plugin marketplace add buvis/agent-plugins --ref feature/specflow-00008 --json`, then `codex plugin add specflow@buvis-agent-plugins --json` | Pass: Codex cloned the ref into `$CODEX_HOME/.tmp/marketplaces/buvis-agent-plugins`, read its `.claude-plugin/marketplace.json`, and installed `specflow@buvis-agent-plugins` `0.1.0` from `<clone>/plugins/specflow` into the same cache path | Yes: `--ref <branch-or-tag>` or `owner/repo@ref`; without a ref the default branch is used, which carries the catalog only once this branch is merged |

`diff -rq` between `plugins/specflow/` and each cache copy (Python bytecode
excluded) reports no difference, so both routes install the same package.
Codex's own marketplace file, `.agents/plugins/marketplace.json`, is not
needed: the Claude-compatible catalog is read as written, which resolves the
"to be verified" Codex install line of the 00008 design.

## Final status

```json
{
  "statusVersion": 1,
  "specs": [
    {
      "spec": "00001-hello-world",
      "specType": "feature",
      "profile": "standard",
      "phase": "implementation",
      "state": "valid",
      "hold": null,
      "artifacts": {
        "requirements": "approved",
        "design": "approved",
        "tasks": "approved"
      },
      "stale": [],
      "gates": {
        "design": "open",
        "tasks": "open",
        "implementation": "open"
      },
      "blockers": [],
      "warnings": [],
      "nextTask": {
        "id": "T-001",
        "title": "Deliver the fixed greeting with process-level verification"
      }
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
    "requirements": "approved",
    "design": "approved",
    "tasks": "approved"
  },
  "phase": "implementation",
  "changes": [],
  "ambiguous": []
}
```

## Artifact snapshot

These are the files as Codex left them, captured after task approval.
The Q&A log retains dates originally written by Kiro; the actual observed
Kiro run dates are in `kiro-ide.md`. Later host steps append their results
without rewriting this historical snapshot.

### `.kiro/specflow/intake/processed/00001-hello-world/idea.md`

~~~~markdown
# Hello world

Create a standard, requirements-first spec named 00001-hello-world.

Use the default `.kiro/specs` folder. Keep `.agents/specflow.json` absent.

The program `hello.py` must print "Hello, world!" with one newline and exit 0.

Include a standard-library unittest for its output and exit code.
~~~~

### `.kiro/specflow/intake/processed/00001-hello-world/qa-log.md`

~~~~markdown
# Q&A log: 00001 hello-world

## Intake choices (2026-10-25)

- Spec type: feature. Basis: a new program, not a defect.
- Workflow order: requirements-first. Basis: the developer asked for a requirements-first spec; the input is a behavior request, not a design.
- Profile: standard. Basis: all four dimensions rate low (a single fixed-string program), so the rating alone would recommend quick; the developer explicitly asked for a standard spec, which overrides the recommendation.

## Discovery 2026-10-25

- Classification: empty repository. Basis: the workspace holds only `.git/` and `.vscode/`; no source file, framework config, package manifest, source folder, or submodule.
- Coverage: read in full the workspace root listing; no source paths exist to skim or skip.
- D1: No existing code or conventions. The binding technical constraint is standard-library-only Python; tests use the standard-library `unittest` framework (from the developer's input).
- D2: No root instruction files (`AGENTS.md`, `CLAUDE.md`, root steering) are present in the workspace, so no repository constraints apply to the affected paths.

## Q1 - Clarifying questions (2026-10-25)

- Question: none asked.
- Answer: "The input specifies the program behavior, the exit code, the newline, the test framework, the spec name, the profile, the workflow order, and the specs folder completely."
- Reading: every intake and requirements topic is answered by the input, so no clarifying question materially changes scope or behavior.

## Review: requirements.md 2026-10-25

- 1 | Question | Fix the trailing newline as a single LF (\n) | option 1 applied (REQ-001.2 and REQ-003.1) | resolved

## Review: design.md 2026-10-29

- Domain: local command-line tool; maturity: draft for approval; standard profile, Tier 2 because lifetime is unspecified.
- Isolated adversarial pre-pass: one pass, no findings. Cardinal sins checked: none present; stateful, production, credential, public API, and vendor concerns do not apply to this local fixed-output example.
- Comprehension pass: no confusion notes. All Tier 2 techniques, ten stress scenarios, and anti-pattern checks ran; no actionable findings. No lenses or scripts skipped. Tier 3 personas and counterfactuals are not applicable at this tier.
- Checklist 027 Solid: Overview and Requirement traceability connect behavior and criteria.
- Checklist 028 Solid: Context and constraints identifies the solo developer as owner.
- Checklist 029 Solid: Context and constraints bounds technology, repository state, and assumptions.
- Checklist 030 Solid: Alternatives considered includes the smallest diff and standard-library reuse.
- Checklist 031 Solid: Architecture has two files and one dependency direction.
- Checklist 032 Solid: Data model defines transient values; no persistent lifecycle applies.
- Checklist 033 Solid: Components and interfaces gives command, signatures, bytes, and exit status.
- Checklist 034 Not applicable: Data and control flow has no shared state or concurrent writes.
- Checklist 035 Not applicable: Architecture has one bounded greeting, with no service load or performance requirement.
- Checklist 036 Solid: Error handling names launch, output, and timeout failures.
- Checklist 037 Solid: Testing strategy and Error handling expose output, exit, and test failures; no service telemetry applies.
- Checklist 038 Solid: Security and privacy bounds trust and avoids shell interpretation.
- Checklist 039 Not applicable: Security and privacy identifies no personal or persisted data.
- Checklist 040 Solid: Architecture introduces no infrastructure; local developer ownership suffices.
- Checklist 041 Not applicable: Rollout and migration describes local files, with no deployed topology.
- Checklist 042 Solid: Rollout and migration gives introduction, verification, and removal backout.
- Checklist 043 Solid: Testing strategy exercises the actual process and exact bytes.
- Checklist 044 Not applicable: There are no design-constrained intermediate deployment states.
- Checklist 045 Solid: Rollout and migration uses this design for execution and verification commands.
- Checklist 046 Solid: Risks and edge cases supplies mitigations and fallback; Open decisions has none.
- Checklist 047 Solid: Section audit found no weight outliers; names and criteria agree.
- Checklist 048 Solid: Architecture avoids helpers, frameworks, and packaging.
- Checklist 049 Solid: Placement and rollout contain only reversible new local files.
- Checklist 050 Solid: Architecture records rationale and rejected options in two ADRs.
- Checklist 051 Solid: Full workspace discovery confirms placement targets are absent and no reusable source exists.
- Premortem: A later maintainer could replace the process test with an in-process check and lose the exit contract. The design explicitly names the process boundary and both assertions. Platform newline translation could also change bytes. Exact byte assertions expose that failure, and the risk section gives a fallback. No additional mitigation is required for this scope.
- Scripts: section_weight_audit has no outliers; claim_ladder_scan flags only configurable in future-change notes, not a current quality claim; adversarial_signal_scan finds no signals.
- Recap: zero findings raised, resolved, disputed, deferred, or open at every severity. Explicit confirmation of soundness after the selected lenses supplies the review surprise criterion; no blockers remain for actionability. Developer surprise feedback and design approval are pending. No approval recorded.
~~~~

### `.kiro/specs/00001-hello-world/.config.kiro`

~~~~json
{"specId": "da79623a-262e-4eeb-9f8b-287694bdb476", "workflowType": "requirements-first", "specType": "feature"}
~~~~

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
      "status": "approved",
      "sha256": "1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0",
      "approvedSha256": "1eceb5baa20596b1e5d931ce93f0ddcd5d95103d9202ec93457db3ab7a3876f0",
      "approvedAt": "2026-10-27T21:47:41Z",
      "approvedCommit": "5a88b2f07c7ac123932c91a43533f4e67b0820b4"
    },
    "design": {
      "path": "design.md",
      "status": "approved",
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
      "status": "approved",
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

### `.kiro/specs/00001-hello-world/design.md`

~~~~markdown
# Design: Hello World

## Overview

Provide a small Python command-line program and one standard-library unittest that verifies the actual process output and success status. The approved requirements remain the behavioral authority.

## Context and constraints

`.kiro/specs/00001-hello-world/requirements.md` requires the fixed greeting, exactly one LF, exit 0, and automated assertions. Its Python and unittest assumptions come from `.kiro/specflow/intake/processed/00001-hello-world/idea.md`.

The repository has no source, dependency manifest, existing helpers, or repository instruction files. Discovery covered every non-Git file, including the intake log and Kiro sidecars; no source was skipped. The solo developer owns this local example. No production service or deployment is involved.

## Architecture

Two independent root files suffice: the executable script and its process-level test. The test launches the script; the script depends only on Python's built-in output facilities. There are no services, persistent stores, or runtime configuration.

ADR-001: Direct script output.
- Context: one fixed output needs no reusable application API.
- Decision: one guarded print statement, using `if __name__ == "__main__":`, with natural successful interpreter termination.
- Consequences: minimal code; future configurable greetings require a new design decision.
- Alternatives Rejected: a main function adds an unnecessary interface; leaving the repository unchanged does not deliver the greeting.

ADR-002: Process verification.
- Context: output and process exit status are the acceptance boundary.
- Decision: use unittest and subprocess with the running test interpreter.
- Consequences: one child-process startup, but the real CLI contract is tested without mocks.
- Alternatives Rejected: redirected in-process output cannot verify the actual process exit; third-party test tooling adds an unneeded dependency.

## Module placement

All proposed implementation files are listed below. Both are new; neither exists today.

| Repository-relative path | New or edit | Holds |
|---|---|---|
| `hello.py` | New | Guarded greeting script |
| `test_hello.py` | New | One unittest exercising the script as a child process |

No package, configuration, dependency, or additional documentation file is required. This design itself lives at `.kiro/specs/00001-hello-world/design.md`.

## Components and interfaces

`hello.py` maps to REQ-001 and REQ-002. Command: `python3 hello.py`. Its guarded body calls `print("Hello, world!")` once. It exports no application API. On the workspace's macOS host, stdout bytes are exactly `b"Hello, world!\n"`; normal interpreter completion returns 0. There is no argument processing or input reading.

`test_hello.py` maps to REQ-003. It defines `class HelloTest(unittest.TestCase)` and `def test_output_and_exit_status(self) -> None`. Resolve the script with `Path(__file__).resolve().with_name("hello.py")`. Call `subprocess.run([sys.executable, str(script)], capture_output=True, check=False, timeout=5)` without a shell or text conversion. Assert `result.stdout == b"Hello, world!\n"` and `result.returncode == 0` using `self.assertEqual`. A guarded `unittest.main()` supports direct execution.

## Data model

No persisted entities exist. The script owns one constant greeting string. The test observes `subprocess.CompletedProcess` fields `stdout: bytes`, `stderr: bytes`, and `returncode: int`; stderr is captured for diagnosis, with no new stderr requirement.

## Data and control flow

The user invokes Python on `hello.py`. Python enters the guarded body, writes the greeting with print's default newline, and exits normally. The unittest runner discovers `HelloTest`, launches the same Python interpreter on the resolved script path, waits up to five seconds, and compares the captured bytes and return code. Assertion failures become unittest failures.

## Error handling

An output mismatch or nonzero return code fails the test. A missing script, launch failure, or timeout becomes a unittest error rather than a successful result. Runtime stdout failures use Python's normal exception reporting and unsuccessful exit; no recovery behavior is required for an unavailable output destination. The five-second test timeout bounds waiting for an accidentally hanging script.

## Security and privacy

The program accepts no input, reads no secrets, and uses no network or persistent data. The test invokes a fixed local script with an argument list and no shell. The Python interpreter and repository contents are trusted local development inputs; sandboxing hostile code is outside this example.

## Testing strategy

Run `python3 -m unittest -v test_hello.py` from the repository root. One process-level integration test is sufficient; no mocks, separate unit tests, coverage target, or load suite are needed.

- Happy path: fixed greeting and exit 0 cover REQ-001.1 and REQ-002.1.
- Edge cases: byte equality detects missing or additional newlines, CRLF, spaces, and extra output, covering REQ-001.2 and REQ-003.1.
- Automated success assertion covers REQ-003.2.
- Error cases: subprocess exceptions and timeout fail the suite; arbitrary invalid inputs are not applicable because the program reads none.
- Path resolution supports running the test from another working directory without changing the program path.

## Rollout and migration

After design and task approvals, add the two files and run the test command. There is no data or configuration migration. Backout removes the two newly introduced files; no external state needs recovery. This document supplies the execution and verification commands; no separate runbook is needed.

## Risks and edge cases

- Output newline translation on another operating system: impact l, likelihood l; mitigation: byte-level verification on the current macOS host; fallback: use an explicit byte write if portability becomes required.
- Accidental script hang: impact l, likelihood l; mitigation: subprocess timeout of five seconds; fallback: diagnose the failing test before delivery.
- Likely next change, configurable greeting: bounded by a new input contract and tests; current arguments remain out of scope.
- Likely next change, packaging: bounded by a separate distribution decision; no package scaffolding is introduced now.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Guarded print with default newline | REQ-001.1, REQ-001.2 |
| Normal interpreter termination | REQ-002.1 |
| Child-process byte-output assertion | REQ-003.1, REQ-001.1, REQ-001.2 |
| Child-process return-code assertion | REQ-003.2, REQ-002.1 |

The built-ins, unittest, subprocess, pathlib, and sys satisfy the standard-library-only constraint.

## Alternatives considered

1. Direct guarded print plus subprocess unittest: chosen as the smallest implementation that verifies the full required process boundary, reusing standard-library tools.
2. Main function plus in-process stdout capture: rejected because the extra function does not help this fixed behavior and the test would miss actual exit behavior.
3. Do nothing: smallest diff overall, rejected because there is no existing greeting implementation to extend and no acceptance criterion would be delivered.

## Reuse inventory

Repository searches used `greet|hello|print|output|write|unittest|subprocess` across all non-Git files, including hidden files. Matches were only the existing spec and intake; the known-present term `Hello` in requirements confirmed search coverage. No reusable repository code exists. Reuse Python's built-in print and standard-library unittest, subprocess, pathlib, and sys directly; no new helper abstraction or external service is needed.

## Open decisions

Not applicable: the approved input fixes behavior and technology; placement and test mechanics are reversible implementation choices. No additional assumption requiring an answer was introduced. The assumptions already listed in requirements remain assumptions.
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

1. WHEN the program is run THE SYSTEM SHALL write the text `Hello, world!` to standard output.
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

1. WHEN the test suite runs THE SYSTEM SHALL assert that the program's standard output equals `Hello, world!` followed by exactly one line feed character (`\n`).
2. WHEN the test suite runs THE SYSTEM SHALL assert that the program exits with status code 0.

## Non-functional requirements

- The program and its test rely only on the Python standard library; no third-party dependency is introduced. Source: idea.md (standard-library unittest).

## Risks

- Trailing-whitespace or newline mismatch: impact l, likelihood l; mitigation: the test asserts the exact output including the single trailing newline; fallback: adjust the program's output to match the asserted string.

## Out of scope

- Command-line arguments, configuration, or any greeting other than the fixed `Hello, world!`.
- Internationalization or localization of the greeting.
- Packaging, distribution, or installation of the program.
~~~~

### `.kiro/specs/00001-hello-world/tasks.md`

~~~~markdown
# Tasks: Hello World

- [ ] T-001 Deliver the fixed greeting with process-level verification
  - Requirements: REQ-001, REQ-002, REQ-003
  - Depends on: none
  - Location: hello.py, test_hello.py
  - Reuse: Python's built-in print and standard-library unittest, subprocess, pathlib, and sys; no repository helper exists.
  - Contract: `hello.py` maps to REQ-001 and REQ-002. Command: `python3 hello.py`. Its guarded body calls `print("Hello, world!")` once. It exports no application API. On the workspace's macOS host, stdout bytes are exactly `b"Hello, world!\n"`; normal interpreter completion returns 0. There is no argument processing or input reading.
  - Contract: `test_hello.py` maps to REQ-003. It defines `class HelloTest(unittest.TestCase)` and `def test_output_and_exit_status(self) -> None`. Resolve the script with `Path(__file__).resolve().with_name("hello.py")`. Call `subprocess.run([sys.executable, str(script)], capture_output=True, check=False, timeout=5)` without a shell or text conversion. Assert `result.stdout == b"Hello, world!\n"` and `result.returncode == 0` using `self.assertEqual`. A guarded `unittest.main()` supports direct execution.
  - Details: Add the two new root files. Guard the script output with `if __name__ == "__main__":`. Keep the script and its single integration test together so the task passes after its own changes. Use only the standard library. Follow the design's rollout: add both files, then run the test. The approved design supplies execution documentation; no separate runbook, compatibility scaffolding, dependency file, or temporary artifact is needed.
  - Acceptance criteria: REQ-001 criteria 1, 2; REQ-002 criterion 1; REQ-003 criteria 1, 2
  - Verify: Run `python3 -m unittest -v test_hello.py` from the repository root; `HelloTest.test_output_and_exit_status` must pass its exact-byte stdout and zero-returncode assertions. Run `python3 test_hello.py` to verify the guarded test entry point. Review both new files for standard-library-only imports and confirm no temporary implementation files remain.

## Completion criteria

- [ ] T-001 verification passes: the process emits exactly `b"Hello, world!\n"` and returns 0.
- [ ] All three requirements and their five acceptance criteria are covered by the passing process test.
- [ ] Only hello.py and test_hello.py are added for implementation; execution documentation remains in the design, and no dependency or temporary files are introduced.
~~~~
