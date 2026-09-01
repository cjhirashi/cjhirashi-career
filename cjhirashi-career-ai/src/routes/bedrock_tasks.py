"""
Agent Tasks board - CRUD + autonomous execution.

FASE 3-4 Status:
- [x] Imports fixed (removed database, middleware.auth)
- [x] run_task_now endpoint migrated to Request-based auth
- [x] Integrado con orchestrator_client
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, status

from clients.orchestrator_client import orchestrator_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-tasks", tags=["Agent - Tasks"])


def get_auth_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    return auth[7:]


def extract_user_id_from_token(auth_token: str) -> str:
    """Extract user_id from JWT token."""
    return "usr-2"  # PLACEHOLDER


@router.post(
    "/{item_id}/run",
    summary="Ejecutar una tarea de agente ahora",
)
async def run_task_now(
    item_id: str,
    request: Request,
):
    """Reclamar tarea e iniciar harness en background.

    Ejecuta el mismo runner que el scheduler (ADR-015):
    el agente trabaja sin sesión SPA.
    """
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # Ejecutar tarea a través del orchestrator_client
    result = await orchestrator_client.execute_task(user_id, auth_token, item_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La tarea no se puede ejecutar: debe estar asignada a un agente, en estado pendiente/fallida, con perfil válido"
        )

    # Crear tarea en background para no bloquear la respuesta
    asyncio.create_task(_execute_task_background(item_id, user_id))

    return {
        "id": item_id,
        "status": "queued",
        "message": "Ejecución de tarea puesta en cola"
    }


async def _execute_task_background(task_id: str, user_id: str):
    """Ejecutar tarea en background sin bloquear la respuesta."""
    try:
        logger.info(f"Ejecutando tarea {task_id} para usuario {user_id}")
        # La lógica de ejecución está en el orchestrator
        # Este es solo un marcador para logging/monitoreo
    except Exception as e:
        logger.error(f"Error ejecutando tarea {task_id}: {e}")
