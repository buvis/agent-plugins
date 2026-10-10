"""Spec numbers: the next free one, and numbers used twice. Reads names only, never contents."""

from __future__ import annotations

import os
import re
from pathlib import Path

NUMBER = re.compile(r"^(\d{5})-")
FIX = (
    "Renumber the newer item and every place that cites it, before it is cited further."
)


def subfolders(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else []


def numbered_items(
    repo: Path,
    config: dict[str, object],
    stages: tuple[str, ...] = ("new", "processed"),
) -> list[Path]:
    """Intake items: numbered folders one level under each stage, or two inside a group."""
    items = []
    for stage in stages:
        for entry in subfolders(repo / str(config["root"]) / "intake" / stage):
            if NUMBER.match(entry.name):
                items.append(entry)
            else:
                items += [p for p in subfolders(entry) if NUMBER.match(p.name)]
    return items


def spec_folders(repo: Path, config: dict[str, object]) -> list[Path]:
    """Numbered folders directly under the specs folder; Kiro-native unnumbered ones are skipped."""
    return [
        p for p in subfolders(repo / str(config["specsDir"])) if NUMBER.match(p.name)
    ]


def scanned_names(repo: Path, config: dict[str, object]) -> list[str]:
    """Every file and folder name, at any depth, in the numberScan folders."""
    names = []
    for folder in config.get("numberScan", []):
        for _, dirs, files in os.walk(repo / str(folder)):
            names += dirs + files
    return names


def next_number(repo: Path, config: dict[str, object]) -> str:
    """One more than the highest five-digit prefix in use; read-only."""
    names = [p.name for p in numbered_items(repo, config) + spec_folders(repo, config)]
    names += scanned_names(repo, config)
    numbers = [int(m[1]) for name in names if (m := NUMBER.match(name))]
    return f"{max(numbers, default=0) + 1:05d}"


def number_clashes(repo: Path, config: dict[str, object]) -> list[dict[str, str]]:
    """A number used by two intake items, or by two spec folders."""
    findings = []
    for kind, folders in (
        ("intake items", numbered_items(repo, config)),
        ("spec folders", spec_folders(repo, config)),
    ):
        seen: dict[str, list[Path]] = {}
        for folder in folders:
            seen.setdefault(NUMBER.match(folder.name)[1], []).append(folder)
        for number, clash in sorted(seen.items()):
            if len(clash) > 1:
                paths = ", ".join(p.relative_to(repo).as_posix() for p in clash)
                findings.append(
                    {
                        "level": "error",
                        "file": clash[-1].relative_to(repo).as_posix(),
                        "rule": "number-clashes",
                        "message": f"number {number} is used by two {kind}: {paths}",
                        "fix": FIX,
                    },
                )
    return findings
