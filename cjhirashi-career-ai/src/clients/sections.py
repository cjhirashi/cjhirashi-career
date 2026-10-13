"""Clientes de secciones del Admin (`/admin/sections`) y metodologías operativas (RF-003)."""
from typing import Any, Dict, List, Optional

from clients.api_client import ApiClient
from clients.career import _ID_RE, CareerClient, _check

METHODOLOGIES_RESOURCE = "operational-methodologies"


class SectionsClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def list(self) -> List[Dict[str, Any]]:
        return await self._api.get_json("/admin/sections")

    async def get(self, section_id: str) -> Dict[str, Any]:
        return await self._api.get_json(f"/admin/sections/{_check(section_id, _ID_RE, 'id')}")

    async def update(self, section_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.put_json(f"/admin/sections/{_check(section_id, _ID_RE, 'id')}", json=payload)


class MethodologiesClient:
    """`/career/operational-methodologies` (el filtrado `applies_to_caller` es lógica del harness)."""

    def __init__(self, api: ApiClient, career: Optional[CareerClient] = None):
        self._career = career or CareerClient(api)

    async def list(self, **kw) -> List[Dict[str, Any]]:
        return await self._career.list(METHODOLOGIES_RESOURCE, **kw)

    async def get(self, methodology_id: str) -> Dict[str, Any]:
        return await self._career.get(METHODOLOGIES_RESOURCE, methodology_id)

    async def update(self, methodology_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._career.update(METHODOLOGIES_RESOURCE, methodology_id, payload)
