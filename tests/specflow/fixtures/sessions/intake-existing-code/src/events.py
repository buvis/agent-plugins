"""In-process events (session fixture)."""

HANDLERS: dict[str, list] = {}


def emit(name: str, data: dict) -> None:
    for handler in HANDLERS.get(name, []):
        handler(data)
