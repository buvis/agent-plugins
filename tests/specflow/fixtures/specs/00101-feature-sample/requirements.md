# Requirements: Import retries

Sources: docs/dev/project-management/intake/processed/00101-import-retries

## Purpose

Nightly imports lose rows when the source drops a connection. This spec keeps those rows.

## Scope

The nightly import job and its retry file. Live imports stay as they are.

## Assumptions

- The source sends at most 100,000 rows a night (Q1).

## Requirements

### REQ-001: Retry failed rows

Source: the idea

**User story:** As an operator, I want failed rows retried, so that a dropped connection loses no data.

#### Acceptance criteria

1. WHEN a row fails to import THE SYSTEM SHALL write it to the retry file.
2. WHEN the next import starts THE SYSTEM SHALL import the retry file first.

### REQ-002: Report the failure rate

Source: Q2

**User story:** As an operator, I want the failure rate in the import log, so that I can see when the source gets worse.

#### Acceptance criteria

1. WHEN an import ends THE SYSTEM SHALL log the share of failed rows.

## Non-functional requirements

- Under 0.1% of rows fail in a normal night.

## Risks

- The retry file grows without bound: impact m, likelihood l; mitigation: cap it at 10,000 rows; fallback: alert the operator.

## Out of scope

- Retrying live imports.
