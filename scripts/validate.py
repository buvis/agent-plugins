#!/usr/bin/env python3
"""Validate the portable structure of every plugin in this repository."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_NAME = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SKILL_NAME = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$",
)
MANIFEST_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}


class ValidationError(Exception):
    """Collectable validation failure."""


def require(condition: bool, path: Path, message: str) -> None:
    if not condition:
        raise ValidationError(f"{path}: {message}")


def load_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path}: invalid JSON: {error}") from error
    require(isinstance(value, dict), path, "must contain a JSON object")
    return value


def is_string(value: object, *, nonempty: bool = False) -> bool:
    return isinstance(value, str) and (not nonempty or bool(value))


def validate_manifest(plugin: Path) -> dict[str, object]:
    path = plugin / "plugin.json"
    require(path.is_file(), path, "missing required manifest")
    require(
        path.resolve().is_relative_to(plugin.resolve()),
        path,
        "resolves outside plugin root",
    )
    manifest = load_object(path)

    unknown = sorted(set(manifest) - MANIFEST_FIELDS)
    require(not unknown, path, f"unknown top-level fields: {', '.join(unknown)}")
    require(
        manifest.get("$schema") == PLUGIN_SCHEMA,
        path,
        "unsupported or missing $schema",
    )

    name = manifest.get("name")
    require(is_string(name, nonempty=True), path, "name must be a non-empty string")
    name = cast("str", name)
    require(
        len(name) <= 64 and PLUGIN_NAME.fullmatch(name) is not None,
        path,
        "invalid plugin name",
    )
    require(name == plugin.name, path, "name must match the plugin directory")

    for field in ("description", "homepage", "repository", "license"):
        if field in manifest:
            require(is_string(manifest[field]), path, f"{field} must be a string")

    version = manifest.get("version")
    require(
        is_string(version, nonempty=True),
        path,
        "repository policy requires a version",
    )
    version = cast("str", version)
    require(
        SEMVER.fullmatch(version) is not None,
        path,
        "version must use Semantic Versioning",
    )
    require(
        is_string(manifest.get("description"), nonempty=True),
        path,
        "repository policy requires a description",
    )
    require(
        is_string(manifest.get("license"), nonempty=True),
        path,
        "repository policy requires a license",
    )

    author = manifest.get("author")
    require(
        isinstance(author, dict),
        path,
        "repository policy requires an author object",
    )
    author = cast("dict[str, object]", author)
    require(
        not set(author) - {"name", "email", "url"},
        path,
        "author contains unknown fields",
    )
    require(
        is_string(author.get("name"), nonempty=True),
        path,
        "author.name is required",
    )
    for field, value in author.items():
        require(is_string(value), path, f"author.{field} must be a string")

    if "keywords" in manifest:
        keywords = manifest["keywords"]
        require(isinstance(keywords, list), path, "keywords must be an array")
        keywords = cast("list[object]", keywords)
        require(
            all(is_string(item) for item in keywords),
            path,
            "keywords must contain only strings",
        )

    if "extensions" in manifest:
        extensions = manifest["extensions"]
        require(isinstance(extensions, dict), path, "extensions must be an object")
        extensions = cast("dict[str, object]", extensions)
        require(
            all(isinstance(value, dict) for value in extensions.values()),
            path,
            "each extension value must be an object",
        )

    return manifest


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValidationError(f"{path}: cannot read skill: {error}") from error
    require(
        bool(lines) and lines[0].strip() == "---",
        path,
        "must start with YAML frontmatter",
    )

    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValidationError(
            f"{path}: frontmatter has no closing delimiter",
        ) from error

    fields: dict[str, str] = {}
    index = 1
    while index < end:
        line = lines[index]
        if line and not line[0].isspace() and ":" in line:
            key, raw_value = line.split(":", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if raw_value in {">", ">-", ">+", "|", "|-", "|+"}:
                block: list[str] = []
                index += 1
                while index < end and (not lines[index] or lines[index][0].isspace()):
                    block.append(lines[index].strip())
                    index += 1
                fields[key] = (
                    (" " if raw_value.startswith(">") else "\n").join(block).strip()
                )
                continue
            fields[key] = scalar(raw_value)
        index += 1
    return fields


def validate_skills(plugin: Path) -> int:
    skills = plugin / "skills"
    if not skills.exists():
        return 0
    require(skills.is_dir(), skills, "must be a directory")
    require(
        skills.resolve().is_relative_to(plugin.resolve()),
        skills,
        "resolves outside plugin root",
    )

    count = 0
    for skill in sorted(path for path in skills.iterdir() if path.is_dir()):
        path = skill / "SKILL.md"
        require(path.is_file(), path, "each skill directory must contain SKILL.md")
        require(
            path.resolve().is_relative_to(plugin.resolve()),
            path,
            "resolves outside plugin root",
        )
        fields = frontmatter(path)
        name = fields.get("name", "")
        description = fields.get("description", "")
        require(
            SKILL_NAME.fullmatch(name) is not None and len(name) <= 64,
            path,
            "invalid skill name",
        )
        require(
            name == skill.name,
            path,
            "frontmatter name must match the skill directory",
        )
        require(
            1 <= len(description) <= 1024,
            path,
            "description must contain 1-1024 characters",
        )
        if "compatibility" in fields:
            require(
                1 <= len(fields["compatibility"]) <= 500,
                path,
                "compatibility must contain 1-500 characters",
            )
        count += 1
    return count


def contained_suffix(value: str) -> bool:
    depth = 0
    for part in value.replace("\\", "/").split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            depth -= 1
            if depth < 0:
                return False
        else:
            depth += 1
    return True


def validate_url(path: Path, value: object) -> None:
    require(
        is_string(value, nonempty=True),
        path,
        "remote server URL must be a non-empty string",
    )
    value = cast("str", value)
    parsed = urlsplit(value)
    require(
        parsed.scheme in {"http", "https"} and bool(parsed.hostname),
        path,
        "remote URL must be absolute HTTP(S)",
    )
    require(
        parsed.username is None and parsed.password is None,
        path,
        "remote URL must not contain user information",
    )
    require(not parsed.fragment, path, "remote URL must not contain a fragment")
    host = parsed.hostname or ""
    loopback = host == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    require(
        parsed.scheme == "https" or loopback,
        path,
        "non-loopback MCP URLs must use HTTPS",
    )


def validate_mcp(plugin: Path) -> None:
    path = plugin / "mcp.json"
    if not path.exists():
        return
    require(path.is_file(), path, "must be a regular file")
    require(
        path.resolve().is_relative_to(plugin.resolve()),
        path,
        "resolves outside plugin root",
    )
    config = load_object(path)
    require(
        set(config) == {"$schema", "mcpServers"},
        path,
        "must contain only $schema and mcpServers",
    )
    require(config.get("$schema") == MCP_SCHEMA, path, "unsupported or missing $schema")
    servers = config.get("mcpServers")
    require(isinstance(servers, dict), path, "mcpServers must be an object")
    servers = cast("dict[str, object]", servers)

    for name, server in servers.items():
        server_path = Path(f"{path}#{name}")
        require(
            isinstance(name, str) and bool(name),
            server_path,
            "server name must be non-empty",
        )
        require(isinstance(server, dict), server_path, "server must be an object")
        server = cast("dict[str, object]", server)
        transport = server.get("type")
        if transport == "stdio":
            allowed = {"type", "command", "args", "env", "cwd"}
            require(
                not set(server) - allowed,
                server_path,
                "stdio server contains unknown fields",
            )
            command = server.get("command")
            require(
                is_string(command, nonempty=True),
                server_path,
                "stdio server requires command",
            )
            command = cast("str", command)
            if command.startswith("./"):
                require(
                    contained_suffix(command[2:]),
                    server_path,
                    "command escapes the plugin root",
                )
            else:
                require(
                    "/" not in command and "\\" not in command,
                    server_path,
                    "command must be bare or start with ./",
                )
            if "args" in server:
                require(
                    isinstance(server["args"], list)
                    and all(is_string(item) for item in server["args"]),
                    server_path,
                    "args must be strings",
                )
            if "env" in server:
                env = server["env"]
                require(isinstance(env, dict), server_path, "env must be an object")
                env = cast("dict[str, object]", env)
                require(
                    not {"PLUGIN_ROOT", "PLUGIN_DATA"} & set(env),
                    server_path,
                    "env must not override reserved variables",
                )
                require(
                    all(
                        is_string(key) and is_string(value)
                        for key, value in env.items()
                    ),
                    server_path,
                    "env keys and values must be strings",
                )
            if "cwd" in server:
                cwd = server["cwd"]
                require(is_string(cwd), server_path, "cwd must be a string")
                cwd = cast("str", cwd)
                if cwd.startswith("./"):
                    suffix = cwd[2:]
                elif cwd in {"${PLUGIN_ROOT}", "${PLUGIN_DATA}"}:
                    suffix = ""
                elif cwd.startswith("${PLUGIN_ROOT}/"):
                    suffix = cwd[len("${PLUGIN_ROOT}/") :]
                elif cwd.startswith("${PLUGIN_DATA}/"):
                    suffix = cwd[len("${PLUGIN_DATA}/") :]
                else:
                    message = (
                        f"{server_path}: cwd must be plugin-relative or rooted at "
                        "a plugin variable"
                    )
                    raise ValidationError(message)
                require(
                    contained_suffix(suffix),
                    server_path,
                    "cwd escapes its permitted root",
                )
        elif transport in {"streamable-http", "sse"}:
            allowed = {"type", "url", "headers"}
            require(
                not set(server) - allowed,
                server_path,
                "remote server contains unknown fields",
            )
            validate_url(server_path, server.get("url"))
            if "headers" in server:
                headers = server["headers"]
                require(
                    isinstance(headers, dict),
                    server_path,
                    "headers must be an object",
                )
                headers = cast("dict[str, object]", headers)
                require(
                    all(
                        is_string(key) and is_string(value)
                        for key, value in headers.items()
                    ),
                    server_path,
                    "header names and values must be strings",
                )
        else:
            raise ValidationError(f"{server_path}: unknown MCP transport {transport!r}")


def validate_containment(plugin: Path) -> None:
    root = plugin.resolve()
    for path in plugin.rglob("*"):
        if path.is_symlink():
            require(
                path.resolve().is_relative_to(root),
                path,
                "symlink resolves outside plugin root",
            )


def default_plugins() -> list[Path]:
    paths: list[Path] = []
    template = ROOT / "templates" / "example-plugin"
    if template.is_dir():
        paths.append(template)
    plugins = ROOT / "plugins"
    if plugins.is_dir():
        paths.extend(sorted(path for path in plugins.iterdir() if path.is_dir()))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="plugin directories; defaults to the template and plugins/*",
    )
    args = parser.parse_args()
    plugins = (
        [path.resolve() for path in args.paths] if args.paths else default_plugins()
    )
    errors: list[str] = []
    skill_count = 0

    for plugin in plugins:
        try:
            require(plugin.is_dir(), plugin, "plugin path must be a directory")
            validate_manifest(plugin)
            validate_containment(plugin)
            skill_count += validate_skills(plugin)
            validate_mcp(plugin)
        except ValidationError as error:
            errors.append(str(error))

    # Maintainer skills live outside every package; the skill rules still apply.
    agents = ROOT / ".agents"
    if not args.paths and (agents / "skills").is_dir():
        try:
            skill_count += validate_skills(agents)
        except ValidationError as error:
            errors.append(str(error))

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(plugins)} plugin package(s) and {skill_count} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
