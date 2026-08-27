"""
BedrockUsageLog Model - token usage/cost per Agent Bedrock chat turn.

Written best-effort by `services/bedrock_service.py` after every turn (one
row per turn, summed across however many tool-use round-trips it took) -
never blocks the chat response if logging itself fails. Feeds the "Costo
del asistente IA" panel on the admin metrics dashboard.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class BedrockUsageLog(Base):
    __tablename__ = "bedrock_usage_logs"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    session_id = Column(String(64), nullable=False, index=True)
    model_id = Column(String(150), nullable=False, index=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    # Prompt caching de Bedrock: lecturas de prefijo cacheado (0.10x) y
    # escrituras al crear/extender el prefijo (1.25x).
    cache_read_tokens = Column(Integer, nullable=False, default=0)
    cache_write_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Numeric(12, 6), nullable=False, default=0)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<BedrockUsageLog(id={self.id}, model_id='{self.model_id}', cost={self.estimated_cost_usd})>"
