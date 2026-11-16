"""Shared base class for per-account DAV clients.

Both :class:`calcard_mcp.caldav_client.CalDAVClient` (built on the ``caldav``
library's ``DAVClient``) and :class:`calcard_mcp.carddav_client.CardDAVClient`
(built directly on :mod:`httpx` because ``caldav`` 3.x dropped CardDAV) hold
the same per-account context: the resolved account, the shared server config,
and the absolute URL of the account's principal collection.

This module factors out that common state. Transport setup stays in the
subclasses because the two stacks are different (caldav-lib vs raw httpx)
and there is no productive way to share it without inventing a parallel
abstraction.

Imports:

* :class:`calcard_mcp.accounts.ResolvedAccount` for the resolved account.
* :class:`calcard_mcp.config.ServerConfig` for shared HTTP settings.
"""

from __future__ import annotations

from calcard_mcp.accounts import ResolvedAccount
from calcard_mcp.config import ServerConfig

__all__ = ["DAVClientBase"]


class DAVClientBase:
    """Shared per-account context for CalDAV and CardDAV clients.

    Subclasses must call ``super().__init__(account, server)`` and then set
    up their own transport against :attr:`_base_url`.

    :cvar account: Resolved account this client operates as.
    :vartype account: :class:`calcard_mcp.accounts.ResolvedAccount`
    :cvar server: Shared server settings.
    :vartype server: :class:`calcard_mcp.config.ServerConfig`
    """

    def __init__(self, account: ResolvedAccount, server: ServerConfig) -> None:
        """Store the per-account context shared by all DAV transports.

        :param account: Account whose credentials drive every request.
        :type account: :class:`calcard_mcp.accounts.ResolvedAccount`
        :param server: Shared server configuration.
        :type server: :class:`calcard_mcp.config.ServerConfig`
        """
        self.account: ResolvedAccount = account
        self.server: ServerConfig = server
        self._base_url: str = f"{server.base_url}{account.config.principal_path}"
