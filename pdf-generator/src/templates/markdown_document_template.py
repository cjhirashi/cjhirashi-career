"""HTML template wrapper for free-form Markdown -> PDF documents (WeasyPrint).

Applies the CSS Paged Media (`@page`) conventions documented in
`server/Guia PDF WeasyPrint y CSS paged media.md` (tamaño carta, márgenes
que reservan espacio para encabezado/pie, numeración de página) so el
resultado sea visualmente consistente con el resto de documentos del
proyecto (paleta cyan usada en CVTemplate/CoverLetterTemplate).
"""

import html as html_escape


class MarkdownDocumentTemplate:
    """Wraps converted Markdown HTML in a styled, printable page."""

    # Matches CVTemplate.PRIMARY_COLOR / SECTION_COLOR
    PRIMARY_COLOR = "#0891B2"  # Cyan-600
    TEXT_COLOR = "#111827"
    MUTED_COLOR = "#6B7280"

    @classmethod
    def render(cls, title: str, body_html: str) -> str:
        """Build the full HTML document ready for WeasyPrint.

        Args:
            title: Document title (used in the header margin box and as
                the page `<title>`).
            body_html: HTML already converted from the user's Markdown.

        Returns:
            A complete HTML string (doctype, head with CSS, body).
        """
        safe_title = html_escape.escape(title)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<style>
{cls._css(safe_title)}
</style>
</head>
<body>
<article class="markdown-body">
{body_html}
</article>
</body>
</html>"""

    @classmethod
    def _css(cls, safe_title: str) -> str:
        """Build the CSS, including the `@page` paged-media rules."""
        return f"""
@page {{
    size: letter;
    margin-top: 28mm;
    margin-bottom: 22mm;
    margin-left: 18mm;
    margin-right: 18mm;

    @top-left {{
        content: "{safe_title}";
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        font-weight: 700;
        color: {cls.PRIMARY_COLOR};
        letter-spacing: 0.5px;
    }}

    @bottom-right {{
        content: "Página " counter(page) " de " counter(pages);
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        font-weight: 600;
        color: {cls.PRIMARY_COLOR};
    }}
}}

@page :first {{
    margin-top: 18mm;

    @top-left {{ content: none; }}
    @bottom-right {{ content: none; }}
}}

body {{
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: {cls.TEXT_COLOR};
}}

.markdown-body h1 {{
    font-size: 20pt;
    font-weight: 700;
    color: {cls.TEXT_COLOR};
    margin: 0 0 6pt 0;
}}

.markdown-body h2 {{
    font-size: 14pt;
    font-weight: 700;
    color: {cls.PRIMARY_COLOR};
    border-bottom: 1pt solid {cls.PRIMARY_COLOR};
    padding-bottom: 3pt;
    margin: 16pt 0 8pt 0;
}}

.markdown-body h3 {{
    font-size: 12pt;
    font-weight: 700;
    color: {cls.TEXT_COLOR};
    margin: 12pt 0 6pt 0;
}}

.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {{
    font-size: 10.5pt;
    font-weight: 700;
    color: {cls.TEXT_COLOR};
    margin: 10pt 0 4pt 0;
}}

.markdown-body p {{
    margin: 0 0 8pt 0;
    text-align: left;
}}

.markdown-body ul,
.markdown-body ol {{
    margin: 0 0 8pt 0;
    padding-left: 18pt;
}}

.markdown-body li {{
    margin-bottom: 3pt;
}}

.markdown-body a {{
    color: {cls.PRIMARY_COLOR};
    text-decoration: underline;
}}

.markdown-body strong {{
    font-weight: 700;
}}

.markdown-body em {{
    font-style: italic;
}}

.markdown-body blockquote {{
    margin: 8pt 0;
    padding: 4pt 10pt;
    border-left: 3pt solid {cls.PRIMARY_COLOR};
    color: {cls.MUTED_COLOR};
    font-style: italic;
}}

.markdown-body code {{
    font-family: 'Courier New', monospace;
    font-size: 9.5pt;
    background-color: #F3F4F6;
    padding: 1pt 3pt;
    border-radius: 2pt;
}}

.markdown-body pre {{
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    background-color: #F3F4F6;
    padding: 8pt;
    border-radius: 3pt;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 0 0 8pt 0;
}}

.markdown-body pre code {{
    background-color: transparent;
    padding: 0;
}}

.markdown-body hr {{
    border: none;
    border-top: 0.75pt solid #E5E7EB;
    margin: 12pt 0;
}}

.markdown-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 0 0 8pt 0;
    font-size: 9.5pt;
}}

.markdown-body th,
.markdown-body td {{
    border: 0.75pt solid #E5E7EB;
    padding: 4pt 6pt;
    text-align: left;
}}

.markdown-body th {{
    background-color: #F3F4F6;
    font-weight: 700;
    color: {cls.TEXT_COLOR};
}}
"""
