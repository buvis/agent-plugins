#!/usr/bin/env python3
"""Kiro adapter: automated engine runs through `kiro-cli chat --v3`.

Live turns stay blocked until `--probe-live` yields a passing boundary proof
for this exact CLI version, agent server version, package, and configuration.
R1's manual IDE checks are separate and remain mandatory.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from collections.abc import Iterator
from pathlib import Path

import run_claude as runner
import score

AGENT = "specflow-eval"
# Fixture-local instruction files only; nothing personal and nothing inherited.
RESOURCES = ["file://AGENTS.md", "file://.kiro/steering/**/*.md"]
SETTING = "chat.disableInheritingDefaultResources"
# https://kiro.dev/docs/sandbox/ ($KIRO_HOME/settings/sandbox.json)
SANDBOX = {"enabled": True, "networkAccess": "DEFAULT_BLOCKED", "mcpSandboxing": True}
# Name of a synthetic variable; the probe checks that tools never receive it.
SECRET_VARIABLE = "SPECFLOW_SYNTHETIC_" + "TOKEN"
KAS = re.compile(r'kas\.server\.starting \{[^\n]*?"version":"([^"\s;]+)"')
# Observed on 2.35.1 when Seatbelt cannot start (for example inside another
# Seatbelt sandbox): the host still reports the sandbox as active, and every
# shell command ends with this text and exit code 71 instead of running.
SANDBOX_START_FAILURE = "sandbox-exec: sandbox_apply"
SANDBOX_WARNING = re.compile(r"(?im)^\[(?:WARN|ERROR)\][^\n]*sandbox")
# Prefix of the host's own result for a call stopped by a permission rule.
DENIAL = "Blocked by a permission rule"
# Resumed turns and agents without instruction files emit no steering_inclusion
# update. Every turn does report matched context files. Treating that list as a
# measured inventory is a proposed contract revision; it stays off until the
# developer approves it. The files are still reported, so taint is detected.
CONTEXT_INVENTORY_APPROVED = False
# Workspace folders the host loads as configuration on the next launch
# (--trust-workspace admits them without asking). No fixture needs them, so a
# turn may not write them and a launch refuses a workspace that has them.
HOST_CONFIGURATION = (
    ".kiro/agents",
    ".kiro/hooks",
    ".kiro/settings",
    ".kiro/workflows",
)
NATIVE_PROBES = {
    "native-control-read-denied": ("read", "control"),
    "native-home-read-denied": ("read", "home"),
    "native-other-workspace-read-denied": ("read", "other"),
    "native-symlink-read-denied": ("read", "read_link"),
    "native-plugin-write-denied": ("edit", "plugin_new"),
    "native-symlink-write-denied": ("edit", "link_new"),
    "plugin-read": ("read", "manifest"),
}
PROBE_INSTRUCTIONS = {
    "AGENTS.md": "Synthetic fixture instruction.\n",
    ".kiro/steering/rule.md": "Synthetic fixture steering rule.\n",
}


# Kiro's shell is a login shell with its own PATH (it found the system Python,
# observed 2026-11-15), so the probe names the supervisor's interpreter.
PROBE_COMMAND = f"{Path(sys.executable).resolve()} -I -B probe.py"


def deny_around(root: Path, keep: list[Path], expand: bool) -> list[str]:
    """Paths under root to deny so that no kept path, or its parents, is denied.

    The shell sandbox did not honour a rule's `exclude` (observed 2026-11-15: a
    deny on the workspaces folder made the workspace itself unreadable, even
    for getcwd). So a deny never names a folder that holds a readable path;
    it names that folder's other entries instead. Unexpanded, it returns one
    stable placeholder, for the configuration digest.
    """
    inside = [path for path in keep if path.is_relative_to(root)]
    if not inside:
        return [str(root)]
    if not expand:
        return [f"<entries of {root} around {sorted(str(p) for p in inside)}>"]
    denied = []
    for entry in sorted(root.iterdir()) if root.is_dir() else []:
        if entry in inside:
            continue
        try:
            # An entry the supervisor cannot inspect is denied like any other.
            target = entry.resolve() if entry.is_symlink() else None
        except OSError:
            target = None
        # The sandbox resolves a denied link to its target. An alias of a
        # kept path (mise's `3.15` beside `3.15.2`) would hide that path
        # (observed 2026-11-15: Python could not read its own library).
        if target and any(p == target or p.is_relative_to(target) for p in inside):
            continue
        if any(path.is_relative_to(entry) for path in inside):
            denied += deny_around(entry, inside, expand)
        else:
            denied.append(str(entry))
    return denied


def kiro_agent(
    batch: Path, workspace: Path, plugin: Path, *, expand: bool = True
) -> dict:
    """Custom agent with V3 permission rules; a deny always beats an allow.

    Schema: https://kiro.dev/docs/custom-agents/configuration-reference/ and
    https://kiro.dev/docs/permissions/. A pattern without wildcards also
    matches its children. Headless runs turn every unanswered request into a
    denial, so anything not allowed here is denied. The shell is allowed
    because the Seatbelt sandbox, shaped by these file rules, is its boundary.
    """
    real, runtime = Path.home().resolve(), Path(sys.base_prefix).resolve()
    private = [batch / "control", batch / "home", real, batch / "workspaces"]
    readable = [workspace, plugin, runtime]
    rules = [
        {
            "capability": "fs_read",
            "match": [str(path) for path in readable],
            "effect": "allow",
        },
        {"capability": "fs_write", "match": [str(workspace)], "effect": "allow"},
        {"capability": "shell", "effect": "allow"},
        {"capability": "skill", "effect": "allow"},
        {"capability": "power", "effect": "allow"},
        {
            "capability": "fs_read",
            "match": [
                path for root in private for path in deny_around(root, readable, expand)
            ],
            "effect": "deny",
        },
        {
            "capability": "fs_write",
            "match": [
                path
                for root in (*private, batch / "resources")
                for path in deny_around(root, [workspace], expand)
            ],
            "effect": "deny",
        },
        {
            "capability": "fs_write",
            "match": [str(workspace / name) for name in HOST_CONFIGURATION],
            "effect": "deny",
        },
        *(
            {"capability": name, "effect": "deny"}
            for name in ("web_fetch", "web_search", "mcp", "subagent")
        ),
    ]
    return {
        "name": AGENT,
        "description": "Isolated specflow evaluation agent",
        "tools": ["read", "write", "shell"],
        "resources": RESOURCES,
        "includePowers": True,
        "includeMcpJson": False,
        "mcpServers": {},
        "permissions": {"rules": rules},
    }


def write_configuration(home: Path, batch: Path, workspace: Path, plugin: Path) -> None:
    """Generate the per-turn agent and sandbox files inside the private home."""
    files = {
        home / "agents" / f"{AGENT}.json": kiro_agent(batch, workspace, plugin),
        home / "settings/sandbox.json": SANDBOX,
    }
    for path, value in files.items():
        path.parent.mkdir(mode=0o700, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")
        path.chmod(0o600)


def instruction_hashes(*roots: Path) -> dict[str, str]:
    """Hash every candidate file before launch; later bytes prove nothing."""
    hashes = {}
    for root in roots:
        for path in root.rglob("*"):
            if (
                ".git" in path.relative_to(root).parts
                or path.is_symlink()
                or not path.is_file()
            ):
                continue
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def reduce_call(calls: dict[str, dict], update: dict) -> None:
    identifier = update.get("toolCallId")
    if not isinstance(identifier, str) or not identifier:
        raise runner.HostError("Kiro emitted invalid tool evidence")
    call = calls.setdefault(
        identifier,
        {"kind": None, "path": None, "command": "", "status": None, "output": {}},
    )
    if isinstance(update.get("kind"), str):
        call["kind"] = update["kind"]
    if "status" in update:
        call["status"] = update["status"]
    data = update.get("rawInput")
    data = data if isinstance(data, dict) else {}
    if isinstance(data.get("command"), str):
        call["command"] = data["command"]
    places = update.get("locations")
    named = [
        place["path"]
        for place in (places if isinstance(places, list) else [])
        if isinstance(place, dict) and isinstance(place.get("path"), str)
    ]
    path = named[0] if named else data.get("path")
    if isinstance(path, str) and path:
        call["path"] = path
    if isinstance(update.get("rawOutput"), dict):
        call["output"] = update["rawOutput"]
    # Shell output arrives as text content; its raw-output key is not documented.
    for part in update["content"] if isinstance(update.get("content"), list) else []:
        inner = part.get("content") if isinstance(part, dict) else None
        if isinstance(inner, dict) and isinstance(inner.get("text"), str):
            call["text"] = call.get("text", "") + inner["text"] + "\n"


def reduce_update(turn: dict, update: dict) -> None:
    """Fold one ACP session update into the turn summary."""
    meta = update.get("_meta")
    kiro = meta.get("kiro") if isinstance(meta, dict) else None
    kiro = kiro if isinstance(kiro, dict) else {}
    options = update.get("configOptions")
    for option in options if isinstance(options, list) else []:
        if isinstance(option, dict) and option.get("id") == "model":
            turn["model"] = option.get("currentValue")
    commands = update.get("availableCommands")
    for entry in commands if isinstance(commands, list) else []:
        text = json.dumps(entry, sort_keys=True) if isinstance(entry, dict) else ""
        if '"power": {"name": "specflow"' in text and '"type": "skill"' in text:
            turn["skills"].add(entry.get("name"))
    if kiro.get("kind") == "steering_inclusion":
        documents = kiro.get("steeringDocuments")
        if not isinstance(documents, list) or any(
            not isinstance(uri, str) or not uri for uri in documents
        ):
            raise runner.HostError("Kiro emitted invalid instruction evidence")
        turn["steering"] = [*(turn["steering"] or []), *documents]
    if kiro.get("kind") == "context_usage":
        breakdown = kiro.get("breakdown")
        files = breakdown.get("contextFiles") if isinstance(breakdown, dict) else None
        items = files.get("items") if isinstance(files, dict) else None
        if isinstance(items, list):
            turn["context"] = [
                *(turn["context"] or []),
                *(
                    item["uri"]
                    for item in items
                    if isinstance(item, dict)
                    and item.get("matched") is True
                    and isinstance(item.get("uri"), str)
                ),
            ]
    if update.get("sessionUpdate") in ("tool_call", "tool_call_update"):
        reduce_call(turn["calls"], update)


def read_stream(result: subprocess.CompletedProcess) -> dict:
    """Reduce one stream-json run without judging its tool calls.

    Events observed on kiro-cli 2.35.1: runStarted, sandboxStatus,
    sessionUpdate (ACP), runError, runFinished. Raw stream text never enters a
    record or an error message.
    """
    if result.returncode:
        raise runner.HostError("Kiro turn failed")
    try:
        events = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]
    except ValueError:
        raise runner.HostError("Kiro emitted invalid JSONL") from None
    if (
        len(events) < 2
        or any(
            not isinstance(e, dict) or not isinstance(e.get("data"), dict)
            for e in events
        )
        or events[0].get("type") != "runStarted"
        or events[0]["data"].get("engine") != "v3"
        or [e.get("type") for e in events].count("runFinished") != 1
        or events[-1].get("type") != "runFinished"
        or any(e.get("type") == "runError" for e in events)
    ):
        raise runner.HostError("Kiro omitted ordered turn evidence")
    final = events[-1]["data"]
    session, reply = final.get("sessionId"), final.get("finalText")
    if (
        final.get("status") != "success"
        or final.get("finalTextTruncated") is not False
        or not isinstance(reply, str)
        or not reply.strip()
    ):
        raise runner.HostError("Kiro turn did not finish with a complete reply")
    if (
        not isinstance(session, str)
        or not session.strip()
        or any(e["data"].get("sessionId", session) != session for e in events)
    ):
        raise runner.HostError("Kiro omitted or changed conversation identity")
    turn = {
        "session": session,
        "reply": reply,
        "model": None,
        "sandbox": [e["data"] for e in events if e.get("type") == "sandboxStatus"],
        "steering": None,
        "context": None,
        "skills": set(),
        "calls": {},
    }
    for event in events[1:-1]:
        update = event["data"].get("update")
        if event.get("type") == "sessionUpdate" and isinstance(update, dict):
            reduce_update(turn, update)
    return turn


def sandbox_active(turn: dict, stderr: str) -> bool:
    """True when the host reports the sandbox on and no command lost it."""
    return (
        bool(turn["sandbox"])
        and all(
            status.get("status") == "active"
            and status.get("networkMode") == "default_blocked"
            for status in turn["sandbox"]
        )
        and not SANDBOX_WARNING.search(stderr)
        and not any(
            SANDBOX_START_FAILURE in str(call["output"].get("output", ""))
            for call in turn["calls"].values()
        )
    )


def reject_failures(turn: dict) -> None:
    """Stop on a permission denial or an unfinished call.

    A call that fails for another reason is ordinary work, as on the other
    hosts: a command that exits nonzero, or a lookup of a file that does not
    exist (observed 2026-11-15: a Power steering-file lookup by a wrong path
    stopped a whole session).
    """
    for call in turn["calls"].values():
        code = call["output"].get("exitCode")
        denied = DENIAL in f"{call['output'].get('message')} {call.get('text', '')}"
        if call["status"] == "completed" or (call["status"] == "failed" and not denied):
            continue
        # Names the call so a stopped session can be diagnosed; the record
        # normalizes batch and home paths before it is stored.
        reason = " ".join(
            str(value)[:200]
            for value in (call["output"].get("message"), call.get("text"))
            if value
        )
        raise runner.HostError(
            "Kiro reported a failed, denied, or unfinished call: "
            f"kind={call['kind']} status={call['status']} exit={code} "
            f"target={call['path'] or call['command'][:200]!r} reason={reason!r}"
        )


def instruction_evidence(
    turn: dict, workspace: Path, hashes: dict[str, str]
) -> tuple[dict[str, dict], bool]:
    """Host-reported loaded files, each with its pre-launch hash when known."""
    observations = {}
    for uri in [*(turn["steering"] or []), *(turn["context"] or [])]:
        path = Path(urllib.parse.unquote(uri.removeprefix("file://")))
        path = path if path.is_absolute() else workspace / path
        observations[str(path)] = {"sha256": hashes.get(str(path)), "imports": []}
    measured = turn["steering"] is not None or (
        CONTEXT_INVENTORY_APPROVED and turn["context"] is not None
    )
    return observations, measured


def named_reads(turn: dict, workspace: Path, plugin: Path) -> tuple[list[str], bool]:
    """Files the tool stream names as read; False when a read cannot be named."""
    reads, known = [], True
    for call in turn["calls"].values():
        if call["kind"] == "read":
            path = workspace / call["path"] if call["path"] else None
            if path and path.is_file():
                reads.append(str(path))
            else:
                known = False
        elif call["kind"] == "execute":
            named, clear = runner.shell_reads(call["command"], workspace, plugin)
            reads += named
            known = known and clear
        elif call["kind"] != "edit":
            known = False
    return reads, known


class Kiro:
    host = "kiro-ide"

    def __init__(self, model: str) -> None:
        self.model = model
        self.version = "not-started"
        self.cli: str | None = None
        self.kas: str | None = None
        self.expected_kas: str | None = None
        self.read_measurement = "not-measured"
        self.plugin = score.PLUGIN
        self.root: Path | None = None
        self.home: Path | None = None
        self.boundary: dict | None = None
        self.configuration_sha256: str | None = None
        self.boundary_sha256: str | None = None
        self.new_conversation()

    def new_conversation(self) -> None:
        self.conversation: str | None = None
        self.instruction_observations: dict[str, dict] = {}
        self.instruction_measurement = "not-measured"

    def identify(self) -> None:
        """Fix executable, versions, and configuration digest before any launch.

        The agent server reports its version only when a turn starts. Until
        then the adapter adopts the version named by the supplied boundary
        proof, so the proof can match before launch; every turn must then
        report that same version or it fails.
        """
        if self.home is None:
            # run_batch points plugin at the batch copy before preflight.
            self.root = self.plugin.parent.parent
        if (
            self.root is None
            or not (self.root / "control").is_dir()
            or not (self.root / "workspaces").is_dir()
        ):
            raise runner.HostError("Kiro launch needs the external batch layout")
        executable = shutil.which("kiro-cli")
        if not executable:
            raise runner.HostError("kiro-cli executable not found")
        self.executable = executable
        version = runner.command([executable, "--version"], self.root, timeout=30)
        if version.returncode or not version.stdout.split():
            raise runner.HostError("could not identify installed Kiro")
        self.cli = f"kiro-cli {version.stdout.split()[-1]}"
        proved = (self.boundary or {}).get("hostVersion")
        prefix = f"{self.cli}; KAS "
        self.expected_kas = (
            proved.removeprefix(prefix)
            if isinstance(proved, str) and proved.startswith(prefix)
            else None
        )
        server = self.kas or self.expected_kas
        self.version = f"{prefix}{server}" if server else self.cli
        session = self.root / "workspaces/session"
        installed = self.root / "control/kiro-home/powers/installed/specflow"
        agent = runner.normalize(
            kiro_agent(self.root, session, installed, expand=False),
            {
                str(session): "<workspace>",
                str(self.root): "<batch>",
                str(Path.home().resolve()): "<home>",
                str(Path(sys.base_prefix).resolve()): "<python-runtime>",
            },
        )
        self.configuration_sha256 = score.evidence_digest(
            {
                "agent": agent,
                "settings": {SETTING: True},
                "sandbox": SANDBOX,
                "version": self.cli,
                "arguments": self.arguments("<prompt>", template=True)[1:],
            }
        )

    def preflight(self) -> None:
        self.identify()
        if not (self.kas or self.expected_kas):
            # A proof without the server version covers only half of the host.
            raise runner.HostError(
                f"{self.host} launch blocked: no boundary proof names this CLI "
                "version with an agent server version (run --probe-live)"
            )
        runner.accept_boundary(
            self, score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        )

    def environment(self) -> dict[str, str]:
        return {
            "PATH": os.pathsep.join(
                [str(Path(sys.executable).resolve().parent), os.defpath]
            ),
            # Measured on kiro-cli 2.35.1: with HOME pointed at an empty
            # directory `kiro-cli whoami` exits 1 and a turn asks for a new
            # sign-in. The sign-in lives outside KIRO_HOME, so the real HOME
            # stays; the permission rules and the sandbox deny tools access.
            "HOME": str(Path.home()),
            "KIRO_HOME": str(self.home),
            "LANG": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PYTHONDONTWRITEBYTECODE": "1",
            # No secret here: Kiro passes its environment on to tools and has
            # no control to strip a variable (the planted synthetic variable
            # reached the shell, observed 2026-11-15). Its sign-in is not an
            # environment variable.
        }

    def arguments(self, prompt: str, *, template: bool = False) -> list[str]:
        """Launch flags. The template form is turn-independent, for the digest."""
        resume = (
            ["--resume-id", self.conversation]
            if self.conversation and not template
            else []
        )
        return [
            getattr(self, "executable", "kiro-cli"),
            "chat",
            "--v3",
            "--no-interactive",
            "--output-format",
            "stream-json",
            "--trust-workspace",
            "--agent",
            AGENT,
            "--model",
            "<model>" if template else self.model,
            *resume,
            prompt,
        ]

    def run(self, *args: str) -> subprocess.CompletedProcess:
        """A short host management command under the private home."""
        return runner.command(
            [self.executable, *args], self.root, self.environment(), 60
        )

    @contextlib.contextmanager
    def install(self, workspace: Path) -> Iterator[None]:
        """Build the private home, install the Power, and verify both."""
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        if self.root is None:
            self.root = self.plugin.parent.parent
        source, home = self.root / "resources/specflow", self.root / "control/kiro-home"
        home.mkdir(mode=0o700)
        self.home = home
        try:
            installed = home / "powers/installed/specflow"
            write_configuration(home, self.root, workspace, installed)
            if self.run("settings", SETTING, "true").returncode:
                raise runner.HostError("Kiro refused the resource inheritance setting")
            self.require_setting()
            if self.run("powers", "install", str(source)).returncode:
                raise runner.HostError("Kiro Power installation failed")
            if not installed.is_dir() or installed.is_symlink():
                raise runner.HostError("Kiro did not install the Power in its home")
            runner.verify_plugin(installed, revision)
            # Exit status only; the account output is never read or printed.
            if self.run("whoami").returncode:
                raise runner.HostError("Kiro is not signed in")
            agent = home / "agents" / f"{AGENT}.json"
            if self.run("agent", "validate", "--path", str(agent)).returncode:
                raise runner.HostError("Kiro rejected the generated agent")
            if (home / "AGENTS.md").exists() or any((home / "steering").rglob("*")):
                raise runner.HostError("unexpected global Kiro instructions")
            self.plugin = installed
            yield
        finally:
            self.home, self.plugin = None, source

    def require_setting(self) -> None:
        try:
            applied = score.read_json(self.home / "settings/cli.json").get(SETTING)
        except (OSError, ValueError, AttributeError):
            applied = None
        if applied is not True:
            raise runner.HostError("Kiro resource inheritance setting is not applied")

    @contextlib.contextmanager
    def batch(self, workspace: Path) -> Iterator[None]:
        # This guard also protects direct callers, outside run_batch.
        self.preflight()
        with self.install(workspace):
            yield

    def launch(self, prompt: str, workspace: Path) -> subprocess.CompletedProcess:
        """One host process under the generated configuration; no shell."""
        if self.home is None:
            raise runner.HostError("Kiro batch was not started")
        if workspace.parent != self.root / "workspaces":
            raise runner.HostError("workspace is outside the batch")
        for name in HOST_CONFIGURATION:
            path = workspace / name
            if path.exists() or path.is_symlink():
                # For example, a workspace agent would replace the generated one.
                raise runner.HostError(f"workspace carries Kiro configuration: {name}")
        write_configuration(self.home, self.root, workspace, self.plugin)
        self.require_setting()
        return runner.command(self.arguments(prompt), workspace, self.environment())

    def identity(self, result: subprocess.CompletedProcess) -> dict:
        """Check conversation, model, and server version; commit nothing."""
        turn = read_stream(result)
        if self.conversation is not None and turn["session"] != self.conversation:
            raise runner.HostError("Kiro omitted or changed conversation identity")
        model = turn["model"]
        if not isinstance(model, str) or model.strip().lower() in (
            "",
            "auto",
            "default",
        ):
            raise runner.HostError("Kiro did not report an explicit model")
        server = KAS.search(result.stderr or "")
        if not server:
            raise runner.HostError("Kiro omitted its agent server version")
        if (self.kas or self.expected_kas) not in (None, server.group(1)):
            raise runner.HostError(
                "Kiro agent server version differs from the proven one"
            )
        turn["kas"] = server.group(1)
        return turn

    def commit(self, turn: dict) -> None:
        self.conversation, self.model, self.kas = (
            turn["session"],
            turn["model"],
            turn["kas"],
        )
        self.version = f"{self.cli or 'kiro-cli unknown'}; KAS {self.kas}"

    def accept_turn(
        self,
        result: subprocess.CompletedProcess,
        workspace: Path,
        hashes: dict[str, str],
    ) -> tuple[str, list[str]]:
        """Reduce a turn; conversation state advances only when it is complete."""
        turn = self.identity(result)
        if not sandbox_active(turn, result.stderr or ""):
            raise runner.HostError("Kiro shell sandbox is not active")
        reject_failures(turn)
        self.commit(turn)
        self.instruction_observations, measured = instruction_evidence(
            turn, workspace, hashes
        )
        self.instruction_measurement = "measured" if measured else "not-measured"
        reads, known = named_reads(turn, workspace, self.plugin)
        self.read_measurement = "measured" if known else "not-measured"
        return turn["reply"], reads

    def turn(self, prompt: str, workspace: Path) -> tuple[str, list[str]]:
        if self.home is None:
            raise runner.HostError("Kiro batch was not started")
        self.preflight()
        hashes = instruction_hashes(workspace, self.plugin)
        return self.accept_turn(self.launch(prompt, workspace), workspace, hashes)


# Prints only the names of the tool environment's variables, never a value.
ENVIRONMENT_COMMAND = (
    f"{Path(sys.executable).resolve()} -I -B -c "
    "'import json, os; print(json.dumps(sorted(os.environ)))'"
)
SECRET_NAME = re.compile(r"(?i)key|secret|token|password|credential|auth")


def environment_check(turn: dict) -> dict:
    """The tool environment must hold no secret-like variable.

    Kiro cannot strip a variable from tools, so the supervisor gives the host
    none to strip; this check reads what a sandboxed shell tool really got.
    """
    runs = [
        call
        for call in turn["calls"].values()
        if call["kind"] == "execute" and call["command"].strip() == ENVIRONMENT_COMMAND
    ]
    names = None
    text = "\n".join(
        [runs[0].get("text", ""), *map(str, runs[0]["output"].values())]
        if len(runs) == 1
        else []
    )
    for line in text.splitlines():
        try:
            found = json.loads(line)
        except ValueError:
            continue
        if isinstance(found, list) and all(isinstance(n, str) for n in found):
            names = found
    risky = sorted(n for n in names or [] if SECRET_NAME.search(n))
    return {
        "passed": bool(names) and not risky,
        "evidence": "Kiro has no control to strip variables from tools; the "
        "supervisor passes it none that is secret. Variable names a sandboxed "
        f"shell tool received: {len(names) if names else 'not reported'}; "
        f"secret-like names: {risky}",
    }


def probe_prompt(payload: dict[str, str]) -> str:
    steps = [
        f"{'write' if kind == 'edit' else kind} tool on {payload[key]}"
        + (" with content: probe" if kind == "edit" else "")
        for kind, key in NATIVE_PROBES.values()
    ]
    steps.append(f"shell tool with exactly this command: {PROBE_COMMAND}")
    steps.append(f"shell tool with exactly this command: {ENVIRONMENT_COMMAND}")
    return (
        "This is a permission self-test. Make each tool call below once, in "
        "order. Some are denied; that is expected. Never retry, never use a "
        "different tool or path, and continue after a denial. Then reply: done.\n"
        + "\n".join(f"{n}. {step}" for n, step in enumerate(steps, 1))
    )


def native_checks(turn: dict, payload: dict[str, str], leaked: bool) -> dict:
    """Verdicts from the host's own status for each read and write tool call."""
    checks = {}
    for name, (kind, key) in NATIVE_PROBES.items():
        call = next(
            (
                c
                for c in turn["calls"].values()
                if c["kind"] == kind and c["path"] == payload[key]
            ),
            None,
        )
        status = call["status"] if call else None
        blocked = status == "failed" and str(
            call["output"].get("message", "")
        ).startswith(DENIAL)
        passed = status == "completed" if name == "plugin-read" else blocked
        checks[name] = {
            "passed": passed and not leaked,
            "evidence": f"{kind} tool on <{key}>: host status={status}; "
            f"permission rule block={blocked}; sentinel in stream={leaked}",
        }
    return checks


def instruction_checks(
    adapter: Kiro, turn: dict, workspace: Path, fixture: dict, hashes: dict
) -> dict:
    observations, measured = instruction_evidence(turn, workspace, hashes)
    inventory = runner.classify_instructions(
        observations,
        complete=measured,
        workspace=workspace,
        expected=fixture,
        plugin=adapter.plugin,
        plugin_files=runner.snapshot(adapter.plugin),
    )
    loaded = {str(workspace / name) for name in PROBE_INSTRUCTIONS}
    exact = set(inventory["instructionFiles"]) == loaded
    return {
        "instruction-inventory": {
            "passed": inventory["classification"] == "clean" and exact,
            "evidence": f"host steering telemetry present={measured}; "
            f"{len(observations)} files reported, classified "
            f"{inventory['classification']}; only fixture files={exact}",
        },
        "fixture-instructions": {
            "passed": loaded <= set(observations),
            "evidence": "fixture AGENTS.md and steering rule appear in the "
            f"host's loaded-file telemetry: {loaded <= set(observations)}",
        },
    }


def probe_checks(
    adapter: Kiro,
    turn: dict,
    result: subprocess.CompletedProcess,
    probe: tuple[Path, dict[str, str], dict[str, str], str],
    hashes: dict[str, str],
    revision: str,
) -> dict:
    """Every verdict comes from the stream, the script's errno, or the disk."""
    workspace, payload, fixture, secret = probe
    runs = [
        call
        for call in turn["calls"].values()
        if call["kind"] == "execute" and "probe.py" in call["command"]
    ]
    exact = all(call["command"].strip() == PROBE_COMMAND for call in runs)
    checks = runner.shell_probe_checks(
        [
            "\n".join(
                [
                    call.get("text", ""),
                    *(v for v in call["output"].values() if isinstance(v, str)),
                    f"exit code: {call['output'].get('exitCode')}",
                ]
            )
            for call in runs
        ]
        if exact
        else [],
        workspace,
        payload,
        extra=("plugin-read",),
    )
    checks["tool-secret-environment-denied"] = environment_check(turn)
    shell_read = checks["plugin-read"]["passed"]
    checks.update(native_checks(turn, payload, secret in result.stdout))
    checks["plugin-read"]["passed"] = checks["plugin-read"]["passed"] and shell_read
    checks["plugin-read"]["evidence"] += f"; sandboxed shell read={shell_read}"
    checks.update(instruction_checks(adapter, turn, workspace, fixture, hashes))
    intact = (
        runner.package_revision(adapter.plugin) == revision
        and not Path(payload["plugin_new"]).exists()
    )
    for name, check in checks.items():
        if name.endswith("write-denied"):
            check["passed"] = check["passed"] and intact
            check["evidence"] += f"; plugin tree intact={intact}"
    active = "spec-workflow" in turn["skills"]
    checks["plugin-activation"] = {
        "passed": active,
        "evidence": f"host lists the specflow Power's spec-workflow skill: {active}",
    }
    sandboxed = sandbox_active(turn, result.stderr or "")
    checks["effective-settings"] = {
        "passed": sandboxed
        and all(c["passed"] for n, c in checks.items() if n.endswith("-denied")),
        "evidence": f"host reports an active network-blocked shell sandbox and "
        f"no command lost it: {sandboxed}; every generated denial observed",
    }
    return checks


@score.deadline(runner.SESSION_TIMEOUT)
def live_probe(model: str, *, scratch: Path = runner.EXTERNAL_SCRATCH) -> dict:
    """Signed-in installed-host proof with synthetic sentinels; never a credential.

    The model only issues the listed tool calls. Nothing it says about
    isolation is read.
    """
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    adapter = Kiro(model)
    with runner.external_batch(revision, scratch=scratch) as batch:
        adapter.plugin = batch / "resources/specflow"
        adapter.identify()
        seed = batch / "workspaces/seed"
        seed.mkdir(mode=0o700)
        runner.initialize_workspace(seed)
        with adapter.install(seed):
            # The home sentinel sits beside the Power exception in KIRO_HOME.
            probe = runner.prepare_probe(
                batch,
                adapter.plugin,
                SECRET_VARIABLE,
                PROBE_INSTRUCTIONS,
                home_sentinel=adapter.home / "sentinel.txt",
            )
            workspace, payload = probe[0], probe[1]
            hashes = instruction_hashes(workspace, adapter.plugin)
            result = adapter.launch(probe_prompt(payload), workspace)
            turn = adapter.identity(result)
            adapter.commit(turn)
            checks = probe_checks(adapter, turn, result, probe, hashes, revision)
            proof = {
                "scope": "installed-host-boundary",
                "host": adapter.host,
                "hostVersion": adapter.version,
                "model": adapter.model,
                "runtimeRevision": revision,
                "configurationSha256": adapter.configuration_sha256,
                "runnerSha256": runner.runner_digest(adapter),
                "checks": runner.normalize(checks, {str(batch): "<batch>"}),
            }
    proof["checks"]["cleanup"] = {
        "passed": not batch.exists(),
        "evidence": "private batch directory absent after the probe",
    }
    return proof


def live_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Signed-in Kiro boundary probe")
    parser.add_argument("--probe-live", action="store_true", required=True)
    parser.add_argument("--model", required=True, help="explicit model; never auto")
    args = parser.parse_args(argv)
    try:
        if args.model in {"auto", "default"}:
            raise score.RecordError("choose an explicit model")
        with runner.interruption_signals():
            proof = live_probe(args.model)
    except (runner.HostError, score.RecordError) as error:
        print(f"live probe stopped: {error}", file=sys.stderr)
        return 2
    except (
        OSError,
        ValueError,
        KeyboardInterrupt,
        subprocess.SubprocessError,
    ) as error:
        print(f"live probe stopped: {type(error).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(proof, indent=2, sort_keys=True))
    return int(
        not all(
            proof["checks"].get(name, {}).get("passed") is True
            for name in score.RELEASE_BOUNDARY_CHECKS
        )
    )


if __name__ == "__main__":
    if "--probe-live" in sys.argv:
        raise SystemExit(live_main(sys.argv[1:]))
    raise SystemExit(runner.main(adapter_type=Kiro))
