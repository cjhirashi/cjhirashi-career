"""HTML template PDF generator (WeasyPrint)."""
import logging
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_URL = str(Path(__file__).resolve().parent)


class HtmlTemplateGenerator:
    """Renders custom HTML + optional CSS into a PDF."""

    def generate(self, title: str, html_body: str, css_content: str | None = None) -> BytesIO:
        if not html_body or not html_body.strip():
            raise ValueError("html_body is required")

        from weasyprint import HTML

        safe_title = title or "Document"
        full_html = self.compose_html(safe_title, html_body, css_content or "")

        try:
            pdf_bytes = HTML(string=full_html, base_url=_BASE_URL).write_pdf()
            buf = BytesIO(pdf_bytes)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error("HTML template PDF failed: %s", e)
            raise ValueError(f"Failed to generate PDF: {e}") from e

    @staticmethod
    def compose_html(title: str, html_body: str, css_block: str) -> str:
        stripped = html_body.strip()
        lower = stripped.lower()
        is_full_document = lower.startswith("<!doctype") or lower.startswith("<html")

        base_css = """
@page { size: letter; margin: 18mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #111827; }
"""

        if is_full_document:
            inject = f"<style>\n{base_css}\n{css_block}\n</style>"
            if "</head>" in lower:
                idx = lower.index("</head>")
                return stripped[:idx] + inject + stripped[idx:]
            return inject + stripped

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{base_css}
{css_block}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
