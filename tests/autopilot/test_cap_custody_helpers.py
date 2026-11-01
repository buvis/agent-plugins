"""Packaged cap classification and pure custody proposals keep source semantics without state."""

from __future__ import annotations

import copy
import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
REAL_RUN = subprocess.run
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
KEYS = ("ref", "severity", "file", "line", "regression", "commit")
HEADER = "| Ref | Consensus | Severity | Issue | File | Found By |\n|---|---|---|---|---|---|"
BASE_FILES = {
    "src/a.py": "a1\na2\na3\na4\na5\n",
    "src/Mixed.py": "m1\nm2\nm3\n",
    "docs/guide.md": "g1\ng2\n",
    "pkg/newer/z.py": "z1\n",
    "does not exist.md": "d1\n",
}


def load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


@pytest.fixture
def cap():
    return load("cap_check")


@pytest.fixture
def custody():
    return load("custody")


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(key, raising=False)
    env = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CEILING_DIRECTORIES": f"{tmp_path}:{tmp_path.resolve()}",
        "GIT_AUTHOR_NAME": "Tess",
        "GIT_AUTHOR_EMAIL": "tess@example.invalid",
        "GIT_COMMITTER_NAME": "Tess",
        "GIT_COMMITTER_EMAIL": "tess@example.invalid",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def git_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[tuple, dict]]:
    calls: list[tuple[tuple, dict]] = []

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return REAL_RUN(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    return calls


def git(cwd: Path, *args: str) -> str:
    result = REAL_RUN(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def short(repo: Path, sha: str) -> str:
    return git(repo, "log", "--format=%h", "-1", sha)


@pytest.fixture
def history(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "master")
    base = commit(repo, BASE_FILES, "base")
    one = commit(
        repo,
        {"src/a.py": "a1\na2\na3 rework\na4\na5\n", "pkg/new/y.py": "y1\n"},
        "rework one",
    )
    two = commit(
        repo,
        {"src/Mixed.py": "m1\nm2 rework\nm3\n", "pkg/new/y.py": "y1\ny2\n"},
        "rework two",
    )
    git(repo, "checkout", "-q", "-b", "side")
    side = commit(repo, {"side.txt": "s1\n"}, "side")
    git(repo, "checkout", "-q", "master")
    return {"repo": repo, "A": base, "B1": one, "B2": two, "S": side}


def table(*rows: tuple[str, str, str]) -> str:
    body = "\n".join(
        f"| {ref} | [2/3] | {sev} | issue {ref} | {cell} | alice |"
        for ref, sev, cell in rows
    )
    return f"# Review\n\n## Consolidated Findings\n\n{HEADER}\n{body}\n\n## Lens Notes\n\nnone\n"


def classify(
    cap,
    h: dict,
    text: str,
    previous: str | None = "A",
    head: str = "B2",
    root: Path | None = None,
):
    return cap.classify_findings(
        repo_root=root or h["repo"],
        review_text=text,
        previous_head=h[previous] if previous else None,
        head=h[head],
    )


@pytest.mark.parametrize(
    ("cell", "file", "line", "regression", "commit_key"),
    [
        ("src/a.py:3", "src/a.py", 3, True, "B1"),
        ("src/a.py:1", "src/a.py", 1, False, None),
        ("src/Mixed.py:2", "src/Mixed.py", 2, True, "B2"),
        ("`src/a.py:3` (rework hunk)", "src/a.py", 3, True, "B1"),
        ("./src/./a.py:3", "src/a.py", 3, True, "B1"),
        ("src/a.py#L3", "src/a.py", 3, True, "B1"),
        ("src/a.py:1-3", "src/a.py", 1, True, "B1"),
        ("src/a.py:1,3", "src/a.py", 1, True, "B1"),
        ("src/a.py:1,2", "src/a.py", 1, False, None),
        ("src/MIXED.py:2", "src/Mixed.py", 2, True, "B2"),
        ("src/mixed.pyc:2", "src/mixed.pyc", 2, None, None),
        ("pkg/new", "pkg/new", None, True, "B1"),
        ("pkg/newer", "pkg/newer", None, False, None),
        ("src/Mixed.py", "src/Mixed.py", None, True, "B2"),
        ("docs/guide.md", "docs/guide.md", None, False, None),
        ("docs/guide.md; `src/a.py:3`", "src/a.py", 3, True, "B1"),
        ("docs/guide.md, gone.py", "gone.py", None, None, None),
        ("src/a.py:3; gone.py", "gone.py", None, None, None),
        ("gone.py:4", "gone.py", 4, None, None),
        ("src/a.py:99", "src/a.py", 99, None, None),
    ],
    ids=[
        "introduced-line",
        "untouched-line",
        "second-rework-commit",
        "backtick-annotation",
        "normpath",
        "hash-line",
        "range-every-line",
        "comma-every-line",
        "comma-untouched",
        "unique-casefold",
        "casefold-near-miss",
        "first-subtree-touch",
        "sibling-prefix-subtree",
        "first-file-touch",
        "unchanged-file",
        "multipath-regression",
        "multipath-unresolved",
        "unresolved-beats-true",
        "missing-path",
        "line-past-end",
    ],
)
def test_classifies_each_file_cell_with_null_for_unresolved_paths(
    cap,
    history: dict,
    cell: str,
    file: str,
    line: int | None,
    regression: bool | None,
    commit_key: str | None,
) -> None:
    rows = classify(cap, history, table(("R1", "🟠", cell)))
    assert len(rows) == 1
    row = rows[0]
    expected_commit = (
        short(history["repo"], history[commit_key]) if commit_key else None
    )
    assert {key: row[key] for key in KEYS} == {
        "ref": "R1",
        "severity": "high",
        "file": file,
        "line": line,
        "regression": regression,
        "commit": expected_commit,
    }
    assert row["regression"] is regression
    assert set(row) <= {*KEYS, "reason"}
    if regression is None:
        assert isinstance(row["reason"], str) and row["reason"]


def test_classifies_only_high_and_critical_rows_from_bullets_and_tables_in_order(
    cap, history: dict
) -> None:
    text = table(
        ("R1", "🟡", "src/a.py:3"),
        ("R2", "🟠", "src/a.py:3"),
        ("R3", "⚪", "src/Mixed.py:2"),
        ("R4", "🔴 Critical", "src/a.py:1"),
    ).replace(
        "## Consolidated Findings\n\n",
        "## Consolidated Findings\n\n- [2/3] 🔴 bullet finding | src/Mixed.py:2 | Found by: bob\n\n",
    )
    rows = classify(cap, history, text)
    assert [
        (r["ref"], r["severity"], r["file"], r["line"], r["regression"]) for r in rows
    ] == [
        ("", "critical", "src/Mixed.py", 2, True),
        ("R2", "high", "src/a.py", 3, True),
        ("R4", "critical", "src/a.py", 1, False),
    ]
    assert rows[0]["commit"] == short(history["repo"], history["B2"])
    assert rows[1]["commit"] == short(history["repo"], history["B1"])


def test_normalizes_to_git_toplevel_independent_of_cwd_without_touching_the_tree(
    cap,
    history: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = history["repo"]
    state = repo / "docs" / "dev" / "project-management" / "autopilot" / "state.json"
    state.parent.mkdir(parents=True)
    state.write_text('{"phase": "review"}', encoding="utf-8")
    other = tmp_path / "other"
    other.mkdir()
    git(other, "init", "-q", "-b", "master")
    commit(other, {"src/a.py": "unrelated\n"}, "other")
    monkeypatch.chdir(other)
    before = (
        git(repo, "status", "--porcelain", "--ignored"),
        git(repo, "rev-parse", "HEAD"),
    )
    text = table(("R1", "🟠", f"{repo}/src/a.py:3"), ("R2", "🟠", "src/a.py:1"))
    from_top = classify(cap, history, text)
    from_subdir = classify(cap, history, text, root=repo / "src")
    assert from_top == from_subdir
    assert [(r["file"], r["regression"]) for r in from_top] == [
        ("src/a.py", True),
        ("src/a.py", False),
    ]
    assert (
        git(repo, "status", "--porcelain", "--ignored"),
        git(repo, "rev-parse", "HEAD"),
    ) == before
    assert state.read_text(encoding="utf-8") == '{"phase": "review"}'
    assert sorted(p.name for p in state.parent.iterdir()) == ["state.json"]


@pytest.mark.parametrize("previous", [None, ""], ids=["none", "empty"])
def test_missing_previous_head_returns_empty_without_git_or_parsing(
    cap,
    tmp_path: Path,
    git_calls: list,
    previous: str | None,
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    for text in ("no findings section at all", table(("R1", "🔴", "src/a.py:3"))):
        assert (
            cap.classify_findings(
                repo_root=plain, review_text=text, previous_head=previous, head="b" * 40
            )
            == []
        )
    assert git_calls == []


@pytest.mark.parametrize(
    "text",
    [
        table(("R1", "🟡", "src/a.py:3"), ("R2", "⚪ low", "src/a.py:1")),
        "# Review\n\n## Consolidated Findings\n\nNo findings.\n",
    ],
    ids=["medium-low-only", "empty-section"],
)
def test_rows_without_high_or_critical_make_no_git_calls(
    cap, tmp_path: Path, git_calls: list, text: str
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    rows = cap.classify_findings(
        repo_root=plain, review_text=text, previous_head="a" * 40, head="b" * 40
    )
    assert rows == []
    assert git_calls == []


def test_high_row_outside_a_git_repository_raises(cap, tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(cap.CapCheckError):
        cap.classify_findings(
            repo_root=plain,
            review_text=table(("R1", "🟠", "src/a.py:3")),
            previous_head="a" * 40,
            head="b" * 40,
        )


@pytest.mark.parametrize(
    "text",
    [
        "# Review\n\nno findings heading\n",
        f"# Review\n\n## Consolidated Findings\n\n{HEADER}\n| R1 | [2/3] | 🟠 | truncated\n",
        f"# Review\n\n## Consolidated Findings\n\n{HEADER}\n| R1 | [2/3] | 🟠 | a | x.py | b |\n| R1 | [2/3] | 🟠 | c | y.py | b |\n",
    ],
    ids=["no-section", "unterminated-row", "duplicate-ref"],
)
def test_unreadable_review_text_raises(cap, history: dict, text: str) -> None:
    with pytest.raises(cap.CapCheckError):
        classify(cap, history, text)


@pytest.mark.parametrize(
    "case", ["short", "equal", "reversed", "unreachable", "unknown", "tree"]
)
def test_rework_range_must_be_proven(cap, history: dict, case: str) -> None:
    repo, base, head = history["repo"], history["A"], history["B2"]
    previous, current = {
        "short": (base[:12], head),
        "equal": (head, head),
        "reversed": (head, base),
        "unreachable": (base, history["S"]),
        "unknown": (base, "0" * 40),
        "tree": (base, git(repo, "rev-parse", f"{head}^{{tree}}")),
    }[case]
    with pytest.raises(cap.CapCheckError):
        cap.classify_findings(
            repo_root=repo,
            review_text=table(("R1", "🟠", "src/a.py:3")),
            previous_head=previous,
            head=current,
        )


def test_side_branch_head_is_accepted_once_reachable_from_head(
    cap, history: dict
) -> None:
    git(history["repo"], "checkout", "-q", "side")
    rows = classify(cap, history, table(("R1", "🟠", "side.txt")), head="S")
    assert [(r["file"], r["regression"], r["commit"]) for r in rows] == [
        ("side.txt", True, short(history["repo"], history["S"])),
    ]


def test_corrupt_object_raises_instead_of_reporting_missing_or_clean(
    cap, history: dict
) -> None:
    repo = history["repo"]
    text = table(("R1", "🟠", "does not exist.md:1"))
    assert [r["regression"] for r in classify(cap, history, text)] == [False]
    blob = git(repo, "rev-parse", f"{history['B2']}:does not exist.md")
    (repo / ".git" / "objects" / blob[:2] / blob[2:]).unlink()
    with pytest.raises(cap.CapCheckError):
        classify(cap, history, text)


def test_classify_bounds_every_git_command_to_thirty_seconds(
    cap, history: dict, git_calls: list
) -> None:
    classify(cap, history, table(("R1", "🟠", "src/a.py:3"), ("R2", "🔴", "pkg/new")))
    assert git_calls
    assert all(kwargs.get("timeout") == 30 for _args, kwargs in git_calls)


def capture_errors(cap) -> tuple[type[Exception], ...]:
    """capture_range's refusal types: the module's CapCheckError, plus the
    pinned source's CustodyError when the module keeps that name."""
    names = ("CapCheckError", "CustodyError")
    return tuple(getattr(cap, name) for name in names if hasattr(cap, name))


@pytest.mark.parametrize(("base_key", "count"), [("A", 2), ("B1", 1)])
def test_capture_range_reports_range_count_and_branch(
    cap,
    history: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    base_key: str,
    count: int,
) -> None:
    monkeypatch.chdir(tmp_path)
    base = history[base_key]
    assert cap.capture_range(str(history["repo"]), None, base) == (
        f"{base}..{history['B2']}",
        count,
        "master",
    )


def test_capture_range_supports_empty_tree_and_detached_head(
    cap, history: dict
) -> None:
    repo = str(history["repo"])
    assert cap.capture_range(repo, None, EMPTY_TREE) == (
        f"{EMPTY_TREE}..{history['B2']}",
        3,
        "master",
    )
    git(history["repo"], "checkout", "-q", "--detach", history["B1"])
    assert cap.capture_range(repo, None, history["A"]) == (
        f"{history['A']}..{history['B1']}",
        1,
        "HEAD",
    )


def test_capture_range_uses_explicit_bare_git_dir(cap, tmp_path: Path) -> None:
    store, work = tmp_path / "store.git", tmp_path / "work"
    work.mkdir()
    git(tmp_path, "init", "-q", "--bare", "-b", "trunk", str(store))
    prefix = ("--git-dir", str(store), "--work-tree", str(work))
    shas = []
    for name in ("one", "two", "three"):
        (work / f"{name}.txt").write_text(name, encoding="utf-8")
        git(work, *prefix, "add", "-A")
        git(work, *prefix, "commit", "-q", "-m", name)
        shas.append(git(work, *prefix, "rev-parse", "HEAD"))
    assert cap.capture_range(str(work), str(store), shas[0]) == (
        f"{shas[0]}..{shas[2]}",
        2,
        "trunk",
    )
    with pytest.raises(capture_errors(cap)):
        cap.capture_range(str(work), None, shas[0])


@pytest.mark.parametrize("case", ["uppercase", "short", "unknown", "missing-root"])
def test_capture_range_refuses_bad_base_or_root(
    cap, history: dict, tmp_path: Path, case: str
) -> None:
    root, base = str(history["repo"]), history["A"]
    root, base = {
        "uppercase": (root, base.upper()),
        "short": (root, base[:39]),
        "unknown": (root, "0" * 40),
        "missing-root": (str(tmp_path / "absent"), base),
    }[case]
    with pytest.raises(capture_errors(cap)):
        cap.capture_range(root, None, base)


def test_capture_range_bounds_every_git_command_to_thirty_seconds(
    cap, history: dict, git_calls: list
) -> None:
    cap.capture_range(str(history["repo"]), None, history["A"])
    assert git_calls
    assert all(kwargs.get("timeout") == 30 for _args, kwargs in git_calls)


ENTRY = {
    "prd": "00042-alpha.md",
    "batch": "7",
    "op_id": "op-7a",
    "detail": "critical  finding\n\tin auth",
    "commit_range": f"{'a' * 40}..{'b' * 40}",
    "commits": 3,
    "branch": "master",
    "repo_root": "/repo/alpha",
    "git_dir": None,
}
OTHER = {
    "prd": "00043-beta.md",
    "batch": "70",
    "op_id": "op-70",
    "detail": "second",
    "commit_range": f"{'c' * 40}..{'d' * 40}",
    "commits": 1,
    "branch": "trunk",
    "repo_root": "/repo/beta",
    "git_dir": "/repo/beta.git",
}


def prefix(batch: str) -> str:
    return f"> **Custody (cap_critical, batch {batch}):**"


def keys(entry: dict) -> list[str]:
    return [
        f"critical_on_master: {entry['commit_range']}",
        f"ledger: deferred/{entry['batch']}-deferred.json#{entry['op_id']}",
    ]


def split_notice(text: str, entry: dict, detail: str) -> str:
    """Text with the batch notice line replaced by <N>, after checking that line."""
    lines = text.split("\n")
    hits = [
        i for i, line in enumerate(lines) if line.startswith(prefix(entry["batch"]))
    ]
    assert len(hits) == 1
    line = lines[hits[0]]
    head = (
        f"{prefix(entry['batch'])} {detail} Commits {entry['commit_range']} "
        f"({entry['commits']}) are live on {entry['branch']}."
    )
    assert line.startswith(head)
    assert "controller" in line.lower()
    return "\n".join([*lines[: hits[0]], "<N>", *lines[hits[0] + 1 :]])


def test_refresh_upserts_keys_inside_closed_frontmatter(custody) -> None:
    text = "---\ntitle: Alpha\ncritical_on_master: stale\nstatus: hold\n---\n# Alpha\n\n## Problem Statement\n\nBody.\n"
    result = custody.refresh_hold_prd(text, ENTRY)
    k_range, k_ledger = keys(ENTRY)
    assert split_notice(result, ENTRY, "critical finding in auth") == (
        f"---\ntitle: Alpha\n{k_range}\nstatus: hold\n{k_ledger}\n---\n"
        "# Alpha\n\n## Problem Statement\n\n<N>\n\n\nBody.\n"
    )


@pytest.mark.parametrize(
    ("filler", "closed"),
    [(18, True), (19, False)],
    ids=["closes-line-19", "closes-line-20"],
)
def test_refresh_honours_twenty_line_closed_frontmatter_rule(
    custody, filler: int, closed: bool
) -> None:
    head = ["---", *(f"k{i}: v" for i in range(filler)), "---"]
    text = "\n".join([*head, "# Beta", ""])
    result = split_notice(custody.refresh_hold_prd(text, OTHER), OTHER, "second").split(
        "\n"
    )
    if closed:
        assert result == [*head[:-1], *keys(OTHER), "---", "# Beta", "", "<N>", "", ""]
    else:
        assert result == [
            "---",
            *keys(OTHER),
            "---",
            *head,
            "# Beta",
            "",
            "<N>",
            "",
            "",
        ]


@pytest.mark.parametrize(
    ("text", "expected_body"),
    [
        (
            "# Title\nintro\n### Problem Statement\nwhy\n",
            "# Title\nintro\n### Problem Statement\n\n<N>\n\nwhy\n",
        ),
        (
            "intro\n## Problem Statements\n# Title\nrest\n",
            "intro\n## Problem Statements\n# Title\n\n<N>\n\nrest\n",
        ),
        ("intro\n#Title\n", "intro\n#Title\n\n<N>\n"),
        ("intro", "intro\n\n<N>\n"),
        ("", "\n<N>\n"),
    ],
    ids=[
        "problem-statement",
        "h1-fallback",
        "end-fallback",
        "no-trailing-newline",
        "empty",
    ],
)
def test_refresh_inserts_notice_at_heading_or_end(
    custody, text: str, expected_body: str
) -> None:
    result = custody.refresh_hold_prd(text, ENTRY)
    fresh = "\n".join(["---", *keys(ENTRY), "---"])
    assert (
        split_notice(result, ENTRY, "critical finding in auth")
        == f"{fresh}\n{expected_body}"
    )


def test_refresh_replaces_same_batch_notice_and_is_idempotent(custody) -> None:
    original = "# Alpha\n\n## Problem Statement\n\nBody.\n"
    with_other = custody.refresh_hold_prd(original, OTHER)
    once = custody.refresh_hold_prd(with_other, ENTRY)
    assert custody.refresh_hold_prd(once, ENTRY) == once
    other_line = next(
        line for line in with_other.split("\n") if line.startswith(prefix("70"))
    )
    changed = {**ENTRY, "detail": "new   detail", "commits": 4}
    again = custody.refresh_hold_prd(once, changed)
    assert split_notice(again, changed, "new detail") == split_notice(
        once, ENTRY, "critical finding in auth"
    )
    assert other_line in again.split("\n")
    assert again.split("\n").count(keys(ENTRY)[1]) == 1
    assert again.split("\n").count(keys(OTHER)[1]) == 0
    assert (
        sum(line.startswith("critical_on_master:") for line in again.split("\n")) == 1
    )


def test_refresh_requires_entry_fields(custody) -> None:
    entry = {key: value for key, value in ENTRY.items() if key != "commit_range"}
    with pytest.raises(KeyError, match="commit_range"):
        custody.refresh_hold_prd("# Alpha\n", entry)


def test_upsert_replaces_op_id_twin_without_mutating_input(custody) -> None:
    entries = [{"op_id": "op-1", "detail": "one"}, {"op_id": "op-10", "detail": "ten"}]
    before = copy.deepcopy(entries)
    replacement = {"op_id": "op-1", "detail": "replaced"}
    result, appended = custody.upsert_entry(entries, replacement)
    assert (result, appended) == (
        [replacement, {"op_id": "op-10", "detail": "ten"}],
        False,
    )
    assert entries == before and result is not entries
    assert custody.upsert_entry(result, replacement) == (result, False)


@pytest.mark.parametrize(
    ("entries", "op_id"),
    [
        ([], "op-1"),
        ([{"op_id": "op-1"}, {"op_id": "op-10"}], "op-2"),
        ([{"op_id": "op-10"}], "op-1"),
    ],
    ids=["empty", "many", "prefix-near-miss"],
)
def test_upsert_appends_new_op_id(custody, entries: list[dict], op_id: str) -> None:
    entry = {"op_id": op_id, "detail": "new"}
    result, appended = custody.upsert_entry(entries, entry)
    assert (result, appended) == ([*entries, entry], True)
    assert custody.upsert_entry(result, entry) == (result, False)


def test_upsert_requires_op_id(custody) -> None:
    with pytest.raises(KeyError, match="op_id"):
        custody.upsert_entry([{"op_id": "op-1"}], {"detail": "no id"})


def test_marker_entry_copies_scalars_and_capture_verbatim(custody) -> None:
    capture = {
        "commit_range": "a..b",
        "commits": 2,
        "branch": "master",
        "repo_root": "/r",
        "git_dir": None,
    }
    before = copy.deepcopy(capture)
    entry = custody.marker_entry("00042-alpha.md", "7", "op-7a", "detail one", capture)
    assert entry == {
        "prd": "00042-alpha.md",
        "batch": "7",
        "op_id": "op-7a",
        "detail": "detail one",
        **before,
    }
    assert capture == before and entry is not capture
    assert custody.marker_entry("00043-beta.md", "70", "op-70", "two", {}) == {
        "prd": "00043-beta.md",
        "batch": "70",
        "op_id": "op-70",
        "detail": "two",
    }
    with pytest.raises(TypeError, match="mapping"):
        custody.marker_entry("p", "b", "o", "d", None)


def test_migration_records_keep_original_index_type_and_cycle(custody) -> None:
    first = {
        "issue": "x",
        "severity": "high",
        "file": "a.py",
        "action": "deferred",
        "reason": "r1",
    }
    second = {
        "issue": "y",
        "severity": "medium",
        "file": "b.py",
        "action": "deferred",
        "type": "custom",
        "cycle": 1,
    }
    snapshot = {"cycle": 3, "deferred_decisions": ["junk", first, second]}
    before = copy.deepcopy(snapshot)
    assert custody.migration_records(snapshot, "op-9", "00042-alpha.md") == [
        {
            **first,
            "type": "deferred_decision",
            "cycle": 3,
            "prd": "00042-alpha.md",
            "op_id": "op-9-dd1",
        },
        {
            **second,
            "type": "custom",
            "cycle": 1,
            "prd": "00042-alpha.md",
            "op_id": "op-9-dd2",
        },
    ]
    assert snapshot == before
    renamed = custody.migration_records(
        {"cycle": 5, "deferred_decisions": [first]}, "op-x", "00043-beta.md"
    )
    assert renamed == [
        {
            **first,
            "type": "deferred_decision",
            "cycle": 5,
            "prd": "00043-beta.md",
            "op_id": "op-x-dd0",
        }
    ]


@pytest.mark.parametrize(
    "snapshot", [{}, {"deferred_decisions": None}, {"deferred_decisions": []}]
)
def test_migration_records_without_decisions_is_empty(custody, snapshot: dict) -> None:
    assert custody.migration_records(snapshot, "op-9", "00042-alpha.md") == []


def test_migration_records_rejects_non_mapping_snapshot(custody) -> None:
    with pytest.raises(AttributeError, match="get"):
        custody.migration_records(None, "op-9", "00042-alpha.md")


@pytest.mark.parametrize(
    "name",
    [
        "resolve",
        "record_critical",
        "load_marker",
        "write_marker",
        "marker_lock",
        "read_journal",
        "append_journal",
        "pending",
        "project_root",
        "store_git",
        "mirror_mutator",
    ],
)
def test_custody_exposes_no_state_or_resolve_operation(custody, name: str) -> None:
    assert not hasattr(custody, name)


def test_modules_load_from_package_without_source_or_test_runtime(cap, custody) -> None:
    for module in (cap, custody):
        assert Path(module.__file__).resolve().parent == SCRIPTS.resolve()
    forbidden = (ROOT / "docs").resolve()
    loaded = [
        Path(m.__file__).resolve()
        for m in list(sys.modules.values())
        if getattr(m, "__file__", None)
    ]
    assert not [path for path in loaded if path.is_relative_to(forbidden)]
