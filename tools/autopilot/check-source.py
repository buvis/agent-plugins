#!/usr/bin/env python3
"""Audit the frozen autopilot inventory against an explicitly supplied Git source."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath


PIN = "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48"
REPOSITORY = "https://github.com/buvis/claude-autopilot"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _index(rows: list[dict], key: str) -> dict[str, dict]:
    result = {row[key]: row for row in rows}
    _require(len(result) == len(rows), f"Duplicate {key}")
    return result


def _sections(blob: bytes) -> list[dict]:
    lines = blob.decode("utf-8").splitlines(keepends=True)
    headings = []
    counts: Counter[str] = Counter()
    fenced = False
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match or fenced:
            continue
        heading = match[2]
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")
        anchor = slug + (f"-{counts[slug]}" if counts[slug] else "")
        counts[slug] += 1
        headings.append((len(match[1]), heading, anchor, number))
    result = []
    for index, (level, heading, anchor, start) in enumerate(headings):
        end = next(
            (row[3] - 1 for row in headings[index + 1 :] if row[0] <= level),
            len(lines),
        )
        result.append({
            "anchor": anchor, "heading": heading, "start_line": start,
            "end_line": end,
            "sha256": hashlib.sha256("".join(lines[start - 1 : end]).encode()).hexdigest(),
        })
    return result


def _regressions(path: str, blob: bytes) -> list[dict]:
    common = {
        "source_path": path,
        "git_blob_id": hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest(),
        "source_blob_sha256": hashlib.sha256(blob).hexdigest(),
    }
    if not path.endswith(".py"):
        return [{
            **common, "source_regression_id": path,
            "test_identity": "script-or-module",
            "case_sha256": common["source_blob_sha256"],
        }]
    text = blob.decode("utf-8")
    lines = text.splitlines(keepends=True)
    result = []
    for node in ast.parse(text, filename=path).body:
        if isinstance(node, ast.ClassDef):
            candidates = [(f"{node.name}::{child.name}", child) for child in node.body
                          if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            candidates = [(node.name, node)]
        else:
            continue
        for identity, function in candidates:
            if not function.name.startswith("test"):
                continue
            start = min([function.lineno] + [d.lineno for d in function.decorator_list])
            end = function.end_lineno
            decorators = [ast.get_source_segment(text, d) for d in function.decorator_list]
            result.append({
                **common, "source_regression_id": f"{path}::{identity}",
                "test_identity": identity, "start_line": start, "end_line": end,
                "case_sha256": hashlib.sha256("".join(lines[start - 1 : end]).encode()).hexdigest(),
                "parameterization": [d for d in decorators if "parametrize" in d],
            })
    return result


def _load_snapshots(tools: Path) -> tuple[dict, dict]:
    pin = json.loads((tools / "source-pin.json").read_bytes())
    inventory_bytes = (tools / "source-inventory.json").read_bytes()
    inventory = json.loads(inventory_bytes)
    mapping = json.loads((tools / "source-map.json").read_bytes())
    _require(pin == {
        "schema_version": 1, "source_repository": REPOSITORY,
        "commit": PIN, "pinned_at": "2026-10-24",
    }, "Unexpected pinned source identity")
    for document in (inventory, mapping):
        _require(document["schema_version"] == 1 and document["source_commit"] == PIN,
                 "Snapshot does not identify the pinned source")
    _require(inventory["source_repository"] == REPOSITORY, "Source repository mismatch")
    _require(mapping["source_inventory_sha256"] == hashlib.sha256(inventory_bytes).hexdigest(),
             "Source inventory digest mismatch")

    root = tools.parent.parent
    for name, group in (("expanded", "expanded_inventory_ids"),
                        ("principal", "principal_inventory_ids")):
        basis = inventory["inventory_basis"][name]
        path = (root / basis["path"]).resolve()
        _require(path.is_relative_to(root), f"Invalid inventory basis path: {name}")
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == basis["sha256"],
                 f"Inventory basis digest mismatch: {name}")
        _require(basis["count"] == len(inventory[group]), f"Inventory basis count mismatch: {name}")
    return inventory, mapping


def _git(source_root: Path, *arguments: str) -> bytes:
    # Do not let the caller's Git environment redirect the explicitly named root.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_NO_REPLACE_OBJECTS="1")
    completed = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(source_root), *arguments],
        capture_output=True, env=environment, timeout=60,
    )
    if completed.returncode:
        raise ValueError(f"Pinned source Git read failed: {completed.stderr.decode(errors='replace').strip()}")
    return completed.stdout


def _source_files(source_root: Path, inventory: dict) -> tuple[dict, dict, dict]:
    _require(_git(source_root, "cat-file", "-t", PIN).strip() == b"commit", "Pinned object is not a commit")
    commit = _git(source_root, "cat-file", "commit", PIN)
    _require(hashlib.sha1(f"commit {len(commit)}\0".encode() + commit).hexdigest() == PIN,
             "Pinned commit object digest mismatch")
    tree = {}
    for record in _git(source_root, "ls-tree", "-r", "-z", PIN).split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode().split()
        path = raw_path.decode("utf-8")
        if path.split("/", 1)[0] in {"agents", "dev", "hooks", "skills"} or path in {
            "LICENSE", "README.md", "plugin.json", ".claude-plugin/plugin.json",
        }:
            _require(kind == "blob", f"Non-blob source entry: {path} ({mode})")
            tree[path] = object_id
    files = _index(inventory["source_files"], "source_path")
    _require(set(tree) == set(files),
             f"Source file set mismatch: missing={sorted(set(tree) - set(files))}, "
             f"unknown={sorted(set(files) - set(tree))}")
    blobs = {}
    sections = {}
    for path, row in files.items():
        relative = PurePosixPath(path)
        _require(not relative.is_absolute() and ".." not in relative.parts,
                 f"Invalid source path: {path}")
        blob = _git(source_root, "show", "--no-ext-diff", "--no-textconv", f"{PIN}:{path}")
        blob_id = hashlib.sha1(f"blob {len(blob)}\0".encode() + blob).hexdigest()
        _require(row["git_blob_id"] == tree[path] == blob_id,
                 f"Git blob identity mismatch: {path}")
        _require(row["blob_sha256"] == hashlib.sha256(blob).hexdigest()
                 and row["size_bytes"] == len(blob), f"Source blob digest/size mismatch: {path}")
        blobs[path] = blob
        if path.endswith(".md"):
            sections[path] = _sections(blob)

    return files, blobs, sections


def _audit_assets(inventory: dict, mapping: dict, files: dict, sections: dict) -> int:
    assets = _index(inventory["assets"], "source_asset_id")
    _require(set(assets) == set(inventory["required_asset_ids"])
             and len(assets) == len(inventory["required_asset_ids"]), "Required asset set mismatch")
    mapped_assets = _index([r for r in mapping["assets"] if r["source_asset_id"] is not None],
                           "source_asset_id")
    _require(set(assets) == set(mapped_assets), "Mapped asset set mismatch")
    for identity, row in assets.items():
        path = row["source_path"]
        for key in ("git_blob_id", "blob_sha256"):
            _require(row[key] == files[path][key], f"Asset {key} mismatch: {identity}")
        _require(row["sections"] == sections.get(path, []), f"Asset sections mismatch: {identity}")
        mapped = mapped_assets[identity]
        _require(mapped["source_blob_sha256"] == row["blob_sha256"], f"Mapped asset digest mismatch: {identity}")
        plan = _index(mapped["section_plan"], "source_anchor")
        _require({key: value["source_sha256"] for key, value in plan.items()}
                 == {s["anchor"]: s["sha256"] for s in row["sections"]},
                 f"Mapped asset sections mismatch: {identity}")

    return len(assets)


def _behavior_rows(inventory: dict, mapping: dict) -> tuple[dict, dict]:
    behaviors = _index(inventory["behaviors"], "source_behavior_id")
    expected = []
    for group, count in (("expanded_inventory_ids", 1034), ("principal_inventory_ids", 42),
                         ("configuration_field_ids", 302), ("code_only_ids", 3)):
        _require(len(inventory[group]) == count, f"Inventory group size mismatch: {group}")
        expected.extend(inventory[group])
    _require(len(set(expected)) == len(expected) and set(expected) == set(behaviors)
             == set(inventory["expected_behavior_ids"])
             and len(inventory["expected_behavior_ids"]) == len(expected), "Behavior set mismatch")
    mapped_behaviors = _index(mapping["behaviors"], "source_behavior_id")
    _require(set(mapped_behaviors) == set(behaviors), "Mapped behavior set mismatch")
    return behaviors, mapped_behaviors


def _audit_behaviors(behaviors: dict, mapped_behaviors: dict, blobs: dict, sections: dict) -> None:
    for identity, row in behaviors.items():
        _require(row["source_anchors"] and row["source_anchors"] == mapped_behaviors[identity]["source_anchors"],
                 f"Behavior source anchors mismatch: {identity}")
        for anchor in row["source_anchors"]:
            path = anchor["path"]
            lines = blobs[path].decode("utf-8").splitlines(keepends=True)
            start, end = anchor["start_line"], anchor["end_line"]
            _require(1 <= start <= end <= len(lines), f"Behavior range mismatch: {identity} {path}")
            content = "".join(lines[start - 1 : end])
            if "source_text" in anchor:
                content = content.rstrip("\r\n")
            _require(anchor["sha256"] == hashlib.sha256(content.encode()).hexdigest(),
                     f"Behavior digest mismatch: {identity} {path}")
            if anchor["anchor"] == "file":
                _require(start == 1 and end == len(lines), f"Whole-file anchor mismatch: {identity}")
            elif "heading" in anchor:
                section = {key: value for key, value in anchor.items() if key != "path"}
                _require(section in sections[path], f"Behavior section mismatch: {identity} {path}")
            else:
                _require(anchor["anchor"] == f"L{start}" and start == end
                         and anchor["source_text"] == lines[start - 1].rstrip("\r\n"),
                         f"Behavior line anchor mismatch: {identity} {path}")



def _audit_regressions(inventory: dict, mapping: dict, blobs: dict) -> int:
    regressions = _index(inventory["regression_cases"], "source_regression_id")
    actual = _index([case for path, blob in blobs.items()
                     if PurePosixPath(path).name.startswith("test_")
                     for case in _regressions(path, blob)], "source_regression_id")
    _require(actual == regressions, "Pinned regression identities, ranges, parameterization or digests mismatch")
    _require(set(actual) == set(inventory["source_regression_ids"])
             and len(actual) == len(inventory["source_regression_ids"]), "Regression ID set mismatch")
    mapped_regressions = _index(mapping["regression_cases"], "source_regression_id")
    _require(set(mapped_regressions) == set(actual), "Mapped regression set mismatch")
    for identity, row in actual.items():
        for key in ("source_path", "test_identity", "source_blob_sha256", "case_sha256"):
            _require(mapped_regressions[identity][key] == row[key], f"Mapped regression {key} mismatch: {identity}")
    return len(actual)


def _audit(source_root: Path) -> None:
    inventory, mapping = _load_snapshots(Path(__file__).resolve().parent)
    files, blobs, sections = _source_files(source_root, inventory)
    asset_count = _audit_assets(inventory, mapping, files, sections)
    behaviors, mapped_behaviors = _behavior_rows(inventory, mapping)
    _audit_behaviors(behaviors, mapped_behaviors, blobs, sections)
    regression_count = _audit_regressions(inventory, mapping, blobs)
    print(f"Source audit passed: {PIN}; {len(files)} files, {asset_count} assets, "
          f"{len(behaviors)} behaviors, {regression_count} regression cases")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Git repository containing the exact pinned source commit")
    arguments = parser.parse_args()
    try:
        _audit(arguments.source_root.resolve())
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, subprocess.TimeoutExpired) as error:
        print(f"Source audit failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
