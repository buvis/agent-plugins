"""Wire-input coercers shared across :mod:`calcard_mcp.tools` submodules.

Some MCP clients (notably Claude Desktop, when the underlying model
serialises a complex array argument) deliver list parameters as a
JSON-encoded string instead of a native JSON array. The
:func:`coerce_json_array` helper detects that shape and decodes it
before Pydantic validation runs; native arrays pass through unchanged.
The wire ``inputSchema`` is unaffected — Pydantic v2's
:class:`pydantic.BeforeValidator` does not alter JSON-Schema generation.

The :data:`StrListWire` alias is the typed shorthand for tool parameters
declared as ``list[str]``. Modules that need a typed-element list (e.g.
the contact tools' typed ``{value, type}`` entries) declare their own
``Annotated`` alias using :data:`JsonArrayBeforeValidator` directly.
"""

from __future__ import annotations

import json
from typing import Annotated

from pydantic import BeforeValidator

__all__ = ["JsonArrayBeforeValidator", "StrListWire", "coerce_json_array"]


def coerce_json_array(value: object) -> object:
    """JSON-decode a string-encoded array; pass everything else through.

    :param value: Tool argument value as delivered by the MCP framework.
    :type value: object
    :returns: ``json.loads(value)`` when ``value`` is a parseable JSON
        string, the original ``value`` when ``json.loads`` fails (so
        Pydantic can raise its native typed error), or ``value``
        unchanged for any non-string input.
    :rtype: object
    """
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            # Let Pydantic raise its own typed validation error rather
            # than masking the original bad input.
            return value
    return value


JsonArrayBeforeValidator = BeforeValidator(coerce_json_array)
"""Reusable :class:`pydantic.BeforeValidator` that delegates to :func:`coerce_json_array`."""


StrListWire = Annotated[list[str], JsonArrayBeforeValidator]
"""Typed alias for tool parameters declared as ``list[str]`` on the wire.

Equivalent to ``list[str]`` for schema generation; runtime accepts a
JSON-encoded-string variant for tolerance of misbehaving MCP clients.
"""
