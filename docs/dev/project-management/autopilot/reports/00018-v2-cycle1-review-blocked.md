# AP00018 v2 cycle 1 review capability pause

The required independent review could not be certified. State is paused at
`host_review_capability`. No completed review artifact, convergence, rework task,
cap change, or backend substitution was recorded. The PRD remains in `wip/`;
batch `202611090642`, cycle 1, cap 3, work base and all 11 completed tasks remain.

Implementation provenance is audited in
`00018-autopilot-controller-kernel-v2-implementation-models.json` and its sibling
Markdown file. The driver validated 37 log-backed evidence rows and required both
Anthropic and OpenAI three-lens rosters. Current attempt model/provider fields
already agreed with the observed logs. The missing cycle field was initialized
to the source's initial value 1 before dispatch; no prior cycle was reset.

All six reviewer processes were awaited. Their terminal statuses and dispatch
IDs are in `00018-v2-cycle1-dispatch-results.json`. Every dispatch row was closed
as an unusable review. There were no reviewer permission denials or network
failures. No launcher guards or permission settings were removed.

| Provider | Lenses | Requested | Observed result | Certification |
| --- | --- | --- | --- | --- |
| Anthropic, Kiro | Alice, Blake, Bob | Opus/xhigh | `claude-opus-5.5`, effort `medium`; helper exit 1 | Rejected |
| OpenAI, Codex | Alice, Blake, Bob | `gpt-6.1-sol`/high | Explicitly reported unread inputs; helper exit 0 | Rejected for missing coverage |

Kiro stderr reports `failed to set effort 'xhigh'`. Raw configuration updates
record medium. The later configuration advertises effort levels, so this evidence
does not prove that the model itself lacks effort support; it proves that this
invocation did not apply the required setting. Exact raw lines and hashes are in
`00018-v2-cycle1-effort-failure-evidence.json`. Original JSONL/stderr remain intact.
Extracted final texts end in `.invalid-effort.txt`; they are not accepted reviews
and have no successful Anthropic receipt. The helper correctly refused them.

The coordinator incorrectly prepended the Kiro/Copilot-only read/glob/grep policy
to the OpenAI prompts too. Those sessions expose shell-based filesystem tools,
not tools with those names. All three correctly reported unavailable inspection;
their failing rubric verdicts are infrastructure failures, not verified product
defects. Their immutable receipts prove transport completion only. They cannot
satisfy the provider review guard. No product repair was started from them.

Original prompts, context, full diff, pack and input hashes are under
`00018-v2-cycle1-inputs/`. Before dispatch, required paths were checked as regular,
readable repository files outside ignored paths. Blake's prompt was checked to
exclude the context, diff and task list. Both provider rosters received fresh,
isolated invocations. Optional Carl was omitted because the bundled transport
cannot enforce the host's restricted tool policy; all three required lenses were
still dispatched independently for both required providers.

The source's Bob inlining workaround was not used in the failed dispatch; the
coordinator incorrectly relied on read-tool transport. Recovery now has corrected
OpenAI tool-policy candidates and a complete source-style Bob inlined prompt,
`bob-openai-recovery-inlined.md` (5,271,058 bytes). No corrected prompt was
dispatched. Check its actual context budget before dispatch; a tool-policy-only
Bob candidate does not replace the source's mandatory final assembly. Refresh
gate evidence during that final assembly. Preserve blind isolation for Blake.
Use a new dispatch/output ID for the fresh roster. Never overwrite the original
outputs, raw events, prompt manifest or receipts.

The user host contract requires incomplete model/effort evidence to stop review.
This is not quota/auth exhaustion, so its alternate-launcher retry permission
does not authorize another transport here. The pause was written through
`statectl`; no state JSON was edited directly. An attended operator decision is
required before choosing a different supported Anthropic route and resuming.
The prepared recovery choice is
`AUTOCODEX_ANTHROPIC_BACKENDS=copilot,claude`: exclude the failed Kiro route,
retain explicit Opus/xhigh, and require fresh raw model/effort proof. This choice
has not been applied or dispatched. It does not authorize accepting the medium
reviews or substituting same-company coverage.

Verification: the staged full suite passed **1554 tests**, zero failures/skips,
in 657.15 seconds. Validator: 3 packages/15 skills. Validator unittest: 59 passed.
Marketplace, bundle exporter and helper source-map checks exited zero.

The installed verifier requires a `PASS/FAIL/SKIP/EXIT` line. Its first counted
pass measured 1553 passed and 1 failed because the coordinator placed the pytest
launcher under `docs/`. The package-isolation test correctly rejects any loaded
module from that directory. That failed log and CLI-written record are preserved
as `00018-v2-cycle1-harness-failed-*`. No assertion was weakened. The corrected
launcher runs from `/tmp/`; the exact failing test then passed (1 passed, 0.03s).
The adapter source is retained as `00018-v2-cycle1-counts-adapter.py.txt`.
The corrected full counted verification passed **1554 tests**, zero failures/skips.
Its CLI-written record and full output are `00018-v2-cycle1-final-verification.json`
and `00018-v2-cycle1-final-gate.txt`; hashes and adapter provenance are recorded
separately. The earlier harness failure remains intact.
The recorded command uses `/tmp/autocodex-ap00018-review-counts-ed2bb331.py`.
That active verification helper is retained for recovery; its source/hash are
archived. Other operational scratch scripts were archived and removed.

No push, installation, publication, source retirement, custody acceptance,
production edit or workflow cap increase occurred.

1. Keep the unattended loop stopped while this state remains paused.
2. Open interactive recovery in `/Users/bob/git/src/github.com/buvis/agent-plugins`.
3. Read this report, the installed Resume procedure, and the committed pause reason.
4. Select an Anthropic route that proves Opus and xhigh in raw metadata.
5. Complete prompt preflight using the prepared recovery inputs and current gate evidence.
6. Apply the authorized Resume through the existing state CLI without changing cycle, cap, batch, or tasks.
7. End the recovery session before running `autocodex` again.
