# AP 00013 v2 agent self-debug report

## Failure Capture
- Session / task: planner 7effadc7-bbde-4651-8261-c38b4c067398; work session 6c916023-47fa-4ce2-b40b-ad99805df362; task 1.
- Goal in progress: execute the four-task correction with the PRD's explicit Opus worker floor and full review pipeline.
- Error: all four compiled task records said Sonnet. Task 3 was also incorrectly qwen-eligible. Tess dispatched as worker-sonnet/model sonnet, actual claude-sonnet-5-5, row cd542dc7.
- Last successful step: Tess returned tests; shape/style checks passed. No product implementation or test commit occurred.
- Last failed tool / command: the planner's four classify_tier.py invocations omitted --default-model opus. Their line estimates were 110, 150, 20, 40; each used the matching docs/dev/tmp/plan-N-files.txt and plan-N-text.txt.
- Repeated pattern seen: coordinator assumptions were not checked against actual persisted metadata. Earlier direct implementation was a separate protocol error; the corrected Opus session followed the wrong saved tier. The root coordinator failed to detect that metadata discrepancy before launch.
- Context pressure: final recorded counter snapshot {"count": 66, "session": "6c916023-47fa-4ce2-b40b-ad99805df362", "usage": 221259}. No context-limit or quota failure caused this discrepancy.
- Environment assumptions to verify: PRD frontmatter has default_model: opus; the installed classifier supports --default-model; state metadata drives the worker persona/model and Devon gate.

## Diagnosis

This is a deterministic plan-compilation/policy error, not provider failure.
Rerunning all four exact classifier calls with --default-model opus returned
model opus, tier_reason floor, exit 0 for each. The task floor also makes
qwen_eligible false with reason tier. The procedure is documented in the
installed plan-tasks/SKILL.md section 4.7. No installed runtime was patched.

## Recovery Action
- Diagnosis chosen: omitted model-floor argument, followed by missed validation of compiled state.
- Smallest action taken: interrupt the active loop (exit 130), preserve the lower-tier test draft and telemetry, correct only the four task tier/Qwen fields through task-set-meta, and return task 1 to pending.
- Why this is safe: no production changes or task completion exist; requirements, design, task dependencies, estimates and cap remain unchanged. Preserve the tests as evidence, outside the active test tree; fresh Opus Tess must author from requirements without the abandoned implementation or lower-tier draft.
- What evidence would prove the fix worked: direct assertions that every task has model opus, floor reason and Qwen disabled; then a new measured Tess dispatch with explicit worker-opus/model opus and actual model metadata, followed by the required quality, Devon, red, Ivan, deslop and Pat gates.

## Agent Self-Debug Report
- Session / task: AP 00013 v2 orchestration recovery, task 1.
- Failure: a required Opus test-authoring step ran at Sonnet due to incorrectly compiled metadata.
- Root cause: planner omitted the floor flag; root trusted the stated plan instead of validating its persisted tiers.
- Recovery action: preserve evidence, correct metadata through the supported writer, validate it before relaunch, and require observed dispatch provenance.
- Result: partial; metadata correction is pending the checks below and no feature work is certified.
- Token / time burn risk: blind relaunches repeat invalid work. Do not retry the same route without a discriminating metadata and dispatch check.
- Follow-up needed: finish all four tasks and the fresh five-lens review, then AP 00018 and the backlog. This draft does not satisfy the Tess gate.
- Preventive change to encode later: AP 00015's plan/work port should reject compiled tiers below the PRD floor before dispatch. This is a durable finding, not a patch to the frozen or installed runtime.

## Preserved evidence

Lower-tier test draft: 00013-v2-lower-tier-tests.py.txt, sha256
2046482de606ff177640b30e91bb200c1ed940b32c562be07f685adb91fc74ef. Actual Tess model was verified from
agent-aee39165a838fc898.jsonl. Native telemetry row cd542dc7 correctly records
that its process finished; that does not certify the required tier. Do not
rewrite that event or claim it was an Opus dispatch. No Ivan implementor
attempt occurred, so the aborted coordinator run remains this linked report,
not a fabricated worker attempt. No push occurred.
