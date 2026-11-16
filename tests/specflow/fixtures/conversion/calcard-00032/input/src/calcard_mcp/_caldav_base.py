"""Shared base for the CalDAV client and its mixins.

This module holds the constants, lightweight dataclasses, and module-level
helper functions that both :mod:`calcard_mcp.caldav_client` and its mixin
modules (:mod:`calcard_mcp._caldav_recurrence`,
:mod:`calcard_mcp._caldav_mutation`, :mod:`calcard_mcp._caldav_service`)
depend on. Keeping them here breaks the import cycle: the import direction is
shared-base ← mixins ← caldav_client, so the mixin modules can reference these
names without importing the assembled client back.

Imports:

* :mod:`logging` for the shared module logger.
* :mod:`datetime` for timezone-aware datetime coercion.
* :mod:`zoneinfo.ZoneInfo` to resolve IANA timezones.
* :class:`calcard_mcp._binary.BinaryReference` /
  :class:`calcard_mcp._binary.GeoCoordinates` for typed-field signatures.
* :class:`calcard_mcp.ical.Alarm`, :class:`calcard_mcp.ical.Attendee`,
  :class:`calcard_mcp.ical.EventSummary`, :class:`calcard_mcp.ical.Person`,
  :class:`calcard_mcp.ical.RecurrenceRule` for typed-field signatures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from calcard_mcp._binary import BinaryReference, GeoCoordinates
from calcard_mcp.ical import (
    Alarm,
    Attendee,
    EventSummary,
    Person,
    RecurrenceRule,
)

# caldav-lib prefers ``niquests`` and falls back to ``requests``; the two
# packages declare independent exception hierarchies. Catch both so the
# REPORT path's transport-error wrapping (PRD 00007 §7.3) works no matter
# which transport caldav resolved at import time.
_transport_exceptions: list[type[BaseException]] = []
try:
    from niquests.exceptions import RequestException as _NiquestsRequestException

    _transport_exceptions.append(_NiquestsRequestException)
except ImportError:
    pass
try:
    from requests.exceptions import RequestException as _RequestsRequestException

    _transport_exceptions.append(_RequestsRequestException)
except ImportError:
    pass
_TRANSPORT_EXCEPTIONS: tuple[type[BaseException], ...] = tuple(_transport_exceptions)

_LOG = logging.getLogger("calcard_mcp.caldav_client")


@dataclass(frozen=True, slots=True)
class CalendarSummary:
    """Lightweight description of a calendar collection.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar name: Human-readable calendar name (``displayname`` property).
    :vartype name: str
    :cvar url: Absolute URL of the calendar collection.
    :vartype url: str
    """

    account_id: str
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class FreeSlot:
    """A window of time where every queried account is free.

    :cvar start: Slot start (timezone-aware UTC).
    :vartype start: datetime.datetime
    :cvar end: Slot end (timezone-aware UTC).
    :vartype end: datetime.datetime
    """

    start: datetime
    end: datetime


def _to_aware_datetime(value: Any, fallback_tz: str) -> datetime | None:
    """Coerce an icalendar DTSTART/DTEND ``.dt`` value to a tz-aware datetime.

    icalendar returns either a :class:`datetime.date` (for DATE-valued
    properties on all-day events) or a :class:`datetime.datetime` (for
    DATE-TIME values). The partial-update guard in :meth:`CalDAVClient.update_event`
    needs both sides of its comparison to be tz-aware datetimes; otherwise a
    ``date`` versus tz-aware ``datetime`` comparison raises ``TypeError``.

    :param value: ``date | datetime | None``. ``None`` is returned as-is.
    :param fallback_tz: IANA timezone applied when ``value`` is naive or a date.
    :returns: Timezone-aware ``datetime`` or ``None``.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=ZoneInfo(fallback_tz))
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=ZoneInfo(fallback_tz))
    return None


def _inherit_master_transp(override: EventSummary, master: EventSummary) -> EventSummary:
    """Return ``override`` with master's TRANSP filled in when undeclared.

    Per RFC 5545 §3.8.4.4 a RECURRENCE-ID override inherits from the master
    and replaces only the properties it declares. The parser normalizes a
    missing or malformed TRANSP line to ``transparency == ""``, so the
    truthiness check below treats ``""`` as "not declared" and substitutes
    the master's value; any non-empty override value wins as-is.
    """
    if override.transparency:
        return override
    return replace(override, transparency=master.transparency)


def _status_cancelled(summary: EventSummary) -> bool:
    """Return whether ``summary``'s VEVENT carries ``STATUS:CANCELLED``.

    ``STATUS`` is not a projected :class:`EventSummary` field, so it lands
    verbatim in ``raw_properties``. The comparison is case-insensitive: RFC
    5545 mandates uppercase ``STATUS`` values on the wire, but servers vary.

    :param summary: Event summary to inspect.
    :type summary: :class:`EventSummary`
    :returns: ``True`` when any ``STATUS`` value equals ``CANCELLED``.
    :rtype: bool
    """
    return any(
        value.strip().casefold() == "cancelled"
        for value in summary.raw_properties.get("STATUS", [])
    )


def _touched_typed_fields(
    *,
    categories: list[str] | None,
    classification: str,
    url: str,
    geo: GeoCoordinates | None,
    transparency: str,
    resources: list[str] | None,
    comments: list[str] | None,
    contacts: list[str] | None,
    related_to: list[str] | None,
    organizer: Person | None,
    attendees: list[Attendee] | None,
    alarms: list[Alarm] | None,
    attachments: list[BinaryReference] | None,
    recurrence: RecurrenceRule | None,
    exdates: list[datetime] | None,
    rdates: list[datetime] | None,
    recurrence_id: datetime | None,
) -> list[str]:
    """Return the names of typed VEVENT fields the caller actually supplied.

    A list-typed kwarg is considered "touched" whenever it is not :data:`None`
    (an empty list still touches: it asks the writer to clear emission). A
    string-typed kwarg (``classification``, ``url``, ``transparency``) is
    touched when non-empty, mirroring :func:`build_event_ical`'s skip rule.
    Dataclass-shaped kwargs (``geo``, ``organizer``, ``recurrence``) and
    scalar ``recurrence_id`` are touched only when not :data:`None`.

    The returned list drives which :class:`EventSummary` fields the verifier
    diffs after the write.
    """
    touched: list[str] = []
    if categories is not None:
        touched.append("categories")
    if classification:
        touched.append("classification")
    if url:
        touched.append("url")
    if geo is not None:
        touched.append("geo")
    if transparency:
        touched.append("transparency")
    if resources is not None:
        touched.append("resources")
    if comments is not None:
        touched.append("comments")
    if contacts is not None:
        touched.append("contacts")
    if related_to is not None:
        touched.append("related_to")
    if organizer is not None:
        touched.append("organizer")
    if attendees is not None:
        touched.append("attendees")
    if alarms is not None:
        touched.append("alarms")
    if attachments is not None:
        touched.append("attachments")
    if recurrence is not None:
        touched.append("recurrence")
    if exdates is not None:
        touched.append("exdates")
    if rdates is not None:
        touched.append("rdates")
    if recurrence_id is not None:
        touched.append("recurrence_id")
    return touched
