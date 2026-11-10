# Scenario records and manual runs

T-056 is **incomplete**. Requirements, design, and tasks were approved on
2026-11-10. The scorer and shared batch machinery have deterministic tests;
synthetic records under `fixtures/results/` are never release evidence.
Claude and Codex entry points still record `notRun` and exit before a live host.
Codex conversation handling, the Kiro adapter, host policies/instruction capture,
release-eligibility enforcement, and the three-host live self-check remain.

## Approved environment and remaining proof

The canonical contract is 00009's `design.md`, Eval runners of T-056. D11's
isolated Codex home is decided; no personal-file move or tainted-evidence waiver
exists. The approved revision replaces active-sign-in copying with independent
login directly into the batch home. `temporary_home` accepts a supervisor
provisioning callback, never an existing credential path; it checks private,
regular, unlinked authentication state before installation. The live provisioner
is deliberately unimplemented until the isolated launch route is verified.
Synthetic tests cover installation, mismatch, errors, interruption, and cleanup.

The approved scratch layout is an external private batch under the macOS system
temporary root, containing `workspaces/`, `resources/`, and `control/`. The old
repository-local root cannot support the required Git initialization under the
active Seatbelt profile. The current blocked engine still uses that legacy root
for synthetic checks; external layout and installed-host boundary proof remain
to be implemented. Do not remove the preflight refusal merely to try a session.

The approved Claude route uses an isolated configuration home, setup-token auth,
verified fixture settings, and an explicit plugin read directory with native-tool
and shell write denial. Codex needs restricted reads excluding its credential
home except the installed plugin subtree. Kiro needs proven resource-inheritance
and tool restrictions. Check effective settings, complete loaded-instruction
inventory, required helper/reference access, denied credential reads and plugin writes,
and cleanup before admitting release evidence. Never infer isolation from a
model's own statement or from successful synthetic tests.

On 2026-11-10, `codex sandbox macos --help` failed with
`sandbox-exec: sandbox_apply: Operation not permitted`, including the normal
escalated attempt. The developer attempted to approve broker request
`de45a93cb7035582b243fcb97d9d1c5e`; warrant refused because the resolved
mise-managed Codex executable is outside `trusted_exe_roots`. The request is
refused, not pending, and did not execute the diagnostic. Do not retry it through
a wrapper, relocate the binary, or broaden broker trust as part of this task.
The developer subsequently ran that command outside `run-agent` and received
`sandbox-exec: execvp() of 'macos' failed: No such file or directory`. The command
was incorrect for installed 0.167.0: local `codex help sandbox` succeeds and
shows `codex sandbox [OPTIONS] [COMMAND]...`, with no `macos` subcommand. Thus
the old invocation tried to execute a program named `macos`; it was not a help
check. The initial outer-profile denial remains valid, but does not establish
that the installed sandbox is unusable outside that profile.

The corrected developer-run launch check is
`codex sandbox -- /bin/echo specflow-sandbox-ok`, outside `run-agent`, using the
installed executable directly. Expected output is `specflow-sandbox-ok` with
exit 0. It uses no model or authentication. This checks command launch only;
restricted-read policy, write denial, instruction inventory, and all boundary
sentinels remain unproven. No live runner is enabled by this check.
The developer subsequently reported the expected marker. This confirms command
launch outside the outer profile; the pasted prompt's leading status is not a
separately measured exit code for that command.

### Synthetic shell boundary probe

`run_codex.py --probe-boundary --codex <installed-executable>` now combines the
next shell checks in one developer-run command. Run it outside `run-agent` from
the repository root, using Python 3.10 or later. It creates and removes its own
private system-temporary batch. It never logs in, loads real authentication,
calls a model, changes broker trust, or enables the live runner.

Start the supervisor with an explicit environment, because it rejects inherited
`GIT_*` settings before setup. Resolve Python through mise before clearing the
environment; invoking `mise exec` inside the cleared environment could add
settings again. Keep the caller's shell configuration unchanged:

```sh
/usr/bin/env -i HOME="$HOME" PATH="/usr/bin:/bin" "$(mise which python3)" -B tests/specflow/evals/runners/run_codex.py --probe-boundary --codex <installed-executable>
```

The developer's first probe invocation stopped at the inherited-Git guard. No
batch or sandbox was created. The revised launch prefix was checked separately:
Python 3.15.2 starts with no inherited `GIT_*` variables. Actual boundary execution
still requires the developer's terminal outside `run-agent`.


The probe verifies a copy of the plugin against its committed tree, creates an
independent Git workspace and an empty Codex home, and generates a candidate
[permissions profile](https://learn.chatgpt.com/docs/permissions). It requests
strict configuration and inclusion of managed configuration. Runtime reads are
limited to platform defaults and the selected Python installation; workspace
writes and plugin reads are explicit. The generated policy is reported, not
claimed to be an independent dump of effective settings.

Eleven checks cover workspace read/write, plugin read, helper status, denied
control/home/other-workspace/temporary-sentinel reads, plugin writes, and symlink
read/write attempts. Reads and writes use Python and child shell tools; only
EACCES/EPERM satisfies a direct denied operation. Missing files, malformed or
incomplete reports, nonzero sandbox exit, and failed cleanup cannot pass. The
home sentinel is inside the disposable Codex home; no real personal file is a
test target. A real-home deny rule is generated but not independently probed.

Output is one JSON diagnostic with versions, package/policy/probe fingerprints,
normalized generated policy, each check, and cleanup. Exit 0 means these shell
checks passed; exit 1 means the report failed; exit 2 means setup was unavailable
or interrupted. The probe has a 180-second total deadline and reuses process-group
cleanup. Its report always has `releaseEvidence: false`: native Codex file tools,
loaded-instruction inventory, network enforcement, independent authentication,
and the live adapter remain unproven. Rerun neither the refused broker request
nor sandbox execution from the outer-profile agent session.


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

Unchanged files come from the recorded Git fixture tree, not the current fixture
directory. Continuations reconstruct their exact parent record. Keep the Git
objects and parent records available; unavailable evidence is an error.
`validation_*` assertions reconstruct the finished workspace and use the shipped
validator only when its clean package revision matches the record.

File and read paths are exact, workspace-relative names. Patterns are Python
regular expressions. Message `turn` indices are one-based. `before_turn: 2`
examines reads from turn 1 only. Unknown reads cannot pass either positive or
negative read assertions. An absent file cannot pass `file_lacks`.
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
