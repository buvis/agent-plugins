"""Integration pinning for PRD 00010 §10.8 failure surfaces."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import fastmcp
import fastmcp.exceptions
import httpx
import pytest

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalDAVClient
from calcard_mcp.carddav_client import CardDAVClient
from calcard_mcp.config import AppConfig
from calcard_mcp.errors import WriteVerificationError
from calcard_mcp.server import build_server
from calcard_mcp.vcard import build_vcard

from .conftest import CleanupTracker
from .conftest import calendar_url as _calendar_url

pytestmark = pytest.mark.integration


def _address_book_url(app_config: AppConfig, account_id: str = "bob") -> str:
    registry = AccountRegistry(app_config)
    client = CardDAVClient(registry.resolve(account_id), app_config.server)
    try:
        return client.list_address_books()[0].url
    finally:
        client.close()


async def test_create_contact_unknown_account_lists_known_ids(
    radicale_app_config: AppConfig,
) -> None:
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    try:
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(fastmcp.exceptions.ToolError) as excinfo:
                await fmcp.call_tool(
                    "create_contact",
                    {
                        "account": "nonexistent",
                        "address_book_url": "http://x",
                        "full_name": "Test",
                    },
                )
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()

    message = str(excinfo.value)
    assert "nonexistent" in message
    for account_id in ("bob", "eva", "sophia", "emma"):
        assert account_id in message


async def test_create_event_with_start_after_end_raises_tool_error(
    radicale_app_config: AppConfig,
) -> None:
    """PRD §10.8 / cycle-2 review: drive through ``fastmcp.Client`` so the
    structured ``ValueError`` is observed as the wrapped MCP ``ToolError``,
    consistent with the other §10.8 surfaces."""
    cal_url = _calendar_url(radicale_app_config)
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    try:
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(
                fastmcp.exceptions.ToolError,
                match=r"end.*after.*start",
            ):
                await fmcp.call_tool(
                    "create_event",
                    {
                        "calendar_url": cal_url,
                        "summary": "bad",
                        "start": "2027-06-01T11:00:00+00:00",
                        "end": "2027-06-01T10:00:00+00:00",
                    },
                )
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()


async def test_create_contact_for_emma_raises_account_not_writable_error(
    radicale_app_config: AppConfig,
) -> None:
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    try:
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(
                fastmcp.exceptions.ToolError,
                match=r"emma.*read-only",
            ):
                await fmcp.call_tool(
                    "create_contact",
                    {
                        "account": "emma",
                        "address_book_url": "http://x",
                        "full_name": "Test",
                    },
                )
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()


async def test_update_contact_unknown_uid_includes_uid_in_message(
    radicale_app_config: AppConfig,
) -> None:
    ab_url = _address_book_url(radicale_app_config)
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    try:
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(fastmcp.exceptions.ToolError) as excinfo:
                await fmcp.call_tool(
                    "update_contact",
                    {
                        "account": "bob",
                        "address_book_url": ab_url,
                        "uid": "nonexistent-uid-12345",
                        "note": "x",
                    },
                )
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()

    assert "nonexistent-uid-12345" in str(excinfo.value)


async def test_update_contact_after_concurrent_etag_bump_raises_tool_error(
    radicale_app_config: AppConfig,
    unique_uid: str,
    track_for_cleanup: CleanupTracker,
) -> None:
    """PRD §10.8 / cycle-2 review: drive the WriteVerificationError surface
    through ``fastmcp.Client`` and observe it as the wrapped MCP ``ToolError``.

    The drift hook must fire on the *same* CardDAVClient instance the server
    uses internally; ``contact_service.client_for("bob")`` returns that
    instance, so the hook installed there fires during the MCP-driven
    ``update_contact`` call.
    """
    registry = AccountRegistry(radicale_app_config)
    account = registry.resolve("bob")
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    inner_client = contact_service.client_for("bob")
    ab_url = inner_client.list_address_books()[0].url
    created_uid: str | None = None

    def _cleanup_created_contact() -> None:
        if created_uid is None:
            return
        inner_client.delete_contact(address_book_url=ab_url, uid=created_uid)

    track_for_cleanup.add(
        unique_uid,
        _cleanup_created_contact,
        f"contact ETag conflict cleanup for {unique_uid}",
    )

    try:
        created = inner_client.create_contact(
            address_book_url=ab_url,
            full_name=f"Concurrent {unique_uid}",
        )
        created_uid = created.uid
        mutated_body = build_vcard(
            uid=created.uid,
            full_name=f"Mutated {unique_uid}",
            given_name=None,
            family_name=None,
            emails=None,
            phones=None,
            organization=None,
            title=None,
            note=None,
        )
        with httpx.Client(
            auth=(account.config.username, account.password),
            timeout=radicale_app_config.server.timeout,
        ) as raw:
            response = raw.put(
                created.url,
                content=mutated_body,
                headers={"Content-Type": "text/vcard; charset=utf-8"},
            )
            response.raise_for_status()

        mutated_after_update = False

        def _mutate_after_update_put(response: httpx.Response) -> None:
            nonlocal mutated_after_update
            if mutated_after_update or response.request.method != "PUT":
                return
            mutated_after_update = True
            verifier_drift_body = build_vcard(
                uid=created.uid,
                full_name=f"Mutated {unique_uid}",
                given_name=None,
                family_name=None,
                emails=None,
                phones=None,
                organization=None,
                title=None,
                note="server-side drift",
            )
            with httpx.Client(
                auth=(account.config.username, account.password),
                timeout=radicale_app_config.server.timeout,
            ) as raw:
                drift_response = raw.put(
                    created.url,
                    content=verifier_drift_body,
                    headers={"Content-Type": "text/vcard; charset=utf-8"},
                )
                drift_response.raise_for_status()

        http_client = cast(httpx.Client, vars(inner_client)["_http"])
        http_client.event_hooks["response"].append(_mutate_after_update_put)
        try:
            async with fastmcp.Client(server) as fmcp:
                with pytest.raises(fastmcp.exceptions.ToolError) as excinfo:
                    await fmcp.call_tool(
                        "update_contact",
                        {
                            "account": "bob",
                            "address_book_url": ab_url,
                            "uid": created.uid,
                            "note": "updated note",
                        },
                    )
        finally:
            http_client.event_hooks["response"].remove(_mutate_after_update_put)

        assert mutated_after_update
        # PRD 00010 §10.8 acceptance: failure-mode message must carry the
        # diagnostic context (UID + ETag pair) so callers can act on the
        # failure beyond the exception type. ToolError preserves the wrapped
        # WriteVerificationError message verbatim.
        msg = str(excinfo.value)
        assert created.uid in msg, msg
        assert "pre_etag=" in msg, msg
        assert "post_etag=" in msg, msg
        # And the field-diff content must still surface the drifted field.
        assert "NOTE" in msg or "note" in msg, msg
        assert "server-side drift" in msg, msg
    finally:
        track_for_cleanup.drain(unique_uid)
        contact_service.close()
        todo_service.close()
        calendar_service.close()


async def test_create_event_with_malformed_recurrence_raw_raises_tool_error(
    radicale_app_config: AppConfig,
) -> None:
    """PRD §10.8 / cycle-2 review: malformed RRULE FREQ surface routed through
    ``fastmcp.Client`` so the iCal-layer ``ValueError`` is observed as the
    wrapped MCP ``ToolError``."""
    cal_url = _calendar_url(radicale_app_config)
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    try:
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(
                fastmcp.exceptions.ToolError,
                match=r"FREQ|RRULE",
            ):
                await fmcp.call_tool(
                    "create_event",
                    {
                        "calendar_url": cal_url,
                        "summary": "bad rrule",
                        "start": "2027-06-01T10:00:00+00:00",
                        "end": "2027-06-01T10:30:00+00:00",
                        "recurrence": {"raw": "FREQ=BOGUS"},
                    },
                )
    finally:
        contact_service.close()
        todo_service.close()
        calendar_service.close()


def test_update_event_after_concurrent_etag_bump_raises_write_verification_error(
    radicale_app_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
    unique_uid: str,
    track_for_cleanup: CleanupTracker,
) -> None:
    """Mirror of the contacts equivalent for VEVENT writes (PRD 00010 §10.4 +
    §10.8): a server-side modification between client PUT and verifier GET must
    surface a structured ``WriteVerificationError`` whose message carries the
    diagnostic UID and ETag pair.

    The drift fires from inside ``_verify_event`` (between the PUT and the
    re-read), so the verifier's GET sees the drifted body.

    Stays at the direct ``CalDAVClient`` layer rather than driving through
    ``fastmcp.Client``: ``build_server`` does not return the internal
    :class:`CalendarService`, so the test cannot install the drift hook on
    the same client instance the MCP server uses for ``bob``. The contact
    equivalent (``test_update_contact_after_concurrent_etag_bump_raises_tool_error``)
    drives through ``fastmcp.Client`` because ``ContactService`` *is* returned.
    """
    registry = AccountRegistry(radicale_app_config)
    account = registry.resolve("bob")
    client = CalDAVClient(account, radicale_app_config.server)
    cal_url = _calendar_url(radicale_app_config)
    created_uid: str | None = None

    def _cleanup_created_event() -> None:
        if created_uid is None:
            return
        client.delete_event(calendar_url=cal_url, uid=created_uid)

    track_for_cleanup.add(
        unique_uid,
        _cleanup_created_event,
        f"direct event ETag conflict cleanup for {unique_uid}",
    )

    try:
        start = datetime(2027, 6, 8, 9, tzinfo=UTC)
        end = start + timedelta(minutes=30)
        created = client.create_event(
            calendar_url=cal_url,
            summary=f"Concurrent {unique_uid}",
            start=start,
            end=end,
        )
        created_uid = created.uid

        listed = client.list_events(cal_url, start - timedelta(hours=1), end + timedelta(hours=1))
        resource_url = next(event.resource_url for event in listed if event.uid == created.uid)

        drift_body = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//calcard-mcp//drift//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{created.uid}\r\n"
            "DTSTAMP:20270608T000000Z\r\n"
            "DTSTART:20270608T090000Z\r\n"
            "DTEND:20270608T093000Z\r\n"
            "SUMMARY:server-side drift\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        mutated_after_update = False
        # `_verify_event` is a deliberate test seam between PUT and re-read.
        # Read via cast(Any, ...) and write via monkeypatch.setattr to keep
        # the strict pyright pass clean (reportPrivateUsage applies to typed
        # attribute access, not to Any-typed attribute access or
        # MonkeyPatch.setattr's string-name installer). monkeypatch auto-
        # undoes the install at test teardown, so no manual finally needed.
        original_verify = cast(Any, client)._verify_event

        def _drift_then_verify(*args: object, **kwargs: object) -> None:
            nonlocal mutated_after_update
            if not mutated_after_update:
                mutated_after_update = True
                with httpx.Client(
                    auth=(account.config.username, account.password),
                    timeout=radicale_app_config.server.timeout,
                ) as raw:
                    drift_response = raw.put(
                        resource_url,
                        content=drift_body,
                        headers={"Content-Type": "text/calendar; charset=utf-8"},
                    )
                    drift_response.raise_for_status()
            return original_verify(*args, **kwargs)

        monkeypatch.setattr(client, "_verify_event", _drift_then_verify)
        with pytest.raises(WriteVerificationError) as excinfo:
            client.update_event(
                calendar_url=cal_url,
                uid=created.uid,
                summary=f"Updated {unique_uid}",
            )

        assert mutated_after_update
        msg = str(excinfo.value)
        assert created.uid in msg, msg
        assert "pre_etag=" in msg, msg
        assert "post_etag=" in msg, msg
        assert "SUMMARY" in msg or "summary" in msg, msg
        assert "server-side drift" in msg, msg
        assert excinfo.value.field_diffs, "expected structured field_diffs"
    finally:
        track_for_cleanup.drain(unique_uid)
        client.close()


async def test_update_event_after_concurrent_etag_bump_raises_tool_error(
    radicale_app_config: AppConfig,
    monkeypatch: pytest.MonkeyPatch,
    unique_uid: str,
    track_for_cleanup: CleanupTracker,
) -> None:
    """Drive the event ETag-conflict path through ``fastmcp.Client``.

    ``build_server`` does not expose the internal ``CalendarService``, so this
    installs the drift seam at the ``CalDAVClient`` class level. That makes the
    server-owned client instance hit the same between-PUT-and-re-read mutation
    window that the direct-client sibling test covers.
    """
    registry = AccountRegistry(radicale_app_config)
    account = registry.resolve("bob")
    client = CalDAVClient(account, radicale_app_config.server)
    cal_url = _calendar_url(radicale_app_config)
    server, contact_service, todo_service, calendar_service = build_server(radicale_app_config)
    created_uid: str | None = None

    def _cleanup_created_event() -> None:
        if created_uid is None:
            return
        client.delete_event(calendar_url=cal_url, uid=created_uid)

    track_for_cleanup.add(
        unique_uid,
        _cleanup_created_event,
        f"MCP event ETag conflict cleanup for {unique_uid}",
    )

    try:
        start = datetime(2027, 6, 8, 11, tzinfo=UTC)
        end = start + timedelta(minutes=30)
        created = client.create_event(
            calendar_url=cal_url,
            summary=f"Concurrent MCP {unique_uid}",
            start=start,
            end=end,
        )
        created_uid = created.uid

        drift_body = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//calcard-mcp//drift//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{created.uid}\r\n"
            "DTSTAMP:20270608T000000Z\r\n"
            "DTSTART:20270608T110000Z\r\n"
            "DTEND:20270608T113000Z\r\n"
            "SUMMARY:server-side drift\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        mutated_after_update = False
        original_verify = cast(Any, CalDAVClient)._verify_event

        def _drift_then_verify(
            self: CalDAVClient,
            event: Any,
            *,
            summary: str | None,
            description: str | None,
            location: str | None,
        ) -> None:
            nonlocal mutated_after_update
            if not mutated_after_update:
                mutated_after_update = True
                with httpx.Client(
                    auth=(self.account.config.username, self.account.password),
                    timeout=self.server.timeout,
                ) as raw:
                    drift_response = raw.put(
                        created.resource_url,
                        content=drift_body,
                        headers={"Content-Type": "text/calendar; charset=utf-8"},
                    )
                    drift_response.raise_for_status()
            return original_verify(
                self,
                event,
                summary=summary,
                description=description,
                location=location,
            )

        monkeypatch.setattr(CalDAVClient, "_verify_event", _drift_then_verify)
        async with fastmcp.Client(server) as fmcp:
            with pytest.raises(fastmcp.exceptions.ToolError) as excinfo:
                await fmcp.call_tool(
                    "update_event",
                    {
                        "account": "bob",
                        "calendar_url": cal_url,
                        "uid": created.uid,
                        "summary": f"Updated MCP {unique_uid}",
                    },
                )

        assert mutated_after_update
        msg = str(excinfo.value)
        assert created.uid in msg, msg
        assert "pre_etag=" in msg, msg
        assert "post_etag=" in msg, msg
        assert "SUMMARY" in msg or "summary" in msg, msg
        assert "server-side drift" in msg, msg
    finally:
        track_for_cleanup.drain(unique_uid)
        contact_service.close()
        todo_service.close()
        calendar_service.close()
        client.close()
