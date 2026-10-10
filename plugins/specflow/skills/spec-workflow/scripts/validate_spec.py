#!/usr/bin/env python3
"""specflow helper: status, validation, hashes, code baseline, and reconciliation.

Run from the repository root. Exit codes: 0 success, 1 validation failure,
2 state error (malformed or unsupported state, a refused configuration, a write
conflict, a failed git call, an unreadable artifact), 3 usage error. Only `reconcile` writes, and only derived facts into
a spec's .specflow.json; nothing here records an approval.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from specflow_helper import WORKFLOW_VERSION
from specflow_helper.canonical import sha256_canonical, sha256_raw
from specflow_helper.checks import GitError, validate
from specflow_helper.config import ConfigError, load_config
from specflow_helper.drift import code_baseline
from specflow_helper.numbers import next_number
from specflow_helper.reconcile import ConflictError, reconcile
from specflow_helper.state import PHASES, StateError
from specflow_helper.status import status

OK, FAILED, STATE_ERROR, USAGE = 0, 1, 2, 3


class UsageError(Exception):
    """Arguments the command cannot run with."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def git(repo: Path, *args: str) -> str | None:
    """git's output, or None when git is missing or the call fails."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def repo_root() -> Path:
    """The git top level when there is one, else the working directory."""
    top = git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(top) if top else Path.cwd()


def folder(value: str) -> Path:
    path = Path(value).resolve()
    if not path.is_dir():
        raise UsageError(f"{value}: no such folder")
    return path


def emit(value: object, as_json: bool, text: str) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False) if as_json else text)


def status_line(spec: dict) -> str:
    gates = ", ".join(f"{gate} {value}" for gate, value in spec["gates"].items())
    task = spec["nextTask"]
    upcoming = f"; next {task['id'] or task['title']}" if task else ""
    return f"{spec['spec']}: {spec['phase']}; gates {gates}{upcoming}"


def run_status(args: argparse.Namespace, repo: Path) -> int:
    dirs = [folder(args.spec_dir)] if args.spec_dir else []
    document = status(repo, dirs)
    lines = [status_line(spec) for spec in document["specs"]]
    lines += [
        f"problem: {p['rule']}: {p['message']} Fix: {p['fix']}"
        for p in document["problems"]
    ]
    lines += [f"intake: {name}" for name in document["intake"]]
    emit(document, args.json, "\n".join(lines))
    invalid = any(spec["state"] == "invalid" for spec in document["specs"])
    return FAILED if document["problems"] or invalid else OK


def run_validate(args: argparse.Namespace, repo: Path) -> int:
    findings = validate(repo, folder(args.spec_dir), args.phase)
    errors = [f for f in findings if f["level"] == "error"]
    code = FAILED if errors else OK
    if any(f["rule"] == "state-valid" for f in errors):
        code = STATE_ERROR
    lines = [
        f"{f['level']}: {f['file']}: {f['rule']}: {f['message']} Fix: {f['fix']}"
        for f in findings
    ]
    emit(
        {"exitCode": code, "findings": findings},
        args.json,
        "\n".join(lines) or "valid",
    )
    return code


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_hash(args: argparse.Namespace, repo: Path) -> int:
    path = Path(args.file)
    if not path.is_file():
        raise UsageError(f"{args.file}: no such file")
    if args.raw:
        print(sha256_raw(path))
        return OK
    digest = sha256_canonical(path)
    if not args.json:
        print(digest)
        return OK
    record = {"sha256": digest, "approvedAt": now()}
    commit = git(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    if commit:
        record["approvedCommit"] = commit
    record["workflowVersion"] = WORKFLOW_VERSION
    emit(record, True, "")
    return OK


def run_code_baseline(args: argparse.Namespace, repo: Path) -> int:
    folder(args.spec_dir)
    if git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        value = {"status": "not_checked", "reason": "not a Git repository"}
    else:
        value = code_baseline(repo, args.paths)
    emit(value, True, "")
    return OK


def run_reconcile(args: argparse.Namespace, repo: Path) -> int:
    result = reconcile(folder(args.spec_dir), dry_run=args.dry_run)
    verb = "would set" if args.dry_run else "set"
    lines = [f"{result['spec']}: phase {result['phase']}"]
    lines += [
        f"{verb} {c['artifact']}.{c['field']}: {c['from']} -> {c['to']}"
        for c in result["changes"]
    ]
    lines += [
        f"needs the developer: {a['artifact']} ({a['path']}): {a['reason']}"
        for a in result["ambiguous"]
    ]
    emit(result, args.json, "\n".join(lines))
    return OK


def run_next_number(args: argparse.Namespace, repo: Path) -> int:
    print(next_number(repo, load_config(repo)))
    return OK


def parser() -> Parser:
    top = Parser(prog="validate_spec.py", description=__doc__.splitlines()[0])
    commands = top.add_subparsers(dest="command", required=True, parser_class=Parser)
    p = commands.add_parser("status", help="status of one spec, or of every spec")
    p.add_argument("spec_dir", nargs="?")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=run_status)
    p = commands.add_parser("validate", help="run the checks of a phase")
    p.add_argument("spec_dir")
    p.add_argument("--phase", choices=PHASES)
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=run_validate)
    p = commands.add_parser("hash", help="canonical (default) or raw SHA-256 of a file")
    p.add_argument("file")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--raw", action="store_true")
    mode.add_argument("--json", action="store_true")
    p.set_defaults(run=run_hash)
    p = commands.add_parser(
        "code-baseline",
        help="hashes of the design's placement files",
    )
    p.add_argument("spec_dir")
    p.add_argument("--paths", nargs="+", required=True)
    p.set_defaults(run=run_code_baseline)
    p = commands.add_parser("reconcile", help="refresh derived hashes and statuses")
    p.add_argument("spec_dir")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=run_reconcile)
    p = commands.add_parser("next-number", help="the next free spec number; read-only")
    p.set_defaults(run=run_next_number)
    return top


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        repo = repo_root()
        load_config(repo)
        return args.run(args, repo)
    except UsageError as problem:
        print(f"usage error: {problem}", file=sys.stderr)
        return USAGE
    except ConfigError as problem:
        print(f"configuration error: {problem}", file=sys.stderr)
        return STATE_ERROR
    except (StateError, ConflictError, GitError) as problem:
        print(f"state error: {problem}", file=sys.stderr)
        return STATE_ERROR
    except (OSError, UnicodeDecodeError) as problem:
        print(f"state error: cannot read: {problem}", file=sys.stderr)
        return STATE_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
