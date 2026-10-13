"""Cliente del CRUD genérico de carrera (RF-003).

Enrutado de `resource_key` (contracts/harness-api-dependencies.md):
`pdf-output-templates` -> /pdf-templates · `pdf-template-styles` -> /pdf-template-styles ·
`agent-tasks` -> BD propia (LOCAL, nunca por REST) · resto -> /career/<recurso>.
"""
import json
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

from clients.api_client import ApiClient, ApiError

PAGE_SIZE = 100  # máximo que acepta la API por página
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_NON_CAREER = {"pdf-output-templates": "/pdf-templates", "pdf-template-styles": "/pdf-template-styles"}
LOCAL_RESOURCES = frozenset({"agent-tasks"})


class LocalResourceError(Exception):
    """El recurso vive en la BD del harness: no se pide a la API."""


def _check(value: str, pattern: "re.Pattern[str]", what: str) -> str:
    if not isinstance(value, str) or not pattern.match(value):
        raise ValueError(f"{what} inválido: {value!r}")
    return quote(value, safe="")


class CareerClient:
    def __init__(self, api: ApiClient, max_items: Optional[int] = None):
        from config import settings

        self._api = api
        self._max_items = max_items or settings.API_LIST_MAX_ITEMS

    # -- rutas ----------------------------------------------------------------
    @staticmethod
    def base_path(resource: str) -> str:
        key = _check(resource, _KEY_RE, "resource_key")
        if key in LOCAL_RESOURCES:
            raise LocalResourceError(f"{key!r} es un recurso local del harness (BD propia)")
        return _NON_CAREER.get(key, f"/career/{key}")

    def _item(self, resource: str, item_id: str) -> str:
        return f"{self.base_path(resource)}/{_check(item_id, _ID_RE, 'id')}"

    @staticmethod
    def _is_career(base: str) -> bool:
        return base.startswith("/career/")

    # -- lectura --------------------------------------------------------------
    async def list(
        self,
        resource: str,
        *,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        base = self.base_path(resource)
        extra = {"search": search, "sort_by": sort_by}
        if not self._is_career(base) and (any(v is not None for v in extra.values()) or filters):
            raise ValueError(f"{resource!r} sólo admite paginación (sin search/filters/sort)")
        wanted = min(limit, self._max_items) if limit else self._max_items
        items: List[Dict[str, Any]] = []
        while len(items) < wanted:
            size = min(PAGE_SIZE, wanted - len(items))
            params: Dict[str, Any] = {"skip": len(items), "limit": size}
            if self._is_career(base):
                params.update(
                    search=search,
                    sort_by=sort_by,
                    sort_dir=sort_dir if sort_by else None,
                    filters=json.dumps(filters) if filters else None,
                )
            page = await self._api.get_json(base, params=params) or []
            items.extend(page)
            if len(page) < size:
                break
        return items[:wanted]

    async def get(self, resource: str, item_id: str) -> Dict[str, Any]:
        return await self._api.get_json(self._item(resource, item_id))

    async def count(
        self, resource: str, *, search: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        base = self.base_path(resource)
        if not self._is_career(base):
            raise ValueError(f"{resource!r} no ofrece /count")
        params = {"search": search, "filters": json.dumps(filters) if filters else None}
        return (await self._api.get_json(f"{base}/count", params=params))["count"]

    async def distinct(self, resource: str, field: str) -> List[Any]:
        base = self.base_path(resource)
        if not self._is_career(base):
            raise ValueError(f"{resource!r} no ofrece /distinct")
        out = await self._api.get_json(f"{base}/distinct/{_check(field, _FIELD_RE, 'campo')}")
        return out["values"]

    # -- escritura ------------------------------------------------------------
    async def create(self, resource: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.post_json(self.base_path(resource), json=payload)

    async def update(self, resource: str, item_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._api.put_json(self._item(resource, item_id), json=payload)

    async def delete(self, resource: str, item_id: str) -> None:
        await self._api.delete_json(self._item(resource, item_id))

    async def bulk_update(
        self, resource: str, updates: Sequence[Tuple[str, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """N× PUT secuencial (no hay endpoint masivo). Un fallo no aborta el resto."""
        results: List[Dict[str, Any]] = []
        for item_id, payload in updates:
            try:
                row = await self.update(resource, item_id, payload)
                results.append({"id": item_id, "ok": True, "record": row})
            except ApiError as exc:
                results.append({"id": item_id, "ok": False, "error": exc.detail, "status": exc.status})
        return results
