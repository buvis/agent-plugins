"""Local helpers run without OVCAQ, hidden workflow state or lifecycle wiring."""

from __future__ import annotations

import functools
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from test_local_boundary import (
    CASES, HELPERS, POISON, ROOT, STATE, World, findings_sets, kwargs_for, make_world, one_json,
    run_cli, stage_payload, tree, valid_batch, write_input,
)
from test_local_boundary_verify import ARTIFACT, LOG, marker_argv, verify
from test_review_close_helpers_gates import carry_batch

STAGED = str(Path("docs") / "dev" / "tmp" / "rev")


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


def real(path: Path | str) -> str:
    return os.path.realpath(path)


@functools.cache
def baseline_modules() -> frozenset[str]:
    """Non-stdlib modules the interpreter loads before any facade code runs."""
    script = ("import sys, json; print(json.dumps(sorted({m.split('.')[0] for m in sys.modules}"
              " - set(sys.stdlib_module_names))))")
    proc = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True,
                          text=True, timeout=60, check=True)
    return frozenset(json.loads(proc.stdout))


def poisoned(world: World, *extra: Path) -> set[str]:
    files = [project / STATE / name for project in (world.host, world.target) for name in POISON]
    return {real(path) for path in (*files, *extra)}


def opened(audit: dict) -> set[str]:
    return {real(path) for kind, path in audit["events"] if kind == "open"}


def spawned(audit: dict) -> list[str]:
    return [name for kind, name in audit["events"] if kind == "spawn"]


def watched(world: World, *skip: str) -> dict[str, dict]:
    """Trees of every place a helper could leave state, minus explicitly requested outputs."""
    places = (world.host, world.target, world.cwd, world.home)
    return {str(place): {rel: body for rel, body in tree(place).items()
                         if not any(rel == s or rel.startswith(s + os.sep) for s in skip)}
            for place in places}


def assert_no_hidden_state(world: World, audit: dict, before: dict, *extra: Path,
                           skip: tuple[str, ...] = ()) -> None:
    touched = opened(audit) & poisoned(world, *extra)
    assert not touched, touched
    assert watched(world, *skip) == before


# --- controller_action_not_yet_wired --------------------------------------------------------------


@pytest.mark.parametrize("token", ["run-autopilot", "move-prd", "poisoned-state-path"])
def test_controller_action_not_yet_wired_refuses_before_reads_imports_or_writes(
    world: World, token: str,
) -> None:
    operation = str(world.host / STATE / "state.json") if token == "poisoned-state-path" else token
    before = watched(world)
    proc, audit = run_cli(world, "--controller-action", operation, cwd=world.host, audited=True)
    assert proc.returncode == 3, proc.stderr
    report = one_json(proc)
    assert report == {"schema_version": 1, "ok": False, "error": "controller-required",
                      "operation": operation}
    assert type(report["schema_version"]) is int
    assert spawned(audit) == []
    assert not set(audit["loaded"]) & set(HELPERS), audit["loaded"]
    assert_no_hidden_state(world, audit, before)


def test_controller_action_not_yet_wired_differs_from_a_snapshot_refusal_that_reads_input(
    world: World,
) -> None:
    case, chosen = carry_batch()
    request = write_input(world, kwargs_for(case, chosen))
    before = watched(world)
    proc, audit = run_cli(world, "--prepare-close", request, cwd=world.host, audited=True)
    assert proc.returncode == 3, proc.stderr
    report = one_json(proc)
    assert (report["error"], report["operation"]) == ("controller-required", "prepare-close")
    assert real(request) in opened(audit)
    assert "review_close" in audit["loaded"]
    # The host state.json holds a snapshot that would satisfy the carry row; it stays unread.
    assert_no_hidden_state(world, audit, before)


# --- local_helpers_without_ovcaq ------------------------------------------------------------------


def helper_calls(world: World) -> list[tuple[Any, ...]]:
    case, chosen = valid_batch()
    evidence = write_input(world, {"evidence": CASES["full-clean"]["input"]})
    context = write_input(world, {"expected_context": CASES["full-clean"]["expected_context"]})
    return [
        ("--group-findings", write_input(world, {"findings": findings_sets()[0]})),
        ("--check-evidence", evidence, "--expected-context", context),
        ("--prepare-close", write_input(world, kwargs_for(case, chosen))),
        ("--stage-review", write_input(world, stage_payload(world.target))),
        ("--catchup-probe", "--project-root", world.target),
    ]


def forbidden_lookups(world: World, audit: dict) -> list[str]:
    allowed = [real(p) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix, world.base)]
    roots = [real(ROOT), real(Path.home())]

    def inside(path: str, base: str) -> bool:
        return path == base or path.startswith(base + os.sep)
    return [path for path in opened(audit)
            if any(inside(path, r) for r in roots) and not any(inside(path, a) for a in allowed)]


def test_local_helpers_without_ovcaq_run_from_a_target_only_copy(world: World) -> None:
    scripts = {p.stem for p in world.facade.parent.glob("*.py")} | {"__main__"}
    for arguments in helper_calls(world):
        before = watched(world, STAGED)
        proc, audit = run_cli(world, *arguments, audited=True)
        assert proc.returncode == 0, (arguments[0], proc.stderr)
        assert one_json(proc)["schema_version"] == 1
        extra_modules = set(audit["loaded"]) - baseline_modules()
        assert extra_modules <= scripts, (arguments[0], extra_modules - scripts)
        assert forbidden_lookups(world, audit) == [], arguments[0]
        assert set(spawned(audit)) <= {"git"}, (arguments[0], spawned(audit))
        assert_no_hidden_state(world, audit, before, skip=(STAGED,))
    assert (world.target / STAGED).is_dir()
    assert list(world.home.iterdir()) == []


def test_local_helpers_without_ovcaq_ignore_decoy_runtime_modules_beside_cwd_and_home(
    world: World,
) -> None:
    decoy = "import pathlib\npathlib.Path(__file__).with_suffix('.imported').write_text('x')\n"
    names = ("statectl", "ovcaq", "supervisor", "runtime")
    for place in (world.cwd, world.home, world.host):
        for name in names:
            (place / f"{name}.py").write_text(decoy, encoding="utf-8")
    for arguments in helper_calls(world)[:3]:
        proc, audit = run_cli(world, *arguments, cwd=world.host, audited=True)
        assert proc.returncode == 0, proc.stderr
        assert not set(audit["loaded"]) & set(names)
    leftovers = [p for place in (world.cwd, world.home, world.host)
                 for p in place.glob("*.imported")]
    assert leftovers == []


# --- no_hidden_workflow_state ---------------------------------------------------------------------


def state_inputs(world: World) -> dict[str, Path]:
    """Identical request files inside the executing live state and in an explicit folder."""
    live = world.host / STATE
    case, chosen = valid_batch()
    bodies = {
        "findings.json": {"schema_version": 1, "findings": findings_sets()[0]},
        "evidence.json": {"schema_version": 1, "evidence": CASES["full-clean"]["input"]},
        "context.json": {"schema_version": 1,
                         "expected_context": CASES["full-clean"]["expected_context"]},
        "close.json": {"schema_version": 1, **kwargs_for(case, chosen)},
    }
    for name, body in bodies.items():
        for folder in (live, world.base / "inputs"):
            (folder / name).write_text(json.dumps(body), encoding="utf-8")
    (world.base / "inputs" / "alias.json").symlink_to(live / "findings.json")
    (world.base / "inputs" / "state-link").symlink_to(live, target_is_directory=True)
    return {name: live / name for name in bodies}


def test_no_hidden_workflow_state_inputs_inside_live_state_are_refused_unread(
    world: World,
) -> None:
    live = state_inputs(world)
    outside = {name: world.base / "inputs" / name for name in live}
    refused = (
        ("--group-findings", live["findings.json"]),
        ("--group-findings", world.base / "inputs" / "alias.json"),
        ("--group-findings", world.base / "inputs" / "state-link" / "findings.json"),
        ("--group-findings", world.host / STATE / "state.json"),
        ("--prepare-close", live["close.json"]),
        ("--check-evidence", live["evidence.json"], "--expected-context", outside["context.json"]),
        ("--check-evidence", outside["evidence.json"], "--expected-context", live["context.json"]),
        ("--check-evidence", outside["evidence.json"], "--expected-context",
         outside["context.json"], "--policy", world.host / STATE / "state.json"),
    )
    before = watched(world)
    for arguments in refused:
        proc, audit = run_cli(world, *arguments, cwd=world.host, audited=True)
        assert proc.returncode == 2, (arguments, proc.returncode, proc.stderr)
        assert proc.stderr.strip()
        assert_no_hidden_state(world, audit, before, *live.values())
    for arguments in (("--group-findings", outside["findings.json"]),
                      ("--prepare-close", outside["close.json"]),
                      ("--check-evidence", outside["evidence.json"], "--expected-context",
                       outside["context.json"])):
        proc, audit = run_cli(world, *arguments, cwd=world.host, audited=True)
        assert proc.returncode == 0, (arguments, proc.stderr)
        assert {real(a) for a in arguments[1::2]} <= opened(audit)


def test_no_hidden_workflow_state_verification_never_reuses_or_rewrites_the_live_record(
    world: World,
) -> None:
    outputs = (str(Path(ARTIFACT)), str(Path(LOG)))
    before = watched(world, *outputs)
    proc, audit = verify(world, marker_argv(world), cwd=world.target, audited=True)
    assert proc.returncode == 0, proc.stderr
    report = one_json(proc)
    assert report["artifact"]["head_sha"] != "poison"
    assert json.loads((world.target / ARTIFACT).read_bytes()) == report["artifact"]
    assert (world.base / "spawned").read_text("utf-8") == "spawned"
    assert_no_hidden_state(world, audit, before, skip=outputs)
    for name, text in POISON.items():
        assert (world.target / STATE / name).read_text("utf-8") == text
