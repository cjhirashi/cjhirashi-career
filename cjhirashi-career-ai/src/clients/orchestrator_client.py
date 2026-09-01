"""
HTTP Client for Orchestrator API (FASE 3).

The IA service is stateless for career data — it reads/writes entirely through
HTTP calls to the Orchestrator (main API). This enforces single-writer pattern
and maintains separation of concerns.

Pattern: All career CRUD goes through this client, not direct DB access.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx
from config import settings

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """HTTP client for Orchestrator API calls."""

    def __init__(self, timeout: float = settings.ORCHESTRATOR_API_TIMEOUT_SECONDS):
        self.base_url = settings.ORCHESTRATOR_API_BASE_URL.rstrip("/")
        self.timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        """Return async HTTP client (for use within async context)."""
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def get_user(self, user_id: str, auth_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Orchestrator."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/users/{user_id}",
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get user {user_id}: {e}")
                return None

    async def get_career_data(self, user_id: str, auth_token: str) -> Optional[Dict[str, Any]]:
        """Get career CRUD data (identities, competencies, work history, etc.)."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/career/{user_id}",
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get career data for {user_id}: {e}")
                return None

    async def create_work_history(
        self,
        user_id: str,
        auth_token: str,
        **work_history_data,
    ) -> Optional[Dict[str, Any]]:
        """Create a new work history entry."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/work-history",
                    json={"user_id": user_id, **work_history_data},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to create work history: {e}")
                return None

    async def update_career_stage(
        self,
        user_id: str,
        auth_token: str,
        stage_id: str,
        **stage_data,
    ) -> Optional[Dict[str, Any]]:
        """Update career stage."""
        async with await self._get_client() as client:
            try:
                response = await client.patch(
                    f"/career-stages/{stage_id}",
                    json=stage_data,
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to update career stage {stage_id}: {e}")
                return None

    async def create_competency(
        self,
        user_id: str,
        auth_token: str,
        **competency_data,
    ) -> Optional[Dict[str, Any]]:
        """Create a new competency."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/competencies",
                    json={"user_id": user_id, **competency_data},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to create competency: {e}")
                return None

    async def get_usage_metrics(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Get usage metrics (Bedrock cost tracking, agent execution stats)."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/usage-metrics/{user_id}",
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get usage metrics for {user_id}: {e}")
                return None

    async def log_agent_usage(
        self,
        user_id: str,
        auth_token: str,
        input_tokens: int,
        output_tokens: int,
        model_id: str,
        cost_usd: float,
    ) -> Optional[Dict[str, Any]]:
        """Log Bedrock usage to Orchestrator for tracking."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/usage-logs",
                    json={
                        "user_id": user_id,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "model_id": model_id,
                        "cost_usd": cost_usd,
                    },
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to log usage: {e}")
                return None

    async def get_conversations(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener conversaciones del usuario."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/conversations",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo conversaciones: {e}")
                return None

    async def get_conversation_messages(
        self,
        user_id: str,
        auth_token: str,
        session_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener mensajes de una conversación."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/conversations/{session_id}/messages",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo mensajes: {e}")
                return None

    async def rename_conversation(
        self,
        user_id: str,
        auth_token: str,
        session_id: str,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Renombrar conversación."""
        async with await self._get_client() as client:
            try:
                response = await client.patch(
                    f"/conversations/{session_id}",
                    json={"title": title, "user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error renombrando conversación: {e}")
                return None

    async def delete_conversation(
        self,
        user_id: str,
        auth_token: str,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Eliminar conversación."""
        async with await self._get_client() as client:
            try:
                response = await client.delete(
                    f"/conversations/{session_id}",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error eliminando conversación: {e}")
                return None

    async def get_memory(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener registros de memoria."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/memory",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo memoria: {e}")
                return None

    async def get_memory_events(
        self,
        user_id: str,
        auth_token: str,
        session_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener eventos de memoria para una conversación."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/memory/events/{session_id}",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo eventos de memoria: {e}")
                return None

    async def get_catalog(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener catálogo de perfiles de agente."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/catalog",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo catálogo: {e}")
                return None

    async def get_custom_tools(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener herramientas personalizadas."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/custom-tools",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo herramientas personalizadas: {e}")
                return None

    async def create_custom_tool(
        self,
        user_id: str,
        auth_token: str,
        name: str,
        url: str,
        headers: Dict = None,
    ) -> Optional[Dict[str, Any]]:
        """Crear herramienta personalizada."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/custom-tools",
                    json={"user_id": user_id, "name": name, "url": url, "headers": headers or {}},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error creando herramienta: {e}")
                return None

    async def execute_task(
        self,
        user_id: str,
        auth_token: str,
        task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Ejecutar tarea."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/tasks/{task_id}/run",
                    json={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error ejecutando tarea: {e}")
                return None

    async def get_audit_log(
        self,
        user_id: str,
        auth_token: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[List[Dict[str, Any]]]:
        """Obtener registro de auditoría."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/audit-log",
                    params={"user_id": user_id, "limit": limit, "offset": offset},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo registro de auditoría: {e}")
                return None

    async def verify_token(
        self,
        auth_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Verificar token JWT con el Orchestrator."""
        async with await self._get_client() as client:
            try:
                response = await client.post(
                    f"/auth/verify",
                    json={"token": auth_token},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error verificando token: {e}")
                return None

    async def get_system_prompt(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Obtener instrucciones del sistema (system prompt)."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/instructions",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo instrucciones: {e}")
                return None

    async def set_system_prompt(
        self,
        user_id: str,
        auth_token: str,
        prompt: str,
    ) -> Optional[Dict[str, Any]]:
        """Actualizar instrucciones del sistema."""
        async with await self._get_client() as client:
            try:
                response = await client.patch(
                    f"/instructions",
                    json={"user_id": user_id, "prompt": prompt},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error actualizando instrucciones: {e}")
                return None

    async def get_global_rules(
        self,
        user_id: str,
        auth_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Obtener reglas globales."""
        async with await self._get_client() as client:
            try:
                response = await client.get(
                    f"/rules",
                    params={"user_id": user_id},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error obteniendo reglas: {e}")
                return None

    async def set_global_rules(
        self,
        user_id: str,
        auth_token: str,
        rules: str,
    ) -> Optional[Dict[str, Any]]:
        """Actualizar reglas globales."""
        async with await self._get_client() as client:
            try:
                response = await client.patch(
                    f"/rules",
                    json={"user_id": user_id, "rules": rules},
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error actualizando reglas: {e}")
                return None


# Singleton instance
orchestrator_client = OrchestratorClient()
