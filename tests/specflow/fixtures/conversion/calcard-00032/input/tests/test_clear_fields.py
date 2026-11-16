"""Tests for the ``clear_fields`` parameter (PRD 00001 §1.6).

Both ``update_event`` (optional DESCRIPTION, LOCATION) and ``update_contact``
(optional ORG, TITLE, NOTE) must support explicit removal distinct from
"preserve" (``None``) and "set to empty string".
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
import respx
from httpx import Response
from icalendar import Calendar as ICalCalendar

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalDAVClient
from calcard_mcp.caltodo_client import CalTodoClient
from calcard_mcp.carddav_client import CardDAVClient
from calcard_mcp.config import AppConfig, ServerConfig
from calcard_mcp.ical import (
    Alarm,
    Attendee,
    Person,
    RecurrenceRule,
    apply_event_clears,
    build_event_ical,
    parse_vevent_to_summary,
)
from calcard_mcp.ical import BinaryReference as EventBinaryReference
from calcard_mcp.ical import GeoCoordinates as EventGeoCoordinates
from calcard_mcp.vcard import (
    BinaryReference,
    Gender,
    GeoCoordinates,
    PartialDate,
    PostalAddress,
    Relation,
    TypedURI,
    apply_contact_clears,
    build_vcard,
    parse_vcard,
    parse_vcard_to_summary,
    serialize_vcard,
)
from calcard_mcp.vtodo import (
    apply_todo_clears,
    build_vtodo,
    parse_vtodo,
)

from .conftest import FakeCalDAV, FakeCalTodo, build_fake_event, build_fake_todo

_ICAL_WITH_OPTIONALS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VEVENT
UID:u1@calcard
DTSTAMP:20260501T000000Z
DTSTART:20260501T090000Z
DTEND:20260501T100000Z
SUMMARY:Meeting
DESCRIPTION:Original description
LOCATION:Conference room
END:VEVENT
END:VCALENDAR
"""


def _no_verify_server(server: ServerConfig) -> ServerConfig:
    return ServerConfig(
        base_url=server.base_url,
        verify_tls=server.verify_tls,
        timeout=server.timeout,
        verify_writes=False,
    )


# ---------------------------------------------------------------------------
# update_event
# ---------------------------------------------------------------------------


def _wire_event(fake_caldav: FakeCalDAV, event: Any) -> None:
    fake_caldav.dav_client.calendar.side_effect = None
    fake_caldav.dav_client.calendar.return_value = fake_caldav.resolve_calendar(
        url="https://dav.example.com/bob/cal/"
    )
    fake_caldav.events_by_uid["u1@calcard"] = event


def _vevent(ical_text: str) -> Any:
    parsed: Any = ICalCalendar.from_ical(ical_text)
    return next(iter(parsed.walk("VEVENT")))


def test_clear_fields_removes_description(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_OPTIONALS)
    _wire_event(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        clear_fields=["description"],
    )

    ve = _vevent(event.data)
    assert ve.get("DESCRIPTION") is None
    assert str(ve.get("LOCATION")) == "Conference room"  # untouched


def test_clear_fields_clears_both_description_and_location(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_OPTIONALS)
    _wire_event(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        clear_fields=["description", "location"],
    )
    ve = _vevent(event.data)
    assert ve.get("DESCRIPTION") is None
    assert ve.get("LOCATION") is None


def test_clear_fields_rejects_required_field(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_OPTIONALS)
    _wire_event(fake_caldav, event)

    with pytest.raises(ValueError):
        client.update_event(
            calendar_url="https://dav.example.com/bob/cal/",
            uid="u1@calcard",
            clear_fields=["summary"],
        )


def test_clear_wins_over_explicit_value(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Per PRD: listing a field in clear_fields wins even if the same field is also set."""
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_OPTIONALS)
    _wire_event(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        description="Would be ignored",
        clear_fields=["description"],
    )
    ve = _vevent(event.data)
    assert ve.get("DESCRIPTION") is None


def test_empty_string_sets_description_to_empty_not_removed(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    """Per PRD 1.6: an empty string preserves the property with an empty value.
    This is the documented middle state, distinct from ``None`` (preserve) and
    ``clear_fields=["description"]`` (remove the property entirely).
    """
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_OPTIONALS)
    _wire_event(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        description="",
        location="",
    )
    ve = _vevent(event.data)
    description = ve.get("DESCRIPTION")
    location = ve.get("LOCATION")
    assert description is not None, "DESCRIPTION must be present (set to empty), not removed"
    assert str(description) == ""
    assert location is not None, "LOCATION must be present (set to empty), not removed"
    assert str(location) == ""


# ---------------------------------------------------------------------------
# update_contact
# ---------------------------------------------------------------------------

_VCARD_WITH_OPTIONALS = """BEGIN:VCARD
VERSION:3.0
UID:c1@calcard
FN:Jane Doe
N:Doe;Jane;;;
ORG:Acme
TITLE:Engineer
NOTE:Prefers tea
END:VCARD
"""


def _build_carddav_client(app_config: AppConfig) -> CardDAVClient:
    return CardDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )


def _mock_find_and_update(
    respx_mock: respx.MockRouter,
    *,
    ab_url: str,
    resource_url: str,
    initial_vcard: str,
) -> dict[str, str]:
    """Install respx routes for a minimal update_contact flow.

    Returns a dict holding the latest PUT body so tests can inspect it.
    """
    multistatus = f"""<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:response>
    <D:href>{resource_url}</D:href>
    <D:propstat>
      <D:prop>
        <D:getetag>"etag-before"</D:getetag>
        <C:address-data>{initial_vcard}</C:address-data>
      </D:prop>
      <D:status>HTTP/1.1 200 OK</D:status>
    </D:propstat>
  </D:response>
</D:multistatus>
"""
    respx_mock.request("REPORT", ab_url).mock(return_value=Response(405))
    respx_mock.request("PROPFIND", ab_url).mock(
        return_value=Response(207, content=multistatus.encode("utf-8"))
    )
    respx_mock.get(resource_url).mock(
        return_value=Response(
            200,
            content=initial_vcard.encode("utf-8"),
            headers={"ETag": '"etag-before"'},
        )
    )
    captured: dict[str, str] = {"body": ""}

    def _put(request: Any) -> Response:
        captured["body"] = request.content.decode("utf-8")
        return Response(204, headers={"ETag": '"etag-after"'})

    respx_mock.put(resource_url).mock(side_effect=_put)
    return captured


def test_update_contact_clears_organization(app_config: AppConfig) -> None:
    client = _build_carddav_client(app_config)
    ab_url = "https://dav.example.com/bob/ab/"
    resource_url = "https://dav.example.com/bob/ab/c1.vcf"
    with respx.mock(assert_all_called=False) as mock:
        captured = _mock_find_and_update(
            mock,
            ab_url=ab_url,
            resource_url=resource_url,
            initial_vcard=_VCARD_WITH_OPTIONALS,
        )
        client.update_contact(
            address_book_url=ab_url,
            uid="c1@calcard",
            clear_fields=["organization"],
        )
    assert "ORG" not in captured["body"]
    assert "TITLE:Engineer" in captured["body"]
    assert "NOTE:Prefers tea" in captured["body"]


def test_update_contact_clears_all_three_optional_fields(app_config: AppConfig) -> None:
    client = _build_carddav_client(app_config)
    ab_url = "https://dav.example.com/bob/ab/"
    resource_url = "https://dav.example.com/bob/ab/c1.vcf"
    with respx.mock(assert_all_called=False) as mock:
        captured = _mock_find_and_update(
            mock,
            ab_url=ab_url,
            resource_url=resource_url,
            initial_vcard=_VCARD_WITH_OPTIONALS,
        )
        client.update_contact(
            address_book_url=ab_url,
            uid="c1@calcard",
            clear_fields=["organization", "title", "note"],
        )
    body = captured["body"]
    assert "ORG" not in body
    assert "TITLE" not in body
    assert "NOTE" not in body


def test_update_contact_rejects_required_field(app_config: AppConfig) -> None:
    client = _build_carddav_client(app_config)
    ab_url = "https://dav.example.com/bob/ab/"
    resource_url = "https://dav.example.com/bob/ab/c1.vcf"
    with respx.mock(assert_all_called=False) as mock:
        _mock_find_and_update(
            mock,
            ab_url=ab_url,
            resource_url=resource_url,
            initial_vcard=_VCARD_WITH_OPTIONALS,
        )
        with pytest.raises(ValueError):
            client.update_contact(
                address_book_url=ab_url,
                uid="c1@calcard",
                clear_fields=["full_name"],
            )


def test_contact_clear_wins_over_explicit_value(app_config: AppConfig) -> None:
    client = _build_carddav_client(app_config)
    ab_url = "https://dav.example.com/bob/ab/"
    resource_url = "https://dav.example.com/bob/ab/c1.vcf"
    with respx.mock(assert_all_called=False) as mock:
        captured = _mock_find_and_update(
            mock,
            ab_url=ab_url,
            resource_url=resource_url,
            initial_vcard=_VCARD_WITH_OPTIONALS,
        )
        client.update_contact(
            address_book_url=ab_url,
            uid="c1@calcard",
            note="Would be ignored",
            clear_fields=["note"],
        )
    assert "NOTE" not in captured["body"]


def test_contact_empty_string_preserves_property_with_empty_value(app_config: AppConfig) -> None:
    """Per PRD 1.6: passing an empty string sets the field to empty, distinct
    from ``None`` (preserve original) and ``clear_fields=["org"]`` (remove the
    property entirely).
    """
    client = _build_carddav_client(app_config)
    ab_url = "https://dav.example.com/bob/ab/"
    resource_url = "https://dav.example.com/bob/ab/c1.vcf"
    with respx.mock(assert_all_called=False) as mock:
        captured = _mock_find_and_update(
            mock,
            ab_url=ab_url,
            resource_url=resource_url,
            initial_vcard=_VCARD_WITH_OPTIONALS,
        )
        client.update_contact(
            address_book_url=ab_url,
            uid="c1@calcard",
            organization="",
            note="",
        )
    body = captured["body"]
    # The properties remain present (so the server can record "deliberately empty")
    # but with no value after the colon. Distinct from clear_fields, where the
    # entire property line is gone.
    assert "ORG" in body, "ORG must remain (set to empty), not be removed"
    assert "NOTE" in body, "NOTE must remain (set to empty), not be removed"
    # Sanity: the original non-empty values are gone.
    assert "ORG:Acme" not in body
    assert "NOTE:Prefers tea" not in body


_PURE_ACCOUNT_ID = "bob"
_PURE_BOOK_URL = "https://dav.example.com/bob/contacts/"
_PURE_RES_URL = "https://dav.example.com/bob/contacts/c1.vcf"


def _full_surface_vcard() -> str:
    return build_vcard(
        uid="c1@calcard",
        full_name="Jane Doe",
        given_name="Jane",
        family_name="Doe",
        emails=[],
        phones=[],
        addresses=[PostalAddress(street="1 Main", locality="Town", type="home")],
        urls=[TypedURI(value="https://example.com", type="work")],
        impps=[TypedURI(value="xmpp:jane@example.com", type="home")],
        nicknames=["Janie"],
        categories=["work"],
        relations=[Relation(value="urn:uuid:rel", type="friend")],
        languages=["en"],
        timezone="Europe/Bratislava",
        role="Engineer",
        kind="group",
        geo=GeoCoordinates(latitude=48.1486, longitude=17.1077),
        gender=Gender(sex="F", identity="woman"),
        members=["urn:uuid:member"],
        birthday=PartialDate(year=1990, month=5, day=6),
        anniversary=PartialDate(year=2015, month=6, day=7),
        photo=BinaryReference(value="https://example.com/photo.jpg"),
        logo=BinaryReference(value="https://example.com/logo.png"),
        sound=BinaryReference(value="https://example.com/sound.ogg"),
        key=BinaryReference(value="https://example.com/key.asc"),
        organization="Acme",
        title="Engineer",
        note="Prefers tea",
    )


@pytest.mark.parametrize(
    "clear_field",
    [
        "addresses",
        "urls",
        "impps",
        "nicknames",
        "categories",
        "relations",
        "languages",
        "members",
        "photo",
        "logo",
        "sound",
        "key",
        "gender",
        "birthday",
        "anniversary",
        "timezone",
        "geo",
        "role",
        "kind",
        "organization",
        "title",
        "note",
    ],
)
def test_apply_contact_clears_supports_full_contact_surface(clear_field: str) -> None:
    parsed = parse_vcard(_full_surface_vcard())
    apply_contact_clears(parsed, [clear_field])
    summary = parse_vcard_to_summary(
        serialize_vcard(parsed),
        account_id=_PURE_ACCOUNT_ID,
        address_book_url=_PURE_BOOK_URL,
        resource_url=_PURE_RES_URL,
    )
    assert summary is not None
    assert {
        "addresses": summary.addresses == [],
        "urls": summary.urls == [],
        "impps": summary.impps == [],
        "nicknames": summary.nicknames == [],
        "categories": summary.categories == [],
        "relations": summary.relations == [],
        "languages": summary.languages == [],
        "members": summary.members == [],
        "photo": summary.photo is None,
        "logo": summary.logo is None,
        "sound": summary.sound is None,
        "key": summary.key is None,
        "gender": summary.gender is None,
        "birthday": summary.birthday is None,
        "anniversary": summary.anniversary is None,
        "timezone": summary.timezone == "",
        "geo": summary.geo is None,
        "role": summary.role == "",
        "kind": summary.kind == "",
        "organization": summary.organization == "",
        "title": summary.title == "",
        "note": summary.note == "",
    }[clear_field]


def test_apply_contact_clears_unknown_field_error_mentions_sorted_allowlist() -> None:
    parsed = parse_vcard(_full_surface_vcard())
    with pytest.raises(ValueError) as exc_info:
        apply_contact_clears(parsed, ["not-a-field"])
    expected_allowlist = sorted(
        [
            "addresses",
            "anniversary",
            "birthday",
            "categories",
            "gender",
            "geo",
            "impps",
            "key",
            "kind",
            "languages",
            "logo",
            "members",
            "nicknames",
            "note",
            "organization",
            "photo",
            "relations",
            "role",
            "sound",
            "timezone",
            "title",
            "urls",
        ]
    )
    message = str(exc_info.value)
    assert "valid clear_fields:" in message
    assert str(expected_allowlist) in message


# ---------------------------------------------------------------------------
# update_event — full-surface clear_fields
# ---------------------------------------------------------------------------

_PURE_EVENT_ACCOUNT_ID = "bob"
_PURE_EVENT_CAL_URL = "https://dav.example.com/bob/cal/"
_PURE_EVENT_RES_URL = "https://dav.example.com/bob/cal/u-full.ics"


def _full_surface_vevent_ical() -> str:
    return build_event_ical(
        uid="u-full@calcard",
        summary="Full surface",
        start=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
        end=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        description="desc",
        location="loc",
        categories=["work", "urgent"],
        classification="private",
        url="https://example.com/event",
        geo=EventGeoCoordinates(latitude=48.1486, longitude=17.1077),
        transparency="opaque",
        resources=["projector"],
        comments=["a comment"],
        contacts=["mailto:desk@example.com"],
        related_to=["parent-uid"],
        organizer=Person(address="mailto:org@example.com", common_name="Org"),
        attendees=[Attendee(address="mailto:a@example.com", common_name="Alice")],
        alarms=[Alarm(action="display", trigger="-PT15M", description="Reminder")],
        attachments=[
            EventBinaryReference(value="https://example.com/file.pdf", media_type="application/pdf")
        ],
        recurrence=RecurrenceRule(raw="FREQ=WEEKLY;COUNT=10"),
        exdates=[datetime(2026, 5, 6, 12, 0, tzinfo=UTC)],
        rdates=[datetime(2026, 6, 6, 12, 0, tzinfo=UTC)],
        recurrence_id=datetime(2026, 5, 6, 12, 0, tzinfo=UTC),
    )


_NEW_EVENT_CLEAR_FIELDS: list[str] = [
    "categories",
    "classification",
    "url",
    "geo",
    "transparency",
    "resources",
    "comments",
    "contacts",
    "related_to",
    "organizer",
    "attendees",
    "alarms",
    "attachments",
    "recurrence",
    "exdates",
    "rdates",
    "recurrence_id",
]


@pytest.mark.parametrize("clear_field", _NEW_EVENT_CLEAR_FIELDS)
def test_apply_event_clears_supports_full_event_surface(clear_field: str) -> None:
    parsed: Any = ICalCalendar.from_ical(_full_surface_vevent_ical())
    vevent = next(iter(parsed.walk("VEVENT")))
    apply_event_clears(vevent, [clear_field])
    summary = parse_vevent_to_summary(
        parsed.to_ical().decode("utf-8"),
        account_id=_PURE_EVENT_ACCOUNT_ID,
        calendar_url=_PURE_EVENT_CAL_URL,
        resource_url=_PURE_EVENT_RES_URL,
        fallback_tz="UTC",
    )
    assert summary is not None
    expectation = {
        "categories": summary.categories == [],
        "classification": summary.classification == "",
        "url": summary.url == "",
        "geo": summary.geo is None,
        "transparency": summary.transparency == "",
        "resources": summary.resources == [],
        "comments": summary.comments == [],
        "contacts": summary.contacts == [],
        "related_to": summary.related_to == [],
        "organizer": summary.organizer is None,
        "attendees": summary.attendees == [],
        "alarms": summary.alarms == [],
        "attachments": summary.attachments == [],
        "recurrence": summary.recurrence is None,
        "exdates": summary.exdates == [],
        "rdates": summary.rdates == [],
        "recurrence_id": summary.recurrence_id is None,
    }[clear_field]
    assert expectation, f"clear_field {clear_field!r} did not revert to empty/default"
    # Spot-check at least 2 unrelated fields are preserved.
    assert summary.uid == "u-full@calcard"
    assert summary.summary == "Full surface"


def test_apply_event_clears_unknown_field_error_mentions_sorted_allowlist() -> None:
    parsed: Any = ICalCalendar.from_ical(_full_surface_vevent_ical())
    vevent = next(iter(parsed.walk("VEVENT")))
    with pytest.raises(ValueError) as exc_info:
        apply_event_clears(vevent, ["nonsense"])
    expected_allowlist = sorted(
        [
            "description",
            "location",
            "categories",
            "classification",
            "url",
            "geo",
            "transparency",
            "resources",
            "comments",
            "contacts",
            "related_to",
            "organizer",
            "attendees",
            "alarms",
            "attachments",
            "recurrence",
            "exdates",
            "rdates",
            "recurrence_id",
        ]
    )
    message = str(exc_info.value)
    assert "valid clear_fields:" in message
    assert str(expected_allowlist) in message


_ICAL_WITH_NEW_PROPERTIES = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VEVENT
UID:u1@calcard
DTSTAMP:20260501T000000Z
DTSTART:20260501T090000Z
DTEND:20260501T100000Z
SUMMARY:Meeting
CATEGORIES:work,urgent
TRANSP:OPAQUE
RRULE:FREQ=WEEKLY;COUNT=10
END:VEVENT
END:VCALENDAR
"""


def test_clear_fields_round_trip_clears_categories_transparency_recurrence(
    app_config: AppConfig,
    fake_caldav: FakeCalDAV,
) -> None:
    client = CalDAVClient(
        AccountRegistry(app_config).default(),
        _no_verify_server(app_config.server),
    )
    event = build_fake_event(data=_ICAL_WITH_NEW_PROPERTIES)
    _wire_event(fake_caldav, event)

    client.update_event(
        calendar_url="https://dav.example.com/bob/cal/",
        uid="u1@calcard",
        clear_fields=["categories", "transparency", "recurrence"],
    )

    body = event.data
    assert "CATEGORIES" not in body
    assert "TRANSP" not in body
    assert "RRULE" not in body
    # Required / preserved properties remain.
    assert "UID:u1@calcard" in body
    assert "SUMMARY:Meeting" in body
    assert "DTSTART:20260501T090000Z" in body
    assert "DTEND:20260501T100000Z" in body


# ---------------------------------------------------------------------------
# update_task — full-surface clear_fields
# ---------------------------------------------------------------------------

_PURE_TODO_ACCOUNT_ID = "bob"
_PURE_TODO_LIST_URL = "https://dav.example.com/bob/tasks/"
_PURE_TODO_RES_URL = "https://dav.example.com/bob/tasks/t-full.ics"


def _full_surface_vtodo_ical() -> str:
    return build_vtodo(
        uid="t-full@calcard",
        summary="Full surface",
        description="desc",
        due=datetime(2026, 5, 1, 17, 0, tzinfo=UTC),
        status="in-process",
        priority=5,
        percent_complete=40,
        completed=datetime(2026, 4, 30, 12, 0, tzinfo=UTC),
        categories=["work", "urgent"],
        classification="private",
        url="https://example.com/task",
        geo=EventGeoCoordinates(latitude=48.1486, longitude=17.1077),
        resources=["projector"],
        comments=["a comment"],
        contacts=["mailto:desk@example.com"],
        related_to=["parent-uid"],
        organizer=Person(address="mailto:org@example.com", common_name="Org"),
        attendees=[Attendee(address="mailto:a@example.com", common_name="Alice")],
        alarms=[Alarm(action="display", trigger="-PT15M", description="Reminder")],
        attachments=[
            EventBinaryReference(value="https://example.com/file.pdf", media_type="application/pdf")
        ],
        recurrence=RecurrenceRule(raw="FREQ=WEEKLY;COUNT=10"),
        exdates=[datetime(2026, 5, 6, 12, 0, tzinfo=UTC)],
        rdates=[datetime(2026, 6, 6, 12, 0, tzinfo=UTC)],
        recurrence_id=datetime(2026, 5, 6, 12, 0, tzinfo=UTC),
    )


_NEW_TODO_CLEAR_FIELDS: list[str] = [
    "categories",
    "classification",
    "url",
    "geo",
    "resources",
    "comments",
    "contacts",
    "related_to",
    "organizer",
    "attendees",
    "alarms",
    "attachments",
    "recurrence",
    "exdates",
    "rdates",
    "recurrence_id",
]


@pytest.mark.parametrize("clear_field", _NEW_TODO_CLEAR_FIELDS)
def test_apply_todo_clears_supports_full_todo_surface(clear_field: str) -> None:
    parsed: Any = ICalCalendar.from_ical(_full_surface_vtodo_ical())
    vtodo = next(iter(parsed.walk("VTODO")))
    apply_todo_clears(vtodo, [clear_field])
    summary = parse_vtodo(
        parsed.to_ical().decode("utf-8"),
        account_id=_PURE_TODO_ACCOUNT_ID,
        task_list_url=_PURE_TODO_LIST_URL,
        resource_url=_PURE_TODO_RES_URL,
        fallback_tz="UTC",
    )
    assert summary is not None
    expectation = {
        "categories": summary.categories == [],
        "classification": summary.classification == "",
        "url": summary.url == "",
        "geo": summary.geo is None,
        "resources": summary.resources == [],
        "comments": summary.comments == [],
        "contacts": summary.contacts == [],
        "related_to": summary.related_to == [],
        "organizer": summary.organizer is None,
        "attendees": summary.attendees == [],
        "alarms": summary.alarms == [],
        "attachments": summary.attachments == [],
        "recurrence": summary.recurrence is None,
        "exdates": summary.exdates == [],
        "rdates": summary.rdates == [],
        "recurrence_id": summary.recurrence_id is None,
    }[clear_field]
    assert expectation, f"clear_field {clear_field!r} did not revert to empty/default"
    # Spot-check at least 2 unrelated fields are preserved.
    assert summary.uid == "t-full@calcard"
    assert summary.summary == "Full surface"


def test_apply_todo_clears_rejects_transparency_for_tasks() -> None:
    """``transparency`` is event-only; the VTODO allowlist must not include it."""
    parsed: Any = ICalCalendar.from_ical(_full_surface_vtodo_ical())
    vtodo = next(iter(parsed.walk("VTODO")))
    with pytest.raises(ValueError) as exc_info:
        apply_todo_clears(vtodo, ["transparency"])
    expected_allowlist = sorted(
        [
            "description",
            "due",
            "completed",
            "categories",
            "classification",
            "url",
            "geo",
            "resources",
            "comments",
            "contacts",
            "related_to",
            "organizer",
            "attendees",
            "alarms",
            "attachments",
            "recurrence",
            "exdates",
            "rdates",
            "recurrence_id",
        ]
    )
    message = str(exc_info.value)
    assert "valid clear_fields:" in message
    assert str(expected_allowlist) in message
    assert "transparency" not in expected_allowlist
    assert "'transparency'" not in str(expected_allowlist)


_VTODO_WITH_NEW_PROPERTIES = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//calcard-mcp//EN
BEGIN:VTODO
UID:t1@calcard
DTSTAMP:20260501T000000Z
SUMMARY:Plan
STATUS:NEEDS-ACTION
PRIORITY:0
PERCENT-COMPLETE:0
CATEGORIES:work,urgent
ATTENDEE;CN=Alice:mailto:a@example.com
RRULE:FREQ=WEEKLY;COUNT=10
END:VTODO
END:VCALENDAR
"""


def _no_verify_server_for_todo(server: ServerConfig) -> ServerConfig:
    return ServerConfig(
        base_url=server.base_url,
        verify_tls=server.verify_tls,
        timeout=server.timeout,
        verify_writes=False,
    )


def _wire_todo(fake_caltodo: FakeCalTodo, todo: Any) -> None:
    calendar = fake_caltodo.resolve_calendar(url="https://dav.example.com/bob/tasks/")
    calendar.get_supported_components.return_value = ["VTODO"]
    fake_caltodo.dav_client.calendar.side_effect = None
    fake_caltodo.dav_client.calendar.return_value = calendar
    fake_caltodo.todos_by_uid["t1@calcard"] = todo


def test_update_task_clear_fields_round_trip_clears_categories_recurrence_attendees(
    app_config: AppConfig,
    fake_caltodo: FakeCalTodo,
) -> None:
    client = CalTodoClient(
        AccountRegistry(app_config).default(),
        _no_verify_server_for_todo(app_config.server),
    )
    todo = build_fake_todo(
        data=_VTODO_WITH_NEW_PROPERTIES,
        url="https://dav.example.com/bob/tasks/t1.ics",
    )
    _wire_todo(fake_caltodo, todo)

    client.update_task(
        task_list_url="https://dav.example.com/bob/tasks/",
        uid="t1@calcard",
        clear_fields=["categories", "recurrence", "attendees"],
    )

    body = todo.data
    assert "CATEGORIES" not in body
    assert "RRULE" not in body
    assert "ATTENDEE" not in body
    # Required / preserved properties remain.
    assert "UID:t1@calcard" in body
    assert "SUMMARY:Plan" in body
