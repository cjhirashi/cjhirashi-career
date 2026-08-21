"""Markdown Document Generator Service (free-form content, WeasyPrint)."""

import logging
from io import BytesIO
from pathlib import Path

import markdown
from weasyprint import HTML

from src.templates.markdown_document_template import MarkdownDocumentTemplate
from src.services.pdf_service import PDFService

logger = logging.getLogger(__name__)

# Markdown extensions: tables, fenced code blocks, and automatic <br> on
# single newlines (closer to how users expect a free-text editor to behave).
MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "nl2br"]

# base_url so WeasyPrint could resolve relative assets if the template ever
# references any (per the WeasyPrint + CSS paged media guide).
_TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent / "templates")


class MarkdownDocumentGenerator:
    """Service for generating PDFs from free-form Markdown content."""

    def __init__(self):
        """Initialize Markdown Document Generator."""
        self.pdf_service = PDFService()

    def generate_document(self, title: str, content: str) -> BytesIO:
        """Generate a PDF from a Markdown string.

        Args:
            title: Document title (shown in the page header).
            content: Raw Markdown content to render.

        Returns:
            BytesIO object with PDF data.

        Raises:
            ValueError: If content is empty or generation fails.
        """
        if not content or not content.strip():
            raise ValueError("Content is required and cannot be empty")

        try:
            logger.info(f"Generating Markdown document: {title}")

            body_html = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS)
            full_html = MarkdownDocumentTemplate.render(title=title, body_html=body_html)

            pdf_bytes = HTML(string=full_html, base_url=_TEMPLATES_DIR).write_pdf()

            pdf_buffer = BytesIO(pdf_bytes)
            pdf_buffer.seek(0)

            logger.info(f"Markdown document generated successfully: {title}")
            return pdf_buffer

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error generating Markdown document: {str(e)}")
            raise ValueError(f"Failed to generate document: {str(e)}")

    def get_document_filename(self, title: str) -> str:
        """Get formatted PDF filename for the document.

        Args:
            title: Document title.

        Returns:
            Formatted filename.
        """
        return self.pdf_service.generate_filename("Document", title)
