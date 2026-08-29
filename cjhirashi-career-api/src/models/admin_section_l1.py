"""Sección L1 del Admin (ADR-022; CRUD ADR-023 corrección).

Nodo de primer nivel bajo un grupo. Puede tener 0–10 vistas y sub-secciones L2.

Desde ADR-023 (corrección) el CRUD completo (crear, editar, borrar, mover de
nivel) vive en la API — ver ``services/section_catalog.py``. ``origin='code'``
identifica lo sembrado por el seeder/migración (prune acotado a esas filas);
``origin='admin'`` identifica lo creado por el operador vía API (nunca tocado
por el seeder). ``visibility_level`` (ADR-023) es el gate genérico de acceso —
ver ``VISIBILITY_LEVELS`` en ``section_catalog.py``.
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener

SECTION_TYPES = ("table", "functional", "metrics", "bucket")


class AdminSectionL1(Base):
    __tablename__ = "admin_sections_l1"
    __table_args__ = (
        CheckConstraint(
            "section_type IN ('table', 'functional', 'metrics', 'bucket')",
            name="ck_admin_sections_l1_section_type",
        ),
        Index(
            "uq_admin_sections_l1_path",
            "path",
            unique=True,
            postgresql_where=text("path IS NOT NULL"),
            sqlite_where=text("path IS NOT NULL"),
        ),
        Index("ix_admin_sections_l1_group_sort", "group_id", "sort_order"),
    )

    id = Column(String(20), primary_key=True)
    group_id = Column(
        String(20),
        ForeignKey("admin_section_groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    system_name = Column(String(80), nullable=False, unique=True)
    label = Column(String(120), nullable=False)
    path = Column(String(120), nullable=True)
    section_type = Column(String(20), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    origin = Column(String(16), nullable=False, default="code", server_default="code")
    # ADR-023 (corrección): gate genérico de visibilidad — ver
    # services/section_catalog.py::VISIBILITY_LEVELS.
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
        return f"<AdminSectionL1(id={self.id!r}, system_name={self.system_name!r})>"


register_id_listener(AdminSectionL1, "s1")
