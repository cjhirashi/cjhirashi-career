"""
PdfTemplateStyle — estilos CSS reutilizables para plantillas PDF (WeasyPrint).

Varias plantillas pueden referenciar el mismo estilo vía style_id.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener


class PdfTemplateStyle(Base):
    __tablename__ = "pdf_template_styles"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(120), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    css_content = Column(Text, nullable=False)
    style_guide = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


register_id_listener(PdfTemplateStyle, "pds")
