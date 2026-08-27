"""Reporte de fallas del MCP al registro central del sistema (ADR-018).

El MCP no tiene acceso a la base de datos, así que envía la falla por HTTP al
endpoint público `POST /system/error-report` de la API. Fire-and-forget: nunca
lanza y nunca bloquea el resultado de la tool.
"""
import json
import os
import threading
import traceback
import urllib.request

_API_URL = os.getenv("API_INTERNAL_URL", "http://cjhirashi-career-api:8001").rstrip("/")
_ENDPOINT = f"{_API_URL}/system/error-report"
_TIMEOUT = 5


def _post(payload: dict) -> None:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            _ENDPOINT, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=_TIMEOUT).read()
    except Exception:
        # El registro es best-effort; no rompe la tool.
        pass


def report_error(message: str, source: str, *, exc: BaseException | None = None,
                 severity: str = "error", context: dict | None = None) -> None:
    payload = {
        "message": str(message)[:8000] or "Error desconocido",
        "source": f"mcp:{source}"[:255],
        "severity": severity if severity in ("warning", "error", "critical") else "error",
    }
    if exc is not None:
        payload["error_type"] = type(exc).__name__
        payload["stack_trace"] = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )[:20000]
    if context:
        payload["context"] = context
    # En hilo aparte para no añadir latencia a la respuesta de la tool.
    threading.Thread(target=_post, args=(payload,), daemon=True).start()
