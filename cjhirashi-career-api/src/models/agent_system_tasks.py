"""
AgentSystemTask — tablero de trabajo, cola de agentes y orquestador de planes (ADR-015/016).

Una fila puede ser:

- *Usuario*: recordatorio o trabajo manual. El scheduler no la ejecuta;
  si le toca el turno, se crea una notificación.
- *Agente*: el `task_scheduler` invoca Bedrock a `scheduled_at` o al
  pasar el turno (`execute_on_turn`), aunque el Admin esté cerrado.
- *Padre con subtareas*: orquestador. No se ejecuta como agente; avanza
  hijas en `sort_order` respetando `is_blocking` (ADR-016).
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func
from database import Base

TASK_STATUSES = ("pending", "in_progress", "done", "cancelled", "failed")
TASK_ASSIGNEE_TYPES = ("user", "agent")
TASK_PRIORITIES = ("low", "medium", "high")
TASK_TERMINAL_STATUSES = ("done", "cancelled")


from services.id_generator import register_id_listener


class AgentSystemTask(Base):
    __tablename__ = "agent_system_tasks"
    __table_args__ = (
        Index("ix_bedrock_tasks_scheduler", "assignee_type", "status", "scheduled_at"),
        Index("ix_bedrock_tasks_parent_sort", "parent_id", "sort_order"),
    )

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    notes = Column(Text, nullable=True)

    assignee_type = Column(String(20), nullable=False, default="user", index=True)
    agent_profile_id = Column(String(50), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), nullable=False, default="medium")

    parent_id = Column(
        String(20),
        ForeignKey("agent_system_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sort_order = Column(Integer, nullable=False, default=0)
    is_blocking = Column(Boolean, nullable=False, default=True)
    execute_on_turn = Column(Boolean, nullable=False, default=False)
    turn_notified_at = Column(DateTime(timezone=True), nullable=True)

    execution_result = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AgentSystemTask(id={self.id}, title='{self.title}', status='{self.status}')>"


register_id_listener(AgentSystemTask, "btk")
