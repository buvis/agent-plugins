"""Host capability types and probe dispatch by host_id."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

CAPABILITY_NAMES = ("identity", "delegation", "isolation", "interception")

UNAVAILABLE_NO_BINARY = "no_binary"
UNAVAILABLE_NO_AUTH = "no_auth"


@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    status: str
    reason: str | None


@dataclass(frozen=True)
class HostCapability:
    host_id: str
    statuses: dict[str, CapabilityStatus]


@dataclass(frozen=True)
class ProbeResult:
    host_id: str
    available: bool
    capability: HostCapability | None
    probed_at: str
    evidence_path: str | None


def _lazy_probe(module_name: str):
    def probe(*, project_root: Path) -> ProbeResult:
        return importlib.import_module(module_name).probe(project_root=project_root)

    return probe


# Lazy import: each entry imports its sibling adapter module on first call, so hosts imports without claude/codex/gemini.
_ADAPTERS = {
    "claude": _lazy_probe("claude"),
    "codex": _lazy_probe("codex"),
    "gemini": _lazy_probe("gemini"),
}


def probe_host(host_id: str, *, project_root: Path) -> ProbeResult:
    fn = _ADAPTERS.get(host_id)
    if fn is None:
        raise ValueError(f"unknown host_id: {host_id!r}")
    return fn(project_root=project_root)
