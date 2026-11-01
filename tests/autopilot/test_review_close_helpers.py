"""Packaged review close prepares classified proposals from validated evidence without workflow state."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

import pytest
import test_contract as contract
from test_contract import ROOT

PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
FIXTURES = contract.load(contract.FIXTURES_FILE)
CASES = {case["name"]: case for case in FIXTURES["cases"]}
V1 = FIXTURES["policies"]["v1"]
REVIEW_REF = "docs/dev/tmp/review/review-file.txt"
EMOJI = {"critical": "\U0001f534", "high": "\U0001f7e0", "medium": "\U0001f7e1", "low": "⚪"}
FINDINGS_TOKENS = {"findings_mismatch", "findings_uncovered", "findings_ref_required", "findings_malformed"}
ACTIONS = ("fix-proposed", "deferred")
DROP = object()
# ref -> (AP00012 severity, title, file or None, [(finding_id, reviewer job)])
ROWS: dict[str, tuple[str, str, str | None, list[tuple[str, str]]]] = {
    "R1": ("high", "Wrong default", "src/a.py", [("F1", "alice"), ("F2", "blake")]),
    "R2": ("medium", "Slow loop", "src/b.py", [("F3", "alice"), ("F4", "bob")]),
    "R3": ("low", "Typo", None, [("F5", "bob")]),
    "R4": ("medium", "Stale doc", "docs/guide.md", [("F6", "alice"), ("F7", "blake")]),
    "R5": ("high", "Null deref", "src/c.py", [("F8", "bob")]),
}
HEADER = "| Ref | Consensus | Severity | Issue | File | Task | Found By |\n|---|---|---|---|---|---|---|\n"


def load_sibling(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


@pytest.fixture
def rc():
    return load_sibling("review_close")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def table_row(ref: str) -> str:
    severity, title, file, links = ROWS[ref]
    finders = sorted({job for _, job in links})
    return f"| {ref} | [{len(finders)}/3] | {EMOJI[severity]} | {title} | {file or 'N/A'} | - | {', '.join(finders)} |\n"


def review_text(section: str, count: int) -> str:
    verdict = f"Verdict: {count} findings" if count else "Verdict: converged"
    return (
        "# Review of naïve café\n\n## Alice\nnotes\n\n## Blake\nnotes\n\n## Bob\nnotes\n\n"
        f"{section}\n{verdict}\nTests: 12 passed\n"
    )


def findings_text(table_refs: list[str]) -> str:
    if not table_refs:
        return review_text("## Consolidated Findings\n\nNone.\n", 0)
    body = HEADER + "".join(table_row(ref) for ref in table_refs)
    return review_text("## Consolidated Findings\n\n" + body, len(table_refs))


def evidence_for(refs: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    clean = CASES["full-clean"]
    context, evidence = copy.deepcopy(clean["expected_context"]), copy.deepcopy(clean["input"])
    links = [(fid, job, ref) for ref in refs for fid, job in ROWS[ref][3]]
    for result in evidence["reviewer_results"]:
        ids = [fid for fid, job, _ in links if job == result["job_ref"]]
        if ids:
            result["outcome"] = "findings"
            result["finding_ids"] = ids
    evidence["findings"] = [
        {"finding_id": fid, "result_id": f"{job}-1", "severity": ROWS[ref][0], "title": ROWS[ref][1],
         "file": ROWS[ref][2], "task_ref": None, "evidence": f"EVIDENCE-{fid} body"}
        for fid, job, ref in links
    ]
    return context, evidence


def set_text(case: dict[str, Any], text: str) -> dict[str, Any]:
    case["text"] = text
    artifact = next(a for a in case["evidence"]["artifacts"] if a["kind"] == "review-file")
    artifact["path"] = REVIEW_REF
    artifact["sha256"] = sha(text)
    return case


def scenario(refs: list[str], table_refs: list[str] | None = None) -> dict[str, Any]:
    context, evidence = evidence_for(refs)
    case = {"context": context, "evidence": evidence}
    return set_text(case, findings_text(refs if table_refs is None else table_refs))


def row(ref: str, classification: Any, **over: Any) -> dict[str, Any]:
    severity, title, file, links = ROWS[ref]
    base = {
        "ref": ref, "severity": EMOJI[severity], "file": file or "N/A", "issue": title,
        "classification": classification, "finding_ids": [fid for fid, _ in links],
        "found_by": sorted({job for _, job in links}),
    }
    base.update(over)
    return {k: v for k, v in base.items() if v is not DROP}


def kwargs_for(case: dict[str, Any], chosen: Any, **over: Any) -> dict[str, Any]:
    kwargs = {
        "policy": V1, "expected_context": case["context"], "evidence": case["evidence"],
        "review_ref": REVIEW_REF, "review_text": case["text"], "chosen_findings": chosen,
        "cycle": 2, "batch_id": "decision-gate", "default_tier": "sonnet",
    }
    kwargs.update(over)
    return kwargs


def run(rc, case: dict[str, Any], chosen: Any, **over: Any) -> dict[str, Any]:
    return rc.prepare_close(**kwargs_for(case, chosen, **over))


def assert_ok(report: Any) -> None:
    assert isinstance(report, dict), report
    assert report["ok"] is True, report
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert report["controller_required"] is True


def assert_refused(report: Any, error: str | None = None) -> None:
    assert isinstance(report, dict), report
    assert report["ok"] is False, report
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert isinstance(report.get("error"), str) and report["error"]
    assert not report.get("task_proposals") and not report.get("decision_proposals")
    if error is not None:
        assert report["error"] == error, report
        assert isinstance(report.get("reason"), str) and report["reason"]


def assert_rejected(rc, case: dict[str, Any], chosen: Any, **over: Any) -> None:
    """Either a refusal report or a ValueError for a malformed shape; never proposals."""
    try:
        report = run(rc, case, chosen, **over)
    except ValueError:
        return
    assert_refused(report)


def valid_batch() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix"), row("R2", "defer"), row("R3", "verify", reason="already covered by T4")]
    return case, chosen


def proposals_with(report: dict[str, Any], key: str, value: Any) -> list[dict[str, Any]]:
    return [p for p in report["decision_proposals"] if p.get(key) == value]


def actioned(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [p for p in report["decision_proposals"] if p.get("action") in ACTIONS]


# --- proposal shape -----------------------------------------------------------------------


def test_valid_batch_proposes_fix_task_and_decisions_without_ids_or_applied_claims(rc):
    case, chosen = valid_batch()
    before = copy.deepcopy((case, chosen))
    report = run(rc, case, chosen)
    assert_ok(report)
    assert {"task_proposals", "decision_proposals", "rubric_verdicts", "reviewer_results"} <= set(report)
    assert "applied" not in report and "auto-fixed" not in json.dumps(report)
    [task] = report["task_proposals"]
    assert "id" not in task and task["model"] == "sonnet"
    assert task["name"] == "[D2] src/a.py"
    lines = task["description"].splitlines()
    assert lines[0] == "### Findings (verbatim)" and len(lines) == 2
    assert lines[1].startswith(f"- {EMOJI['high']} src/a.py: Wrong default")
    [fix] = proposals_with(report, "action", "fix-proposed")
    assert (fix["cycle"], fix["issue"], fix["severity"]) == (2, "Wrong default", "high")
    [defer] = proposals_with(report, "action", "deferred")
    assert (defer["cycle"], defer["issue"], defer["severity"], defer["file"]) == (
        2, "Slow loop", EMOJI["medium"], "src/b.py")
    assert isinstance(defer["reason"], str) and defer["reason"]
    [verify] = proposals_with(report, "classification", "verify")
    assert verify["reason"] == "already covered by T4"
    assert (case, chosen) == before


@pytest.mark.parametrize("cycle,tier", [(2, "sonnet"), (5, "opus")])
def test_cycle_and_default_tier_reach_every_proposal(rc, cycle, tier):
    case, chosen = valid_batch()
    report = run(rc, case, chosen, cycle=cycle, default_tier=tier)
    assert_ok(report)
    [task] = report["task_proposals"]
    assert task["name"] == f"[D{cycle}] src/a.py" and "Tail sweep" not in task["name"]
    assert task["model"] == tier
    assert [p["cycle"] for p in actioned(report)] == [cycle, cycle]


def test_fix_rows_group_into_one_task_per_rework_group_and_no_fix_rows_propose_none(rc):
    groups = load_sibling("rework_groups")
    case = scenario(["R1", "R4", "R2"])
    chosen = [row("R1", "fix"), row("R4", "fix"), row("R2", "defer")]
    report = run(rc, case, chosen)
    assert_ok(report)
    expected = [f"[D2] {g['name_hint']}" for g in groups.group([chosen[0], chosen[1]])]
    assert len(expected) == 2
    assert [t["name"] for t in report["task_proposals"]] == expected
    assert len(proposals_with(report, "action", "fix-proposed")) == 2
    report = run(rc, case, [row("R1", "defer"), row("R4", "defer"), row("R2", "defer")])
    assert_ok(report)
    assert report["task_proposals"] == []
    assert len(proposals_with(report, "action", "deferred")) == 3


def test_clean_evidence_with_no_consolidated_rows_prepares_empty_proposals(rc):
    case = scenario([])
    report = run(rc, case, [])
    assert_ok(report)
    assert report["task_proposals"] == [] and report["decision_proposals"] == []
    outcomes = {r["job_ref"]: r["outcome"] for r in report["reviewer_results"]}
    assert outcomes == {"alice": "clean", "blake": "clean", "bob": "clean"}


def test_rubric_verdicts_and_reviewer_results_come_from_validated_evidence(rc):
    case, chosen = valid_batch()
    verdict = case["evidence"]["rubric_verdicts"][0]
    verdict["verdict"] = "fail"
    report = run(rc, case, chosen)
    assert_ok(report)
    pairs = {(v["rule_id"], v["verdict"]) for v in report["rubric_verdicts"]}
    expected = {(v["rule_id"], v["verdict"]) for v in case["evidence"]["rubric_verdicts"]}
    assert expected <= pairs and (verdict["rule_id"], "fail") in pairs
    outcomes = {r["job_ref"]: r["outcome"] for r in report["reviewer_results"]}
    assert outcomes == {"alice": "findings", "blake": "findings", "bob": "findings"}


def test_linked_source_findings_keep_the_evidence_body_while_issue_is_the_title(rc):
    case, chosen = valid_batch()
    report = run(rc, case, chosen)
    assert_ok(report)
    dumped = json.dumps(report, ensure_ascii=False)
    for fid in ("F1", "F2", "F3", "F4", "F5"):
        assert f"EVIDENCE-{fid} body" in dumped
    assert all("EVIDENCE-" not in str(p.get("issue", "")) for p in report["decision_proposals"])
    assert "EVIDENCE-" not in report["task_proposals"][0]["name"]


# --- evidence and review artifact -----------------------------------------------------------


def stale_prd(case: dict[str, Any]) -> None:
    case["evidence"]["source_bindings"]["prd_sha256"] = "1" * 63 + "0"


def stale_code(case: dict[str, Any]) -> None:
    case["evidence"]["verification"]["code_identity"] = "3" * 39 + "4"


def blind_diff(case: dict[str, Any]) -> None:
    blake = next(r for r in case["evidence"]["reviewer_results"] if r["job_ref"] == "blake")
    blake["received_input_refs"].append("diff:review-fixtures")


@pytest.mark.parametrize("mutate", [stale_prd, stale_code, blind_diff])
def test_invalid_evidence_is_refused_before_any_findings_check(rc, mutate):
    case, chosen = valid_batch()
    mutate(case)
    report = run(rc, case, chosen + [row("R4", "fix")])
    assert_refused(report)
    assert report["error"] not in FINDINGS_TOKENS


@pytest.mark.parametrize("variant", [
    lambda t: t + "\n",
    lambda t: t.replace("\n", "\r\n"),
    lambda t: unicodedata.normalize("NFD", t),
], ids=["trailing-newline", "crlf", "nfd"])
def test_review_text_must_hash_exactly_to_the_review_file_artifact(rc, variant):
    case, chosen = valid_batch()
    changed = variant(case["text"])
    assert changed != case["text"]
    assert_refused(run(rc, case, chosen, review_text=changed))


@pytest.mark.parametrize("ref", [REVIEW_REF + ".bak", "review-file.txt", "docs/dev/tmp/review/"])
def test_review_ref_must_equal_the_review_file_artifact_path(rc, ref):
    case, chosen = valid_batch()
    assert_refused(run(rc, case, chosen, review_ref=ref))


def test_review_ref_is_plumbed_and_exactly_one_review_file_artifact_is_required(rc):
    case, chosen = valid_batch()
    other = "docs/dev/tmp/review/round-2.md"
    artifact = next(a for a in case["evidence"]["artifacts"] if a["kind"] == "review-file")
    artifact["path"] = other
    assert_ok(run(rc, case, chosen, review_ref=other))
    assert_refused(run(rc, case, chosen))
    second = dict(artifact, artifact_id="review-file-2", path=REVIEW_REF)
    case["evidence"]["artifacts"].append(second)
    assert_refused(run(rc, case, chosen))
    assert_refused(run(rc, case, chosen, review_ref=other))


# --- finding linkage --------------------------------------------------------------------------


def test_finding_group_equivalence_links_equal_normalized_keys_to_one_row(rc):
    case, chosen = valid_batch()
    f2 = next(f for f in case["evidence"]["findings"] if f["finding_id"] == "F2")
    f2["title"] = "wrong  Default"
    report = run(rc, case, chosen)
    assert_ok(report)
    assert len(report["task_proposals"]) == 1


@pytest.mark.parametrize("field,value", [
    ("severity", "medium"), ("file", "src/a.pyc"), ("file", None), ("title", "Wrong defaults"),
], ids=["severity", "file-suffix", "null-file", "different-title"])
def test_linked_finding_must_match_row_severity_file_and_title(rc, field, value):
    case, chosen = valid_batch()
    f2 = next(f for f in case["evidence"]["findings"] if f["finding_id"] == "F2")
    f2[field] = value
    assert_refused(run(rc, case, chosen))


def test_null_file_projects_to_na_and_a_real_file_does_not(rc):
    case, chosen = valid_batch()
    assert_ok(run(rc, case, chosen))
    f5 = next(f for f in case["evidence"]["findings"] if f["finding_id"] == "F5")
    f5["file"] = "src/n.py"
    assert_refused(run(rc, case, chosen))


@pytest.mark.parametrize("ids_r1,ids_r3", [
    (["F1"], ["F5"]),
    (["F1", "F2", "F9"], ["F5"]),
    (["F1", "F2", "F1"], ["F5"]),
    (["F1", "F2"], ["F5", "F1"]),
    ([], ["F5"]),
    (DROP, ["F5"]),
], ids=["missing", "unknown", "duplicate", "multiply-linked", "empty", "absent"])
def test_every_evidence_finding_is_linked_by_exactly_one_row(rc, ids_r1, ids_r3):
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix", finding_ids=ids_r1), row("R2", "defer"), row("R3", "verify", finding_ids=ids_r3)]
    assert_rejected(rc, case, chosen)


@pytest.mark.parametrize("found_by,accepted", [
    (["blake", "alice", "alice"], True),
    (["alice"], False),
    (["alice", "blake", "bob"], False),
    (["alice", "blakey"], False),
])
def test_caller_found_by_must_equal_the_derived_reviewer_set(rc, found_by, accepted):
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix", found_by=found_by), row("R2", "defer"), row("R3", "defer")]
    report = run(rc, case, chosen)
    if accepted:
        assert_ok(report)
    else:
        assert_refused(report)


# --- consolidated table cross-check -----------------------------------------------------------


def test_chosen_row_absent_from_the_table_is_a_findings_mismatch(rc):
    case = scenario(["R1", "R2", "R3"], table_refs=["R1", "R3"])
    chosen = [row("R1", "fix"), row("R2", "defer"), row("R3", "defer")]
    assert_refused(run(rc, case, chosen), "findings_mismatch")
    chosen[1] = row("R2", "defer", ref="R9")
    assert_refused(run(rc, case, chosen), "findings_mismatch")


def test_table_row_no_chosen_row_covers_is_uncovered(rc):
    case = scenario(["R1", "R3"], table_refs=["R1", "R3", "R2"])
    chosen = [row("R1", "fix"), row("R3", "defer")]
    assert_refused(run(rc, case, chosen), "findings_uncovered")


def test_ref_less_table_requires_a_ref_column(rc):
    case = scenario(["R1"])
    body = "| Consensus | Severity | Issue | File | Task | Found By |\n|---|---|---|---|---|---|\n"
    body += f"| [2/3] | {EMOJI['high']} | Wrong default | src/a.py | - | alice, blake |\n"
    set_text(case, review_text("## Consolidated Findings\n\n" + body, 1))
    assert_refused(run(rc, case, [row("R1", "fix")]), "findings_ref_required")


@pytest.mark.parametrize("refs", [["R1"], []], ids=["with-rows", "clean"])
def test_review_without_a_findings_section_is_malformed_with_no_legacy_escape(rc, refs):
    case = scenario(refs)
    set_text(case, review_text("## Notes\n\nnothing here\n", len(refs)))
    assert_refused(run(rc, case, [row(r, "defer") for r in refs]), "findings_malformed")


def test_header_only_table_is_malformed(rc):
    case = scenario([])
    set_text(case, review_text("## Consolidated Findings\n\n" + HEADER, 0))
    assert_refused(run(rc, case, []), "findings_malformed")


def test_lowercase_ref_selects_its_row_but_conflicting_or_duplicate_refs_are_rejected(rc):
    case, chosen = valid_batch()
    assert_ok(run(rc, case, [dict(chosen[0], ref="r1"), *chosen[1:]]))
    conflicting = [*chosen, row("R1", "defer", finding_ids=DROP, found_by=DROP)]
    assert_rejected(rc, case, conflicting)
    duplicate = [*chosen, row("R1", "fix", finding_ids=DROP, found_by=DROP)]
    assert_rejected(rc, case, duplicate)


def test_off_table_verify_row_adds_nothing_but_an_off_table_fix_row_is_rejected(rc):
    case, chosen = valid_batch()
    note = {"severity": EMOJI["medium"], "file": "x.py", "issue": "noise", "classification": "verify"}
    baseline = run(rc, case, chosen)
    report = run(rc, case, [*chosen, note])
    assert_ok(report)
    assert report["task_proposals"] == baseline["task_proposals"]
    assert actioned(report) == actioned(baseline)
    assert_rejected(rc, case, [*chosen, dict(note, classification="fix")])
    assert_rejected(rc, case, [*chosen, dict(note, finding_ids=["F1"])])


@pytest.mark.parametrize("classification", ["Fix", "fixed", "", None])
def test_unknown_classification_is_rejected(rc, classification):
    case, chosen = valid_batch()
    chosen[0]["classification"] = classification
    assert_rejected(rc, case, chosen)


@pytest.mark.parametrize("chosen", ["R1", {"ref": "R1"}, ["R1"]], ids=["string", "dict", "row-string"])
def test_malformed_chosen_findings_shape_raises_value_error(rc, chosen):
    case = scenario(["R1"])
    with pytest.raises(ValueError):
        run(rc, case, chosen)


# --- no state access ----------------------------------------------------------------------------

RUNNER = r"""
import json, os, sys
sys.dont_write_bytecode = True
calls = json.loads(sys.stdin.read())
events = []
WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND
def hook(name, args):
    if name == "open" and isinstance(args[0], (str, bytes)):
        mode = args[1] if isinstance(args[1], str) else ""
        flags = args[2] if isinstance(args[2], int) else 0
        events.append([os.fsdecode(args[0]), any(m in mode for m in "wax+") or bool(flags & WRITE)])
    elif name in ("subprocess.Popen", "os.system", "os.posix_spawn", "os.exec"):
        events.append([name, True])
sys.addaudithook(hook)
sys.path.insert(0, sys.argv[1])
import review_close
reports, mutated = [], []
for kwargs in calls:
    before = json.dumps(kwargs, sort_keys=True)
    try:
        reports.append(review_close.prepare_close(**kwargs))
    except ValueError:
        reports.append({"raised": "ValueError"})
    mutated.append(json.dumps(kwargs, sort_keys=True) != before)
loaded = [m for m in ("statectl", "test_contract", "jsonschema") if sys.modules.get(m) is not None]
print(json.dumps({"reports": reports, "mutated": mutated, "loaded": loaded, "events": events}))
"""


def tree(base: Path) -> dict[str, bytes | None]:
    return {str(p.relative_to(base)): p.read_bytes() if p.is_file() else None for p in base.rglob("*")}


def no_state_calls() -> list[dict[str, Any]]:
    case, chosen = valid_batch()
    stale = copy.deepcopy(case)
    stale_prd(stale)
    tail = scenario(["R2", "R4"])
    snapshot = {"cycle": 2, "tasks": [], "rework_task_ids": [], "decision_gate_review_ref": REVIEW_REF,
                "deferred_decisions": []}
    mismatch = scenario(["R1", "R2", "R3"], table_refs=["R1", "R3"])
    return [
        kwargs_for(case, chosen),
        kwargs_for(stale, chosen),
        kwargs_for(tail, [row("R2", "fix"), row("R4", "defer")], batch_id="tail-sweep", read_snapshot=snapshot),
        kwargs_for(mismatch, chosen[:2] + [row("R3", "defer")]),
        kwargs_for(scenario([]), []),
    ]


def test_review_preparation_no_state_touches_no_state_queue_or_markers(tmp_path):
    state = tmp_path / "docs" / "dev" / "project-management" / "autopilot"
    state.mkdir(parents=True)
    (state / "state.json").write_text('{"phase": "review", "tasks": []}', encoding="utf-8")
    before = tree(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-I", "-c", RUNNER, str(SCRIPTS)],
        input=json.dumps(no_state_calls()), cwd=tmp_path, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert tree(tmp_path) == before
    out = json.loads(proc.stdout)
    assert out["loaded"] == [] and out["mutated"] == [False] * 5
    assert [r.get("ok") for r in out["reports"]] == [True, False, True, False, True]
    assert out["reports"][3]["error"] == "findings_mismatch"
    tmp_real = os.path.realpath(tmp_path)
    contracts = os.path.realpath(PACKAGE / "contracts") + os.sep
    for path, writes in out["events"]:
        real = os.path.realpath(os.path.join(tmp_real, path))
        assert not writes, path
        assert not real.startswith(tmp_real + os.sep), path
        if not real.endswith((".py", ".pyc", ".so")):
            assert real.startswith(contracts), path


# --- caller snapshots -----------------------------------------------------------------------------


def carry_task(**over: Any) -> dict[str, Any]:
    task = {"id": "T7", "name": "Fix typo", "carry_refs": ["R3"], "carry_cycle": 2,
            "escalation_reason": "review_flag", "status": "pending"}
    task.update(over)
    return task


def snapshot(**over: Any) -> dict[str, Any]:
    snap = {"cycle": 2, "tasks": [carry_task()], "rework_task_ids": ["T7"],
            "decision_gate_review_ref": REVIEW_REF, "deferred_decisions": []}
    snap.update(over)
    return snap


def carry_batch() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case = scenario(["R1", "R2", "R3"])
    return case, [row("R1", "fix"), row("R2", "defer"), row("R3", "carry", reason="re-queued as T7")]


def assert_controller_required(report: Any) -> None:
    assert isinstance(report, dict), report
    assert report["ok"] is False and report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert report["error"] == "controller-required" and report["operation"] == "prepare-close"
    assert not report.get("task_proposals")


def deferral(**over: Any) -> dict[str, Any]:
    entry = {"cycle": 1, "issue": "earlier", "severity": "medium", "file": "src/b.py",
             "action": "deferred", "reason": "r"}
    entry.update(over)
    return entry


# --- decision-gate single voice ---------------------------------------------------------------


@pytest.mark.parametrize("found_by", [["bob"], ["bob", "bob"], DROP], ids=["one", "duplicated", "missing"])
def test_decision_gate_low_fix_from_one_reviewer_is_single_voice(rc, found_by):
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix"), row("R2", "defer"), row("R3", "fix", found_by=found_by)]
    assert_refused(run(rc, case, chosen), "single_voice_fix")


def test_decision_gate_single_voice_applies_only_to_medium_or_low_fix_rows(rc):
    groups = load_sibling("rework_groups")
    case = scenario(["R2", "R3", "R5"])
    chosen = [row("R2", "fix"), row("R3", "defer"), row("R5", "fix")]
    report = run(rc, case, chosen)
    assert_ok(report)
    expected = [f"[D2] {g['name_hint']}" for g in groups.group([chosen[0], chosen[2]])]
    assert [t["name"] for t in report["task_proposals"]] == expected
    medium_single = scenario(["R2"])
    f4 = next(f for f in medium_single["evidence"]["findings"] if f["finding_id"] == "F4")
    f4["result_id"] = "alice-1"
    for result in medium_single["evidence"]["reviewer_results"]:
        if result["job_ref"] == "alice":
            result["finding_ids"] = ["F3", "F4"]
        if result["job_ref"] == "bob":
            result["outcome"], result["finding_ids"] = "clean", []
    assert_refused(run(rc, medium_single, [row("R2", "fix", found_by=["alice"])]), "single_voice_fix")
    assert_ok(run(rc, medium_single, [row("R2", "defer", found_by=["alice"])]))


def test_caller_label_cannot_invent_a_second_finder(rc):
    case = scenario(["R1", "R2", "R3"])
    chosen = [row("R1", "fix"), row("R2", "defer"), row("R3", "fix", found_by=["bob", "carl"])]
    assert_refused(run(rc, case, chosen))


# --- carry ----------------------------------------------------------------------------------------


def test_carry_row_without_a_snapshot_requires_the_controller(rc):
    case, chosen = carry_batch()
    assert_controller_required(run(rc, case, chosen))
    assert_controller_required(run(rc, case, chosen, read_snapshot=None))


@pytest.mark.parametrize("snap", [
    snapshot(),
    snapshot(tasks=[carry_task(carry_refs=["r3"])]),
    snapshot(tasks=[carry_task(id="T1", status="completed"), carry_task(escalation_reason="fable_rescue")],
             rework_task_ids=["T1", "T7"]),
], ids=["exact", "lowercase-ref", "second-task-matches"])
def test_carry_row_backed_by_an_unfinished_requeued_task_is_proposed_without_a_task(rc, snap):
    case, chosen = carry_batch()
    before = copy.deepcopy(snap)
    report = run(rc, case, chosen, read_snapshot=snap)
    assert_ok(report)
    assert [t["name"] for t in report["task_proposals"]] == ["[D2] src/a.py"]
    [carry] = proposals_with(report, "classification", "carry")
    assert carry["reason"] == "re-queued as T7"
    assert snap == before


@pytest.mark.parametrize("snap", [
    snapshot(tasks=[carry_task(status="completed")]),
    snapshot(tasks=[carry_task(carry_cycle=1)]),
    snapshot(rework_task_ids=["T70"]),
    snapshot(tasks=[carry_task(escalation_reason="manual")]),
    snapshot(tasks=[carry_task(carry_refs=["R33"])]),
    snapshot(tasks=[carry_task(id="T1"), carry_task(carry_cycle=1)], rework_task_ids=["T7"]),
    snapshot(tasks=[]),
], ids=["completed", "old-cycle", "not-requeued", "other-escalation", "near-miss-ref", "split", "no-tasks"])
def test_carry_row_without_one_task_meeting_every_condition_is_unmatched(rc, snap):
    case, chosen = carry_batch()
    assert_refused(run(rc, case, chosen, read_snapshot=snap), "carry_unmatched")


def test_snapshot_from_another_cycle_is_refused(rc):
    case, chosen = carry_batch()
    assert_ok(run(rc, case, chosen, cycle=2, read_snapshot=snapshot()))
    assert_refused(run(rc, case, chosen, cycle=3, read_snapshot=snapshot()))


@pytest.mark.parametrize("snap", [
    [],
    "snapshot",
    snapshot(tasks="T7"),
    snapshot(rework_task_ids="T7"),
    {k: v for k, v in snapshot().items() if k != "cycle"},
], ids=["list", "string", "tasks-string", "rework-string", "no-cycle"])
def test_malformed_supplied_snapshot_is_invalid_input(rc, snap):
    case, chosen = carry_batch()
    report = run(rc, case, chosen, read_snapshot=snap)
    assert_refused(report)
    assert report["error"] == "invalid-input"


# --- tail sweep -----------------------------------------------------------------------------------


def tail(rc, refs: list[str], chosen: list[dict[str, Any]], **over: Any) -> dict[str, Any]:
    over.setdefault("read_snapshot", snapshot(tasks=[], rework_task_ids=[]))
    return run(rc, scenario(refs), chosen, batch_id="tail-sweep", **over)


@pytest.mark.parametrize("cycle,tier", [(2, "sonnet"), (3, "opus")])
def test_tail_sweep_prefixes_task_names_and_keeps_cycle_and_tier(rc, cycle, tier):
    snap = snapshot(cycle=cycle, tasks=[], rework_task_ids=[])
    report = tail(rc, ["R2", "R4"], [row("R2", "fix"), row("R4", "defer")],
                  cycle=cycle, default_tier=tier, read_snapshot=snap)
    assert_ok(report)
    [task] = report["task_proposals"]
    assert (task["name"], task["model"]) == (f"[D{cycle}] Tail sweep: src/b.py", tier)
    [defer] = proposals_with(report, "action", "deferred")
    assert (defer["cycle"], defer["severity"], defer["file"]) == (cycle, EMOJI["medium"], "docs/guide.md")


def test_tail_sweep_without_a_snapshot_requires_the_controller(rc):
    report = run(rc, scenario(["R2", "R4"]), [row("R2", "fix"), row("R4", "defer")], batch_id="tail-sweep")
    assert_controller_required(report)


def test_tail_sweep_refuses_a_carry_row_before_the_missing_receipt(rc):
    chosen = [row("R2", "fix"), row("R4", "carry")]
    snap = snapshot(decision_gate_review_ref=None, tasks=[], rework_task_ids=[])
    assert_refused(tail(rc, ["R2", "R4"], chosen, read_snapshot=snap), "carry_in_tail_sweep")


@pytest.mark.parametrize("receipt", [None, REVIEW_REF + ".old", "docs/dev/tmp/review/review-file"])
def test_tail_sweep_needs_this_reviews_decision_gate_receipt_before_any_row_check(rc, receipt):
    snap = snapshot(decision_gate_review_ref=receipt, tasks=[], rework_task_ids=[])
    chosen = [row("R1", "fix"), row("R2", "fix")]
    assert_refused(tail(rc, ["R1", "R2"], chosen, read_snapshot=snap), "tail_sweep_before_decision_gate")
    assert_refused(tail(rc, [], [], read_snapshot=snap), "tail_sweep_before_decision_gate")


def test_empty_tail_sweep_is_refused(rc):
    assert_refused(tail(rc, [], []), "tail_sweep_empty")


def test_tail_sweep_refuses_rows_above_medium_before_single_voice_and_deferrals(rc):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral()])
    chosen = [row("R1", "fix"), row("R2", "fix"), row("R3", "defer")]
    assert_refused(tail(rc, ["R1", "R2", "R3"], chosen, read_snapshot=snap), "tail_sweep_above_medium")


def test_tail_sweep_refuses_a_single_voice_row_before_deferrals(rc):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral()])
    chosen = [row("R2", "fix"), row("R3", "defer")]
    assert_refused(tail(rc, ["R2", "R3"], chosen, read_snapshot=snap), "tail_sweep_single_voice")


@pytest.mark.parametrize("over,duplicate", [
    ({"severity": "medium", "file": " src/b.py "}, True),
    ({"severity": EMOJI["medium"], "file": "src/b.py"}, True),
    ({"severity": EMOJI["medium"], "file": "src/b.py.orig"}, False),
    ({"severity": "low", "file": "src/b.py"}, False),
], ids=["word-padded", "emoji", "near-miss-file", "other-severity"])
def test_tail_sweep_refuses_a_row_duplicating_an_open_deferral(rc, over, duplicate):
    snap = snapshot(tasks=[], rework_task_ids=[], deferred_decisions=[deferral(**over)])
    report = tail(rc, ["R2", "R4"], [row("R2", "fix"), row("R4", "defer")], read_snapshot=snap)
    if duplicate:
        assert_refused(report, "tail_sweep_duplicates_deferral")
    else:
        assert_ok(report)
