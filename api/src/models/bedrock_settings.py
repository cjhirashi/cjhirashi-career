"""
BedrockSettings Model - single-row table holding the agent's runtime-editable
configuration (currently just the system prompt override). Single row
because Agent Bedrock is a single-operator assistant (Carlos), not a
multi-tenant product - see CLAUDE.md.

`system_prompt = NULL` means "use the built-in default" (see
`services/bedrock_service.py::_default_system_prompt`) - resetting to
default is just clearing this column, not a separate code path.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.sql import func
from database import Base


class BedrockSettings(Base):
    __tablename__ = "bedrock_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    system_prompt = Column(Text, nullable=True)
    # Harness local — modelo activo y límites (ADR-008)
    active_model_id = Column(String(150), nullable=True)
    orchestrator_model_id = Column(String(150), nullable=True)
    max_round_trips = Column(Integer, nullable=False, default=6)
    history_window = Column(Integer, nullable=False, default=20)
    daily_budget_usd = Column(Numeric(10, 4), nullable=False, default=5.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BedrockSettings(id={self.id})>"
