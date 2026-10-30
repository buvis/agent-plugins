# AP00018 remaining-work replan 1

Original review base remains `535e433cf83351bca3c12c9e87c5da08eed8d666`.
No completion review ran. The 50,000-byte dispatch cap and 75,000-token
replan estimate ceiling remain unchanged.

Completed task 1 is retained with its original attempts, rather than executed
again. Task 2's tests from `b219b14` and `a2a7b72` remain contributing work.
Their original Devon exploit/strengthening evidence remains in `00018-build.md`
and the raw task 2 reports. The first remaining task moves their 44 methods
without changing their ASTs; it adds no behavioral assertions. Tess and Devon
are not repeated for that pure test relocation. Subsequent runtime tasks use
the preserved tests and their full tier gates, including Devon.

| Current task | Scope | Estimated tokens | Tier/reason |
| --- | --- | ---: | --- |
| 1 | Retained completed characterization | 63296 | original opus |
| 2 | Split retained tests by API | 70573 | opus/floor |
| 3 | Strict schema | 60238 | opus/contract |
| 4 | Atomic store | 59590 | opus/contract |
| 5 | Root containment | 59417 | opus/contract |
| 6 | Bootstrap, snapshot and intent recovery | 62967 | opus/contract |
| 7 | Owner lease and bounded receipt admission | 62518 | opus/contract |
| 8 | Bundle export and installed isolation | 59546 | opus/contract |
| 9 | Package provenance registration | 69434 | opus/contract |
| 10 | Support/recovery documentation | 63484 | opus/floor |

Estimates use existing expected-writable file bytes / 4, task body bytes / 4,
55,000 overhead and a conservative 3,500-token PRD slice allowance. New
runtime files have no existing bytes. Generated source-map output is never
an unbounded worker input; its snapshot/full-diff protocol remains mandatory.
The classifier ran for each remaining task with the PRD's `default_model:
opus` floor. Canonical `check-plan` passed via the pre-existing explicit
`plan_expansion: allow`; no override was introduced here.

The PRD supplies decomposition and dependencies. The remaining tasks follow
that order. Bootstrap is independently usable/testable before owner operations;
owner handlers remain unavailable until implemented. Schema, store and root
tests collect independently after the mechanical relocation. Interfaces and
their implementations remain coupled; no split was manufactured for Qwen.
There are no new PRD/design conflicts or unresolved planning questions.

Qwen planning probe: healthy, approved `unsloth/Qwen3.8-27B-GGUF:UD-Q6_K_XL`.
The Opus floor excludes every task from Qwen. Source native Claude Opus
dispatches map to native `gpt-6.1-sol` / high. Driver provider mapping explicitly
supports independent Anthropic review for OpenAI implementation. No Gemini
route is selected. Raw native metadata is retained per dispatched worker;
requested configuration alone is not treated as observed model evidence.

Prior model/test contributions must remain in the eventual whole-change audit,
including completed characterization's `gpt-6-astra` retry and retained test
authors' `gpt-6.1-sol`. Replanning does not erase those contributions.
