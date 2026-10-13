"""Cliente de plantillas y estilos PDF (`/pdf-templates`, `/pdf-template-styles`, RF-003)."""
from typing import Any, Dict, List, Optional, Tuple

from clients.api_client import ApiClient
from clients.career import _ID_RE, _check

TEMPLATES = "/pdf-templates"
STYLES = "/pdf-template-styles"


def _item(base: str, item_id: str) -> str:
    return f"{base}/{_check(item_id, _ID_RE, 'id')}"


class PdfClient:
    def __init__(self, api: ApiClient):
        self._api = api

    # -- plantillas -----------------------------------------------------------
    async def list_templates(
        self, *, document_type: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[Dict[str, Any]]:
        params = {"document_type": document_type, "skip": skip, "limit": limit}
        return await self._api.get_json(TEMPLATES, params=params)

    async def get_template(self, template_id: str) -> Dict[str, Any]:
        return await self._api.get_json(_item(TEMPLATES, template_id))

    async def default_template(self, document_type: str) -> Dict[str, Any]:
        return await self._api.get_json(f"{TEMPLATES}/defaults/by-type", params={"document_type": document_type})

    async def create_template(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(TEMPLATES, json=payload)

    async def update_template(self, template_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.put_json(_item(TEMPLATES, template_id), json=payload)

    async def delete_template(self, template_id: str) -> None:
        await self._api.delete_json(_item(TEMPLATES, template_id))

    async def render_template(self, template_id: str, payload: Dict[str, Any]) -> Tuple[bytes, str]:
        return await self._api.post_bytes(f"{_item(TEMPLATES, template_id)}/render", json=payload)

    # -- estilos --------------------------------------------------------------
    async def list_styles(self, *, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        return await self._api.get_json(STYLES, params={"skip": skip, "limit": limit})

    async def get_style(self, style_id: str) -> Dict[str, Any]:
        return await self._api.get_json(_item(STYLES, style_id))

    async def create_style(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(STYLES, json=payload)

    async def update_style(self, style_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.put_json(_item(STYLES, style_id), json=payload)

    async def delete_style(self, style_id: str) -> None:
        await self._api.delete_json(_item(STYLES, style_id))
