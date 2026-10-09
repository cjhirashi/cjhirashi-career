"""
OperationalMethodology Model - protocols/frameworks that document HOW to work
across the career-domain tables and how they relate to each other (e.g. "a
change in Identity propagates to Competencies, Evidence, ..."). Content lives
in Markdown, authored the same convention as every other long-text field in
this app - see `content`. Not exposed on the public portal, admin-only.
Career domain (v2) - Soporte operativo.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class OperationalMethodology(Base):
    __tablename__ = "operational_methodologies"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    # IDs canónicos agent_* para quienes aplica esta metodología — SÓLO L1/L3
    # desde spec 004 (los L2 la reciben vía sección). Vacío/null + section_ids
    # vacío/null = compartida (todos). Lista = sólo esos perfiles L1/L3.
    agent_profile_ids = Column(JSONB, nullable=True)
    # IDs sec-N de las secciones del Admin a las que está ligada esta
    # metodología (spec 004). Un agente L2 ligado a alguna de esas secciones la
    # recibe. Vacío/null = no ligada a ninguna sección.
    section_ids = Column(JSONB, nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<OperationalMethodology(id={self.id}, title='{self.title}')>"

register_id_listener(OperationalMethodology, "opm")
