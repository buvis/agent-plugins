"""Multi-account CardDAV client built on :mod:`httpx`.

The upstream ``caldav`` library dropped CardDAV support in its 3.x line, so
this module implements the subset of RFC 6352 (CardDAV) calcard-mcp needs
directly:

* PROPFIND with Depth:1 for address-book discovery,
* PROPFIND with Depth:1 plus ``<C:address-data/>`` for contact listing,
* GET / PUT / DELETE for CRUD.

XML responses are parsed with :mod:`xml.etree.ElementTree`; the Python 3.12+
stdlib parser does not expand external entities, which is sufficient for
talking to a trusted home CardDAV server.

Pure vCard (de)serialisation lives in :mod:`calcard_mcp.vcard`; this module
owns transport, write verification flow, and PROPFIND/REPORT XML parsing only.

Imports:

* :mod:`logging` for diagnostics on stderr.
* :mod:`uuid` to mint fresh vCard ``UID`` values.
* :mod:`xml.etree.ElementTree` for CardDAV response parsing.
* :mod:`httpx` for synchronous HTTP with basic auth.
* :class:`calcard_mcp.accounts.ResolvedAccount` and
  :class:`calcard_mcp.accounts.AccountRegistry` for credential lookup.
* :class:`calcard_mcp.config.ServerConfig` for shared HTTP settings.
* :class:`calcard_mcp.errors.ProtocolError` for unexpected server responses.
* :mod:`calcard_mcp.vcard` for pure vCard (de)serialisation helpers.
* :func:`calcard_mcp.verifier.verify_fields` and
  :func:`calcard_mcp.verifier.verify_etag` for read-after-write checks.
"""

from __future__ import annotations

import logging
import re
import uuid
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal
from xml.sax.saxutils import escape as xml_escape

import httpx

from calcard_mcp.accounts import AccountRegistry, ResolvedAccount
from calcard_mcp.config import ServerConfig
from calcard_mcp.dav_client import DAVClientBase
from calcard_mcp.errors import ProtocolError, WriteVerificationError
from calcard_mcp.vcard import (
    BinaryReference,
    ContactSummary,
    ContactValue,
    Gender,
    GeoCoordinates,
    PartialDate,
    PostalAddress,
    Relation,
    TypedURI,
    apply_contact_clears,
    build_vcard,
    format_partial_date,
    parse_vcard,
    parse_vcard_to_summary,
    replace_addresses,
    replace_multi_typed,
    replace_org,
    replace_relations,
    replace_string_lines,
    replace_string_list,
    replace_typed_uris,
    serialize_vcard,
    set_binary,
    set_gender,
    set_geo,
    set_kind,
    set_members,
    set_partial_date,
    set_single,
    update_name,
)
from calcard_mcp.verifier import coerce_expected, verify_etag, verify_fields

__all__ = [
    "AddressBookSummary",
    "CardDAVClient",
    "ContactService",
    "ContactSummary",
    "ContactValue",
]

_LOG = logging.getLogger(__name__)

_DAV_NS = "DAV:"
_CARDDAV_NS = "urn:ietf:params:xml:ns:carddav"


def _build_expected_typed(
    emails: list[ContactValue] | None,
    phones: list[ContactValue] | None,
    addresses: list[PostalAddress] | None = None,
    urls: list[TypedURI] | None = None,
    impps: list[TypedURI] | None = None,
    relations: list[Relation] | None = None,
    languages: list[str] | None = None,
    members: list[str] | None = None,
    nicknames: list[str] | None = None,
    categories: list[str] | None = None,
) -> dict[str, frozenset[tuple[str, ...]]] | None:
    """Project optional typed write inputs into the verifier's ``expected_typed`` shape.

    Returns :data:`None` when neither input was supplied (caller must preserve
    the field), so the verifier does not assert any expectation about that
    field. An empty list (the clear path) maps to ``frozenset()``, which causes
    the verifier to fail if the server kept stale entries.
    """
    expected: dict[str, frozenset[tuple[str, ...]]] = {}
    if emails is not None:
        expected["email"] = frozenset((entry.value, entry.type) for entry in emails)
    if phones is not None:
        expected["tel"] = frozenset((entry.value, entry.type) for entry in phones)
    if addresses is not None:
        expected["adr"] = frozenset(
            (
                entry.po_box,
                entry.extended,
                entry.street,
                entry.locality,
                entry.region,
                entry.postal_code,
                entry.country,
                entry.type,
            )
            for entry in addresses
        )
    if urls is not None:
        expected["url"] = frozenset((entry.value, entry.type) for entry in urls)
    if impps is not None:
        expected["impp"] = frozenset((entry.value, entry.type) for entry in impps)
    if relations is not None:
        expected["related"] = frozenset((entry.value, entry.type) for entry in relations)
    if languages is not None:
        expected["lang"] = frozenset((entry,) for entry in languages)
    if members is not None:
        expected["member"] = frozenset((entry,) for entry in members)
    if nicknames is not None:
        expected["nickname"] = frozenset((entry,) for entry in nicknames)
    if categories is not None:
        expected["categories"] = frozenset((entry,) for entry in categories)
    return expected or None


def _format_geo(value: GeoCoordinates | None) -> str | None:
    if value is None:
        return None
    return f"{value.latitude};{value.longitude}"


def _format_gender(value: Gender | None) -> str | None:
    if value is None:
        return None
    return f"{value.sex};{value.identity}"


def _format_partial_date(value: PartialDate | None) -> str | None:
    """None-guarded thin wrapper around :func:`vcard.format_partial_date`."""
    if value is None:
        return None
    return format_partial_date(value)


def _format_binary(value: BinaryReference | None) -> str | None:
    """Project a :class:`BinaryReference` to a comparable wire-form string.

    The CardDAV write-verifier compares the user-supplied
    :class:`BinaryReference` against the value parsed back from the server.
    The server stores binary properties (PHOTO/LOGO/SOUND/KEY) in the vCard
    3.0 ``ENCODING=b;TYPE=<subtype>:<payload>`` inline form, which the
    parser's read projection canonicalises back to
    ``data:<subtype>;base64,<payload>`` (the media subtype only,
    e.g. ``wav`` not ``audio/wav``). This helper applies the same
    subtype-only canonicalisation to the user's input so the two strings can
    be compared directly. URI-form values (``http://``, ``https://``,
    ``file://``) are returned unchanged.

    Mirrors the canonicalisation rule in :func:`calcard_mcp.vcard._emit_binary`.

    :param value: The user-supplied binary reference, or ``None``.
    :type value: BinaryReference | None
    :returns: Canonical comparable string, or ``None`` when ``value`` is ``None``.
    :rtype: str | None
    """
    if value is None:
        return None
    data_match = re.match(
        r"^data:([^;,]*)(?:;[^;,]+)*;base64,(.+)$",
        value.value,
        flags=re.IGNORECASE,
    )
    if data_match is None:
        return value.value
    media_type, payload = data_match.groups()
    media_type = media_type or value.media_type
    subtype = media_type.split("/", 1)[1] if "/" in media_type else media_type
    canonical_media = subtype.lower()
    return f"data:{canonical_media};base64,{payload}"


@dataclass(frozen=True, slots=True)
class AddressBookSummary:
    """Lightweight description of an address book collection.

    :cvar account_id: Owning account id.
    :vartype account_id: str
    :cvar name: Human-readable address book name.
    :vartype name: str
    :cvar url: Absolute URL of the collection.
    :vartype url: str
    """

    account_id: str
    name: str
    url: str


class CardDAVClient(DAVClientBase):
    """Per-account CardDAV client with verified writes.

    :cvar account: Resolved account this client operates as.
    :vartype account: :class:`calcard_mcp.accounts.ResolvedAccount`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, account: ResolvedAccount, server: ServerConfig) -> None:
        """Build a CardDAV client for a single account.

        :param account: Account whose credentials drive every request.
        :type account: :class:`calcard_mcp.accounts.ResolvedAccount`
        :param server: Shared server configuration.
        :type server: :class:`calcard_mcp.config.ServerConfig`
        """
        super().__init__(account, server)
        self._http: httpx.Client = httpx.Client(
            auth=(account.config.username, account.password),
            verify=server.verify_tls,
            timeout=server.timeout,
            headers={"User-Agent": "calcard-mcp"},
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool.

        :returns: None.
        :rtype: None
        """
        self._http.close()

    @property
    def is_closed(self) -> bool:
        """Whether the underlying HTTP connection pool has been closed.

        :returns: ``True`` once :meth:`close` has been called (or the client
            was used as a context manager that exited), ``False`` otherwise.
        :rtype: bool
        """
        return bool(self._http.is_closed)

    def list_address_books(self) -> list[AddressBookSummary]:
        """List every address book owned by this account.

        :returns: Address book summaries in server order.
        :rtype: list[:class:`AddressBookSummary`]
        :raises calcard_mcp.errors.ProtocolError: When PROPFIND fails.
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">'
            "<D:prop>"
            "<D:resourcetype/>"
            "<D:displayname/>"
            "</D:prop>"
            "</D:propfind>"
        )
        raw = self._propfind(self._base_url, depth="1", body=body)
        summaries: list[AddressBookSummary] = []
        for href_elem, prop_elem in _iter_response_props(raw):
            resourcetype = prop_elem.find(f"{{{_DAV_NS}}}resourcetype")
            if resourcetype is None:
                continue
            if resourcetype.find(f"{{{_CARDDAV_NS}}}addressbook") is None:
                continue
            book_url = self._absolute(href_elem.text or "")
            displayname_elem = prop_elem.find(f"{{{_DAV_NS}}}displayname")
            name = (displayname_elem.text or "").strip() if displayname_elem is not None else ""
            if not name:
                name = book_url.rstrip("/").rsplit("/", 1)[-1]
            summaries.append(
                AddressBookSummary(account_id=self.account.id, name=name, url=book_url)
            )
        return summaries

    def list_contacts(self, address_book_url: str) -> list[ContactSummary]:
        """List every contact in ``address_book_url``.

        Tries the RFC 6352 §10.4 canonical path first
        (``addressbook-query`` REPORT with an empty filter), falling
        back to PROPFIND for servers that prefer that style. Radicale
        3.x serves vCard bodies only via REPORT — PROPFIND with
        ``<C:address-data/>`` returns the property in a 404 propstat —
        so REPORT is the necessary primary path.

        :param address_book_url: Absolute address book URL.
        :type address_book_url: str
        :returns: Contact summaries sorted by full name.
        :rtype: list[:class:`ContactSummary`]
        """
        report_summaries = self._list_contacts_via_report(address_book_url)
        if report_summaries is not None:
            return report_summaries

        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">'
            "<D:prop>"
            "<D:getetag/>"
            "<C:address-data/>"
            "</D:prop>"
            "</D:propfind>"
        )
        raw = self._propfind(address_book_url, depth="1", body=body)
        summaries: list[ContactSummary] = []
        for href_elem, prop_elem in _iter_response_props(raw):
            resource_url = self._absolute(href_elem.text or "")
            if resource_url.rstrip("/") == address_book_url.rstrip("/"):
                continue
            ad_elem = prop_elem.find(f"{{{_CARDDAV_NS}}}address-data")
            if ad_elem is None or not ad_elem.text:
                continue
            parsed = parse_vcard_to_summary(
                ad_elem.text,
                account_id=self.account.id,
                address_book_url=address_book_url,
                resource_url=resource_url,
            )
            if parsed is not None:
                summaries.append(parsed)
        summaries.sort(key=lambda contact: contact.full_name.casefold())
        return summaries

    def search_contacts(self, query: str) -> list[ContactSummary]:
        """Search every address book on this account for contacts matching ``query``.

        The match is a case-insensitive substring check against full name,
        every email, every phone, organization, title, and note.

        :param query: Substring to match.
        :type query: str
        :returns: Matching contacts, deduplicated by ``UID``.
        :rtype: list[:class:`ContactSummary`]
        """
        needle = query.strip().casefold()
        seen: set[str] = set()
        results: list[ContactSummary] = []
        for book in self.list_address_books():
            for contact in self.list_contacts(book.url):
                if contact.uid in seen:
                    continue
                haystack = " ".join(
                    [
                        contact.full_name,
                        contact.organization,
                        contact.title,
                        contact.note,
                        *(entry.value for entry in contact.emails),
                        *(entry.value for entry in contact.phones),
                    ]
                ).casefold()
                if needle in haystack:
                    results.append(contact)
                    seen.add(contact.uid)
        return results

    def create_contact(
        self,
        *,
        address_book_url: str,
        full_name: str,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: list[ContactValue] | None = None,
        phones: list[ContactValue] | None = None,
        addresses: list[PostalAddress] | None = None,
        urls: list[TypedURI] | None = None,
        impps: list[TypedURI] | None = None,
        nicknames: list[str] | None = None,
        categories: list[str] | None = None,
        relations: list[Relation] | None = None,
        languages: list[str] | None = None,
        timezone: str | None = None,
        geo: GeoCoordinates | None = None,
        role: str | None = None,
        kind: Literal["individual", "group", "org", "location", ""] | None = None,
        members: list[str] | None = None,
        gender: Gender | None = None,
        birthday: PartialDate | None = None,
        anniversary: PartialDate | None = None,
        photo: BinaryReference | None = None,
        logo: BinaryReference | None = None,
        sound: BinaryReference | None = None,
        key: BinaryReference | None = None,
        organization: str | None = None,
        title: str | None = None,
        note: str | None = None,
    ) -> ContactSummary:
        """Create a vCard in ``address_book_url`` and verify the server stored it.

        :param address_book_url: Target address book URL.
        :type address_book_url: str
        :param full_name: ``FN`` property (required by RFC 6350).
        :type full_name: str
        :param given_name: Optional ``N`` first-name component.
        :type given_name: str | None
        :param family_name: Optional ``N`` family-name component.
        :type family_name: str | None
        :param emails: Optional list of typed ``EMAIL`` entries; each entry's
            ``type`` must be ``"work"``, ``"home"``, ``"mobile"``, or ``"other"``.
        :type emails: list[:class:`ContactValue`] | None
        :param phones: Optional list of typed ``TEL`` entries.
        :type phones: list[:class:`ContactValue`] | None
        :param addresses: Optional typed ``ADR`` entries.
        :type addresses: list[:class:`PostalAddress`] | None
        :param urls: Optional typed ``URL`` entries.
        :type urls: list[:class:`TypedURI`] | None
        :param impps: Optional typed ``IMPP`` entries.
        :type impps: list[:class:`TypedURI`] | None
        :param nicknames: Optional ``NICKNAME`` entries.
        :type nicknames: list[str] | None
        :param categories: Optional ``CATEGORIES`` entries.
        :type categories: list[str] | None
        :param relations: Optional typed ``RELATED`` entries.
        :type relations: list[:class:`Relation`] | None
        :param languages: Optional ``LANG`` entries.
        :type languages: list[str] | None
        :param timezone: Optional ``TZ`` value.
        :type timezone: str | None
        :param geo: Optional ``GEO`` coordinates.
        :type geo: :class:`GeoCoordinates` | None
        :param role: Optional ``ROLE`` value.
        :type role: str | None
        :param kind: Optional ``KIND`` value (written as ``X-ADDRESSBOOKSERVER-KIND`` on vCard 3.0).
        :type kind: typing.Literal["individual", "group", "org", "location", ""] | None
        :param members: Optional ``MEMBER`` entries (valid with ``kind="group"``).
        :type members: list[str] | None
        :param gender: Optional ``GENDER`` value (written as ``X-GENDER`` on vCard 3.0).
        :type gender: :class:`Gender` | None
        :param birthday: Optional ``BDAY`` partial date.
        :type birthday: :class:`PartialDate` | None
        :param anniversary: Optional ``ANNIVERSARY`` partial date.
        :type anniversary: :class:`PartialDate` | None
        :param photo: Optional ``PHOTO`` URI/data reference.
        :type photo: :class:`BinaryReference` | None
        :param logo: Optional ``LOGO`` URI/data reference.
        :type logo: :class:`BinaryReference` | None
        :param sound: Optional ``SOUND`` URI/data reference.
        :type sound: :class:`BinaryReference` | None
        :param key: Optional ``KEY`` URI/data reference.
        :type key: :class:`BinaryReference` | None
        :param organization: Optional ``ORG`` value.
        :type organization: str | None
        :param title: Optional ``TITLE`` value.
        :type title: str | None
        :param note: Optional ``NOTE`` value.
        :type note: str | None
        :returns: Summary of the freshly created contact.
        :rtype: :class:`ContactSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When verification fails.
        :raises calcard_mcp.errors.ProtocolError: When the server refuses the write.
        """
        uid = f"{uuid.uuid4()}@calcard-mcp"
        body = build_vcard(
            uid=uid,
            full_name=full_name,
            given_name=given_name,
            family_name=family_name,
            emails=emails,
            phones=phones,
            addresses=addresses,
            urls=urls,
            impps=impps,
            nicknames=nicknames,
            categories=categories,
            relations=relations,
            languages=languages,
            timezone=timezone,
            geo=geo,
            role=role,
            kind=kind,
            members=members,
            gender=gender,
            birthday=birthday,
            anniversary=anniversary,
            photo=photo,
            logo=logo,
            sound=sound,
            key=key,
            organization=organization,
            title=title,
            note=note,
        )
        resource_url = f"{address_book_url.rstrip('/')}/{uid}.vcf"
        response = self._request(
            "PUT",
            resource_url,
            content=body,
            headers={
                "Content-Type": "text/vcard; charset=utf-8",
                "If-None-Match": "*",
            },
        )
        if response.status_code not in (200, 201, 204):
            raise ProtocolError(
                f"create_contact PUT failed for {self.account.id!r}: HTTP {response.status_code}"
            )

        if self.server.verify_writes:
            stored_text, get_etag = self._get_vcard_text_and_etag(resource_url)
            expected = coerce_expected(
                [
                    ("FN", full_name),
                    ("ORG", organization),
                    ("TITLE", title),
                    ("NOTE", note),
                    ("TZ", timezone),
                    ("ROLE", role),
                    ("X-ADDRESSBOOKSERVER-KIND", kind),
                    ("GEO", _format_geo(geo)),
                    ("X-GENDER", _format_gender(gender)),
                    ("BDAY", _format_partial_date(birthday)),
                    ("ANNIVERSARY", _format_partial_date(anniversary)),
                    ("PHOTO", _format_binary(photo)),
                    ("LOGO", _format_binary(logo)),
                    ("SOUND", _format_binary(sound)),
                    ("KEY", _format_binary(key)),
                ]
            )
            expected_typed = _build_expected_typed(
                emails,
                phones,
                addresses=addresses,
                urls=urls,
                impps=impps,
                relations=relations,
                languages=languages,
                members=members,
                nicknames=nicknames,
                categories=categories,
            )
            if expected or expected_typed:
                verify_fields(
                    stored_text,
                    component="VCARD",
                    expected=expected,
                    expected_typed=expected_typed,
                )
            post_etag = response.headers.get("etag") or get_etag
            if post_etag:
                verify_etag(pre_etag=None, post_etag=post_etag)
            else:
                _LOG.warning(
                    "server returned no ETag for %s; relying on field-level verification",
                    self.account.id,
                )

        summary = self._fetch_summary(resource_url, address_book_url)
        if summary is None:
            raise ProtocolError("server returned a vCard without a readable FN")
        return summary

    def update_contact(
        self,
        *,
        address_book_url: str,
        uid: str,
        full_name: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: list[ContactValue] | None = None,
        phones: list[ContactValue] | None = None,
        addresses: list[PostalAddress] | None = None,
        urls: list[TypedURI] | None = None,
        impps: list[TypedURI] | None = None,
        nicknames: list[str] | None = None,
        categories: list[str] | None = None,
        relations: list[Relation] | None = None,
        languages: list[str] | None = None,
        timezone: str | None = None,
        geo: GeoCoordinates | None = None,
        role: str | None = None,
        kind: Literal["individual", "group", "org", "location", ""] | None = None,
        members: list[str] | None = None,
        gender: Gender | None = None,
        birthday: PartialDate | None = None,
        anniversary: PartialDate | None = None,
        photo: BinaryReference | None = None,
        logo: BinaryReference | None = None,
        sound: BinaryReference | None = None,
        key: BinaryReference | None = None,
        organization: str | None = None,
        title: str | None = None,
        note: str | None = None,
        clear_fields: list[str] | None = None,
    ) -> ContactSummary:
        """Update fields on an existing vCard and verify the change round-tripped.

        Any argument left as :data:`None` is preserved. Passing an empty list for
        ``emails`` or ``phones`` clears those properties.

        :param address_book_url: Address book URL that holds the vCard.
        :type address_book_url: str
        :param uid: ``UID`` of the vCard to modify.
        :type uid: str
        :param full_name: New ``FN`` or :data:`None`.
        :type full_name: str | None
        :param given_name: New ``N`` first-name or :data:`None`.
        :type given_name: str | None
        :param family_name: New ``N`` family-name or :data:`None`.
        :type family_name: str | None
        :param emails: Replacement list of typed emails or :data:`None`. Each
            entry's ``type`` must be ``"work"``, ``"home"``, ``"mobile"``, or
            ``"other"``.
        :type emails: list[:class:`ContactValue`] | None
        :param phones: Replacement list of typed phones or :data:`None`.
        :type phones: list[:class:`ContactValue`] | None
        :param addresses: Replacement typed ``ADR`` entries or :data:`None`.
        :type addresses: list[:class:`PostalAddress`] | None
        :param urls: Replacement typed ``URL`` entries or :data:`None`.
        :type urls: list[:class:`TypedURI`] | None
        :param impps: Replacement typed ``IMPP`` entries or :data:`None`.
        :type impps: list[:class:`TypedURI`] | None
        :param nicknames: Replacement ``NICKNAME`` entries or :data:`None`.
        :type nicknames: list[str] | None
        :param categories: Replacement ``CATEGORIES`` entries or :data:`None`.
        :type categories: list[str] | None
        :param relations: Replacement typed ``RELATED`` entries or :data:`None`.
        :type relations: list[:class:`Relation`] | None
        :param languages: Replacement ``LANG`` entries or :data:`None`.
        :type languages: list[str] | None
        :param timezone: Replacement ``TZ`` value or :data:`None`.
        :type timezone: str | None
        :param geo: Replacement ``GEO`` coordinates or :data:`None`.
        :type geo: :class:`GeoCoordinates` | None
        :param role: Replacement ``ROLE`` value or :data:`None`.
        :type role: str | None
        :param kind: Replacement ``KIND`` value or :data:`None`.
        :type kind: typing.Literal["individual", "group", "org", "location", ""] | None
        :param members: Replacement ``MEMBER`` entries or :data:`None`.
        :type members: list[str] | None
        :param gender: Replacement ``GENDER`` value or :data:`None`.
        :type gender: :class:`Gender` | None
        :param birthday: Replacement ``BDAY`` partial date or :data:`None`.
        :type birthday: :class:`PartialDate` | None
        :param anniversary: Replacement ``ANNIVERSARY`` partial date or :data:`None`.
        :type anniversary: :class:`PartialDate` | None
        :param photo: Replacement ``PHOTO`` reference or :data:`None`.
        :type photo: :class:`BinaryReference` | None
        :param logo: Replacement ``LOGO`` reference or :data:`None`.
        :type logo: :class:`BinaryReference` | None
        :param sound: Replacement ``SOUND`` reference or :data:`None`.
        :type sound: :class:`BinaryReference` | None
        :param key: Replacement ``KEY`` reference or :data:`None`.
        :type key: :class:`BinaryReference` | None
        :param organization: New ``ORG`` or :data:`None`.
        :type organization: str | None
        :param title: New ``TITLE`` or :data:`None`.
        :type title: str | None
        :param note: New ``NOTE`` or :data:`None`.
        :type note: str | None
        :param clear_fields: Optional list of lowercase field names to remove
            from the vCard. Valid entries: ``"addresses"``, ``"urls"``,
            ``"impps"``, ``"nicknames"``, ``"categories"``, ``"relations"``,
            ``"languages"``, ``"members"``, ``"photo"``, ``"logo"``, ``"sound"``,
            ``"key"``, ``"gender"``, ``"birthday"``, ``"anniversary"``,
            ``"timezone"``, ``"geo"``, ``"role"``, ``"kind"``,
            ``"organization"``, ``"title"``, ``"note"``. ``"full_name"`` and
            the structured name are required by RFC 6350 and cannot be cleared
            — including them raises :class:`ValueError`. Clearing wins over
            any matching argument with the same name in the same call.
            ``raw_properties`` is read-only on the wire and is not accepted as
            an update parameter; unknown properties are preserved by parsing,
            mutating known fields, and re-serialising.
        :type clear_fields: list[str] | None
        :returns: Summary of the updated contact.
        :rtype: :class:`ContactSummary`
        :raises calcard_mcp.errors.WriteVerificationError: When verification fails.
        :raises calcard_mcp.errors.ProtocolError: When the contact cannot be found or saved,
            or when the server returns a vCard body that does not parse.
        """
        resource_url, pre_etag, body_text = self._find_by_uid(address_book_url, uid)
        try:
            parsed: Any = parse_vcard(body_text)
        except ValueError as exc:
            raise ProtocolError(
                f"server returned a vCard at {resource_url!r} that vobject could not parse"
            ) from exc

        if full_name is not None:
            set_single(parsed, "fn", full_name)
        if given_name is not None or family_name is not None:
            update_name(parsed, given_name, family_name)
        if emails is not None:
            replace_multi_typed(parsed, "email", emails)
        if phones is not None:
            replace_multi_typed(parsed, "tel", phones)
        if addresses is not None:
            replace_addresses(parsed, addresses)
        if urls is not None:
            replace_typed_uris(parsed, "url", urls)
        if impps is not None:
            replace_typed_uris(parsed, "impp", impps)
        if nicknames is not None:
            replace_string_list(parsed, "nickname", nicknames)
        if categories is not None:
            replace_string_list(parsed, "categories", categories)
        if relations is not None:
            replace_relations(parsed, relations)
        if languages is not None:
            replace_string_lines(parsed, "lang", languages)
        if timezone is not None:
            set_single(parsed, "tz", timezone)
        if geo is not None:
            set_geo(parsed, geo)
        if role is not None:
            set_single(parsed, "role", role)
        if kind is not None:
            set_kind(parsed, kind)
        if members is not None:
            set_members(parsed, members, kind)
        if gender is not None:
            set_gender(parsed, gender)
        if birthday is not None:
            set_partial_date(parsed, "bday", birthday)
        if anniversary is not None:
            set_partial_date(parsed, "anniversary", anniversary)
        if photo is not None:
            set_binary(parsed, "photo", photo)
        if logo is not None:
            set_binary(parsed, "logo", logo)
        if sound is not None:
            set_binary(parsed, "sound", sound)
        if key is not None:
            set_binary(parsed, "key", key)
        if organization is not None:
            replace_org(parsed, organization)
        if title is not None:
            set_single(parsed, "title", title)
        if note is not None:
            set_single(parsed, "note", note)

        # PRD 00001 §1.6: explicit clear wins over any also-provided value.
        if clear_fields:
            apply_contact_clears(parsed, clear_fields)

        # RFC 6350 §6.1.5: MEMBER is allowed only on KIND=group cards. The
        # build path enforces this in build_vcard; mirror the invariant here
        # so an update that flips kind away from "group" cannot leave behind
        # dangling MEMBER lines and emit an RFC-invalid card to the server.
        # Run after apply_contact_clears so clear_fields=['members'] is the
        # documented escape hatch for the group->non-group transition.
        post_kind_prop = parsed.contents.get("kind", []) or parsed.contents.get(
            "x-addressbookserver-kind", []
        )
        post_kind = str(post_kind_prop[0].value) if post_kind_prop else ""
        if parsed.contents.get("member") and post_kind != "group":
            raise ValueError(
                f"members can only be set when kind='group'; got kind={post_kind!r} for members"
            )

        new_body = serialize_vcard(parsed)
        headers = {"Content-Type": "text/vcard; charset=utf-8"}
        if pre_etag:
            headers["If-Match"] = pre_etag
        response = self._request("PUT", resource_url, content=new_body, headers=headers)
        if response.status_code not in (200, 201, 204):
            raise ProtocolError(
                f"update_contact PUT failed for {uid!r}: HTTP {response.status_code}"
            )

        if self.server.verify_writes:
            stored_text, get_etag = self._get_vcard_text_and_etag(resource_url)
            cleared = set(clear_fields or ())
            expected_field_values: list[tuple[str, str | None, str | None]] = [
                ("FN", full_name, None),
                ("ORG", organization, "organization"),
                ("TITLE", title, "title"),
                ("NOTE", note, "note"),
                ("TZ", timezone, "timezone"),
                ("ROLE", role, "role"),
                ("X-ADDRESSBOOKSERVER-KIND", kind, "kind"),
                ("GEO", _format_geo(geo), "geo"),
                ("X-GENDER", _format_gender(gender), "gender"),
                ("BDAY", _format_partial_date(birthday), "birthday"),
                ("ANNIVERSARY", _format_partial_date(anniversary), "anniversary"),
                ("PHOTO", _format_binary(photo), "photo"),
                ("LOGO", _format_binary(logo), "logo"),
                ("SOUND", _format_binary(sound), "sound"),
                ("KEY", _format_binary(key), "key"),
            ]
            expected = coerce_expected(
                [
                    (field_name, value)
                    for field_name, value, clear_name in expected_field_values
                    if clear_name is None or clear_name not in cleared
                ]
            )
            expected_typed = _build_expected_typed(
                emails,
                phones,
                addresses=addresses,
                urls=urls,
                impps=impps,
                relations=relations,
                languages=languages,
                members=members,
                nicknames=nicknames,
                categories=categories,
            )
            if expected_typed:
                typed_clear_map = {
                    "emails": "email",
                    "phones": "tel",
                    "addresses": "adr",
                    "urls": "url",
                    "impps": "impp",
                    "relations": "related",
                    "languages": "lang",
                    "members": "member",
                    "nicknames": "nickname",
                    "categories": "categories",
                }
                expected_typed = {
                    key: value
                    for key, value in expected_typed.items()
                    if key
                    not in {typed_clear_map[name] for name in cleared if name in typed_clear_map}
                } or None
            post_etag = response.headers.get("etag") or get_etag
            if expected or expected_typed:
                # PRD 00010 §10.8 diagnostic context (UID, ETag pair) — embed
                # at the call site rather than threading through verify_fields.
                try:
                    verify_fields(
                        stored_text,
                        component="VCARD",
                        expected=expected,
                        expected_typed=expected_typed,
                    )
                except WriteVerificationError as exc:
                    raise WriteVerificationError(
                        f"{exc} (uid={uid!r}, pre_etag={pre_etag!r}, post_etag={post_etag!r})",
                        field_diffs=exc.field_diffs,
                    ) from exc
            if post_etag:
                try:
                    verify_etag(pre_etag=pre_etag, post_etag=post_etag)
                except WriteVerificationError as exc:
                    raise WriteVerificationError(
                        f"{exc} (uid={uid!r}, pre_etag={pre_etag!r}, post_etag={post_etag!r})",
                        field_diffs=exc.field_diffs,
                    ) from exc
            else:
                _LOG.warning(
                    "server returned no ETag for %s; relying on field-level verification",
                    self.account.id,
                )

        summary = self._fetch_summary(resource_url, address_book_url)
        if summary is None:
            raise ProtocolError("server returned a vCard without a readable FN")
        return summary

    def delete_contact(self, *, address_book_url: str, uid: str) -> None:
        """Delete the vCard with ``uid`` from ``address_book_url`` and verify absence.

        :param address_book_url: Address book URL that holds the vCard.
        :type address_book_url: str
        :param uid: ``UID`` of the vCard to remove.
        :type uid: str
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.ProtocolError: When the delete fails or the vCard
            is still reachable afterwards.
        """
        resource_url, pre_etag, _body = self._find_by_uid(address_book_url, uid)
        headers: dict[str, str] = {}
        if pre_etag:
            headers["If-Match"] = pre_etag
        response = self._request("DELETE", resource_url, headers=headers)
        if response.status_code not in (200, 202, 204, 404):
            raise ProtocolError(f"delete_contact failed for {uid!r}: HTTP {response.status_code}")

        if self.server.verify_writes:
            check = self._request("GET", resource_url)
            if check.status_code < 400:
                raise ProtocolError(
                    f"contact {uid!r} still present after delete on {self.account.id!r}"
                )

    def _propfind(self, url: str, *, depth: str, body: str) -> bytes:
        """Issue a PROPFIND and return the raw 207 Multi-Status body.

        :param url: Target URL.
        :type url: str
        :param depth: ``Depth`` header value (``"0"`` or ``"1"``).
        :type depth: str
        :param body: PROPFIND request XML body.
        :type body: str
        :returns: Raw XML response bytes.
        :rtype: bytes
        :raises calcard_mcp.errors.ProtocolError: When the response is not 207.
        """
        response = self._request(
            "PROPFIND",
            url,
            content=body,
            headers={
                "Depth": depth,
                "Content-Type": "application/xml; charset=utf-8",
            },
        )
        if response.status_code != 207:
            raise ProtocolError(f"PROPFIND {url!r} returned HTTP {response.status_code}")
        return response.content

    def _request(
        self,
        method: str,
        url: str,
        *,
        content: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Wrap ``httpx.Client.request`` with uniform error translation.

        :param method: HTTP method name.
        :type method: str
        :param url: Absolute URL.
        :type url: str
        :param content: Optional request body.
        :type content: str | None
        :param headers: Optional request headers.
        :type headers: dict[str, str] | None
        :returns: The :class:`httpx.Response`.
        :rtype: :class:`httpx.Response`
        :raises calcard_mcp.errors.ProtocolError: On transport-level failures.
        """
        try:
            return self._http.request(method, url, content=content, headers=headers)
        except httpx.HTTPError as exc:
            raise ProtocolError(
                f"CardDAV {method} {url!r} failed for {self.account.id!r}: {exc}"
            ) from exc

    def _absolute(self, href: str) -> str:
        """Expand an href returned by the server into an absolute URL.

        :param href: ``D:href`` value from a PROPFIND response.
        :type href: str
        :returns: Absolute URL reachable by :attr:`_http`.
        :rtype: str
        """
        if href.startswith("http://") or href.startswith("https://"):
            return href
        if not href.startswith("/"):
            href = f"/{href}"
        return f"{self.server.base_url}{href}"

    def _get_vcard_text(self, resource_url: str) -> str:
        """GET a vCard resource and return its body text.

        :param resource_url: Absolute URL of a ``.vcf`` resource.
        :type resource_url: str
        :returns: Decoded response body.
        :rtype: str
        :raises calcard_mcp.errors.ProtocolError: On non-200 responses.
        """
        text, _ = self._get_vcard_text_and_etag(resource_url)
        return text

    def _get_vcard_text_and_etag(self, resource_url: str) -> tuple[str, str | None]:
        """GET a vCard resource and return its body text plus the response ``ETag``.

        Used by the post-write verification path so a single GET supplies
        both the body for :func:`verify_fields` and the ``ETag`` header for
        :func:`verify_etag`, replacing the previous two-GET pattern.

        :param resource_url: Absolute URL of a ``.vcf`` resource.
        :type resource_url: str
        :returns: ``(body_text, etag_or_none)``.
        :rtype: tuple[str, str | None]
        :raises calcard_mcp.errors.ProtocolError: On non-200 responses.
        """
        response = self._request("GET", resource_url)
        if response.status_code != 200:
            raise ProtocolError(f"GET {resource_url!r} returned HTTP {response.status_code}")
        return response.text, response.headers.get("etag") or None

    def _find_by_uid(self, address_book_url: str, uid: str) -> tuple[str, str | None, str]:
        """Locate the href, current ETag, and body of the vCard with ``uid``.

        Prefers RFC 6352 §8.6 ``addressbook-query`` REPORT with a UID
        prop-filter so the server can return only the matching vCard
        (single round-trip instead of a full-book scan). Falls back to
        ``PROPFIND Depth: 1`` + client-side UID match for servers that do
        not implement REPORT (older Radicale builds, some Baikal configs)
        or that respond with anything other than 207 to the REPORT.

        Both code paths request ``<C:address-data/>`` so the matching
        vCard body comes back in the multistatus response — the body is
        threaded through as the third return value to avoid a redundant
        GET on top of the lookup.

        :param address_book_url: Address book URL to search.
        :type address_book_url: str
        :param uid: ``UID`` of the vCard.
        :type uid: str
        :returns: ``(resource_url, etag_or_none, body_text)`` for the matching vCard.
        :rtype: tuple[str, str | None, str]
        :raises calcard_mcp.errors.ProtocolError: When no vCard matches ``uid``
            via either path.
        """
        fast = self._addressbook_query_by_uid(address_book_url, uid)
        if fast is not None:
            return fast
        return self._propfind_scan_by_uid(address_book_url, uid)

    def _list_contacts_via_report(self, address_book_url: str) -> list[ContactSummary] | None:
        """List every contact via RFC 6352 §10.4 ``addressbook-query`` REPORT.

        Returns :data:`None` when the server does not honor the REPORT
        (non-207 status, malformed body) so the caller can fall back to
        PROPFIND. An empty 207 multistatus is a valid "no contacts in
        this book" response — returns ``[]`` in that case.

        :param address_book_url: Address book URL to enumerate.
        :type address_book_url: str
        :returns: Sorted contact summaries on success, :data:`None`
            when the server's REPORT response is unusable.
        :rtype: list[:class:`ContactSummary`] | None
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<C:addressbook-query xmlns:D="DAV:" '
            'xmlns:C="urn:ietf:params:xml:ns:carddav">'
            "<D:prop><D:getetag/><C:address-data/></D:prop>"
            "<C:filter/>"
            "</C:addressbook-query>"
        )
        response = self._request(
            "REPORT",
            address_book_url,
            content=body,
            headers={
                "Depth": "1",
                "Content-Type": "application/xml; charset=utf-8",
            },
        )
        if response.status_code != 207:
            _LOG.debug(
                "addressbook-query REPORT not honored on %s (HTTP %s); falling back to PROPFIND",
                address_book_url,
                response.status_code,
            )
            return None
        try:
            iter_props = list(_iter_response_props(response.content))
        except ProtocolError as exc:
            _LOG.warning(
                "addressbook-query REPORT on %s returned 207 with malformed body; "
                "falling back to PROPFIND: %s",
                address_book_url,
                exc,
            )
            return None
        summaries: list[ContactSummary] = []
        for href_elem, prop_elem in iter_props:
            resource_url = self._absolute(href_elem.text or "")
            if resource_url.rstrip("/") == address_book_url.rstrip("/"):
                continue
            ad_elem = prop_elem.find(f"{{{_CARDDAV_NS}}}address-data")
            if ad_elem is None or not ad_elem.text:
                continue
            parsed = parse_vcard_to_summary(
                ad_elem.text,
                account_id=self.account.id,
                address_book_url=address_book_url,
                resource_url=resource_url,
            )
            if parsed is not None:
                summaries.append(parsed)
        summaries.sort(key=lambda contact: contact.full_name.casefold())
        return summaries

    def _addressbook_query_by_uid(
        self, address_book_url: str, uid: str
    ) -> tuple[str, str | None, str] | None:
        """Issue an addressbook-query REPORT filtered on UID.

        Returns :data:`None` when the server responds with anything other
        than 207, when the 207 contains zero matching responses, or when
        the matching response's vCard parses but its UID does not equal
        ``uid`` exactly. ``None`` triggers the PROPFIND fallback in the
        caller; we cannot distinguish "server doesn't understand REPORT"
        from "server understood, found nothing" with full confidence.

        :param address_book_url: Address book URL to query.
        :type address_book_url: str
        :param uid: ``UID`` to match.
        :type uid: str
        :returns: ``(resource_url, etag_or_none, body_text)`` on a confident
            match, or :data:`None` to defer to the PROPFIND scan.
        :rtype: tuple[str, str | None, str] | None
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<C:addressbook-query xmlns:D="DAV:" '
            'xmlns:C="urn:ietf:params:xml:ns:carddav">'
            "<D:prop><D:getetag/><C:address-data/></D:prop>"
            "<C:filter>"
            '<C:prop-filter name="UID">'
            '<C:text-match collation="i;octet" match-type="equals">'
            f"{xml_escape(uid)}</C:text-match>"
            "</C:prop-filter>"
            "</C:filter>"
            "</C:addressbook-query>"
        )
        response = self._request(
            "REPORT",
            address_book_url,
            content=body,
            headers={
                "Depth": "1",
                "Content-Type": "application/xml; charset=utf-8",
            },
        )
        if response.status_code != 207:
            _LOG.debug(
                "addressbook-query REPORT not supported on %s (HTTP %s); "
                "falling back to PROPFIND scan",
                address_book_url,
                response.status_code,
            )
            return None
        try:
            iter_props = _iter_response_props(response.content)
        except ProtocolError as exc:
            # The server returned 207 (claiming a multistatus body) but the
            # body itself is malformed. That's a server-side bug, not a
            # missing feature — we still fall back to PROPFIND so the user's
            # operation succeeds, but log at WARNING so operators see the
            # broken-REPORT signal instead of a silent fallback.
            _LOG.warning(
                "addressbook-query REPORT on %s returned 207 with malformed body; "
                "falling back to PROPFIND scan: %s",
                address_book_url,
                exc,
            )
            return None
        return _match_uid_in_responses(
            iter_props,
            address_book_url=address_book_url,
            uid=uid,
            absolute=self._absolute,
        )

    def _propfind_scan_by_uid(self, address_book_url: str, uid: str) -> tuple[str, str | None, str]:
        """Walk every vCard in the book via PROPFIND, looking for ``uid``.

        Used when the REPORT fast path returns :data:`None`. This matches
        the pre-2.4 behaviour exactly so servers that lack REPORT support
        keep working unchanged.

        :param address_book_url: Address book URL to scan.
        :type address_book_url: str
        :param uid: ``UID`` to match.
        :type uid: str
        :returns: ``(resource_url, etag_or_none, body_text)`` for the matching vCard.
        :rtype: tuple[str, str | None, str]
        :raises calcard_mcp.errors.ProtocolError: When no vCard matches ``uid``.
        """
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">'
            "<D:prop>"
            "<D:getetag/>"
            "<C:address-data/>"
            "</D:prop>"
            "</D:propfind>"
        )
        raw = self._propfind(address_book_url, depth="1", body=body)
        match = _match_uid_in_responses(
            _iter_response_props(raw),
            address_book_url=address_book_url,
            uid=uid,
            absolute=self._absolute,
        )
        if match is None:
            raise ProtocolError(f"contact {uid!r} not found in address book {address_book_url!r}")
        return match

    def _fetch_summary(
        self,
        resource_url: str,
        address_book_url: str,
    ) -> ContactSummary | None:
        """GET a vCard and project it into a :class:`ContactSummary`.

        :param resource_url: vCard URL.
        :type resource_url: str
        :param address_book_url: Owning address book URL.
        :type address_book_url: str
        :returns: Projected summary, or :data:`None` when parsing fails.
        :rtype: :class:`ContactSummary` | None
        """
        body_text = self._get_vcard_text(resource_url)
        return parse_vcard_to_summary(
            body_text,
            account_id=self.account.id,
            address_book_url=address_book_url,
            resource_url=resource_url,
        )


def _iter_response_props(
    multistatus_bytes: bytes,
) -> list[tuple[ET.Element, ET.Element]]:
    """Iterate ``(href, prop)`` pairs from a 207 Multi-Status XML body.

    Only HTTP 200 ``propstat`` entries contribute properties; 4xx / 5xx blocks
    are skipped so callers see exactly the properties the server could return.
    When a server splits successful properties across multiple 200 ``propstat``
    blocks within a single response, every child of every 200 block is merged
    into one synthetic ``prop`` element so callers do not silently lose data.

    :param multistatus_bytes: Raw XML bytes from a PROPFIND 207 response.
    :type multistatus_bytes: bytes
    :returns: List of ``(href_element, merged_prop_element)`` tuples, one per
        ``D:response`` that has at least one 200 ``propstat`` block.
    :rtype: list[tuple[:class:`xml.etree.ElementTree.Element`,
        :class:`xml.etree.ElementTree.Element`]]
    :raises calcard_mcp.errors.ProtocolError: When ``multistatus_bytes`` does
        not parse as XML.
    """
    try:
        root = ET.fromstring(multistatus_bytes)
    except ET.ParseError as exc:
        raise ProtocolError(f"CardDAV server returned a body that is not valid XML: {exc}") from exc
    result: list[tuple[ET.Element, ET.Element]] = []
    for response_elem in root.findall(f"{{{_DAV_NS}}}response"):
        href_elem = response_elem.find(f"{{{_DAV_NS}}}href")
        if href_elem is None:
            continue
        merged = ET.Element(f"{{{_DAV_NS}}}prop")
        for propstat in response_elem.findall(f"{{{_DAV_NS}}}propstat"):
            status = propstat.findtext(f"{{{_DAV_NS}}}status", default="")
            if " 200 " not in f" {status} ":
                continue
            prop = propstat.find(f"{{{_DAV_NS}}}prop")
            if prop is None:
                continue
            for child in prop:
                merged.append(child)
        if len(merged) == 0:
            continue
        result.append((href_elem, merged))
    return result


def _match_uid_in_responses(
    responses: list[tuple[ET.Element, ET.Element]],
    *,
    address_book_url: str,
    uid: str,
    absolute: Callable[[str], str],
) -> tuple[str, str | None, str] | None:
    """Walk PROPFIND/REPORT response pairs and return the vCard whose ``UID`` equals ``uid``.

    The defensive UID-equality check is the same regardless of which CardDAV
    operation produced the responses: REPORT's ``addressbook-query`` filter
    is best-effort (servers may ignore unknown collations or filter types),
    so we re-confirm exact equality before trusting the server's match.

    :param responses: Output of :func:`_iter_response_props` over the response XML.
    :type responses: list[tuple[:class:`xml.etree.ElementTree.Element`,
        :class:`xml.etree.ElementTree.Element`]]
    :param address_book_url: Address book URL; used to skip the self-href that
        servers sometimes include in the multistatus body.
    :type address_book_url: str
    :param uid: vCard ``UID`` to match exactly.
    :type uid: str
    :param absolute: Callable that turns a possibly-relative href into an
        absolute URL (typically :meth:`CardDAVClient._absolute`).
    :type absolute: typing.Callable[[str], str]
    :returns: ``(resource_url, etag_or_none, body_text)`` for the matching
        vCard (the body is the ``<C:address-data/>`` text already returned
        in the multistatus body — callers can avoid an extra GET), or
        :data:`None` when no response in ``responses`` matches.
    :rtype: tuple[str, str | None, str] | None
    """
    for href_elem, prop_elem in responses:
        resource_url = absolute(href_elem.text or "")
        if resource_url.rstrip("/") == address_book_url.rstrip("/"):
            continue
        ad_elem = prop_elem.find(f"{{{_CARDDAV_NS}}}address-data")
        if ad_elem is None or not ad_elem.text:
            continue
        body_text = ad_elem.text
        try:
            parsed: Any = parse_vcard(body_text)
        except ValueError:
            continue
        uid_prop = getattr(parsed, "uid", None)
        if uid_prop is None or str(uid_prop.value) != uid:
            continue
        etag_elem = prop_elem.find(f"{{{_DAV_NS}}}getetag")
        etag = etag_elem.text if etag_elem is not None else None
        return resource_url, etag, body_text
    return None


class ContactService:
    """Fan-out service that picks the right :class:`CardDAVClient` per account.

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
        self._clients: dict[str, CardDAVClient] = {
            account.id: CardDAVClient(account, server) for account in registry.all()
        }

    def client_for(self, name: str | None) -> CardDAVClient:
        """Return the :class:`CardDAVClient` bound to the account matching ``name``.

        :param name: Account id or display name; :data:`None` selects the default.
        :type name: str | None
        :returns: Client for the resolved account.
        :rtype: :class:`CardDAVClient`
        """
        account = self.registry.resolve(name)
        return self._clients[account.id]

    def close(self) -> None:
        """Close every per-account :class:`CardDAVClient`'s HTTP connection pool.

        Safe to call multiple times; closing an already-closed
        :class:`httpx.Client` is a no-op.

        :returns: None.
        :rtype: None
        """
        for client in self._clients.values():
            client.close()

    def __enter__(self) -> ContactService:
        """Return ``self`` so :class:`ContactService` can be used as a context manager.

        :returns: This instance.
        :rtype: :class:`ContactService`
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
