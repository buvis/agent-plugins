# Closeout external prerequisite audit — 2026-11-04

Read-only inspection of buvis/ovcaq at
91ce9b6f0b6d74bda1b3be23421e84baa8986f68 (clean working tree).
OV00059 mixed-driver-jobs and OV00060 supervisor-sync remain in backlog;
OV00062 process identity is done. AP00017 profile-conformance requires actual
Codex/Gemini standalone and managed lifecycle receipts, without Claude fallback
or unavailable-as-passed evidence. OV00059 owns the Gemini driver and routing;
OV00060 explicitly exports those real managed receipts for AP00017.
The missing external managed capability blocks complete managed certification,
not unrelated AP implementation or standalone checks. No external repository
was edited and no host/conformance tests were run for this audit.

Future wave preparation: scratch docs/dev/tmp/wave-release-checks matches the
10 current validate.yml checks. Copy and commit as dev/bin/release-checks on
integration branch after closeout before wave base; do not run scratch copy
because its relative cd resolves to docs. Integration worktree
~/git/src/worktrees/agent-plugins/closeout makes launcher-generated siblings
stay under the authorized worktree root. AP13/AP18 must be done and WIP empty
before lane seed, since launcher retains inherited tracked PRDs. Assembly
requires drained/dead lanes; fresh wave review precedes land; land ff-only
updates integration root, then merge master ff-only, normal push, green CI.

The required OVCAQ source files src/ovcaq/drivers/gemini.py and
src/ovcaq/runtime/job_router.py were both absent at the audited revision.
Local agent-plugins origin/master had no divergent commits after a normal
fetch. This is a remote-state observation, not authorization to bypass tests.
