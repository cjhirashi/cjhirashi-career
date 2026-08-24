"""HTML template PDF generator (WeasyPrint)."""

import logging
from io import BytesIO
from pathlib import Path

from weasyprint import HTML

from src.services.pdf_service import PDFService

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent / "templates")


class HtmlTemplateGenerator:
    """Renders custom HTML + optional CSS into a PDF."""

    def __init__(self):
        self.pdf_service = PDFService()

    def generate(self, title: str, html_body: str, css_content: str | None = None) -> BytesIO:
        if not html_body or not html_body.strip():
            raise ValueError("html_body is required")

        safe_title = title or "Document"
        css_block = css_content or ""
        full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>
@page {{ size: letter; margin: 18mm; }}
body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #111827; }}
{css_block}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

        try:
            pdf_bytes = HTML(string=full_html, base_url=_TEMPLATES_DIR).write_pdf()
            buf = BytesIO(pdf_bytes)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("HTML template PDF failed: %s", e)
            raise ValueError(f"Failed to generate PDF: {e}") from e

    def get_filename(self, title: str) -> str:
        return self.pdf_service.generate_filename("Template", title)
