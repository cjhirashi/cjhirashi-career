"""Registro centralizado de fallas del sistema (ADR-018).

- `POST /system/error-report` — ingesta pública (SPA Admin/Portfolio y MCP),
  con rate-limit por IP y límite de tamaño de cuerpo. Sin auth por diseño:
  el Portfolio es anónimo y el MCP no tiene credenciales de usuario.
- `GET/PATCH/DELETE /settings/error-reports*` — consulta y gestión, solo Carlos
  (JWT), consumido por la pantalla *Settings → Reportes de Falla* del Admin.
"""
from __future__ import annotations

import time
from collections import deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.error_reports import (
    ErrorReportDetail,
    ErrorReportIngest,
    ErrorReportList,
    ErrorReportSummary,
    ErrorReportUpdate,
    PurgeResolvedRequest,
    PurgeResolvedResponse,
)
from services import error_report_service
from services.error_reporting import report_error

router = APIRouter(tags=["Error Reports"])

# --- Rate-limit del endpoint público ---------------------------------------
_INGEST_MAX_BODY = 32 * 1024          # 32 KB por request
_INGEST_WINDOW_SECONDS = 60
_INGEST_MAX_PER_WINDOW = 30           # por IP y ventana
_ingest_hits: dict[str, deque] = {}
_ingest_lock = Lock()


def _rate_limited(client_ip: str) -> bool:
    now = time.monotonic()
    with _ingest_lock:
        bucket = _ingest_hits.setdefault(client_ip, deque())
        while bucket and now - bucket[0] > _INGEST_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _INGEST_MAX_PER_WINDOW:
            return True
        bucket.append(now)
        # Poda oportunista para no crecer sin límite.
        if len(_ingest_hits) > 2048:
            for ip in [k for k, v in _ingest_hits.items() if not v]:
                _ingest_hits.pop(ip, None)
    return False


@router.post("/system/error-report", status_code=status.HTTP_202_ACCEPTED)
async def ingest_error_report(payload: ErrorReportIngest, request: Request) -> dict:
    """Ingesta pública de una falla. Rate-limited; nunca lanza por el registro."""
    client_ip = request.client.host if request.client else "desconocido"
    if _rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados reportes; intenta más tarde.",
        )
    body_len = request.headers.get("content-length")
    if body_len and int(body_len) > _INGEST_MAX_BODY:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Cuerpo demasiado grande.",
        )
    context = dict(payload.context or {})
    context.setdefault("client_ip", client_ip)
    if payload.stack_trace:
        context.setdefault("reported_stack_trace", payload.stack_trace)
    report_error(
        payload.message,
        payload.source,
        error_type=payload.error_type,
        context=context or None,
        severity=payload.severity,
    )
    return {"accepted": True}


@router.get(
    "/settings/error-reports",
    response_model=ErrorReportList,
    summary="Lista paginada de reportes de falla",
)
async def list_error_reports(
    resolved: bool | None = Query(default=None),
    severity: str | None = Query(default=None),
    source: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await error_report_service.list_reports(
        db,
        resolved=resolved,
        severity=severity,
        source=source,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/settings/error-reports/summary",
    response_model=ErrorReportSummary,
    summary="Contadores de reportes pendientes / resueltos",
)
async def error_reports_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await error_report_service.summary(db)


@router.post(
    "/settings/error-reports/purge-resolved",
    response_model=PurgeResolvedResponse,
    summary="Elimina reportes resueltos antiguos",
)
async def purge_resolved_error_reports(
    payload: PurgeResolvedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await error_report_service.purge_resolved(
        db, older_than_days=payload.older_than_days
    )
    return {"deleted": deleted}


@router.get(
    "/settings/error-reports/{report_id}",
    response_model=ErrorReportDetail,
    summary="Detalle de un reporte de falla",
)
async def get_error_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await error_report_service.get_report(db, report_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
    return item


@router.patch(
    "/settings/error-reports/{report_id}",
    response_model=ErrorReportDetail,
    summary="Marca un reporte como resuelto o lo reabre",
)
async def update_error_report(
    report_id: str,
    payload: ErrorReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = getattr(current_user, "id", None) or getattr(current_user, "email", "usuario")
    if payload.resolved:
        item = await error_report_service.resolve_report(
            db, report_id, notes=payload.resolution_notes, actor=str(actor)
        )
    else:
        item = await error_report_service.reopen_report(db, report_id, actor=str(actor))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
    return item


@router.delete(
    "/settings/error-reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina un reporte de falla",
)
async def delete_error_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await error_report_service.delete_report(db, report_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
