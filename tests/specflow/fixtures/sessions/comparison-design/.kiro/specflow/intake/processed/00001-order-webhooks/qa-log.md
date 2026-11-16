# Q&A log: 00001 order-webhooks

## Intake (2026-10-14)

- Spec type: feature. Workflow order: requirements-first. Profile: standard (a public contract and a persistent store).

## Q1 - Retries (2026-10-14)

- Question: What should happen when a URL does not answer?
- Answer: "Try again a few times, then give up and show me."
- Reading: up to three retries with growing waits, then a visible failure.

## Requirements approval (2026-10-15)

- Artifact: `.kiro/specs/00001-order-webhooks/requirements.md`.
- Decision: approved by the developer. Question: "Do you approve the requirements?" Answer: "Yes."
