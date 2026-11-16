"""Multi-account CalDAV VTODO client built on the :mod:`caldav` library.

Pure VTODO byte-pushing lives in :mod:`calcard_mcp.vtodo`; this module owns
transport, write-verification flow, and the supported-component filter that
keeps task tooling pointed at calendars whose server confirms VTODO support.

Imports:

* :mod:`logging` for diagnostics on stderr.
* :mod:`uuid` to mint fresh VTODO UIDs on creation.
* :class:`caldav.DAVClient` from the ``caldav`` package for protocol access.
* :class:`caldav.lib.error.NotFoundError` for boundary-wrapping into
  :class:`calcard_mcp.errors.ProtocolError`.
* :mod:`icalendar` for in-place mutation of VTODO components during update.
* :class:`calcard_mcp.accounts.ResolvedAccount` and
  :class:`calcard_mcp.accounts.AccountRegistry` for credential lookup.
* :class:`calcard_mcp.config.ServerConfig` for shared HTTP settings.
* :class:`calcard_mcp.dav_client.DAVClientBase` as the per-account base.
* :class:`calcard_mcp.errors.ProtocolError` to signal unexpected server responses.
* :mod:`calcard_mcp.vtodo` for pure VTODO (de)serialisation helpers.
* :func:`calcard_mcp.verifier.verify_fields` and
  :func:`calcard_mcp.verifier.verify_etag` for read-after-write checks.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from caldav.davclient import DAVClient
from caldav.lib.error import NotFoundError
from icalendar import Calendar as ICalCalendar

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
from calcard_mcp.accounts import AccountRegistry, ResolvedAccount
from calcard_mcp.config import ServerConfig
from calcard_mcp.dav_client import DAVClientBase
from calcard_mcp.errors import ProtocolError
from calcard_mcp.ical import Alarm, Attendee, Person, RecurrenceRule, make_aware
from calcard_mcp.verifier import (
    coerce_expected,
    verify_etag,
    verify_fields,
    verify_summary_fields,
)
from calcard_mcp.vtodo import (
    TaskSummary,
    apply_todo_clears,
    build_vtodo,
    parse_vtodo,
    replace_fields,
)

__all__ = [
    "CalTodoClient",
    "TaskListSummary",
    "TaskSummary",
    "TodoService",
]

_LOG = logging.getLogger(__name__)


class _ClearSentinel:
    """Marker requesting that ``COMPLETED`` be cleared from the saved VTODO."""


_CLEAR_COMPLETED = _ClearSentinel()


def _apply_status_auto_fields(
    prior_status: str | None,
    *,
    status: str | None,
    completed: datetime | None,
    percent_complete: int | None,
) -> tuple[datetime | _ClearSentinel | None, int | None]:
    """Resolve ``COMPLETED`` / ``PERCENT-COMPLETE`` per PRD §5.4 transition rules.

    Returns ``(effective_completed, effective_percent_complete)``. The two
    auto-managed fields are decided independently — explicit caller values
    always win for their own field, and the auto-fill still applies to the
    other field.

    * Transition INTO ``completed`` (``status="completed"`` and prior status
      was anything else, including :data:`None` on create):

        * ``completed`` defaults to ``datetime.now(UTC)`` when caller passes
          :data:`None`.
        * ``percent_complete`` defaults to ``100`` when caller passes
          :data:`None`.

    * Transition AWAY FROM ``completed`` (``status`` is set to a non-completed
      value and prior status was ``"completed"``):

        * ``completed`` becomes :data:`_CLEAR_COMPLETED` when caller passes
          :data:`None` (callers route this into ``clear_fields=["completed"]``).
        * ``percent_complete`` defaults to ``0`` when caller passes :data:`None`.

    * No transition (status unchanged, status omitted, or status equals prior
      status): caller-supplied values pass through unchanged.

    :param prior_status: Server-stored status before this call, or :data:`None`
        for ``create_task``.
    :type prior_status: str | None
    :param status: Status this call is setting; :data:`None` means "unchanged".
    :type status: str | None
    :param completed: Caller-supplied ``COMPLETED``, if any.
    :type completed: datetime.datetime | None
    :param percent_complete: Caller-supplied ``PERCENT-COMPLETE``, if any.
    :type percent_complete: int | None
    :returns: Effective ``(completed, percent_complete)`` after applying the
        auto-completion semantics.
    :rtype: tuple[datetime.datetime | :class:`_ClearSentinel` | None, int | None]
    """
    transition_into = status == "completed" and prior_status != "completed"
    transition_away = status is not None and status != "completed" and prior_status == "completed"
    effective_completed: datetime | _ClearSentinel | None = completed
    effective_percent: int | None = percent_complete
    if transition_into:
        if completed is None:
            effective_completed = datetime.now(UTC)
        if percent_complete is None:
            effective_percent = 100
    elif transition_away:
        if completed is None:
            effective_completed = _CLEAR_COMPLETED
        if percent_complete is None:
            effective_percent = 0
    return effective_completed, effective_percent


def _touched_typed_fields_todo(
    *,
    categories: list[str] | None,
    classification: str,
    url: str,
    geo: GeoCoordinates | None,
    resources: list[str] | None,
    comments: list[str] | None,
    contacts: list[str] | None,
    related_to: list[str] | None,
    organizer: Person | None,
    attendees: list[Attendee] | None,
    alarms: list[Alarm] | None,
    attachments: list[BinaryReference] | None,
    recurrence: RecurrenceRule | None,
    exdates: list[datetime] | None,
    rdates: list[datetime] | None,
    recurrence_id: datetime | None,
) -> list[str]:
    """Return the names of typed VTODO fields the caller actually supplied.

    Mirror of :func:`calcard_mcp._caldav_base._touched_typed_fields` minus
    ``transparency`` (VTODO has no ``TRANSP`` property). A list-typed kwarg
    is "touched" whenever it is not :data:`None` (an empty list still touches:
    it asks the writer to clear emission). String-typed kwargs
    (``classification``, ``url``) are touched when non-empty. Dataclass-shaped
    kwargs (``geo``, ``organizer``, ``recurrence``) and scalar
    ``recurrence_id`` are touched only when not :data:`None`.

    The returned list drives which :class:`TaskSummary` fields the verifier
    diffs after the write.
    """
    touched: list[str] = []
    if categories is not None:
        touched.append("categories")
    if classification:
        touched.append("classification")
    if url:
        touched.append("url")
    if geo is not None:
        touched.append("geo")
    if resources is not None:
        touched.append("resources")
    if comments is not None:
        touched.append("comments")
    if contacts is not None:
        touched.append("contacts")
    if related_to is not None:
        touched.append("related_to")
    if organizer is not None:
        touched.append("organizer")
    if attendees is not None:
        touched.append("attendees")
    if alarms is not None:
        touched.append("alarms")
    if attachments is not None:
        touched.append("attachments")
    if recurrence is not None:
        touched.append("recurrence")
    if exdates is not None:
        touched.append("exdates")
    if rdates is not None:
        touched.append("rdates")
    if recurrence_id is not None:
        touched.append("recurrence_id")
    return touched


@dataclass(frozen=True, slots=True)
class TaskListSummary:
    """Lightweight description of a calendar collection that supports VTODO.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar name: Human-readable task list name (``displayname`` property).
    :vartype name: str
    :cvar url: Absolute URL of the task list collection.
    :vartype url: str
    """

    account_id: str
    name: str
    url: str


class CalTodoClient(DAVClientBase):
    """Per-account CalDAV client for VTODO operations with verified writes.

    :cvar account: Resolved account this client operates as.
    :vartype account: :class:`calcard_mcp.accounts.ResolvedAccount`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, account: ResolvedAccount, server: ServerConfig) -> None:
        """Build a CalTodo client for a single account.

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
        self._closed: bool = False

    def close(self) -> None:
        """Close the underlying ``caldav`` HTTP session if exposed.

        ``caldav`` 1.x exposes the underlying :class:`requests.Session` as a
        ``session`` attribute; closing it releases pooled connections. The
        attribute is best-effort because the path may shift across library
        versions, so any failure during teardown is logged at debug level
        and otherwise ignored — a teardown that raises would mask the real
        error from the caller.

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

        :returns: ``True`` once :meth:`close` has been called (or the
            owning :class:`TodoService` was used as a context manager
            that exited), ``False`` otherwise.
        :rtype: bool
        """
        return self._closed

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

    def _calendar(self, url: str) -> Any:
        """Resolve a :class:`caldav.Calendar` by its URL.

        :param url: Absolute calendar URL.
        :type url: str
        :returns: The :class:`caldav.Calendar` object.
        :rtype: typing.Any
        :raises calcard_mcp.errors.ProtocolError: When the calendar cannot be resolved.
        """
        try:
            return self._dav.calendar(url=url)
        except NotFoundError as exc:
            raise ProtocolError(f"calendar not found at {url!r}") from exc

    def list_task_lists(self) -> list[TaskListSummary]:
        """List every calendar that advertises VTODO support for this account.

        Per PRD VTODO §1, only calendars whose
        ``supported-calendar-component-set`` advertises ``VTODO`` are
        surfaced. caldav's :meth:`Calendar.get_supported_components` returns
        an empty list when the server omits the property entirely; such
        calendars are excluded — the task tooling refuses to act on
        unconfirmed servers.

        :returns: Task list summaries in server-provided order.
        :rtype: list[:class:`TaskListSummary`]
        """
        principal = self._principal()
        summaries: list[TaskListSummary] = []
        for calendar in principal.calendars():
            components = cast(list[str], calendar.get_supported_components())
            if "VTODO" not in components:
                continue
            name = calendar.get_display_name() or str(calendar.url).rstrip("/").rsplit("/", 1)[-1]
            summaries.append(
                TaskListSummary(account_id=self.account.id, name=name, url=str(calendar.url))
            )
        return summaries

    def list_tasks(self, task_list_url: str) -> list[TaskSummary]:
        """List every VTODO in ``task_list_url`` projected through :func:`parse_vtodo`.

        :param task_list_url: Absolute task list URL.
        :type task_list_url: str
        :returns: Task summaries in server-provided order.
        :rtype: list[:class:`TaskSummary`]
        """
        calendar = self._calendar(task_list_url)
        raw_todos = cast(list[Any], calendar.todos(include_completed=True))
        summaries: list[TaskSummary] = []
        for todo in raw_todos:
            parsed = parse_vtodo(
                todo.data,
                account_id=self.account.id,
                task_list_url=task_list_url,
                resource_url=str(getattr(todo, "url", "")),
                fallback_tz=self.account.config.timezone,
            )
            if parsed is None:
                continue
            summaries.append(parsed)
        return summaries

    def search_tasks(self, query: str) -> list[TaskSummary]:
        """Search every task list on this account for tasks matching ``query``.

        Case-insensitive substring match against ``SUMMARY`` and
        ``DESCRIPTION``; deduplicated by UID so a task that exists in two
        lists surfaces once.

        :param query: Substring to search for.
        :type query: str
        :returns: Matching task summaries.
        :rtype: list[:class:`TaskSummary`]
        """
        needle = query.strip().casefold()
        seen: set[str] = set()
        results: list[TaskSummary] = []
        for task_list in self.list_task_lists():
            for task in self.list_tasks(task_list.url):
                haystack = " ".join([task.summary, task.description]).casefold()
                if needle not in haystack:
                    continue
                if task.uid in seen:
                    continue
                seen.add(task.uid)
                results.append(task)
        return results

    def create_task(
        self,
        *,
        task_list_url: str,
        summary: str,
        description: str | None = None,
        due: datetime | None = None,
        status: str = "needs-action",
        priority: int = 0,
        percent_complete: int | None = None,
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
    ) -> TaskSummary:
        """Create a VTODO in ``task_list_url`` and verify the server stored it.

        Per PRD §5.4, calling ``create_task`` with ``status="completed"``
        without an explicit ``percent_complete`` auto-fills ``COMPLETED`` to
        ``datetime.now(UTC)`` and ``PERCENT-COMPLETE`` to ``100``.

        :param task_list_url: Target task list URL.
        :type task_list_url: str
        :param summary: VTODO ``SUMMARY`` property.
        :type summary: str
        :param description: Optional ``DESCRIPTION`` property.
        :type description: str | None
        :param due: Optional ``DUE`` (timezone-aware or made-aware via account tz).
        :type due: datetime.datetime | None
        :param status: Lower-case task status.
        :type status: str
        :param priority: Task priority in ``0..=9``.
        :type priority: int
        :param percent_complete: Completion percentage in ``0..=100``. When
            :data:`None`, defaults to ``0`` unless ``status="completed"``
            triggers auto-completion (in which case ``100`` is used).
        :type percent_complete: int | None
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
        :returns: Summary of the freshly created task.
        :rtype: :class:`TaskSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When verification fails.
        :raises calcard_mcp.errors.ProtocolError: When the server refuses the write.
        """
        effective_completed, effective_percent = _apply_status_auto_fields(
            prior_status=None,
            status=status,
            completed=None,
            percent_complete=percent_complete,
        )
        # _CLEAR_COMPLETED is unreachable when prior_status is None — the
        # transition-away branch requires prior_status == "completed".
        completed_to_save: datetime | None = (
            effective_completed if isinstance(effective_completed, datetime) else None
        )
        final_percent = effective_percent if effective_percent is not None else 0

        calendar = self._calendar(task_list_url)
        uid = f"{uuid.uuid4()}@calcard-mcp"
        tz = self.account.config.timezone
        due_aware = make_aware(due, tz) if due is not None else None
        ical = build_vtodo(
            uid=uid,
            summary=summary,
            description=description,
            due=due_aware,
            status=status,
            priority=priority,
            percent_complete=final_percent,
            completed=completed_to_save,
            categories=categories,
            classification=classification,
            url=url,
            geo=geo,
            resources=resources,
            comments=comments,
            contacts=contacts,
            related_to=related_to,
            organizer=organizer,
            attendees=attendees,
            alarms=alarms,
            attachments=attachments,
            recurrence=recurrence,
            exdates=exdates,
            rdates=rdates,
            recurrence_id=recurrence_id,
        )
        try:
            created = calendar.save_todo(ical)
        except Exception as exc:
            raise ProtocolError(f"create_task failed for {self.account.id!r}: {exc}") from exc

        touched_typed_fields = _touched_typed_fields_todo(
            categories=categories,
            classification=classification,
            url=url,
            geo=geo,
            resources=resources,
            comments=comments,
            contacts=contacts,
            related_to=related_to,
            organizer=organizer,
            attendees=attendees,
            alarms=alarms,
            attachments=attachments,
            recurrence=recurrence,
            exdates=exdates,
            rdates=rdates,
            recurrence_id=recurrence_id,
        )

        if self.server.verify_writes:
            self._verify_task(
                created,
                summary=summary,
                description=description,
                status=status,
                priority=priority,
                percent_complete=final_percent,
                completed=completed_to_save,
            )
            if touched_typed_fields:
                self._verify_typed_fields(
                    intended_ical=ical,
                    actual=created,
                    task_list_url=task_list_url,
                    fields=touched_typed_fields,
                )
            self._verify_etag_with_fallback(created, pre_etag=None)

        stored = parse_vtodo(
            created.data,
            account_id=self.account.id,
            task_list_url=task_list_url,
            resource_url=str(getattr(created, "url", "")),
            fallback_tz=tz,
        )
        if stored is None:
            raise ProtocolError("server returned a VTODO that could not be parsed")
        return stored

    def update_task(
        self,
        *,
        task_list_url: str,
        uid: str,
        summary: str | None = None,
        description: str | None = None,
        due: datetime | None = None,
        status: str | None = None,
        priority: int | None = None,
        percent_complete: int | None = None,
        completed: datetime | None = None,
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
        clear_fields: list[str] | None = None,
    ) -> TaskSummary:
        """Update fields on an existing VTODO and verify the change round-tripped.

        Per PRD §5.4, transitioning ``status`` into ``"completed"`` auto-fills
        ``COMPLETED`` (current UTC) and ``PERCENT-COMPLETE=100`` when neither
        is supplied explicitly. Transitioning out of ``"completed"`` clears
        ``COMPLETED`` and resets ``PERCENT-COMPLETE`` to ``0`` under the same
        condition. Caller-supplied values always win over the auto-fill.

        :param task_list_url: Task list URL that holds the task.
        :type task_list_url: str
        :param uid: VTODO ``UID`` of the task to modify.
        :type uid: str
        :param summary: New ``SUMMARY`` or :data:`None` to leave unchanged.
        :type summary: str | None
        :param description: New ``DESCRIPTION`` or :data:`None` to leave unchanged.
        :type description: str | None
        :param due: New ``DUE`` or :data:`None` to leave unchanged.
        :type due: datetime.datetime | None
        :param status: New ``STATUS`` or :data:`None` to leave unchanged.
        :type status: str | None
        :param priority: New ``PRIORITY`` or :data:`None` to leave unchanged.
        :type priority: int | None
        :param percent_complete: New ``PERCENT-COMPLETE`` or :data:`None`.
        :type percent_complete: int | None
        :param completed: New ``COMPLETED`` (timezone-aware) or :data:`None` to
            leave the auto-completion logic in charge.
        :type completed: datetime.datetime | None
        :param categories: New ``CATEGORIES`` (empty list emits no line) or
            :data:`None` to leave unchanged.
        :type categories: list[str] | None
        :param classification: New ``CLASS`` (empty string leaves unchanged).
        :type classification: str
        :param url: New ``URL`` (empty string leaves unchanged).
        :type url: str
        :param geo: New ``GEO`` or :data:`None` to leave unchanged.
        :type geo: GeoCoordinates | None
        :param resources: New ``RESOURCES`` (empty list emits no line) or
            :data:`None` to leave unchanged.
        :type resources: list[str] | None
        :param comments: New ``COMMENT`` values (empty list emits no lines) or
            :data:`None` to leave unchanged.
        :type comments: list[str] | None
        :param contacts: New ``CONTACT`` values (empty list emits no lines) or
            :data:`None` to leave unchanged.
        :type contacts: list[str] | None
        :param related_to: New ``RELATED-TO`` values (empty list emits no lines)
            or :data:`None` to leave unchanged.
        :type related_to: list[str] | None
        :param organizer: New ``ORGANIZER`` or :data:`None` to leave unchanged.
        :type organizer: Person | None
        :param attendees: New ``ATTENDEE`` list (empty list emits no lines) or
            :data:`None` to leave unchanged.
        :type attendees: list[Attendee] | None
        :param alarms: New ``VALARM`` sub-components (empty list emits no
            blocks) or :data:`None` to leave unchanged.
        :type alarms: list[Alarm] | None
        :param attachments: New ``ATTACH`` values (empty list emits no lines)
            or :data:`None` to leave unchanged.
        :type attachments: list[BinaryReference] | None
        :param recurrence: New ``RRULE`` or :data:`None` to leave unchanged.
        :type recurrence: RecurrenceRule | None
        :param exdates: New ``EXDATE`` values (empty list emits no lines) or
            :data:`None` to leave unchanged.
        :type exdates: list[datetime.datetime] | None
        :param rdates: New ``RDATE`` values (empty list emits no lines) or
            :data:`None` to leave unchanged.
        :type rdates: list[datetime.datetime] | None
        :param recurrence_id: New ``RECURRENCE-ID`` or :data:`None` to leave
            unchanged.
        :type recurrence_id: datetime.datetime | None
        :param clear_fields: Optional list of lowercase field names to remove
            from the task. Valid entries: ``"alarms"``, ``"attachments"``,
            ``"attendees"``, ``"categories"``, ``"classification"``,
            ``"comments"``, ``"completed"``, ``"contacts"``, ``"description"``,
            ``"due"``, ``"exdates"``, ``"geo"``, ``"organizer"``, ``"rdates"``,
            ``"recurrence"``, ``"recurrence_id"``, ``"related_to"``,
            ``"resources"``, ``"url"``. ``"summary"``, ``"status"``,
            ``"priority"``, ``"percent_complete"`` are required fields and
            cannot be cleared. Clearing wins over any matching positive
            argument in the same call.
        :type clear_fields: list[str] | None
        :returns: Summary of the updated task.
        :rtype: :class:`TaskSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When verification fails.
        :raises calcard_mcp.errors.ProtocolError: When the task cannot be found or updated.
        """
        calendar = self._calendar(task_list_url)
        todo = self._fetch_by_uid(calendar, uid)
        pre_etag = getattr(todo, "etag", None)

        try:
            calendar_data: Any = ICalCalendar.from_ical(todo.data)
        except Exception as exc:
            raise ProtocolError(
                f"server returned an iCalendar body for {uid!r} that icalendar could not parse"
            ) from exc
        vtodo: Any = None
        for component in cast(list[Any], calendar_data.walk("VTODO")):
            vtodo = component
            break
        if vtodo is None:
            raise ProtocolError(f"task {uid!r} contains no VTODO component")

        prior_status_raw = vtodo.get("STATUS")
        prior_status: str | None = (
            str(prior_status_raw).lower() if prior_status_raw is not None else None
        )
        effective_completed, effective_percent = _apply_status_auto_fields(
            prior_status,
            status=status,
            completed=completed,
            percent_complete=percent_complete,
        )
        if isinstance(effective_completed, _ClearSentinel):
            completed_to_save: datetime | None = None
            merged_clear: list[str] = list(clear_fields or [])
            if not any(name.lower() == "completed" for name in merged_clear):
                merged_clear.append("completed")
            effective_clear_fields: list[str] | None = merged_clear
        else:
            completed_to_save = effective_completed
            effective_clear_fields = clear_fields

        tz = self.account.config.timezone
        due_aware = make_aware(due, tz) if due is not None else None
        # PRD 00001 §1.6: clears must win over any also-provided positive value.
        # Pass ``clear_fields=None`` to ``replace_fields`` and apply clears
        # ourselves at the end, after the new typed-field emission below.
        replace_fields(
            vtodo,
            summary=summary,
            description=description,
            due=due_aware,
            status=status,
            priority=priority,
            percent_complete=effective_percent,
            completed=completed_to_save,
            clear_fields=None,
        )

        # New typed properties: pop the existing line(s), then re-emit using
        # the shared helpers. ``None`` leaves the property untouched; an empty
        # list / empty string clears emission (matching ``build_vtodo``).
        if categories is not None:
            vtodo.pop("CATEGORIES", None)
            emit_categories(vtodo, categories)
        if classification:
            vtodo.pop("CLASS", None)
            emit_classification(vtodo, classification)
        if url:
            vtodo.pop("URL", None)
            emit_url(vtodo, url)
        if geo is not None:
            vtodo.pop("GEO", None)
            emit_geo(vtodo, geo)
        if resources is not None:
            vtodo.pop("RESOURCES", None)
            emit_resources(vtodo, resources)
        if comments is not None:
            vtodo.pop("COMMENT", None)
            emit_text_properties(vtodo, "comment", comments)
        if contacts is not None:
            vtodo.pop("CONTACT", None)
            emit_text_properties(vtodo, "contact", contacts)
        if related_to is not None:
            vtodo.pop("RELATED-TO", None)
            emit_text_properties(vtodo, "related-to", related_to)
        if organizer is not None:
            vtodo.pop("ORGANIZER", None)
            emit_person(vtodo, "organizer", organizer)
        if attendees is not None:
            vtodo.pop("ATTENDEE", None)
            for attendee in attendees:
                emit_attendee(vtodo, attendee)
        if attachments is not None:
            vtodo.pop("ATTACH", None)
            for attachment in attachments:
                emit_attach(vtodo, attachment)
        if recurrence is not None:
            vtodo.pop("RRULE", None)
            emit_rrule(vtodo, recurrence)
        if exdates is not None:
            vtodo.pop("EXDATE", None)
            for exdate in exdates:
                vtodo.add("exdate", as_utc_datetime(exdate))
        if rdates is not None:
            vtodo.pop("RDATE", None)
            for rdate in rdates:
                vtodo.add("rdate", as_utc_datetime(rdate))
        if recurrence_id is not None:
            vtodo.pop("RECURRENCE-ID", None)
            vtodo.add("recurrence-id", as_utc_datetime(recurrence_id))
        if alarms is not None:
            vtodo.subcomponents = [child for child in vtodo.subcomponents if child.name != "VALARM"]
            for alarm in alarms:
                emit_alarm(vtodo, alarm)

        if effective_clear_fields:
            apply_todo_clears(vtodo, effective_clear_fields)

        intended_ical = calendar_data.to_ical().decode("utf-8")
        todo.data = intended_ical
        try:
            todo.save()
        except Exception as exc:
            raise ProtocolError(f"update_task failed for {uid!r}: {exc}") from exc

        if self.server.verify_writes:
            cleared = {name.lower() for name in (effective_clear_fields or ())}
            self._verify_task(
                todo,
                summary=summary,
                # Do not verify a field we just cleared — the server legitimately
                # stores it as empty/missing.
                description=None if "description" in cleared else description,
                status=status,
                priority=priority,
                percent_complete=effective_percent,
                # When COMPLETED was cleared (auto-clear via status transition
                # or explicit clear_fields=["completed"]), the property is
                # absent from the body — skip field verification for it.
                # Otherwise verify the datetime that was actually written.
                completed=None if "completed" in cleared else completed_to_save,
            )
            touched_typed_fields = _touched_typed_fields_todo(
                categories=categories,
                classification=classification,
                url=url,
                geo=geo,
                resources=resources,
                comments=comments,
                contacts=contacts,
                related_to=related_to,
                organizer=organizer,
                attendees=attendees,
                alarms=alarms,
                attachments=attachments,
                recurrence=recurrence,
                exdates=exdates,
                rdates=rdates,
                recurrence_id=recurrence_id,
            )
            # A field that was both touched and cleared resolves to "cleared":
            # the server legitimately stores it as empty/missing, and the
            # parsed read-back will reflect the default (empty list / None).
            touched_typed_fields = [name for name in touched_typed_fields if name not in cleared]
            if touched_typed_fields:
                self._verify_typed_fields(
                    intended_ical=intended_ical,
                    actual=todo,
                    task_list_url=task_list_url,
                    fields=touched_typed_fields,
                )
            self._verify_etag_with_fallback(todo, pre_etag=pre_etag)

        stored = parse_vtodo(
            todo.data,
            account_id=self.account.id,
            task_list_url=task_list_url,
            resource_url=str(getattr(todo, "url", "")),
            fallback_tz=tz,
        )
        if stored is None:
            raise ProtocolError("server returned a VTODO that could not be parsed")
        return stored

    def delete_task(self, *, task_list_url: str, uid: str) -> None:
        """Delete the VTODO with ``uid`` from ``task_list_url`` and verify absence.

        :param task_list_url: Task list URL that holds the task.
        :type task_list_url: str
        :param uid: VTODO ``UID`` of the task to remove.
        :type uid: str
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.ProtocolError: When the initial delete fails or
            the task is still reachable after delete.
        """
        calendar = self._calendar(task_list_url)
        todo = self._fetch_by_uid(calendar, uid)
        try:
            todo.delete()
        except Exception as exc:
            raise ProtocolError(f"delete_task failed for {uid!r}: {exc}") from exc

        if self.server.verify_writes:
            try:
                calendar.todo_by_uid(uid)
            except NotFoundError:
                return
            raise ProtocolError(
                f"task {uid!r} still present after delete on account {self.account.id!r}"
            )

    def _fetch_by_uid(self, calendar: Any, uid: str) -> Any:
        """Return the :class:`caldav.Todo` with ``uid`` in ``calendar``.

        :param calendar: :class:`caldav.Calendar` to search.
        :type calendar: typing.Any
        :param uid: VTODO ``UID``.
        :type uid: str
        :returns: The matching :class:`caldav.Todo`.
        :rtype: typing.Any
        :raises calcard_mcp.errors.ProtocolError: When no task has the requested UID.
        """
        try:
            return calendar.todo_by_uid(uid)
        except NotFoundError as exc:
            raise ProtocolError(f"task {uid!r} not found in calendar {calendar.url!r}") from exc

    def _verify_etag_with_fallback(self, todo: Any, *, pre_etag: str | None) -> None:
        """Run ETag verification, tolerating servers that omit the post-PUT ETag.

        ``_verify_task`` has already called ``todo.load()``, so ``todo.etag``
        reflects a follow-up GET. If the server still exposes no ETag, log
        a warning and rely on field-level verification rather than failing
        the write.

        :param todo: The task object just verified by :meth:`_verify_task`.
        :type todo: typing.Any
        :param pre_etag: ETag read before the write (``None`` for creates).
        :type pre_etag: str | None
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.WriteVerificationError: When a non-empty
            post-write ETag is present but equals ``pre_etag``.
        """
        post_etag = getattr(todo, "etag", None)
        if not post_etag:
            _LOG.warning(
                "server returned no ETag for %s; relying on field-level verification",
                self.account.id,
            )
            return
        verify_etag(pre_etag=pre_etag, post_etag=post_etag)

    def _verify_task(
        self,
        todo: Any,
        *,
        summary: str | None,
        description: str | None,
        status: str | None,
        priority: int | None,
        percent_complete: int | None,
        completed: datetime | None,
    ) -> None:
        """Re-read ``todo`` and assert the intended properties are persisted.

        DUE is intentionally not field-verified here: its serialised form
        (``20260601T120000Z`` vs ``20260601T120000`` with TZID parameter)
        depends on server timezone conventions, and the ETag check already
        catches silent body tampering.

        STATUS is uppercased before comparison: RFC 5545 mandates uppercase
        STATUS values (``COMPLETED``, ``NEEDS-ACTION``, ...) on the wire, and
        :func:`calcard_mcp.vtodo.build_vtodo` writes them that way. vobject
        parses property values verbatim, so a spec-compliant server returns
        the uppercase form regardless of what the client wrote.

        :param todo: :class:`caldav.Todo` just written by the server.
        :type todo: typing.Any
        :param summary: Intended ``SUMMARY`` value or :data:`None` to skip.
        :type summary: str | None
        :param description: Intended ``DESCRIPTION`` value or :data:`None` to skip.
        :type description: str | None
        :param status: Intended ``STATUS`` value (lowercase project form) or
            :data:`None` to skip; uppercased internally before comparison.
        :type status: str | None
        :param priority: Intended ``PRIORITY`` value or :data:`None` to skip.
        :type priority: int | None
        :param percent_complete: Intended ``PERCENT-COMPLETE`` value or :data:`None`.
        :type percent_complete: int | None
        :param completed: Intended ``COMPLETED`` (timezone-aware) or :data:`None`
            to skip — pass :data:`None` when ``COMPLETED`` was cleared from the
            body, since a missing property must not be field-verified.
        :type completed: datetime.datetime | None
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.WriteVerificationError: On any field mismatch.
        """
        try:
            todo.load()
        except Exception as exc:
            raise ProtocolError(f"could not re-read task after write: {exc}") from exc
        expected = coerce_expected(
            [
                ("SUMMARY", summary),
                ("DESCRIPTION", description),
                ("STATUS", status.upper() if status is not None else None),
                ("PRIORITY", str(priority) if priority is not None else None),
                (
                    "PERCENT-COMPLETE",
                    str(percent_complete) if percent_complete is not None else None,
                ),
                # icalendar serialises COMPLETED at second precision, so vobject
                # parses the round-tripped value with microsecond=0. Normalise
                # the intended value the same way before stringifying or the
                # comparison would fail on auto-filled timestamps that carry
                # ``datetime.now(UTC)``'s microseconds.
                (
                    "COMPLETED",
                    str(completed.replace(microsecond=0)) if completed is not None else None,
                ),
            ]
        )
        if expected:
            verify_fields(todo.data, component="VTODO", expected=expected)

    def _verify_typed_fields(
        self,
        *,
        intended_ical: str,
        actual: Any,
        task_list_url: str,
        fields: list[str],
    ) -> None:
        """Diff the typed VTODO properties the caller touched, post-write.

        Parses the iCal we sent (``intended_ical``) and the server's read-back
        (``actual.data``, refreshed by :meth:`_verify_task`) into
        :class:`TaskSummary` instances and runs them through
        :func:`calcard_mcp.verifier.verify_summary_fields`. Only the listed
        ``fields`` are diffed.

        :param intended_ical: The iCalendar text the client wrote to the server.
        :type intended_ical: str
        :param actual: :class:`caldav.Todo` whose ``data`` attribute holds the
            server's post-write read-back (already refreshed by
            :meth:`_verify_task`).
        :type actual: typing.Any
        :param task_list_url: URL of the owning task list (passed to the parser).
        :type task_list_url: str
        :param fields: Typed field names to diff (e.g. ``"categories"``,
            ``"organizer"``, ``"recurrence"``).
        :type fields: list[str]
        :raises calcard_mcp.errors.WriteVerificationError: When any listed
            field differs between intended and actual.
        :raises calcard_mcp.errors.ProtocolError: When either side fails to
            parse into a usable :class:`TaskSummary`.
        """
        resource_url = str(getattr(actual, "url", ""))
        fallback_tz = self.account.config.timezone
        intended_summary = parse_vtodo(
            intended_ical,
            account_id=self.account.id,
            task_list_url=task_list_url,
            resource_url=resource_url,
            fallback_tz=fallback_tz,
        )
        if intended_summary is None:
            raise ProtocolError(
                "could not project intended VTODO into a TaskSummary for verification"
            )
        actual_summary = parse_vtodo(
            actual.data,
            account_id=self.account.id,
            task_list_url=task_list_url,
            resource_url=resource_url,
            fallback_tz=fallback_tz,
        )
        if actual_summary is None:
            raise ProtocolError("could not project server VTODO response into a TaskSummary")
        verify_summary_fields(intended_summary, actual_summary, fields=fields)


class TodoService:
    """Fan-out service that picks the right :class:`CalTodoClient` per account.

    :cvar registry: Resolved account registry.
    :vartype registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, registry: AccountRegistry, server: ServerConfig) -> None:
        """Initialise the service with a shared pool of per-account clients.

        :param registry: Resolved account registry.
        :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
        :param server: Shared server configuration.
        :type server: :class:`calcard_mcp.config.ServerConfig`
        """
        self.registry: AccountRegistry = registry
        self.server: ServerConfig = server
        self._clients: dict[str, CalTodoClient] = {
            account.id: CalTodoClient(account, server) for account in registry.all()
        }

    def client_for(self, name: str | None) -> CalTodoClient:
        """Return the :class:`CalTodoClient` bound to the account matching ``name``.

        :param name: Account id or display name; :data:`None` selects the default.
        :type name: str | None
        :returns: Client for the resolved account.
        :rtype: :class:`CalTodoClient`
        """
        account = self.registry.resolve(name)
        return self._clients[account.id]

    def close(self) -> None:
        """Close every per-account :class:`CalTodoClient`'s HTTP connection pool.

        :returns: None.
        :rtype: None
        """
        for client in self._clients.values():
            client.close()

    def __enter__(self) -> TodoService:
        """Return ``self`` so :class:`TodoService` can be used as a context manager.

        :returns: This instance.
        :rtype: :class:`TodoService`
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
