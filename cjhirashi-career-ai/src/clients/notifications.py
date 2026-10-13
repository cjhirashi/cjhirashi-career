"""Cliente de `POST /notifications` (RF-020): sólo con el token de la cuenta de servicio."""
from typing import Any, Dict, Optional

from clients.api_client import ApiClient


class NotificationsClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def create(
        self,
        *,
        user_id: str,
        title: str,
        body: Optional[str] = None,
        kind: str = "task_turn",
        resource_key: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id, "kind": kind, "title": title, "body": body,
            "resource_key": resource_key, "resource_id": resource_id,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        # La API sólo acepta este endpoint al rol `service`, también durante un turno de usuario.
        return await self._api.post_json("/notifications", json=payload, auth="service")
