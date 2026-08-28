"""Sección L2 del Admin (ADR-022).

Sub-sección de una L1. Misma forma que L1 salvo que cuelga de ``parent_l1_id``
(ON DELETE CASCADE) en vez de un grupo. En este lote el registro en código no
declara estructura L2, así que la tabla queda vacía tras el seed; el operador la
poblará cuando llegue el drag entre niveles (ADR-022 §Seguimiento).
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


class AdminSectionL2(Base):
    __tablename__ = "admin_sections_l2"
    __table_args__ = (
        CheckConstraint(
            "section_type IN ('table', 'functional', 'metrics', 'bucket')",
            name="ck_admin_sections_l2_section_type",
        ),
        Index(
            "uq_admin_sections_l2_path",
            "path",
            unique=True,
            postgresql_where=text("path IS NOT NULL"),
            sqlite_where=text("path IS NOT NULL"),
        ),
        Index("ix_admin_sections_l2_parent_sort", "parent_l1_id", "sort_order"),
    )

    id = Column(String(20), primary_key=True)
    parent_l1_id = Column(
        String(20),
        ForeignKey("admin_sections_l1.id", ondelete="CASCADE"),
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
        return f"<AdminSectionL2(id={self.id!r}, system_name={self.system_name!r})>"


register_id_listener(AdminSectionL2, "s2")
