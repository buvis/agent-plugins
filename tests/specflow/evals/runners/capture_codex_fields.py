"""Developer-only diagnostic: capture two varying instruction fields, never evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from pathlib import Path

import run_codex
from run_codex import permission_text


def selected_fields(state: dict, normalize: Callable) -> dict:
    """Keep the two requested fields only, using the adapter's path normalization."""
    return {
        name: normalize(state.get(parent, {}).get(field))
        for name, parent, field in (
            ("permissions.instructions", "permissions", "instructions"),
            ("host_skills.body", "host_skills", "body"),
        )
    }


def render_only(model: str, out: Path) -> int:
    """Render two fresh eval profiles without sign-in, model calls or live evidence."""
    revision = (
        run_codex.score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    )
    samples = []
    for name in ("probe", "session"):
        with run_codex.runner.external_batch(revision) as batch:
            adapter = run_codex.Codex(model)
            adapter.plugin = batch / "resources/specflow"
            adapter.identify()
            adapter.home = batch / "control/codex-home"
            adapter.home.mkdir(mode=0o700)
            workspace = batch / "workspaces" / name
            workspace.mkdir(mode=0o700)
            run_codex.runner.initialize_workspace(workspace)
            (adapter.home / "specflow.config.toml").write_text(
                run_codex.eval_config(
                    workspace,
                    adapter.plugin,
                    adapter.git,
                    adapter.runtime,
                )
            )
            result = run_codex.runner.command(
                [
                    adapter.executable,
                    "--profile",
                    "specflow",
                    "debug",
                    "prompt-input",
                    "-c",
                    "model=" + json.dumps(model),
                ],
                workspace,
                adapter.environment(),
            )
            if result.returncode:
                raise run_codex.runner.HostError(
                    f"renderer stopped with exit {result.returncode}; no model was called"
                )
            items = json.loads(result.stdout)
            fragments = []
            for item in items:
                if item.get("role") == "developer":
                    for content in item.get("content", []):
                        fragments.extend(
                            re.findall(
                                r"<permissions instructions>.*?</permissions instructions>",
                                content.get("text", ""),
                                re.DOTALL,
                            )
                        )
            if not fragments:
                raise run_codex.runner.HostError(
                    "renderer supplied no permission fragment"
                )
            samples.append(
                {
                    "case": name,
                    "permissions.renderedText": adapter.effective_profile(
                        fragments, workspace
                    ),
                }
            )
    descriptor = os.open(
        out / "render-fields.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"diagnosticOnly": True, "samples": samples}, stream, indent=2)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("probe", "session", "render"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.model in {"auto", "default"}:
        parser.error("choose an explicit model")
    args.out.mkdir(parents=True, exist_ok=True)
    if args.phase == "render":
        return render_only(args.model, args.out)
    capture = args.out / f"{args.phase}-fields.json"
    # Refuse overwrites and links; these files contain instruction text.
    descriptor = os.open(capture, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    samples = []
    original = run_codex.instruction_channels
    original_launch = run_codex.Codex.launch
    active = []

    def launch(adapter: run_codex.Codex, prompt: str, workspace: Path) -> object:
        active[:] = [adapter, workspace]
        return original_launch(adapter, prompt, workspace)

    def observe(state: dict, normalize: Callable) -> dict:
        sample = selected_fields(state, normalize)
        # The snapshot stores an opaque hash here. Render with the same
        # private home/profile; no model request, login, or permission change.
        adapter, workspace = active
        rendered = run_codex.runner.command(
            [
                adapter.executable,
                "--profile",
                "specflow",
                "debug",
                "prompt-input",
                "-c",
                "model=" + json.dumps(adapter.model),
            ],
            workspace,
            adapter.environment(),
        )
        try:
            items = json.loads(rendered.stdout) if rendered.returncode == 0 else []
        except ValueError:
            items = []
        text = permission_text(items, state.get("permissions", {}).get("instructions"))
        sample["permissions.renderedHashVerified"] = text is not None
        sample["permissions.renderedText"] = normalize(text)
        samples.append(sample)
        return original(state, normalize)

    run_codex.instruction_channels = observe
    run_codex.Codex.launch = launch
    try:
        with run_codex.runner.interruption_signals():
            if args.phase == "probe":
                proof = run_codex.live_probe(args.model)
                proof_path = args.out / "codex-proof.json"
                with proof_path.open("x", encoding="utf-8") as stream:
                    json.dump(proof, stream, indent=2)
                return int(
                    not all(
                        proof["checks"].get(name, {}).get("passed") is True
                        for name in run_codex.score.RELEASE_BOUNDARY_CHECKS
                    )
                )
            return run_codex.runner.main(
                [
                    "status-summary",
                    "--model",
                    args.model,
                    "--boundary-proof",
                    str(args.out / "codex-proof.json"),
                    "--evals",
                    "tests/specflow/fixtures/results/self-check",
                    "--out",
                    str(args.out / "records"),
                ],
                adapter_type=run_codex.Codex,
            )
    finally:
        run_codex.instruction_channels = original
        run_codex.Codex.launch = original_launch
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"diagnosticOnly": True, "samples": samples}, stream, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
