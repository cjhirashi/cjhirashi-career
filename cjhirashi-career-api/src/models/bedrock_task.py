"""
BedrockTask — tablero de trabajo de Carlos y cola de ejecución de agentes.

Una fila puede ser:

- *Usuario*: recordatorio o trabajo manual (calendario / Gantt / kanban).
  El scheduler no la ejecuta.
- *Agente*: el `task_scheduler` invoca el harness Bedrock a `scheduled_at`
  con el `user_id` dueño, aunque el Admin esté cerrado (ADR-015).

Sigue el CRUD genérico (`/agent-tasks`, resource_key `agent-tasks`) para que
las tools del agente y el L3 `agent_task_manager` operen el mismo tablero.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from database import Base

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled", "failed")
TASK_ASSIGNEE_TYPES = ("user", "agent")
TASK_PRIORITIES = ("low", "medium", "high")


from services.id_generator import register_id_listener


class BedrockTask(Base):
    __tablename__ = "bedrock_tasks"
    __table_args__ = (
        Index("ix_bedrock_tasks_scheduler", "assignee_type", "status", "scheduled_at"),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    notes = Column(Text, nullable=True)

    assignee_type = Column(String(20), nullable=False, default="user", index=True)
    agent_profile_id = Column(String(50), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), nullable=False, default="medium")

    execution_result = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BedrockTask(id={self.id}, title='{self.title}', status='{self.status}')>"

register_id_listener(BedrockTask, "btk")
