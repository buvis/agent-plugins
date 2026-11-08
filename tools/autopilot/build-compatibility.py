#!/usr/bin/env python3
"""Generates per-host compatibility bundles from contracts/hosts.json and each
adapter's own declared-and-implemented capability set. Writes
plugins/autopilot/compatibility/<host_id>.json for each host declared in the
contract, containing exactly the declared capabilities the adapter implements.
The tool never probes, so the bundles are identical on every machine. A
declared capability the adapter does not implement aborts the build with a
non-zero exit and leaves no bundle behind."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot" / "scripts"),
)


def _implemented(host_id: str) -> frozenset[str]:
    """The adapter's own IMPLEMENTED_CAPABILITIES - a code fact, read without
    probing, so the generated bundle cannot depend on this machine."""
    return importlib.import_module(host_id).IMPLEMENTED_CAPABILITIES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    contract_path = project_root / "plugins" / "autopilot" / "contracts" / "hosts.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    compatibility_dir = project_root / "plugins" / "autopilot" / "compatibility"

    bundles = {}
    for host_id, declaration in contract["hosts"].items():
        declared = set(declaration["capabilities"])
        overclaimed = sorted(declared - _implemented(host_id))
        if overclaimed:
            print(
                f"host {host_id!r}: declared capability {overclaimed[0]!r} is unimplemented",
                file=sys.stderr,
            )
            sys.exit(1)
        bundles[host_id] = {
            "host_id": host_id,
            "capabilities": sorted(declared),
            "probe_kind": "static",
        }

    for host_id, bundle in bundles.items():
        compatibility_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = compatibility_dir / f"{host_id}.json"
        bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
