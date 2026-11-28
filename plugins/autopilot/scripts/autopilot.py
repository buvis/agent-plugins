#!/usr/bin/env python3
"""Expose the packaged review contracts without starting runtime services."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import errno
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys


_ROOT_KEYS = {
    "schema_version", "procedure", "reviewer_jobs", "rubric_sets",
    "doubt_label_map", "execution_profiles", "artifact_kinds",
    "input_kinds", "source_bindings", "policy_digest",
}
_CAPABILITIES = [
    "review-policy-v1", "review-evidence-v1", "review-fixtures-v1",
    "stage-review-v1", "group-findings-v1", "check-evidence-v1",
    "prepare-close-v1", "catchup-probe-v1", "verification-artifact-v1",
    "controller-required-v1", "hosts-v1", "guards-v1", "diagnose-v1",
    "hook-v1",
    "request-job-v1", "bind-job-v1", "close-child-v1", "resolve-roles-v1",
    "record-session-v1",
]
_MODES = (
    "list_capabilities", "export_policy", "stage_review", "group_findings",
    "check_evidence", "prepare_close", "catchup_probe", "verify",
    "controller_action", "probe_host", "run_guard", "diagnose", "hook",
    "request_job", "bind_job", "close_child", "resolve_roles", "record_session",
)
_COMPANIONS = {
    "out": ("export_policy", "request_job"),
    "expected_context": ("check_evidence",),
    "policy": ("check_evidence",),
    "context": ("run_guard",),
    "project_root": ("catchup_probe", "verify", "probe_host", "diagnose",
                     "request_job", "bind_job", "close_child", "record_session"),
    "head_sha": ("verify",),
    "artifact": ("verify",),
    "log": ("verify",),
    "git_dir": ("verify",),
    "work_tree": ("verify",),
    "timeout": ("verify",),
    "event": ("hook",),
    "profile": ("resolve_roles",),
    "lane": ("resolve_roles",),
    "facts": ("resolve_roles",),
}
_REQUIRED = {
    "check_evidence": ("expected_context",),
    "catchup_probe": ("project_root",),
    "verify": ("project_root", "head_sha", "artifact", "log"),
    "probe_host": ("project_root",),
    "run_guard": ("context",),
    "diagnose": ("project_root",),
    "hook": ("event",),
    "request_job": ("project_root", "out"),
    "bind_job": ("project_root",),
    "close_child": ("project_root",),
    "resolve_roles": ("profile", "lane"),
    "record_session": ("project_root",),
}
_INPUTS = ("stage_review", "group_findings", "check_evidence",
           "expected_context", "policy", "prepare_close", "context", "out", "facts")
_LIVE_STATE = ("docs", "dev", "project-management", "autopilot")
_JOB_KEYS = {"job_id", "role_id", "host_id", "tier", "effort", "inputs", "excluded_input_kinds"}


class _Usage(Exception):
    """A usage, input or path error: exit 2 with a stderr diagnostic."""


class _Refused(Exception):
    """A jobs.JobRefused refusal: exit 1 with one `ok: false` JSON line and a
    silent stderr; the message is the refusal code."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--list-capabilities", action="store_true")
    modes.add_argument("--export-policy", action="store_true")
    for flag in ("--stage-review", "--group-findings", "--check-evidence",
                 "--prepare-close", "--request-job", "--bind-job", "--close-child"):
        modes.add_argument(flag, type=Path)
    modes.add_argument("--catchup-probe", action="store_true")
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--controller-action")
    modes.add_argument("--probe-host")
    modes.add_argument("--run-guard")
    modes.add_argument("--diagnose", action="store_true")
    modes.add_argument("--hook")
    modes.add_argument("--resolve-roles", action="store_true")
    modes.add_argument("--record-session")
    for flag in ("--out", "--expected-context", "--policy", "--project-root",
                 "--artifact", "--log", "--context", "--facts",
                 "--git-dir", "--work-tree"):
        parser.add_argument(flag, type=Path)
    parser.add_argument("--head-sha")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--event")
    parser.add_argument("--profile")
    parser.add_argument("--lane")
    return parser


def _check_companions(parser: argparse.ArgumentParser, args: argparse.Namespace,
                      mode: str, rest: list[str] | None) -> None:
    for flag, modes in _COMPANIONS.items():
        if getattr(args, flag) is not None and mode not in modes:
            wanted = " or ".join("--" + m.replace("_", "-") for m in modes)
            parser.error(f"--{flag.replace('_', '-')} requires {wanted}")
    for flag in _REQUIRED.get(mode, ()):
        if getattr(args, flag) is None:
            parser.error(f"--{mode.replace('_', '-')} requires --{flag.replace('_', '-')}")
    if (rest is not None) != (mode == "verify"):
        parser.error("'-- ARGV...' is required by --verify and accepted by nothing else")


def _in_live_state(path: Path) -> bool:
    """True when the unresolved or resolved path lies in live workflow state;
    realpath follows symlinks without opening the file."""
    for candidate in (os.path.abspath(path), os.path.realpath(path)):
        parts = Path(candidate).parts
        if any(tuple(p.casefold() for p in parts[i:i + 4]) == _LIVE_STATE
               for i in range(len(parts))):
            return True
    return False


def _helper(name: str):
    sys.dont_write_bytecode = True  # leave no __pycache__ beside the packaged helpers
    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module(name)


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise _Usage(f"cannot read {path}: {error}") from error


def _request(path: Path, fields: set[str] | None = None) -> dict:
    body = _read_json(path)
    version = body.get("schema_version") if isinstance(body, dict) else None
    if type(version) is not int or version != 1:
        raise _Usage(f"{path} must be a JSON object with integer schema_version 1")
    kwargs = {key: value for key, value in body.items() if key != "schema_version"}
    if fields is not None and set(kwargs) != fields:
        raise _Usage(f"{path} must carry exactly {sorted(fields)} beside schema_version")
    return kwargs


def _call(function, kwargs: dict) -> dict:
    try:
        return function(**kwargs)
    except (TypeError, ValueError) as error:
        raise _Usage(str(error)) from error


def _job_call(function, kwargs: dict):
    """`_call` for jobs.py: an invalid_request refusal or a path error is a
    usage error, any other JobRefused is a refusal."""
    try:
        return function(**kwargs)
    except _helper("jobs").JobRefused as refused:
        if refused.code == "invalid_request":
            raise _Usage(str(refused)) from refused
        raise _Refused(refused.code) from refused
    except (OSError, TypeError, ValueError) as error:
        raise _Usage(str(error)) from error


def _stage_review(args: argparse.Namespace) -> tuple[dict, int]:
    report = _call(_helper("review_stage").stage_review, _request(args.stage_review))
    if report["ok"]:
        return report, 0
    return report, 2 if report["error"] in {"invalid-input", "unsafe-output", "write-failed"} else 1


def _group_findings(args: argparse.Namespace) -> tuple[dict, int]:
    findings = _request(args.group_findings, {"findings"})["findings"]
    if not isinstance(findings, list):
        raise _Usage("findings must be a list")
    groups = _call(_helper("rework_groups").group, {"findings": findings})
    return {"schema_version": 1, "ok": True, "groups": groups}, 0


def _check_evidence(args: argparse.Namespace) -> tuple[dict, int]:
    review_evidence = _helper("review_evidence")
    evidence = _request(args.check_evidence, {"evidence"})["evidence"]
    context = _request(args.expected_context, {"expected_context"})["expected_context"]
    policy = review_evidence.load_policy() if args.policy is None else _read_json(args.policy)
    report = review_evidence.check_evidence(policy, context, evidence)
    return report, 0 if report["ok"] else 1


def _prepare_close(args: argparse.Namespace) -> tuple[dict, int]:
    report = _call(_helper("review_close").prepare_close, _request(args.prepare_close))
    if report["ok"]:
        return report, 0
    return report, 3 if report["error"] == "controller-required" else 1


def _catchup_probe(args: argparse.Namespace) -> tuple[dict, int]:
    return _helper("catchup").probe(args.project_root), 0


def _probe_host(args: argparse.Namespace) -> tuple[dict, int]:
    return asdict(_call(_helper("hosts").probe_host,
                        {"host_id": args.probe_host, "project_root": args.project_root})), 0


def _run_guard(args: argparse.Namespace) -> tuple[dict, int]:
    return asdict(_call(_helper("guards").run_guard,
                        {"duty": args.run_guard, "context": _read_json(args.context),
                         "seam": None})), 0


def _diagnose(args: argparse.Namespace) -> tuple[dict, int]:
    return _helper("doctor").diagnose(project_root=args.project_root), 0


def _request_job(args: argparse.Namespace) -> tuple[dict, int]:
    jobs, hosts = _helper("jobs"), _helper("hosts")
    body = _request(args.request_job, _JOB_KEYS)
    if os.path.lexists(args.out):
        raise _Usage(f"{args.out} already exists")
    host_id = next((host for host in hosts.ADAPTERS
                    if hosts.adapter(host).SESSION_ENV_VAR in os.environ), None)
    if host_id is None:
        raise _Refused("missing_native_session")
    ancestry = _job_call(jobs.derive_ancestry,
                         {"env": os.environ, "project_root": args.project_root})
    request = _job_call(jobs.build_job_request, {
        **body, "requester": hosts.current_session(host_id, os.environ),
        "ancestry": ancestry, "project_root": args.project_root})
    return _job_call(jobs.request_job, {"request": request, "seam": None,
                                        "project_root": args.project_root,
                                        "request_file": args.out}), 0


def _bind_job(args: argparse.Namespace) -> tuple[dict, int]:
    jobs, hosts = _helper("jobs"), _helper("hosts")
    payload = _read_json(args.bind_job)
    request = _job_call(jobs.JobRequest.from_payload, {"payload": payload})
    child = hosts.current_session(request.host_id, os.environ)
    if child is None:
        raise _Refused("missing_native_session")
    record = _job_call(jobs.bind_job_session, {"payload": payload, "child": child,
                                               "project_root": args.project_root})
    return {"schema_version": 1, "ok": True, **record}, 0


def _close_child(args: argparse.Namespace) -> tuple[dict, int]:
    jobs, hosts = _helper("jobs"), _helper("hosts")
    body = _request(args.close_child, {"child", "outcome", "artifact_path"})
    if not isinstance(body["child"], dict) or body["child"].get("kind") != "in-session" \
            or not isinstance(body["artifact_path"], str):
        raise _Usage(f"{args.close_child} must carry an in-session child and a string artifact_path")
    parent = hosts.current_session("claude", os.environ)
    if parent is None:
        raise _Refused("missing_native_session")
    root = Path(args.project_root).resolve()
    record = _job_call(jobs.close_native_child, {
        "parent": parent, "child": body["child"], "outcome": body["outcome"],
        "raw_output": sys.stdin.buffer.read(), "artifact_path": root / body["artifact_path"],
        "project_root": root})
    return {"schema_version": 1, "ok": True, **record}, 0


def _resolve_roles(args: argparse.Namespace) -> tuple[dict, int]:
    roles, hosts = _helper("roles"), _helper("hosts")
    facts = roles.ProfileFacts(gemini_cli_available=False, doubt_reviewer=None,
                               implementor_codex_present=False)
    if args.facts is not None:
        body = _read_json(args.facts)
        if not isinstance(body, dict):
            raise _Usage(f"{args.facts} must be a JSON object")
        facts = _call(roles.ProfileFacts, body)
        if not (isinstance(facts.gemini_cli_available, bool)
                and isinstance(facts.implementor_codex_present, bool)
                and (facts.doubt_reviewer is None or isinstance(facts.doubt_reviewer, str))):
            raise _Usage(f"{args.facts} holds a fact of the wrong type")
    implemented = {host_id: hosts.adapter(host_id).IMPLEMENTED_CAPABILITIES
                   for host_id in hosts.ADAPTERS}
    resolved = _call(roles.resolve_profile, {
        "policy": _helper("review_evidence").load_policy(), "profile_id": args.profile,
        "lane": args.lane, "facts": facts, "implemented": implemented, "observed": None})
    return asdict(resolved), 0 if resolved.status == "resolvable" else 1


def _record_session(args: argparse.Namespace) -> tuple[dict, int]:
    """Always exits 0; traces through interception's own writer under the
    same AUTOPILOT_HOOK_TRACE gate and trace-directory confinement."""
    hosts, interception = _helper("hosts"), _helper("interception")
    if args.record_session not in hosts.ADAPTERS:
        raise _Usage(f"unknown host: {args.record_session!r}")
    session = hosts.current_session(args.record_session, os.environ)
    root = Path(args.project_root).resolve()
    decision = interception.HookDecision(
        host_id=args.record_session, event="record_session", session=session,
        project_root=str(root), bound=False, outcomes=(), skipped=(), allowed=True,
        additional_context=None)
    trace = os.environ.get(interception.TRACE_ENV)
    traced = bool(trace) and interception._resolve_trace_path(trace, root) is not None
    if traced:
        interception._write_trace(decision, os.environ)
    return {"schema_version": 1, "host_id": args.record_session,
            "session": interception._session_dict(session),
            "plugin_root": str(Path(__file__).resolve().parents[1]), "traced": traced}, 0


def _hook(args: argparse.Namespace) -> int:
    """Dispatch a registered host hook event to `interception.run_hook` and
    relay its reply verbatim: the adapter already encodes allow/deny in
    `reply.stdout`, so this prints that text as-is and exits `reply.exit_code`
    rather than wrapping it in this CLI's usual JSON-report envelope."""
    interception = _helper("interception")
    stdin = sys.stdin.buffer.read()
    try:
        reply = interception.run_hook(args.hook, args.event, stdin, env=os.environ)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2
    except ValueError as error:
        print(f"autopilot: {error}", file=sys.stderr)
        return 2
    if reply.stdout:
        print(reply.stdout)
    return reply.exit_code


def _verify(args: argparse.Namespace) -> tuple[dict, int]:
    kwargs = {
        "argv": args.argv, "project_root": args.project_root,
        "head_sha": args.head_sha, "artifact_path": args.artifact,
        "log_path": args.log,
    }
    if args.timeout is not None:
        kwargs["timeout"] = args.timeout
    if (args.git_dir is None) != (args.work_tree is None):
        raise _Usage("--git-dir and --work-tree must be given together")
    if args.git_dir is not None:
        kwargs["git_dir"], kwargs["work_tree"] = args.git_dir, args.work_tree
    report = _call(_helper("verification").run_verification, kwargs)
    if report["ok"]:
        return report, 0 if report["artifact"]["reusable"] else 1
    return report, 2 if report["error"] == "unsafe-artifact-path" else 1


_OPERATIONS = {
    "stage_review": _stage_review, "group_findings": _group_findings,
    "check_evidence": _check_evidence, "prepare_close": _prepare_close,
    "catchup_probe": _catchup_probe, "verify": _verify,
    "probe_host": _probe_host, "run_guard": _run_guard, "diagnose": _diagnose,
    "request_job": _request_job, "bind_job": _bind_job, "close_child": _close_child,
    "resolve_roles": _resolve_roles, "record_session": _record_session,
}


def _run_operation(mode: str, args: argparse.Namespace) -> int:
    try:
        for flag in _INPUTS:
            path = getattr(args, flag)
            if path is not None and _in_live_state(path):
                raise _Usage(f"{path} is inside live autopilot state")
        report, code = _OPERATIONS[mode](args)
    except _Usage as error:
        print(f"autopilot: {error}", file=sys.stderr)
        return 2
    except _Refused as refused:
        print(json.dumps({"schema_version": 1, "ok": False, "error": str(refused)}))
        return 1
    if code:
        print(f"autopilot: {mode.replace('_', '-')} failed: {report.get('error', 'non-reusable result')}",
              file=sys.stderr)
    print(json.dumps(report))
    return code


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    rest = None
    if "--" in argv:
        split = argv.index("--")
        argv, rest = argv[:split], argv[split + 1:]
    parser = _parser()
    args = parser.parse_args(argv)
    mode = next(m for m in _MODES if getattr(args, m) not in (None, False))
    _check_companions(parser, args, mode, rest)
    if args.list_capabilities:
        print(json.dumps(_CAPABILITIES, separators=(",", ":")))
        return 0
    if args.controller_action is not None:
        print(json.dumps({"schema_version": 1, "ok": False, "error": "controller-required",
                          "operation": args.controller_action}))
        return 3
    if args.export_policy:
        if args.out is not None and _in_live_state(args.out):
            print(f"autopilot: {args.out} is inside live autopilot state", file=sys.stderr)
            return 2
        return _export_policy(args.out)
    if args.hook is not None:
        return _hook(args)
    args.argv = rest
    return _run_operation(mode, args)


def _export_policy(out: Path | None) -> int:
    try:
        policy_path = Path(__file__).resolve().parents[1] / "contracts" / "review-policy-v1.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict) or set(policy) != _ROOT_KEYS:
            raise ValueError("policy must contain exactly the review-policy-v1 root fields")
        if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
            raise ValueError("policy schema_version must be integer 1")
        pending = [policy]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, float):
                raise ValueError("policy numbers must be finite JSON integers")
        digest = policy["policy_digest"]
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("policy_digest must be a lowercase SHA-256 digest")
        payload = dict(policy)
        del payload["policy_digest"]
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True, allow_nan=False).encode("utf-8")
        if hashlib.sha256(serialized).hexdigest() != digest:
            raise ValueError("policy_digest does not match the packaged policy")
        output = (json.dumps(policy, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        if out is None:
            sys.stdout.buffer.write(output)
        else:
            _write_policy(out, output)
    except (OSError, ValueError) as error:
        print(f"autopilot: {error}", file=sys.stderr)
        return 1
    return 0


def _write_policy(out: Path, output: bytes) -> None:
    """Inspect the opened inode before truncating; aliases cannot redirect a
    write. Opens nonblocking so a FIFO with no reader refuses instead of
    hanging; refuses up front on a platform without O_NOFOLLOW rather than
    crashing on the attribute lookup."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError(f"{out}: platform has no O_NOFOLLOW support")
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(out, flags, 0o666)
    except OSError as error:
        if error.errno == errno.ENXIO:
            raise ValueError(f"{out} has no reader (FIFO)") from error
        raise
    with os.fdopen(fd, "wb") as sink:
        # `fd` is owned by `sink` from here on: any exception below, including
        # one from set_blocking itself, still closes it via this `with` block.
        os.set_blocking(sink.fileno(), True)
        info = os.fstat(sink.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"{out} must be a regular file with one hard link")
        os.ftruncate(sink.fileno(), 0)
        sink.write(output)


if __name__ == "__main__":
    raise SystemExit(main())
