"""Pure vCard (de)serialisation helpers — no HTTP, no caldav library.

This module owns vCard byte-pushing: building vCards from field arguments,
parsing them back into :class:`ContactSummary`, and the in-place mutation
helpers (set/replace/clear) that the update flow drives. Errors raised here
are :class:`ValueError`. The transport layer in
:mod:`calcard_mcp.carddav_client` is responsible for wrapping these into
:class:`calcard_mcp.errors.ProtocolError` when the parse failure originated
from a server response.

Imports:

* :mod:`vobject` for vCard AST construction and parsing.
"""

from __future__ import annotations

import base64
import calendar
import re
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, cast

import vobject  # type: ignore[import-untyped]

from ._binary import BinaryReference, GeoCoordinates
from ._raw_props import encode_raw_property_value

# vobject ships no py.typed marker; rebinding as Any at the FFI boundary
# keeps call sites clean. The per-file ANN401 ignore in pyproject.toml
# documents that this is intentional.
_vobject: Any = vobject

__all__ = [
    "BinaryReference",
    "ContactSummary",
    "ContactValue",
    "Gender",
    "GeoCoordinates",
    "PartialDate",
    "PostalAddress",
    "Relation",
    "TypedURI",
    "apply_contact_clears",
    "build_vcard",
    "format_partial_date",
    "parse_vcard",
    "parse_vcard_to_summary",
    "project_label",
    "project_type_label",
    "replace_addresses",
    "replace_multi_typed",
    "replace_org",
    "replace_relations",
    "replace_string_lines",
    "replace_string_list",
    "replace_typed_uris",
    "serialize_vcard",
    "set_binary",
    "set_gender",
    "set_geo",
    "set_kind",
    "set_members",
    "set_partial_date",
    "set_single",
    "update_name",
]


_TYPE_PRECEDENCE: tuple[Literal["work", "home", "mobile"], ...] = (
    "work",
    "home",
    "mobile",
)
_URI_TYPE_PRECEDENCE: tuple[Literal["work", "home"], ...] = ("work", "home")
_RELATION_TYPE_PRECEDENCE: tuple[
    Literal["spouse", "child", "parent", "sibling", "friend", "colleague", "manager", "assistant"],
    ...,
] = (
    "spouse",
    "child",
    "parent",
    "sibling",
    "friend",
    "colleague",
    "manager",
    "assistant",
)
# `other` deliberately maps to no TYPE parameter on the wire (RFC 6350 §6.4.2
# allows absent TYPE; we preserve the spec's "no specific type" default).
_WIRE_TO_VCARD_TYPE: dict[str, str] = {
    "work": "WORK",
    "home": "HOME",
    "mobile": "CELL",
}
_FULL_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_PARTIAL_DATE_RE = re.compile(r"^--(\d{2})-(\d{2})$")
_PARTIAL_MONTH_RE = re.compile(r"^--(\d{2})$")
_YEAR_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
_YEAR_ONLY_RE = re.compile(r"^(\d{4})$")


@dataclass(frozen=True, slots=True)
class ContactValue:
    """Typed value paired with one of the four supported vCard TYPE labels.

    :cvar value: The bare email address or phone string.
    :vartype value: str
    :cvar type: Wire-form type label.
    :vartype type: typing.Literal["work", "home", "mobile", "other"]
    """

    value: str
    type: Literal["work", "home", "mobile", "other"]


@dataclass(frozen=True, slots=True)
class PostalAddress:
    """Typed postal address. RFC 6350 §6.3.1 ADR with the seven components.

    :cvar po_box: Post-office-box component.
    :vartype po_box: str
    :cvar extended: Extended-address component (e.g. apartment number).
    :vartype extended: str
    :cvar street: Street-address component.
    :vartype street: str
    :cvar locality: Locality (city) component.
    :vartype locality: str
    :cvar region: Region (state/province) component.
    :vartype region: str
    :cvar postal_code: Postal-code component.
    :vartype postal_code: str
    :cvar country: Country component.
    :vartype country: str
    :cvar type: Wire-form type label. ``other`` emits no ``TYPE`` parameter
        on the wire (RFC 6350 §6.3.1 default).
    :vartype type: typing.Literal["work", "home", "other"]
    """

    po_box: str = ""
    extended: str = ""
    street: str = ""
    locality: str = ""
    region: str = ""
    postal_code: str = ""
    country: str = ""
    type: Literal["work", "home", "other"] = "other"


@dataclass(frozen=True, slots=True)
class TypedURI:
    """Single-valued URI with a wire-form type label.

    Used for typed multi-valued URI properties — RFC 6350 §6.7.8 URL and
    §6.4.3 IMPP.

    :cvar value: The URI string.
    :vartype value: str
    :cvar type: Wire-form type label. ``other`` emits no ``TYPE`` parameter.
    :vartype type: typing.Literal["work", "home", "other"]
    """

    value: str
    type: Literal["work", "home", "other"] = "other"


@dataclass(frozen=True, slots=True)
class Relation:
    """RFC 6350 §6.6.6 RELATED. ``value`` is a URI or text label; ``type`` is the relationship.

    :cvar value: URI (e.g. ``urn:uuid:...``) or free text identifying the
        related entity.
    :vartype value: str
    :cvar type: Relationship label. ``other`` emits no ``TYPE`` parameter.
    :vartype type: typing.Literal["spouse", "child", "parent", "sibling",
        "friend", "colleague", "manager", "assistant", "other"]
    """

    value: str
    type: Literal[
        "spouse",
        "child",
        "parent",
        "sibling",
        "friend",
        "colleague",
        "manager",
        "assistant",
        "other",
    ] = "other"


@dataclass(frozen=True, slots=True)
class Gender:
    """RFC 6350 §6.2.7 GENDER.

    :cvar sex: One of ``M`` / ``F`` / ``O`` / ``N`` / ``U``, or empty
        when omitted.
    :vartype sex: typing.Literal["M", "F", "O", "N", "U", ""]
    :cvar identity: Free-text identity component; may be empty.
    :vartype identity: str
    """

    sex: Literal["M", "F", "O", "N", "U", ""] = ""
    identity: str = ""


@dataclass(frozen=True, slots=True)
class PartialDate:
    """RFC 6350 §4.3.1 partial-date value (used by BDAY / ANNIVERSARY).

    The vCard 4.0 form ``--MM-DD`` expresses a date with the year omitted;
    ``--MM`` omits both year and day. This dataclass uses ``0`` for any
    component that should be omitted on the wire.

    :cvar year: Four-digit year, or ``0`` when omitted.
    :vartype year: int
    :cvar month: Month 1-12, or ``0`` when omitted.
    :vartype month: int
    :cvar day: Day 1-31, or ``0`` when omitted.
    :vartype day: int
    """

    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        """Validate partial-date component ranges and combinations.

        Rejects out-of-range fields and semantically invalid combinations:
        a day with no month, and calendar-impossible day-of-month
        (e.g. ``Feb 31``, ``Apr 31``, ``Feb 29`` in a non-leap year). When the
        year is omitted (``year=0``), February day-of-month is checked against
        a leap year so ``--02-29`` is accepted.
        """
        if self.year < 0:
            raise ValueError(f"year {self.year!r} must be greater than or equal to 0")
        if self.month < 0 or self.month > 12:
            raise ValueError(f"month {self.month!r} must be between 0 and 12")
        if self.day < 0 or self.day > 31:
            raise ValueError(f"day {self.day!r} must be between 0 and 31")
        if self.day > 0 and self.month == 0:
            raise ValueError(
                f"day without month is not a valid partial date: "
                f"year={self.year}, month=0, day={self.day}"
            )
        if self.month > 0 and self.day > 0:
            year_for_calendar = self.year if self.year > 0 else 4
            max_day = calendar.monthrange(year_for_calendar, self.month)[1]
            if self.day > max_day:
                raise ValueError(
                    f"day-of-month is calendar-impossible: "
                    f"year={self.year}, month={self.month}, day={self.day} "
                    f"(max day for this month: {max_day})"
                )


def parse_vcard(text: str) -> Any:
    """Parse a vCard body and return the vobject AST.

    Use :func:`parse_vcard_to_summary` for the projected dataclass; this
    raw-AST variant is for callers who need to mutate the parsed card
    (e.g. the update flow) before serialising it back out.

    :param text: Raw vCard text.
    :type text: str
    :returns: vobject-parsed vCard component.
    :rtype: typing.Any
    :raises ValueError: When the body cannot be parsed by vobject.
    """
    try:
        return _vobject.readOne(text)
    except Exception as exc:
        raise ValueError(f"vCard body could not be parsed: {exc}") from exc


def _undo_property_escape_on_lines(text: str, prop: str, char: str) -> str:
    r"""Undo vobject's ``\<char>`` -> ``<char>`` escape on prefix-matched lines.

    Operates only on lines that begin with ``<prop>:`` (no parameters).

    vobject escapes commas inside NICKNAME values and semicolons inside
    GENDER/X-GENDER values; we want the wire form to carry the raw character
    instead so that callers see a single comma-joined NICKNAME line and the
    GENDER ``sex;identity`` separator survives. A naive global ``str.replace``
    risks corrupting other property lines that happen to contain the same
    substring (e.g. a NOTE that mentions ``NICKNAME:a\,b``). Anchoring the
    transform to lines starting with the property prefix eliminates that risk.

    Lines with parameters (e.g. ``NICKNAME;FOO=bar:value``) are left untouched
    -- vobject's escaping is the canonical wire form for parameterised lines.
    Original line endings are preserved.

    :param text: Serialised vCard text.
    :type text: str
    :param prop: Uppercased property name to match (e.g. ``"NICKNAME"``).
    :type prop: str
    :param char: The metacharacter whose ``\<char>`` form should be unescaped.
    :type char: str
    :returns: Text with the per-line unescape applied.
    :rtype: str
    """
    needle = f"{prop}:"
    escape_pat = f"\\{char}"
    return "".join(
        line.replace(escape_pat, char) if line.startswith(needle) else line
        for line in text.splitlines(keepends=True)
    )


def serialize_vcard(parsed: Any) -> str:
    """Serialise a vobject-parsed vCard back to text.

    :param parsed: vobject-parsed vCard component.
    :type parsed: typing.Any
    :returns: The serialised vCard as text.
    :rtype: str
    """
    serialised = str(parsed.serialize())
    if parsed.contents.get("nickname"):
        serialised = _undo_property_escape_on_lines(serialised, "NICKNAME", ",")
    if parsed.contents.get("x-gender"):
        serialised = _undo_property_escape_on_lines(serialised, "X-GENDER", ";")
    return serialised


@dataclass(frozen=True, slots=True)
class ContactSummary:
    """Projected view of a vCard.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar address_book_url: URL of the address book that holds this contact.
    :vartype address_book_url: str
    :cvar uid: vCard ``UID`` property.
    :vartype uid: str
    :cvar full_name: vCard ``FN`` property.
    :vartype full_name: str
    :cvar emails: Typed ``EMAIL`` entries.
    :vartype emails: list[ContactValue]
    :cvar phones: Typed ``TEL`` entries.
    :vartype phones: list[ContactValue]
    :cvar organization: Optional ``ORG`` value.
    :vartype organization: str
    :cvar title: Optional ``TITLE`` value.
    :vartype title: str
    :cvar note: Optional ``NOTE`` value.
    :vartype note: str
    :cvar url: Absolute URL of the vCard resource.
    :vartype url: str
    :cvar addresses: Typed postal ``ADR`` entries.
    :vartype addresses: list[PostalAddress]
    :cvar urls: Typed ``URL`` entries.
    :vartype urls: list[TypedURI]
    :cvar impps: Typed ``IMPP`` entries.
    :vartype impps: list[TypedURI]
    :cvar nicknames: ``NICKNAME`` entries.
    :vartype nicknames: list[str]
    :cvar categories: ``CATEGORIES`` entries.
    :vartype categories: list[str]
    :cvar relations: Typed ``RELATED`` entries.
    :vartype relations: list[Relation]
    :cvar languages: ``LANG`` entries.
    :vartype languages: list[str]
    :cvar timezone: Optional ``TZ`` value.
    :vartype timezone: str
    :cvar geo: Optional ``GEO`` coordinates.
    :vartype geo: GeoCoordinates | None
    :cvar role: Optional ``ROLE`` value.
    :vartype role: str
    :cvar kind: ``KIND`` value.
    :vartype kind: typing.Literal["individual", "group", "org", "location", ""]
    :cvar members: ``MEMBER`` entries.
    :vartype members: list[str]
    :cvar gender: Optional ``GENDER`` value.
    :vartype gender: Gender | None
    :cvar birthday: Optional ``BDAY`` partial date.
    :vartype birthday: PartialDate | None
    :cvar anniversary: Optional ``ANNIVERSARY`` partial date.
    :vartype anniversary: PartialDate | None
    :cvar photo: Optional ``PHOTO`` reference.
    :vartype photo: BinaryReference | None
    :cvar logo: Optional ``LOGO`` reference.
    :vartype logo: BinaryReference | None
    :cvar sound: Optional ``SOUND`` reference.
    :vartype sound: BinaryReference | None
    :cvar key: Optional ``KEY`` reference.
    :vartype key: BinaryReference | None
    :cvar raw_properties: Additional (non-typed) properties keyed by uppercased
        property name. Values are value-only segments: the ``NAME:`` prefix and
        trailing CRLF are stripped (e.g. ``X-CUSTOM-FIELD:opaque-value`` becomes
        ``"opaque-value"``). When a property carries parameters they are
        preserved as a leading ``;PARAM=VALUE[;PARAM=VALUE...]:`` prefix on the
        value (e.g. ``X-FOO;TYPE=BAR:value`` becomes ``";TYPE=BAR:value"``);
        parameterless properties have no leading ``;``.
    :vartype raw_properties: dict[str, list[str]]
    """

    account_id: str
    address_book_url: str
    uid: str
    full_name: str
    emails: list[ContactValue] = field(default_factory=list[ContactValue])
    phones: list[ContactValue] = field(default_factory=list[ContactValue])
    organization: str = ""
    title: str = ""
    note: str = ""
    url: str = ""
    addresses: list[PostalAddress] = field(default_factory=list[PostalAddress])
    urls: list[TypedURI] = field(default_factory=list[TypedURI])
    impps: list[TypedURI] = field(default_factory=list[TypedURI])
    nicknames: list[str] = field(default_factory=list[str])
    categories: list[str] = field(default_factory=list[str])
    relations: list[Relation] = field(default_factory=list[Relation])
    languages: list[str] = field(default_factory=list[str])
    timezone: str = ""
    geo: GeoCoordinates | None = None
    role: str = ""
    kind: Literal["individual", "group", "org", "location", ""] = ""
    members: list[str] = field(default_factory=list[str])
    gender: Gender | None = None
    birthday: PartialDate | None = None
    anniversary: PartialDate | None = None
    photo: BinaryReference | None = None
    logo: BinaryReference | None = None
    sound: BinaryReference | None = None
    key: BinaryReference | None = None
    raw_properties: dict[str, list[str]] = field(default_factory=dict[str, list[str]])


def project_label(params: list[str], allowed: tuple[str, ...]) -> str:
    """Project a list of vCard ``TYPE`` parameter values to a single wire-form label.

    Lowercases each entry, splits comma-joined parameter values into
    individual labels, and returns the first match in ``allowed`` precedence
    order. Returns ``"other"`` when no known label matches.

    :param params: Raw ``TYPE`` parameter values as returned by :mod:`vobject`.
    :type params: list[str]
    :param allowed: Precedence-ordered tuple of accepted lower-case labels.
    :type allowed: tuple[str, ...]
    :returns: First matching label, or ``"other"`` if none match.
    :rtype: str
    """
    # vobject can return multi-value TYPE parameters either pre-split
    # (``["WORK", "VOICE"]``) or as one comma-joined entry (``["WORK,VOICE"]``,
    # the quoted vCard 4.0 form). Splitting on commas locally is forgiving
    # of both shapes without relying on vobject internals.
    normalised: set[str] = set()
    for raw in params:
        for piece in raw.split(","):
            lower = piece.strip().lower()
            if lower:
                normalised.add(lower)
    for known in allowed:
        if known in normalised:
            return known
    return "other"


def project_type_label(params: list[str]) -> Literal["work", "home", "mobile", "other"]:
    """Project ``TYPE`` parameter values to an EMAIL/TEL wire-form type label.

    Wraps :func:`project_label` with EMAIL/TEL-specific normalisation:
    ``cell`` → ``mobile`` (vCard 3.0 spelling used by some legacy servers).
    Precedence is ``work > home > mobile``; absent matches yield ``other``.

    :param params: Raw ``TYPE`` parameter values as returned by :mod:`vobject`.
    :type params: list[str]
    :returns: Projected wire-form type label.
    :rtype: typing.Literal["work", "home", "mobile", "other"]
    """
    normalised_params: list[str] = []
    for raw in params:
        normalised_params.append(
            ",".join(
                "mobile" if piece.strip().lower() == "cell" else piece for piece in raw.split(",")
            )
        )
    label = project_label(normalised_params, _TYPE_PRECEDENCE)
    return cast(Literal["work", "home", "mobile", "other"], label)


def _project_uri_type_label(params: list[str]) -> Literal["work", "home", "other"]:
    return cast(
        Literal["work", "home", "other"],
        project_label(params, _URI_TYPE_PRECEDENCE),
    )


def _project_relation_type_label(
    params: list[str],
) -> Literal[
    "spouse",
    "child",
    "parent",
    "sibling",
    "friend",
    "colleague",
    "manager",
    "assistant",
    "other",
]:
    return cast(
        Literal[
            "spouse",
            "child",
            "parent",
            "sibling",
            "friend",
            "colleague",
            "manager",
            "assistant",
            "other",
        ],
        project_label(params, _RELATION_TYPE_PRECEDENCE),
    )


class _TypedEntry(Protocol):
    # Read-only attributes (declared via @property) so concrete dataclasses
    # whose ``type`` fields are narrower ``Literal[...]`` types satisfy the
    # protocol — mutable attribute declarations would be invariant.
    @property
    def value(self) -> str: ...
    @property
    def type(self) -> str: ...


def _emit_typed(card: Any, field_name: str, entry: _TypedEntry) -> None:
    """Append a typed multi-valued property to ``card`` (or any vobject parent).

    Emits a single ``TYPE=`` parameter for non-``other`` types; emits no
    ``TYPE`` for ``type='other'`` per RFC 6350's "absent means unspecified"
    default.
    """
    prop = card.add(field_name)
    prop.value = entry.value
    if entry.type != "other":
        prop.type_param = _WIRE_TO_VCARD_TYPE[entry.type]


_BINARY_DATA_URI_PATTERN = re.compile(
    r"^data:([^;,]*)((?:;[^;,]+)*);base64,(.+)$",
    flags=re.IGNORECASE,
)
_BINARY_ALLOWED_SCHEMES: tuple[str, ...] = ("data", "http", "https", "file")


def _emit_binary(card: Any, prop_name: str, ref: BinaryReference) -> None:
    lower_prop = prop_name.lower()
    value = ref.value
    if value.startswith("data:"):
        match = _BINARY_DATA_URI_PATTERN.match(value)
        if match is None:
            raise ValueError(
                f"malformed {lower_prop} data: URI: expected "
                "'data:<media-type>[;<param>=<value>]*;base64,<payload>'"
            )
        media_type, _extra_params, payload = match.groups()
        media_type = media_type or ref.media_type
        if not media_type:
            raise ValueError(
                f"{lower_prop} data: URI requires a media_type "
                "(either inline as 'data:<media>;base64,...' or via "
                "BinaryReference.media_type)"
            )
        try:
            base64.b64decode(payload, validate=True)
        except Exception as exc:
            raise ValueError(f"invalid base64 payload in {lower_prop} data URI") from exc
        prop = card.add(lower_prop)
        subtype = media_type.split("/", 1)[1] if "/" in media_type else media_type
        prop.value = payload
        prop.encoding_param = "b"
        if subtype:
            prop.type_param = subtype.upper()
        prop.encoded = True
        return
    if value.startswith(("http://", "https://", "file://")):
        prop = card.add(lower_prop)
        prop.value = value
        prop.value_param = "URI"
        return
    scheme = value.split(":", 1)[0].lower() if ":" in value else value.lower()
    raise ValueError(
        f"unsupported {lower_prop} URI scheme: {scheme}; "
        f"allowed: {', '.join(_BINARY_ALLOWED_SCHEMES)}"
    )


def build_vcard(
    *,
    uid: str,
    full_name: str,
    given_name: str | None,
    family_name: str | None,
    emails: list[ContactValue] | None,
    phones: list[ContactValue] | None,
    addresses: list[PostalAddress] | None = None,
    urls: list[TypedURI] | None = None,
    impps: list[TypedURI] | None = None,
    nicknames: list[str] | None = None,
    categories: list[str] | None = None,
    relations: list[Relation] | None = None,
    languages: list[str] | None = None,
    timezone: str | None = None,
    role: str | None = None,
    kind: Literal["individual", "group", "org", "location", ""] | None = None,
    geo: GeoCoordinates | None = None,
    gender: Gender | None = None,
    members: list[str] | None = None,
    birthday: PartialDate | None = None,
    anniversary: PartialDate | None = None,
    photo: BinaryReference | None = None,
    logo: BinaryReference | None = None,
    sound: BinaryReference | None = None,
    key: BinaryReference | None = None,
    organization: str | None,
    title: str | None,
    note: str | None,
) -> str:
    """Serialise a vCard 3.0 document from simple field arguments.

    :param uid: Unique identifier for the card.
    :type uid: str
    :param full_name: ``FN`` property.
    :type full_name: str
    :param given_name: Optional given name.
    :type given_name: str | None
    :param family_name: Optional family name.
    :type family_name: str | None
    :param emails: Optional list of typed ``EMAIL`` entries.
    :type emails: list[ContactValue] | None
    :param phones: Optional list of typed ``TEL`` entries.
    :type phones: list[ContactValue] | None
    :param addresses: Optional list of typed ``ADR`` entries.
    :type addresses: list[PostalAddress] | None
    :param urls: Optional list of typed ``URL`` entries.
    :type urls: list[TypedURI] | None
    :param impps: Optional list of typed ``IMPP`` entries.
    :type impps: list[TypedURI] | None
    :param nicknames: Optional ``NICKNAME`` entries.
    :type nicknames: list[str] | None
    :param categories: Optional ``CATEGORIES`` entries.
    :type categories: list[str] | None
    :param relations: Optional list of typed ``RELATED`` entries.
    :type relations: list[Relation] | None
    :param languages: Optional ``LANG`` entries.
    :type languages: list[str] | None
    :param timezone: Optional ``TZ`` value.
    :type timezone: str | None
    :param role: Optional ``ROLE`` value.
    :type role: str | None
    :param kind: Optional ``KIND`` value (emitted as ``X-ADDRESSBOOKSERVER-KIND`` on vCard 3.0).
    :type kind: typing.Literal["individual", "group", "org", "location", ""] | None
    :param geo: Optional ``GEO`` coordinates.
    :type geo: GeoCoordinates | None
    :param gender: Optional ``GENDER`` value (emitted as ``X-GENDER`` on vCard 3.0).
    :type gender: Gender | None
    :param members: Optional ``MEMBER`` values; valid only when ``kind="group"``.
    :type members: list[str] | None
    :param birthday: Optional ``BDAY`` partial date.
    :type birthday: PartialDate | None
    :param anniversary: Optional ``ANNIVERSARY`` partial date.
    :type anniversary: PartialDate | None
    :param photo: Optional ``PHOTO`` reference.
    :type photo: BinaryReference | None
    :param logo: Optional ``LOGO`` reference.
    :type logo: BinaryReference | None
    :param sound: Optional ``SOUND`` reference.
    :type sound: BinaryReference | None
    :param key: Optional ``KEY`` reference.
    :type key: BinaryReference | None
    :param organization: Optional ``ORG`` value.
    :type organization: str | None
    :param title: Optional ``TITLE`` value.
    :type title: str | None
    :param note: Optional ``NOTE`` value.
    :type note: str | None
    :returns: The serialised vCard as UTF-8 text.
    :rtype: str

    .. note::
       Structured-typed fields (``geo``, ``gender``, ``birthday``,
       ``anniversary``, ``photo``, ``logo``, ``sound``, ``key``) accept only
       ``None`` (omit / preserve on update) or a value instance (set). They
       have no "empty" representation: removal on the update path is via
       ``clear_fields`` (see :func:`apply_contact_clears`), not by passing
       an empty value here. Scalar string fields (``timezone``, ``role``)
       and list fields (``addresses``, ``urls``, ...) accept an empty string
       or empty list respectively to set the value to empty.
    """
    card: Any = _vobject.vCard()
    card.add("uid").value = uid
    card.add("fn").value = full_name
    name = card.add("n")
    name.value = _vobject.vcard.Name(
        family=family_name or "",
        given=given_name or "",
    )
    for entry in emails or []:
        _emit_typed(card, "email", entry)
    for entry in phones or []:
        _emit_typed(card, "tel", entry)
    for entry in addresses or []:
        prop = card.add("adr")
        prop.value = _vobject.vcard.Address(
            box=entry.po_box,
            extended=entry.extended,
            street=entry.street,
            city=entry.locality,
            region=entry.region,
            code=entry.postal_code,
            country=entry.country,
        )
        if entry.type != "other":
            prop.type_param = _WIRE_TO_VCARD_TYPE[entry.type]
    for entry in urls or []:
        _emit_typed(card, "url", entry)
    for entry in impps or []:
        _emit_typed(card, "impp", entry)
    # NICKNAME and CATEGORIES intentionally take different shapes here:
    # CATEGORIES is a vobject list-typed property (round-trips a Python
    # list cleanly: ``CATEGORIES:friend,colleague,family`` parses back as
    # ``prop.value=['friend','colleague','family']``).
    #
    # NICKNAME is asymmetric: vobject's serialiser rejects a list value
    # (calls ``str.replace`` on it), so the only way to assign multiple
    # values is via a comma-joined string. But its parser truncates the
    # roundtrip ``NICKNAME:Ali,Smith`` (unescaped comma) to the single
    # string ``"Ali"`` -- silently dropping every value past the first
    # comma. The user-facing read path (``parse_vcard_to_summary``) reads
    # raw text and is unaffected, but the write verifier walks vobject's
    # AST and false-positives on every multi-value NICKNAME write.
    #
    # Emitting one NICKNAME line per entry side-steps the vobject parser
    # quirk entirely. RFC 6350 §6.2.3 cardinality is "*" so multi-instance
    # NICKNAME lines are the canonical multi-value form.
    for nickname in nicknames or []:
        card.add("nickname").value = nickname
    if categories:
        card.add("categories").value = categories
    for entry in relations or []:
        prop = card.add("related")
        prop.value = entry.value
        if entry.type != "other":
            prop.type_param = entry.type.upper()
    for language in languages or []:
        card.add("lang").value = language
    if timezone:
        card.add("tz").value = timezone
    if role:
        card.add("role").value = role
    if kind not in (None, ""):
        card.add("x-addressbookserver-kind").value = kind
    if geo is not None:
        card.add("geo").value = f"{geo.latitude};{geo.longitude}"
    gender_joined = ""
    if gender is not None:
        gender_joined = f"{gender.sex};{gender.identity}"
        card.add("x-gender").value = gender_joined
    if members:
        if kind != "group":
            raise ValueError(
                f"members can only be set when kind='group'; got kind={kind!r} for members"
            )
        for member in members:
            card.add("member").value = member
    if birthday is not None:
        formatted_birthday = format_partial_date(birthday)
        if formatted_birthday is not None:
            card.add("bday").value = formatted_birthday
    if anniversary is not None:
        formatted_anniversary = format_partial_date(anniversary)
        if formatted_anniversary is not None:
            card.add("anniversary").value = formatted_anniversary
    if photo is not None:
        _emit_binary(card, "photo", photo)
    if logo is not None:
        _emit_binary(card, "logo", logo)
    if sound is not None:
        _emit_binary(card, "sound", sound)
    if key is not None:
        _emit_binary(card, "key", key)
    if organization:
        card.add("org").value = [organization]
    if title:
        card.add("title").value = title
    if note:
        card.add("note").value = note
    serialised = str(card.serialize())
    if nicknames:
        # vobject still escapes a literal comma inside an individual NICKNAME
        # value (e.g. ``nicknames=["Smith, Jr."]`` emits ``NICKNAME:Smith\, Jr.``).
        # Strip the escape to keep the wire form readable; the regular parser
        # handles both forms.
        serialised = _undo_property_escape_on_lines(serialised, "NICKNAME", ",")
    if gender_joined:
        serialised = _undo_property_escape_on_lines(serialised, "X-GENDER", ";")
    return serialised


def _unfold_vcard_lines(text: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.startswith((" ", "\t")):
            current += raw[1:]
            continue
        if current:
            lines.append(current)
        current = raw
    if current:
        lines.append(current)
    return lines


def _parse_list_string_values(text: str, property_name: str) -> list[str]:
    values: list[str] = []
    for line in _unfold_vcard_lines(text):
        upper = line.upper()
        prefix = f"{property_name.upper()}:"
        param_prefix = f"{property_name.upper()};"
        if not (upper.startswith(prefix) or upper.startswith(param_prefix)):
            continue
        if ":" not in line:
            continue
        raw_value = line.split(":", 1)[1]
        for item in raw_value.split(","):
            unescaped = item.replace("\\,", ",").strip()
            if unescaped:
                values.append(unescaped)
    return values


def format_partial_date(value: PartialDate) -> str | None:
    """Format a :class:`PartialDate` into the vCard wire string.

    Full dates emit ``YYYY-MM-DD``; year-omitted partials emit the vCard 4.0
    ``--MM-DD`` and ``--MM`` forms; year-only and year+month partials emit
    ``YYYY`` and ``YYYY-MM`` respectively. ``PartialDate(0, 0, 0)`` returns
    :data:`None` so callers can skip emission entirely.

    Unsupported combinations are rejected at construction by
    ``PartialDate.__post_init__``, so this function never raises.
    """
    year = value.year
    month = value.month
    day = value.day
    if year == 0 and month == 0 and day == 0:
        return None
    if year > 0 and month > 0 and day > 0:
        return f"{year:04d}-{month:02d}-{day:02d}"
    if year == 0 and month > 0 and day > 0:
        return f"--{month:02d}-{day:02d}"
    if year == 0 and month > 0 and day == 0:
        return f"--{month:02d}"
    if year > 0 and month > 0 and day == 0:
        return f"{year:04d}-{month:02d}"
    return f"{year:04d}"


def _parse_partial_date(raw_value: str) -> PartialDate | None:
    # Server vCards may carry calendar-impossible dates (e.g. ``BDAY:1990-02-31``
    # or ``BDAY:1990-02-29`` in a non-leap year). The regex passes; PartialDate's
    # ``__post_init__`` then rejects the combination. Mirror the GeoCoordinates
    # parser-fallback above and project unparseable dates to ``None`` so a
    # single bad contact does not crash ``list_contacts`` for the whole book.
    try:
        full_date = _FULL_DATE_RE.match(raw_value)
        if full_date:
            year, month, day = full_date.groups()
            return PartialDate(year=int(year), month=int(month), day=int(day))
        partial_date = _PARTIAL_DATE_RE.match(raw_value)
        if partial_date:
            month, day = partial_date.groups()
            return PartialDate(year=0, month=int(month), day=int(day))
        partial_month = _PARTIAL_MONTH_RE.match(raw_value)
        if partial_month:
            (month,) = partial_month.groups()
            return PartialDate(year=0, month=int(month), day=0)
        year_month = _YEAR_MONTH_RE.match(raw_value)
        if year_month:
            year, month = year_month.groups()
            return PartialDate(year=int(year), month=int(month), day=0)
        year_only = _YEAR_ONLY_RE.match(raw_value)
        if year_only:
            (year,) = year_only.groups()
            return PartialDate(year=int(year), month=0, day=0)
    except ValueError:
        return None
    return None


def _parse_binary_reference(props: list[Any]) -> BinaryReference | None:
    if not props:
        return None
    prop = props[0]
    encoding_params = [
        piece.strip().lower() for raw in prop.params.get("ENCODING", []) for piece in raw.split(",")
    ]
    if "b" in encoding_params:
        type_params = [
            piece.strip().lower() for raw in prop.params.get("TYPE", []) for piece in raw.split(",")
        ]
        media_type = type_params[0] if type_params else ""
        raw_value: Any = prop.value
        if isinstance(raw_value, bytes):
            payload = base64.b64encode(raw_value).decode("ascii")
        else:
            payload = str(raw_value)
        return BinaryReference(value=f"data:{media_type};base64,{payload}", media_type=media_type)
    value_params = [
        piece.strip().upper() for raw in prop.params.get("VALUE", []) for piece in raw.split(",")
    ]
    if "URI" in value_params:
        return BinaryReference(value=str(prop.value), media_type="")
    return None


def parse_vcard_to_summary(
    text: str,
    *,
    account_id: str,
    address_book_url: str,
    resource_url: str,
) -> ContactSummary | None:
    """Parse a vCard body into a :class:`ContactSummary`.

    Returns :data:`None` when the body is unparseable or when ``FN`` is
    absent (RFC 6350 requires ``FN``; cards without one are not useful
    contacts).

    Each ``EMAIL`` / ``TEL`` line is projected to a :class:`ContactValue`
    via :func:`project_type_label`, which collapses multi-``TYPE`` entries
    to a single wire-form label using the precedence
    ``work > home > mobile > other``. Unknown ``TYPE`` values surface as
    ``type='other'``; multi-TYPE entries collapse to the most-specific
    known match.

    :param text: Raw vCard text.
    :type text: str
    :param account_id: Owning account id.
    :type account_id: str
    :param address_book_url: URL of the owning address book.
    :type address_book_url: str
    :param resource_url: URL of the vCard resource.
    :type resource_url: str
    :returns: Projected summary, or :data:`None` on the failure modes above.
    :rtype: :class:`ContactSummary` | None
    """
    try:
        parsed: Any = _vobject.readOne(text)
    except Exception:
        return None
    fn_prop = getattr(parsed, "fn", None)
    if fn_prop is None:
        return None
    emails: list[ContactValue] = []
    for prop in parsed.contents.get("email", []):
        params: list[str] = list(prop.params.get("TYPE", []))
        emails.append(ContactValue(value=str(prop.value), type=project_type_label(params)))
    phones: list[ContactValue] = []
    for prop in parsed.contents.get("tel", []):
        params = list(prop.params.get("TYPE", []))
        phones.append(ContactValue(value=str(prop.value), type=project_type_label(params)))
    addresses: list[PostalAddress] = []
    for prop in parsed.contents.get("adr", []):
        params = list(prop.params.get("TYPE", []))
        addresses.append(
            PostalAddress(
                po_box=(getattr(prop.value, "box", "") or ""),
                extended=(getattr(prop.value, "extended", "") or ""),
                street=(getattr(prop.value, "street", "") or ""),
                locality=(getattr(prop.value, "city", "") or ""),
                region=(getattr(prop.value, "region", "") or ""),
                postal_code=(getattr(prop.value, "code", "") or ""),
                country=(getattr(prop.value, "country", "") or ""),
                type=_project_uri_type_label(params),
            )
        )
    urls: list[TypedURI] = []
    for prop in parsed.contents.get("url", []):
        params = list(prop.params.get("TYPE", []))
        urls.append(TypedURI(value=str(prop.value), type=_project_uri_type_label(params)))
    impps: list[TypedURI] = []
    for prop in parsed.contents.get("impp", []):
        params = list(prop.params.get("TYPE", []))
        impps.append(TypedURI(value=str(prop.value), type=_project_uri_type_label(params)))
    relations: list[Relation] = []
    for prop in parsed.contents.get("related", []):
        params = list(prop.params.get("TYPE", []))
        relations.append(Relation(value=str(prop.value), type=_project_relation_type_label(params)))
    nicknames = _parse_list_string_values(text, "NICKNAME")
    categories = _parse_list_string_values(text, "CATEGORIES")
    languages: list[str] = [str(prop.value) for prop in parsed.contents.get("lang", [])]
    tz_prop: list[Any] = parsed.contents.get("tz", [])
    role_prop: list[Any] = parsed.contents.get("role", [])
    kind_prop: list[Any] = parsed.contents.get("kind", [])
    x_kind_prop: list[Any] = parsed.contents.get("x-addressbookserver-kind", [])
    raw_kind = ""
    if kind_prop:
        raw_kind = str(kind_prop[0].value)
    elif x_kind_prop:
        raw_kind = str(x_kind_prop[0].value)
    # KIND values outside the typed enum (e.g. vCard 4.0 'application') fall
    # back to "" rather than smuggling a runtime-foreign string through the
    # Literal-typed dataclass field. Both KIND and X-ADDRESSBOOKSERVER-KIND
    # are also in excluded_raw_property_names, so unknown values do not appear
    # in raw_properties either; they are dropped from the projected summary.
    kind_value = raw_kind if raw_kind in ("individual", "group", "org", "location") else ""
    geo_value: GeoCoordinates | None = None
    geo_prop: list[Any] = parsed.contents.get("geo", [])
    if geo_prop:
        raw_geo = str(geo_prop[0].value)
        parts = raw_geo.split(";")
        if len(parts) == 2:
            try:
                geo_value = GeoCoordinates(latitude=float(parts[0]), longitude=float(parts[1]))
            except ValueError:
                geo_value = None
    members = [str(prop.value) for prop in parsed.contents.get("member", [])]
    gender_prop: list[Any] = parsed.contents.get("gender", [])
    x_gender_prop: list[Any] = parsed.contents.get("x-gender", [])
    parsed_gender: Gender | None = None
    if gender_prop or x_gender_prop:
        raw_gender = str((gender_prop or x_gender_prop)[0].value)
        sex, identity = [*raw_gender.split(";", 1), ""][:2]
        parsed_gender = Gender(
            sex=cast(Literal["M", "F", "O", "N", "U", ""], sex),
            identity=identity,
        )
    birthday_value: PartialDate | None = None
    bday_prop: list[Any] = parsed.contents.get("bday", [])
    if bday_prop:
        birthday_value = _parse_partial_date(str(bday_prop[0].value))
    anniversary_value: PartialDate | None = None
    anniversary_prop: list[Any] = parsed.contents.get("anniversary", [])
    if anniversary_prop:
        anniversary_value = _parse_partial_date(str(anniversary_prop[0].value))
    photo_value = _parse_binary_reference(parsed.contents.get("photo", []))
    logo_value = _parse_binary_reference(parsed.contents.get("logo", []))
    sound_value = _parse_binary_reference(parsed.contents.get("sound", []))
    key_value = _parse_binary_reference(parsed.contents.get("key", []))
    org_prop: list[Any] = parsed.contents.get("org", [])
    organization = ""
    if org_prop:
        value: Any = org_prop[0].value
        items = cast(list[Any], value if isinstance(value, list) else [value])
        organization = ", ".join(str(item) for item in items)
    title_prop: list[Any] = parsed.contents.get("title", [])
    note_prop: list[Any] = parsed.contents.get("note", [])
    uid_prop: list[Any] = parsed.contents.get("uid", [])
    excluded_raw_property_names = {
        "VERSION",
        "PRODID",
        "UID",
        "FN",
        "N",
        "EMAIL",
        "TEL",
        "ORG",
        "TITLE",
        "NOTE",
        "ADR",
        "URL",
        "IMPP",
        "NICKNAME",
        "CATEGORIES",
        "RELATED",
        "LANG",
        "TZ",
        "GEO",
        "ROLE",
        "KIND",
        "MEMBER",
        "GENDER",
        "BDAY",
        "ANNIVERSARY",
        "PHOTO",
        "LOGO",
        "SOUND",
        "KEY",
        "X-GENDER",
        "X-ADDRESSBOOKSERVER-KIND",
    }
    raw_properties: dict[str, list[str]] = {}
    for name, properties in parsed.contents.items():
        uppercase_name = str(name).upper()
        if uppercase_name in excluded_raw_property_names:
            continue
        for prop in properties:
            value = encode_raw_property_value(str(prop.value), prop.params)
            raw_properties.setdefault(uppercase_name, []).append(value)
    return ContactSummary(
        account_id=account_id,
        address_book_url=address_book_url,
        uid=str(uid_prop[0].value) if uid_prop else "",
        full_name=str(fn_prop.value),
        emails=emails,
        phones=phones,
        organization=organization,
        title=str(title_prop[0].value) if title_prop else "",
        note=str(note_prop[0].value) if note_prop else "",
        url=resource_url,
        addresses=addresses,
        urls=urls,
        impps=impps,
        nicknames=nicknames,
        categories=categories,
        relations=relations,
        languages=languages,
        timezone=str(tz_prop[0].value) if tz_prop else "",
        geo=geo_value,
        role=str(role_prop[0].value) if role_prop else "",
        kind=kind_value,
        members=members,
        gender=parsed_gender,
        birthday=birthday_value,
        anniversary=anniversary_value,
        photo=photo_value,
        logo=logo_value,
        sound=sound_value,
        key=key_value,
        raw_properties=raw_properties,
    )


def set_single(parsed: Any, field_name: str, value: str) -> None:
    """Replace the single-valued ``field_name`` property on ``parsed``.

    :param parsed: vobject-parsed vCard.
    :type parsed: typing.Any
    :param field_name: Lowercase vCard field name (``fn``, ``org``, ...).
    :type field_name: str
    :param value: Replacement value.
    :type value: str
    :returns: None. The function modifies ``parsed`` in place.
    :rtype: None
    """
    existing: list[Any] = parsed.contents.get(field_name, [])
    for item in list(existing):
        parsed.remove(item)
    parsed.add(field_name).value = value


def replace_org(parsed: Any, value: str) -> None:
    """Replace the ``ORG`` property with a single-component organization value.

    vCard ``ORG`` (RFC 6350 §6.6.4) is structurally an ordered list of
    components: organization name followed by zero or more organizational
    units. vobject reflects that by storing the value as a Python list. If
    a plain string is assigned to ``parsed.org.value``, vobject iterates
    the string and stores each character as a separate component — turning
    ``"Acme"`` into ``["A", "c", "m", "e"]`` on the wire and on read-back.

    This helper wraps the value in a single-element list to match
    :func:`build_vcard`'s create-path behaviour and avoid the iteration
    pitfall.

    :param parsed: vobject-parsed vCard component to mutate.
    :type parsed: typing.Any
    :param value: New organization name (single component; org units are
        not supported on the tool surface).
    :type value: str
    :returns: None. The function modifies ``parsed`` in place.
    :rtype: None
    """
    for item in list(parsed.contents.get("org", [])):
        parsed.remove(item)
    parsed.add("org").value = [value]


def replace_multi_typed(parsed: Any, field_name: str, values: list[ContactValue]) -> None:
    """Replace every instance of a typed multi-valued property on ``parsed``.

    Used for ``email`` and ``tel`` properties. Each emitted property carries a
    ``TYPE`` parameter for non-``other`` entries; ``other`` emits no ``TYPE``
    parameter (RFC 6350 §6.4.2 default).

    :param parsed: vobject-parsed vCard.
    :type parsed: typing.Any
    :param field_name: Lowercase vCard field name (``email`` or ``tel``).
    :type field_name: str
    :param values: New set of typed entries; an empty list removes the property.
    :type values: list[ContactValue]
    :returns: None. The function modifies ``parsed`` in place.
    :rtype: None
    """
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    for entry in values:
        _emit_typed(parsed, field_name, entry)


def replace_addresses(parsed: Any, addresses: list[PostalAddress]) -> None:
    """Replace every ``ADR`` property on ``parsed`` with ``addresses``."""
    for item in list(parsed.contents.get("adr", [])):
        parsed.remove(item)
    for entry in addresses:
        prop = parsed.add("adr")
        prop.value = _vobject.vcard.Address(
            box=entry.po_box,
            extended=entry.extended,
            street=entry.street,
            city=entry.locality,
            region=entry.region,
            code=entry.postal_code,
            country=entry.country,
        )
        if entry.type != "other":
            prop.type_param = _WIRE_TO_VCARD_TYPE[entry.type]


def replace_typed_uris(
    parsed: Any,
    field_name: Literal["url", "impp"],
    values: list[TypedURI],
) -> None:
    """Replace every typed ``URL``/``IMPP`` property on ``parsed``."""
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    for entry in values:
        _emit_typed(parsed, field_name, entry)


def replace_relations(parsed: Any, values: list[Relation]) -> None:
    """Replace every ``RELATED`` property on ``parsed``."""
    for item in list(parsed.contents.get("related", [])):
        parsed.remove(item)
    for entry in values:
        prop = parsed.add("related")
        prop.value = entry.value
        if entry.type != "other":
            prop.type_param = entry.type.upper()


def replace_string_list(parsed: Any, field_name: str, values: list[str]) -> None:
    """Replace a comma-or-multi-instance string list property.

    CATEGORIES round-trips a Python list through vobject natively. NICKNAME
    must use multi-instance lines (one property per value): vobject's
    parser silently truncates a comma-joined single-line ``NICKNAME:a,b``
    to the first segment ``"a"`` on read-back, breaking the verifier.
    See ``build_vcard``'s NICKNAME emission block for the full rationale.
    """
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    if not values:
        return
    if field_name == "categories":
        parsed.add(field_name).value = values
        return
    if field_name == "nickname":
        for value in values:
            parsed.add(field_name).value = value
        return
    parsed.add(field_name).value = ",".join(values)


def replace_string_lines(parsed: Any, field_name: str, values: list[str]) -> None:
    """Replace a multi-line list property where each item is one property line."""
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    for value in values:
        parsed.add(field_name).value = value


def set_partial_date(parsed: Any, field_name: str, value: PartialDate) -> None:
    """Replace a ``BDAY``/``ANNIVERSARY`` value using partial-date wire rules."""
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    formatted = format_partial_date(value)
    if formatted is not None:
        parsed.add(field_name).value = formatted


def set_binary(parsed: Any, field_name: str, ref: BinaryReference) -> None:
    """Replace a binary reference property using scheme-aware dispatch."""
    for item in list(parsed.contents.get(field_name, [])):
        parsed.remove(item)
    _emit_binary(parsed, field_name, ref)


def set_gender(parsed: Any, value: Gender) -> None:
    """Replace ``GENDER`` (vCard 3.0 fallback wire form: ``X-GENDER``)."""
    for item in list(parsed.contents.get("gender", [])):
        parsed.remove(item)
    for item in list(parsed.contents.get("x-gender", [])):
        parsed.remove(item)
    parsed.add("x-gender").value = f"{value.sex};{value.identity}"


def set_geo(parsed: Any, value: GeoCoordinates) -> None:
    """Replace ``GEO`` with ``<latitude>;<longitude>``."""
    for item in list(parsed.contents.get("geo", [])):
        parsed.remove(item)
    parsed.add("geo").value = f"{value.latitude};{value.longitude}"


def set_kind(parsed: Any, value: Literal["individual", "group", "org", "location", ""]) -> None:
    """Replace ``KIND`` (vCard 3.0 fallback wire form: ``X-ADDRESSBOOKSERVER-KIND``).

    Mirrors the ``build_vcard`` skip-on-empty behaviour: passing ``""`` removes
    any prior ``KIND`` / ``X-ADDRESSBOOKSERVER-KIND`` lines but does not emit
    a new empty-valued property.
    """
    for item in list(parsed.contents.get("kind", [])):
        parsed.remove(item)
    for item in list(parsed.contents.get("x-addressbookserver-kind", [])):
        parsed.remove(item)
    if value:
        parsed.add("x-addressbookserver-kind").value = value


def set_members(
    parsed: Any,
    values: list[str],
    kind: Literal["individual", "group", "org", "location", ""] | None,
) -> None:
    """Replace ``MEMBER`` values, enforcing ``kind='group'`` when non-empty."""
    for item in list(parsed.contents.get("member", [])):
        parsed.remove(item)
    if not values:
        return
    effective_kind = kind
    if effective_kind is None:
        kind_prop: list[Any] = parsed.contents.get("kind", [])
        x_kind_prop: list[Any] = parsed.contents.get("x-addressbookserver-kind", [])
        if kind_prop:
            effective_kind = cast(
                Literal["individual", "group", "org", "location", ""],
                str(kind_prop[0].value),
            )
        elif x_kind_prop:
            effective_kind = cast(
                Literal["individual", "group", "org", "location", ""], str(x_kind_prop[0].value)
            )
        else:
            effective_kind = ""
    if effective_kind != "group":
        raise ValueError(
            f"members can only be set when kind='group'; got kind={effective_kind!r} for members"
        )
    for value in values:
        parsed.add("member").value = value


def update_name(parsed: Any, given_name: str | None, family_name: str | None) -> None:
    """Update the ``N`` structured-name property in place on a parsed vCard.

    :param parsed: vobject-parsed vCard component.
    :type parsed: typing.Any
    :param given_name: New given name or :data:`None` to preserve.
    :type given_name: str | None
    :param family_name: New family name or :data:`None` to preserve.
    :type family_name: str | None
    :returns: None.
    :rtype: None
    """
    name_prop: Any = getattr(parsed, "n", None)
    if name_prop is None:
        name_prop = parsed.add("n")
        name_prop.value = _vobject.vcard.Name()
    if given_name is not None:
        name_prop.value.given = given_name
    if family_name is not None:
        name_prop.value.family = family_name


_CLEARABLE_CONTACT_FIELDS: dict[str, str | tuple[str, ...]] = {
    "addresses": "adr",
    "urls": "url",
    "impps": "impp",
    "nicknames": "nickname",
    "categories": "categories",
    "relations": "related",
    "languages": "lang",
    "members": "member",
    "photo": "photo",
    "logo": "logo",
    "sound": "sound",
    "key": "key",
    "gender": ("gender", "x-gender"),
    "birthday": "bday",
    "anniversary": "anniversary",
    "timezone": "tz",
    "geo": "geo",
    "role": "role",
    "kind": ("kind", "x-addressbookserver-kind"),
    "organization": "org",
    "title": "title",
    "note": "note",
}


def apply_contact_clears(parsed: Any, clear_fields: list[str]) -> None:
    """Remove vCard properties named in ``clear_fields`` from ``parsed`` in place.

    :param parsed: vobject-parsed vCard component to mutate.
    :type parsed: typing.Any
    :param clear_fields: Lowercase argument names; values outside
        :data:`_CLEARABLE_CONTACT_FIELDS` raise :class:`ValueError`.
    :type clear_fields: list[str]
    :returns: None.
    :rtype: None
    :raises ValueError: When any entry is not a valid clear_fields name.
    """
    for name in clear_fields:
        vcard_names = _CLEARABLE_CONTACT_FIELDS.get(name.lower())
        if vcard_names is None:
            raise ValueError(
                f"field {name!r} is not a valid clear_fields entry and cannot be cleared; "
                f"valid clear_fields: {sorted(_CLEARABLE_CONTACT_FIELDS)}"
            )
        field_names = (vcard_names,) if isinstance(vcard_names, str) else vcard_names
        for field_name in field_names:
            for item in list(parsed.contents.get(field_name, [])):
                parsed.remove(item)
