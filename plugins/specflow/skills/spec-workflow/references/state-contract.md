# State contract

How the agent reads and writes `.specflow.json`, and when it runs each helper operation. The helper is `scripts/validate_spec.py`, run from the repository root.

## The state file

`.specflow.json` sits in the spec folder and holds only what the files cannot show:

- `schemaVersion` (1), `specId` (the spec folder's name), `specType` (`feature` or `bugfix`), `profile` (`standard` or `quick`), `workflowOrder` (`requirements-first` or `design-first`), and `workflowVersion`.
- `artifacts.requirements`, `artifacts.design`, `artifacts.tasks`: each with `path`, `status` (`missing`, `draft`, `approved`, or `stale`), and `sha256`. An approved record adds `approvedSha256`, `approvedAt`, `approvedCommit` when the repository has a commit, and `upstreamSha256` when the artifact has an upstream artifact. A design approval adds `approvedCode`; a dependent approval may add `acceptedMarkers`.
- `hold`, optional: `{"status": "on_hold" or "abandoned", "reason": "...", "since": "YYYY-MM-DD"}`, set and cleared only on the developer's instruction.

It never holds the phase, a transcript, a prompt the developer typed, a secret, an absolute path, or a host session ID. A bugfix spec keeps its requirements record under `requirements` with the path `bugfix.md`.

Precedence: the Markdown controls content, `tasks.md` controls task progress, and state controls only approvals, accepted markers, and the hold. A hash mismatch makes state wrong, never the Markdown.

## When an approval holds

```text
approved := status == "approved"
            AND canonical hash of the current text == approvedSha256
            AND upstreamSha256 names every existing upstream artifact
            AND each named upstream hash == that artifact's current canonical hash
```

The canonical hash ignores line endings and trailing whitespace, and in `tasks.md` the checkbox state and each task's `Outcome:` and `Exception:` lines, so progress never stales the plan.

A changed artifact stales its own approval and every approval downstream of it:

| Order | Changed | Stale |
|---|---|---|
| Requirements-First | requirements | requirements, design, tasks |
| Requirements-First | design | design, tasks |
| Design-First | design | design, requirements, tasks |
| Design-First | requirements | requirements, tasks |
| Both | tasks (outside progress) | tasks; implementation stops |

Implementation never stales the plan by itself. When building shows an upstream error, correct that artifact; the normal staling follows.

## Reconciliation

`reconcile` reads the artifacts and the state, hashes the artifacts, propagates staleness, derives the phase, and evaluates spec dependencies. It writes only derived facts, each artifact's `sha256` and a `missing`, `draft`, or `stale` status, and never an approval, a marker acceptance, a code baseline, or a hold. It never creates a state file and never replaces a malformed one. Run it with `--dry-run` first, show the developer what it found, then run it to write once the reading is unambiguous or confirmed.

Recovery mode, when artifacts exist without `.specflow.json`: infer only what the files show, and ask the developer to confirm each approval you cannot prove. A recorded receipt (a dated approval in the intake item's `qa-log.md`) is such a proof only after the developer confirms it.

## Recording an approval

1. `validate_spec.py validate <spec-dir> --phase <phase>` reports no error for the artifact. For a design or a task plan, no marker of an upstream artifact is left without an acceptance by name. Any error, such as a code fence that never closes, stops the approval until it is fixed.
2. `validate_spec.py hash <artifact> --json` gives the values to record: `sha256`, the UTC time for `approvedAt`, the current commit for `approvedCommit` when one exists, and `workflowVersion`.
3. For a design in a Git repository, `validate_spec.py code-baseline <spec-dir> --paths ...` with the explicit file paths of the design's placement section gives `approvedCode`. When the placement is ambiguous or missing, the agent writes `{"status": "not_checked", "reason": "<why>"}` itself; for a design that says it touches no file, `{"status": "not_applicable", "reason": "<the design's reason>"}`.
4. After the developer's explicit answer, the agent writes the approval fields, and any markers accepted by name, into `.specflow.json`. Resume never refreshes a code baseline without reapproval.

Copy every value from the helper's output; compose none. The approval record takes `sha256` as both `sha256` and `approvedSha256`, and `upstreamSha256` when `hash --json` gives it. An accepted marker is recorded as `{"artifact": "<upstream artifact>", "line": "<the exact marker line>"}` in `acceptedMarkers`; the reason for accepting it goes to the approval summary and the Q&A log, not to state.

## When each helper operation runs

- `status`: at the start of every invocation, before anything is proposed. It writes nothing, and it is all a status request runs.
- `reconcile --dry-run`: on resume, before the summary of the resumed state.
- `reconcile`: after that summary, to write the derived facts; never before it.
- `validate`: before each approval, and before implementation starts. On an intake item (`--phase intake`): after a sketch spike writes or changes its mockups, before the agent presents them.
- `next-number`: when a new idea claims a spec number.
- `hash` and `code-baseline`: at an approval, as above. `hash --raw <file>` before a write, see next.

## The check before a write

At the start of an operation, note `hash --raw` of each file you will change, `.specflow.json` included, and compare it again immediately before writing. A difference stops the write: show the developer what changed and wait. The canonical hash is not used for this, since for `tasks.md` it ignores the progress an implementation writes. One writer per spec is the contract; there is no lock.

## Without Python 3

The skill is read-only. It reports what it can read, drafts artifacts, and may create the spec folder with `.config.kiro`; it writes no `.specflow.json` and records no approval, and it says why and that installing Python 3 fixes it. It writes the three confirmed intake choices (spec type, workflow order, profile) into the intake item's `qa-log.md`, where recovery mode on the next host finds them. Before it overwrites a file it re-reads it and stops if the content differs from what it read.
