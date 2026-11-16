"""MCP tool registrations for task (VTODO/CalDAV) operations.

The :func:`register` function is invoked once during server construction.
It attaches the task-related MCP tools (``list_task_lists``,
``list_tasks``, ``search_tasks``, ``create_task``, ``update_task``,
``delete_task``) to the supplied :class:`fastmcp.FastMCP` instance.

Imports:

* :mod:`asyncio` to offload sync CalDAV calls onto worker threads.
* :mod:`datetime` for parameter types on tool functions.
* :mod:`dataclasses.asdict` to project frozen summaries into MCP-friendly dicts.
* :class:`fastmcp.FastMCP` for the tool registry.
* :class:`calcard_mcp.accounts.AccountRegistry` for write-safety checks.
* :class:`calcard_mcp.caltodo_client.TodoService` for per-account clients.
* :class:`calcard_mcp.vtodo.TaskSummary` for the projected dict shape.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caltodo_client import TodoService
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
from calcard_mcp.vtodo import TaskSummary

__all__ = ["register"]


def register(server: FastMCP, registry: AccountRegistry, service: TodoService) -> None:
    """Attach task tools to ``server``.

    :param server: :class:`FastMCP` instance.
    :type server: :class:`fastmcp.FastMCP`
    :param registry: Account registry used for write-safety checks.
    :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :param service: Configured task service.
    :type service: :class:`calcard_mcp.caltodo_client.TodoService`
    :returns: None. Tools are registered on ``server`` in place.
    :rtype: None
    """

    @server.tool
    @tool_logged
    async def list_task_lists(account: str | None = None) -> list[dict[str, str]]:
        """List every VTODO-supporting task list on one account.

        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: One record per task list with ``account_id``, ``name``, and ``url``.
        :rtype: list[dict[str, str]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_task_lists)
        return [asdict(item) for item in result]

    @server.tool
    @tool_logged
    async def list_tasks(
        task_list_url: str,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """List every task in one task list.

        :param task_list_url: Task list URL returned by list_task_lists.
        :type task_list_url: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Task records in server order.
        :rtype: list[dict[str, typing.Any]]
        """
        registry.require_url_match(registry.resolve(account), task_list_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_tasks, task_list_url)
        return [task_to_dict(item) for item in result]

    @server.tool(
        description=(
            "Search every task list on one account for tasks whose summary or "
            "description contains 'query' (case-insensitive). Results are "
            "deduplicated by UID."
        ),
    )
    @tool_logged
    async def search_tasks(
        query: str,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search every task list on one account for a substring match.

        :param query: Substring to match (case-insensitive).
        :type query: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Matching tasks.
        :rtype: list[dict[str, typing.Any]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.search_tasks, query)
        return [task_to_dict(item) for item in result]

    @server.tool(
        description=(
            "Create a task in a task list. 'task_list_url' and 'summary' are "
            "required. Naive datetimes are interpreted in the account's "
            "configured timezone. Optional structured fields cover the full "
            "iCalendar VTODO surface: categories, classification, url, geo, "
            "resources, comments, contacts, related_to, organizer, attendees, "
            "alarms, attachments, recurrence, exdates, rdates, recurrence_id."
        ),
    )
    @tool_logged
    async def create_task(
        task_list_url: str,
        summary: str,
        account: str | None = None,
        description: str | None = None,
        due: datetime | None = None,
        status: str = "needs-action",
        priority: int = 0,
        percent_complete: int | None = None,
        categories: StrListWire | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinatesWire | None = None,
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
        """Create a task in a task list.

        :param task_list_url: Task list URL returned by list_task_lists.
        :type task_list_url: str
        :param summary: Task title.
        :type summary: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param description: Body text.
        :type description: str | None
        :param due: Due datetime. Naive datetimes use the account's timezone.
        :type due: datetime.datetime | None
        :param status: Lifecycle state. One of 'needs-action', 'in-process',
            'completed', 'cancelled'. Setting to 'completed' auto-sets the
            completed timestamp and percent_complete=100; transitioning away
            clears them.
        :type status: str
        :param priority: Priority 0-9. 0 means undefined; 1 is highest, 9 is
            lowest (RFC 5545).
        :type priority: int
        :param percent_complete: Percent complete 0-100. Set explicitly;
            auto-managed when status transitions to 'completed'.
        :type percent_complete: int | None
        :param categories: VTODO ``CATEGORIES`` values.
        :type categories: list[str] | None
        :param classification: VTODO ``CLASS`` value (e.g. ``public``, ``private``).
        :type classification: str
        :param url: VTODO ``URL`` value.
        :type url: str
        :param geo: VTODO ``GEO`` coordinates ({latitude, longitude}).
        :type geo: GeoCoordinatesWire | None
        :param resources: VTODO ``RESOURCES`` values.
        :type resources: list[str] | None
        :param comments: VTODO ``COMMENT`` values.
        :type comments: list[str] | None
        :param contacts: VTODO ``CONTACT`` values.
        :type contacts: list[str] | None
        :param related_to: VTODO ``RELATED-TO`` values.
        :type related_to: list[str] | None
        :param organizer: VTODO ``ORGANIZER`` ({address, common_name}).
        :type organizer: PersonWire | None
        :param attendees: VTODO ``ATTENDEE`` entries.
        :type attendees: list[AttendeeWire] | None
        :param alarms: Nested VALARM blocks.
        :type alarms: list[AlarmWire] | None
        :param attachments: VTODO ``ATTACH`` URI references.
        :type attachments: list[BinaryReferenceWire] | None
        :param recurrence: VTODO ``RRULE`` value.
        :type recurrence: RecurrenceRuleWire | None
        :param exdates: VTODO ``EXDATE`` values.
        :type exdates: list[datetime.datetime] | None
        :param rdates: VTODO ``RDATE`` values.
        :type rdates: list[datetime.datetime] | None
        :param recurrence_id: VTODO ``RECURRENCE-ID`` value.
        :type recurrence_id: datetime.datetime | None
        :returns: The created task.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``task_list_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), task_list_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.create_task,
            task_list_url=task_list_url,
            summary=summary,
            description=description,
            due=due,
            status=status,
            priority=priority,
            percent_complete=percent_complete,
            categories=categories,
            classification=classification,
            url=url,
            geo=to_geo(geo),
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
        return task_to_dict(result)

    @server.tool(
        description=(
            "Update fields on an existing task. Argument semantics: None "
            "preserves the field; for 'description' an empty string sets the "
            "property to empty; for 'classification' and 'url' an empty string "
            "is treated as preserve (use 'clear_fields' to remove). List "
            "'clear_fields' to remove any supported property entirely. "
            "Valid clear_fields entries: 'description', 'due', 'completed', "
            "'categories', 'classification', 'url', 'geo', 'resources', "
            "'comments', 'contacts', 'related_to', 'organizer', 'attendees', "
            "'alarms', 'attachments', 'recurrence', 'exdates', 'rdates', "
            "'recurrence_id'. Explicit field values in the same call win over "
            "status auto-completion (e.g. status='completed', "
            "percent_complete=42 stores 42). Naive datetimes are interpreted "
            "in the account's configured timezone."
        ),
    )
    @tool_logged
    async def update_task(
        task_list_url: str,
        uid: str,
        account: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        due: datetime | None = None,
        status: str | None = None,
        priority: int | None = None,
        percent_complete: int | None = None,
        completed: datetime | None = None,
        categories: StrListWire | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinatesWire | None = None,
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
        """Update an existing VTODO with read-after-write verification.

        :param task_list_url: Task list URL returned by list_task_lists.
        :type task_list_url: str
        :param uid: UID of the task, returned by list_tasks or search_tasks.
        :type uid: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param summary: New task title.
        :type summary: str | None
        :param description: New body text.
        :type description: str | None
        :param due: Due datetime. Naive datetimes use the account's timezone.
        :type due: datetime.datetime | None
        :param status: Lifecycle state. One of 'needs-action', 'in-process',
            'completed', 'cancelled'. Setting to 'completed' auto-sets the
            completed timestamp and percent_complete=100; transitioning away
            clears them.
        :type status: str | None
        :param priority: Priority 0-9. 0 means undefined; 1 is highest, 9 is
            lowest (RFC 5545).
        :type priority: int | None
        :param percent_complete: Percent complete 0-100. Set explicitly;
            auto-managed when status transitions to 'completed'.
        :type percent_complete: int | None
        :param completed: Explicit completion timestamp. Wins over the
            status-driven auto-fill.
        :type completed: datetime.datetime | None
        :param categories: New ``CATEGORIES`` values.
        :type categories: list[str] | None
        :param classification: New ``CLASS`` (empty leaves unchanged).
        :type classification: str
        :param url: New ``URL`` (empty leaves unchanged).
        :type url: str
        :param geo: New ``GEO`` value or :data:`None` to leave unchanged.
        :type geo: GeoCoordinatesWire | None
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
            ``due``, ``completed``, ``categories``, ``classification``,
            ``url``, ``geo``, ``resources``, ``comments``, ``contacts``,
            ``related_to``, ``organizer``, ``attendees``, ``alarms``,
            ``attachments``, ``recurrence``, ``exdates``, ``rdates``,
            ``recurrence_id``.
        :type clear_fields: list[str] | None
        :returns: The updated task.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``task_list_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), task_list_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.update_task,
            task_list_url=task_list_url,
            uid=uid,
            summary=summary,
            description=description,
            due=due,
            status=status,
            priority=priority,
            percent_complete=percent_complete,
            completed=completed,
            categories=categories,
            classification=classification,
            url=url,
            geo=to_geo(geo),
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
        return task_to_dict(result)

    @server.tool
    @tool_logged
    async def delete_task(
        task_list_url: str,
        uid: str,
        account: str | None = None,
    ) -> dict[str, str]:
        """Delete a task by UID.

        :param task_list_url: Task list URL returned by list_task_lists.
        :type task_list_url: str
        :param uid: UID of the task, returned by list_tasks or search_tasks.
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
            ``task_list_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), task_list_url)
        client = service.client_for(account)
        await asyncio.to_thread(
            client.delete_task,
            task_list_url=task_list_url,
            uid=uid,
        )
        return {"status": "deleted", "uid": uid}


def task_to_dict(task: TaskSummary) -> dict[str, Any]:
    """Project a :class:`TaskSummary` into an MCP-friendly dict with ISO timestamps.

    :param task: :class:`calcard_mcp.vtodo.TaskSummary` instance.
    :type task: :class:`calcard_mcp.vtodo.TaskSummary`
    :returns: Dict suitable for JSON serialisation.
    :rtype: dict[str, typing.Any]
    """
    data = asdict(task)
    data["due"] = task.due.isoformat() if task.due is not None else None
    data["completed"] = task.completed.isoformat() if task.completed is not None else None
    data["exdates"] = [dt.isoformat() for dt in task.exdates]
    data["rdates"] = [dt.isoformat() for dt in task.rdates]
    data["recurrence_id"] = (
        task.recurrence_id.isoformat() if task.recurrence_id is not None else None
    )
    if task.recurrence is not None and task.recurrence.until is not None:
        data["recurrence"]["until"] = task.recurrence.until.isoformat()
    return data
