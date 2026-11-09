# Portable Autopilot recovery

Authorized on 2026-11-09: “proceed to recovery”, then “well then we must finish portable autopilot”. This authorizes implementation and verification of the existing port, including bounded recovery revisions. It does not authorize publication, live installation, migration, source retirement, custody acceptance, force pushes or changing security controls.

## Authority and runtime

Load the user-global instructions from ~/.claude/AGENTS.md and this repository's AGENTS.md. Their standing autonomy applies to routine reversible work. Use the installed Autopilot workflow through the existing autocodex host adapter, including its canonical state writer and model-provider review policy. The portable package is the product being built; its intentionally unavailable entry points are not the build runtime. Never patch or run a loop in buvis/claude-autopilot. Never edit the installed plugin to work around a defect.

Preserve every skill-mandated task gate and isolated review lens. Native worker tiers follow the host mapping and PRD floors. Completion review runs in a fresh process after a committed build handoff. Review includes Alice consensus, Blake PRD-only blindness, and Bob doubt plus de-slop with complete rubrics; preserve any additional policy-required roles. Actual implementation models determine independent review providers. Try authorized alternative Anthropic routes on quota exhaustion; never switch routes to evade a permission denial, silently downgrade, or fabricate evidence.

## Admission and order

The old batch is closed and its state is archived. Six downstream PRDs remained blocked, not completed. The held v1 PRDs, all review evidence, deferred records and custody journal remain unchanged.

The two v2 PRDs are bounded recovery revisions of existing units, not retries that reset the old attempt counters:

- AP00018 v2 completes the controller kernel, preserving previously implemented behavior and closing owner/capacity failures plus final delivery evidence. It replaces the failed 40K planning premise with normally sized, bounded tasks. No increased prompt limit or omitted role is authorized.
- AP00014 v2 waits for AP00018 v2. It completes native host behavior, compatibility assets, guard enforcement, genuine isolated probes and truthful delivery evidence. Every retained v1 review finding needs a test-backed disposition. Reporting a capability as unavailable is honest but does not implement a mandatory feature.

Select through the installed workflow. Expected dependency order: 00018-v2, 00014-v2, 00015, 00019, 00020, 00021, 00016, 00017. The existing downstream PRDs retain their scope and gates. Reuse completed work after checking it, not by replaying implementation or importing historical completion flags into new tasks. Do not restore old archived state over a new batch.

Both recovery revisions retain full-lane reviews and an explicit three-cycle cap. If one exhausts its bounds, preserve its failure evidence and follow the existing park/recovery policy. This authorization does not permit creating v3, raising caps again or an unbounded repair loop.

## Custody and completion

AP00014 v1 has pending critical-on-master custody. Leave its marker and journal intact while repairing. No accept/revert/branch-and-revert decision is implied by this scope. Do not push while pending custody or failing required gates remain. The supported unattended entry explicitly reports pending custody and permits independent local work; use that documented path.

The implementation suite and repository validator must pass. Do not exempt the historical controller failures, broadly exempt AP00014 paths, weaken assertions, skip required scenarios, or repin old evidence to untested bytes. Preserve old receipts; record truthful successor evidence for ownership changes.

AP00019 already owns the drained-versus-ineligible behavior. Prove that an empty eligible set with remaining dependency-blocked PRDs reports blocked work. Until that implementation ships, report the current legacy driver's “drained” wording as no eligible work, not product completion.

Portable completion requires AP00017's real isolated Codex/Gemini profile and distribution evidence. Do not substitute Claude for the required Gemini certification role or claim success from mocked/static capability checks. Missing real-host capabilities block certification, while unrelated implementation may continue. Do not remove unavailable-entry gates ahead of the PRD that makes the corresponding operation executable.

Keep all work local. At the final boundary report completed PRDs, remaining blockers, exact verification results and any pending custody. The product is unfinished until its final certification gates pass.

## Baseline verification

### Reviewer transport recovery, 2026-11-09

The first session paused at host_per_task_review_transport because neither available Sonnet wrapper combined explicit effort, disabled tools and headless resume. This is a reversible host compatibility defect within the authorized recovery, not a new approval gate. The canonical personal wrapper in agent-skills now supports `--effort high -t "" -S UUID -f PROMPT -o OUTPUT` for fresh Pat reviews and `--effort high -t "" -R UUID -f DELTA -o OUTPUT` for resumed reviews. Use ~/.agents/skills/use-sonnet/scripts/sonnet-run.sh for these calls, retaining every existing nesting/permission guard; no installed-plugin or frozen-repository patch is involved. Never pass -a or -y for Pat.

Preserve the paused plan, batch ID, design reviews, attempts, committed characterization and pending custody. Task 9 is committed and marked completed, but its attempt has null review/verification fields. Reconcile and perform its outstanding mandatory Pat review from recorded diff and verification evidence before proceeding; do not replay implementation or fabricate a review stamp. Task 10 and the parent task 1 reconciliation remain pending. Resume build through the canonical state writer after the wrapper validation passes; do not reset tasks or caps.

Transport fix: agent-skills commit 3ce5d55. Its shell regression harness passed 36 checks (the six new cases failed before the fix). Skill validation passed, and braid check with the explicit canonical source reported zero drift. The installed Claude CLI help confirms the tools, effort and resume flags. The mandatory skills repository test run produced 4335 passed, 9 skipped, 1 failed in 338.36s: skills/glean/scripts/test_glean.py::test_scan_reports_a_file_the_host_will_not_stat_instead_of_crashing. That unrelated PermissionError is in unchanged glean code (`git diff HEAD -- skills/glean` was empty); no claim of an all-green skills suite is made. This failure is recorded for its owner rather than folded into the portable Autopilot recovery. This repository's validator passes (3 packages, 15 skills).

Before implementation on 2026-11-09, the unmodified production tree produced **20 failed, 1433 passed in 332.71s** with `mise exec -- uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q --tb=short`. Eight failures are in test_controller_capacity.py, seven in test_controller_owner.py, four in test_controller_owner_recovery.py, and one is test_helper_provenance_real.py::test_new_helper_files_are_owned_and_digested_from_current_bytes (CHANGELOG.md differs from its pinned receipt revision). This is a failing baseline, not an acceptance exemption.

Both recovery PRDs pass the create-prd grounding checker with zero blocking or unverified rows. Repository validation passes: 3 plugin packages and 15 skills. Recovery admission commit: eb54a3a.

## Unresolved questions

None needed to begin implementation. Real host capability availability is measured by probes; custody disposition remains a separate attended decision after concrete repair evidence exists.
