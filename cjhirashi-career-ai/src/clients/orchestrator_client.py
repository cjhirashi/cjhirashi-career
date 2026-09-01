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

    # Add more methods as needed for other CRUD operations
    # (create identity, update profile, etc.)


# Singleton instance
orchestrator_client = OrchestratorClient()
