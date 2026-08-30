"""
Scheduler de tareas asignadas a agentes y orquestador de planes (ADR-015/016).

Carlos programa una fila en `bedrock_tasks` con assignee_type=agent y
scheduled_at, o marca execute_on_turn en una subtarea. Este loop, arrancado
en el lifespan de la API (un worker uvicorn), reclama las filas listas e
invoca el harness Bedrock con el user_id dueño. No hay JWT ni SPA.

Si la fila es una subtarea, respeta is_blocking de las hermanas anteriores.
El padre con hijas no se ejecuta: orquesta. Un turno de usuario genera
user_notifications.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.agent_system_tasks import TASK_TERMINAL_STATUSES, AgentSystemTask
from models.user_notification import UserNotification
from services.error_reporting import report_error

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
MAX_TASKS_PER_TICK = 3
RESULT_MAX_CHARS = 8000
ERROR_MAX_CHARS = 2000

_RUNNABLE_STATUSES = ("pending", "failed")
_background_tasks: set[asyncio.Task] = set()


def build_execution_prompt(task: AgentSystemTask) -> str:
    """Instrucción que el harness recibe como si fuera un turno de usuario."""
    description = (task.description or "").strip() or "(sin descripción)"
    due = task.due_at.isoformat() if task.due_at else "no definida"
    parent = f"\nPlan padre: {task.parent_id}" if task.parent_id else ""
    return (
        "Se te asignó una tarea programada. Ejecútala ahora de forma autónoma; "
        "el usuario no está en sesión y no puede confirmar nada.\n\n"
        f"Título: {task.title}\n"
        f"Descripción:\n{description}\n\n"
        f"Fecha límite: {due}\n"
        f"Prioridad: {task.priority}\n"
        f"Id de la tarea: {task.id}{parent}\n\n"
        "Usa tus herramientas para completar el trabajo. Al terminar, resume "
        "qué hiciste, qué ids creaste o actualizaste y qué quedó pendiente. "
        "No pidas confirmación."
    )


def group_children(tasks: Iterable[AgentSystemTask]) -> dict[str | None, list[AgentSystemTask]]:
    grouped: dict[str | None, list[AgentSystemTask]] = defaultdict(list)
    for task in tasks:
        grouped[task.parent_id].append(task)
    for siblings in grouped.values():
        siblings.sort(key=lambda item: (item.sort_order or 0, item.created_at or datetime.min.replace(tzinfo=timezone.utc), item.id or ""))
    return grouped


def is_blocked(task: AgentSystemTask, siblings: list[AgentSystemTask]) -> bool:
    """True if a previous blocking sibling is not done/cancelled."""
    if not task.parent_id:
        return False
    for sibling in siblings:
        if sibling.id == task.id:
            return False
        if sibling.is_blocking and sibling.status not in TASK_TERMINAL_STATUSES:
            return True
    return False


def has_children(task: AgentSystemTask, grouped: dict[str | None, list[AgentSystemTask]]) -> bool:
    return bool(grouped.get(task.id))


def is_agent_ready(task: AgentSystemTask, siblings: list[AgentSystemTask], now: datetime, *, orchestrator: bool) -> bool:
    if orchestrator:
        return False
    if task.assignee_type != "agent" or not task.agent_profile_id:
        return False
    if task.status not in _RUNNABLE_STATUSES:
        return False
    if is_blocked(task, siblings):
        return False
    if task.execute_on_turn:
        return True
    if task.scheduled_at is None:
        return False
    scheduled = task.scheduled_at
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    return scheduled <= now


def is_user_turn(task: AgentSystemTask, siblings: list[AgentSystemTask], *, orchestrator: bool) -> bool:
    if orchestrator:
        return False
    if task.assignee_type != "user" or task.status != "pending":
        return False
    return not is_blocked(task, siblings)


def rollup_parent_status(parent: AgentSystemTask, children: list[AgentSystemTask]) -> None:
    if not children or parent.status == "cancelled":
        return
    active = [child for child in children if child.status not in TASK_TERMINAL_STATUSES]
    if not active:
        parent.status = "cancelled" if all(child.status == "cancelled" for child in children) else "done"
        return
    if parent.status == "pending":
        parent.status = "in_progress"


def _is_runnable_agent_task(task: AgentSystemTask) -> bool:
    return (
        task.assignee_type == "agent"
        and bool(task.agent_profile_id)
        and task.status in _RUNNABLE_STATUSES
    )


async def claim_task_for_user(
    db: AsyncSession, user_id: str, task_id: str
) -> Optional[AgentSystemTask]:
    """Marca una tarea del usuario como in_progress si es ejecutable por un agente."""
    result = await db.execute(
        select(AgentSystemTask).where(AgentSystemTask.id == task_id, AgentSystemTask.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None or not _is_runnable_agent_task(task):
        return None
    child = await db.execute(select(AgentSystemTask.id).where(AgentSystemTask.parent_id == task_id).limit(1))
    if child.scalar_one_or_none() is not None:
        return None
    if task.parent_id:
        siblings_result = await db.execute(
            select(AgentSystemTask).where(
                AgentSystemTask.user_id == user_id,
                AgentSystemTask.parent_id == task.parent_id,
            )
        )
        siblings = group_children(siblings_result.scalars().all())[task.parent_id]
        if is_blocked(task, siblings):
            return None
    task.status = "in_progress"
    task.error_message = None
    await db.flush()
    return task


def _pick_ready_agent_ids(tasks: list[AgentSystemTask], now: datetime) -> list[str]:
    grouped = group_children(tasks)
    ids: list[str] = []
    for task in tasks:
        siblings = grouped.get(task.parent_id, [task] if not task.parent_id else [])
        if not task.parent_id:
            siblings = grouped.get(None, [])
        if is_agent_ready(task, siblings, now, orchestrator=has_children(task, grouped)):
            ids.append(task.id)
        if len(ids) >= MAX_TASKS_PER_TICK:
            break
    return ids


async def _load_tasks(db: AsyncSession) -> list[AgentSystemTask]:
    result = await db.execute(select(AgentSystemTask))
    return list(result.scalars().all())


async def claim_due_task_ids(now: Optional[datetime] = None) -> list[str]:
    """Reclama agentes listos: hora vencida, o turno desbloqueado."""
    moment = now or datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        tasks = await _load_tasks(db)
        ids: list[str] = []
        grouped = group_children(tasks)
        for task in tasks:
            siblings = grouped.get(task.parent_id, [])
            if task.parent_id is None:
                siblings = grouped.get(None, [])
            if not is_agent_ready(task, siblings, moment, orchestrator=has_children(task, grouped)):
                continue
            task.status = "in_progress"
            task.error_message = None
            ids.append(task.id)
            if len(ids) >= MAX_TASKS_PER_TICK:
                break
        await db.commit()
        return ids


async def _notify_user_turns(db: AsyncSession, tasks: list[AgentSystemTask]) -> None:
    grouped = group_children(tasks)
    now = datetime.now(timezone.utc)
    for task in tasks:
        siblings = grouped.get(task.parent_id, [])
        if task.parent_id is None:
            siblings = grouped.get(None, [])
        if not is_user_turn(task, siblings, orchestrator=has_children(task, grouped)):
            continue
        if task.turn_notified_at is not None:
            continue
        db.add(
            UserNotification(
                user_id=task.user_id,
                kind="task_turn",
                title=f"Tarea pendiente: {task.title}",
                body=(
                    "Te toca ejecutar esta tarea. Márcala como hecha en Vista cuando termines."
                    if not task.parent_id
                    else "Te toca esta subtarea del plan. El resto espera si es bloqueante."
                ),
                resource_key="agent-tasks",
                resource_id=task.id,
            )
        )
        task.turn_notified_at = now


async def _rollup_parents(tasks: list[AgentSystemTask]) -> None:
    grouped = group_children(tasks)
    by_id = {task.id: task for task in tasks}
    for parent_id, children in grouped.items():
        if not parent_id:
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            continue
        rollup_parent_status(parent, children)


async def advance_from_task(task_id: str) -> None:
    """Tras un cambio: notifica turnos de usuario, resume padres y reclama agentes listos."""
    async with AsyncSessionLocal() as db:
        tasks = await _load_tasks(db)
        if not any(item.id == task_id for item in tasks):
            await db.commit()
            return
        await _notify_user_turns(db, tasks)
        await _rollup_parents(tasks)
        await db.commit()
    ids = await claim_due_task_ids()
    for claimed_id in ids:
        if claimed_id == task_id:
            continue
        await execute_claimed_task(claimed_id)


def enqueue_advance(task_id: Optional[str], parent_id: Optional[str] = None) -> None:
    target = parent_id or task_id
    if not target:
        return
    task = asyncio.create_task(advance_from_task(target))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def execute_claimed_task(task_id: str) -> None:
    """Corre el harness sobre una tarea ya reclamada (status=in_progress)."""
    from services.bedrock.agent_loop import run_single_turn_sync
    from services.bedrock.agent_profiles import get_profile
    from services.bedrock.errors import BedrockError

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AgentSystemTask).where(AgentSystemTask.id == task_id))
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
            enqueue_advance(task.id, task.parent_id)
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
            enqueue_advance(task.id, task.parent_id)
        except (BedrockError, Exception) as exc:
            logger.exception("Scheduled task %s failed: %s", task_id, exc)
            report_error(
                str(exc),
                f"scheduler:task_scheduler:{task_id}",
                error_type=type(exc).__name__,
                exc=exc,
                context={"task_id": task_id, "agent_profile_id": task.agent_profile_id},
                severity="error",
            )
            try:
                await db.rollback()
            except Exception:
                logger.exception("Rollback after task %s failure also failed", task_id)
            async with AsyncSessionLocal() as db2:
                failed = await db2.get(AgentSystemTask, task_id)
                if failed is not None and failed.status == "in_progress":
                    failed.status = "failed"
                    failed.error_message = str(exc)[:ERROR_MAX_CHARS]
                    failed.executed_at = datetime.now(timezone.utc)
                    await db2.commit()
                    enqueue_advance(failed.id, failed.parent_id)


async def run_due_tasks() -> None:
    async with AsyncSessionLocal() as db:
        tasks = await _load_tasks(db)
        await _notify_user_turns(db, tasks)
        await _rollup_parents(tasks)
        await db.commit()
    ids = await claim_due_task_ids()
    for task_id in ids:
        await execute_claimed_task(task_id)


async def scheduler_loop() -> None:
    """Loop infinito — arrancar como task asyncio desde app.py y cancelar al apagar."""
    while True:
        try:
            await run_due_tasks()
        except Exception as exc:
            logger.exception("Task scheduler tick failed")
            report_error(
                str(exc) or "Task scheduler tick failed",
                "scheduler:task_scheduler:tick",
                error_type=type(exc).__name__,
                exc=exc,
                severity="critical",
            )
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
