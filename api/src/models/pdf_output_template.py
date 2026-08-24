"""
PdfOutputTemplate — plantillas HTML/CSS para salida PDF (WeasyPrint).

Agente pdf_design las diseña; search y pdf-generator las consumen.
Ver ADR-010.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class PdfOutputTemplate(Base):
    __tablename__ = "pdf_output_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(120), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    html_template = Column(Text, nullable=False)
    css_content = Column(Text, nullable=True)
    variables_schema = Column(JSONB, nullable=True)
    preview_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
