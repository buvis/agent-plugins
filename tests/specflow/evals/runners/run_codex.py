#!/usr/bin/env python3
"""Codex batch setup; live turns remain blocked pending T-056's launch contract."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
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

    def preflight(self) -> None:
        raise runner.HostError(
            "Codex launch blocked: independent sign-in provisioning and native "
            "instruction/read isolation remain unproven"
        )

    def provision(self, home: Path) -> None:
        raise runner.HostError("independent sign-in provisioning is not implemented")

    @contextlib.contextmanager
    def batch(self, workspace: Path) -> Iterator[None]:
        # This guard also protects direct callers, outside run_batch.
        self.preflight()
        revision = score.git("rev-parse", "HEAD:plugins/specflow").decode().strip()
        with temporary_home(workspace, revision, provision=self.provision):
            yield


if __name__ == "__main__":
    raise SystemExit(
        probe_main(sys.argv[1:])
        if "--probe-boundary" in sys.argv or "--probe-instructions" in sys.argv
        else runner.main(adapter_type=Codex)
    )
