"""The workspace config, .agents/specflow.json, with every configured path checked before use."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from .schema import check_schema, load_schema

CONFIG_FILE = Path(".agents") / "specflow.json"
DEFAULTS: dict[str, object] = {
    "root": ".kiro/specflow",
    "specsDir": ".kiro/specs",
    "numberScan": [],
}
DRIVE = re.compile(r"^[A-Za-z]:")


class ConfigError(Exception):
    """The config file is unreadable, invalid, or names a path that is refused."""


def refuse_reason(repo: Path, value: str) -> str | None:
    """Why a configured path is refused (SEC-002.5); a link that resolves inside is allowed."""
    if value.startswith(("/", "~", "\\")) or DRIVE.match(value):
        return "is absolute"
    if ".." in PurePosixPath(value.replace("\\", "/")).parts:
        return "holds a .. segment"
    if not (repo / value).resolve().is_relative_to(repo.resolve()):
        return "resolves outside the repository"
    return None


def load_config(repo: Path) -> dict[str, object]:
    """root, specsDir, and numberScan, with the defaults applied; ConfigError when unusable."""
    path = repo / CONFIG_FILE
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_bytes().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ConfigError(f"{CONFIG_FILE}: cannot be read: {error}") from error
        if not isinstance(data, dict):
            raise ConfigError(f"{CONFIG_FILE}: must contain a JSON object")
        errors = check_schema(data, load_schema("specflow-config.schema.json"))
        if errors:
            raise ConfigError(f"{CONFIG_FILE}: " + "; ".join(errors))
    config = {key: data.get(key, default) for key, default in DEFAULTS.items()}
    for value in [config["root"], config["specsDir"], *config["numberScan"]]:
        reason = refuse_reason(repo, str(value))
        if reason:
            raise ConfigError(f"{CONFIG_FILE}: configured path {value} {reason}")
    return config
