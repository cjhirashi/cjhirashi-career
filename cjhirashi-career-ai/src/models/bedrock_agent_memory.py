"""
BedrockAgentMemory — memoria del agente en Postgres con full-text (RF-022, D-15).

Sustituye a la memoria que vivía solo en Qdrant. `search_vector` es una columna
generada (`to_tsvector(<MEMORY_FTS_CONFIG>, text)`) con índice GIN; el idioma se fija
al crear la tabla (migración 0001) y por defecto es `spanish` (D-24).
"""
from sqlalchemy import Column, Computed, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import func

from config import settings
from database import Base
from services.id_generator import register_id_listener


class BedrockAgentMemory(Base):
    __tablename__ = "bedrock_agent_memory"
    __table_args__ = (
        # Idempotencia de la migración desde Qdrant: un punto por usuario.
        UniqueConstraint("user_id", "source_ref", name="uq_bedrock_agent_memory_user_source_ref"),
        Index("ix_bedrock_agent_memory_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_bedrock_agent_memory_user_profile", "user_id", "agent_profile_id"),
    )

    id = Column(String(20), primary_key=True)  # bam-N
    user_id = Column(String(20), nullable=False, index=True)
    kind = Column(String(20), nullable=False)  # note | fact | manual
    agent_profile_id = Column(String(50), nullable=True)  # NULL = global del usuario
    text = Column(Text, nullable=False)
    search_vector = Column(
        TSVECTOR,
        Computed(f"to_tsvector('{settings.MEMORY_FTS_CONFIG}'::regconfig, text)", persisted=True),
        nullable=True,
    )
    source = Column(String(20), nullable=False)  # harness | qdrant_import
    source_ref = Column(String(100), nullable=True)  # id del punto Qdrant
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<BedrockAgentMemory(id={self.id}, kind={self.kind!r})>"


register_id_listener(BedrockAgentMemory, "bam")
