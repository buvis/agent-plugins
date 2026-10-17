"""Fetch reports (session fixture)."""

from src.util.retry import with_backoff


def fetch(url: str) -> bytes:
    return with_backoff(lambda: b"")
