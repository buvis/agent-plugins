"""Prepare review-close proposals from validated AP00012 review evidence.

Port of the pure parts of the pinned `review_close` (`_mutation_context`,
`_findings_block`, `_add_decisions`) and of its refusal order, without the
state mutator: the report proposes rework tasks and decisions for the
controller to apply. It never discovers, reads or writes workflow state; the
optional read snapshot is caller data. Stdlib only.
"""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from typing import Any, Literal, TypedDict

import rework_groups
from findings import Row, finding_key, reviewed_rows
from review_evidence import check_evidence

KNOWN_CLASSIFICATIONS = ("verify", "discard", "fix", "defer", "carry")
# verify/discard rows are never applied, so the source lets them sit outside
# the consolidated table as bookkeeping notes.
_SKIPPED_CLASSIFICATIONS = ("verify", "discard")
_EMOJI = {
    "critical": "\U0001f534",
    "high": "\U0001f7e0",
    "medium": "\U0001f7e1",
    "low": "⚪",
}
_FINDINGS_PROBLEMS = {
    "no-section": "no '## Consolidated Findings' section in the review file",
    "unreadable-table": (
        "found a findings table whose header or rows could not be read: "
        "expected a header naming Severity, Issue and File and rows shaped "
        "| [m/n] | ... |, each closed with its own trailing |"
    ),
}
_REF_REQUIRED = (
    "coverage requires a Ref column; this section has at least one row with none"
)


class CarryTaskSnapshot(TypedDict):
    id: str
    name: str
    carry_refs: list[str]
    carry_cycle: int
    escalation_reason: Literal["review_flag", "fable_rescue"]
    status: str


class CloseReadSnapshot(TypedDict):
    cycle: int
    tasks: list[CarryTaskSnapshot]
    rework_task_ids: list[str]
    decision_gate_review_ref: str | None
    deferred_decisions: list[dict]


def _refusal(error: str, reason: str) -> dict[str, Any]:
    return {"schema_version": 1, "ok": False, "error": error, "reason": reason}


def _controller_required() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "ok": False,
        "error": "controller-required",
        "operation": "prepare-close",
    }


def _ref(row: dict) -> str:
    return str(row.get("ref", "")).strip().upper()


def _severity(row: dict) -> str:
    """The severity word of an emoji or word severity, "" when neither."""
    return finding_key(str(row.get("severity", "")), "", "")[0]


def _row_key(row: dict) -> tuple[str, str, str]:
    return finding_key(
        str(row.get("severity", "")),
        str(row.get("file", "")),
        str(row.get("issue", "")),
    )


def _finding_key(finding: dict) -> tuple[str, str, str]:
    """An AP00012 finding projected to a consolidated row's key."""
    return finding_key(
        _EMOJI[finding["severity"]], finding["file"] or "N/A", finding["title"]
    )


def _is_bookkeeping(row: dict) -> bool:
    """A verify/discard note outside the consolidated table: no ref, no links."""
    return (
        row.get("classification") in _SKIPPED_CLASSIFICATIONS
        and "finding_ids" not in row
        and not _ref(row)
    )


def _artifact_problem(evidence: dict, review_ref: Any, review_text: Any) -> str | None:
    reviews = [a for a in evidence["artifacts"] if a["kind"] == "review-file"]
    if len(reviews) != 1:
        return f"evidence needs exactly one review-file artifact, found {len(reviews)}"
    if reviews[0]["path"] != review_ref:
        return f"review_ref {review_ref!r} is not the review-file artifact path"
    if not isinstance(review_text, str) or (
        hashlib.sha256(review_text.encode("utf-8")).hexdigest() != reviews[0]["sha256"]
    ):
        return "review_text does not hash to the review-file artifact sha256"
    return None


def _snapshot_valid(snap: Any) -> bool:
    return (
        isinstance(snap, dict)
        and type(snap.get("cycle")) is int
        and isinstance(snap.get("tasks"), list)
        and all(isinstance(t, dict) for t in snap["tasks"])
        and isinstance(snap.get("rework_task_ids"), list)
        and "decision_gate_review_ref" in snap
        and isinstance(snap["decision_gate_review_ref"], (str, type(None)))
        and isinstance(snap.get("deferred_decisions"), list)
    )


def _input_refusal(
    evidence: dict,
    review_ref: Any,
    review_text: Any,
    rows: list[dict],
    cycle: int,
    batch_id: str,
    snap: Any,
) -> dict[str, Any] | None:
    """Artifact, classification and snapshot refusals, before any linkage."""
    problem = _artifact_problem(evidence, review_ref, review_text)
    if problem is not None:
        return _refusal("review_artifact_mismatch", problem)
    unknown = [r.get("classification") for r in rows]
    unknown = [c for c in unknown if c not in KNOWN_CLASSIFICATIONS]
    if unknown:
        return _refusal(
            "unknown_classification",
            f"classification {unknown[0]!r} is not one of {'|'.join(KNOWN_CLASSIFICATIONS)}",
        )
    if snap is None:
        needed = batch_id == "tail-sweep" or any(
            r["classification"] == "carry" for r in rows
        )
        return _controller_required() if needed else None
    if not _snapshot_valid(snap):
        return _refusal(
            "invalid-input",
            "read_snapshot needs cycle, tasks, rework_task_ids, "
            "decision_gate_review_ref and deferred_decisions",
        )
    if snap["cycle"] != cycle:
        return _refusal(
            "snapshot_cycle_mismatch",
            f"read_snapshot cycle {snap['cycle']} is not cycle {cycle}",
        )
    return None


def _row_links(
    n: int, row: dict, findings: dict[str, dict], jobs: dict[str, str]
) -> tuple[dict | None, str | None]:
    """({"findings", "found_by"} for one consolidated row, or its problem)."""
    ids = row.get("finding_ids")
    if not (
        isinstance(ids, list)
        and ids
        and all(isinstance(i, str) for i in ids)
        and len(set(ids)) == len(ids)
    ):
        return None, f"row {n}: finding_ids must be a nonempty list of unique strings"
    unknown = [i for i in ids if i not in findings]
    if unknown:
        return None, f"row {n}: unknown finding ids {unknown}"
    linked = [findings[i] for i in ids]
    off = [f["finding_id"] for f in linked if _finding_key(f) != _row_key(row)]
    if off:
        return None, f"row {n}: findings {off} differ in severity, file or issue"
    derived = sorted({jobs[f["result_id"]] for f in linked})
    found_by = row.get("found_by")
    if "found_by" in row and not (
        isinstance(found_by, list)
        and all(isinstance(j, str) for j in found_by)
        and set(found_by) == set(derived)
    ):
        return None, f"row {n}: found_by {found_by!r} is not the reviewer set {derived}"
    return {"findings": linked, "found_by": derived}, None


def _link(evidence: dict, rows: list[dict]) -> tuple[dict[int, dict], str | None]:
    """Links of every consolidated row by index, or the first attribution
    problem. Every evidence finding must be linked by exactly one row."""
    findings = {f["finding_id"]: f for f in evidence["findings"]}
    jobs = {r["result_id"]: r["job_ref"] for r in evidence["reviewer_results"]}
    links: dict[int, dict] = {}
    seen: Counter[str] = Counter()
    for n, row in enumerate(rows):
        if _is_bookkeeping(row):
            continue
        link, problem = _row_links(n, row, findings, jobs)
        if problem is not None:
            return {}, problem
        seen.update(row["finding_ids"])
        links[n] = link
    multiply = sorted(i for i, count in seen.items() if count > 1)
    missing = sorted(set(findings) - set(seen))
    if multiply or missing:
        return {}, f"findings linked more than once {multiply}, never linked {missing}"
    return links, None


def _backed(row: dict, reviewed: list[Row]) -> bool:
    """A ref row is backed by the table row holding that ref with an agreeing
    severity and file; a ref-less row by an exact normalized key."""
    severity, file, issue = _row_key(row)
    ref = _ref(row)
    if ref:
        return any(
            r.ref == ref and (r.severity, r.file) == (severity, file) for r in reviewed
        )
    return bool(issue) and any(
        (r.severity, r.file, r.issue.lower()) == (severity, file, issue)
        for r in reviewed
    )


def _cross_check(text: str, rows: list[dict], coverage: bool) -> dict | None:
    """Chosen rows against the consolidated table, in the source order:
    malformed, duplicate or conflicting ref, ref-required, unbacked, uncovered."""
    reviewed, problem = reviewed_rows(text)
    if problem is not None:
        return _refusal("findings_malformed", _FINDINGS_PROBLEMS[problem])
    refs: dict[str, Any] = {}
    for row in rows:
        ref = _ref(row)
        if ref in refs:
            return _refusal(
                "findings_mismatch",
                f"finding ref {ref} chosen twice: {refs[ref]} and {row['classification']}",
            )
        if ref:
            refs[ref] = row["classification"]
    if coverage and any(r.ref == "" for r in reviewed):
        return _refusal("findings_ref_required", _REF_REQUIRED)
    for row in rows:
        if not _is_bookkeeping(row) and not _backed(row, reviewed):
            return _refusal(
                "findings_mismatch",
                "chosen finding absent from the review file's consolidated findings: "
                f"{_ref(row)} {row.get('severity', '')} {row.get('file', '')} | "
                f"{row.get('issue', '')}",
            )
    uncovered = [r.ref for r in reviewed if r.ref not in refs]
    if coverage and uncovered:
        return _refusal(
            "findings_uncovered",
            f"review rows no chosen finding names: {', '.join(uncovered)}",
        )
    return None


def _found_by_count(row: dict, jobs: set[str]) -> int:
    """Distinct validated reviewer jobs in a list `found_by`; missing or
    non-list counts as zero."""
    found_by = row.get("found_by")
    if not isinstance(found_by, list):
        return 0
    return len({j for j in found_by if isinstance(j, str)} & jobs)


def _single_voice_refusal(rows: list[dict], batch_id: str, jobs: set[str]) -> dict | None:
    """A decision gate refuses the first medium/low fix row with fewer than
    two finders; a tail sweep refuses the first row of any kind."""
    if batch_id == "decision-gate":
        for row in rows:
            if (
                row["classification"] == "fix"
                and _severity(row) in ("medium", "low")
                and _found_by_count(row, jobs) < 2
            ):
                return _refusal(
                    "single_voice_fix",
                    f"a single-voice medium/low row cannot become a task: {row.get('ref')}",
                )
        return None
    for row in rows:
        if _found_by_count(row, jobs) < 2:
            return _refusal(
                "tail_sweep_single_voice",
                f"tail sweep refuses a single-voice row: {row.get('ref') or row.get('file')}",
            )
    return None


def _deferral_key(entry: dict) -> tuple[str, str]:
    """Normalized (severity word, file) of a row or a deferral entry."""
    return finding_key(str(entry.get("severity", "")), str(entry.get("file", "")), "")[:2]


def _tail_sweep_refusal(
    snap: dict, review_ref: str, rows: list[dict], jobs: set[str]
) -> dict | None:
    """Tail-sweep refusals in the source order: carry, missing decision-gate
    receipt for this review, empty, above medium, single voice, duplicate
    open deferral."""
    if any(r["classification"] == "carry" for r in rows):
        return _refusal("carry_in_tail_sweep", "a tail-sweep batch never carries a carry row")
    if snap["decision_gate_review_ref"] != review_ref:
        return _refusal(
            "tail_sweep_before_decision_gate",
            "tail sweep refused: this review's decision-gate batch has no receipt",
        )
    if not rows:
        return _refusal("tail_sweep_empty", "tail sweep findings must not be empty")
    above = [r for r in rows if _severity(r) in ("critical", "high")]
    if above:
        return _refusal(
            "tail_sweep_above_medium",
            f"tail sweep refuses rows above medium: {above[0].get('ref') or above[0].get('file')}",
        )
    single_voice = _single_voice_refusal(rows, "tail-sweep", jobs)
    if single_voice is not None:
        return single_voice
    open_keys = {_deferral_key(d) for d in snap["deferred_decisions"] if isinstance(d, dict)}
    for row in rows:
        if _deferral_key(row) in open_keys:
            return _refusal(
                "tail_sweep_duplicates_deferral",
                f"tail sweep row duplicates an open deferral: {row.get('severity', '')} "
                f"{_deferral_key(row)[1]}",
            )
    return None


def _carry_unmatched(row: dict, cycle: int, snap: dict) -> bool:
    """True unless one task carries the row's ref for this cycle, is re-queued
    by a review flag or fable rescue, and is not completed."""
    ref = _ref(row)
    return not ref or not any(
        ref in [str(r).strip().upper() for r in (t.get("carry_refs") or [])]
        and t.get("carry_cycle") == cycle
        and str(t.get("id")) in snap["rework_task_ids"]
        and t.get("escalation_reason") in ("review_flag", "fable_rescue")
        and t.get("status") != "completed"
        for t in snap["tasks"]
    )


def _gate_refusal(
    snap: dict | None, review_ref: str, rows: list[dict], cycle: int, batch_id: str, jobs: set[str]
) -> dict | None:
    if batch_id == "tail-sweep":
        return _tail_sweep_refusal(snap, review_ref, rows, jobs)
    if batch_id == "decision-gate":
        single_voice = _single_voice_refusal(rows, batch_id, jobs)
        if single_voice is not None:
            return single_voice
    for row in rows:
        if row["classification"] == "carry" and _carry_unmatched(row, cycle, snap):
            return _refusal(
                "carry_unmatched",
                f"carry row ref {_ref(row) or '(none)'}: no unfinished re-queued task "
                f"of cycle {cycle} carries it",
            )
    return None


def _findings_block(findings: list[dict]) -> str:
    lines = []
    for f in findings:
        found_by = f.get("found_by") or []
        suffix = f" (found by: {', '.join(found_by)})" if found_by else ""
        lines.append(f"- {f['severity']} {f['file']}: {f['issue']}{suffix}")
    return "### Findings (verbatim)\n" + "\n".join(lines) + "\n"


def _task_proposals(
    rows: list[dict], links: dict[int, dict], cycle: int, batch_id: str, tier: str
) -> list[dict]:
    """One proposed task per rework group of the fix rows; no durable ids."""
    prefix = "Tail sweep: " if batch_id == "tail-sweep" else ""
    fixes = [
        {
            "severity": _EMOJI[_severity(row)],
            "file": str(row.get("file", "")),
            "issue": str(row.get("issue", "")),
            "found_by": links[n]["found_by"],
        }
        for n, row in enumerate(rows)
        if row["classification"] == "fix"
    ]
    return [
        {
            "name": f"[D{cycle}] {prefix}{grp['name_hint']}",
            "description": _findings_block(grp["findings"]),
            "model": tier,
        }
        for grp in rework_groups.group(fixes)
    ]


def _decision(row: dict, link: dict | None, cycle: int) -> dict[str, Any]:
    """A fix-proposed or deferred decision, or the supplied verify, discard or
    carry classification; each keeps its linked source findings unchanged."""
    classification = row["classification"]
    proposal: dict[str, Any] = {
        "ref": _ref(row),
        "classification": classification,
        "cycle": cycle,
        "issue": str(row.get("issue", "")),
        "finding_ids": list(row.get("finding_ids") or []),
        "source_findings": copy.deepcopy(link["findings"]) if link else [],
    }
    if classification == "fix":
        proposal.update(
            severity=_severity(row),
            action="fix-proposed",
            reason=row.get("reason") or "fix proposed by review-close",
        )
    elif classification == "defer":
        proposal.update(
            severity=_EMOJI[_severity(row)],
            file=str(row.get("file", "")),
            action="deferred",
            reason=row.get("reason") or "deferred by review-close",
        )
    else:
        proposal.update(
            severity=row.get("severity"), file=row.get("file"), reason=row.get("reason")
        )
    return proposal


def prepare_close(
    *,
    policy: dict,
    expected_context: dict,
    evidence: dict,
    review_ref: str,
    review_text: str,
    chosen_findings: list[dict],
    cycle: int,
    batch_id: str,
    default_tier: str,
    read_snapshot: CloseReadSnapshot | None = None,
) -> dict:
    """Validate the evidence, review artifact, finding links, consolidated
    table and close gates, then propose tasks and decisions. ValueError when
    `chosen_findings` is not a list of row objects."""
    if not isinstance(chosen_findings, list) or not all(
        isinstance(row, dict) for row in chosen_findings
    ):
        raise ValueError("chosen_findings must be a list of row objects")
    checked = check_evidence(policy, expected_context, evidence)
    if not checked["ok"]:
        return _refusal("invalid-evidence", ", ".join(checked["defects"]))
    rows = chosen_findings
    refusal = _input_refusal(
        evidence, review_ref, review_text, rows, cycle, batch_id, read_snapshot
    )
    if refusal is not None:
        return refusal
    links, problem = _link(evidence, rows)
    if problem is not None:
        return _refusal("attribution_mismatch", problem)
    jobs = {r["job_ref"] for r in evidence["reviewer_results"]}
    tail_sweep = batch_id == "tail-sweep"
    refusal = _cross_check(review_text, rows, not tail_sweep) or _gate_refusal(
        read_snapshot, review_ref, rows, cycle, batch_id, jobs
    )
    if refusal is not None:
        return refusal
    return {
        "schema_version": 1,
        "ok": True,
        "controller_required": True,
        "task_proposals": _task_proposals(rows, links, cycle, batch_id, default_tier),
        "decision_proposals": [_decision(r, links.get(n), cycle) for n, r in enumerate(rows)],
        # A tail sweep proposes no lens close-out.
        "rubric_verdicts": [] if tail_sweep else copy.deepcopy(evidence["rubric_verdicts"]),
        "reviewer_results": [] if tail_sweep else copy.deepcopy(evidence["reviewer_results"]),
    }
