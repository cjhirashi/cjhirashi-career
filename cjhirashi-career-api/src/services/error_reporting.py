"""Camino de ESCRITURA del registro centralizado de fallas (ADR-018).

`report_error(...)` es el punto único por el que cualquier parte del sistema
deja un registro en la tabla `error_reports`. Diseño:

- **Nunca lanza.** Un fallo al registrar la falla se traga con `logger.error`;
  jamás debe romper el flujo que ya venía fallando.
- **Nunca reentra.** Un guard con `contextvars` corta el bucle
  "error al registrar el error".
- **Engine síncrono propio (psycopg2).** Independiente del event loop async de
  la app y de la sesión de la request que falló (que puede estar en rollback).
  Desde código async se usa `areport_error` (threadpool).
- **Deduplicación por huella.** Si ya hay una fila pendiente con el mismo
  `fingerprint`, se incrementa `occurrences` y se refresca `last_seen_at` en vez
  de crear otra.

El camino de LECTURA/gestión vive en `services/error_report_service.py`.
"""
from __future__ import annotations

import contextvars
import hashlib
import logging
import re
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from config import settings

logger = logging.getLogger(__name__)

_VALID_SEVERITY = {"warning", "error", "critical"}
_MAX_MESSAGE = 8000
_MAX_STACK = 20000

_in_reporting: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_in_error_reporting", default=False
)

# --- Engine síncrono dedicado -------------------------------------------------
_SYNC_URL = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
_engine = create_engine(_SYNC_URL, poolclass=NullPool, future=True)
_SyncSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

# --- Normalización del mensaje para agrupar repeticiones ---------------------
_RE_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)
_RE_HEX = re.compile(r"0x[0-9a-fA-F]+")
_RE_NUM = re.compile(r"\d+")
_RE_WS = re.compile(r"\s+")


def _normalize(message: str) -> str:
    text = message or ""
    text = _RE_UUID.sub("<uuid>", text)
    text = _RE_HEX.sub("<hex>", text)
    text = _RE_NUM.sub("<n>", text)
    text = _RE_WS.sub(" ", text).strip()
    return text[:500]


def _fingerprint(source: str, error_type: Optional[str], message: str) -> str:
    raw = f"{source}|{error_type or ''}|{_normalize(message)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def report_error(
    message: Any,
    source: str,
    *,
    error_type: Optional[str] = None,
    exc: Optional[BaseException] = None,
    context: Optional[dict] = None,
    severity: str = "error",
) -> None:
    """Registra una falla en `error_reports`. No lanza nunca.

    Args:
        message: Texto del error.
        source: Dónde se generó, p. ej. ``"api:POST /career/vacancies"``,
            ``"service:pdf_service.generate_pdf"``, ``"scheduler:task_scheduler"``,
            ``"bedrock:tool.create_career_record"``, ``"mcp:cv_generator"``.
        error_type: Nombre de la clase de excepción (se deduce de ``exc``).
        exc: Excepción original; de ella se extrae el traceback.
        context: Datos extra serializables (request_path, status_code, task_id…).
        severity: ``warning`` | ``error`` | ``critical``.
    """
    if _in_reporting.get():
        logger.error("report_error reentrante ignorado: %s @ %s", message, source)
        return
    token = _in_reporting.set(True)
    try:
        severity = severity if severity in _VALID_SEVERITY else "error"
        text = (str(message).strip() if message is not None else "") or (
            error_type or "Error desconocido"
        )
        text = text[:_MAX_MESSAGE]
        source = (str(source).strip() or "desconocido")[:255]
        if error_type is None and exc is not None:
            error_type = type(exc).__name__
        if error_type:
            error_type = str(error_type)[:120]

        stack: Optional[str] = None
        if exc is not None:
            stack = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )[:_MAX_STACK]

        fingerprint = _fingerprint(source, error_type, text)
        now = datetime.now(timezone.utc)

        session = _SyncSession()
        try:
            from models.error_report import ErrorReport

            existing = session.execute(
                select(ErrorReport)
                .where(
                    ErrorReport.fingerprint == fingerprint,
                    ErrorReport.resolved.is_(False),
                )
                .order_by(ErrorReport.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            if existing is not None:
                existing.occurrences = (existing.occurrences or 1) + 1
                existing.last_seen_at = now
                existing.message = text
                existing.severity = severity
                if context:
                    existing.context = context
                if stack:
                    existing.stack_trace = stack
            else:
                session.add(
                    ErrorReport(
                        message=text,
                        source=source,
                        error_type=error_type or None,
                        stack_trace=stack,
                        context=context or None,
                        severity=severity,
                        resolved=False,
                        fingerprint=fingerprint,
                        occurrences=1,
                        first_seen_at=now,
                        last_seen_at=now,
                    )
                )
            session.commit()
        except Exception as inner:  # noqa: BLE001 - camino de reporte, nunca propaga
            session.rollback()
            logger.error(
                "No se pudo registrar la falla en error_reports: %s "
                "(falla original: %s @ %s)",
                inner,
                text,
                source,
            )
        finally:
            session.close()
    except Exception as outer:  # noqa: BLE001 - blindaje total del camino de reporte
        logger.error("Fallo inesperado en report_error: %s", outer)
    finally:
        _in_reporting.reset(token)


async def areport_error(message: Any, source: str, **kwargs: Any) -> None:
    """Versión async: ejecuta `report_error` en un threadpool.

    Para usar desde handlers/servicios async sin bloquear el event loop.
    """
    from starlette.concurrency import run_in_threadpool

    await run_in_threadpool(lambda: report_error(message, source, **kwargs))


@contextmanager
def capture_errors(
    source: str,
    *,
    severity: str = "error",
    reraise: bool = True,
    context: Optional[dict] = None,
) -> Iterator[None]:
    """Envuelve un bloque: registra cualquier excepción y (opcional) la re-lanza.

    Uso::

        with capture_errors("scheduler:task_scheduler", reraise=False):
            _run_due_tasks()
    """
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - se re-lanza salvo reraise=False
        report_error(
            str(exc) or exc.__class__.__name__,
            source,
            error_type=exc.__class__.__name__,
            exc=exc,
            context=context,
            severity=severity,
        )
        if reraise:
            raise
