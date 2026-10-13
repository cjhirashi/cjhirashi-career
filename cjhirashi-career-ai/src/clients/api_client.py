"""Cliente HTTP único hacia la API de datos (RF-003, RF-004).

- Un `httpx.AsyncClient` por proceso, `base_url = API_BASE_URL`, timeouts explícitos.
- Sin credencial por defecto: toma el `Principal` (JWT del usuario) o, si no hay, el
  `ServiceContext` activo; si no hay ninguno lanza `MissingCredentialError`.
- Reintenta (máx. 2) sólo métodos idempotentes ante 5xx/timeout/error de red.
- Todo status >= 400 se traduce a `ApiError(status, detail)`; `status == 0` = sin respuesta.
"""
import asyncio
from typing import Any, Dict, Optional, Tuple

import httpx

from middleware.principal import current_principal, current_service_context

IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE"})
MAX_RETRIES = 2
AUTH_MODES = ("context", "service", "none")


class ApiError(Exception):
    """Respuesta de error de la API (401/403/404/409/422/…) o fallo de transporte (status 0)."""

    def __init__(self, status: int, detail: Any = None):
        self.status = status
        self.detail = detail
        super().__init__(f"API {status}: {detail}")


class MissingCredentialError(Exception):
    """No hay `Principal` ni `ServiceContext`: el cliente no inventa credenciales."""


def _detail(response: httpx.Response) -> Any:
    try:
        body = response.json()
    except ValueError:
        return response.text
    if isinstance(body, dict) and "detail" in body:
        return body["detail"]
    return body


class ApiClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: Optional[float] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        max_retries: int = MAX_RETRIES,
        backoff: float = 0.2,
    ):
        from config import settings

        self.base_url = base_url or settings.API_BASE_URL
        self._max_retries = min(max_retries, MAX_RETRIES)
        self._backoff = backoff
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout if timeout is not None else settings.API_TIMEOUT_SECONDS, connect=5.0),
            transport=transport,
        )

    async def aclose(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()

    # -- credencial -----------------------------------------------------------
    @staticmethod
    def _bearer(token: Optional[str]) -> Dict[str, str]:
        if not token or not token.strip():
            raise MissingCredentialError("la credencial está vacía: no se envía 'Bearer ' sin token")
        return {"Authorization": f"Bearer {token.strip()}"}

    def _headers(self, auth: str) -> Dict[str, str]:
        if auth not in AUTH_MODES:
            raise ValueError(f"auth inválido: {auth!r} (esperado {AUTH_MODES})")
        if auth == "none":
            return {}
        if auth == "service":
            from config import settings

            return self._bearer(settings.AI_SERVICE_TOKEN)
        principal = current_principal()
        if principal is not None:
            return self._bearer(principal.token)
        service = current_service_context()
        if service is not None:
            return self._bearer(service.token)
        raise MissingCredentialError("sin Principal ni ServiceContext: no hay credencial hacia la API")

    # -- núcleo ---------------------------------------------------------------
    async def send(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Any = None,
        data: Optional[Dict[str, Any]] = None,
        files: Any = None,
        auth: str = "context",
    ) -> httpx.Response:
        method = method.upper()
        headers = self._headers(auth)
        params = {k: v for k, v in (params or {}).items() if v is not None} or None
        retries = self._max_retries if method in IDEMPOTENT_METHODS else 0
        attempt = 0
        while True:
            try:
                response = await self._client.request(
                    method, path, params=params, json=json, data=data, files=files, headers=headers
                )
            except httpx.TransportError as exc:
                self._client.cookies.clear()  # timeouts, conexión rechazada, etc.
                if attempt < retries:
                    attempt += 1
                    await asyncio.sleep(self._backoff * attempt)
                    continue
                raise ApiError(0, f"sin respuesta de la API: {type(exc).__name__}") from exc
            # El cliente es compartido entre usuarios: nunca se conservan cookies de la API.
            self._client.cookies.clear()
            if response.status_code >= 500 and attempt < retries:
                attempt += 1
                await asyncio.sleep(self._backoff * attempt)
                continue
            if response.status_code >= 400:
                raise ApiError(response.status_code, _detail(response))
            return response

    @staticmethod
    def _parse(response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def get_json(self, path: str, **kw) -> Any:
        return self._parse(await self.send("GET", path, **kw))

    async def post_json(self, path: str, **kw) -> Any:
        return self._parse(await self.send("POST", path, **kw))

    async def put_json(self, path: str, **kw) -> Any:
        return self._parse(await self.send("PUT", path, **kw))

    async def patch_json(self, path: str, **kw) -> Any:
        return self._parse(await self.send("PATCH", path, **kw))

    async def delete_json(self, path: str, **kw) -> Any:
        return self._parse(await self.send("DELETE", path, **kw))

    async def get_bytes(self, path: str, **kw) -> Tuple[bytes, str]:
        r = await self.send("GET", path, **kw)
        return r.content, r.headers.get("content-type", "")

    async def post_bytes(self, path: str, **kw) -> Tuple[bytes, str]:
        r = await self.send("POST", path, **kw)
        return r.content, r.headers.get("content-type", "")


_default: Optional[ApiClient] = None


def get_api_client() -> ApiClient:
    """Instancia por proceso (los clientes por familia la reciben inyectada)."""
    global _default
    if _default is None:
        _default = ApiClient()
    return _default
