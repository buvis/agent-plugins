"""Fake claude/codex/gemini binaries for probe-host.py live-run tests.

The fake logs how it was launched (with the session id it minted, the
`AUTOPILOT_PLUGIN_ROOT` it was handed and the record command its prompt
names), runs every PreToolUse hook command its registration surface names
(claude: the `--plugin-dir` manifest's `hooks` file; codex:
`<-C dir>/.codex/hooks.json`) on the push the prompt asks for, and pushes only
when no hook denied. `claude`, the delegation-capable host, also fires the
`Agent` PreToolUse hook twice on a bound run: once as a parent dispatch and
once as a nested dispatch whose payload carries an `agent_id`. `gemini` has no
hook/push logic: it runs the record command its prompt names, with its own
minted session id exported as `GEMINI_SESSION_ID`, and prints that output.
FAKE_HOST_MODE bends that for reject cases: `ignore_deny` pushes anyway,
`no_push` never pushes, `escape` appends a trace line naming a foreign
plugin_root, `fail` exits 1 before doing anything, `hang` sleeps far past any
probe timeout, `same_session` reuses one session id for every launch,
`extra_line` appends one more honest trace line (the copy's own plugin_root) on
the control run, and `silent_refusal` skips the hooks on bound runs, writes an
honest trace line with no outcome and does not push, so the push is refused for
no recorded reason. Delegation modes (claude): `no_dispatch` fires no `Agent`
hook, `no_parent` fires only the nested one, `no_nested` fires only the parent
one. Gemini modes: `no_record` echoes the prompt without running the record
command, `echo_marker` prints a bare `--record-session gemini-<n>` marker,
`auth_fail` exits 1 printing FAKE_AUTH_MESSAGE on FAKE_AUTH_STREAM (stderr or
stdout), `fail_after_record` runs the record command, then exits 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

FAKE_STDOUT_MARK = "fake-host-stdout-7d2e91"
FAKE_HANG_SECONDS = 30
FAKE_HOST = r"""#!@PYTHON@
import json, os, re, shlex, subprocess, sys, time, uuid
from pathlib import Path
host, args, prompt = Path(sys.argv[0]).name, sys.argv[1:], sys.stdin.read()
mode = os.environ["FAKE_HOST_MODE"]
session = "5e55" * 8 if mode == "same_session" else uuid.uuid4().hex
record_cmd = ""
for text in prompt.splitlines():
    if "--record-session" in text and "autopilot.py" in text:
        start = text.find(shlex.quote(sys.executable))
        record_cmd = text[start:] if start >= 0 else text
        break
with open(os.environ["FAKE_HOST_LOG"], "a") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "prompt": prompt, "home": os.environ.get("HOME"),
                          "trace": os.environ.get("AUTOPILOT_HOOK_TRACE"), "session": session,
                          "plugin_root_env": os.environ.get("AUTOPILOT_PLUGIN_ROOT"),
                          "record_command": record_cmd}) + "\n")
if mode == "auth_fail":
    stream = sys.stdout if os.environ.get("FAKE_AUTH_STREAM") == "stdout" else sys.stderr
    print(os.environ.get("FAKE_AUTH_MESSAGE", "Error: Not logged in"), file=stream)
    sys.exit(1)
if mode == "fail":
    sys.exit("IneligibleTierError: fake host refused")
if mode == "hang":
    time.sleep(@HANG@)
    sys.exit(0)
if host == "gemini":
    if mode == "echo_marker":
        index = sum(1 for _ in open(os.environ["FAKE_HOST_LOG"])) - 1
        print(f"--record-session gemini-{index}")
    elif mode == "no_record":
        print(prompt)
    elif record_cmd:
        done = subprocess.run(record_cmd, shell=True, cwd=os.getcwd(), capture_output=True, text=True,
                              env=os.environ | {"GEMINI_SESSION_ID": session})
        sys.stdout.write(done.stdout)
        sys.stderr.write(done.stderr)
    if mode == "fail_after_record":
        sys.exit("boom: fake host died after recording")
    print(json.dumps({"result": "@MARK@", "session_id": session}))
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
def fire(tool, tool_input, **extra):
    payload = json.dumps({"session_id": session, "hook_event_name": "PreToolUse", "tool_name": tool,
                          "tool_input": tool_input, "cwd": str(workdir), **extra})
    refused = False
    for group in find(json.loads(hooks.read_text()), "PreToolUse") or []:
        if (group.get("matcher") or "*") not in ("*", tool) and not re.fullmatch(group["matcher"], tool):
            continue
        for hook in group.get("hooks", []):
            done = subprocess.run(hook["command"], shell=True, cwd=workdir, env=env, input=payload,
                                  capture_output=True, text=True)
            try:
                reply = json.loads(done.stdout or "null")
            except ValueError:
                reply = None
            refused |= done.returncode == 2 or bool({"deny", "block"} & set(map(str, leaves(reply))))
    return refused
push = re.search(r"git push probe-remote HEAD:refs/heads/probe-[a-z0-9-]+", prompt).group(0)
control = push.endswith("probe-control")
silent = mode == "silent_refusal" and not control
honest_root = os.path.realpath(workdir.parent / "plugin")
denied = False
if host == "claude" and not control and not silent and mode != "no_dispatch":
    child = {"description": "autopilot probe child", "prompt": "probe", "subagent_type": "general-purpose"}
    if mode != "no_parent":
        fire("Agent", child)
    if mode != "no_nested":
        fire("Agent", child, agent_id="probe-child-" + session[:8])
if not silent:
    denied = fire("Bash", {"command": push})
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
    """Write executable fake `claude`, `codex` and `gemini` into `bin_dir`."""
    script = (
        FAKE_HOST.replace("@PYTHON@", sys.executable)
        .replace("@MARK@", FAKE_STDOUT_MARK)
        .replace("@HANG@", str(FAKE_HANG_SECONDS))
    )
    for name in ("claude", "codex", "gemini"):
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
