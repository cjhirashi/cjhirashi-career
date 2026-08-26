"""
Foto de un agente del catálogo, elegida desde el bucket MinIO.

Independiente del override de prompt: quitar el suffix no borra la foto.
"""
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from database import Base


class BedrockAgentProfilePhoto(Base):
    __tablename__ = "bedrock_agent_profile_photos"

    profile_id = Column(String(50), primary_key=True)
    photo_url = Column(String(1024), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BedrockAgentProfilePhoto(profile_id={self.profile_id!r})>"
