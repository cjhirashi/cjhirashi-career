"""Resuelve el CSS de una plantilla PDF desde su estilo referenciado."""
from sqlalchemy.ext.asyncio import AsyncSession

from models.pdf_output_template import PdfOutputTemplate
from models.pdf_template_style import PdfTemplateStyle


async def resolve_template_css(db: AsyncSession, template: PdfOutputTemplate) -> str | None:
    if not template.style_id:
        return None
    style = await db.get(PdfTemplateStyle, template.style_id)
    if style is None or not style.is_active:
        return None
    return style.css_content or None
