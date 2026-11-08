#!/usr/bin/env python3
"""Generates per-host compatibility bundles from contracts/hosts.json and the
live probe results. Writes plugins/autopilot/compatibility/<host_id>.json for
each host declared in the contract, containing exactly the capabilities the
live adapter reports as available. A declared capability the live adapter
reports as unimplemented aborts the build with a non-zero exit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot" / "scripts"),
)

import hosts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    contract_path = project_root / "plugins" / "autopilot" / "contracts" / "hosts.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    compatibility_dir = project_root / "plugins" / "autopilot" / "compatibility"

    for host_id, declaration in contract["hosts"].items():
        declared_capabilities = declaration["capabilities"]
        probe_result = hosts.probe_host(host_id, project_root=project_root)
        if probe_result.capability is None:
            continue
        statuses = probe_result.capability.statuses

        for name in declared_capabilities:
            if statuses[name].status == "unimplemented":
                print(
                    f"host {host_id!r}: declared capability {name!r} is unimplemented",
                    file=sys.stderr,
                )
                sys.exit(1)

        available = sorted(
            name for name in declared_capabilities if statuses[name].status == "available"
        )
        bundle = {"host_id": host_id, "capabilities": available}

        compatibility_dir.mkdir(parents=True, exist_ok=True)
        bundle_path = compatibility_dir / f"{host_id}.json"
        bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
