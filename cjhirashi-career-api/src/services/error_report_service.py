"""Camino de LECTURA / gestión del registro de fallas (ADR-018).

Fuente única usada por la ruta REST (`routes/error_reports.py`) y por la tool de
Bedrock `error_report_settings` (`services/bedrock/tools.py`). El camino de
ESCRITURA (captura de fallas) vive en `services/error_reporting.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.error_report import SEVERITIES, ErrorReport

MAX_PAGE_SIZE = 100


def _serialize(row: ErrorReport, *, detail: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": row.id,
        "message": row.message,
        "source": row.source,
        "error_type": row.error_type,
        "severity": row.severity,
        "resolved": row.resolved,
        "occurrences": row.occurrences,
        "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
        "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        "resolved_by": row.resolved_by,
        "resolution_notes": row.resolution_notes,
    }
    if detail:
        data["stack_trace"] = row.stack_trace
        data["context"] = row.context
    return data


async def list_reports(
    db: AsyncSession,
    *,
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    filters = []
    if resolved is not None:
        filters.append(ErrorReport.resolved.is_(resolved))
    if severity in SEVERITIES:
        filters.append(ErrorReport.severity == severity)
    if source:
        filters.append(ErrorReport.source.ilike(f"%{source}%"))
    if q:
        filters.append(ErrorReport.message.ilike(f"%{q}%"))

    total = await db.scalar(
        select(func.count()).select_from(ErrorReport).where(*filters)
    )
    result = await db.execute(
        select(ErrorReport)
        .where(*filters)
        .order_by(ErrorReport.resolved.asc(), ErrorReport.last_seen_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()
    return {
        "items": [_serialize(r) for r in rows],
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < int(total or 0),
    }


async def get_report(db: AsyncSession, report_id: str) -> Optional[dict[str, Any]]:
    row = await db.get(ErrorReport, report_id)
    return _serialize(row, detail=True) if row else None


async def summary(db: AsyncSession) -> dict[str, Any]:
    pending = await db.scalar(
        select(func.count()).select_from(ErrorReport).where(ErrorReport.resolved.is_(False))
    )
    resolved = await db.scalar(
        select(func.count()).select_from(ErrorReport).where(ErrorReport.resolved.is_(True))
    )
    by_sev_rows = await db.execute(
        select(ErrorReport.severity, func.count())
        .where(ErrorReport.resolved.is_(False))
        .group_by(ErrorReport.severity)
    )
    by_severity = {sev: 0 for sev in SEVERITIES}
    for sev, count in by_sev_rows.all():
        by_severity[sev] = int(count)
    newest = await db.scalar(
        select(func.max(ErrorReport.last_seen_at)).where(ErrorReport.resolved.is_(False))
    )
    return {
        "pending": int(pending or 0),
        "resolved": int(resolved or 0),
        "by_severity": by_severity,
        "newest_pending_at": newest.isoformat() if newest else None,
    }


async def resolve_report(
    db: AsyncSession,
    report_id: str,
    *,
    notes: Optional[str],
    actor: str,
) -> Optional[dict[str, Any]]:
    row = await db.get(ErrorReport, report_id)
    if not row:
        return None
    row.resolved = True
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by = (actor or "desconocido")[:50]
    if notes is not None:
        row.resolution_notes = notes or None
    await db.flush()
    return _serialize(row, detail=True)


async def reopen_report(
    db: AsyncSession,
    report_id: str,
    *,
    actor: str,
) -> Optional[dict[str, Any]]:
    row = await db.get(ErrorReport, report_id)
    if not row:
        return None
    row.resolved = False
    row.resolved_at = None
    row.resolved_by = None
    row.resolution_notes = None
    await db.flush()
    return _serialize(row, detail=True)


async def delete_report(db: AsyncSession, report_id: str) -> bool:
    row = await db.get(ErrorReport, report_id)
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def purge_resolved(db: AsyncSession, *, older_than_days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(older_than_days, 0))
    result = await db.execute(
        delete(ErrorReport)
        .where(ErrorReport.resolved.is_(True), ErrorReport.resolved_at < cutoff)
        .execution_options(synchronize_session=False)
    )
    await db.flush()
    return int(result.rowcount or 0)
