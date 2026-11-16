"""Shared MCP wire shapes for iCalendar typed properties.

The calendar (VEVENT) and task (VTODO) tool surfaces share the same
typed-property surface (PRD §9 — single dataclass set serves both
component kinds, with VTODO lacking only ``TRANSP``). This module
declares the wire shapes once so :mod:`calcard_mcp.tools.calendar` and
:mod:`calcard_mcp.tools.todo` import them rather than redeclaring.

Wire-shape rule (established in :mod:`calcard_mcp.tools.contact`):

* A wire shape with a nested :class:`Literal` enum field becomes a
  :class:`pydantic.BaseModel` so the per-element enum constraints
  surface in the generated ``inputSchema``.
* A plain shape stays as :class:`TypedDict`.

Conversion helpers map wire entries to the underlying iCal dataclasses
in :mod:`calcard_mcp.ical`. Each helper preserves :data:`None` so
"argument omitted" stays distinguishable from "argument set to empty".
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import BaseModel

from calcard_mcp._binary import BinaryReference
from calcard_mcp.ical import Alarm, Attendee, GeoCoordinates, Person, RecurrenceRule
from calcard_mcp.tools._coerce import JsonArrayBeforeValidator

__all__ = [
    "AlarmListWire",
    "AlarmWire",
    "AttachmentListWire",
    "AttendeeListWire",
    "AttendeeWire",
    "BinaryReferenceWire",
    "ExDateListWire",
    "GeoCoordinatesWire",
    "PersonWire",
    "RDateListWire",
    "RecurrenceRuleWire",
    "to_alarms",
    "to_attachments",
    "to_attendees",
    "to_geo",
    "to_organizer",
    "to_recurrence",
]


class PersonWire(TypedDict):
    """Calendar-user reference: address (URI) and optional common_name (display)."""

    address: str
    common_name: NotRequired[str]


class AttendeeWire(BaseModel):
    """ATTENDEE entry with role/partstat/cu_type enums and rsvp flag."""

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


class AlarmWire(BaseModel):
    """VALARM block: action display/email, trigger, plus description/summary/attendees."""

    action: Literal["display", "email"]
    trigger: str
    description: str = ""
    summary: str = ""
    attendees: list[PersonWire] = []


class RecurrenceRuleWire(BaseModel):
    """RRULE: pass ``raw`` for full RFC 5545 syntax or fill structured fields."""

    raw: str = ""
    freq: Literal["secondly", "minutely", "hourly", "daily", "weekly", "monthly", "yearly", ""] = ""
    interval: int = 0
    count: int = 0
    until: datetime | None = None
    by_day: list[str] = []
    by_month_day: list[int] = []
    by_month: list[int] = []
    by_set_pos: list[int] = []
    week_start: Literal["MO", "TU", "WE", "TH", "FR", "SA", "SU", ""] = ""


class GeoCoordinatesWire(TypedDict):
    """Geo coordinates with WGS-84 latitude and longitude floats."""

    latitude: float
    longitude: float


class BinaryReferenceWire(TypedDict):
    """Binary URI reference: data: URI or external URI with optional media_type."""

    value: str
    media_type: NotRequired[str]


# Annotated list aliases. The :class:`pydantic.BeforeValidator` shared from
# :mod:`tools._coerce` runs *before* Pydantic's list/array validator so
# JSON-encoded-string arguments pass through unchanged. JSON-Schema
# generation is unaffected by ``BeforeValidator`` in Pydantic v2, so the
# wire ``inputSchema`` stays array-only.
AttendeeListWire = Annotated[list[AttendeeWire], JsonArrayBeforeValidator]
AlarmListWire = Annotated[list[AlarmWire], JsonArrayBeforeValidator]
AttachmentListWire = Annotated[list[BinaryReferenceWire], JsonArrayBeforeValidator]
ExDateListWire = Annotated[list[datetime], JsonArrayBeforeValidator]
RDateListWire = Annotated[list[datetime], JsonArrayBeforeValidator]


def to_attendees(entries: list[AttendeeWire] | None) -> list[Attendee] | None:
    """Convert wire entries to :class:`Attendee`; preserve :data:`None`."""
    if entries is None:
        return None
    return [
        Attendee(
            address=entry.address,
            common_name=entry.common_name,
            role=entry.role,
            partstat=entry.partstat,
            rsvp=entry.rsvp,
            cu_type=entry.cu_type,
        )
        for entry in entries
    ]


def to_alarms(entries: list[AlarmWire] | None) -> list[Alarm] | None:
    """Convert wire entries to :class:`Alarm`; preserve :data:`None`."""
    if entries is None:
        return None
    return [
        Alarm(
            action=entry.action,
            trigger=entry.trigger,
            description=entry.description,
            summary=entry.summary,
            attendees=[
                Person(
                    address=person["address"],
                    common_name=person.get("common_name", ""),
                )
                for person in entry.attendees
            ],
        )
        for entry in entries
    ]


def to_recurrence(entry: RecurrenceRuleWire | None) -> RecurrenceRule | None:
    """Convert wire object to :class:`RecurrenceRule`; preserve :data:`None`."""
    if entry is None:
        return None
    return RecurrenceRule(
        raw=entry.raw,
        freq=entry.freq,
        interval=entry.interval,
        count=entry.count,
        until=entry.until,
        by_day=list(entry.by_day),
        by_month_day=list(entry.by_month_day),
        by_month=list(entry.by_month),
        by_set_pos=list(entry.by_set_pos),
        week_start=entry.week_start,
    )


def to_attachments(
    entries: list[BinaryReferenceWire] | None,
) -> list[BinaryReference] | None:
    """Convert wire entries to :class:`BinaryReference`; preserve :data:`None`."""
    if entries is None:
        return None
    return [
        BinaryReference(value=entry["value"], media_type=entry.get("media_type", ""))
        for entry in entries
    ]


def to_geo(entry: GeoCoordinatesWire | None) -> GeoCoordinates | None:
    """Convert wire object to :class:`GeoCoordinates`; preserve :data:`None`."""
    if entry is None:
        return None
    return GeoCoordinates(latitude=entry["latitude"], longitude=entry["longitude"])


def to_organizer(entry: PersonWire | None) -> Person | None:
    """Convert wire object to :class:`Person`; preserve :data:`None`."""
    if entry is None:
        return None
    return Person(address=entry["address"], common_name=entry.get("common_name", ""))
