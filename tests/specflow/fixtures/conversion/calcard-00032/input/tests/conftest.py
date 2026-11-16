"""Shared pytest fixtures for calcard-mcp tests.

Two test-harness shapes are provided:

* **CalDAV**: :mod:`caldav` uses its own transport (not httpx), so tests
  substitute the :class:`caldav.davclient.DAVClient` class at import time
  with a :class:`unittest.mock.MagicMock`. The ``patch_caldav`` fixture
  returns a handle for configuring the fake principal / calendars / events.

* **CardDAV**: :mod:`calcard_mcp.carddav_client` uses :mod:`httpx`
  directly, so tests use :mod:`respx` to mock HTTP responses. The
  ``app_config`` fixture supplies a minimal two-account :class:`AppConfig`
  for both shapes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from calcard_mcp.config import AppConfig


@pytest.fixture
def app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    """Minimal two-account configuration: ``bob`` (writable, default) and ``eva`` (read-only)."""
    monkeypatch.setenv("PW", "secret")
    body = """
server:
  base_url: https://dav.example.com
  verify_tls: true
  timeout: 5.0
  verify_writes: true
accounts:
  - id: bob
    display_names: [Bob]
    principal_path: /bob/
    username: bob
    password_env: PW
    default: true
    writable: true
    timezone: Europe/Bratislava
  - id: eva
    display_names: [Eva]
    principal_path: /eva/
    username: eva
    password_env: PW
    writable: false
    timezone: Europe/Bratislava
"""
    path = tmp_path / "config.yaml"
    path.write_text(body, encoding="utf-8")
    return AppConfig.load(path)


class FakeCalDAV:
    """Container for a stubbed caldav DAVClient and its returned fakes.

    Tests configure the attributes directly:

    * ``dav_client`` — the DAVClient instance returned by the patched class.
    * ``principal`` — returned by ``dav_client.principal()``.
    * ``calendars`` — list returned by ``principal.calendars()``.
    * ``events_by_calendar_url`` — mapping ``calendar_url -> list of fake events``
      consulted by the ``calendar.search(...)`` side effect installed below.
    * ``events_by_uid`` — mapping ``uid -> fake event`` consulted by the
      ``calendar.event_by_uid(...)`` side effect.
    """

    def __init__(self) -> None:
        self.dav_client: Any = MagicMock(name="DAVClient")
        self.principal: Any = MagicMock(name="Principal")
        self.calendars: list[Any] = []
        self.events_by_calendar_url: dict[str, list[Any]] = {}
        self.events_by_uid: dict[str, Any] = {}

        self.dav_client.principal.return_value = self.principal
        self.principal.calendars.return_value = self.calendars
        self.dav_client.calendar.side_effect = self.resolve_calendar

    def resolve_calendar(self, *, url: str) -> Any:
        for calendar in self.calendars:
            if str(calendar.url) == url:
                return calendar
        calendar: Any = MagicMock(name=f"Calendar({url})")
        calendar.url = url

        def _search(**_kwargs: Any) -> list[Any]:
            return self.events_by_calendar_url.get(url, [])

        def _event_by_uid(uid: str) -> Any:
            return self.events_by_uid.get(uid)

        calendar.search.side_effect = _search
        calendar.event_by_uid.side_effect = _event_by_uid
        self.calendars.append(calendar)
        return calendar


@pytest.fixture
def fake_caldav(monkeypatch: pytest.MonkeyPatch) -> FakeCalDAV:
    """Install a FakeCalDAV and replace ``DAVClient`` in :mod:`calcard_mcp.caldav_client`.

    The patched symbol is the bound name inside ``caldav_client`` (not the
    source module), so the client under test receives the fake without the
    real ``caldav`` package ever being invoked.
    """
    fake = FakeCalDAV()

    def _fake_ctor(**_kwargs: Any) -> Any:
        return fake.dav_client

    monkeypatch.setattr("calcard_mcp.caldav_client.DAVClient", _fake_ctor)
    return fake


def build_fake_event(
    *,
    data: str,
    url: str = "https://dav.example.com/bob/calendar/event.ics",
    etag: str | None = '"etag-1"',
) -> MagicMock:
    """Build a MagicMock that mirrors the caldav Event surface used by the client."""
    event: Any = MagicMock(name=f"Event({url})")
    event.data = data
    event.url = url
    event.etag = etag
    event.load = MagicMock(name="Event.load")
    event.save = MagicMock(name="Event.save")
    event.delete = MagicMock(name="Event.delete")
    return event


class FakeCalTodo:
    """Container for a stubbed caldav DAVClient targeted at VTODO operations.

    Tests configure the attributes directly:

    * ``dav_client`` — the DAVClient instance returned by the patched class.
    * ``principal`` — returned by ``dav_client.principal()``.
    * ``calendars`` — list returned by ``principal.calendars()``.
    * ``todos_by_calendar_url`` — mapping ``calendar_url -> list of fake todos``
      consulted by the ``calendar.todos(...)`` side effect.
    * ``todos_by_uid`` — mapping ``uid -> fake todo`` consulted by
      ``calendar.todo_by_uid(...)``. A missing ``uid`` raises
      :class:`caldav.lib.error.NotFoundError`.
    """

    def __init__(self) -> None:
        self.dav_client: Any = MagicMock(name="DAVClient")
        self.principal: Any = MagicMock(name="Principal")
        self.calendars: list[Any] = []
        self.todos_by_calendar_url: dict[str, list[Any]] = {}
        self.todos_by_uid: dict[str, Any] = {}

        self.dav_client.principal.return_value = self.principal
        self.principal.calendars.return_value = self.calendars
        self.dav_client.calendar.side_effect = self.resolve_calendar

    def resolve_calendar(self, *, url: str) -> Any:
        for calendar in self.calendars:
            if str(calendar.url) == url:
                return calendar
        # Local import so the conftest stays light and so the fake matches
        # the same caldav exception type the client wraps at its boundary.
        from caldav.lib.error import NotFoundError

        calendar: Any = MagicMock(name=f"Calendar({url})")
        calendar.url = url

        def _todos(**_kwargs: Any) -> list[Any]:
            return self.todos_by_calendar_url.get(url, [])

        def _todo_by_uid(uid: str) -> Any:
            try:
                return self.todos_by_uid[uid]
            except KeyError as exc:
                raise NotFoundError(f"todo {uid!r} not found") from exc

        calendar.todos.side_effect = _todos
        calendar.todo_by_uid.side_effect = _todo_by_uid
        # Default: calendar advertises both VEVENT and VTODO support. Tests
        # override per-case with calendar.get_supported_components.return_value.
        calendar.get_supported_components.return_value = ["VEVENT", "VTODO"]
        self.calendars.append(calendar)
        return calendar


@pytest.fixture
def fake_caltodo(monkeypatch: pytest.MonkeyPatch) -> FakeCalTodo:
    """Install a FakeCalTodo and replace ``DAVClient`` in :mod:`calcard_mcp.caltodo_client`.

    The patched symbol is the bound name inside ``caltodo_client`` (not the
    source module), so the client under test receives the fake without the
    real ``caldav`` package ever being invoked.
    """
    fake = FakeCalTodo()

    def _fake_ctor(**_kwargs: Any) -> Any:
        return fake.dav_client

    monkeypatch.setattr("calcard_mcp.caltodo_client.DAVClient", _fake_ctor)
    return fake


def build_fake_todo(
    *,
    data: str,
    url: str = "https://dav.example.com/bob/tasks/t1.ics",
    etag: str | None = '"etag-1"',
) -> MagicMock:
    """Build a MagicMock that mirrors the caldav Todo surface used by the client."""
    todo: Any = MagicMock(name=f"Todo({url})")
    todo.data = data
    todo.url = url
    todo.etag = etag
    todo.load = MagicMock(name="Todo.load")
    todo.save = MagicMock(name="Todo.save")
    todo.delete = MagicMock(name="Todo.delete")
    return todo
