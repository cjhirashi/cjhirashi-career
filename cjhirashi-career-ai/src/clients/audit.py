"""Cliente de `/audit-log` (RF-021): historial de cambios del agente y restauración, con el JWT del usuario."""
from typing import Any, Dict, List, Optional

from clients.api_client import ApiClient
from clients.career import _ID_RE, _check


class AuditClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def list(
        self, *, limit: int = 50, offset: int = 0, resource: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset, "resource": resource}
        return await self._api.get_json("/audit-log", params=params)

    async def restore(self, audit_id: str) -> Dict[str, Any]:
        return await self._api.post_json(f"/audit-log/{_check(audit_id, _ID_RE, 'id')}/restore")
