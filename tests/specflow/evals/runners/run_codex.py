#!/usr/bin/env python3
"""Codex batch setup; live turns remain blocked pending T-056's launch contract."""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path

import run_claude as runner
import score


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
    raise SystemExit(runner.main(adapter_type=Codex))
