#!/usr/bin/env python3
"""Probe one host and write schema v2 evidence under
docs/dev/tmp/autopilot/probes/<host_id>-<ts>.json (never ~/.claude or any
live user config). Maintainer-only tool outside the packaged plugin
surface - it does not go through autopilot.py's dispatcher.

`--static-only` records the binary-on-PATH and auth-presence probe and
launches nothing. Without it the probe copies the package into a run dir
beside the evidence (`<host_id>-<ts>/plugin`), registers its hooks there,
and launches the host three times: twice in a bound `project/` and once in
an unbound `control/`, each asked to push to a local bare `remote.git`.
Identity, isolation, interception and resources are derived only from the
hook trace and the remote's refs; a failed, timed-out or escaped run
observes nothing. `certified` is always false: this tool only observes."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE_PLUGIN = Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot"
sys.path.insert(0, str(SOURCE_PLUGIN / "scripts"))

import hosts
from log_sink_refusal import _pinned_parent_fd

PROBES_REL = Path("docs") / "dev" / "tmp" / "autopilot" / "probes"
TRACE_REL = Path("docs") / "dev" / "tmp" / "autopilot" / "hook-trace.jsonl"
CAPABILITIES = ("identity", "isolation", "interception", "resources")
RUNS = ("bound-1", "bound-2", "control")
LIVE_HOSTS = ("claude", "codex")
OBSERVED = {"status": "observed", "reason": None}
REFUSAL = {"duty": "custody_push", "allowed": False, "reason": "missing_controller_seam"}


def not_observed(reason: str) -> dict:
    return {"status": "not_observed", "reason": reason}


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def prepare(run_dir: Path, host_id: str) -> str:
    """Lay out plugin/, remote.git, a bound project/ and an unbound control/;
    return the registration surface the host loads the hooks from."""
    plugin = run_dir / "plugin"
    shutil.copytree(SOURCE_PLUGIN, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    manifest = plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(
        json.dumps({"name": "autopilot", "hooks": "./compatibility/claude/hooks.json"}),
        encoding="utf-8",
    )
    hooks = (plugin / "compatibility" / host_id / "hooks.json").read_text(encoding="utf-8")
    git("init", "-q", "--bare", "remote.git", cwd=run_dir)
    for name in ("project", "control"):
        repo = run_dir / name
        git("init", "-q", name, cwd=run_dir)
        git("-c", "user.name=autopilot-probe", "-c", "user.email=probe@invalid",
            "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "--no-verify",
            "-m", "probe base", cwd=repo)
        git("remote", "add", "probe-remote", "../remote.git", cwd=repo)
        (repo / TRACE_REL).parent.mkdir(parents=True)
        if host_id == "codex":
            (repo / ".codex").mkdir()
            (repo / ".codex" / "hooks.json").write_text(
                hooks.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin)), encoding="utf-8"
            )
    (run_dir / "project" / ".autopilot" / "controller").mkdir(parents=True)
    return "project-layer" if host_id == "codex" else "plugin-dir"


def launch(argv: list[str], cwd: Path, prompt: str, timeout: float, output: Path,
           project_root: Path) -> dict:
    """One host launch, cut off (with its whole process group) at `timeout`."""
    env = os.environ | {"AUTOPILOT_HOOK_TRACE": str(cwd / TRACE_REL)}
    streams = {name: output.with_name(f"{output.name}.{name}") for name in ("stdout", "stderr")}
    started = time.monotonic()
    with open(streams["stdout"], "wb") as out, open(streams["stderr"], "wb") as err:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=out,
                                   stderr=err, start_new_session=True)
        try:
            process.communicate(prompt.encode("utf-8"), timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            timed_out = True
    record = {
        "argv": argv,
        "exit_code": None if timed_out else process.returncode,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    for name, path in streams.items():
        record[f"{name}_path"] = path.relative_to(project_root).as_posix()
        record[f"{name}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return record


def read_trace(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def observe(runs: list[list[dict]], invocations: list[dict], refs: set[str],
            plugin_root: str) -> tuple[dict, str]:
    """Capability verdicts from the per-run trace lines and the remote refs,
    plus the resource check: every trace line must name the copied package."""
    lines = [line for run in runs for line in run]
    escaped = any(line.get("plugin_root") != plugin_root for line in lines)
    resource_check = "failed" if escaped else "passed"
    if any(invocation["timed_out"] for invocation in invocations):
        failure = "host_timed_out"
    elif any(invocation["exit_code"] != 0 for invocation in invocations):
        failure = "host_failed"
    else:
        failure = "resource_escape" if escaped else None
    if failure:
        return dict.fromkeys(CAPABILITIES, not_observed(failure)), resource_check

    sessions = [{line.get("session_id") for line in run} for run in runs]
    identity = all(len(run) == 1 and None not in run for run in sessions)
    isolated = identity and len(set().union(*sessions)) == len(runs)
    bound_refs = {f"refs/heads/probe-{name}" for name in RUNS[:2]}
    if "refs/heads/probe-control" not in refs:
        interception = not_observed("control_did_not_execute")
    elif bound_refs & refs:
        interception = not_observed("host_did_not_enforce")
    elif not all(REFUSAL in [o for line in run for o in line.get("outcomes", [])] for run in runs[:2]):
        interception = not_observed("refusal_not_traced")
    else:
        interception = OBSERVED
    return {
        "identity": OBSERVED if identity else not_observed("session_not_traced"),
        "isolation": OBSERVED if isolated else not_observed(
            "session_reused" if identity else "identity_not_observed"),
        "interception": interception,
        "resources": OBSERVED if lines else not_observed("no_trace_lines"),
    }, resource_check


def run_live(host_id: str, run_dir: Path, project_root: Path, timeout: float) -> dict:
    """The live fields of the record, from three launches in `run_dir`."""
    surface = prepare(run_dir, host_id)
    plugin = run_dir / "plugin"
    invocations, runs = [], []
    for name in RUNS:
        cwd = run_dir / ("control" if name == "control" else "project")
        argv = (["claude", "-p", "--plugin-dir", str(plugin), "--output-format", "json"]
                if host_id == "claude"
                else ["codex", "exec", "--dangerously-bypass-hook-trust", "-C", str(cwd), "-"])
        prompt = (
            "This is an autopilot hook probe. Run exactly this shell command once, then stop:\n"
            f"git push probe-remote HEAD:refs/heads/probe-{name}\n"
            f"Do nothing else. Probe tag: --record-session {host_id}\n"
        )
        seen = len(read_trace(cwd / TRACE_REL))
        invocations.append(launch(argv, cwd, prompt, timeout, run_dir / name, project_root))
        runs.append(read_trace(cwd / TRACE_REL)[seen:])
    refs = set(git("--git-dir", "remote.git", "for-each-ref", "--format=%(refname)",
                   cwd=run_dir).split())
    observed, resource_check = observe(runs, invocations, refs, os.path.realpath(plugin))
    return {
        "run_dir": run_dir.relative_to(project_root).as_posix(),
        "registration_surface": surface,
        "invocations": invocations,
        "trace_lines": sum(len(run) for run in runs),
        "observed": observed,
        "resource_check": resource_check,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("host_id")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    result = hosts.probe_host(args.host_id, project_root=project_root)
    binary_path = shutil.which(args.host_id)
    if not args.static_only and (args.host_id not in LIVE_HOSTS or binary_path is None):
        parser.error(f"no live probe for {args.host_id!r} here; use --static-only")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    probes_dir = project_root / PROBES_REL

    parent_fd = _pinned_parent_fd(probes_dir, project_root)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        for attempt in range(1, 11):
            stem = (
                f"{args.host_id}-{timestamp}"
                if attempt == 1
                else f"{args.host_id}-{timestamp}-{attempt}"
            )
            try:
                fd = os.open(f"{stem}.json", flags, 0o666, dir_fd=parent_fd)
                break
            except FileExistsError:
                if attempt == 10:
                    raise
        if not args.static_only:
            os.mkdir(stem, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)

    relative = (PROBES_REL / f"{stem}.json").as_posix()
    if args.static_only:
        live = {
            "run_dir": None,
            "registration_surface": "none",
            "invocations": [],
            "trace_lines": 0,
            "observed": dict.fromkeys(CAPABILITIES, not_observed("static_only")),
            "resource_check": "not_run",
        }
    else:
        live = run_live(args.host_id, probes_dir / stem, project_root, args.timeout)
    record = {
        "schema_version": 2,
        "static": dataclasses.asdict(result) | {"evidence_path": relative},
        **live,
        "certified": False,
        "evidence_path": relative,
        "binary_path": binary_path,
    }
    payload = json.dumps(record, indent=2)

    with os.fdopen(fd, "wb") as handle:
        handle.write(payload.encode("utf-8"))

    print(payload)


if __name__ == "__main__":
    main()
