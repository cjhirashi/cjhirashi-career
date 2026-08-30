"""
Tablero de tareas (usuario o agente) — CRUD genérico + ejecución autónoma.

El resource_key `agent-tasks` se registra al importar este módulo para que
las tools genéricas del harness operen el tablero. `POST /{id}/run` dispara
el mismo runner que el scheduler (ADR-015): el agente trabaja sin sesión SPA.
"""
import asyncio
import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.agent_system_tasks import AgentSystemTask
from models.user import User
from routes.career_common import build_crud_router
from schemas.bedrock_task import AgentSystemTaskCreate, AgentSystemTaskResponse, AgentSystemTaskUpdate
from services import task_scheduler

logger = logging.getLogger(__name__)

router = build_crud_router(
    prefix="/agent-tasks",
    tags=["Agent - Tasks"],
    model=AgentSystemTask,
    create_schema=AgentSystemTaskCreate,
    update_schema=AgentSystemTaskUpdate,
    response_schema=AgentSystemTaskResponse,
    entity_name="tarea",
    after_write=lambda obj: task_scheduler.enqueue_advance(getattr(obj, "id", None), getattr(obj, "parent_id", None)),
)


@router.post(
    "/{item_id}/run",
    response_model=AgentSystemTaskResponse,
    summary="Ejecutar ahora una tarea asignada a un agente",
)
async def run_task_now(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reclama la tarea y lanza el harness en background. No espera a Bedrock."""
    task = await task_scheduler.claim_task_for_user(db, current_user.id, item_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La tarea no se puede ejecutar ahora: debe estar asignada a un "
                "agente, en estado pendiente o fallida, y con un perfil válido."
            ),
        )
    await db.commit()
    asyncio.create_task(task_scheduler.execute_claimed_task(task.id))
    logger.info("Task %s claimed for immediate agent execution", task.id)
    return task
