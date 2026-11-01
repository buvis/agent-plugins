"""Explicit verification artifact reuse is judged strictly against the current tree."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from test_verification import (
    GREEN,
    PM,
    SCRATCH,
    apply_dirt,
    checked_run,
    commit,
    git,
    head,
    isolated_git,
    paths,
    repo,
    script,
    verification,
    write,
)

FIXTURES = (isolated_git, repo, verification)
REUSE_ARGV = [*script(f"print({GREEN!r})"), "a  b"]


@pytest.fixture
def prior(verification, repo: Path) -> dict:
    art = checked_run(verification, repo, REUSE_ARGV)
    assert art["reusable"] is True
    for item in paths(repo):
        item.unlink()
    return art


def verdict(
    verification, repo: Path, prior, argv=None, head_sha=None
) -> tuple[str, dict]:
    return verification.reuse_verdict(
        prior=prior,
        argv=REUSE_ARGV if argv is None else argv,
        project_root=repo,
        head_sha=head(repo) if head_sha is None else head_sha,
    )


@pytest.mark.parametrize("change", ["none", "store-commit", "store-dirt"])
def test_green_artifact_is_reused_across_store_only_changes(
    verification, repo: Path, prior: dict, change: str
) -> None:
    if change == "store-commit":
        commit(repo, {PM + "notes.md": "later notes\n"}, "store only")
    elif change == "store-dirt":
        write(repo, {PM + "draft.md": "draft\n"})
    assert verdict(verification, repo, copy.deepcopy(prior)) == ("reused", prior)


def _mutate(art: dict, path: tuple, value) -> dict:
    changed = copy.deepcopy(art)
    target = changed
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return changed


MUTATIONS = {
    "kind-near-miss": (("kind",), "verification-artifact-v2"),
    "schema-bool": (("schema_version",), True),
    "schema-two": (("schema_version",), 2),
    "missing-reusable": (("reusable",), KeyError),
    "extra-field": (("extra",), 1),
    "reusable-false": (("reusable",), False),
    "reusable-int": (("reusable",), 1),
    "output-limit": (("output_limit_exceeded",), True),
    "exit-nonzero": (("exit_code",), 1),
    "exit-null": (("exit_code",), None),
    "exit-string": (("exit_code",), "0"),
    "summary-null": (("summary",), None),
    "summary-missing-passed": (("summary", "passed"), KeyError),
    "summary-passed-null": (("summary", "passed"), None),
    "summary-failed": (("summary", "failed"), 1),
    "summary-exit": (("summary", "exit_code"), 1),
    "summary-skipped-null": (("summary", "skipped"), None),
    "summary-skipped-string": (("summary", "skipped"), "1"),
    "argv-not-list": (("argv",), "python"),
    "timed-out": (("timed_out",), True),
    "head-moved": (("head_moved",), True),
    "dirty-paths": (("dirty_paths",), ["src/x"]),
    "log-string": (("log",), "x"),
    "log-empty": (("log",), {}),
    "log-missing-sha256": (("log", "sha256"), KeyError),
}


@pytest.mark.parametrize("case", sorted(MUTATIONS))
def test_malformed_or_failed_artifact_is_stale(
    verification, repo: Path, prior: dict, case: str
) -> None:
    path, value = MUTATIONS[case]
    assert verdict(verification, repo, _mutate(prior, path, value)) == ("stale", {})


@pytest.mark.parametrize(
    "bad", [None, "artifact", [], {}], ids=["none", "string", "list", "empty"]
)
def test_missing_or_non_object_prior_is_stale(verification, repo: Path, bad) -> None:
    assert verdict(verification, repo, bad) == ("stale", {})


@pytest.mark.parametrize("form", ["short", "upper", "symbolic"])
def test_prior_sha_must_be_full_lowercase_hex(
    verification, repo: Path, prior: dict, form: str
) -> None:
    sha = prior["head_sha"]
    forged = {"short": sha[:12], "upper": sha.upper(), "symbolic": "HEAD"}[form]
    assert verdict(verification, repo, _mutate(prior, ("head_sha",), forged)) == (
        "stale",
        {},
    )


@pytest.mark.parametrize(
    "argv",
    [
        [*REUSE_ARGV[:-1], "a b"],
        [*REUSE_ARGV[:-1], "a  b "],
        REUSE_ARGV[:-1],
        [*REUSE_ARGV, "extra"],
        [],
    ],
    ids=["collapsed-space", "trailing-space", "fewer", "more", "empty"],
)
def test_argv_must_match_exactly_without_normalization(
    verification, repo: Path, prior: dict, argv: list[str]
) -> None:
    assert verdict(verification, repo, prior, argv=argv) == ("stale", {})


def test_product_change_after_artifact_head_is_stale(
    verification, repo: Path, prior: dict
) -> None:
    commit(repo, {"src/app.py": "print('changed')\n"}, "product change")
    assert verdict(verification, repo, prior) == ("stale", {})


def test_scratch_commit_after_artifact_head_is_stale(
    verification, repo: Path, prior: dict
) -> None:
    commit(repo, {SCRATCH + "keep.txt": "changed\n"}, "scratch change")
    assert verdict(verification, repo, prior) == ("stale", {})


@pytest.mark.parametrize(
    "dirt",
    [
        {"src/app.py": "print('dirty')\n"},
        {"untracked.py": "x\n"},
        {"src/app.py": None},
    ],
    ids=["tracked", "untracked", "tracked-deletion"],
)
def test_dirty_product_tree_is_stale(
    verification, repo: Path, prior: dict, dirt: dict[str, str | None]
) -> None:
    apply_dirt(repo, dirt)
    assert verdict(verification, repo, prior) == ("stale", {})


def test_artifact_head_that_is_not_an_ancestor_is_stale(
    verification, repo: Path, prior: dict
) -> None:
    git(repo, "checkout", "-q", "-b", "side")
    side = commit(repo, {PM + "side.md": "side\n"}, "side")
    git(repo, "checkout", "-q", "master")
    master = commit(repo, {PM + "main.md": "main\n"}, "master store")
    sibling = _mutate(prior, ("head_sha",), side)
    assert verdict(verification, repo, sibling, head_sha=master) == ("stale", {})
    assert verdict(verification, repo, prior, head_sha=master) == ("reused", prior)


@pytest.mark.parametrize("failure", ["not-a-repo", "unknown-prior-sha", "unknown-head"])
def test_git_errors_are_stale(
    verification, repo: Path, tmp_path: Path, prior: dict, failure: str
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    root = plain if failure == "not-a-repo" else repo
    art = (
        _mutate(prior, ("head_sha",), "f" * 40)
        if failure == "unknown-prior-sha"
        else prior
    )
    head_sha = "e" * 40 if failure == "unknown-head" else prior["head_sha"]
    result = verification.reuse_verdict(
        prior=art, argv=REUSE_ARGV, project_root=root, head_sha=head_sha
    )
    assert result == ("stale", {})
