"""Runtime account registry and resolver.

Imports:

* :mod:`dataclasses` for a frozen runtime record that bundles config + resolved password.
* :mod:`posixpath` for path normalization (``..``/``.`` resolution) in
  :meth:`AccountRegistry.require_url_match`.
* :mod:`urllib.parse` for URL scheme/netloc/path inspection used by
  :meth:`AccountRegistry.require_url_match`.
* :class:`calcard_mcp.config.AccountConfig` and :class:`calcard_mcp.config.AppConfig`
  describe the loaded configuration.
* :class:`calcard_mcp.errors.AccountNotFoundError`,
  :class:`calcard_mcp.errors.AccountNotWritableError`, and
  :class:`calcard_mcp.errors.CrossAccountAccessError` signal lookup and
  safety failures.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from urllib.parse import urlparse

from calcard_mcp.config import AccountConfig, AppConfig
from calcard_mcp.errors import (
    AccountNotFoundError,
    AccountNotWritableError,
    CrossAccountAccessError,
)


@dataclass(frozen=True, slots=True)
class ResolvedAccount:
    """An account with its password materialised from its configured credential source.

    :cvar config: Static configuration loaded from YAML.
    :vartype config: :class:`calcard_mcp.config.AccountConfig`
    :cvar password: Password resolved via :meth:`AccountConfig.resolve_password`.
    :vartype password: str
    """

    config: AccountConfig
    password: str

    @property
    def id(self) -> str:
        """Return the canonical id.

        :returns: The account id.
        :rtype: str
        """
        return self.config.id


class AccountRegistry:
    """In-memory lookup of configured accounts keyed by id or display name.

    :cvar accounts: Mapping of account id to :class:`ResolvedAccount`.
    :vartype accounts: dict[str, :class:`ResolvedAccount`]
    """

    def __init__(self, app_config: AppConfig) -> None:
        """Initialise the registry from a loaded :class:`AppConfig`.

        :param app_config: Validated configuration.
        :type app_config: :class:`calcard_mcp.config.AppConfig`
        :raises calcard_mcp.errors.ConfigError: Propagated from password resolution.
        """
        self._app_config: AppConfig = app_config
        # Parse the configured server base_url once; it is a frozen config value
        # and serves as the single authoritative reference for the scheme/host
        # comparison performed by :meth:`require_url_match`.
        base_parsed = urlparse(app_config.server.base_url)
        self._base_scheme: str = base_parsed.scheme
        self._base_netloc: str = base_parsed.netloc
        self.accounts: dict[str, ResolvedAccount] = {
            account.id: ResolvedAccount(config=account, password=account.resolve_password())
            for account in app_config.accounts
        }

    def all(self) -> list[ResolvedAccount]:
        """List every resolved account in configuration order.

        :returns: List of resolved accounts.
        :rtype: list[:class:`ResolvedAccount`]
        """
        return [self.accounts[account.id] for account in self._app_config.accounts]

    def default(self) -> ResolvedAccount:
        """Return the default account.

        :returns: The resolved default account.
        :rtype: :class:`ResolvedAccount`
        """
        return self.accounts[self._app_config.default_account.id]

    def resolve(self, name: str | None) -> ResolvedAccount:
        """Resolve an account by id or any display name, defaulting when ``name`` is absent.

        :param name: Account id or display name; :data:`None` or empty falls back to default.
        :type name: str | None
        :returns: Matching resolved account.
        :rtype: :class:`ResolvedAccount`
        :raises calcard_mcp.errors.AccountNotFoundError: When no configured account matches.
        """
        if name is None or not name.strip():
            return self.default()
        for account in self.all():
            if account.config.matches(name):
                return account
        known = ", ".join(account.id for account in self.all())
        raise AccountNotFoundError(f"no account matches {name!r}; configured: {known}")

    def resolve_many(self, names: list[str] | None) -> list[ResolvedAccount]:
        """Resolve a list of account names, returning every account when ``names`` is absent.

        :param names: List of account ids or display names; :data:`None` means "all accounts".
        :type names: list[str] | None
        :returns: Resolved accounts preserving input order, deduplicated by id.
        :rtype: list[:class:`ResolvedAccount`]
        :raises calcard_mcp.errors.AccountNotFoundError: When any name fails to match.
        """
        if names is None:
            return self.all()
        resolved: list[ResolvedAccount] = []
        seen: set[str] = set()
        for name in names:
            account = self.resolve(name)
            if account.id not in seen:
                resolved.append(account)
                seen.add(account.id)
        return resolved

    def require_writable(self, account: ResolvedAccount) -> None:
        """Assert that ``account`` permits writes.

        :param account: Account to check.
        :type account: :class:`ResolvedAccount`
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.AccountNotWritableError: When ``writable`` is :data:`False`.
        """
        if not account.config.writable:
            raise AccountNotWritableError(
                f"account {account.id!r} is configured read-only; refusing to mutate"
            )

    def require_url_match(self, account: ResolvedAccount, url: str) -> None:
        """Assert that ``url`` targets ``account``'s configured server and principal.

        Guards credential attachment: all URL-taking tools route through this
        method before a URL is handed to an HTTP client that attaches the
        account's HTTP Basic credentials. The check has three parts:

        * **Scheme + host gate** — when ``url`` carries a netloc, its scheme
          and host MUST equal those of the configured ``server.base_url``.
          A mismatch would send the account's credentials off-host or over a
          downgraded/upgraded scheme (credential exfiltration / SSRF), so it
          raises :class:`~calcard_mcp.errors.CrossAccountAccessError` naming
          the configured host. Relative (netloc-less) URLs skip this gate and
          are path-checked only.
        * **Path normalization** — the URL path is normalized with
          :func:`posixpath.normpath` (resolving ``.``/``..``) before the
          principal-prefix check, so a ``..`` segment cannot escape the
          principal (e.g. ``/eva/../bob/`` normalizes to ``/bob/``).
        * **Principal-prefix gate** — the normalized path MUST be rooted in
          ``account``'s principal path. The trailing slash anchors the segment
          so ``/bob/`` does not match ``/bobby/``.

        Catches the common LLM mistake of passing a URL that belongs to one
        principal while leaving ``account`` unset (or set to a different
        principal). The downstream CalDAV/CardDAV server would reject a
        cross-principal path with HTTP 403; raising upstream surfaces an
        actionable error pointing at the right ``account`` value.

        :param account: Resolved account whose configured server and principal
            path the URL must target.
        :type account: :class:`ResolvedAccount`
        :param url: Calendar / address book / task list / resource URL.
        :type url: str
        :returns: None.
        :rtype: None
        :raises calcard_mcp.errors.CrossAccountAccessError: When the URL's
            scheme or host differs from the configured ``server.base_url``, or
            when its normalized path is not rooted in
            ``account.config.principal_path``.
        """
        parsed = urlparse(url)
        # Scheme + host gate: an absolute URL (one carrying a netloc) must
        # target the configured server exactly. Relative URLs have no netloc
        # and are path-checked only, preserving prior behavior.
        if parsed.netloc and (
            parsed.scheme != self._base_scheme or parsed.netloc != self._base_netloc
        ):
            raise CrossAccountAccessError(
                f"URL {url!r} targets host {parsed.netloc!r} over scheme "
                f"{parsed.scheme!r}, which does not match the configured server "
                f"{self._base_netloc!r} over scheme {self._base_scheme!r}. "
                f"Pass a URL on the configured server so account credentials "
                f"are not sent off-host."
            )
        principal = account.config.principal_path
        if not principal.endswith("/"):
            principal = principal + "/"
        # Normalize the path (resolve ./..) before the prefix check so `..`
        # traversal cannot escape the principal. normpath strips a trailing
        # slash, so re-append one when the raw path ended with `/`, preserving
        # the trailing-slash segment anchor (e.g. `/bob/` vs `/bobby/`).
        raw_path = parsed.path
        normalized = posixpath.normpath(raw_path)
        if raw_path.endswith("/") and not normalized.endswith("/"):
            normalized = normalized + "/"
        if not normalized.startswith(principal):
            known = ", ".join(a.id for a in self.all())
            raise CrossAccountAccessError(
                f"URL {url!r} is not rooted in principal path "
                f"{account.config.principal_path!r} of account {account.id!r}. "
                f"Pass 'account' matching the URL's owner (configured ids: {known})."
            )
