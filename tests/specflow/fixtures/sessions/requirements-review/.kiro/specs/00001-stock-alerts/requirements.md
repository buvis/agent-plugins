# Requirements: Stock alerts

Sources: .kiro/specflow/intake/processed/00001-stock-alerts/

## Purpose

Warn the shop owner when a product is about to run out, so that it can be reordered before the shelf is empty.

## Scope

Alerts for products whose stock falls under a threshold. Alerts go to the shop owner by email.

## Assumptions

- Stock counts are already kept per product in `src/inventory.py` (source: the repository).
- The threshold is one number for the whole shop; whether it should be per product is still to be decided.

## Requirements

### REQ-001: Low-stock alert

Source: the idea

**User story:** As a shop owner, I want an alert when a product runs low, so that I can reorder it in time.

#### Acceptance criteria

1. WHEN a product's stock falls under the threshold THE SYSTEM SHALL send the shop owner an email naming the product and its stock.
2. THE SYSTEM SHALL send the alert within one minute of the stock change.
3. THE SYSTEM SHALL alert quickly and reliably.
4. THE SYSTEM SHALL send the alert through the Twilio SMS API.

### REQ-002: Alert history

Source: Q2

**User story:** As a shop owner, I want to see past alerts, so that I can spot products that run out often.

#### Acceptance criteria

1. THE SYSTEM SHALL keep every alert in one CSV file per shop, appended forever and never moved.
2. THE SYSTEM SHALL export the history and import a history file from another shop.

### REQ-003: Nightly digest

Source: the idea

**User story:** As a shop owner, I want alerts batched, so that I am not interrupted during the day.

#### Acceptance criteria

1. THE SYSTEM SHALL send all alerts of the day in one email at 22:00.

### REQ-004: Dark mode

Source: the idea

**User story:** As a shop owner, I want the admin page in dark mode, so that it is easier on the eyes at night.

#### Acceptance criteria

1. WHEN the shop owner enables dark mode THE SYSTEM SHALL show the admin page with a dark theme.

### REQ-005: Run-out date

Source: Q3

**User story:** As a shop owner, I want the alert to say when the product will run out, so that I can plan the reorder.

#### Acceptance criteria

1. THE SYSTEM SHALL take the run-out date from the existing inventory forecast service.

## Non-functional requirements

- The alert code is written in Rust.
- The alert channel is one of a fixed list: email, and nothing else.

## Risks

- Email delivery fails silently: impact m, likelihood m; mitigation: log each send; fallback: show the alert on the admin page.

## Out of scope

- Any channel but email; the alert code may assume email.
- Dark mode for the public shop pages.

## Unresolved questions

- None.
