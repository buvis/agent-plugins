"""Shared value-only encoding for ``raw_properties`` maps.

Both the vCard parser (:mod:`calcard_mcp.vcard`) and the iCal parser
(:mod:`calcard_mcp._ical_parse`) expose unknown properties as value-only
segments in their ``raw_properties`` dict: the ``NAME:`` prefix and trailing
CRLF are stripped. When a property carries parameters they are preserved as a
leading ``;PARAM=VALUE[;PARAM=VALUE...]:`` prefix on the value so they are not
silently dropped. Parameter names are emitted in sorted order so the encoding
is deterministic regardless of the parser's internal ordering.
"""

from __future__ import annotations

from typing import Any, cast


def _join_param_values(values: Any) -> str:
    """Join a parameter's value(s) with ``,``.

    vobject yields a list per parameter; icalendar yields either a scalar or a
    list. A bare string is returned as-is (never iterated character by
    character).

    :param values: a single parameter value or a list/tuple of values.
    :returns: the comma-joined values.
    """
    if isinstance(values, (list, tuple)):
        return ",".join(str(v) for v in cast("list[Any]", values))
    return str(values)


def encode_raw_property_value(value_text: str, params: Any) -> str:
    """Return ``value_text``, prefixed with sorted ``;PARAM=VALUE:`` when params exist.

    :param value_text: the property value with no ``NAME:`` prefix or trailing
        CRLF.
    :param params: a mapping of parameter name to value (scalar) or list of
        values, or a falsy value when the property is parameterless.
    :returns: ``value_text`` unchanged when ``params`` is empty, otherwise
        ``";P1=v;P2=a,b:" + value_text`` with parameter names sorted.
    """
    if not params:
        return value_text
    prefix = "".join(
        f";{name}={_join_param_values(params[name])}" for name in sorted(params)
    )
    return f"{prefix}:{value_text}"
