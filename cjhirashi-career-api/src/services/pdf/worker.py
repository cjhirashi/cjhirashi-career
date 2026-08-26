"""Process-pool workers for WeasyPrint.

A native crash in Cairo/Pango must not take down the uvicorn parent.
These functions are top-level so ProcessPoolExecutor can pickle them.
"""


def render_html_template_pdf(title: str, html_body: str, css_content: str | None) -> bytes:
    from services.pdf.html_template_generator import HtmlTemplateGenerator

    generator = HtmlTemplateGenerator()
    buffer = generator.generate(title=title, html_body=html_body, css_content=css_content)
    return buffer.getvalue()


def render_markdown_document_pdf(title: str, content: str) -> bytes:
    from services.pdf.markdown_document_generator import MarkdownDocumentGenerator

    generator = MarkdownDocumentGenerator()
    buffer = generator.generate_document(title=title, content=content)
    return buffer.getvalue()
