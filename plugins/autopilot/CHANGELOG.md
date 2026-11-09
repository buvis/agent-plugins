# Changelog

## [Unreleased]

### Added

- **autopilot**: Add static host adapters for Claude, Codex and Gemini with a declared-capability contract and generated compatibility bundles. A declared capability is one the adapter implements, so the contract and the bundles are identical on every machine; auth presence appears only in per-run probe evidence, never in a committed artifact. Claude declares identity, delegation, isolation and interception; Codex declares isolation only; Gemini declares none, because neither host implements native session identity or in-session delegation yet. Capability status is a static observation (binary on PATH plus auth presence), never a live invocation. No host execution or certification is claimed.
- Add stdlib-only, read-only dirty-tree checks and verify log-sink refusal with a descriptor-pinned sink opener, keeping the pinned semantics.
- Add the advisory local AP00012 review evidence checker that validates policy invariants, closed wire shapes, and every semantic defect against an independent expected context, without certifying host execution.
- Add stdlib-only session helpers that read consolidated review findings, strip finding-line leads, and group findings into rework tasks with the pinned semantics.
- **autopilot**: add packaged review staging helper (review_stage)
- Add a stdlib-only review-close helper that prepares task and decision proposals from validated review evidence.
- Add stdlib-only cap-check and custody proposal helpers.
- Add a stateless optional catchup probe for gh and engram.
- Add a bounded verification runner and artifact reuse check.
- Add versioned local facade operations for review staging, grouping, evidence checks, close proposals, catchup probes and verification, with a controller-required refusal.
- Add helper provenance (`helper_dispositions`) to the source map, which keeps controller-owned functions controller-only and reassigns no regression owner, plus a README section on the local helper operations and their limits.
- Add the bounded public controller CLI with private workflow bootstrap, authenticated exact replay, read-only snapshots, installed contract metadata, and durable matching-request credential-intent recovery.
- Add read-only explicit project-root resolution with descriptor-based private path and fixed artifact alias checks.
- Add the locked, atomic controller state store with fsynced state/backup publication, exact failure repair, revision checks, artifact alias guards, directory binding, and security-identical offline restore.

- Add the versioned controller state schema with bounded JSON decoding and isolated state creation and validation.
- Add read-only local PRD prerequisite diagnostics based on completed PRD filenames.
- Add the local contract-capabilities and canonical policy-export facade, with packaged-policy digest and integer-domain checks and a delegating maintainer exporter.
- Add the explicit pinned-source provenance audit for source files, asset sections, behavior anchors, and regression identities and digests.
- Add 55 self-contained golden review evidence fixtures and alternate policy binding, covering complete lane rosters, fallback and retry histories, stale bindings, input isolation, attribution, artifacts, and rubric verdicts. No host execution or certification is claimed.
- Add the draft 2020-12 review evidence schema and expected-context definition, with closed wire shapes and conditional validation. No host execution or certification is claimed.
- Add gated review policy foundation data with pinned source bindings and test-only dependencies. No host execution or certification is claimed.
- Add the gated package README with preserved historical source sections, current local facade usage, delivery receipts, and a dedicated Python 3.12 integration CI job. No host execution or certification is claimed.

### Fixed

- **autopilot**: rotate owner leases and operator credentials recoverably, retaining exact receipt replay without restoring retired mutation authority.
- **autopilot**: restore transaction publication guard checks at every durability boundary, preserving exact state and backup rollback when evidence changes.
- **autopilot**: `--verify` accepts a relative `--project-root` again and judges it exactly as its absolute spelling, instead of refusing every output path it resolves with `unsafe-artifact-path`.
- **autopilot**: `--verify` proves both its log sink and its result-artifact sink openable before it spawns the child and judges each sink by the file it actually opened; when the spawn fails, an existing log and result artifact stay byte-identical and a log this run created is removed; it reports a sink open, write or close failure as its own controlled error with the child killed, stops the child's leftover processes when a sink fails late, and removes only a leaf it created; `--export-policy --out` refuses a reader-less FIFO instead of hanging and refuses up front where `O_NOFOLLOW` is missing; the log sink judges containment before it reads a Git pointer.
- **autopilot**: `--verify` removes only the result artifact that its own failed run created; a file that took the artifact's name during the run, a leaf that became a directory, or a parent that became a symlink is left untouched and never replaces the run's own reported failure.
- **autopilot**: after a failed result-artifact write or close, `--verify` empties (or makes unparseable) the written file wherever it was moved, and reports in its reason when even that fails. A write that failed before it began leaves an existing artifact's earlier record in place.
- **autopilot**: `--verify` and the log-sink check judge an output path by its components after the leading spelling of the project root: any symlink below the root (including one that leaves the project and returns, or one to the root itself) or a `..` component below the root is refused with `unsafe-artifact-path`, whichever way the root is spelled; a symlinked ancestor of the root stays allowed.
- **autopilot**: `--verify` and the log-sink check no longer read a nested repository's Git pointer.
- **autopilot**: review staging refuses a destination whose Git check cannot answer, refuses a reviewer whose grant omits the PRD instead of inlining an empty one, and fills the shared context file with granted input kinds only.
- **autopilot**: review staging accepts a clean destination outside any repository under a non-English Git locale, writes no context content when no reviewer reads the shared context, and reports a missing PRD grant in the standard refusal shape.
- **autopilot**: session helpers refuse hardlinked policy outputs, case aliases of verification inputs and worktree Git pointers, and external Git metadata staging roots; failed process starts preserve outputs and return a controlled report.
- **autopilot**: staged context obeys every input-kind grant, tail sweeps accept selected finding subsets while preserving attribution checks, and attempt validation uses memory bounded by the submitted history.
- **autopilot**: `--verify` log-sink validation opens no file it refuses by location and refuses a path under a not-yet-created directory of a nested repository; review-close refuses a row whose issue differs from the review table and rejects malformed carry snapshot tasks.
- **autopilot**: review staging given a subdirectory as `project_root` writes its artifacts under the repo root, not a stray `docs/dev/tmp/` tree in that subdirectory.
- **autopilot**: malformed `--group-findings`, `--prepare-close` and `--stage-review` request values exit 2 as usage errors instead of crashing.
- **autopilot**: review staging and `--export-policy` refuse live workflow state in any spelling case, and staging applies the tracked-file, live-state and symlink checks to artifact roots outside the project.
- **autopilot**: a staged reviewer prompt omits the diff, pack and history its manifest does not list.
- **autopilot**: a staged reviewer prompt reaches pack findings and settled history only through a per-job context file that its manifest allows.
- **autopilot**: `--verify` refuses a log or artifact path that is an argv input file, and a modified store file named by a tracked product symlink makes the artifact non-reusable.
- **autopilot**: review staging refuses a destination with its standard controlled refusal, instead of a traceback, when the git-dir check times out or git cannot start.
