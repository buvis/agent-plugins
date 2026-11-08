"""The committed map, package docs and generator hygiene honor the helper provenance contract.

The committed-map checks fail until the coordinator runs update_helper_map.py
against the committed package revision and commits the generated map.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from test_helper_provenance import (
    HELPER_ONLY,
    HELPER_TARGETS,
    REFRESHED,
    ROOT,
    SELECTORS,
    TOOL,
    assert_functions_follow_table,
    assert_regression_row,
    by_key,
    canon,
    digest,
    make_repo,
    run_tool,
)

MAP = ROOT / "tools/autopilot/source-map.json"
PIN = "e960ef1cc43e72bf92593b2f16c7a37c71ea7e48"
INVENTORY_SHA = "f55c98bba2b4b3c94ce588b6c616258186dd0bb2164800b2d34271acc25dfb5d"
# json.dumps(value, sort_keys=True) digests of the pre-generation committed map.
FROZEN = {
    "behaviors": "8c49f9a1b77d83fa1c9ef4ed711aa1ef9e6fa62b825309ad7e23e9cff30a7763",
    "resource_edges": "39382053172cf854eb107c631d41b84d6fa77913123b56b8c09bc5f7047bce2b",
    "evidence_policy": "661002b2cf3e89314a8da8c45cf8c9642a91a6e4429d24ff2ab349f8d8485339",
    "owner_bindings": "bbc225221cb8cdc514c1abddaa6e5cfd5aa69a5442103cd4b74f46b9f3b07e46",
    "regression_cases": "e7331e78365b23d430469e0edbcd4be456b1fffe69ca16e2e27411c59dca3648",
}
CONTROLLER_PREFIXES = ("plugins/autopilot/controller/", "plugins/autopilot/contracts/controller/")
AP00014_TARGETS = frozenset({
    "plugins/autopilot/scripts/hosts.py",
    "plugins/autopilot/scripts/claude.py",
    "plugins/autopilot/scripts/codex.py",
    "plugins/autopilot/scripts/gemini.py",
    "plugins/autopilot/scripts/jobs.py",
    "plugins/autopilot/scripts/guards.py",
    "plugins/autopilot/scripts/doctor.py",
    "plugins/autopilot/contracts/hosts.json",
    "tools/autopilot/probe-host.py",
    "tools/autopilot/build-compatibility.py",
    "plugins/autopilot/compatibility/claude.json",
    "plugins/autopilot/compatibility/gemini.json",
    "plugins/autopilot/compatibility/codex.json",
})
OTHER_ASSETS_SHA = "381542752d61f87dfecdcc0c88519adbcb37993f24d8edd5157416b8ce72ee4f"
OLD_OWNERS_SHA = "2fd9c26dc6177f1fb38c6ea26fce2a7df9852892fb02632b07eac3e6925e4d20"
# Refreshed authored rows without destination_blob_sha256 and evidence.
REFRESHED_STABLE = {
    "plugins/autopilot/README.md": "703e0325df63a5d07d204f99c62a25d44fb98623524c905606ceb3ab13092b15",
    "plugins/autopilot/CHANGELOG.md": "370956d952b6d62ec837c35964ec43e72356bc5ff57683b40bd4126e4ea777db",
    "plugins/autopilot/scripts/autopilot.py": "10cd4760d9fb52e9c2cf603953e76e9ebfa9748a9dcfc1529e165b4aa8b996ab",
}
# Characterization: rows, sorted-id sha256 prefix and delivery owners per helper.
CHARACTERIZED = {
    "review_stage": (54, "0a1b270fc8bbbeb8", {"00020": 53, "00016": 1}),
    "findings_section": (125, "10a6dada3829e53b", {"00020": 125}),
    "rework_groups": (37, "3fd7f65b0f1c8e02", {"00020": 37}),
    "gate_lead": (89, "d264c0ef96ba5f33", {"00020": 89}),
    "review_close": (96, "214d42bccbb44019", {"00020": 72, "00019": 23, "00016": 1}),
    "cap_check": (41, "a7d9d655fdb21fae", {"00019": 41}),
    "custody": (134, "1a257dcd226c7ea9", {"00020": 115, "00019": 11, "00021": 8}),
    "catchup_probe": (26, "58a4a1a4a7adb501", {"00019": 26}),
    "verification": (37, "2a83a2af25367781", {"00021": 37}),
    "dirty_tree": (47, "5da0f66c02c992ce", {"00021": 47}),
    "log_sink_refusal": (4, "cca766d677c1fe51", {"00021": 4}),
}
CONTROLLER_OWNED_SHA = (
    "be27d9036a716e0140bd128010c842b2a4bf68d96c44a49d3fae74067759501d"
)
HISTORICAL_HEADINGS = (
    "autopilot",
    "What's inside",
    "Recursion guard",
    "Paths",
    "Install",
    "Update",
    "Alternative: install directly from this repo",
    "What intentionally stays out",
    "Development",
    "License",
    "Autoclaude role effort",
    "Current local facade",
)
NEW_CAPABILITIES = (
    "stage-review-v1",
    "group-findings-v1",
    "check-evidence-v1",
    "prepare-close-v1",
    "catchup-probe-v1",
    "verification-artifact-v1",
    "controller-required-v1",
)
LEGACY_CAPABILITIES = ("review-policy-v1", "review-evidence-v1", "review-fixtures-v1")
NEGATION = r"(?i)\b(?:no|not|never|unavailable|without|cannot)\b|n't\b"
HEADING = re.compile(r"^(#{1,6})[^\S\n]+(.+?)[^\S\n]*#*[^\S\n]*$", re.MULTILINE)


def sha_of_ids(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


@pytest.fixture(scope="module")
def mapping() -> dict:
    return json.loads(MAP.read_bytes())


def single_assets(mapping: dict, paths: list[str]) -> dict[str, dict]:
    # Two source assets share plugins/autopilot/plugin.json, so index only the named paths.
    found = {
        path: [row for row in mapping["assets"] if row["destination_path"] == path]
        for path in paths
    }
    for path, rows in found.items():
        assert len(rows) == 1, path
    return {path: rows[0] for path, rows in found.items()}


def selected(mapping: dict) -> dict[str, list[dict]]:
    return {
        helper: [
            row for row in mapping["regression_cases"] if row["source_path"] in files
        ]
        for helper, files in SELECTORS.items()
    }


def test_committed_map_carries_versioned_helper_dispositions(mapping: dict) -> None:
    dispositions = mapping["helper_dispositions"]
    assert set(dispositions) == {
        "schema_version",
        "source_commit",
        "functions",
        "regressions",
    }
    assert (
        type(dispositions["schema_version"]) is int
        and dispositions["schema_version"] == 1
    )
    assert mapping["source_commit"] == PIN
    assert dispositions["source_commit"] == mapping["source_commit"]
    assert_functions_follow_table(dispositions["functions"])
    evidence = {
        row["evidence"]
        for row in dispositions["functions"] + dispositions["regressions"]
    }
    assert evidence
    for path in evidence:
        assert (ROOT / path).is_file(), path


def test_committed_regressions_cover_exactly_the_characterized_union(
    mapping: dict,
) -> None:
    groups = selected(mapping)
    union: set[str] = set()
    for helper, (count, prefix, owners) in CHARACTERIZED.items():
        ids = [row["source_regression_id"] for row in groups[helper]]
        assert len(ids) == count, helper
        assert sha_of_ids(ids)[:16] == prefix, helper
        assert dict(Counter(row["delivery_prd"] for row in groups[helper])) == owners, (
            helper
        )
        union.update(ids)
    assert len(union) == 601
    rows = by_key(mapping["helper_dispositions"]["regressions"], "source_regression_id")
    assert set(rows) == union
    known = {row["source_regression_id"] for row in mapping["regression_cases"]}
    assert set(rows) <= known
    for identity, row in rows.items():
        helpers = {
            h
            for h, members in groups.items()
            if any(m["source_regression_id"] == identity for m in members)
        }
        expected = "helper-facet" if helpers <= HELPER_ONLY else "controller-only"
        assert_regression_row(row, helpers, expected)


def test_preexisting_regression_ownership_is_referenced_not_reassigned(
    mapping: dict,
) -> None:
    assert (
        hashlib.sha256(canon(mapping["regression_cases"]).encode()).hexdigest()
        == FROZEN["regression_cases"]
    )
    exact = {
        f"skills/run-autopilot/cli/test_{name}.py"
        for name in (
            "review_stage",
            "rework_groups",
            "custody",
            "catchup_probe",
            "verification",
            "cap_check",
        )
    }
    owned = [row for row in mapping["regression_cases"] if row["source_path"] in exact]
    assert len(owned) == 185
    assert (
        sha_of_ids([row["source_regression_id"] for row in owned])
        == CONTROLLER_OWNED_SHA
    )
    for row in owned:
        assert row["owner_repository"] == "buvis/agent-plugins"
        assert row["disposition"] == "replaced"
        assert row["delivery_prd"] in {"00019", "00020", "00021"}
    assert not [
        row for row in mapping["regression_cases"] if row["delivery_prd"] == "00013"
    ]
    helper_rows = [row for rows in selected(mapping).values() for row in rows]
    for row in helper_rows:
        statuses = [
            row["evidence"]["status"],
            *(p["status"] for p in row["evidence"]["profile_evidence"].values()),
        ]
        assert "passed" not in statuses, row["source_regression_id"]


def test_unrelated_arrays_and_original_owners_stay_byte_semantic(mapping: dict) -> None:
    assert mapping["source_inventory_sha256"] == INVENTORY_SHA
    for key, expected in FROZEN.items():
        assert hashlib.sha256(canon(mapping[key]).encode()).hexdigest() == expected, key
    skipped = set(REFRESHED) | HELPER_TARGETS | AP00014_TARGETS
    others = [
        row
        for row in mapping["assets"]
        if row["destination_path"] not in skipped
        and not row["destination_path"].startswith(CONTROLLER_PREFIXES)
    ]
    assert hashlib.sha256(canon(others).encode()).hexdigest() == OTHER_ASSETS_SHA
    assets = single_assets(mapping, list(REFRESHED_STABLE))
    for path, expected in REFRESHED_STABLE.items():
        stable = {
            k: v
            for k, v in assets[path].items()
            if k not in ("destination_blob_sha256", "evidence")
        }
        assert hashlib.sha256(canon(stable).encode()).hexdigest() == expected, path
    old = [
        row for row in mapping["authored_file_owners"] if row["delivery_prd"] == "00012"
    ]
    assert hashlib.sha256(canon(old).encode()).hexdigest() == OLD_OWNERS_SHA


def assert_receipts_file(evidence: dict) -> None:
    artifact = ROOT / evidence["artifact_id"]
    assert artifact.resolve().is_relative_to(ROOT.resolve())
    assert digest(artifact.read_bytes()) == evidence["artifact_sha256"]
    receipts = json.loads(artifact.read_bytes())
    assert receipts["schema_version"] == 1 and receipts["prd"] == "00013"
    assert receipts["tasks"]
    for task in receipts["tasks"]:
        assert type(task["passed"]) is int and task["passed"] > 0, task
        assert task["tests"].strip() and task["command"].strip()
    assert receipts["real_host"]["status"] == "unavailable"
    assert receipts["real_host"]["reason"].strip()


def assert_refreshed_evidence(assets: dict) -> None:
    receipts_evidence = assets[sorted(HELPER_TARGETS)[0]]["evidence"]
    assert assets[REFRESHED[0]]["evidence"] == receipts_evidence
    receipts = json.loads((ROOT / receipts_evidence["artifact_id"]).read_bytes())
    revision = receipts["package_revision"]
    assert re.fullmatch(r"[0-9a-f]{40}", revision), revision
    for path in REFRESHED[1:]:
        sha = digest((ROOT / path).read_bytes())
        assert assets[path]["evidence"] == {
            "status": "passed",
            "artifact_id": path,
            "artifact_sha256": sha,
            "tested_package_revision": revision,
        }, path
        shown = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{revision}:{path}"],
            capture_output=True,
            timeout=60,
        )
        assert shown.returncode == 0, shown.stderr
        assert digest(shown.stdout) == sha, path


def test_new_helper_files_are_owned_and_digested_from_current_bytes(
    mapping: dict,
) -> None:
    assets = single_assets(mapping, sorted(HELPER_TARGETS) + list(REFRESHED))
    owners = by_key(mapping["authored_file_owners"], "path")
    for path in sorted(HELPER_TARGETS) + list(REFRESHED):
        assert assets[path]["destination_blob_sha256"] == digest(
            (ROOT / path).read_bytes()
        ), path
    for path in sorted(HELPER_TARGETS):
        row = assets[path]
        assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
        assert_receipts_file(row["evidence"])
        owner = owners[path]
        assert owner["delivery_prd"] == "00013"
        assert owner["owner_repository"] == "buvis/agent-plugins"
        assert owner["source_asset_id"] is None and owner["source_blob_sha256"] is None
        assert owner["acceptance_cases"]
    assert_refreshed_evidence(assets)
    # Controller files are registered by AP00018, never claimed by AP00013 helpers.
    controller = [
        row["destination_path"]
        for row in mapping["assets"]
        if row["destination_path"].startswith(CONTROLLER_PREFIXES)
    ]
    controller_assets = single_assets(mapping, controller)
    for path in controller:
        assert "AP00013" not in controller_assets[path]["adaptation_reason"], path
        assert owners[path]["delivery_prd"] == "00018", path


def test_ap00014_rows_are_owned_and_digested_from_current_bytes(mapping: dict) -> None:
    """Every AP00014 row is owned by 00014 and digests its current bytes."""
    assets = single_assets(mapping, sorted(AP00014_TARGETS))
    owners = by_key(mapping["authored_file_owners"], "path")
    for path in sorted(AP00014_TARGETS):
        assert assets[path]["destination_blob_sha256"] == digest(
            (ROOT / path).read_bytes()
        ), path
        assert owners[path]["delivery_prd"] == "00014", path
        assert owners[path]["owner_repository"] == "buvis/agent-plugins", path
        assert owners[path]["source_asset_id"] is None, path
        assert owners[path]["source_blob_sha256"] is None, path
        assert owners[path]["acceptance_cases"], path


def pinned_source_root() -> Path | None:
    candidate = Path(
        os.environ.get("AUTOPILOT_SOURCE_ROOT", ROOT.parent / "claude-autopilot")
    )
    probe = subprocess.run(
        ["git", "-C", str(candidate), "cat-file", "-e", f"{PIN}^{{commit}}"],
        capture_output=True,
        timeout=60,
    )
    return candidate if probe.returncode == 0 else None


def test_source_audit_accepts_the_generated_map(tmp_path: Path) -> None:
    source = pinned_source_root()
    if source is None:
        pytest.skip("pinned source checkout unavailable; set AUTOPILOT_SOURCE_ROOT")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/autopilot/check-source.py"),
            "--source-root",
            str(source),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert PIN in result.stdout


def test_generator_check_accepts_the_committed_map(tmp_path: Path) -> None:
    result = run_tool("--map", MAP, "--check", cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def readme_sections(text: str) -> list[tuple[int, str, str]]:
    matches = list(HEADING.finditer(text))
    sections = []
    for index, match in enumerate(matches):
        level = len(match[1])
        end = next(
            (m.start() for m in matches[index + 1 :] if len(m[1]) <= level), len(text)
        )
        sections.append((level, match[2], text[match.end() : end]))
    return sections


def has_sentence(text: str, *patterns: str) -> bool:
    sentences = re.split(r"(?<=[.!?])\s+|\n\s*\n", text)
    return any(all(re.search(p, s) for p in patterns) for s in sentences)


def test_readme_keeps_every_historical_section() -> None:
    text = (ROOT / "plugins/autopilot/README.md").read_text()
    headings = [title for _, title, _ in readme_sections(text)]
    for heading in HISTORICAL_HEADINGS:
        assert headings.count(heading) == 1, heading
    assert text.count("<!-- Historical source body begins. -->") == 11
    assert text.count("<!-- Historical source body ends. -->") == 11
    assert PIN in text
    for option in ("--list-capabilities", "--export-policy"):
        assert re.search(r"python3[^\n]*scripts/autopilot\.py[^\n]*" + option, text), (
            option
        )


def test_readme_documents_delivered_helpers_and_their_limits() -> None:
    text = (ROOT / "plugins/autopilot/README.md").read_text()
    new = [
        body
        for _, title, body in readme_sections(text)
        if title not in HISTORICAL_HEADINGS
    ]
    assert new, "no new README section"
    body = "\n".join(new)
    for capability in NEW_CAPABILITIES + LEGACY_CAPABILITIES:
        assert capability in body, capability
    assert "controller-required" in body
    assert re.search(r"(?i)\bexit(?:s|\s+code|\s+status)?\s+(?:with\s+)?`?3\b", body)
    assert has_sentence(body, r"(?i)custody", r"(?i)\bcap", NEGATION)
    assert has_sentence(body, r"(?i)publi", NEGATION)
    assert has_sentence(body, r"(?i)install", NEGATION)
    assert has_sentence(body, r"(?i)real[- ]host", r"(?i)unavailable")


def test_changelog_adds_the_provenance_and_readme_entry() -> None:
    text = (ROOT / "plugins/autopilot/CHANGELOG.md").read_text()
    unreleased = text.split("## [Unreleased]", 1)[1].split("\n## ", 1)[0]
    added = unreleased.split("### Added", 1)[1].split("\n### ", 1)[0]
    bullets = [line for line in added.splitlines() if line.startswith("- ")]
    assert [
        b
        for b in bullets
        if re.search(r"(?i)provenance|helper_dispositions", b)
        and re.search(r"README", b)
    ]


def test_generator_is_an_unshipped_stdlib_only_tool() -> None:
    assert TOOL.relative_to(ROOT).as_posix() == "tools/autopilot/update_helper_map.py"
    assert not list((ROOT / "plugins").rglob("update_helper_map.py"))
    tree = ast.parse(TOOL.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import"
            names.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
    assert names
    assert names <= set(sys.stdlib_module_names) | {"__future__"}, names - set(
        sys.stdlib_module_names
    )


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_generator_neither_reads_nor_writes_live_autopilot_state(
    tmp_path: Path,
) -> None:
    root, cwd = tmp_path / "repo", tmp_path / "cwd"
    mapping = make_repo(root, "9" * 40, "live")
    live_dirs = [base / "docs/dev/project-management/autopilot" for base in (root, cwd)]
    for live in live_dirs:
        live.mkdir(parents=True)
        (live / "state.json").write_text('{"phase": "work"}\n')
        live.chmod(0o000)
    try:
        result = run_tool("--map", mapping, "--root", root, cwd=cwd)
    finally:
        for live in live_dirs:
            live.chmod(0o755)
    assert result.returncode == 0, result.stderr
    for live in live_dirs:
        assert sorted(os.listdir(live)) == ["state.json"]
        assert (live / "state.json").read_text() == '{"phase": "work"}\n'
    assert "helper_dispositions" in json.loads(mapping.read_bytes())
