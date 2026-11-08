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


CAPABILITY_STATUSES = ("supported", "unavailable", "unimplemented")


@dataclass(frozen=True)
class ProbeResult:
    """`capability` is None exactly when `available` is False.

    `probe_kind` is always "static" in this package: every adapter probe is a
    binary-on-PATH plus auth-presence observation. A live invocation is AP 00017's
    certification work and OV 00059's managed launch, never this package's, so
    `certified` is always False here and no field of this record may be read as
    evidence that a host executed anything.

    `unavailable_reason` is non-None exactly when `available` is False.
    `authenticated` records auth presence for an available host (None when the
    host is unavailable, so auth was never checked).
    """

    host_id: str
    available: bool
    capability: HostCapability | None
    probed_at: str
    evidence_path: str | None
    probe_kind: str = "static"
    unavailable_reason: str | None = None
    authenticated: bool | None = None
    certified: bool = False

    def __post_init__(self) -> None:
        """Enforces EVERY invariant this record documents, so a defaulted
        construction site cannot serialise a contradictory state. A documented
        guarantee that construction can violate is not a guarantee."""
        if self.available:
            if self.capability is None or self.unavailable_reason is not None:
                raise ValueError(f"{self.host_id}: available result must carry a capability and no reason")
            if not isinstance(self.authenticated, bool):
                raise ValueError(f"{self.host_id}: available result must record auth presence")
        else:
            if self.capability is not None or self.unavailable_reason is None:
                raise ValueError(f"{self.host_id}: unavailable result must carry a reason and no capability")
            if self.authenticated is not None:
                raise ValueError(f"{self.host_id}: unavailable result never checked auth")
        if self.probe_kind != "static":
            raise ValueError(f"{self.host_id}: this package performs only static probes")
        if self.certified is not False:
            raise ValueError(f"{self.host_id}: this package never certifies a host")


def unavailable(host_id: str, *, probed_at: str, reason: str) -> ProbeResult:
    """The single construction site for an unavailable host: `capability` is
    always None and `reason` is always recorded, so no adapter can break the
    ProbeResult invariant or drop the no_binary/no_auth distinction."""
    return ProbeResult(
        host_id=host_id,
        available=False,
        capability=None,
        probed_at=probed_at,
        evidence_path=None,
        unavailable_reason=reason,
        authenticated=None,
    )


def statuses_from(
    implemented: frozenset[str], *, authenticated: bool
) -> dict[str, CapabilityStatus]:
    """Capability statuses for an available host, derived from the adapter's
    own `IMPLEMENTED_CAPABILITIES`.

    A name the adapter does not implement is "unimplemented" with reason None
    (the status already says why). A name it does implement is "supported" when
    the host is authenticated, else "unavailable" with reason `no_auth`. The
    returned mapping always has exactly `CAPABILITY_NAMES` as its keys, in that
    order.

    "supported" is deliberately NOT "available". This package performs only
    static probes, so the strongest honest claim is "this adapter implements
    this capability and the host is authenticated" - never "this capability was
    observed working". A reader wanting the latter needs AP 00017's
    certification, and `ProbeResult.certified` is False precisely to say so.
    """
    statuses: dict[str, CapabilityStatus] = {}
    for name in CAPABILITY_NAMES:
        if name not in implemented:
            statuses[name] = CapabilityStatus(
                name=name, status="unimplemented", reason=None
            )
        elif authenticated:
            statuses[name] = CapabilityStatus(name=name, status="supported", reason=None)
        else:
            statuses[name] = CapabilityStatus(
                name=name, status="unavailable", reason=UNAVAILABLE_NO_AUTH
            )
    return statuses


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
