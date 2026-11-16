"""Unit tests for :mod:`calcard_mcp.accounts`."""

from __future__ import annotations

from pathlib import Path

import pytest

from calcard_mcp.accounts import AccountRegistry
from calcard_mcp.config import AppConfig
from calcard_mcp.errors import (
    AccountNotFoundError,
    AccountNotWritableError,
    CrossAccountAccessError,
)


def _config(tmp_path: Path) -> AppConfig:
    body = """
server:
  base_url: https://example.com
accounts:
  - id: bob
    display_names: [Bob]
    principal_path: /bob/
    username: bob
    password_env: PW
    default: true
    writable: true
  - id: eva
    display_names: [Eva]
    principal_path: /eva/
    username: eva
    password_env: PW
    writable: false
"""
    path = tmp_path / "config.yaml"
    path.write_text(body, encoding="utf-8")
    return AppConfig.load(path)


def _config_dav_local(tmp_path: Path) -> AppConfig:
    """Second config whose ``server.base_url`` is ``http://dav.local``.

    Used by the scheme-mismatch and ``..`` traversal exploration cases, which
    need a base_url distinct from the ``https://example.com`` used by
    :func:`_config`.
    """
    body = """
server:
  base_url: http://dav.local
accounts:
  - id: bob
    display_names: [Bob]
    principal_path: /bob/
    username: bob
    password_env: PW
    default: true
    writable: true
  - id: eva
    display_names: [Eva]
    principal_path: /eva/
    username: eva
    password_env: PW
    writable: false
"""
    path = tmp_path / "config_dav_local.yaml"
    path.write_text(body, encoding="utf-8")
    return AppConfig.load(path)


def test_resolve_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    assert registry.resolve(None).id == "bob"
    assert registry.resolve("").id == "bob"


def test_resolve_by_display_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    assert registry.resolve("Eva").id == "eva"
    assert registry.resolve("eva").id == "eva"


def test_resolve_unknown_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    with pytest.raises(AccountNotFoundError):
        registry.resolve("Emma")


def test_resolve_many_deduplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    resolved = registry.resolve_many(["bob", "Bob", "eva"])
    assert [account.id for account in resolved] == ["bob", "eva"]


def test_require_writable_rejects_readonly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    with pytest.raises(AccountNotWritableError):
        registry.require_writable(registry.resolve("eva"))


def test_require_url_match_accepts_url_under_principal_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    # Various legitimate URLs rooted at /bob/, on the configured server.
    registry.require_url_match(bob, "https://example.com/bob/")
    registry.require_url_match(bob, "https://example.com/bob/calendar/")
    registry.require_url_match(bob, "https://example.com/bob/calendar/c1@calcard.ics")
    registry.require_url_match(bob, "https://example.com/bob/contacts/")


def test_require_url_match_rejects_cross_account_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    with pytest.raises(CrossAccountAccessError, match=r"account 'bob'.*configured ids: bob, eva"):
        registry.require_url_match(bob, "https://example.com/eva/contacts/c1.vcf")


def test_require_url_match_rejects_prefix_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`/bob/` must not match `/bobby/...` — the trailing slash anchors the segment."""
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    with pytest.raises(CrossAccountAccessError):
        registry.require_url_match(bob, "https://example.com/bobby/calendar/")


# ---------------------------------------------------------------------------
# Bug condition exploration tests (Property 1: Bug Condition — Unsafe URLs Are
# Rejected). These encode the EXPECTED POST-FIX behavior and are EXPECTED TO
# FAIL on the current UNFIXED guard, which performs only a raw path-prefix
# check and therefore accepts all four URLs. The failure confirms the bug:
# off-host, off-scheme, and `..`-traversal URLs slip through and would be sent
# to an HTTP client with the account's credentials attached.
# ---------------------------------------------------------------------------


def test_require_url_match_rejects_off_host_matching_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off-host URL whose path matches the principal must be rejected (req 2.1).

    base_url is ``https://example.com``; the URL points at ``attacker.tld`` but
    its path ``/eva/book/`` is rooted in eva's principal, so F accepts it and
    credentials would be sent off-host. F' must raise and name the configured
    host so the caller can self-correct.

    **Validates: Requirements 2.1**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    eva = registry.resolve("eva")
    with pytest.raises(CrossAccountAccessError, match=r"example\.com"):
        registry.require_url_match(eva, "https://attacker.tld/eva/book/")


def test_require_url_match_rejects_scheme_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """URL whose scheme differs from base_url must be rejected (req 2.2).

    base_url is ``http://dav.local``; the URL uses ``https`` against the same
    host with a principal-rooted path, so F accepts it. F' must raise.

    **Validates: Requirements 2.2**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config_dav_local(tmp_path))
    eva = registry.resolve("eva")
    with pytest.raises(CrossAccountAccessError):
        registry.require_url_match(eva, "https://dav.local/eva/book/")


def test_require_url_match_rejects_traversal_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`..` traversal that escapes the principal once normalized is rejected (req 2.3).

    base_url is ``http://dav.local``. Raw path ``/eva/../bob/cal/`` starts with
    ``/eva/`` (F accepts) but normalizes to ``/bob/cal/`` — a different
    principal. F' must raise.

    **Validates: Requirements 2.3**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config_dav_local(tmp_path))
    eva = registry.resolve("eva")
    with pytest.raises(CrossAccountAccessError):
        registry.require_url_match(eva, "http://dav.local/eva/../bob/cal/")


def test_require_url_match_rejects_off_host_base_url_shaped_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off-host URL with a base_url-shaped path must be rejected (edge, req 2.1).

    base_url is ``https://example.com``; ``http://localhost:5232/bob/contacts/``
    mismatches both scheme and host while its path is rooted in bob's
    principal, so F accepts it. F' must raise. This is the assertion migrated
    away from the happy-path test in task 4.

    **Validates: Requirements 2.1**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    with pytest.raises(CrossAccountAccessError):
        registry.require_url_match(bob, "http://localhost:5232/bob/contacts/")


# ---------------------------------------------------------------------------
# Preservation property tests (Property 2: Preservation — Legitimate And
# Already-Rejected URLs Are Unchanged). These pin every URL shape that
# legitimately passes (or already correctly rejects) today, so the fix can be
# proven not to disturb them. They are EXPECTED TO PASS on the current UNFIXED
# guard (observation-first methodology) and must keep passing after the fix.
# ---------------------------------------------------------------------------


def test_require_url_match_preserves_radicale_shaped_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Radicale-shaped resource URL matching base_url stays accepted (req 3.1).

    base_url is ``https://example.com``; the URL is exactly the shape Radicale
    returns from ``list_calendars`` — scheme + host match, resource file under
    the principal. F accepts it; F' must continue to accept it.

    **Validates: Requirements 3.1**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    registry.require_url_match(bob, "https://example.com/bob/calendar/c1@calcard.ics")


def test_require_url_match_preserves_relative_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative (netloc-less) URL rooted in the principal stays accepted (req 3.2).

    A path-only URL carries no netloc, so the scheme/host gate is skipped and
    only the path is checked. F accepts it; F' must continue to accept it.

    **Validates: Requirements 3.2**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    registry.require_url_match(bob, "/bob/calendar/")


def test_require_url_match_preserves_scheme_host_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact principal root with matching scheme+host stays accepted (req 3.3).

    base_url is ``https://example.com``; the URL is the principal root itself
    with a matching scheme and host. F accepts it; F' must continue to accept
    it.

    **Validates: Requirements 3.3**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    registry.require_url_match(bob, "https://example.com/bob/")


def test_require_url_match_preserves_nested_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A nested collection URL matching base_url stays accepted (req 3.1, 3.3).

    base_url is ``https://example.com``; a directory-style nested collection
    under the principal must survive path normalization (trailing slash
    re-appended). F accepts it; F' must continue to accept it.

    **Validates: Requirements 3.1, 3.3**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    registry.require_url_match(bob, "https://example.com/bob/calendar/")


def test_require_url_match_preserves_prefix_collision_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`/bob/` must keep rejecting `/bobby/...` after normalization (req 3.4).

    base_url is ``https://example.com``; the trailing-slash segment anchor must
    survive normalization so a prefix-collision host path still raises. F
    raises; F' must continue to raise.

    **Validates: Requirements 3.4**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    with pytest.raises(CrossAccountAccessError):
        registry.require_url_match(bob, "https://example.com/bobby/calendar/")


def test_require_url_match_preserves_not_rooted_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A not-rooted path keeps raising with the principal-path message (req 3.4).

    base_url is ``https://example.com``; ``/eva/...`` is not under bob's
    principal, so the original path-prefix gate raises. F raises; F' must
    continue to raise with the unchanged message naming the principal path and
    configured ids.

    **Validates: Requirements 3.4**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    with pytest.raises(CrossAccountAccessError, match=r"account 'bob'.*configured ids: bob, eva"):
        registry.require_url_match(bob, "https://example.com/eva/contacts/c1.vcf")


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/bob/../bob/calendar/",  # normalizes back to /bob/calendar/
        "https://example.com/bob/calendar/../calendar/",  # stays under /bob/
        "https://example.com/bob/./calendar/",  # . segment is a no-op
    ],
)
def test_require_url_match_preserves_traversal_that_stays_under_principal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """`..`/`.` segments that normalize back under the principal stay accepted.

    This pins the fix/preservation boundary: only the "normalized-stays-under-
    principal → accept" direction is asserted here (the "escapes → reject"
    direction lives in the exploration test). On UNFIXED code these are
    accepted because their raw path already starts with ``/bob/``; F' must
    continue to accept them because normalization keeps them under the
    principal.

    **Validates: Requirements 3.3**
    """
    monkeypatch.setenv("PW", "secret")
    registry = AccountRegistry(_config(tmp_path))
    bob = registry.resolve("bob")
    registry.require_url_match(bob, url)
