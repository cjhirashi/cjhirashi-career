"""
BedrockUsageRoundLog — costo granular por llamada Converse, tool o imagen.

Un turno puede generar varias filas (orquestador + delegaciones).
Ver docs/BEDROCK-SYSTEM.md.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base


class BedrockUsageRoundLog(Base):
    __tablename__ = "bedrock_usage_round_logs"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    session_id = Column(String(100), nullable=False, index=True)
    model_id = Column(String(150), nullable=True, index=True)
    round_type = Column(String(30), nullable=False, default="converse", index=True)
    tool_name = Column(String(100), nullable=True)
    agent_profile_id = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    # Prompt caching de Bedrock: tokens leídos de un prefijo ya cacheado (0.10x)
    # y tokens escritos al crear/extender el prefijo cacheado (1.25x).
    cache_read_tokens = Column(Integer, nullable=False, default=0)
    cache_write_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Numeric(12, 6), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
