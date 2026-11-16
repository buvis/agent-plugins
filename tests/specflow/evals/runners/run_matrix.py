"""Probe each host, run the approved matrix, and retain one failure summary.

Run only in a developer terminal outside run-agent. Authentication remains owned
by each existing adapter; Codex can request a fresh login for each isolated batch.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

import run_claude as runner
import run_codex
import run_kiro
import score

SMOKE = (
    "status-summary",
    "concurrent-edit",
    "conversion-calcard",
    "intake-all-supplied",
    "requirements-review",
    "design-review",
    "tasks-planning",
    "implementation-failed-check",
    "completion-success",
)
HOSTS = {
    "claude-code": (runner.Claude, runner.boundary_probe, "claude-haiku-5-5"),
    "codex": (run_codex.Codex, run_codex.live_probe, "gpt-6.1-sol"),
    "kiro-ide": (run_kiro.Kiro, run_kiro.live_probe, "claude-haiku-5.5"),
}


def eval_directory(name: str) -> Path:
    extra = score.EVALS / "scenarios" / name
    return extra if extra.is_dir() else score.EVALS


def groups(host: str, directory: Path = runner.SESSIONS) -> list[str]:
    names = (
        sorted(p.stem for p in directory.glob("*.json"))
        if host == "claude-code"
        else SMOKE
    )
    roots = []
    for name in names:
        root = runner.sessions_for(name, directory)[0][1]["name"]
        if root not in roots:
            roots.append(root)
    return roots


def execute_host(
    host: str,
    model: str,
    out: Path,
    proofs: Path,
    *,
    run: Callable = runner.run_batch,
    registry: dict = HOSTS,
    selected: list[str] | None = None,
) -> list[dict]:
    adapter_type, probe, _ = registry[host]
    names = groups(host) if selected is None else selected
    rows = []
    try:
        proof = probe(model)
        score.write_json(proofs / f"{host}.json", proof)
        passed = all(
            proof.get("checks", {}).get(k, {}).get("passed") is True
            for k in score.RELEASE_BOUNDARY_CHECKS
        )
    except (OSError, ValueError, runner.HostError) as error:
        rows.append({"host": host, "session": "probe", "code": 2, "reason": str(error)})
        passed = False
    if not passed:
        return rows + [
            {
                "host": host,
                "session": n,
                "code": 2,
                "reason": "boundary probe failed; no session launched",
            }
            for n in names
        ]
    for name in names:
        adapter = adapter_type(model)
        adapter.boundary = proof
        try:
            code = run(adapter, name, out, eval_dir=eval_directory(name))
            rows.append({"host": host, "session": name, "code": code})
        except (OSError, ValueError, runner.HostError) as error:
            rows.append(
                {"host": host, "session": name, "code": 2, "reason": str(error)}
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=score.EVALS / "results")
    parser.add_argument(
        "--proofs", type=Path, default=runner.ROOT / "docs/dev/tmp/specflow/proofs"
    )
    parser.add_argument("--dry-run", action="store_true")
    for host, (_, _, model) in HOSTS.items():
        parser.add_argument(f"--{host}-model", default=model)
    args = parser.parse_args(argv)
    if args.dry_run:
        print(json.dumps({h: groups(h) for h in HOSTS}, indent=2))
        return 0
    if not sys.stdin.isatty():
        parser.error("run in a developer terminal for independent Codex sign-in")
    # Refuse mutable or uncommitted inputs before any paid probe.
    paths = ["plugins/specflow", "tests/specflow/evals", "tests/specflow/fixtures"]
    dirty = score.git("status", "--porcelain", "--", *paths).decode()
    if dirty.strip():
        parser.error(
            "commit frozen package, runner, session, eval and fixture inputs first"
        )
    args.proofs.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        with runner.interruption_signals():
            for host in HOSTS:
                model = getattr(args, host.replace("-", "_") + "_model")
                if model in {"auto", "default"}:
                    parser.error("choose explicit models")
                rows.extend(execute_host(host, model, args.out, args.proofs))
    finally:
        score.write_json(
            args.proofs / "matrix-summary.json",
            {"commit": score.git("rev-parse", "HEAD").decode().strip(), "rows": rows},
        )
        print("HOST          SESSION                                  EXIT")
        for row in rows:
            print(f"{row['host']:13} {row['session']:40} {row['code']}")
        print(
            "Exit 1 can mean pending human review. No row alone certifies release evidence."
        )
    return max((r["code"] for r in rows), default=2)


if __name__ == "__main__":
    raise SystemExit(main())
