"""Reporte de fallas del harness a `POST /system/error-report` (ingesta pública, sin auth; RF-003).

Nunca lanza: reportar una falla no puede provocar otra."""
import logging
from typing import Any, Dict

from clients.api_client import ApiClient, ApiError

logger = logging.getLogger(__name__)


class ErrorsClient:
    def __init__(self, api: ApiClient):
        self._api = api

    async def report(self, payload: Dict[str, Any]) -> bool:
        try:
            await self._api.post_json("/system/error-report", json=payload, auth="none")
            return True
        except ApiError as exc:
            logger.warning("no se pudo reportar el error a la API: %s", exc)
            return False
        except Exception as exc:  # contrato: nunca lanza (p. ej. payload no serializable)
            logger.warning("no se pudo reportar el error a la API: %s", type(exc).__name__)
            return False
