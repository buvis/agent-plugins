"""Check the five-digit citations of the specs and intake items for rot.

Scans every Markdown file under the configured specs folder and `<root>/intake/`
(the workspace of `.agents/specflow.json`, with the defaults `.kiro/specs` and
`.kiro/specflow`) and resolves each five-digit `NNNNN-` citation against the spec
folders and the intake items. A citation that resolves to neither is a finding.
A line holding the literal token `link-ok:` is exempt. Home paths, absolute
paths, and `[[...]]` links are warned about and never resolved.

Usage: python3 scripts/check_links.py [--root DIR] [--json]

Called from `references/review/cross-spec.md` of the spec-workflow skill; paths
are relative to the skill folder. Exit 0 when clean, 1 on a dangling citation or
a scan error; warnings never change the exit code.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from specflow_helper.config import ConfigError, load_config
from specflow_helper.structural import MACHINE_PATH, WIKI_LINK

# [SR-RVX-072] The citation pattern skips a five-digit run that follows a digit, a slash, a dot, or a dash, so a longer number or a path segment is not a citation.
CITATION = re.compile(r"(?<![\d/.-])(\d{5})-")
# [SR-RVX-071] A token holding a glob, a template slot, an ellipsis, or an NNNNN, XXXX, or YYYY placeholder is skipped; trailing punctuation is stripped before the lookup.
PLACEHOLDER = re.compile(r"[*?<>{}$]|\.\.\.|NNNNN|XXXX|YYYY")
WAIVER = "link-ok:"
# [SR-RVX-075] The tests of this script are unittest cases run on a fixture tree inside the repository that holds them; no other framework and no fixture outside that repository.


# [SR-RVX-069] Only the configured specs folder and `<root>/intake/` are scanned, read through the workspace config; the filtering is in code, not left to the reviewer.
def sources(root: Path, config: dict) -> tuple[list[Path], list[str]]:
    """The Markdown files to scan, and the scan errors of links that leave the repository.

    Links are followed only while they stay inside the repository; a folder seen
    once is not entered again, so a link to an ancestor cannot loop.
    """
    files: list[Path] = []
    errors: list[str] = []
    real_root = root.resolve()
    seen: set[Path] = set()

    def outside(path: Path) -> bool:
        if path.resolve().is_relative_to(real_root):
            return False
        errors.append(
            f"{path.relative_to(root).as_posix()}: leads outside the repository, not read"
        )
        return True

    for base in (root / str(config["specsDir"]), root / str(config["root"]) / "intake"):
        if not base.is_dir():
            continue
        for here, folders, names in os.walk(base, followlinks=True):
            for name in sorted(folders):
                folder = Path(here) / name
                if outside(folder) or folder.resolve() in seen:
                    folders.remove(name)
                seen.add(folder.resolve())
            for name in names:
                path = Path(here) / name
                if path.suffix == ".md" and not outside(path):
                    files.append(path)
    return sorted(files), errors


# [SR-RVX-070] A citation resolves when a spec folder or an intake item under `new/` or `processed/` (in a group folder too) starts with its five digits.
# [SR-RVX-074] The folders are listed once per run and the numbers kept, so a citation repeated a hundred times costs one directory walk.
@functools.cache
def resolvable_numbers(root: Path, specs_dir: str, workspace: str) -> frozenset[str]:
    numbers: set[str] = set()
    folders = [root / specs_dir]
    intake = root / workspace / "intake"
    for bucket in ("new", "processed"):
        if (intake / bucket).is_dir():
            folders.append(intake / bucket)
            folders += [p for p in (intake / bucket).iterdir() if p.is_dir()]
    for folder in folders:
        if folder.is_dir():
            numbers |= {
                p.name[:5] for p in folder.iterdir() if re.match(r"\d{5}-", p.name)
            }
    return frozenset(numbers)


def scan_file(
    path: Path, root: Path, numbers: frozenset[str]
) -> tuple[list[dict], list[dict], list[str]]:
    findings: list[dict] = []
    warnings: list[dict] = []
    shown = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return [], [], [f"{shown}: unreadable ({error})"]
    for number, line in enumerate(lines, start=1):
        if WAIVER in line:
            continue
        for match in CITATION.finditer(line):
            token = line[match.start() :].split()[0].rstrip(".,;:!?)`")
            if PLACEHOLDER.search(token):
                continue
            if match[1] not in numbers:
                findings.append(
                    {
                        "file": shown,
                        "line": number,
                        "target": f"{match[1]}- (no spec or intake item)",
                        "citing_line": line.strip(),
                    }
                )
        # [SR-RVX-079] A home path or an absolute path is a warning, never resolved: it means nothing on another machine.
        # [SR-RVX-078] A `[[...]]` link is a warning, never resolved: it names a store outside the repository.
        for match in (*MACHINE_PATH.finditer(line), *WIKI_LINK.finditer(line)):
            warnings.append(
                {
                    "file": shown,
                    "line": number,
                    "target": match[0],
                    "citing_line": line.strip(),
                }
            )
    return findings, warnings, []


def run(root: Path) -> dict:
    """The findings, warnings, and scan errors of one run; the shape `--json` prints."""
    result: dict = {"findings": [], "warnings": [], "scan_errors": []}
    if not root.is_dir():
        result["scan_errors"].append(f"{root}: not a folder")
        return result
    try:
        config = load_config(root)
    except ConfigError as error:
        result["scan_errors"].append(str(error))
        return result
    files, errors = sources(root, config)
    result["scan_errors"] += errors
    numbers = resolvable_numbers(root, str(config["specsDir"]), str(config["root"]))
    for path in files:
        findings, warnings, errors = scan_file(path, root, numbers)
        result["findings"] += findings
        result["warnings"] += warnings
        result["scan_errors"] += errors
    return result


# [SR-RVX-073] Exit 0 when clean and 1 on a finding or a scan error; `--json` prints `findings`, `warnings`, and `scan_errors`, and an unreadable file is a scan error, not a crash.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--root",
        default=".",
        help="the repository root (default: the working directory)",
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    args = parser.parse_args(argv)
    result = run(Path(args.root))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["findings"]:
            print(
                f"{item['file']}:{item['line']} -> missing {item['target']}\n    | {item['citing_line']}"
            )
        for item in result["warnings"]:
            print(
                f"{item['file']}:{item['line']} -> warning {item['target']} does not resolve on another machine"
            )
        for error in result["scan_errors"]:
            print(f"SCAN ERROR: {error}", file=sys.stderr)
        print(
            f"{len(result['findings'])} dangling, {len(result['warnings'])} warnings, "
            f"{len(result['scan_errors'])} scan errors"
        )
    return 1 if result["findings"] or result["scan_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
