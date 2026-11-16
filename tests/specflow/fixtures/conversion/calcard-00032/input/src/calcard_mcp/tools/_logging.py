"""Audit-quality per-call logging for MCP tools.

Emits one line on entry with the full request payload, and one on exit
with elapsed time and the full response (or a FAIL line on raise with
the exception class and message). Writes go to a self-owned log file
at :data:`AUDIT_LOG_PATH` (``~/.claude/calcard-mcp.log``) so the audit
trail is reliably available regardless of how the host MCP client
(Claude Desktop, Cowork, etc.) handles subprocess stderr capture.
A secondary write to :data:`sys.stderr` keeps direct CLI runs visible.

The framework-injected ``ctx`` parameter (FastMCP
:class:`fastmcp.Context` for progress reporting) is excluded — it is
not part of the wire request and its repr is noisy.

This module deliberately bypasses :mod:`logging` and writes directly to
its destinations. fastmcp's :meth:`fastmcp.FastMCP.run_async` runs
:func:`logging.config.dictConfig` with the default
``disable_existing_loggers=True`` policy at transport startup, which
turns every pre-existing logger (including ours) into a record-dropping
no-op; direct writes are immune.

Use:

.. code-block:: python

    @server.tool
    @tool_logged
    async def my_tool(...) -> ...:
        ...

Decorator order matters: ``@tool_logged`` must be the *inner* decorator
so :func:`fastmcp.FastMCP.tool` wraps the logged version. ``functools.wraps``
preserves ``__wrapped__``, so fastmcp's :func:`inspect.signature` schema
introspection still resolves to the original function's annotations.
"""

from __future__ import annotations

import functools
import inspect
import json
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["AUDIT_LOG_PATH", "tool_logged"]

AUDIT_LOG_PATH = Path.home() / ".claude" / "calcard-mcp.log"
"""Self-owned audit log file. Created (with parents) on first write."""


def tool_logged[T](func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Wrap a coroutine MCP tool with stderr-direct audit logging.

    :param func: The coroutine tool function to wrap.
    :type func: collections.abc.Callable[..., collections.abc.Awaitable[T]]
    :returns: The wrapped function with the same signature as ``func``.
    :rtype: collections.abc.Callable[..., collections.abc.Awaitable[T]]
    """
    sig = inspect.signature(func)
    name = func.__name__

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        bound = sig.bind_partial(*args, **kwargs)
        audit_args = {k: v for k, v in bound.arguments.items() if k != "ctx"}
        start = time.monotonic()
        _emit("INFO", f"CALL {name} args={_safe_json(audit_args)}")
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            _emit(
                "WARNING",
                f"FAIL {name} [{elapsed_ms:.0f}ms] {type(exc).__name__}: {exc}",
            )
            raise
        elapsed_ms = (time.monotonic() - start) * 1000
        _emit("INFO", f"DONE {name} [{elapsed_ms:.0f}ms] result={_safe_json(result)}")
        return result

    return wrapper


def _emit(level: str, message: str) -> None:
    """Append a single audit line to :data:`AUDIT_LOG_PATH` and stderr.

    Mirrors the stdlib ``%(asctime)s %(levelname)s %(name)s: %(message)s``
    format so the audit file reads like a familiar Python log.

    The file is the primary destination (always present, host-app
    agnostic). Stderr is the secondary destination, useful for direct
    CLI runs where the operator is watching the terminal. Both writes
    are best-effort: an :class:`OSError` from either side is suppressed
    so that a logging glitch never breaks tool execution.

    :param level: Severity label (``"INFO"`` / ``"WARNING"``).
    :type level: str
    :param message: Pre-formatted audit message.
    :type message: str
    :returns: None.
    :rtype: None
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    line = f"{timestamp} {level} calcard_mcp.tools: {message}\n"
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    try:
        sys.stderr.write(line)
        sys.stderr.flush()
    except OSError:
        pass


def _safe_json(obj: Any) -> str:
    """Serialise ``obj`` as a single-line JSON string for log output.

    Falls back to :func:`repr` when the object contains values that
    :func:`json.dumps` cannot handle even with ``default=str`` (rare;
    most tool args and results are already JSON-friendly because they
    cross the MCP wire).

    :param obj: Any tool argument or return value.
    :type obj: typing.Any
    :returns: JSON-encoded string, or :func:`repr` fallback.
    :rtype: str
    """
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(obj)
