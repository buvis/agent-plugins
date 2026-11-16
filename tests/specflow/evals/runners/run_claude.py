#!/usr/bin/env python3
"""Claude adapter and shared, host-neutral scenario batch machinery.

The live entry points fail closed while T-056's environment proof is missing.
No flag in this module waives the approval or spending-limit requirements.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

sys.dont_write_bytecode = True
import score

ROOT = score.ROOT
SCRATCH = ROOT / "docs/dev/tmp/specflow/evals"
EXTERNAL_SCRATCH = Path("/private/tmp" if sys.platform == "darwin" else "/tmp")
TURN_TIMEOUT = 600
MAX_SESSION_TURNS = 24
SESSION_TIMEOUT = 1800
BATCH_TIMEOUT = 7200
SESSION_BUDGET_USD = 5
FIXTURES = ROOT / "tests/specflow/fixtures"
SESSIONS = score.EVALS / "sessions"


class HostError(RuntimeError):
    """A host failed before or during a turn."""


def command(
    args: list[str], cwd: Path, env: dict | None = None, timeout: float = TURN_TIMEOUT
) -> subprocess.CompletedProcess:
    """Never use a shell; terminate the process group, including tools, on timeout."""
    timeout = score.remaining_timeout(timeout)
    with subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        # A host must never read the supervisor's terminal as extra prompt text.
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
            raise
    return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)


def git_workspace(workspace: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_SYSTEM="/dev/null",
    )
    result = command(["git", *args], workspace, env, 30)
    if result.returncode:
        raise HostError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def initialize_workspace(workspace: Path) -> None:
    if (workspace / ".git").exists():
        raise HostError("scratch workspace already has Git metadata")
    git_workspace(workspace, "init")
    verify_workspace(workspace, committed=False)
    git_workspace(workspace, "add", "--all")
    git_workspace(
        workspace,
        "-c",
        "user.name=specflow fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-m",
        "Fixture baseline",
    )
    verify_workspace(workspace)


def verify_workspace(workspace: Path, *, committed: bool = True) -> None:
    if not (workspace / ".git").is_dir() or (workspace / ".git").is_symlink():
        raise HostError("scratch workspace must have its own .git directory")
    top = Path(git_workspace(workspace, "rev-parse", "--show-toplevel")).resolve()
    git_dir = Path(
        git_workspace(workspace, "rev-parse", "--absolute-git-dir")
    ).resolve()
    if top != workspace.resolve() or git_dir != workspace.resolve() / ".git":
        raise HostError("scratch workspace is not its own Git root")
    if committed:
        git_workspace(workspace, "rev-parse", "--verify", "HEAD")


def snapshot(workspace: Path) -> dict[str, str]:
    files = {}
    for path in sorted(workspace.rglob("*")):
        relative = path.relative_to(workspace)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            raise HostError(f"cannot capture symbolic link: {relative}")
        if path.is_file():
            files[relative.as_posix()] = path.read_text(encoding="utf-8")
    return files


def write_files(workspace: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = workspace / score.safe_path(name)
        if not path.resolve().is_relative_to(workspace.resolve()):
            raise HostError("file resolves outside the workspace")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def normalize(value: object, replacements: dict[str, str]) -> object:
    """Replace roots recursively, including dictionary keys and embedded prose."""
    if isinstance(value, str):
        for root, token in sorted(
            replacements.items(), key=lambda pair: len(pair[0]), reverse=True
        ):
            if root:
                value = value.replace(root, token)
        return value
    if isinstance(value, list):
        return [normalize(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            normalize(key, replacements): normalize(item, replacements)
            for key, item in value.items()
        }
    return value


def classify_instructions(
    loaded: dict[str, dict],
    *,
    complete: bool,
    workspace: Path,
    expected: dict[str, str],
    plugin: Path,
    plugin_files: dict[str, str],
) -> dict:
    """Classify observed load-time hashes/imports before any path normalization.

    The supervisor supplies the immutable baseline plus explicit edits and the
    verified plugin bytes. A later filesystem read cannot measure what a host
    loaded. Adapters without load-time evidence must leave complete false.
    """
    workspace, plugin = workspace.resolve(), plugin.resolve()
    entries, unknown = [], complete is not True
    resolved = set()
    for name, observation in loaded.items():
        path = Path(name)
        if not path.is_absolute():
            raise HostError("instruction inventory paths must be absolute")
        path = path.resolve()
        resolved.add(str(path))
        in_plugin = path.is_relative_to(plugin)
        root, baseline = (plugin, plugin_files) if in_plugin else (workspace, expected)
        content = (
            baseline.get(path.relative_to(root).as_posix())
            if path.is_relative_to(root)
            else None
        )
        digest = observation.get("sha256")
        if content is None:
            classification, reason = "tainted", "outside expected inputs"
        elif not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            classification, reason = "unknown", "load-time content was not measured"
        elif digest != hashlib.sha256(content.encode()).hexdigest():
            classification, reason = "tainted", "loaded content differs from input"
        else:
            classification, reason = (
                "allowed",
                "matches verified plugin"
                if in_plugin
                else "matches baseline or explicit edit",
            )
        imports = observation.get("imports")
        if not isinstance(imports, list) or any(
            not isinstance(p, str) or not Path(p).is_absolute() for p in imports
        ):
            imports, unknown = [], True
        entries.append(
            {
                "path": str(path),
                "sha256": digest,
                "imports": [str(Path(p).resolve()) for p in imports],
                "plugin": in_plugin,
                "classification": classification,
                "reason": reason,
            }
        )
    unknown = unknown or any(
        e["classification"] == "unknown" or any(p not in resolved for p in e["imports"])
        for e in entries
    )
    classification = (
        "tainted"
        if any(e["classification"] == "tainted" for e in entries)
        else "unknown"
        if unknown
        else "clean"
    )
    return {
        "classification": classification,
        "complete": not unknown,
        "instructionFiles": sorted({e["path"] for e in entries if not e["plugin"]}),
        "entries": entries,
    }


def package_revision(plugin: Path) -> str:
    """Compute Git's tree hash without an index, writes, or trusting HEAD's bytes."""
    entries = []
    for path in plugin.iterdir():
        if path.is_symlink():
            mode = "120000"
            oid = score.object_id(os.readlink(path).encode())
            sort_name = path.name
        elif path.is_dir():
            mode, oid, sort_name = "40000", package_revision(path), path.name + "/"
        elif path.is_file():
            mode = "100755" if path.stat().st_mode & 0o111 else "100644"
            oid, sort_name = score.object_id(path.read_bytes()), path.name
        else:
            raise HostError("unsupported package file type")
        entries.append(
            (
                sort_name.encode(),
                mode.encode() + b" " + path.name.encode() + b"\0" + bytes.fromhex(oid),
            )
        )
    body = b"".join(entry for _, entry in sorted(entries))
    return hashlib.sha1(b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()


def verify_plugin(plugin: Path, revision: str) -> None:
    if package_revision(plugin) != revision:
        raise HostError("installed plugin differs from runtimeRevision")


@contextlib.contextmanager
def external_batch(
    revision: str, *, scratch: Path = EXTERNAL_SCRATCH
) -> Iterator[Path]:
    """Own disposable state and refuse remnants rather than deleting unknown work."""
    scratch = scratch.resolve(strict=True)
    if scratch.is_relative_to(ROOT.resolve()) or scratch.is_relative_to(
        Path.home().resolve()
    ):
        raise HostError("batch scratch must be outside the checkout and home")
    if list(scratch.glob("specflow-evals-*")) or (
        SCRATCH.exists() and any(SCRATCH.iterdir())
    ):
        raise HostError(
            "residual private evaluation directory; inspect and remove it before another batch"
        )
    for ancestor in (scratch, *scratch.parents):
        for name in (
            "AGENTS.md",
            "AGENTS.override.md",
            "CLAUDE.md",
            ".claude/CLAUDE.md",
            ".codex/config.toml",
        ):
            path = ancestor / name
            if path.exists() or path.is_symlink():
                raise HostError("unexpected ancestor instructions/configuration")
    with tempfile.TemporaryDirectory(prefix="specflow-evals-", dir=scratch) as folder:
        root = Path(folder).resolve()
        for name in ("workspaces", "resources", "control"):
            (root / name).mkdir(mode=0o700)
        verify_plugin(score.PLUGIN, revision)
        plugin = root / "resources/specflow"
        shutil.copytree(score.PLUGIN, plugin, symlinks=True)
        verify_plugin(plugin, revision)
        if any(p.is_symlink() for p in plugin.rglob("*")):
            raise HostError("evaluation resource tree contains a symlink")
        yield root
    if root.exists():
        raise HostError("private evaluation directory remains after cleanup")


def sessions_for(name: str, directory: Path = SESSIONS) -> list[tuple[Path, dict]]:
    sessions = {}
    for path in sorted(directory.glob("*.json")):
        session = score.read_json(path)
        errors = score.check_schema(
            session, score.read_json(score.SCHEMAS / "session.schema.json")
        )
        if errors or session["name"] != path.stem or not session["turns"]:
            raise score.RecordError(f"invalid session: {path.name}")
        sessions[session["name"]] = (path, session)
    if name not in sessions:
        raise score.RecordError(f"unknown session: {name}")
    ancestors = set()
    while "continues" in sessions[name][1]:
        if name in ancestors:
            raise score.RecordError("cyclic session continuation")
        ancestors.add(name)
        name = sessions[name][1]["continues"]
        if name not in sessions:
            raise score.RecordError("missing continuation parent")
    ordered = []

    def visit(current: str) -> None:
        if current in {s["name"] for _, s in ordered}:
            raise score.RecordError("cyclic session continuation")
        ordered.append(sessions[current])
        for child, (_, session) in sessions.items():
            if session.get("continues") == current:
                visit(child)

    visit(name)
    if any(len(session["turns"]) > MAX_SESSION_TURNS for _, session in ordered):
        raise score.RecordError(f"session exceeds turn limit ({MAX_SESSION_TURNS})")
    return ordered


def reserve_record(out: Path, host: str, session: str) -> tuple[Path, int]:
    folder = out / host / session
    folder.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        path = folder / f"{number}.json"
        try:
            with path.open("x", encoding="utf-8"):
                pass
            return path, number
        except FileExistsError:
            number += 1


def capture_status(workspace: Path, *, plugin: Path = score.PLUGIN) -> dict | None:
    result = command(
        [
            sys.executable,
            "-B",
            str(plugin / "skills/spec-workflow/scripts/validate_spec.py"),
            "status",
            "--json",
        ],
        workspace,
        timeout=30,
    )
    if result.returncode not in {0, 1}:
        return None
    try:
        document = json.loads(result.stdout)
    except ValueError:
        return None
    return document if document.get("statusVersion") == 1 else None


# Name of the environment variable that carries the supervisor's setup sign-in.
AUTH_VARIABLE = "CLAUDE_CODE_OAUTH_" + "TOKEN"
# Runs inside the host at each load event, so the hash is load-time content.
HOOK = """import hashlib, json, sys
event = json.load(sys.stdin)
try:
    with open(event["file_path"], "rb") as handle:
        event["sha256"] = hashlib.sha256(handle.read()).hexdigest()
except (KeyError, OSError):
    pass
with open(sys.argv[1], "a", encoding="utf-8") as log:
    log.write(json.dumps(event) + "\\n")
"""
ROOT_INSTRUCTIONS = ("CLAUDE.md", ".claude/CLAUDE.md")
# Workspace files the host loads as configuration on the next launch.
HOST_SETTINGS = (".claude/settings.json", ".claude/settings.local.json", ".mcp.json")


def runner_digest(adapter: object) -> str:
    """Hash of the shared runner and the adapter's own module: proofs bind to both."""
    files = {Path(__file__), Path(sys.modules[type(adapter).__module__].__file__)}
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def claude_settings(batch: Path, workspace: Path) -> dict:
    """Supervisor settings: default-deny native tools, mandatory shell sandbox.

    Keys: https://code.claude.com/docs/en/settings and /sandboxing. A `//`
    prefix makes a permission path absolute. The installed host has no command
    that prints effective settings, so acceptance is proven by behavior: the
    boundary probe for this exact configuration, and a hook marker each turn.
    """
    control, home = batch / "control", batch / "home"
    plugin = batch / "resources/specflow"
    hook = {
        "hooks": [
            {
                "type": "command",
                "command": " ".join(
                    json.dumps(str(part))
                    for part in (
                        Path(sys.executable).resolve(),
                        "-I",
                        "-B",
                        control / "hook.py",
                        control / "instructions.jsonl",
                    )
                ),
            }
        ]
    }
    private = [control, home, Path.home().resolve()]
    return {
        "autoMemoryEnabled": False,
        "claudeMdExcludes": [f"{Path.home().resolve()}/**"],
        "enableAllProjectMcpServers": False,
        "hooks": {"SessionStart": [hook], "InstructionsLoaded": [hook]},
        "permissions": {
            # dontAsk denies everything else, including other workspaces.
            "allow": ["Bash", "Skill", f"Edit(/{workspace}/**)", f"Read(/{plugin}/**)"],
            "deny": [
                *(f"{tool}(/{p}/**)" for p in private for tool in ("Read", "Edit")),
                f"Edit(/{plugin}/**)",
                # A turn must not write configuration the next launch would load.
                *(f"Edit(/{workspace / name})" for name in HOST_SETTINGS),
            ],
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": [str(p) for p in (*private, batch / "workspaces")],
                "allowRead": [str(workspace), str(Path(sys.base_prefix).resolve())],
                "denyWrite": [
                    str(plugin),
                    *(str(workspace / name) for name in HOST_SETTINGS),
                ],
            },
            "network": {"allowedDomains": []},
            "credentials": {"envVars": [{"name": AUTH_VARIABLE, "mode": "deny"}]},
        },
    }


def read_instruction_log(log: Path) -> tuple[dict[str, dict], bool]:
    """Return load observations and whether the supervisor hooks ran at all."""
    try:
        events = [json.loads(line) for line in log.read_text().splitlines() if line]
    except (OSError, ValueError):
        return {}, False
    loads = [e for e in events if e.get("hook_event_name") == "InstructionsLoaded"]
    if any(not isinstance(e.get("file_path"), str) for e in loads):
        return {}, False
    observations: dict[str, dict] = {}
    for event in loads:
        path, digest = event["file_path"], event.get("sha256")
        previous = observations.get(path)
        observations[path] = {
            # Two different contents in one turn cannot both be the baseline.
            "sha256": digest if not previous or previous["sha256"] == digest else None,
            "imports": sorted(
                {c["file_path"] for c in loads if c.get("parent_file_path") == path}
            ),
        }
    return observations, any(e.get("hook_event_name") == "SessionStart" for e in events)


def tool_blocks(events: list[dict]) -> Iterator[dict]:
    """Content blocks of the stream; some events carry plain-text messages."""
    for event in events:
        message = event.get("message") if isinstance(event, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict):
                yield block


def named_reads(
    events: list[dict], workspace: Path, plugin: Path | None = None
) -> tuple[list[str], bool]:
    """Successful native reads only; other tools leave the inventory incomplete."""
    blocks = list(tool_blocks(events))
    results = {
        block["tool_use_id"]: block
        for block in blocks
        if block.get("type") == "tool_result" and block.get("tool_use_id")
    }
    reads, known = [], True
    for block in blocks:
        if block.get("type") != "tool_use":
            continue
        data = block.get("input", {})
        result = results.get(block.get("id"))
        path = data.get("file_path") if isinstance(data, dict) else None
        if (
            block.get("name") == "Read"
            and isinstance(path, str)
            and path
            and result is not None
            and not result.get("is_error", False)
        ):
            target = workspace / path
            reads.append(str(target))
            # The event names the requested path, not every alias of its
            # target. Do not resolve a link after the call and claim that
            # this was necessarily the target at read time.
            known = known and unaliased_path(target)
        else:
            # Searches and edits can read files too. Unknown tools are never
            # assumed read-free, even if their arguments name no file.
            known = False
    return reads, known


def unaliased_path(path: Path) -> bool:
    """Do not infer historical read targets by resolving current aliases."""
    try:
        return path == path.resolve(strict=True)
    except (OSError, RuntimeError):
        return False


def shell_reads(
    text: str, workspace: Path, plugin: Path | None = None
) -> tuple[list[str], bool]:
    """No access trace: arguments may be unread; helpers may read unnamed files.

    Parsing source or resolving paths afterwards cannot recover actual reads.
    """
    return [], False


def accept_boundary(adapter: Claude, revision: str) -> None:
    """Keep a host blocked until a passing proof matches it exactly."""
    proof = getattr(adapter, "boundary", None)
    proof = proof if isinstance(proof, dict) else {}
    checks = proof.get("checks")
    checks = checks if isinstance(checks, dict) else {}
    if (
        proof.get("scope") != "installed-host-boundary"
        or proof.get("host") != adapter.host
        or proof.get("hostVersion") != adapter.version
        or proof.get("configurationSha256") != adapter.configuration_sha256
        or proof.get("runtimeRevision") != revision
        or proof.get("runnerSha256") != runner_digest(adapter)
        or any(
            not isinstance(checks.get(name), dict)
            or checks[name].get("passed") is not True
            for name in score.RELEASE_BOUNDARY_CHECKS
        )
    ):
        raise HostError(
            f"{adapter.host} launch blocked: no passing boundary proof for this "
            "host version, package, configuration, and runner (run its live probe)"
        )
    adapter.boundary_sha256 = score.evidence_digest(proof)


class Claude:
    host = "claude-code"

    def __init__(self, model: str) -> None:
        self.model = model
        self.version = "not-started"
        self.conversation: str | None = None
        self.cost = 0.0
        self.instruction_files: list[str] = []
        self.instruction_observations: dict[str, dict] = {}
        self.instruction_measurement = "not-measured"
        self.read_measurement = "not-measured"
        self.plugin = score.PLUGIN
        self.boundary: dict | None = None
        self.configuration_sha256: str | None = None
        self.boundary_sha256: str | None = None

    def identify(self) -> None:
        """Fix executable, version, and configuration digest before any launch."""
        batch = self.plugin.parent.parent
        if (
            self.plugin != batch / "resources/specflow"
            or not (batch / "control").is_dir()
        ):
            raise HostError("Claude launch needs the external batch layout")
        if not os.environ.get(AUTH_VARIABLE):
            raise HostError(f"Claude launch needs the setup sign-in in {AUTH_VARIABLE}")
        if Path("/Library/Application Support/ClaudeCode").exists():
            raise HostError("managed Claude policy present; effective settings unknown")
        self.executable = shutil.which("claude")
        if not self.executable:
            raise HostError("claude executable not found")
        version = command([self.executable, "--version"], batch, timeout=30)
        if version.returncode or not version.stdout.split():
            raise HostError("could not identify installed Claude Code")
        self.version = version.stdout.split()[0]
        settings = normalize(
            claude_settings(batch, batch / "workspaces/session"),
            {
                str(batch / "workspaces/session"): "<workspace>",
                str(batch): "<batch>",
                str(Path.home().resolve()): "<home>",
                str(Path(sys.base_prefix).resolve()): "<python-runtime>",
                str(Path(sys.executable).resolve()): "<python>",
            },
        )
        self.configuration_sha256 = score.evidence_digest(
            {
                "settings": settings,
                "hook": HOOK,
                "version": self.version,
                "arguments": self.arguments("<budget>")[1:],
            }
        )

    def preflight(self) -> None:
        self.identify()
        accept_boundary(self, package_revision(self.plugin))

    @contextlib.contextmanager
    def batch(self, workspace: Path) -> Iterator[None]:
        yield

    def new_conversation(self) -> None:
        self.conversation = None
        self.cost = 0.0

    def arguments(self, budget: str) -> list[str]:
        """Fixed launch flags; batch-relative so the digest is machine-neutral."""
        return [
            getattr(self, "executable", "claude"),
            "-p",
            "--plugin-dir",
            "../../resources/specflow",
            "--add-dir",
            "../../resources/specflow",
            "--settings",
            "../../control/settings.json",
            "--setting-sources",
            "project,local",
            "--permission-mode",
            "dontAsk",
            "--max-budget-usd",
            budget,
            "--output-format",
            "stream-json",
            "--verbose",
        ]

    def launch(self, prompt: str, workspace: Path, budget: float) -> list[dict]:
        """One host process under the generated configuration; no shell."""
        batch = self.plugin.parent.parent
        control, home = batch / "control", batch / "home"
        if workspace.parent != batch / "workspaces":
            raise HostError("workspace is outside the batch")
        # Project and local settings load on every launch: only the committed
        # fixture bytes are admitted, never something an earlier turn wrote.
        for name in HOST_SETTINGS:
            path = workspace / name
            current = path.read_text() if path.is_file() else None
            try:
                committed = git_workspace(workspace, "show", f"HEAD:{name}")
            except HostError:
                committed = None
            if (current is None) != (committed is None) or (
                current is not None and current.strip() != committed
            ):
                raise HostError(f"workspace host settings differ from fixture: {name}")
        for folder in (control / "claude-home", home):
            folder.mkdir(mode=0o700, exist_ok=True)
        (control / "hook.py").write_text(HOOK)
        (control / "settings.json").write_text(
            json.dumps(claude_settings(batch, workspace), indent=2)
        )
        (control / "instructions.jsonl").write_text("")
        args = [*self.arguments(str(budget)), "--model", self.model]
        if self.conversation:
            args += ["--resume", self.conversation]
        env = {
            "PATH": str(Path(sys.executable).resolve().parent)
            + os.pathsep
            + os.defpath,
            "HOME": str(home),
            "CLAUDE_CONFIG_DIR": str(control / "claude-home"),
            AUTH_VARIABLE: os.environ[AUTH_VARIABLE],
            "CLAUDE_NESTED": "1",
            "_CLAUDE_NOTIFY_QUIET": "1",
            "LANG": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        result = command([*args, prompt], workspace, env)
        if result.returncode:
            raise HostError("Claude turn failed")
        try:
            events = [json.loads(line) for line in result.stdout.splitlines() if line]
        except ValueError:
            raise HostError("Claude emitted invalid stream output") from None
        init = next(
            (
                e
                for e in events
                if e.get("type") == "system" and e.get("subtype") == "init"
            ),
            {},
        )
        if "specflow:spec-workflow" not in init.get("skills", []):
            raise HostError("Claude did not load specflow")
        if (
            not init.get("model")
            or init.get("claude_code_version") != self.version
            or not init.get("session_id")
        ):
            raise HostError("Claude omitted model, version, or conversation evidence")
        if self.conversation and self.conversation != init["session_id"]:
            raise HostError("Claude resumed a different conversation")
        self.model, self.conversation = init["model"], init["session_id"]
        return events

    def turn(self, prompt: str, workspace: Path) -> tuple[str, list[str]]:
        self.preflight()
        remaining = SESSION_BUDGET_USD - self.cost
        if remaining <= 0:
            raise HostError("session spending cap reached")
        expected_roots = [
            str(workspace / name)
            for name in ROOT_INSTRUCTIONS
            if (workspace / name).is_file()
        ]
        events = self.launch(prompt, workspace, remaining)
        final = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if (
            final.get("is_error")
            or final.get("permission_denials")
            or final.get("subtype") != "success"
        ):
            raise HostError(
                "Claude turn did not succeed or requested denied permissions"
            )
        cost = final.get("total_cost_usd")
        if not isinstance(cost, (int, float)) or isinstance(cost, bool):
            raise HostError("Claude omitted cost evidence")
        # ponytail: always adds. If the host reports a cumulative figure on a
        # resumed conversation this over-counts and stops a session early;
        # the other reading could let a session exceed its cap.
        self.cost += cost
        batch = self.plugin.parent.parent
        observations, hooked = read_instruction_log(
            batch / "control/instructions.jsonl"
        )
        if not hooked:
            raise HostError("Claude ignored the supervisor settings")
        self.instruction_observations = observations
        # A root fixture instruction the host did not report means a lost event.
        self.instruction_measurement = (
            "measured"
            if all(path in observations for path in expected_roots)
            else "not-measured"
        )
        reads, known = named_reads(events, workspace, self.plugin)
        self.read_measurement = "measured" if known else "not-measured"
        if not isinstance(final.get("result"), str):
            raise HostError("Claude omitted the final reply")
        return final["result"], reads


@score.deadline(SESSION_TIMEOUT)
def play_session(adapter: Claude, session: dict, workspace: Path, record: dict) -> None:
    adapter.new_conversation()
    baseline = snapshot(workspace)
    expected = baseline.copy()
    plugin = getattr(adapter, "plugin", score.PLUGIN)
    verify_plugin(plugin, record["runtimeRevision"])
    plugin_files = snapshot(plugin)
    inventories, reads_known = [], []
    try:
        for turn_number, turn in enumerate(session["turns"], 1):
            score.remaining_timeout(TURN_TIMEOUT)
            if "expects" in turn and (
                not record["messages"]
                or not re.search(turn["expects"], record["messages"][-1])
            ):
                record["brokenAt"] = turn_number
                break
            if edit := turn.get("edit"):
                write_files(workspace, {edit["path"]: edit["text"]})
                expected[edit["path"]] = edit["text"]
            verify_workspace(workspace)
            prompt = turn["developer"]
            if turn_number == 1:
                prompt = (
                    "Use the installed specflow spec-workflow skill for this request.\n"
                    + prompt
                )
            adapter.instruction_observations = {}
            adapter.instruction_measurement = "not-measured"
            adapter.read_measurement = "not-measured"
            message, reads = adapter.turn(prompt, workspace)
            reads_known.append(adapter.read_measurement == "measured")
            record["messages"].append(message)
            record["filesRead"].append(
                [p.removeprefix(str(workspace) + "/") for p in reads]
            )
            inventories.append(
                classify_instructions(
                    getattr(adapter, "instruction_observations", {}),
                    complete=getattr(adapter, "instruction_measurement", "not-measured")
                    == "measured",
                    workspace=workspace,
                    expected=expected,
                    plugin=plugin,
                    plugin_files=plugin_files,
                )
            )
        score.remaining_timeout(TURN_TIMEOUT)
        record["status"] = capture_status(
            workspace, plugin=getattr(adapter, "plugin", score.PLUGIN)
        )
        if record["status"] is None:
            record["notRun"] = "status helper could not run"
    except (HostError, OSError, ValueError, subprocess.SubprocessError) as error:
        record["notRun"] = str(error)
    finally:
        current = snapshot(workspace)
        record["files"] = [
            {"path": p, "text": text}
            for p, text in current.items()
            if baseline.get(p) != text
        ]
        record["unchanged"] = [p for p in current if baseline.get(p) == current[p]]
        record["model"], record["hostVersion"] = adapter.model, adapter.version
        record["instructionFiles"] = sorted(
            {p for i in inventories for p in i["instructionFiles"]}
        )
        record["instructionMeasurement"] = (
            "measured"
            if inventories and all(i["complete"] for i in inventories)
            else "not-measured"
        )
        record["readMeasurement"] = (
            "measured" if reads_known and all(reads_known) else "not-measured"
        )
        reported = {
            "costUsd": getattr(adapter, "cost", None),
            "tokensPerTurn": getattr(adapter, "usage", None),
        }
        record["notes"] = (
            record.get("notes", "")
            + f" Reported usage: {json.dumps(reported, sort_keys=True)}."
            + "\n"
            + score.EVIDENCE_PREFIX
            + json.dumps(
                {
                    "instructions": inventories,
                    "configurationSha256": getattr(
                        adapter, "configuration_sha256", None
                    ),
                    "boundarySha256": getattr(adapter, "boundary_sha256", None),
                },
                sort_keys=True,
            )
        )


@score.deadline(BATCH_TIMEOUT)
def run_batch(
    adapter: Claude,
    name: str,
    out: Path,
    *,
    session_dir: Path = SESSIONS,
    eval_dir: Path = score.EVALS,
) -> int:
    sessions = sessions_for(name, session_dir)
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    verify_plugin(score.PLUGIN, revision)
    fixture = FIXTURES / score.safe_path(sessions[0][1]["fixture"])
    if not fixture.resolve().is_relative_to(FIXTURES.resolve()):
        raise score.RecordError("fixture leaves the fixture root")
    fixture_revision = (
        score.git("rev-parse", f"HEAD:{fixture.relative_to(ROOT).as_posix()}")
        .decode()
        .strip()
    )
    # Read committed fixture bytes. Approval hashes are never regenerated.
    initial = score.tree_files(fixture_revision)
    verify_plugin(fixture, fixture_revision)
    records, completed, code = {}, {}, 0
    with external_batch(revision) as root:
        adapter.plugin = root / "resources/specflow"
        replacements = {
            str(root): "<batch>",
            str(ROOT): "<repository>",
            str(score.PLUGIN): "<plugin>",
            str(adapter.plugin): "<plugin>",
            str(Path.home()): "<home>",
        }
        startup_error = None
        try:
            adapter.preflight()
        except (HostError, OSError, ValueError, subprocess.SubprocessError) as error:
            startup_error = str(error)
        with contextlib.ExitStack() as resources:
            batch_started = False
            for session_path, session in sessions:
                path, number = reserve_record(out, adapter.host, session["name"])
                record = {
                    "schemaVersion": 1,
                    "host": adapter.host,
                    "hostVersion": adapter.version,
                    "mode": "automated",
                    "session": session["name"],
                    "model": adapter.model,
                    "instructionFiles": [],
                    "runtimeRevision": revision,
                    "fixtureRevision": fixture_revision,
                    "sessionRevision": score.object_id(session_path.read_bytes()),
                    "status": None,
                    "messages": [],
                    "filesRead": [],
                    "files": [],
                    "unchanged": [],
                    "readMeasurement": "not-measured",
                    "instructionMeasurement": "not-measured",
                    "releaseEvidence": False,
                    "notes": (
                        f"Requested model: {adapter.model}; reported identity unverified until launch. "
                        f"Limits: {MAX_SESSION_TURNS} turns; {TURN_TIMEOUT}s per turn; "
                        f"{SESSION_TIMEOUT}s per session; {BATCH_TIMEOUT}s per batch."
                    ),
                }
                workspace = root / "workspaces" / session["name"]
                workspace.mkdir()
                replacements[str(workspace)] = "<workspace>"
                parent = session.get("continues")
                if parent:
                    record["continuesRun"] = {
                        "host": adapter.host,
                        "session": parent,
                        "n": records[parent],
                    }
                # A killed process leaves valid not-run evidence, never an empty file.
                score.write_json(
                    path,
                    normalize(
                        {**record, "notRun": "runner interrupted before completion"},
                        replacements,
                    ),
                )
                try:
                    if startup_error:
                        raise HostError(startup_error)
                    score.remaining_timeout(TURN_TIMEOUT)
                    if parent and parent not in completed:
                        raise HostError("continuation parent did not finish")
                    write_files(workspace, completed[parent] if parent else initial)
                    initialize_workspace(workspace)
                    if not batch_started:
                        try:
                            resources.enter_context(adapter.batch(workspace))
                            # A host may install its own verified plugin copy.
                            replacements[str(adapter.plugin)] = "<plugin>"
                        except (
                            HostError,
                            OSError,
                            ValueError,
                            subprocess.SubprocessError,
                        ) as error:
                            startup_error = str(error)
                            raise
                        batch_started = True
                    play_session(adapter, session, workspace, record)
                    if not record.get("notRun") and not record.get("brokenAt"):
                        completed[session["name"]] = snapshot(workspace)
                except (
                    HostError,
                    OSError,
                    ValueError,
                    subprocess.SubprocessError,
                ) as error:
                    record["notRun"] = str(error)
                except KeyboardInterrupt:
                    startup_error = "runner interrupted"
                    record["notRun"] = startup_error
                normalized = normalize(record, replacements)
                score.validate_record(normalized)
                if "notRun" not in normalized:
                    try:
                        session_code = score.score_record(
                            normalized, eval_dir, results=out
                        )
                        code = max(code, session_code)
                        if session_code:
                            completed.pop(session["name"], None)
                        score.remaining_timeout(TURN_TIMEOUT)
                    except (
                        score.RecordError,
                        OSError,
                        ValueError,
                        subprocess.SubprocessError,
                    ) as error:
                        normalized["notRun"] = f"scoring could not finish: {error}"
                        normalized.pop("scores", None)
                        code = max(
                            code,
                            1
                            if isinstance(error, subprocess.TimeoutExpired)
                            and normalized["messages"]
                            else 2,
                        )
                    except KeyboardInterrupt:
                        startup_error = "runner interrupted during scoring"
                        normalized["notRun"] = startup_error
                        normalized.pop("scores", None)
                        code = max(code, 1 if normalized["messages"] else 2)
                else:
                    code = max(code, 2 if not normalized["messages"] else 1)
                if normalized.get("notRun"):
                    completed.pop(session["name"], None)
                score.write_json(path, normalized)
                records[session["name"]] = number
                print(path)
    return code


# Runs through the host's shell tool. Only EACCES/EPERM counts as a denial.
SHELL_PROBE = r"""
import errno, json, os, subprocess, sys
p = json.load(open("probe.json"))
def denied(path, mode):
    try:
        with open(path, mode) as handle:
            handle.read() if mode == "r" else handle.write("x")
    except OSError as error:
        return error.errno in (errno.EACCES, errno.EPERM)
    return False
out = {
    "shell-control-read-denied": denied(p["control"], "r"),
    "shell-home-read-denied": denied(p["home"], "r"),
    "shell-other-workspace-read-denied": denied(p["other"], "r"),
    "shell-symlink-read-denied": denied(p["read_link"], "r"),
    "shell-plugin-write-denied": denied(p["manifest"], "a"),
    "shell-symlink-write-denied": denied(p["write_link"], "a"),
    "tool-secret-environment-denied": not os.environ.get(p["variable"]),
    "plugin-read": os.access(p["manifest"], os.R_OK) and bool(open(p["manifest"]).read()),
}
helper = subprocess.run(
    [sys.executable, "-B", p["helper"], "status", "--json"],
    capture_output=True, text=True,
)
try:
    out["helper-status"] = (
        helper.returncode in (0, 1) and json.loads(helper.stdout)["statusVersion"] == 1
    )
except (ValueError, KeyError):
    out["helper-status"] = False
print(json.dumps({p["report"]: out}))
"""
NATIVE_PROBES = {
    "native-control-read-denied": ("Read", "control"),
    "native-home-read-denied": ("Read", "home"),
    "native-other-workspace-read-denied": ("Read", "other"),
    "native-symlink-read-denied": ("Read", "read_link"),
    "native-plugin-write-denied": ("Write", "plugin_new"),
    "native-symlink-write-denied": ("Write", "link_new"),
    "plugin-read": ("Read", "manifest"),
}
PROBE_COMMAND = "python3 -I -B probe.py"


def prepare_probe(
    batch: Path,
    plugin: Path,
    variable: str,
    instructions: dict[str, str],
    home_sentinel: Path | None = None,
) -> tuple[Path, dict[str, str], dict[str, str], str]:
    """Build the probe workspace: sentinels, symlinks, and the shell script.

    Native writes create new files, one through a symlinked folder, so a
    refusal cannot come from a missing prior read or a patch context mismatch.
    """
    workspace = batch / "workspaces/probe"
    other, home = batch / "workspaces/other", batch / "home"
    for folder in (workspace, other, home):
        folder.mkdir(mode=0o700, exist_ok=True)
    secret = os.urandom(16).hex()
    payload = {
        "control": str(batch / "control/sentinel.txt"),
        "home": str(home_sentinel or home / "sentinel.txt"),
        "other": str(other / "sentinel.txt"),
        "read_link": str(workspace / "control-link"),
        "write_link": str(workspace / "plugin-link"),
        "link_new": str(workspace / "plugin-folder-link/probe-link-write.txt"),
        "manifest": str(plugin / "plugin.json"),
        "plugin_new": str(plugin / "probe-write.txt"),
        "helper": str(plugin / "skills/spec-workflow/scripts/validate_spec.py"),
        "variable": variable,
        "report": os.urandom(8).hex(),
    }
    for key in ("control", "home", "other"):
        Path(payload[key]).write_text(f"Synthetic sentinel {secret}\n")
    Path(payload["read_link"]).symlink_to(payload["control"])
    Path(payload["write_link"]).symlink_to(payload["manifest"])
    Path(payload["link_new"]).parent.symlink_to(plugin, target_is_directory=True)
    fixture = {
        **instructions,
        "probe.py": SHELL_PROBE,
        "probe.json": json.dumps(payload),
    }
    write_files(workspace, fixture)
    initialize_workspace(workspace)
    return workspace, payload, fixture, secret


def shell_probe_checks(
    outputs: list[str],
    workspace: Path,
    payload: dict[str, str],
    extra: tuple[str, ...] = (),
) -> dict[str, dict]:
    """Checks decided by the supervisor script's own errno report.

    The script and its report token sit in the model-writable workspace, so the
    report counts only when both files are unchanged and the command ran once.
    """
    shell, reported = {}, False
    intact = (workspace / "probe.py").read_text() == SHELL_PROBE and (
        workspace / "probe.json"
    ).read_text() == json.dumps(payload)
    trusted = len(outputs) == 1 and intact
    for line in outputs[0].splitlines() if trusted else []:
        try:
            found = json.loads(line)[payload["report"]]
        except (ValueError, KeyError, TypeError):
            continue
        shell, reported = (found if isinstance(found, dict) else {}), True
    # A missing report must say why, or a failed probe cannot be diagnosed.
    why = ""
    if not reported:
        tail = normalize(
            outputs[0][-400:] if len(outputs) == 1 else "",
            {
                str(workspace.parent.parent): "<batch>",
                str(Path.home().resolve()): "<home>",
            },
        )
        why = (
            f" (no report: probe command ran {len(outputs)} time(s) as "
            f"instructed; script files unchanged={intact}; output tail: {tail!r})"
        )
    return {
        name: {
            "passed": shell.get(name) is True,
            "evidence": "errno result of the supervisor script run by the "
            f"sandboxed shell tool: {shell.get(name)}{why}",
        }
        for name in sorted(score.RELEASE_BOUNDARY_CHECKS)
        if name.startswith("shell-")
        or name in ("helper-status", "tool-secret-environment-denied", *extra)
    }


@score.deadline(TURN_TIMEOUT)
def boundary_probe(model: str, *, scratch: Path = EXTERNAL_SCRATCH) -> dict:
    """Live installed-host proof with synthetic sentinels; never a credential.

    The model only issues the listed tool calls. Every verdict comes from the
    host's tool stream, the script's errno results, and files on disk; nothing
    the model says about isolation is read.
    """
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    adapter = Claude(model)
    with external_batch(revision, scratch=scratch) as batch:
        adapter.plugin = batch / "resources/specflow"
        adapter.identify()
        workspace, payload, fixture, secret = prepare_probe(
            batch,
            adapter.plugin,
            AUTH_VARIABLE,
            {
                "CLAUDE.md": "Synthetic fixture instruction.\n\n@imported.md\n",
                "imported.md": "Synthetic imported instruction.\n",
            },
        )
        steps = [
            f"{tool} tool on {payload[key]}"
            + (" with content: probe" if tool == "Write" else "")
            for tool, key in NATIVE_PROBES.values()
        ]
        steps.append(f"Bash tool with exactly this command: {PROBE_COMMAND}")
        prompt = (
            "This is a permission self-test. Make each tool call below once, in "
            "order. Some are denied; that is expected. Never retry, never use a "
            "different tool or path, and continue after a denial. Then reply: done.\n"
            + "\n".join(f"{n}. {step}" for n, step in enumerate(steps, 1))
        )
        events = adapter.launch(prompt, workspace, 1)
        raw = json.dumps(events)
        final = next((e for e in reversed(events) if e.get("type") == "result"), {})
        # Only the host's own permission-denial list counts as a denial: a tool
        # can also fail for reasons that say nothing about the generated rules.
        refused = {
            d.get("tool_use_id")
            for d in final.get("permission_denials") or []
            if isinstance(d, dict)
        }
        calls, errors, outputs, shell_runs = {}, {}, {}, []
        for block in tool_blocks(events):
            if block.get("type") == "tool_use":
                data = block.get("input", {})
                calls[
                    (block.get("name"), data.get("file_path") or data.get("command"))
                ] = block.get("id")
                if block.get("name") == "Bash" and "probe.py" in str(
                    data.get("command")
                ):
                    shell_runs.append(block.get("id"))
            elif block.get("type") == "tool_result":
                errors[block.get("tool_use_id")] = block.get("is_error") is True
                content = block.get("content")
                outputs[block.get("tool_use_id")] = (
                    content
                    if isinstance(content, str)
                    else "\n".join(
                        part.get("text", "")
                        for part in content or []
                        if isinstance(part, dict)
                    )
                )
        checks = {}

        def check(name: str, passed: bool, evidence: str) -> None:
            checks[name] = {"passed": bool(passed), "evidence": evidence}

        for name, (tool, key) in NATIVE_PROBES.items():
            call = calls.get((tool, payload[key]))
            failed = errors.get(call)
            wanted = name != "plugin-read"
            check(
                name,
                call is not None
                and failed is wanted
                and (call in refused) is wanted
                and secret not in raw,
                f"{tool} on <{key}>: host result error={failed}; in the host's "
                f"permission denials={call in refused}; sentinel in "
                f"stream={secret in raw}",
            )
        exact = calls.get(("Bash", PROBE_COMMAND))
        # The report token is readable by the model, so the script's report
        # counts only when the turn made the instructed calls and no other:
        # nothing could then replace the script or change the shell's folder.
        instructed = {
            *((tool, payload[key]) for tool, key in NATIVE_PROBES.values()),
            ("Bash", PROBE_COMMAND),
        }
        made = sum(1 for b in tool_blocks(events) if b.get("type") == "tool_use")
        checks.update(
            shell_probe_checks(
                [outputs.get(run, "") for run in shell_runs]
                if shell_runs == [exact]
                and set(calls) == instructed
                and made == len(instructed)
                else [],
                workspace,
                payload,
            )
        )
        observations, hooked = read_instruction_log(
            batch / "control/instructions.jsonl"
        )
        inventory = classify_instructions(
            observations,
            complete=hooked,
            workspace=workspace,
            expected=fixture,
            plugin=adapter.plugin,
            plugin_files=snapshot(adapter.plugin),
        )
        loaded = {str(workspace / name) for name in ("CLAUDE.md", "imported.md")}
        check(
            "instruction-inventory",
            inventory["classification"] == "clean" and set(observations) == loaded,
            f"load hook reported {len(observations)} files, classified "
            f"{inventory['classification']}",
        )
        check(
            "fixture-instructions",
            loaded <= set(observations),
            "fixture CLAUDE.md and its import appear in the load hook log",
        )
        check("plugin-activation", True, "init event lists specflow:spec-workflow")
        intact = (
            package_revision(adapter.plugin) == revision
            and not Path(payload["plugin_new"]).exists()
        )
        for name, result in checks.items():
            if name.endswith("write-denied"):
                result["passed"] = result["passed"] and intact
                result["evidence"] += f"; plugin tree intact={intact}"
        check(
            "effective-settings",
            hooked
            and all(c["passed"] for n, c in checks.items() if n.endswith("-denied")),
            "supervisor hook marker present and every generated denial observed",
        )
        normalized = normalize(checks, {str(batch): "<batch>"})
        proof = {
            "scope": "installed-host-boundary",
            "host": adapter.host,
            "hostVersion": adapter.version,
            "model": adapter.model,
            "runtimeRevision": revision,
            "configurationSha256": adapter.configuration_sha256,
            "runnerSha256": runner_digest(adapter),
            "checks": normalized,
        }
    proof["checks"]["cleanup"] = {
        "passed": not batch.exists(),
        "evidence": "private batch directory absent after the probe",
    }
    return proof


def main(argv: list[str] | None = None, adapter_type: type = Claude) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", nargs="?")
    parser.add_argument("--model", required=True, help="explicit model; never auto")
    parser.add_argument("--out", type=Path, default=score.EVALS / "results")
    parser.add_argument("--boundary-proof", type=Path, help="reviewed probe output")
    parser.add_argument(
        "--evals", type=Path, default=score.EVALS, help="folder of evals to score"
    )
    parser.add_argument(
        "--probe-boundary",
        action="store_true",
        help="run the live synthetic boundary probe and print its proof",
    )
    args = parser.parse_args(argv)
    try:
        if args.model in {"auto", "default"}:
            raise score.RecordError("choose an explicit model")
        if args.probe_boundary:
            if adapter_type is not Claude:
                raise score.RecordError("this host has its own probe command")
            with interruption_signals():
                proof = boundary_probe(args.model)
            print(json.dumps(proof, indent=2, sort_keys=True))
            return int(
                not all(
                    proof["checks"].get(name, {}).get("passed") is True
                    for name in score.RELEASE_BOUNDARY_CHECKS
                )
            )
        if not args.session:
            raise score.RecordError("name a session")
        adapter = adapter_type(args.model)
        if args.boundary_proof:
            adapter.boundary = score.read_json(args.boundary_proof)
        with interruption_signals():
            return run_batch(adapter, args.session, args.out, eval_dir=args.evals)
    except (
        HostError,
        score.RecordError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"runner: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("runner: interrupted before a run could be recorded", file=sys.stderr)
        return 2


@contextlib.contextmanager
def interruption_signals() -> Iterator[None]:
    """Turn termination into normal unwinding; never change callers' handlers."""

    def interrupt(signum: int, frame: object) -> None:
        raise KeyboardInterrupt

    previous = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        for number in previous:
            signal.signal(number, interrupt)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
