"""
Task scheduler worker — consumes from Redis Streams and executes scheduled agent tasks.

FASE 1: Replaces task_scheduler.py's asyncio loop with a standalone worker process
that consumes from Redis Streams via consumer groups.

Idempotence: Verifies task status in Postgres before executing; Bedrock execution
is also idempotent (same session_id → same result if re-run).

Stream: `bedrock:scheduled-tasks`
Consumer Group: `bedrock-workers`
Message format: {task_id, scheduled_at (ISO 8601 timestamp)}
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.agent_system_tasks import TASK_TERMINAL_STATUSES, AgentSystemTask
from models.user_notification import UserNotification
from services.error_reporting import report_error
from services.redis_client import get_redis

logger = logging.getLogger(__name__)

STREAM_KEY = "bedrock:scheduled-tasks"
CONSUMER_GROUP = "bedrock-workers"
CONSUMER_NAME = "worker-1"
POLL_TIMEOUT_MS = 1000
RESULT_MAX_CHARS = 8000
ERROR_MAX_CHARS = 2000


async def ensure_consumer_group(redis_client):
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info(f"Created consumer group {CONSUMER_GROUP} on {STREAM_KEY}")
    except redis_client.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.debug(f"Consumer group {CONSUMER_GROUP} already exists")
        else:
            raise


def _build_execution_prompt(task: AgentSystemTask) -> str:
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


async def process_message(msg_id: str, data: dict) -> bool:
    """
    Process a single task message from the stream.
    Returns True if processed successfully, False if should retry.
    """
    task_id = data.get("task_id")

    if not task_id:
        logger.error(f"Message {msg_id}: missing task_id, discarding")
        return True  # Discard malformed message

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AgentSystemTask).where(AgentSystemTask.id == task_id))
            task = result.scalar_one_or_none()

            if task is None:
                logger.warning(f"Task {task_id} not found, discarding message {msg_id}")
                return True  # Discard; task was deleted

            # Idempotence: skip if already done/failed (not pending/failed)
            if task.status not in ("pending", "failed"):
                logger.info(f"Task {task_id} already {task.status}, skipping (msg {msg_id})")
                return True  # Already processed

            # Verify agent profile exists
            if not task.agent_profile_id:
                logger.warning(f"Task {task_id}: no agent_profile_id")
                task.status = "failed"
                task.error_message = "No agent profile assigned"
                await db.commit()
                return True  # Terminal state

            # Mark as in_progress before executing
            task.status = "in_progress"
            task.error_message = None
            await db.commit()

        # Execute the task (separate session to avoid deadlocks)
        success = await _execute_task(task_id)
        return success

    except Exception as exc:
        logger.exception(f"Unexpected error processing message {msg_id}")
        report_error(
            str(exc), f"worker:task_worker:process:{msg_id}",
            error_type=type(exc).__name__, exc=exc,
            context={"task_id": task_id},
            severity="error",
        )
        return False  # Retry


async def _execute_task(task_id: str) -> bool:
    """Execute the Bedrock agent task. Returns True if successful."""
    from services.bedrock.agent_loop import run_single_turn_sync
    from services.bedrock.agent_profiles import get_profile
    from services.bedrock.errors import BedrockError

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AgentSystemTask).where(AgentSystemTask.id == task_id))
        task = result.scalar_one_or_none()

        if task is None or task.status != "in_progress":
            logger.warning(f"Task {task_id} disappeared or status changed before execution")
            return True  # Don't retry

        try:
            profile = get_profile(task.agent_profile_id)
        except KeyError:
            task.status = "failed"
            task.error_message = f"Agent not found: {task.agent_profile_id}"
            await db.commit()
            logger.error(f"Task {task_id}: agent profile not found")
            return True  # Terminal state

        try:
            record_history = profile.level < 3
            event = await run_single_turn_sync(
                db,
                user_id=task.user_id,
                session_id=f"scheduled-task-{task.id}",
                message=_build_execution_prompt(task),
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
            logger.info(f"Task {task_id} completed successfully")
            return True

        except (BedrockError, Exception) as exc:
            logger.exception(f"Task {task_id} execution failed")
            report_error(
                str(exc), f"worker:task_worker:execute:{task_id}",
                error_type=type(exc).__name__, exc=exc,
                context={"task_id": task_id, "agent_profile_id": task.agent_profile_id},
                severity="error",
            )
            try:
                await db.rollback()
            except Exception:
                logger.exception(f"Rollback after task {task_id} failure also failed")

            async with AsyncSessionLocal() as db2:
                failed = await db2.get(AgentSystemTask, task_id)
                if failed is not None and failed.status == "in_progress":
                    failed.status = "failed"
                    failed.error_message = str(exc)[:ERROR_MAX_CHARS]
                    failed.executed_at = datetime.now(timezone.utc)
                    await db2.commit()
                    logger.info(f"Task {task_id} marked as failed")
            return True  # Terminal state; don't retry


async def worker_loop(redis_client) -> None:
    """Main worker loop — consume and process messages."""
    await ensure_consumer_group(redis_client)
    logger.info(f"Worker started, consuming from {STREAM_KEY}")

    while True:
        try:
            # Read messages from consumer group
            messages = await redis_client.xreadgroup(
                {STREAM_KEY: ">"},  # > = new messages
                CONSUMER_GROUP,
                CONSUMER_NAME,
                count=1,
                block=POLL_TIMEOUT_MS,
            )

            if not messages:
                continue

            for stream_key, msgs in messages:
                for msg_id, data in msgs:
                    success = await process_message(msg_id, data)
                    if success:
                        await redis_client.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    else:
                        logger.warning(f"Message {msg_id} failed; will retry on next poll")

        except asyncio.CancelledError:
            logger.info("Worker shutting down")
            break
        except Exception as exc:
            logger.exception("Worker loop error")
            report_error(
                str(exc), "worker:task_worker:loop",
                error_type=type(exc).__name__, exc=exc,
                severity="critical",
            )
            await asyncio.sleep(5)


async def main():
    """Entry point for the worker."""
    try:
        redis_client = await get_redis()
        await worker_loop(redis_client)
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as exc:
        logger.exception("Worker failed to start")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
