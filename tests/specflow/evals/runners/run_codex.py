#!/usr/bin/env python3
"""Codex batch setup; live turns remain blocked pending T-056's launch contract."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import run_claude as runner
import score

PROBE_CHECKS = {
    "workspace-read",
    "workspace-write",
    "plugin-read",
    "helper-status",
    "control-read-denied",
    "home-read-denied",
    "other-workspace-read-denied",
    "temp-read-denied",
    "plugin-write-denied",
    "symlink-read-denied",
    "symlink-write-denied",
}
# Runs inside the sandbox; every attempted file access targets disposable data.
# Python and child-shell operations are both checked. These are NOT Codex native
# file-tool or loaded-instruction measurements.
PROBE_SCRIPT = r"""
import errno, json, pathlib, subprocess, sys
p = json.loads(sys.argv[1])
checks = {}
def read_check(name: str, path: str, denied: bool = False) -> None:
    try:
        pathlib.Path(path).read_bytes()
        direct = not denied
    except OSError as error:
        direct = denied and error.errno in (errno.EACCES, errno.EPERM)
    shell = subprocess.run(['/bin/cat', path], capture_output=True, timeout=10)
    checks[name] = bool(direct and ((shell.returncode != 0) if denied else
                                    (shell.returncode == 0)))
    if not checks[name]:
        print(f'{name}: direct_ok={direct}, child_exit={shell.returncode}; '
              + shell.stderr.decode(errors='replace')[-500:], file=sys.stderr)
def write_check(name: str, path: str, denied: bool = False) -> None:
    try:
        with open(path, 'a') as stream:
            stream.write('synthetic probe write\n')
        direct = not denied
    except OSError as error:
        direct = denied and error.errno in (errno.EACCES, errno.EPERM)
    shell = subprocess.run(['/bin/sh', '-c', 'printf probe >> "$1"', 'probe', path],
                           capture_output=True, timeout=10)
    checks[name] = bool(direct and ((shell.returncode != 0) if denied else
                                    (shell.returncode == 0)))
    if not checks[name]:
        print(f'{name}: direct_ok={direct}, child_exit={shell.returncode}; '
              + shell.stderr.decode(errors='replace')[-500:], file=sys.stderr)
read_check('workspace-read', p['instruction'])
write_check('workspace-write', p['output'])
read_check('plugin-read', p['manifest'])
for name, key in [('control-read-denied', 'control'), ('home-read-denied', 'home'),
                  ('other-workspace-read-denied', 'other'), ('temp-read-denied', 'temp'),
                  ('symlink-read-denied', 'read_link')]:
    read_check(name, p[key], True)
write_check('plugin-write-denied', p['manifest'], True)
write_check('symlink-write-denied', p['write_link'], True)
helper = subprocess.run([sys.executable, '-B', p['helper'], 'status', '--json'],
                        capture_output=True, text=True, timeout=30)
try:
    state = json.loads(helper.stdout)
    checks['helper-status'] = (helper.returncode == 0 and state.get('statusVersion') == 1
                               and state.get('problems') == [])
except ValueError:
    checks['helper-status'] = False
if not checks['helper-status']:
    print('helper-status: ' + helper.stderr[-1000:] + helper.stdout[-1000:], file=sys.stderr)
print(json.dumps(checks, sort_keys=True))
"""


def probe_passed(checks: dict) -> bool:
    return set(checks) == PROBE_CHECKS and all(
        value is True for value in checks.values()
    )


def prompt_summary(raw: str, marker: str) -> dict:
    """Inspect rendering without publishing its contents or asserting completeness."""
    try:
        inputs = json.loads(raw)
    except ValueError:
        inputs = None
    valid = isinstance(inputs, list) and all(isinstance(item, dict) for item in inputs)
    return {
        "scope": "instruction-rendering-only",
        "releaseEvidence": False,
        "instructionMeasurement": "not-measured",
        "fixtureIncluded": valid
        and any(
            isinstance(block, dict)
            and isinstance(block.get("text"), str)
            and marker in block["text"]
            for item in inputs
            for block in (
                item["content"] if isinstance(item.get("content"), list) else []
            )
        ),
        "inputCount": len(inputs) if valid else 0,
        "renderSha256": hashlib.sha256(raw.encode()).hexdigest(),
    }


def diagnostic_categories(text: str) -> list[str]:
    """Publish only fixed failure labels, never arbitrary host diagnostic text."""
    lower = text.lower()
    categories = {
        "permission-denied": (
            "operation not permitted",
            "permission denied",
            "sandbox_apply",
        ),
        "authentication": ("authentication", "not logged in", "login", "auth.json"),
        "configuration": (
            "configuration",
            "config.toml",
            "unknown field",
            "invalid value",
        ),
        "model": ("model",),
        "network": ("network", "connect", "dns", "request"),
        "missing-file": ("no such file", "not found"),
        "temporary-home-aliases": (
            "refusing to create helper binaries under temporary dir",
        ),
    }
    return [
        name
        for name, patterns in categories.items()
        if any(p in lower for p in patterns)
    ]


def prepare_probe(batch: Path) -> dict[str, str]:
    """Prepare disposable synthetic targets; never read a real credential."""
    for ancestor in (batch, *batch.parents):
        for name in (
            "AGENTS.md",
            "AGENTS.override.md",
            "CLAUDE.md",
            ".codex/config.toml",
        ):
            candidate = ancestor / name
            if candidate.exists() or candidate.is_symlink():
                raise runner.HostError("unexpected ancestor instructions/configuration")
    workspace = batch / "workspaces/probe"
    home = batch / "control/codex-home"
    plugin = home / "plugins/specflow"
    for folder in (workspace, home, batch / "workspaces/other", batch / "resources"):
        folder.mkdir(parents=True, mode=0o700, exist_ok=True)
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    shutil.copytree(score.PLUGIN, plugin, symlinks=True)
    runner.verify_plugin(plugin, revision)
    if any(path.is_symlink() for path in plugin.rglob("*")):
        raise runner.HostError("probe requires a plugin tree without symlinks")
    payload = {
        "workspace": str(workspace),
        "codex_home": str(home),
        "plugin": str(plugin),
        "runtimeRevision": revision,
        "instruction": str(workspace / "AGENTS.md"),
        "output": str(workspace / "output.txt"),
        "manifest": str(plugin / "plugin.json"),
        "helper": str(plugin / "skills/spec-workflow/scripts/validate_spec.py"),
        "control": str(batch / "control/sentinel.txt"),
        "home": str(home / "synthetic-sign-in.txt"),
        "other": str(batch / "workspaces/other/sentinel.txt"),
        "temp": str(batch / "outside-workspace.txt"),
        "read_link": str(workspace / "control-link"),
        "write_link": str(workspace / "plugin-link"),
    }
    for key in ("instruction", "output", "control", "home", "other", "temp"):
        path = Path(payload[key])
        path.write_text("Synthetic specflow boundary sentinel.\n")
        path.chmod(0o600)
    Path(payload["read_link"]).symlink_to(payload["control"])
    Path(payload["write_link"]).symlink_to(payload["manifest"])
    return payload


def probe_config(payload: dict[str, str], *, git_executable: Path) -> str:
    """Candidate profile from https://learn.chatgpt.com/docs/permissions."""
    runtime = Path(sys.base_prefix).resolve()
    if runtime in {Path("/"), Path.home().resolve(), Path("/private/tmp")}:
        raise runner.HostError("Python runtime read scope is too broad")
    rules = {
        ":root": "deny",
        ":minimal": "read",
        ":tmpdir": "deny",
        ":slash_tmp": "deny",
        str(Path.home().resolve()): "deny",
        payload["workspace"]: "write",
        payload["plugin"]: "read",
        str(runtime): "read",
        str(git_executable): "read",
    }
    return "\n".join(
        [
            'default_permissions = "specflow-probe"',
            "[permissions.specflow-probe]",
            'extends = ":workspace"',
            "[permissions.specflow-probe.filesystem]",
            *(f'{json.dumps(path)} = "{access}"' for path, access in rules.items()),
            "[permissions.specflow-probe.network]",
            "enabled = false",
            "",
        ]
    )


@score.deadline(180)
def boundary_probe(
    codex: Path,
    *,
    git_executable: Path,
    scratch: Path = Path("/private/tmp"),
    inspect_instructions: bool = False,
) -> dict:
    """Developer-run macOS shell probe; deliberately separate from live preflight."""
    if any(key.startswith("GIT_") for key in os.environ):
        raise runner.HostError("remove inherited GIT_ variables before the probe")
    if sys.platform != "darwin":
        raise runner.HostError("this boundary probe requires macOS")
    codex = codex.resolve(strict=True)
    git_executable = git_executable.resolve(strict=True)
    if (
        git_executable.name != "git"
        or not git_executable.is_file()
        or not os.access(git_executable, os.X_OK)
    ):
        raise runner.HostError("select an executable Git file named git")
    with tempfile.TemporaryDirectory(prefix="specflow-evals-", dir=scratch) as folder:
        batch = Path(folder).resolve()
        payload = prepare_probe(batch)
        marker = "specflow-fixture-" + uuid.uuid4().hex
        if inspect_instructions:
            Path(payload["instruction"]).write_text(
                marker + "\nSynthetic fixture instructions.\n"
            )
        workspace, home = Path(payload["workspace"]), Path(payload["codex_home"])
        config = probe_config(payload, git_executable=git_executable)
        (home / "config.toml").write_text(config)
        (home / "config.toml").chmod(0o600)
        env = {
            "PATH": str(git_executable.parent) + os.pathsep + os.defpath,
            "HOME": str(batch / "control/empty-home"),
            "CODEX_HOME": str(home),
            "TMPDIR": str(batch),
            "LANG": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        Path(env["HOME"]).mkdir(mode=0o700)
        for args in (
            [str(git_executable), "init"],
            [str(git_executable), "add", "--all"],
            [
                str(git_executable),
                "-c",
                "user.name=specflow probe",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Synthetic boundary probe",
            ],
        ):
            result = runner.command(args, workspace, env, 30)
            if result.returncode:
                raise runner.HostError(
                    "probe Git setup failed; no sandbox command started"
                )
        for args, expected in (
            ([str(git_executable), "rev-parse", "--show-toplevel"], workspace),
            (
                [str(git_executable), "rev-parse", "--absolute-git-dir"],
                workspace / ".git",
            ),
        ):
            result = runner.command(args, workspace, env, 30)
            if result.returncode or Path(result.stdout.strip()).resolve() != expected:
                raise runner.HostError("probe workspace is not its own Git root")
        version = runner.command([str(codex), "--version"], workspace, env, 10)
        if version.returncode:
            raise runner.HostError("could not identify installed Codex")
        git_version = runner.command(
            [str(git_executable), "--version"], workspace, env, 10
        )
        if git_version.returncode or not git_version.stdout.startswith("git version "):
            raise runner.HostError("could not identify selected Git")
        args = (
            [
                str(codex),
                "debug",
                "prompt-input",
                "Synthetic instruction discovery check.",
            ]
            if inspect_instructions
            else [
                str(codex),
                "sandbox",
                "--permission-profile",
                "specflow-probe",
                "--include-managed-config",
                "--cd",
                str(workspace),
                "--",
                str(Path(sys.executable).resolve()),
                "-I",
                "-B",
                "-c",
                PROBE_SCRIPT,
                json.dumps(payload),
            ]
        )
        result = runner.command(
            args,
            workspace,
            env,
            90,
        )
        try:
            checks = json.loads(result.stdout)
        except ValueError:
            checks = {}
        if not isinstance(checks, dict):
            checks = {}
        normalized_config = runner.normalize(
            config,
            {
                str(batch): "<batch>",
                str(Path.home()): "<home>",
                str(Path(sys.base_prefix).resolve()): "<python-runtime>",
                str(git_executable): "<git-runtime>",
            },
        )
        report = {
            "scope": "synthetic-shell-boundary-only",
            "releaseEvidence": False,
            "hostVersion": version.stdout.strip(),
            "pythonVersion": sys.version.split()[0],
            "gitVersion": git_version.stdout.strip(),
            "gitRuntimeSha256": hashlib.sha256(git_executable.read_bytes()).hexdigest(),
            "runtimeRevision": payload["runtimeRevision"],
            "generatedPolicy": normalized_config,
            "policySha256": hashlib.sha256(normalized_config.encode()).hexdigest(),
            "probeSha256": hashlib.sha256(PROBE_SCRIPT.encode()).hexdigest(),
            "runnerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "checks": checks,
            "exitCode": result.returncode,
            "passed": result.returncode == 0 and probe_passed(checks),
            "diagnostic": runner.normalize(
                result.stderr[-4000:],
                {
                    str(batch): "<batch>",
                    str(codex): "<codex>",
                    str(Path.home()): "<home>",
                    str(score.ROOT): "<repository>",
                },
            ),
        }
        if inspect_instructions:
            # This diagnostic is neither a tool-denial test nor a complete
            # inventory. Keep raw prompt text and stderr out of public output.
            summary = prompt_summary(result.stdout, marker)
            report = {
                **{
                    k: report[k]
                    for k in (
                        "hostVersion",
                        "pythonVersion",
                        "gitVersion",
                        "gitRuntimeSha256",
                        "runtimeRevision",
                        "generatedPolicy",
                        "policySha256",
                        "runnerSha256",
                        "exitCode",
                    )
                },
                **summary,
                "passed": result.returncode == 0 and summary["fixtureIncluded"],
                "diagnosticSha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
                "diagnosticCategories": diagnostic_categories(result.stderr),
            }
    report["cleanup"] = not batch.exists()
    report["passed"] = report["passed"] and report["cleanup"]
    return report


def probe_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Synthetic Codex shell boundary probe")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--probe-boundary", action="store_true")
    modes.add_argument("--probe-instructions", action="store_true")
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--git-executable", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with runner.interruption_signals():
            report = boundary_probe(
                args.codex,
                git_executable=args.git_executable,
                inspect_instructions=args.probe_instructions,
            )
        print(json.dumps(report, indent=2))
        return 0 if report["passed"] else 1
    except (runner.HostError, score.RecordError) as error:
        print(f"boundary probe stopped: {error}", file=sys.stderr)
        return 2
    except (
        OSError,
        ValueError,
        KeyboardInterrupt,
        subprocess.SubprocessError,
    ) as error:
        print(f"boundary probe stopped: {type(error).__name__}", file=sys.stderr)
        return 2


@contextlib.contextmanager
def temporary_home(
    workspace: Path,
    revision: str,
    *,
    scratch: Path = runner.SCRATCH,
    provision: Callable[[Path], None],
) -> Iterator[Path]:
    """Provision directly into a fresh home; never accept an existing sign-in path."""
    runner.verify_workspace(workspace)
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codex-home-", dir=scratch) as folder:
        home = Path(folder)
        provision(home)
        sign_in = home / "auth.json"
        if sign_in.is_symlink() or not sign_in.is_file():
            raise runner.HostError("independent sign-in must be a regular file")
        metadata = sign_in.stat()
        if metadata.st_nlink != 1 or metadata.st_mode & 0o777 != 0o600:
            raise runner.HostError("independent sign-in must be private and unlinked")
        env = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SSL_CERT_FILE"}
        }
        env["CODEX_HOME"] = str(home)
        for args in (
            ["codex", "plugin", "marketplace", "add", str(score.ROOT), "--json"],
            ["codex", "plugin", "add", "specflow@buvis-agent-plugins", "--json"],
        ):
            result = runner.command(args, workspace, env)
            if result.returncode:
                # Installer output can contain authentication data; never persist it.
                raise runner.HostError(
                    f"Codex plugin setup failed (exit {result.returncode})"
                )
        cache = home / "plugins/cache/buvis-agent-plugins/specflow"
        installed = list(cache.glob("*/plugin.json"))
        if len(installed) != 1:
            raise runner.HostError(
                "Codex setup did not produce exactly one specflow package"
            )
        plugin = installed[0].parent
        if not plugin.resolve().is_relative_to(home.resolve()):
            raise runner.HostError("Codex installed package leaves the temporary home")
        runner.verify_plugin(plugin, revision)
        yield home


class Codex:
    host = "codex"

    def __init__(self, model: str) -> None:
        self.model = model
        self.version = "not-started"
        self.instruction_files: list[str] = []
        self.instruction_observations: dict[str, dict] = {}
        self.instruction_measurement = "not-measured"
        self.read_measurement = "not-measured"
        self.plugin = score.PLUGIN
        self.root: Path | None = None
        self.home: Path | None = None
        self.commands: list[str] = []
        self.runtime: list[Path] = []
        self.boundary: dict | None = None
        self.configuration_sha256: str | None = None
        self.boundary_sha256: str | None = None
        self.new_conversation()

    def new_conversation(self) -> None:
        self.conversation: str | None = None
        self.calls_seen = 0
        self.usage: list[dict[str, int]] = []
        self.instruction_files = []
        self.instruction_observations = {}
        self.instruction_measurement = "not-measured"

    def accept_turn(self, result: subprocess.CompletedProcess) -> tuple[str, list[str]]:
        """Reduce exec JSONL without running a host or asserting its isolation.

        Source: https://learn.chatgpt.com/docs/non-interactive-mode
        Exec reports thread identity and token usage, not a resolved model or a
        complete instruction/read inventory. Raw streams never enter records or
        error messages. Commit conversation state only after a complete turn.
        """
        if result.returncode:
            raise runner.HostError("Codex turn failed")
        try:
            events = [
                json.loads(line) for line in result.stdout.splitlines() if line.strip()
            ]
        except ValueError:
            raise runner.HostError("Codex emitted invalid JSONL") from None
        if (
            len(events) < 4
            or any(not isinstance(e, dict) for e in events)
            or events[0].get("type") != "thread.started"
            or events[1].get("type") != "turn.started"
            or events[-1].get("type") != "turn.completed"
        ):
            raise runner.HostError("Codex omitted ordered turn evidence")
        thread = events[0].get("thread_id")
        if (
            not isinstance(thread, str)
            or not thread.strip()
            or (self.conversation is not None and self.conversation != thread)
        ):
            raise runner.HostError("Codex omitted or changed conversation identity")
        messages, commands = [], []
        for event in events[2:-1]:
            if event.get("type") not in (
                "item.started",
                "item.updated",
                "item.completed",
            ):
                raise runner.HostError(
                    "Codex emitted unexpected or failed turn evidence"
                )
            item = event.get("item")
            if not isinstance(item, dict) or not isinstance(item.get("type"), str):
                raise runner.HostError("Codex emitted invalid item evidence")
            # A command that exits nonzero is ordinary work, not a host failure.
            if (
                item["type"] == "error"
                or ("status" in item and not isinstance(item["status"], str))
                or item.get("status") == "declined"
                or (
                    item.get("status") == "failed"
                    and item["type"] != "command_execution"
                )
            ):
                raise runner.HostError("Codex reported a failed or denied operation")
            if event["type"] == "item.completed":
                if item["type"] == "agent_message":
                    text = item.get("text")
                    if not isinstance(text, str) or not text.strip():
                        raise runner.HostError("Codex omitted reply text")
                    messages.append(text)
                elif item["type"] == "command_execution":
                    commands.append(str(item.get("command", "")))
        usage = events[-1].get("usage")
        if (
            not messages
            or not isinstance(usage, dict)
            or not {"input_tokens", "cached_input_tokens", "output_tokens"}
            <= usage.keys()
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in usage.values()
            )
            or usage["cached_input_tokens"] > usage["input_tokens"]
        ):
            raise runner.HostError("Codex omitted valid reply or token usage")
        self.conversation = thread
        self.usage.append(usage.copy())
        self.commands = commands
        self.instruction_files = []
        self.instruction_observations = {}
        self.instruction_measurement = "not-measured"
        return messages[-1], []

    def identify(self) -> None:
        """Fix executables, version, and configuration digest before any launch."""
        if self.home is None:
            # run_batch points plugin at the batch copy before preflight.
            self.root = self.plugin.parent.parent
        if (
            self.root is None
            or not (self.root / "control").is_dir()
            or not (self.root / "workspaces").is_dir()
        ):
            raise runner.HostError("Codex launch needs the external batch layout")
        found = shutil.which("codex")
        if not found:
            raise runner.HostError("codex executable not found")
        binary = codex_binary(found)
        executable = str(binary)
        self.executable, self.git = executable, find_git()
        # Codex's own bin folder: the main binary and its helper binaries. A
        # folder that holds anything else (a `codex` file in ~/bin) is refused.
        if any(not p.name.startswith("codex") for p in binary.parent.iterdir()):
            raise runner.HostError("the Codex binary folder holds other files")
        self.runtime = [binary.parent, *shell_runtime()]
        home = Path.home().resolve()
        broad = {Path("/"), Path("/tmp"), Path("/private/tmp"), home, *home.parents}
        if any(path in broad or path == self.root for path in self.runtime):
            raise runner.HostError("a Codex runtime read grant is too broad")
        version = runner.command([executable, "--version"], self.root, timeout=30)
        if version.returncode or not version.stdout.split():
            raise runner.HostError("could not identify installed Codex")
        self.version = version.stdout.split()[-1]
        policy = runner.normalize(
            eval_config(
                self.root / "workspaces/session",
                Path("<plugin>"),
                self.git,
                self.runtime,
            ),
            {
                **{str(path): "<codex-runtime>" for path in self.runtime},
                str(self.root / "workspaces/session"): "<workspace>",
                str(Path.home().resolve()): "<home>",
                str(Path(sys.base_prefix).resolve()): "<python-runtime>",
                str(self.git): "<git-runtime>",
            },
        )
        self.configuration_sha256 = score.evidence_digest(
            {
                "policy": policy,
                # The policy text hides which paths the runtime grants name.
                "grants": hashlib.sha256(
                    "\n".join(sorted(map(str, self.runtime))).encode()
                ).hexdigest(),
                "version": self.version,
                "python": sys.version.split()[0],
                "git": hashlib.sha256(self.git.read_bytes()).hexdigest(),
                "arguments": self.arguments("<prompt>", template=True)[1:],
            }
        )

    def preflight(self) -> None:
        self.identify()
        runner.accept_boundary(
            self, score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        )

    def provision(self, home: Path) -> None:
        """Fresh interactive sign-in by the developer, stored only in this home."""
        if not sys.stdin.isatty():
            raise runner.HostError(
                "independent Codex sign-in needs a developer terminal"
            )
        (home / "config.toml").write_text('cli_auth_credentials_store = "file"\n')
        print("Sign in to Codex for this evaluation batch only.", file=sys.stderr)
        # Inherits the terminal on purpose; nothing from it is captured or stored.
        result = subprocess.run(
            [self.executable, "login"],
            env={
                **self.environment(),
                "CODEX_HOME": str(home),
                "HOME": str(Path.home()),
            },
            timeout=score.remaining_timeout(600),
            check=False,
        )
        if result.returncode:
            raise runner.HostError("independent Codex sign-in did not complete")

    def environment(self) -> dict[str, str]:
        return {
            "PATH": os.pathsep.join(
                [
                    str(Path(sys.executable).resolve().parent),
                    str(self.git.parent),
                    os.defpath,
                ]
            ),
            "HOME": str(self.root / "home"),
            "CODEX_HOME": str(self.home),
            "TMPDIR": str(self.root),
            "LANG": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "PYTHONDONTWRITEBYTECODE": "1",
            # Synthetic value: the probe checks that tools never receive it.
            SECRET_VARIABLE: "synthetic",
        }

    def arguments(self, prompt: str, *, template: bool = False) -> list[str]:
        """Launch flags. The template form is turn-independent, for the digest."""
        resume = (
            ["resume", self.conversation] if self.conversation and not template else []
        )
        return [
            getattr(self, "executable", "codex"),
            "exec",
            "--profile",
            "specflow",
            *resume,
            "--json",
            "--strict-config",
            "--ignore-rules",
            "--model",
            "<model>" if template else self.model,
            prompt,
        ]

    def effective_profile(self, profile: object, workspace: Path) -> object:
        """The host-recorded profile with this batch's paths made comparable."""
        return runner.normalize(
            profile,
            {
                **{str(path): "<codex-runtime>" for path in self.runtime},
                str(workspace): "<workspace>",
                str(self.plugin): "<plugin>",
                str(self.root): "<batch>",
                str(Path.home().resolve()): "<home>",
                str(Path(sys.base_prefix).resolve()): "<python-runtime>",
                str(self.git): "<git-runtime>",
            },
        )

    @contextlib.contextmanager
    def install(self, workspace: Path) -> Iterator[None]:
        """Sign in, install specflow, and verify it, all inside the batch."""
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        if self.root is None:
            self.root = self.plugin.parent.parent
        (self.root / "home").mkdir(mode=0o700, exist_ok=True)

        def provision(home: Path) -> None:
            self.home = home
            self.provision(home)

        try:
            with temporary_home(
                workspace,
                revision,
                scratch=self.root / "control",
                provision=provision,
            ) as home:
                for name in ("AGENTS.md", "AGENTS.override.md"):
                    if (home / name).exists():
                        raise runner.HostError("unexpected global Codex instructions")
                self.plugin = next(
                    (home / "plugins/cache/buvis-agent-plugins/specflow").glob("*")
                )
                yield
        finally:
            self.home = None
            self.plugin = self.root / "resources/specflow"

    @contextlib.contextmanager
    def batch(self, workspace: Path) -> Iterator[None]:
        # This guard also protects direct callers, outside run_batch.
        self.preflight()
        with self.install(workspace):
            yield

    def launch(self, prompt: str, workspace: Path) -> subprocess.CompletedProcess:
        if self.home is None:
            raise runner.HostError("Codex batch was not started")
        if workspace.parent != self.root / "workspaces":
            raise runner.HostError("workspace is outside the batch")
        profile = self.home / "specflow.config.toml"
        profile.write_text(eval_config(workspace, self.plugin, self.git, self.runtime))
        profile.chmod(0o600)
        return runner.command(self.arguments(prompt), workspace, self.environment())

    def turn(self, prompt: str, workspace: Path) -> tuple[str, list[str]]:
        if self.home is None:
            raise runner.HostError("Codex batch was not started")
        self.preflight()
        source = next(
            (
                path
                for name in ("AGENTS.override.md", "AGENTS.md")
                if (path := workspace / name).is_file() and path.read_text().strip()
            ),
            None,
        )
        expected = source.read_bytes() if source else b""
        reply, _ = self.accept_turn(self.launch(prompt, workspace))
        record = read_rollout(self.home, self.conversation)
        context = record["contexts"][-1] if record["contexts"] else {}
        if record["version"] != self.version or not context.get("model"):
            raise runner.HostError("Codex omitted version or model evidence")
        self.model = context["model"]
        if (context.get("permission_profile") or {}).get("type") in (
            None,
            "disabled",
        ) or (context.get("sandbox_policy") or {}).get("type") == "danger-full-access":
            raise runner.HostError("Codex did not apply the generated profile")
        # A default sandbox is also "not disabled": require the proven profile.
        if self.effective_profile(context["permission_profile"], workspace) != (
            self.boundary or {}
        ).get("effectiveProfile"):
            raise runner.HostError("Codex applied a profile the proof does not cover")
        self.instruction_observations, complete = instruction_evidence(
            record["state"].get("agents_md"), workspace, source, expected
        )
        self.instruction_measurement = (
            "measured" if complete and ROLLOUT_INVENTORY_APPROVED else "not-measured"
        )
        # Calls come from the session record: the exec stream does not show
        # every shell call. A patch is a write; any other call is unnameable.
        calls = rollout_calls(self.home, self.conversation)
        reads, known = [], True
        for call in calls[self.calls_seen :]:
            if PATCH_CALL.fullmatch(call["input"]):
                continue
            text = literal_command(call["input"])
            if text is None:
                # A script that does more than one literal shell call can
                # read files this adapter cannot name.
                known = False
                continue
            named, clear = runner.shell_reads(text, workspace, self.plugin)
            reads += named
            known = known and clear
        self.calls_seen = len(calls)
        self.read_measurement = "measured" if known else "not-measured"
        return reply, reads


# Name of a synthetic variable; the tool environment policy must strip it.
SECRET_VARIABLE = "SPECFLOW_SYNTHETIC_" + "TOKEN"
# The host records the merged instruction text it loaded, not file paths. The
# path comes from Codex's documented discovery rule (one file in the Git root,
# no imports, nothing below the working directory). Treating that pair as a
# measured inventory is a proposed contract revision; it stays off until the
# developer approves it (00009 QA log, 2026-11-15).
ROLLOUT_INVENTORY_APPROVED = False


def find_git() -> Path:
    """The real Git file; macOS's /usr/bin/git is a launcher that needs more reads."""
    if sys.platform == "darwin":
        found = runner.command(["/usr/bin/xcrun", "--find", "git"], Path("/"), None, 30)
        candidate = found.stdout.strip() if not found.returncode else ""
    else:
        candidate = shutil.which("git") or ""
    path = Path(candidate).resolve() if candidate else None
    if not path or path.name != "git" or not path.is_file():
        raise runner.HostError("could not locate the Git executable")
    return path


def codex_binary(executable: str) -> Path:
    """The real Codex file, with every symbolic link resolved.

    A mise shim resolves to the `mise` binary, not to Codex, so ask mise for
    the real file. Codex re-executes the path it was launched by inside the
    generated profile; a link in a denied folder on that path stops the launch
    (observed 2026-11-15 with mise's `latest` link), so launch the resolved file.
    """
    binary = Path(executable)
    if binary.resolve().name == "mise":
        found = runner.command(
            [str(binary.resolve()), "which", "codex"], Path("/"), None, 30
        )
        if found.returncode or not found.stdout.strip():
            raise runner.HostError("could not resolve the Codex executable")
        binary = Path(found.stdout.strip())
    binary = binary.resolve()
    if binary.name != "codex" or not binary.is_file():
        raise runner.HostError("could not resolve the Codex executable")
    return binary


def eval_config(
    workspace: Path, plugin: Path, git_executable: Path, runtime: list[Path]
) -> str:
    """Per-turn profile: the proven probe policy plus sign-in and tool settings.

    Codex loads instructions through a helper that re-executes its own binary
    inside this profile, so its `bin` folder needs a read grant. Observed
    2026-11-15: without it no session starts (sandbox-exec execvp, exit 71).
    """
    lines = probe_config(
        {"workspace": str(workspace), "plugin": str(plugin)},
        git_executable=git_executable,
    ).splitlines()
    network = lines.index("[permissions.specflow-probe.network]")
    lines[network:network] = [f'{json.dumps(str(path))} = "read"' for path in runtime]
    return "\n".join(
        [
            lines[0],
            'cli_auth_credentials_store = "file"',
            "project_doc_fallback_filenames = []",
            # A login shell rebuilds PATH from the system profile and then
            # finds macOS's Git launcher, which fails in the sandbox: the
            # status helper returned no result (observed 2026-11-15).
            "allow_login_shell = false",
            *lines[1:],
            "[shell_environment_policy]",
            'inherit = "core"',
            "ignore_default_excludes = false",
            # Tools do not inherit these from the host process. Without them
            # Git reads its system configuration, which the profile denies,
            # and the status helper fails (observed 2026-11-15).
            (
                'set = { GIT_CONFIG_NOSYSTEM = "1", GIT_CONFIG_GLOBAL = "/dev/null", '
                'PYTHONDONTWRITEBYTECODE = "1" }'
            ),
            "",
        ]
    )


def read_rollout(home: Path, thread: str | None) -> dict:
    """Read the host's own session record: version, turn contexts, loaded state."""
    files = list((home / "sessions").glob(f"**/rollout-*{thread}.jsonl"))
    if not thread or len(files) != 1:
        raise runner.HostError("Codex session record not found")
    version, contexts, state = None, [], {}
    try:
        for line in files[0].read_text().splitlines():
            entry = json.loads(line)
            payload = entry.get("payload") or {}
            if entry.get("type") == "session_meta":
                version = payload.get("cli_version")
            elif entry.get("type") == "turn_context":
                contexts.append(payload)
            elif entry.get("type") == "world_state":
                update = payload.get("state") or {}
                if payload.get("full"):
                    state = dict(update)
                else:
                    for key, value in update.items():
                        old = state.get(key)
                        state[key] = (
                            {**old, **value}
                            if isinstance(old, dict) and isinstance(value, dict)
                            else value
                        )
    except (OSError, ValueError, AttributeError):
        raise runner.HostError("Codex session record is unreadable") from None
    return {"version": version, "contexts": contexts, "state": state}


# The login shell rebuilds PATH and finds the system Python first, so the probe
# names the supervisor's interpreter.
PROBE_COMMAND = f"{Path(sys.executable).resolve()} -I -B probe.py"
# Codex tools are called from a small script. Only these two whole-script
# shapes are understood; anything else can do work this adapter cannot name.
EXEC_CALL = re.compile(
    r"\s*(?:text\(\s*)?await tools\.exec_command\(\{\s*cmd\s*:\s*"
    r'"((?:[^"\\]|\\.)*)"(?:\s*,\s*max_output_tokens\s*:\s*\d+)?\s*\}\)\)?;?\s*'
)
PATCH_CALL = re.compile(
    r'\s*(?:text\(\s*)?await tools\.apply_patch\("(?:[^"\\]|\\.)*"\)\)?;?\s*'
)


def literal_command(source: str) -> str | None:
    """The shell command of a script that is one literal exec_command call."""
    match = EXEC_CALL.fullmatch(source)
    # An escape would need JavaScript string rules to read: treat as opaque.
    return match.group(1) if match and "\\" not in match.group(1) else None


def output_text(value: object) -> str:
    """Flatten a recorded tool result; a shell result nests stdout in JSON text."""
    text = []
    for part in value if isinstance(value, list) else [value]:
        raw = part.get("text") if isinstance(part, dict) else part
        raw = raw if isinstance(raw, str) else json.dumps(raw)
        try:
            inner = json.loads(raw)
        except ValueError:
            inner = None
        if isinstance(inner, dict) and "output" in inner:
            raw = f"{inner['output']}\nexit code: {inner.get('exit_code')}"
        text.append(raw)
    return "\n".join(text)


def rollout_calls(home: Path, thread: str | None) -> list[dict]:
    """Tool calls with their results, from the host's own session record.

    The exec stream omits a call the host rejects before it runs, and showed no
    item for a sandboxed shell call (observed 2026-11-15). The record has both.
    """
    calls: list[dict] = []
    by_id: dict[object, dict] = {}
    for path in (home / "sessions").glob(f"**/rollout-*{thread}.jsonl"):
        for line in path.read_text().splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            payload = entry.get("payload") if isinstance(entry, dict) else None
            kind = str(payload.get("type")) if isinstance(payload, dict) else ""
            if kind.endswith("_call"):
                source = payload.get("input") or payload.get("arguments") or ""
                call = {
                    "name": payload.get("name"),
                    "input": source if isinstance(source, str) else json.dumps(source),
                    "output": "",
                }
                calls.append(call)
                by_id[payload.get("call_id")] = call
            elif kind.endswith("_call_output") and calls:
                call = by_id.get(payload.get("call_id"), calls[-1])
                call["output"] += output_text(payload.get("output"))
    return calls


def link_nodes(path: Path) -> list[Path]:
    """Every symbolic link met while resolving path, then the real file."""
    nodes, current = [], Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            target = Path(os.path.normpath(current.parent / os.readlink(current)))
            resolved = link_nodes(target)
            nodes += [current, *resolved[:-1]]
            current = resolved[-1]
    return [*nodes, current]


def shell_runtime() -> list[Path]:
    """Read grants that let Codex start the user's login shell.

    Codex runs every shell command through that shell. Outside the system
    folders (Homebrew bash here) the profile hid it: `execvp() of
    '/opt/homebrew/bin/bash' failed` (observed 2026-11-15). Grant the shell,
    the non-system libraries it links, and each link on the way to them; the
    profile needs a link's own path as well as its target.
    """
    try:
        shell = Path(pwd.getpwuid(os.getuid()).pw_shell)
    except KeyError:
        raise runner.HostError("could not identify the login shell") from None
    system = ("/bin/", "/usr/bin/", "/usr/lib/", "/System/")
    if str(shell.resolve()).startswith(system):
        return []
    files = [shell]
    if sys.platform == "darwin":
        listed = runner.command(
            ["/usr/bin/otool", "-L", str(shell.resolve())], Path("/"), None, 30
        )
        if listed.returncode:
            raise runner.HostError("could not list the login shell's libraries")
        for line in listed.stdout.splitlines()[1:]:
            library = line.split()[0] if line.split() else ""
            if library.startswith("/") and not library.startswith(system):
                files.append(Path(library))
    # A grant on a link's own path did not let Codex follow it (same failure
    # with the link and its target both granted, 2026-11-15): the profile
    # appears to resolve granted paths. A link is readable only through its
    # real parent folder, so grant that folder; its other entries' targets
    # stay ungranted.
    return list(
        dict.fromkeys(
            node.parent if node.is_symlink() else node
            for file in files
            for node in link_nodes(file)
        )
    )


def instruction_evidence(
    agents: object, workspace: Path, source: Path | None, expected: bytes
) -> tuple[dict[str, dict], bool]:
    """Compare the host-recorded instruction text with the pre-launch file."""
    agents = agents if isinstance(agents, dict) else {}
    raw = agents.get("text")
    text = raw if isinstance(raw, str) else ""
    if not text.strip():
        # Nothing loaded. A fixture instruction that should have loaded is unknown.
        return {}, source is None
    directory = agents.get("directory")
    if (
        source
        and text.strip() == expected.decode().strip()
        and isinstance(directory, str)
        and Path(directory).resolve() == workspace.resolve()
    ):
        digest = hashlib.sha256(expected).hexdigest()
        return {str(source): {"sha256": digest, "imports": []}}, True
    # Unexpected or different text: report it so classification taints the run.
    where = source or Path(str(directory or workspace)) / "AGENTS.md"
    digest = hashlib.sha256(text.encode()).hexdigest()
    return {str(where): {"sha256": digest, "imports": []}}, True


@score.deadline(runner.SESSION_TIMEOUT)
def live_probe(model: str, *, scratch: Path = runner.EXTERNAL_SCRATCH) -> dict:
    """Signed-in installed-host proof with synthetic sentinels.

    Codex has no native read tool: its item types are command_execution,
    file_change, and tool calls, so the native read checks restate the shell
    result and say so. Native writes are apply_patch attempts. Verdicts come
    from the supervisor script, the host's session record, and files on disk.
    """
    revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
    adapter = Codex(model)
    with runner.external_batch(revision, scratch=scratch) as batch:
        adapter.plugin = batch / "resources/specflow"
        adapter.identify()
        seed = batch / "workspaces/seed"
        seed.mkdir(mode=0o700)
        runner.initialize_workspace(seed)
        with adapter.install(seed):
            instructions = {"AGENTS.md": "Synthetic fixture instruction.\n"}
            # The home sentinel sits beside the plugin exception in CODEX_HOME.
            workspace, payload, _, secret = runner.prepare_probe(
                batch,
                adapter.plugin,
                SECRET_VARIABLE,
                instructions,
                home_sentinel=adapter.home / "sentinel.txt",
            )
            helper = f"{Path(sys.executable).resolve()} -B {payload['helper']} status"
            prompt = (
                "This is a permission self-test. Do each step once, in order. "
                "Some are denied; that is expected. Never retry or use another "
                "way, and continue after a denial. Then reply: done.\n"
                f"1. Run exactly this shell command: {PROBE_COMMAND}\n"
                f"2. Use apply_patch to add the file {payload['plugin_new']} "
                "with one line: probe\n"
                f"3. Use apply_patch to add the file {payload['link_new']} "
                "with one line: probe\n"
                # Not a check: its recorded output explains a helper failure.
                f"4. Run exactly this shell command: {helper}"
            )
            result = adapter.launch(prompt, workspace)
            if result.returncode or "thread.started" not in result.stdout:
                # Developer terminal only: say why, with batch paths removed.
                tail = runner.normalize(
                    (result.stderr or result.stdout)[-1500:],
                    {str(batch): "<batch>", str(Path.home().resolve()): "<home>"},
                )
                raise runner.HostError(
                    f"Codex exited {result.returncode} before a session started: "
                    f"{diagnostic_categories(result.stderr)}\n{tail}"
                )
            items, thread = [], None
            for line in result.stdout.splitlines():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict):
                    thread = event.get("thread_id", thread)
                    if event.get("type") == "item.completed":
                        items.append(event.get("item") or {})
            calls = rollout_calls(adapter.home, thread)
            # The report token is readable by the model, so the script's
            # report counts only when the session made the instructed calls,
            # each as one literal call, and no other.
            commands = [literal_command(c["input"]) for c in calls]
            patches = sum(1 for c in calls if PATCH_CALL.fullmatch(c["input"]))
            instructed = (
                sorted(c for c in commands if c) == sorted([PROBE_COMMAND, helper])
                and patches == 2
                and len(calls) == 4
            )
            checks = runner.shell_probe_checks(
                [
                    c["output"]
                    for c, text in zip(calls, commands)
                    if text == PROBE_COMMAND
                ]
                if instructed
                else [],
                workspace,
                payload,
                extra=("plugin-read",),
            )
            for name in sorted(score.RELEASE_BOUNDARY_CHECKS):
                if name.startswith("native-") and name.endswith("read-denied"):
                    shell = checks[name.replace("native-", "shell-")]
                    checks[name] = {
                        "passed": shell["passed"],
                        "evidence": "Codex has no native read tool; reads are "
                        f"shell commands. Shell result: {shell['passed']}",
                    }
            intact = (
                runner.package_revision(adapter.plugin) == revision
                and not Path(payload["plugin_new"]).exists()
            )
            refused = {
                str(change.get("path"))
                for i in items
                if i.get("type") == "file_change"
                and i.get("status") in ("failed", "declined")
                for change in i.get("changes") or []
                if isinstance(change, dict)
            }
            for name, key in (
                ("native-plugin-write-denied", "plugin_new"),
                ("native-symlink-write-denied", "link_new"),
            ):
                # The host rejects a patch outside the project before any
                # stream item exists; its session record keeps the refusal.
                attempted = payload[key] in refused or any(
                    "apply_patch" in c["input"]
                    and payload[key] in c["input"]
                    and (
                        "patch rejected" in c["output"]
                        or "Failed to write" in c["output"]
                    )
                    for c in calls
                )
                checks[name] = {
                    "passed": attempted and intact and secret not in result.stdout,
                    "evidence": f"apply_patch on <{key}> refused by host="
                    f"{attempted}; plugin tree intact={intact}",
                }
            for name in ("shell-plugin-write-denied", "shell-symlink-write-denied"):
                checks[name]["passed"] = checks[name]["passed"] and intact
            record = read_rollout(adapter.home, thread)
            context = record["contexts"][-1] if record["contexts"] else {}
            profile = context.get("permission_profile") or {}
            source = workspace / "AGENTS.md"
            observations, complete = instruction_evidence(
                record["state"].get("agents_md"),
                workspace,
                source,
                source.read_bytes(),
            )
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            loaded = observations == {str(source): {"sha256": digest, "imports": []}}
            checks["instruction-inventory"] = {
                "passed": complete and loaded,
                "evidence": "host session record holds exactly the fixture "
                f"AGENTS.md text for the workspace: {loaded}",
            }
            checks["fixture-instructions"] = {
                "passed": loaded,
                "evidence": "fixture AGENTS.md text appears in the host record",
            }
            active = "spec-workflow" in json.dumps(record["state"])
            checks["plugin-activation"] = {
                "passed": active,
                "evidence": f"host session state names the specflow skill: {active}",
            }
            applied = (
                profile.get("type") not in (None, "disabled")
                and (context.get("sandbox_policy") or {}).get("type")
                != "danger-full-access"
            )
            checks["effective-settings"] = {
                "passed": applied
                and record["version"] == adapter.version
                and all(
                    c["passed"] for n, c in checks.items() if n.endswith("-denied")
                ),
                "evidence": "host turn context records an active permission "
                f"profile: {applied}; every generated denial observed",
            }
            proof = {
                "scope": "installed-host-boundary",
                "host": adapter.host,
                "hostVersion": adapter.version,
                "model": context.get("model"),
                "runtimeRevision": revision,
                "configurationSha256": adapter.configuration_sha256,
                "runnerSha256": runner.runner_digest(adapter),
                "effectiveProfile": adapter.effective_profile(profile, workspace),
                # Not evidence: what the host did, so a failed probe can be read.
                "observed": runner.normalize(
                    [
                        {
                            "type": i.get("type"),
                            "status": i.get("status"),
                            "command": i.get("command"),
                            "exitCode": i.get("exit_code"),
                            "changes": i.get("changes"),
                            "text": str(
                                i.get("aggregated_output") or i.get("text") or ""
                            )[-300:],
                        }
                        for i in items
                    ]
                    + [
                        {
                            "name": c["name"],
                            "input": c["input"][-400:],
                            "output": c["output"][-600:],
                        }
                        for c in calls
                    ],
                    {
                        str(batch): "<batch>",
                        str(Path.home().resolve()): "<home>",
                        secret: "<sentinel>",
                    },
                ),
                "checks": checks,
            }
    proof["checks"]["cleanup"] = {
        "passed": not batch.exists(),
        "evidence": "private batch directory absent after the probe",
    }
    return proof


def live_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Signed-in Codex boundary probe")
    parser.add_argument("--probe-live", action="store_true", required=True)
    parser.add_argument("--model", required=True, help="explicit model; never auto")
    args = parser.parse_args(argv)
    try:
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
    raise SystemExit(
        probe_main(sys.argv[1:])
        if "--probe-boundary" in sys.argv or "--probe-instructions" in sys.argv
        else runner.main(adapter_type=Codex)
    )
