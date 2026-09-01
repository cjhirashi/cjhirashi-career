"""Destinos de delegación editables por perfil (subset de los permitidos por nivel)."""
from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from database import Base


class AgentSystemDelegation(Base):
    __tablename__ = "agent_system_agent_delegation"

    profile_id = Column(String(50), primary_key=True)
    # Lista de agent_* ; fila presente = override (lista vacía = no delega a nadie).
    target_ids = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AgentSystemDelegation(profile_id={self.profile_id!r})>"
