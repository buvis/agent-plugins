# Scenario records and manual runs

T-056 is **complete** (2026-11-15): all three adapters passed their live
boundary probe and the live self-check; see the 00009 QA log. Synthetic records
under `fixtures/results/` are never release evidence. Each adapter stays
blocked until a passing boundary proof for its exact host version, package
revision, generated configuration, and runner code is supplied with
`--boundary-proof`. A proof must be made in a developer terminal outside
`run-agent`, because a nested Seatbelt sandbox cannot start inside it, and it
goes stale when the host upgrades or a runner file changes.

Open for T-057: Codex records are not yet `measured` (two host instruction
fields differ between probe and session), and no live session had measured
reads.

## Host telemetry and controls (measured 2026-11-15)

Installed hosts: Claude Code 2.1.325, Codex 0.167.2, kiro-cli 2.35.1 with
Kiro Agent Server 0.66.70. Codex moved from 0.167.0, so the recorded shell and
instruction-rendering diagnostics below are historical for that version.

| Host | Instruction telemetry | Read telemetry | Isolation controls |
|---|---|---|---|
| Claude Code | `InstructionsLoaded` hook: one event per loaded file, with `load_reason` and `parent_file_path` for imports. It fires on every resumed turn. Observed live for root, import, rule, and nested loads. | `Read`/`Grep` tool events and shell commands in the stream | Empty `CLAUDE_CONFIG_DIR`, `--setting-sources project,local`, generated `--settings` (default-deny permissions, mandatory shell sandbox, sign-in stripped from tool processes) |
| Codex | Session record `world_state.agents_md` holds the merged instruction text and its directory, rewritten on a resumed turn when the file changes. No file paths. Nothing below the working directory loads. | `command_execution` items | Private `CODEX_HOME`, per-turn permission profile; the session record's `turn_context` reports the effective profile, model, and CLI version |
| Kiro | Stream update `steering_inclusion` lists the URI of every loaded instruction file; `context_usage` lists context files | `tool_call` updates with `rawInput.path` | `KIRO_HOME` relocates settings, agents, Powers, and sessions while the sign-in stays valid; with `chat.disableInheritingDefaultResources` and a custom agent only fixture instructions load |

The in-session checks behind this table used synthetic workspaces. Two of
them, one Codex and one Kiro turn, ran under the normal profile to read the
event format only; they are not isolation evidence.

**Claude collector.** A supervisor hook hashes each file at its load event and
appends the event to `<batch>/control/instructions.jsonl`. A `SessionStart`
marker proves that the generated settings were read; a turn without it fails.
A root `CLAUDE.md` that exists but was not reported leaves the turn unmeasured.

**Codex collector (contract revision pending).** The host records loaded text,
not paths. The adapter names the path from Codex's documented discovery rule
(one `AGENTS.override.md` or `AGENTS.md` in the Git root, no imports) and accepts
it only when the host-recorded text equals the file as it was before launch.
The developer accepted that reading on 2026-11-15 with one addition: every
other instruction field the host records must have the fingerprint the
boundary probe saw (`instructionChannels` in the proof). A turn that differs
stays `not-measured`.

Codex 0.169 stores `permissions.instructions` as a hash of rendered text.
The adapter renders that text with the same private home/profile, verifies its
original bytes against the host-recorded hash, then fingerprints the normalized
text. Missing text or a hash mismatch fails the probe's instruction-inventory
check and leaves session instructions unmeasured. No instruction channel is
excluded. This rendering makes no model call. A runner change stales the proof.
The renderer receives the live turn's recorded model and approval policy:
`exec` defaults to `never`, whereas `debug prompt-input` otherwise uses its
ordinary approval policy. Missing live policy/model leaves instructions unmeasured.

The disposable Codex home and eval profile set `plugins._default.enabled = false`
and explicitly enable only `specflow@buvis-agent-plugins`. This prevents account
plugin synchronization from expanding the skill catalog between turns. The
instruction fingerprint check remains mandatory; an unexpected catalog is not
normalized away. These settings do not modify the developer's normal home.

## Live proof procedure

Run each step in a developer terminal outside `run-agent`, from the
repository root. A probe uses synthetic sentinels only and costs one short
model turn.

1. Make the scratch folder: `mkdir -p docs/dev/tmp/specflow/proofs`.
2. Export the Claude setup sign-in: `export CLAUDE_CODE_OAUTH_TOKEN="$(<~/.local/secrets/claude-setup-token)"`.
3. Run `python3 -B tests/specflow/evals/runners/run_claude.py --probe-boundary --model claude-haiku-5-5 > docs/dev/tmp/specflow/proofs/claude.json`. Exit 0 means every check passed.
4. Run `python3 -B tests/specflow/evals/runners/run_codex.py --probe-live --model <codex-model> > docs/dev/tmp/specflow/proofs/codex.json`. Sign in when Codex asks. The sign-in lives only in the batch directory.
5. Read both proof files. Each check names its evidence.
6. Run the self-check session: `python3 -B tests/specflow/evals/runners/run_claude.py status-summary --model claude-haiku-5-5 --boundary-proof docs/dev/tmp/specflow/proofs/claude.json --evals tests/specflow/fixtures/results/self-check --out docs/dev/tmp/specflow/results`. The expected exit is 1: one eval passes and the impossible eval fails.
7. Run the same session with `run_codex.py`, `<codex-model>`, and `proofs/codex.json`. Sign in again when Codex asks.
8. Run `python3 -B tests/specflow/evals/runners/run_kiro.py --probe-live --model claude-haiku-5.5 > docs/dev/tmp/specflow/proofs/kiro.json`. Kiro uses its existing sign-in; nothing is copied.
9. Run the same session with `run_kiro.py`, `claude-haiku-5.5`, and `proofs/kiro.json`.
10. Compare the records: `python3 -B tests/specflow/evals/runners/score.py --compare docs/dev/tmp/specflow/results/claude-code/status-summary/1.json docs/dev/tmp/specflow/results/codex/status-summary/1.json docs/dev/tmp/specflow/results/kiro-ide/status-summary/1.json`. Exit 0 means equal status fields.

**Kiro limits found on 2.35.1.** The sign-in does not survive an empty `HOME`,
so the Kiro process keeps the real `HOME`; `KIRO_HOME` and the agent's deny
rules carry the isolation. `steering_inclusion` appears only on the first turn
of a conversation and not at all for an agent without instruction files. Every
turn reports `context_usage` with the matched context files; the adapter adds
them to its observations. That list counts as the inventory of a later turn
only under a proof with `contextInventoryVerified: true`: the probe adds an
instruction file before a second turn and requires the list to show it
(decided 2026-11-15). No documented Kiro control strips environment variables
from tools; the probe's `tool-secret-environment-denied` check decides. Inside
`run-agent` Kiro reports its sandbox as active while every shell command fails
with `sandbox_apply: Operation not permitted`; the adapter treats that as a
failure.

A proof is bound to the host version, the committed package tree, and the
generated configuration. Any change to one of them needs a new probe.

Codex reduces the documented exec JSONL events: ordered thread, start, and
completion evidence, the same thread on a resumed turn, a final reply, and
nonnegative token usage. A shell command that exits nonzero is ordinary work.
A failed or declined file change, an error item, a malformed stream, or a
nonzero process exit fails the turn without advancing conversation state or
storing raw output.

## Approved environment and remaining proof

The canonical contract is 00009's `design.md`, Eval runners of T-056. D11's
isolated Codex home is decided; no personal-file move or tainted-evidence waiver
exists. The approved revision replaces active-sign-in copying with independent
login directly into the batch home. `temporary_home` accepts a supervisor
provisioning callback, never an existing credential path; it checks private,
regular, unlinked authentication state before installation. The provisioner
runs `codex login` in the developer's terminal with file storage inside the
batch home; it refuses to start without a terminal. The sign-in happens inside
the batch clock, so it shortens the batch budget instead of preceding it.
Synthetic tests cover installation, mismatch, errors, interruption, and cleanup.

The approved scratch layout is an external private batch under the macOS system
temporary root, containing `workspaces/`, `resources/`, and `control/`. The old
repository-local root cannot support the required Git initialization under the
active Seatbelt profile. The shared engine now creates the external layout,
verifies the resource copy, and uses its helper for status capture. It refuses
ancestor instructions and residual external or legacy private state. Tests use
mocked host/Git boundaries; this is not installed-host isolation evidence.
Do not remove the preflight refusal merely to try a session.

The approved Claude route uses an isolated configuration home, setup-token auth,
verified fixture settings, and an explicit plugin read directory with native-tool
and shell write denial. Codex needs restricted reads excluding its credential
home except the installed plugin subtree. Kiro needs proven resource-inheritance
and tool restrictions. Check effective settings, complete loaded-instruction
inventory, required helper/reference access, denied credential reads and plugin writes,
and cleanup before admitting release evidence. Never infer isolation from a
model's own statement or from successful synthetic tests.

## Verified synthetic shell boundary

The developer-run Codex probe passed all eleven checks on 2026-11-10, with
sandbox exit 0 and cleanup true. Versions: Codex 0.167.0, Python 3.15.2, Apple Git
2.54.0 (Apple Git-157). Normalized policy SHA-256:
`53a54b5b99edd7cd40b22105ab8a177518f06bed4a0a1f1bc934a455e179ddf5`.
The full developer-reported diagnostic and fingerprints are retained in 00009's
QA log under "T-056 shell boundary passed". This is shell evidence only;
`releaseEvidence` remains false.

The probe uses a private external batch, an independent Git workspace, a plugin
copy verified against its committed tree, and an empty unauthenticated Codex
home. It selects a named [permissions profile](https://learn.chatgpt.com/docs/permissions)
and includes managed configuration. The generated policy grants platform/Python
runtime reads, read access to the explicitly selected Git executable, workspace
writes, and plugin reads. No read grant covers the containing developer-tools
directory. The chosen Git directory leads the clean child PATH so the helper
uses that executable. Git version and binary SHA-256 are reported.

Checks cover workspace read/write, plugin read, helper status, denied control/home/
other-workspace/temporary-sentinel reads, plugin writes, and symlink read/write
attempts. Both Python and child shell operations are tested. Only EACCES/EPERM
satisfies a direct denied operation; missing files cannot pass. Missing checks,
nonzero sandbox exit, or failed cleanup cannot pass. The home sentinel is in the
disposable Codex home; no real personal file is a test target.

Use this command from the repository root in a developer terminal outside
`run-agent` when a changed configuration needs another proof. Resolve Python
before clearing inherited environment settings:

```sh
/usr/bin/env -i HOME="$HOME" PATH="/usr/bin:/bin" "$(mise which python3)" -B tests/specflow/evals/runners/run_codex.py --probe-boundary --codex <installed-executable> --git-executable <git-file>
```

The observed Git executable is
`/Library/Developer/CommandLineTools/usr/bin/git`. The probe never logs in,
loads real credentials, calls a model, changes broker trust, or enables the live
runner. It has a 180-second deadline and process-group cleanup. Exit 0 means
these checks passed, 1 means the report failed, and 2 means setup was unavailable
or interrupted. Output includes normalized generated policy, fingerprints,
checks, and cleanup; it is not an independent dump of effective settings.

The helper-alias warning persisted in the successful run and did not prevent any
of these eleven checks. Native Codex file tools, complete loaded-instruction
inventory, real-home and network enforcement, independent authentication, and
the live adapter remain unproven. Do not extend this result to those controls.
The outer-profile agent still cannot launch the nested sandbox, and warrant
refused its executable path. Do not retry either refused route. Earlier probe
syntax/setup failures are preserved in the QA log, not repeated here.

## Instruction-rendering diagnostic

Installed Codex 0.167.0 exposes `debug prompt-input`; the
[official command reference](https://learn.chatgpt.com/docs/developer-commands#codex-debug-prompt-input)
describes its rendered input list. The separate `--probe-instructions` mode
prepares synthetic instructions and an empty home, verifies Git and plugin
setup, and invokes that renderer. It never invokes `sandbox`, `exec`, or
`login`. Raw input and stderr are discarded; the report contains fingerprints,
fixed diagnostic categories, input count, fixture-marker presence, and cleanup.
Its 180-second deadline includes preparation and rendering.

The developer-run diagnostic passed outside `run-agent` on 2026-11-13:
exit 0, seven rendered inputs, fixture included, and cleanup true. Codex was
0.167.0, Python 3.15.2, and Apple Git 2.54.0. Runner SHA-256
`bccf8c232f2c71c56fd19ccb485a8874fdef12d61e8d09778291625cf7afd7fd`,
plugin tree, Git binary, and normalized policy fingerprints matched the checkout.
Only `temporary-home-aliases` remained in the diagnostic categories. The full
normalized report is retained in 00009's QA log. No repeat is needed for these
unchanged inputs.

The earlier agent-side failure remains historical: exit 1, no inputs,
`permission-denied` and `temporary-home-aliases`, cleanup true. Its exact denied
operation was not retained; neither category identifies a particular attempted
path or sandbox operation. Do not retry in the agent profile. If changed inputs
require a repeat, use a developer terminal outside `run-agent`:

1. Open a developer terminal outside `run-agent`.
2. Change to the `feature-specflow-00009` working directory.
3. Run `/usr/bin/env -i HOME="$HOME" PATH="/usr/bin:/bin" "$(mise which python3)" -B tests/specflow/evals/runners/run_codex.py --probe-instructions --codex "$(mise which codex)" --git-executable /Library/Developer/CommandLineTools/usr/bin/git`.
4. Preserve the diagnostic JSON with its tested fingerprints.

Even exit 0 proves fixture inclusion only. The report always keeps
`instructionMeasurement: not-measured` and `releaseEvidence: false`: a rendered
input array has not been proven to enumerate every instruction source, import,
or subsequent load. Native read/write denial, actual-home sentinel denial,
effective configuration, tool environments, and network policy remain separate
checks. The passing shell report remains tied to its original runner/configuration.

The renderer's fixture-marker check is superseded by the per-turn collectors
described under "Host telemetry and controls". It never certified an adapter.

## Implemented resource controls

The shared engine rejects more than 24 developer turns per session, including
continuation sessions. Monotonic limits are 600 seconds per command/turn,
1800 seconds per session, and 7200 seconds per batch, including setup and
scoring. Nested timeouts use the remaining enclosing deadline. Expiry prevents
another process/turn; interrupted records carry no scores. SIGINT/SIGTERM unwind
cleanup, and a timed-out process group receives TERM, then KILL after at most
five seconds. The judge uses the same process-group cleanup and deadline budget.
Claude retains its USD 5 conversation cap; the judge has USD 1 per judgment.
Codex/Kiro have no approved dollar ceiling: their time limits are not cost caps.
Independent authentication provisioning must precede the timed live batch when
that integration is implemented. SIGKILL/machine failure still needs residual
private-directory inspection before another batch.

## Manual procedure

Use Kiro IDE only for the three Kiro steps in T-051, T-052, and the spec-type
opening notes for `intake-bugfix` and `shared-dialogue-design-first`. Other
sessions use the automated runners after the launch blockers are resolved.

1. Resolve the host's instruction-isolation and permission blockers before starting a session.
2. Record the actual host version and model.
3. Read the session and every eval that names it.
4. Record the package tree, fixture tree, and session blob from the tested Git revision.
5. Copy the fixture into the authorized external batch workspace described by the approved design.
6. Apply workflow inventory copy entries in order when using a T-050 assembled workspace.
7. Preserve the fixture's stored approval hashes.
8. Initialize and commit the scratch repository.
9. Verify `git rev-parse --show-toplevel` names the scratch directory.
10. Verify `git rev-parse --absolute-git-dir` names that directory's own `.git`.
11. Open one new conversation for the session.
12. Before each turn, check its `expects` expression against the previous final reply.
13. Stop on a mismatch and record that one-based turn number as `brokenAt`.
14. Apply each turn's `edit` before sending its `developer` text.
15. Capture one final reply and one file-read list for each completed developer turn.
16. Record unknown reads as empty lists with `readMeasurement: not-measured`.
17. List observed instruction files and record whether that list is complete.
18. Capture `validate_spec.py status --json` from the scratch repository.
19. Store created and modified UTF-8 files as `files` entries with `path` and `text`.
20. Store surviving baseline-identical file paths in `unchanged`.
21. Omit deleted baseline paths from both lists.
22. Record an interrupted run with `notRun`, its reason, and no scores.
23. Start a continuation in a new conversation using its parent's finished workspace.
24. Set `continuesRun` to the parent's host, session, and numbered record.
25. Normalize workspace, plugin, repository, batch, and home roots throughout the entire record.
26. Validate the record against `schemas/result.schema.json` and `score.validate_record`.
27. Read the record for secrets and machine paths before storing it.
28. Save the next unused `results/<host>/<session>/<n>.json` number.
29. Score the record and retain it even when it fails.

`normalize` in `run_claude.py` recursively replaces roots inside messages, file
contents, paths, dictionary keys, and nested status. Use `<workspace>`, `<plugin>`,
`<repository>`, `<batch>`, and `<home>` as placeholders. Replace the longest root
first. Never copy authentication material or raw host streams into a record.
The run schema allows `status: null`; this is unavailable status, never proof of
cross-host equivalence. Binary files and symlinks are rejected by the current
capture implementation instead of being omitted silently.

The instruction collector must supply load-time SHA-256 values and an exhaustive
import list for each loaded path, for every turn. It must not infer those values
from a later disk snapshot or a model's own answer. `classify_instructions`
resolves paths before normalization and compares them with the initial fixture
or reconstructed parent plus explicit edits. Generated instructions in the same
session are not added to that expected baseline. The verified plugin is checked
separately and excluded from `instructionFiles`. Missing content or import
observations remain unknown; unsupported adapters never claim measurement.

Per-turn classifications are stored in one `specflow-evidence-v1: ` JSON line
inside `notes`, together with `configurationSha256` and `boundarySha256`.
These are source evidence, so changing them invalidates rubric reviews. The
result schema and its existing fields are unchanged.

## Scoring

```sh
python3 tests/specflow/evals/runners/score.py path/to/record.json
python3 tests/specflow/evals/runners/score.py --compare claude.json codex.json kiro.json
python3 tests/specflow/evals/runners/score.py path/to/record.json --evals tests/specflow/fixtures/results/evals
```

Exit 0 means every matching eval passed (or the compared status fields agree).
Exit 1 means a failed eval, broken session, not-run record, or unjudged rubric.
Exit 2 means unavailable evidence or invalid input. Comparison checks session and
revision identity before comparing each spec's `phase`, `artifacts`, `gates`,
`hold`, and whether `nextTask` is null. It ignores task titles.

Ordinary scoring clears any previous release claim. To recheck eligibility,
supply both `--candidate <manifest.json>` and `--boundary-proof <proof.json>`.
Scoring exit codes retain their original meaning; inspect `releaseEvidence`
separately. Neither option enables a host or overrides its preflight.

The maintainer's candidate manifest names `runtimeRevision`, `fixtureRevision`,
`sessionRevision`, and `evalRevisions` (a map of rule IDs to Git blob IDs).
The independently reviewed boundary proof names `scope: installed-host-boundary`,
`host`, `hostVersion`, `runtimeRevision`, `configurationSha256`, and `checks`.
Every name in `score.RELEASE_BOUNDARY_CHECKS` requires an object with literal
`passed: true` and a nonempty `evidence` reference to the observed proof. Those
references must be reviewed; the scorer cannot turn self-reported booleans into
measurements. Use synthetic sentinel targets, never credentials. The inventory's
`boundarySha256` is `score.evidence_digest` of that reviewed proof object.
The configuration fingerprint must cover effective settings, installed versions,
runtime executables, and the tool policy for the run; normalize only disposable
roots, never policy content.

`certify_release` rescans evals and judgments, checks frozen revisions, replays
expected instruction content from immutable Git inputs, checks imports and each
turn's inventory, verifies session completeness and status, and matches proof
identity/configuration. Shell-only proof, missing reviews, stale inputs, unknown
inventories, and taint remain ineligible. A failed parent prevents its dependent
session from launching. No current live adapter supplies a complete proof.

Unchanged files come from the recorded Git fixture tree, not the current fixture
directory. Continuations reconstruct their exact parent record. Keep the Git
objects and parent records available; unavailable evidence is an error.
`validation_*` assertions reconstruct the finished workspace and use the shipped
validator only when its clean package revision matches the record.

File and read paths are exact, workspace-relative names. Patterns are Python
regular expressions. Message `turn` indices are one-based. `before_turn: 2`
examines reads from turn 1 only. Unknown reads cannot pass either positive or
negative read assertions. An absent file cannot pass `file_lacks`.

Read measurement limitation (offline review, 2026-11-16): shell command
arguments and code-mode output are not filesystem access events. Even a
successful command can name unread files and read unnamed files through helpers,
imports, searches, shell expansion, aliases, or subprocesses. The adapters keep
such turns `not-measured`; they do not extract positive reads from arguments.
Codex's retained calls support manual review but cannot establish a complete
read inventory. Parsing more JavaScript shapes does not resolve this limitation.

Claude native `Read` needs a matching successful tool result; Kiro native `read`
needs completed status and a regular file. These record the named path only.
Aliases whose current resolved path differs leave the inventory incomplete;
a post-call filesystem lookup cannot establish a historical symlink target.
Search, edit/patch, and unknown tool calls also leave it incomplete. A failed or
missing read result is unknown, not proof of either reading or not reading.
The existing scorer requires a complete measured inventory for both read
assertion kinds, even when some successful native reads were retained. It gates
release eligibility through those assertions; sessions with no read assertion
are not globally rejected solely for unknown reads. No schema or acceptance
criterion was changed. A complete shell-read method still needs host or OS
access telemetry covering the tools and their descendants, with per-turn scope,
successful access outcomes, and path identity; the retained records lack it.

Feasibility check (2026-11-16, synthetic probe, QA log "Offline read-telemetry
feasibility"): no unprivileged route supplies that telemetry. APFS access times
miss `cp` and clone copies and name no process, so they are not used, also not
as a partial signal. The one complete source found is Endpoint Security
(`eslogger` with `open`, `mmap`, `clone`, `copyfile`, `fork`, `exec`, `exit`),
which needs root and Full Disk Access for the supervising terminal. It is not
run or integrated; using it is the developer's decision.

Question counting ignores fenced code and listed options. A consecutive run of
question marks ends one question. The total-count assertion sums the questions
across replies. A broken session fails every eval, including absence checks.

## Rubric review

`--judge-model <explicit-id>` invokes a text-only Claude judge with a fixed
prompt, no tools, a 120-second timeout and a USD 1 cap per judgement. Choose a
different model from the host under test. The actual reported judge model is
stored as `model:<id>`; missing model evidence or tools enabled rejects the result.
No live judgement was run during this implementation session.

The scorer stores model verdicts and reasons. For P PASS verdicts, it samples
`min(P, max(10, ceil(P / 10)))` without replacement, once per evidence digest.
No passes means no sample; fewer than ten means review all. Every FAIL and each
sampled PASS needs a human verdict. Require manual review of all rubrics when
`10 * wrong > sample_size`: one wrong of three escalates, one of ten does not,
two of ten do. Pending review leaves rubric scores failing. The policy version
in the digest invalidates older samples made under the smaller minimum.

Supply completed human judgements through `--review-file <file>`:

```json
{
  "evidenceSha256": "copy rubricReview.evidenceSha256 from the record",
  "verdicts": {
    "SR-DLG-003:1": {
      "verdict": "PASS",
      "judge": "human:developer",
      "reason": "Describe the evidence you checked."
    }
  }
}
```

Keys are rule ID plus one-based assertion number. The evidence digest binds the
review to source evidence, matching eval bytes, and sampling policy. Derived
scores, review state, and release eligibility are excluded, so marking eligibility
cannot invalidate its required human review. Changed instruction observations or
other source evidence still invalidate old judgments. Full manual judging uses the same format for every rubric. The
scorer never supplies a human judgement or waiver itself.
