"""Capture the approved single-order handoff and external-edit coexistence.

Called by run_matrix after probes. These records are compatibility evidence,
not per-rule eval records. Every step retains status, artifact bytes and hashes.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
from pathlib import Path

import run_claude as runner
import score

SPEC = ".kiro/specs/00001-greeting"
STEPS = (
    (
        "requirements",
        "kiro-ide",
        "Use specflow. Create requirements for intake 00001-greeting as a standard feature, requirements-first. The scope is one Python greet() function returning Hello and a unittest. Use .kiro/specs/00001-greeting. Draft requirements only.",
    ),
    (
        "design",
        "codex",
        "Use specflow. I approve the requirements for 00001-greeting. Record approval and draft its design, then stop.",
    ),
    (
        "tasks",
        "claude-code",
        "Use specflow. I approve the design. Record approval and draft tasks, then stop.",
    ),
    (
        "approve-tasks",
        "claude-code",
        "Use specflow. I approve the task plan. Record approval and stop before implementation.",
    ),
    (
        "edit-requirements",
        "claude-code",
        "Use specflow. Add this requirement to approved requirements: greet() returns Hello as a string. Record no new approvals; report the resulting stale gates and stop.",
    ),
    (
        "reapprove",
        "claude-code",
        "Use specflow. I approve the changed requirements and the existing design and tasks after checking their alignment with that requirement. Record all three approvals in order and stop.",
    ),
    (
        "implementation",
        "codex",
        "Use specflow. Implement the approved tasks for 00001-greeting, run their checks, and record actual Outcomes. Stop before completion verification.",
    ),
    (
        "verification",
        "kiro-ide",
        "Use specflow. Verify completion of 00001-greeting using the actual code and tests. Report gates, task state and remaining limitations.",
    ),
    (
        "external-edit",
        "kiro-ide",
        "Do not invoke specflow or change .specflow.json. Append this sentence to .kiro/specs/00001-greeting/requirements.md: External writer requires the greeting to end without a newline. This is an external artifact edit only.",
    ),
    (
        "resume",
        "codex",
        "Use specflow. Resume 00001-greeting after the external edit. Report stale approvals and preserve the edit. Do not approve, implement, or revert anything.",
    ),
)


def capture(workspace: Path, plugin: Path) -> dict:
    files = runner.snapshot(workspace)
    artifacts = {p: text for p, text in files.items() if p.startswith(SPEC + "/")}
    hashes = {}
    helper = plugin / "skills/spec-workflow/scripts/validate_spec.py"
    for name in ("requirements.md", "design.md", "tasks.md"):
        path = workspace / SPEC / name
        if path.is_file():
            result = runner.command(
                [runner.sys.executable, "-B", str(helper), "hash", str(path), "--json"],
                workspace,
            )
            if result.returncode:
                raise runner.HostError("artifact hash command failed")
            hashes[name] = json.loads(result.stdout)
    return {
        "status": runner.capture_status(workspace, plugin=plugin),
        "files": artifacts,
        "paths": sorted(artifacts),
        "hashes": hashes,
    }


def checks(rows: list[dict]) -> list[str]:
    failures = []
    by_step = {row["step"]: row for row in rows}
    if set(by_step) != {step for step, _, _ in STEPS}:
        failures.append("handoff did not finish all steps")
    for row in rows:
        if row.get("error") or row.get("status") is None:
            failures.append(row["step"] + ": unavailable evidence")
    before, after = by_step.get("external-edit", {}), by_step.get("resume", {})
    req = SPEC + "/requirements.md"
    state = SPEC + "/.specflow.json"
    previous = by_step.get("verification", {})
    if before.get("files", {}).get(state) != previous.get("files", {}).get(state):
        failures.append("external writer changed specflow state")
    if "External writer requires" not in before.get("files", {}).get(req, ""):
        failures.append("external edit missing")
    if before.get("files", {}).get(req) != after.get("files", {}).get(req):
        failures.append("resume changed the external edit")
    for step in ("edit-requirements", "resume"):
        specs = (by_step.get(step, {}).get("status") or {}).get("specs", [])
        entry = next(
            (spec for spec in specs if spec.get("spec") == "00001-greeting"), {}
        )
        stale = entry.get("artifacts", {})
        if any(
            stale.get(name) != "stale" for name in ("requirements", "design", "tasks")
        ):
            failures.append(step + ": required approvals were not stale")
    specs = (by_step.get("verification", {}).get("status") or {}).get("specs", [])
    entry = next((spec for spec in specs if spec.get("spec") == "00001-greeting"), {})
    if entry.get("phase") != "complete" or entry.get("nextTask") is not None:
        failures.append("verification did not reach completion")
    for row in rows:
        if row.get("instructions", {}).get("classification") != "clean":
            failures.append(row["step"] + ": instructions were not measured clean")
    for step in ("approve-tasks", "reapprove", "implementation", "verification"):
        specs = (by_step.get(step, {}).get("status") or {}).get("specs", [])
        entry = next(
            (spec for spec in specs if spec.get("spec") == "00001-greeting"), {}
        )
        if any(
            entry.get("artifacts", {}).get(name) != "approved"
            for name in ("requirements", "design", "tasks")
        ):
            failures.append(step + ": approved artifact state was not carried")
    for previous_step, next_step, names in (
        ("requirements", "design", ("requirements.md",)),
        ("design", "tasks", ("requirements.md", "design.md")),
        ("reapprove", "implementation", ("requirements.md", "design.md")),
        (
            "implementation",
            "verification",
            ("requirements.md", "design.md", "tasks.md"),
        ),
    ):
        for name in names:
            before_hash = (
                by_step.get(previous_step, {})
                .get("hashes", {})
                .get(name, {})
                .get("sha256")
            )
            after_hash = (
                by_step.get(next_step, {}).get("hashes", {}).get(name, {}).get("sha256")
            )
            if not before_hash or before_hash != after_hash:
                failures.append(
                    next_step
                    + ": canonical artifact changed across host handoff: "
                    + name
                )
    return failures


@score.deadline(runner.BATCH_TIMEOUT)
def execute(models: dict[str, str], proofs: Path, out: Path, registry: dict) -> dict:
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    rows = []
    with runner.external_batch(revision) as root, contextlib.ExitStack() as resources:
        workspace = root / "workspaces/handoff"
        workspace.mkdir()
        fixture = runner.FIXTURES / "workflow/intake-only"
        runner.write_files(workspace, runner.snapshot(fixture))
        runner.initialize_workspace(workspace)
        replacements = {
            str(workspace): "<workspace>",
            str(root): "<batch>",
            str(runner.ROOT): "<repository>",
            str(Path.home()): "<home>",
        }
        adapters = {}
        for step, host, prompt in STEPS:
            row = {"step": step, "host": host, "prompt": prompt}
            try:
                if host not in adapters:
                    adapter = registry[host][0](models[host])
                    adapter.plugin = root / "resources/specflow"
                    adapter.boundary = score.read_json(proofs / f"{host}.json")
                    adapter.preflight()
                    resources.enter_context(adapter.batch(workspace))
                    adapters[host] = adapter
                adapter = adapters[host]
                adapter.new_conversation()
                expected = runner.snapshot(workspace)
                reply, reads = adapter.turn(
                    prompt
                    if step == "external-edit"
                    else runner.workflow_prompt(prompt, adapter.plugin),
                    workspace,
                )
                runner.verify_plugin(adapter.plugin, revision)
                inventory = runner.classify_instructions(
                    adapter.instruction_observations,
                    complete=adapter.instruction_measurement == "measured",
                    workspace=workspace,
                    expected=expected,
                    plugin=adapter.plugin,
                    plugin_files=runner.snapshot(adapter.plugin),
                )
                row.update(capture(workspace, adapter.plugin))
                row.update(
                    reply=reply,
                    reads=reads,
                    model=adapter.model,
                    hostVersion=adapter.version,
                    instructions=inventory,
                    boundarySha256=score.evidence_digest(adapter.boundary),
                )
            except (
                OSError,
                ValueError,
                runner.HostError,
                subprocess.SubprocessError,
            ) as error:
                row["error"] = str(error)
            rows.append(runner.normalize(row, replacements))
            score.write_json(
                out,
                {"runtimeRevision": revision, "rows": rows, "failures": checks(rows)},
            )
            if row.get("error"):
                break
    result = {"runtimeRevision": revision, "rows": rows, "failures": checks(rows)}
    score.write_json(out, result)
    return result
