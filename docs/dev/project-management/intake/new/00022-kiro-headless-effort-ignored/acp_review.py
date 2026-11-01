"""Run one Claude reviewer through Kiro ACP with an explicit model and effort.

usage: python3 acp_review.py <prompt-file> <output-file> [model] [effort]

`kiro-cli chat --effort` is ignored headless in this Kiro build, so this client
opens an ACP session, sets the effort config option explicitly, verifies the
model and effort the agent reports, then sends the prompt. The agent profile
`review-readonly` exposes read tools only; every permission request is denied.
Writes the final text to <output>, raw events to <output>.jsonl and a receipt
to <output>.receipt.json. Exit 0 only when model and effort match and the turn
ended normally.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

prompt_file, output_file = Path(sys.argv[1]), Path(sys.argv[2])
model = sys.argv[3] if len(sys.argv) > 3 else "claude-opus-5.5"
effort = sys.argv[4] if len(sys.argv) > 4 else "xhigh"
raw_path = output_file.with_name(output_file.name + ".jsonl")
receipt_path = output_file.with_name(output_file.name + ".receipt.json")
repo = Path(__file__).resolve().parents[4]

proc = subprocess.Popen(
    ["kiro-cli", "acp", "--agent-engine", "v3"],
    cwd=repo,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=output_file.with_name(output_file.name + ".err").open("w"),
    text=True,
    bufsize=1,
)
raw = raw_path.open("w", encoding="utf-8")
lock = threading.Lock()
pending: dict[int, dict] = {}
events = threading.Condition(lock)
state = {"model": "", "effort": "", "text": [], "tools": 0, "denied": [], "errors": []}
next_id = [0]
closed = [False]


def send(message: dict) -> None:
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()


def request(method: str, params: dict, timeout: float = 600) -> dict:
    with lock:
        next_id[0] += 1
        rid = next_id[0]
    send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
    with events:
        if not events.wait_for(lambda: rid in pending or closed[0], timeout=timeout):
            raise SystemExit(f"timeout waiting for {method}")
        if rid not in pending:
            raise SystemExit(f"agent exited during {method}")
        return pending.pop(rid)


def track_options(options: list) -> None:
    for option in options or []:
        if option.get("id") == "model":
            state["model"] = option.get("currentValue", "")
        elif option.get("id") == "effortLevel":
            state["effort"] = option.get("currentValue", "")
            state["effort_option"] = True


def reader() -> None:
    for line in proc.stdout:
        raw.write(line)
        raw.flush()
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "id" in msg and "method" not in msg:
            with events:
                pending[msg["id"]] = msg
                events.notify_all()
            continue
        method, params = msg.get("method"), msg.get("params") or {}
        if "id" in msg:  # agent -> client request
            if method == "session/request_permission":
                state["denied"].append(params.get("toolCall", {}).get("title"))
                send({"jsonrpc": "2.0", "id": msg["id"],
                      "result": {"outcome": {"outcome": "cancelled"}}})
            else:
                send({"jsonrpc": "2.0", "id": msg["id"],
                      "error": {"code": -32601, "message": f"unsupported: {method}"}})
            continue
        if method == "session/update":
            update = params.get("update") or {}
            kind = update.get("sessionUpdate")
            meta = update.get("_meta", {}).get("kiro", {})
            with lock:
                if kind == "config_option_update":
                    track_options(update.get("configOptions"))
                    events.notify_all()
                elif kind == "agent_message_chunk":
                    content = update.get("content") or {}
                    if content.get("type") == "text":
                        state["text"].append(content.get("text", ""))
                elif kind == "tool_call":
                    state["tools"] += 1
                if meta.get("kind") == "display_error":
                    state["errors"].append(f"{meta.get('errorType')}: {meta.get('message')}")
    with events:
        closed[0] = True
        events.notify_all()


threading.Thread(target=reader, daemon=True).start()
result: dict = {"exit": None}
try:
    init = request("initialize", {
        "protocolVersion": 1,
        "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
    })
    session = request("session/new", {"cwd": str(repo), "mcpServers": []})
    if "error" in session:
        raise SystemExit(f"session/new failed: {session['error']}")
    sid = session["result"]["sessionId"]
    track_options(session["result"].get("configOptions"))
    reply = request("session/set_config_option", {"sessionId": sid, "configId": "mode", "value": "review-readonly"})
    if "error" in reply:
        reply = request("session/set_mode", {"sessionId": sid, "modeId": "review-readonly"})
    if "error" in reply:
        raise SystemExit(f"set agent mode failed: {reply['error']}")
    track_options((reply.get("result") or {}).get("configOptions"))
    if state["model"] != model:
        reply = request("session/set_config_option", {"sessionId": sid, "configId": "model", "value": model})
        track_options((reply.get("result") or {}).get("configOptions"))
    # The effort option appears only after the model catalog loads.
    with events:
        events.wait_for(lambda: state.get("effort_option") or closed[0], timeout=120)
    reply = request("session/set_config_option", {"sessionId": sid, "configId": "effortLevel", "value": effort})
    if "error" in reply:
        raise SystemExit(f"set effort failed: {reply['error']}")
    track_options((reply.get("result") or {}).get("configOptions"))
    pre = {"model": state["model"], "effort": state["effort"]}
    if pre != {"model": model, "effort": effort}:
        raise SystemExit(f"model/effort not applied before prompt: {pre}")
    turn = request("session/prompt", {
        "sessionId": sid,
        "prompt": [{"type": "text", "text": prompt_file.read_text(encoding="utf-8")}],
    }, timeout=5400)
    stop = (turn.get("result") or {}).get("stopReason")
    post = {"model": state["model"], "effort": state["effort"]}
    ok = stop == "end_turn" and post == pre and not state["errors"] and "error" not in turn
    result = {"ok": ok, "session": sid, "stopReason": stop, "turn_error": turn.get("error"),
              "requested": {"model": model, "effort": effort}, "before_prompt": pre, "after_turn": post}
except SystemExit as exc:
    result = {"ok": False, "failure": str(exc)}
finally:
    proc.stdin.close()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
text = "".join(state["text"])
output_file.write_text(text, encoding="utf-8")
result.update({"tool_calls": state["tools"], "permission_denied": state["denied"],
               "errors": state["errors"], "chars": len(text)})
receipt_path.write_text(json.dumps(result, indent=1), encoding="utf-8")
print(json.dumps(result, indent=1))
sys.exit(0 if result.get("ok") else 1)
