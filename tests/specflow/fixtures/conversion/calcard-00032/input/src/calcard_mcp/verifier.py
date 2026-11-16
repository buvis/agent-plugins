"""Read-after-write verification for CalDAV and CardDAV mutations.

Imports:

* :mod:`typing` for protocol-style callable annotations.
* :mod:`vobject` to parse returned iCalendar / vCard payloads.
* :class:`calcard_mcp.errors.WriteVerificationError` to report verification failures
  with a field-level diff.
* :func:`calcard_mcp.vcard.project_type_label` to project ``TYPE=`` parameters down
  to a single wire-form label so that typed multi-valued field comparisons (emails,
  phones) match the lossy-by-design read projection.
* :class:`calcard_mcp.ical.EventSummary` / :class:`calcard_mcp.vtodo.TaskSummary` /
  :class:`calcard_mcp.ical.RecurrenceRule` for typed-summary field-level diffs in
  :func:`verify_summary_fields`.
"""

from __future__ import annotations

import base64
from collections.abc import Iterable, Mapping
from dataclasses import astuple
from typing import Any, cast

import vobject  # type: ignore[import-untyped]

from calcard_mcp.errors import WriteVerificationError
from calcard_mcp.ical import EventSummary, RecurrenceRule
from calcard_mcp.vcard import project_label, project_type_label
from calcard_mcp.vtodo import TaskSummary

_BINARY_FIELDS: frozenset[str] = frozenset({"PHOTO", "LOGO", "SOUND", "KEY"})

# vobject has no py.typed and ships partially-annotated module-level helpers;
# rebind as Any so usages in this file don't trigger reportUnknownMemberType.
_vobject: Any = vobject


def _stringify(value: Any) -> str:
    """Convert a vobject property value into a comparable string.

    :param value: Property value as returned by :mod:`vobject` (a string, datetime,
        list, or other serialisable type).
    :type value: typing.Any
    :returns: Trimmed string representation suitable for equality checks.
    :rtype: str
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_stringify(item) for item in cast(list[Any], value))
    return str(value).strip()


def _extract(component: Any, field: str) -> str:
    """Extract a single property value from a vobject component.

    :param component: Parsed vobject component (a :class:`vobject.icalendar.VEvent`
        or :class:`vobject.vcard.VCard`).
    :type component: typing.Any
    :param field: Property name, case-insensitive (e.g. ``"SUMMARY"``, ``"FN"``).
    :type field: str
    :returns: The property value as a string, or an empty string when absent.
    :rtype: str
    """
    try:
        prop = component.contents.get(field.lower())
    except AttributeError:
        return ""
    if not prop:
        return ""
    if field.upper() in _BINARY_FIELDS:
        return _extract_binary(prop[0])
    return _stringify(prop[0].value)


def _extract_binary(prop: Any) -> str:
    """Project a binary property (PHOTO/LOGO/SOUND/KEY) to its canonical wire form.

    vobject decodes ``ENCODING=b`` properties to raw bytes; rendering those
    via :func:`_stringify` would yield ``b'...'`` and never match the
    ``data:<subtype>;base64,<payload>`` form produced by the builder. For
    inline binary values we re-encode the bytes and reconstruct the data URI
    using the ``TYPE`` parameter as the subtype, mirroring
    :func:`calcard_mcp.vcard._parse_binary_reference` and
    :func:`calcard_mcp.carddav_client._format_binary`.

    External-URI binary properties (``VALUE=URI``) compare against the raw
    URI string, so they fall through to the standard stringification.
    """
    encoding_param = getattr(prop, "encoding_param", "") or ""
    if isinstance(encoding_param, str) and encoding_param.lower() == "b":
        type_params: list[str] = list(prop.params.get("TYPE", []))
        subtype = type_params[0].split(",", 1)[0].strip().lower() if type_params else ""
        raw_value: Any = prop.value
        if isinstance(raw_value, bytes):
            payload = base64.b64encode(raw_value).decode("ascii")
        else:
            payload = str(raw_value).strip()
        return f"data:{subtype};base64,{payload}"
    return _stringify(prop.value)


def _iter_string_list_values(props: list[Any]) -> list[str]:
    values: list[str] = []
    for prop in props:
        raw_value = prop.value
        if isinstance(raw_value, list):
            pieces = [str(item) for item in cast(list[Any], raw_value)]
        else:
            pieces = str(raw_value).split(",")
        for piece in pieces:
            item = piece.replace("\\,", ",").strip()
            if item:
                values.append(item)
    return values


def _typed_field_actual(target: Any, field_lower: str) -> frozenset[tuple[str, ...]]:
    actual: set[tuple[str, ...]] = set()
    if field_lower in {"email", "tel"}:
        for prop in target.contents.get(field_lower, []):
            params: list[str] = list(prop.params.get("TYPE", []))
            actual.add((str(prop.value), project_type_label(params)))
        return frozenset(actual)
    if field_lower == "adr":
        for prop in target.contents.get("adr", []):
            params = list(prop.params.get("TYPE", []))
            actual.add(
                (
                    getattr(prop.value, "box", "") or "",
                    getattr(prop.value, "extended", "") or "",
                    getattr(prop.value, "street", "") or "",
                    getattr(prop.value, "city", "") or "",
                    getattr(prop.value, "region", "") or "",
                    getattr(prop.value, "code", "") or "",
                    getattr(prop.value, "country", "") or "",
                    project_label(params, ("work", "home")),
                )
            )
        return frozenset(actual)
    if field_lower in {"url", "impp"}:
        for prop in target.contents.get(field_lower, []):
            params = list(prop.params.get("TYPE", []))
            actual.add((str(prop.value), project_label(params, ("work", "home"))))
        return frozenset(actual)
    if field_lower == "related":
        allowed = (
            "spouse",
            "child",
            "parent",
            "sibling",
            "friend",
            "colleague",
            "manager",
            "assistant",
        )
        for prop in target.contents.get("related", []):
            params = list(prop.params.get("TYPE", []))
            actual.add((str(prop.value), project_label(params, allowed)))
        return frozenset(actual)
    if field_lower in {"lang", "member"}:
        for prop in target.contents.get(field_lower, []):
            actual.add((str(prop.value),))
        return frozenset(actual)
    if field_lower in {"nickname", "categories"}:
        values = _iter_string_list_values(target.contents.get(field_lower, []))
        return frozenset((value,) for value in values)
    return frozenset(actual)


def verify_fields(
    raw: str,
    *,
    component: str,
    expected: Mapping[str, str],
    expected_typed: Mapping[str, frozenset[tuple[str, ...]]] | None = None,
) -> None:
    """Assert that a stored iCal/vCard payload matches the expected field values.

    The function parses ``raw`` with :mod:`vobject`, walks to the named
    ``component`` (``VEVENT``, ``VTODO``, or ``VCARD``), and compares each
    ``expected`` key/value against the stored value. Mismatches are collected
    and raised as a single :class:`calcard_mcp.errors.WriteVerificationError`.

    Typed multi-valued comparison: ``expected_typed`` is keyed by lowercase
    component name (``"email"`` or ``"tel"``); each value is the expected
    ``frozenset`` of ``(value, type)`` tuples. The actual set is built by
    iterating the matching properties on the parsed component and projecting
    each ``TYPE=`` parameter list with
    :func:`calcard_mcp.vcard.project_type_label` — so an ``EMAIL;TYPE=fax``
    surfaces as ``(value, "other")``, mirroring the lossy read.

    :param raw: Raw iCalendar or vCard text as returned by the server after the write.
    :type raw: str
    :param component: vobject component name to inspect (``"VEVENT"``, ``"VCARD"``, ...).
    :type component: str
    :param expected: Mapping of property name to intended value.
    :type expected: collections.abc.Mapping[str, str]
    :param expected_typed: Optional typed multi-set comparison; key is lowercase
        component name (``"email"`` / ``"tel"``), value is the expected
        ``frozenset`` of ``(value, type)`` tuples.
    :type expected_typed: collections.abc.Mapping[str, frozenset[tuple[str, ...]]] | None
    :returns: None.
    :rtype: None
    :raises calcard_mcp.errors.WriteVerificationError: When any expected property
        is missing or has a value that differs from the intended value.
    """
    try:
        parsed: Any = _vobject.readOne(raw)
    except Exception as exc:  # vobject raises plain Exception on parse errors
        # Intentional remap: a server returning unparseable text in the
        # read-after-write step is a *verification* failure (the write may
        # have succeeded, but we cannot prove correctness), not a transport
        # ProtocolError. Do not "fix" this to ProtocolError — the caller
        # relies on WriteVerificationError to know the write reached the
        # server but field-level proof is missing.
        raise WriteVerificationError(
            f"could not parse server response as {component}: {exc}"
        ) from exc

    target: Any = parsed
    container_name = component.lower()
    if container_name != getattr(parsed, "name", "").lower():
        children: list[Any] = parsed.contents.get(container_name, [])
        if not children:
            raise WriteVerificationError(
                f"server response does not contain a {component} component"
            )
        target = children[0]

    diffs: list[tuple[str, str, str]] = []
    for field, intended in expected.items():
        actual = _extract(target, field)
        if _stringify(intended) != actual:
            diffs.append((field, _stringify(intended), actual))

    if expected_typed:
        for field_lower, expected_set in expected_typed.items():
            actual_set = _typed_field_actual(target, field_lower)
            if actual_set != expected_set:
                diffs.append(
                    (
                        field_lower.upper(),
                        _format_typed_set(expected_set),
                        _format_typed_set(actual_set),
                    )
                )

    if diffs:
        summary = "; ".join(
            f"{field}: intended={wanted!r} actual={got!r}" for field, wanted, got in diffs
        )
        raise WriteVerificationError(
            f"write verification failed for {component}: {summary}",
            field_diffs=diffs,
        )


def _format_typed_set(entries: frozenset[tuple[str, ...]]) -> str:
    """Render a typed multi-set as a stable, human-readable string for diffs."""
    return "{" + ", ".join(repr(tuple(entry)) for entry in sorted(entries)) + "}"


def verify_etag(
    *,
    pre_etag: str | None,
    post_etag: str | None,
) -> None:
    """Assert that a write produced a fresh ETag distinct from the pre-write ETag.

    This is the strict primitive. PRD 00001 §1.4's "best-effort when no
    pre-write ETag existed" tolerance is implemented at the call sites — see
    :meth:`calcard_mcp.caldav_client.CalDAVClient._verify_etag_with_fallback`
    and :meth:`calcard_mcp.carddav_client.CardDAVClient._resolve_post_etag` —
    which decline to invoke this function when ``post_etag`` is empty. Do
    not weaken the primitive itself; if you find a code path that needs to
    accept an empty post-ETag, that decision belongs in the caller.

    When ``pre_etag`` is :data:`None` (resource did not exist before the write),
    any non-empty ``post_etag`` is accepted. When both are present, they must
    differ. An absent ``post_etag`` always fails.

    :param pre_etag: ETag the client read immediately before the write, or :data:`None`
        when creating a new resource.
    :type pre_etag: str | None
    :param post_etag: ETag returned by the server after the write.
    :type post_etag: str | None
    :returns: None.
    :rtype: None
    :raises calcard_mcp.errors.WriteVerificationError: When ``post_etag`` is missing
        or unchanged from ``pre_etag``.
    """
    if not post_etag:
        raise WriteVerificationError("server did not return an ETag after the write")
    if pre_etag is not None and pre_etag == post_etag:
        raise WriteVerificationError(
            f"ETag did not change after write (pre=post={post_etag!r}); "
            "server may have ignored the update"
        )


def coerce_expected(pairs: Iterable[tuple[str, str | None]]) -> dict[str, str]:
    """Build an ``expected`` mapping from a series of optional ``(field, value)`` pairs.

    Pairs whose value is :data:`None` are dropped, so callers can pass through
    optional tool arguments without branching at every call site.

    :param pairs: Iterable of ``(field_name, intended_value_or_none)`` tuples.
    :type pairs: collections.abc.Iterable[tuple[str, str | None]]
    :returns: Dictionary containing only the pairs whose value was not :data:`None`.
    :rtype: dict[str, str]
    """
    return {field: value for field, value in pairs if value is not None}


# ---------------------------------------------------------------------------
# Typed-summary field comparison (EventSummary / TaskSummary)
# ---------------------------------------------------------------------------

# Plain string-list fields compared as case-sensitive frozensets.
_PLAIN_STRING_LIST_FIELDS: frozenset[str] = frozenset(
    {"resources", "comments", "contacts", "related_to"}
)

# Dataclass-shaped collection fields whose entries are flattened with
# ``dataclasses.astuple`` (recursive) before frozenset construction so the
# server-side ordering and parameter wire-shape can be compared cleanly.
_DATACLASS_COLLECTION_FIELDS: frozenset[str] = frozenset({"attendees", "alarms", "attachments"})

# Datetime-list collections compared as frozensets of ``datetime`` objects.
_DATETIME_LIST_FIELDS: frozenset[str] = frozenset({"exdates", "rdates"})

# Scalar fields compared with direct ``==``.
_SCALAR_FIELDS: frozenset[str] = frozenset(
    {"classification", "transparency", "url", "recurrence_id"}
)

# Dataclass scalar fields compared via ``dataclasses.astuple`` so :data:`None`
# vs :data:`None` is equal and a populated dataclass diffs cleanly.
_DATACLASS_SCALAR_FIELDS: frozenset[str] = frozenset({"geo", "organizer"})


def _categories_set(values: list[str]) -> frozenset[str]:
    """Case-fold a categories list into a frozenset for RFC-tolerant comparison."""
    return frozenset(value.casefold() for value in values)


def _hashable(value: Any) -> Any:
    """Recursively convert lists to tuples so a value can sit in a frozenset.

    ``dataclasses.astuple`` recurses into nested dataclasses but leaves any
    ``list`` fields as plain lists in the output tuple — those are not
    hashable, so a frozenset over astuple results would crash. This helper
    walks the result and converts every list to a tuple.
    """
    if isinstance(value, list):
        return tuple(_hashable(item) for item in cast(list[Any], value))
    if isinstance(value, tuple):
        return tuple(_hashable(item) for item in cast(tuple[Any, ...], value))
    return value


def _dataclass_collection_set(items: list[Any]) -> frozenset[Any]:
    """Flatten a list of (frozen) dataclasses into a comparable frozenset."""
    return frozenset(_hashable(astuple(item)) for item in items)


# RRULE keys that ``RecurrenceRule``'s structured fields can express. Keys
# outside this set live only in ``raw`` — a server modifying e.g. BYHOUR is
# invisible to a structured-only comparison, so raw inequality must win.
_STRUCTURED_RRULE_KEYS: frozenset[str] = frozenset(
    {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "BYSETPOS", "WKST"}
)


def _rrule_key_set(raw: str) -> frozenset[str]:
    """Extract uppercased keys from an RRULE wire string (``FREQ=...;BYDAY=...``)."""
    keys: set[str] = set()
    for part in raw.split(";"):
        key, sep, _ = part.partition("=")
        if sep:
            keys.add(key.strip().upper())
    return frozenset(keys)


def _recurrence_equal(intended: RecurrenceRule | None, actual: RecurrenceRule | None) -> bool:
    """Compare two :class:`RecurrenceRule` values per PRD §9.9 rules.

    Byte-identical ``raw`` is a sufficient fast-path. Otherwise fall through
    to structured-field comparison with ``by_day``, ``by_month_day``,
    ``by_month``, ``by_set_pos`` projected to sets so ``MO,FR`` matches
    ``FR,MO`` — server-side BYDAY reorder must not trip the verifier even
    when both parser-populated raws differ.

    The structured fall-through is gated by :data:`_STRUCTURED_RRULE_KEYS`:
    if either raw carries a key outside that set (BYHOUR / BYMINUTE /
    BYSECOND / BYWEEKNO / BYYEARDAY etc.), raw inequality wins so a
    server-side change to those keys surfaces as a diff. ``None`` vs
    ``None`` is equal; any one-sided ``None`` diffs.
    """
    if intended is None and actual is None:
        return True
    if intended is None or actual is None:
        return False
    if intended.raw and actual.raw and intended.raw == actual.raw:
        return True
    if intended.raw and actual.raw:
        combined_keys = _rrule_key_set(intended.raw) | _rrule_key_set(actual.raw)
        if not combined_keys.issubset(_STRUCTURED_RRULE_KEYS):
            return False
    return (
        intended.freq == actual.freq
        and intended.interval == actual.interval
        and intended.count == actual.count
        and intended.until == actual.until
        and frozenset(intended.by_day) == frozenset(actual.by_day)
        and frozenset(intended.by_month_day) == frozenset(actual.by_month_day)
        and frozenset(intended.by_month) == frozenset(actual.by_month)
        and frozenset(intended.by_set_pos) == frozenset(actual.by_set_pos)
        and intended.week_start == actual.week_start
    )


def _dataclass_scalar_tuple(value: Any) -> tuple[Any, ...] | None:
    """Project a (frozen) dataclass scalar to a tuple, preserving ``None``."""
    if value is None:
        return None
    return astuple(value)


def _summary_field_diff(
    intended: EventSummary | TaskSummary,
    actual: EventSummary | TaskSummary,
    field_name: str,
) -> tuple[str, str, str] | None:
    """Compute one ``(field, intended_repr, actual_repr)`` diff entry, or ``None``.

    Skips ``raw_properties`` per PRD §9.9: opaque round-trip is verified
    elsewhere by parse-mutate-serialise.
    """
    if field_name == "raw_properties":
        return None
    intended_value: Any = getattr(intended, field_name)
    actual_value: Any = getattr(actual, field_name)

    if field_name == "categories":
        intended_set = _categories_set(intended_value)
        actual_set = _categories_set(actual_value)
        if intended_set == actual_set:
            return None
        return (field_name, repr(sorted(intended_set)), repr(sorted(actual_set)))

    if field_name in _PLAIN_STRING_LIST_FIELDS:
        intended_set = frozenset(intended_value)
        actual_set = frozenset(actual_value)
        if intended_set == actual_set:
            return None
        return (field_name, repr(sorted(intended_set)), repr(sorted(actual_set)))

    if field_name in _DATACLASS_COLLECTION_FIELDS:
        intended_collection = _dataclass_collection_set(intended_value)
        actual_collection = _dataclass_collection_set(actual_value)
        if intended_collection == actual_collection:
            return None
        return (
            field_name,
            repr(sorted(intended_collection, key=repr)),
            repr(sorted(actual_collection, key=repr)),
        )

    if field_name in _DATETIME_LIST_FIELDS:
        intended_dt_set = frozenset(intended_value)
        actual_dt_set = frozenset(actual_value)
        if intended_dt_set == actual_dt_set:
            return None
        return (
            field_name,
            repr(sorted(intended_dt_set, key=lambda dt: dt.isoformat())),
            repr(sorted(actual_dt_set, key=lambda dt: dt.isoformat())),
        )

    if field_name == "recurrence":
        if _recurrence_equal(intended_value, actual_value):
            return None
        return (field_name, repr(intended_value), repr(actual_value))

    if field_name in _DATACLASS_SCALAR_FIELDS:
        intended_tuple = _dataclass_scalar_tuple(intended_value)
        actual_tuple = _dataclass_scalar_tuple(actual_value)
        if intended_tuple == actual_tuple:
            return None
        return (field_name, repr(intended_tuple), repr(actual_tuple))

    if field_name in _SCALAR_FIELDS:
        if intended_value == actual_value:
            return None
        return (field_name, repr(intended_value), repr(actual_value))

    raise ValueError(
        f"verify_summary_fields: unsupported field {field_name!r}; "
        "extend the comparison rules in verifier.py to include it"
    )


def verify_summary_fields(
    intended: EventSummary | TaskSummary,
    actual: EventSummary | TaskSummary,
    *,
    fields: Iterable[str],
) -> None:
    """Diff named fields on two parsed summaries and raise on any drift.

    Compares field-by-field per PRD §9.9 type-aware rules:

    * ``categories`` — case-folded ``frozenset`` (RFC-permitted server folding).
    * ``resources`` / ``comments`` / ``contacts`` / ``related_to`` —
      ``frozenset`` of strings.
    * ``attendees`` / ``alarms`` / ``attachments`` — ``frozenset`` of
      ``dataclasses.astuple(item)`` (recurses into nested dataclasses
      such as ``Alarm.attendees``).
    * ``exdates`` / ``rdates`` — ``frozenset`` of ``datetime`` values.
    * ``recurrence`` — byte-identical ``raw`` is the fast-path; otherwise
      structured-field comparison wins with ``by_day`` / ``by_month_day`` /
      ``by_month`` / ``by_set_pos`` projected to sets so server-side BYDAY
      reorder compares equal. Structured fall-through is gated: if either
      raw carries a key outside the structured projection (BYHOUR /
      BYMINUTE / BYSECOND / BYWEEKNO / BYYEARDAY etc.), raw inequality
      wins so server-side modification of those keys surfaces as a diff.
    * ``geo`` / ``organizer`` — ``dataclasses.astuple`` tuple equality;
      ``None`` vs ``None`` is equal.
    * ``recurrence_id`` / ``classification`` / ``transparency`` / ``url`` —
      direct equality.
    * ``raw_properties`` — skipped (opaque round-trip is verified by the
      parse-mutate-serialise path, not field-level diff).

    Read-back deltas (e.g. server strips ``RSVP=TRUE`` from an attendee)
    surface as a :class:`WriteVerificationError` with both halves of the
    diff visible in :attr:`WriteVerificationError.field_diffs`.

    :param intended: Summary built from the values the caller asked the
        server to store.
    :type intended: :class:`EventSummary` | :class:`TaskSummary`
    :param actual: Summary parsed from the post-write server response.
    :type actual: :class:`EventSummary` | :class:`TaskSummary`
    :param fields: Attribute names to compare; ``raw_properties`` entries
        are silently skipped per PRD §9.9.
    :type fields: collections.abc.Iterable[str]
    :returns: None.
    :rtype: None
    :raises WriteVerificationError: When any compared field differs.
    """
    diffs: list[tuple[str, str, str]] = []
    for field_name in fields:
        diff = _summary_field_diff(intended, actual, field_name)
        if diff is not None:
            diffs.append(diff)
    if diffs:
        summary = "; ".join(
            f"{field}: intended={wanted} actual={got}" for field, wanted, got in diffs
        )
        raise WriteVerificationError(
            f"summary verification failed: {summary}",
            field_diffs=diffs,
        )
