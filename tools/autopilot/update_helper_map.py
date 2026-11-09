"""Add AP00013 helper provenance to the source map without reassigning any owner.

The function/effect/regression facts are copied from
docs/dev/project-management/reviews/00013-helper-source-characterization.md.
This maintainer tool is not shipped, certifies no controller execution and no
host profile, and never reads or writes live autopilot workflow state.

Without --receipts it uses DEFAULT_RECEIPTS under the root when that file
exists, and otherwise records delivery evidence as "unavailable". The README.md
and CHANGELOG.md rows get self-referential evidence pinned to the receipts'
optional package_revision; the other refreshed and new rows cite the receipts.

Without --successor-receipts it uses DEFAULT_SUCCESSOR_RECEIPTS under the root
when that file exists. A valid AP00018 successor supersedes the exact AP00013
receipts loaded, never rewrites them, and certifies exactly the paths it lists:
README.md and CHANGELOG.md get self-referential evidence pinned to its
package_revision, and controller assets cite the successor itself.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = "skills/run-autopilot/cli/"
SCRIPTS = "skills/run-autopilot/scripts/"
TESTS = "tests/autopilot/"
OWNER = "buvis/agent-plugins"
DEFAULT_RECEIPTS = (
    "docs/dev/project-management/autopilot/reports/00013-helper-delivery-receipts.json"
)
DEFAULT_SUCCESSOR_RECEIPTS = (
    "docs/dev/project-management/autopilot/reports/"
    "00018-v2-controller-delivery-receipts.json"
)
CONTROLLER_PREFIXES = (
    "plugins/autopilot/controller/",
    "plugins/autopilot/contracts/controller/",
)
CONTROLLER_CONTRACT = "plugins/autopilot/contracts/controller-v1.json"
CONTROLLER_SCENARIO = "controller_action_not_yet_wired"
CONTROLLER_EVIDENCE = TESTS + "test_local_boundary.py"
MIXED_EXCLUSION = (
    "Controller-only: this regression belongs to a mixed source module, so the per-row "
    "helper split is not claimed; the module-level helper scenario carries the helper "
    "facet and the existing owner keeps the row."
)

# module -> (packaged helper, helper scenario, evidence test, extracted functions,
#            controller-owned function -> why the helper cannot own it).
TABLE = {
    "review_stage": (
        "review_stage",
        "review_preparation_no_state",
        "test_review_helpers.py",
        "render_tasks _cell findings_section _prd_body _run_inputs _plan _eve_inputs "
        "_mech_checks _section _output_format _incremental_block _filesystem_notes "
        "preflight_persona render_roster",
        {
            "stage": "creates staging directories under the discovered repo root (writes state)",
            "_write_inputs": "writes staged input files",
            "_gather": "runs the gather-context script as a supervisor",
            "run_pack": "runs the engram subprocess as a supervisor",
            "_run_script": "spawns a script process as its supervisor",
            "run_gate_line": "runs the verification gate and writes its record",
            "_gate_result_line": "writes the verification gate record line",
            "_render_one": "runs render_prompt.py and writes the prompt",
            "_open_row": "records a dispatch row",
            "_arm": "stamps workflow state through statectl",
            "_append": "writes appended rows to workflow files",
        },
    ),
    "findings_section": (
        "findings",
        "finding_group_equivalence",
        "test_finding_groups.py",
        "_reviewed_keys _section_bounds _table_keys _table_header _row_from_table "
        "_table_cells _finding_key _normalize_issue _split_severity_cell Row",
        {},
    ),
    "rework_groups": (
        "rework_groups",
        "finding_group_equivalence",
        "test_finding_groups.py",
        "file_key _dirs _merge_pair _cap group",
        {},
    ),
    "gate_lead": (
        "gate_lead",
        "finding_group_equivalence",
        "test_finding_groups.py",
        "_strip_lead",
        {},
    ),
    "review_close": (
        "review_close",
        "helper_source_parity",
        "test_review_close_helpers.py",
        "_frontmatter_lines _nested_pairs _findings_block _mutation_context _add_decisions "
        "_add_rework_tasks _lens_states _dispatch_outcomes _no_verdict_refusal "
        "_findings_refusal _carry_unmatched _carry_reason _severity_file_key "
        "_matches_open_deferral _single_voice_refusal _found_by_count "
        "_tail_sweep_preconditions",
        {
            "close": "orchestrates the close and writes workflow state",
            "_close_mutator": "mutates workflow state through statectl",
            "_set_lens_state": "writes lens state",
            "_prelock_refusal": "loads live workflow state for the applied-batch key",
            "_carry_refusal": "judges loaded live workflow state",
            "_tail_sweep_refusal": "judges loaded live workflow state",
            "_end_dispatch_rows": "ends dispatch rows through a subprocess",
            "_read_review_file": "reads the review file found in live workflow state",
            "_gate_review": "gates the review file found in live workflow state",
        },
    ),
    "cap_check": (
        "cap_check",
        "helper_source_parity",
        "test_cap_custody_helpers.py",
        "CapCheckError _parse_number_list _split_file_line _clean_segment _segment_lines "
        "_normalise_path _parse_file_cell _missing_path_error _unreadable_cell_error "
        "_verify_range _introducing_commit _first_commit_touching _file_exists_at "
        "_pair_commit _pairs_verdict _classify_row classify_findings",
        {
            "rework_range": "derives heads from frontmatter and workflow state, not explicit heads",
            "_head_sha": "infers the head from workflow state",
            "_read_text": "reads frontmatter and workflow state files",
        },
    ),
    "custody": (
        "custody",
        "helper_source_parity",
        "test_cap_custody_helpers_custody.py",
        "upsert_entry marker_entry refresh_hold_prd _refresh_block _insert_notice "
        "_notice_prefix migration_records git_argv capture_range read_journal _live_rows "
        "unresolved_from_journal",
        {
            "marker_lock": "takes the custody marker flock lock",
            "append_journal": "appends to the custody journal",
            "compact_journal": "rewrites the custody journal",
            "pending": "reads pending custody from the live marker state",
            "project_root": "discovers the project root on its own",
            "repo_and_git_dir": "discovers the repository and git dir on its own",
            "store_git": "runs git against the discovered workflow state store",
            "load_marker": "loads the live custody marker",
            "write_marker": "writes or unlinks the custody marker",
            "record_critical": "writes the critical custody record",
            "mirror_mutator": "mutates mirrored workflow state",
            "_drop_mirror": "drops the mirrored workflow state",
            "_recorded_choice": "reads the recorded choice from the live journal",
            "_refuse_unless_clean": "checks the live state store before custody writes",
            "_reverted_targets": "derives revert targets from the live journal",
            "_pin_custody_branch": "writes the custody branch pin",
            "_apply_git": "applies git writes to the state store",
            "_cleanup": "removes custody markers and locks",
            "_resolve_locked": "resolves custody under the marker lock",
            "resolve": "resolves custody and writes the journal and marker",
        },
    ),
    "catchup_probe": (
        "catchup",
        "catchup_optional_absent",
        "test_catchup.py",
        "_run_probe _skips",
        {
            "probe": "loads live state, discovers the project root and writes the cached probe",
            "_utc_now": "stamps the cached probe written to workflow state",
        },
    ),
    "verification": (
        "verification",
        "verification_artifact_reuse",
        "test_verification.py",
        "normalize_command _record_shape_ok _parse_summary _timed_out_result "
        "_lock_timeout_result _head_moved_result _dirty_result reuse_verdict _spawn_gate "
        "_drain_bounded _reap _kill_gate _SignalGuard _deferred_signals _pinned_parent_fd "
        "_descend _open_log_sink",
        {
            "run_gate": "takes the workflow lock and writes the gate log and record",
            "_acquire_lock": "acquires the workflow verification lock",
            "_lock_and_check": "acquires the workflow lock and checks workflow state",
            "_write_record": "writes the last-verification record",
            "_record_gate": "writes the gate record",
            "_run_locked_gate": "runs the gate supervisor under the workflow lock and unlinks files",
            "_gate_under_lock": "runs the gate supervisor under the workflow lock",
            "_refuse_verify_log_path": "judges log paths against the discovered workflow state root",
        },
    ),
    "dirty_tree": (
        "dirty_tree",
        "verification_artifact_reuse",
        "test_verification_reuse.py",
        "_iter_porcelain_z_records _dirty_path_is_in_store _store_roots _dirty_store_paths "
        "_store_symlink_targets_changed _dirty_outside_store_paths _hidden_flag_edits "
        "_dirty_outside_store _dirty_check _ancestor_and_clean _log_rel_and_tracked "
        "_untracked_log_exclusion",
        {},
    ),
    "log_sink_refusal": (
        "log_sink_refusal",
        "verification_artifact_reuse",
        "test_verification.py",
        "refuse _toplevel _identity_targets _identity_hit _worktree_gitdir_pointer "
        "_symlinked_component _in_nested_repo",
        {},
    ),
}
# Test-file selectors per helper; gate_lead's files are a subset of findings_section's.
SELECTORS = {
    "review_stage": [
        CLI + f"test_review_stage{s}.py"
        for s in (
            "",
            "_paths",
            "_run_script",
            "_run_script_signals",
            "_gate_result_line",
        )
    ]
    + ["skills/review-work-completion/scripts/test_skill_stages_via_review_stage.py"],
    "findings_section": [
        CLI + f"test_gate_findings_{s}.py"
        for s in ("classification", "real_fixtures", "shapes", "table", "unread_shapes")
    ],
    "rework_groups": [
        CLI + "test_rework_groups.py",
        SCRIPTS + "test_rework_groups_prose.py",
    ],
    "gate_lead": [
        CLI + f"test_gate_findings_{s}.py"
        for s in ("shapes", "unread_shapes", "classification")
    ],
    "review_close": [
        CLI + f"test_review_close{s}.py"
        for s in ("", "_apply", "_carry", "_lowsev", "_tail_sweep")
    ]
    + [
        CLI + "test_main_review_close_validation.py",
        SCRIPTS + "test_phase_review_closes_via_review_close.py",
    ],
    "cap_check": [CLI + "test_cap_check.py", CLI + "test_cap_check_cells.py"],
    "custody": [
        CLI + f"test_custody{s}.py"
        for s in (
            "",
            "_entry",
            "_loud",
            "_prose",
            "_prose_schema",
            "_resolve",
            "_stall",
        )
    ]
    + [CLI + "test_render_custody.py", CLI + "test_store_tree_custody.py"],
    "catchup_probe": [CLI + "test_catchup_probe.py", CLI + "test_catchup_probe_cli.py"],
    "verification": [
        CLI + f"test_verification{s}.py" for s in ("", "_normalize", "_reuse_verdict")
    ],
    "dirty_tree": [
        CLI + f"test_verification_{s}.py"
        for s in ("dirty", "dirty_paths", "dirty_symlink", "hidden_flags")
    ],
    "log_sink_refusal": [CLI + "test_verification_log_sink.py"],
}
HELPER_FILES = (
    "findings",
    "gate_lead",
    "rework_groups",
    "review_evidence",
    "evidence_shapes",
    "dirty_tree",
    "log_sink_refusal",
    "review_stage",
    "review_close",
    "cap_check",
    "custody",
    "catchup",
    "verification",
)
HELPER_PATHS = tuple(f"plugins/autopilot/scripts/{name}.py" for name in HELPER_FILES)
REFRESHED = (
    "plugins/autopilot/scripts/autopilot.py",
    "plugins/autopilot/README.md",
    "plugins/autopilot/CHANGELOG.md",
)
AP00014_DIGESTED = (
    "plugins/autopilot/compatibility/claude.json",
    "plugins/autopilot/compatibility/codex.json",
    "plugins/autopilot/compatibility/gemini.json",
    "plugins/autopilot/contracts/hosts.json",
    "plugins/autopilot/scripts/claude.py",
    "plugins/autopilot/scripts/codex.py",
    "plugins/autopilot/scripts/doctor.py",
    "plugins/autopilot/scripts/gemini.py",
    "plugins/autopilot/scripts/guards.py",
    "plugins/autopilot/scripts/hosts.py",
    "plugins/autopilot/scripts/jobs.py",
)
CONTROLLER_KEYS = {f"{m}:{f}" for m, row in TABLE.items() for f in row[4]}


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()


def function_rows() -> list[dict]:
    rows = []
    for module, (target, scenario, evidence, extracted, controller) in TABLE.items():
        for function in extracted.split():
            rows.append(
                {
                    "key": f"{module}:{function}",
                    "module": module,
                    "function": function,
                    "scope": "extracted",
                    "target_module": f"plugins/autopilot/scripts/{target}.py",
                    "target_scenario": scenario,
                    "owner_scope": "helper-facet",
                    "controller_exclusion": None,
                    "evidence": TESTS + evidence,
                }
            )
        for function, reason in controller.items():
            rows.append(
                {
                    "key": f"{module}:{function}",
                    "module": module,
                    "function": function,
                    "scope": "controller-owned",
                    "target_module": None,
                    "target_scenario": CONTROLLER_SCENARIO,
                    "owner_scope": "controller-only",
                    "controller_exclusion": f"Controller-owned: {reason}.",
                    "evidence": CONTROLLER_EVIDENCE,
                }
            )
    return rows


def regression_row(identity: str, module: str) -> dict:
    _, scenario, evidence, _, controller = TABLE[module]
    mixed = bool(controller)
    return {
        "source_regression_id": identity,
        "key": module,
        "disposition": "controller-only" if mixed else "helper-facet",
        "target_scenario": CONTROLLER_SCENARIO if mixed else scenario,
        "owner_scope": "controller-only" if mixed else "helper-facet",
        "controller_exclusion": MIXED_EXCLUSION if mixed else None,
        "evidence": TESTS + evidence,
    }


def validate(dispositions: dict, document: dict) -> None:
    keys = [row["key"] for row in dispositions["functions"]]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate helper function key")
    ids = [row["source_regression_id"] for row in dispositions["regressions"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate helper regression id")
    unknown = set(ids) - {
        row["source_regression_id"] for row in document["regression_cases"]
    }
    if unknown:
        raise ValueError(f"unknown regression ids: {sorted(unknown)}")
    helper_owned = [
        row["key"]
        for row in dispositions["functions"]
        if row["owner_scope"] == "helper-facet" and row["key"] in CONTROLLER_KEYS
    ]
    if helper_owned:
        raise ValueError(
            f"controller-owned functions given a helper facet: {helper_owned}"
        )
    unknown_keys = [
        row["key"] for row in dispositions["regressions"] if row["key"] not in TABLE
    ]
    if unknown_keys:
        raise ValueError(f"unknown helper regression keys: {unknown_keys}")
    mixed_helper = [
        row["source_regression_id"]
        for row in dispositions["regressions"]
        if row["owner_scope"] == "helper-facet" and TABLE[row["key"]][4]
    ]
    if mixed_helper:
        raise ValueError(
            f"mixed-module regressions given a helper facet: {mixed_helper}"
        )


def build_dispositions(document: dict) -> dict:
    ids = [row["source_regression_id"] for row in document["regression_cases"]]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate source_regression_id in regression_cases")
    regressions = []
    for row in document["regression_cases"]:
        module = next(
            (m for m, files in SELECTORS.items() if row["source_path"] in files), None
        )
        if module is not None:
            regressions.append(regression_row(row["source_regression_id"], module))
    return {
        "schema_version": 1,
        "source_commit": document["source_commit"],
        "functions": function_rows(),
        "regressions": regressions,
    }


def validate_receipts(receipts: dict, prd: str = "00013") -> None:
    def text(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    tasks = receipts.get("tasks")
    if (
        type(receipts.get("schema_version")) is not int
        or receipts["schema_version"] != 1
    ):
        raise ValueError("receipts schema_version must be the integer 1")
    if receipts.get("prd") != prd or not isinstance(tasks, list) or not tasks:
        raise ValueError(f"receipts must be for PRD {prd} and list at least one task")
    for task in tasks:
        passed = task.get("passed")
        if type(passed) is not int or passed <= 0:
            raise ValueError(
                f"receipt task needs a positive integer passed count: {task}"
            )
        if not text(task.get("tests")) or not text(task.get("command")):
            raise ValueError(f"receipt task needs tests and command: {task}")
    host = receipts.get("real_host")
    if (
        not isinstance(host, dict)
        or host.get("status") != "unavailable"
        or not text(host.get("reason"))
    ):
        raise ValueError(
            "receipts real_host must be unavailable with a reason; never passed"
        )
    if "package_revision" in receipts:
        revision = receipts["package_revision"]
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("receipts package_revision must be 40 lowercase hex")


def validate_successor_receipts(
    successor: dict, supersedes_artifact: dict | None
) -> None:
    if not isinstance(successor, dict):
        raise ValueError("successor receipts must be a JSON object")
    validate_receipts(successor, prd="00018")
    if "package_revision" not in successor:
        raise ValueError("successor receipts need a package_revision")
    if (
        supersedes_artifact is None
        or successor.get("supersedes") != supersedes_artifact
    ):
        raise ValueError(
            "successor receipts must supersede the exact AP00013 receipts loaded"
        )
    paths = successor.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ValueError("successor receipts must list at least one path")
    for path in paths:
        if (
            not isinstance(path, str)
            or {"", ".", ".."} & set(path.split("/"))
            or not (
                path in (*REFRESHED[1:], CONTROLLER_CONTRACT)
                or path.startswith(CONTROLLER_PREFIXES)
            )
        ):
            raise ValueError(
                f"successor path is not README, CHANGELOG or a controller asset: {path!r}"
            )
    if len(set(paths)) != len(paths):
        raise ValueError("successor paths must be unique")


def asset_row(path: str, digest: str, evidence: dict) -> dict:
    return {
        "source_asset_id": None,
        "destination_path": path,
        "source_blob_sha256": None,
        "destination_blob_sha256": digest,
        "adaptation_reason": "Newly authored AP00013 local helper; no pinned source asset or "
        "source sections. Delivery evidence records packaged bytes, not "
        "controller execution or host certification.",
        "disposition": "adapted",
        "section_plan": [],
        "entry_point_gate": {
            "status": "not-applicable",
            "operation": "none",
            "entry_point": None,
        },
        "acceptance_cases": [
            {
                "case_id": f"asset-new-{path.removeprefix('plugins/autopilot/')}",
                "expected_outcome": "The packaged local helper exists at the recorded digest; it owns "
                "no controller effect and certifies no host execution.",
                "status": evidence["status"],
            }
        ],
        "evidence": evidence,
    }


def owner_row(path: str) -> dict:
    return {
        "path": path,
        "source_asset_id": None,
        "source_blob_sha256": None,
        "owner_repository": OWNER,
        "delivery_prd": "00013",
        "acceptance_cases": [
            {
                "case_id": f"authored-{path}",
                "expected_outcome": "The packaged AP00013 local helper exists at the recorded "
                "digest and owns no controller effect.",
            }
        ],
    }


def upsert(rows: list[dict], field: str, row: dict) -> None:
    for index, existing in enumerate(rows):
        if existing[field] == row[field]:
            rows[index] = row
            return
    rows.append(row)


def refresh_ap00014_digests(assets: list[dict], root: Path) -> None:
    ap00014 = set(AP00014_DIGESTED)
    for row in assets:
        if row["destination_path"] in ap00014:
            row["destination_blob_sha256"] = hashlib.sha256(
                (root / row["destination_path"]).read_bytes()
            ).hexdigest()


def apply_successor(result: dict, root: Path, successor: dict, artifact: dict) -> None:
    revision = successor["package_revision"]
    cited = {"status": "passed", **artifact, "tested_package_revision": revision}
    listed = set(successor["paths"])
    if CONTROLLER_CONTRACT in listed:
        path = CONTROLLER_CONTRACT
        digest = hashlib.sha256((root / path).read_bytes()).hexdigest()
        row = asset_row(path, digest, dict(cited))
        row["adaptation_reason"] = (
            "Newly authored AP00018 controller contract bundle; no pinned source "
            "asset or source sections. Delivery evidence records packaged bytes, "
            "not host certification."
        )
        row["acceptance_cases"][0]["expected_outcome"] = (
            "The packaged controller contract bundle exists at the recorded digest; "
            "it certifies no host execution."
        )
        owner = owner_row(path)
        owner["delivery_prd"] = "00018"
        owner["acceptance_cases"] = [
            {
                "case_id": f"authored-{path}",
                "expected_outcome": "The packaged AP00018 controller contract bundle "
                "exists at the recorded digest.",
            }
        ]
        upsert(result["assets"], "destination_path", row)
        upsert(result["authored_file_owners"], "path", owner)
    for row in result["assets"]:
        path = row["destination_path"]
        if path not in listed:
            continue
        sha = hashlib.sha256((root / path).read_bytes()).hexdigest()
        row["destination_blob_sha256"] = sha
        row["evidence"] = dict(cited)
        if path in REFRESHED[1:]:
            row["evidence"].update(artifact_id=path, artifact_sha256=sha)


def refresh_shared_evidence(
    assets: list[dict],
    root: Path,
    evidence: dict,
    unavailable: dict,
    revision: str | None,
) -> None:
    for row in assets:
        path = row["destination_path"]
        if path not in REFRESHED:
            continue
        sha = hashlib.sha256((root / path).read_bytes()).hexdigest()
        row["destination_blob_sha256"] = sha
        if path == REFRESHED[0]:
            row["evidence"] = dict(evidence)
        elif revision is None:
            row["evidence"] = dict(unavailable)
        else:
            row["evidence"] = {
                "status": "passed",
                "artifact_id": path,
                "artifact_sha256": sha,
                "tested_package_revision": revision,
            }


def apply(
    document: dict,
    receipts: dict | None,
    root: Path = ROOT,
    artifact: dict | None = None,
    successor: dict | None = None,
    successor_artifact: dict | None = None,
) -> dict:
    if "helper_dispositions" in document:
        validate(document["helper_dispositions"], document)
    if receipts is not None:
        validate_receipts(receipts)
    has_successor = successor is not None or successor_artifact is not None
    if has_successor:
        validate_successor_receipts(successor, artifact)
    result = copy.deepcopy(document)
    result["helper_dispositions"] = build_dispositions(document)
    unavailable = {
        "status": "unavailable",
        "artifact_id": None,
        "artifact_sha256": None,
        "tested_package_revision": None,
    }
    evidence = dict(unavailable)
    if receipts is not None and artifact is not None:
        evidence.update(status="passed", **artifact)
    for path in HELPER_PATHS:
        digest = hashlib.sha256((root / path).read_bytes()).hexdigest()
        upsert(
            result["assets"],
            "destination_path",
            asset_row(path, digest, dict(evidence)),
        )
        upsert(result["authored_file_owners"], "path", owner_row(path))
    revision = (receipts or {}).get("package_revision")
    refresh_shared_evidence(result["assets"], root, evidence, unavailable, revision)
    if has_successor:
        apply_successor(result, root, successor, successor_artifact)
    refresh_ap00014_digests(result["assets"], root)
    return result


def write_atomically(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def load_artifact(
    given: Path | None, default: str, root: Path
) -> tuple[object, dict | None]:
    if given is None and os.path.isfile(root / default):
        given = root / default
    if given is None:
        return None, None
    given = given.resolve()
    data = given.read_bytes()
    return json.loads(data), {
        "artifact_id": given.relative_to(root).as_posix(),
        "artifact_sha256": hashlib.sha256(data).hexdigest(),
    }


def run(arguments: argparse.Namespace) -> int:
    path = arguments.map.resolve()
    root = (arguments.root or path.parents[2]).resolve()
    raw = path.read_bytes()
    receipts, artifact = load_artifact(arguments.receipts, DEFAULT_RECEIPTS, root)
    successor, successor_artifact = load_artifact(
        arguments.successor_receipts, DEFAULT_SUCCESSOR_RECEIPTS, root
    )
    rendered = encode(
        apply(
            json.loads(raw),
            receipts,
            root,
            artifact,
            successor=successor,
            successor_artifact=successor_artifact,
        )
    )
    if arguments.check:
        if rendered != raw:
            print(
                f"{path} is not the generated helper map; rerun without --check",
                file=sys.stderr,
            )
            return 1
        return 0
    if rendered != raw:
        write_atomically(path, rendered)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, help="Repository root; defaults to the map's repo root"
    )
    parser.add_argument(
        "--receipts",
        type=Path,
        help="Coordinator-authored task receipts JSON; defaults to "
        f"ROOT/{DEFAULT_RECEIPTS} when that file exists",
    )
    parser.add_argument(
        "--successor-receipts",
        type=Path,
        help="AP00018 successor receipts JSON; defaults to "
        f"ROOT/{DEFAULT_SUCCESSOR_RECEIPTS} when that file exists",
    )
    parser.add_argument(
        "--check", action="store_true", help="Exit 0 only if the map is generated"
    )
    arguments = parser.parse_args()
    try:
        return run(arguments)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"update_helper_map failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
