# Profile: standard

The default depth, mapped to AWS AI-DLC depth Standard. Read the AWS passages marked `[standard]` or `[both]`.

Use it whenever any of these is true, unless the developer explicitly decides otherwise: the change is security-sensitive, architectural, a data migration, a public API, cross-component, about concurrency or timing, must match an existing implementation's behavior, invents an algorithm or a predicate, or is destructive.

## Questions

About 3 to 12 content questions per artifact, one at a time. At intake, all topics share one budget. The range is guidance, not a cap: ask what materially changes scope or behavior, and stop when nothing does.

## What each phase runs

| Phase | Standard runs |
|---|---|
| Intake | Repository discovery: pattern scan, dependency map, conventions, and integration surface, with a coverage statement |
| Requirements | Complete requirements analysis: every requirement sourced, risks listed, and a contradiction check across the requirements |
| Design | A full technical design: every section of the design shape, alternatives including the smallest diff, reuse searches, and exact contracts |
| Tasks | Task decomposition with sizing checks, copied contracts, and owned verification |
| Implementation | One task at a time, each checked after its own verification |
| Verification | Tests and checks proportionate to the changed behavior, mapped to tasks and requirements |

A bugfix spec runs the same depth and keeps its own shape: `bugfix.md`, the bugfix design, and the four fixed tasks. Discovery reads the code around the defect before the design is drafted.
