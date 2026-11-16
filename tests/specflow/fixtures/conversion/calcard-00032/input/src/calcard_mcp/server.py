"""MCP server wiring: builds the FastMCP instance and delegates tool registration.

Tool registration lives in :mod:`calcard_mcp.tools`, organised by domain
(``accounts``, ``calendar``, ``contact``, ``todo``). This module's job
is to construct the per-account services, instantiate FastMCP, and call
each domain module's ``register`` entry point in order.

Imports:

* :mod:`contextlib` for :class:`~contextlib.ExitStack`, which runs every
  registered cleanup callback regardless of which one raises.
* :mod:`logging` for the cleanup-error logger.
* :class:`fastmcp.FastMCP` as the high-level MCP server.
* :class:`calcard_mcp.accounts.AccountRegistry` for account resolution.
* :class:`calcard_mcp.caldav_client.CalendarService`,
  :class:`calcard_mcp.carddav_client.ContactService`, and
  :class:`calcard_mcp.caltodo_client.TodoService` as the per-account
  client pools.
* :class:`calcard_mcp.config.AppConfig` for the loaded configuration.
* :mod:`calcard_mcp.tools.accounts`, :mod:`calcard_mcp.tools.calendar`,
  :mod:`calcard_mcp.tools.contact`, :mod:`calcard_mcp.tools.todo` for
  the per-domain tool registrations.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Protocol

from fastmcp import FastMCP

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.caldav_client import CalendarService
from calcard_mcp.caltodo_client import TodoService
from calcard_mcp.carddav_client import ContactService
from calcard_mcp.config import AppConfig
from calcard_mcp.tools import accounts as accounts_tools
from calcard_mcp.tools import calendar as calendar_tools
from calcard_mcp.tools import contact as contact_tools
from calcard_mcp.tools import todo as todo_tools

logger = logging.getLogger(__name__)


class _Closeable(Protocol):
    """Structural type for the per-account services that own connection pools."""

    def close(self) -> None: ...


def safe_close(service: _Closeable) -> None:
    """Best-effort ``close()`` that logs and swallows ``Exception`` errors.

    Used by :func:`build_server` and :func:`calcard_mcp.__main__.run`
    on their cleanup paths so a routine close-time ``Exception`` does
    not displace the original failure (registration error / shutdown
    reason) as the propagating exception. In production no service
    ``close()`` is expected to raise (each implementation already
    swallows transport-level errors internally), so this swallow-and-log
    layer is defence in depth rather than a routine code path.

    Scope is :class:`Exception` only. :class:`BaseException` signals
    (:class:`KeyboardInterrupt`, :class:`SystemExit`,
    :class:`asyncio.CancelledError`) deliberately propagate so a Ctrl-C,
    ``sys.exit``, or task cancel that lands inside ``close()`` is not
    silently dropped.

    Note that propagation does **not** abort an enclosing
    :class:`contextlib.ExitStack` cleanup chain. ``ExitStack.__exit__``
    catches every exception (including :class:`BaseException`) from each
    callback and continues popping subsequent callbacks; the propagating
    exception out of the ``with`` block is the **last** raise, with
    earlier raises (including any original error already in flight)
    chained as ``__context__``. So a ``BaseException`` from one
    ``close()`` lets the remaining ``close()`` callbacks still run, and
    can demote the original failure to ``__context__`` of the
    BaseException that surfaces. Callers that need stricter primary-
    exception preservation must avoid raising ``BaseException`` from
    ``close()``.

    :param service: An object with a ``close()`` method.
    :type service: :class:`_Closeable`
    :returns: None.
    :rtype: None
    """
    try:
        service.close()
    except Exception:
        logger.exception(
            "error closing %s during shutdown; swallowed to preserve original failure",
            type(service).__name__,
        )


def build_server(
    config: AppConfig,
) -> tuple[FastMCP, ContactService, TodoService, CalendarService]:
    """Construct and register a :class:`fastmcp.FastMCP` instance.

    The returned :class:`ContactService` owns the underlying CardDAV
    :class:`httpx.Client` connection pools, the returned
    :class:`TodoService` owns the underlying ``caldav`` HTTP sessions of
    the per-account VTODO clients, and the returned
    :class:`CalendarService` owns the underlying ``caldav`` HTTP
    sessions of the per-account VEVENT/free-busy clients. Callers are
    responsible for closing all three (e.g. via ``contact_service.close()``,
    ``todo_service.close()``, and ``calendar_service.close()`` or ``with``
    syntax) to release the pools cleanly.

    Cleanup on the error path runs every ``close()`` in LIFO order via
    :class:`contextlib.ExitStack`. Each close is wrapped in
    :func:`safe_close`, which catches :class:`Exception` only and logs
    the failure, so a routine close-time :class:`Exception` keeps the
    original FastMCP / tool-registration error as the propagating
    exception. ``safe_close`` does **not** swallow
    :class:`BaseException` (``KeyboardInterrupt``, ``SystemExit``,
    ``asyncio.CancelledError``); a ``BaseException`` from one ``close()``
    propagates and chains via Python's exception-context machinery.
    ``ExitStack`` continues popping the remaining callbacks (the chain
    is not aborted), and the registration error is demoted to
    ``__context__`` of whatever ``BaseException`` last raised. No
    service ``close()`` is expected to raise ``BaseException`` in
    production; the prose documents what happens if one ever does.

    :param config: Loaded application configuration.
    :type config: :class:`calcard_mcp.config.AppConfig`
    :returns: Four-tuple of the fully wired :class:`FastMCP` (ready for
        :meth:`FastMCP.run_async`), the :class:`ContactService`, the
        :class:`TodoService`, and the :class:`CalendarService`. The
        caller MUST close all three services on shutdown to release
        their connection pools.
    :rtype: tuple[:class:`fastmcp.FastMCP`,
        :class:`calcard_mcp.carddav_client.ContactService`,
        :class:`calcard_mcp.caltodo_client.TodoService`,
        :class:`calcard_mcp.caldav_client.CalendarService`]
    """
    registry = AccountRegistry(config)
    calendar_service = CalendarService(registry, config)
    contact_service = ContactService(registry, config.server)
    todo_service = TodoService(registry, config.server)
    # ContactService, TodoService, and CalendarService each own connection
    # pools that were just opened. If FastMCP construction or any
    # tool-registration step raises below, the caller never receives the
    # services and would leak the pools. Stage every close() on an
    # ExitStack wrapped in safe_close: on the success path we ``pop_all``
    # so the caller owns cleanup, and on any raise inside the ``with``
    # block ExitStack runs every wrapped callback in LIFO order. Register
    # in construction order (calendar, contact, todo) so LIFO firing yields
    # strict reverse-of-construction close order (todo, contact, calendar).
    # safe_close swallows close-time errors so the original failure
    # (registration error) remains the propagating exception.
    with contextlib.ExitStack() as cleanup:
        cleanup.callback(safe_close, calendar_service)
        cleanup.callback(safe_close, contact_service)
        cleanup.callback(safe_close, todo_service)
        # Auth placeholder: deployment PRD will plug ``auth=BearerAuthProvider(...)`` here.
        server = FastMCP(
            name="calcard-mcp",
            instructions=(
                "Multi-account CalDAV and CardDAV tools. The server holds separate "
                "credentials for every configured account; pass the 'account' "
                "argument (id or display name) on every call to act as that user. "
                "When acting on a calendar/address-book/task-list URL, 'account' "
                "must match the URL's owner — a mismatch raises "
                "CrossAccountAccessError before any HTTP traffic. Omit 'account' "
                "to use the default account. Writes are verified by re-reading "
                "the server-stored record. Call list_accounts first to discover "
                "valid account ids."
            ),
        )
        accounts_tools.register(server, registry)
        calendar_tools.register(server, registry, calendar_service)
        contact_tools.register(server, registry, contact_service)
        todo_tools.register(server, registry, todo_service)
        cleanup.pop_all()
    return server, contact_service, todo_service, calendar_service
