"""Cliente de `/career/job-discoveries` (RF-003)."""
from typing import Any, Dict, List

from clients.api_client import ApiClient

BASE = "/career/job-discoveries"


class JobDiscoveryClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def providers(self) -> List[Dict[str, Any]]:
        return await self._api.get_json(f"{BASE}/providers")

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(f"{BASE}/run", json=payload)

    async def import_url(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(f"{BASE}/import-url", json=payload)

    async def save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(f"{BASE}/save", json=payload)
