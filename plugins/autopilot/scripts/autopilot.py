#!/usr/bin/env python3
"""Expose the packaged review contracts without starting runtime services."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
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
    "controller-required-v1",
]
_MODES = (
    "list_capabilities", "export_policy", "stage_review", "group_findings",
    "check_evidence", "prepare_close", "catchup_probe", "verify",
    "controller_action",
)
_COMPANIONS = {
    "out": ("export_policy",),
    "expected_context": ("check_evidence",),
    "policy": ("check_evidence",),
    "project_root": ("catchup_probe", "verify"),
    "head_sha": ("verify",),
    "artifact": ("verify",),
    "log": ("verify",),
    "timeout": ("verify",),
}
_REQUIRED = {
    "check_evidence": ("expected_context",),
    "catchup_probe": ("project_root",),
    "verify": ("project_root", "head_sha", "artifact", "log"),
}
_INPUTS = ("stage_review", "group_findings", "check_evidence",
           "expected_context", "policy", "prepare_close")
_LIVE_STATE = ("docs", "dev", "project-management", "autopilot")


class _Usage(Exception):
    """A usage, input or path error: exit 2 with a stderr diagnostic."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--list-capabilities", action="store_true")
    modes.add_argument("--export-policy", action="store_true")
    for flag in ("--stage-review", "--group-findings", "--check-evidence",
                 "--prepare-close"):
        modes.add_argument(flag, type=Path)
    modes.add_argument("--catchup-probe", action="store_true")
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--controller-action")
    for flag in ("--out", "--expected-context", "--policy", "--project-root",
                 "--artifact", "--log"):
        parser.add_argument(flag, type=Path)
    parser.add_argument("--head-sha")
    parser.add_argument("--timeout", type=float)
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
        if any(parts[i:i + 4] == _LIVE_STATE for i in range(len(parts))):
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


def _verify(args: argparse.Namespace) -> tuple[dict, int]:
    kwargs = {
        "argv": args.argv, "project_root": args.project_root,
        "head_sha": args.head_sha, "artifact_path": args.artifact,
        "log_path": args.log,
    }
    if args.timeout is not None:
        kwargs["timeout"] = args.timeout
    report = _call(_helper("verification").run_verification, kwargs)
    if report["ok"]:
        return report, 0 if report["artifact"]["reusable"] else 1
    return report, 2 if report["error"] == "unsafe-artifact-path" else 1


_OPERATIONS = {
    "stage_review": _stage_review, "group_findings": _group_findings,
    "check_evidence": _check_evidence, "prepare_close": _prepare_close,
    "catchup_probe": _catchup_probe, "verify": _verify,
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
        return _export_policy(args.out)
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
            out.write_bytes(output)
    except (OSError, ValueError) as error:
        print(f"autopilot: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
