"""The helper map generator CLI validates its inputs and writes the map atomically.

Shared synthetic builders live in test_helper_provenance.py.
"""

from __future__ import annotations

import copy
import json
import os
import re
import resource
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
from test_helper_provenance import (
    CLI,
    HELPER_TARGETS,
    REFRESHED,
    TOOL,
    UNRELATED,
    asset_row,
    by_key,
    canon,
    digest,
    encode,
    load_tool,
    make_repo,
    owner_row,
    run_tool,
    synthetic_map,
    valid_receipts,
    write_receipts,
)

EVIDENCE_FIELDS = set(asset_row("x")["evidence"])
REVISION = re.compile(r"^[0-9a-f]{40}$")
FSIZE_LIMIT = 4096
DEFAULT_RECEIPTS = (
    "docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json"
)


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return load_tool()


def tamper_writer(dispositions: dict) -> None:
    row = next(
        r for r in dispositions["functions"] if r["key"] == "custody:write_marker"
    )
    row.update(
        scope="extracted",
        owner_scope="helper-facet",
        controller_exclusion=None,
        target_module="plugins/autopilot/scripts/custody.py",
    )


def tamper_duplicate_key(dispositions: dict) -> None:
    dispositions["functions"].append(copy.deepcopy(dispositions["functions"][0]))


def tamper_unknown_id(dispositions: dict) -> None:
    extra = copy.deepcopy(dispositions["regressions"][0])
    extra["source_regression_id"] = (
        CLI + "test_custody.py::test_absent_from_regression_cases"
    )
    dispositions["regressions"].append(extra)


def tamper_duplicate_id(dispositions: dict) -> None:
    dispositions["regressions"].append(copy.deepcopy(dispositions["regressions"][0]))


@pytest.mark.parametrize(
    "tamper",
    [tamper_writer, tamper_duplicate_key, tamper_unknown_id, tamper_duplicate_id],
    ids=["helper-owned-writer", "duplicate-key", "unknown-id", "duplicate-id"],
)
def test_tampered_dispositions_are_never_kept(
    tool: ModuleType, tmp_path: Path, tamper
) -> None:
    clean = tool.apply(synthetic_map("1" * 40), None)
    tampered = copy.deepcopy(clean)
    tamper(tampered["helper_dispositions"])
    try:
        regenerated = tool.apply(tampered, None)
    except ValueError:
        regenerated = None
    if regenerated is not None:
        assert canon(regenerated["helper_dispositions"]) == canon(
            clean["helper_dispositions"]
        )
    mapping = make_repo(tmp_path, "1" * 40, "t", tampered)
    before = mapping.read_bytes()
    result = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert result.returncode != 0
    assert mapping.read_bytes() == before


@pytest.mark.parametrize(
    "identity",
    [
        CLI + "test_custody.py::test_writes_marker",
        CLI + "test_review_close_carry.py::test_carries",
    ],
    ids=["custody", "review-close"],
)
def test_mixed_module_regression_given_a_helper_facet_is_rejected(
    tool: ModuleType, tmp_path: Path, identity: str
) -> None:
    tampered = tool.apply(synthetic_map("1" * 40), None)
    row = next(
        r
        for r in tampered["helper_dispositions"]["regressions"]
        if r["source_regression_id"] == identity
    )
    row.update(owner_scope="helper-facet", disposition="helper-facet")
    with pytest.raises(ValueError, match=re.escape(identity)):
        tool.apply(tampered, None)
    mapping = make_repo(tmp_path, "1" * 40, "m", tampered)
    before = mapping.read_bytes()
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode != 0
    assert mapping.read_bytes() == before


def receipts_variant(change) -> dict:
    data = valid_receipts()
    change(data)
    return data


@pytest.mark.parametrize(
    "receipts",
    [
        receipts_variant(lambda d: d["real_host"].update(status="passed")),
        receipts_variant(lambda d: d["tasks"][1].update(passed=0)),
        receipts_variant(lambda d: d["tasks"][0].update(passed=True)),
        receipts_variant(lambda d: d["tasks"][1].update(passed="7")),
        receipts_variant(lambda d: d["tasks"][0].pop("passed")),
        receipts_variant(lambda d: d.update(tasks=[])),
        receipts_variant(lambda d: d.update(prd="00012")),
        receipts_variant(lambda d: d.update(schema_version=2)),
        receipts_variant(lambda d: d.update(schema_version=True)),
        receipts_variant(lambda d: d["tasks"][0].update(tests="  ")),
        receipts_variant(lambda d: d["tasks"][1].update(command="")),
        receipts_variant(lambda d: d.update(package_revision="A" * 40)),
    ],
    ids=[
        "real-host-passed",
        "zero-passed",
        "bool-passed",
        "string-passed",
        "missing-passed",
        "empty-tasks",
        "wrong-prd",
        "future-schema",
        "bool-schema",
        "blank-tests",
        "blank-command",
        "bad-package-revision",
    ],
)
def test_receipts_claiming_success_without_counts_or_a_real_host_are_rejected(
    tool: ModuleType, tmp_path: Path, receipts: dict
) -> None:
    with pytest.raises(ValueError):
        tool.apply(synthetic_map("1" * 40), receipts)
    accepted = tool.apply(synthetic_map("1" * 40), valid_receipts())
    assert "helper_dispositions" in accepted
    mapping = make_repo(tmp_path, "1" * 40, "r")
    before = mapping.read_bytes()
    path = write_receipts(tmp_path, receipts)
    result = run_tool(
        "--map", mapping, "--root", tmp_path, "--receipts", path, cwd=tmp_path
    )
    assert result.returncode != 0
    assert mapping.read_bytes() == before


def assets_by_path(document: dict) -> dict:
    return by_key(document["assets"], "destination_path")


def assert_authored_row(row: dict, template: dict) -> None:
    assert row["disposition"] == "adapted"
    assert isinstance(row["adaptation_reason"], str)
    assert row["adaptation_reason"].strip()
    assert set(row["entry_point_gate"]) == set(template["entry_point_gate"])
    cases = row["acceptance_cases"]
    assert cases
    for case in cases:
        assert isinstance(case["case_id"], str) and case["case_id"].strip()
        assert isinstance(case["expected_outcome"], str)
        assert case["expected_outcome"].strip()


def assert_receipt_evidence(evidence: dict, root: Path, receipts: Path | None) -> None:
    if receipts is None:
        assert evidence["status"] == "unavailable"
        return
    assert set(evidence) == EVIDENCE_FIELDS
    assert evidence["status"] == "passed"
    assert evidence["artifact_id"] == receipts.relative_to(root).as_posix()
    assert evidence["artifact_sha256"] == digest(receipts.read_bytes())
    revision = evidence["tested_package_revision"]
    assert revision is None or REVISION.match(revision), revision


def assert_refreshed_assets(assets: dict, root: Path, receipts: Path | None) -> None:
    helper_evidence = assets[sorted(HELPER_TARGETS)[0]]["evidence"]
    revision = None
    if receipts is not None:
        revision = json.loads(receipts.read_bytes()).get("package_revision")
        assert assets[REFRESHED[0]]["evidence"] == helper_evidence
    for relative in REFRESHED:
        sha = digest((root / relative).read_bytes())
        assert assets[relative]["destination_blob_sha256"] == sha
    for relative in REFRESHED[1:]:
        evidence = assets[relative]["evidence"]
        if revision is None:
            assert evidence["status"] == "unavailable", relative
            assert evidence["tested_package_revision"] is None, relative
            continue
        assert evidence == {
            "status": "passed",
            "artifact_id": relative,
            "artifact_sha256": digest((root / relative).read_bytes()),
            "tested_package_revision": revision,
        }, relative


def assert_helper_assets(document: dict, root: Path, receipts: Path | None) -> None:
    assets = assets_by_path(document)
    template = assets[REFRESHED[0]]
    for relative in sorted(HELPER_TARGETS):
        row = assets[relative]
        assert set(row) == set(template), relative
        assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
        assert row["destination_blob_sha256"] == digest((root / relative).read_bytes())
        assert_authored_row(row, template)
        assert_receipt_evidence(row["evidence"], root, receipts)
    assert_refreshed_assets(assets, root, receipts)
    assert not [p for p in assets if "/controller/" in p]
    skill = assets["plugins/autopilot/skills/work/SKILL.md"]
    assert canon(skill) == canon(
        asset_row(skill["destination_path"], "skills/work/SKILL.md")
    )


def assert_helper_owners(document: dict) -> None:
    owners = by_key(document["authored_file_owners"], "path")
    for relative in HELPER_TARGETS:
        row = owners[relative]
        assert set(row) == set(owner_row(relative))
        assert row["delivery_prd"] == "00013"
        assert row["owner_repository"] == "buvis/agent-plugins"
        assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
        assert row["acceptance_cases"] and all(
            c["case_id"].strip() and c["expected_outcome"].strip()
            for c in row["acceptance_cases"]
        )
    for relative in (REFRESHED[0], REFRESHED[2]):
        assert owners[relative] == owner_row(relative)


def test_cli_writes_canonical_map_with_helper_assets_owners_and_receipts(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    mapping = make_repo(root, "4" * 40, "first")
    receipts = write_receipts(root, {**valid_receipts(), "package_revision": "a" * 40})
    receipt_bytes = receipts.read_bytes()
    elsewhere = tmp_path / "cwd"
    elsewhere.mkdir()
    result = run_tool(
        "--map", mapping, "--root", root, "--receipts", receipts, cwd=elsewhere
    )
    assert result.returncode == 0, result.stderr
    written = mapping.read_bytes()
    document = json.loads(written)
    assert written == encode(document)
    assert document["helper_dispositions"]["source_commit"] == "4" * 40
    assert receipts.read_bytes() == receipt_bytes
    assert_helper_assets(document, root, receipts)
    assert_helper_owners(document)
    for key in UNRELATED:
        assert canon(document[key]) == canon(synthetic_map("4" * 40)[key]), key
    again = run_tool(
        "--map", mapping, "--root", root, "--receipts", receipts, cwd=elsewhere
    )
    assert again.returncode == 0, again.stderr
    assert mapping.read_bytes() == written


def test_cli_without_receipts_records_unavailable_evidence(tmp_path: Path) -> None:
    mapping = make_repo(tmp_path, "5" * 40, "bare")
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert_helper_assets(json.loads(mapping.read_bytes()), tmp_path, None)


def test_cli_without_receipts_uses_the_default_receipts_file_when_present(
    tmp_path: Path,
) -> None:
    mapping = make_repo(tmp_path, "5" * 40, "default")
    receipts = tmp_path / DEFAULT_RECEIPTS
    receipts.parent.mkdir(parents=True)
    receipts.write_text(
        json.dumps({**valid_receipts(), "package_revision": "b" * 40}) + "\n"
    )
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert_helper_assets(json.loads(mapping.read_bytes()), tmp_path, receipts)
    check = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert check.returncode == 0, check.stderr


def test_asset_digests_follow_the_selected_root(tmp_path: Path) -> None:
    default_root, other_root = tmp_path / "default", tmp_path / "other"
    mapping = make_repo(default_root, "6" * 40, "default-bytes")
    copy_map = make_repo(other_root, "6" * 40, "other-bytes")
    assert run_tool("--map", mapping, cwd=tmp_path).returncode == 0
    assert (
        run_tool("--map", copy_map, "--root", default_root, cwd=tmp_path).returncode
        == 0
    )
    from_default = assets_by_path(json.loads(mapping.read_bytes()))
    from_explicit = assets_by_path(json.loads(copy_map.read_bytes()))
    for relative in ("plugins/autopilot/scripts/custody.py", REFRESHED[1]):
        expected = digest((default_root / relative).read_bytes())
        assert from_default[relative]["destination_blob_sha256"] == expected
        assert from_explicit[relative]["destination_blob_sha256"] == expected
        assert expected != digest((other_root / relative).read_bytes())


def test_check_exits_zero_only_for_an_already_generated_map(tmp_path: Path) -> None:
    mapping = make_repo(tmp_path, "7" * 40, "check")
    before = mapping.read_bytes()
    stale = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert stale.returncode != 0
    assert mapping.read_bytes() == before
    assert run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path).returncode == 0
    generated = mapping.read_bytes()
    fresh = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert fresh.returncode == 0, fresh.stderr
    assert mapping.read_bytes() == generated
    (tmp_path / "plugins/autopilot/scripts/findings.py").write_text("# changed bytes\n")
    drifted = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert drifted.returncode != 0
    assert mapping.read_bytes() == generated


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory write permission")
def test_failed_write_leaves_the_old_map_in_place(tmp_path: Path) -> None:
    mapping = make_repo(tmp_path, "8" * 40, "atomic")
    before = mapping.read_bytes()
    listing = sorted(os.listdir(mapping.parent))
    mapping.parent.chmod(0o555)
    try:
        result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    finally:
        mapping.parent.chmod(0o755)
    assert result.returncode != 0
    assert mapping.read_bytes() == before
    assert sorted(os.listdir(mapping.parent)) == listing
    retry = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert retry.returncode == 0, retry.stderr
    assert "helper_dispositions" in json.loads(mapping.read_bytes())
    assert sorted(os.listdir(mapping.parent)) == listing


def cap_file_size() -> None:
    # Python ignores SIGXFSZ, so a write past the cap raises OSError (EFBIG).
    _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    resource.setrlimit(resource.RLIMIT_FSIZE, (FSIZE_LIMIT, hard))


def tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_write_failing_midway_leaves_the_old_map_and_no_temp_file(
    tmp_path: Path,
) -> None:
    mapping = make_repo(tmp_path, "8" * 40, "midway")
    before = mapping.read_bytes()
    listing = tree(tmp_path)
    result = subprocess.run(
        [sys.executable, str(TOOL), "--map", str(mapping), "--root", str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=300,
        preexec_fn=cap_file_size,
    )
    assert result.returncode != 0
    assert mapping.read_bytes() == before
    assert tree(tmp_path) == listing
    retry = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert retry.returncode == 0, retry.stderr
    assert len(mapping.read_bytes()) > FSIZE_LIMIT
    assert tree(tmp_path) == listing
