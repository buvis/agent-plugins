"""Packaged review staging writes isolated artifacts and complete prompts without workflow state."""

from __future__ import annotations

import copy
import hashlib
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import test_contract as contract
from test_contract import ROOT

PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
FIXTURES = contract.load(contract.FIXTURES_FILE)
CASES = {case["name"]: case for case in FIXTURES["cases"]}
TREE = "4" * 40
PRD_REF = "prd:00019"
TREE_REF = f"repo-tree:{TREE}"
DIFF_REF = "diff:review-fixtures"
DESIGN = "DESIGN-MARKER-7f3a design body"
CONTEXT = "CONTEXT-MARKER-91c2 broad review context"
DIFF = "diff --git a/x.py b/x.py\n+DIFF-MARKER-55d0\n"
PACK = "PACK-MARKER-a1b2 similar code"
SETTLED = "SETTLED-MARKER-c3d4"
PRIOR = "PRIOR-FINDINGS-MARKER-e5f6"
GATE = "TEST-GATE-MARKER-0a9b 512 passed"
PRD = (
    "# PRD 00019\r\n\n  Leading and trailing spaces  \n"
    "## Design Doc\nliteral heading inside the actual PRD\n"
    "Tokens stay literal: {PRD} {RUBRIC} {OUTPUT_FORMAT} {CONTEXT_FILE}\n"
    "naïve café"
)
BLAKE_TOKENS = ("{PRD}", "{RUBRIC}", "{OUTPUT_FORMAT}")
BOB_TOKENS = (
    "{CONTEXT_FILE}",
    "{DIFF_FILE}",
    "{REVIEW_CHECKLIST}",
    "{RUBRIC}",
    "{OUTPUT_FORMAT}",
)


@pytest.fixture
def stage():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module("review_stage")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, timeout=60)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "docs" / "dev" / "tmp").mkdir(parents=True)
    state = project / "docs" / "dev" / "project-management" / "autopilot"
    state.mkdir(parents=True)
    (state / "state.json").write_text('{"phase": "review"}', encoding="utf-8")
    wip = project / "docs" / "dev" / "project-management" / "prds" / "wip"
    wip.mkdir(parents=True)
    (wip / "00019-review.md").write_text(PRD, encoding="utf-8")
    git("init", "-q", str(project))
    return project


def context_for(prd_text: str, case: str = "full-clean") -> dict[str, Any]:
    context = copy.deepcopy(CASES[case]["expected_context"])
    context["source_bindings"]["prd_sha256"] = sha(prd_text)
    return context


def texts_for(context: dict[str, Any], prd_text: str) -> dict[str, str]:
    values = {PRD_REF: prd_text, TREE_REF: TREE, DIFF_REF: DIFF}
    return {
        ref: values.get(ref, f"LITERAL-{ref}")
        for ref in context["allowed_inputs"]["input_refs"]
    }


def call(stage, root: Path, **overrides: Any) -> dict[str, Any]:
    prd_text = overrides.pop("prd_text", PRD)
    context = overrides.pop("expected_context", None) or context_for(prd_text)
    kwargs = {
        "project_root": root,
        "artifact_root": root / "docs" / "dev" / "tmp" / "rev",
        "cycle_id": "c1",
        "tasks": [],
        "prd_text": prd_text,
        "design_text": DESIGN,
        "context_text": CONTEXT,
        "diff_text": DIFF,
        "expected_context": context,
        "input_texts": texts_for(context, prd_text),
        "pack_text": PACK,
        "settled_text": SETTLED,
        "prior_findings_text": PRIOR,
        "test_gate_text": GATE,
    }
    kwargs.update(overrides)
    return stage.stage_review(**kwargs)


def snapshot(base: Path, skip: Path | None = None) -> dict[str, bytes | None]:
    out: dict[str, bytes | None] = {}
    for path in base.rglob("*"):
        if ".git" in path.relative_to(base).parts:
            continue
        if skip is not None and (path == skip or skip in path.parents):
            continue
        if path.is_symlink():
            out[str(path.relative_to(base))] = os.readlink(path).encode()
        else:
            out[str(path.relative_to(base))] = (
                None if path.is_dir() else path.read_bytes()
            )
    return out


def text(path: str | Path) -> str:
    return Path(path).read_bytes().decode("utf-8")


def assert_refused(report: Any) -> None:
    assert isinstance(report, dict), report
    assert report["ok"] is False
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int


def assert_invalid_input(report: Any) -> None:
    assert_refused(report)
    assert report["error"] == "invalid-input"


def roster(context: dict[str, Any]) -> set[str]:
    return {row["job_id"] for row in context["resolved_roster"]}


# --- result shape and artifacts ---------------------------------------------------------------


def test_success_report_lists_hashed_absolute_artifacts_and_one_prompt_per_resolved_job(
    stage, root
):
    report = call(stage, root)
    art = (root / "docs" / "dev" / "tmp" / "rev").resolve()
    assert set(report) == {
        "schema_version",
        "ok",
        "artifacts",
        "prompts",
        "input_manifest",
    }
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert report["ok"] is True
    names = set()
    for row in report["artifacts"]:
        assert set(row) == {"kind", "path", "sha256"}
        assert isinstance(row["kind"], str) and row["kind"]
        path = Path(row["path"])
        assert path.is_absolute() and art in path.resolve().parents
        assert row["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        names.add(path.name)
    staged = {
        "review-tasks-c1.md",
        "review-prd-raw-c1.md",
        "review-prd-c1.md",
        "review-context-c1.md",
        "review-diff-c1.diff",
    }
    assert staged <= names
    assert set(report["prompts"]) == {"alice", "blake", "bob"}
    for job, prompt in report["prompts"].items():
        assert Path(prompt).is_absolute() and Path(prompt).name == f"{job}-prompt-c1.md"
        assert Path(prompt).resolve().parent == art and Path(prompt).is_file()
    written = {p.name for p in art.iterdir()}
    assert written == names | {Path(p).name for p in report["prompts"].values()}


def test_prompt_roster_follows_the_supplied_context_not_a_discovered_lane(stage, root):
    full = call(stage, root, cycle_id="full1")
    context = context_for(PRD, "fast-track-clean")
    fast = call(stage, root, cycle_id="fast1", expected_context=context)
    assert set(full["prompts"]) == roster(CASES["full-clean"]["expected_context"])
    assert set(fast["prompts"]) == roster(context)
    assert set(fast["prompts"]) != set(full["prompts"])
    assert all(
        Path(p).name.endswith("-prompt-fast1.md") for p in fast["prompts"].values()
    )


def test_relative_artifact_root_resolves_against_project_root_not_cwd(
    stage, root, tmp_path, monkeypatch
):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    report = call(stage, root, artifact_root=Path("docs/dev/tmp/relrev"))
    assert report["ok"] is True
    assert (root / "docs" / "dev" / "tmp" / "relrev" / "review-prd-raw-c1.md").is_file()
    assert list(elsewhere.rglob("*")) == []
    assert all(Path(row["path"]).is_absolute() for row in report["artifacts"])


def test_diff_file_is_written_only_when_diff_text_is_supplied(stage, root):
    art = root / "docs" / "dev" / "tmp" / "rev"
    with_diff = call(stage, root, cycle_id="d1")
    assert DIFF in text(art / "review-diff-d1.diff")
    without = call(stage, root, cycle_id="d2", diff_text=None)
    assert without["ok"] is True
    assert not (art / "review-diff-d2.diff").exists()
    assert all(
        not Path(row["path"]).name.endswith(".diff") for row in without["artifacts"]
    )
    assert any(
        Path(row["path"]).name == "review-diff-d1.diff"
        for row in with_diff["artifacts"]
    )


def test_context_file_carries_the_supplied_context_text(stage, root):
    art = root / "docs" / "dev" / "tmp" / "rev"
    call(stage, root, cycle_id="k1")
    call(stage, root, cycle_id="k2", context_text="CONTEXT-OTHER-3e3e")
    assert CONTEXT in text(art / "review-context-k1.md")
    assert "CONTEXT-OTHER-3e3e" in text(art / "review-context-k2.md")
    assert CONTEXT not in text(art / "review-context-k2.md")


# --- cycle id ----------------------------------------------------------------------------------


@pytest.mark.parametrize("cycle_id", ["c1", "A", "7.b_c-9", "x..y"])
def test_cycle_id_matching_the_pattern_is_accepted(stage, root, cycle_id):
    report = call(stage, root, cycle_id=cycle_id)
    assert report["ok"] is True
    assert (
        root / "docs" / "dev" / "tmp" / "rev" / f"review-prd-raw-{cycle_id}.md"
    ).is_file()


@pytest.mark.parametrize(
    "cycle_id", ["", ".c1", "-c1", "_c1", "c1/x", "../c1", "c 1", "c1\n", "c1:x"]
)
def test_cycle_id_outside_the_pattern_is_refused_before_any_write(
    stage, root, tmp_path, cycle_id
):
    before = snapshot(tmp_path)
    assert_refused(call(stage, root, cycle_id=cycle_id))
    assert snapshot(tmp_path) == before


# --- PRD bytes and source identity ---------------------------------------------------------------


@pytest.mark.parametrize(
    "prd_text",
    [PRD, "line one\nline two\n\n", "  x\r\n"],
    ids=["mixed", "blank-tail", "crlf"],
)
def test_raw_prd_preserves_exact_utf8_bytes(stage, root, prd_text):
    report = call(stage, root, prd_text=prd_text)
    assert report["ok"] is True
    raw = root / "docs" / "dev" / "tmp" / "rev" / "review-prd-raw-c1.md"
    assert raw.read_bytes() == prd_text.encode("utf-8")
    row = next(r for r in report["artifacts"] if Path(r["path"]).name == raw.name)
    assert row["sha256"] == sha(prd_text)


@pytest.mark.parametrize(
    "variant",
    [PRD.strip(), PRD + "\n", PRD.replace("\r\n", "\n"), PRD[:-1]],
    ids=["trimmed", "newline-added", "crlf-normalized", "truncated"],
)
def test_prd_text_differing_from_the_bound_digest_is_refused_before_any_write(
    stage, root, tmp_path, variant
):
    context = context_for(PRD)
    before = snapshot(tmp_path)
    report = call(
        stage,
        root,
        prd_text=variant,
        expected_context=context,
        input_texts=texts_for(context, variant),
    )
    assert_invalid_input(report)
    assert snapshot(tmp_path) == before


def test_prd_input_ref_must_carry_the_same_content_as_prd_text(stage, root, tmp_path):
    context = context_for(PRD)
    texts = texts_for(context, PRD)
    texts[PRD_REF] = PRD + " "
    before = snapshot(tmp_path)
    assert_invalid_input(call(stage, root, expected_context=context, input_texts=texts))
    assert snapshot(tmp_path) == before


def test_repo_tree_ref_must_name_the_bound_tree_sha(stage, root, tmp_path):
    context = context_for(PRD)
    near = texts_for(context, PRD)
    near[TREE_REF] = "4" * 39 + "5"
    other = texts_for(context, PRD)
    del other[TREE_REF]
    other["repo-tree:" + "5" * 40] = "5" * 40
    before = snapshot(tmp_path)
    for texts in (near, other):
        assert_invalid_input(
            call(stage, root, expected_context=context, input_texts=texts)
        )
    assert snapshot(tmp_path) == before
    good = call(
        stage, root, expected_context=context, input_texts=texts_for(context, PRD)
    )
    assert good["ok"] is True


def test_invalid_expected_context_is_refused_before_any_write(stage, root, tmp_path):
    corrupt = context_for(PRD)
    corrupt["session_identities"]["independent_contexts_required"] = False
    before = snapshot(tmp_path)
    assert_refused(
        call(
            stage,
            root,
            expected_context=corrupt,
            input_texts=texts_for(context_for(PRD), PRD),
        )
    )
    assert snapshot(tmp_path) == before


def test_input_values_are_inline_text_never_opened_as_paths(stage, root):
    decoy = root / "docs" / "dev" / "tmp" / "decoy.txt"
    decoy.write_text("DECOY-FILE-CONTENT-77aa", encoding="utf-8")
    context = context_for(PRD)
    texts = texts_for(context, PRD)
    texts["rubric:review-policy-v1"] = str(decoy)
    report = call(stage, root, expected_context=context, input_texts=texts)
    art = root / "docs" / "dev" / "tmp" / "rev"
    assert report["ok"] is True
    assert all("DECOY-FILE-CONTENT-77aa" not in text(p) for p in art.iterdir())


# --- raw versus merged PRD -----------------------------------------------------------------------


def test_only_the_merged_prd_appends_design_and_raw_keeps_literal_design_heading(
    stage, root
):
    call(stage, root, cycle_id="m1")
    call(stage, root, cycle_id="m2", design_text="DESIGN-OTHER-4b4b")
    art = root / "docs" / "dev" / "tmp" / "rev"
    raw, merged = text(art / "review-prd-raw-m1.md"), text(art / "review-prd-m1.md")
    assert "## Design Doc\nliteral heading inside the actual PRD" in raw
    assert DESIGN not in raw
    assert PRD in merged and DESIGN in merged
    assert merged.index(DESIGN) > merged.index(PRD)
    other = text(art / "review-prd-m2.md")
    assert "DESIGN-OTHER-4b4b" in other and DESIGN not in other


# --- task rendering and findings precedent -------------------------------------------------------

TABLE_HEAD = (
    "| ID | Task | Status | Commit | Description | Shared with |\n"
    "|----|------|--------|--------|-------------|-------------|\n"
)
FOLDED = [
    {
        "id": 3,
        "name": "Parse | split",
        "status": "done",
        "commit": "abc1234",
        "description": "first line\nsecond | part\n",
        "companions": [4],
    },
    {
        "id": 4,
        "name": "",
        "subject": "Subject fallback",
        "status": "done",
        "commit": "abc1234",
        "description": None,
        "companions": [3, "7b"],
    },
]
FOLDED_ROWS = (
    "| 3 | Parse \\| split | done | abc1234 | first line second \\| part | 4 |\n"
    "| 4 | Subject fallback | done | abc1234 |  | 3, 7b |\n"
)


def test_render_tasks_of_no_tasks_is_the_empty_string(stage):
    assert stage.render_tasks([]) == ""


def test_render_tasks_escapes_pipes_and_newlines_and_keeps_each_folded_task_row(stage):
    tasks = copy.deepcopy(FOLDED)
    assert stage.render_tasks(tasks) == TABLE_HEAD + FOLDED_ROWS
    assert tasks == FOLDED


def test_render_tasks_strips_cells_and_treats_missing_companions_and_none_as_empty(
    stage,
):
    tasks = [
        {
            "id": "  t1 ",
            "name": None,
            "subject": "\n Sub \n",
            "status": None,
            "commit": " c0ffee ",
            "description": "  padded  ",
        }
    ]
    assert stage.render_tasks(tasks) == (
        TABLE_HEAD + "| t1 | Sub |  | c0ffee | padded |  |\n"
    )


def test_render_tasks_keeps_input_order(stage):
    rows = stage.render_tasks(list(reversed(FOLDED))).splitlines()
    assert rows[2].startswith("| 4 |") and rows[3].startswith("| 3 |")
    assert len(rows) == 4


def test_findings_precedent_without_a_pack_uses_the_pinned_fallback(stage):
    assert stage.findings_precedent(None) == "(no pack available this cycle)"


def test_findings_precedent_without_the_section_uses_the_pinned_fallback(stage):
    pack = "# Pack\nFindings precedent is mentioned in prose.\n## Other\nbody\n"
    assert stage.findings_precedent(pack) == (
        "(the pack has no Findings precedent section)"
    )


@pytest.mark.parametrize("stop", ["## Other", "# Top"])
def test_findings_precedent_stops_at_a_same_or_higher_heading_but_keeps_deeper_ones(
    stage, stop
):
    pack = (
        "# Pack\nintro\n## Findings precedent\n\nF1 fixed by guard\n"
        f"### Deeper\nkept detail\n\n{stop}\nOUTSIDE\n"
    )
    assert stage.findings_precedent(pack) == "F1 fixed by guard\n### Deeper\nkept detail"


def test_findings_precedent_heading_match_is_case_insensitive_and_runs_to_the_end(stage):
    pack = "## findings PRECEDENT\n  F2 precedent  \n#### Deep\ntail\n"
    assert stage.findings_precedent(pack) == "F2 precedent  \n#### Deep\ntail"


def test_level_one_findings_precedent_runs_through_subheadings_to_the_next_top_heading(
    stage,
):
    pack = (
        "# Findings precedent\nlead\n## Sub one\na\n#nospace line\n## Sub two\nb\n"
        "# Next\nOUTSIDE\n"
    )
    assert stage.findings_precedent(pack) == (
        "lead\n## Sub one\na\n#nospace line\n## Sub two\nb"
    )


def test_staged_task_and_context_files_carry_task_rows_and_precedent_text(stage, root):
    pack = "# Pack\n## Findings precedent\nPRECEDENT-MARKER-9d9d guard\n## Other\nx\n"
    report = call(stage, root, cycle_id="t5", tasks=copy.deepcopy(FOLDED), pack_text=pack)
    art = root / "docs" / "dev" / "tmp" / "rev"
    assert report["ok"] is True
    tasks_file = text(art / "review-tasks-t5.md")
    assert TABLE_HEAD + FOLDED_ROWS in tasks_file
    assert "PRECEDENT-MARKER-9d9d guard" in text(art / "review-context-t5.md")
    blake = text(report["prompts"]["blake"])
    assert "Parse \\| split" not in blake and "PRECEDENT-MARKER-9d9d" not in blake


# --- prompts and isolation -----------------------------------------------------------------------


def blake_forbidden(art: Path, cycle: str) -> list[str]:
    paths = [
        art / f"review-prd-{cycle}.md",
        art / f"review-context-{cycle}.md",
        art / f"review-diff-{cycle}.diff",
        art / f"review-tasks-{cycle}.md",
    ]
    return [
        DESIGN,
        CONTEXT,
        "DIFF-MARKER-55d0",
        PACK,
        SETTLED,
        PRIOR,
        GATE,
        DIFF_REF,
        *[p.name for p in paths],
        *[str(p) for p in paths],
        "alice-prompt",
        "bob-prompt",
    ]


def test_blake_receives_raw_prd_and_blind_rubric_without_any_nonblind_input(
    stage, root
):
    report = call(stage, root)
    art = root / "docs" / "dev" / "tmp" / "rev"
    prompt = text(report["prompts"]["blake"])
    assert prompt.count(PRD) == 1
    assert "B1: The implementation satisfies all specified behaviors" in prompt
    for needle in blake_forbidden(art, "c1") + [
        str(art.resolve() / "review-prd-c1.md")
    ]:
        assert needle not in prompt, needle
    manifest = set(report["input_manifest"]["blake"])
    assert PRD_REF in manifest and DIFF_REF not in manifest
    assert manifest <= set(
        CASES["full-clean"]["expected_context"]["allowed_inputs"]["per_job"]["blake"]
    )


def test_blake_isolation_holds_for_a_second_roster_and_cycle(stage, root):
    context = context_for(PRD, "fast-track-clean")
    report = call(stage, root, cycle_id="ft2", expected_context=context)
    art = root / "docs" / "dev" / "tmp" / "rev"
    prompt = text(report["prompts"]["blake"])
    assert PRD in prompt
    for needle in blake_forbidden(art, "ft2"):
        assert needle not in prompt, needle
    assert set(report["input_manifest"]["blake"]) <= set(
        context["allowed_inputs"]["per_job"]["blake"]
    )
    assert DIFF_REF not in report["input_manifest"]["blake"]


def test_nonblind_manifests_stay_within_allowed_refs_and_keep_the_diff(stage, root):
    report = call(stage, root)
    allowed = CASES["full-clean"]["expected_context"]["allowed_inputs"]["per_job"]
    assert set(report["input_manifest"]) == {"alice", "blake", "bob"}
    for job, refs in report["input_manifest"].items():
        assert isinstance(refs, list)
        assert set(refs) <= set(allowed[job]), job
        assert PRD_REF in refs
    for job in ("alice", "bob"):
        assert DIFF_REF in report["input_manifest"][job]


def test_bob_prompt_points_at_staged_context_and_diff_and_carries_the_doubt_appendix(
    stage, root
):
    report = call(stage, root, cycle_id="b7")
    art = (root / "docs" / "dev" / "tmp" / "rev").resolve()
    prompt = text(report["prompts"]["bob"])
    assert "review-context-b7.md" in prompt and "review-diff-b7.diff" in prompt
    assert "review-context-c1.md" not in prompt
    contexts = [
        Path(r["path"])
        for r in report["artifacts"]
        if Path(r["path"]).name == "review-context-b7.md"
    ]
    assert [p.resolve() for p in contexts] == [art / "review-context-b7.md"]
    for rule in ("D1", "D2", "D3", "D4", "D5"):
        assert rule in prompt, rule
    for bucket in ("FIX", "VERIFY", "KNOWN"):
        assert bucket in prompt, bucket
    blake = text(report["prompts"]["blake"])
    assert "D1:" not in blake and "D5:" not in blake


def test_template_tokens_are_substituted_once_and_injected_tokens_stay_literal(
    stage, root
):
    report = call(stage, root)
    blake = text(report["prompts"]["blake"])
    assert PRD in blake
    outside = blake.replace(PRD, "")
    for token in BLAKE_TOKENS:
        assert token not in outside, token
    bob = text(report["prompts"]["bob"])
    for token in BOB_TOKENS:
        assert token not in bob.replace(PRD, ""), token


# --- output path safety ----------------------------------------------------------------------------


def unsafe_live_state(root: Path, tmp_path: Path) -> Path:
    return root / "docs" / "dev" / "project-management" / "autopilot" / "review"


def unsafe_git_internals(root: Path, tmp_path: Path) -> Path:
    return root / ".git" / "review"


def unsafe_symlink_escape(root: Path, tmp_path: Path) -> Path:
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "docs" / "dev" / "tmp" / "link").symlink_to(
        outside, target_is_directory=True
    )
    return root / "docs" / "dev" / "tmp" / "link" / "rev"


def unsafe_symlink_output(root: Path, tmp_path: Path) -> Path:
    art = root / "docs" / "dev" / "tmp" / "rev"
    art.mkdir()
    target = root / "docs" / "dev" / "tmp" / "target.md"
    target.write_text("TARGET", encoding="utf-8")
    (art / "alice-prompt-c1.md").symlink_to(target)
    return art


def unsafe_tracked_output(root: Path, tmp_path: Path) -> Path:
    art = root / "docs" / "dev" / "tmp" / "rev"
    art.mkdir()
    (art / "review-context-c1.md").write_text("TRACKED", encoding="utf-8")
    git("-C", str(root), "add", "docs/dev/tmp/rev/review-context-c1.md")
    git(
        "-C",
        str(root),
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "track",
    )
    return art


def unsafe_nested_repo(root: Path, tmp_path: Path) -> Path:
    sub = root / "vendor" / "sub"
    sub.mkdir(parents=True)
    git("init", "-q", str(sub))
    return sub / "rev"


def unsafe_executable_existing(root: Path, tmp_path: Path) -> Path:
    art = root / "docs" / "dev" / "tmp" / "rev"
    art.mkdir()
    (art / "review-prd-c1.md").write_text("OLD", encoding="utf-8")
    (art / "review-prd-c1.md").chmod(0o755)
    return art


def unsafe_hardlinked_existing(root: Path, tmp_path: Path) -> Path:
    art = root / "docs" / "dev" / "tmp" / "rev"
    art.mkdir()
    other = root / "docs" / "dev" / "tmp" / "other.txt"
    other.write_text("SHARED", encoding="utf-8")
    os.link(other, art / "review-prd-c1.md")
    return art


@pytest.mark.parametrize(
    "make",
    [
        unsafe_live_state,
        unsafe_git_internals,
        unsafe_symlink_escape,
        unsafe_symlink_output,
        unsafe_tracked_output,
        unsafe_nested_repo,
        unsafe_executable_existing,
        unsafe_hardlinked_existing,
    ],
    ids=lambda f: f.__name__,
)
def test_unsafe_output_destination_is_refused_before_any_write(
    stage, root, tmp_path, make
):
    art = make(root, tmp_path)
    before = snapshot(tmp_path)
    assert_refused(call(stage, root, artifact_root=art))
    assert snapshot(tmp_path) == before
    assert not (root / ".git" / "review").exists()
    assert not (root / "vendor" / "sub" / "rev").exists()


def test_existing_regular_untracked_output_file_is_replaced(stage, root):
    art = root / "docs" / "dev" / "tmp" / "rev"
    art.mkdir()
    stale = art / "review-prd-raw-c1.md"
    stale.write_text("STALE", encoding="utf-8")
    stale.chmod(0o644)
    report = call(stage, root, artifact_root=art)
    assert report["ok"] is True
    assert stale.read_bytes() == PRD.encode("utf-8")


# --- no workflow state ------------------------------------------------------------------------------


def test_staging_touches_no_state_queue_or_markers_and_leaves_inputs_unmutated(
    stage, root, tmp_path
):
    art = root / "docs" / "dev" / "tmp" / "rev"
    context = context_for(PRD)
    texts = texts_for(context, PRD)
    tasks: list[dict] = []
    frozen = copy.deepcopy((context, texts, tasks))
    before = snapshot(tmp_path)
    report = call(stage, root, expected_context=context, input_texts=texts, tasks=tasks)
    assert report["ok"] is True
    assert snapshot(tmp_path, skip=art) == before
    assert (context, texts, tasks) == frozen
    assert {Path(p).resolve().parent for p in report["prompts"].values()} == {
        art.resolve()
    }
