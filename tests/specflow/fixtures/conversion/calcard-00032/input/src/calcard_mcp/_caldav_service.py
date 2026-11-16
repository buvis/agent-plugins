"""Pure free-time computation for the calendar dispatcher.

This module holds the timezone resolution and free-slot computation helpers
that :class:`calcard_mcp.caldav_client.CalendarService` delegates to. The
functions are pure (no transport, no I/O) so they live apart from the
fan-out service that calls them.

The import direction is shared-base ← this module ← caldav_client: it imports
:class:`calcard_mcp._caldav_base.FreeSlot` but never the assembled
:class:`calcard_mcp.caldav_client.CalDAVClient` or ``CalendarService``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

from calcard_mcp._caldav_base import FreeSlot


def resolve_zone(timezone: str | None) -> tzinfo:
    """Resolve a timezone name into a :class:`datetime.tzinfo`.

    When ``timezone`` is :data:`None`, returns the server's system local
    zone — preserving the historical zero-config behaviour while making
    the dependency explicit (callers don't accidentally rely on
    :meth:`datetime.astimezone` defaults inside other helpers).

    :param timezone: IANA timezone name, or :data:`None` for system local.
    :type timezone: str | None
    :returns: A :class:`tzinfo` suitable for working-hour evaluation.
    :rtype: datetime.tzinfo
    :raises zoneinfo.ZoneInfoNotFoundError: When ``timezone`` is provided
        but does not name a known IANA zone.
    """
    if timezone is None:
        return datetime.now().astimezone().tzinfo or UTC
    return ZoneInfo(timezone)


def compute_free_slots(
    busy: list[tuple[datetime, datetime]],
    *,
    start: datetime,
    end: datetime,
    duration_minutes: int,
    working_hours: tuple[int, int] | None,
    zone: tzinfo,
) -> list[FreeSlot]:
    """Pure free-slot computation: merges busy intervals and walks the free gaps.

    :param busy: Unmerged ``(start_utc, end_utc)`` busy intervals from any
        number of accounts; may be empty.
    :type busy: list[tuple[datetime.datetime, datetime.datetime]]
    :param start: Earliest acceptable slot start (inclusive).
    :type start: datetime.datetime
    :param end: Latest acceptable slot end (exclusive).
    :type end: datetime.datetime
    :param duration_minutes: Minimum required slot length in minutes.
    :type duration_minutes: int
    :param working_hours: Optional ``(start_hour, end_hour)`` filter in ``zone``.
    :type working_hours: tuple[int, int] | None
    :param zone: Timezone in which ``working_hours`` is evaluated.
    :type zone: datetime.tzinfo
    :returns: List of free slots ordered by start time.
    :rtype: list[:class:`FreeSlot`]
    """
    merged = _merge_intervals(busy)
    duration = timedelta(minutes=duration_minutes)
    cursor = start.astimezone(UTC)
    horizon = end.astimezone(UTC)
    slots: list[FreeSlot] = []
    for busy_start, busy_end in merged:
        if busy_start > cursor and busy_start - cursor >= duration:
            slots.extend(_slice_window(cursor, busy_start, duration, working_hours, zone))
        if busy_end > cursor:
            cursor = busy_end
    if horizon > cursor and horizon - cursor >= duration:
        slots.extend(_slice_window(cursor, horizon, duration, working_hours, zone))
    return slots


def _merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Merge overlapping ``(start, end)`` intervals.

    :param intervals: List of half-open ``(start, end)`` pairs.
    :type intervals: list[tuple[datetime.datetime, datetime.datetime]]
    :returns: Disjoint, sorted intervals covering the same instants.
    :rtype: list[tuple[datetime.datetime, datetime.datetime]]
    """
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda pair: pair[0])
    merged: list[tuple[datetime, datetime]] = [ordered[0]]
    for current_start, current_end in ordered[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    return merged


def _slice_window(
    window_start: datetime,
    window_end: datetime,
    duration: timedelta,
    working_hours: tuple[int, int] | None,
    zone: tzinfo,
) -> list[FreeSlot]:
    """Slice a free window into one or more concrete slots of length ``duration``.

    When ``working_hours`` is provided, each slot must start and end within
    ``[start_hour:00, end_hour:00)`` on the same day in ``zone``; slots that
    straddle the working window are shortened to fit or dropped when too small.

    :param window_start: Start of the available window (UTC).
    :type window_start: datetime.datetime
    :param window_end: End of the available window (UTC).
    :type window_end: datetime.datetime
    :param duration: Minimum slot length.
    :type duration: datetime.timedelta
    :param working_hours: Optional ``(start_hour, end_hour)`` filter in ``zone``.
    :type working_hours: tuple[int, int] | None
    :param zone: Timezone in which ``working_hours`` is evaluated.
    :type zone: datetime.tzinfo
    :returns: One or more :class:`FreeSlot` objects, possibly empty.
    :rtype: list[:class:`FreeSlot`]
    """
    if working_hours is None:
        if window_end - window_start >= duration:
            return [FreeSlot(start=window_start, end=window_end)]
        return []

    start_hour, end_hour = working_hours
    slots: list[FreeSlot] = []
    cursor = window_start
    while cursor + duration <= window_end:
        local = cursor.astimezone(zone)
        day_start = local.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = local.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        if local < day_start:
            cursor = day_start.astimezone(UTC)
            continue
        if local + duration > day_end:
            next_day = (day_start + timedelta(days=1)).astimezone(UTC)
            cursor = next_day
            continue
        slot_end = min(cursor + duration, day_end.astimezone(UTC), window_end)
        slots.append(FreeSlot(start=cursor, end=slot_end))
        cursor = slot_end
    return slots
