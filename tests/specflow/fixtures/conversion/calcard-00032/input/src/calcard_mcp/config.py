"""YAML configuration loading and validation for calcard-mcp.

Imports:

* :mod:`os` to resolve passwords referenced by environment variable name.
* :mod:`pathlib.Path` for type-safe filesystem paths.
* :mod:`typing` for :data:`typing.Self` in alternate constructors.
* :mod:`yaml` to parse the configuration document.
* :class:`pydantic.BaseModel` and friends to validate the parsed structure.
* :class:`calcard_mcp.errors.ConfigError` to signal loading and validation failures.
* :mod:`calcard_mcp.credentials` for direct native-store and 1Password lookup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from calcard_mcp.credentials import (
    read_keychain,
    read_onepassword,
    read_onepassword_item,
    read_windows,
)
from calcard_mcp.errors import ConfigError


class ServerConfig(BaseModel):
    """Global server-level settings shared by every account.

    :cvar base_url: HTTPS base URL of the CalDAV/CardDAV server, without trailing slash.
    :vartype base_url: str
    :cvar verify_tls: When :data:`False`, disable TLS verification (self-signed certs only).
    :vartype verify_tls: bool
    :cvar timeout: HTTP request timeout in seconds.
    :vartype timeout: float
    :cvar verify_writes: When :data:`True`, every mutating call is followed by a
        read-after-write check.
    :vartype verify_writes: bool
    :cvar use_freebusy_report: When :data:`True`, ``find_free_time`` issues a
        CalDAV ``<C:free-busy-query>`` REPORT against calendars that advertise
        support via ``DAV:supported-report-set``; on per-call REPORT failure
        it falls back transparently to event-walk for that one call. Set to
        :data:`False` to force every call through event-walk (debugging or a
        broken server).
    :vartype use_freebusy_report: bool
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    base_url: str
    verify_tls: bool = True
    timeout: float = 15.0
    verify_writes: bool = True
    use_freebusy_report: bool = True

    @field_validator("base_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        """Strip any trailing slashes from ``base_url`` so paths concatenate cleanly.

        :param value: Raw ``base_url`` value from YAML.
        :type value: str
        :returns: ``value`` with any trailing ``/`` characters removed.
        :rtype: str
        """
        return value.rstrip("/")


class CredentialStoreConfig(BaseModel):
    """Identify a native generic credential by service and optional account name.

    The account defaults to the CalDAV/CardDAV username when omitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    service: str = Field(min_length=1)
    account: str | None = Field(default=None, min_length=1)


class OnePasswordConfig(BaseModel):
    """Identify a 1Password field by secret URI or readable vault/item names.

    ``command`` may be an absolute executable path for GUI-launched MCP clients.
    ``account`` selects a 1Password account when multiple accounts are signed in.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    reference: str | None = Field(default=None, pattern=r"^op://[^/]+/[^/]+/.+$")
    vault: str | None = Field(default=None, min_length=1)
    item: str | None = Field(default=None, min_length=1)
    field: str | None = Field(default=None, min_length=1)
    command: str = Field(default="op", min_length=1)
    account: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate_selector(self) -> Self:
        """Require either a URI or a vault/item pair, never a mixture."""
        if self.reference is not None:
            if any(value is not None for value in (self.vault, self.item, self.field)):
                raise ValueError("reference cannot be combined with vault, item, or field")
        elif self.vault is None or self.item is None:
            raise ValueError("1Password requires reference or both vault and item")
        return self


class AccountConfig(BaseModel):
    """Configuration for a single principal (family member).

    :cvar id: Stable canonical identifier used by tools to address the account.
    :vartype id: str
    :cvar display_names: Human-friendly aliases used for fuzzy resolution in tool calls.
    :vartype display_names: list[str]
    :cvar principal_path: Path to the account's CalDAV/CardDAV principal on the server.
    :vartype principal_path: str
    :cvar username: HTTP basic auth username for this account.
    :vartype username: str
    :cvar password_env: Name of the environment variable that holds the password.
    :vartype password_env: str | None
    :cvar password_keychain: macOS generic credential reference.
    :vartype password_keychain: CredentialStoreConfig | None
    :cvar password_windows: Windows generic credential reference.
    :vartype password_windows: CredentialStoreConfig | None
    :cvar password_1password: 1Password secret reference and CLI settings.
    :vartype password_1password: OnePasswordConfig | None
    :cvar default: When :data:`True`, tool calls that omit ``account`` use this account.
    :vartype default: bool
    :cvar writable: When :data:`False`, write tools refuse to mutate this account.
    :vartype writable: bool
    :cvar timezone: IANA timezone name applied to naive datetimes and new events.
    :vartype timezone: str
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    display_names: list[str] = Field(default_factory=list)
    principal_path: str
    username: str
    password_env: str | None = Field(default=None, min_length=1)
    password_keychain: CredentialStoreConfig | None = None
    password_windows: CredentialStoreConfig | None = None
    password_1password: OnePasswordConfig | None = None
    default: bool = False
    writable: bool = True
    timezone: str = "UTC"

    @model_validator(mode="after")
    def _validate_password_source(self) -> Self:
        """Require one explicit password source, with no implicit fallback."""
        sources = (
            self.password_env,
            self.password_keychain,
            self.password_windows,
            self.password_1password,
        )
        if sum(source is not None for source in sources) != 1:
            raise ValueError(
                "exactly one password source is required: password_env, password_keychain, "
                "password_windows, or password_1password"
            )
        return self

    @field_validator("principal_path")
    @classmethod
    def _ensure_path_shape(cls, value: str) -> str:
        """Normalise ``principal_path`` to have a leading and trailing slash.

        :param value: Raw principal path.
        :type value: str
        :returns: Path that starts and ends with a single ``/``.
        :rtype: str
        """
        path = value if value.startswith("/") else f"/{value}"
        return path if path.endswith("/") else f"{path}/"

    def resolve_password(self) -> str:
        """Read the password from this account's explicitly selected source.

        :returns: The password string.
        :rtype: str
        :raises calcard_mcp.errors.ConfigError: When lookup fails or the password is empty.
        """
        if self.password_keychain is not None:
            return read_keychain(
                self.password_keychain.service,
                self.password_keychain.account or self.username,
                account_id=self.id,
            )
        if self.password_windows is not None:
            return read_windows(
                self.password_windows.service,
                self.password_windows.account or self.username,
                account_id=self.id,
            )
        if self.password_1password is not None:
            source = self.password_1password
            if source.reference is not None:
                return read_onepassword(
                    source.reference,
                    command=source.command,
                    account=source.account,
                    account_id=self.id,
                )
            if source.vault is not None and source.item is not None:
                return read_onepassword_item(
                    source.vault,
                    source.item,
                    source.field or "password",
                    command=source.command,
                    account=source.account,
                    account_id=self.id,
                )
        if self.password_env is not None:
            try:
                value = os.environ[self.password_env]
            except KeyError:
                value = ""
            if not value:
                raise ConfigError(
                    f"account {self.id!r}: environment variable {self.password_env!r} "
                    "is unset or empty"
                )
            return value
        raise ConfigError(f"account {self.id!r}: no password source configured")

    def matches(self, name: str) -> bool:
        """Return whether ``name`` matches this account by id or any display name.

        :param name: Candidate identifier from a tool call; comparison is case-insensitive.
        :type name: str
        :returns: :data:`True` when ``name`` matches the id or any display name.
        :rtype: bool
        """
        candidate = name.strip().casefold()
        if candidate == self.id.casefold():
            return True
        return any(candidate == alias.casefold() for alias in self.display_names)


class AppConfig(BaseModel):
    """Top-level configuration: server settings plus the list of accounts.

    :cvar server: Global server and HTTP settings.
    :vartype server: :class:`ServerConfig`
    :cvar accounts: One entry per principal the operator manages.
    :vartype accounts: list[:class:`AccountConfig`]
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    server: ServerConfig
    accounts: list[AccountConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_account_invariants(self) -> Self:
        """Enforce uniqueness of account ids and at most one ``default`` account.

        :returns: The validated :class:`AppConfig` instance.
        :rtype: :class:`AppConfig`
        :raises ValueError: When ids collide or multiple accounts are marked default.
        """
        seen: set[str] = set()
        for account in self.accounts:
            key = account.id.casefold()
            if key in seen:
                raise ValueError(f"duplicate account id: {account.id!r}")
            seen.add(key)
        defaults = [account for account in self.accounts if account.default]
        if len(defaults) > 1:
            ids = ", ".join(account.id for account in defaults)
            raise ValueError(f"multiple accounts marked default: {ids}")
        return self

    @property
    def default_account(self) -> AccountConfig:
        """Return the account marked ``default``, falling back to the first account.

        :returns: The account used when a tool call omits the ``account`` parameter.
        :rtype: :class:`AccountConfig`
        """
        for account in self.accounts:
            if account.default:
                return account
        return self.accounts[0]

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load and validate an :class:`AppConfig` from ``path``.

        :param path: Path to a YAML config document.
        :type path: pathlib.Path
        :returns: Validated configuration instance.
        :rtype: :class:`AppConfig`
        :raises calcard_mcp.errors.ConfigError: When the file is missing, unparseable,
            or fails schema validation.
        """
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ConfigError(f"config root must be a mapping in {path}")
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            raise ConfigError(f"config validation failed for {path}:\n{exc}") from exc
