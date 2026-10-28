"""Read and update bounded provenance rows without loading the map into a prompt.

This maintainer tool does not classify dependencies or certify review evidence.
Review the complete emitted diff through the normal task pipeline.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

INPUT_LIMIT = 18000
DIFF_LIMIT = 24000
IDENTITY_FIELDS = ("source_path", "source_line", "source_behavior_id", "source_anchors", "reference")


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()


def selected(row: dict, scope: dict) -> bool:
    if scope["collection"] == "assets":
        return row.get("destination_path") == scope["path"]
    return (row.get("source_path") == scope["path"]
            and type(row.get("source_line")) is int
            and scope["first"] <= row["source_line"] <= scope["last"])


def identity(row: dict, collection: str) -> str:
    fields = ("destination_path",) if collection == "assets" else IDENTITY_FIELDS
    return json.dumps({key: row[key] for key in fields if key in row}, sort_keys=True)


def snapshot(path: Path, collection: str, source: str, first: int = 1, last: int = 1000000) -> dict:
    if collection not in {"resource_edges", "assets"} or first < 1 or last < first:
        raise ValueError("invalid collection or line range")
    raw = path.read_bytes()
    document = json.loads(raw)
    scope = {"collection": collection, "path": source, "first": first, "last": last}
    result = {"map_sha256": hashlib.sha256(raw).hexdigest(), "scope": scope,
              "rows": [row for row in document[collection] if selected(row, scope)]}
    if len(encode(result)) > INPUT_LIMIT:
        raise ValueError("input budget exceeded; select fewer source lines")
    return result


def full_diff(path: Path, before: bytes, after: bytes) -> str:
    # Git handles repetitive multi-megabyte JSON without difflib's quadratic cost.
    with tempfile.TemporaryDirectory(prefix="map-diff-") as directory:
        temporary = Path(directory)
        (temporary / "before.json").write_bytes(before)
        (temporary / "after.json").write_bytes(after)
        result = subprocess.run(
            ["git", "diff", "--no-index", "--no-ext-diff", "--no-textconv",
             "--no-color", "--text", "--unified=3", "--", "before.json", "after.json"],
            cwd=temporary, capture_output=True, text=True, timeout=30,
        )
        if result.returncode not in (0, 1):
            raise ValueError(f"diff failed: {result.stderr.strip()}")
        lines = result.stdout.splitlines(keepends=True)
        for number, line in enumerate(lines):
            if line.startswith(("diff --git ", "--- ", "+++ ")):
                lines[number] = line.replace("a/before.json", str(path)).replace("b/after.json", str(path))
        return "".join(lines)


def apply(path: Path, before: dict, replacement: list[dict], *, write: bool) -> str:
    # A stable lock path covers read/check/replace, including competing helper calls.
    with path.with_suffix(path.suffix + ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != before["map_sha256"]:
            raise ValueError("stale snapshot; read the current slice again")
        scope = before["scope"]
        current = snapshot(path, scope["collection"], scope["path"], scope["first"], scope["last"])
        if current != before:
            raise ValueError("snapshot rows do not match the selected map data")
        if not isinstance(replacement, list) or any(not isinstance(row, dict) for row in replacement):
            raise ValueError("replacement must be an array of objects")
        if not all(selected(row, scope) for row in replacement):
            raise ValueError("replacement escapes selected scope")
        collection = scope["collection"]
        replacements = {identity(row, collection): row for row in replacement}
        if len(replacements) != len(replacement):
            raise ValueError("duplicate replacement identity")
        existing = {identity(row, collection) for row in before["rows"]}
        if not existing <= replacements.keys():
            raise ValueError("replacement removes or changes an existing identity")
        if collection == "assets" and len(replacement) != len(before["rows"]):
            raise ValueError("asset updates cannot create records")
        document = json.loads(raw)
        rows = document[collection]
        document[collection] = [replacements[identity(row, collection)] if selected(row, scope) else row
                                for row in rows]
        document[collection].extend(row for key, row in replacements.items() if key not in existing)
        rendered = encode(document)
        diff = full_diff(path, raw, rendered)
        if len(diff.encode()) > DIFF_LIMIT:
            raise ValueError("diff budget exceeded; split this update before applying")
        if write and rendered != raw:
            fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(rendered)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        return diff


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=Path(__file__).with_name("source-map.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("show")
    show.add_argument("collection", choices=["resource_edges", "assets"])
    show.add_argument("path")
    show.add_argument("--first", type=int, default=1)
    show.add_argument("--last", type=int, default=1000000)
    show.add_argument("--out", type=Path, required=True)
    update = commands.add_parser("apply")
    update.add_argument("--snapshot", type=Path, required=True)
    update.add_argument("--replacement", type=Path, required=True)
    update.add_argument("--write", action="store_true", help="Default is a read-only diff preview")
    args = parser.parse_args()
    try:
        if args.command == "show":
            result = snapshot(args.map, args.collection, args.path, args.first, args.last)
            if args.out.resolve() == args.map.resolve():
                raise ValueError("snapshot output must not overwrite the map")
            args.out.write_bytes(encode(result))
            print(f"{len(result['rows'])} rows; {len(encode(result))} bytes; {args.out}")
        else:
            diff = apply(args.map, json.loads(args.snapshot.read_bytes()),
                         json.loads(args.replacement.read_bytes()), write=args.write)
            if args.write:
                print(f"Applied {len(diff.encode())}-byte diff; preview need not be read twice.")
            else:
                print(diff, end="")
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"map_slice: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
