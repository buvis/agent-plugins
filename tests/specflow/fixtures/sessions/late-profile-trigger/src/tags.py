"""Tags (session fixture)."""


def articles_with(tag: str, articles: list[dict]) -> list[dict]:
    return [a for a in articles if tag in a["tags"]]
