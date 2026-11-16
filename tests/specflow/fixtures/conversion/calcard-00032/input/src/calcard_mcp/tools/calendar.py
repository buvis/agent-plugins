"""MCP tool registrations for calendar (CalDAV) operations.

The :func:`register` function is invoked once during server construction.
It attaches the calendar-related MCP tools (``list_calendars``,
``list_events``, ``search_events``, ``create_event``, ``update_event``,
``delete_event``, ``find_free_time``) to the supplied
:class:`fastmcp.FastMCP` instance.

Imports:

* :mod:`asyncio` to offload sync CalDAV calls onto worker threads.
* :mod:`datetime` for parameter types on tool functions.
* :mod:`dataclasses.asdict` to project frozen summaries into MCP-friendly dicts.
* :class:`fastmcp.FastMCP` for the tool registry.
* :class:`fastmcp.Context` for per-account progress reporting in
  ``find_free_time``.
* :class:`calcard_mcp.accounts.AccountRegistry` for write-safety checks.
* :class:`calcard_mcp.caldav_client.CalendarService` for per-account clients.
* :class:`calcard_mcp.ical` dataclasses for the typed iCal property surface
  the tool functions accept on the wire.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastmcp import Context, FastMCP

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalendarService, compute_free_slots, resolve_zone
from calcard_mcp.tools._coerce import StrListWire
from calcard_mcp.tools._ical_wire import (
    AlarmListWire,
    AttachmentListWire,
    AttendeeListWire,
    ExDateListWire,
    GeoCoordinatesWire,
    PersonWire,
    RDateListWire,
    RecurrenceRuleWire,
    to_alarms,
    to_attachments,
    to_attendees,
    to_geo,
    to_organizer,
    to_recurrence,
)
from calcard_mcp.tools._logging import tool_logged

__all__ = ["register"]


def register(server: FastMCP, registry: AccountRegistry, service: CalendarService) -> None:
    """Attach calendar tools to ``server``.

    :param server: :class:`FastMCP` instance.
    :type server: :class:`fastmcp.FastMCP`
    :param registry: Account registry used for write-safety checks.
    :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :param service: Configured calendar service.
    :type service: :class:`calcard_mcp.caldav_client.CalendarService`
    :returns: None. Tools are registered on ``server`` in place.
    :rtype: None
    """

    @server.tool(
        description=(
            "List every VEVENT-supporting calendar on one account. "
            "Use the URLs as 'calendar_url' for list_events, create_event, "
            "update_event, and delete_event."
        ),
    )
    @tool_logged
    async def list_calendars(account: str | None = None) -> list[dict[str, str]]:
        """List every VEVENT-supporting calendar on one account.

        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: One record per calendar with ``account_id``, ``name``, and ``url``.
        :rtype: list[dict[str, str]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_calendars)
        return [asdict(item) for item in result]

    @server.tool(
        description=(
            "List events in one calendar between 'start' (inclusive) and 'end' "
            "(exclusive). Recurring events are expanded into per-instance "
            "occurrences. Naive datetimes are interpreted in the account's "
            "configured timezone."
        ),
    )
    @tool_logged
    async def list_events(
        calendar_url: str,
        start: datetime,
        end: datetime,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """List events in one calendar between two timestamps.

        :param calendar_url: Calendar URL returned by list_calendars.
        :type calendar_url: str
        :param start: Inclusive range start. Naive datetimes use the account's timezone.
        :type start: datetime.datetime
        :param end: Exclusive range end. Naive datetimes use the account's timezone.
        :type end: datetime.datetime
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Event records ordered by start time.
        :rtype: list[dict[str, typing.Any]]
        """
        registry.require_url_match(registry.resolve(account), calendar_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_events, calendar_url, start, end)
        return [event_to_dict(item) for item in result]

    @server.tool(
        description=(
            "Search every calendar on one account for events whose title, "
            "description, or location contains 'query' (case-insensitive), "
            "between 'start' (inclusive) and 'end' (exclusive)."
        ),
    )
    @tool_logged
    async def search_events(
        query: str,
        start: datetime,
        end: datetime,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search events across every calendar on one account.

        :param query: Substring to match (case-insensitive).
        :type query: str
        :param start: Inclusive range start. Naive datetimes use the account's timezone.
        :type start: datetime.datetime
        :param end: Exclusive range end. Naive datetimes use the account's timezone.
        :type end: datetime.datetime
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Matching events.
        :rtype: list[dict[str, typing.Any]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.search_events, query, start, end)
        return [event_to_dict(item) for item in result]

    @server.tool(
        description=(
            "Create an event in a calendar. 'summary', 'start', and 'end' are "
            "required. Naive datetimes are interpreted in the account's "
            "configured timezone. Optional structured fields cover the full "
            "iCalendar VEVENT surface: categories, classification, url, geo, "
            "transparency, resources, comments, contacts, related_to, "
            "organizer, attendees, alarms, attachments, recurrence, exdates, "
            "rdates, recurrence_id."
        ),
    )
    @tool_logged
    async def create_event(
        calendar_url: str,
        summary: str,
        start: datetime,
        end: datetime,
        account: str | None = None,
        description: str | None = None,
        location: str | None = None,
        categories: StrListWire | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinatesWire | None = None,
        transparency: str = "",
        resources: StrListWire | None = None,
        comments: StrListWire | None = None,
        contacts: StrListWire | None = None,
        related_to: StrListWire | None = None,
        organizer: PersonWire | None = None,
        attendees: AttendeeListWire | None = None,
        alarms: AlarmListWire | None = None,
        attachments: AttachmentListWire | None = None,
        recurrence: RecurrenceRuleWire | None = None,
        exdates: ExDateListWire | None = None,
        rdates: RDateListWire | None = None,
        recurrence_id: datetime | None = None,
    ) -> dict[str, Any]:
        """Create an event in a calendar.

        :param calendar_url: Calendar URL returned by list_calendars.
        :type calendar_url: str
        :param summary: Event title.
        :type summary: str
        :param start: Event start. Naive datetimes use the account's timezone.
        :type start: datetime.datetime
        :param end: Event end. Naive datetimes use the account's timezone.
        :type end: datetime.datetime
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param description: Body text.
        :type description: str | None
        :param location: Where the event happens.
        :type location: str | None
        :param categories: VEVENT ``CATEGORIES`` values.
        :type categories: list[str] | None
        :param classification: VEVENT ``CLASS`` value (e.g. ``public``, ``private``).
        :type classification: str
        :param url: VEVENT ``URL`` value.
        :type url: str
        :param geo: VEVENT ``GEO`` coordinates ({latitude, longitude}).
        :type geo: GeoCoordinatesWire | None
        :param transparency: VEVENT ``TRANSP`` (``opaque`` or ``transparent``).
        :type transparency: str
        :param resources: VEVENT ``RESOURCES`` values.
        :type resources: list[str] | None
        :param comments: VEVENT ``COMMENT`` values.
        :type comments: list[str] | None
        :param contacts: VEVENT ``CONTACT`` values.
        :type contacts: list[str] | None
        :param related_to: VEVENT ``RELATED-TO`` values.
        :type related_to: list[str] | None
        :param organizer: VEVENT ``ORGANIZER`` ({address, common_name}).
        :type organizer: PersonWire | None
        :param attendees: VEVENT ``ATTENDEE`` entries.
        :type attendees: list[AttendeeWire] | None
        :param alarms: Nested VALARM blocks.
        :type alarms: list[AlarmWire] | None
        :param attachments: VEVENT ``ATTACH`` URI references.
        :type attachments: list[BinaryReferenceWire] | None
        :param recurrence: VEVENT ``RRULE`` value.
        :type recurrence: RecurrenceRuleWire | None
        :param exdates: VEVENT ``EXDATE`` values.
        :type exdates: list[datetime.datetime] | None
        :param rdates: VEVENT ``RDATE`` values.
        :type rdates: list[datetime.datetime] | None
        :param recurrence_id: VEVENT ``RECURRENCE-ID`` value.
        :type recurrence_id: datetime.datetime | None
        :returns: The created event.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``calendar_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), calendar_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.create_event,
            calendar_url=calendar_url,
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            categories=categories,
            classification=classification,
            url=url,
            geo=to_geo(geo),
            transparency=transparency,
            resources=resources,
            comments=comments,
            contacts=contacts,
            related_to=related_to,
            organizer=to_organizer(organizer),
            attendees=to_attendees(attendees),
            alarms=to_alarms(alarms),
            attachments=to_attachments(attachments),
            recurrence=to_recurrence(recurrence),
            exdates=exdates,
            rdates=rdates,
            recurrence_id=recurrence_id,
        )
        return event_to_dict(result)

    @server.tool(
        description=(
            "Update fields on an existing event. Argument semantics: None "
            "preserves the field; for 'description' and 'location' an empty "
            "string sets the property to empty; for 'classification', 'url', "
            "'transparency' an empty string is treated as preserve (use "
            "'clear_fields' to remove). List 'clear_fields' to remove any "
            "supported property entirely. "
            "Valid clear_fields entries: 'description', 'location', 'categories', "
            "'classification', 'url', 'geo', 'transparency', 'resources', "
            "'comments', 'contacts', 'related_to', 'organizer', 'attendees', "
            "'alarms', 'attachments', 'recurrence', 'exdates', 'rdates', "
            "'recurrence_id'. Naive datetimes are interpreted in the account's "
            "configured timezone."
        ),
    )
    @tool_logged
    async def update_event(
        calendar_url: str,
        uid: str,
        account: str | None = None,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        categories: StrListWire | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinatesWire | None = None,
        transparency: str = "",
        resources: StrListWire | None = None,
        comments: StrListWire | None = None,
        contacts: StrListWire | None = None,
        related_to: StrListWire | None = None,
        organizer: PersonWire | None = None,
        attendees: AttendeeListWire | None = None,
        alarms: AlarmListWire | None = None,
        attachments: AttachmentListWire | None = None,
        recurrence: RecurrenceRuleWire | None = None,
        exdates: ExDateListWire | None = None,
        rdates: RDateListWire | None = None,
        recurrence_id: datetime | None = None,
        clear_fields: StrListWire | None = None,
    ) -> dict[str, Any]:
        """Update an existing VEVENT with read-after-write verification.

        :param calendar_url: Calendar URL that holds the event.
        :type calendar_url: str
        :param uid: UID of the event, returned by list_events or search_events.
        :type uid: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param summary: New event title.
        :type summary: str | None
        :param start: New start. Naive datetimes use the account's timezone.
        :type start: datetime.datetime | None
        :param end: New end. Naive datetimes use the account's timezone.
        :type end: datetime.datetime | None
        :param description: New body text.
        :type description: str | None
        :param location: New location.
        :type location: str | None
        :param categories: New ``CATEGORIES`` values.
        :type categories: list[str] | None
        :param classification: New ``CLASS`` (empty leaves unchanged).
        :type classification: str
        :param url: New ``URL`` (empty leaves unchanged).
        :type url: str
        :param geo: New ``GEO`` value or :data:`None` to leave unchanged.
        :type geo: GeoCoordinatesWire | None
        :param transparency: New ``TRANSP`` (empty leaves unchanged).
        :type transparency: str
        :param resources: New ``RESOURCES`` values.
        :type resources: list[str] | None
        :param comments: New ``COMMENT`` values.
        :type comments: list[str] | None
        :param contacts: New ``CONTACT`` values.
        :type contacts: list[str] | None
        :param related_to: New ``RELATED-TO`` values.
        :type related_to: list[str] | None
        :param organizer: New ``ORGANIZER`` value.
        :type organizer: PersonWire | None
        :param attendees: New ``ATTENDEE`` list.
        :type attendees: list[AttendeeWire] | None
        :param alarms: New nested VALARM blocks.
        :type alarms: list[AlarmWire] | None
        :param attachments: New ``ATTACH`` URI references.
        :type attachments: list[BinaryReferenceWire] | None
        :param recurrence: New ``RRULE`` value.
        :type recurrence: RecurrenceRuleWire | None
        :param exdates: New ``EXDATE`` values.
        :type exdates: list[datetime.datetime] | None
        :param rdates: New ``RDATE`` values.
        :type rdates: list[datetime.datetime] | None
        :param recurrence_id: New ``RECURRENCE-ID`` value.
        :type recurrence_id: datetime.datetime | None
        :param clear_fields: Field names to remove. Allowed: ``description``,
            ``location``, ``categories``, ``classification``, ``url``, ``geo``,
            ``transparency``, ``resources``, ``comments``, ``contacts``,
            ``related_to``, ``organizer``, ``attendees``, ``alarms``,
            ``attachments``, ``recurrence``, ``exdates``, ``rdates``,
            ``recurrence_id``.
        :type clear_fields: list[str] | None
        :returns: The updated event.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``calendar_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), calendar_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.update_event,
            calendar_url=calendar_url,
            uid=uid,
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            categories=categories,
            classification=classification,
            url=url,
            geo=to_geo(geo),
            transparency=transparency,
            resources=resources,
            comments=comments,
            contacts=contacts,
            related_to=related_to,
            organizer=to_organizer(organizer),
            attendees=to_attendees(attendees),
            alarms=to_alarms(alarms),
            attachments=to_attachments(attachments),
            recurrence=to_recurrence(recurrence),
            exdates=exdates,
            rdates=rdates,
            recurrence_id=recurrence_id,
            clear_fields=clear_fields,
        )
        return event_to_dict(result)

    @server.tool
    @tool_logged
    async def delete_event(
        calendar_url: str,
        uid: str,
        account: str | None = None,
    ) -> dict[str, str]:
        """Delete an event by UID.

        :param calendar_url: Calendar URL that holds the event.
        :type calendar_url: str
        :param uid: UID of the event, returned by list_events or search_events.
        :type uid: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: ``{"status": "deleted", "uid": uid}`` on success.
        :rtype: dict[str, str]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``calendar_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), calendar_url)
        client = service.client_for(account)
        await asyncio.to_thread(
            client.delete_event,
            calendar_url=calendar_url,
            uid=uid,
        )
        return {"status": "deleted", "uid": uid}

    @server.tool(
        description=(
            "Find time windows where every listed account is free for a given duration. "
            "Omit 'accounts' to include every configured account. "
            "Working-hour bounds are evaluated in 'timezone' (IANA name); when "
            "omitted, the server's system local timezone is used."
        ),
    )
    @tool_logged
    async def find_free_time(
        start: datetime,
        end: datetime,
        duration_minutes: int,
        ctx: Context,
        accounts: StrListWire | None = None,
        working_hours_start: int | None = None,
        working_hours_end: int | None = None,
        timezone: str | None = None,
    ) -> list[dict[str, str]]:
        """Find common free slots across accounts.

        Reports per-account progress through ``ctx`` so MCP clients can
        render a scan indicator on multi-account requests. ``ctx.info``
        fires *before* each account's scan ("scanning X") so the user
        sees what's currently in flight; ``ctx.report_progress`` fires
        *after* each account's scan completes, so ``progress=N/total``
        always reflects work that genuinely finished — if account ``i``'s
        scan raises, the client only saw ``progress=(i-1)/total`` and
        knows the failure happened on account ``i``. ``ctx`` is a
        framework-injected parameter and is excluded from the wire-format
        tool schema.

        :param start: Earliest acceptable slot start. Naive datetimes use ``timezone``.
        :type start: datetime.datetime
        :param end: Latest acceptable slot end. Naive datetimes use ``timezone``.
        :type end: datetime.datetime
        :param duration_minutes: Minimum slot length in minutes.
        :type duration_minutes: int
        :param ctx: Framework-injected MCP context for progress reporting.
        :type ctx: :class:`fastmcp.Context`
        :param accounts: Account ids or display names. Omit to include every configured account.
        :type accounts: list[str] | None
        :param working_hours_start: Start hour (0-23) in ``timezone``.
        :type working_hours_start: int | None
        :param working_hours_end: End hour (0-23) in ``timezone``.
        :type working_hours_end: int | None
        :param timezone: IANA timezone for working-hour bounds. Omit for server local timezone.
        :type timezone: str | None
        :returns: List of ``{"start", "end"}`` ISO 8601 records.
        :rtype: list[dict[str, str]]
        """
        window = (
            (working_hours_start, working_hours_end)
            if working_hours_start is not None and working_hours_end is not None
            else None
        )
        resolved = registry.resolve_many(accounts)
        zone = resolve_zone(timezone)
        busy: list[tuple[datetime, datetime]] = []
        total = len(resolved)
        for index, account in enumerate(resolved, start=1):
            await ctx.info(f"scanning {account.id}")
            busy.extend(
                await asyncio.to_thread(service.busy_intervals_for_account, account.id, start, end)
            )
            # Strict completion semantics: progress is emitted only after the
            # per-account scan succeeds, so progress=N/total never claims a
            # failed-but-still-in-flight account is done.
            await ctx.report_progress(progress=index, total=total)
        slots = compute_free_slots(
            busy,
            start=start,
            end=end,
            duration_minutes=duration_minutes,
            working_hours=window,
            zone=zone,
        )
        return [{"start": slot.start.isoformat(), "end": slot.end.isoformat()} for slot in slots]


def event_to_dict(event: Any) -> dict[str, Any]:
    """Project an :class:`EventSummary` into an MCP-friendly dict with ISO timestamps.

    :param event: :class:`calcard_mcp.ical.EventSummary` instance.
    :type event: typing.Any
    :returns: Dict suitable for JSON serialisation.
    :rtype: dict[str, typing.Any]
    """
    data = asdict(event)
    data["start"] = event.start.isoformat()
    data["end"] = event.end.isoformat()
    data["exdates"] = [dt.isoformat() for dt in event.exdates]
    data["rdates"] = [dt.isoformat() for dt in event.rdates]
    data["recurrence_id"] = (
        event.recurrence_id.isoformat() if event.recurrence_id is not None else None
    )
    if event.recurrence is not None and event.recurrence.until is not None:
        data["recurrence"]["until"] = event.recurrence.until.isoformat()
    return data
