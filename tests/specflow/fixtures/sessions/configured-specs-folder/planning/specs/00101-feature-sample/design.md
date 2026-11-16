# Design: Import retries

## Overview

Failed rows go to a retry file that the next import reads first.

## Context and constraints

- The import runs once a night (Q1).

## Architecture

The importer writes failures to `retry.csv` and reads it at start.

## Module placement

| Path | New or edit | Task | Holds |
|---|---|---|---|
| `src/import/retry.py` | new | T-001 | the retry file |
| `src/import/log.py` | edit | T-002 | the failure rate |

## Components and interfaces

`retry.write(row)` and `retry.drain() -> list[Row]`.

## Data model

`retry.csv` holds one failed row per line, in the source's own columns.

## Data and control flow

Start, drain the retry file, import, write failures, log the rate.

## Error handling

| Condition | Required behavior |
|---|---|
| The retry file is unreadable | Stop the import and alert the operator |

## Security and privacy

Not applicable: the rows hold no personal data.

## Testing strategy

Unit tests for `retry.py`; one import test with a dropped connection.

## Rollout and migration

Not applicable: the retry file starts empty.

## Risks and edge cases

- A row fails twice: impact l, likelihood m; mitigation: keep it in the file; fallback: alert after three nights.

## Requirement traceability

| Design element | Criteria |
|---|---|
| `retry.py` | REQ-001.1, REQ-001.2 |
| Failure rate in the log | REQ-002.1 |
| Row volume | Portability |

## Alternatives considered

1. **A queue service.** Rejected: one file serves one nightly job.

## Reuse inventory

- The CSV reader the importer already uses.

## Open decisions

Not applicable: no decision is open.
