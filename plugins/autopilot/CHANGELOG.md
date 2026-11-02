# Changelog

## [Unreleased]

### Added

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

- **autopilot**: `--verify` log-sink validation opens no file it refuses by location and refuses a path under a not-yet-created directory of a nested repository; review-close refuses a row whose issue differs from the review table and rejects malformed carry snapshot tasks.
- **autopilot**: review staging given a subdirectory as `project_root` writes its artifacts under the repo root, not a stray `docs/dev/tmp/` tree in that subdirectory.
- **autopilot**: malformed `--group-findings`, `--prepare-close` and `--stage-review` request values exit 2 as usage errors instead of crashing.
- **autopilot**: review staging and `--export-policy` refuse live workflow state in any spelling case, and staging applies the tracked-file, live-state and symlink checks to artifact roots outside the project.
- **autopilot**: a staged reviewer prompt omits the diff, pack and history its manifest does not list.
- **autopilot**: a staged reviewer prompt reaches pack findings and settled history only through a per-job context file that its manifest allows.
- **autopilot**: `--verify` refuses a log or artifact path that is an argv input file, and a modified store file named by a tracked product symlink makes the artifact non-reusable.
