#!/usr/bin/env python3
"""Export the pinnable controller contract bundle of an autopilot plugin root.

Writes <plugin-root>/contracts/controller-v1.json from plugin.json and the raw
bytes of the controller schema and fixtures. --check writes nothing and exits 1
when the bundle on disk is missing, not a regular file, or differs.
Self-contained stdlib script; it never reads live workflow state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot"
TARGET = Path("contracts") / "controller-v1.json"
SCHEMA = Path("contracts") / "controller" / "workflow-v1.json"
FIXTURES = Path("contracts") / "controller" / "fixtures-v1.json"
# The export tests check these equal literal sets in the test and are a subset
# of what `controller/main.py --json contract` reports. Kept as a literal copy
# rather than an import of autopilot_state.protocol (this script is
# self-contained stdlib and never reads live workflow state) - the
# authoritative definition this must track is
# plugins/autopilot/controller/autopilot_state/protocol.py's
# OWNER_OPERATIONS / public_contract().
OPERATIONS = [
    "workflow.open",
    "owner.acquire",
    "owner.release",
    "owner.recover",
    "prd.enter",
    "phase.handoff",
    "prd.stall",
    "prd.park",
    "prd.defer",
    "prd.complete",
    "task.replace",
    "task.start",
    "task.finish",
    "task.attempt",
    "lane.route",
    "policy.bind",
    "job.plan",
    "job.claim",
    "job.record_exit",
    "job.next",
]
CAPABILITIES = [
    "workflow.core.v1",
    "workflow.lifecycle.v1",
    "workflow.tasks.v1",
    "workflow.policy.v1",
    "workflow.jobs.v1",
]
LIMIT = 16777216


def checked(root: Path, relative: Path, regular: bool = True) -> Path:
    """root / relative with no symlink component; a regular file under LIMIT."""
    path = root
    for part in relative.parts:
        path = path / part
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"{path} is a symlink")
    if regular and not (stat.S_ISREG(info.st_mode) and info.st_size < LIMIT):
        raise ValueError(f"{path} is not a regular file under {LIMIT} bytes")
    return path


def build_bundle(root: Path) -> bytes:
    manifest = json.loads(checked(root, Path("plugin.json")).read_bytes())
    version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(version, str) or not version:
        raise ValueError("plugin.json version must be a non-empty string")
    bundle = {
        "protocol_major": 1,
        "package_version": version,
        "schema_digest": hashlib.sha256(checked(root, SCHEMA).read_bytes()).hexdigest(),
        "fixture_digest": hashlib.sha256(
            checked(root, FIXTURES).read_bytes()
        ).hexdigest(),
        "operations": OPERATIONS,
        "capabilities": CAPABILITIES,
    }
    return (json.dumps(bundle, indent=2, sort_keys=True) + "\n").encode("utf-8")


def matches(target: Path, expected: bytes) -> bool:
    try:
        info = target.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode) or info.st_size != len(expected):
        return False
    return target.read_bytes() == expected


def write_atomic(target: Path, data: bytes, mode: int) -> None:
    fd, temp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except BaseException:
        os.unlink(temp)
        raise


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.plugin_root
    try:
        data = build_bundle(root)
        checked(root, TARGET.parent, regular=False)
        if args.check:
            if matches(root / TARGET, data):
                return 0
            print(f"error: {root / TARGET} is stale or missing", file=sys.stderr)
            return 1
        # Same permission bits as the sibling contracts, not mkstemp's 0600.
        mode = stat.S_IMODE((root / SCHEMA).stat().st_mode) & 0o666
        write_atomic(root / TARGET, data, mode)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
