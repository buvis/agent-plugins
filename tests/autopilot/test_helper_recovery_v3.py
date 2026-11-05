"""Recovery v3: symlink refusal is anchored to the leading spelling of the project root."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from test_helper_recovery_v2 import (
    ARTIFACT,
    commit_repo,
    core_names,
    failure_shape,
    project,
    reap,
    spy_on_spawn,
    stage_module,
    staged_files,
)
from test_helper_recovery_v2_sinks import CHILD_OUTPUT, seed
from test_helper_rework_sinks import (
    commit_link,
    gate_at,
    leave_untouched,
    spellings_of,
    swap_log_before_open,
    token_child,
)
from test_local_boundary import World, library, make_world
from test_review_helpers import assert_refused, call, snapshot

__all__ = ["project"]  # fixture re-exported for pytest

PARENT = "has a parent-directory component"
RETURN_LOG = b"RETURNED-LOG-SENTINEL-8a41\n"
RETURN_ART = b"RETURNED-ARTIFACT-SENTINEL-8a42\n"  # differs from RETURN_LOG
RACE_LOG = b"RACED-LOG-SENTINEL-8a43\n"
SPELLS = [
    ("resolved", "resolved"),
    ("alias", "alias"),
    ("alias", "resolved"),
    ("resolved", "alias"),
]
SPELL_IDS = [f"{root}-root-{out}-outputs" for root, out in SPELLS]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spy_on_os_open(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Records every os.open call, so a refusal can be proven to come before any open."""
    real = os.open
    calls: list[str] = []

    def spy(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        calls.append(os.fsdecode(path))
        return real(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", spy)
    return calls


def build_tree(tmp_path: Path) -> dict[str, Path]:
    """A plain directory root with every spelling and link shape the anchor must tell apart."""
    base = tmp_path.resolve()
    root = base / "root"
    for sub in ("logs", "sub", "docs/tmp"):
        (root / sub).mkdir(parents=True)
    (base / "links").mkdir()
    (base / "links" / "alias").symlink_to(root, target_is_directory=True)
    (base / "x").mkdir()
    (base / "x" / "anc").symlink_to(base, target_is_directory=True)
    (base / "ext").mkdir()
    (base / "ext" / "back").symlink_to(root, target_is_directory=True)
    (root / "sub" / "out").symlink_to(base / "ext", target_is_directory=True)
    (root / "self").symlink_to(root, target_is_directory=True)
    (root / "swap").symlink_to(base / "ext", target_is_directory=True)
    (root / "loop").symlink_to(root / "loop")
    (base / "loopy").symlink_to(base / "loopy")
    (base / "root-x" / "logs").mkdir(parents=True)
    (base / "side").mkdir()
    (base / "ext" / "deeper").mkdir()
    (root / "a" / "b" / "c").mkdir(parents=True)
    (root / "a" / "b" / "c" / "link").symlink_to(base / "ext", target_is_directory=True)
    (root / "inner").symlink_to(root / "logs", target_is_directory=True)
    (root / "logs" / "real.log").write_bytes(b"real\n")
    (root / "logs" / "leaf.log").symlink_to(root / "logs" / "real.log")
    (base / "far" / "d1" / "d2").mkdir(parents=True)
    (base / "far" / "d1" / "d2" / "alias").symlink_to(root, target_is_directory=True)
    return {
        "base": base,
        "root": root,
        "alias": base / "links" / "alias",
        "anc": base / "x" / "anc",
        "ext": base / "ext",
        "sibling": base / "root-x",
        "far": base / "far" / "d1" / "d2" / "alias",
    }


# --- _root_anchor counts the leading root spelling, shortest first ------------------------------


ANCHOR_CASES = [
    "resolved",
    "alias-path",
    "ancestor-path",
    "deep-alias-path",
    "alias-root",
    "root-itself",
    "shortest",
    "return-link-spelling",
    "parent-below-root",
    "parent-in-spelling",
    "loop-below",
    "relative",
    "empty",
    "near-miss-sibling",
    "loop-above",
    "outside",
]


@pytest.mark.parametrize("case", ANCHOR_CASES)
def test_sink_alias_root_anchor_counts_the_shortest_prefix_that_spells_the_root(
    tmp_path: Path,
    case: str,
) -> None:
    t = build_tree(tmp_path)
    root, n = t["root"], len(t["root"].parts)
    cases = {
        "resolved": (root / "logs" / "a.log", root, n),
        "alias-path": (t["alias"] / "logs" / "a.log", root, n + 1),
        "ancestor-path": (t["anc"] / "root" / "logs" / "a.log", root, n + 2),
        "deep-alias-path": (t["far"] / "logs" / "a.log", root, n + 3),
        "alias-root": (root / "logs" / "a.log", t["alias"], n),
        "root-itself": (root, root, n),
        "shortest": (root / "sub" / "out" / "back" / "logs" / "a.log", root, n),
        "return-link-spelling": (t["ext"] / "back" / "logs" / "a.log", root, n + 1),
        "parent-below-root": (root / ".." / "root" / "out", root, n),
        "parent-in-spelling": (t["base"] / "side" / ".." / "root" / "out", root, n + 2),
        "loop-below": (root / "loop" / "x", root, n),
        "relative": (Path("root/logs/a.log"), root, None),
        "empty": (Path(""), root, None),
        "near-miss-sibling": (t["sibling"] / "logs" / "a.log", root, None),
        "loop-above": (t["base"] / "loopy" / "root" / "a.log", root, None),
        "outside": (t["ext"] / "a.log", root, None),
    }
    path, given_root, expected = cases[case]
    assert library("log_sink_refusal")._root_anchor(path, given_root) == expected


# --- _symlinked_component checks every component after the anchor, with no other stop rule ------


SYMLINK_CASES = [
    ("return-to-root-below", "root", "shortest", True),
    ("return-to-root-alias-root", "alias", "shortest", True),
    ("return-to-root-alias-path", "root", "alias-shortest", True),
    ("link-to-root-itself", "root", "self", True),
    ("loop-below-root", "root", "loop", True),
    ("fail-closed-outside", "root", "outside", True),
    ("link-three-levels-below-root", "root", "deep-link", True),
    ("symlinked-leaf-inside-root", "root", "leaf", True),
    ("link-between-dirs-inside-root", "root", "inner", True),
    ("link-between-dirs-alias-root", "alias", "inner", True),
    ("plain-alias-root", "alias", "plain", False),
    ("plain-deep-dirs", "root", "deep-plain", False),
    ("plain-ancestor-path", "root", "ancestor", False),
    ("the-root-itself", "root", "root", False),
]


@pytest.mark.parametrize(
    ("case", "root_key", "path_key", "expected"),
    SYMLINK_CASES,
    ids=[case[0] for case in SYMLINK_CASES],
)
def test_sink_alias_symlinked_component_sees_every_link_below_the_root_spelling(
    tmp_path: Path,
    case: str,
    root_key: str,
    path_key: str,
    expected: bool,
) -> None:
    t = build_tree(tmp_path)
    root = t["root"]
    paths = {
        "shortest": root / "sub" / "out" / "back" / "logs" / "a.log",
        "alias-shortest": t["alias"] / "sub" / "out" / "back" / "logs" / "a.log",
        "self": root / "self" / "logs" / "a.log",
        "loop": root / "loop" / "x",
        "outside": t["ext"] / "a.log",
        "deep-link": root / "a" / "b" / "c" / "link" / "x.log",
        "leaf": root / "logs" / "leaf.log",
        "inner": root / "inner" / "a.log",
        "plain": root / "logs" / "a.log",
        "deep-plain": root / "a" / "b" / "c" / "x.log",
        "ancestor": t["anc"] / "root" / "logs" / "a.log",
        "root": root,
    }
    sink = library("log_sink_refusal")
    given_root = t[root_key]
    assert (
        sink._symlinked_component(paths[path_key], given_root, given_root) is expected
    ), case


# --- refuse and _pinned_parent_fd reject `..` below the root before opening anything -----------


@pytest.mark.parametrize(
    ("case", "parts", "expected"),
    [
        ("parent-inside", ("sub", "..", "out.log"), PARENT),
        ("parent-at-root", ("..", "repo", "out.log"), PARENT),
        ("parent-deep", ("sub", "a", "b", "..", "out.log"), PARENT),
        ("dotted-leaf", ("sub", "..log"), None),
        ("dotted-dir", ("sub..", "out.log"), None),
    ],
    ids=[
        "sub-dotdot-out",
        "dotdot-root-out",
        "deep-dotdot-out",
        "near-miss-leaf",
        "near-miss-dir",
    ],
)
def test_sink_alias_refuse_names_a_parent_directory_component_below_the_root(
    tmp_path: Path,
    isolated_git: None,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    parts: tuple[str, ...],
    expected: str | None,
) -> None:
    project = commit_repo(tmp_path.resolve() / "repo", {"src/app.py": "a\n"})
    (project / "sub" / "a" / "b").mkdir(parents=True)
    sink = library("log_sink_refusal")
    opened = spy_on_os_open(monkeypatch)
    assert sink.refuse(project.joinpath(*parts), project) == expected, case
    if expected is not None:
        assert opened == [], f"refuse opened {opened} before refusing a '..' path"


def test_sink_alias_refuse_accepts_a_parent_component_inside_the_root_spelling(
    tmp_path: Path,
    isolated_git: None,
) -> None:
    """Only components after the root spelling count; a `..` that spells the root is fine."""
    base = tmp_path.resolve()
    project = commit_repo(base / "repo", {"src/app.py": "a\n"})
    (base / "side").mkdir()
    sink = library("log_sink_refusal")
    assert (
        sink.refuse(base / "side" / ".." / "repo" / "logs" / "a.log", project) is None
    )
    assert (
        sink.refuse(base / "side" / ".." / "repo" / ".." / "repo" / "a.log", project)
        == PARENT
    )


def test_sink_alias_refuse_names_a_symlinked_leaf_inside_the_root(
    tmp_path: Path,
    isolated_git: None,
) -> None:
    """The leaf is checked too, even when its link stays inside the root."""
    project = commit_repo(tmp_path.resolve() / "repo", {"src/app.py": "a\n"})
    (project / "logs").mkdir()
    real = seed(project / "logs" / "real.log", RACE_LOG)
    (project / "logs" / "leaf.log").symlink_to(real)
    sink = library("log_sink_refusal")
    leaf = project / "logs" / "leaf.log"
    assert sink._symlinked_component(leaf, project, project) is True
    assert sink.refuse(leaf, project) == "is a symlink"
    assert sink.refuse(project / "logs" / "real.log", project) is None


@pytest.mark.parametrize(
    "case",
    [
        "sub-dotdot",
        "dotdot-root",
        "deep-dotdot",
        "near-miss-sibling",
        "outside",
        "relative",
    ],
)
def test_sink_alias_pinned_parent_fd_refuses_before_opening_any_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    t = build_tree(tmp_path)
    root = t["root"]
    parents = {
        "sub-dotdot": root / "sub" / "..",
        "dotdot-root": root / ".." / "root",
        "deep-dotdot": root / "docs" / "tmp" / "..",
        "near-miss-sibling": t["sibling"] / "logs",
        "outside": t["ext"],
        "relative": Path("root/logs"),
    }
    sink = library("log_sink_refusal")
    opened = spy_on_os_open(monkeypatch)
    with pytest.raises(OSError):
        os.close(sink._pinned_parent_fd(parents[case], root))
    assert opened == [], f"{case}: opened {opened} before refusing"


@pytest.mark.parametrize(
    ("case", "root_key", "parent_parts", "real_parts"),
    [
        ("logs-alias-root", "alias", ("root", "logs"), ("logs",)),
        ("docs-alias-parent", "root", ("alias", "docs", "tmp"), ("docs", "tmp")),
        ("root-itself", "alias", ("root",), ()),
        ("ancestor-parent", "root", ("anc", "root", "logs"), ("logs",)),
        ("deep-alias-parent", "root", ("far", "logs"), ("logs",)),
        ("parent-in-spelling", "root", ("base", "side", "..", "root", "logs"), ("logs",)),
    ],
)
def test_sink_alias_pinned_parent_fd_opens_the_named_directory_under_any_root_spelling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    root_key: str,
    parent_parts: tuple[str, ...],
    real_parts: tuple[str, ...],
) -> None:
    t = build_tree(tmp_path)
    parent = t[parent_parts[0]].joinpath(*parent_parts[1:])
    expected = os.stat(t["root"].joinpath(*real_parts))
    opened = spy_on_os_open(monkeypatch)
    fd = library("log_sink_refusal")._pinned_parent_fd(parent, t[root_key])
    try:
        got = os.fstat(fd)
    finally:
        os.close(fd)
    assert (got.st_dev, got.st_ino) == (expected.st_dev, expected.st_ino), case
    assert opened, "the descriptor did not come from os.open"


@pytest.mark.parametrize(
    ("case", "root_key", "link"),
    [
        ("outward-link-alias-root", "alias", "swap"),
        ("link-to-root-itself", "root", "self"),
        ("middle-link", "root", "swap/deeper"),
    ],
)
def test_sink_alias_pinned_parent_fd_refuses_a_symlink_below_the_root(
    tmp_path: Path,
    case: str,
    root_key: str,
    link: str,
) -> None:
    t = build_tree(tmp_path)
    with pytest.raises(OSError):
        os.close(
            library("log_sink_refusal")._pinned_parent_fd(t["root"] / link, t[root_key])
        )


# --- run_verification: leave-and-return paths are refused before the spawn ----------------------


def leave_and_return(
    world: World, tmp_path: Path, case: str, pointee: Path
) -> tuple[Path, Path]:
    """R/sub/out (committed) -> an outside directory whose `back` link returns to `pointee`."""
    (world.target.resolve() / "sub").mkdir()
    ext = tmp_path / f"{case}-ext"
    ext.mkdir()
    link = commit_link(world, "sub/out", ext)
    back = ext / "back"
    back.symlink_to(pointee, target_is_directory=True)
    return link, back


def assert_refused_before_spawn(
    report: dict, marker: Path, sentinels: dict[Path, str]
) -> None:
    assert (report["schema_version"], report["ok"]) == (1, False), report
    assert report["error"] == "unsafe-artifact-path", report
    assert not marker.exists(), "the child ran against an output path through a symlink"
    for path, before in sentinels.items():
        assert digest(path) == before, f"the refused run rewrote {path}"


def run_returning(
    world: World,
    tmp_path: Path,
    spelling: tuple[str, str],
    through: str,
    returns_to: str | None,
) -> tuple[dict, Path, dict[Path, str], Path]:
    """`returns_to` names the below-root directory `back` points at; None means the root."""
    spellings = spellings_of(world, tmp_path)
    real = spellings["resolved"]
    landing = real / returns_to if returns_to else real
    case = f"{through}-{spelling[0]}-{spelling[1]}-{returns_to or 'root'}"
    leave_and_return(world, tmp_path, case, landing)
    below = Path() if returns_to else Path("logs")  # where the returned output lands
    name, body = ("returned.log", RETURN_LOG) if through == "log" else ("returned.json", RETURN_ART)
    held = seed(landing / below / name, body)
    sentinels = {held: digest(held)}
    root, spelled = spellings[spelling[0]], spellings[spelling[1]]
    via = spelled / "sub" / "out" / "back" / below
    log = via / name if through == "log" else spelled / "logs" / f"{case}-plain.log"
    artifact = via / name if through == "artifact" else spelled / ARTIFACT
    marker = tmp_path / f"{case}-marker.txt"
    argv = token_child(tmp_path, f"{case}-child", "BACK-TOKEN-8a44", marker)
    report = gate_at(world, argv, root, log, artifact)
    return report, marker, sentinels, real / "logs" / f"{case}-plain.log"


@pytest.mark.parametrize("through", ["log", "artifact"])
@pytest.mark.parametrize("spelling", SPELLS, ids=SPELL_IDS)
def test_sink_alias_a_path_returning_to_a_below_root_directory_is_refused(
    world: World,
    tmp_path: Path,
    isolated_git: None,
    through: str,
    spelling: tuple[str, str],
) -> None:
    """Control (rows 1-2): already refused at v2 by test_helper_rework_sinks R-D1."""
    report, marker, sentinels, plain = run_returning(
        world, tmp_path, spelling, through, "sub2"
    )
    assert_refused_before_spawn(report, marker, sentinels)
    assert not plain.exists(), "the refused run wrote the other output"
    assert not (world.target.resolve() / ARTIFACT).exists()


@pytest.mark.parametrize("through", ["log", "artifact"])
@pytest.mark.parametrize("spelling", SPELLS, ids=SPELL_IDS)
def test_sink_alias_a_path_returning_through_a_link_to_the_root_itself_is_refused(
    world: World,
    tmp_path: Path,
    isolated_git: None,
    through: str,
    spelling: tuple[str, str],
) -> None:
    """Row 3, fail-first: `back` points at the root, so a component below it spells the root."""
    report, marker, sentinels, plain = run_returning(
        world, tmp_path, spelling, through, None
    )
    assert_refused_before_spawn(report, marker, sentinels)
    assert not plain.exists(), "the refused run wrote the other output"
    assert not (world.target.resolve() / ARTIFACT).exists()


@pytest.mark.parametrize("through", ["log", "artifact"])
@pytest.mark.parametrize(
    ("tag", "dotted"),
    [
        ("inner", ("logs", "..", "logs")),
        ("through-root", ("..", "target project", "logs")),
        ("deep", ("logs", "deep", "..")),
    ],
    ids=["inner-dotdot", "dotdot-through-root", "deep-dotdot"],
)
def test_sink_alias_an_output_path_with_a_parent_component_below_the_root_is_refused(
    world: World,
    tmp_path: Path,
    isolated_git: None,
    through: str,
    tag: str,
    dotted: tuple[str, ...],
) -> None:
    real = world.target.resolve()
    (real / "logs" / "deep").mkdir(parents=True, exist_ok=True)
    assert real.name == "target project"
    case = f"{through}-{tag}"
    marker = tmp_path / f"{case}-marker.txt"
    argv = token_child(tmp_path, f"{case}-child", "DOTDOT-TOKEN-8a45", marker)
    log = (
        real.joinpath(*dotted, f"{case}.log")
        if through == "log"
        else real / "logs" / "p.log"
    )
    artifact = (
        real.joinpath(*dotted, f"{case}.json")
        if through == "artifact"
        else real / ARTIFACT
    )
    report = gate_at(world, argv, real, log, artifact)
    assert_refused_before_spawn(report, marker, {})
    for name in (f"{case}.log", f"{case}.json", "p.log"):
        assert not (real / "logs" / name).exists(), f"the refused run wrote {name}"
    assert not (real / ARTIFACT).exists()


# --- run_verification: a parent swapped for a symlink after the judgment fails the sink ---------


def swap_logs_for_a_link_to_itself(log: Path) -> None:
    """Moves the log's `logs` ancestor aside and puts a symlink to it under its name.

    The leaf keeps its inode, so only refusing to follow the link keeps the log unwritten.
    """
    logs = next(p for p in log.parents if p.name == "logs")
    held = logs.with_name("logs-held")
    logs.rename(held)
    logs.symlink_to(held.resolve(), target_is_directory=True)


@pytest.mark.parametrize("nest", [(), ("nest", "deep")], ids=["in-logs", "two-below-logs"])
@pytest.mark.parametrize("swap", [True, False], ids=["swapped", "untouched"])
@pytest.mark.parametrize(
    "spelling",
    [("alias", "resolved"), ("resolved", "alias"), ("ancestor", "alias")],
    ids=[
        "alias-root-resolved-log",
        "resolved-root-alias-log",
        "ancestor-root-alias-log",
    ],
)
def test_sink_alias_a_log_parent_swapped_for_a_symlink_after_refuse_fails_the_sink(
    world: World,
    tmp_path: Path,
    isolated_git: None,
    monkeypatch: pytest.MonkeyPatch,
    spelling: tuple[str, str],
    swap: bool,
    nest: tuple[str, ...],
) -> None:
    """Row 4, fail-first: the descent below the root never follows a link, whatever spelling.

    The swapped-in link leads back to the same directory inside the root, so resolving the
    parent would land under the root and write the existing log through the link. With
    `nest`, the link is a middle component, not the log's own parent.
    """
    spellings = spellings_of(world, tmp_path)
    real = spellings["resolved"]
    (real / "logs").joinpath(*nest).mkdir(parents=True, exist_ok=True)
    held = seed((real / "logs").joinpath(*nest, "raced.log"), RACE_LOG)
    before = digest(held)
    case = f"{spelling[0]}-{spelling[1]}-{swap}-{len(nest)}"
    root, spelled = spellings[spelling[0]], spellings[spelling[1]]
    log = (spelled / "logs").joinpath(*nest, "raced.log")
    marker = tmp_path / f"{case}-marker.txt"
    argv = token_child(tmp_path, f"{case}-child", "RACE-TOKEN-8a46", marker)
    replace = swap_logs_for_a_link_to_itself if swap else leave_untouched
    swapped = swap_log_before_open(monkeypatch, log, replace)
    children = spy_on_spawn(monkeypatch, argv)
    try:
        report = gate_at(world, argv, root, log, spelled / ARTIFACT)
    finally:
        reap(children)
    assert swapped == [log], "the window before the sink opened was never reached"
    if not swap:
        assert report["ok"] is True, report
        assert CHILD_OUTPUT in held.read_bytes(), "the untouched log was never written"
        return
    failure_shape(report, "sink-failed")
    assert not marker.exists(), "the child ran against a sink reached through a symlink"
    moved = real / "logs-held"
    assert os.readlink(real / "logs") == str(moved)
    assert sorted(os.listdir(moved.joinpath(*nest))) == ["raced.log"]
    assert digest(moved.joinpath(*nest, "raced.log")) == before, "written through the link"
    assert not (real / ARTIFACT).exists()


# --- run_verification: a root reached through a symlinked ancestor still succeeds ---------------


@pytest.mark.parametrize(
    ("root_spelling", "out_spelling", "token"),
    [
        ("ancestor", "ancestor", "ANC-TOKEN-8a47"),
        ("ancestor", "resolved", "ANC-TOKEN-8a48"),
        ("resolved", "ancestor", "ANC-TOKEN-8a49"),
    ],
)
def test_sink_alias_a_root_reached_through_a_symlinked_ancestor_still_succeeds(
    world: World,
    tmp_path: Path,
    isolated_git: None,
    root_spelling: str,
    out_spelling: str,
    token: str,
) -> None:
    """Row 5, control: no symlink below the root, so the run is accepted and both sinks written."""
    spellings = spellings_of(world, tmp_path)
    real = spellings["resolved"]
    root, spelled = spellings[root_spelling], spellings[out_spelling]
    case = f"{root_spelling}-{out_spelling}"
    marker = tmp_path / f"{case}-marker.txt"
    argv = token_child(tmp_path, f"{case}-child", token, marker)
    artifact = Path("docs", "dev", "tmp", f"{case}.json")
    report = gate_at(
        world, argv, root, spelled / "logs" / f"{case}.log", spelled / artifact
    )
    assert report["ok"] is True, report
    assert marker.read_text("utf-8") == str(real)
    assert token.encode() in (real / "logs" / f"{case}.log").read_bytes()
    assert json.loads((real / artifact).read_bytes())["argv"] == argv
    assert not (real / ARTIFACT).exists(), "the gate ignored the given artifact path"


def test_sink_alias_outputs_whose_root_spelling_has_a_parent_component_still_succeed(
    world: World,
    tmp_path: Path,
    isolated_git: None,
) -> None:
    """Control: a `..` inside the root spelling is not below the root, so the run is accepted."""
    real = world.target.resolve()
    (real.parent / "spell-side").mkdir()
    spelled = real.parent / "spell-side" / ".." / real.name
    marker = tmp_path / "dotdot-spelling-marker.txt"
    argv = token_child(tmp_path, "dotdot-spelling-child", "SPELL-TOKEN-8a4a", marker)
    artifact = Path("docs", "dev", "tmp", "dotdot-spelling.json")
    report = gate_at(
        world, argv, real, spelled / "logs" / "dotdot-spelling.log", spelled / artifact
    )
    assert report["ok"] is True, report
    assert marker.read_text("utf-8") == str(real)
    assert b"SPELL-TOKEN-8a4a" in (real / "logs" / "dotdot-spelling.log").read_bytes()
    assert json.loads((real / artifact).read_bytes())["argv"] == argv


# --- stage_review: a git-dir probe that times out or cannot start fails closed -----------------


PROBE_FLAG = "--is-inside-git-dir"
PROBE_ENV = ("PROBE_FAILURE_ENV_SENTINEL", "probe-env-8a4b")
REFUSAL_SHAPE = {"schema_version", "ok", "error", "detail"}
GIT_INTERNALS = "artifact_root is inside git internals"  # review_stage's existing refusal text
PROBE_FAILURES = [
    lambda: subprocess.TimeoutExpired(["git", "rev-parse", PROBE_FLAG], 60),
    lambda: FileNotFoundError(2, "No such file or directory", "git"),
    lambda: PermissionError(13, "Permission denied", "git"),
    lambda: OSError(errno.ENOEXEC, "Exec format error", "git"),
]
PROBE_FAILURE_IDS = ["timeout", "git-not-found", "git-not-permitted", "git-not-executable"]
PROBE_DESTINATIONS = [
    ("pf1", ("outside", "rev"), True),
    ("pf2", ("far", "notes.gitlike", "deep", "rev"), False),
]
PROBE_DESTINATION_IDS = ["existing-parent", "missing-ancestors-gitlike-name"]


def stub_git_dir_probe(
    monkeypatch: pytest.MonkeyPatch, outcome: BaseException | subprocess.CompletedProcess | None
) -> list[dict[str, Any]]:
    """Raises or returns `outcome` only for the git-dir probe; None and every other call run git."""
    real = subprocess.run
    probes: list[dict[str, Any]] = []

    def run(*args: Any, **kwargs: Any) -> Any:
        argv = args[0] if args else kwargs.get("args", ())
        if PROBE_FLAG in [str(part) for part in argv]:
            probes.append(dict(kwargs))
            if isinstance(outcome, BaseException):
                raise outcome
            if outcome is not None:
                return outcome
        return real(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    return probes


def outside_destination(
    tmp_path: Path, parts: tuple[str, ...], make_parent: bool
) -> tuple[Path, Path]:
    """The outside destination and the existing ancestor the probe must run from."""
    destination = tmp_path.resolve().joinpath(*parts)
    if make_parent:
        destination.parent.mkdir(parents=True)
    return destination, destination.parent if make_parent else tmp_path.resolve()


def assert_probe_reached(probes: list[dict[str, Any]], ancestor: Path) -> None:
    """The probe ran from the destination's existing ancestor with its locale and timeout."""
    assert probes, "the git-dir probe was never reached for an outside destination"
    for kwargs in probes:
        assert Path(kwargs["cwd"]) == ancestor, kwargs["cwd"]
        assert kwargs["timeout"] == 60, kwargs
        env = kwargs["env"]
        assert (env["LC_ALL"], env["LANGUAGE"]) == ("C", "C"), env
        assert env[PROBE_ENV[0]] == PROBE_ENV[1], "the probe dropped the process environment"


def assert_git_internals_refusal(
    report: dict, destination: Path, project: Path, tmp_path: Path, before: dict
) -> None:
    assert_refused(report)
    assert report["error"] == "unsafe-output", report
    assert set(report) == REFUSAL_SHAPE, report
    assert report["detail"] == GIT_INTERNALS, report
    assert not destination.exists() and staged_files(destination) == set()
    assert staged_files(project / "docs" / "dev" / "tmp" / "rev") == set()
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize(
    ("cycle", "parts", "make_parent"), PROBE_DESTINATIONS, ids=PROBE_DESTINATION_IDS
)
@pytest.mark.parametrize("failure", PROBE_FAILURES, ids=PROBE_FAILURE_IDS)
def test_probe_failure_refuses_an_outside_destination_with_the_controlled_refusal(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Any,
    cycle: str,
    parts: tuple[str, ...],
    make_parent: bool,
) -> None:
    """Fail-first at v2 (d3cd7fa): the probe error escaped stage_review as a traceback."""
    destination, ancestor = outside_destination(tmp_path, parts, make_parent)
    monkeypatch.setenv(*PROBE_ENV)
    before = snapshot(tmp_path)
    probes = stub_git_dir_probe(monkeypatch, failure())
    report = call(stage_module(), project, cycle_id=cycle, artifact_root=destination)
    assert_git_internals_refusal(report, destination, project, tmp_path, before)
    assert_probe_reached(probes, ancestor)


@pytest.mark.parametrize("failure", PROBE_FAILURES, ids=PROBE_FAILURE_IDS)
def test_probe_failure_git_dir_check_itself_fails_closed_without_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: Any
) -> None:
    """The check answers "inside git internals" itself; no wider catch may stand in for it."""
    ancestor = tmp_path.resolve()
    monkeypatch.setenv(*PROBE_ENV)
    probes = stub_git_dir_probe(monkeypatch, failure())
    assert stage_module()._is_inside_git_dir(ancestor) is True
    assert_probe_reached(probes, ancestor)


def test_probe_failure_an_interrupt_during_the_probe_propagates(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only probe errors fail closed; an interrupt is not turned into a refusal."""
    destination, ancestor = outside_destination(tmp_path, ("outside", "rev"), True)
    monkeypatch.setenv(*PROBE_ENV)
    probes = stub_git_dir_probe(monkeypatch, KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        call(stage_module(), project, cycle_id="pf1", artifact_root=destination)
    assert staged_files(destination) == set()
    assert_probe_reached(probes, ancestor)


def test_probe_failure_control_refuses_a_destination_the_probe_reports_inside_git_internals(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Control: a probe that answers "true" gets the same git-internals refusal."""
    destination, ancestor = outside_destination(tmp_path, ("outside", "rev"), True)
    monkeypatch.setenv(*PROBE_ENV)
    before = snapshot(tmp_path)
    answer = subprocess.CompletedProcess(["git"], 0, stdout="true\n", stderr="")
    probes = stub_git_dir_probe(monkeypatch, answer)
    report = call(stage_module(), project, cycle_id="pf1", artifact_root=destination)
    assert_git_internals_refusal(report, destination, project, tmp_path, before)
    assert_probe_reached(probes, ancestor)


@pytest.mark.parametrize(
    ("cycle", "parts", "make_parent"), PROBE_DESTINATIONS, ids=PROBE_DESTINATION_IDS
)
def test_probe_failure_control_accepts_the_same_destination_when_the_probe_answers(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cycle: str,
    parts: tuple[str, ...],
    make_parent: bool,
) -> None:
    """Control: outside any repository, git answers "not a git repository" and staging proceeds."""
    destination, ancestor = outside_destination(tmp_path, parts, make_parent)
    monkeypatch.setenv(*PROBE_ENV)
    probes = stub_git_dir_probe(monkeypatch, None)
    report = call(stage_module(), project, cycle_id=cycle, artifact_root=destination)
    assert report["ok"] is True, report
    assert {Path(a["path"]).parent for a in report["artifacts"]} == {destination}
    assert core_names(cycle) | {f"review-pack-{cycle}.md"} <= staged_files(destination)
    assert_probe_reached(probes, ancestor)
