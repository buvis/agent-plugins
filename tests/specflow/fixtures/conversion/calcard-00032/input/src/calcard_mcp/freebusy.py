"""Pure VFREEBUSY parsing — no HTTP, no caldav library.

Mirrors :mod:`calcard_mcp.ical` for the freebusy side: takes a
``text/calendar`` body containing one VFREEBUSY component (the response
shape of an RFC 4791 ``<C:free-busy-query>`` REPORT) and projects it
into UTC ``(start, end)`` busy-interval tuples.

The transport layer in :mod:`calcard_mcp.caldav_client` is responsible
for wrapping :class:`ValueError` into
:class:`calcard_mcp.errors.ProtocolError` when the parse failure
originated from a server response.

Imports:

* :mod:`datetime` for timezone-aware datetime handling.
* :mod:`icalendar` for VCALENDAR / VFREEBUSY / vPeriod parsing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from icalendar import Calendar as ICalCalendar

__all__ = ["parse_vfreebusy"]

_BUSY_FBTYPES: frozenset[str] = frozenset({"BUSY", "BUSY-UNAVAILABLE", "BUSY-TENTATIVE"})


def parse_vfreebusy(body: str) -> list[tuple[datetime, datetime]]:
    """Parse a VFREEBUSY ``text/calendar`` body into UTC busy intervals.

    Iterates the FREEBUSY lines of the first VFREEBUSY component, keeps
    entries whose ``FBTYPE`` parameter is ``BUSY``, ``BUSY-UNAVAILABLE``,
    ``BUSY-TENTATIVE``, or absent (RFC 5545 §3.2.9 default is ``BUSY``),
    and drops entries with ``FBTYPE=FREE``. Both period forms defined by
    RFC 5545 §3.3.9 — ``start/end`` and ``start/duration`` — are
    handled; multi-period FREEBUSY lines (comma-separated) are flattened
    into individual tuples. The result is sorted ascending by start.

    :param body: ``text/calendar`` body containing a VFREEBUSY component.
    :type body: str
    :returns: Busy intervals as UTC-aware ``(start, end)`` datetime
        tuples, sorted by start.
    :rtype: list[tuple[datetime.datetime, datetime.datetime]]
    :raises ValueError: When the body cannot be parsed, when no
        VFREEBUSY component is present, or when a FREEBUSY period
        value is malformed.
    """
    try:
        calendar: Any = ICalCalendar.from_ical(body)
    except Exception as exc:
        raise ValueError(f"unparseable iCalendar body: {exc}") from exc

    # PRD 00007 §7.1: parse the first VFREEBUSY component. RFC 4791 §7.10
    # (<C:free-busy-query> REPORT) responds with at most one VCALENDAR
    # containing one VFREEBUSY, so this is the realistic shape; additional
    # components in a malformed response are ignored.
    components = list(cast(list[Any], calendar.walk("VFREEBUSY")))
    if not components:
        raise ValueError("VFREEBUSY component not found in iCalendar body")

    intervals: list[tuple[datetime, datetime]] = []
    vfreebusy = components[0]
    raw = vfreebusy.get("FREEBUSY")
    if raw is not None:
        periods = cast(list[Any], raw if isinstance(raw, list) else [raw])
        for period in periods:
            fbtype = str(period.params.get("FBTYPE", "BUSY")).upper()
            if fbtype not in _BUSY_FBTYPES:
                continue
            start, end = _period_endpoints(period)
            intervals.append((start, end))

    intervals.sort(key=lambda pair: pair[0])
    return intervals


def _period_endpoints(period: Any) -> tuple[datetime, datetime]:
    """Return ``(start_utc, end_utc)`` for an icalendar :class:`vPeriod`.

    :param period: Parsed ``vPeriod`` instance from
        :mod:`icalendar.prop.dt.period`.
    :type period: typing.Any
    :returns: UTC-aware start and end datetimes.
    :rtype: tuple[datetime.datetime, datetime.datetime]
    :raises ValueError: When the period attributes cannot be projected
        to two datetimes (malformed input that survived ``from_ical``).
    """
    start = getattr(period, "start", None)
    end = getattr(period, "end", None)
    if isinstance(start, datetime) and isinstance(end, datetime):
        return _to_utc(start), _to_utc(end)
    if isinstance(start, datetime) and isinstance(end, timedelta):
        return _to_utc(start), _to_utc(start + end)
    raise ValueError(f"malformed FREEBUSY period: {period!r}")


def _to_utc(value: datetime) -> datetime:
    """Coerce a datetime to a UTC-aware copy.

    Naive inputs are treated as UTC (RFC 4791 wire format requires UTC
    for VFREEBUSY periods, so a server returning naive datetimes here
    is misbehaving — but treating them as UTC is the documented
    interpretation rather than a silent mismatch).

    :param value: Datetime that may be naive or aware.
    :type value: datetime.datetime
    :returns: UTC-aware datetime.
    :rtype: datetime.datetime
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
