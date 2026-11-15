"""§8 hook entry: binding discovery, duty evaluation and the CLI hook path.

Dispatches duty calls an adapter's `translate_hook` names to `guards.run_guard`,
merges in controller facts for bound, controller-keyed pure duties, and renders
the reply through the adapter's own `render_hook_reply`. Writes an opt-in trace
line; never records tool_input, commands or contexts in the trace.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import guards
import hosts
from guards import GuardDuty, GuardOutcome
from hosts import NativeSession
from jobs import ControllerSeam
from log_sink_refusal import _pinned_parent_fd

NEUTRAL_EVENTS = {
    "PreToolUse": "pre_tool",
    "PostToolUse": "post_tool",
    "Stop": "stop",
    "SessionStart": "session_start",
}
MAX_HOOK_INPUT_BYTES = 1048576
MAX_TRACE_BYTES = 1048576
TRACE_ENV = "AUTOPILOT_HOOK_TRACE"
BINDING_MARKER = (".autopilot", "controller")

_STATEFUL_DUTIES = frozenset(
    {GuardDuty.CUSTODY_PUSH, GuardDuty.STATE_INTEGRITY, GuardDuty.REVIEW_COMPLETENESS, GuardDuty.LIVE_JOB}
)
_FACTS_SCHEMA: dict[GuardDuty, dict[str, type]] = {
    GuardDuty.POST_HANDOFF: {"leave_recorded": bool, "leave_session": str},
    GuardDuty.DEPARTURE: {
        "leave_row_written": bool,
        "last_store_write_at": int,
        "leave_row_at": int,
    },
    GuardDuty.CONTEXT_REINJECTION: {"contract_card_present": bool, "contract_card_body": str},
}
_MAX_CARD_BODY_BYTES = 65536


@dataclass(frozen=True)
class HookRegistration:
    event: str
    matcher: str | None
    timeout: int


@dataclass(frozen=True)
class DutyCall:
    duty: GuardDuty
    context: Mapping[str, object]


@dataclass(frozen=True)
class HookDecision:
    host_id: str
    event: str
    session: NativeSession | None
    project_root: str
    bound: bool
    outcomes: tuple[GuardOutcome, ...]
    skipped: tuple[tuple[str, str], ...]
    allowed: bool
    additional_context: str | None


@dataclass(frozen=True)
class HookReply:
    stdout: str
    exit_code: int


def find_binding(cwd: Path) -> Path | None:
    """The nearest ancestor of `cwd` (`cwd` included) holding a real
    `.autopilot/controller` directory, never crossing above the first
    ancestor that itself holds a `.git` entry."""
    current = cwd
    while True:
        candidate = current
        for part in BINDING_MARKER:
            candidate = candidate / part
        try:
            found = stat.S_ISDIR(os.lstat(candidate).st_mode)
        except OSError:
            found = False
        if found:
            return current
        if (current / ".git").exists():
            return None
        if current.parent == current:
            return None
        current = current.parent


def _validate_facts(duty: GuardDuty, facts: object) -> dict | None:
    schema = _FACTS_SCHEMA.get(duty)
    if schema is None:
        return {}
    if not isinstance(facts, dict) or set(facts) != set(schema):
        return None
    for key, kind in schema.items():
        if not isinstance(facts[key], kind):
            return None
    if duty is GuardDuty.CONTEXT_REINJECTION:
        body = facts["contract_card_body"]
        if len(body.encode("utf-8")) > _MAX_CARD_BODY_BYTES:
            return None
    return dict(facts)


def _session_dict(session: NativeSession | None) -> dict | None:
    if session is None:
        return None
    return {"host_id": session.host_id, "session_id": session.session_id, "source": session.source}


def evaluate_hook(
    host_id: str,
    event: str,
    payload: Mapping[str, object],
    *,
    env: Mapping[str, str],
    seam: ControllerSeam | None,
) -> HookDecision:
    adapter = hosts.adapter(host_id)
    duty_calls = adapter.translate_hook(event, payload)
    session = hosts.current_session(host_id, env)
    cwd_value = payload.get("cwd")
    cwd = Path(cwd_value) if isinstance(cwd_value, str) else Path(".")
    binding = find_binding(cwd)
    bound = binding is not None
    project_root = str(binding) if bound else str(cwd)

    outcomes: list[GuardOutcome] = []
    skipped: list[tuple[str, str]] = []
    additional_context: str | None = None

    for call in duty_calls:
        duty = call.duty
        context = dict(call.context)
        controller_keyed = duty in _STATEFUL_DUTIES or duty in _FACTS_SCHEMA

        if not bound and controller_keyed:
            skipped.append((duty.value, "unbound"))
            continue

        if bound and controller_keyed:
            if seam is None:
                outcomes.append(
                    GuardOutcome(
                        duty=duty, allowed=False, reason="missing_controller_seam", stateful=True
                    )
                )
                continue
            if duty in _FACTS_SCHEMA:
                try:
                    facts = seam.read_facts(duty.value, _session_dict(session), project_root)
                except Exception:
                    facts = None
                validated = _validate_facts(duty, facts)
                if validated is None:
                    outcomes.append(
                        GuardOutcome(
                            duty=duty,
                            allowed=False,
                            reason="malformed_controller_facts",
                            stateful=True,
                        )
                    )
                    continue
                context.update(validated)

        outcome = guards.run_guard(duty, context, seam=seam)
        outcomes.append(outcome)
        if duty is GuardDuty.CONTEXT_REINJECTION and outcome.allowed:
            additional_context = context.get("contract_card_body")

    return HookDecision(
        host_id=host_id,
        event=event,
        session=session,
        project_root=project_root,
        bound=bound,
        outcomes=tuple(outcomes),
        skipped=tuple(skipped),
        allowed=all(outcome.allowed for outcome in outcomes),
        additional_context=additional_context,
    )


def _invalid_input_reply(event: str) -> HookReply:
    if event == "PreToolUse":
        stdout = json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "hook_input_invalid",
                }
            }
        )
    else:
        stdout = json.dumps({"systemMessage": "autopilot: hook_input_invalid"})
    return HookReply(stdout=stdout, exit_code=0)


def _parse_hook_input(stdin: bytes) -> dict | None:
    if len(stdin) > MAX_HOOK_INPUT_BYTES:
        return None
    try:
        payload = json.loads(stdin.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or "cwd" not in payload:
        return None
    return payload


def run_hook(host_id: str, event: str, stdin: bytes, *, env: Mapping[str, str]) -> HookReply:
    adapter = hosts.adapter(host_id)
    registrations = getattr(adapter, "HOOK_REGISTRATIONS", {})
    if event not in registrations:
        raise SystemExit(2)

    payload = _parse_hook_input(stdin)
    if payload is None:
        return _invalid_input_reply(event)

    decision = evaluate_hook(host_id, event, payload, env=env, seam=None)
    stop_active = bool(payload.get("stop_hook_active"))
    reply = adapter.render_hook_reply(event, decision, stop_active=stop_active)
    _write_trace(decision, env)
    return reply


def _write_trace(decision: HookDecision, env: Mapping[str, str]) -> None:
    trace_path = env.get(TRACE_ENV)
    if not trace_path:
        return
    project_root = Path(decision.project_root)
    candidate = Path(trace_path)
    try:
        allowed_dir = (project_root / "docs" / "dev" / "tmp" / "autopilot").resolve()
        resolved = candidate.resolve() if candidate.is_absolute() else (project_root / candidate).resolve()
        if not resolved.is_relative_to(allowed_dir):
            print("autopilot: trace write refused: outside docs/dev/tmp/autopilot", file=sys.stderr)
            return
    except OSError as exc:
        print(f"autopilot: trace write refused: {exc}", file=sys.stderr)
        return

    line = {
        "ts": time.time(),
        "host_id": decision.host_id,
        "event": decision.event,
        "session_id": decision.session.session_id if decision.session else None,
        "session_source": decision.session.source if decision.session else None,
        "plugin_root": str(Path(__file__).resolve().parents[1]),
        "bound": decision.bound,
        "outcomes": [
            {"duty": outcome.duty.value, "allowed": outcome.allowed, "reason": outcome.reason}
            for outcome in decision.outcomes
        ],
    }
    try:
        parent_fd = _pinned_parent_fd(resolved.parent, project_root)
        try:
            fd = os.open(
                resolved.name,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
                0o666,
                dir_fd=parent_fd,
            )
        finally:
            os.close(parent_fd)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                print("autopilot: trace write refused: not a plain regular file", file=sys.stderr)
                return
            if info.st_size >= MAX_TRACE_BYTES:
                return
            os.write(fd, (json.dumps(line) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
    except OSError as exc:
        print(f"autopilot: trace write refused: {exc}", file=sys.stderr)
