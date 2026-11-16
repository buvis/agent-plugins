"""calcard-mcp: multi-account CalDAV/CardDAV MCP server.

This package exposes a Model Context Protocol (MCP) server that bridges an
LLM to any RFC 4791 (CalDAV) and RFC 6352 (CardDAV) server. It is designed
for family-scale multi-account setups where one operator holds credentials
for every principal and manages calendars and contacts on their behalf.

Imports:

* :mod:`calcard_mcp.config` provides :class:`calcard_mcp.config.AppConfig`
  and related Pydantic models for loading YAML configuration.
* :mod:`calcard_mcp.accounts` exposes :class:`calcard_mcp.accounts.AccountRegistry`
  which resolves accounts by id or display name.
* :mod:`calcard_mcp.caldav_client` and :mod:`calcard_mcp.carddav_client`
  implement the protocol clients.
* :mod:`calcard_mcp.verifier` implements read-after-write verification.
* :mod:`calcard_mcp.server` wires the MCP stdio server and tool registry.
"""

from calcard_mcp.errors import (
    AccountNotFoundError,
    CalcardError,
    ConfigError,
    WriteVerificationError,
)

__all__ = [
    "AccountNotFoundError",
    "CalcardError",
    "ConfigError",
    "WriteVerificationError",
]

__version__ = "0.1.0"
