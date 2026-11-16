#!/usr/bin/env python3
"""Generates per-host compatibility bundles from contracts/hosts.json
(schema_version 2) and each adapter's own declared-and-implemented
capability set, gated through hosts.adapter() so an unknown host_id raises
before any module is imported.

Writes plugins/autopilot/compatibility/<host_id>.json for every host
declared in the contract, and plugins/autopilot/compatibility/<host_id>/hooks.json
for every host whose contract declaration carries a non-null registration.
The tool never probes a live host, so the bundles are identical on every
machine. A declared capability set that does not equal the adapter's own
IMPLEMENTED_CAPABILITIES aborts the build with a non-zero exit and leaves
no file behind.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "plugins" / "autopilot" / "scripts"),
)

hosts = importlib.import_module("hosts")
guards = importlib.import_module("guards")

ALL_DUTIES = tuple(duty.value for duty in guards.GuardDuty)
_HOOK_COMMAND = 'python3 "{root}/scripts/autopilot.py" --hook {host_id} --event {event}'


def _implemented(host_id: str) -> frozenset[str]:
    """The adapter's own IMPLEMENTED_CAPABILITIES - a code fact, read without
    probing, so the generated bundle cannot depend on this machine. Resolved
    through hosts.adapter() so an unknown host_id raises before any import."""
    return hosts.adapter(host_id).IMPLEMENTED_CAPABILITIES


def _synthetic_payload(event: str, matcher: str | None) -> dict:
    """A deterministic payload shaped to trip exactly the duty calls a real
    hook of this event/matcher would make, so duty coverage is a code fact
    derived from translate_hook, never a hand-copied table."""
    payload: dict = {"cwd": "/tmp", "session_id": "s-1"}
    if event not in ("PreToolUse", "PostToolUse"):
        return payload
    tool_name = matcher.split("|")[0] if matcher else None
    payload["tool_name"] = tool_name
    if tool_name == "Bash":
        payload["tool_input"] = {"command": "git push origin main"}
    elif tool_name == "apply_patch":
        payload["tool_input"] = {"patch": "*** Add File: a.txt\n+x\n"}
    elif tool_name == "Skill":
        payload["tool_input"] = {"skill": "autopilot:work"}
    elif tool_name == "Agent":
        payload["tool_input"] = {"prompt": "dispatch autopilot:work"}
    else:
        payload["tool_input"] = {"file_path": "/tmp/a.txt"}
    return payload


def _covered_duties(host_id: str) -> set[str]:
    """The duty names some registration of `host_id` maps to, discovered by
    feeding each of its HOOK_REGISTRATIONS a synthetic payload through its
    own translate_hook - never a hardcoded per-host table."""
    module = hosts.adapter(host_id)
    registrations = getattr(module, "HOOK_REGISTRATIONS", ())
    found: set[str] = set()
    for registration in registrations:
        payload = _synthetic_payload(registration.event, registration.matcher)
        for duty_call in module.translate_hook(registration.event, payload):
            found.add(duty_call.duty.value)
    return found


def _duty_coverage(host_id: str, declaration: dict) -> dict[str, str]:
    registration = declaration.get("registration")
    if registration is None:
        reason = declaration.get("blockers", {}).get("interception")
        return {duty: f"blocked:{reason}" for duty in ALL_DUTIES}
    found = _covered_duties(host_id)
    return {duty: ("intercepted" if duty in found else "not_applicable_on_host") for duty in ALL_DUTIES}


def _validate(host_id: str, declaration: dict) -> str | None:
    """The first violation of the §3 invariants for `host_id`, or None."""
    declared = set(declaration["capabilities"])
    implemented = _implemented(host_id)
    overclaimed = sorted(declared - implemented)
    if overclaimed:
        return f"host {host_id!r}: declared capability {overclaimed[0]!r} is unimplemented"
    underclaimed = sorted(implemented - declared)
    if underclaimed:
        return f"host {host_id!r}: implemented capability {underclaimed[0]!r} is undeclared"
    module = hosts.adapter(host_id)
    if declaration.get("session_env_var") != module.SESSION_ENV_VAR:
        return f"host {host_id!r}: session_env_var does not match the adapter's SESSION_ENV_VAR"
    has_registration = declaration.get("registration") is not None
    if has_registration != ("interception" in declared):
        return f"host {host_id!r}: registration must be non-null iff interception is declared"
    for capability, reason in declaration.get("blockers", {}).items():
        if capability in declared:
            continue
        if not reason:
            return f"host {host_id!r}: blocker for {capability!r} has no reason"
    return None


def _bundle(host_id: str, declaration: dict) -> dict:
    declared = sorted(declaration["capabilities"])
    return {
        "schema_version": 2,
        "host_id": host_id,
        "capabilities": declared,
        "probe_kind": "static",
        "certified": False,
        "registration": declaration.get("registration"),
        "duty_coverage": _duty_coverage(host_id, declaration),
        "blockers": declaration.get("blockers", {}),
    }


def _hooks_asset(host_id: str, declaration: dict) -> dict | None:
    registration = declaration.get("registration")
    if registration is None:
        return None
    module = hosts.adapter(host_id)
    events: dict[str, list[dict]] = {}
    for reg in module.HOOK_REGISTRATIONS:
        entry: dict = {}
        if reg.matcher is not None:
            entry["matcher"] = reg.matcher
        entry["hooks"] = [
            {
                "type": "command",
                "command": _HOOK_COMMAND.format(
                    root=module.PLUGIN_ROOT_EXPR, host_id=host_id, event=reg.event
                ),
                "timeout": reg.timeout,
            }
        ]
        events.setdefault(reg.event, []).append(entry)
    return {"hooks": events}


def _planned_files(contract: dict, compatibility_dir: Path) -> dict[Path, dict]:
    planned: dict[Path, dict] = {}
    for host_id, declaration in contract["hosts"].items():
        planned[compatibility_dir / f"{host_id}.json"] = _bundle(host_id, declaration)
        hooks = _hooks_asset(host_id, declaration)
        if hooks is not None:
            asset_path = compatibility_dir.parent / declaration["registration"]["asset"]
            planned[asset_path] = hooks
    return planned


def _existing_files(compatibility_dir: Path) -> set[Path]:
    if not compatibility_dir.is_dir():
        return set()
    found = {p for p in compatibility_dir.glob("*.json") if p.is_file()}
    for host_dir in compatibility_dir.iterdir():
        if host_dir.is_dir():
            hooks_path = host_dir / "hooks.json"
            if hooks_path.is_file():
                found.add(hooks_path)
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    contract_path = project_root / "plugins" / "autopilot" / "contracts" / "hosts.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    for host_id, declaration in contract["hosts"].items():
        violation = _validate(host_id, declaration)
        if violation is not None:
            print(violation, file=sys.stderr)
            sys.exit(1)

    compatibility_dir = project_root / "plugins" / "autopilot" / "compatibility"
    planned = _planned_files(contract, compatibility_dir)
    existing = _existing_files(compatibility_dir)

    if args.check:
        for path in sorted(planned):
            expected = json.dumps(planned[path], indent=2) + "\n"
            if not path.is_file():
                print(f"missing: {path}", file=sys.stderr)
                sys.exit(1)
            if path.read_text(encoding="utf-8") != expected:
                print(f"differs: {path}", file=sys.stderr)
                sys.exit(1)
        for path in sorted(existing - set(planned)):
            print(f"extra: {path}", file=sys.stderr)
            sys.exit(1)
        return

    for path in existing - set(planned):
        path.unlink()

    for path, obj in planned.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(path)


if __name__ == "__main__":
    main()
