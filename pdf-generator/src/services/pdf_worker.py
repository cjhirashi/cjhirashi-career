"""Process-pool worker for CPU-heavy WeasyPrint rendering.

Runs in a separate process so a native crash (segfault) in Cairo/Pango
cannot take down the uvicorn parent process.
"""


def render_html_template_pdf(title: str, html_body: str, css_content: str | None) -> bytes:
    from src.services.html_template_generator import HtmlTemplateGenerator

    generator = HtmlTemplateGenerator()
    buffer = generator.generate(title=title, html_body=html_body, css_content=css_content)
    return buffer.getvalue()
