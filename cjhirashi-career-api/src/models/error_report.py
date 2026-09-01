"""Registro centralizado de fallas del sistema (ADR-018).

Cada fila es una falla detectada en cualquier parte del sistema (handler global
de la API, bloque ``except`` del código, scheduler in-process, loop de Bedrock,
MCP server o los SPA de Admin/Portfolio). El atributo ``resolved`` arranca en
``False`` — pendiente de revisión — y pasa a ``True`` cuando la falla se corrige.

Errores repetidos con la misma huella (``fingerprint``) no crean filas nuevas
mientras siguen pendientes: se incrementa ``occurrences`` y se actualiza
``last_seen_at``. El camino de escritura vive en
``services/error_reporting.py``; el de lectura/gestión en
``services/error_report_service.py``.
"""
from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener

SEVERITIES = ("warning", "error", "critical")


class ErrorReport(Base):
    __tablename__ = "error_reports"
    __table_args__ = (
        Index("ix_error_reports_open", "resolved", "severity", "last_seen_at"),
        Index("ix_error_reports_fp_open", "fingerprint", "resolved"),
    )

    id = Column(String(20), primary_key=True)

    # --- Qué y dónde ---
    message = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, index=True)
    error_type = Column(String(120), nullable=True)
    stack_trace = Column(Text, nullable=True)
    context = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    severity = Column(String(20), nullable=False, default="error")

    # --- Estado de revisión (el atributo pedido) ---
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(50), nullable=True)

    # --- Agrupación de repeticiones ---
    fingerprint = Column(String(64), nullable=False, index=True)
    occurrences = Column(Integer, nullable=False, default=1)

    # --- Auditoría temporal ---
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        estado = "resuelto" if self.resolved else "pendiente"
        return f"<ErrorReport(id={self.id}, source={self.source!r}, {estado})>"


register_id_listener(ErrorReport, "err")
