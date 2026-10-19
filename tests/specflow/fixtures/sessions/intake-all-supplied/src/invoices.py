"""Invoice views (session fixture)."""


def invoice_html(number: str, total: str) -> str:
    return f"<h1>Invoice {number}</h1><p>Total {total}</p>"
