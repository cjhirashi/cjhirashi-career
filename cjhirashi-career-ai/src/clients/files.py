"""Cliente de `/files` (RF-003): subida multipart, metadatos, contenido crudo y visibilidad."""
from typing import Any, Dict, List, Optional, Tuple

from clients.api_client import ApiClient
from clients.career import _ID_RE, _check


class FilesClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def upload(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        *,
        category: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Dict[str, Any]:
        data = {"category": category, "description": description}
        if is_public is not None:
            data["is_public"] = "true" if is_public else "false"
        data = {k: v for k, v in data.items() if v is not None}
        return await self._api.post_json(
            "/files", data=data, files={"file": (filename, content, content_type)}
        )

    async def list(
        self,
        *,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        params = {"category": category, "file_type": file_type, "skip": skip, "limit": limit}
        return await self._api.get_json("/files", params=params)

    async def get(self, file_id: str) -> Dict[str, Any]:
        """Metadatos (`GET /files/{id}`, D-25)."""
        return await self._api.get_json(f"/files/{_check(file_id, _ID_RE, 'id')}")

    async def get_raw(self, file_id: str) -> Tuple[bytes, str]:
        return await self._api.get_bytes(f"/files/{_check(file_id, _ID_RE, 'id')}/raw")

    async def get_download_url(self, file_id: str) -> str:
        """URL firmada de corta vida (`GET /files/{id}/download` -> `PresignedUrlResponse.url`)."""
        out = await self._api.get_json(f"/files/{_check(file_id, _ID_RE, 'id')}/download")
        return out["url"]

    async def set_visibility(self, file_id: str, is_public: bool) -> Dict[str, Any]:
        return await self._api.patch_json(
            f"/files/{_check(file_id, _ID_RE, 'id')}/visibility", json={"is_public": is_public}
        )
