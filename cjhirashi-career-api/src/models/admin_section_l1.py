"""Sección L1 del Admin (ADR-022).

Nodo de primer nivel bajo un grupo. Puede tener 0–10 vistas y sub-secciones L2.
``system_name`` / ``label`` / ``path`` / ``section_type`` son propiedad del código
(seeder). ``group_id`` (re-parent) y ``sort_order`` son propiedad del operador.

``origin`` (ruling #5 de ADR-022): ``'code'`` para todo lo que siembra el registro
en código; el prune del seeder solo borra filas ``origin='code'``. Reservado para
el futuro catálogo de componentes UI, donde el operador podrá crear secciones
(``origin='admin'``) que el seeder no debe tocar.
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
