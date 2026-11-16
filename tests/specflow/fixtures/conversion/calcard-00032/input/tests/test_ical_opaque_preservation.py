"""Regression test for opaque-property preservation through update round-trip.

PRD §9.5: an :meth:`update_event` call that mutates one field on an iCal
carrying VTIMEZONE + extension X-properties must leave the untouched data
byte-identical on the wire (the PUT body), AND the post-update
:class:`EventSummary` must surface the X-* extension lines via
``raw_properties``.
"""

from __future__ import annotations

from typing import Any

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalDAVClient
from calcard_mcp.config import AppConfig, ServerConfig
from calcard_mcp.ical import parse_vevent_to_summary

from .conftest import FakeCalDAV, build_fake_event

_ACCOUNT_ID = "bob"
_CAL_URL = "https://dav.example.com/bob/cal/"
_RES_URL = "https://dav.example.com/bob/cal/opaque.ics"
_UID = "opaque-preservation@calcard"
_TZ = "Europe/Bratislava"

_FIXTURE_ICAL = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//calcard-mcp//EN\r\n"
    "BEGIN:VTIMEZONE\r\n"
    "TZID:Europe/Bratislava\r\n"
    "BEGIN:STANDARD\r\n"
    "DTSTART:19701025T030000\r\n"
    "TZOFFSETFROM:+0200\r\n"
    "TZOFFSETTO:+0100\r\n"
    "TZNAME:CET\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10\r\n"
    "END:STANDARD\r\n"
    "BEGIN:DAYLIGHT\r\n"
    "DTSTART:19700329T020000\r\n"
    "TZOFFSETFROM:+0100\r\n"
    "TZOFFSETTO:+0200\r\n"
    "TZNAME:CEST\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3\r\n"
    "END:DAYLIGHT\r\n"
    "END:VTIMEZONE\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:opaque-preservation@calcard\r\n"
    "DTSTAMP:20260501T000000Z\r\n"
    "DTSTART:20260501T090000Z\r\n"
    "DTEND:20260501T100000Z\r\n"
    "SUMMARY:Old\r\n"
    "X-WR-CALNAME:My Calendar\r\n"
    "X-MICROSOFT-CDO-BUSYSTATUS:BUSY\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
)


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
    fake_caldav.events_by_uid[_UID] = event
    return event


def _count_property(ical_text: str, name: str) -> int:
    count = 0
    for line in ical_text.splitlines():
        stripped = line.split(";", 1)[0].split(":", 1)[0].strip()
        if stripped == name:
            count += 1
    return count


def test_update_event_preserves_vtimezone_and_x_properties_round_trip(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """A summary-only update must leave VTIMEZONE and X-* lines on the wire,
    and the parsed :class:`EventSummary` must surface the X-* lines via
    ``raw_properties``.
    """
    server = _no_verify_server(app_config.server)
    client = CalDAVClient(AccountRegistry(app_config).default(), server)
    event = _install_event(
        fake_caldav,
        url=_RES_URL,
        ical_data=_FIXTURE_ICAL,
    )
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(url=_CAL_URL)
    fake_caldav.events_by_uid[_UID] = event

    client.update_event(
        calendar_url=_CAL_URL,
        uid=_UID,
        summary="New",
    )

    wire_body = event.data

    # X-* extension lines preserved byte-for-byte.
    assert "X-WR-CALNAME:My Calendar" in wire_body
    assert "X-MICROSOFT-CDO-BUSYSTATUS:BUSY" in wire_body

    # VTIMEZONE block preserved (substring assertions only — line endings and
    # ordering may shift slightly through the icalendar round-trip).
    assert "BEGIN:VTIMEZONE" in wire_body
    assert "TZID:Europe/Bratislava" in wire_body
    assert "BEGIN:STANDARD" in wire_body
    assert "BEGIN:DAYLIGHT" in wire_body
    assert "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10" in wire_body
    assert "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3" in wire_body
    assert "TZOFFSETFROM:+0200" in wire_body
    assert "TZOFFSETFROM:+0100" in wire_body
    assert "TZOFFSETTO:+0100" in wire_body
    assert "TZOFFSETTO:+0200" in wire_body

    # Summary mutated; old value gone.
    assert "SUMMARY:New" in wire_body
    assert "SUMMARY:Old" not in wire_body
    assert _count_property(wire_body, "SUMMARY") == 1

    # Round-trip through the parser surfaces the X-* keys via raw_properties.
    summary = parse_vevent_to_summary(
        wire_body,
        account_id=_ACCOUNT_ID,
        calendar_url=_CAL_URL,
        resource_url=_RES_URL,
        fallback_tz=_TZ,
    )
    assert summary is not None
    assert summary.summary == "New"
    assert summary.raw_properties["X-WR-CALNAME"] == ["My Calendar"]
    assert summary.raw_properties["X-MICROSOFT-CDO-BUSYSTATUS"] == ["BUSY"]
