"""Packaged pure custody proposals keep source semantics without state."""

from __future__ import annotations

import copy

import pytest
from test_cap_custody_helpers import load


@pytest.fixture
def custody():
    return load("custody")


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
            "# Title\n## Problem Statement\na\n## Problem Statement\nb\n",
            "# Title\n## Problem Statement\n\n<N>\n\na\n## Problem Statement\nb\n",
        ),
        (
            "intro\n## Problem Statements\n# Title\nrest\n",
            "intro\n## Problem Statements\n# Title\n\n<N>\n\nrest\n",
        ),
        (
            "intro\n# One\na\n# Two\nb\n",
            "intro\n# One\n\n<N>\n\na\n# Two\nb\n",
        ),
        ("intro\n#Title\n", "intro\n#Title\n\n<N>\n"),
        ("intro", "intro\n\n<N>\n"),
        ("", "\n<N>\n"),
    ],
    ids=[
        "problem-statement",
        "first-of-two-problem-statements",
        "h1-fallback",
        "first-of-two-h1s",
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
