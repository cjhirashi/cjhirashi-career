"""Tests for in-process PDF generation (WeasyPrint)."""
import pytest

from services.pdf.html_template_generator import HtmlTemplateGenerator
from services.pdf.markdown_document_template import MarkdownDocumentTemplate
from services.pdf_service import (
    PDFGeneratorError,
    generate_html_template_pdf,
    generate_markdown_document,
)


class TestHtmlCompose:
    def test_wraps_fragment(self):
        html = HtmlTemplateGenerator.compose_html("Título", "<p>Hola</p>", "h1{color:red}")
        assert "<!DOCTYPE html>" in html
        assert "<p>Hola</p>" in html
        assert "h1{color:red}" in html
        assert "<title>Título</title>" in html

    def test_injects_style_into_full_document(self):
        src = "<!DOCTYPE html><html><head></head><body><p>x</p></body></html>"
        html = HtmlTemplateGenerator.compose_html("Doc", src, "body{margin:0}")
        assert "body{margin:0}" in html
        assert html.lower().index("<style>") < html.lower().index("</head>")


class TestMarkdownTemplate:
    def test_escapes_title_in_header(self):
        out = MarkdownDocumentTemplate.render('Hi "there"', "<p>body</p>")
        assert "Hi &quot;there&quot;" in out
        assert "<p>body</p>" in out


class TestWeasyPrintRender:
    @pytest.fixture(autouse=True)
    def _need_weasyprint(self):
        pytest.importorskip("weasyprint")

    def test_html_fragment_produces_pdf(self):
        buf = HtmlTemplateGenerator().generate("Test", "<h1>Hola</h1>", None)
        data = buf.getvalue()
        assert data[:4] == b"%PDF"
        assert len(data) > 200

    def test_empty_html_raises(self):
        with pytest.raises(ValueError, match="html_body"):
            HtmlTemplateGenerator().generate("Test", "  ", None)

    def test_markdown_produces_pdf(self):
        from services.pdf.markdown_document_generator import MarkdownDocumentGenerator

        buf = MarkdownDocumentGenerator().generate_document("CV", "# Hola\n\nMundo")
        data = buf.getvalue()
        assert data[:4] == b"%PDF"
        assert len(data) > 200

    def test_empty_markdown_raises(self):
        from services.pdf.markdown_document_generator import MarkdownDocumentGenerator

        with pytest.raises(ValueError, match="Content is required"):
            MarkdownDocumentGenerator().generate_document("CV", "   ")


class TestPdfServicePoolWrappers:
    """Public API used by routes and Bedrock tools."""

    @pytest.mark.asyncio
    async def test_html_success_returns_bytes(self, monkeypatch):
        async def fake_run(fn, *args):
            assert args[0] == "Título"
            return b"%PDF-fake"

        monkeypatch.setattr("services.pdf_service._run_in_pool", fake_run)
        out = await generate_html_template_pdf("Título", "<p>x</p>", "h1{}")
        assert out == b"%PDF-fake"

    @pytest.mark.asyncio
    async def test_html_valueerror_becomes_pdf_error(self, monkeypatch):
        async def fake_run(fn, *args):
            raise ValueError("html_body is required")

        monkeypatch.setattr("services.pdf_service._run_in_pool", fake_run)
        with pytest.raises(PDFGeneratorError, match="html_body"):
            await generate_html_template_pdf("T", "  ", None)

    @pytest.mark.asyncio
    async def test_markdown_success_returns_bytes(self, monkeypatch):
        async def fake_run(fn, *args):
            return b"%PDF-md"

        monkeypatch.setattr("services.pdf_service._run_in_pool", fake_run)
        out = await generate_markdown_document("CV", "# Hola")
        assert out == b"%PDF-md"

    @pytest.mark.asyncio
    async def test_markdown_valueerror_becomes_pdf_error(self, monkeypatch):
        async def fake_run(fn, *args):
            raise ValueError("Content is required")

        monkeypatch.setattr("services.pdf_service._run_in_pool", fake_run)
        with pytest.raises(PDFGeneratorError, match="Content is required"):
            await generate_markdown_document("CV", "   ")
