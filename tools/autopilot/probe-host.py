#!/usr/bin/env python3
"""CLI wrapper around `hosts.probe_host`, writing real probe evidence under
docs/dev/tmp/autopilot/probes/<host_id>-<ts>.json (never ~/.claude or any
live user config). Maintainer-only tool outside the packaged plugin
surface - it does not go through autopilot.py's dispatcher."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot" / "scripts"),
)

import hosts
from log_sink_refusal import _pinned_parent_fd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("host_id")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    result = hosts.probe_host(args.host_id, project_root=project_root)
    payload = json.dumps(dataclasses.asdict(result), indent=2)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    probes_dir = project_root / "docs" / "dev" / "tmp" / "autopilot" / "probes"
    filename = f"{args.host_id}-{timestamp}.json"

    parent_fd = _pinned_parent_fd(probes_dir, project_root)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        fd = os.open(filename, flags, 0o666, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload.encode("utf-8"))

    print(payload)


if __name__ == "__main__":
    main()
