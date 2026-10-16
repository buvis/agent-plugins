# Validation rules

Structural rules: the files alone prove each one, so the helper enforces it and no judgment is needed. `validate_spec.py validate <spec-dir>` reports a broken rule as a finding with the file, the check name given in brackets below, and the fix. An `error` makes the run fail; a `warning` never does. Inline code and fenced blocks are skipped wherever a rule says "outside code".

## Artifact text

- [SR-VAL-001] An artifact holds no `TBD`, `TODO`, `???`, or bare `N/A` outside code. Only `design.md` marks a section that does not apply, as `Not applicable: <reason>`, and the reason is never empty; the other artifacts leave such a section out. (`placeholders`, error)
- [SR-VAL-002] Before an artifact is approved, validation lists every open marker of the artifacts upstream of it in the workflow order: a `(guess)` outside code, a list item under `## Unresolved questions`, or a list item under `## Open decisions`. A marker stays open until the developer resolves it or accepts it by name on that approval, and each finding names the upstream file, since the marker is a question to ask, not a defect of the artifact being approved. (`open-markers`, error)
- [SR-VAL-003] A home-directory path, an absolute path, or a `[[...]]` link in an artifact gets a warning, because it does not resolve on another machine: write a repository-relative path, or name the source in words. (`portable-links`, warning)
- [SR-VAL-004] An artifact whose code fence never closes fails validation, because fence tracking decides what the hash and the scans leave out; no approval of it is recorded until the fence is closed. (`closed-fences`, error)
- [SR-VAL-005] A requirement in `requirements.md` with no `Source:` line gets a warning; a Kiro-made document has none, so the warning never blocks. (`requirement-source`, warning)

## Artifact structure

- [SR-VAL-006] Each requirement starts with a stable ID heading, used once, and holds at least one numbered acceptance criterion; a `bugfix.md` holds its three behavior sections, each with clauses numbered in sequence and in the pattern of its section. (`requirement-ids`, error)
- [SR-VAL-007] Each task has a stable ID used once and a well-formed checkbox, depends only on tasks above it, and carries `Requirements:` and `Verify:` lines. (`task-structure`, error)
- [SR-VAL-008] Every requirement is cited by at least one task, and a task cites only requirements and criteria its spec holds. (`requirement-coverage`, error)
- [SR-VAL-009] The artifacts the phase needs exist and read as UTF-8 text, and an intake item holds its `idea.md`. (`required-files`, error)

## Numbers, sources, and folders

- [SR-VAL-010] No spec number is used by two intake items or by two spec folders. (`number-clashes`, error)
- [SR-VAL-011] The requirements artifact carries a `Sources:` line that names the intake item with the spec's own number. (`sources-line`, error)
- [SR-VAL-012] Validation fails while specs sit in a real `.kiro/specs/` folder and the configuration names another specs folder, and while version control ignores the specs folder. (`specs-folder`, error)

## Dependencies, gates, and state

- [SR-VAL-013] A `Depends on:` declaration sits where the grammar puts it, appears once, and lists references that each resolve to one readable spec; self-reference and cycles are reported with the cycle path. (`spec-dependencies`, error)
- [SR-VAL-014] Implementation is refused while the task plan is not approved, an upstream artifact is stale or carries a marker no approval accepted, or a prerequisite spec is not complete; a change to the design's placement files since its approval gets a warning and closes no gate. (`gates`, error)
- [SR-VAL-015] A task that cites a criterion of another spec names a spec on its own `Depends on:` line, and a requirement and criterion that spec holds. (`cross-spec-references`, error)
- [SR-VAL-016] `.specflow.json` passes the state schema of its version, so each approval records its time, its hash, and the commit when one exists. (`state-valid`, error)
- [SR-VAL-017] The status output names each unfinished or invalid prerequisite as an implementation blocker, with its reference and reason, and offers no next task while one remains. (helper tests)
- [SR-VAL-018] The status output reports a change to the design's placement files as an advisory warning that closes no gate. (helper tests)
