"""Cliente de `/linkedin` (RF-003)."""
from typing import Any, Dict, List

from clients.api_client import ApiClient
from clients.career import _ID_RE, _check


class LinkedInClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def status(self) -> Dict[str, Any]:
        return await self._api.get_json("/linkedin/status")

    async def list_posts(self) -> List[Dict[str, Any]]:
        return await self._api.get_json("/linkedin/posts")

    async def create_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json("/linkedin/posts", json=payload)

    async def delete_post(self, post_id: str) -> None:
        await self._api.delete_json(f"/linkedin/posts/{_check(post_id, _ID_RE, 'id')}")
