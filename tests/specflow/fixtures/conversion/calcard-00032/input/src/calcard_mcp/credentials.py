"""Read passwords from explicitly selected vaults without environment injection."""

from __future__ import annotations

import json
import subprocess
import sys
from importlib import import_module
from typing import cast

from calcard_mcp.errors import ConfigError


def _read_command(args: list[str], *, account_id: str, provider: str) -> str:
    """Capture a provider's output, suppressing secret-bearing exception details."""
    try:
        result = subprocess.run(
            args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
            timeout=60,
        )
        value = result.stdout.decode("utf-8")
    except FileNotFoundError:
        raise ConfigError(f"account {account_id!r}: {provider} executable not found") from None
    except subprocess.TimeoutExpired:
        raise ConfigError(f"account {account_id!r}: {provider} lookup timed out") from None
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        raise ConfigError(
            f"account {account_id!r}: {provider} lookup failed; check the item and vault access"
        ) from None
    return value


def _require_password(value: str | None, *, account_id: str, provider: str) -> str:
    """Reject absent secrets without stripping meaningful password whitespace."""
    if not value:
        raise ConfigError(f"account {account_id!r}: {provider} password is missing or empty")
    return value


def read_keychain(service: str, username: str, *, account_id: str) -> str:
    """Read a macOS generic password using the system Keychain utility."""
    if sys.platform != "darwin":
        raise ConfigError(f"account {account_id!r}: password_keychain requires macOS")
    value = _read_command(
        ["/usr/bin/security", "find-generic-password", "-s", service, "-a", username, "-w"],
        account_id=account_id,
        provider="macOS Keychain",
    )
    # security appends one newline; any whitespace in the password must survive.
    return _require_password(
        value.removesuffix("\n"), account_id=account_id, provider="macOS Keychain"
    )


def read_onepassword(reference: str, *, command: str, account: str | None, account_id: str) -> str:
    """Read a 1Password field through the CLI's authenticated desktop integration."""
    args = [command, "read", "--no-newline"]
    if account is not None:
        args.extend(["--account", account])
    args.append(reference)
    value = _read_command(args, account_id=account_id, provider="1Password")
    return _require_password(value, account_id=account_id, provider="1Password")


def read_onepassword_item(
    vault: str, item: str, field: str, *, command: str, account: str | None, account_id: str
) -> str:
    """Read a named field from a named item, including titles unsupported by op:// URIs."""
    args = [
        command,
        "item",
        "get",
        "--vault",
        vault,
        "--fields",
        f"label={field}",
        "--format",
        "json",
        "--reveal",
    ]
    if account is not None:
        args.extend(["--account", account])
    args.extend(["--", item])
    output = _read_command(args, account_id=account_id, provider="1Password")
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        raise ConfigError(
            f"account {account_id!r}: 1Password returned an invalid field response"
        ) from None
    value = cast(dict[str, object], data).get("value") if isinstance(data, dict) else None
    if not isinstance(value, str):
        raise ConfigError(f"account {account_id!r}: 1Password returned an invalid field response")
    return _require_password(value, account_id=account_id, provider="1Password")


def read_windows(service: str, username: str, *, account_id: str) -> str:
    """Read a generic credential using only keyring's Windows Credential Manager backend."""
    if sys.platform != "win32":
        raise ConfigError(f"account {account_id!r}: password_windows requires Windows")
    try:
        # Explicitly select the native backend; never autodetect a third-party store.
        windows = import_module("keyring.backends.Windows")
        value: str | None = windows.WinVaultKeyring().get_password(service, username)
    except ImportError:
        raise ConfigError(
            f"account {account_id!r}: Windows credentials require the windows-credentials extra; "
            "install with uv sync --extra windows-credentials"
        ) from None
    except Exception:
        # Native backend exceptions can include the credential blob. Do not log or chain them.
        raise ConfigError(
            f"account {account_id!r}: Windows Credential Manager lookup failed; "
            "check the item and vault access"
        ) from None
    return _require_password(value, account_id=account_id, provider="Windows Credential Manager")
