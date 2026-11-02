#!/usr/bin/env python3
"""Generate the root Claude Code marketplace from plugins/*/plugin.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate import ROOT, ValidationError, validate_manifest

MARKETPLACE = Path(".claude-plugin") / "marketplace.json"
NAME = "buvis-agent-plugins"
DESCRIPTION = "Portable agent plugins published by buvis."
OWNER = {"name": "buvis", "url": "https://github.com/buvis"}


def build_manifest(root: Path) -> str:
    """The exact text of the marketplace file for the plugins under root.

    Every plugins/*/plugin.json is checked with validate_manifest first; a
    plugin without a .claude-plugin/plugin.json gets no entry.
    """
    plugins = root / "plugins"
    folders = sorted(path for path in plugins.iterdir() if path.is_dir())
    entries: list[dict[str, object]] = []
    for plugin in folders:
        manifest = validate_manifest(plugin)
        if not (plugin / ".claude-plugin" / "plugin.json").is_file():
            continue
        entries.append(
            {
                "name": manifest["name"],
                "source": f"./plugins/{plugin.name}",
                "description": manifest["description"],
                "version": manifest["version"],
            },
        )
    catalog = {
        "name": NAME,
        "description": DESCRIPTION,
        "owner": OWNER,
        "plugins": entries,
    }
    return json.dumps(catalog, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 when the committed file differs",
    )
    args = parser.parse_args()
    target = ROOT / MARKETPLACE
    try:
        text = build_manifest(ROOT)
    except (ValidationError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.check:
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current != text:
            print(
                f"error: {target} is out of date; run python3 {Path(__file__).name}",
                file=sys.stderr,
            )
            return 1
        print(f"{target} is up to date.")
        return 0

    target.parent.mkdir(exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"Wrote {target}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
