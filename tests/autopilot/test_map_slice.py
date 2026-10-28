"""Bounded maintenance must not discard the rest of the provenance map."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("map_slice", ROOT / "tools/autopilot/map_slice.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.fixture
def mapping_path(tmp_path: Path) -> Path:
    path = tmp_path / "map.json"
    path.write_bytes(MODULE.encode({
        "schema_version": 1,
        "assets": [{"destination_path": "plugins/autopilot/CHANGELOG.md", "evidence": {"status": "passed"}}],
        "behaviors": [{"source_behavior_id": "P01", "text": "untouched"}],
        "regression_cases": [{"source_regression_id": "test_one"}],
        "resource_edges": [
            {"source_path": "skills/a.md", "source_line": 3, "reference": "one.py", "kind": "informational-provenance"},
            {"source_path": "skills/a.md", "source_line": 20, "reference": "two.py", "kind": "external-capability"},
            {"source_behavior_id": "P01", "reference": "tool", "kind": "external-capability"},
        ],
    }))
    return path


def test_update_and_append_preserve_every_unselected_record(mapping_path: Path) -> None:
    before = json.loads(mapping_path.read_bytes())
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    replacement = copy.deepcopy(snapshot["rows"])
    replacement[0]["kind"] = "external-capability"
    replacement.append({"source_path": "skills/a.md", "source_line": 4, "reference": "new.py", "kind": "external-capability"})
    diff = MODULE.apply(mapping_path, snapshot, replacement, write=False)
    assert mapping_path.read_bytes() == MODULE.encode(before)
    assert "+" in diff and "new.py" in diff
    MODULE.apply(mapping_path, snapshot, replacement, write=True)
    after = json.loads(mapping_path.read_bytes())
    assert after["resource_edges"] == [replacement[0], *before["resource_edges"][1:], replacement[1]]
    after.pop("resource_edges")
    before.pop("resource_edges")
    assert after == before


def test_stale_snapshot_refuses_without_writing(mapping_path: Path) -> None:
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    mapping_path.write_bytes(mapping_path.read_bytes() + b"\n")
    before = mapping_path.read_bytes()
    with pytest.raises(ValueError, match="stale"):
        MODULE.apply(mapping_path, snapshot, snapshot["rows"], write=True)
    assert mapping_path.read_bytes() == before


@pytest.mark.parametrize("replacement", [
    [],
    [{"source_path": "skills/other.md", "source_line": 3, "reference": "one.py"}],
    [{"source_path": "skills/a.md", "source_line": 30, "reference": "one.py"}],
    [{"source_path": "skills/a.md", "source_line": 3, "reference": "changed.py"}],
], ids=["deletion", "other-source", "other-lines", "changed-identity"])
def test_scope_and_existing_identity_cannot_be_changed(mapping_path: Path, replacement: list[dict]) -> None:
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    before = mapping_path.read_bytes()
    with pytest.raises(ValueError):
        MODULE.apply(mapping_path, snapshot, replacement, write=True)
    assert mapping_path.read_bytes() == before


def test_duplicate_identity_refuses(mapping_path: Path) -> None:
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    with pytest.raises(ValueError, match="duplicate"):
        MODULE.apply(mapping_path, snapshot, snapshot["rows"] * 2, write=True)


def test_oversized_diff_refuses_before_write(mapping_path: Path) -> None:
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    replacement = copy.deepcopy(snapshot["rows"])
    replacement[0]["reason"] = "x" * 25000
    before = mapping_path.read_bytes()
    with pytest.raises(ValueError, match="diff budget"):
        MODULE.apply(mapping_path, snapshot, replacement, write=True)
    assert mapping_path.read_bytes() == before


def test_asset_slice_preserves_all_other_data(mapping_path: Path) -> None:
    before = json.loads(mapping_path.read_bytes())
    snapshot = MODULE.snapshot(mapping_path, "assets", "plugins/autopilot/CHANGELOG.md")
    replacement = copy.deepcopy(snapshot["rows"])
    replacement[0]["evidence"]["artifact_id"] = "reviewed-receipt.json"
    MODULE.apply(mapping_path, snapshot, replacement, write=True)
    before["assets"] = replacement
    assert json.loads(mapping_path.read_bytes()) == before


def test_snapshot_cannot_forge_scope_or_rows(mapping_path: Path) -> None:
    snapshot = MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)
    snapshot["rows"][0]["reference"] = "forged.py"
    with pytest.raises(ValueError, match="snapshot"):
        MODULE.apply(mapping_path, snapshot, snapshot["rows"], write=True)


def test_large_snapshot_requires_a_smaller_slice(mapping_path: Path) -> None:
    document = json.loads(mapping_path.read_bytes())
    document["resource_edges"][0]["reason"] = "x" * 19000
    mapping_path.write_bytes(MODULE.encode(document))
    with pytest.raises(ValueError, match="input budget"):
        MODULE.snapshot(mapping_path, "resource_edges", "skills/a.md", 1, 10)


def test_diff_preserves_data_that_looks_like_a_temporary_filename(mapping_path: Path) -> None:
    snapshot = MODULE.snapshot(mapping_path, "assets", "plugins/autopilot/CHANGELOG.md")
    replacement = copy.deepcopy(snapshot["rows"])
    replacement[0]["evidence"]["artifact_id"] = "a/before.json b/after.json"
    diff = MODULE.apply(mapping_path, snapshot, replacement, write=False)
    assert '"artifact_id": "a/before.json b/after.json"' in diff
