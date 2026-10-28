#!/usr/bin/env python3
"""Delegate maintainer policy export to the portable package facade."""

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    facade = Path(__file__).resolve().parents[2] / "plugins" / "autopilot" / "scripts" / "autopilot.py"
    main = runpy.run_path(str(facade))["main"]
    raise SystemExit(main(["--export-policy", *sys.argv[1:]]))
