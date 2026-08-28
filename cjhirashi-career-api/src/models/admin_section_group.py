"""Grupo del sidebar izquierdo del Admin (ADR-022).

Un grupo solo agrupa secciones L1 en el sidebar; nunca tiene vistas. La
estructura (``system_name``, ``name``) es propiedad del código y la siembra el
seeder ``services/admin_sections_seed.py``. El ``sort_order`` es propiedad del
operador (se inserta con el valor de código y luego el Admin lo reordena).
"""
from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener


class AdminSectionGroup(Base):
    __tablename__ = "admin_section_groups"
    __table_args__ = (
        Index("ix_admin_section_groups_sort", "sort_order"),
    )

    id = Column(String(20), primary_key=True)
    system_name = Column(String(60), nullable=False, unique=True)
    name = Column(String(120), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AdminSectionGroup(id={self.id!r}, system_name={self.system_name!r})>"


register_id_listener(AdminSectionGroup, "grp")
