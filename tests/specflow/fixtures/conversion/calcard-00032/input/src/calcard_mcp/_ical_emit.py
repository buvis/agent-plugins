"""Reusable iCalendar property emission helpers."""

from __future__ import annotations

import base64
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol, cast

from icalendar import Alarm as ICalAlarm
from icalendar.prop import vCategory, vText

from ._binary import BinaryReference, GeoCoordinates


class _PersonLike(Protocol):
    @property
    def address(self) -> str: ...
    @property
    def common_name(self) -> str: ...


class _AttendeeLike(_PersonLike, Protocol):
    @property
    def role(self) -> str: ...
    @property
    def partstat(self) -> str: ...
    @property
    def rsvp(self) -> bool: ...
    @property
    def cu_type(self) -> str: ...


class _AlarmLike(Protocol):
    @property
    def action(self) -> str: ...
    @property
    def trigger(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def summary(self) -> str: ...
    @property
    def attendees(self) -> Sequence[_PersonLike]: ...


class _RecurrenceRuleLike(Protocol):
    @property
    def raw(self) -> str: ...
    @property
    def freq(self) -> str: ...
    @property
    def interval(self) -> int: ...
    @property
    def count(self) -> int: ...
    @property
    def until(self) -> datetime | None: ...
    @property
    def by_day(self) -> list[str]: ...
    @property
    def by_month_day(self) -> list[int]: ...
    @property
    def by_month(self) -> list[int]: ...
    @property
    def by_set_pos(self) -> list[int]: ...
    @property
    def week_start(self) -> str: ...


class _ComponentLike(Protocol):
    def __setitem__(self, key: str, value: object) -> None: ...
    def add(
        self,
        name: str,
        value: object,
        parameters: dict[str, str] | None = None,
        encode: bool = True,
    ) -> None: ...
    def add_component(self, component: object) -> None: ...


def emit_categories(component: _ComponentLike, categories: Sequence[str] | None) -> None:
    """Append a CATEGORIES property when non-empty values are present."""
    non_empty = [value for value in categories or [] if value]
    if non_empty:
        component.add("categories", non_empty)


def emit_classification(component: _ComponentLike, classification: str) -> None:
    """Append a CLASS property when present."""
    if classification:
        component.add("class", classification.upper())


def emit_url(component: _ComponentLike, url: str) -> None:
    """Append a URL property when present."""
    if url:
        component.add("url", url)


def emit_geo(component: _ComponentLike, geo: GeoCoordinates | None) -> None:
    """Append a GEO property when present."""
    if geo is not None:
        component.add("geo", (geo.latitude, geo.longitude))


def emit_resources(component: _ComponentLike, resources: Sequence[str] | None) -> None:
    """Append a RESOURCES property when non-empty values are present."""
    non_empty = [value for value in resources or [] if value]
    if non_empty:
        component["RESOURCES"] = vCategory(non_empty)


def emit_text_properties(
    component: _ComponentLike, prop_name: str, values: Sequence[str] | None
) -> None:
    """Append one text property per non-empty value."""
    for value in values or []:
        if value:
            component.add(prop_name, value)


def emit_person(component: _ComponentLike, prop_name: str, person: _PersonLike) -> None:
    """Append an ORGANIZER/ATTENDEE-like person property."""
    if not person.address:
        return
    parameters: dict[str, str] = {}
    if person.common_name:
        parameters["CN"] = person.common_name
    component.add(prop_name, person.address, parameters=parameters)


def emit_attendee(component: _ComponentLike, attendee: _AttendeeLike) -> None:
    """Append an ATTENDEE property with supported RFC 5545 parameters."""
    if not attendee.address:
        return
    parameters: dict[str, str] = {}
    if attendee.common_name:
        parameters["CN"] = attendee.common_name
    parameters["ROLE"] = attendee.role.upper()
    parameters["PARTSTAT"] = attendee.partstat.upper()
    parameters["RSVP"] = "TRUE" if attendee.rsvp else "FALSE"
    parameters["CUTYPE"] = attendee.cu_type.upper()
    component.add("attendee", attendee.address, parameters=parameters)


def _is_relative_trigger(trigger: str) -> bool:
    """ISO 8601 durations start with ``P``, ``+P`` or ``-P``; absolute datetimes don't."""
    return trigger.startswith(("P", "+P", "-P"))


def emit_alarm(component: _ComponentLike, alarm: _AlarmLike) -> None:
    """Append a VALARM sub-component, enforcing action-specific invariants."""
    if not alarm.trigger:
        raise ValueError("alarm requires non-empty trigger")
    if alarm.action == "display" and not alarm.description:
        raise ValueError("display alarm requires non-empty description")
    if alarm.action == "email" and not alarm.description:
        raise ValueError("email alarm requires non-empty description")
    if alarm.action == "email" and not alarm.summary:
        raise ValueError("email alarm requires non-empty summary")
    if alarm.action == "email" and not alarm.attendees:
        raise ValueError("email alarm requires at least one attendee")

    valarm = cast(_ComponentLike, ICalAlarm())
    valarm.add("action", alarm.action.upper())
    trigger_prop = vText(alarm.trigger)
    if not _is_relative_trigger(alarm.trigger):
        trigger_prop.params.update({"VALUE": "DATE-TIME"})
    valarm.add("trigger", trigger_prop, encode=False)
    valarm.add("description", alarm.description)
    if alarm.action == "email":
        valarm.add("summary", alarm.summary)
        for attendee in alarm.attendees:
            emit_person(valarm, "attendee", attendee)
    component.add_component(valarm)


def _format_utc_ical_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def as_utc_datetime(value: datetime) -> datetime:
    """Return a UTC-aware datetime for iCalendar recurrence properties."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


# Validate raw RRULE strings: reject FREQ values that the parser will not
# round-trip. Mirrors the whitelist in _ical_parse._FREQ_VALUES so that emit
# and parse stay symmetric.
_RAW_RRULE_FREQ_VALUES = frozenset(
    {"SECONDLY", "MINUTELY", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
)


def _rule_is_empty(rule: _RecurrenceRuleLike) -> bool:
    return (
        rule.raw == ""
        and rule.freq == ""
        and rule.interval == 0
        and rule.count == 0
        and rule.until is None
        and rule.by_day == []
        and rule.by_month_day == []
        and rule.by_month == []
        and rule.by_set_pos == []
        and rule.week_start == ""
    )


def emit_rrule(component: _ComponentLike, rule: _RecurrenceRuleLike) -> None:
    """Append an RRULE property when the rule has raw or structured content."""
    if _rule_is_empty(rule):
        return
    if rule.raw:
        freq_match = re.search(r"FREQ=([A-Z]+)", rule.raw, re.IGNORECASE)
        if not freq_match or freq_match.group(1).upper() not in _RAW_RRULE_FREQ_VALUES:
            raise ValueError(
                "invalid RRULE FREQ value "
                f"(must be one of {sorted(_RAW_RRULE_FREQ_VALUES)}): {rule.raw!r}"
            )
        component.add("rrule", rule.raw)
        return

    parts: list[str] = []
    if rule.freq:
        parts.append(f"FREQ={rule.freq.upper()}")
    if rule.interval:
        parts.append(f"INTERVAL={rule.interval}")
    if rule.count:
        parts.append(f"COUNT={rule.count}")
    if rule.until is not None:
        parts.append(f"UNTIL={_format_utc_ical_datetime(rule.until)}")
    if rule.by_day:
        parts.append(f"BYDAY={','.join(rule.by_day)}")
    if rule.by_month_day:
        parts.append(f"BYMONTHDAY={','.join(str(value) for value in rule.by_month_day)}")
    if rule.by_month:
        parts.append(f"BYMONTH={','.join(str(value) for value in rule.by_month)}")
    if rule.by_set_pos:
        parts.append(f"BYSETPOS={','.join(str(value) for value in rule.by_set_pos)}")
    if rule.week_start:
        parts.append(f"WKST={rule.week_start}")
    if parts:
        component.add("rrule", ";".join(parts))


_BINARY_DATA_URI_PATTERN = re.compile(
    r"^data:([^;,]*)((?:;[^;,]+)*);base64,(.+)$",
    flags=re.IGNORECASE,
)
_BINARY_ALLOWED_SCHEMES: tuple[str, ...] = ("data", "http", "https", "file")


def emit_attach(component: _ComponentLike, ref: BinaryReference) -> None:
    """Append an ATTACH property using data/http/https/file URI dispatch."""
    value = ref.value
    if value.startswith("data:"):
        match = _BINARY_DATA_URI_PATTERN.match(value)
        if match is None:
            raise ValueError(
                "malformed attach data: URI: expected "
                "'data:<media-type>[;<param>=<value>]*;base64,<payload>'"
            )
        media_type, _extra_params, payload = match.groups()
        media_type = media_type or ref.media_type
        if not media_type:
            raise ValueError(
                "attach data: URI requires a media_type "
                "(either inline as 'data:<media>;base64,...' or via "
                "BinaryReference.media_type)"
            )
        try:
            base64.b64decode(payload, validate=True)
        except Exception as exc:
            raise ValueError("invalid base64 payload in attach data URI") from exc
        prop = vText(payload)
        prop.params.update(
            {
                "ENCODING": "BASE64",
                "VALUE": "BINARY",
                "FMTTYPE": media_type,
            }
        )
        component.add("attach", prop, encode=False)
        return

    if value.startswith(("http://", "https://", "file://")):
        prop = vText(value)
        if ref.media_type:
            prop.params.update({"FMTTYPE": ref.media_type})
        component.add("attach", prop, encode=False)
        return

    raise ValueError(f"unsupported scheme; accepted: {', '.join(_BINARY_ALLOWED_SCHEMES)}")
