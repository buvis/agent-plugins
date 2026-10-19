# Requirements: CSV import errors

Sources: .kiro/specflow/intake/processed/00001-csv-import-errors/

## Purpose

Show which lines of an uploaded CSV were rejected.

## Requirements

### REQ-001: CSV import errors

Source: the idea

**User story:** As a user, I want this change, so that show which lines of an uploaded CSV were rejected.

#### Acceptance criteria

1. WHEN an upload has rejected lines THE SYSTEM SHALL list each rejected line with its number and reason.
2. THE SYSTEM SHALL accept files of at most 1,000 rows (guess).
