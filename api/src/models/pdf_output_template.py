"""
PdfOutputTemplate — plantillas HTML para salida PDF (WeasyPrint).

Los estilos CSS viven en PdfTemplateStyle y se referencian con style_id.
Agente pdf_design las diseña; search y pdf-generator las consumen.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener


class PdfOutputTemplate(Base):
    __tablename__ = "pdf_output_templates"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(120), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    html_template = Column(Text, nullable=False)
    style_id = Column(String(20), ForeignKey("pdf_template_styles.id", ondelete="SET NULL"), nullable=True, index=True)
    variables = Column(Text, nullable=True)
    variables_schema = Column(JSONB, nullable=True)
    preview_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


register_id_listener(PdfOutputTemplate, "pdt")
