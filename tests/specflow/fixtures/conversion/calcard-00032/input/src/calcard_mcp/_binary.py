"""Shared value-type dataclasses used by both vCard and iCal modules.

These shapes live here (rather than in :mod:`calcard_mcp.vcard`) so the
iCal modules (:mod:`calcard_mcp.ical`, :mod:`calcard_mcp.vtodo`) can import
them for ``ATTACH`` and ``GEO`` emission without depending on the vCard
module, and without a circular import that the reverse arrangement would
create.

:mod:`calcard_mcp.vcard` re-exports both :class:`BinaryReference` and
:class:`GeoCoordinates` for back-compat; existing callers continue to use
``from calcard_mcp.vcard import BinaryReference`` / ``GeoCoordinates``.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["BinaryReference", "GeoCoordinates"]


@dataclass(frozen=True, slots=True)
class BinaryReference:
    """URI to inline data or external resource.

    Used for vCard ``PHOTO`` / ``LOGO`` / ``SOUND`` / ``KEY`` (RFC 6350
    §6.2.4 / §6.6.3 / §6.7.5 / §6.8.1) and iCalendar ``ATTACH``
    (RFC 5545 §3.8.1.1).

    :cvar value: Either an absolute URL (``http://``, ``https://``,
        ``file://``) or a ``data:`` URI carrying inline base64
        (``data:<media_type>;base64,<payload>``).
    :vartype value: str
    :cvar media_type: Optional MIME media type. Required when ``value`` is
        a ``data:`` URI without an inline media-type segment; otherwise
        derived from the URI itself.
    :vartype media_type: str
    """

    value: str
    media_type: str = ""


@dataclass(frozen=True, slots=True)
class GeoCoordinates:
    """WGS-84 latitude / longitude pair shared between vCard and iCalendar.

    Covers both vCard ``GEO`` (RFC 6350 §6.5.2) and iCalendar ``GEO``
    (RFC 5545 §3.8.1.6); the wire shape is identical (``GEO:lat;lon``)
    so a single dataclass serves both.

    :cvar latitude: Decimal latitude (degrees).
    :vartype latitude: float
    :cvar longitude: Decimal longitude (degrees).
    :vartype longitude: float
    """

    latitude: float
    longitude: float
