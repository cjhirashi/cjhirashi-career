"""Overrides editables de una sección del Admin (agente, sidebar, descripción)."""
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from database import Base


class AdminSectionOverride(Base):
    __tablename__ = "admin_section_overrides"

    # PK sintético de la sección: ``sec-N`` (ADR-021). Antes era el slug legible
    # (``dashboard``, ``career-projects``…), que ahora vive en
    # ``AdminSectionSpec.system_name``. La migración re-mapea las filas existentes.
    section_id = Column(String(40), primary_key=True)
    agent_profile_id = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    # { view_key: { description, sidebar_title, sidebar_body } }
    views = Column(JSONB, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AdminSectionOverride(section_id={self.section_id!r})>"
