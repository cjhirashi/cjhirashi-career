"""Grupo del sidebar izquierdo del Admin (ADR-022; CRUD ADR-023 corrección).

Un grupo solo agrupa secciones L1 en el sidebar; nunca tiene vistas. Desde
ADR-023 (corrección) el CRUD completo (crear, editar, borrar, reordenar) vive en
la API — ver ``services/section_catalog.py``. ``origin`` distingue lo sembrado
por la migración (``'code'``) de lo creado por el operador (``'admin'``,
default); es puramente informativo, el seeder ya no poda grupos.
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
    # ADR-023 (corrección): mismo patrón que admin_sections_l1/l2/l3. `'code'`
    # para lo sembrado por la migración (11 grupos congelados + el grupo
    # protegido `admin`); `'admin'` (default) para lo creado por el operador vía
    # POST /admin/section-groups. Puramente informativo — el seeder YA NO poda
    # grupos/secciones (la BD manda desde esta corrección).
    origin = Column(String(16), nullable=False, default="admin", server_default="admin")
    # ADR-023 (corrección): gate genérico de visibilidad — ver
    # services/section_catalog.py::VISIBILITY_LEVELS. "standard" para todo salvo
    # el grupo protegido `admin` (system_name reservado, sembrado por migración).
    visibility_level = Column(
        String(20), nullable=False, default="standard", server_default="standard"
    )
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
