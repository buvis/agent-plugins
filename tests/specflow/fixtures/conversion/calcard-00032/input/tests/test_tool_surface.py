"""Pin the Python-callable surface (parameter names, order, types, return type).

PRD 00003 deleted the previous version of this snapshot because
``inspect.signature(tool.fn, eval_str=True)`` could not resolve forward
references after standalone ``fastmcp`` wrapped the registered function
(the wrap loses ``__globals__``), and ``Context`` parameters carry a
runtime sentinel default that's not stable to spell.

This replacement reads ``tool.fn.__annotations__`` directly. With
``from __future__ import annotations`` in every tool module, those
values are plain strings — no resolution required, no Context default
involved. ``dict.__eq__`` ignores order, so we compare list-of-tuples
to also lock down declaration order and catch silent reorders.

Wire-format coverage (descriptions, JSON-Schema shapes,
``additionalProperties``) lives in
:mod:`tests.test_tool_surface_snapshot`. The async-only registration
gate also lives there. This file complements both with parameter-name,
parameter-order, parameter-type, and return-type assertions.
"""

from __future__ import annotations

from typing import Any

import pytest

from calcard_mcp.config import AppConfig
from calcard_mcp.server import build_server

# Each entry is the ordered ``__annotations__`` of the registered tool's
# original Python callable. ``ctx`` for ``find_free_time`` is the
# framework-injected :class:`fastmcp.Context` parameter; we keep it in
# the snapshot so any rename or removal is a deliberate, visible change.
EXPECTED_ANNOTATIONS: dict[str, list[tuple[str, str]]] = {
    # Accounts
    "list_accounts": [
        ("return", "list[dict[str, Any]]"),
    ],
    # Calendars
    "list_calendars": [
        ("account", "str | None"),
        ("return", "list[dict[str, str]]"),
    ],
    "list_events": [
        ("calendar_url", "str"),
        ("start", "datetime"),
        ("end", "datetime"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "search_events": [
        ("query", "str"),
        ("start", "datetime"),
        ("end", "datetime"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "create_event": [
        ("calendar_url", "str"),
        ("summary", "str"),
        ("start", "datetime"),
        ("end", "datetime"),
        ("account", "str | None"),
        ("description", "str | None"),
        ("location", "str | None"),
        ("categories", "StrListWire | None"),
        ("classification", "str"),
        ("url", "str"),
        ("geo", "GeoCoordinatesWire | None"),
        ("transparency", "str"),
        ("resources", "StrListWire | None"),
        ("comments", "StrListWire | None"),
        ("contacts", "StrListWire | None"),
        ("related_to", "StrListWire | None"),
        ("organizer", "PersonWire | None"),
        ("attendees", "AttendeeListWire | None"),
        ("alarms", "AlarmListWire | None"),
        ("attachments", "AttachmentListWire | None"),
        ("recurrence", "RecurrenceRuleWire | None"),
        ("exdates", "ExDateListWire | None"),
        ("rdates", "RDateListWire | None"),
        ("recurrence_id", "datetime | None"),
        ("return", "dict[str, Any]"),
    ],
    "update_event": [
        ("calendar_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("summary", "str | None"),
        ("start", "datetime | None"),
        ("end", "datetime | None"),
        ("description", "str | None"),
        ("location", "str | None"),
        ("categories", "StrListWire | None"),
        ("classification", "str"),
        ("url", "str"),
        ("geo", "GeoCoordinatesWire | None"),
        ("transparency", "str"),
        ("resources", "StrListWire | None"),
        ("comments", "StrListWire | None"),
        ("contacts", "StrListWire | None"),
        ("related_to", "StrListWire | None"),
        ("organizer", "PersonWire | None"),
        ("attendees", "AttendeeListWire | None"),
        ("alarms", "AlarmListWire | None"),
        ("attachments", "AttachmentListWire | None"),
        ("recurrence", "RecurrenceRuleWire | None"),
        ("exdates", "ExDateListWire | None"),
        ("rdates", "RDateListWire | None"),
        ("recurrence_id", "datetime | None"),
        ("clear_fields", "StrListWire | None"),
        ("return", "dict[str, Any]"),
    ],
    "delete_event": [
        ("calendar_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("return", "dict[str, str]"),
    ],
    "find_free_time": [
        ("start", "datetime"),
        ("end", "datetime"),
        ("duration_minutes", "int"),
        ("ctx", "Context"),
        ("accounts", "StrListWire | None"),
        ("working_hours_start", "int | None"),
        ("working_hours_end", "int | None"),
        ("timezone", "str | None"),
        ("return", "list[dict[str, str]]"),
    ],
    # Contacts
    "list_address_books": [
        ("account", "str | None"),
        ("return", "list[dict[str, str]]"),
    ],
    "list_contacts": [
        ("address_book_url", "str"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "search_contacts": [
        ("query", "str"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "create_contact": [
        ("address_book_url", "str"),
        ("full_name", "str"),
        ("account", "str | None"),
        ("given_name", "str | None"),
        ("family_name", "str | None"),
        ("emails", "ContactValueListWire | None"),
        ("phones", "ContactValueListWire | None"),
        ("addresses", "PostalAddressListWire | None"),
        ("urls", "TypedURIListWire | None"),
        ("impps", "TypedURIListWire | None"),
        ("nicknames", "StringListWire | None"),
        ("categories", "StringListWire | None"),
        ("relations", "RelationListWire | None"),
        ("languages", "StringListWire | None"),
        ("timezone", "str | None"),
        ("geo", "GeoCoordinatesWire | None"),
        ("role", "str | None"),
        ("kind", "Literal['individual', 'group', 'org', 'location', ''] | None"),
        ("members", "StringListWire | None"),
        ("gender", "GenderWire | None"),
        ("birthday", "PartialDateWire | None"),
        ("anniversary", "PartialDateWire | None"),
        ("photo", "BinaryReferenceWire | None"),
        ("logo", "BinaryReferenceWire | None"),
        ("sound", "BinaryReferenceWire | None"),
        ("key", "BinaryReferenceWire | None"),
        ("organization", "str | None"),
        ("title", "str | None"),
        ("note", "str | None"),
        ("return", "dict[str, Any]"),
    ],
    "update_contact": [
        ("address_book_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("full_name", "str | None"),
        ("given_name", "str | None"),
        ("family_name", "str | None"),
        ("emails", "ContactValueListWire | None"),
        ("phones", "ContactValueListWire | None"),
        ("addresses", "PostalAddressListWire | None"),
        ("urls", "TypedURIListWire | None"),
        ("impps", "TypedURIListWire | None"),
        ("nicknames", "StringListWire | None"),
        ("categories", "StringListWire | None"),
        ("relations", "RelationListWire | None"),
        ("languages", "StringListWire | None"),
        ("timezone", "str | None"),
        ("geo", "GeoCoordinatesWire | None"),
        ("role", "str | None"),
        ("kind", "Literal['individual', 'group', 'org', 'location', ''] | None"),
        ("members", "StringListWire | None"),
        ("gender", "GenderWire | None"),
        ("birthday", "PartialDateWire | None"),
        ("anniversary", "PartialDateWire | None"),
        ("photo", "BinaryReferenceWire | None"),
        ("logo", "BinaryReferenceWire | None"),
        ("sound", "BinaryReferenceWire | None"),
        ("key", "BinaryReferenceWire | None"),
        ("organization", "str | None"),
        ("title", "str | None"),
        ("note", "str | None"),
        ("clear_fields", "StrListWire | None"),
        ("return", "dict[str, Any]"),
    ],
    "delete_contact": [
        ("address_book_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("return", "dict[str, str]"),
    ],
    # Tasks
    "list_task_lists": [
        ("account", "str | None"),
        ("return", "list[dict[str, str]]"),
    ],
    "list_tasks": [
        ("task_list_url", "str"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "search_tasks": [
        ("query", "str"),
        ("account", "str | None"),
        ("return", "list[dict[str, Any]]"),
    ],
    "create_task": [
        ("task_list_url", "str"),
        ("summary", "str"),
        ("account", "str | None"),
        ("description", "str | None"),
        ("due", "datetime | None"),
        ("status", "str"),
        ("priority", "int"),
        ("percent_complete", "int | None"),
        ("categories", "StrListWire | None"),
        ("classification", "str"),
        ("url", "str"),
        ("geo", "GeoCoordinatesWire | None"),
        ("resources", "StrListWire | None"),
        ("comments", "StrListWire | None"),
        ("contacts", "StrListWire | None"),
        ("related_to", "StrListWire | None"),
        ("organizer", "PersonWire | None"),
        ("attendees", "AttendeeListWire | None"),
        ("alarms", "AlarmListWire | None"),
        ("attachments", "AttachmentListWire | None"),
        ("recurrence", "RecurrenceRuleWire | None"),
        ("exdates", "ExDateListWire | None"),
        ("rdates", "RDateListWire | None"),
        ("recurrence_id", "datetime | None"),
        ("return", "dict[str, Any]"),
    ],
    "update_task": [
        ("task_list_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("summary", "str | None"),
        ("description", "str | None"),
        ("due", "datetime | None"),
        ("status", "str | None"),
        ("priority", "int | None"),
        ("percent_complete", "int | None"),
        ("completed", "datetime | None"),
        ("categories", "StrListWire | None"),
        ("classification", "str"),
        ("url", "str"),
        ("geo", "GeoCoordinatesWire | None"),
        ("resources", "StrListWire | None"),
        ("comments", "StrListWire | None"),
        ("contacts", "StrListWire | None"),
        ("related_to", "StrListWire | None"),
        ("organizer", "PersonWire | None"),
        ("attendees", "AttendeeListWire | None"),
        ("alarms", "AlarmListWire | None"),
        ("attachments", "AttachmentListWire | None"),
        ("recurrence", "RecurrenceRuleWire | None"),
        ("exdates", "ExDateListWire | None"),
        ("rdates", "RDateListWire | None"),
        ("recurrence_id", "datetime | None"),
        ("clear_fields", "StrListWire | None"),
        ("return", "dict[str, Any]"),
    ],
    "delete_task": [
        ("task_list_url", "str"),
        ("uid", "str"),
        ("account", "str | None"),
        ("return", "dict[str, str]"),
    ],
}


@pytest.fixture
async def registered_tools(app_config: AppConfig) -> Any:
    """Build the FastMCP server and yield ``{tool_name: Tool}``.

    The :class:`ContactService` returned alongside the server owns httpx
    pools and must be closed; the fixture handles cleanup.
    """
    server, contact_service, todo_service, calendar_service = build_server(app_config)
    try:
        tools = await server.list_tools()
        yield {tool.name: tool for tool in tools}
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()


@pytest.mark.asyncio
async def test_tool_names_match_expected(registered_tools: dict[str, Any]) -> None:
    assert set(registered_tools) == set(EXPECTED_ANNOTATIONS), (
        "Tool name set drifted from the snapshot. Update EXPECTED_ANNOTATIONS in "
        "the same commit if intentional."
    )


@pytest.mark.asyncio
async def test_tool_count(registered_tools: dict[str, Any]) -> None:
    assert len(registered_tools) == len(EXPECTED_ANNOTATIONS), (
        f"expected {len(EXPECTED_ANNOTATIONS)} tools, got {len(registered_tools)}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", sorted(EXPECTED_ANNOTATIONS))
async def test_tool_annotations_match_expected(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """Pin parameter names, order, types, and return type via ``__annotations__``.

    This catches: param rename, param reorder, param add/remove, type change,
    return-type change. With ``from __future__ import annotations`` the
    values are raw strings — the comparison is unambiguous.
    """
    tool: Any = registered_tools[tool_name]
    actual = list(tool.fn.__annotations__.items())
    expected = EXPECTED_ANNOTATIONS[tool_name]
    assert actual == expected, (
        f"Annotations for tool {tool_name!r} drifted.\n  expected: {expected}\n  actual:   {actual}"
    )
