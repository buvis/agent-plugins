"""Explicit-source build verification; never part of the offline test suite."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path("/Users/bob/git/src/github.com/buvis/agent-plugins")
SOURCE = Path("/Users/bob/git/src/github.com/buvis/claude-autopilot")
PIN = "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48"
REPORT = ROOT / "docs/dev/project-management/autopilot/reports/00012-task-5-explicit-mutations.json"
RESULTS: list[dict] = []


def run(argv: list[str], *, cwd: Path | None = None, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, input=data, capture_output=True, timeout=300)


def checked(argv: list[str], *, data: bytes | None = None) -> bytes:
    result = run(argv, data=data)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout


def record(name: str, tool: Path, source: Path, cwd: Path, accepted: bool) -> None:
    argv = [sys.executable, str(tool), "--source-root", str(source)]
    result = run(argv, cwd=cwd)
    row = {"name": name, "argv": argv, "cwd": str(cwd), "exit_code": result.returncode,
           "expected": "accepted" if accepted else "rejected",
           "stdout": result.stdout.decode(errors="replace"),
           "stderr": result.stderr.decode(errors="replace")}
    row["passed"] = (result.returncode == 0) == accepted
    RESULTS.append(row)
    REPORT.write_text(json.dumps({"pin": PIN, "cases": RESULTS}, indent=2) + "\n")
    print(name, result.returncode, row["passed"], flush=True)


def copy_target(destination: Path, inventory: dict, mapping: dict) -> Path:
    directory = destination / "tools/autopilot"
    directory.mkdir(parents=True)
    for name in ("check-source.py", "source-pin.json"):
        shutil.copy2(ROOT / "tools/autopilot" / name, directory / name)
    for basis in inventory["inventory_basis"].values():
        if isinstance(basis, dict) and "path" in basis:
            path = destination / basis["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / basis["path"], path)
    inventory_bytes = (json.dumps(inventory, indent=2, ensure_ascii=False) + "\n").encode()
    (directory / "source-inventory.json").write_bytes(inventory_bytes)
    mapping = copy.deepcopy(mapping)
    mapping["source_inventory_sha256"] = hashlib.sha256(inventory_bytes).hexdigest()
    (directory / "source-map.json").write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n")
    return directory / "check-source.py"


def make_source(destination: Path) -> None:
    checked(["git", "init", "--quiet", str(destination)])
    objects = checked(["git", "-C", str(SOURCE), "rev-list", "--objects", "--no-object-names", PIN + "^{tree}"])
    objects += (PIN + "\n").encode()
    pack = checked(["git", "-C", str(SOURCE), "pack-objects", "--stdout"], data=objects)
    checked(["git", "-C", str(destination), "unpack-objects"], data=pack)
    checked(["git", "-C", str(destination), "update-ref", "refs/heads/master", PIN])
    checked(["git", "-C", str(destination), "symbolic-ref", "HEAD", "refs/heads/master"])
    checked(["git", "-C", str(destination), "reset", "--hard", PIN])


def altered_snapshot(name: str, inventory: dict, mapping: dict, base: Path, fixture: Path, cwd: Path) -> None:
    changed = copy.deepcopy(inventory)
    if name == "changed-later-file-digest":
        changed["source_files"][-1]["blob_sha256"] = "0" * 64
    elif name == "changed-section-digest":
        asset = next(row for row in changed["assets"] if row["sections"])
        asset["sections"][0]["sha256"] = "0" * 64
    elif name == "changed-behavior-anchor-digest":
        changed["behaviors"][-1]["source_anchors"][0]["sha256"] = "0" * 64
    elif name == "changed-regression-case-digest":
        case = next(row for row in reversed(changed["regression_cases"]) if row["test_identity"] != "script-or-module")
        case["case_sha256"] = "0" * 64
    elif name == "changed-inventory-basis-digest":
        changed["inventory_basis"]["expanded"]["sha256"] = "0" * 64
    tool = copy_target(base / name, changed, mapping)
    record(name, tool, fixture, cwd, False)


def main() -> int:
    inventory = json.loads((ROOT / "tools/autopilot/source-inventory.json").read_text())
    mapping = json.loads((ROOT / "tools/autopilot/source-map.json").read_text())
    with tempfile.TemporaryDirectory(prefix="ap00012-provenance-") as directory:
        base = Path(directory)
        cwd = base / "unrelated-cwd"
        cwd.mkdir()
        tool = ROOT / "tools/autopilot/check-source.py"
        record("real-pin-from-unrelated-cwd", tool, SOURCE, cwd, True)
        fixture = base / "copied-exact-pin"
        make_source(fixture)
        record("copied-exact-pin-from-unrelated-cwd", tool, fixture, cwd, True)
        later = next(row for row in reversed(inventory["source_files"]) if row["git_blob_id"] != inventory["source_files"][0]["git_blob_id"])
        oid = later["git_blob_id"]
        object_path = fixture / ".git/objects" / oid[:2] / oid[2:]
        original = object_path.read_bytes()
        object_path.unlink()
        checked(["git", "-C", str(fixture), "cat-file", "-e", PIN + "^{commit}"])
        record("pin-present-later-blob-missing", tool, fixture, cwd, False)
        object_path.write_bytes(original)
        decoded = zlib.decompress(original)
        corrupted = decoded[:-1] + bytes([decoded[-1] ^ 1])
        assert len(corrupted) == len(decoded)
        object_path.write_bytes(zlib.compress(corrupted))
        record("same-size-later-source-object-corruption", tool, fixture, cwd, False)
        object_path.write_bytes(original)
        baseline = copy_target(base / "relocated-target", inventory, mapping)
        record("relocated-target-valid-snapshots", baseline, fixture, cwd, True)
        for name in ("changed-later-file-digest", "changed-section-digest", "changed-behavior-anchor-digest",
                     "changed-regression-case-digest", "changed-inventory-basis-digest"):
            altered_snapshot(name, inventory, mapping, base, fixture, cwd)
    return 0 if all(row["passed"] for row in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
