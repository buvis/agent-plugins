# Requirements: Retry uploads

Sources: .kiro/specflow/intake/processed/00001-retry-uploads/

## Purpose

Retry a failed upload to the archive server.

## Requirements

### REQ-001: Retry uploads

Source: the idea

**User story:** As a user, I want this change, so that retry a failed upload to the archive server.

#### Acceptance criteria

1. WHEN an upload fails with a timeout THE SYSTEM SHALL retry it up to three times with a growing wait.
2. WHEN the server answers THE SYSTEM SHALL read its ISO 8601 `stored_at` timestamp.
