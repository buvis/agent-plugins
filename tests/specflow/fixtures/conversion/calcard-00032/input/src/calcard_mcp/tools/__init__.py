"""MCP tool registrations, organised by domain.

Each submodule owns one domain's tools and exposes a single ``register``
entry point that :func:`calcard_mcp.server.build_server` calls in order:

* :mod:`calcard_mcp.tools.accounts` — ``list_accounts``.
* :mod:`calcard_mcp.tools.calendar` — calendar (CalDAV) tools.
* :mod:`calcard_mcp.tools.contact` — contact (CardDAV) tools.
* :mod:`calcard_mcp.tools.todo` — task (VTODO) tools.

The split keeps tool surface coherent per domain and lets ``server.py``
stay a thin wiring module.
"""
