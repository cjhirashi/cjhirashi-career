"""Markdown → PDF (WeasyPrint)."""
import logging
from io import BytesIO
from pathlib import Path

import markdown

from services.pdf.markdown_document_template import MarkdownDocumentTemplate

logger = logging.getLogger(__name__)

MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "nl2br"]
_BASE_URL = str(Path(__file__).resolve().parent)


class MarkdownDocumentGenerator:
    def generate_document(self, title: str, content: str) -> BytesIO:
        if not content or not content.strip():
            raise ValueError("Content is required and cannot be empty")

        try:
            from weasyprint import HTML

            body_html = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS)
            full_html = MarkdownDocumentTemplate.render(title=title, body_html=body_html)
            pdf_bytes = HTML(string=full_html, base_url=_BASE_URL).write_pdf()
            pdf_buffer = BytesIO(pdf_bytes)
            pdf_buffer.seek(0)
            return pdf_buffer
        except ValueError:
            raise
        except Exception as e:
            logger.error("Error generating Markdown document: %s", e)
            raise ValueError(f"Failed to generate document: {e}") from e
