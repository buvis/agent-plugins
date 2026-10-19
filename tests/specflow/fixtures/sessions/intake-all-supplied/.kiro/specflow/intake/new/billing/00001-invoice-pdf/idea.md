# Idea: invoice-pdf

Received: 2026-10-16

Add a "Download PDF" link to the invoice page. The PDF renders the existing
invoice HTML with weasyprint, which requirements.txt already installs. The HTML
view and its URL must not change. No system outside this repository is
involved. Tests are written before the code; no thin slice is needed, it is one
endpoint. Done when the download returns a PDF that shows the invoice number
and the total.
