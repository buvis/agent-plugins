CLOSURE | resolved | "plugins/autopilot/CHANGELOG.md:35: ... describes a test-only change under Fixed. ... Bullet 33 and README:297 likewise restate implementation mechanics (pinned descriptors, inode matching) rather than the user-visible effect, and the README does not document the empty-log residue after a failed spawn." | The test-only "attempt validation holds its memory bound" bullet is deleted. CHANGELOG bullet 33 and the README now say "removes only the result artifact that its own failed run created" with no descriptor or inode wording. The README adds "a run log that did not exist before stays absent, and a run log that did exist keeps its bytes", so an empty left-behind log is not presented as a feature.

CLOSURE | resolved | "00013-helper-recovery-v2.md:22: The recovery report never states the actual measured peak ... record the number with the exact command" | The new "Attempt-validation allocation peak (measured)" section gives the exact `python -I docs/dev/tmp/ap13-allocation-probe.py` command, exit 0, and verbatim output. That output has plain peak 95314 against ceiling 1000000 and injected peak 1695370. The section states that the probe is scratch-only and untracked, and the numbers match the recorded verification block.

CLOSURE | resolved | "00013-helper-delivery-receipts.json:33: Receipt provenance records the alias, not the served model: `implementation.model: "opus"` ..." | `implementation` is split into `build_lane` (claude-opus-5, high), `rework_lane` implementor (claude-sonnet-5-5), Pat (claude-sonnet-5-5) and coordinator (claude-opus-5). Task 6's implementor model and the Pat effort are marked "not captured". The source map was regenerated with `--check` passing, and the 23 changed lines are exactly the hash and revision fields.

MEDIUM | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:81 (also 00013-helper-recovery-v2.md:3) | The receipt scope says the 668-pass evidence was "measured against packaged revision 0ed4c17", and the report's first line calls 0ed4c17 the tested revision. The recorded verification says the coordinator took the 21-file run before this task's edits. 0ed4c17 is the README/CHANGELOG edit commit, so it did not exist when the run happened. The T1-T4 precedent disclosed the same gap ("evidence commit 9e89a59 ... product bytes identical to the tested revision"). This diff states no such disclosure for the new pin, and the provenance tests check hashes, not this claim. | Add one sentence to the receipt `scope` and the report header. It should say which commit the 21-file run actually ran at, and that 0ed4c17 differs from it only in `plugins/autopilot/README.md` and `CHANGELOG.md`. Verify that product-byte identity before writing it, and state it only if it holds.

LOW | plugins/autopilot/CHANGELOG.md:34 | The unchanged bullet "`--verify` leaves no log behind after a failed spawn" reads as if a pre-existing log is removed. Bullet 32 and the new README text say an existing log keeps its bytes and only an absent log stays absent. | Reword to "a log that did not exist stays absent after a failed spawn".

LOW | docs/dev/project-management/autopilot/reports/00013-helper-recovery-v2.md:221 | The sentence "This one replaces the committed framework-selftest that cycle-1 rework task 7 deleted" says a scratch, untracked probe replaces a committed test. The probe is not a test and cannot guard a regression. The sentence "The committed test keeps only the plain measurement" has no support in the recorded verification. The probe's output cannot be reproduced from the repository, because only its path is recorded. | Drop the "replaces" wording. Record the probe's sha256 or inline its source so the command is reproducible. State the committed test's name only if it can be cited.

LOW | docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json:57 | The `effort` field mixes served values (build lane transcript `high`), configured values (`medium (agent frontmatter)`, `high (recorded in the loop session brief)`) and "not captured". The recorded verification confirms only the model ids. Nothing is falsely claimed, but a consumer reading `effort` alone cannot tell served from configured. | Rename the configured values to `effort_configured`, or prefix them with "configured:", so only served effort appears under `effort`.

---

Coordinator disposition (not part of Pat's reply):

- The MEDIUM is CONFIRMED and fixed through one Ivan retry dispatch. Verification
  before the fix: `git diff --name-only 016b6b3..0ed4c17` lists only
  plugins/autopilot/CHANGELOG.md and plugins/autopilot/README.md, and the same
  diff restricted to `tests/`, `plugins/autopilot/scripts/` and `tools/` is
  empty, so the 21-file measurement does apply to the pinned revision's product
  bytes once that is stated.
- The three LOW findings are recorded and NOT fixed at this step. LOW is noted
  and proceeds; cycle 2's lenses adjudicate them on the full diff.
