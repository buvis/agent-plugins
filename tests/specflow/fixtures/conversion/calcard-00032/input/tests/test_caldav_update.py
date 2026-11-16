"""Tests for :meth:`calcard_mcp.caldav_client.CalDAVClient.update_event`.

PRD 00001 §1.3: dict-assignment on an ``icalendar.Event`` does not wrap in
``vText`` and can accumulate duplicate properties. Replace with
``pop``/``add`` so a second update does not leave two SUMMARY lines in the
stored iCal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from icalendar import Calendar as ICalCalendar

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalDAVClient
from calcard_mcp.config import AppConfig, ServerConfig
from calcard_mcp.errors import ProtocolError

from .conftest import FakeCalDAV, build_fake_event

_BASE_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VEVENT
UID:u1@calcard
DTSTAMP:20260501T000000Z
DTSTART:20260501T090000Z
DTEND:20260501T100000Z
SUMMARY:Original
DESCRIPTION:Original description
LOCATION:Original location
END:VEVENT
END:VCALENDAR
"""

_ALL_DAY_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VEVENT
UID:u1@calcard
DTSTAMP:20260501T000000Z
DTSTART;VALUE=DATE:20260501
DTEND;VALUE=DATE:20260502
SUMMARY:All-day Original
END:VEVENT
END:VCALENDAR
"""


def _no_verify_server(server: ServerConfig) -> ServerConfig:
    return ServerConfig(
        base_url=server.base_url,
        verify_tls=server.verify_tls,
        timeout=server.timeout,
        verify_writes=False,
    )


def _install_event(
    fake_caldav: FakeCalDAV,
    *,
    url: str,
    ical_data: str,
) -> Any:
    event = build_fake_event(data=ical_data, url=url)
    fake_caldav.events_by_uid["u1@calcard"] = event
    return event


def _count_property(ical_text: str, name: str) -> int:
    count = 0
    for line in ical_text.splitlines():
        stripped = line.split(";", 1)[0].split(":", 1)[0].strip()
        if stripped == name:
            count += 1
    return count


def test_update_event_replaces_summary_rather_than_appending(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """PRD 1.3: a second update_event call must not produce two SUMMARY lines."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data=_BASE_ICAL,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        summary="Second",
    )
    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        summary="Third",
    )

    assert _count_property(event.data, "SUMMARY") == 1
    parsed: Any = ICalCalendar.from_ical(event.data)
    vevents = list(parsed.walk("VEVENT"))
    assert len(vevents) == 1
    assert str(vevents[0].get("SUMMARY")) == "Third"


def test_update_event_replaces_all_mutable_fields(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data=_BASE_ICAL,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event

    new_start = datetime(2026, 6, 10, 14, 0, tzinfo=UTC)
    new_end = datetime(2026, 6, 10, 15, 0, tzinfo=UTC)
    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        summary="New summary",
        description="New description",
        location="New location",
        start=new_start,
        end=new_end,
    )

    for name in ("SUMMARY", "DESCRIPTION", "LOCATION", "DTSTART", "DTEND"):
        assert _count_property(event.data, name) == 1, f"{name} should appear exactly once"

    parsed: Any = ICalCalendar.from_ical(event.data)
    vevent = next(iter(parsed.walk("VEVENT")))
    assert str(vevent.get("SUMMARY")) == "New summary"
    assert str(vevent.get("DESCRIPTION")) == "New description"
    assert str(vevent.get("LOCATION")) == "New location"


def test_update_event_preserves_unspecified_fields(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data=_BASE_ICAL,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        summary="Only summary changed",
    )

    parsed: Any = ICalCalendar.from_ical(event.data)
    vevent = next(iter(parsed.walk("VEVENT")))
    assert str(vevent.get("SUMMARY")) == "Only summary changed"
    assert str(vevent.get("DESCRIPTION")) == "Original description"
    assert str(vevent.get("LOCATION")) == "Original location"


@pytest.mark.parametrize("field_name", ["SUMMARY", "DESCRIPTION", "LOCATION"])
def test_update_event_produces_valid_ical_without_duplicate(
    field_name: str,
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Sanity-check: for every mutable string field, a single update yields a single line."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data=_BASE_ICAL,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event

    kwargs: dict[str, Any] = {field_name.lower(): "New value"}
    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        **kwargs,
    )

    assert _count_property(event.data, field_name) == 1


def _install_default_event(
    fake_caldav: FakeCalDAV,
    *,
    ical_data: str = _BASE_ICAL,
) -> Any:
    event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data=ical_data,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event
    return event


def test_update_event_rejects_partial_start_that_makes_end_le_start(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """PRD 00010 cycle-1 review (Bob 🟠): ``end <= start`` guard must also fire
    when only ``start`` is patched against an existing ``DTEND`` that the new
    start would push past."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    _install_default_event(fake_caldav)

    # Existing event runs 09:00-10:00. Pushing start to 11:00 (no end change)
    # would leave end (10:00) <= start (11:00).
    with pytest.raises(ValueError, match="event end must be after start"):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            start=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
        )


def test_update_event_rejects_partial_end_that_makes_end_le_start(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Symmetric to the start-only case: pulling end behind the existing start
    must surface the same guard."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    _install_default_event(fake_caldav)

    # Existing event runs 09:00-10:00. Pulling end back to 08:00 would leave
    # end (08:00) <= start (09:00).
    with pytest.raises(ValueError, match="event end must be after start"):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            end=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
        )


def test_update_event_accepts_partial_start_that_keeps_ordering(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Partial-start updates that keep ``end > start`` must still succeed."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_default_event(fake_caldav)

    # Pull start back to 08:00; existing end (10:00) is still after it.
    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        start=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
    )

    parsed: Any = ICalCalendar.from_ical(event.data)
    vevent = next(iter(parsed.walk("VEVENT")))
    assert vevent.get("DTSTART").dt == datetime(2026, 5, 1, 8, 0, tzinfo=UTC)
    assert vevent.get("DTEND").dt == datetime(2026, 5, 1, 10, 0, tzinfo=UTC)


def test_update_event_accepts_partial_end_that_keeps_ordering(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Partial-end updates that keep ``end > start`` must still succeed."""
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_default_event(fake_caldav)

    # Push end forward to 11:00; existing start (09:00) is still before it.
    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        end=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
    )

    parsed: Any = ICalCalendar.from_ical(event.data)
    vevent = next(iter(parsed.walk("VEVENT")))
    assert vevent.get("DTSTART").dt == datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
    assert vevent.get("DTEND").dt == datetime(2026, 5, 1, 11, 0, tzinfo=UTC)


def test_update_event_partial_end_against_all_day_event_raises_value_error(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """PRD 00010 cycle-2 review (Alice/Diana 🟠): when the existing VEVENT is
    an all-day event (DATE-valued DTSTART/DTEND), a partial update that
    supplies only a tz-aware ``end`` earlier than the existing all-day start
    must raise the structured ``ValueError`` (not ``TypeError`` from a
    ``date`` versus ``datetime`` comparison).
    """
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    _install_default_event(fake_caldav, ical_data=_ALL_DAY_ICAL)

    # Existing all-day event spans 2026-05-01 → 2026-05-02 (DATE-valued).
    # Pulling end back to 2026-04-29 12:00 UTC is clearly before any tz
    # interpretation of the all-day start; the guard must surface ValueError
    # rather than letting a date/datetime comparison raise TypeError.
    with pytest.raises(ValueError, match="event end must be after start"):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            end=datetime(2026, 4, 29, 12, 0, tzinfo=UTC),
        )


def test_update_event_partial_start_against_all_day_event_raises_value_error(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Symmetric all-day case: pushing start past the existing all-day end
    must also surface the ValueError without the date/datetime TypeError.
    """
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    _install_default_event(fake_caldav, ical_data=_ALL_DAY_ICAL)

    # Existing all-day event ends at 2026-05-02 (midnight). Pushing start to
    # 2026-05-04 12:00 UTC is clearly after any tz interpretation of the
    # all-day end.
    with pytest.raises(ValueError, match="event end must be after start"):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            start=datetime(2026, 5, 4, 12, 0, tzinfo=UTC),
        )


def test_update_event_wraps_malformed_ical_into_protocol_error(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """If the server returns iCal text that ``icalendar`` cannot parse,
    :meth:`update_event` must surface :class:`ProtocolError` instead of
    leaking the raw library exception. Mirrors the cycle-1 fix that wrapped
    ``vobject.readOne`` in ``update_contact``.
    """
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    bogus_event = _install_event(
        fake_caldav,
        url="https://dav.example.com/bob/cal/u1.ics",
        ical_data="NOT A VCALENDAR",
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = bogus_event

    with pytest.raises(ProtocolError):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            summary="Anything",
        )
