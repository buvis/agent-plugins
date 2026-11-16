"""Exception hierarchy for calcard-mcp.

Imports:

This module intentionally has no runtime imports; it defines only exception
classes that other modules raise and callers catch.
"""

from __future__ import annotations


class CalcardError(Exception):
    """Base class for all calcard-mcp errors."""


class ConfigError(CalcardError):
    """Raise when the YAML config is missing, malformed, or references an undefined secret."""


class AccountNotFoundError(CalcardError):
    """Raise when a tool call references an account id or display name that is not configured."""


class AccountNotWritableError(CalcardError):
    """Raise when a write is attempted against an account configured as read-only."""


class WriteVerificationError(CalcardError):
    """Raise when a read-after-write check fails to confirm the intended change.

    :cvar field_diffs: Human-readable list of ``(field, intended, actual)`` tuples.
    :vartype field_diffs: list[tuple[str, str, str]]
    """

    def __init__(
        self,
        message: str,
        *,
        field_diffs: list[tuple[str, str, str]] | None = None,
    ) -> None:
        """Initialise the error with a message and optional field-level diff list.

        :param message: Human-readable error summary.
        :type message: str
        :param field_diffs: List of ``(field_name, intended_value, actual_value)`` tuples
            describing where the server's stored record differs from what was sent.
        :type field_diffs: list[tuple[str, str, str]] | None
        """
        super().__init__(message)
        self.field_diffs: list[tuple[str, str, str]] = field_diffs or []


class ProtocolError(CalcardError):
    """Raise when the CalDAV/CardDAV server returns an unexpected response."""


class CrossAccountAccessError(CalcardError):
    """Raise when a URL belongs to a principal other than the resolved account.

    Surfaced before any HTTP traffic so MCP clients see a clear actionable
    message ("pass account=<owner>") instead of a downstream HTTP 403 from
    the CalDAV/CardDAV server.
    """
