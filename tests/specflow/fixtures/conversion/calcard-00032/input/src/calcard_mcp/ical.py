"""Pure iCal (de)serialisation helpers — no HTTP, no caldav library.

This module owns iCalendar byte-pushing: building VEVENT documents from
field arguments, parsing them back into :class:`EventSummary`, extracting
RRULE text, and clearing optional VEVENT fields. Errors raised here are
:class:`ValueError`. The transport layer in :mod:`calcard_mcp.caldav_client`
is responsible for wrapping these into :class:`calcard_mcp.errors.ProtocolError`
when the parse failure originated from a server response.

Imports:

* :mod:`datetime` for timezone-aware datetime handling.
* :mod:`zoneinfo.ZoneInfo` to resolve IANA timezones for naive input.
* :mod:`icalendar` for iCal AST construction and parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta, tzinfo
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from icalendar import Calendar as ICalCalendar
from icalendar import Event as ICalEvent

from ._binary import BinaryReference, GeoCoordinates
from ._ical_emit import (
    as_utc_datetime,
    emit_alarm,
    emit_attach,
    emit_attendee,
    emit_categories,
    emit_classification,
    emit_geo,
    emit_person,
    emit_resources,
    emit_rrule,
    emit_text_properties,
    emit_url,
)
from ._ical_parse import (
    date_to_midnight,
    extract_alarms,
    extract_attachments,
    extract_attendees,
    extract_categories,
    extract_dt_list,
    extract_geo,
    extract_organizer,
    extract_raw_properties,
    extract_recurrence,
    extract_recurrence_id,
    extract_resources,
    extract_text_list,
)

__all__ = [
    "Alarm",
    "Attendee",
    "BinaryReference",
    "EventSummary",
    "GeoCoordinates",
    "Person",
    "RecurrenceRule",
    "apply_event_clears",
    "build_event_ical",
    "extract_rrule_text",
    "make_aware",
    "parse_vevent_to_summary",
    "resolve_tz_name",
]


@dataclass(frozen=True, slots=True)
class Person:
    """RFC 5545 §3.8.4 ORGANIZER / ATTENDEE common shape.

    The ``address`` is the bare value (typically a ``mailto:`` URI but any
    URI form is permitted); ``common_name`` populates the ``CN`` parameter.

    :cvar address: URI value (e.g. ``mailto:user@example.com``).
    :vartype address: str
    :cvar common_name: Display name for the ``CN`` parameter; empty
        skips emission.
    :vartype common_name: str
    """

    address: str
    common_name: str = ""


@dataclass(frozen=True, slots=True)
class Attendee:
    """RFC 5545 §3.8.4.1 ATTENDEE.

    Carries the address plus the ``CN`` / ``ROLE`` / ``PARTSTAT`` /
    ``RSVP`` / ``CUTYPE`` parameter values. Wire-form mapping is
    handled by the builder (lowercased here, uppercased on serialise).

    :cvar address: URI value (e.g. ``mailto:user@example.com``).
    :vartype address: str
    :cvar common_name: Display name for the ``CN`` parameter.
    :vartype common_name: str
    :cvar role: One of ``chair``, ``req-participant``, ``opt-participant``,
        ``non-participant``.
    :vartype role: str
    :cvar partstat: Participation status. One of ``needs-action``,
        ``accepted``, ``declined``, ``tentative``, ``delegated``.
    :vartype partstat: str
    :cvar rsvp: Whether a reply is expected.
    :vartype rsvp: bool
    :cvar cu_type: Calendar-user type. One of ``individual``, ``group``,
        ``resource``, ``room``, ``unknown``.
    :vartype cu_type: str
    """

    address: str
    common_name: str = ""
    role: Literal["chair", "req-participant", "opt-participant", "non-participant"] = (
        "req-participant"
    )
    partstat: Literal["needs-action", "accepted", "declined", "tentative", "delegated"] = (
        "needs-action"
    )
    rsvp: bool = False
    cu_type: Literal["individual", "group", "resource", "room", "unknown"] = "individual"


@dataclass(frozen=True, slots=True)
class Alarm:
    """RFC 5545 §3.6.6 VALARM. Display + email triggers; audio out of scope.

    Action-specific invariants (display requires DESCRIPTION, email
    requires DESCRIPTION + ATTENDEE) are enforced by the builder, not the
    dataclass; server-supplied alarms with weaker validation should still
    project cleanly through the parser.

    :cvar action: ``display`` or ``email``.
    :vartype action: str
    :cvar trigger: Trigger value verbatim (``-PT15M`` relative form or an
        absolute UTC datetime string ``20260506T093000Z``); the wire form
        is preserved unchanged.
    :vartype trigger: str
    :cvar description: ``DESCRIPTION`` property; required for both actions
        at emission time.
    :vartype description: str
    :cvar summary: ``SUMMARY`` property; emitted for ``email`` only.
    :vartype summary: str
    :cvar attendees: Attendee list; required to be non-empty for ``email``.
    :vartype attendees: list[Person]
    """

    action: Literal["display", "email"]
    trigger: str
    description: str = ""
    summary: str = ""
    attendees: list[Person] = field(default_factory=list[Person])


@dataclass(frozen=True, slots=True)
class RecurrenceRule:
    """RFC 5545 §3.8.5.3 RRULE. Structured for the common cases.

    The ``raw`` field carries the original RRULE text and wins on
    serialisation when set; the structured fields populate it on read but
    are advisory for mutation. Callers building an RRULE from scratch fill
    the structured fields; advanced callers pass ``raw`` directly.

    :cvar raw: Original RRULE text (e.g. ``FREQ=WEEKLY;BYDAY=MO,WE,FR``).
        Wins on serialisation when non-empty.
    :vartype raw: str
    :cvar freq: Frequency keyword. Empty when unset.
    :vartype freq: str
    :cvar interval: Repeat interval (e.g. ``2`` for every other week);
        ``0`` means unset.
    :vartype interval: int
    :cvar count: Total occurrence count; ``0`` means unset.
    :vartype count: int
    :cvar until: UNTIL boundary (UTC datetime); :data:`None` means unset.
    :vartype until: datetime.datetime | None
    :cvar by_day: BYDAY entries (e.g. ``["MO", "TU", "1FR"]``).
    :vartype by_day: list[str]
    :cvar by_month_day: BYMONTHDAY entries.
    :vartype by_month_day: list[int]
    :cvar by_month: BYMONTH entries.
    :vartype by_month: list[int]
    :cvar by_set_pos: BYSETPOS entries.
    :vartype by_set_pos: list[int]
    :cvar week_start: WKST keyword. Empty when unset.
    :vartype week_start: str
    """

    raw: str = ""
    freq: Literal["secondly", "minutely", "hourly", "daily", "weekly", "monthly", "yearly", ""] = ""
    interval: int = 0
    count: int = 0
    until: datetime | None = None
    by_day: list[str] = field(default_factory=list[str])
    by_month_day: list[int] = field(default_factory=list[int])
    by_month: list[int] = field(default_factory=list[int])
    by_set_pos: list[int] = field(default_factory=list[int])
    week_start: Literal["MO", "TU", "WE", "TH", "FR", "SA", "SU", ""] = ""


@dataclass(frozen=True, slots=True)
class EventSummary:
    """Lightweight description of a single VEVENT instance.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar calendar_url: Absolute URL of the calendar that holds this event.
    :vartype calendar_url: str
    :cvar uid: VEVENT ``UID`` property.
    :vartype uid: str
    :cvar summary: VEVENT ``SUMMARY`` property.
    :vartype summary: str
    :cvar start: Event start time (timezone-aware).
    :vartype start: datetime.datetime
    :cvar end: Event end time (timezone-aware).
    :vartype end: datetime.datetime
    :cvar location: VEVENT ``LOCATION`` property or an empty string.
    :vartype location: str
    :cvar resource_url: Absolute URL of the event resource.
    :vartype resource_url: str
    :cvar description: VEVENT ``DESCRIPTION`` property or an empty string.
    :vartype description: str
    :cvar categories: VEVENT ``CATEGORIES`` values.
    :vartype categories: list[str]
    :cvar classification: Lower-case VEVENT ``CLASS`` value.
    :vartype classification: typing.Literal["public", "private", "confidential", ""]
    :cvar url: VEVENT ``URL`` property or an empty string.
    :vartype url: str
    :cvar geo: VEVENT ``GEO`` coordinates or :data:`None`.
    :vartype geo: GeoCoordinates | None
    :cvar transparency: Lower-case VEVENT ``TRANSP`` value.
    :vartype transparency: typing.Literal["opaque", "transparent", ""]
    :cvar resources: VEVENT ``RESOURCES`` values.
    :vartype resources: list[str]
    :cvar comments: VEVENT ``COMMENT`` values.
    :vartype comments: list[str]
    :cvar contacts: VEVENT ``CONTACT`` values.
    :vartype contacts: list[str]
    :cvar related_to: VEVENT ``RELATED-TO`` values.
    :vartype related_to: list[str]
    :cvar organizer: VEVENT ``ORGANIZER`` value or :data:`None`.
    :vartype organizer: Person | None
    :cvar attendees: VEVENT ``ATTENDEE`` values.
    :vartype attendees: list[Attendee]
    :cvar alarms: Nested VEVENT ``VALARM`` components.
    :vartype alarms: list[Alarm]
    :cvar attachments: VEVENT ``ATTACH`` values.
    :vartype attachments: list[BinaryReference]
    :cvar recurrence: VEVENT ``RRULE`` value or :data:`None`.
    :vartype recurrence: RecurrenceRule | None
    :cvar exdates: VEVENT ``EXDATE`` values.
    :vartype exdates: list[datetime.datetime]
    :cvar rdates: VEVENT ``RDATE`` values.
    :vartype rdates: list[datetime.datetime]
    :cvar recurrence_id: VEVENT ``RECURRENCE-ID`` value or :data:`None`.
    :vartype recurrence_id: datetime.datetime | None
    :cvar raw_properties: Unsupported or not-yet-projected VEVENT property values.
    :vartype raw_properties: dict[str, list[str]]
    """

    account_id: str
    calendar_url: str
    uid: str
    summary: str
    start: datetime
    end: datetime
    location: str
    resource_url: str
    description: str = ""
    categories: list[str] = field(default_factory=list[str])
    classification: Literal["public", "private", "confidential", ""] = ""
    url: str = ""
    geo: GeoCoordinates | None = None
    transparency: Literal["opaque", "transparent", ""] = ""
    resources: list[str] = field(default_factory=list[str])
    comments: list[str] = field(default_factory=list[str])
    contacts: list[str] = field(default_factory=list[str])
    related_to: list[str] = field(default_factory=list[str])
    organizer: Person | None = None
    attendees: list[Attendee] = field(default_factory=list[Attendee])
    alarms: list[Alarm] = field(default_factory=list[Alarm])
    attachments: list[BinaryReference] = field(default_factory=list[BinaryReference])
    recurrence: RecurrenceRule | None = None
    exdates: list[datetime] = field(default_factory=list[datetime])
    rdates: list[datetime] = field(default_factory=list[datetime])
    recurrence_id: datetime | None = None
    raw_properties: dict[str, list[str]] = field(default_factory=dict[str, list[str]])


def make_aware(value: datetime, fallback_tz: str) -> datetime:
    """Return a timezone-aware copy of ``value``, applying ``fallback_tz`` when naive.

    :param value: Datetime that may be naive or aware.
    :type value: datetime.datetime
    :param fallback_tz: IANA timezone name applied when ``value`` is naive.
    :type fallback_tz: str
    :returns: Timezone-aware datetime.
    :rtype: datetime.datetime
    """
    if value.tzinfo is not None:
        return value
    return value.replace(tzinfo=ZoneInfo(fallback_tz))


def _resolve_event_bounds(vevent: Any, fallback_tz: str) -> tuple[datetime, datetime] | None:
    """Resolve a VEVENT's timezone-aware ``(start, end)`` datetimes.

    All-day (``VALUE=DATE``) starts are coerced to midnight datetimes; the
    end is taken from ``DTEND``, else ``DTSTART + DURATION``, else the
    RFC 5545 §3.6.1 default (next midnight for an all-day start, equal to
    the start for a ``DATE-TIME`` start).

    :param vevent: Parsed VEVENT component to inspect.
    :type vevent: typing.Any
    :param fallback_tz: IANA timezone name applied to naive datetimes.
    :type fallback_tz: str
    :returns: The ``(start, end)`` pair, or :data:`None` when ``DTSTART``
        is absent.
    :rtype: tuple[datetime.datetime, datetime.datetime] | None
    """
    start_raw = vevent.get("DTSTART")
    if start_raw is None:
        return None
    start_val = start_raw.dt
    all_day = isinstance(start_val, date) and not isinstance(start_val, datetime)
    start_dt: datetime = date_to_midnight(cast(date, start_val))
    end_raw = vevent.get("DTEND")
    end_dt: datetime
    if end_raw is not None:
        end_dt = date_to_midnight(cast(date, end_raw.dt))
    elif vevent.get("DURATION") is not None:
        end_dt = start_dt + vevent["DURATION"].dt
    elif all_day:
        end_dt = start_dt + timedelta(days=1)
    else:
        end_dt = start_dt
    return make_aware(start_dt, fallback_tz), make_aware(end_dt, fallback_tz)


def resolve_tz_name(tz: tzinfo | None, fallback: str) -> str:
    """Return an IANA timezone name for ``tz``, or ``fallback`` when undeterminable.

    Bridges tzinfo objects parsed by icalendar/dateutil back to an IANA
    name string suitable for :class:`zoneinfo.ZoneInfo`. Handles three
    cases:

    * :class:`zoneinfo.ZoneInfo` exposes the IANA name as ``.key``.
    * UTC tzinfo flavors that lack ``.key`` (stdlib :data:`datetime.UTC`,
      dateutil ``tzutc()``) are recognised by ``tzname() == "UTC"`` and a
      zero ``utcoffset`` and resolved to ``"UTC"``.
    * Anything else (custom fixed-offset tzinfo, unknown class) falls back
      to the supplied ``fallback`` string.

    :param tz: tzinfo instance to inspect, or :data:`None`.
    :type tz: datetime.tzinfo | None
    :param fallback: IANA name returned when ``tz`` cannot be identified.
    :type fallback: str
    :returns: IANA timezone name.
    :rtype: str
    """
    if tz is None:
        return fallback
    key = getattr(tz, "key", None)
    if key:
        return cast(str, key)
    if tz is UTC:
        return "UTC"
    try:
        if tz.utcoffset(None) == UTC.utcoffset(None) and tz.tzname(None) == "UTC":
            return "UTC"
    except (TypeError, ValueError):
        pass
    return fallback


def build_event_ical(
    *,
    uid: str,
    summary: str,
    start: datetime,
    end: datetime,
    description: str | None,
    location: str | None,
    categories: list[str] | None = None,
    classification: str = "",
    url: str = "",
    geo: GeoCoordinates | None = None,
    transparency: str = "",
    resources: list[str] | None = None,
    comments: list[str] | None = None,
    contacts: list[str] | None = None,
    related_to: list[str] | None = None,
    organizer: Person | None = None,
    attendees: list[Attendee] | None = None,
    alarms: list[Alarm] | None = None,
    recurrence: RecurrenceRule | None = None,
    exdates: list[datetime] | None = None,
    rdates: list[datetime] | None = None,
    recurrence_id: datetime | None = None,
    attachments: list[BinaryReference] | None = None,
) -> str:
    """Serialise an iCalendar document containing a single VEVENT.

    :param uid: Unique identifier for the event.
    :type uid: str
    :param summary: Event summary.
    :type summary: str
    :param start: Event start (timezone-aware).
    :type start: datetime.datetime
    :param end: Event end (timezone-aware).
    :type end: datetime.datetime
    :param description: Optional description.
    :type description: str | None
    :param location: Optional location.
    :type location: str | None
    :param categories: Optional VEVENT ``CATEGORIES`` values.
    :type categories: list[str] | None
    :param classification: Optional VEVENT ``CLASS`` value.
    :type classification: str
    :param url: Optional VEVENT ``URL`` value.
    :type url: str
    :param geo: Optional VEVENT ``GEO`` coordinates.
    :type geo: GeoCoordinates | None
    :param transparency: Optional VEVENT ``TRANSP`` value.
    :type transparency: str
    :param resources: Optional VEVENT ``RESOURCES`` values.
    :type resources: list[str] | None
    :param comments: Optional VEVENT ``COMMENT`` values.
    :type comments: list[str] | None
    :param contacts: Optional VEVENT ``CONTACT`` values.
    :type contacts: list[str] | None
    :param related_to: Optional VEVENT ``RELATED-TO`` values.
    :type related_to: list[str] | None
    :param organizer: Optional VEVENT ``ORGANIZER`` value.
    :type organizer: Person | None
    :param attendees: Optional VEVENT ``ATTENDEE`` values.
    :type attendees: list[Attendee] | None
    :param alarms: Optional nested VEVENT ``VALARM`` components.
    :type alarms: list[Alarm] | None
    :param recurrence: Optional VEVENT ``RRULE`` value.
    :type recurrence: RecurrenceRule | None
    :param exdates: Optional VEVENT ``EXDATE`` values.
    :type exdates: list[datetime.datetime] | None
    :param rdates: Optional VEVENT ``RDATE`` values.
    :type rdates: list[datetime.datetime] | None
    :param recurrence_id: Optional VEVENT ``RECURRENCE-ID`` value.
    :type recurrence_id: datetime.datetime | None
    :param attachments: Optional VEVENT ``ATTACH`` values.
    :type attachments: list[BinaryReference] | None
    :returns: The iCalendar document as UTF-8 text.
    :rtype: str
    :raises ValueError: When an alarm violates action-specific invariants or
        an attachment URI uses an unsupported scheme.
    """
    calendar: Any = ICalCalendar()
    calendar.add("prodid", "-//calcard-mcp//EN")
    calendar.add("version", "2.0")
    event: Any = ICalEvent()
    event.add("uid", uid)
    event.add("summary", summary)
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("dtstamp", datetime.now(tz=UTC))
    if description is not None:
        event.add("description", description)
    if location is not None:
        event.add("location", location)
    emit_categories(event, categories)
    emit_classification(event, classification)
    emit_url(event, url)
    emit_geo(event, geo)
    if transparency:
        event.add("transp", transparency.upper())
    emit_resources(event, resources)
    emit_text_properties(event, "comment", comments)
    emit_text_properties(event, "contact", contacts)
    emit_text_properties(event, "related-to", related_to)
    if organizer is not None:
        emit_person(event, "organizer", organizer)
    for attendee in attendees or []:
        emit_attendee(event, attendee)
    if recurrence is not None:
        emit_rrule(event, recurrence)
    for exdate in exdates or []:
        event.add("exdate", as_utc_datetime(exdate))
    for rdate in rdates or []:
        event.add("rdate", as_utc_datetime(rdate))
    if recurrence_id is not None:
        event.add("recurrence-id", as_utc_datetime(recurrence_id))
    for attachment in attachments or []:
        emit_attach(event, attachment)
    for alarm in alarms or []:
        emit_alarm(event, alarm)
    calendar.add_component(event)
    return cast(str, calendar.to_ical().decode("utf-8"))


def extract_rrule_text(event_data: str) -> str | None:
    """Return the ``RRULE:...`` text from an iCal body, if present.

    :param event_data: Raw iCalendar text.
    :type event_data: str
    :returns: Raw RRULE string (e.g. ``"FREQ=DAILY;COUNT=5"``), or
        :data:`None` when the body cannot be parsed or has no recurrence rule.
    :rtype: str | None
    """
    try:
        parsed: Any = ICalCalendar.from_ical(event_data)
    except Exception:
        return None
    for component in cast(list[Any], parsed.walk("VEVENT")):
        rrule = component.get("RRULE")
        if rrule is None:
            return None
        return rrule.to_ical().decode("utf-8")
    return None


_DIRECTLY_HANDLED_PROPERTIES: frozenset[str] = frozenset(
    {
        # Universal exclusions per PRD §9.4.
        "VERSION",
        "PRODID",
        "DTSTAMP",
        "UID",
        "CREATED",
        "LAST-MODIFIED",
        "SEQUENCE",
        "SUMMARY",
        "DTSTART",
        "DTEND",
        "LOCATION",
        "DESCRIPTION",
        "CATEGORIES",
        "CLASS",
        "URL",
        "GEO",
        "TRANSP",
        "RESOURCES",
        "COMMENT",
        "CONTACT",
        "RELATED-TO",
        "ORGANIZER",
        "ATTENDEE",
        "RRULE",
        "EXDATE",
        "RDATE",
        "RECURRENCE-ID",
        "ATTACH",
    }
)


def _build_event_summary(
    parsed: Any,
    vevent: Any,
    *,
    account_id: str,
    calendar_url: str,
    resource_url: str,
    start_dt: datetime,
    end_dt: datetime,
    anchor_tz_name: str,
    master_anchor_tz_name: str | None = None,
) -> EventSummary:
    """Project a parsed VEVENT plus resolved bounds into an EventSummary."""
    classification = str(vevent.get("CLASS", "")).lower()
    if classification not in {"public", "private", "confidential", ""}:
        classification = ""
    transparency = str(vevent.get("TRANSP", "")).lower()
    if transparency not in {"opaque", "transparent", ""}:
        transparency = ""
    return EventSummary(
        account_id=account_id,
        calendar_url=calendar_url,
        uid=str(vevent.get("UID", "")),
        summary=str(vevent.get("SUMMARY", "")),
        start=start_dt,
        end=end_dt,
        location=str(vevent.get("LOCATION", "")),
        resource_url=resource_url,
        description=str(vevent.get("DESCRIPTION", "")),
        categories=extract_categories(vevent),
        classification=cast(Literal["public", "private", "confidential", ""], classification),
        url=str(vevent.get("URL", "")),
        geo=extract_geo(vevent),
        transparency=cast(Literal["opaque", "transparent", ""], transparency),
        resources=extract_resources(vevent),
        comments=extract_text_list(vevent, "COMMENT"),
        contacts=extract_text_list(vevent, "CONTACT"),
        related_to=extract_text_list(vevent, "RELATED-TO"),
        organizer=extract_organizer(vevent),
        attendees=extract_attendees(vevent),
        alarms=extract_alarms(vevent),
        attachments=extract_attachments(vevent),
        recurrence=extract_recurrence(vevent),
        exdates=extract_dt_list(vevent, "EXDATE", anchor_tz_name),
        rdates=extract_dt_list(vevent, "RDATE", anchor_tz_name),
        recurrence_id=extract_recurrence_id(
            vevent, anchor_tz_name, master_anchor_tz_name=master_anchor_tz_name
        ),
        raw_properties=extract_raw_properties(parsed, vevent, _DIRECTLY_HANDLED_PROPERTIES),
    )


def parse_vevent_to_summary(
    event_data: str,
    *,
    account_id: str,
    calendar_url: str,
    resource_url: str,
    fallback_tz: str,
    master_anchor_tz_name: str | None = None,
) -> EventSummary | None:
    """Project an iCalendar VEVENT body into an :class:`EventSummary`.

    Returns :data:`None` when the body is unparseable, when no VEVENT
    component is present, or when ``DTSTART`` is absent.

    :param event_data: Raw iCalendar text.
    :type event_data: str
    :param account_id: Owning account id, copied into the summary.
    :type account_id: str
    :param calendar_url: URL of the owning calendar, copied into the summary.
    :type calendar_url: str
    :param resource_url: URL of the event resource, copied into the summary.
    :type resource_url: str
    :param fallback_tz: IANA name applied to naive DTSTART/DTEND.
    :type fallback_tz: str
    :param master_anchor_tz_name: When supplied, forces RECURRENCE-ID anchoring
        to this tz instead of the override's own DTSTART-derived anchor for
        date-only and naive-datetime RECURRENCE-ID values. Tz-aware
        RECURRENCE-ID values are unaffected.
    :type master_anchor_tz_name: str | None
    :returns: Projected summary, or :data:`None` on any of the failure
        modes above.
    :rtype: :class:`EventSummary` | None
    """
    try:
        parsed: Any = ICalCalendar.from_ical(event_data)
    except Exception:
        return None
    for vevent in cast(list[Any], parsed.walk("VEVENT")):
        bounds = _resolve_event_bounds(vevent, fallback_tz)
        if bounds is None:
            return None
        start_dt, end_dt = bounds
        # EXDATE/RDATE anchor to the master DTSTART's tz per RFC 5545 §3.8.5.1.
        # The supplied ``fallback_tz`` only applies when DTSTART itself is naive.
        anchor_tz_name = resolve_tz_name(start_dt.tzinfo, fallback_tz)
        return _build_event_summary(
            parsed,
            vevent,
            account_id=account_id,
            calendar_url=calendar_url,
            resource_url=resource_url,
            start_dt=start_dt,
            end_dt=end_dt,
            anchor_tz_name=anchor_tz_name,
            master_anchor_tz_name=master_anchor_tz_name,
        )
    return None


_CLEARABLE_EVENT_FIELDS: dict[str, str] = {
    "description": "DESCRIPTION",
    "location": "LOCATION",
    "categories": "CATEGORIES",
    "classification": "CLASS",
    "url": "URL",
    "geo": "GEO",
    "transparency": "TRANSP",
    "resources": "RESOURCES",
    "comments": "COMMENT",
    "contacts": "CONTACT",
    "related_to": "RELATED-TO",
    "organizer": "ORGANIZER",
    "attendees": "ATTENDEE",
    "attachments": "ATTACH",
    "recurrence": "RRULE",
    "exdates": "EXDATE",
    "rdates": "RDATE",
    "recurrence_id": "RECURRENCE-ID",
    "alarms": "VALARM",
}


def apply_event_clears(vevent: Any, clear_fields: list[str]) -> None:
    """Remove optional properties named in ``clear_fields`` from ``vevent`` in place.

    :param vevent: Parsed VEVENT component to mutate (an :class:`icalendar.Event`).
    :type vevent: typing.Any
    :param clear_fields: Lowercase argument names; values other than those
        in :data:`_CLEARABLE_EVENT_FIELDS` raise :class:`ValueError`.
    :type clear_fields: list[str]
    :returns: None.
    :rtype: None
    :raises ValueError: When any entry names a required (non-clearable) field.
    """
    for name in clear_fields:
        key = name.lower()
        ical_name = _CLEARABLE_EVENT_FIELDS.get(key)
        if ical_name is None:
            raise ValueError(
                f"field {name!r} is required and cannot be cleared; "
                f"valid clear_fields: {sorted(_CLEARABLE_EVENT_FIELDS)}"
            )
        if key == "alarms":
            vevent.subcomponents = [
                child for child in vevent.subcomponents if child.name != "VALARM"
            ]
            continue
        vevent.pop(ical_name, None)
