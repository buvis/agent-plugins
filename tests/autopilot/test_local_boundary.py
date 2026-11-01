"""Versioned local facade operations wire packaged helpers behind one JSON protocol."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from test_review_close_helpers import kwargs_for, row, scenario, valid_batch
from test_review_close_helpers_gates import carry_batch
from test_review_close_helpers_gates import snapshot as close_snapshot
from test_review_helpers import (
    CONTEXT, DESIGN, DIFF, GATE, PACK, PRD, PRIOR, SETTLED, context_for, roster, texts_for,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "plugins" / "autopilot"
SCRIPTS = PACKAGE / "scripts"
FIXTURES = json.loads((PACKAGE / "contracts" / "review-fixtures-v1.json").read_text("utf-8"))
CASES = {case["name"]: case for case in FIXTURES["cases"]}
STATE = Path("docs") / "dev" / "project-management" / "autopilot"
LEGACY = ["review-policy-v1", "review-evidence-v1", "review-fixtures-v1"]
OPERATIONS = {
    "stage-review-v1", "group-findings-v1", "check-evidence-v1", "prepare-close-v1",
    "catchup-probe-v1", "verification-artifact-v1", "controller-required-v1",
}
HELPERS = ("review_stage", "findings", "rework_groups", "review_evidence", "review_close",
           "catchup", "verification")
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Tess", "GIT_AUTHOR_EMAIL": "tess@example.invalid",
    "GIT_COMMITTER_NAME": "Tess", "GIT_COMMITTER_EMAIL": "tess@example.invalid",
}
POISON = {
    "state.json": json.dumps({"phase": "review", **close_snapshot()}),
    "last-verification.json": '{"schema_version": 1, "reusable": true, "head_sha": "poison"}',
    "review-in-progress": "POISON-MARKER",
}

# Records every open (including os.open relative to a dir_fd), every spawn and
# every non-stdlib module the facade loaded, then exits with the facade's code.
AUDIT = r"""
import json, os, runpy, sys
log_path, facade = sys.argv[1], sys.argv[2]
sys.argv = [facade, *sys.argv[3:]]
events, active = [], [True]
real_open = os.open
def fd_path(fd):
    try:
        import fcntl
        raw = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))
        return raw.split(b"\0", 1)[0].decode()
    except (ImportError, AttributeError):
        return os.readlink(f"/proc/self/fd/{fd}")
def traced_open(path, flags, mode=0o777, *, dir_fd=None):
    name = os.fsdecode(path)
    if active[0] and dir_fd is not None and not os.path.isabs(name):
        events.append(["open", os.path.join(fd_path(dir_fd), name)])
    return real_open(path, flags, mode, dir_fd=dir_fd)
os.open = traced_open
def hook(name, args):
    if not active[0]:
        return
    if name == "open" and isinstance(args[0], (str, bytes)):
        events.append(["open", os.path.abspath(os.fsdecode(args[0]))])
    elif name in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.spawn"):
        argv = args[1]
        first = argv[0] if isinstance(argv, (list, tuple)) and argv else argv
        exe = os.fsdecode(first) if isinstance(first, (str, bytes, os.PathLike)) else str(first)
        events.append(["spawn", os.path.basename(exe)])
    elif name == "os.system":
        events.append(["spawn", str(args[0])])
sys.addaudithook(hook)
code = 0
try:
    runpy.run_path(facade, run_name="__main__")
except SystemExit as exc:
    code = exc.code
finally:
    active[0] = False
    loaded = sorted({m.split(".")[0] for m in sys.modules} - set(sys.stdlib_module_names))
    with open(log_path, "w", encoding="utf-8") as handle:
        json.dump({"events": events, "loaded": loaded}, handle)
raise SystemExit(code)
"""


@dataclass
class World:
    base: Path
    host: Path
    facade: Path
    target: Path
    cwd: Path
    home: Path
    bin: Path
    env: dict[str, str]


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                            text=True, timeout=60, env={**os.environ, **GIT_ENV})
    return result.stdout.strip()


def poison(project: Path) -> None:
    (project / STATE).mkdir(parents=True)
    for name, text in POISON.items():
        (project / STATE / name).write_text(text, encoding="utf-8")


def make_world(tmp_path: Path) -> World:
    """Target-only package copy in a poisoned host project, plus a poisoned target project."""
    host, target = tmp_path / "host project", tmp_path / "target project"
    # python -I ignores PYTHONDONTWRITEBYTECODE; a copied stale .pyc would be rewritten.
    shutil.copytree(PACKAGE, host / "plugins" / "autopilot",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    cwd, home, bindir = tmp_path / "unrelated cwd", tmp_path / "empty home", tmp_path / "bin"
    for directory in (cwd, home, bindir, tmp_path / "inputs"):
        directory.mkdir()
    (bindir / "git").symlink_to(shutil.which("git"))
    for project in (host, target):
        project.mkdir(exist_ok=True)
        git(project, "init", "-q", "-b", "master")
        poison(project)
    (target / "docs" / "dev" / "tmp").mkdir(parents=True)
    (target / "docs" / "dev" / "tmp" / "keep.txt").write_text("keep\n", encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("print('app')\n", encoding="utf-8")
    git(target, "add", "-A")
    git(target, "commit", "-q", "-m", "base")
    env = {"HOME": str(home), "XDG_CONFIG_HOME": str(home), "XDG_CACHE_HOME": str(home),
           "XDG_STATE_HOME": str(home), "PATH": str(bindir), "PYTHONDONTWRITEBYTECODE": "1",
           "LANG": "C.UTF-8", "GIT_CEILING_DIRECTORIES": str(tmp_path), **GIT_ENV}
    facade = host / "plugins" / "autopilot" / "scripts" / "autopilot.py"
    return World(tmp_path, host, facade, target, cwd, home, bindir, env)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return make_world(tmp_path)


def run_cli(world: World, *args: Any, cwd: Path | None = None,
            audited: bool = False) -> tuple[subprocess.CompletedProcess, dict | None]:
    log = world.base / f"audit-{uuid.uuid4().hex}.json"
    prefix = ["-c", AUDIT, str(log)] if audited else []
    proc = subprocess.run(
        [sys.executable, "-I", *prefix, str(world.facade), *map(str, args)],
        cwd=cwd or world.cwd, env=world.env, capture_output=True, timeout=180,
    )
    audit = json.loads(log.read_text("utf-8")) if audited else None
    return proc, audit


def one_json(proc: subprocess.CompletedProcess) -> Any:
    """json.loads rejects trailing data, so this proves exactly one JSON value."""
    return json.loads(proc.stdout.decode("utf-8"))


def assert_usage(proc: subprocess.CompletedProcess) -> None:
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    assert proc.stderr.strip(), "usage errors need a stderr diagnostic"


def write_input(world: World, payload: Any, version: Any = 1, name: str | None = None,
                raw: bytes | None = None) -> Path:
    path = world.base / "inputs" / (name or f"{uuid.uuid4().hex}.json")
    if raw is None:
        body = {"schema_version": version, **payload} if version is not None else dict(payload)
        raw = json.dumps(body).encode("utf-8")
    path.write_bytes(raw)
    return path


def tree(base: Path) -> dict[str, bytes | None]:
    return {str(p.relative_to(base)): None if p.is_dir() else p.read_bytes()
            for p in base.rglob("*") if ".git" not in p.relative_to(base).parts}


def library(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module(name)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def stage_payload(project_root: Path | str, cycle: str = "c7", case: str = "full-clean",
                  artifact_root: str = "docs/dev/tmp/rev") -> dict[str, Any]:
    context = context_for(PRD, case)
    return {
        "project_root": str(project_root), "artifact_root": artifact_root, "cycle_id": cycle,
        "tasks": [], "prd_text": PRD, "design_text": DESIGN, "context_text": CONTEXT,
        "diff_text": DIFF, "expected_context": context, "input_texts": texts_for(context, PRD),
        "pack_text": PACK, "settled_text": SETTLED, "prior_findings_text": PRIOR,
        "test_gate_text": GATE,
    }


def findings_sets() -> list[list[dict[str, Any]]]:
    def finding(severity: str, file: str, issue: str, **extra: Any) -> dict[str, Any]:
        return {"severity": severity, "file": file, "issue": issue, **extra}
    return [
        [finding("🔴", "src/b.py", "C", ref="R1"), finding("🟠", "src/a.py:10", "A"),
         finding("🟡", "src/c/d.py", "D"), finding("🟡", "lib/e.py", "E"),
         finding("⚪", "docs/x.md", "X")],
        [finding("🟡", "tools/f.py", "F"), finding("🟡", "tools/g.py", "G")],
        [],
    ]


def evidence_inputs(world: World, case: str) -> tuple[Path, Path]:
    evidence = write_input(world, {"evidence": CASES[case]["input"]})
    context = write_input(world, {"expected_context": CASES[case]["expected_context"]})
    return evidence, context


# --- legacy operations -------------------------------------------------------------------------


def test_list_capabilities_keeps_legacy_array_and_adds_exactly_the_implemented_operations(
    world: World,
) -> None:
    proc, _ = run_cli(world, "--list-capabilities")
    assert proc.returncode == 0, proc.stderr
    ids = one_json(proc)
    assert isinstance(ids, list) and ids[:3] == LEGACY
    assert proc.stdout == json.dumps(ids, separators=(",", ":")).encode() + b"\n"
    assert len(ids) == len(set(ids)) == len(LEGACY) + len(OPERATIONS)
    assert set(ids[3:]) == OPERATIONS
    assert not [i for i in ids if "cap" in i.split("-") or "custody" in i]
    assert list(world.home.iterdir()) == [] and list(world.cwd.iterdir()) == []


def test_export_policy_is_the_unwrapped_canonical_policy(world: World) -> None:
    proc, _ = run_cli(world, "--export-policy")
    policy = json.loads((PACKAGE / "contracts" / "review-policy-v1.json").read_bytes())
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == canonical(policy) + b"\n"
    assert "ok" not in one_json(proc) and one_json(proc)["schema_version"] == 1


# --- argument and envelope usage errors -----------------------------------------------------------


def test_operations_are_mutually_exclusive_and_missing_companions_are_usage_errors(
    world: World,
) -> None:
    request = write_input(world, {"findings": findings_sets()[0]})
    evidence, context = evidence_inputs(world, "full-clean")
    invalid = (
        (), ("--group-findings", request, "--stage-review", request),
        ("--list-capabilities", "--group-findings", request),
        ("--export-policy", "--prepare-close", request),
        ("--controller-action", "run-autopilot", "--group-findings", request),
        ("--catchup-probe", "--project-root", world.target, "--group-findings", request),
        ("--check-evidence", evidence), ("--expected-context", context),
        ("--catchup-probe",), ("--group-findings",), ("--group-findings-v1", request),
    )
    before = tree(world.base)
    for arguments in invalid:
        proc, _ = run_cli(world, *arguments)
        assert_usage(proc)
    assert tree(world.base) == before
    accepted, _ = run_cli(world, "--group-findings", request)
    assert accepted.returncode == 0, accepted.stderr


@pytest.mark.parametrize("version", [None, 0, 2, -1, True, 1.0, "1"],
                         ids=["missing", "zero", "higher", "negative", "bool", "float", "string"])
def test_request_schema_version_must_be_the_integer_one_before_effects(
    world: World, version: Any,
) -> None:
    before = tree(world.target)
    stage = write_input(world, stage_payload(world.target), version=version)
    group = write_input(world, {"findings": findings_sets()[0]}, version=version)
    good_evidence, good_context = evidence_inputs(world, "full-clean")
    bad_evidence = write_input(world, {"evidence": CASES["full-clean"]["input"]}, version)
    bad_context = write_input(
        world, {"expected_context": CASES["full-clean"]["expected_context"]}, version)
    case, chosen = valid_batch()
    close = write_input(world, kwargs_for(case, chosen), version=version)
    for arguments in (
        ("--stage-review", stage), ("--group-findings", group), ("--prepare-close", close),
        ("--check-evidence", bad_evidence, "--expected-context", good_context),
        ("--check-evidence", good_evidence, "--expected-context", bad_context),
    ):
        proc, _ = run_cli(world, *arguments)
        assert_usage(proc)
    assert tree(world.target) == before
    accepted, _ = run_cli(world, "--check-evidence", good_evidence, "--expected-context",
                          good_context)
    assert accepted.returncode == 0, accepted.stderr


def test_malformed_missing_and_non_object_inputs_are_usage_errors(world: World) -> None:
    missing = world.base / "inputs" / "absent.json"
    bodies = (b"", b"{", b"[]", b'"text"', b"null", b'{"schema_version": 1, "findings": [}',
              b'{"schema_version": 1, "findings": [], "schema_version": NaN}')
    paths = [write_input(world, {}, raw=body) for body in bodies]
    for path in (missing, *paths):
        proc, _ = run_cli(world, "--group-findings", path)
        assert_usage(proc)
    _, context = evidence_inputs(world, "full-clean")
    proc, _ = run_cli(world, "--check-evidence", missing, "--expected-context", context)
    assert_usage(proc)
    evidence, _ = evidence_inputs(world, "full-clean")
    broken_policy = write_input(world, {}, raw=b'{"policy_digest": ')
    proc, _ = run_cli(world, "--check-evidence", evidence, "--expected-context", context,
                      "--policy", broken_policy)
    assert proc.returncode == 2 and proc.stderr.strip()


def test_requests_with_missing_mistyped_or_unknown_keyword_fields_are_usage_errors(
    world: World,
) -> None:
    case, chosen = valid_batch()
    close, stage = kwargs_for(case, chosen), stage_payload(world.target)
    invalid = (
        ("--group-findings", {}), ("--group-findings", {"findings": "x"}),
        ("--group-findings", {"findings": {}}),
        ("--group-findings", {"findings": findings_sets()[0], "extra": 1}),
        ("--prepare-close", {}),
        ("--prepare-close", {key: v for key, v in close.items() if key != "review_ref"}),
        ("--prepare-close", {**close, "extra": 1}),
        ("--stage-review", {}),
        ("--stage-review", {key: v for key, v in stage.items() if key != "cycle_id"}),
        ("--stage-review", {**stage, "extra": 1}),
    )
    before = tree(world.target)
    for option, payload in invalid:
        proc, _ = run_cli(world, option, write_input(world, payload))
        assert_usage(proc)
    assert tree(world.target) == before
    for option, payload in (("--group-findings", {"findings": findings_sets()[0]}),
                            ("--prepare-close", close)):
        accepted, _ = run_cli(world, option, write_input(world, payload))
        assert accepted.returncode == 0, (option, accepted.stderr)


# --- group findings -------------------------------------------------------------------------------


def test_group_findings_envelopes_the_library_groups(world: World) -> None:
    rework_groups = library("rework_groups")
    seen = []
    for findings in findings_sets():
        request = write_input(world, {"findings": findings})
        proc, _ = run_cli(world, "--group-findings", request)
        assert proc.returncode == 0, proc.stderr
        report = one_json(proc)
        expected = rework_groups.group(copy.deepcopy(findings))
        assert report == {"schema_version": 1, "ok": True, "groups": expected}
        assert type(report["schema_version"]) is int
        seen.append(len(report["groups"]))
    assert seen[0] > 1 and seen[-1] == 0 and len(set(seen)) == 3


# --- check evidence -------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["full-clean", "fast-track-clean", "full-missing-alice",
                                  "full-changed-prd"])
def test_check_evidence_uses_the_packaged_policy_and_maps_invalid_evidence_to_exit_1(
    world: World, case: str,
) -> None:
    review_evidence = library("review_evidence")
    evidence, context = evidence_inputs(world, case)
    proc, _ = run_cli(world, "--check-evidence", evidence, "--expected-context", context)
    expected = review_evidence.check_evidence(
        review_evidence.load_policy(), CASES[case]["expected_context"], CASES[case]["input"])
    assert one_json(proc) == expected
    accepted = CASES[case]["expect"]["outcome"] == "accepted"
    assert expected["ok"] is accepted
    assert proc.returncode == (0 if accepted else 1), proc.stderr
    if not accepted:
        assert set(CASES[case]["expect"]["defects"]) <= set(one_json(proc)["defects"])


def test_check_evidence_reads_an_explicit_alternate_policy_unchanged(world: World) -> None:
    review_evidence = library("review_evidence")
    case = CASES["full-stale-policy-binding"]
    evidence, context = evidence_inputs(world, "full-stale-policy-binding")
    reports = {}
    for name in ("v1", "v1-alt"):
        policy = world.base / "inputs" / f"policy-{name}.json"
        policy.write_text(json.dumps(FIXTURES["policies"][name]), encoding="utf-8")
        proc, _ = run_cli(world, "--check-evidence", evidence, "--expected-context", context,
                          "--policy", policy)
        reports[name] = one_json(proc)
        assert reports[name] == review_evidence.check_evidence(
            FIXTURES["policies"][name], case["expected_context"], case["input"])
        assert proc.returncode == (0 if reports[name]["ok"] else 1)
    assert reports["v1"] != reports["v1-alt"]
    default, _ = run_cli(world, "--check-evidence", evidence, "--expected-context", context)
    assert one_json(default) == reports["v1"]


# --- stage review ---------------------------------------------------------------------------------


def test_stage_review_writes_under_the_relative_artifact_root_of_the_explicit_project(
    world: World,
) -> None:
    rosters = []
    for cycle, case in (("c7", "full-clean"), ("fast2", "fast-track-clean")):
        request = write_input(world, stage_payload(world.target, cycle, case))
        proc, _ = run_cli(world, "--stage-review", request)
        assert proc.returncode == 0, proc.stderr
        report = one_json(proc)
        assert set(report) == {"schema_version", "ok", "artifacts", "prompts", "input_manifest"}
        assert report["schema_version"] == 1 and report["ok"] is True
        art = (world.target / "docs" / "dev" / "tmp" / "rev").resolve()
        assert set(report["prompts"]) == roster(CASES[case]["expected_context"])
        for job, prompt in report["prompts"].items():
            assert Path(prompt).resolve() == art / f"{job}-prompt-{cycle}.md"
        for item in report["artifacts"]:
            path = Path(item["path"])
            assert path.resolve().parent == art
            assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        rosters.append(set(report["prompts"]))
    assert rosters[0] != rosters[1]
    assert list(world.cwd.iterdir()) == []


def test_stage_review_refuses_a_live_state_artifact_root_as_a_path_error(world: World) -> None:
    before = tree(world.target)
    for artifact_root in (str(STATE / "review"), str(world.target / ".git" / "review")):
        request = write_input(world, stage_payload(world.target, artifact_root=artifact_root))
        proc, _ = run_cli(world, "--stage-review", request)
        assert proc.returncode == 2, proc.stderr
        report = one_json(proc)
        assert report["schema_version"] == 1 and report["ok"] is False
    assert tree(world.target) == before
    safe = write_input(world, stage_payload(world.target, artifact_root="docs/dev/tmp/rev2"))
    proc, _ = run_cli(world, "--stage-review", safe)
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize(
    ("override", "error", "code"),
    [({"cycle_id": "../x"}, "invalid-input", 2),
     ({"expected_context": {"schema_version": 1}}, "invalid-expected-context", 1)],
    ids=["unsafe-cycle-id", "invalid-expected-context"],
)
def test_stage_review_input_and_preparation_refusals_exit_nonzero_without_writes(
    world: World, override: dict[str, Any], error: str, code: int,
) -> None:
    before = tree(world.target)
    request = write_input(world, {**stage_payload(world.target), **override})
    proc, _ = run_cli(world, "--stage-review", request)
    assert proc.returncode == code, (proc.returncode, proc.stderr)
    report = one_json(proc)
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert (report["ok"], report["error"]) == (False, error)
    assert tree(world.target) == before and list(world.cwd.iterdir()) == []


# --- prepare close --------------------------------------------------------------------------------


def test_prepare_close_emits_library_proposals_and_maps_refusals(world: World) -> None:
    review_close = library("review_close")
    case, chosen = valid_batch()
    mismatch = scenario(["R1", "R2", "R3"], table_refs=["R1", "R3"])
    missing_alice = {**kwargs_for(case, chosen),
                     "evidence": CASES["full-missing-alice"]["input"],
                     "expected_context": CASES["full-missing-alice"]["expected_context"]}
    calls = (
        (kwargs_for(case, chosen), 0),
        (kwargs_for(case, chosen, cycle=5, default_tier="opus"), 0),
        (kwargs_for(mismatch, chosen[:2] + [row("R3", "defer")]), 1),
        (kwargs_for(scenario([]), []), 0),
        (missing_alice, 1),
    )
    reports = []
    for kwargs, code in calls:
        proc, _ = run_cli(world, "--prepare-close", write_input(world, kwargs))
        assert proc.returncode == code, proc.stderr
        reports.append(one_json(proc))
        assert reports[-1] == review_close.prepare_close(**copy.deepcopy(kwargs))
    assert reports[0] != reports[1]
    assert reports[2]["error"] == "findings_mismatch"
    assert (reports[4]["ok"], reports[4]["error"]) == (False, "invalid-evidence")


def test_prepare_close_without_a_needed_snapshot_is_controller_required(world: World) -> None:
    case, chosen = carry_batch()
    proc, _ = run_cli(world, "--prepare-close", write_input(world, kwargs_for(case, chosen)))
    assert proc.returncode == 3, proc.stderr
    report = one_json(proc)
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert (report["ok"], report["error"], report["operation"]) == (
        False, "controller-required", "prepare-close")
    with_snapshot = kwargs_for(case, chosen, read_snapshot=close_snapshot())
    proc, _ = run_cli(world, "--prepare-close", write_input(world, with_snapshot))
    assert proc.returncode == 0, proc.stderr
    assert one_json(proc)["ok"] is True


# --- catch-up probe -------------------------------------------------------------------------------


def fake_tool(world: World, name: str, code: int, stderr: str = "") -> Path:
    log = world.base / f"{name}-cwd.txt"
    tool = world.bin / name
    tool.write_text(f"#!/bin/sh\npwd -P > '{log}'\nprintf '%s\\n' '{stderr}' >&2\nexit {code}\n",
                    encoding="utf-8")
    tool.chmod(0o755)
    return log


def test_catchup_probe_without_tools_is_a_successful_observation(world: World) -> None:
    before = tree(world.target)
    proc, _ = run_cli(world, "--catchup-probe", "--project-root", world.target)
    assert proc.returncode == 0, proc.stderr
    report = one_json(proc)
    assert report["schema_version"] == 1 and type(report["schema_version"]) is int
    assert (report["gh"], report["engram"]) == ("absent", "absent")
    assert sorted(report["skip"]) == ["engram", "github-state"]
    assert tree(world.target) == before
    missing, _ = run_cli(world, "--catchup-probe")
    assert_usage(missing)


@pytest.mark.parametrize(
    ("gh_code", "gh_token", "engram_err", "engram_token"),
    [(0, "ok", "", "ok"), (1, "unauthenticated", "", "ok"),
     (2, "unauthenticated", "error: not inside a registered repo", "unregistered")],
    ids=["all-ok", "gh-exit-1", "gh-exit-2-engram-unregistered"],
)
def test_catchup_probe_runs_the_tools_in_the_explicit_project_root(
    world: World, gh_code: int, gh_token: str, engram_err: str, engram_token: str,
) -> None:
    gh_log = fake_tool(world, "gh", gh_code)
    engram_log = fake_tool(world, "engram", 0, engram_err)
    for project in (world.target, world.base / "second root"):
        project.mkdir(exist_ok=True)
        proc, _ = run_cli(world, "--catchup-probe", "--project-root", project)
        assert proc.returncode == 0, proc.stderr
        report = one_json(proc)
        assert (report["gh"], report["engram"]) == (gh_token, engram_token)
        assert ("github-state" in report["skip"]) is (gh_token != "ok")
        assert ("engram" in report["skip"]) is (engram_token != "ok")
        for log in (gh_log, engram_log):
            assert log.read_text("utf-8").strip() == str(project.resolve())
