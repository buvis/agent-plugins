"""Tests for ETag tolerance in CalDAV create/update flows.

PRD 00001 §1.4: some servers (older Radicale, some SOGo configs) omit the
ETag header on PUT. The client must re-read via GET, and degrade to
field-level verification with a warning when the server still exposes no
ETag. ``verify_etag`` itself stays strict.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import pytest

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalDAVClient
from calcard_mcp.config import AppConfig, ServerConfig
from calcard_mcp.errors import WriteVerificationError

from .conftest import FakeCalDAV, build_fake_event

_BASE_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VEVENT
UID:u1@calcard
DTSTAMP:20260501T000000Z
DTSTART:20260501T090000Z
DTEND:20260501T100000Z
SUMMARY:Edited
DESCRIPTION:Edited description
LOCATION:Edited location
END:VEVENT
END:VCALENDAR
"""


def _wire_fake(fake_caldav: FakeCalDAV, event: Any) -> None:
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event


def _verify_server(app_config: AppConfig, *, verify_writes: bool = True) -> ServerConfig:
    base = app_config.server
    return ServerConfig(
        base_url=base.base_url,
        verify_tls=base.verify_tls,
        timeout=base.timeout,
        verify_writes=verify_writes,
    )


def test_update_event_succeeds_when_load_refreshes_etag(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Server sets etag to None on PUT but populates it on subsequent GET/load."""
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _verify_server(app_config),
    )
    event = build_fake_event(data=_BASE_ICAL, etag='"before-edit"')
    call_count = {"n": 0}

    def _load_populates_etag() -> None:
        # First call (inside _verify_event) does nothing; after save() cleared etag,
        # a follow-up load restores it with a fresh value.
        call_count["n"] += 1
        event.etag = '"after-edit"'

    event.load.side_effect = _load_populates_etag

    def _save_drops_etag() -> None:
        event.etag = None  # simulate server returning empty ETag on PUT

    event.save.side_effect = _save_drops_etag
    _wire_fake(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        summary="Edited",
        description="Edited description",
        location="Edited location",
    )
    assert event.etag == '"after-edit"'


def test_update_event_warns_when_etag_stays_empty(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Server never exposes an ETag; the write succeeds and a warning is logged."""
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _verify_server(app_config),
    )
    event = build_fake_event(data=_BASE_ICAL, etag='"before-edit"')

    event.save.side_effect = lambda: setattr(event, "etag", None)
    event.load.side_effect = lambda: None  # load does not refresh etag
    _wire_fake(fake_caldav, event)

    with caplog.at_level(logging.WARNING, logger="calcard_mcp.caldav_client"):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            summary="Edited",
            description="Edited description",
            location="Edited location",
        )
    assert any(
        "no ETag" in record.message and "bob" in record.message for record in caplog.records
    ), "expected a warning about the missing ETag"


def test_update_event_still_fails_when_etag_unchanged_after_write(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """If ETag remains identical post-write, ``verify_etag`` must still reject."""
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _verify_server(app_config),
    )
    event = build_fake_event(data=_BASE_ICAL, etag='"same"')
    # save does not change the etag, load leaves it identical
    event.save.side_effect = lambda: None
    event.load.side_effect = lambda: None
    _wire_fake(fake_caldav, event)

    with pytest.raises(WriteVerificationError):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            summary="Edited",
            description="Edited description",
            location="Edited location",
        )


def test_create_event_warns_when_server_returns_empty_etag(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _verify_server(app_config),
    )
    # Wire the fake: save_event returns a fresh event whose etag is never populated.
    created = build_fake_event(
        data=_BASE_ICAL.replace("Edited", "Created"),
        etag=None,
    )
    created.load.side_effect = lambda: None

    fake_calendar: Any = fake_caldav.resolve_calendar(url="https://dav.example.com/bob/cal/")

    def _save_event(_ical: str) -> Any:
        return created

    fake_calendar.save_event = _save_event
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_calendar

    with caplog.at_level(logging.WARNING, logger="calcard_mcp.caldav_client"):
        client.create_event(
            calendar_url="https://dav.example.com/bob/cal/",
            summary="Created",
            start=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
            end=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
            description="Created description",
            location="Created location",
        )
    assert any("no ETag" in record.message for record in caplog.records)
