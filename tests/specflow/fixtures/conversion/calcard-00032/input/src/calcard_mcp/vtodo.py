"""Pure VTODO (de)serialisation helpers — no HTTP, no caldav library.

This module owns VTODO byte-pushing: building VTODO documents from field
arguments, parsing them back into :class:`TaskSummary`, and the in-place
mutation helper :func:`replace_fields` that the update flow drives. Errors
raised here are :class:`ValueError`. The transport layer in
:mod:`calcard_mcp.caltodo_client` is responsible for wrapping these into
:class:`calcard_mcp.errors.ProtocolError` when the parse failure originated
from a server response.

Imports:

* :mod:`datetime` for timezone-aware datetime handling.
* :mod:`icalendar` for iCal AST construction and parsing.
* :func:`calcard_mcp.ical.make_aware` for timezone resolution of naive input.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, cast

from icalendar import Calendar as ICalCalendar
from icalendar import Todo as ICalTodo

from calcard_mcp._binary import BinaryReference, GeoCoordinates
from calcard_mcp._ical_emit import (
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
from calcard_mcp._ical_parse import (
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
from calcard_mcp.ical import Alarm, Attendee, Person, RecurrenceRule, make_aware, resolve_tz_name

__all__ = [
    "TaskStatus",
    "TaskSummary",
    "apply_todo_clears",
    "build_vtodo",
    "parse_vtodo",
    "replace_fields",
]

# icalendar 7.x ships VEVENT with ``ignore_exceptions=True`` (broken
# properties surface as ``vBroken`` so the rest of the body still parses)
# but VTODO with ``ignore_exceptions=False`` (the whole component fails on
# any malformed property). Align VTODO with VEVENT so a single bad property
# (e.g. malformed GEO) projects through ``parse_vtodo`` as the field's
# default, mirroring :func:`calcard_mcp.ical.parse_vevent_to_summary`.
ICalTodo.ignore_exceptions = True

TaskStatus = Literal["needs-action", "in-process", "completed", "cancelled"]

_STATUS_VALUES: tuple[str, ...] = (
    "needs-action",
    "in-process",
    "completed",
    "cancelled",
)


@dataclass(frozen=True, slots=True)
class TaskSummary:
    """Lightweight description of a single VTODO instance.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar task_list_url: Absolute URL of the task list that holds this task.
    :vartype task_list_url: str
    :cvar uid: VTODO ``UID`` property.
    :vartype uid: str
    :cvar summary: VTODO ``SUMMARY`` property.
    :vartype summary: str
    :cvar status: Lower-case VTODO ``STATUS`` value.
    :vartype status: str
    :cvar priority: VTODO ``PRIORITY`` value (0-9).
    :vartype priority: int
    :cvar percent_complete: VTODO ``PERCENT-COMPLETE`` value (0-100).
    :vartype percent_complete: int
    :cvar resource_url: Absolute URL of the task resource.
    :vartype resource_url: str
    :cvar description: VTODO ``DESCRIPTION`` property or an empty string.
    :vartype description: str
    :cvar due: Optional VTODO ``DUE`` (timezone-aware) or :data:`None`.
    :vartype due: datetime.datetime | None
    :cvar completed: Optional VTODO ``COMPLETED`` (timezone-aware) or :data:`None`.
    :vartype completed: datetime.datetime | None
    :cvar categories: VTODO ``CATEGORIES`` values.
    :vartype categories: list[str]
    :cvar classification: Lower-case VTODO ``CLASS`` value.
    :vartype classification: typing.Literal["public", "private", "confidential", ""]
    :cvar url: VTODO ``URL`` property or an empty string.
    :vartype url: str
    :cvar geo: VTODO ``GEO`` coordinates or :data:`None`.
    :vartype geo: GeoCoordinates | None
    :cvar resources: VTODO ``RESOURCES`` values.
    :vartype resources: list[str]
    :cvar comments: VTODO ``COMMENT`` values.
    :vartype comments: list[str]
    :cvar contacts: VTODO ``CONTACT`` values.
    :vartype contacts: list[str]
    :cvar related_to: VTODO ``RELATED-TO`` values.
    :vartype related_to: list[str]
    :cvar organizer: VTODO ``ORGANIZER`` value or :data:`None`.
    :vartype organizer: Person | None
    :cvar attendees: VTODO ``ATTENDEE`` values.
    :vartype attendees: list[Attendee]
    :cvar alarms: Nested VTODO ``VALARM`` components.
    :vartype alarms: list[Alarm]
    :cvar attachments: VTODO ``ATTACH`` values.
    :vartype attachments: list[BinaryReference]
    :cvar recurrence: VTODO ``RRULE`` value or :data:`None`.
    :vartype recurrence: RecurrenceRule | None
    :cvar exdates: VTODO ``EXDATE`` values.
    :vartype exdates: list[datetime.datetime]
    :cvar rdates: VTODO ``RDATE`` values.
    :vartype rdates: list[datetime.datetime]
    :cvar recurrence_id: VTODO ``RECURRENCE-ID`` value or :data:`None`.
    :vartype recurrence_id: datetime.datetime | None
    :cvar raw_properties: Unsupported or not-yet-projected VTODO property values.
    :vartype raw_properties: dict[str, list[str]]
    """

    account_id: str
    task_list_url: str
    uid: str
    summary: str
    status: TaskStatus
    priority: int
    percent_complete: int
    resource_url: str
    description: str = ""
    due: datetime | None = None
    completed: datetime | None = None
    categories: list[str] = field(default_factory=list[str])
    classification: Literal["public", "private", "confidential", ""] = ""
    url: str = ""
    geo: GeoCoordinates | None = None
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
        "DESCRIPTION",
        # VTODO-specific scalars projected into typed fields.
        "DUE",
        "COMPLETED",
        "STATUS",
        "PERCENT-COMPLETE",
        "PRIORITY",
        # Shared full-iCal property surface.
        "CATEGORIES",
        "CLASS",
        "URL",
        "GEO",
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


def _validate_status(status: str) -> None:
    if status not in _STATUS_VALUES:
        raise ValueError(f"status {status!r} is invalid; valid values: {list(_STATUS_VALUES)}")


def _validate_priority(priority: int) -> None:
    if not 0 <= priority <= 9:
        raise ValueError(f"priority {priority!r} is out of range; valid range: 0..=9")


def _validate_percent_complete(percent_complete: int) -> None:
    if not 0 <= percent_complete <= 100:
        raise ValueError(
            f"percent_complete {percent_complete!r} is out of range; valid range: 0..=100"
        )


def build_vtodo(
    *,
    uid: str,
    summary: str,
    description: str | None,
    due: datetime | None,
    status: str,
    priority: int,
    percent_complete: int,
    completed: datetime | None,
    categories: list[str] | None = None,
    classification: str = "",
    url: str = "",
    geo: GeoCoordinates | None = None,
    resources: list[str] | None = None,
    comments: list[str] | None = None,
    contacts: list[str] | None = None,
    related_to: list[str] | None = None,
    organizer: Person | None = None,
    attendees: list[Attendee] | None = None,
    alarms: list[Alarm] | None = None,
    attachments: list[BinaryReference] | None = None,
    recurrence: RecurrenceRule | None = None,
    exdates: list[datetime] | None = None,
    rdates: list[datetime] | None = None,
    recurrence_id: datetime | None = None,
) -> str:
    """Serialise an iCalendar document containing a single VTODO.

    :param uid: Unique identifier for the task.
    :type uid: str
    :param summary: Task summary.
    :type summary: str
    :param description: Optional description.
    :type description: str | None
    :param due: Optional due date/time (timezone-aware).
    :type due: datetime.datetime | None
    :param status: Lower-case task status; must be in :data:`_STATUS_VALUES`.
    :type status: str
    :param priority: Task priority in ``0..=9``.
    :type priority: int
    :param percent_complete: Completion percentage in ``0..=100``.
    :type percent_complete: int
    :param completed: Optional completion timestamp (timezone-aware).
    :type completed: datetime.datetime | None
    :param categories: Optional VTODO ``CATEGORIES`` values.
    :type categories: list[str] | None
    :param classification: Optional VTODO ``CLASS`` value.
    :type classification: str
    :param url: Optional VTODO ``URL`` value.
    :type url: str
    :param geo: Optional VTODO ``GEO`` coordinates.
    :type geo: GeoCoordinates | None
    :param resources: Optional VTODO ``RESOURCES`` values.
    :type resources: list[str] | None
    :param comments: Optional VTODO ``COMMENT`` values.
    :type comments: list[str] | None
    :param contacts: Optional VTODO ``CONTACT`` values.
    :type contacts: list[str] | None
    :param related_to: Optional VTODO ``RELATED-TO`` values.
    :type related_to: list[str] | None
    :param organizer: Optional VTODO ``ORGANIZER`` value.
    :type organizer: Person | None
    :param attendees: Optional VTODO ``ATTENDEE`` values.
    :type attendees: list[Attendee] | None
    :param alarms: Optional nested VTODO ``VALARM`` components.
    :type alarms: list[Alarm] | None
    :param attachments: Optional VTODO ``ATTACH`` values.
    :type attachments: list[BinaryReference] | None
    :param recurrence: Optional VTODO ``RRULE`` value.
    :type recurrence: RecurrenceRule | None
    :param exdates: Optional VTODO ``EXDATE`` values.
    :type exdates: list[datetime.datetime] | None
    :param rdates: Optional VTODO ``RDATE`` values.
    :type rdates: list[datetime.datetime] | None
    :param recurrence_id: Optional VTODO ``RECURRENCE-ID`` value.
    :type recurrence_id: datetime.datetime | None
    :returns: The iCalendar document as UTF-8 text.
    :rtype: str
    :raises ValueError: When ``status``, ``priority``, or ``percent_complete``
        fall outside their valid ranges, when an alarm violates
        action-specific invariants, or when an attachment URI uses an
        unsupported scheme.
    """
    _validate_status(status)
    _validate_priority(priority)
    _validate_percent_complete(percent_complete)
    calendar: Any = ICalCalendar()
    calendar.add("prodid", "-//calcard-mcp//EN")
    calendar.add("version", "2.0")
    todo: Any = ICalTodo()
    now = datetime.now(tz=UTC)
    todo.add("uid", uid)
    todo.add("summary", summary)
    todo.add("status", status.upper())
    todo.add("priority", priority)
    todo.add("percent-complete", percent_complete)
    todo.add("created", now)
    todo.add("dtstamp", now)
    todo.add("last-modified", now)
    if description is not None:
        todo.add("description", description)
    if due is not None:
        todo.add("due", due)
    if completed is not None:
        todo.add("completed", completed)
    emit_categories(todo, categories)
    emit_classification(todo, classification)
    emit_url(todo, url)
    emit_geo(todo, geo)
    emit_resources(todo, resources)
    emit_text_properties(todo, "comment", comments)
    emit_text_properties(todo, "contact", contacts)
    emit_text_properties(todo, "related-to", related_to)
    if organizer is not None:
        emit_person(todo, "organizer", organizer)
    for attendee in attendees or []:
        emit_attendee(todo, attendee)
    if recurrence is not None:
        emit_rrule(todo, recurrence)
    for exdate in exdates or []:
        todo.add("exdate", as_utc_datetime(exdate))
    for rdate in rdates or []:
        todo.add("rdate", as_utc_datetime(rdate))
    if recurrence_id is not None:
        todo.add("recurrence-id", as_utc_datetime(recurrence_id))
    for attachment in attachments or []:
        emit_attach(todo, attachment)
    for alarm in alarms or []:
        emit_alarm(todo, alarm)
    calendar.add_component(todo)
    return cast(str, calendar.to_ical().decode("utf-8"))


def parse_vtodo(
    task_data: str,
    *,
    account_id: str,
    task_list_url: str,
    resource_url: str,
    fallback_tz: str,
) -> TaskSummary | None:
    """Project an iCalendar VTODO body into a :class:`TaskSummary`.

    Returns :data:`None` when the body is unparseable, when no VTODO
    component is present, or when ``UID`` is missing. ``DUE`` values that
    are pure :class:`datetime.date` (i.e. ``VALUE=DATE`` all-day tasks)
    project to ``due=None``.

    :param task_data: Raw iCalendar text.
    :type task_data: str
    :param account_id: Owning account id, copied into the summary.
    :type account_id: str
    :param task_list_url: URL of the owning task list, copied into the summary.
    :type task_list_url: str
    :param resource_url: URL of the task resource, copied into the summary.
    :type resource_url: str
    :param fallback_tz: IANA name applied to naive DUE/COMPLETED.
    :type fallback_tz: str
    :returns: Projected summary, or :data:`None` on any of the failure
        modes above.
    :rtype: :class:`TaskSummary` | None
    """
    try:
        parsed: Any = ICalCalendar.from_ical(task_data)
    except Exception:
        return None
    for component in cast(list[Any], parsed.walk("VTODO")):
        vtodo: Any = component
        uid_raw = vtodo.get("UID")
        if uid_raw is None:
            return None
        due_raw = vtodo.get("DUE")
        due_dt: datetime | None = None
        if due_raw is not None:
            due_value = due_raw.dt
            if isinstance(due_value, datetime):
                due_dt = make_aware(due_value, fallback_tz)
        completed_raw = vtodo.get("COMPLETED")
        completed_dt: datetime | None = None
        if completed_raw is not None:
            completed_value = completed_raw.dt
            if isinstance(completed_value, datetime):
                completed_dt = make_aware(completed_value, fallback_tz)
        status_raw = vtodo.get("STATUS")
        status_str = str(status_raw).lower() if status_raw is not None else "needs-action"
        # Servers are not constrained to RFC 5545's enumerated STATUS values; project to
        # `needs-action` when an unknown literal arrives so TaskSummary.status stays
        # narrowly typed.
        status: TaskStatus = (
            cast(TaskStatus, status_str) if status_str in _STATUS_VALUES else "needs-action"
        )
        priority_raw = vtodo.get("PRIORITY")
        priority = int(priority_raw) if priority_raw is not None else 0
        percent_raw = vtodo.get("PERCENT-COMPLETE")
        percent_complete = int(percent_raw) if percent_raw is not None else 0
        classification = str(vtodo.get("CLASS", "")).lower()
        if classification not in {"public", "private", "confidential", ""}:
            classification = ""
        # EXDATE/RDATE anchor per RFC 5545 §3.8.5.1 follows DTSTART. VTODOs
        # often ship DUE only (no DTSTART), so we fall back to DUE's tz as a
        # pragmatic proxy, and to ``fallback_tz`` (account tz) when neither
        # property is present.
        dtstart_raw = vtodo.get("DTSTART")
        dtstart_tzinfo = None
        if dtstart_raw is not None and isinstance(dtstart_raw.dt, datetime):
            dtstart_tzinfo = dtstart_raw.dt.tzinfo
        if dtstart_tzinfo is not None:
            anchor_tz_name = resolve_tz_name(dtstart_tzinfo, fallback_tz)
        elif due_dt is not None:
            anchor_tz_name = resolve_tz_name(due_dt.tzinfo, fallback_tz)
        else:
            anchor_tz_name = fallback_tz
        return TaskSummary(
            account_id=account_id,
            task_list_url=task_list_url,
            uid=str(uid_raw),
            summary=str(vtodo.get("SUMMARY", "")),
            status=status,
            priority=priority,
            percent_complete=percent_complete,
            resource_url=resource_url,
            description=str(vtodo.get("DESCRIPTION", "")),
            due=due_dt,
            completed=completed_dt,
            categories=extract_categories(vtodo),
            classification=cast(Literal["public", "private", "confidential", ""], classification),
            url=str(vtodo.get("URL", "")),
            geo=extract_geo(vtodo),
            resources=extract_resources(vtodo),
            comments=extract_text_list(vtodo, "COMMENT"),
            contacts=extract_text_list(vtodo, "CONTACT"),
            related_to=extract_text_list(vtodo, "RELATED-TO"),
            organizer=extract_organizer(vtodo),
            attendees=extract_attendees(vtodo),
            alarms=extract_alarms(vtodo),
            attachments=extract_attachments(vtodo),
            recurrence=extract_recurrence(vtodo),
            exdates=extract_dt_list(vtodo, "EXDATE", anchor_tz_name),
            rdates=extract_dt_list(vtodo, "RDATE", anchor_tz_name),
            recurrence_id=extract_recurrence_id(vtodo, anchor_tz_name),
            raw_properties=extract_raw_properties(parsed, vtodo, _DIRECTLY_HANDLED_PROPERTIES),
        )
    return None


_CLEARABLE_TODO_FIELDS: dict[str, str] = {
    "description": "DESCRIPTION",
    "due": "DUE",
    "completed": "COMPLETED",
    "categories": "CATEGORIES",
    "classification": "CLASS",
    "url": "URL",
    "geo": "GEO",
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


def _replace_property(vtodo: Any, name: str, value: Any) -> None:
    vtodo.pop(name, None)
    vtodo.add(name, value)


def apply_todo_clears(vtodo: Any, clear_fields: list[str]) -> None:
    """Remove optional properties named in ``clear_fields`` from ``vtodo`` in place.

    :param vtodo: Parsed VTODO component to mutate (an :class:`icalendar.Todo`).
    :type vtodo: typing.Any
    :param clear_fields: Lowercase argument names; values other than those
        in :data:`_CLEARABLE_TODO_FIELDS` raise :class:`ValueError`.
    :type clear_fields: list[str]
    :returns: None.
    :rtype: None
    :raises ValueError: When any entry names a required (non-clearable) field.
    """
    for name in clear_fields:
        key = name.lower()
        ical_name = _CLEARABLE_TODO_FIELDS.get(key)
        if ical_name is None:
            raise ValueError(
                f"field {name!r} is required and cannot be cleared; "
                f"valid clear_fields: {sorted(_CLEARABLE_TODO_FIELDS)}"
            )
        if key == "alarms":
            vtodo.subcomponents = [child for child in vtodo.subcomponents if child.name != "VALARM"]
            continue
        vtodo.pop(ical_name, None)


def replace_fields(
    vtodo: Any,
    *,
    summary: str | None = None,
    description: str | None = None,
    due: datetime | None = None,
    status: str | None = None,
    priority: int | None = None,
    percent_complete: int | None = None,
    completed: datetime | None = None,
    clear_fields: list[str] | None = None,
) -> None:
    """Update VTODO properties in place on ``vtodo``.

    Each non-:data:`None` argument replaces the corresponding property.
    ``clear_fields`` removes optional properties; only entries listed in
    :data:`_CLEARABLE_TODO_FIELDS` (case-insensitive) are accepted.

    :param vtodo: Parsed VTODO component to mutate (an :class:`icalendar.Todo`).
    :type vtodo: typing.Any
    :param summary: Replacement ``SUMMARY`` or :data:`None` to preserve.
    :type summary: str | None
    :param description: Replacement ``DESCRIPTION`` or :data:`None` to preserve.
    :type description: str | None
    :param due: Replacement ``DUE`` (timezone-aware) or :data:`None` to preserve.
    :type due: datetime.datetime | None
    :param status: Replacement ``STATUS`` (lower-case) or :data:`None` to preserve.
    :type status: str | None
    :param priority: Replacement ``PRIORITY`` (0..=9) or :data:`None` to preserve.
    :type priority: int | None
    :param percent_complete: Replacement ``PERCENT-COMPLETE`` (0..=100) or
        :data:`None` to preserve.
    :type percent_complete: int | None
    :param completed: Replacement ``COMPLETED`` (timezone-aware) or
        :data:`None` to preserve.
    :type completed: datetime.datetime | None
    :param clear_fields: Lowercase argument names of optional fields to
        remove; values outside :data:`_CLEARABLE_TODO_FIELDS` raise
        :class:`ValueError`.
    :type clear_fields: list[str] | None
    :returns: None.
    :rtype: None
    :raises ValueError: When ``status``, ``priority``, or ``percent_complete``
        fall outside their valid ranges, or when ``clear_fields`` names a
        required (non-clearable) field.
    """
    if status is not None:
        _validate_status(status)
    if priority is not None:
        _validate_priority(priority)
    if percent_complete is not None:
        _validate_percent_complete(percent_complete)
    if summary is not None:
        _replace_property(vtodo, "summary", summary)
    if description is not None:
        _replace_property(vtodo, "description", description)
    if due is not None:
        _replace_property(vtodo, "due", due)
    if status is not None:
        _replace_property(vtodo, "status", status.upper())
    if priority is not None:
        _replace_property(vtodo, "priority", priority)
    if percent_complete is not None:
        _replace_property(vtodo, "percent-complete", percent_complete)
    if completed is not None:
        _replace_property(vtodo, "completed", completed)
    if clear_fields:
        apply_todo_clears(vtodo, clear_fields)
