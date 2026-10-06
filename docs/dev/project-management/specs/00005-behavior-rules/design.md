# Design: specflow behavior rules

## Overview

This spec makes parity measurable before a single rule is written. It builds the rule inventory, the list of required decision criteria, the checker that fails CI when a row, a criterion, a rule, or a check is missing, the validator checks for structural rules, and the formats in which behavioral rules are tested. The rule texts themselves arrive with the references of 00006 and 00007.

## Context and constraints

- Depends on 00002 (the package boundary, which keeps the inventory, the criteria list, and `check_rules.py` out of the package) and on 00004 (the helper, its check registry `CHECKS`, and `check_schema`).
- The two port plans are the input: `docs/dev/project-management/discovery/00001-specflow-port-agent-skills.md` (Plan A) and `docs/dev/project-management/discovery/00001-specflow-port-autopilot-phases.md` (Plan B). Both hold their rows under `## Inventory Matrix`, in tables with the header `id | source skill | phase | row | classification | reason | code-only | evidence`.
- The checker runs before the files it checks exist. Until 00006 and 00007 finish, CI runs it per finished area; the release runs it with no filter.
- Maintainer tooling is dependency-free Python (`AGENTS.md`, whole repository) and may import the shipped helper; the package never imports maintainer tooling.

Section numbers such as `§7.3` in carried passages are those of the source design in intake item 00001; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section.

## Architecture

```text
tools/specflow/
├── check_rules.py                # Rule inventory checks
└── rules/
    ├── inventory.json            # Rule ID -> sources, file, kind, check; no rule text
    ├── criteria.json             # The required decision criteria
    ├── inventory.schema.json     # The shape of each, checked with check_schema
    └── criteria.schema.json
plugins/specflow/skills/spec-workflow/
├── references/validation-rules.md            # Text of structural rules no phase file carries (area VAL)
└── scripts/specflow_helper/checks.py         # The check registry of 00004, extended here
tests/specflow/
├── evals/
│   ├── schemas/                  # session.schema.json, eval.schema.json
│   ├── examples/                 # One valid session and one valid eval
│   ├── sessions/<name>.json      # Written with each reference, from 00006 on
│   └── SR-<area>-NNN.json        # One per behavioral rule, from 00006 on
└── rules/                        # Tests of check_rules.py
```

The inventory is the hub. A port-plan row or a required criterion points into it; each of its rules points to one distributed file, where the rule text lives once, and to one check. `check_rules.py` walks those links and fails on a missing one.

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `tools/specflow/rules/inventory.json` | new | T-070 | every approved Plan A row as one or more rules, with planned files and checks |
| `tools/specflow/rules/criteria.json` | new | T-070 | the 33 required criterion IDs |
| `tools/specflow/rules/inventory.schema.json`, `tools/specflow/rules/criteria.schema.json` | new | T-070 | the shapes of the two files, applied by the checker with `check_schema` |
| `tools/specflow/check_rules.py` | new | T-070 | the checker |
| `tests/specflow/rules/test_check_rules.py` | new | T-070 | its tests; fixtures are built in temporary folders |
| `.github/workflows/validate.yml` | edit | T-070 | two steps: the checker's tests, and the checker with the list of finished areas |
| `plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py` | edit | T-071 | one named check per structural rule |
| `plugins/specflow/skills/spec-workflow/references/validation-rules.md` | new | T-071 | structural rule texts, tagged with their IDs |
| `tests/specflow/contract/test_checks.py` | edit | T-071 | one seeded defect per check |
| `tools/specflow/rules/inventory.json` | edit | T-071 | the check name of each structural rule |
| `.github/workflows/validate.yml` | edit | T-071 | the checker step changes to `--area VAL` |
| `tests/specflow/evals/schemas/session.schema.json`, `tests/specflow/evals/schemas/eval.schema.json` | new | T-069 | the two formats |
| `tests/specflow/evals/examples/session.json`, `tests/specflow/evals/examples/eval.json` | new | T-069 | one example of each |
| `tools/specflow/check_rules.py` | edit | T-069 | an `evals/<rule-id>.json` check resolves only to a file that validates |
| `tests/specflow/rules/test_eval_formats.py` | new | T-069 | their tests |

## Components and interfaces

### Behavior rules

This is the adapter-rule layer of decision 2026-09-27 #5 (RULE-001). Each approved port or redesign row of a port plan becomes one or more numbered rules. The rules live in local files, separate from the AWS references; a catch-up never edits them. A rule that comes from a decision instead of a port-plan row cites it as `D:<decision date>#<n>` in its sources (for example the discovery rules of `D:2026-10-03#10`, `#11`, and `#12`).

**Where a rule lives.** Rule text lives once, in the distributed runtime file that uses it, tagged with its ID:

```markdown
- [SR-DLG-007] Ask one question per message.
```

IDs are `SR-<area>-NNN`, never reused. Areas match files: `DLG` (shared dialogue in `artifact-contract.md`), `INT` (`phases/intake.md`), `REQ` (`phases/requirements.md`), `DSN` (`phases/design.md`), `TSK` (`phases/tasks.md`), `IMP` (`phases/implementation.md`), `VER` (`phases/verification.md`), `VAL` (`validation-rules.md`, for structural rule text no phase file carries), `RVC` (`review/core.md`), `RVR` (`review/requirements.md`), `RVD` (`review/design/`), `RVX` (`review/cross-spec.md`), and `SKL` (`SKILL.md`: intent and trigger rows, the language rule, and the gate and status rules that 00006 writes from its requirements). A rule that ports a script behavior also names the script, and that script's tests carry the check.

**Inventory.** `tools/specflow/rules/inventory.json` is maintainer-only. It maps each rule to its sources and its check, and holds no rule text, so the text cannot drift:

```json
{
  "schemaVersion": 1,
  "plans": {
    "A": "docs/dev/project-management/discovery/00001-specflow-port-agent-skills.md",
    "B": "docs/dev/project-management/discovery/00001-specflow-port-autopilot-phases.md"
  },
  "rules": [
    {"id": "SR-DLG-007", "file": "artifact-contract.md", "kind": "behavioral",
     "check": "evals/SR-DLG-007.json", "sources": ["A:ELI-16", "D:2026-10-03#14"]},
    {"id": "SR-TSK-004", "file": "phases/tasks.md", "kind": "structural",
     "check": "validator:tasks-premise", "sources": ["A:PRD-17", "B:PLT-19"]},
    {"id": "SR-DLG-008", "file": "artifact-contract.md", "kind": "behavioral",
     "check": "evals/SR-DLG-008.json", "sources": ["D:2026-10-03#11"],
     "criteria": ["ART-002.14"]}
  ]
}
```

**Checks.** A structural rule is one that files alone can prove (IDs, EARS shape, traceability, placeholders, `Sources:` line, spec numbers, section presence, task order); `validate_spec.py` enforces it under a named check. A behavioral rule is about what the agent says or does across turns (one question per message, recommended option first, apply an edit before the next finding); one scenario eval covers it (§15). A row with both parts becomes two rules, so each rule has exactly one check. A check is one of three kinds: `evals/<rule-id>.json`, `validator:<check-name>`, or `test:<path>::<test name>` for a rule carried by a ported script's tests.

**Decision-criterion coverage (decision 2026-10-04 #4).** The maintainer-only `tools/specflow/rules/criteria.json` records the required set independently of the inventory. Its initial complete content is:

```json
{
  "schemaVersion": 1,
  "requiredCriteria": [
    "WF-003.11", "WF-003.12", "WF-003.13", "WF-003.14",
    "WF-003.15", "WF-003.16", "WF-003.17", "WF-003.18",
    "ART-002.12", "ART-002.13", "ART-002.14", "ART-002.15",
    "ART-002.16", "ART-002.17", "ART-002.18",
    "ART-001.11", "ART-003.12", "INT-001.8", "INT-002.8",
    "WF-001.9", "WF-004.8", "VAL-001.11", "VAL-001.12",
    "INT-001.5", "SEC-002.2", "ART-002.11", "WF-002.1",
    "STATE-001.2", "STATE-003.1", "VAL-001.5", "VAL-001.8",
    "ART-004.16", "VAL-001.13"
  ]
}
```

The last two IDs are the criteria that decision 2026-10-04 #9 added; they joined by the developer's ruling of 2026-10-04 (D8). The source listed 31; the list holds 33, and RULE-001 criterion 1 says 33.

Inventory rules carry a `criteria` array only when they cover these criteria. Each listed criterion must occur on at least one rule; several rules may cover one compound criterion, and one shared rule may cover several criteria. Split structural and behavioral obligations using the existing rule kinds and one check per rule. Every mapped rule retains its `D:<date>#<n>` source(s), including later rulings that change the behavior. Do not duplicate check IDs or rule prose in the required list: follow criterion → inventory rule → existing check. IDs in this list remain stable when a ruling changes their text; update the rule and assertions instead. Adding/removing required IDs is a reviewed scope edit, never a list generated from whatever rules happen to exist. No decision-prose or upstream parser is added.

Reject an absent list, unsupported schema, empty/malformed/duplicate IDs, and inventory criterion IDs outside the required set. A full run fails if any required ID has no mapping or any mapped rule/check fails the existing checks; it prints criterion → rule → check rows for review. `--area` may filter runtime-file/check existence during construction, but still checks the complete required list and mappings; it cannot hide a wholly omitted criterion. These links prove traceability, not that a test's assertions are sufficient: reference authors and release review must check every obligation of each criterion, including mixed behavior, against its assertions.

**Routing approved rows.** Shared dialogue and approval-summary behavior from §5.2 routes first to `artifact-contract.md` (`DLG`), regardless of source phase; multiple sources share one rule and phase files point to it. Remaining rows go to a file by source skill and `phase` column; review-specific behavior takes the review route below:

| Source skill | Phase column | File |
|---|---|---|
| any | shared dialogue or approval summary (§5.2), regardless of phase | `artifact-contract.md` (`DLG`) |
| elicit-requirements, create-prd | intake | `phases/intake.md` |
| elicit-requirements, create-prd | requirements | `phases/requirements.md` |
| elicit-requirements, create-prd | design | `phases/design.md` |
| create-prd | tasks | `phases/tasks.md` |
| design-solution | design drafting, reuse, placement, contracts, output/status | `phases/design.md` (`DSN`) |
| design-solution | design review: DSN-35 through DSN-52, DSN-56/57, excluding drops | `review/design/` (`RVD`), with the phase handoff in `phases/design.md` |
| plan-tasks | tasks, including PLT-41 and PLT-61 ruled redesign | `phases/tasks.md` (`TSK`); sizing checks also feed `review/cross-spec.md` |
| spike | any | `phases/intake.md` (spike path, §6.8) |
| review-discovery-doc | requirements | `review/requirements.md` |
| review-design-doc | design | the matching file in `review/design/` |
| review-prd-backlog | intake, requirements, design, tasks, verification | `review/cross-spec.md` |
| any review skill | cross | `review/core.md` |
| any | trigger rows that name an intent | `SKILL.md` |
| any | code-only rows (`-S`, `-C` IDs) | the ported script and its tests |

Rows ruled redesign in the drop walkthrough (ELI-57, PRD-31, RPB-28, RPB-53, RPB-59, RPB-78, RPB-C2, RPB-C3) follow the same table by phase, or by the file their ruling names. The struck row (RPB-C6) gets no rule.

**CI.** `tools/specflow/check_rules.py` reads each plan's matrix tables (row ID and final classification), the required-criterion list, and the inventory, then applies both port-row and decision-criterion coverage checks above plus the rule/file/check checks. It also runs with `--area` for construction, under the filtering limits above. Missing criterion diagnostics name its ID; a decision-level citation does not substitute for the missing mapping.

**Release coverage.** Every accepted rule, including `RVX` and advisory-script rules, must have its file and check before release 0.1 (requirements §9), and every required decision criterion must map through to them. There is no `slice` exemption or `--slice` mode. During construction an `--area` check can verify a completed area; the release runs `check_rules.py` without an area filter and skips nothing.

### `check_rules.py`

```text
python3 tools/specflow/check_rules.py [--area AREA[,AREA...]]
```

Run from the repository root. It prints one line per failure as `error: <subject>: <message>`, where the subject is a plan row, a criterion, or a rule ID, one coverage row per pair of required criterion and rule, as `<criterion> -> <rule> -> <check>`, and one line per plan with the number of rows it read. Exit codes: 0 pass, 1 one or more failures; a usage error exits 2.

What it reads:

- Plan rows: every table under `## Inventory Matrix` in each file of the inventory's `plans` map. The header must be `id | source skill | phase | row | classification | reason | code-only | evidence`; a table there with another header fails. Cells are split on a `|` that no backslash precedes, and a row without exactly eight cells fails. The row ID is the first cell, the final classification the fifth, and it is one of `port`, `redesign`, `drop`, `struck`; any other value fails. `port` and `redesign` rows each need one or more rules; `drop` and `struck` rows must have none. A row is approved once it stands in the matrix with `port` or `redesign`; the change that edits a plan is where that approval is reviewed.
- The JSON example above is the end state. T-070 writes `plans` with the key `A` only and no `B:` source, so the checker does not read the second plan before its rows have rules; T-079 (00007) adds the key `B` and all its mappings in one change.
- `tools/specflow/rules/criteria.json` and `tools/specflow/rules/inventory.json`, in the shapes shown above. A rule's `sources` entry has one of three forms: `<plan key>:<row id>`, `D:<date>#<n>` for a decision, or `R:<criterion>` for a rule written from a requirement of this product that no port row or decision stands behind (00006 uses it for implementation, verification, bugfix, and gate behavior that a session must prove). Behavior that a `drop` ruling adds gets no form of its own: its rule cites the decision (`D:`) or the criterion (`R:`) behind it, and a rule that cites a `drop` row still fails (bundle B2).
- Where a rule's `file` lives. It resolves under `plugins/specflow/skills/spec-workflow/references/`, with three exceptions: `SKILL.md` is `plugins/specflow/skills/spec-workflow/SKILL.md`, a path that starts with `scripts/` resolves under `plugins/specflow/skills/spec-workflow/`, and a path that starts with `convert-prd/` resolves under `plugins/specflow/skills/`.
- Whether a check exists. `validator:<check-name>` is a key of `CHECKS` in the shipped `specflow_helper/checks.py`. `evals/<rule-id>.json` is that file under `tests/specflow/evals/`, valid against the eval schema, naming a session file that exists. `test:<path>::<test name>` is a file at that repository path that defines a function of that name.

The tag of a rule is a list item that starts `- [SR-<area>-NNN] `, outside fenced code, in a Markdown file; for a rule carried by a script, a comment line that starts `# [SR-<area>-NNN] `. Only that form counts, so a pointer to a rule, which writes the bare ID, is not a second tag. A rule's `file` is a regular file, never a folder. The checker sets `sys.dont_write_bytecode = True` before it imports the shipped helper, so it leaves no `__pycache__` in the package.

It also checks the inventory itself: the file exists, parses, passes its schema, and has a supported `schemaVersion`; no rule ID repeats; a `structural` rule has a `validator:` or `test:` check and a `behavioral` rule an `evals/` check; an `evals/<rule-id>.json` check carries its own rule's ID; no rule's `file` is under `aws/`; and every tag found in the package belongs to a rule of the inventory.

What it fails on, besides the conditions the paragraphs above state (the plan-row rules, the tag form, a folder as `file`, and the six inventory checks): a `port` or `redesign` row with no rule; a rule whose source names a `drop` or `struck` row, an unknown row, or an unknown plan; a required criterion with no rule; a criteria list that is absent, fails its schema, has an unsupported `schemaVersion`, is empty, or holds a malformed or repeated ID; an inventory `criteria` entry outside the required list; a rule with no `check`; a rule whose `file` does not exist; a rule whose tag `[<rule ID>]` is absent from its file or present in a second file under `plugins/specflow/skills/`; a check that does not exist.

`--area` names the areas whose files and checks must exist, by the `<area>` of `SR-<area>-NNN`. For a rule of another area the file, tag, and check-existence tests are skipped; every other test still runs, so a criterion with no mapping fails under any filter. `--area none` skips those three tests for every rule; it is what CI runs from T-070 until the first area is finished. An area name the inventory does not use is a usage error, exit 2. An area passes only when the last task that writes its rules has landed.

### Structural checks of T-071

T-071 registers these checks in `CHECKS`, each with its phases, and adds one more for each structural rule of the inventory that no check of 00004 already enforces, named in kebab case for what it proves; where a 00004 check enforces the rule, the inventory names that check's key. `open-markers` uses the marker scanner of 00004. It is registered for every phase from `requirements` on and reads only the artifacts upstream of the phase's own artifact in the spec's workflow order, so in the first artifact's phase it reads none. Each finding names the upstream file, so the approval procedure of 00006 reads the findings as the markers to ask about, not as errors of the artifact being approved. As the status output of 00004 says, such a marker never closes the gate that lets drafting start; it blocks the dependent artifact's approval until the developer resolves it or accepts it by name, and the acceptance recorded with that approval clears the finding. A test, `test_every_structural_rule_check_is_registered`, compares the inventory with `CHECKS`.

| Check name | Rule | Level |
|---|---|---|
| `placeholders` | no `TBD`, `TODO`, `???`, or bare `N/A` outside inline code and fences; `Not applicable: <reason>` with a reason, in `design.md` only (ART-001.10 of 00004) | error |
| `open-markers` | each `(guess)` outside inline code and fences, each list item under `## Unresolved questions`, and each list item under `## Open decisions` of an upstream artifact that no recorded acceptance covers (VAL-001.9) | error, on the upstream file; phases `requirements` on |
| `portable-links` | absolute or home-directory paths and `[[...]]` links (VAL-001.10) | warning |
| `closed-fences` | a code fence that never closes (VAL-001.11) | error |
| `requirement-source` | a requirement in `requirements.md` with no `Source:` line (VAL-001.12) | warning |

A structural rule's text is tagged with its ID in `validation-rules.md` unless a phase reference already carries it.

### Sessions and evals

Evals and runs are separate. A **session**, `tests/specflow/evals/sessions/<name>.json`, is a fixture repository plus scripted developer turns (for example one design seeded with a defect per cardinal sin, walked through `review design`). An **eval**, `tests/specflow/evals/SR-<area>-NNN.json`, is one behavioral rule's assertions over one named session. Each rule still has its own eval (decision 2026-09-27 #5), but a host runs each session once and scores every eval that uses it, so the run count follows the number of sessions, not the number of rules.

- Assertions are deterministic where they can be: files created, unchanged, or containing a pattern; one question per agent message; the recommended option listed first. A rubric assertion, judged by the developer by hand (ruling D10 of 2026-10-04; the scorer of 00009 stores the verdict), is used only when no deterministic check fits, and the eval says which it is.

## Data model

The inventory and the criteria list have the shapes shown under Behavior rules. Each has a schema beside it, `tools/specflow/rules/inventory.schema.json` and `criteria.schema.json`, written by T-070 and applied by the checker with `check_schema` (bundle B1). T-069 defines the two test formats; both are checked with `check_schema` of 00004.

Session, `tests/specflow/evals/sessions/<name>.json`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `name` | string | yes | equals the file name without `.json` |
| `fixture` | string | yes, unless `continues` is set | a folder under `tests/specflow/fixtures/`, copied to a scratch workspace before a run; a continuing session names none |
| `turns` | array | yes | objects with `developer`, what the developer says at that turn; an optional `edit` (`path` and `text`), which the runner writes into the workspace before that turn, as a second writer would; and an optional `expects`, a pattern the agent's previous reply must match, or the session is broken at that turn |
| `continues` | string | no | the `name` of a session whose finished workspace this one starts from, in a new conversation; the schema requires exactly one of `fixture` and `continues`, with `oneOf` |

Eval, `tests/specflow/evals/SR-<area>-NNN.json`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | integer | yes | `1` |
| `rule` | string | yes | the rule ID; equals the file name without `.json` |
| `session` | string | yes | the `name` of the session it is scored on |
| `assertions` | array | yes | one or more objects, each with a `kind` |

Assertion kinds. Six come from the source list: `file_exists` (`path`), `file_unchanged` (`path`), `file_matches` (`path`, `pattern`), `one_question_per_message`, `recommended_option_first`, and `rubric` (`rubric`: the question to judge). The sessions the source describes need nine more, all deterministic: `file_absent` (`path`) and `file_lacks` (`path`, `pattern`); `message_matches` and `message_lacks` (`pattern`, optional `turn`); `question_count_at_most` (`count`); `file_read` and `file_not_read` (`path`, optional `before_turn`); `validation_passes` and `validation_reports` (`check`), which run `validate` of 00004 on the session's finished workspace. Every kind but `rubric` is deterministic. A `path` is relative to the session's workspace, a `pattern` is a Python `re` search, and an assertion is scored after the last turn unless it names a `turn`. The schema checker of 00004 has no keyword for "one or more", so `check_rules.py` itself rejects an eval with no assertion, and a session or eval whose name field differs from its file name; the two files under `examples/` are exempt from the name rule. The scorer of 00009 implements exactly this list; a later kind is added to the eval schema and to the scorer in one change.

The result of a run, and the runners, belong to 00009.

## Data and control flow

`check_rules.py`, in order: load the criteria list and the inventory; read the plan rows; test row coverage, then criterion coverage, then each rule's file, tag, and check; print the failures and the coverage rows. Every test runs even after a failure.

Order over time: T-070 encodes the whole Plan A inventory with planned files and check references, so every required criterion has its mapping from the first day. Each reference task of 00006 and 00007 then writes its rule texts and checks and adds its area to the CI step. T-079 (00007) adds the Plan B rows; T-080 (00007) adds the `CNV` area. The release (T-063, 00001) runs the checker with no filter.

## Error handling

| Condition | Required behavior |
|---|---|
| Unclosed code fence in an artifact | Fail validation; record no approval until it is closed |

A checker failure names its subject, so a missing mapping reads as the criterion or the row it is missing for. A plan file with no matrix table, or a matrix row with an empty classification, is a failure, not an empty pass. A malformed eval record fails with the path of the bad value, also when it is reached through a criterion mapping.

## Security and privacy

- The checker reads repository files and writes nothing. It uses no network and runs no check it finds; it only tests that the check exists.
- The inventory, the criteria list, the checker, and the eval records are maintainer-only. The release check of 00002 fails if any of their names appears inside the package.
- The inventory holds no rule text, so a rule cannot be changed there without the distributed file changing.
- A session may script a synthetic credential to test redaction; no session or fixture holds a real one.

## Testing strategy

- An unclosed code fence fails validation and blocks approval.
- A requirement without a `Source:` line warns and never fails.

- Run `check_rules.py` without filters: every approved row and required decision criterion has a rule, and every rule has a check that exists. Check the 33-criterion output against the assertions, not just the presence of links. Regression fixtures remove a whole criterion mapping while leaving its decision source, remove the mapped check, omit the required list, and introduce duplicate/unknown criterion IDs; all fail with targeted diagnostics. Shared-rule and mixed-kind mappings pass. `--area` still rejects a completely unmapped criterion.

`unittest`, with tests named for the rule they enforce. The checker's tests build small plan, inventory, and criteria fixtures in temporary folders.

- T-070, `tests/specflow/rules/test_check_rules.py`: `test_every_approved_plan_a_row_has_a_rule`, `test_no_drop_or_struck_row_has_a_rule`, `test_rejects_unmapped_row`, `test_rejects_rule_without_check`, `test_rejects_missing_check`, `test_rejects_missing_rule_file`, `test_rejects_rule_tag_in_two_files`, `test_required_list_is_the_reviewed_ids`, `test_rejects_criterion_with_only_a_decision_source`, `test_rejects_missing_criteria_list`, `test_rejects_duplicate_criterion_id`, `test_rejects_unknown_criterion_id`, `test_accepts_shared_rule_and_mixed_kind_split`, `test_area_filter_skips_other_areas_files_only`, `test_area_filter_still_rejects_unmapped_criterion`, `test_prints_criterion_rule_check_rows`; and for the conditions this design adds: `test_rejects_table_with_another_header`, `test_rejects_row_without_eight_cells`, `test_splits_cells_on_unescaped_pipes_only`, `test_rejects_unknown_classification`, `test_rejects_folder_as_rule_file`, `test_only_the_list_item_form_is_a_tag`, `test_rejects_unreadable_inventory`, `test_rejects_inventory_that_fails_its_schema`, `test_rejects_criteria_list_that_fails_its_schema`, `test_rejects_repeated_rule_id`, `test_rejects_kind_and_check_mismatch`, `test_rejects_eval_check_of_another_rule`, `test_rejects_rule_file_under_aws`, `test_rejects_tag_of_no_rule`, `test_area_none_skips_file_tag_and_check_tests`, `test_unknown_area_is_a_usage_error`.
- T-071, `tests/specflow/contract/test_checks.py`: one seeded defect per check fails with file, rule, and fix; an artifact with an unclosed fence fails; a warning never changes the exit status; `test_every_structural_rule_check_is_registered`; `test_open_markers_reads_only_upstream_artifacts`. `python3 tools/specflow/check_rules.py --area VAL` passes.
- T-069, `tests/specflow/rules/test_eval_formats.py`: both examples validate; `test_eval_check_resolves_only_to_a_valid_file`; `test_rejects_malformed_eval_record`; `test_rejects_malformed_eval_through_a_criterion_mapping`; `test_several_criteria_may_share_one_eval`.

## Rollout and migration

The CI step is `python3 tools/specflow/check_rules.py --area <areas>` with the comma-separated list of finished areas. It starts as `--area none` with T-070 and becomes `--area VAL` with T-071. Each reference task of 00006 and 00007 appends its area in the change that completes the area: `INT` joins with T-072 and `RVD` with T-077, since two tasks share each of those areas. The filter is a construction aid: the release runs with no filter and skips nothing.

Nothing migrates. The personal skills keep working until their parity gates pass (00009) and their owners retire them.

## Risks and edge cases

- A rule maps to a check whose assertions do not cover its whole obligation: impact h, likelihood m; mitigation: reference authors check every obligation of each criterion against its assertions; fallback: the release review of the 33 required criteria (T-063) rejects the mapping.
- A port plan's table layout changes and rows go unread: impact h, likelihood l; mitigation: a plan with no matrix row, or a row with an unknown classification, fails; fallback: the checker prints how many rows it read per plan, and the release review compares that with the plan tables by hand.
- Likely next change, a third port plan: the `plans` map takes any key; impact l, likelihood m; mitigation: sources are written `<plan key>:<row id>`; fallback: none needed.
- Likely next change, a new rule area: an area is tied to one file by the routing table; impact l, likelihood m; mitigation: the area is the middle of the rule ID, so adding one is a new row in that table and a new entry in the file-resolution rule; fallback: route the rule to `validation-rules.md`.
- Likely next change, the required-criterion list grows: its content is reviewed scope, and RULE-001 criterion 1 names its size; impact m, likelihood h, since two criteria were added on 2026-10-04; mitigation: an addition is one reviewed edit to the list and to that criterion, as ruling D8 made; fallback: cover the new criteria by rules without listing them.
- Edge case: one rule may cover several criteria, and one criterion may need several rules; both pass. A decision citation in `sources` with no `criteria` entry covers nothing.

## Requirement traceability

| Design element | Criteria |
|---|---|
| Inventory, routing of approved rows, required-criterion list | RULE-001.1 |
| Rule text once, tagged with its ID, in one distributed file; the tag test | RULE-001.2 |
| Check kinds; structural checks of T-071; session and eval formats | RULE-001.3 |
| `check_rules.py` and its CI step | RULE-001.5 |
| `open-markers` | VAL-001.9 |
| `portable-links` | VAL-001.10 |
| `closed-fences` | VAL-001.11 |
| `requirement-source` | VAL-001.12 |

## Alternatives considered

1. **A mapping document reviewed by hand** (smallest diff: one Markdown table from rows to rules, no script). Rejected. RULE-001 criterion 5 requires CI to fail on a gap, and a table nobody runs is how a dropped behavior goes unseen.
2. **An inventory, a criteria list, and a checker** (chosen). The added tool buys a failing build for every missing link, during construction per area and at release in full.
3. **Rule text in the inventory.** Rejected by the source: with the text in one distributed file and only its ID in the inventory, the text cannot drift.
4. **A requirements-traceability tool or an eval framework.** Rejected without a registry search: maintainer tooling is dependency-free (`AGENTS.md`), the links are three JSON lookups, and Kiro IDE needs a recorded manual run that a framework's own runner would not produce.

## Reuse inventory

- `specflow_helper/schema.py` (00004): `check_schema(instance: object, schema: dict, path: str = "$") -> list[str]`, for the session, eval, inventory, and criteria files.
- `specflow_helper/checks.py` (00004): `CHECKS` and `Finding`; T-071 adds entries, and the checker reads the keys.
- `tools/specflow/verify_release.py` (00002): the error-line format and the collect-then-exit pattern.
- `tests/specflow/release/` (00002) and `tests/specflow/contract/` (00004): the test patterns and the CI job.
- The two port plans, read as data.
- Searches: the repository holds one code module, `scripts/validate.py`, read in full; a search for `inventory|criteria|rule|eval|parity`, case-insensitive, over `scripts`, `.github`, `plugins`, and `templates` is recorded in the intake log. Nothing there maps rules to checks.

## Open decisions

No decision is open. Rulings of 2026-10-04 (design gates report), taken in above: D8, `ART-004.16` and `VAL-001.13` join the required list, which holds 33; and the three fixes of bundle B (a schema file beside the inventory and the criteria list, no source form of its own for behavior a `drop` ruling adds, and the reworded description of area `SKL`).

Choices the source left to the design, made above and listed for approval: the checker's command line, exit codes, and output lines; how a rule's `file` resolves; the five check names; the field lists of the session and eval formats; the examples' folder; and the CI step that lists finished areas.
