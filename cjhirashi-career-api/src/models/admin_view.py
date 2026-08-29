"""Vista de una sección del Admin (ADR-022).

Una vista es una pestaña dentro de una sección (lista, kanban, ficha, principal…).
Vive bajo exactamente una sección: ``owner_l1_id`` **o** ``owner_l2_id`` **o**
``owner_l3_id`` (CHECK ``ck_admin_views_single_owner``).

Columnas de código (seeder, upsert): ``key``, ``label``, ``sort_order``,
``has_controls_window``, ``tool_names``, ``data_source``, ``resource_key``.

Columnas del operador (Admin / tool Bedrock ``admin_view_settings``; el seeder
**nunca** las toca):
- ``responsible_agent_profile_id``: system name de un perfil **L2** (referencia
  blanda ``String(50)``, NO FK — el catálogo de agentes vive solo en código).
  ``NULL`` ⇒ chat contextual apagado en la vista.
- ``instructions``: texto del panel del sidebar derecho. ``NULL``/"" ⇒ panel
  apagado.

``tool_names`` usa ``JSON`` con variante ``JSONB`` en PostgreSQL para que las
suites SQLite lo compilen; se lee entero y se compara en Python.
"""
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener

DATA_SOURCES = ("crud", "computed", "singleton", "external")

_SINGLE_OWNER = (
    "(CASE WHEN owner_l1_id IS NOT NULL THEN 1 ELSE 0 END"
    " + CASE WHEN owner_l2_id IS NOT NULL THEN 1 ELSE 0 END"
    " + CASE WHEN owner_l3_id IS NOT NULL THEN 1 ELSE 0 END) = 1"
)


class AdminView(Base):
    __tablename__ = "admin_views"
    __table_args__ = (
        CheckConstraint(_SINGLE_OWNER, name="ck_admin_views_single_owner"),
        CheckConstraint(
            "data_source IN ('crud', 'computed', 'singleton', 'external')",
            name="ck_admin_views_data_source",
        ),
        CheckConstraint(
            "resource_key IS NULL OR data_source IN ('crud', 'singleton')",
            name="ck_admin_views_resource_key_scope",
        ),
        Index(
            "uq_admin_views_l1_key",
            "owner_l1_id",
            "key",
            unique=True,
            postgresql_where=text("owner_l1_id IS NOT NULL"),
            sqlite_where=text("owner_l1_id IS NOT NULL"),
        ),
        Index(
            "uq_admin_views_l2_key",
            "owner_l2_id",
            "key",
            unique=True,
            postgresql_where=text("owner_l2_id IS NOT NULL"),
            sqlite_where=text("owner_l2_id IS NOT NULL"),
        ),
        Index(
            "uq_admin_views_l3_key",
            "owner_l3_id",
            "key",
            unique=True,
            postgresql_where=text("owner_l3_id IS NOT NULL"),
            sqlite_where=text("owner_l3_id IS NOT NULL"),
        ),
        Index("ix_admin_views_l1_sort", "owner_l1_id", "sort_order"),
        Index("ix_admin_views_l2_sort", "owner_l2_id", "sort_order"),
        Index("ix_admin_views_l3_sort", "owner_l3_id", "sort_order"),
        Index("ix_admin_views_responsible", "responsible_agent_profile_id"),
    )

    id = Column(String(20), primary_key=True)
    owner_l1_id = Column(
        String(20), ForeignKey("admin_sections_l1.id", ondelete="CASCADE"), nullable=True
    )
    owner_l2_id = Column(
        String(20), ForeignKey("admin_sections_l2.id", ondelete="CASCADE"), nullable=True
    )
    owner_l3_id = Column(
        String(20), ForeignKey("admin_sections_l3.id", ondelete="CASCADE"), nullable=True
    )
    key = Column(String(40), nullable=False)
    label = Column(String(120), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    has_controls_window = Column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    tool_names = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    data_source = Column(
        String(20), nullable=False, default="crud", server_default="crud"
    )
    resource_key = Column(String(80), nullable=True)
    responsible_agent_profile_id = Column(String(50), nullable=True)
    instructions = Column(Text, nullable=True)
    origin = Column(String(16), nullable=False, default="code", server_default="code")
    # ADR-023 (corrección): columna nueva en las 4 tablas por consistencia del
    # mecanismo genérico; el gate de superusuario NO aplica hoy a vistas (§2 del
    # contrato — ninguna vista cuelga del grupo `admin` en este lote).
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

    @property
    def owner_id(self) -> str:
        return self.owner_l1_id or self.owner_l2_id or self.owner_l3_id

    @property
    def owner_level(self) -> int:
        if self.owner_l1_id:
            return 1
        if self.owner_l2_id:
            return 2
        return 3

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AdminView(id={self.id!r}, key={self.key!r}, owner={self.owner_id!r})>"


register_id_listener(AdminView, "vw")
