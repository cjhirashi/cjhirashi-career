"""
Scheduler de tareas asignadas a agentes (ADR-015).

Carlos programa una fila en `bedrock_tasks` con assignee_type=agent y
scheduled_at. Este loop, arrancado en el lifespan de la API (un worker
uvicorn, igual que linkedin_scheduler), reclama las filas vencidas e
invoca el harness Bedrock con el user_id dueño. No hay JWT ni SPA: el
agente trabaja con el Admin cerrado.

L1/L2: historial en sesión `scheduled-task-{id}`.
L3: record_history=False (no tienen chat de usuario).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.bedrock_task import BedrockTask

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
MAX_TASKS_PER_TICK = 3
RESULT_MAX_CHARS = 8000
ERROR_MAX_CHARS = 2000

_RUNNABLE_STATUSES = ("pending", "failed")


def build_execution_prompt(task: BedrockTask) -> str:
    """Instrucción que el harness recibe como si fuera un turno de usuario."""
    description = (task.description or "").strip() or "(sin descripción)"
    due = task.due_at.isoformat() if task.due_at else "no definida"
    return (
        "Se te asignó una tarea programada. Ejecútala ahora de forma autónoma; "
        "el usuario no está en sesión y no puede confirmar nada.\n\n"
        f"Título: {task.title}\n"
        f"Descripción:\n{description}\n\n"
        f"Fecha límite: {due}\n"
        f"Prioridad: {task.priority}\n"
        f"Id de la tarea: {task.id}\n\n"
        "Usa tus herramientas para completar el trabajo. Al terminar, resume "
        "qué hiciste, qué ids creaste o actualizaste y qué quedó pendiente. "
        "No pidas confirmación."
    )


def _is_runnable_agent_task(task: BedrockTask) -> bool:
    return (
        task.assignee_type == "agent"
        and bool(task.agent_profile_id)
        and task.status in _RUNNABLE_STATUSES
    )


async def claim_task_for_user(
    db: AsyncSession, user_id: str, task_id: str
) -> Optional[BedrockTask]:
    """Marca una tarea del usuario como in_progress si es ejecutable por un agente."""
    result = await db.execute(
        select(BedrockTask).where(BedrockTask.id == task_id, BedrockTask.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None or not _is_runnable_agent_task(task):
        return None
    task.status = "in_progress"
    task.error_message = None
    await db.flush()
    return task


async def claim_due_task_ids(now: Optional[datetime] = None) -> list[str]:
    """Reclama hasta MAX_TASKS_PER_TICK tareas de agente cuyo scheduled_at ya pasó."""
    moment = now or datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BedrockTask)
            .where(
                BedrockTask.assignee_type == "agent",
                BedrockTask.status == "pending",
                BedrockTask.agent_profile_id.is_not(None),
                BedrockTask.scheduled_at.is_not(None),
                BedrockTask.scheduled_at <= moment,
            )
            .order_by(BedrockTask.scheduled_at.asc())
            .limit(MAX_TASKS_PER_TICK)
        )
        tasks = list(result.scalars().all())
        ids: list[str] = []
        for task in tasks:
            task.status = "in_progress"
            task.error_message = None
            ids.append(task.id)
        await db.commit()
        return ids


async def execute_claimed_task(task_id: str) -> None:
    """Corre el harness sobre una tarea ya reclamada (status=in_progress)."""
    from services.bedrock.agent_loop import run_single_turn_sync
    from services.bedrock.agent_profiles import get_profile
    from services.bedrock.errors import BedrockError

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(BedrockTask).where(BedrockTask.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            logger.warning("Scheduled task %s disappeared before execution", task_id)
            return
        if task.status != "in_progress" or not task.agent_profile_id:
            logger.info("Scheduled task %s skipped: status=%s", task_id, task.status)
            return

        try:
            profile = get_profile(task.agent_profile_id)
        except KeyError:
            task.status = "failed"
            task.error_message = f"Agente desconocido: {task.agent_profile_id}"
            await db.commit()
            return

        record_history = profile.level < 3
        try:
            event = await run_single_turn_sync(
                db,
                user_id=task.user_id,
                session_id=f"scheduled-task-{task.id}",
                message=build_execution_prompt(task),
                chat_surface="contextual",
                agent_profile_id=profile.id,
                page_context={
                    "route": "/tasks",
                    "page_title": "Tareas programadas",
                    "resource_key": "agent-tasks",
                },
                record_history=record_history,
                load_session_history=record_history,
                delegation_depth=1 if profile.level == 3 else 0,
            )
            reply = (event or {}).get("reply") or ""
            await db.refresh(task)
            task.executed_at = datetime.now(timezone.utc)
            task.execution_result = reply[:RESULT_MAX_CHARS]
            task.error_message = None
            if task.status == "in_progress":
                task.status = "done"
            await db.commit()
            logger.info("Scheduled task %s finished with status=%s", task.id, task.status)
        except (BedrockError, Exception) as exc:
            logger.exception("Scheduled task %s failed: %s", task_id, exc)
            try:
                await db.rollback()
            except Exception:
                logger.exception("Rollback after task %s failure also failed", task_id)
            async with AsyncSessionLocal() as db2:
                failed = await db2.get(BedrockTask, task_id)
                if failed is not None and failed.status == "in_progress":
                    failed.status = "failed"
                    failed.error_message = str(exc)[:ERROR_MAX_CHARS]
                    failed.executed_at = datetime.now(timezone.utc)
                    await db2.commit()


async def run_due_tasks() -> None:
    ids = await claim_due_task_ids()
    for task_id in ids:
        await execute_claimed_task(task_id)


async def scheduler_loop() -> None:
    """Loop infinito — arrancar como task asyncio desde app.py y cancelar al apagar."""
    while True:
        try:
            await run_due_tasks()
        except Exception:
            logger.exception("Task scheduler tick failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
