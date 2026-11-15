"""Cross-session job requests, session binding and native-child cleanup.

Builds validated host-neutral job.plan requests and either returns a
standalone launch instruction or forwards the request to a controller seam.
Binds a fresh child session to its request and closes in-session children.
Never starts, signals or stops a process (AP 00014 architecture fit).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import shlex
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Protocol

import hosts

TIERS = ("haiku", "sonnet", "opus", "fable")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
MAX_JOB_DEPTH = 1
MAX_CHILD_DEPTH = 1
MAX_INPUT_BYTES = 33554432
MAX_JOB_FILE_BYTES = 2097152
INTENT_SCHEMA = "autopilot.job-intent.v1"
JOB_ENV = "AUTOPILOT_JOB_REQUEST"
DEPTH_ENV = "AUTOPILOT_DISPATCH_DEPTH"
LINEAGE_DIR = PurePosixPath("docs/dev/tmp/autopilot/jobs")
CHILD_OUTCOMES = ("completed", "cancelled", "failed")

_FIXED = {
    "intent_schema": INTENT_SCHEMA,
    "operation": "job.plan",
    "required_capability": "workflow.jobs.v1",
    "execution": "cross-session",
    "isolation": "fresh-session",
}
_PAYLOAD_KEYS = {
    *_FIXED, "job_id", "role_id", "host_id", "tier", "effort", "inputs",
    "excluded_input_kinds", "requester", "ancestry", "request_id",
}
_STATE_PARTS = ("docs", "dev", "project-management", "autopilot")
_PLUGIN = Path(__file__).resolve().parents[1]
_POLICY = _PLUGIN / "contracts" / "review-policy-v1.json"
_WORKFLOW = _PLUGIN / "contracts" / "controller" / "workflow-v1.json"
_MALFORMED_REPLY = {"accepted": False, "job_ref": None, "error": "malformed_controller_reply"}


class JobRefused(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


class ControllerSeam(Protocol):
    def submit_job(self, intent: dict) -> dict: ...

    def evaluate_guard(self, duty: str, context: dict) -> dict: ...

    def read_facts(self, duty: str, session: dict | None, project_root: str) -> dict: ...


def _invalid(detail: str) -> JobRefused:
    return JobRefused("invalid_request", detail)


def _one_of(value: object, table) -> bool:
    return isinstance(value, str) and value in table


def _input_kinds() -> tuple[str, ...]:
    return tuple(json.loads(_POLICY.read_text(encoding="utf-8"))["input_kinds"])


def _controller_error_codes() -> tuple[str, ...]:
    document = json.loads(_WORKFLOW.read_text(encoding="utf-8"))
    return tuple(document["x-controller"]["error_codes"])


def _mapping(value: object, keys: set[str], what: str) -> Mapping:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise _invalid(f"{what} must hold exactly {sorted(keys)}")
    return value


def _check_relative_path(path: object) -> None:
    """A non-empty relative POSIX path with no parent step, outside the
    controller state tree."""
    if not isinstance(path, str) or not path:
        raise _invalid("path must be a non-empty string")
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise _invalid(f"path {path!r} must be relative without parent steps")
    casefolded = tuple(part.casefold() for part in pure.parts[: len(_STATE_PARTS)])
    if casefolded == _STATE_PARTS:
        raise _invalid(f"path {path!r} is controller state")


def _check_identity(field: str, value: object) -> None:
    try:
        size = len(value.encode("utf-8")) if isinstance(value, str) else 0
    except UnicodeEncodeError:
        size = 0
    if not 1 <= size <= 256:
        raise _invalid(f"{field} must hold 1 to 256 UTF-8 bytes")
    if value in {*hosts.PROVIDER_HOSTS, *hosts.ADAPTERS, *TIERS}:
        raise _invalid(f"{field} {value!r} is a provider, host or tier name")


@dataclasses.dataclass(frozen=True)
class InputRef:
    kind: str
    path: str
    sha256: str


@dataclasses.dataclass(frozen=True)
class AncestryEntry:
    host_id: str
    job_id: str
    session_id: str

    def __post_init__(self) -> None:
        if not _one_of(self.host_id, hosts.ADAPTERS):
            raise _invalid(f"unknown ancestry host_id: {self.host_id!r}")
        for value in (self.job_id, self.session_id):
            if not isinstance(value, str) or not value:
                raise _invalid("ancestry job_id and session_id must be non-empty strings")


@dataclasses.dataclass(frozen=True)
class JobRequest:
    job_id: str
    role_id: str
    host_id: str
    tier: str
    effort: str
    inputs: tuple[InputRef, ...]
    excluded_input_kinds: tuple[str, ...]
    requester: hosts.NativeSession
    ancestry: tuple[AncestryEntry, ...]

    def __post_init__(self) -> None:
        _check_identity("job_id", self.job_id)
        _check_identity("role_id", self.role_id)
        for field, table in (("host_id", hosts.ADAPTERS), ("tier", TIERS), ("effort", EFFORTS)):
            if not _one_of(getattr(self, field), table):
                raise _invalid(f"unknown {field}: {getattr(self, field)!r}")
        if not isinstance(self.requester, hosts.NativeSession):
            raise JobRefused("missing_native_session", "requester has no native session")
        kinds = _input_kinds()
        for kind in self.excluded_input_kinds:
            if kind not in kinds:
                raise _invalid(f"unknown excluded input kind: {kind!r}")
        for ref in self.inputs:
            if ref.kind not in kinds:
                raise _invalid(f"unknown input kind: {ref.kind!r}")
            if ref.kind in self.excluded_input_kinds:
                raise _invalid(f"input kind {ref.kind!r} is excluded")
            _check_relative_path(ref.path)
            if not isinstance(ref.sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", ref.sha256):
                raise _invalid(f"input {ref.path!r} has no lowercase sha256")
        if any(e.host_id == self.host_id and e.job_id == self.job_id for e in self.ancestry):
            raise JobRefused("recursive_job",
                             f"host {self.host_id!r} job {self.job_id!r} already in ancestry")
        if len(self.ancestry) >= MAX_JOB_DEPTH:
            raise JobRefused("recursion_depth", f"ancestry depth {len(self.ancestry)}")

    def _body(self) -> dict:
        return {
            "intent_schema": INTENT_SCHEMA,
            "operation": _FIXED["operation"],
            "required_capability": _FIXED["required_capability"],
            "job_id": self.job_id,
            "role_id": self.role_id,
            "host_id": self.host_id,
            "execution": _FIXED["execution"],
            "isolation": _FIXED["isolation"],
            "tier": self.tier,
            "effort": self.effort,
            "inputs": [dataclasses.asdict(ref) for ref in self.inputs],
            "excluded_input_kinds": list(self.excluded_input_kinds),
            "requester": {"host_id": self.requester.host_id,
                          "session_id": self.requester.session_id,
                          "source": self.requester.source},
            "ancestry": [dataclasses.asdict(entry) for entry in self.ancestry],
        }

    @property
    def request_id(self) -> str:
        return _canonical_id(self._body())

    def to_payload(self) -> dict:
        body = self._body()
        body["request_id"] = _canonical_id(body)
        return body

    @classmethod
    def from_payload(cls, payload: object) -> JobRequest:
        """Rebuilds and revalidates a request; the payload must match its own
        request_id. Input files are not read here (bind_job_session does)."""
        payload = _mapping(payload, _PAYLOAD_KEYS, "payload")
        body = {key: value for key, value in payload.items() if key != "request_id"}
        try:
            matches = payload["request_id"] == _canonical_id(body)
        except (TypeError, ValueError):
            matches = False
        if not matches:
            raise _invalid("payload does not match its request_id")
        if any(payload[key] != value for key, value in _FIXED.items()):
            raise _invalid("payload fixed fields differ from job.plan")
        if not all(isinstance(payload[key], list)
                   for key in ("inputs", "excluded_input_kinds", "ancestry")):
            raise _invalid("inputs, excluded_input_kinds and ancestry must be lists")
        requester = _mapping(payload["requester"], {"host_id", "session_id", "source"},
                             "requester")
        try:
            session = hosts.NativeSession(**requester)
        except (TypeError, ValueError, AttributeError) as error:
            raise _invalid(f"requester: {error}") from None
        return cls(
            job_id=payload["job_id"],
            role_id=payload["role_id"],
            host_id=payload["host_id"],
            tier=payload["tier"],
            effort=payload["effort"],
            inputs=tuple(InputRef(**_mapping(item, {"kind", "path", "sha256"}, "input"))
                         for item in payload["inputs"]),
            excluded_input_kinds=tuple(payload["excluded_input_kinds"]),
            requester=session,
            ancestry=tuple(
                AncestryEntry(**_mapping(item, {"host_id", "job_id", "session_id"}, "ancestry"))
                for item in payload["ancestry"]
            ),
        )


def _canonical_id(body: dict) -> str:
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_input(item: object, root: Path) -> InputRef:
    """The InputRef for a {kind, path} mapping, digesting the regular file it
    resolves to inside `root`."""
    item = _mapping(item, {"kind", "path"}, "input")
    _check_relative_path(item["path"])
    target = (root / item["path"]).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise _invalid(f"input {item['path']!r} is not a regular file inside the project")
    _check_relative_path(target.relative_to(root).as_posix())
    if target.stat().st_size > MAX_INPUT_BYTES:
        raise _invalid(f"input {item['path']!r} exceeds {MAX_INPUT_BYTES} bytes")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return InputRef(kind=item["kind"], path=item["path"], sha256=digest)


def _lineage_path(host_id: str, session_id: str) -> PurePosixPath:
    return LINEAGE_DIR / f"{host_id}-{hashlib.sha256(session_id.encode('utf-8')).hexdigest()}.json"


def build_job_request(
    *,
    job_id: str,
    role_id: str,
    host_id: str,
    tier: str,
    effort: str,
    inputs: list,
    excluded_input_kinds: list,
    requester: hosts.NativeSession | None,
    ancestry: tuple,
    project_root: Path,
) -> JobRequest:
    root = Path(project_root).resolve()
    refs = sorted((_read_input(item, root) for item in inputs),
                  key=lambda ref: (ref.kind, ref.path))
    request = JobRequest(
        job_id=job_id, role_id=role_id, host_id=host_id, tier=tier, effort=effort,
        inputs=tuple(refs), excluded_input_kinds=tuple(excluded_input_kinds),
        requester=requester, ancestry=tuple(ancestry),
    )
    # A bound job session keeps its depth even when its env was stripped.
    record = root / _lineage_path(requester.host_id, requester.session_id)
    if os.path.lexists(record):
        try:
            bound_depth = len(json.loads(record.read_text(encoding="utf-8"))["ancestry"])
        except (OSError, ValueError, KeyError, TypeError):
            bound_depth = MAX_JOB_DEPTH  # an unreadable record fails closed
        if bound_depth >= MAX_JOB_DEPTH:
            raise JobRefused("recursion_depth", "requester is a bound job session")
    return request


def derive_ancestry(env: Mapping[str, str], project_root: Path) -> tuple[AncestryEntry, ...]:
    """The current session's ancestry: empty without JOB_ENV, else the job
    file's ancestry plus this job's host, job and current native session.
    DEPTH_ENV alone, without JOB_ENV, still backstops recursion depth even
    when the job file's env was stripped."""
    if DEPTH_ENV in env:
        value = env[DEPTH_ENV]
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
            raise _invalid(f"{DEPTH_ENV} must be a non-negative integer")
        if int(value) >= MAX_JOB_DEPTH:
            raise JobRefused("recursion_depth", f"dispatch depth {value}")
    if JOB_ENV not in env:
        return ()
    try:
        with open(Path(project_root) / env[JOB_ENV], "rb") as stream:
            data = stream.read(MAX_JOB_FILE_BYTES + 1)
    except OSError as error:
        raise _invalid(f"job file unreadable: {error}") from None
    if len(data) > MAX_JOB_FILE_BYTES:
        raise _invalid(f"job file exceeds {MAX_JOB_FILE_BYTES} bytes")
    try:
        payload = json.loads(data)
    except ValueError:
        raise _invalid("job file is not JSON") from None
    request = JobRequest.from_payload(payload)
    session = hosts.current_session(request.host_id, env)
    if session is None:
        raise JobRefused("missing_native_session", "job session has no native session")
    return (*request.ancestry, AncestryEntry(host_id=request.host_id, job_id=request.job_id,
                                             session_id=session.session_id))


def _write_new(root: Path, relative: PurePosixPath, data: bytes) -> None:
    """Creates `root/relative` exclusively, never following a symlink below
    `root`: each directory is created if missing and opened O_NOFOLLOW."""
    fd = os.open(root, os.O_DIRECTORY)
    try:
        for name in relative.parts[:-1]:
            try:
                os.mkdir(name, dir_fd=fd)
            except FileExistsError:
                pass
            next_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        out = os.open(relative.name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                      0o666, dir_fd=fd)
    finally:
        os.close(fd)
    with os.fdopen(out, "wb") as stream:
        stream.write(data)


def write_binding_record(host_id: str, session_id: str, record: dict, *,
                         project_root: Path) -> str:
    """Writes the lineage record for a child session; never overwrites one."""
    relative = _lineage_path(host_id, session_id)
    _write_new(Path(project_root).resolve(), relative, json.dumps(record).encode("utf-8"))
    return relative.as_posix()


def bind_job_session(payload: object, *, child: hosts.NativeSession,
                     project_root: Path) -> dict:
    """Binds a fresh session of the job's host to the request after
    re-verifying every input digest, and records the lineage once."""
    request = JobRequest.from_payload(payload)
    if child.host_id != request.host_id:
        raise JobRefused("host_mismatch", f"child host {child.host_id!r} is not {request.host_id!r}")
    if child.session_id == request.requester.session_id:
        raise JobRefused("same_session", "child reuses the requester session")
    root = Path(project_root).resolve()
    if os.path.lexists(root / _lineage_path(child.host_id, child.session_id)):
        raise JobRefused("recursion_depth", "child session is already bound to a job")
    for ref in request.inputs:
        try:
            current = _read_input({"kind": ref.kind, "path": ref.path}, root)
        except JobRefused:
            current = None
        if current != ref:
            raise JobRefused("input_digest_mismatch", f"input {ref.path!r} changed")
    body = request.to_payload()
    record = {
        "schema_version": 1,
        "request_id": body["request_id"],
        "job_id": request.job_id,
        "host_id": request.host_id,
        "child_session": {"host_id": child.host_id, "session_id": child.session_id,
                          "source": child.source},
        "requester_session": body["requester"],
        "verified_inputs": body["inputs"],
        "ancestry": [*body["ancestry"],
                     {"host_id": request.requester.host_id, "job_id": request.job_id,
                      "session_id": request.requester.session_id}],
    }
    write_binding_record(child.host_id, child.session_id, record, project_root=root)
    return record


def close_native_child(*, parent: hosts.NativeSession, child: Mapping, outcome: str,
                       raw_output: bytes, artifact_path: Path, project_root: Path) -> dict:
    """Writes an in-session child's raw output once and reports its digest."""
    child = _mapping(child, {"child_id", "kind", "parent_session_id", "depth"}, "child")
    depth = child["depth"]
    if not isinstance(child["child_id"], str) or not child["child_id"] \
            or isinstance(depth, bool) or not isinstance(depth, int):
        raise _invalid("child_id must be a non-empty string and depth an integer")
    if outcome not in CHILD_OUTCOMES:
        raise _invalid(f"unknown outcome: {outcome!r}")
    if child["kind"] != "in-session" or child["parent_session_id"] != parent.session_id:
        raise JobRefused("foreign_child", "child is not this session's in-session child")
    if depth > MAX_CHILD_DEPTH:
        raise JobRefused("recursion_depth", f"child depth {depth}")
    root = Path(project_root).resolve()
    path = Path(artifact_path)
    if ".." in path.parts or not path.is_relative_to(root):
        raise _invalid(f"artifact {path} is outside the project")
    relative = PurePosixPath(path.relative_to(root).as_posix())
    _check_relative_path(relative.as_posix())
    _write_new(root, relative, raw_output)
    return {
        "schema_version": 1,
        "child_id": child["child_id"],
        "outcome": outcome,
        "artifact": {"path": relative.as_posix(),
                     "sha256": hashlib.sha256(raw_output).hexdigest(),
                     "bytes": len(raw_output)},
        "cleanup": "completed",
    }


def _build_job_argv(adapter, request: JobRequest) -> list[str]:
    build = getattr(adapter, "build_job_argv", None)
    if build is None:
        raise _invalid(f"host {request.host_id!r} adapter cannot build a job argv")
    argv = build(request)
    if not isinstance(argv, list):
        raise _invalid(f"host {request.host_id!r} adapter returned no job argv")
    return list(argv)


def _valid_reply(reply: object) -> bool:
    if not isinstance(reply, dict) or set(reply) != {"accepted", "job_ref", "error"}:
        return False
    if reply["accepted"] is True:
        return isinstance(reply["job_ref"], str) and bool(reply["job_ref"]) \
            and reply["error"] is None
    return reply["accepted"] is False and reply["job_ref"] is None \
        and _one_of(reply["error"], _controller_error_codes())


def _write_request_file(resolved_file: Path, root: Path, payload: dict) -> None:
    try:
        relative = resolved_file.relative_to(root).as_posix()
    except ValueError:
        raise _invalid("request_file must be inside project_root") from None
    _check_relative_path(relative)
    data = json.dumps(payload).encode("utf-8")
    try:
        fd = os.open(resolved_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o666)
    except FileNotFoundError:
        resolved_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(resolved_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o666)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def _standalone_instruction(request: JobRequest, argv: list[str], request_file: Path,
                             root: Path) -> dict:
    depth = str(len(request.ancestry) + 1)
    script = Path(__file__).resolve().parent / "autopilot.py"
    bind = (f'python3 {shlex.quote(str(script))} --bind-job "${JOB_ENV}" '
            f"--project-root {shlex.quote(str(root))}")
    listed = "\n".join(f"- {ref.kind}: {ref.path}" for ref in request.inputs)
    stdin = (f"You are {request.role_id} for job {request.job_id}.\n"
             f"Before anything else, bind this session to the job:\n{bind}\n"
             f"Then read only these inputs:\n{listed}\n")
    return {
        "host_id": request.host_id,
        "argv": argv,
        "stdin": stdin,
        "env": {JOB_ENV: str(request_file), DEPTH_ENV: depth},
        "manual_settings": {"tier": request.tier, "effort": request.effort},
        "steps": [
            f"Start a fresh {request.host_id} session with {JOB_ENV}={request_file} "
            f"and {DEPTH_ENV}={depth} in its environment.",
            f"Set the model tier to {request.tier} and effort to {request.effort} by hand.",
            "Run the argv and pass the stdin text to it.",
            f"The child runs --bind-job on {request_file} before it reads any input.",
        ],
    }


def request_job(request: JobRequest, *, seam: ControllerSeam | None, project_root: Path,
                request_file: Path | None) -> dict:
    """Standalone mode (seam None) writes the request file and returns a
    launch instruction; controller mode forwards the payload to
    seam.submit_job and nests its validated reply. Never starts a process."""
    if seam is not None:
        try:
            reply = seam.submit_job(request.to_payload())
        except Exception:  # a raising seam is a malformed reply, never a fallback
            reply = None
        reply = dict(reply) if _valid_reply(reply) else dict(_MALFORMED_REPLY)
        return {"schema_version": 1, "mode": "controller", "request": request.to_payload(),
                "reply": reply}
    if request_file is None:
        raise _invalid("standalone mode needs a request file")
    argv = _build_job_argv(hosts.adapter(request.host_id), request)
    payload = request.to_payload()
    root = Path(project_root).resolve()
    resolved_file = Path(request_file).resolve()
    _write_request_file(resolved_file, root, payload)
    instruction = _standalone_instruction(request, argv, request_file, root)
    return {"schema_version": 1, "mode": "standalone", "request": payload, "instruction": instruction}
