"""Overrides editables de una sección del Admin: agente L2 del chat contextual
del sidebar derecho y textos del sidebar por vista (feature 001).
"""
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from database import Base


class AdminSectionOverride(Base):
    __tablename__ = "admin_section_overrides"

    # PK sintético de la sección: ``sec-N`` (ADR-021). Antes era el slug legible
    # (``dashboard``, ``career-projects``…), que ahora vive en
    # ``AdminSectionSpec.system_name``. La migración re-mapea las filas existentes.
    section_id = Column(String(40), primary_key=True)
    # Agente L2 que atiende el chat contextual de la sección; NULL = sin chat.
    agent_profile_id = Column(String(50), nullable=True)
    # { view_key: { sidebar_title?, sidebar_body? } } — override por sub-campo:
    # ausente = hereda el texto de código; "" = override vacío explícito.
    views = Column(JSONB, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AdminSectionOverride(section_id={self.section_id!r})>"
