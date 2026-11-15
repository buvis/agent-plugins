"""Developer-only diagnostic: capture two varying instruction fields, never evidence."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from pathlib import Path

import run_codex


def selected_fields(state: dict, normalize: Callable) -> dict:
    """Keep the two requested fields only, using the adapter's path normalization."""
    return {
        name: normalize(state.get(parent, {}).get(field))
        for name, parent, field in (
            ("permissions.instructions", "permissions", "instructions"),
            ("host_skills.body", "host_skills", "body"),
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("probe", "session"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.model in {"auto", "default"}:
        parser.error("choose an explicit model")
    args.out.mkdir(parents=True, exist_ok=True)
    capture = args.out / f"{args.phase}-fields.json"
    # Refuse overwrites and links; these files contain instruction text.
    descriptor = os.open(capture, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    samples = []
    original = run_codex.instruction_channels

    def observe(state: dict, normalize: Callable) -> dict:
        samples.append(selected_fields(state, normalize))
        return original(state, normalize)

    run_codex.instruction_channels = observe
    try:
        with run_codex.runner.interruption_signals():
            if args.phase == "probe":
                proof = run_codex.live_probe(args.model)
                proof_path = args.out / "codex-proof.json"
                with proof_path.open("x", encoding="utf-8") as stream:
                    json.dump(proof, stream, indent=2)
                return int(not all(
                    proof["checks"].get(name, {}).get("passed") is True
                    for name in run_codex.score.RELEASE_BOUNDARY_CHECKS
                ))
            return run_codex.runner.main([
                "status-summary", "--model", args.model,
                "--boundary-proof", str(args.out / "codex-proof.json"),
                "--evals", "tests/specflow/fixtures/results/self-check",
                "--out", str(args.out / "records"),
            ], adapter_type=run_codex.Codex)
    finally:
        run_codex.instruction_channels = original
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"diagnosticOnly": True, "samples": samples}, stream, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
