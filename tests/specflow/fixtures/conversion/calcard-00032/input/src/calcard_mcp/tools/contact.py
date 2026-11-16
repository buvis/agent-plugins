"""MCP tool registrations for contact (CardDAV) operations.

The :func:`register` function is invoked once during server construction.
It attaches the contact-related MCP tools (``list_address_books``,
``list_contacts``, ``search_contacts``, ``create_contact``,
``update_contact``, ``delete_contact``) to the supplied
:class:`fastmcp.FastMCP` instance.

Imports:

* :mod:`asyncio` to offload sync CardDAV calls onto worker threads.
* :mod:`dataclasses.asdict` to project frozen summaries into MCP-friendly dicts.
* :class:`fastmcp.FastMCP` for the tool registry.
* :class:`calcard_mcp.accounts.AccountRegistry` for write-safety checks.
* :class:`calcard_mcp.carddav_client.ContactService` for per-account clients.
* :class:`calcard_mcp.vcard.ContactValue` for the typed email/phone wire model.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from fastmcp import FastMCP
from pydantic import BaseModel

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.carddav_client import ContactService
from calcard_mcp.tools._coerce import JsonArrayBeforeValidator, StrListWire
from calcard_mcp.tools._logging import tool_logged
from calcard_mcp.vcard import (
    BinaryReference,
    ContactValue,
    Gender,
    GeoCoordinates,
    PartialDate,
    PostalAddress,
    Relation,
    TypedURI,
)

__all__ = ["register"]

# ``ContactValueWire`` is the wire shape of a typed email/phone entry. The
# Pydantic schema generator embeds this class's docstring into the generated
# ``inputSchema`` as the ``items.description`` of every typed array parameter,
# so the docstring is intentionally short and user-facing. If a future fastmcp
# release drops the per-element ``type`` enum from the generated schema, switch
# this declaration to a :class:`pydantic.BaseModel` subclass with the same
# fields and re-bless the snapshot.


class ContactValueWire(TypedDict):
    """Typed contact value: {value, type} with one of work/home/mobile/other."""

    value: str
    type: Literal["work", "home", "mobile", "other"]


class PostalAddressWire(BaseModel):
    """Postal address with optional components and type work/home/other."""

    po_box: str = ""
    extended: str = ""
    street: str = ""
    locality: str = ""
    region: str = ""
    postal_code: str = ""
    country: str = ""
    type: Literal["work", "home", "other"] = "other"


class TypedURIWire(BaseModel):
    """Typed URI entry: {value, type} where type is work/home/other."""

    value: str
    type: Literal["work", "home", "other"] = "other"


class RelationWire(BaseModel):
    """Typed relation: {value, type} where type is spouse/child/.../other."""

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


class BinaryReferenceWire(TypedDict):
    """Binary URI reference: data: URI or external URI with optional media_type."""

    value: str
    media_type: NotRequired[str]


class GenderWire(BaseModel):
    """Gender value: sex (M/F/O/N/U or empty) and optional identity."""

    sex: Literal["M", "F", "O", "N", "U", ""] = ""
    identity: str = ""


class GeoCoordinatesWire(TypedDict):
    """Geo coordinates with WGS-84 latitude and longitude floats."""

    latitude: float
    longitude: float


class PartialDateWire(TypedDict):
    """Partial date object with year/month/day integers."""

    year: int
    month: int
    day: int


def _to_contact_values(
    entries: list[ContactValueWire] | None,
) -> list[ContactValue] | None:
    """Convert wire entries to :class:`ContactValue`; preserve :data:`None`."""
    if entries is None:
        return None
    return [ContactValue(value=entry["value"], type=entry["type"]) for entry in entries]


def _to_postal_addresses(
    entries: list[PostalAddressWire] | None,
) -> list[PostalAddress] | None:
    """Convert wire entries to :class:`PostalAddress`; preserve :data:`None`."""
    if entries is None:
        return None
    return [
        PostalAddress(
            po_box=entry.po_box,
            extended=entry.extended,
            street=entry.street,
            locality=entry.locality,
            region=entry.region,
            postal_code=entry.postal_code,
            country=entry.country,
            type=entry.type,
        )
        for entry in entries
    ]


def _to_typed_uris(entries: list[TypedURIWire] | None) -> list[TypedURI] | None:
    """Convert wire entries to :class:`TypedURI`; preserve :data:`None`."""
    if entries is None:
        return None
    return [TypedURI(value=entry.value, type=entry.type) for entry in entries]


def _to_relations(entries: list[RelationWire] | None) -> list[Relation] | None:
    """Convert wire entries to :class:`Relation`; preserve :data:`None`."""
    if entries is None:
        return None
    return [Relation(value=entry.value, type=entry.type) for entry in entries]


def _to_binary(entry: BinaryReferenceWire | None) -> BinaryReference | None:
    """Convert wire object to :class:`BinaryReference`; preserve :data:`None`."""
    if entry is None:
        return None
    return BinaryReference(
        value=entry["value"],
        media_type=entry.get("media_type", ""),
    )


def _to_gender(entry: GenderWire | None) -> Gender | None:
    """Convert wire object to :class:`Gender`; preserve :data:`None`."""
    if entry is None:
        return None
    return Gender(sex=entry.sex, identity=entry.identity)


def _to_geo(entry: GeoCoordinatesWire | None) -> GeoCoordinates | None:
    """Convert wire object to :class:`GeoCoordinates`; preserve :data:`None`."""
    if entry is None:
        return None
    return GeoCoordinates(latitude=entry["latitude"], longitude=entry["longitude"])


def _to_partial_date(entry: PartialDateWire | None) -> PartialDate | None:
    """Convert wire object to :class:`PartialDate`; preserve :data:`None`."""
    if entry is None:
        return None
    return PartialDate(year=entry["year"], month=entry["month"], day=entry["day"])


# ``ContactValueListWire`` is the runtime-coerced equivalent of
# ``list[ContactValueWire]``. The :class:`pydantic.BeforeValidator`
# (shared from :mod:`calcard_mcp.tools._coerce`) runs *before* Pydantic's
# list/array validator, so a JSON-encoded string argument is decoded
# transparently. JSON-Schema generation is unaffected by
# ``BeforeValidator`` in Pydantic v2, so the wire ``inputSchema`` stays
# array-only and the v4 snapshot test does not need re-blessing.
ContactValueListWire = Annotated[list[ContactValueWire], JsonArrayBeforeValidator]
PostalAddressListWire = Annotated[list[PostalAddressWire], JsonArrayBeforeValidator]
TypedURIListWire = Annotated[list[TypedURIWire], JsonArrayBeforeValidator]
RelationListWire = Annotated[list[RelationWire], JsonArrayBeforeValidator]
StringListWire = Annotated[list[str], JsonArrayBeforeValidator]


def register(server: FastMCP, registry: AccountRegistry, service: ContactService) -> None:
    """Attach contact tools to ``server``.

    :param server: :class:`FastMCP` instance.
    :type server: :class:`fastmcp.FastMCP`
    :param registry: Account registry used for write-safety checks.
    :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :param service: Configured contact service.
    :type service: :class:`calcard_mcp.carddav_client.ContactService`
    :returns: None. Tools are registered on ``server`` in place.
    :rtype: None
    """

    @server.tool
    @tool_logged
    async def list_address_books(account: str | None = None) -> list[dict[str, str]]:
        """List every address book on one account.

        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: One record per address book with ``account_id``, ``name``, and ``url``.
        :rtype: list[dict[str, str]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_address_books)
        return [asdict(item) for item in result]

    @server.tool(
        description=(
            "List every contact in one address book. Returns full vCard records: "
            "typed arrays (emails/phones/addresses/urls/impps/relations), list "
            "fields (nicknames/categories/languages/members), structured fields "
            "(gender/birthday/anniversary/photo/logo/sound/key/geo), scalar "
            "fields (timezone/role/kind/organization/title/note), and "
            "raw_properties for unknown vCard fields."
        ),
    )
    @tool_logged
    async def list_contacts(
        address_book_url: str,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """List every contact in one address book.

        :param address_book_url: Address book URL returned by list_address_books.
        :type address_book_url: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Contact records sorted by full name, including typed contact
            arrays (emails/phones/addresses/urls/impps/relations), structured
            fields (gender/birthday/anniversary/photo/logo/sound/key/geo), and
            ``raw_properties`` for unknown vCard fields.
        :rtype: list[dict[str, typing.Any]]
        """
        registry.require_url_match(registry.resolve(account), address_book_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(client.list_contacts, address_book_url)
        return [asdict(item) for item in result]

    @server.tool(
        description=(
            "Search every address book on one account for contacts whose full "
            "name, organization, title, note, email, or phone contains 'query' "
            "(case-insensitive). Results include typed arrays "
            "(emails/phones/addresses/urls/impps/relations), structured fields "
            "(gender/birthday/anniversary/photo/logo/sound/key/geo), and "
            "raw_properties for unknown vCard fields."
        ),
    )
    @tool_logged
    async def search_contacts(
        query: str,
        account: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search every address book on one account for a substring match.

        :param query: Substring to match (case-insensitive).
        :type query: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: Matching contacts.
        :rtype: list[dict[str, typing.Any]]
        """
        client = service.client_for(account)
        result = await asyncio.to_thread(client.search_contacts, query)
        return [asdict(item) for item in result]

    @server.tool(
        description=(
            "Create a contact in an address book. 'full_name' is required; "
            "given/family name and full vCard fields are optional: "
            "emails/phones/addresses/urls/impps/nicknames/categories/relations/"
            "languages/members/timezone/geo/role/kind/gender/birthday/"
            "anniversary/photo/logo/sound/key/organization/title/note. "
            "Binary fields accept URI references: "
            "photo={'value':'data:image/png;base64,...','media_type':'image/png'} "
            "or logo={'value':'https://example.com/logo.svg'}."
        ),
    )
    @tool_logged
    async def create_contact(
        address_book_url: str,
        full_name: str,
        account: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: ContactValueListWire | None = None,
        phones: ContactValueListWire | None = None,
        addresses: PostalAddressListWire | None = None,
        urls: TypedURIListWire | None = None,
        impps: TypedURIListWire | None = None,
        nicknames: StringListWire | None = None,
        categories: StringListWire | None = None,
        relations: RelationListWire | None = None,
        languages: StringListWire | None = None,
        timezone: str | None = None,
        geo: GeoCoordinatesWire | None = None,
        role: str | None = None,
        kind: Literal["individual", "group", "org", "location", ""] | None = None,
        members: StringListWire | None = None,
        gender: GenderWire | None = None,
        birthday: PartialDateWire | None = None,
        anniversary: PartialDateWire | None = None,
        photo: BinaryReferenceWire | None = None,
        logo: BinaryReferenceWire | None = None,
        sound: BinaryReferenceWire | None = None,
        key: BinaryReferenceWire | None = None,
        organization: str | None = None,
        title: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Create a contact with full name and optional structured fields.

        :param address_book_url: Address book URL returned by list_address_books.
        :type address_book_url: str
        :param full_name: Full display name.
        :type full_name: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param given_name: Given name.
        :type given_name: str | None
        :param family_name: Family name.
        :type family_name: str | None
        :param emails: Email addresses with types. Each entry is {value, type}
            where type is one of: work, home, mobile, other.
        :type emails: list[ContactValueWire] | None
        :param phones: Phone numbers with types. Each entry is {value, type}
            where type is one of: work, home, mobile, other.
        :type phones: list[ContactValueWire] | None
        :param organization: Organization name.
        :type organization: str | None
        :param title: Job title.
        :type title: str | None
        :param note: Free-form note.
        :type note: str | None
        :returns: The created contact.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``address_book_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), address_book_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.create_contact,
            address_book_url=address_book_url,
            full_name=full_name,
            given_name=given_name,
            family_name=family_name,
            emails=_to_contact_values(emails),
            phones=_to_contact_values(phones),
            addresses=_to_postal_addresses(addresses),
            urls=_to_typed_uris(urls),
            impps=_to_typed_uris(impps),
            nicknames=nicknames,
            categories=categories,
            relations=_to_relations(relations),
            languages=languages,
            timezone=timezone,
            geo=_to_geo(geo),
            role=role,
            kind=kind,
            members=members,
            gender=_to_gender(gender),
            birthday=_to_partial_date(birthday),
            anniversary=_to_partial_date(anniversary),
            photo=_to_binary(photo),
            logo=_to_binary(logo),
            sound=_to_binary(sound),
            key=_to_binary(key),
            organization=organization,
            title=title,
            note=note,
        )
        return asdict(result)

    @server.tool(
        description=(
            "Update fields on an existing contact. Argument semantics: None "
            "preserves the field, an empty string sets it to empty, and listing "
            "the field name in 'clear_fields' removes the property entirely. "
            "Pass an empty list for list fields to clear those. Structured "
            "fields ('geo', 'gender', 'birthday', 'anniversary', 'photo', "
            "'logo', 'sound', 'key') have no empty representation -- pass "
            "None to preserve, a value to set, or list the field name in "
            "'clear_fields' to remove. Supports emails/phones/addresses/urls/"
            "impps/nicknames/categories/relations/languages/members and "
            "timezone/geo/role/kind/gender/birthday/anniversary/photo/logo/"
            "sound/key/organization/title/note. Valid clear_fields entries: "
            "'addresses', 'urls', 'impps', 'nicknames', 'categories', "
            "'relations', 'languages', 'members', 'photo', 'logo', 'sound', "
            "'key', 'gender', 'birthday', 'anniversary', 'timezone', 'geo', "
            "'role', 'kind', 'organization', 'title', 'note'."
        ),
    )
    @tool_logged
    async def update_contact(
        address_book_url: str,
        uid: str,
        account: str | None = None,
        full_name: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        emails: ContactValueListWire | None = None,
        phones: ContactValueListWire | None = None,
        addresses: PostalAddressListWire | None = None,
        urls: TypedURIListWire | None = None,
        impps: TypedURIListWire | None = None,
        nicknames: StringListWire | None = None,
        categories: StringListWire | None = None,
        relations: RelationListWire | None = None,
        languages: StringListWire | None = None,
        timezone: str | None = None,
        geo: GeoCoordinatesWire | None = None,
        role: str | None = None,
        kind: Literal["individual", "group", "org", "location", ""] | None = None,
        members: StringListWire | None = None,
        gender: GenderWire | None = None,
        birthday: PartialDateWire | None = None,
        anniversary: PartialDateWire | None = None,
        photo: BinaryReferenceWire | None = None,
        logo: BinaryReferenceWire | None = None,
        sound: BinaryReferenceWire | None = None,
        key: BinaryReferenceWire | None = None,
        organization: str | None = None,
        title: str | None = None,
        note: str | None = None,
        clear_fields: StrListWire | None = None,
    ) -> dict[str, Any]:
        """Update an existing vCard with read-after-write verification.

        :param address_book_url: Address book URL that holds the contact.
        :type address_book_url: str
        :param uid: UID of the contact, returned by list_contacts or search_contacts.
        :type uid: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :param full_name: New full display name.
        :type full_name: str | None
        :param given_name: New given name.
        :type given_name: str | None
        :param family_name: New family name.
        :type family_name: str | None
        :param emails: Replacement email list with types. Each entry is
            {value, type} where type is one of: work, home, mobile, other.
            Empty list clears the field.
        :type emails: list[ContactValueWire] | None
        :param phones: Replacement phone list with types. Each entry is
            {value, type} where type is one of: work, home, mobile, other.
            Empty list clears the field.
        :type phones: list[ContactValueWire] | None
        :param organization: New organization name.
        :type organization: str | None
        :param title: New job title.
        :type title: str | None
        :param note: New note.
        :type note: str | None
        :param clear_fields: Field names to remove. Allowed: "addresses", "urls",
            "impps", "nicknames", "categories", "relations", "languages",
            "members", "photo", "logo", "sound", "key", "gender", "birthday",
            "anniversary", "timezone", "geo", "role", "kind", "organization",
            "title", "note".
        :type clear_fields: list[str] | None
        :returns: The updated contact.
        :rtype: dict[str, typing.Any]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``address_book_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), address_book_url)
        client = service.client_for(account)
        result = await asyncio.to_thread(
            client.update_contact,
            address_book_url=address_book_url,
            uid=uid,
            full_name=full_name,
            given_name=given_name,
            family_name=family_name,
            emails=_to_contact_values(emails),
            phones=_to_contact_values(phones),
            addresses=_to_postal_addresses(addresses),
            urls=_to_typed_uris(urls),
            impps=_to_typed_uris(impps),
            nicknames=nicknames,
            categories=categories,
            relations=_to_relations(relations),
            languages=languages,
            timezone=timezone,
            geo=_to_geo(geo),
            role=role,
            kind=kind,
            members=members,
            gender=_to_gender(gender),
            birthday=_to_partial_date(birthday),
            anniversary=_to_partial_date(anniversary),
            photo=_to_binary(photo),
            logo=_to_binary(logo),
            sound=_to_binary(sound),
            key=_to_binary(key),
            organization=organization,
            title=title,
            note=note,
            clear_fields=clear_fields,
        )
        return asdict(result)

    @server.tool
    @tool_logged
    async def delete_contact(
        address_book_url: str,
        uid: str,
        account: str | None = None,
    ) -> dict[str, str]:
        """Delete a contact by UID.

        :param address_book_url: Address book URL that holds the contact.
        :type address_book_url: str
        :param uid: UID of the contact, returned by list_contacts or search_contacts.
        :type uid: str
        :param account: Account id or display name (e.g. 'eva' or 'Eva') to act
            on behalf of. The server holds separate credentials for every
            configured account; pass the account that owns any URL on writes.
            Omit to use the default account.
        :type account: str | None
        :returns: ``{"status": "deleted", "uid": uid}`` on success.
        :rtype: dict[str, str]
        :raises calcard_mcp.errors.AccountNotWritableError: When the account is read-only.
        :raises calcard_mcp.errors.CrossAccountAccessError: When
            ``address_book_url`` does not belong to ``account``.
        """
        registry.require_writable(registry.resolve(account))
        registry.require_url_match(registry.resolve(account), address_book_url)
        client = service.client_for(account)
        await asyncio.to_thread(
            client.delete_contact,
            address_book_url=address_book_url,
            uid=uid,
        )
        return {"status": "deleted", "uid": uid}
