# Scenario records and manual runs

T-056 is **incomplete**. The scorer and shared batch machinery have deterministic
tests. The Claude entry point records `notRun` and exits 2 before starting a host.
Codex and Kiro adapters and the three-host live self-check are still outstanding.
Synthetic records under `fixtures/results/` are instrument tests, never release
evidence. No instruction-isolation choice or evidence waiver has been granted.

## Launch blockers

- Claude: the 2026-11-09 reference/status permission denial must not be retried
  through another permission mode. Instruction isolation is also unproven.
  See `docs/dev/project-management/plans/specflow-release-fast-path.md`, section 8.
- Codex: the developer must choose instruction-file isolation before a batch.
  A temporary home must contain only sign-in and the installed plugin, pass a
  package-tree comparison, and be removed on success and failure. No setup,
  sign-in copy, or personal instruction-file move was attempted in T-056.
- Codex and Kiro: installed `codex exec --help`, `codex exec resume --help`, and
  `kiro-cli chat --help`, read on 2026-11-10, expose no per-session spending cap.
  The design requires one on every runner. A timeout is not a spending cap.
  Resolve that contract before enabling either adapter. Kiro also needs proven
  instruction isolation and permissions restricted to the scratch workspace.
  The [Kiro headless documentation](https://kiro.dev/docs/cli/headless/) documents
  scoped permissions and structured output, but does not establish those
  properties for this machine's configuration.

The shared engine sets a 600-second turn timeout and a USD 5 Claude session
budget. Its Claude permission mode is `default`; it grants no additional tools,
directories, or permission bypass. Its preflight deliberately refuses launch.
Removing that refusal requires implementing and verifying the missing controls,
not an undocumented command-line override. No stored run is marked release
evidence automatically.

## Manual procedure

Use Kiro IDE only for the three Kiro steps in T-051, T-052, and the spec-type
opening notes for `intake-bugfix` and `shared-dialogue-design-first`. Other
sessions use the automated runners after the launch blockers are resolved.

1. Resolve the host's instruction-isolation and permission blockers before starting a session.
2. Record the actual host version and model.
3. Read the session and every eval that names it.
4. Record the package tree, fixture tree, and session blob from the tested Git revision.
5. Copy the fixture into a new directory under ignored `docs/dev/tmp/specflow/evals/`.
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

The scorer stores model verdicts, reasons, and a random 10% sample of PASS
verdicts, rounded up per run. Every FAIL and each sampled PASS needs a human
verdict. More than 10% disagreement in the sample requires human review of every
rubric in that session. Pending review leaves rubric scores failing.

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
review to the run and matching eval bytes. A changed run or eval invalidates old
judgements. Full manual judging uses the same format for every rubric. The
scorer never supplies a human judgement or waiver itself.
