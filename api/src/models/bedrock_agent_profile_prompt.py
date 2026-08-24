"""Per-agent system prompt suffix overrides (editable from Admin Panel)."""
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from database import Base


class BedrockAgentProfilePrompt(Base):
    __tablename__ = "bedrock_agent_profile_prompts"

    profile_id = Column(String(50), primary_key=True)
    system_prompt_suffix = Column(Text, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BedrockAgentProfilePrompt(profile_id={self.profile_id!r})>"
