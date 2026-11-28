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
# Synthetic developer answers. Unstated, each became a (guess) or an open
# question that no generic approval could accept (live run 2026-11-24).
CHOICES = (
    " These are my confirmed choices, not guesses or open questions:"
    " greet() takes no arguments; the function lives in greeting.py and its test"
    " in test_greeting.py, both at the repository root, and I accept those file"
    " names; the code uses only the Python standard library; the test runs with"
    " python3 -m unittest from the repository root."
)
ACCEPT = (
    CHOICES + " If a guess, unresolved question or open decision about one of"
    " those choices remains in an upstream artifact, I accept each such marker by"
    " name and you record it as an accepted marker with the approval."
)
# A drafted Verify command with a bug of its own left its task unchecked, so
# no host could reach completion (live run 2026-11-28).
VERIFY = (
    " In each task, the Verify line uses only python3 -m unittest commands or a"
    " python3 -c command that imports greeting and asserts on greet(). Write no"
    " other verification command and no task that only verifies other tasks."
)
STEPS = (
    (
        "requirements",
        "kiro-ide",
        "Use specflow. Create requirements for intake 00001-greeting as a standard feature, requirements-first. The scope is one Python greet() function returning Hello and a unittest. Use .kiro/specs/00001-greeting. Draft requirements only."
        + CHOICES,
    ),
    (
        "design",
        "codex",
        "Use specflow. I approve the requirements for 00001-greeting. Record approval and draft its design, then stop."
        + CHOICES,
    ),
    (
        "tasks",
        "claude-code",
        "Use specflow. I approve the design. Record approval and draft tasks, then stop."
        + ACCEPT
        + VERIFY,
    ),
    (
        "approve-tasks",
        "claude-code",
        "Use specflow. I approve the task plan. Record approval and stop before implementation."
        + ACCEPT,
    ),
    (
        "edit-requirements",
        "claude-code",
        "Use specflow. Change the approved requirements: in the existing acceptance criterion for the greet() return value, state that the returned value has type str. Add no new requirement and no new requirement ID. Record no new approvals; report the resulting stale gates and stop.",
    ),
    (
        "reapprove",
        "claude-code",
        "Use specflow. I approve the changed requirements and the existing design and tasks after checking their alignment with that change. Record all three approvals in order and stop."
        + ACCEPT,
    ),
    (
        "implementation",
        "codex",
        "Use specflow. Implement the approved tasks for 00001-greeting, run their checks, and record actual Outcomes. Stop before completion verification.",
    ),
    (
        "verification",
        "kiro-ide",
        "Use specflow. Verify completion of 00001-greeting using the actual code and tests: run the completion checks and tick each completion criterion that holds. Then report gates, task state and remaining limitations.",
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


APPROVALS = ("tasks", "approve-tasks", "reapprove")


def step_prompt(
    step: str, prompt: str, workspace: Path, plugin: Path = score.PLUGIN
) -> str:
    """Before an approval, accept every open upstream marker by its exact line.

    A host may write an open question no fixed request predicts (live run
    2026-11-25), and an approval needs each marker named. The lines come from
    the helper's status, plus those already accepted, so that a rewritten
    approval keeps them. This scripted developer accepts all of them: the
    handoff measures state carried across hosts, not marker judgment.
    """
    if step not in APPROVALS:
        return prompt
    status = runner.capture_status(workspace, plugin=plugin) or {}
    lines = [
        blocker.get("reference")
        for spec in status.get("specs", [])
        if spec.get("spec") == "00001-greeting"
        for blocker in spec.get("blockers", [])
        if " marker not accepted for the " in str(blocker.get("reason"))
    ]
    try:
        state = json.loads((workspace / SPEC / ".specflow.json").read_text())
        records = state["artifacts"].values()
        lines += [m["line"] for r in records for m in r.get("acceptedMarkers", [])]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass  # no readable state: only the helper's blockers are named
    lines = list(dict.fromkeys(line for line in lines if isinstance(line, str)))
    if not lines:
        return prompt
    return (
        prompt + " I accept each of these open markers by name, as it is written, and"
        " you record each as an accepted marker with every approval it blocks: "
        + " | ".join(lines)
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
                prompt = row["prompt"] = step_prompt(
                    step, prompt, workspace, adapter.plugin
                )
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
