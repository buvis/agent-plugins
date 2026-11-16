"""Write, verify, and projection mixin for the CalDAV client.

This module defines :class:`CalDAVMutationMixin`, a mixin carrying the
verified-write surface (:meth:`create_event`, :meth:`update_event`,
:meth:`delete_event`), the read-after-write verification helpers
(:meth:`_verify_event`, :meth:`_verify_typed_fields`,
:meth:`_verify_etag_with_fallback`), and the UID fetch (:meth:`_fetch_by_uid`).
The methods stay methods — they use ``self`` and resolve transport helpers
(``_calendar``, ``account``, ``server``) and the VEVENT-to-:class:`EventSummary`
projection (``_event_to_summary``, kept on the concrete ``CalDAVClient`` itself)
on the assembled :class:`calcard_mcp.caldav_client.CalDAVClient`.

The import direction is shared-base ← this mixin ← caldav_client, so this
module imports from :mod:`calcard_mcp._caldav_base` but never from
:mod:`calcard_mcp.caldav_client`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, cast

from caldav.lib.error import NotFoundError
from icalendar import Calendar as ICalCalendar

from calcard_mcp._binary import BinaryReference, GeoCoordinates
from calcard_mcp._caldav_base import (
    _LOG,
    _to_aware_datetime,
    _touched_typed_fields,
)
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
from calcard_mcp.errors import ProtocolError, WriteVerificationError
from calcard_mcp.ical import (
    Alarm,
    Attendee,
    EventSummary,
    Person,
    RecurrenceRule,
    apply_event_clears,
    build_event_ical,
    make_aware,
    parse_vevent_to_summary,
)
from calcard_mcp.verifier import (
    coerce_expected,
    verify_etag,
    verify_fields,
    verify_summary_fields,
)


class CalDAVMutationMixin:
    """Verified create/update/delete writes and projection for ``CalDAVClient``."""

    account: Any
    server: Any
    _calendar: Any
    _event_to_summary: Any

    def create_event(
        self,
        *,
        calendar_url: str,
        summary: str,
        start: datetime,
        end: datetime,
        description: str | None = None,
        location: str | None = None,
        categories: list[str] | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinates | None = None,
        transparency: str = "",
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
    ) -> EventSummary:
        """Create a VEVENT in ``calendar_url`` and verify the server stored it.

        :param calendar_url: Target calendar URL.
        :type calendar_url: str
        :param summary: VEVENT ``SUMMARY`` property.
        :type summary: str
        :param start: Event start.
        :type start: datetime.datetime
        :param end: Event end.
        :type end: datetime.datetime
        :param description: Optional ``DESCRIPTION`` property.
        :type description: str | None
        :param location: Optional ``LOCATION`` property.
        :type location: str | None
        :param categories: Optional VEVENT ``CATEGORIES`` values.
        :type categories: list[str] | None
        :param classification: Optional VEVENT ``CLASS`` value.
        :type classification: str
        :param url: Optional VEVENT ``URL`` value.
        :type url: str
        :param geo: Optional VEVENT ``GEO`` coordinates.
        :type geo: GeoCoordinates | None
        :param transparency: Optional VEVENT ``TRANSP`` value.
        :type transparency: str
        :param resources: Optional VEVENT ``RESOURCES`` values.
        :type resources: list[str] | None
        :param comments: Optional VEVENT ``COMMENT`` values.
        :type comments: list[str] | None
        :param contacts: Optional VEVENT ``CONTACT`` values.
        :type contacts: list[str] | None
        :param related_to: Optional VEVENT ``RELATED-TO`` values.
        :type related_to: list[str] | None
        :param organizer: Optional VEVENT ``ORGANIZER`` value.
        :type organizer: Person | None
        :param attendees: Optional VEVENT ``ATTENDEE`` values.
        :type attendees: list[Attendee] | None
        :param alarms: Optional nested VEVENT ``VALARM`` components.
        :type alarms: list[Alarm] | None
        :param attachments: Optional VEVENT ``ATTACH`` values.
        :type attachments: list[BinaryReference] | None
        :param recurrence: Optional VEVENT ``RRULE`` value.
        :type recurrence: RecurrenceRule | None
        :param exdates: Optional VEVENT ``EXDATE`` values.
        :type exdates: list[datetime.datetime] | None
        :param rdates: Optional VEVENT ``RDATE`` values.
        :type rdates: list[datetime.datetime] | None
        :param recurrence_id: Optional VEVENT ``RECURRENCE-ID`` value.
        :type recurrence_id: datetime.datetime | None
        :returns: Summary of the freshly created event.
        :rtype: :class:`EventSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When the server-side copy
            differs from what was sent.
        :raises calcard_mcp.errors.ProtocolError: When the server refuses the write.
        """
        calendar = self._calendar(calendar_url)
        uid = f"{uuid.uuid4()}@calcard-mcp"
        tz = self.account.config.timezone
        start_aware = make_aware(start, tz)
        end_aware = make_aware(end, tz)
        # VEVENT has explicit DTSTART/DTEND ordering. VTODO exposes a due-only
        # model here, so caltodo_client intentionally has no symmetric guard.
        if end_aware <= start_aware:
            raise ValueError(
                f"event end must be after start (got start={start_aware!r}, end={end_aware!r})"
            )
        ical = build_event_ical(
            uid=uid,
            summary=summary,
            start=start_aware,
            end=end_aware,
            description=description,
            location=location,
            categories=categories,
            classification=classification,
            url=url,
            geo=geo,
            transparency=transparency,
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
            created = calendar.save_event(ical)
        except Exception as exc:
            raise ProtocolError(f"create_event failed for {self.account.id!r}: {exc}") from exc

        touched_typed_fields = _touched_typed_fields(
            categories=categories,
            classification=classification,
            url=url,
            geo=geo,
            transparency=transparency,
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
            self._verify_event(created, summary=summary, description=description, location=location)
            if touched_typed_fields:
                self._verify_typed_fields(
                    intended_ical=ical,
                    actual=created,
                    calendar_url=calendar_url,
                    fields=touched_typed_fields,
                )
            self._verify_etag_with_fallback(created, pre_etag=None)

        stored = self._event_to_summary(created, calendar_url)
        if stored is None:
            raise ProtocolError("server returned an event without a readable start/end")
        return stored

    def update_event(
        self,
        *,
        calendar_url: str,
        uid: str,
        summary: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
        categories: list[str] | None = None,
        classification: str = "",
        url: str = "",
        geo: GeoCoordinates | None = None,
        transparency: str = "",
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
    ) -> EventSummary:
        """Update fields on an existing VEVENT and verify the change round-tripped.

        :param calendar_url: Calendar URL that holds the event.
        :type calendar_url: str
        :param uid: VEVENT ``UID`` of the event to modify.
        :type uid: str
        :param summary: New ``SUMMARY`` or :data:`None` to leave unchanged.
        :type summary: str | None
        :param start: New start or :data:`None` to leave unchanged.
        :type start: datetime.datetime | None
        :param end: New end or :data:`None` to leave unchanged.
        :type end: datetime.datetime | None
        :param clear_fields: Optional list of lowercase field names to remove
            from the event. Valid entries: ``"description"``, ``"location"``,
            ``"categories"``, ``"classification"``, ``"url"``, ``"geo"``,
            ``"transparency"``, ``"resources"``, ``"comments"``, ``"contacts"``,
            ``"related_to"``, ``"organizer"``, ``"attendees"``, ``"alarms"``,
            ``"attachments"``, ``"recurrence"``, ``"exdates"``, ``"rdates"``,
            ``"recurrence_id"``. ``"summary"``, ``"start"``, and ``"end"`` are
            required fields and cannot be cleared — including them raises
            :class:`ValueError`. Clearing wins over any matching positive
            argument in the same call.
        :type clear_fields: list[str] | None
        :param description: New ``DESCRIPTION`` or :data:`None` to leave unchanged.
        :type description: str | None
        :param location: New ``LOCATION`` or :data:`None` to leave unchanged.
        :type location: str | None
        :param categories: New ``CATEGORIES`` (empty list emits no line) or
            :data:`None` to leave unchanged.
        :type categories: list[str] | None
        :param classification: New ``CLASS`` (empty string leaves unchanged).
        :type classification: str
        :param url: New ``URL`` (empty string leaves unchanged).
        :type url: str
        :param geo: New ``GEO`` value or :data:`None` to leave unchanged.
        :type geo: GeoCoordinates | None
        :param transparency: New ``TRANSP`` (empty string leaves unchanged).
        :type transparency: str
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
        :returns: Summary of the updated event.
        :rtype: :class:`EventSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When verification fails.
        :raises calcard_mcp.errors.ProtocolError: When the event cannot be found or updated.
        """
        calendar = self._calendar(calendar_url)
        event = self._fetch_by_uid(calendar, uid)
        pre_etag = getattr(event, "etag", None)

        try:
            calendar_data: Any = ICalCalendar.from_ical(event.data)
        except Exception as exc:
            raise ProtocolError(
                f"server returned an iCalendar body for {uid!r} that icalendar could not parse"
            ) from exc
        vevent: Any = None
        for component in cast(list[Any], calendar_data.walk("VEVENT")):
            vevent = component
            break
        if vevent is None:
            raise ProtocolError(f"event {uid!r} contains no VEVENT component")

        tz = self.account.config.timezone
        start_aware = make_aware(start, tz) if start is not None else None
        end_aware = make_aware(end, tz) if end is not None else None
        # PRD 00010 cycle-1 review (Bob 🟠): a partial update must validate
        # against the *merged* DTSTART/DTEND, not just the patch fields. Fall
        # back to the existing vevent values when only one bound is patched.
        # PRD 00010 cycle-2 review (Alice/Diana 🟠): when the existing VEVENT
        # is an all-day event, ``existing_start.dt`` is a ``datetime.date``;
        # comparing it to a tz-aware ``datetime`` patch raises TypeError. Coerce
        # both sides to tz-aware datetimes (date → midnight in account tz)
        # before the comparison so the guard always raises ValueError.
        if start_aware is not None or end_aware is not None:
            existing_start = vevent.get("DTSTART")
            existing_end = vevent.get("DTEND")
            effective_start = (
                start_aware
                if start_aware is not None
                else _to_aware_datetime(
                    existing_start.dt if existing_start is not None else None, tz
                )
            )
            effective_end = (
                end_aware
                if end_aware is not None
                else _to_aware_datetime(existing_end.dt if existing_end is not None else None, tz)
            )
            if (
                effective_start is not None
                and effective_end is not None
                and effective_end <= effective_start
            ):
                raise ValueError(
                    "event end must be after start "
                    f"(got start={effective_start!r}, end={effective_end!r})"
                )
        # PRD 00001 §1.3: replace every touched property rather than relying on
        # icalendar's __setitem__ semantics (which have drifted across versions
        # and may leave multi-instance properties or skip vText wrapping).
        if summary is not None:
            vevent.pop("SUMMARY", None)
            vevent.add("SUMMARY", summary)
        if description is not None:
            vevent.pop("DESCRIPTION", None)
            vevent.add("DESCRIPTION", description)
        if location is not None:
            vevent.pop("LOCATION", None)
            vevent.add("LOCATION", location)
        if start_aware is not None:
            vevent.pop("DTSTART", None)
            vevent.add("DTSTART", start_aware)
        if end_aware is not None:
            vevent.pop("DTEND", None)
            vevent.add("DTEND", end_aware)

        # New typed properties: pop the existing line(s), then re-emit using
        # the shared helpers. ``None`` leaves the property untouched; an empty
        # list / empty string clears emission (matching ``build_event_ical``).
        if categories is not None:
            vevent.pop("CATEGORIES", None)
            emit_categories(vevent, categories)
        if classification:
            vevent.pop("CLASS", None)
            emit_classification(vevent, classification)
        if url:
            vevent.pop("URL", None)
            emit_url(vevent, url)
        if geo is not None:
            vevent.pop("GEO", None)
            emit_geo(vevent, geo)
        if transparency:
            vevent.pop("TRANSP", None)
            vevent.add("transp", transparency.upper())
        if resources is not None:
            vevent.pop("RESOURCES", None)
            emit_resources(vevent, resources)
        if comments is not None:
            vevent.pop("COMMENT", None)
            emit_text_properties(vevent, "comment", comments)
        if contacts is not None:
            vevent.pop("CONTACT", None)
            emit_text_properties(vevent, "contact", contacts)
        if related_to is not None:
            vevent.pop("RELATED-TO", None)
            emit_text_properties(vevent, "related-to", related_to)
        if organizer is not None:
            vevent.pop("ORGANIZER", None)
            emit_person(vevent, "organizer", organizer)
        if attendees is not None:
            vevent.pop("ATTENDEE", None)
            for attendee in attendees:
                emit_attendee(vevent, attendee)
        if attachments is not None:
            vevent.pop("ATTACH", None)
            for attachment in attachments:
                emit_attach(vevent, attachment)
        if recurrence is not None:
            vevent.pop("RRULE", None)
            emit_rrule(vevent, recurrence)
        if exdates is not None:
            vevent.pop("EXDATE", None)
            for exdate in exdates:
                vevent.add("exdate", as_utc_datetime(exdate))
        if rdates is not None:
            vevent.pop("RDATE", None)
            for rdate in rdates:
                vevent.add("rdate", as_utc_datetime(rdate))
        if recurrence_id is not None:
            vevent.pop("RECURRENCE-ID", None)
            vevent.add("recurrence-id", as_utc_datetime(recurrence_id))
        if alarms is not None:
            vevent.subcomponents = [
                child for child in vevent.subcomponents if child.name != "VALARM"
            ]
            for alarm in alarms:
                emit_alarm(vevent, alarm)

        # PRD 00001 §1.6: explicit clear wins over any also-provided value.
        if clear_fields:
            apply_event_clears(vevent, clear_fields)

        intended_ical = calendar_data.to_ical().decode("utf-8")
        event.data = intended_ical
        try:
            event.save()
        except Exception as exc:
            raise ProtocolError(f"update_event failed for {uid!r}: {exc}") from exc

        if self.server.verify_writes:
            cleared = {name.lower() for name in clear_fields or ()}
            try:
                self._verify_event(
                    event,
                    summary=summary,
                    # Do not verify a field we just cleared — the server legitimately
                    # stores it as empty/missing.
                    description=None if "description" in cleared else description,
                    location=None if "location" in cleared else location,
                )
                touched_typed_fields = _touched_typed_fields(
                    categories=categories,
                    classification=classification,
                    url=url,
                    geo=geo,
                    transparency=transparency,
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
                touched_typed_fields = [
                    name for name in touched_typed_fields if name not in cleared
                ]
                if touched_typed_fields:
                    self._verify_typed_fields(
                        intended_ical=intended_ical,
                        actual=event,
                        calendar_url=calendar_url,
                        fields=touched_typed_fields,
                    )
                self._verify_etag_with_fallback(event, pre_etag=pre_etag)
            except WriteVerificationError as exc:
                # PRD 00010 §10.8 diagnostic context (UID, ETag pair) — embed
                # at the call site rather than threading through verify_*.
                post_etag = getattr(event, "etag", None)
                raise WriteVerificationError(
                    f"{exc} (uid={uid!r}, pre_etag={pre_etag!r}, post_etag={post_etag!r})",
                    field_diffs=exc.field_diffs,
                ) from exc

        stored = self._event_to_summary(event, calendar_url)
        if stored is None:
            raise ProtocolError("server returned an event without a readable start/end")
        return stored

    def delete_event(self, *, calendar_url: str, uid: str) -> None:
        """Delete the VEVENT with ``uid`` from ``calendar_url`` and verify absence.

        :param calendar_url: Calendar URL that holds the event.
        :type calendar_url: str
        :param uid: VEVENT ``UID`` of the event to remove.
        :type uid: str
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.WriteVerificationError: When the event is still
            reachable after delete.
        :raises calcard_mcp.errors.ProtocolError: When the initial delete fails.
        """
        calendar = self._calendar(calendar_url)
        event = self._fetch_by_uid(calendar, uid)
        try:
            event.delete()
        except Exception as exc:
            raise ProtocolError(f"delete_event failed for {uid!r}: {exc}") from exc

        if self.server.verify_writes:
            try:
                calendar.event_by_uid(uid)
            except NotFoundError:
                return
            raise ProtocolError(
                f"event {uid!r} still present after delete on account {self.account.id!r}"
            )

    def _fetch_by_uid(self, calendar: Any, uid: str) -> Any:
        """Return the :class:`caldav.Event` with ``uid`` in ``calendar``.

        :param calendar: :class:`caldav.Calendar` to search.
        :type calendar: typing.Any
        :param uid: VEVENT ``UID``.
        :type uid: str
        :returns: The matching :class:`caldav.Event`.
        :rtype: typing.Any
        :raises calcard_mcp.errors.ProtocolError: When no event has the requested UID.
        """
        try:
            return calendar.event_by_uid(uid)
        except NotFoundError as exc:
            raise ProtocolError(f"event {uid!r} not found in calendar {calendar.url!r}") from exc

    def _verify_etag_with_fallback(self, event: Any, *, pre_etag: str | None) -> None:
        """Run ETag verification, tolerating servers that omit the post-PUT ETag.

        ``_verify_event`` has already called ``event.load()``, so ``event.etag``
        reflects a follow-up GET. If the server still exposes no ETag, log a
        warning and rely on field-level verification rather than failing the
        write.

        :param event: The event object just verified by :meth:`_verify_event`.
        :type event: typing.Any
        :param pre_etag: ETag read before the write (``None`` for creates).
        :type pre_etag: str | None
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.WriteVerificationError: When a non-empty
            post-write ETag is present but equals ``pre_etag``.
        """
        post_etag = getattr(event, "etag", None)
        if not post_etag:
            _LOG.warning(
                "server returned no ETag for %s; relying on field-level verification",
                self.account.id,
            )
            return
        verify_etag(pre_etag=pre_etag, post_etag=post_etag)

    def _verify_event(
        self,
        event: Any,
        *,
        summary: str | None,
        description: str | None,
        location: str | None,
    ) -> None:
        """Re-read ``event`` and assert the intended properties are persisted.

        :param event: :class:`caldav.Event` just written by the server.
        :type event: typing.Any
        :param summary: Intended ``SUMMARY`` value or :data:`None` to skip.
        :type summary: str | None
        :param description: Intended ``DESCRIPTION`` value or :data:`None` to skip.
        :type description: str | None
        :param location: Intended ``LOCATION`` value or :data:`None` to skip.
        :type location: str | None
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.WriteVerificationError: On any field mismatch.
        """
        try:
            event.load()
        except Exception as exc:
            raise ProtocolError(f"could not re-read event after write: {exc}") from exc
        expected = coerce_expected(
            [
                ("SUMMARY", summary),
                ("DESCRIPTION", description),
                ("LOCATION", location),
            ]
        )
        if expected:
            verify_fields(event.data, component="VEVENT", expected=expected)

    def _verify_typed_fields(
        self,
        *,
        intended_ical: str,
        actual: Any,
        calendar_url: str,
        fields: list[str],
    ) -> None:
        """Diff the typed VEVENT properties the caller touched, post-write.

        Parses the iCal we sent (``intended_ical``) and the server's read-back
        (``actual.data``, refreshed by :meth:`_verify_event`) into
        :class:`EventSummary` instances and runs them through
        :func:`calcard_mcp.verifier.verify_summary_fields`. Only the listed
        ``fields`` are diffed; identical baseline values for the required
        scalar fields (``account_id``, ``calendar_url``, ...) match on both
        sides because the same parser is applied to both inputs with the
        same context.

        :param intended_ical: The iCalendar text the client wrote to the server.
        :type intended_ical: str
        :param actual: :class:`caldav.Event` whose ``data`` attribute holds the
            server's post-write read-back (already refreshed by
            :meth:`_verify_event`).
        :type actual: typing.Any
        :param calendar_url: URL of the owning calendar (passed to the parser).
        :type calendar_url: str
        :param fields: Typed field names to diff (e.g. ``"categories"``,
            ``"organizer"``, ``"recurrence"``).
        :type fields: list[str]
        :raises calcard_mcp.errors.WriteVerificationError: When any listed
            field differs between intended and actual.
        :raises calcard_mcp.errors.ProtocolError: When either side fails to
            parse into a usable :class:`EventSummary`.
        """
        resource_url = str(getattr(actual, "url", ""))
        fallback_tz = self.account.config.timezone
        intended_summary = parse_vevent_to_summary(
            intended_ical,
            account_id=self.account.id,
            calendar_url=calendar_url,
            resource_url=resource_url,
            fallback_tz=fallback_tz,
        )
        if intended_summary is None:
            raise ProtocolError(
                "could not project intended VEVENT into an EventSummary for verification"
            )
        actual_summary = parse_vevent_to_summary(
            actual.data,
            account_id=self.account.id,
            calendar_url=calendar_url,
            resource_url=resource_url,
            fallback_tz=fallback_tz,
        )
        if actual_summary is None:
            raise ProtocolError("could not project server VEVENT response into an EventSummary")
        verify_summary_fields(intended_summary, actual_summary, fields=fields)
