---
prd: docs/dev/project-management/prds/wip/00012-autopilot-package-contract-v1.md
review: 2
date: 2026-10-29
head_sha: aeaccb906b68d7276c736dfb3d75096a3eb6cb50
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
dispatch_rows:
  bob: 2244e3db
---

# Review: 00012-autopilot-package-contract-v1

Diff range: `b1e05c75d6f0dad01db35258baf565ecaf5a77ad..aeaccb906b68d7276c736dfb3d75096a3eb6cb50`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/alice-output-ap00012-c2.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/blake-output-ap00012-c2.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/bob-output-ap00012-c2.txt.receipt.json

The model-provider guard supersedes the legacy implementor-name guard. All contributing models are OpenAI; every required independent lens ran through the guarded host helper on Anthropic Opus/xhigh. Eve did not run. Carl is optional and omitted from this host's three-lens roster; this change has no UI.

## Review Summary

Reviewed: 46 completed tasks. The full PRD work range was available to implementation-aware reviewers; prior findings were provided for rework verification. Blake received only the PRD, repository access and the test gate. All three invocations were fresh and isolated. Staging succeeded without errors; the context pack was available. No previous verification-check queue exists. No exact runnable VERIFY command was emitted this cycle, so no queue was created.

The source's Codex-only inline-input requirement is adapted to the authorized Claude transport: Bob received the complete assembled persona, rubrics and appendices plus readable context/diff paths. His successful raw tool reads establish that the restriction that motivated inline-only Codex prompts does not apply. The 45 MB full diff was not truncated into a prompt. No implementation thread was resumed.

All three helpers succeeded with immutable raw output and receipts. The mechanical warning about missing assertions is included in R1 and adjudicated below; it was not silently dropped. No fail-first replay was requested because the base lacks this PRD's newly introduced test requirements; the prior cycle records the same replay limitation.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | The [MECH] line "test_dependency_mutations has no assertion" is a false positive: `eq, yes = self.assertEqual, self.assertTrue` renames the assert methods, so the detector cannot see them. The test does assert. Call `self.assertEqual` and `self.assertTrue` directly and drop the alias line. That is easier to read and clears the MECH line. | tests/autopilot/test_resource_closure.py:124 | 20 | ALICE, BOB, mech-check |
| R2 | [2/3] | ⚪ | `FROZEN_EDGES` is about 55 lines of base85 zlib data that no reviewer can read. map_slice only replaces rows in place or appends them, and I checked that `digest("\n".join(sorted(identities[:202])))` equals `EDGE_SHA` today. That one line could replace the blob. The tradeoff: if someone reorders the map rows, the check fails, but it never passes by mistake. Otherwise move the 202 lines into a plain-text fixture pinned by `EDGE_SHA`. | tests/autopilot/test_package.py:32 | 20 | ALICE, BOB |
| R3 | [1/3] | 🟡 | `dependencies()` misses script invocations whose path is in quotes. `prefix = line[:match.start()].rstrip("`` ` `` ")` strips backticks and spaces but not `"` or `'`. So `` `caffeinate -is python3 "$_skill/cli/__main__.py" wave run "$@"` `` at skills/run-autopilot/references/waves.md:243 never matches `COMMAND`. I checked by deleting that edge from the map: `closure_errors` still returns `[]` and every test passes. Changing the strip set to ``rstrip("`\"' ")`` closes the gap: with that change the current map still has 0 errors, and deleting the edge gives `edge count 0`. Add a `python3 "scripts/x.py"` case to `test_dependency_mutations` | tests/autopilot/test_resource_closure.py:56 | 20 | ALICE |
| R4 | [1/3] | 🟡 | `GATE_SIZE` and `GATE_SHA` are defined twice, in test_resource_closure.py:13-14 and tests/autopilot/test_package.py:87-88. test_package.py already does `from test_resource_closure import closure_errors`, so it can import both constants from there and delete its own copies. | tests/autopilot/test_resource_closure.py:13 | 20 | ALICE |
| R5 | [1/3] | 🟡 | The `failure_rule` check for packaged-resource edges sits after the if/elif chain and repeats the `kind == "packaged-resource"` test. Move it into the `if kind == "packaged-resource":` branch at line 94; behavior is unchanged. | tests/autopilot/test_resource_closure.py:108 | 20 | ALICE |
| R6 | [1/3] | 🟡 | The closure oracle misses active script references. Its prose exemption (`decision model|does not use|hand-maintained model`) skips `qwen-integration.md:79` `scripts/work_routing.py`, even though the same paragraph says the output guard calls its classifier. Its verb regex only matches `run|invoke|execute|call`, so "invoking `fablectl.py`" at `model-ladder.md:91` is never found. Both sites have external-capability edges today, but deleting either edge or reclassifying it as informational would still pass. Task 20 required the oracle to catch exactly that. | tests/autopilot/test_resource_closure.py:64 | 20 | BOB |
| R7 | [1/3] | 🟡 | 62 line-anchored external-capability edges have a capability that only repeats the path: 31 read "Host adapter for <reference>" and 31 equal the reference. One is `lane-solo.md:168` `consolidate_findings.py` (source-map.json:277993), a helper Blake named. All are new in this rework: `git grep` finds 0 "Host adapter for" rows at 3dda8f1 and 31 at HEAD. The contract requires an explicit capability and task 20 a concrete one. The oracle only checks that the field is not empty. | tests/autopilot/test_resource_closure.py:100 | 20 | BOB |
| R8 | [1/3] | 🟡 | The deferrals were never reviewed as a set, though task 20 required it. The slices deferred 125 observations, and 122 still have no edge. No disposition appears in rework-completion.md or task20-verification.json. I checked the 3 script entries and none is an active call: `agent-invocation.md:116` says "There is no `fable-run.sh` wrapper", `lane-fast-track.md:26` is an error message, and `model-ladder.md:92` is a section link. Some of the 119 non-script entries are host capabilities with no edge: `model-ladder.md:89` autoclaude, `:167` `~/.codex/hooks.json`, `:173` settings.json, `phase-review.md:145` and `:168` AskUserQuestion. The same capabilities are mapped at other sites (`use-sonnet/SKILL.md:31`, `state-schema.md:217`). | docs/dev/project-management/autopilot/reports/00012-recovery/rework-completion.md | 20 | BOB |
| R9 | [1/3] | ⚪ | Maintainer tool tools/autopilot/map_slice.py (file locking, atomic rewrite, git diff subprocess) and its tests are not in the PRD's repository structure or exports; it came in with a rework commit (20ca08e) | tools/autopilot/map_slice.py:1 | general | BLAKE |
| R10 | [1/3] | ⚪ | The facade adds an `--out PATH` option (also passed through by export-policy.py); the PRD only names capability output and policy export | plugins/autopilot/scripts/autopilot.py:26 | Phase 1 task 3 | BLAKE |
| R11 | [1/3] | ⚪ | PyYAML added as a test dependency for the CI wiring test; the PRD names only test-only jsonschema (and pytest through the test command) | tools/autopilot/requirements-test.txt:3 | Phase 2 task 2 | BLAKE |
| R12 | [1/3] | ⚪ | Three named acceptance scenarios (source_inventory_mapping, review_schema, package_self_contained) have no test or source-map ID with that name; the others appear inside longer test names. Tracing them needs judgment, and the target-only tests copy committed HEAD via `git archive`, so they need git and do not see working-tree edits | tests/autopilot/test_package.py:129 | general | BLAKE |
| R13 | [1/3] | ⚪ | Two external-capability rows still carry the stale informational rule "Historical/source citation only; must not supply missing runtime content.": `dashboard-format.md:10` `scripts/tracon/` (source-map.json:273894), which is the active dashboard, and `:30` `scripts/README.md`. This is the task-28 contradiction the operator asked to resolve, and no check rejects `runtime_rule` on rows that are not informational. | tools/autopilot/source-map.json:273894 | 20 | BOB |
| R14 | [1/3] | ⚪ | `except UnicodeDecodeError: continue` silently drops a file from the closure scan. Every package file is text (.md, .json, `autopilot.py`, LICENSE), so the guard covers a case that can't happen now and would hide a file if one appeared. | tests/autopilot/test_resource_closure.py:40 | 20 | BOB |

## Decision gate

No CRITICAL/HIGH remains. Fourteen findings are fewer than cycle 1's twenty. R1 is discarded: the claimed missing-assertion defect is refuted by the bound unittest assertion methods at test_resource_closure.py:124 and their mutation calls at lines 139–150; alias cleanup is optional and does not fix test coverage. The mechanical warning shares this disposition.

R2 is actionable consensus LOW: extract the exact 202 frozen identities into a readable plain-text fixture, preserving set/subset semantics and EDGE_SHA. Do not replace the frozen set with a positional first-202 assumption. Queue it once through the canonical tail sweep.

R3–R14 are single-voice Medium/Low findings, discarded under the gate's explicit single-voice rule and retained in the settled ledger. This is not a claim that every observation is false. R3 and R6 demonstrate distinct parser blind spots while their edges exist today; the sentence-exemption limitation from task20 remains visible. R7 and R8 retain capability/deferral traceability limitations; R13 retains the stale runtime_rule limitation. No third Pat retry or unbounded repair was started. Blake's scope observations do not authorize removing recovery tooling, export behavior, dependencies, or required test intent.

## Alice

Available: independent Anthropic Claude Opus/xhigh; full raw output follows.

### Anthropic

Provider: Anthropic; served model claude-opus-5-5; effort xhigh; session ee4a92c0-b0b5-44d0-908a-cb45ee0f8641.

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/alice-output-ap00012-c2.txt.receipt.json

Cycle-2 incremental review of `3dda8f1..HEAD`. Both prior findings that went to rework are resolved. One medium gap remains in the new closure oracle, plus small cleanups.

**Prior findings:**
- **Cycle-1 R1 (changelog list break): resolved.** Commit `afbed6a` removes the blank line and `d41c4ec` refreshes the receipt. `test_content_roster` passes.
- **Cycle-1 R2 (resource closure gaps): mostly resolved.**
  - The map adds 776 edges, for 978 in total. Every helper the finding named is now mapped as an active edge and guarded at least once.
  - The fixed-202 check is gone. The test now requires the 202 frozen identities as a subset, rejects duplicates and runs the source-derived oracle.
  - One way past the oracle remains, listed below.

**Gates I ran:**
- Python 3.12 autopilot suite: 104 passed, 0 failed, 0 skipped.
- `scripts/validate.py`: 3 packages, 15 skills.
- Validator unit tests: 12 OK.
- `test_resource_closure.py` takes 0.4s.

[ALICE] 🟡 `dependencies()` misses script invocations whose path is in quotes. `prefix = line[:match.start()].rstrip("`` ` `` ")` strips backticks and spaces but not `"` or `'`. So `` `caffeinate -is python3 "$_skill/cli/__main__.py" wave run "$@"` `` at skills/run-autopilot/references/waves.md:243 never matches `COMMAND`. I checked by deleting that edge from the map: `closure_errors` still returns `[]` and every test passes. Changing the strip set to ``rstrip("`\"' ")`` closes the gap: with that change the current map still has 0 errors, and deleting the edge gives `edge count 0`. Add a `python3 "scripts/x.py"` case to `test_dependency_mutations` | File: tests/autopilot/test_resource_closure.py:56 | Task: 20
[ALICE] 🟡 The [MECH] line "test_dependency_mutations has no assertion" is a false positive: `eq, yes = self.assertEqual, self.assertTrue` renames the assert methods, so the detector cannot see them. The test does assert. Call `self.assertEqual` and `self.assertTrue` directly and drop the alias line. That is easier to read and clears the MECH line. | File: tests/autopilot/test_resource_closure.py:124 | Task: 20
[ALICE] 🟡 `GATE_SIZE` and `GATE_SHA` are defined twice, in test_resource_closure.py:13-14 and tests/autopilot/test_package.py:87-88. test_package.py already does `from test_resource_closure import closure_errors`, so it can import both constants from there and delete its own copies. | File: tests/autopilot/test_resource_closure.py:13 | Task: 20
[ALICE] 🟡 The `failure_rule` check for packaged-resource edges sits after the if/elif chain and repeats the `kind == "packaged-resource"` test. Move it into the `if kind == "packaged-resource":` branch at line 94; behavior is unchanged. | File: tests/autopilot/test_resource_closure.py:108 | Task: 20
[ALICE] ⚪ `FROZEN_EDGES` is about 55 lines of base85 zlib data that no reviewer can read. map_slice only replaces rows in place or appends them, and I checked that `digest("\n".join(sorted(identities[:202])))` equals `EDGE_SHA` today. That one line could replace the blob. The tradeoff: if someone reorders the map rows, the check fails, but it never passes by mistake. Otherwise move the 202 lines into a plain-text fixture pinned by `EDGE_SHA`. | File: tests/autopilot/test_package.py:32 | Task: 20

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

Notes:
- **Not flagged:**
  - About 232 prose mentions mapped as external-capability (for example "run Codex through the `codex-run.sh` helper") are outside the oracle's expected set by design. Only 2 literal invocations are missed: the quoted one above, and `…/statectl.py`, which is already mapped.
  - The 13 external-capability edges marked `planned` are all frozen pre-existing UTIL rows.
  - ruff reports I001, SIM905 and PLW1510, but CI does not run ruff and the import layout matches existing house style.
- **Scratch files:** my probe scripts are in `/tmp/alice-ap12/`. I wrote nothing in the repo.

## Blake

Available: independent Anthropic Claude Opus/xhigh; full raw output follows.

### Anthropic

Provider: Anthropic; served model claude-opus-5-5; effort xhigh; session 51fe44a0-4701-4d19-915a-b0490e68f5de.

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/blake-output-ap00012-c2.txt.receipt.json

Done. I traced every rule against the code. The package is faithful to the PRD; I found only four low-severity scope and traceability items.

What I checked myself (not taken from the test gate):
- `python3 tools/autopilot/check-source.py --source-root …/claude-autopilot` passed: 679 files, 92 assets, 1381 behaviors, 4950 regression cases at the pinned commit.
- A byte comparison against the pinned source:
  - All 59 skill references, the 18 personas and `LICENSE` are byte-identical.
  - Each of the 11 `SKILL.md` files differs only by one inserted 5-line refusal gate after the frontmatter.
- `python3 scripts/validate.py` passed: 3 packages, 15 skills.
- `prerequisites.py --prd 00016` exits 1 and lists `00015`, `00020` and `00021` as missing. `--prd 99999` exits 1 and reports it as unknown.
- The policy matches the pinned source:
  - Full lane: Alice, Blake and Bob required. Carl joins when Gemini is available. Eve joins when the doubt reviewer is Fable or a Codex implementor took part. Rework cap is 2.
  - Fast-track: Alice, Blake, Eve and Bob required, Carl conditional, delta pass by Eve only.
  - Solo: one zero-context Alice review, with Alice also on the delta.
  - The consensus rubric has no R5; that matches the source rubric.
- The 55 golden cases cover everything the PRD names: clean rosters, missing and failed roles, missing rubric verdicts, a group pointing at an unknown finding, and stale PRD/tree/scope/input/result bindings under the same policy.

```
[BLAKE] ⚪ Maintainer tool tools/autopilot/map_slice.py (file locking, atomic rewrite, git diff subprocess) and its tests are not in the PRD's repository structure or exports; it came in with a rework commit (20ca08e) | File: tools/autopilot/map_slice.py:1 | Task: general
[BLAKE] ⚪ The facade adds an `--out PATH` option (also passed through by export-policy.py); the PRD only names capability output and policy export | File: plugins/autopilot/scripts/autopilot.py:26 | Task: Phase 1 task 3
[BLAKE] ⚪ PyYAML added as a test dependency for the CI wiring test; the PRD names only test-only jsonschema (and pytest through the test command) | File: tools/autopilot/requirements-test.txt:3 | Task: Phase 2 task 2
[BLAKE] ⚪ Three named acceptance scenarios (source_inventory_mapping, review_schema, package_self_contained) have no test or source-map ID with that name; the others appear inside longer test names. Tracing them needs judgment, and the target-only tests copy committed HEAD via `git archive`, so they need git and do not see working-tree edits | File: tests/autopilot/test_package.py:129 | Task: general
```

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: fail
B7: fail
B8: fail
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass

The comparison script is still at `/tmp/blake-audit/compare.py`. I left it because every `rm` needs warden approval.

## Bob

Available: independent Anthropic Claude Opus/xhigh; full raw output follows.

### Anthropic

Provider: Anthropic; served model claude-opus-5-5; effort xhigh; session 95ff83bd-845a-4d23-9d77-2b8ff0ab183b.

Receipt: /Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/tmp/bob-output-ap00012-c2.txt.receipt.json

Cycle-2 review of the rework (`3dda8f1..HEAD`): both prior findings are mostly resolved, with three Medium and four Low residual issues. I didn't run any tests. The gate's 104 passes were recorded at d41c4ec, and every commit after that touches only `docs/`.

**Prior findings:**
- **R1 (changelog blank line):** resolved. The blank line is gone, and the CHANGELOG receipt hash (`44f68ed9…`) matches the file.
- **R2 (HIGH, missing script edges):** resolved for the helpers Blake named. Each named site now has an external-capability edge, including `consolidate_findings.py` at `lane-solo.md:168` and `review-work-completion/SKILL.md:381`, and `compute_mech_facts.py` at `fast-track/SKILL.md:265`. The 202 frozen identities are kept as a subset. The issues below are what remains of R2.

[BOB] 🟡 The closure oracle misses active script references. Its prose exemption (`decision model|does not use|hand-maintained model`) skips `qwen-integration.md:79` `scripts/work_routing.py`, even though the same paragraph says the output guard calls its classifier. Its verb regex only matches `run|invoke|execute|call`, so "invoking `fablectl.py`" at `model-ladder.md:91` is never found. Both sites have external-capability edges today, but deleting either edge or reclassifying it as informational would still pass. Task 20 required the oracle to catch exactly that. | File: tests/autopilot/test_resource_closure.py:64 | Task: 20
[BOB] 🟡 62 line-anchored external-capability edges have a capability that only repeats the path: 31 read "Host adapter for <reference>" and 31 equal the reference. One is `lane-solo.md:168` `consolidate_findings.py` (source-map.json:277993), a helper Blake named. All are new in this rework: `git grep` finds 0 "Host adapter for" rows at 3dda8f1 and 31 at HEAD. The contract requires an explicit capability and task 20 a concrete one. The oracle only checks that the field is not empty. | File: tests/autopilot/test_resource_closure.py:100 | Task: 20
[BOB] 🟡 The deferrals were never reviewed as a set, though task 20 required it. The slices deferred 125 observations, and 122 still have no edge. No disposition appears in rework-completion.md or task20-verification.json. I checked the 3 script entries and none is an active call: `agent-invocation.md:116` says "There is no `fable-run.sh` wrapper", `lane-fast-track.md:26` is an error message, and `model-ladder.md:92` is a section link. Some of the 119 non-script entries are host capabilities with no edge: `model-ladder.md:89` autoclaude, `:167` `~/.codex/hooks.json`, `:173` settings.json, `phase-review.md:145` and `:168` AskUserQuestion. The same capabilities are mapped at other sites (`use-sonnet/SKILL.md:31`, `state-schema.md:217`). | File: docs/dev/project-management/autopilot/reports/00012-recovery/rework-completion.md | Task: 20
[BOB] 🟡 The [MECH] line "test_dependency_mutations has no assertion" is a false positive: line 124 aliases the asserts (`eq, yes = self.assertEqual, self.assertTrue`), which hides them from the detector. The test does assert. | File: tests/autopilot/test_resource_closure.py:124 | Task: 20
[BOB] ⚪ Two external-capability rows still carry the stale informational rule "Historical/source citation only; must not supply missing runtime content.": `dashboard-format.md:10` `scripts/tracon/` (source-map.json:273894), which is the active dashboard, and `:30` `scripts/README.md`. This is the task-28 contradiction the operator asked to resolve, and no check rejects `runtime_rule` on rows that are not informational. | File: tools/autopilot/source-map.json:273894 | Task: 20
[BOB] ⚪ `except UnicodeDecodeError: continue` silently drops a file from the closure scan. Every package file is text (.md, .json, `autopilot.py`, LICENSE), so the guard covers a case that can't happen now and would hide a file if one appeared. | File: tests/autopilot/test_resource_closure.py:40 | Task: 20
[BOB] ⚪ `FROZEN_EDGES` is a 58-line base85+zlib blob. The EDGE_SHA digest proves it is intact, but no reviewer can read which 202 identities are frozen. | File: tests/autopilot/test_package.py:30 | Task: 20

R1: pass
R2: fail
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: fail
R10: fail
R11: pass
R12: pass
R13: pass

FIX:
- Oracle misses active references — tests/autopilot/test_resource_closure.py:64 — widen the verb regex at line 58 to `(?i)\b(?:run|invok|execut|call)\w*(?: the)?$`. Replace the phrase-based `cite` test with an explicit frozen set of reviewed citation sites `(src, line, ref)`, built from today's phrase hits minus `skills/work/references/qwen-integration.md:79`. Add mutation cases that delete the edges at `qwen-integration.md:79` and `model-ladder.md:91` and expect errors.
- Capability fields that only repeat the path — tests/autopilot/test_resource_closure.py:100 — rewrite the 62 capability strings as functional descriptions, the way `review-work-completion/SKILL.md:381` reads "Merge reviewer findings, consensus and ledger dismissals." Do it in `map_slice.py` slices under the 24 KB diff limit. Then make `closure_errors` reject a capability that equals the reference, contains it, or starts with "Host adapter for ".
- Deferrals not reviewed — docs/dev/project-management/autopilot/reports/00012-recovery/rework-completion.md:5 — write a deferral disposition file that lists each of the 122 unmapped observations as mapped, informational with a reason, or outside the script-closure scope with an owner PRD. Add external-capability/unavailable edges for the five host-capability sites named above, or record why they are excluded.
- Aliased asserts — tests/autopilot/test_resource_closure.py:124 — delete the alias line and call `self.assertEqual` and `self.assertTrue` directly.
- Stale `runtime_rule` on active rows — tools/autopilot/source-map.json:273894 — remove `runtime_rule` from both dashboard-format rows, or reclassify `:30` as informational. Then assert in `closure_errors` that non-informational rows carry no `runtime_rule`.
- Silent decode skip — tests/autopilot/test_resource_closure.py:38 — remove the try/except so a file that is not UTF-8 fails the test.
- Unreadable frozen blob — tests/autopilot/test_package.py:30 — move the 202 identity lines into a plain-text fixture next to the test, keep the `len == 202` and EDGE_SHA digest asserts on it, and drop the `base64` and `zlib` imports.

VERIFY:
- (none)

KNOWN:
- (none)

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

Verdict: 14 findings
Tests: 104 passed, 0 failed, 0 skipped (reused from last-verification.json at d41c4ec)
