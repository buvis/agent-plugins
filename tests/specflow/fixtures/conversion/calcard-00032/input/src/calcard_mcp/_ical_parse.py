"""Reusable iCalendar property parsing helpers.

Mirrors :mod:`calcard_mcp._ical_emit` for the read direction. Both
:mod:`calcard_mcp.ical` (VEVENT) and :mod:`calcard_mcp.vtodo` (VTODO)
share the projection logic for the common iCal property surface;
component-specific scalars (DTSTART/DTEND for VEVENT, DUE/COMPLETED for
VTODO) stay in the component module.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from ._binary import BinaryReference, GeoCoordinates
from ._ical_emit import as_utc_datetime
from ._raw_props import encode_raw_property_value

_LOGGER = logging.getLogger(__name__)


def _as_list(value: Any) -> list[Any]:
    """Return ``value`` as a list. Wrap single non-list values; ``None`` → ``[]``."""
    if value is None:
        return []
    if isinstance(value, list):
        return list(cast(list[Any], value))
    return [value]


def extract_categories(component: Any) -> list[str]:
    raw = component.get("CATEGORIES")
    if raw is None:
        return []
    cats = getattr(raw, "cats", None)
    if cats is None:
        return [piece for piece in str(raw).split(",") if piece]
    return [str(item) for item in cast(list[Any], cats)]


def extract_resources(component: Any) -> list[str]:
    raw = component.get("RESOURCES")
    if raw is None:
        return []
    cats = getattr(raw, "cats", None)
    if cats is not None:
        return [str(item) for item in cast(list[Any], cats)]
    return [piece for piece in str(raw).split(",") if piece]


def extract_text_list(component: Any, name: str) -> list[str]:
    return [str(item) for item in _as_list(component.get(name))]


def extract_geo(component: Any) -> GeoCoordinates | None:
    raw = component.get("GEO")
    if raw is None:
        return None
    try:
        latitude = float(raw.latitude)
        longitude = float(raw.longitude)
    except Exception:
        _LOGGER.debug("malformed GEO: %r", raw)
        return None
    return GeoCoordinates(latitude=latitude, longitude=longitude)


# ``Person`` and ``Attendee`` live in :mod:`calcard_mcp.ical` to keep that
# module the canonical home for the public dataclasses; this helper module
# imports them lazily through the function bodies below to avoid an
# import cycle (ical.py imports from us).


_VALID_ATTENDEE_ROLES: frozenset[str] = frozenset(
    {"chair", "req-participant", "opt-participant", "non-participant"}
)
_VALID_ATTENDEE_PARTSTATS: frozenset[str] = frozenset(
    {"needs-action", "accepted", "declined", "tentative", "delegated"}
)
_VALID_ATTENDEE_CUTYPES: frozenset[str] = frozenset(
    {"individual", "group", "resource", "room", "unknown"}
)


def extract_organizer(component: Any) -> Any:
    """Project the ORGANIZER property into a :class:`calcard_mcp.ical.Person`.

    Returns :data:`None` when the property is absent.
    """
    from .ical import Person

    raw = component.get("ORGANIZER")
    if raw is None:
        return None
    return Person(
        address=str(raw),
        common_name=str(raw.params.get("CN", "")),
    )


def _attendee_from_prop(prop: Any) -> Any:
    from .ical import Attendee

    params = prop.params
    role = str(params.get("ROLE", "REQ-PARTICIPANT")).lower()
    partstat = str(params.get("PARTSTAT", "NEEDS-ACTION")).lower()
    cu_type = str(params.get("CUTYPE", "INDIVIDUAL")).lower()
    rsvp = str(params.get("RSVP", "FALSE")).upper() == "TRUE"
    if role not in _VALID_ATTENDEE_ROLES:
        role = "req-participant"
    if partstat not in _VALID_ATTENDEE_PARTSTATS:
        partstat = "needs-action"
    if cu_type not in _VALID_ATTENDEE_CUTYPES:
        cu_type = "individual"
    return Attendee(
        address=str(prop),
        common_name=str(params.get("CN", "")),
        role=cast(
            Literal["chair", "req-participant", "opt-participant", "non-participant"],
            role,
        ),
        partstat=cast(
            Literal["needs-action", "accepted", "declined", "tentative", "delegated"],
            partstat,
        ),
        rsvp=rsvp,
        cu_type=cast(Literal["individual", "group", "resource", "room", "unknown"], cu_type),
    )


def extract_attendees(component: Any) -> list[Any]:
    """Project ATTENDEE properties into a list of :class:`calcard_mcp.ical.Attendee`."""
    return [_attendee_from_prop(prop) for prop in _as_list(component.get("ATTENDEE"))]


def extract_dt_list(component: Any, name: str, fallback_tz: str) -> list[datetime]:
    """Return aware datetimes from EXDATE/RDATE properties (list-of-vDDDLists).

    Naive entries (no ``Z``, no ``TZID``) are anchored to ``fallback_tz`` -
    typically the master DTSTART's tz - to match the RFC 5545 §3.8.5.1
    semantics that EXDATE/RDATE values share the master DTSTART's effective
    time. ``VALUE=DATE`` (date-only) entries are surfaced as midnight datetimes
    anchored to ``fallback_tz``.
    """
    results: list[datetime] = []
    for prop in _as_list(component.get(name)):
        dts = getattr(prop, "dts", None)
        if dts is None:
            value = getattr(prop, "dt", None)
            if not isinstance(value, date):
                continue
            results.append(_anchor_datetime(date_to_midnight(value), fallback_tz))
            continue
        for entry in cast(list[Any], dts):
            entry_dt = getattr(entry, "dt", entry)
            if not isinstance(entry_dt, date):
                continue
            results.append(_anchor_datetime(date_to_midnight(entry_dt), fallback_tz))
    return results


def date_to_midnight(value: date) -> datetime:
    """Return ``value`` as a naive midnight :class:`~datetime.datetime`.

    Pass-through when ``value`` is already a :class:`~datetime.datetime`
    (``datetime`` is a ``date`` subclass).
    """
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


def _anchor_datetime(value: datetime, fallback_tz: str) -> datetime:
    """Return ``value`` tz-aware, applying ``fallback_tz`` when naive."""
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=ZoneInfo(fallback_tz))


def extract_recurrence_id(
    component: Any,
    fallback_tz: str,
    *,
    master_anchor_tz_name: str | None = None,
) -> datetime | None:
    """Return the RECURRENCE-ID value as a UTC-aware datetime (RFC 5545 §3.8.4.4).

    ``VALUE=DATE`` (date-only) inputs are coerced to midnight anchored to
    ``master_anchor_tz_name`` when supplied, else ``fallback_tz``, then
    converted to UTC, mirroring the anchor step ``extract_dt_list`` applies
    for EXDATE/RDATE. Datetime inputs pass through ``as_utc_datetime``: aware
    values are converted (the explicit tz wins; ``master_anchor_tz_name``
    does NOT override it), naive values are anchored to
    ``master_anchor_tz_name`` when supplied, or stamped UTC without
    re-anchoring when not (RFC 5545 requires RECURRENCE-ID to share the
    master's value type, so naive RECURRENCE-ID against a tz-aware master is
    malformed input).
    """
    raw = component.get("RECURRENCE-ID")
    if raw is None:
        return None
    value = getattr(raw, "dt", None)
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return as_utc_datetime(value)
        if master_anchor_tz_name is not None:
            return as_utc_datetime(_anchor_datetime(value, master_anchor_tz_name))
        return as_utc_datetime(value)
    if isinstance(value, date):
        anchor = master_anchor_tz_name if master_anchor_tz_name is not None else fallback_tz
        return as_utc_datetime(_anchor_datetime(date_to_midnight(value), anchor))
    return None


_FREQ_VALUES: frozenset[str] = frozenset(
    {"secondly", "minutely", "hourly", "daily", "weekly", "monthly", "yearly"}
)
_WKST_VALUES: frozenset[str] = frozenset({"MO", "TU", "WE", "TH", "FR", "SA", "SU"})


def _recur_first(recur: dict[str, Any], key: str) -> Any:
    value = recur.get(key)
    if value is None:
        return None
    if isinstance(value, list):
        seq = cast(list[Any], value)
        return seq[0] if seq else None
    return value


def _recur_int_list(recur: dict[str, Any], key: str) -> list[int]:
    raw = recur.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [int(item) for item in cast(list[Any], raw)]
    return [int(raw)]


def _recur_str_list(recur: dict[str, Any], key: str) -> list[str]:
    raw = recur.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in cast(list[Any], raw)]
    return [str(raw)]


def extract_recurrence(component: Any) -> Any:
    """Project the RRULE property into :class:`calcard_mcp.ical.RecurrenceRule`."""
    from .ical import RecurrenceRule

    raw = component.get("RRULE")
    if raw is None:
        return None
    raw_text = raw.to_ical().decode("utf-8")
    recur = dict(cast(dict[str, Any], raw))

    freq_raw = _recur_first(recur, "FREQ")
    freq = str(freq_raw).lower() if freq_raw is not None else ""
    if freq not in _FREQ_VALUES:
        freq = ""

    interval_raw = _recur_first(recur, "INTERVAL")
    interval = int(interval_raw) if interval_raw is not None else 0

    count_raw = _recur_first(recur, "COUNT")
    count = int(count_raw) if count_raw is not None else 0

    until_raw = _recur_first(recur, "UNTIL")
    until: datetime | None
    if isinstance(until_raw, datetime):
        until = as_utc_datetime(until_raw)
    elif isinstance(until_raw, date):
        # RFC 5545 §3.3.10: UNTIL may be a DATE (e.g. UNTIL=20260501).
        # Promote to UTC midnight so the structured ``until`` field carries
        # a real value — without this the C2-1 raw-key gate falls through to
        # structured comparison with both sides ``until=None``, silently
        # passing server-side modification of date-valued UNTIL. ``datetime``
        # is a subclass of ``date`` so the datetime branch above handles
        # those first; this branch only fires for date-but-not-datetime.
        until = datetime(until_raw.year, until_raw.month, until_raw.day, tzinfo=UTC)
    else:
        until = None

    wkst_raw = _recur_first(recur, "WKST")
    week_start = str(wkst_raw).upper() if wkst_raw is not None else ""
    if week_start not in _WKST_VALUES:
        week_start = ""

    return RecurrenceRule(
        raw=raw_text,
        freq=cast(
            Literal[
                "secondly",
                "minutely",
                "hourly",
                "daily",
                "weekly",
                "monthly",
                "yearly",
                "",
            ],
            freq,
        ),
        interval=interval,
        count=count,
        until=until,
        by_day=_recur_str_list(recur, "BYDAY"),
        by_month_day=_recur_int_list(recur, "BYMONTHDAY"),
        by_month=_recur_int_list(recur, "BYMONTH"),
        by_set_pos=_recur_int_list(recur, "BYSETPOS"),
        week_start=cast(Literal["MO", "TU", "WE", "TH", "FR", "SA", "SU", ""], week_start),
    )


def _attachment_from_prop(prop: Any) -> BinaryReference:
    params = prop.params
    fmttype = str(params.get("FMTTYPE", ""))
    encoding = str(params.get("ENCODING", "")).upper()
    if encoding == "BASE64":
        payload = prop.to_ical().decode("ascii")
        media_type = fmttype.lower()
        return BinaryReference(
            value=f"data:{media_type};base64,{payload}",
            media_type=fmttype,
        )
    return BinaryReference(value=str(prop), media_type=fmttype)


def extract_attachments(component: Any) -> list[BinaryReference]:
    return [_attachment_from_prop(prop) for prop in _as_list(component.get("ATTACH"))]


def extract_raw_properties(
    parsed: Any, component: Any, directly_handled: frozenset[str]
) -> dict[str, list[str]]:
    """Collect properties the parser does not project, plus VTIMEZONE blocks.

    ``property_items(recursive=False)`` keeps sub-component properties
    (notably those inside ``VALARM``) from leaking into the parent's opaque
    map. ``directly_handled`` is the component-specific exclusion set
    (VEVENT and VTODO share most of it but each adds component-specific
    scalars).

    Values are value-only segments (no ``NAME:`` prefix, no CRLF). When a
    property carries parameters they are preserved as a leading
    ``;PARAM=VALUE[;PARAM=VALUE...]:`` prefix on the value (parameter names
    sorted), matching the vCard ``raw_properties`` contract; this keeps the
    two parsers symmetric and stops parameters being silently dropped.
    """
    result: dict[str, list[str]] = {}
    for name, value in component.property_items(recursive=False):
        if name in {"BEGIN", "END"}:
            continue
        if name in directly_handled:
            continue
        encoded = encode_raw_property_value(str(value), getattr(value, "params", None))
        result.setdefault(name, []).append(encoded)
    for sub in cast(list[Any], parsed.subcomponents):
        if sub.name == "VTIMEZONE":
            result.setdefault("VTIMEZONE", []).append(sub.to_ical().decode("utf-8"))
    return result


def extract_alarms(component: Any) -> list[Any]:
    """Project every supported VALARM sub-component into an :class:`calcard_mcp.ical.Alarm`.

    Audio (and any other non ``display``/``email``) actions are dropped, as
    are alarms missing a ``TRIGGER``. The ``TRIGGER`` wire form is preserved
    verbatim via ``to_ical()`` so relative (``-PT15M``) and absolute
    (``20260506T093000Z``) values survive untouched.
    """
    from .ical import Alarm, Person

    alarms: list[Any] = []
    for sub in cast(list[Any], component.walk("VALARM")):
        action = str(sub.get("ACTION", "")).lower()
        if action not in {"display", "email"}:
            _LOGGER.debug("VALARM dropped: unsupported ACTION %r", action)
            continue
        trigger_prop = sub.get("TRIGGER")
        if trigger_prop is None:
            _LOGGER.debug("VALARM dropped: missing TRIGGER")
            continue
        trigger = trigger_prop.to_ical().decode("utf-8")
        if not trigger:
            _LOGGER.debug("VALARM dropped: empty TRIGGER")
            continue
        attendees = [
            Person(
                address=str(prop),
                common_name=str(prop.params.get("CN", "")),
            )
            for prop in _as_list(sub.get("ATTENDEE"))
        ]
        alarms.append(
            Alarm(
                action=cast(Literal["display", "email"], action),
                trigger=trigger,
                description=str(sub.get("DESCRIPTION", "")),
                summary=str(sub.get("SUMMARY", "")),
                attendees=attendees,
            )
        )
    return alarms
