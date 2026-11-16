# Context efficiency

T-055 remains pending live Claude Code records. Codex and Kiro: not measured,
as approved for 00009. File-path observations cannot prove which passages were
read. Missing paths on incomplete telemetry remain not measured, not absent.

## Sizes

Measured from repository files on 2026-11-16, before the runner freeze.
These are complete file sizes, including frontmatter where present.

| File | Lines | Bytes |
|---|---:|---:|
| `plugins/specflow/skills/convert-prd/SKILL.md` | 29 | 4339 |
| `plugins/specflow/skills/convert-prd/references/conversion.md` | 61 | 8563 |
| `plugins/specflow/skills/spec-workflow/SKILL.md` | 103 | 11334 |
| `plugins/specflow/skills/spec-workflow/references/artifact-contract.md` | 246 | 17798 |
| `plugins/specflow/skills/spec-workflow/references/aws/adaptation.md` | 119 | 8250 |
| `plugins/specflow/skills/spec-workflow/references/aws/design.md` | 108 | 8151 |
| `plugins/specflow/skills/spec-workflow/references/aws/implementation.md` | 99 | 6655 |
| `plugins/specflow/skills/spec-workflow/references/aws/requirements.md` | 168 | 11078 |
| `plugins/specflow/skills/spec-workflow/references/aws/verification.md` | 92 | 5891 |
| `plugins/specflow/skills/spec-workflow/references/phases/design.md` | 40 | 6387 |
| `plugins/specflow/skills/spec-workflow/references/phases/implementation.md` | 16 | 2835 |
| `plugins/specflow/skills/spec-workflow/references/phases/intake.md` | 109 | 16421 |
| `plugins/specflow/skills/spec-workflow/references/phases/requirements.md` | 81 | 10275 |
| `plugins/specflow/skills/spec-workflow/references/phases/tasks.md` | 52 | 8769 |
| `plugins/specflow/skills/spec-workflow/references/phases/verification.md` | 18 | 2378 |
| `plugins/specflow/skills/spec-workflow/references/profiles/quick.md` | 24 | 2008 |
| `plugins/specflow/skills/spec-workflow/references/profiles/standard.md` | 22 | 1636 |
| `plugins/specflow/skills/spec-workflow/references/review/core.md` | 95 | 17030 |
| `plugins/specflow/skills/spec-workflow/references/review/cross-spec.md` | 119 | 15588 |
| `plugins/specflow/skills/spec-workflow/references/review/design/anti-patterns.md` | 5 | 1532 |
| `plugins/specflow/skills/spec-workflow/references/review/design/cardinal-sins.md` | 20 | 1753 |
| `plugins/specflow/skills/spec-workflow/references/review/design/checklist.md` | 33 | 9132 |
| `plugins/specflow/skills/spec-workflow/references/review/design/lenses.md` | 12 | 3774 |
| `plugins/specflow/skills/spec-workflow/references/review/design/pre-pass.md` | 10 | 3101 |
| `plugins/specflow/skills/spec-workflow/references/review/design/stress-tests.md` | 5 | 1170 |
| `plugins/specflow/skills/spec-workflow/references/review/design/techniques.md` | 31 | 9132 |
| `plugins/specflow/skills/spec-workflow/references/review/design/triage.md` | 40 | 9294 |
| `plugins/specflow/skills/spec-workflow/references/review/requirements.md` | 107 | 14831 |
| `plugins/specflow/skills/spec-workflow/references/state-contract.md` | 70 | 6449 |
| `plugins/specflow/skills/spec-workflow/references/validation-rules.md` | 46 | 6296 |

## Skill sections

Lines and bytes exclude the delimiter lines.

| Section | Lines | Bytes |
|---|---:|---:|
| `plugins/specflow/skills/convert-prd/SKILL.md` (frontmatter) | 3 | 346 |
| `plugins/specflow/skills/convert-prd/SKILL.md` (body) | 26 | 3987 |
| `plugins/specflow/skills/spec-workflow/SKILL.md` (frontmatter) | 3 | 483 |
| `plugins/specflow/skills/spec-workflow/SKILL.md` (body) | 100 | 10845 |

## Loading

Pending the frozen Claude Code run. Compare each phase/profile and design-review
tier against the routing tables in the shipped skill; list observed unexpected
references as findings. Do not infer absence from incomplete read events.
