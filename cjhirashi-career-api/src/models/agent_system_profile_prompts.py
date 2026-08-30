"""
AgentSystemProfilePrompt — suffix de system prompt por perfil de agente.

Tabla de configuración editable desde Admin Panel. Una fila por perfil
(orchestrator, identity, search, …). No usa id/user_id estándar.
"""
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from database import Base


class AgentSystemProfilePrompt(Base):
    """Override del suffix del system prompt para un perfil concreto."""

    __tablename__ = "agent_system_agent_profile_prompts"

    # --- Clave primaria (profile_id coincide con agent_profiles.py) ---
    profile_id = Column(String(50), primary_key=True)

    # --- Contenido editable ---
    system_prompt_suffix = Column(Text, nullable=False)

    # --- Auditoría temporal ---
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AgentSystemProfilePrompt(profile_id={self.profile_id!r})>"
