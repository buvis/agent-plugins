"""Fake claude/codex binaries for probe-host.py live-run tests.

The fake logs how it was launched (with the session id it minted), runs every
PreToolUse hook command its registration surface names (claude: the
`--plugin-dir` manifest's `hooks` file; codex: `<-C dir>/.codex/hooks.json`) on
the push the prompt asks for, and pushes only when no hook denied.
FAKE_HOST_MODE bends that for reject cases: `ignore_deny` pushes anyway,
`no_push` never pushes, `escape` appends a trace line naming a foreign
plugin_root, `fail` exits 1 before doing anything, `hang` sleeps far past any
probe timeout, `same_session` reuses one session id for every launch,
`extra_line` appends one more honest trace line (the copy's own plugin_root) on
the control run, and `silent_refusal` skips the hooks on bound runs, writes an
honest trace line with no outcome and does not push, so the push is refused for
no recorded reason.
"""

from __future__ import annotations

import sys
from pathlib import Path

FAKE_STDOUT_MARK = "fake-host-stdout-7d2e91"
FAKE_HANG_SECONDS = 30
FAKE_HOST = r"""#!@PYTHON@
import json, os, re, subprocess, sys, time, uuid
from pathlib import Path
host, args, prompt = Path(sys.argv[0]).name, sys.argv[1:], sys.stdin.read()
mode = os.environ["FAKE_HOST_MODE"]
session = "5e55" * 8 if mode == "same_session" else uuid.uuid4().hex
with open(os.environ["FAKE_HOST_LOG"], "a") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "prompt": prompt, "home": os.environ.get("HOME"),
                          "trace": os.environ.get("AUTOPILOT_HOOK_TRACE"), "session": session}) + "\n")
if mode == "fail":
    sys.exit("IneligibleTierError: fake host refused")
if mode == "hang":
    time.sleep(@HANG@)
    sys.exit(0)
env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
if host == "claude":
    plugin, workdir = Path(args[args.index("--plugin-dir") + 1]), Path(os.getcwd())
    hooks = plugin / json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())["hooks"]
    env.update(CLAUDE_PLUGIN_ROOT=str(plugin), CLAUDE_CODE_SESSION_ID=session)
else:
    workdir = Path(args[args.index("-C") + 1])
    hooks = workdir / ".codex" / "hooks.json"
    env.update(CODEX_SESSION_ID=session)
def find(node, key):
    if isinstance(node, dict):
        return node[key] if key in node else next(
            (hit for hit in (find(v, key) for v in node.values()) if hit is not None), None)
    return None
def leaves(node):
    children = node.values() if isinstance(node, dict) else node if isinstance(node, list) else None
    return [node] if children is None else [leaf for child in children for leaf in leaves(child)]
def note(plugin_root, bound):
    with open(env["AUTOPILOT_HOOK_TRACE"], "a") as trace:
        trace.write(json.dumps({"host_id": host, "event": "PreToolUse", "session_id": session,
                                "plugin_root": plugin_root, "bound": bound,
                                "outcomes": []}) + "\n")
push = re.search(r"git push probe-remote HEAD:refs/heads/probe-[a-z0-9-]+", prompt).group(0)
control = push.endswith("probe-control")
silent = mode == "silent_refusal" and not control
honest_root = os.path.realpath(workdir.parent / "plugin")
payload = json.dumps({"session_id": session, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                      "tool_input": {"command": push}, "cwd": str(workdir)})
denied = False
for group in [] if silent else find(json.loads(hooks.read_text()), "PreToolUse") or []:
    if (group.get("matcher") or "*") not in ("*", "Bash") and not re.fullmatch(group["matcher"], "Bash"):
        continue
    for hook in group.get("hooks", []):
        done = subprocess.run(hook["command"], shell=True, cwd=workdir, env=env, input=payload,
                              capture_output=True, text=True)
        try:
            reply = json.loads(done.stdout or "null")
        except ValueError:
            reply = None
        denied |= done.returncode == 2 or bool({"deny", "block"} & set(map(str, leaves(reply))))
if silent:
    note(honest_root, True)
if mode == "escape":
    note(env["FAKE_FOREIGN_ROOT"], True)
if mode == "extra_line" and control:
    note(honest_root, False)
if mode == "ignore_deny" or (mode != "no_push" and not denied and not silent):
    subprocess.run(push.split(), cwd=workdir, check=True, capture_output=True)
print(json.dumps({"result": "@MARK@", "session_id": session}))
"""


def install_fake_hosts(bin_dir: Path) -> None:
    """Write executable fake `claude` and `codex` into `bin_dir`."""
    script = (
        FAKE_HOST.replace("@PYTHON@", sys.executable)
        .replace("@MARK@", FAKE_STDOUT_MARK)
        .replace("@HANG@", str(FAKE_HANG_SECONDS))
    )
    for name in ("claude", "codex"):
        fake = bin_dir / name
        fake.write_text(script, encoding="utf-8")
        fake.chmod(0o755)


def pre_tool_use_commands(hooks: object) -> list[str]:
    """Every hook command registered under a `PreToolUse` key, at any depth."""
    if isinstance(hooks, list):
        return [command for item in hooks for command in pre_tool_use_commands(item)]
    if not isinstance(hooks, dict):
        return []
    found = [hook.get("command", "") for group in hooks.get("PreToolUse", [])
             for hook in group.get("hooks", [])]
    return found + [command for key, value in hooks.items() if key != "PreToolUse"
                    for command in pre_tool_use_commands(value)]
