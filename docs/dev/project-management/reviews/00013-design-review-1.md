# AP00013 design review 1

Reviewer: isolated native gpt-6.1-sol / high, OpenAI, `/root/design_review_1`.
Source persona slot: design-solution dispatch 1 (host-mapped native).

- **Blocker — Review-close proposals are not bound to validated evidence.** The design checks chosen findings against separately supplied review text, without binding the text to the validated review-file artifact or its rows to attributed evidence findings. Bind exact bytes and findings before generating proposals.
- **Blocker — Staging does not bind PRD content to expected identity.** The design validates expected context but does not hash supplied PRD content against its independent binding. Specify exact UTF-8 serialization and refuse mismatch before output.
- **Cardinal sin — Verification log storage is unbounded.** The in-memory cap does not limit streamed disk logs, and caller timeouts have no finite maximum. Bound disk bytes and timeout; terminate and reap on overflow, and prevent reuse.
- **Non-blocker — Staging path validation may race writes.** Only verification explicitly requires descriptor-relative no-follow writes. A staging parent directory could change between validation and ordinary writing. Consider a shared safe writer.
- **Question — Declared input references lack a representation.** `input_texts` has string values, with no content/path discriminator; verification has no separate artifact-root parameter. Clarify supported representation and root semantics.

The adopted design records the three mandatory fixes and retains the non-blocker and question.
