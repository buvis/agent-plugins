"""MCP tool registrations for account introspection.

The :func:`register` function is invoked once during server construction
in :func:`calcard_mcp.server.build_server`. It attaches the account-related
MCP tools (currently just ``list_accounts``) to the supplied
:class:`fastmcp.FastMCP` instance.

Imports:

* :class:`fastmcp.FastMCP` for the tool registry.
* :class:`calcard_mcp.accounts.AccountRegistry` for the resolved account list.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.tools._logging import tool_logged

__all__ = ["register"]


def register(server: FastMCP, registry: AccountRegistry) -> None:
    """Attach account tools to ``server``.

    :param server: :class:`FastMCP` instance.
    :type server: :class:`fastmcp.FastMCP`
    :param registry: Configured account registry.
    :type registry: :class:`calcard_mcp.accounts.AccountRegistry`
    :returns: None. Tools are registered on ``server`` in place.
    :rtype: None
    """

    @server.tool(
        description=(
            "List every configured account with id, display names, default and "
            "writable flags, and timezone. Call this first to discover valid "
            "values for the 'account' parameter on other tools."
        ),
    )
    @tool_logged
    async def list_accounts() -> list[dict[str, Any]]:
        """Return metadata for every configured account.

        :returns: One record per account.
        :rtype: list[dict[str, typing.Any]]
        """
        return [
            {
                "id": account.config.id,
                "display_names": list(account.config.display_names),
                "default": account.config.default,
                "writable": account.config.writable,
                "timezone": account.config.timezone,
            }
            for account in registry.all()
        ]
