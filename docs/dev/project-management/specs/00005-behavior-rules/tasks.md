# Tasks: specflow behavior rules

The first sub-bullets of `Details:` and `Verify:` are carried from the source plan in intake item 00001. In them, `design §n` means the source design, `.kiro/specs` means the specs folder, and a task ID may belong to another spec; `docs/dev/project-management/reviews/2026-10-04-specflow-split-map.md` names the spec that now holds each section and each task. Lines written for this plan name a task of another spec with its spec, as in `T-030 (00006)`.

- [ ] T-070 Encode the behavior rule inventory
  - Requirements: RULE-001
  - Depends on: none
  - Location: `tools/specflow/rules/inventory.json`, `tools/specflow/rules/criteria.json`, `tools/specflow/rules/inventory.schema.json`, `tools/specflow/rules/criteria.schema.json`, `tools/specflow/check_rules.py`, `tests/specflow/rules/test_check_rules.py`, `.github/workflows/validate.yml`
  - Reuse: `check_schema` of `specflow_helper/schema.py` (00004) for the inventory and the criteria list; the error-line format and the collect-then-exit pattern of `tools/specflow/verify_release.py` (00002).
  - Contract: T-070 writes `plans` with the key `A` only and no `B:` source, so the checker does not read the second plan before its rows have rules; T-079 (00007) adds the key `B` and all its mappings in one change.
  - Details:
    - Turn every approved port and redesign row of Plan A, including the drops ruled redesign, into numbered `SR-<area>-NNN` rules routed by the table in design §5.4; split a row with structural and behavioral parts into two rules.
    - Write `tools/specflow/rules/inventory.json` (rule, file, kind, check, sources, optional criteria; no rule text), the independent `criteria.json` with exactly the 33 IDs the design lists (the 31 of design §5.4 plus `ART-004.16` and `VAL-001.13`, ruling D8), and `tools/specflow/check_rules.py` with its port-row, required-criterion, and rule/file/check failure conditions. Add an `--area` option under §5.4's construction limits. No slice exemptions.
    - Include `RVX` and advisory-script rules in the full release check; accept a `D:<date>#<n>` source for a rule that comes from a decision (design §5.4).
    - Map every required criterion to planned rule IDs and their existing check references, preserving original decisions and later rulings as sources; print criterion → rule → check coverage rows. Do not infer the required set from inventory entries or count a decision source as coverage.
    - Wire the check into maintainer CI.
    - Write a schema beside each file, `inventory.schema.json` and `criteria.schema.json`, applied with `check_schema`. Read plan rows as the design states: the strict header, eight cells split on an unescaped `|`, four classifications. Accept the three source forms `<plan key>:<row id>`, `D:<date>#<n>`, and `R:<criterion>`; a rule that cites a `drop` row fails.
    - Enter a planned check for every rule, `validator:<name>` for a structural rule, or `test:<path>::<test name>` where a ported script's tests carry it, and `evals/<rule-id>.json` for a behavioral one, since a rule with no check fails under any filter. The checker sets `sys.dont_write_bytecode` before it imports the shipped helper, and prints one line per plan with the number of rows it read.
    - CI gets two steps: the checker's tests, and `python3 tools/specflow/check_rules.py --area none` until the first area is finished. An unknown area is a usage error, exit 2.
  - Acceptance criteria: RULE-001 criteria 1, 2, 5
  - Verify:
    - checker fixtures map every approved Plan A row and no struck/drop row; seeded unmapped rows, absent checks/files, and duplicated IDs fail. The required set matches all 33 IDs of the design. Removing a whole criterion mapping while keeping its decision source, removing its check, omitting the list, or adding duplicate/unknown IDs fails with a targeted error. Shared rules and mixed-kind splits pass. Area filtering skips only other areas' runtime-file/check existence, not missing criterion mappings; unfiltered runs also reject missing cross-spec/advisory files and checks. Full-tree coverage gates T-063 (00001) after all references exist.
    - `tests/specflow/rules/test_check_rules.py` passes with the tests the design names for T-070, those for the conditions the design adds among them, and with one case each for four conditions the design states without a test name: the bytecode flag, the per-plan row-count line, a source that names an unknown row or plan, and a plan with no matrix table or with an empty classification.

- [ ] T-071 Add validator checks for the structural rules
  - Requirements: RULE-001; VAL-001; 00004 ART-001 criterion 10; 00004 WF-002 criterion 7
  - Depends on: T-070
  - Location: `plugins/specflow/skills/spec-workflow/scripts/specflow_helper/checks.py`, `plugins/specflow/skills/spec-workflow/references/validation-rules.md`, `tests/specflow/contract/test_checks.py`, `tools/specflow/rules/inventory.json`, `.github/workflows/validate.yml`
  - Reuse: `CHECKS`, `Finding`, and the marker scanner of `specflow_helper` (00004); where a check of 00004 already enforces a structural rule, the inventory names that check's key and no second check is written.
  - Contract: T-071 registers these checks in `CHECKS`, each with its phases, and adds one more for each structural rule of the inventory that no check of 00004 already enforces, named in kebab case for what it proves; where a 00004 check enforces the rule, the inventory names that check's key.
  - Details:
    - Add a named validator check for each structural rule in the inventory, including placeholders per artifact and the `Not applicable: <reason>` form (ART-001.10), the marker list for the WF-002.7 gate (VAL-001.9), the path and wiki-link warnings (VAL-001.10), the unclosed-fence failure (VAL-001.11), and the missing-`Source:` warning (VAL-001.12).
    - Tag each structural rule's text with its ID in `validation-rules.md` (area `VAL`) unless a phase reference already carries it.
    - The five named checks are `placeholders`, `open-markers`, `portable-links`, `closed-fences`, and `requirement-source`, with the levels of the design's table. `open-markers` is registered from `requirements` on, reads only the artifacts upstream of the phase's own artifact, and names the upstream file in each finding.
    - T-070 entered a planned check for every structural rule: for each one whose check is a `validator:` entry, build the check under that name, and edit `inventory.json` only where a name changed or a check of 00004 is reused. Change the CI step to `--area VAL`.
  - Acceptance criteria: RULE-001 criterion 3; VAL-001 criteria 9, 10, 11, 12; 00004 ART-001 criterion 10; 00004 WF-002 criterion 7
  - Verify:
    - `check_rules.py --area VAL` passes, which finds the checks of area `VAL`; seeded defects fail each check with file, rule, and fix; an artifact with an unclosed fence fails with an error finding; warnings never change the exit status. That such an artifact cannot be approved follows from the approval procedure of 00006, which needs a run with no error.
    - `tests/specflow/contract/test_checks.py` holds one seeded defect per check, plus `test_every_structural_rule_check_is_registered`, which covers every structural rule whose check is a `validator:` entry, and `test_open_markers_reads_only_upstream_artifacts`. One more case: an `acceptedMarkers` entry clears an `open-markers` finding, and the finding returns when the accepted line changes.

- [ ] T-069 Define the session and eval formats
  - Requirements: RULE-001
  - Depends on: T-070
  - Location: `tests/specflow/evals/schemas/session.schema.json`, `tests/specflow/evals/schemas/eval.schema.json`, `tests/specflow/evals/examples/session.json`, `tests/specflow/evals/examples/eval.json`, `tools/specflow/check_rules.py`, `tests/specflow/rules/test_eval_formats.py`
  - Reuse: `check_schema` (00004), which has no keyword for "one or more": `check_rules.py` itself rejects an eval with no assertion.
  - Contract: T-069 defines the two test formats; both are checked with `check_schema` of 00004.
  - Details:
    - Define the formats of design §15: a session (`tests/specflow/evals/sessions/<name>.json`, a fixture repository plus scripted developer turns) and an eval (`tests/specflow/evals/SR-<area>-NNN.json`, one rule's assertions over one named session), with deterministic assertion kinds by default and a marked rubric kind.
    - Write one JSON Schema and one example of each; every later reference task writes its eval records in these formats.
    - Give the session and the eval the fields of the design's two tables: a session has `turns` with `developer`, optional `edit`, and optional `expects`, and exactly one of `fixture` and `continues`; an eval names its `rule`, its `session`, and one or more assertions. The fifteen assertion kinds are the design's list; every kind but `rubric` is deterministic, and a rubric is judged by the developer by hand (ruling D10).
    - `check_rules.py` rejects a session or eval whose name field differs from its file name; the two files under `examples/` are exempt. An `evals/<rule-id>.json` check resolves only to a file that validates and that names a session file that exists.
  - Acceptance criteria: RULE-001 criterion 3
  - Verify:
    - both examples validate against their schemas; `check_rules.py` resolves an `evals/<rule-id>.json` check only to a file that validates; a malformed eval record fails with a targeted message, also through a required-criterion mapping. Several criteria may share a rule's eval without requiring extra host-session runs.
    - `tests/specflow/rules/test_eval_formats.py` passes with the tests the design names for T-069, and with one case for an eval that names a session file that does not exist.

## Completion criteria

- [ ] Every task above is checked, each with its `Outcome:` line.
- [ ] CI is green on the final commit: the checker's tests, `python3 tools/specflow/check_rules.py --area VAL`, the contract tests, and the release check.
- [ ] `python3 tools/specflow/check_rules.py --area VAL` prints a coverage row for each of the 33 required criteria.
