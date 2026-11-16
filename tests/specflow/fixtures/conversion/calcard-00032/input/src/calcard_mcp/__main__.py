"""Entry point for running calcard-mcp as a module or console script.

Imports:

* :mod:`argparse` for CLI parsing.
* :mod:`asyncio` to run the MCP stdio server event loop.
* :mod:`contextlib` for :class:`~contextlib.ExitStack`, which guarantees
  every shutdown ``close()`` callback runs regardless of which raises.
* :mod:`logging` for structured diagnostics on stderr.
* :mod:`pathlib.Path` for config file resolution.
* :class:`calcard_mcp.config.AppConfig` for loading YAML configuration.
* :func:`calcard_mcp.server.build_server` to construct the configured server.
* :func:`calcard_mcp.server.safe_close` for the swallow-and-log cleanup
  helper shared with :func:`build_server`.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import sys
from pathlib import Path

from calcard_mcp.config import AppConfig
from calcard_mcp.server import build_server, safe_close

# ``main`` is the only stable public entry point of this module; ``run``
# is the asyncio body it dispatches to and is exposed (rather than
# underscore-private) only because the lifecycle tests need to drive the
# cleanup path directly without going through ``main``'s exception swallow.
# Listing it here documents the test-only contract without reaching for
# pyright's reportPrivateUsage (banned by ``rules/coding-style.md`` "Never
# silence warnings"). External callers should depend on ``main`` only.
__all__ = ["main", "run"]


def _setup_logging(level: str) -> None:
    """Configure stderr logging that survives fastmcp's logging takeover.

    fastmcp's :meth:`fastmcp.FastMCP.run_async` reconfigures the root
    logger via Rich during transport startup, which clobbers any
    prior :func:`logging.basicConfig` call (even with ``force=True``).
    To guarantee our package's audit lines reach stderr regardless of
    what fastmcp does to the root logger, we attach a dedicated
    :class:`logging.StreamHandler` directly to the ``calcard_mcp``
    logger and set ``propagate=False`` so records are emitted exactly
    once and not subject to the root logger's level or handler set.

    :param level: Logging verbosity name (``"DEBUG"`` / ``"INFO"`` /
        ``"WARNING"`` / ``"ERROR"``).
    :type level: str
    :returns: None.
    :rtype: None
    """
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.setLevel(level)
    own = logging.getLogger("calcard_mcp")
    own.setLevel(level)
    # Replace any prior handler so repeated calls (e.g. from tests) don't
    # accumulate duplicate stderr writes.
    for existing in list(own.handlers):
        own.removeHandler(existing)
    own.addHandler(handler)
    own.propagate = False


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments.

    :param argv: Argument vector excluding the program name.
    :type argv: list[str]
    :returns: Parsed argument namespace with ``config`` and ``log_level`` fields.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        prog="calcard-mcp",
        description="Multi-account CalDAV/CardDAV MCP server.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to YAML configuration file (default: ./config.yaml).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http"],
        help="Transport (default: stdio). 'http' is reserved for the deployment PRD.",
    )
    return parser.parse_args(argv)


async def run(config_path: Path, transport: str) -> None:
    """Load config, build the server, and serve over the requested transport.

    Internal entry point: stable consumers should call :func:`main`,
    which wraps this coroutine in :func:`asyncio.run` and translates
    propagating exceptions into a process exit code. ``run`` is module-
    public (rather than underscore-private) only so the lifecycle tests
    can drive the cleanup path directly without ``main``'s
    ``except Exception`` swallow. See :data:`__all__` for the stable
    surface.

    The contact service owns CardDAV ``httpx`` connection pools, the
    todo service owns ``caldav`` HTTP sessions of the per-account VTODO
    clients, and the calendar service owns ``caldav`` HTTP sessions of
    the per-account VEVENT/free-busy clients; all three must be closed
    when the transport shuts down to avoid leaking sockets.

    Cleanup uses :class:`contextlib.ExitStack` so every ``close()`` runs
    in LIFO order even if an earlier one raises. Each close is wrapped
    in :func:`calcard_mcp.server.safe_close`, which catches
    :class:`Exception` only and logs the failure, so a routine close-
    time :class:`Exception` keeps the original shutdown reason
    (``KeyboardInterrupt``, transport error, etc.) as the propagating
    exception. This is what makes :func:`main`'s
    ``except KeyboardInterrupt: return 0`` / ``except Exception: return 1``
    split work for the common case: a clean Ctrl-C still exits 0 even
    if a close raises an :class:`Exception` during teardown.

    ``safe_close`` does **not** swallow :class:`BaseException`
    (``KeyboardInterrupt``, ``SystemExit``, ``asyncio.CancelledError``).
    A ``BaseException`` raised inside a ``close()`` propagates and
    chains via Python's exception-context machinery: ``ExitStack``
    still runs the remaining ``close()`` callbacks (the chain is not
    aborted), and the original shutdown exception is demoted to
    ``__context__`` of whatever ``BaseException`` last raised. In
    particular, if ``run_async`` was already raising an
    :class:`Exception` and a ``close()`` then raises a
    :class:`BaseException`, the BaseException becomes the propagating
    exception out of the ``with`` block, and :func:`main`'s
    ``except KeyboardInterrupt: return 0`` branch could mask the
    original transport :class:`Exception` (which would now live in
    ``__context__``). No service ``close()`` is expected to raise
    ``BaseException`` in production; the prose documents the edge.

    :param config_path: Path to the YAML configuration file.
    :type config_path: pathlib.Path
    :param transport: Transport name; must be ``"stdio"`` for now.
    :type transport: str
    :returns: None. This coroutine runs until the transport closes.
    :rtype: None
    :raises NotImplementedError: When ``transport`` is ``"http"``.
    :raises calcard_mcp.errors.ConfigError: When the config file is missing or invalid.
    """
    if transport == "http":
        raise NotImplementedError(
            "--transport http is reserved for the deployment PRD; use stdio for now."
        )
    config = AppConfig.load(config_path)
    server, contact_service, todo_service, calendar_service = build_server(config)
    # Register in build_server's construction order (calendar, contact, todo)
    # so LIFO firing yields strict reverse-of-construction close order on
    # transport shutdown.
    with contextlib.ExitStack() as cleanup:
        cleanup.callback(safe_close, calendar_service)
        cleanup.callback(safe_close, contact_service)
        cleanup.callback(safe_close, todo_service)
        await server.run_async()


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint.

    :param argv: Optional argument vector; defaults to :data:`sys.argv` when ``None``.
    :type argv: list[str] | None
    :returns: Process exit code (``0`` on clean shutdown, ``1`` on fatal error).
    :rtype: int
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _setup_logging(args.log_level)
    try:
        asyncio.run(run(args.config, args.transport))
    except KeyboardInterrupt:
        return 0
    except Exception:
        logging.getLogger(__name__).exception("fatal error")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
