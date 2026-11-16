"""Listing, recurrence expansion, and search mixin for the CalDAV client.

This module defines :class:`CalDAVRecurrenceMixin`, a mixin carrying
:meth:`list_events`, :meth:`search_events`, and the recurrence-expansion
helpers (EXDATE-only master recovery, UID grouping, RRULE expansion, override
re-anchoring, and deduplication). The methods stay methods — they use ``self``
and resolve transport helpers (``_calendar``, ``_event_to_summary``,
``list_calendars``) on the assembled :class:`calcard_mcp.caldav_client.CalDAVClient`.

The import direction is shared-base ← this mixin ← caldav_client, so this
module imports from :mod:`calcard_mcp._caldav_base` but never from
:mod:`calcard_mcp.caldav_client`.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, cast

from caldav.lib.error import AuthorizationError, DAVError

from calcard_mcp._caldav_base import (
    _LOG,
    _inherit_master_transp,
    _status_cancelled,
)
from calcard_mcp.errors import ProtocolError
from calcard_mcp.ical import (
    EventSummary,
    extract_rrule_text,
    make_aware,
    resolve_tz_name,
)


class CalDAVRecurrenceMixin:
    """Event listing, recurrence expansion, and search behaviour for ``CalDAVClient``."""

    account: Any
    _event_to_summary: Any
    _calendar: Any
    list_calendars: Any

    def _search_with_expand_fallback(
        self,
        calendar: Any,
        start: datetime,
        end: datetime,
        calendar_url: str,
    ) -> list[Any]:
        """Search the calendar with server-side ``expand=True``; fall back on DAV errors.

        Narrowed from the previous ``except Exception``: only :class:`DAVError`
        triggers the non-expand fallback. :class:`AuthorizationError` is
        re-raised so credential failures cannot be silently masked, and any
        non-DAV transport error (network timeout, connection reset) propagates
        unchanged for the caller to wrap.

        :param calendar: Resolved :class:`caldav.Calendar` instance.
        :type calendar: typing.Any
        :param start: Inclusive UTC-aware range start.
        :type start: datetime.datetime
        :param end: Exclusive UTC-aware range end.
        :type end: datetime.datetime
        :param calendar_url: URL of the calendar (for log lines only).
        :type calendar_url: str
        :returns: Raw caldav event list (per-instance when expand worked,
            master-only when the fallback path ran).
        :rtype: list[typing.Any]
        :raises caldav.lib.error.AuthorizationError: On 401/403 from either search.
        :raises caldav.lib.error.DAVError: When the non-expand fallback also
            raises a DAV-level error (caller wraps to :class:`ProtocolError`).
        """
        try:
            return cast(
                list[Any],
                calendar.search(start=start, end=end, event=True, expand=True),
            )
        except AuthorizationError:
            raise
        except DAVError:
            _LOG.debug(
                "server-side expand unsupported for %s; falling back to client-side RRULE",
                calendar_url,
                exc_info=True,
            )
            return cast(list[Any], calendar.search(start=start, end=end, event=True))

    def _fetch_primary_events(
        self,
        calendar: Any,
        start_aware: datetime,
        end_aware: datetime,
        calendar_url: str,
    ) -> list[Any]:
        """Run the primary expand/fallback search, wrapping DAV failures.

        :meth:`_search_with_expand_fallback` re-raises at the FFI boundary for
        its caller to wrap. :class:`AuthorizationError` surfaces as
        :class:`ProtocolError` ("authorization failed") so credential failures
        are never silently masked; any other :class:`DAVError` (e.g. the
        non-expand fallback also failing) surfaces as :class:`ProtocolError`
        ("search failed"). Mirrors the invariant the recovery scan enforces.

        :param calendar: Resolved :class:`caldav.Calendar` instance.
        :type calendar: typing.Any
        :param start_aware: Inclusive aware range start.
        :type start_aware: datetime.datetime
        :param end_aware: Exclusive aware range end.
        :type end_aware: datetime.datetime
        :param calendar_url: Absolute calendar URL (for error messages).
        :type calendar_url: str
        :returns: Raw caldav event list.
        :rtype: list[typing.Any]
        :raises calcard_mcp.errors.ProtocolError: On any DAV-level search failure.
        """
        try:
            return self._search_with_expand_fallback(
                calendar, start_aware, end_aware, calendar_url
            )
        except AuthorizationError as exc:
            raise ProtocolError(
                f"calendar search authorization failed for {calendar_url!r}: {exc}"
            ) from exc
        except DAVError as exc:
            raise ProtocolError(
                f"calendar search failed for {calendar_url!r}: {exc}"
            ) from exc

    def list_events(
        self,
        calendar_url: str,
        start: datetime,
        end: datetime,
    ) -> list[EventSummary]:
        """List events in ``calendar_url`` whose instances fall within ``[start, end)``.

        Recurring events are expanded to per-instance summaries via RFC 4791
        ``expand`` (with local RRULE fallback). Also issues a supplementary
        unbounded recovery scan; see :meth:`_recover_exdate_only_masters` for
        the accepted-cost rationale.

        :param calendar_url: Absolute calendar URL.
        :param start: Inclusive range start.
        :param end: Exclusive range end.
        :returns: Event summaries (one per occurrence) ordered by start time.
        """
        calendar = self._calendar(calendar_url)
        tz = self.account.config.timezone
        start_aware = make_aware(start, tz)
        end_aware = make_aware(end, tz)
        raw_events = self._fetch_primary_events(
            calendar, start_aware, end_aware, calendar_url
        )

        # Recover dropped EXDATE-only masters
        recovered_pairs = self._recover_exdate_only_masters(
            calendar, calendar_url, start_aware, end_aware
        )

        # Group events by UID
        masters_by_uid, overrides_by_uid = self._group_events_by_uid(
            raw_events, recovered_pairs, calendar_url
        )

        # Expand and deduplicate
        summaries = self._expand_and_dedup(
            masters_by_uid, overrides_by_uid, calendar_url, start_aware, end_aware, tz
        )

        return summaries

    def _recover_exdate_only_masters(
        self,
        calendar: Any,
        calendar_url: str,
        start_aware: datetime,
        end_aware: datetime,
    ) -> list[tuple[Any, EventSummary]]:
        """Recover EXDATE-only masters silently dropped by the server.

        Radicale 3.5.0.0 drops a master with EXDATE-but-no-RRULE/RDATE from
        both expand REPORT and time-range searches. Fetch ALL VEVENTs; keep
        only pure-EXDATE masters whose DTSTART falls inside the window.

        ACCEPTED COST (issue 00027): unbounded, runs every call, not gated, not
        capped. Gating is impossible — a dropped master leaves no trace in the
        expand result, so the scan is the only signal. Capping is unsafe — the
        result set is unordered and a cap could drop the target. Re-scoping to
        [start, end) is the original bug. Missed master = regression; extra
        O(N) scan = not — so we always scan.
        """
        try:
            non_expanded = cast(list[Any], calendar.search(event=True))
        except AuthorizationError as exc:
            # Never silently mask a credential/permission failure.
            raise ProtocolError(
                f"calendar search authorization failed for {calendar_url!r}: {exc}"
            ) from exc
        except DAVError:
            # Best-effort recovery: DAV error must not fail the call.
            _LOG.debug(
                "supplementary all-events search failed for %s; EXDATE-only "
                "masters (if any) not recovered",
                calendar_url,
                exc_info=True,
            )
            non_expanded = []

        recovered_pairs: list[tuple[Any, EventSummary]] = []
        for candidate in non_expanded:
            candidate_summary = self._event_to_summary(candidate, calendar_url)
            if (
                candidate_summary is not None
                and candidate_summary.recurrence is None
                and not candidate_summary.rdates
                and candidate_summary.exdates
                and start_aware <= candidate_summary.start < end_aware
            ):
                recovered_pairs.append((candidate, candidate_summary))
        return recovered_pairs

    def _group_events_by_uid(
        self,
        raw_events: list[Any],
        recovered_pairs: list[tuple[Any, EventSummary]],
        calendar_url: str,
    ) -> tuple[
        dict[str, list[tuple[Any, EventSummary]]],
        dict[str, list[tuple[Any, EventSummary]]]
    ]:
        """Group events by UID for later processing.

        Master = a VEVENT with no RECURRENCE-ID; override = a VEVENT carrying one.
        """
        # Group resources by UID so detached RECURRENCE-ID override resources
        # (RFC 5545 §3.8.4.4) can be merged into their master series' local
        # RRULE expansion.
        masters_by_uid: dict[str, list[tuple[Any, EventSummary]]] = {}
        overrides_by_uid: dict[str, list[tuple[Any, EventSummary]]] = {}

        for event in raw_events:
            summary = self._event_to_summary(event, calendar_url)
            if summary is None:
                # Unparseable bodies expand to nothing; skipping them here
                # matches the prior _expand_event(None-summary) -> [] behaviour.
                continue
            if summary.recurrence_id is not None:
                overrides_by_uid.setdefault(summary.uid, []).append((event, summary))
            else:
                masters_by_uid.setdefault(summary.uid, []).append((event, summary))

        # Route recovered pairs using their already-parsed summaries;
        # do NOT call _event_to_summary again (parse-once contract).
        for candidate, candidate_summary in recovered_pairs:
            if candidate_summary.recurrence_id is not None:
                overrides_by_uid.setdefault(candidate_summary.uid, []).append(
                    (candidate, candidate_summary)
                )
            else:
                masters_by_uid.setdefault(candidate_summary.uid, []).append(
                    (candidate, candidate_summary)
                )

        return masters_by_uid, overrides_by_uid

    def _expand_and_dedup(
        self,
        masters_by_uid: dict[str, list[tuple[Any, EventSummary]]],
        overrides_by_uid: dict[str, list[tuple[Any, EventSummary]]],
        calendar_url: str,
        start_aware: datetime,
        end_aware: datetime,
        tz: str,
    ) -> list[EventSummary]:
        """Expand events and perform deduplication.

        Expands recurring events and deduplicates the results based on (uid, start, recurrence_id).
        """
        summaries = self._expand_masters_and_overrides(
            masters_by_uid, overrides_by_uid, calendar_url, start_aware, end_aware, tz
        )

        summaries.extend(
            self._collect_orphan_overrides(overrides_by_uid, start_aware, end_aware)
        )

        # Dedup keyed on (uid, start, recurrence_id). RECURRENCE-ID is part of
        # the key so a detached override moved onto another occurrence's start
        # time (RFC 5545 §3.8.4.4 — each RECURRENCE-ID is a distinct instance)
        # survives instead of colliding with the master-generated occurrence at
        # that start. Genuine duplicates (the same master returned twice, or a
        # master plus a non-override instance resource) all carry
        # recurrence_id=None and still collapse.
        seen: set[tuple[str, datetime, datetime | None]] = set()
        deduped: list[EventSummary] = []
        for summary in summaries:
            key = (summary.uid, summary.start, summary.recurrence_id)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(summary)
        deduped.sort(key=lambda item: item.start)
        return deduped

    def _select_merge_target(
        self,
        uid: str,
        master_pairs: list[tuple[Any, EventSummary]],
    ) -> tuple[list[int], int | None]:
        """Return (recurring_indices, merge_idx) for a UID's master list.

        An override merges into an RRULE expansion only when exactly one master
        is recurring. With zero or multiple recurring masters there is no single
        merge target and overrides surface via the orphan path. Multiple
        recurring masters indicate malformed server input and are warned.
        """
        recurring = [i for i, (_e, s) in enumerate(master_pairs) if s.recurrence is not None]
        if len(recurring) > 1:
            # Malformed server input: a UID with multiple recurring masters
            # has no single merge target, so overrides are routed to the
            # orphan path instead of merged. Surface the ambiguity rather
            # than dropping it silently.
            _LOG.warning(
                "list_events: UID %r returned %d recurring masters; "
                "routing overrides via the orphan path",
                uid,
                len(recurring),
            )
        merge_idx = recurring[0] if len(recurring) == 1 else None
        return recurring, merge_idx

    def _reanchor_overrides(
        self,
        override_pairs: list[tuple[Any, EventSummary]],
        master_pairs: list[tuple[Any, EventSummary]],
        recurring: list[int],
        tz: str,
        calendar_url: str,
    ) -> list[EventSummary]:
        """Re-parse overrides anchored to the recurring master's timezone.

        With exactly one recurring master that master is the merge target; with
        >=2 we still re-anchor against recurring[0] as best-effort (overrides
        surface via the non-merge path but with the correct tz). With zero
        recurring masters no series tz exists and overrides keep first-pass parse.
        """
        if not recurring:
            return [s for _e, s in override_pairs]
        anchor_summary = master_pairs[recurring[0]][1]
        # Fallback to account tz only when master.start.tzinfo is unresolvable
        # (custom tzinfo without `.key`, fixed-offset, etc.).
        master_tz_name = resolve_tz_name(anchor_summary.start.tzinfo, tz)
        reanchored: list[EventSummary] = []
        for ovr_event, _ovr_summary in override_pairs:
            re_parsed = self._event_to_summary(
                ovr_event, calendar_url, master_anchor_tz_name=master_tz_name
            )
            if re_parsed is None:
                raise RuntimeError(
                    f"list_events: re-parse of override {ovr_event.url!r} returned None "
                    f"despite first-pass success — invariant broken"
                )
            reanchored.append(re_parsed)
        return reanchored

    def _expand_masters_and_overrides(
        self,
        masters_by_uid: dict[str, list[tuple[Any, EventSummary]]],
        overrides_by_uid: dict[str, list[tuple[Any, EventSummary]]],
        calendar_url: str,
        start_aware: datetime,
        end_aware: datetime,
        tz: str,
    ) -> list[EventSummary]:
        """Expand master events and handle override merging."""
        summaries: list[EventSummary] = []
        for uid, master_pairs in masters_by_uid.items():
            override_pairs = overrides_by_uid.pop(uid, [])
            recurring, merge_idx = self._select_merge_target(uid, master_pairs)
            overrides = self._reanchor_overrides(
                override_pairs, master_pairs, recurring, tz, calendar_url
            )
            for i, (master_event, master_summary) in enumerate(master_pairs):
                merged = overrides if i == merge_idx else None
                summaries.extend(
                    self._expand_event(
                        master_event,
                        calendar_url,
                        start_aware,
                        end_aware,
                        merged,
                        base_summary=master_summary,
                    )
                )
            if merge_idx is None:
                # No recurring master to merge into; surface in-window overrides.
                # Suppress STATUS:CANCELLED (RFC 5545 §3.8.1.11) to match the
                # merge-path behavior inside _expand_event.
                for override in overrides:
                    if start_aware <= override.start < end_aware and not _status_cancelled(
                        override
                    ):
                        summaries.append(override)
        return summaries

    def _collect_orphan_overrides(
        self,
        overrides_by_uid: dict[str, list[tuple[Any, EventSummary]]],
        start_aware: datetime,
        end_aware: datetime,
    ) -> list[EventSummary]:
        """Return overrides whose master series was not returned at all."""
        # Overrides whose master series was not returned at all have nothing to
        # merge into; surface them standalone when they fall inside the window.
        # No master means no series tz to re-anchor against, so orphan overrides
        # keep their first-pass parse (RECURRENCE-ID anchored to the override's
        # own DTSTART tz) — spec-correct fallback when no master is available.
        # Cancelled-suppression parity with the merge and non-merge paths.
        orphans: list[EventSummary] = []
        for orphan_pairs in overrides_by_uid.values():
            for _ovr_event, override in orphan_pairs:
                if start_aware <= override.start < end_aware and not _status_cancelled(override):
                    orphans.append(override)
        return orphans

    def _expand_event(
        self,
        event: Any,
        calendar_url: str,
        start: datetime,
        end: datetime,
        overrides: list[EventSummary] | None = None,
        base_summary: EventSummary | None = None,
    ) -> list[EventSummary]:
        """Return one :class:`EventSummary` per instance of ``event`` in ``[start, end)``.

        For a non-recurring event this yields the single summary. For a
        master VEVENT with an ``RRULE``, this walks every RRULE occurrence
        in the window via :mod:`dateutil.rrule` and emits a summary per
        occurrence (shifting DTSTART/DTEND by each occurrence's offset
        from the master start). ``EXDATE`` values exclude their matching
        RRULE occurrences; ``RDATE`` values add extra occurrences (subject
        to the ``[start, end)`` window). EXDATE wins over a coinciding
        RDATE per RFC 5545 §3.8.5.1.

        Per-occurrence summaries inherit typed fields from the master,
        including the series-level ``recurrence`` / ``exdates`` / ``rdates``
        triple. ``recurrence_id`` is per-occurrence override identification
        (RFC 5545 §3.8.4.4) and is inherited as-is from the master too
        (typically ``None`` on a non-override master).

        Detached RECURRENCE-ID override resources (RFC 5545 §3.8.4.4) are
        merged in via ``overrides``: when an override's ``recurrence_id``
        matches an RRULE-generated occurrence, the override replaces that
        occurrence entirely (per-instance field edits and time moves are
        already canonical in the override's own summary). An override with
        ``STATUS:CANCELLED`` suppresses its occurrence (RFC 5545 §3.8.1.11).
        Only single-instance overrides (``RANGE`` defaulting to
        ``THISONLY``) are handled; ``RANGE=THISANDFUTURE`` is out of scope.

        EXDATE-vs-override precedence: the EXDATE filter precedes the
        override lookup, so an override whose ``recurrence_id`` coincides
        with an EXDATE'd occurrence is intentionally not consumed by that
        occurrence. The override is not lost — it surfaces at its own
        start via the residual-overrides emit below the RRULE loop. This
        is by design: an explicit RECURRENCE-ID override outranks an
        EXDATE for the same instance, but the implementation expresses
        that ordering by emitting the override at its own (possibly
        moved) start rather than at the EXDATE'd slot.

        :param event: The event returned by ``calendar.search``.
        :type event: typing.Any
        :param calendar_url: URL of the owning calendar.
        :type calendar_url: str
        :param start: Inclusive window start (timezone-aware).
        :type start: datetime.datetime
        :param end: Exclusive window end (timezone-aware).
        :type end: datetime.datetime
        :param overrides: Detached RECURRENCE-ID override summaries for this
            event's UID, or :data:`None` when the event has no overrides.
        :type overrides: list[:class:`EventSummary`] | None
        :param base_summary: Caller-supplied parse of ``event``. When provided,
            the internal :meth:`_event_to_summary` call is skipped — callers
            that already parsed the master VEVENT (e.g. :meth:`list_events`
            via its UID-grouping loop) avoid a redundant re-parse. When
            :data:`None`, ``event`` is parsed internally.
        :type base_summary: :class:`EventSummary` | None
        :returns: One summary per occurrence in ``[start, end)``.
        :rtype: list[:class:`EventSummary`]
        """
        if base_summary is None:
            base_summary = self._event_to_summary(event, calendar_url)
        if base_summary is None:
            return []

        rrule_text = extract_rrule_text(event.data)
        if not rrule_text:
            return [base_summary]

        # Master event has an RRULE → expand locally. Honor the documented
        # [start, end) contract: include occurrences AT start, exclude
        # occurrences AT end. dateutil.rrule.between(..., inc=True) gives a
        # closed [start, end] interval; we filter out the right endpoint to
        # arrive at the half-open contract. When the recurrence has zero
        # occurrences in the window, return an empty list — the master's
        # DTSTART is itself outside the window.
        # dateutil is imported lazily; keep the import local so non-recurring
        # paths don't pay for it.
        from dateutil.rrule import rrulestr

        try:
            rule: Any = rrulestr(rrule_text, dtstart=base_summary.start)
        except ValueError:
            _LOG.debug(
                "RRULE parse failed for %s; returning master only if it falls inside the window",
                base_summary.uid,
                exc_info=True,
            )
            # Best-effort fallback only when the master itself is in window.
            if start <= base_summary.start < end:
                return [base_summary]
            return []

        # base_summary.exdates / .rdates are populated by parse_vevent_to_summary
        # from the same body with the same anchor tz, so reuse them rather than
        # re-parsing event.data here.
        exdate_set: set[datetime] = set(base_summary.exdates)
        # A detached override replaces the occurrence whose RECURRENCE-ID it
        # carries. Keys are the overrides' recurrence_id values; they hash-equal
        # the rrule.between() output because both anchor to the master DTSTART
        # tz (verified by PRD 00013). When two override resources for the same
        # UID carry the same RECURRENCE-ID, resolution is last-write-wins; a
        # WARNING surfaces the drop instead of letting it pass silently.
        override_by_rid: dict[datetime, EventSummary] = {}
        for ovr in overrides or []:
            if ovr.recurrence_id is None:
                continue
            if ovr.recurrence_id in override_by_rid:
                _LOG.warning(
                    "_expand_event: UID %r has duplicate RECURRENCE-ID "
                    "override %s; keeping last (RFC 5545 §3.8.4.4 is silent "
                    "on duplicates)",
                    base_summary.uid,
                    ovr.recurrence_id.isoformat(),
                )
            override_by_rid[ovr.recurrence_id] = ovr
        consumed_override_rids: set[datetime] = set()
        duration = base_summary.end - base_summary.start
        expansions: list[EventSummary] = []
        for occurrence in rule.between(start, end, inc=True):
            if occurrence >= end:
                continue
            if occurrence in exdate_set:
                continue
            override = override_by_rid.get(occurrence)
            if override is not None:
                consumed_override_rids.add(occurrence)
                if _status_cancelled(override):
                    continue
                if start <= override.start < end:
                    expansions.append(_inherit_master_transp(override, base_summary))
                continue
            expansions.append(replace(base_summary, start=occurrence, end=occurrence + duration))
        for recurrence_id, override in override_by_rid.items():
            if recurrence_id in consumed_override_rids:
                continue
            if _status_cancelled(override):
                continue
            if start <= override.start < end:
                expansions.append(_inherit_master_transp(override, base_summary))
        for rdate in base_summary.rdates:
            if not (start <= rdate < end):
                continue
            if rdate in exdate_set:
                # RFC 5545 §3.8.5.1: EXDATE wins over RDATE.
                continue
            expansions.append(replace(base_summary, start=rdate, end=rdate + duration))
        expansions.sort(key=lambda summary: summary.start)
        return expansions

    def search_events(
        self,
        query: str,
        start: datetime,
        end: datetime,
    ) -> list[EventSummary]:
        """Search every calendar on this account for events matching ``query``.

        The match is a case-insensitive substring check against the ``SUMMARY``,
        ``DESCRIPTION``, and ``LOCATION`` fields of events already filtered to
        the time range ``[start, end)``.

        :param query: Substring to search for.
        :type query: str
        :param start: Inclusive range start.
        :type start: datetime.datetime
        :param end: Exclusive range end.
        :type end: datetime.datetime
        :returns: Matching event summaries.
        :rtype: list[:class:`EventSummary`]
        """
        needle = query.strip().casefold()
        results: list[EventSummary] = []
        for calendar in self.list_calendars():
            for event in self.list_events(calendar.url, start, end):
                haystack = " ".join([event.summary, event.location, event.description]).casefold()
                if needle in haystack:
                    results.append(event)
        return results
