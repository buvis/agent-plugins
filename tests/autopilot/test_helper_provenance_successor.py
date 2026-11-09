"""The helper map generator applies an explicit AP00018 successor receipt.

README.md, CHANGELOG.md and the controller assets changed after AP00013, so a
successor receipt bound to a later revision owns them while the AP00013
receipt stays immutable. Shared synthetic builders live in
test_helper_provenance.py.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import ModuleType

import pytest
from test_helper_provenance import (
    REFRESHED,
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
)

REPORTS = "docs/dev/project-management/autopilot/reports/"
AP00013 = REPORTS + "00013-helper-delivery-receipts.json"
SUCCESSOR = REPORTS + "00018-v2-controller-delivery-receipts.json"
OVERRIDE = "reports/successor-override.json"
CONTRACT = "plugins/autopilot/contracts/controller-v1.json"
CONTROLLER = (
    "plugins/autopilot/controller/main.py",
    "plugins/autopilot/contracts/controller/state.json",
)
SHARED = REFRESHED[1:]
# Prefix, suffix and substring near-misses of controller paths are not
# controller assets.
NEAR_MISSES = (
    "plugins/autopilot/contracts/controller-v2.json",
    "plugins/autopilot/controllers/main.py",
    "plugins/autopilot/scripts/controller_shim.py",
    "docs/controller-notes.md",
)
NOT_APPLICABLE_GATE = {
    "status": "not-applicable",
    "operation": "none",
    "entry_point": None,
}
PLANNED = {
    "status": "planned",
    "artifact_id": None,
    "artifact_sha256": None,
    "tested_package_revision": None,
}
REVISIONS = ("c" * 40, "0123456789abcdef0123456789abcdef01234567")


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return load_tool()


def write_json(path: Path, data: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path.read_bytes()


def build_repo(root: Path, tag: str) -> Path:
    document = synthetic_map("4" * 40)
    for path in CONTROLLER + NEAR_MISSES:
        document["assets"].append({**asset_row(path), "evidence": dict(PLANNED)})
    document["authored_file_owners"] += [owner_row(p, "00018") for p in CONTROLLER]
    mapping = make_repo(root, "4" * 40, tag, document)
    for path in (CONTRACT, *NEAR_MISSES):
        write_json(root / path, {"tag": f"{tag} {path}"})
    write_json(root / AP00013, {**valid_receipts(), "package_revision": "a" * 40})
    return mapping


def valid_successor(root: Path, revision: str = REVISIONS[0]) -> dict:
    tests = (
        "tests/autopilot/test_controller_bundle.py",
        "tests/autopilot/test_helper_provenance_successor.py",
    )
    return {
        "schema_version": 1,
        "prd": "00018",
        "supersedes": {
            "artifact_id": AP00013,
            "artifact_sha256": digest((root / AP00013).read_bytes()),
        },
        "package_revision": revision,
        "paths": [*SHARED, CONTRACT, *CONTROLLER],
        "tasks": [
            {"tests": tests[0], "command": f"pytest -q {tests[0]}", "passed": 31},
            {"tests": tests[1], "command": f"pytest -q {tests[1]}", "passed": 9},
        ],
        "real_host": {
            "status": "unavailable",
            "reason": "No real host is reachable from the sandbox.",
        },
    }


def generate(
    tool: ModuleType,
    root: Path,
    mapping: Path,
    successor: dict | None = None,
    successor_id: str = SUCCESSOR,
) -> dict:
    document = json.loads(mapping.read_bytes())
    raw = (root / AP00013).read_bytes()
    artifact = {"artifact_id": AP00013, "artifact_sha256": digest(raw)}
    if successor is None:
        return tool.apply(document, json.loads(raw), root, artifact)
    written = write_json(root / successor_id, successor)
    return tool.apply(
        document,
        json.loads(raw),
        root,
        artifact,
        successor=successor,
        successor_artifact={
            "artifact_id": successor_id,
            "artifact_sha256": digest(written),
        },
    )


def assert_contract_rows(document: dict) -> None:
    rows = [r for r in document["assets"] if r["destination_path"] == CONTRACT]
    assert len(rows) == 1, rows
    row = rows[0]
    assert set(row) == set(asset_row(CONTRACT))
    assert row["source_asset_id"] is None
    assert row["source_blob_sha256"] is None
    # A new authored asset: adapted, no section plan, no entry point.
    assert row["disposition"] == "adapted"
    assert row["section_plan"] == []
    assert row["entry_point_gate"] == NOT_APPLICABLE_GATE
    cases = row["acceptance_cases"]
    assert isinstance(cases, list) and cases, cases
    assert any(case.get("status") == row["evidence"]["status"] for case in cases)
    owners = [r for r in document["authored_file_owners"] if r["path"] == CONTRACT]
    assert len(owners) == 1, owners
    assert set(owners[0]) == set(owner_row(CONTRACT))
    assert owners[0]["delivery_prd"] == "00018"
    assert owners[0]["owner_repository"] == "buvis/agent-plugins"
    assert owners[0]["source_asset_id"] is None
    assert owners[0]["acceptance_cases"]


def assert_other_rows_unchanged(baseline: dict, document: dict) -> None:
    moved = {*SHARED, *CONTROLLER, CONTRACT}
    kept = {"destination_blob_sha256", "evidence"}

    def rest(doc: dict) -> list[dict]:
        return [r for r in doc["assets"] if r["destination_path"] not in moved]

    assert canon(rest(document)) == canon(rest(baseline))
    old, new = (by_key(d["assets"], "destination_path") for d in (baseline, document))
    for path in (*SHARED, *CONTROLLER):
        trimmed = [
            {k: v for k, v in rows[path].items() if k not in kept}
            for rows in (old, new)
        ]
        assert canon(trimmed[0]) == canon(trimmed[1]), path
    owners = [r for r in document["authored_file_owners"] if r["path"] != CONTRACT]
    assert canon(owners) == canon(baseline["authored_file_owners"])
    assert set(document) == set(baseline)
    for key in set(baseline) - {"assets", "authored_file_owners"}:
        assert canon(document[key]) == canon(baseline[key]), key
    assert new[REFRESHED[0]]["evidence"]["artifact_id"] == AP00013
    for path in NEAR_MISSES:
        assert new[path]["evidence"] == PLANNED, path


@pytest.mark.parametrize("revision", REVISIONS)
def test_valid_successor_moves_shared_docs_and_controller_rows_to_it(
    tool: ModuleType, tmp_path: Path, revision: str
) -> None:
    root = tmp_path / revision[:4]
    mapping = build_repo(root, revision[:4])
    baseline = generate(tool, root, mapping)
    document = generate(tool, root, mapping, valid_successor(root, revision))
    assets = by_key(document["assets"], "destination_path")
    for path in SHARED:
        sha = digest((root / path).read_bytes())
        assert assets[path]["destination_blob_sha256"] == sha, path
        assert assets[path]["evidence"] == {
            "status": "passed",
            "artifact_id": path,
            "artifact_sha256": sha,
            "tested_package_revision": revision,
        }, path
    cited = {
        "status": "passed",
        "artifact_id": SUCCESSOR,
        "artifact_sha256": digest((root / SUCCESSOR).read_bytes()),
        "tested_package_revision": revision,
    }
    for path in (*CONTROLLER, CONTRACT):
        sha = digest((root / path).read_bytes())
        assert assets[path]["destination_blob_sha256"] == sha, path
        assert assets[path]["evidence"] == cited, path
    assert_contract_rows(document)
    assert_other_rows_unchanged(baseline, document)


# `paths` is binding: the successor certifies exactly the paths it lists.
NARROW = {
    "contract-only": (CONTRACT,),
    "changelog-and-one-controller": (SHARED[1], CONTROLLER[1]),
}


@pytest.mark.parametrize("listed", NARROW.values(), ids=NARROW.keys())
def test_successor_certifies_only_the_paths_it_lists(
    tool: ModuleType, tmp_path: Path, listed: tuple[str, ...]
) -> None:
    mapping = build_repo(tmp_path, "narrow")
    baseline = generate(tool, tmp_path, mapping)
    successor = {**valid_successor(tmp_path), "paths": list(listed)}
    document = generate(tool, tmp_path, mapping, successor)
    old, new = (by_key(d["assets"], "destination_path") for d in (baseline, document))
    cited = {
        "status": "passed",
        "artifact_id": SUCCESSOR,
        "artifact_sha256": digest((tmp_path / SUCCESSOR).read_bytes()),
        "tested_package_revision": REVISIONS[0],
    }
    for path in (*SHARED, *CONTROLLER):
        if path not in listed:
            # Unlisted rows keep exactly what the generator gives them today.
            assert canon(new[path]) == canon(old[path]), path
            continue
        sha = digest((tmp_path / path).read_bytes())
        assert new[path]["destination_blob_sha256"] == sha, path
        own = {**cited, "artifact_id": path, "artifact_sha256": sha}
        assert new[path]["evidence"] == (cited if path in CONTROLLER else own), path
    for path in set(SHARED) - set(listed):
        assert new[path]["evidence"]["tested_package_revision"] == "a" * 40, path
    for path in set(CONTROLLER) - set(listed):
        assert new[path]["evidence"] == PLANNED, path
    if CONTRACT in listed:
        assert_contract_rows(document)
        assert new[CONTRACT]["evidence"] == cited
    else:
        assert CONTRACT not in new
        owners = {row["path"] for row in document["authored_file_owners"]}
        assert CONTRACT not in owners
    assert_other_rows_unchanged(baseline, document)


INVALID = {
    "wrong-prd": lambda d: d.update(prd="00013"),
    "prd-near-miss": lambda d: d.update(prd="000180"),
    "bool-schema": lambda d: d.update(schema_version=True),
    "future-schema": lambda d: d.update(schema_version=2),
    "upper-revision": lambda d: d.update(package_revision="C" * 40),
    "short-revision": lambda d: d.update(package_revision="c" * 39),
    "long-revision": lambda d: d.update(package_revision="c" * 41),
    "revision-trailing-junk": lambda d: d.update(package_revision="c" * 40 + "-x"),
    "revision-trailing-newline": lambda d: d.update(package_revision="c" * 40 + "\n"),
    "empty-tasks": lambda d: d.update(tasks=[]),
    "zero-passed": lambda d: d["tasks"][1].update(passed=0),
    "negative-passed": lambda d: d["tasks"][1].update(passed=-1),
    "string-passed": lambda d: d["tasks"][0].update(passed="31"),
    "bool-passed": lambda d: d["tasks"][0].update(passed=True),
    "blank-tests": lambda d: d["tasks"][1].update(tests="  "),
    "blank-command": lambda d: d["tasks"][0].update(command=""),
    "real-host-passed": lambda d: d["real_host"].update(status="passed"),
    "real-host-skipped": lambda d: d["real_host"].update(status="skipped"),
    "real-host-blank-status": lambda d: d["real_host"].update(status=""),
    "blank-real-host-reason": lambda d: d["real_host"].update(reason=" "),
    "supersedes-digest-mismatch": lambda d: d["supersedes"].update(
        artifact_sha256=digest(b"other receipts")
    ),
    "supersedes-other-artifact": lambda d: d["supersedes"].update(
        artifact_id=AP00013 + ".bak"
    ),
    "missing-supersedes": lambda d: d.pop("supersedes"),
    "empty-paths": lambda d: d.update(paths=[]),
    "duplicate-path": lambda d: d["paths"].append(SHARED[0]),
    "non-string-path": lambda d: d["paths"].append(7),
    "helper-path": lambda d: d["paths"].append(REFRESHED[0]),
    "contract-near-miss": lambda d: d["paths"].append(NEAR_MISSES[0]),
    "controller-near-miss": lambda d: d["paths"].append(NEAR_MISSES[1]),
    "controller-substring-script": lambda d: d["paths"].append(NEAR_MISSES[2]),
    "controller-substring-doc": lambda d: d["paths"].append(NEAR_MISSES[3]),
    "dotdot-escape-from-controller": lambda d: d["paths"].append(
        "plugins/autopilot/controller/../scripts/autopilot.py"
    ),
    "absolute-controller-path": lambda d: d["paths"].append("/" + CONTROLLER[0]),
    "readme-suffix-near-miss": lambda d: d["paths"].append(SHARED[0] + ".bak"),
}


@pytest.mark.parametrize("change", INVALID.values(), ids=INVALID.keys())
def test_successor_breaking_a_rule_is_refused_without_writing(
    tool: ModuleType, tmp_path: Path, change
) -> None:
    mapping = build_repo(tmp_path, "bad")
    good = valid_successor(tmp_path)
    accepted = generate(tool, tmp_path, mapping, good, OVERRIDE)
    readme = by_key(accepted["assets"], "destination_path")[SHARED[0]]
    assert readme["evidence"]["tested_package_revision"] == REVISIONS[0]
    bad = copy.deepcopy(good)
    change(bad)
    with pytest.raises(ValueError):
        generate(tool, tmp_path, mapping, bad, OVERRIDE)
    write_json(tmp_path / OVERRIDE, bad)
    before = mapping.read_bytes()
    receipts = (tmp_path / AP00013).read_bytes()
    result = run_tool(
        "--map",
        mapping,
        "--root",
        tmp_path,
        "--successor-receipts",
        tmp_path / OVERRIDE,
        cwd=tmp_path,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "update_helper_map failed" in result.stderr
    assert mapping.read_bytes() == before
    assert (tmp_path / AP00013).read_bytes() == receipts


@pytest.mark.parametrize(
    "text",
    ["[]\n", "{not json\n", "", "null\n"],
    ids=["array", "malformed", "empty", "null"],
)
def test_default_successor_that_is_not_a_json_object_is_refused(
    tmp_path: Path, text: str
) -> None:
    mapping = build_repo(tmp_path, "strict")
    (tmp_path / SUCCESSOR).write_text(text)
    before = mapping.read_bytes()
    receipts = (tmp_path / AP00013).read_bytes()
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "update_helper_map failed" in result.stderr
    assert mapping.read_bytes() == before
    assert (tmp_path / AP00013).read_bytes() == receipts


def test_cli_applies_the_default_successor_idempotently(
    tool: ModuleType, tmp_path: Path
) -> None:
    root, elsewhere = tmp_path / "repo", tmp_path / "cwd"
    mapping = build_repo(root, "cli")
    elsewhere.mkdir()
    original = json.loads(mapping.read_bytes())
    successor = write_json(root / SUCCESSOR, valid_successor(root, REVISIONS[1]))
    receipts = (root / AP00013).read_bytes()
    arguments = (
        json.loads(receipts),
        root,
        {"artifact_id": AP00013, "artifact_sha256": digest(receipts)},
    )
    options = {
        "successor": json.loads(successor),
        "successor_artifact": {
            "artifact_id": SUCCESSOR,
            "artifact_sha256": digest(successor),
        },
    }
    result = run_tool("--map", mapping, "--root", root, cwd=elsewhere)
    assert result.returncode == 0, result.stderr
    written = mapping.read_bytes()
    assert written == encode(tool.apply(original, *arguments, **options))
    again = run_tool("--map", mapping, "--root", root, cwd=elsewhere)
    assert again.returncode == 0, again.stderr
    assert mapping.read_bytes() == written
    regenerated = tool.apply(json.loads(written), *arguments, **options)
    assert canon(regenerated) == canon(json.loads(written))
    assert_contract_rows(json.loads(written))
    check = run_tool("--map", mapping, "--root", root, "--check", cwd=elsewhere)
    assert check.returncode == 0, check.stderr
    assert (root / AP00013).read_bytes() == receipts
    assert (root / SUCCESSOR).read_bytes() == successor
    # Changing only the successor receipt makes the written map stale.
    write_json(root / SUCCESSOR, valid_successor(root, REVISIONS[0]))
    stale = run_tool("--map", mapping, "--root", root, "--check", cwd=elsewhere)
    assert stale.returncode == 1, stale.stdout + stale.stderr
    assert mapping.read_bytes() == written


def test_successor_flag_overrides_the_default_successor_path(tmp_path: Path) -> None:
    mapping = build_repo(tmp_path, "flag")
    write_json(tmp_path / SUCCESSOR, valid_successor(tmp_path, REVISIONS[0]))
    override = write_json(tmp_path / OVERRIDE, valid_successor(tmp_path, REVISIONS[1]))
    result = run_tool(
        "--map",
        mapping,
        "--root",
        tmp_path,
        "--successor-receipts",
        tmp_path / OVERRIDE,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assets = by_key(json.loads(mapping.read_bytes())["assets"], "destination_path")
    for path in SHARED:
        assert assets[path]["evidence"]["tested_package_revision"] == REVISIONS[1]
    for path in (*CONTROLLER, CONTRACT):
        assert assets[path]["evidence"] == {
            "status": "passed",
            "artifact_id": OVERRIDE,
            "artifact_sha256": digest(override),
            "tested_package_revision": REVISIONS[1],
        }, path


def test_without_a_successor_receipt_the_generator_behaves_as_today(
    tmp_path: Path,
) -> None:
    mapping = build_repo(tmp_path, "none")
    original = by_key(json.loads(mapping.read_bytes())["assets"], "destination_path")
    receipts = (tmp_path / AP00013).read_bytes()
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    document = json.loads(mapping.read_bytes())
    assets = by_key(document["assets"], "destination_path")
    for path in CONTROLLER + NEAR_MISSES:
        assert canon(assets[path]) == canon(original[path]), path
    assert CONTRACT not in assets
    assert CONTRACT not in {row["path"] for row in document["authored_file_owners"]}
    for path in SHARED:
        sha = digest((tmp_path / path).read_bytes())
        assert assets[path]["evidence"] == {
            "status": "passed",
            "artifact_id": path,
            "artifact_sha256": sha,
            "tested_package_revision": "a" * 40,
        }, path
    assert (tmp_path / AP00013).read_bytes() == receipts
