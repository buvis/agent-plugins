"""A refreshed source-map row agrees with itself, and the revision check never fails open.

Two rules live here. A row the successor receipt certifies may not keep
acceptance statuses or prose that contradict its refreshed evidence, and
`verify_listed_paths_match_revision` may skip its work only for a directory
that is genuinely outside a git work tree. Fixtures come from
test_helper_provenance.py and test_helper_provenance_successor.py.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from types import ModuleType

import pytest
from controller_test_support import commit_all
from test_helper_provenance import by_key, canon, digest, encode, load_tool
from test_helper_provenance_successor import (
    CONTRACT,
    CONTROLLER,
    NEAR_MISSES,
    PLANNED,
    REVISIONS,
    SHARED,
    build_repo,
    generate,
    valid_successor,
    write_json,
)

# The authored sentence that says why a controller row has no pinned source.
LEAD = (
    "Newly authored AP00018 controller file; no pinned source asset or source sections."
)
# Prose that claims the delivery evidence has not landed yet.
ON_HOLD = (
    "AP00018 is on hold: the digest records current packaged bytes, and each "
    "later AP00018 task that changes the file refreshes it."
)
STILL_PLANNED = "AP00018 delivery evidence is still planned."
PENDING = "AP00018 delivery evidence is pending a real host run."
# Prose that claims nothing about the delivery evidence, so the refresh has no
# reason to touch it.
NO_CLAIM = "Packaged bytes exist."
CLAIMS = re.compile(r"(?i)\b(planned|pending|on[\s-]hold)\b")
FRESH_ROW = "plugins/autopilot/controller/autopilot_state/owner.py"
UNRESOLVABLE = ("d" * 40, "9f" * 20)
# A listed path that sorts after every controller and shared path, so checking
# the alphabetically last listed path alone cannot notice a stale sibling.
LATE = "plugins/autopilot/zz.py"
# No refusal may tell its reader that the successor was accepted anyway.
ACCEPTANCE = re.compile(
    r"(?i)(\bproceeding\b|publishing anyway|treated as fine|nothing to worry"
    r"|no problem|\bis fine\b|\blooks fine\b)"
)
# An unresolvable revision must be named as one, not reported as stale bytes.
UNRESOLVED = re.compile(
    r"(?i)(unresolv|cannot resolve|cannot be resolved|could not resolve"
    r"|could not be resolved|does not resolve|not a valid|invalid object"
    r"|unknown revision|bad revision|no such revision)"
)


@pytest.fixture(scope="module")
def tool() -> ModuleType:
    return load_tool()


@pytest.fixture
def plain_git_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep git's messages free of user and system configuration."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in strings(item)]
    return []


def case(path: str, status: str, outcome: str) -> dict:
    return {"case_id": f"asset-{path}", "expected_outcome": outcome, "status": status}


def contradictions() -> dict[str, dict]:
    """Rows authored while the delivery was still planned, pending or on hold."""
    return {
        CONTROLLER[0]: {
            "adaptation_reason": f"{LEAD} {ON_HOLD}",
            "acceptance_cases": [
                case(CONTROLLER[0], "planned", STILL_PLANNED),
                case(CONTROLLER[0] + "#2", "planned", NO_CLAIM),
            ],
        },
        CONTROLLER[1]: {"adaptation_reason": PENDING, "acceptance_cases": []},
        SHARED[0]: {
            "adaptation_reason": f"{LEAD} {ON_HOLD}",
            "acceptance_cases": [case(SHARED[0], "pending", STILL_PLANNED)],
        },
        NEAR_MISSES[0]: {
            "adaptation_reason": ON_HOLD,
            "acceptance_cases": [case(NEAR_MISSES[0], "planned", STILL_PLANNED)],
        },
        NEAR_MISSES[1]: {
            "adaptation_reason": PENDING,
            "acceptance_cases": [case(NEAR_MISSES[1], "planned", STILL_PLANNED)],
        },
    }


def stage(mapping: Path, edits: dict[str, dict]) -> dict:
    document = json.loads(mapping.read_bytes())
    for row in document["assets"]:
        edit = edits.get(row["destination_path"])
        if edit is not None:
            row.update(edit)
    mapping.write_bytes(encode(document))
    return json.loads(mapping.read_bytes())


def run_plain_git(*args: object) -> subprocess.CompletedProcess:
    """Run git in the C locale, as the module under test does."""
    return subprocess.run(
        ["git", *map(str, args)],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "LC_ALL": "C"},
    )


def git_stderr(*args: object) -> str:
    """The first line git itself prints when the given invocation fails."""
    done = run_plain_git(*args)
    assert done.returncode != 0, done.stdout
    lines = done.stderr.strip().splitlines()
    assert lines and lines[0].strip(), done.stderr
    return lines[0]


def assert_refusal(message: str, revision: str, *named: str) -> None:
    """Every refusal binds itself to the successor's revision and still refuses.

    The marker is the literal `package_revision` or the revision itself, so a
    message that only forwards git's stderr does not qualify, and no refusal
    may carry a phrase that says the successor was published anyway.
    """
    assert message.strip(), repr(message)
    assert "package_revision" in message or revision in message, message
    assert not ACCEPTANCE.search(message), message
    for text in named:
        assert text in message, (text, message)


@pytest.mark.parametrize("revision", REVISIONS)
def test_refreshed_listed_row_acceptance_cases_match_its_evidence(
    tool: ModuleType, tmp_path: Path, revision: str
) -> None:
    root = tmp_path / revision[:3]
    mapping = build_repo(root, revision[:3])
    stage(mapping, contradictions())
    document = generate(tool, root, mapping, valid_successor(root, revision))
    rows = by_key(document["assets"], "destination_path")
    for path in (CONTROLLER[0], CONTROLLER[1], SHARED[0]):
        row = rows[path]
        assert row["evidence"]["status"] == "passed", path
        assert row["evidence"]["tested_package_revision"] == revision, path
        for item in row["acceptance_cases"]:
            assert item["status"] == row["evidence"]["status"], (path, item)


def test_refreshed_listed_rows_drop_planned_pending_and_on_hold_prose(
    tool: ModuleType, tmp_path: Path
) -> None:
    mapping = build_repo(tmp_path, "prose")
    staged = stage(mapping, contradictions())
    document = generate(tool, tmp_path, mapping, valid_successor(tmp_path))
    old, new = (by_key(d["assets"], "destination_path") for d in (staged, document))
    for path in (CONTROLLER[0], CONTROLLER[1], SHARED[0], CONTRACT):
        row = new[path]
        for text in strings(row):
            assert not CLAIMS.search(text), (path, text)
        assert row["adaptation_reason"].strip(), path
        for item in row["acceptance_cases"]:
            assert item["expected_outcome"].strip(), (path, item)
    for path in (CONTROLLER[0], CONTROLLER[1], SHARED[0]):
        # The refresh rewrites the claim; it does not drop fields from the row.
        assert set(new[path]) == set(old[path]), path
        assert ON_HOLD not in strings(new[path]), path
        assert PENDING not in strings(new[path]), path
        # The replacement reason describes this row, not the refresh in general.
        reason = new[path]["adaptation_reason"]
        assert path in reason, (path, reason)
        assert "AP00018" in reason, (path, reason)
    # Prose that claims nothing has nothing to contradict, so it survives.
    cases = by_key(new[CONTROLLER[0]]["acceptance_cases"], "case_id")
    assert cases[f"asset-{CONTROLLER[0]}#2"]["expected_outcome"] == NO_CLAIM


def test_a_refresh_keeps_the_authored_leading_sentence_of_the_reason(
    tool: ModuleType, tmp_path: Path
) -> None:
    mapping = build_repo(tmp_path, "lead")
    stage(mapping, contradictions())
    successor = valid_successor(tmp_path)
    document = generate(tool, tmp_path, mapping, successor)
    rows = by_key(document["assets"], "destination_path")
    for path in (CONTROLLER[0], SHARED[0]):
        reason = rows[path]["adaptation_reason"]
        # The why-no-pinned-source sentence survives; the landed sentence follows.
        assert reason.startswith(LEAD + " "), (path, reason)
        landed = reason.removeprefix(LEAD + " ")
        assert path in landed and "AP00018" in landed, (path, reason)
        assert not CLAIMS.search(reason), (path, reason)
    # A reason whose leading sentence is the claim itself keeps none of it.
    reason = rows[CONTROLLER[1]]["adaptation_reason"]
    assert PENDING not in reason and CONTROLLER[1] in reason, reason
    # A second refresh of the refreshed map changes no reason.
    mapping.write_bytes(encode(document))
    regenerated = generate(tool, tmp_path, mapping, successor)
    again = by_key(regenerated["assets"], "destination_path")
    for path in (CONTROLLER[0], CONTROLLER[1], SHARED[0]):
        assert again[path]["adaptation_reason"] == rows[path]["adaptation_reason"]


def test_a_refresh_keeps_every_field_it_has_no_claim_to_rewrite(
    tool: ModuleType, tmp_path: Path
) -> None:
    rewritten = {
        "destination_blob_sha256",
        "evidence",
        "adaptation_reason",
        "acceptance_cases",
    }
    mapping = build_repo(tmp_path, "fields")
    staged = stage(mapping, contradictions())
    document = generate(tool, tmp_path, mapping, valid_successor(tmp_path))
    old, new = (by_key(d["assets"], "destination_path") for d in (staged, document))
    assert old[SHARED[0]]["section_plan"], "the fixture needs a value-bearing field"
    for path in (CONTROLLER[0], CONTROLLER[1], SHARED[0]):
        assert set(new[path]) == set(old[path]), path
        for field in set(old[path]) - rewritten:
            assert canon(new[path][field]) == canon(old[path][field]), (path, field)
        kept = {item["case_id"] for item in old[path]["acceptance_cases"]}
        assert kept <= {item["case_id"] for item in new[path]["acceptance_cases"]}, path


def test_rows_outside_the_successor_paths_keep_their_prose_and_status(
    tool: ModuleType, tmp_path: Path
) -> None:
    mapping = build_repo(tmp_path, "unlisted")
    staged = stage(mapping, contradictions())
    successor = {**valid_successor(tmp_path), "paths": [CONTROLLER[0], CONTRACT]}
    document = generate(tool, tmp_path, mapping, successor)
    old, new = (by_key(d["assets"], "destination_path") for d in (staged, document))
    for path in (CONTROLLER[1], *NEAR_MISSES):
        assert canon(new[path]) == canon(old[path]), path
        assert new[path]["evidence"] == PLANNED, path
    assert new[NEAR_MISSES[0]]["adaptation_reason"] == ON_HOLD
    assert new[NEAR_MISSES[0]]["acceptance_cases"][0]["status"] == "planned"
    assert new[NEAR_MISSES[1]]["adaptation_reason"] == PENDING
    assert new[CONTROLLER[1]]["adaptation_reason"] == PENDING
    # A listed row of the same shape is refreshed and agrees with itself.
    refreshed = new[CONTROLLER[0]]
    assert canon(refreshed) != canon(old[CONTROLLER[0]])
    assert refreshed["evidence"]["status"] == "passed"
    assert [item["status"] for item in refreshed["acceptance_cases"]] == ["passed"] * 2


def test_freshly_registered_listed_rows_agree_with_their_evidence(
    tool: ModuleType, tmp_path: Path
) -> None:
    mapping = build_repo(tmp_path, "fresh")
    stage(mapping, contradictions())
    write_json(tmp_path / FRESH_ROW, {"tag": FRESH_ROW})
    successor = valid_successor(tmp_path)
    successor["paths"].append(FRESH_ROW)
    document = generate(tool, tmp_path, mapping, successor)
    rows = by_key(document["assets"], "destination_path")
    for path in (CONTRACT, FRESH_ROW):
        row = rows[path]
        assert row["destination_blob_sha256"] == digest((tmp_path / path).read_bytes())
        assert row["evidence"]["status"] == "passed", path
        cases = row["acceptance_cases"]
        assert cases, path
        for item in cases:
            assert item["status"] == row["evidence"]["status"], (path, item)
        for text in strings(row):
            assert not CLAIMS.search(text), (path, text)


def test_a_refresh_inside_a_work_tree_is_refused_while_a_listed_file_is_stale(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mapping = build_repo(tmp_path, "callsite")
    stage(mapping, contradictions())
    revision = commit_all(tmp_path, monkeypatch)
    target = tmp_path / CONTROLLER[0]
    body = target.read_text()
    target.write_text(body + "# appended after the revision\n")
    with pytest.raises(ValueError, match="stale") as refused:
        generate(tool, tmp_path, mapping, valid_successor(tmp_path, revision))
    assert_refusal(str(refused.value), revision, CONTROLLER[0])
    # Restoring the listed bytes lets the same receipt refresh the row.
    target.write_text(body)
    document = generate(tool, tmp_path, mapping, valid_successor(tmp_path, revision))
    row = by_key(document["assets"], "destination_path")[CONTROLLER[0]]
    assert row["evidence"]["tested_package_revision"] == revision
    for item in row["acceptance_cases"]:
        assert item["status"] == row["evidence"]["status"], item
    for text in strings(row):
        assert not CLAIMS.search(text), text


def test_listed_paths_are_accepted_at_their_revision_and_refused_when_stale(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_repo(tmp_path, "stale")
    first = commit_all(tmp_path, monkeypatch)
    (tmp_path / CONTROLLER[0]).write_text("# edited after the first revision\n")
    second = commit_all(tmp_path, monkeypatch)
    assert first != second
    listed = {SHARED[0], CONTROLLER[0]}
    assert tool.verify_listed_paths_match_revision(tmp_path, second, listed) is None
    with pytest.raises(ValueError, match="stale") as refused:
        tool.verify_listed_paths_match_revision(tmp_path, first, listed)
    assert_refusal(str(refused.value), first, CONTROLLER[0])
    # Nothing is listed, so nothing is stale.
    assert tool.verify_listed_paths_match_revision(tmp_path, first, set()) is None


def test_a_stale_listed_path_is_refused_wherever_it_sorts(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_repo(tmp_path, "sorts")
    (tmp_path / LATE).write_text("# a listed path that sorts after the rest\n")
    revision = commit_all(tmp_path, monkeypatch)
    (tmp_path / CONTROLLER[0]).write_text("# edited after the revision\n")
    pair = {CONTROLLER[0], LATE}
    assert sorted(pair) == [CONTROLLER[0], LATE]
    with pytest.raises(ValueError, match="stale") as first:
        tool.verify_listed_paths_match_revision(tmp_path, revision, pair)
    assert_refusal(str(first.value), revision, CONTROLLER[0])
    # The real receipt lists fourteen paths, with the stale one among them.
    many = {CONTROLLER[0], LATE, *SHARED, CONTRACT, *NEAR_MISSES}
    assert len(many) > 2
    assert min(many) != CONTROLLER[0] and max(many) != CONTROLLER[0]
    with pytest.raises(ValueError, match="stale") as among:
        tool.verify_listed_paths_match_revision(tmp_path, revision, many)
    assert_refusal(str(among.value), revision, CONTROLLER[0])


# Edits a byte-count or first-bytes comparison would miss. Each keeps the
# file's first eight bytes; the flag says whether it keeps the byte count.
EDITS = {
    "appended-tail": (lambda body: body + "# appended after the revision\n", False),
    "same-length-tail": (lambda body: body[:-2] + "X\n", True),
}


@pytest.mark.parametrize("edit,same_length", EDITS.values(), ids=EDITS.keys())
def test_a_listed_path_is_refused_however_small_its_change_is(
    tool: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    edit,
    same_length: bool,
) -> None:
    build_repo(tmp_path, "bytes")
    revision = commit_all(tmp_path, monkeypatch)
    target = tmp_path / CONTROLLER[0]
    body = target.read_text()
    edited = edit(body)
    assert edited != body and edited[:8] == body[:8]
    assert ((len(edited) == len(body)) is same_length) and len(body) > 8
    target.write_text(edited)
    with pytest.raises(ValueError, match="stale") as refused:
        tool.verify_listed_paths_match_revision(
            tmp_path, revision, {SHARED[0], CONTROLLER[0]}
        )
    assert_refusal(str(refused.value), revision, CONTROLLER[0])


def test_an_edited_path_the_receipt_does_not_list_is_not_checked(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_repo(tmp_path, "near")
    (tmp_path / LATE).write_text("# a listed path that sorts after the rest\n")
    revision = commit_all(tmp_path, monkeypatch)
    (tmp_path / NEAR_MISSES[1]).write_text("# edited, and not listed\n")
    listed = {CONTROLLER[0], LATE}
    assert tool.verify_listed_paths_match_revision(tmp_path, revision, listed) is None
    with pytest.raises(ValueError, match="stale") as refused:
        tool.verify_listed_paths_match_revision(
            tmp_path, revision, listed | {NEAR_MISSES[1]}
        )
    assert_refusal(str(refused.value), revision, NEAR_MISSES[1])


def test_a_directory_outside_a_git_work_tree_skips_verification(
    tool: ModuleType, tmp_path: Path, plain_git_config: None
) -> None:
    build_repo(tmp_path, "nogit")
    absent = "plugins/autopilot/controller/absent.py"
    # The probe fails; the module decides "outside a work tree" from the file
    # system, not from the wording of git's message.
    git_stderr("-C", tmp_path, "rev-parse", "--is-inside-work-tree")
    listed = {SHARED[0], CONTROLLER[0], absent}
    assert (
        tool.verify_listed_paths_match_revision(tmp_path, REVISIONS[0], listed) is None
    )
    assert (
        tool.verify_listed_paths_match_revision(tmp_path, REVISIONS[1], set()) is None
    )


def test_a_localized_git_still_skips_outside_a_work_tree_and_refuses_in_english(
    tool: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plain_git_config: None,
) -> None:
    for name in ("LANGUAGE", "LANG", "LC_ALL", "LC_MESSAGES"):
        monkeypatch.setenv(name, "de" if name == "LANGUAGE" else "de_DE.UTF-8")
    outside = tmp_path / "outside"
    build_repo(outside, "localized")
    assert (
        tool.verify_listed_paths_match_revision(outside, REVISIONS[0], {SHARED[0]})
        is None
    )
    with pytest.raises(ValueError) as refused:
        tool.verify_listed_paths_match_revision(
            tmp_path / "gone", REVISIONS[0], {SHARED[0]}
        )
    assert "fatal:" in str(refused.value), str(refused.value)
    assert_refusal(str(refused.value), REVISIONS[0])


def missing_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    return tmp_path / "gone"


def file_instead_of_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "root.txt"
    path.write_text("not a directory\n")
    return path


def invalid_gitfile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "badgitfile"
    root.mkdir()
    (root / ".git").write_text("gitdir: \n")
    return root


def nonexistent_git_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "plain"
    root.mkdir()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nonexistent-git-dir"))
    return root


def git_dir_without_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "headless"
    root.mkdir()
    run_plain_git("-C", root, "init", "--quiet")
    (root / ".git" / "HEAD").unlink()
    return root


def bare_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository with no work tree: the probe answers `false` at exit 0."""
    root = tmp_path / "bare.git"
    run_plain_git("init", "--quiet", "--bare", root)
    return root


PROBE_FAILURES = {
    "missing-directory": missing_directory,
    "file-instead-of-directory": file_instead_of_directory,
    "invalid-gitfile": invalid_gitfile,
    "nonexistent-git-dir": nonexistent_git_dir,
    "git-dir-without-head": git_dir_without_head,
    "probe-answers-false": bare_repository,
}


@pytest.mark.parametrize("build", PROBE_FAILURES.values(), ids=PROBE_FAILURES.keys())
def test_a_probe_failure_that_is_not_an_absent_work_tree_is_refused(
    tool: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plain_git_config: None,
    build,
) -> None:
    root = build(tmp_path, monkeypatch)
    probe = run_plain_git("-C", root, "rev-parse", "--is-inside-work-tree")
    if probe.returncode == 0:
        expected = probe.stdout.strip()
        assert expected == "false", expected
    else:
        expected = git_stderr("-C", root, "rev-parse", "--is-inside-work-tree")
    with pytest.raises(ValueError) as refused:
        tool.verify_listed_paths_match_revision(root, REVISIONS[0], {SHARED[0]})
    assert expected in str(refused.value), (expected, str(refused.value))
    assert_refusal(str(refused.value), REVISIONS[0])


def test_an_absent_git_executable_is_refused_by_the_module_itself(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    build_repo(root, "nobin")
    revision = commit_all(root, monkeypatch)
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    # A raw FileNotFoundError from subprocess would escape pytest.raises here.
    with pytest.raises(ValueError) as refused:
        tool.verify_listed_paths_match_revision(root, revision, {CONTROLLER[0]})
    assert "git" in str(refused.value).lower()
    assert_refusal(str(refused.value), revision)


@pytest.mark.parametrize("unknown", UNRESOLVABLE)
def test_a_revision_git_cannot_resolve_is_refused_as_unresolvable_not_as_stale(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unknown: str
) -> None:
    root = tmp_path / unknown[:2]
    build_repo(root, "unknown")
    revision = commit_all(root, monkeypatch)
    (root / CONTROLLER[0]).write_text("# edited after the revision\n")
    listed = {CONTROLLER[0]}
    with pytest.raises(ValueError) as stale:
        tool.verify_listed_paths_match_revision(root, revision, listed)
    with pytest.raises(ValueError) as unresolved:
        tool.verify_listed_paths_match_revision(root, unknown, listed)
    assert "stale" in str(stale.value).lower()
    assert_refusal(str(stale.value), revision, CONTROLLER[0])
    assert str(unresolved.value) != str(stale.value)
    assert "stale" not in str(unresolved.value).lower()
    assert unknown in str(unresolved.value)
    assert UNRESOLVED.search(str(unresolved.value)), str(unresolved.value)
    assert_refusal(str(unresolved.value), unknown)


def test_a_listed_path_missing_at_the_revision_is_refused_with_git_stderr(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_repo(tmp_path, "absent")
    (tmp_path / LATE).write_text("# a listed path that sorts after the rest\n")
    revision = commit_all(tmp_path, monkeypatch)
    write_json(tmp_path / FRESH_ROW, {"tag": FRESH_ROW})
    expected = git_stderr("-C", tmp_path, "show", f"{revision}:{FRESH_ROW}")
    listed = {SHARED[0], FRESH_ROW, LATE}
    assert max(listed) == LATE
    with pytest.raises(ValueError) as refused:
        tool.verify_listed_paths_match_revision(tmp_path, revision, listed)
    assert expected in str(refused.value), (expected, str(refused.value))
    assert_refusal(str(refused.value), revision)
