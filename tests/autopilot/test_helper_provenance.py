"""Helper provenance is generated additively and never hands controller effects to a helper.

Synthetic maps prove the generator contract; the committed-map, documentation
and hygiene checks live in test_helper_provenance_real.py.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/autopilot/update_helper_map.py"
CLI = "skills/run-autopilot/cli/"
SCRIPTS = "skills/run-autopilot/scripts/"
HELPER_FILES = ("findings", "gate_lead", "rework_groups", "review_evidence", "evidence_shapes",
                "dirty_tree", "log_sink_refusal", "review_stage", "review_close", "cap_check",
                "custody", "catchup", "verification")
HELPER_TARGETS = {f"plugins/autopilot/scripts/{name}.py" for name in HELPER_FILES}
REFRESHED = ("plugins/autopilot/scripts/autopilot.py", "plugins/autopilot/README.md",
             "plugins/autopilot/CHANGELOG.md")
SCENARIOS = {"helper_source_parity", "review_preparation_no_state", "finding_group_equivalence",
             "catchup_optional_absent", "verification_artifact_reuse", "local_helpers_without_ovcaq",
             "no_hidden_workflow_state", "controller_action_not_yet_wired"}
DISPOSITION_KEYS = {"schema_version", "source_commit", "functions", "regressions"}
FUNCTION_FIELDS = {"key", "module", "function", "scope", "target_module", "target_scenario",
                   "owner_scope", "controller_exclusion", "evidence"}
REGRESSION_FIELDS = {"source_regression_id", "key", "disposition", "target_scenario", "owner_scope",
                     "controller_exclusion", "evidence"}
UNRELATED = ("schema_version", "source_inventory_sha256", "source_commit", "behaviors",
             "resource_edges", "evidence_policy", "owner_bindings", "regression_cases")
EXCLUSION = re.compile(r"(?i)writ|state|journal|marker|lock|dispatch|discover|supervisor")
EVIDENCE = re.compile(r"^tests/autopilot/test_[a-z0-9_]+\.py$")

# The characterization table (reviews/00013-helper-source-characterization.md).
EXTRACTED = {
    "review_stage": "render_tasks _cell findings_section _prd_body _run_inputs _plan _eve_inputs "
                    "_mech_checks _section _output_format _incremental_block _filesystem_notes "
                    "preflight_persona render_roster",
    "findings_section": "_reviewed_keys _section_bounds _table_keys _table_header _row_from_table "
                        "_table_cells _finding_key _normalize_issue _split_severity_cell Row",
    "rework_groups": "file_key _dirs _merge_pair _cap group",
    "gate_lead": "_strip_lead",
    "review_close": "_frontmatter_lines _nested_pairs _findings_block _mutation_context _add_decisions "
                    "_add_rework_tasks _lens_states _dispatch_outcomes _no_verdict_refusal "
                    "_findings_refusal _carry_unmatched _carry_reason _severity_file_key "
                    "_matches_open_deferral _single_voice_refusal _found_by_count "
                    "_tail_sweep_preconditions",
    "cap_check": "CapCheckError _parse_number_list _split_file_line _clean_segment _segment_lines "
                 "_normalise_path _parse_file_cell _missing_path_error _unreadable_cell_error "
                 "_verify_range _introducing_commit _first_commit_touching _file_exists_at "
                 "_pair_commit _pairs_verdict _classify_row classify_findings",
    "custody": "upsert_entry marker_entry refresh_hold_prd _refresh_block _insert_notice _notice_prefix "
               "migration_records git_argv capture_range read_journal _live_rows unresolved_from_journal",
    "catchup_probe": "_run_probe _skips",
    "verification": "normalize_command _record_shape_ok _parse_summary _timed_out_result "
                    "_lock_timeout_result _head_moved_result _dirty_result reuse_verdict _spawn_gate "
                    "_drain_bounded _reap _kill_gate _SignalGuard _deferred_signals _pinned_parent_fd "
                    "_descend _open_log_sink",
    "dirty_tree": "_iter_porcelain_z_records _dirty_path_is_in_store _store_roots _dirty_store_paths "
                  "_store_symlink_targets_changed _dirty_outside_store_paths _hidden_flag_edits "
                  "_dirty_outside_store _dirty_check _ancestor_and_clean _log_rel_and_tracked "
                  "_untracked_log_exclusion",
    "log_sink_refusal": "refuse _toplevel _identity_targets _identity_hit _worktree_gitdir_pointer "
                        "_symlinked_component _in_nested_repo",
}
CONTROLLER = {
    "review_stage": "stage _write_inputs _gather run_pack _run_script run_gate_line _gate_result_line "
                    "_render_one _open_row _arm _append",
    "review_close": "close _close_mutator _set_lens_state _prelock_refusal _carry_refusal "
                    "_tail_sweep_refusal _end_dispatch_rows _read_review_file _gate_review",
    "cap_check": "rework_range _head_sha _read_text",
    "custody": "marker_lock append_journal compact_journal pending project_root repo_and_git_dir "
               "store_git load_marker write_marker record_critical mirror_mutator _drop_mirror "
               "_recorded_choice _refuse_unless_clean _reverted_targets _pin_custody_branch _apply_git "
               "_cleanup _resolve_locked resolve",
    "catchup_probe": "probe _utc_now",
    "verification": "run_gate _acquire_lock _lock_and_check _write_record _record_gate "
                    "_run_locked_gate _gate_under_lock _refuse_verify_log_path",
}
EXTRACTED_KEYS = {f"{m}:{f}" for m, names in EXTRACTED.items() for f in names.split()}
CONTROLLER_KEYS = {f"{m}:{f}" for m, names in CONTROLLER.items() for f in names.split()}
WRITERS = ("custody:write_marker", "custody:record_critical", "verification:run_gate",
           "review_close:close", "review_stage:stage", "catchup_probe:probe")
HELPER_ONLY = {"findings_section", "rework_groups", "gate_lead", "dirty_tree", "log_sink_refusal"}
SELECTORS = {
    "review_stage": [CLI + f"test_review_stage{s}.py" for s in
                     ("", "_paths", "_run_script", "_run_script_signals", "_gate_result_line")]
                    + ["skills/review-work-completion/scripts/test_skill_stages_via_review_stage.py"],
    "findings_section": [CLI + f"test_gate_findings_{s}.py" for s in
                         ("classification", "real_fixtures", "shapes", "table", "unread_shapes")],
    "rework_groups": [CLI + "test_rework_groups.py", SCRIPTS + "test_rework_groups_prose.py"],
    "gate_lead": [CLI + f"test_gate_findings_{s}.py" for s in ("shapes", "unread_shapes", "classification")],
    "review_close": [CLI + f"test_review_close{s}.py" for s in
                     ("", "_apply", "_carry", "_lowsev", "_tail_sweep")]
                    + [CLI + "test_main_review_close_validation.py",
                       SCRIPTS + "test_phase_review_closes_via_review_close.py"],
    "cap_check": [CLI + "test_cap_check.py", CLI + "test_cap_check_cells.py"],
    "custody": [CLI + f"test_custody{s}.py" for s in
                ("", "_entry", "_loud", "_prose", "_prose_schema", "_resolve", "_stall")]
               + [CLI + "test_render_custody.py", CLI + "test_store_tree_custody.py"],
    "catchup_probe": [CLI + "test_catchup_probe.py", CLI + "test_catchup_probe_cli.py"],
    "verification": [CLI + f"test_verification{s}.py" for s in ("", "_normalize", "_reuse_verdict")],
    "dirty_tree": [CLI + f"test_verification_{s}.py" for s in
                   ("dirty", "dirty_paths", "dirty_symlink", "hidden_flags")],
    "log_sink_refusal": [CLI + "test_verification_log_sink.py"],
}

# Synthetic regression rows: id -> (allowed keys, expected disposition).
EXPECTED = {
    CLI + "test_custody.py::test_writes_marker": ({"custody"}, "controller-only"),
    CLI + "test_custody_stall.py::test_reports_stall": ({"custody"}, "controller-only"),
    CLI + "test_review_close_carry.py::test_carries": ({"review_close"}, "controller-only"),
    CLI + "test_gate_findings_shapes.py::test_shape": ({"findings_section", "gate_lead"}, "helper-facet"),
    CLI + "test_gate_findings_table.py::test_table": ({"findings_section"}, "helper-facet"),
    CLI + "test_verification_log_sink.py::test_sink": ({"log_sink_refusal"}, "helper-facet"),
    SCRIPTS + "test_rework_groups_prose.py": ({"rework_groups"}, "helper-facet"),
}
NEAR_MISSES = (CLI + "test_custody_extra.py::test_writes_marker", "other/cli/test_custody.py::test_a",
               CLI + "test_review_stage_extra.py::test_b", CLI + "test_rework_groups_prose.py",
               "dev/bin/test_replay.py::test_c")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()


def canon(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def load_tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("update_helper_map", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return load_tool()


def run_tool(*args: object, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)], cwd=cwd,
                          capture_output=True, text=True, timeout=300)


def planned_evidence() -> dict:
    receipt = {"status": "planned", "artifact_id": None, "artifact_sha256": None,
               "tested_package_revision": None}
    return {**receipt, "profile_evidence": {"source-parity": dict(receipt)}}


def regression_row(identity: str, prd: str = "00020") -> dict:
    path = identity.split("::")[0]
    return {"source_regression_id": identity, "source_path": path,
            "test_identity": identity.split("::")[-1] if "::" in identity else "script-or-module",
            "source_blob_sha256": digest(path.encode()), "case_sha256": digest(identity.encode()),
            "disposition": "replaced", "owner_repository": "buvis/agent-plugins", "delivery_prd": prd,
            "equivalent_target_scenario": f"agent-plugins-{prd}-regression-{identity}",
            "expected_outcome": f"Retain {identity} é.", "evidence": planned_evidence()}


def asset_row(path: str, source_id: str | None = None) -> dict:
    return {"source_asset_id": source_id, "destination_path": path,
            "source_blob_sha256": None if source_id is None else "b" * 64,
            "destination_blob_sha256": "0" * 64,
            "adaptation_reason": f"Authored {path}.", "disposition": "adapted",
            "section_plan": [] if source_id is None else [
                {"source_anchor": "a1", "source_sha256": "c" * 64, "action": "keep", "reason": "r"}],
            "entry_point_gate": {"status": "not-applicable", "operation": "none", "entry_point": None},
            "acceptance_cases": [{"case_id": f"asset-{path}", "expected_outcome": "exists",
                                  "status": "passed"}],
            "evidence": {"status": "passed", "artifact_id": "old-receipt.json",
                         "artifact_sha256": "d" * 64, "tested_package_revision": "e" * 40}}


def owner_row(path: str, prd: str = "00012") -> dict:
    return {"path": path, "source_asset_id": None, "source_blob_sha256": None,
            "owner_repository": "buvis/agent-plugins", "delivery_prd": prd,
            "acceptance_cases": [{"case_id": f"authored-{path}", "expected_outcome": "exists"}]}


def synthetic_map(commit: str, regressions: tuple[str, ...] = (*EXPECTED, *NEAR_MISSES)) -> dict:
    return {
        "schema_version": 1, "source_inventory_sha256": "a" * 64, "source_commit": commit,
        "assets": [asset_row(REFRESHED[0]), asset_row(REFRESHED[1], "README.md"),
                   asset_row(REFRESHED[2]),
                   asset_row("plugins/autopilot/skills/work/SKILL.md", "skills/work/SKILL.md")],
        "behaviors": [{"source_behavior_id": "P01", "reason": "untouched é"}],
        "regression_cases": [regression_row(identity) for identity in regressions],
        "resource_edges": [{"source_path": "skills/a.md", "source_line": 3, "reference": "one.py",
                            "kind": "informational-provenance", "runtime_rule": "none"}],
        "evidence_policy": "Assignments are planned, not certification.",
        "owner_bindings": [{"owner_repository": "buvis/agent-plugins", "basis": "design.md"}],
        "authored_file_owners": [owner_row(REFRESHED[2]), owner_row(REFRESHED[0])],
    }


def valid_receipts() -> dict:
    return {"schema_version": 1, "prd": "00013",
            "tasks": [{"task": 1, "module": "findings", "tests": "tests/autopilot/test_finding_groups.py",
                       "passed": 12, "command": "pytest -q tests/autopilot/test_finding_groups.py"},
                      {"task": 2, "module": "custody", "tests": "tests/autopilot/test_cap_custody_helpers.py",
                       "passed": 7, "command": "pytest -q tests/autopilot/test_cap_custody_helpers.py"}],
            "real_host": {"status": "unavailable", "reason": "No real host is reachable from the sandbox."}}


def make_repo(root: Path, commit: str, tag: str, document: dict | None = None) -> Path:
    files = [f"plugins/autopilot/scripts/{name}.py" for name in HELPER_FILES] + list(REFRESHED)
    files += ["plugins/autopilot/controller/main.py", "plugins/autopilot/contracts/controller/state.json"]
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {tag} {relative}\n")
    mapping = root / "tools/autopilot/source-map.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_bytes(encode(document if document is not None else synthetic_map(commit)))
    return mapping


def write_receipts(root: Path, data: dict) -> Path:
    path = root / "reports/00013-task-receipts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def by_key(rows: list[dict], field: str) -> dict:
    keyed = {row[field]: row for row in rows}
    assert len(keyed) == len(rows), f"duplicate {field}"
    return keyed


def assert_function_row(row: dict) -> None:
    assert set(row) == FUNCTION_FIELDS
    assert row["key"] == f"{row['module']}:{row['function']}"
    assert row["target_scenario"] in SCENARIOS
    assert EVIDENCE.match(row["evidence"]), row["evidence"]
    if row["scope"] == "extracted":
        assert row["owner_scope"] == "helper-facet"
        assert row["controller_exclusion"] is None
        assert row["target_module"] in HELPER_TARGETS
    else:
        assert row["scope"] == "controller-owned"
        assert row["owner_scope"] == "controller-only"
        assert row["target_module"] is None
        assert isinstance(row["controller_exclusion"], str)
        assert EXCLUSION.search(row["controller_exclusion"]), row["key"]


def assert_regression_row(row: dict, keys: set[str], disposition: str) -> None:
    assert set(row) == REGRESSION_FIELDS
    assert row["key"] in keys
    assert row["disposition"] == disposition
    assert row["owner_scope"] == disposition
    assert row["target_scenario"] in SCENARIOS
    assert EVIDENCE.match(row["evidence"]), row["evidence"]
    if disposition == "helper-facet":
        assert row["controller_exclusion"] is None
    else:
        exclusion = row["controller_exclusion"]
        assert isinstance(exclusion, str) and re.search(r"(?i)\bnot\b", exclusion)
        assert re.search(r"(?i)module", exclusion), exclusion


def assert_functions_follow_table(functions: list[dict]) -> None:
    rows = by_key(functions, "key")
    for row in rows.values():
        assert_function_row(row)
    for key in EXTRACTED_KEYS:
        assert rows[key]["scope"] == "extracted", key
    for key in CONTROLLER_KEYS:
        assert rows[key]["scope"] == "controller-owned", key
        assert rows[key]["owner_scope"] == "controller-only", key
    for module in ("rework_groups", "dirty_tree", "log_sink_refusal", "gate_lead"):
        assert rows[f"{module}:{EXTRACTED[module].split()[0]}"]["target_module"] == \
            f"plugins/autopilot/scripts/{module}.py"


def test_dispositions_bind_every_helper_function_and_selected_regression(tool: ModuleType) -> None:
    result = tool.build_dispositions(synthetic_map("1" * 40))
    assert set(result) == DISPOSITION_KEYS
    assert type(result["schema_version"]) is int and result["schema_version"] == 1
    assert result["source_commit"] == "1" * 40
    assert tool.build_dispositions(synthetic_map("2" * 40))["source_commit"] == "2" * 40
    assert_functions_follow_table(result["functions"])
    rows = by_key(result["regressions"], "source_regression_id")
    assert set(rows) == set(EXPECTED)
    for identity, (keys, disposition) in EXPECTED.items():
        assert_regression_row(rows[identity], keys, disposition)


def test_writers_and_supervisors_stay_controller_only(tool: ModuleType) -> None:
    rows = by_key(tool.build_dispositions(synthetic_map("1" * 40))["functions"], "key")
    for key in WRITERS:
        assert rows[key]["owner_scope"] == "controller-only", key
        assert rows[key]["target_module"] is None
    # Near-miss names from the same modules are extracted helper facets.
    for key in ("custody:marker_entry", "catchup_probe:_run_probe", "verification:reuse_verdict"):
        assert rows[key]["owner_scope"] == "helper-facet", key
    assert not any(row["owner_scope"] == "helper-facet" for key, row in rows.items()
                   if key in CONTROLLER_KEYS)


def test_map_without_helper_regressions_yields_no_regression_rows(tool: ModuleType) -> None:
    result = tool.build_dispositions(synthetic_map("1" * 40, NEAR_MISSES))
    assert result["regressions"] == []
    assert_functions_follow_table(result["functions"])
    assert tool.build_dispositions(synthetic_map("1" * 40, ()))["regressions"] == []


def test_apply_adds_only_dispositions_without_mutating_input(tool: ModuleType) -> None:
    document = synthetic_map("3" * 40)
    before = copy.deepcopy(document)
    result = tool.apply(document, None)
    assert document == before
    assert result is not document
    assert result["helper_dispositions"] == tool.build_dispositions(before)
    for key in UNRELATED:
        assert canon(result[key]) == canon(before[key]), key
    assert set(result) == set(before) | {"helper_dispositions"}
    source_rows = [row for row in before["assets"] if row["source_asset_id"] is not None]
    for row in source_rows:
        match = [r for r in result["assets"] if r["destination_path"] == row["destination_path"]]
        assert len(match) == 1
        stable = {k: v for k, v in row.items() if k not in ("destination_blob_sha256", "evidence")}
        assert {k: match[0][k] for k in stable} == stable
    old_owners = [r for r in result["authored_file_owners"] if r["delivery_prd"] == "00012"]
    assert canon(old_owners) == canon(before["authored_file_owners"])
    assert canon(tool.apply(result, None)) == canon(result)


@pytest.mark.parametrize("mutate", [
    lambda d: d["regression_cases"].append(regression_row(CLI + "test_custody.py::test_writes_marker")),
    lambda d: d["regression_cases"].append(regression_row(SCRIPTS + "test_rework_groups_prose.py")),
], ids=["duplicate-controller-id", "duplicate-helper-id"])
def test_duplicate_regression_ids_are_rejected(tool: ModuleType, mutate) -> None:
    document = synthetic_map("1" * 40)
    mutate(document)
    with pytest.raises(ValueError):
        tool.build_dispositions(document)
    with pytest.raises(ValueError):
        tool.apply(document, None)
    clean = synthetic_map("1" * 40, (*EXPECTED, *NEAR_MISSES, CLI + "test_custody.py::test_other"))
    assert len(tool.build_dispositions(clean)["regressions"]) == len(EXPECTED) + 1


def tamper_writer(dispositions: dict) -> None:
    row = next(r for r in dispositions["functions"] if r["key"] == "custody:write_marker")
    row.update(scope="extracted", owner_scope="helper-facet", controller_exclusion=None,
               target_module="plugins/autopilot/scripts/custody.py")


def tamper_duplicate_key(dispositions: dict) -> None:
    dispositions["functions"].append(copy.deepcopy(dispositions["functions"][0]))


def tamper_unknown_id(dispositions: dict) -> None:
    extra = copy.deepcopy(dispositions["regressions"][0])
    extra["source_regression_id"] = CLI + "test_custody.py::test_absent_from_regression_cases"
    dispositions["regressions"].append(extra)


def tamper_duplicate_id(dispositions: dict) -> None:
    dispositions["regressions"].append(copy.deepcopy(dispositions["regressions"][0]))


@pytest.mark.parametrize("tamper", [tamper_writer, tamper_duplicate_key, tamper_unknown_id,
                                    tamper_duplicate_id],
                         ids=["helper-owned-writer", "duplicate-key", "unknown-id", "duplicate-id"])
def test_tampered_dispositions_are_never_kept(tool: ModuleType, tmp_path: Path, tamper) -> None:
    clean = tool.apply(synthetic_map("1" * 40), None)
    tampered = copy.deepcopy(clean)
    tamper(tampered["helper_dispositions"])
    try:
        regenerated = tool.apply(tampered, None)
    except ValueError:
        regenerated = None
    if regenerated is not None:
        assert canon(regenerated["helper_dispositions"]) == canon(clean["helper_dispositions"])
    mapping = make_repo(tmp_path, "1" * 40, "t", tampered)
    before = mapping.read_bytes()
    result = run_tool("--map", mapping, "--root", tmp_path, "--check", cwd=tmp_path)
    assert result.returncode != 0
    assert mapping.read_bytes() == before


def receipts_variant(change) -> dict:
    data = valid_receipts()
    change(data)
    return data


@pytest.mark.parametrize("receipts", [
    receipts_variant(lambda d: d["real_host"].update(status="passed")),
    receipts_variant(lambda d: d["tasks"][1].update(passed=0)),
    receipts_variant(lambda d: d["tasks"][0].update(passed=True)),
    receipts_variant(lambda d: d["tasks"][1].update(passed="7")),
    receipts_variant(lambda d: d["tasks"][0].pop("passed")),
], ids=["real-host-passed", "zero-passed", "bool-passed", "string-passed", "missing-passed"])
def test_receipts_claiming_success_without_counts_or_a_real_host_are_rejected(
        tool: ModuleType, tmp_path: Path, receipts: dict) -> None:
    with pytest.raises(ValueError):
        tool.apply(synthetic_map("1" * 40), receipts)
    accepted = tool.apply(synthetic_map("1" * 40), valid_receipts())
    assert "helper_dispositions" in accepted
    mapping = make_repo(tmp_path, "1" * 40, "r")
    before = mapping.read_bytes()
    path = write_receipts(tmp_path, receipts)
    result = run_tool("--map", mapping, "--root", tmp_path, "--receipts", path, cwd=tmp_path)
    assert result.returncode != 0
    assert mapping.read_bytes() == before


def assets_by_path(document: dict) -> dict:
    return by_key(document["assets"], "destination_path")


def assert_helper_assets(document: dict, root: Path, receipts: Path | None) -> None:
    assets = assets_by_path(document)
    shape = set(assets[REFRESHED[0]])
    for relative in sorted(HELPER_TARGETS):
        row = assets[relative]
        assert set(row) == shape, relative
        assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
        assert row["destination_blob_sha256"] == digest((root / relative).read_bytes())
        evidence = row["evidence"]
        if receipts is None:
            assert evidence["status"] == "unavailable"
        else:
            assert evidence["artifact_id"] == receipts.relative_to(root).as_posix()
            assert evidence["artifact_sha256"] == digest(receipts.read_bytes())
    for relative in REFRESHED:
        assert assets[relative]["destination_blob_sha256"] == digest((root / relative).read_bytes())
    assert not [p for p in assets if "/controller/" in p]
    skill = assets["plugins/autopilot/skills/work/SKILL.md"]
    assert canon(skill) == canon(asset_row(skill["destination_path"], "skills/work/SKILL.md"))


def assert_helper_owners(document: dict) -> None:
    owners = by_key(document["authored_file_owners"], "path")
    for relative in HELPER_TARGETS:
        row = owners[relative]
        assert set(row) == set(owner_row(relative))
        assert row["delivery_prd"] == "00013"
        assert row["owner_repository"] == "buvis/agent-plugins"
        assert row["source_asset_id"] is None and row["source_blob_sha256"] is None
        assert row["acceptance_cases"] and all(c["case_id"].strip() and c["expected_outcome"].strip()
                                               for c in row["acceptance_cases"])
    for relative in (REFRESHED[0], REFRESHED[2]):
        assert owners[relative] == owner_row(relative)


def test_cli_writes_canonical_map_with_helper_assets_owners_and_receipts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    mapping = make_repo(root, "4" * 40, "first")
    receipts = write_receipts(root, valid_receipts())
    receipt_bytes = receipts.read_bytes()
    elsewhere = tmp_path / "cwd"
    elsewhere.mkdir()
    result = run_tool("--map", mapping, "--root", root, "--receipts", receipts, cwd=elsewhere)
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
    again = run_tool("--map", mapping, "--root", root, "--receipts", receipts, cwd=elsewhere)
    assert again.returncode == 0, again.stderr
    assert mapping.read_bytes() == written


def test_cli_without_receipts_records_unavailable_evidence(tmp_path: Path) -> None:
    mapping = make_repo(tmp_path, "5" * 40, "bare")
    result = run_tool("--map", mapping, "--root", tmp_path, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert_helper_assets(json.loads(mapping.read_bytes()), tmp_path, None)


def test_asset_digests_follow_the_selected_root(tmp_path: Path) -> None:
    default_root, other_root = tmp_path / "default", tmp_path / "other"
    mapping = make_repo(default_root, "6" * 40, "default-bytes")
    copy_map = make_repo(other_root, "6" * 40, "other-bytes")
    assert run_tool("--map", mapping, cwd=tmp_path).returncode == 0
    assert run_tool("--map", copy_map, "--root", default_root, cwd=tmp_path).returncode == 0
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
