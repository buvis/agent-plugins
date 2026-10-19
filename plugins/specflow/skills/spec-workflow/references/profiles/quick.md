# Profile: quick

The light depth, mapped to AWS AI-DLC depth Minimal. Read the AWS passages marked `[quick]` or `[both]`.

Recommend it only when requirement clarity, scope breadth, codebase impact, and problem complexity are all low. A change that is security-sensitive, architectural, a data migration, a public API, cross-component, about concurrency or timing, must match an existing implementation's behavior, invents an algorithm or a predicate, or is destructive takes `standard` instead, unless the developer explicitly decides otherwise.

Quick never drops an artifact: a feature spec still writes `requirements.md`, `design.md`, and `tasks.md`, and a bugfix spec `bugfix.md`, `design.md`, and `tasks.md`. The gates are the same as in `standard`.

## Questions

About 0 to 2 content questions per artifact, one at a time. At intake, all topics share one budget. Before you need more than about two, explain what remains and propose `standard`; change the profile only when the developer agrees. If the developer keeps `quick`, agree on the extra questions, narrow the scope, or record the rest as unresolved questions. Never invent an answer to stay within the range.

## What each phase runs

| Phase | Quick runs |
|---|---|
| Intake | Targeted discovery: only the files and conventions the change touches, with a coverage statement |
| Requirements | Concise requirements, each still sourced |
| Design | A minimal design that keeps every section, names the existing pattern it reuses, and says why no broader design is needed |
| Tasks | The same task checks as `standard`, with concise task text |
| Implementation | One task at a time, each checked after its own verification |
| Verification | Regression verification: the tests the changed behavior needs, and the existing suite still green |

A bugfix spec keeps its full shape under `quick`: the design trims prose, never the bugfix sections or the four tasks, and discovery reads the code around the defect before the design is drafted.
