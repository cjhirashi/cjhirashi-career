"""
BedrockTask Model - the agent's own task/plan tracker. Lets Agent Bedrock
break a multi-step request ("update my whole Identity section") into
tracked tasks instead of just doing everything in one uninspectable turn -
Carlos can see the plan, and the agent can check work off across turns or
even across conversations.

Goes through the exact same generic CRUD tools (create_career_record etc.)
as every career-domain resource - see routes/bedrock_tasks.py, which
registers it in RESOURCE_REGISTRY the same way career_support.py does for
tags. Not a career-domain table itself (lives at /agent-tasks, not
/career/*), just built on the same reusable CareerRepository/CRUD-router
machinery since the shape (one user-owned resource with a few text columns)
is identical.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")


from services.id_generator import register_id_listener


class BedrockTask(Base):
    __tablename__ = "bedrock_tasks"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)  # the plan's detail, Markdown
    status = Column(String(20), nullable=False, default="pending", index=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BedrockTask(id={self.id}, title='{self.title}', status='{self.status}')>"

register_id_listener(BedrockTask, "btk")
