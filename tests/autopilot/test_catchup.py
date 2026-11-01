"""Optional catch-up probes classify gh and engram locally, statelessly and through injected seams."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "plugins" / "autopilot" / "scripts"
GH_ARGV = ["gh", "auth", "status"]
ENGRAM_ARGV = ["engram", "status", "--scope", "repo"]
MARKER = "not inside a registered repo"
WATCHED_EVENTS = {
    "open",
    "os.listdir",
    "os.scandir",
    "os.mkdir",
    "os.remove",
    "os.rmdir",
    "os.rename",
    "os.symlink",
    "os.link",
    "shutil.copyfile",
    "shutil.rmtree",
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.posix_spawn",
}
AUDIT: dict = {"active": False, "events": []}


def _record_audit(event: str, args: tuple) -> None:
    if AUDIT["active"] and event in WATCHED_EVENTS:
        AUDIT["events"].append((event, args))


sys.addaudithook(_record_audit)


@pytest.fixture
def catchup():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module("catchup")


class Fakes:
    """Injected which/run seams; outcomes map a binary to (returncode, stdout, stderr) or an exception."""

    def __init__(self, outcomes: dict, installed: tuple = ("gh", "engram")) -> None:
        self.outcomes = outcomes
        self.installed = set(installed)
        self.lookups: list[str] = []
        self.calls: list[tuple[list[str], dict]] = []

    def which(self, name: str) -> str | None:
        self.lookups.append(name)
        return f"/opt/fake/bin/{name}" if name in self.installed else None

    def run(self, *args, **kwargs) -> subprocess.CompletedProcess:
        argv = list(args[0] if args else kwargs.pop("args"))
        self.calls.append((argv, dict(kwargs)))
        if argv[0] not in self.outcomes:
            raise AssertionError(f"unexpected command {argv!r}")
        outcome = self.outcomes[argv[0]]
        if isinstance(outcome, BaseException):
            raise outcome
        code, stdout, stderr = outcome
        return subprocess.CompletedProcess(argv, code, stdout=stdout, stderr=stderr)


def assert_spawned_as_captured_text(kwargs: dict, root: Path) -> None:
    assert Path(kwargs["cwd"]) == root
    assert kwargs["timeout"] == 15
    assert kwargs.get("text") is True or kwargs.get("universal_newlines") is True
    piped = (
        kwargs.get("stdout") == subprocess.PIPE
        and kwargs.get("stderr") == subprocess.PIPE
    )
    assert kwargs.get("capture_output") is True or piped
    assert not kwargs.get("shell")
    assert not kwargs.get("check")
    assert kwargs.get("env") is None


def assert_result(result: dict, gh: str, engram: str, skip: list[str]) -> None:
    assert type(result["schema_version"]) is int
    assert result == {"schema_version": 1, "gh": gh, "engram": engram, "skip": skip}


@pytest.mark.parametrize("name", ["alpha", "beta"])
def test_runs_only_gh_auth_and_engram_repo_status_in_the_explicit_root(
    catchup, tmp_path: Path, name: str
) -> None:
    root = tmp_path / name
    root.mkdir()
    fakes = Fakes({"gh": (0, "Logged in", ""), "engram": (0, "registered", "")})
    result = catchup.probe(root, run=fakes.run, which=fakes.which)
    assert sorted(argv for argv, _ in fakes.calls) == sorted([GH_ARGV, ENGRAM_ARGV])
    for _, kwargs in fakes.calls:
        assert_spawned_as_captured_text(kwargs, root)
    assert set(fakes.lookups) == {"gh", "engram"}
    assert_result(result, "ok", "ok", [])


GH_OUTCOMES = {
    "ok": ((0, "Logged in to github.com", ""), True),
    "unauthenticated": ((1, "", "You are not logged into any GitHub hosts"), True),
    "absent": (None, False),
}
ENGRAM_OUTCOMES = {
    "ok": ((0, "repo: registered", ""), True),
    "unregistered": ((1, "", f"error: {MARKER}\n"), True),
    "absent": (subprocess.TimeoutExpired(ENGRAM_ARGV, 15), True),
}


@pytest.mark.parametrize("gh_token", list(GH_OUTCOMES))
@pytest.mark.parametrize("engram_token", list(ENGRAM_OUTCOMES))
def test_tokens_and_skip_order_follow_each_probe(
    catchup, tmp_path: Path, gh_token: str, engram_token: str
) -> None:
    gh_outcome, gh_installed = GH_OUTCOMES[gh_token]
    engram_outcome, engram_installed = ENGRAM_OUTCOMES[engram_token]
    installed = tuple(
        n for n, keep in (("gh", gh_installed), ("engram", engram_installed)) if keep
    )
    outcomes = {"engram": engram_outcome}
    if gh_outcome is not None:
        outcomes["gh"] = gh_outcome
    fakes = Fakes(outcomes, installed)
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    skip = [
        s
        for s, bad in (
            ("github-state", gh_token != "ok"),
            ("engram", engram_token != "ok"),
        )
        if bad
    ]
    assert_result(result, gh_token, engram_token, skip)


@pytest.mark.parametrize(
    ("code", "stdout", "stderr", "token"),
    [
        (0, "", "", "ok"),
        (0, "You are not logged into any GitHub hosts", MARKER, "ok"),
        (1, "Logged in to github.com", "", "unauthenticated"),
        (4, "", "", "unauthenticated"),
        (2, "", "", "unauthenticated"),
        (255, "", "", "unauthenticated"),
        (-9, "", "", "unauthenticated"),
    ],
    ids=[
        "zero-quiet",
        "zero-noisy",
        "one-noisy",
        "four-quiet",
        "two",
        "255",
        "signal-killed",
    ],
)
def test_gh_exit_code_alone_decides_authentication(
    catchup, tmp_path: Path, code: int, stdout: str, stderr: str, token: str
) -> None:
    fakes = Fakes({"gh": (code, stdout, stderr), "engram": (0, "", "")})
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert_result(result, token, "ok", [] if token == "ok" else ["github-state"])


@pytest.mark.parametrize(
    ("code", "stdout", "stderr", "token"),
    [
        (1, "", MARKER, "unregistered"),
        (0, "", f"warning: {MARKER} (/work/x)\n", "unregistered"),
        (1, "", "Not inside a registered repo", "ok"),
        (1, "", "not inside a registered", "ok"),
        (1, "", "inside a registered repo", "ok"),
        (1, MARKER, "", "ok"),
        (2, "", "engram: internal failure", "ok"),
        (0, "", "", "ok"),
        (1, "", "repo not found", "ok"),
        (1, "", "not inside a  registered repo", "ok"),
        (1, "", "not a git repo", "ok"),
    ],
    ids=[
        "exact",
        "embedded",
        "case",
        "prefix",
        "suffix",
        "stdout-only",
        "nonzero-other",
        "zero-quiet",
        "repo-not-found",
        "double-space",
        "not-a-git-repo",
    ],
)
def test_engram_is_unregistered_only_on_the_exact_stderr_marker(
    catchup, tmp_path: Path, code: int, stdout: str, stderr: str, token: str
) -> None:
    fakes = Fakes({"gh": (0, "", ""), "engram": (code, stdout, stderr)})
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert_result(result, "ok", token, [] if token == "ok" else ["engram"])


@pytest.mark.parametrize(
    ("missing", "present_argv", "gh", "engram", "skip"),
    [
        ("gh", ENGRAM_ARGV, "absent", "ok", ["github-state"]),
        ("engram", GH_ARGV, "ok", "absent", ["engram"]),
    ],
    ids=["gh-missing", "engram-missing"],
)
def test_missing_binary_is_absent_and_never_run(
    catchup,
    tmp_path: Path,
    missing: str,
    present_argv: list,
    gh: str,
    engram: str,
    skip: list,
) -> None:
    present = present_argv[0]
    fakes = Fakes({present: (0, "", "")}, installed=(present,))
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert [argv for argv, _ in fakes.calls] == [present_argv]
    assert missing in fakes.lookups
    assert_result(result, gh, engram, skip)


@pytest.mark.parametrize(
    ("gh_installed", "gh_outcome", "gh", "skip"),
    [
        (True, (1, "", "not logged in"), "unauthenticated", ["github-state", "engram"]),
        (True, OSError(8, "Exec format error"), "absent", ["github-state", "engram"]),
        (False, None, "absent", ["github-state", "engram"]),
        (True, (0, "", ""), "ok", ["engram"]),
    ],
    ids=["gh-unauthenticated", "gh-spawn-failed", "gh-missing", "gh-ok"],
)
def test_missing_engram_is_absent_whatever_gh_reports(
    catchup, tmp_path: Path, gh_installed: bool, gh_outcome, gh: str, skip: list
) -> None:
    outcomes = {} if gh_outcome is None else {"gh": gh_outcome}
    fakes = Fakes(outcomes, installed=("gh",) if gh_installed else ())
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert ENGRAM_ARGV not in [argv for argv, _ in fakes.calls]
    assert "engram" in fakes.lookups
    assert_result(result, gh, "absent", skip)


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError(2, "No such file"),
        PermissionError(13, "Permission denied"),
        OSError(8, "Exec format error"),
        subprocess.TimeoutExpired(["x"], 15),
    ],
    ids=["not-found", "permission", "oserror", "timeout"],
)
@pytest.mark.parametrize("failing", ["gh", "engram"])
def test_spawn_failure_or_timeout_is_absent(
    catchup, tmp_path: Path, error: BaseException, failing: str
) -> None:
    outcomes = {"gh": (0, "", ""), "engram": (0, "", "")}
    outcomes[failing] = error
    fakes = Fakes(outcomes)
    result = catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert sorted(argv for argv, _ in fakes.calls) == sorted([GH_ARGV, ENGRAM_ARGV])
    if failing == "gh":
        assert_result(result, "absent", "ok", ["github-state"])
    else:
        assert_result(result, "ok", "absent", ["engram"])


@pytest.mark.parametrize(
    "error_type",
    [
        RuntimeError,
        NotImplementedError,
        ValueError,
        TypeError,
        KeyError,
        KeyboardInterrupt,
    ],
)
@pytest.mark.parametrize("failing", ["gh", "engram"])
def test_unexpected_run_error_is_surfaced_not_reported_absent(
    catchup, tmp_path: Path, failing: str, error_type: type
) -> None:
    outcomes = {"gh": (0, "", ""), "engram": (0, "", "")}
    outcomes[failing] = error_type(f"{failing} seam exploded")
    fakes = Fakes(outcomes)
    with pytest.raises(error_type, match=f"{failing} seam exploded") as raised:
        catchup.probe(tmp_path, run=fakes.run, which=fakes.which)
    assert type(raised.value) is error_type


def _tree(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): (p.read_bytes() if p.is_file() else b"")
        for p in sorted(root.rglob("*"))
    }


def test_ignores_live_state_and_keeps_no_cache_between_calls(
    catchup, tmp_path: Path
) -> None:
    state = tmp_path / "docs/dev/project-management/autopilot/state.json"
    state.parent.mkdir(parents=True)
    state.write_text(
        json.dumps(
            {
                "batch": {"id": "batch-1"},
                "catchup_probe": {
                    "batch_id": "batch-1",
                    "gh": "ok",
                    "engram": "ok",
                    "checked_at": "2026-01-01T00:00:00Z",
                },
            }
        )
    )
    before = _tree(tmp_path)
    root = Path(str(tmp_path))
    first = Fakes({"gh": (1, "", "not logged in"), "engram": (1, "", MARKER)})
    second = Fakes({"gh": (0, "", ""), "engram": (0, "", "")})
    modules = set(sys.modules)
    AUDIT["events"].clear()
    AUDIT["active"] = True
    try:
        one = catchup.probe(root, run=first.run, which=first.which)
        two = catchup.probe(root, run=second.run, which=second.which)
    finally:
        AUDIT["active"] = False
    assert AUDIT["events"] == []
    assert set(sys.modules) - modules == set()
    assert_result(one, "unauthenticated", "unregistered", ["github-state", "engram"])
    assert_result(two, "ok", "ok", [])
    assert len(first.calls) == 2 and len(second.calls) == 2
    assert root == tmp_path
    assert _tree(tmp_path) == before


def test_import_loads_no_runtime_or_state_modules() -> None:
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import catchup; "
        "print([m for m in sys.modules if m == 'cli' or m.startswith('cli.') "
        "or m.split('.')[-1] in {'state', 'statectl', 'custody'}])"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code, str(SCRIPTS)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=ROOT,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "[]"
