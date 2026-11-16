"""Multi-account CalDAV client built on the :mod:`caldav` library.

Pure iCal byte-pushing lives in :mod:`calcard_mcp.ical`; this module owns
transport, write verification flow, and free-time logic only.

The ~2000-line implementation is split across cohesive sibling modules to keep
every file under the 800-line limit (review rule R13):

* :mod:`calcard_mcp._caldav_base` holds the shared constants, dataclasses, and
  module-level helpers that both this module and the mixins import.
* :mod:`calcard_mcp._caldav_recurrence` supplies the listing / recurrence /
  search mixin (:meth:`CalDAVClient.list_events`, :meth:`search_events`, ...).
* :mod:`calcard_mcp._caldav_mutation` supplies the verified-write mixin
  (:meth:`CalDAVClient.create_event`, :meth:`update_event`, :meth:`delete_event`,
  the verification helpers, and :meth:`_event_to_summary`).
* :mod:`calcard_mcp._caldav_service` supplies the pure free-time helpers
  (:func:`resolve_zone`, :func:`compute_free_slots`).

:class:`CalDAVClient` assembles the mixins onto its core surface (``__init__``,
``close``, ``dav_client``, ``_principal``, ``_calendar``, ``list_calendars``,
and the freebusy methods). ``DAVClient`` stays a module-level name and is
referenced through this module's namespace so ``conftest``'s monkeypatch of
``calcard_mcp.caldav_client.DAVClient`` takes effect.

Imports:

* :mod:`datetime` for timezone-aware datetime handling.
* :class:`caldav.DAVClient` from the ``caldav`` package for protocol access.
* :class:`calcard_mcp.accounts.ResolvedAccount` and
  :class:`calcard_mcp.accounts.AccountRegistry` for credential lookup.
* :class:`calcard_mcp.config.ServerConfig` for shared HTTP settings.
* :class:`calcard_mcp.errors.ProtocolError` to signal unexpected server responses.
* :mod:`calcard_mcp.freebusy` for the VFREEBUSY parser.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any, cast

from caldav.davclient import DAVClient
from caldav.lib.error import AuthorizationError, DAVError, NotFoundError

from calcard_mcp._caldav_base import (
    _TRANSPORT_EXCEPTIONS,
    CalendarSummary,
    FreeSlot,
)
from calcard_mcp._caldav_mutation import CalDAVMutationMixin
from calcard_mcp._caldav_recurrence import CalDAVRecurrenceMixin
from calcard_mcp._caldav_service import compute_free_slots, resolve_zone
from calcard_mcp.accounts import AccountRegistry, ResolvedAccount
from calcard_mcp.config import AppConfig, ServerConfig
from calcard_mcp.dav_client import DAVClientBase
from calcard_mcp.errors import ProtocolError
from calcard_mcp.freebusy import parse_vfreebusy
from calcard_mcp.ical import EventSummary, parse_vevent_to_summary

__all__ = [
    "CalDAVClient",
    "CalendarService",
    "CalendarSummary",
    "EventSummary",
    "FreeSlot",
    "compute_free_slots",
    "resolve_zone",
]

_LOG = logging.getLogger(__name__)


class CalDAVClient(CalDAVRecurrenceMixin, CalDAVMutationMixin, DAVClientBase):
    """Per-account CalDAV client with verified writes.

    The listing / recurrence / search surface lives on
    :class:`calcard_mcp._caldav_recurrence.CalDAVRecurrenceMixin`; the
    verified-write surface lives on
    :class:`calcard_mcp._caldav_mutation.CalDAVMutationMixin`. This class keeps
    the transport core (``__init__``, ``close``, ``dav_client``, ``_principal``,
    ``_calendar``, ``list_calendars``, and the freebusy methods).

    :cvar account: Resolved account this client operates as.
    :vartype account: :class:`calcard_mcp.accounts.ResolvedAccount`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, account: ResolvedAccount, server: ServerConfig) -> None:
        """Build a CalDAV client for a single account.

        :param account: Account whose credentials drive every request.
        :type account: :class:`calcard_mcp.accounts.ResolvedAccount`
        :param server: Shared server configuration.
        :type server: :class:`calcard_mcp.config.ServerConfig`
        """
        super().__init__(account, server)
        # DAVClient is typed as Any: caldav ships py.typed but leaves many
        # method signatures partially-unknown; annotating at the FFI boundary
        # avoids a cascade of downstream inference errors.
        self._dav: Any = DAVClient(
            url=self._base_url,
            username=account.config.username,
            password=account.password,
            ssl_verify_cert=server.verify_tls,
            timeout=int(server.timeout),
        )
        self._freebusy_capable: dict[str, bool] = {}
        self._closed: bool = False

    def close(self) -> None:
        """Close the underlying ``caldav`` HTTP session if exposed.

        Mirrors :meth:`calcard_mcp.caltodo_client.CalTodoClient.close`'s
        defensive pattern: ``caldav`` 1.x exposes the underlying
        :class:`requests.Session` as a ``session`` attribute, and closing it
        releases pooled connections. The attribute is best-effort because the
        path may shift across library versions, so any failure during
        teardown is logged at debug level and otherwise ignored — a teardown
        that raises would mask the real error from the caller.

        :returns: None.
        :rtype: None
        """
        session: Any = getattr(self._dav, "session", None)
        if session is not None:
            try:
                session.close()
            except Exception:
                _LOG.debug(
                    "close() swallowed exception while shutting down DAV session",
                    exc_info=True,
                )
        self._closed = True

    @property
    def is_closed(self) -> bool:
        """Whether :meth:`close` has been called on this client.

        :returns: ``True`` once :meth:`close` has been called, ``False``
            otherwise. Note that this reflects ``calcard-mcp``'s own
            close-call accounting; a still-open underlying session whose
            owning :class:`CalDAVClient` was never closed will still report
            ``False``.
        :rtype: bool
        """
        return self._closed

    @property
    def dav_client(self) -> Any:
        """Return the underlying ``caldav.DAVClient`` for advanced or integration use.

        Tools should prefer the public methods on :class:`CalDAVClient`.
        Integration tests and operator scripts that need to issue raw
        DAV requests (e.g. PUT a VEVENT with an RRULE that the public
        :meth:`create_event` does not expose) can reach the underlying
        client through this accessor.

        :returns: The :class:`caldav.davclient.DAVClient` instance.
        :rtype: typing.Any
        """
        return self._dav

    def _principal(self) -> Any:
        """Fetch the CalDAV principal for this account.

        :returns: :class:`caldav.Principal` object.
        :rtype: typing.Any
        :raises calcard_mcp.errors.ProtocolError: On authentication or discovery failures.
        """
        try:
            return self._dav.principal()
        except Exception as exc:
            raise ProtocolError(
                f"principal discovery failed for {self.account.id!r}: {exc}"
            ) from exc

    def is_freebusy_capable(self, calendar_url: str) -> bool:
        """Return whether ``calendar_url`` advertises ``<C:free-busy-query/>`` support.

        Detection runs once per calendar URL and is cached for the
        process lifetime. Subsequent calls return the cached bit. The
        result of a runtime ``free-busy-query`` REPORT failure does NOT
        flip this bit — the next call retries REPORT.

        :param calendar_url: Absolute calendar URL.
        :type calendar_url: str
        :returns: ``True`` when the server's
            ``DAV:supported-report-set`` PROPFIND response contains
            ``<C:free-busy-query/>``; ``False`` otherwise (including
            on detection error).
        :rtype: bool
        """
        cached = self._freebusy_capable.get(calendar_url)
        if cached is not None:
            return cached
        capable = self._detect_freebusy_capability(calendar_url)
        self._freebusy_capable[calendar_url] = capable
        return capable

    def is_freebusy_capability_known(self, calendar_url: str) -> bool | None:
        """Return the cached capability bit for ``calendar_url`` without probing.

        :param calendar_url: Absolute calendar URL.
        :type calendar_url: str
        :returns: ``True``/``False`` when capability detection has run for
            this URL; :data:`None` when the cache has no entry yet.
        :rtype: bool | None
        """
        return self._freebusy_capable.get(calendar_url)

    def set_freebusy_capability(self, calendar_url: str, capable: bool) -> None:
        """Seed the capability cache for ``calendar_url`` without probing.

        Used by integration tests and operators that already know a
        calendar's capability and want to skip the PROPFIND probe.

        :param calendar_url: Absolute calendar URL.
        :type calendar_url: str
        :param capable: Whether the calendar advertises ``<C:free-busy-query/>``.
        :type capable: bool
        :returns: None.
        :rtype: None
        """
        self._freebusy_capable[calendar_url] = capable

    def _detect_freebusy_capability(self, calendar_url: str) -> bool:
        """Issue a depth-0 PROPFIND for ``DAV:supported-report-set``.

        Returns ``True`` iff the response advertises a
        ``<C:free-busy-query/>`` element nested inside any
        ``<D:supported-report>`` element. Any error during detection
        (network failure, malformed XML, non-2xx status) returns
        ``False`` and is logged at DEBUG: capability detection is
        best-effort and non-fatal.

        :param calendar_url: Calendar URL to probe.
        :type calendar_url: str
        :returns: ``True`` when free-busy-query is advertised.
        :rtype: bool
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:propfind xmlns:D="DAV:">'
            "<D:prop><D:supported-report-set/></D:prop>"
            "</D:propfind>"
        )
        try:
            response: Any = self._dav.propfind(url=calendar_url, props=body, depth=0)
        except Exception as exc:
            # Capability detection is best-effort and non-fatal: any failure
            # (transport, auth, DAV-level) yields False so the dispatcher
            # silently falls through to event-walk for this calendar.
            _LOG.debug(
                "free-busy-query capability PROPFIND failed for %s: %s",
                calendar_url,
                exc,
            )
            return False
        if getattr(response, "status", 0) not in (200, 207):
            _LOG.debug(
                "free-busy-query capability for %s: False (PROPFIND status %s)",
                calendar_url,
                getattr(response, "status", "unknown"),
            )
            return False
        tree: Any = getattr(response, "tree", None)
        capable = False
        if tree is not None:
            # Match any free-busy-query element regardless of wrapper.
            # Both lxml and ElementTree accept fully-qualified tag names.
            for _ in tree.iter("{urn:ietf:params:xml:ns:caldav}free-busy-query"):
                capable = True
                break
        _LOG.debug("free-busy-query capability for %s: %s", calendar_url, capable)
        return capable

    def freebusy_via_report(
        self,
        calendar_url: str,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Issue a CalDAV ``<C:free-busy-query>`` REPORT and return busy intervals.

        The body of the REPORT response is ``text/calendar`` containing
        a single VFREEBUSY component; pure parsing is delegated to
        :func:`calcard_mcp.freebusy.parse_vfreebusy`.

        :param calendar_url: Absolute calendar URL.
        :type calendar_url: str
        :param start: Inclusive UTC range start.
        :type start: datetime.datetime
        :param end: Exclusive UTC range end.
        :type end: datetime.datetime
        :returns: Busy intervals as UTC ``(start, end)`` tuples.
        :rtype: list[tuple[datetime.datetime, datetime.datetime]]
        :raises calcard_mcp.errors.ProtocolError: On non-2xx response,
            on transport failure, or when the response body is not a
            valid VFREEBUSY document.
        :raises caldav.lib.error.AuthorizationError: On 401/403 — propagated
            unchanged so credential failures cannot be silenced.
        """
        start_utc = start.astimezone(UTC)
        end_utc = end.astimezone(UTC)
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<C:free-busy-query xmlns:C="urn:ietf:params:xml:ns:caldav">'
            f'<C:time-range start="{start_utc.strftime("%Y%m%dT%H%M%SZ")}" '
            f'end="{end_utc.strftime("%Y%m%dT%H%M%SZ")}"/>'
            "</C:free-busy-query>"
        )
        try:
            response: Any = self._dav.report(calendar_url, body, 0)
        except AuthorizationError:
            raise
        except DAVError as exc:
            raise ProtocolError(
                f"free-busy-query REPORT for {calendar_url!r} failed: {exc}"
            ) from exc
        except (OSError, *_TRANSPORT_EXCEPTIONS) as exc:
            raise ProtocolError(
                f"free-busy-query REPORT transport error for {calendar_url!r}: {exc}"
            ) from exc
        status = getattr(response, "status", 0)
        if status in (405, 501):
            raise ProtocolError(
                f"server lacks free-busy-query support for {calendar_url!r}: HTTP {status}"
            )
        if status >= 400:
            raise ProtocolError(
                f"free-busy-query REPORT for {calendar_url!r} returned HTTP {status}"
            )
        raw = getattr(response, "raw", "") or ""
        text = raw if isinstance(raw, str) else cast(bytes, raw).decode("utf-8", errors="replace")
        try:
            return parse_vfreebusy(text)
        except ValueError as exc:
            raise ProtocolError(f"malformed VFREEBUSY from {calendar_url!r}: {exc}") from exc

    def list_calendars(self) -> list[CalendarSummary]:
        """List every VEVENT-supporting calendar collection owned by this account.

        Per PRD VTODO §5.5, only collections whose
        ``supported-calendar-component-set`` advertises ``VEVENT`` are
        surfaced. When the property is missing entirely (caldav returns an
        empty list), the collection is included under the legacy assumption:
        VEVENT.

        :returns: Calendar summaries in server-provided order.
        :rtype: list[:class:`CalendarSummary`]
        """
        principal = self._principal()
        summaries: list[CalendarSummary] = []
        for calendar in principal.calendars():
            components = cast(list[str], calendar.get_supported_components())
            if components and "VEVENT" not in components:
                continue
            name = calendar.get_display_name() or str(calendar.url).rstrip("/").rsplit("/", 1)[-1]
            summaries.append(
                CalendarSummary(account_id=self.account.id, name=name, url=str(calendar.url))
            )
        return summaries

    def _calendar(self, url: str) -> Any:
        """Resolve a :class:`caldav.Calendar` by its URL.

        :param url: Absolute calendar URL as returned by :meth:`list_calendars`.
        :type url: str
        :returns: The :class:`caldav.Calendar` object.
        :rtype: typing.Any
        :raises calcard_mcp.errors.ProtocolError: When the calendar cannot be resolved.
        """
        try:
            return self._dav.calendar(url=url)
        except NotFoundError as exc:
            raise ProtocolError(f"calendar not found at {url!r}") from exc

    def _event_to_summary(
        self,
        event: Any,
        calendar_url: str,
        master_anchor_tz_name: str | None = None,
    ) -> EventSummary | None:
        """Project a :class:`caldav.Event` into an :class:`EventSummary`.

        Thin wrapper over :func:`calcard_mcp.ical.parse_vevent_to_summary`
        that supplies the per-account context (id, configured timezone)
        and the resource URL from the caldav object.

        Kept on :class:`CalDAVClient` itself (not a mixin) so it appears in
        ``type(client).__dict__`` — tests grab the unbound original from there
        before instance-patching a parse-counting wrapper.

        :param event: :class:`caldav.Event` with loaded iCal data.
        :type event: typing.Any
        :param calendar_url: URL of the owning calendar.
        :type calendar_url: str
        :param master_anchor_tz_name: Master series' tz applied to this
            override's VALUE=DATE and naive-datetime RECURRENCE-ID values.
            Mirrors :func:`calcard_mcp._ical_parse.extract_recurrence_id`:
            VALUE=DATE RECURRENCE-ID anchors to ``master_anchor_tz_name`` when
            supplied (else the DTSTART-derived anchor); naive-datetime
            RECURRENCE-ID anchors to ``master_anchor_tz_name`` when supplied
            (else stamped UTC); tz-aware RECURRENCE-ID keeps its explicit
            TZID and is never overridden.
        :type master_anchor_tz_name: str | None
        :returns: The projected summary, or :data:`None` when the body fails
            to parse, has no VEVENT, or omits ``DTSTART``.
        :rtype: :class:`EventSummary` | None
        """
        return parse_vevent_to_summary(
            event.data,
            account_id=self.account.id,
            calendar_url=calendar_url,
            resource_url=str(getattr(event, "url", "")),
            fallback_tz=self.account.config.timezone,
            master_anchor_tz_name=master_anchor_tz_name,
        )


class CalendarService:
    """Fan-out service that picks the right :class:`CalDAVClient` per account.

    :cvar registry: Resolved account registry.
    :vartype registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, registry: AccountRegistry, app_config: AppConfig) -> None:
        """Initialise the service with a shared pool of per-account clients.

        :param registry: Resolved account registry.
        :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
        :param app_config: Application configuration; the dispatcher reads
            ``app_config.server.use_freebusy_report`` per call.
        :type app_config: :class:`calcard_mcp.config.AppConfig`
        """
        self.registry: AccountRegistry = registry
        self._app_config: AppConfig = app_config
        self.server: ServerConfig = app_config.server
        self._clients: dict[str, CalDAVClient] = {
            account.id: CalDAVClient(account, app_config.server) for account in registry.all()
        }
        if app_config.server.use_freebusy_report:
            self._warm_freebusy_capabilities()

    def _warm_freebusy_capabilities(self) -> None:
        """Probe every calendar for free-busy-query support, concurrently per account.

        Per PRD 00007 §7.2: capability detection runs at construction
        time, one worker per account. Each worker enumerates the
        account's calendars and primes :attr:`CalDAVClient.freebusy_capable`
        via :meth:`CalDAVClient.is_freebusy_capable`. A failing account
        (network blip, auth glitch) logs a WARNING and is skipped — its
        calendars stay uncached and the dispatcher will retry detection
        lazily on first use, preserving liveness.
        """
        accounts = list(self._clients.items())
        if not accounts:
            return
        with ThreadPoolExecutor(max_workers=len(accounts)) as pool:
            futures = {
                pool.submit(self._warm_account, client): account_id
                for account_id, client in accounts
            }
            for future, account_id in futures.items():
                try:
                    future.result()
                except (ProtocolError, AuthorizationError, DAVError) as exc:
                    _LOG.warning(
                        "free-busy capability warming failed for account %s: %s",
                        account_id,
                        exc,
                    )

    @staticmethod
    def _warm_account(client: CalDAVClient) -> None:
        """Prime ``client.freebusy_capable`` for every calendar of ``client``."""
        for calendar in client.list_calendars():
            client.is_freebusy_capable(calendar.url)

    def client_for(self, name: str | None) -> CalDAVClient:
        """Return the :class:`CalDAVClient` bound to the account matching ``name``.

        :param name: Account id or display name; :data:`None` selects the default.
        :type name: str | None
        :returns: Client for the resolved account.
        :rtype: :class:`CalDAVClient`
        """
        account = self.registry.resolve(name)
        return self._clients[account.id]

    def busy_intervals_for_account(
        self,
        account_name: str | None,
        start: datetime,
        end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Collect UTC ``(start, end)`` busy windows for one account in ``[start, end)``.

        Walks every calendar of the resolved account and gathers the
        ``EventSummary.start`` / ``end`` pairs (already expanded for
        recurring events by :meth:`CalDAVClient.list_events`). The result
        is *not* merged or sorted — :func:`compute_free_slots` does that.

        :param account_name: Account id or display name; :data:`None` selects
            the default account.
        :type account_name: str | None
        :param start: Inclusive query start.
        :type start: datetime.datetime
        :param end: Exclusive query end.
        :type end: datetime.datetime
        :returns: List of ``(start_utc, end_utc)`` tuples, one per event occurrence.
        :rtype: list[tuple[datetime.datetime, datetime.datetime]]
        """
        client = self.client_for(account_name)
        busy: list[tuple[datetime, datetime]] = []
        use_report = self._app_config.server.use_freebusy_report
        for calendar in client.list_calendars():
            if use_report and client.is_freebusy_capable(calendar.url):
                try:
                    busy.extend(client.freebusy_via_report(calendar.url, start, end))
                    continue
                except ProtocolError as exc:
                    _LOG.warning(
                        "free-busy REPORT failed for %s, falling back to event-walk: %s",
                        calendar.url,
                        exc,
                    )
            for event in client.list_events(calendar.url, start, end):
                if event.transparency == "transparent":
                    continue
                busy.append((event.start.astimezone(UTC), event.end.astimezone(UTC)))
        return busy

    def find_free_time(
        self,
        *,
        account_names: list[str] | None,
        start: datetime,
        end: datetime,
        duration_minutes: int,
        working_hours: tuple[int, int] | None = None,
        timezone: str | None = None,
    ) -> list[FreeSlot]:
        """Find windows where every listed account is free for ``duration_minutes``.

        Gathers busy intervals from each account via
        :meth:`busy_intervals_for_account` and feeds them through the pure
        :func:`compute_free_slots` helper.

        :param account_names: Accounts to query; :data:`None` means every configured account.
        :type account_names: list[str] | None
        :param start: Earliest acceptable slot start (inclusive).
        :type start: datetime.datetime
        :param end: Latest acceptable slot end (exclusive).
        :type end: datetime.datetime
        :param duration_minutes: Minimum required slot length in minutes.
        :type duration_minutes: int
        :param working_hours: Optional ``(start_hour, end_hour)`` window,
            e.g. ``(8, 20)``, evaluated in ``timezone``.
        :type working_hours: tuple[int, int] | None
        :param timezone: IANA name (``"Europe/Bratislava"``). When :data:`None`,
            working-hour bounds are evaluated in the server's system local
            timezone — the zero-config path for a family-scale deployment
            where server time matches family time.
        :type timezone: str | None
        :returns: List of free slots ordered by start time.
        :rtype: list[:class:`FreeSlot`]
        :raises zoneinfo.ZoneInfoNotFoundError: When ``timezone`` is provided
            but does not name a known IANA zone.
        """
        zone = resolve_zone(timezone)
        accounts = self.registry.resolve_many(account_names)
        busy: list[tuple[datetime, datetime]] = []
        for account in accounts:
            busy.extend(self.busy_intervals_for_account(account.id, start, end))
        return compute_free_slots(
            busy,
            start=start,
            end=end,
            duration_minutes=duration_minutes,
            working_hours=working_hours,
            zone=zone,
        )

    def close(self) -> None:
        """Close every per-account :class:`CalDAVClient`'s HTTP connection pool.

        Mirrors :meth:`calcard_mcp.caltodo_client.TodoService.close` and
        :meth:`calcard_mcp.carddav_client.ContactService.close`. Long-running
        process owners (the MCP server) call this on shutdown; integration
        tests call it in ``finally:`` blocks to release the underlying
        connection pools deterministically.

        :returns: None.
        :rtype: None
        """
        for client in self._clients.values():
            client.close()

    def __enter__(self) -> CalendarService:
        """Return ``self`` so :class:`CalendarService` can be used as a context manager.

        :returns: This instance.
        :rtype: :class:`CalendarService`
        """
        return self

    def __exit__(self, *_exc_info: object) -> None:
        """Close every owned client on context exit.

        :param _exc_info: Standard ``__exit__`` signature, unused.
        :type _exc_info: object
        :returns: None.
        :rtype: None
        """
        self.close()
