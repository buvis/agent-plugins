#!/usr/bin/env python3
"""Claude adapter and shared, host-neutral scenario batch machinery.

The live entry points fail closed while T-056's environment proof is missing.
No flag in this module waives the approval or spending-limit requirements.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
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
TURN_TIMEOUT = 600
SESSION_BUDGET_USD = 5
PERMISSION_MODE = "default"
FIXTURES = ROOT / "tests/specflow/fixtures"
SESSIONS = score.EVALS / "sessions"


class HostError(RuntimeError):
    """A host failed before or during a turn."""


def command(
    args: list[str], cwd: Path, env: dict | None = None, timeout: int = TURN_TIMEOUT
) -> subprocess.CompletedProcess:
    """Never use a shell; terminate the process group, including tools, on timeout."""
    with subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
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


def package_revision(plugin: Path) -> str:
    """Compute Git's tree hash without an index, writes, or trusting HEAD's bytes."""
    import hashlib

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


def capture_status(workspace: Path) -> dict | None:
    result = command(
        [
            sys.executable,
            "-B",
            str(score.HELPER / "validate_spec.py"),
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


class Claude:
    host = "claude-code"

    def __init__(self, model: str) -> None:
        self.model = model
        self.version = "not-started"
        self.conversation: str | None = None
        self.cost = 0.0
        self.instruction_files: list[str] = []

    def preflight(self) -> None:
        raise HostError(
            "Claude launch blocked: reference/status permissions and instruction isolation remain unproven (plan section 8)"
        )

    @contextlib.contextmanager
    def batch(self) -> Iterator[None]:
        yield

    def new_conversation(self) -> None:
        self.conversation = None
        self.cost = 0.0

    def turn(self, prompt: str, workspace: Path) -> tuple[str, list[str]]:
        remaining = SESSION_BUDGET_USD - self.cost
        if remaining <= 0:
            raise HostError("session spending cap reached")
        args = [
            "claude",
            "-p",
            "--plugin-dir",
            str(score.PLUGIN),
            "--setting-sources",
            "project,local",
            "--permission-mode",
            PERMISSION_MODE,
            "--model",
            self.model,
            "--max-budget-usd",
            str(remaining),
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if self.conversation:
            args += ["--resume", self.conversation]
        env = {**os.environ, "CLAUDE_NESTED": "1", "_CLAUDE_NOTIFY_QUIET": "1"}
        result = command([*args, prompt], workspace, env)
        if result.returncode:
            raise HostError("Claude turn failed")
        events = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]
        init = next(
            (
                e
                for e in events
                if e.get("type") == "system" and e.get("subtype") == "init"
            ),
            {},
        )
        final = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if (
            final.get("is_error")
            or final.get("permission_denials")
            or final.get("subtype") != "success"
        ):
            raise HostError(
                "Claude turn did not succeed or requested denied permissions"
            )
        if "specflow:spec-workflow" not in init.get("skills", []):
            raise HostError("Claude did not load specflow")
        if (
            not init.get("model")
            or not init.get("claude_code_version")
            or not init.get("session_id")
        ):
            raise HostError("Claude omitted model, version, or conversation evidence")
        if self.conversation and self.conversation != init["session_id"]:
            raise HostError("Claude resumed a different conversation")
        self.model, self.version, self.conversation = (
            init["model"],
            init["claude_code_version"],
            init["session_id"],
        )
        # total_cost_usd is cumulative for the resumed Claude conversation.
        self.cost = max(self.cost, float(final["total_cost_usd"]))
        reads = []
        for event in events:
            for block in event.get("message", {}).get("content", []):
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Read"
                ):
                    reads.append(block["input"]["file_path"])
        return final["result"], reads


def play_session(adapter: Claude, session: dict, workspace: Path, record: dict) -> None:
    adapter.new_conversation()
    baseline = snapshot(workspace)
    try:
        for turn_number, turn in enumerate(session["turns"], 1):
            if "expects" in turn and (
                not record["messages"]
                or not re.search(turn["expects"], record["messages"][-1])
            ):
                record["brokenAt"] = turn_number
                break
            if edit := turn.get("edit"):
                write_files(workspace, {edit["path"]: edit["text"]})
            verify_workspace(workspace)
            prompt = turn["developer"]
            if turn_number == 1:
                prompt = (
                    "Use the installed specflow spec-workflow skill for this request.\n"
                    + prompt
                )
            message, reads = adapter.turn(prompt, workspace)
            record["messages"].append(message)
            record["filesRead"].append(
                [p.removeprefix(str(workspace) + "/") for p in reads]
            )
        record["status"] = capture_status(workspace)
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
        record["instructionFiles"] = adapter.instruction_files


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
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="batch-", dir=SCRATCH) as folder:
        root = Path(folder)
        replacements = {
            str(root): "<batch>",
            str(ROOT): "<repository>",
            str(score.PLUGIN): "<plugin>",
            str(Path.home()): "<home>",
        }
        startup_error = None
        try:
            adapter.preflight()
        except (HostError, OSError, ValueError, subprocess.SubprocessError) as error:
            startup_error = str(error)
        with contextlib.ExitStack() as resources:
            if startup_error is None:
                try:
                    resources.enter_context(adapter.batch())
                except (
                    HostError,
                    OSError,
                    ValueError,
                    subprocess.SubprocessError,
                ) as error:
                    startup_error = str(error)
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
                }
                workspace = root / session["name"]
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
                    if parent and parent not in completed:
                        raise HostError("continuation parent did not finish")
                    write_files(workspace, completed[parent] if parent else initial)
                    initialize_workspace(workspace)
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
                normalized = normalize(record, replacements)
                score.validate_record(normalized)
                if "notRun" not in normalized:
                    try:
                        code = max(
                            code, score.score_record(normalized, eval_dir, results=out)
                        )
                    except (
                        score.RecordError,
                        OSError,
                        ValueError,
                        subprocess.SubprocessError,
                    ) as error:
                        normalized["notRun"] = f"scoring could not finish: {error}"
                        normalized.pop("scores", None)
                        code = max(code, 2)
                else:
                    code = max(code, 2 if not normalized["messages"] else 1)
                score.write_json(path, normalized)
                records[session["name"]] = number
                print(path)
    return code


def main(argv: list[str] | None = None, adapter_type: type = Claude) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session")
    parser.add_argument("--model", required=True, help="explicit model; never auto")
    parser.add_argument("--out", type=Path, default=score.EVALS / "results")
    args = parser.parse_args(argv)
    try:
        if args.model in {"auto", "default"}:
            raise score.RecordError("choose an explicit model")
        return run_batch(adapter_type(args.model), args.session, args.out)
    except (
        HostError,
        score.RecordError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"runner: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
