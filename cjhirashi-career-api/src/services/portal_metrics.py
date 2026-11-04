"""
Motor de métricas de la analítica del portafolio (SPEC-0010).

Todas las consultas parten de un único constructor de filtros (`MetricsQuery`)
para que cualquier métrica excluya bots y visitas propias igual y aplique los
mismos cortes. Las definiciones viven en `DICTIONARY` y se exponen por API.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import and_, distinct, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.portal_annotation import PortalAnnotation
from models.portal_daily import PortalDaily
from models.portal_event import PortalEvent
from models.portal_funnel import PortalFunnel
from models.portal_goal import PortalGoal
from models.portal_site import PortalSite
from models.portal_visit import PortalVisit
from models.portal_visitor import PortalVisitor

# Cortes por columna de visita que acepta el parámetro `filters`.
FILTERABLE = {
    "channel": PortalVisit.channel,
    "source": PortalVisit.source,
    "referrer_domain": PortalVisit.referrer_domain,
    "country": PortalVisit.country,
    "region": PortalVisit.region,
    "city": PortalVisit.city,
    "device_type": PortalVisit.device_type,
    "browser": PortalVisit.browser,
    "os": PortalVisit.os,
    "language": PortalVisit.language,
    "utm_campaign": PortalVisit.utm_campaign,
    "utm_source": PortalVisit.utm_source,
    "utm_medium": PortalVisit.utm_medium,
    "application_id": PortalVisit.application_id,
    "entry_page": PortalVisit.entry_page,
    "exit_page": PortalVisit.exit_page,
    "is_new_visitor": PortalVisit.is_new_visitor,
    "converted": PortalVisit.converted,
}

MAX_ACTIVE_MS = 30 * 60 * 1000

DICTIONARY: Dict[str, Any] = {
    "visitor": "Visitante distinto por `visitor_key` (id aleatorio del navegador, sin IP). Quien bloquea el almacenamiento cuenta como un visitante por pestaña.",
    "visit": "Secuencia de eventos del mismo visitante con huecos menores a 30 minutos. Los avisos pasivos de salida se adjuntan a la visita anterior hasta 24 h después.",
    "pageviews": "Páginas cargadas. `pages_per_visit` = vistas / visitas.",
    "engaged_visit": "Visita comprometida: más de 10 s de tiempo activo, o 2 o más vistas de página, o un evento clave (meta con `is_key_event`).",
    "bounce_rate": "Visitas no comprometidas / visitas.",
    "engagement_rate": "Visitas comprometidas / visitas.",
    "active_time": "Tiempo con la pestaña visible; por página se topa en 30 min. Se reporta mediana y p90 por visita, nunca promedio. Las visitas sin aviso de salida cuentan 0.",
    "conversion_rate": "Visitantes distintos con una visita convertida / visitantes distintos.",
    "new_vs_returning": "Visitante nuevo: su primera visita cae en el periodo (`is_new_visitor`). Recurrente: el resto.",
    "channels": "Direct, Organic Search, Organic Social, Email, Referral, Paid, Application (UTM de postulación) y Unknown, derivados con `portal_channel_rules`. El referrer crudo se conserva para reclasificar.",
    "clean_traffic": "Tráfico limpio = `is_bot` falso y `is_owner` falso. Es el predeterminado de toda consulta (`exclude_bots`, `exclude_owner`).",
    "sample_size": "Toda respuesta agregada trae visitas y visitantes que la sustentan. Con muestras pequeñas, no concluyas de porcentajes.",
    "legacy": "Los visitantes con `legacy=true` se reconstruyeron de eventos v1: no tienen origen, dispositivo ni tiempo activo fiable.",
    "timezone": "Los días se cortan en la zona horaria del sitio (por defecto America/Mexico_City).",
}


@dataclass
class MetricsQuery:
    user_id: str
    site: PortalSite
    since: date
    until: date
    exclude_bots: bool = True
    exclude_owner: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.site.timezone or "America/Mexico_City")

    @property
    def start(self) -> datetime:
        return datetime.combine(self.since, datetime.min.time(), tzinfo=self.tz)

    @property
    def end(self) -> datetime:
        return datetime.combine(self.until + timedelta(days=1), datetime.min.time(), tzinfo=self.tz)

    @property
    def days(self) -> int:
        return (self.until - self.since).days + 1

    def shifted(self, since: date, until: date) -> "MetricsQuery":
        return MetricsQuery(self.user_id, self.site, since, until, self.exclude_bots, self.exclude_owner, self.filters)

    def visit_conditions(self) -> List[Any]:
        conds: List[Any] = [
            PortalVisit.user_id == self.user_id,
            PortalVisit.site_id == self.site.id,
            PortalVisit.started_at >= self.start,
            PortalVisit.started_at < self.end,
        ]
        if self.exclude_bots:
            conds.append(PortalVisit.is_bot.is_(False))
        if self.exclude_owner:
            conds.append(PortalVisit.is_owner.is_(False))
        for name, value in self.filters.items():
            column = FILTERABLE.get(name)
            if column is None:
                raise ValueError(f"Filtro desconocido: {name}. Válidos: {', '.join(sorted(FILTERABLE))}")
            conds.append(column.in_(value) if isinstance(value, list) else column == value)
        return conds

    def visit_ids(self):
        return select(PortalVisit.id).where(*self.visit_conditions())


def compare_period(q: MetricsQuery, mode: str) -> Optional[tuple]:
    """Periodo comparado: `previous` (mismo largo, justo antes), `year` (un año atrás),
    `weekday` (corrido en semanas completas para que coincidan los días de la semana)."""
    if mode in (None, "", "none"):
        return None
    if mode == "previous":
        return q.since - timedelta(days=q.days), q.since - timedelta(days=1)
    if mode == "year":
        def back(d: date) -> date:
            try:
                return d.replace(year=d.year - 1)
            except ValueError:  # 29 de febrero
                return d.replace(year=d.year - 1, day=28)
        return back(q.since), back(q.until)
    if mode == "weekday":
        weeks = -(-q.days // 7)
        shift = timedelta(days=7 * weeks)
        return q.since - shift, q.until - shift
    raise ValueError("compare debe ser none, previous, year o weekday")


def _ratio(num: Optional[int], den: Optional[int]) -> Optional[float]:
    return round(num / den, 4) if den else None


def _int(value: Any) -> Optional[int]:
    return None if value is None else int(round(float(value)))


async def resolve_site(db: AsyncSession, user_id: str, site_id: Optional[str]) -> Optional[PortalSite]:
    stmt = select(PortalSite).where(PortalSite.user_id == user_id)
    stmt = stmt.where(PortalSite.id == site_id) if site_id else stmt.where(PortalSite.active.is_(True)).order_by(PortalSite.created_at)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


async def sample_size(db: AsyncSession, q: MetricsQuery) -> Dict[str, int]:
    row = (
        await db.execute(
            select(func.count(), func.count(distinct(PortalVisit.visitor_id))).where(*q.visit_conditions())
        )
    ).one()
    return {"visits": row[0], "visitors": row[1]}


async def kpis(db: AsyncSession, q: MetricsQuery) -> Dict[str, Any]:
    v = PortalVisit
    row = (
        await db.execute(
            select(
                func.count(distinct(v.visitor_id)),
                func.count(),
                func.coalesce(func.sum(v.pageviews), 0),
                func.count().filter(v.is_bounce.is_(True)),
                func.count().filter(v.is_engaged.is_(True)),
                func.percentile_cont(0.5).within_group(v.active_ms),
                func.percentile_cont(0.9).within_group(v.active_ms),
                func.count().filter(v.converted.is_(True)),
                func.count(distinct(v.visitor_id)).filter(v.converted.is_(True)),
                func.count(distinct(v.visitor_id)).filter(v.is_new_visitor.is_(True)),
            ).where(*q.visit_conditions())
        )
    ).one()
    visitors, visits, pageviews, bounces, engaged, median, p90, converted, converting, new = row
    return {
        "visitors": visitors,
        "visits": visits,
        "pageviews": int(pageviews),
        "pages_per_visit": round(pageviews / visits, 2) if visits else None,
        "bounce_rate": _ratio(bounces, visits),
        "engagement_rate": _ratio(engaged, visits),
        "median_active_ms": _int(median),
        "p90_active_ms": _int(p90),
        "converted_visits": converted,
        "converting_visitors": converting,
        "conversion_rate": _ratio(converting, visitors),
        "new_visitors": new,
        "returning_visitors": visitors - new,
    }


def deltas(current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Dict[str, Optional[float]]]:
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for key, cur in current.items():
        prev = previous.get(key)
        if cur is None or prev is None:
            out[key] = {"current": cur, "previous": prev, "delta_abs": None, "delta_pct": None}
            continue
        out[key] = {
            "current": cur,
            "previous": prev,
            "delta_abs": round(cur - prev, 4),
            "delta_pct": round((cur - prev) / prev, 4) if prev else None,
        }
    return out


async def breakdown(db: AsyncSession, q: MetricsQuery, dimension: str, limit: int = 50) -> List[Dict[str, Any]]:
    column = FILTERABLE.get(dimension)
    if column is None:
        raise ValueError(f"Dimensión desconocida: {dimension}. Válidas: {', '.join(sorted(FILTERABLE))}")
    v = PortalVisit
    rows = (
        await db.execute(
            select(
                column,
                func.count(distinct(v.visitor_id)),
                func.count(),
                func.coalesce(func.sum(v.pageviews), 0),
                func.count().filter(v.is_bounce.is_(True)),
                func.percentile_cont(0.5).within_group(v.active_ms),
                func.count().filter(v.converted.is_(True)),
            )
            .where(*q.visit_conditions())
            .group_by(column)
            .order_by(func.count().desc(), column)
            .limit(limit)
        )
    ).all()
    total = sum(r[2] for r in rows) or 1
    return [
        {
            "key": None if key is None else str(key),
            "visitors": visitors,
            "visits": visits,
            "pageviews": int(pageviews),
            "share": round(visits / total, 4),
            "bounce_rate": _ratio(bounces, visits),
            "median_active_ms": _int(median),
            "converted_visits": converted,
        }
        for key, visitors, visits, pageviews, bounces, median, converted in rows
    ]


async def pages(db: AsyncSession, q: MetricsQuery, limit: int = 50) -> List[Dict[str, Any]]:
    e = PortalEvent
    in_scope = e.visit_id.in_(q.visit_ids())
    view_rows = (
        await db.execute(
            select(e.page, func.count(), func.count(distinct(e.visitor_id)))
            .where(in_scope, e.event_type == "pageview")
            .group_by(e.page)
            .order_by(func.count().desc(), e.page)
            .limit(limit)
        )
    ).all()
    names = [r[0] for r in view_rows]
    if not names:
        return []

    entries = dict(
        (await db.execute(
            select(PortalVisit.entry_page, func.count()).where(*q.visit_conditions(), PortalVisit.entry_page.in_(names)).group_by(PortalVisit.entry_page)
        )).all()
    )
    exits = dict(
        (await db.execute(
            select(PortalVisit.exit_page, func.count()).where(*q.visit_conditions(), PortalVisit.exit_page.in_(names)).group_by(PortalVisit.exit_page)
        )).all()
    )
    time_col = func.least(func.coalesce(e.active_ms, e.duration_ms), MAX_ACTIVE_MS)
    medians = dict(
        (await db.execute(
            select(e.page, func.percentile_cont(0.5).within_group(time_col))
            .where(in_scope, e.event_type.in_(["page_duration", "page_leave"]), e.page.in_(names),
                   func.coalesce(e.active_ms, e.duration_ms).is_not(None))
            .group_by(e.page)
        )).all()
    )
    per_visit_scroll = (
        select(e.page.label("page"), func.max(e.scroll_pct).label("max_scroll"))
        .where(in_scope, e.scroll_pct.is_not(None), e.page.in_(names))
        .group_by(e.visit_id, e.page)
        .subquery()
    )
    scrolls = dict(
        (await db.execute(select(per_visit_scroll.c.page, func.avg(per_visit_scroll.c.max_scroll)).group_by(per_visit_scroll.c.page))).all()
    )
    return [
        {
            "page": page,
            "pageviews": views,
            "visitors": visitors,
            "entries": entries.get(page, 0),
            "exits": exits.get(page, 0),
            "exit_rate": _ratio(exits.get(page, 0), views),
            "median_active_ms": _int(medians.get(page)),
            "avg_max_scroll_pct": round(float(scrolls[page]), 1) if scrolls.get(page) is not None else None,
        }
        for page, views, visitors in view_rows
    ]


async def paths(db: AsyncSession, q: MetricsQuery, limit: int = 30) -> List[Dict[str, Any]]:
    e = PortalEvent
    prev = func.lag(e.page).over(partition_by=e.visit_id, order_by=(e.seq, e.id))
    inner = (
        select(e.page.label("page"), prev.label("prev_page"))
        .where(e.visit_id.in_(q.visit_ids()), e.event_type == "pageview")
        .subquery()
    )
    rows = (
        await db.execute(
            select(inner.c.prev_page, inner.c.page, func.count())
            .where(inner.c.prev_page.is_not(None), inner.c.prev_page != inner.c.page)
            .group_by(inner.c.prev_page, inner.c.page)
            .order_by(func.count().desc(), inner.c.prev_page, inner.c.page)
            .limit(limit)
        )
    ).all()
    return [{"from_page": a, "to_page": b, "count": c} for a, b, c in rows]


async def retention(db: AsyncSession, q: MetricsQuery, weeks: int = 4) -> List[Dict[str, Any]]:
    tz = q.site.timezone or "America/Mexico_City"
    vr, vi = PortalVisitor, PortalVisit
    first_week = func.date_trunc("week", func.timezone(tz, vr.first_seen)).label("cohort")
    cohorts = (
        select(vr.id.label("visitor_id"), first_week)
        .where(vr.user_id == q.user_id, vr.site_id == q.site.id, vr.first_seen >= q.start, vr.first_seen < q.end,
               *( [vr.is_bot.is_(False)] if q.exclude_bots else [] ),
               *( [vr.is_owner.is_(False)] if q.exclude_owner else [] ))
        .subquery()
    )
    activity = (
        select(vi.visitor_id.label("visitor_id"), func.date_trunc("week", func.timezone(tz, vi.started_at)).label("wk"))
        .where(vi.user_id == q.user_id, vi.site_id == q.site.id)
        .distinct()
        .subquery()
    )
    offset = func.floor(func.extract("epoch", activity.c.wk - cohorts.c.cohort) / (7 * 86400)).label("n")
    rows = (
        await db.execute(
            select(cohorts.c.cohort, offset, func.count(distinct(cohorts.c.visitor_id)))
            .join(activity, activity.c.visitor_id == cohorts.c.visitor_id)
            .group_by(cohorts.c.cohort, offset)
            .order_by(cohorts.c.cohort)
        )
    ).all()
    grid: Dict[date, List[int]] = {}
    for cohort, n, count in rows:
        n = int(n)
        if 0 <= n <= weeks:
            grid.setdefault(cohort.date(), [0] * (weeks + 1))[n] = count
    return [{"cohort_week": week, "size": counts[0], "active_by_week": counts} for week, counts in sorted(grid.items())]


async def realtime(db: AsyncSession, user_id: str, site: PortalSite, minutes: int = 5) -> Dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    base = [PortalVisit.user_id == user_id, PortalVisit.site_id == site.id, PortalVisit.last_activity_at >= since,
            PortalVisit.is_bot.is_(False), PortalVisit.is_owner.is_(False)]
    visitors = (await db.execute(select(func.count(distinct(PortalVisit.visitor_id))).where(*base))).scalar_one()
    top = (
        await db.execute(
            select(PortalVisit.exit_page, func.count()).where(*base).group_by(PortalVisit.exit_page).order_by(func.count().desc()).limit(10)
        )
    ).all()
    return {
        "site_id": site.id,
        "window_minutes": minutes,
        "visitors_now": visitors,
        "top_pages": [{"page": page, "visitors": n} for page, n in top],
        "generated_at": datetime.now(timezone.utc),
    }


def event_condition(step_type: str, match: Dict[str, Any]):
    """Condición SQL sobre un evento para una meta o paso de embudo; None si no aplica a eventos."""
    e = PortalEvent
    if step_type == "event":
        return e.event_type == match.get("event_type")
    if step_type == "outbound":
        needle = str(match.get("url_contains", "")).lower()
        return and_(e.event_type == "outbound", func.lower(e.target_url).contains(needle, autoescape=True))
    if step_type == "page":
        return and_(e.event_type == "pageview", e.page.startswith(str(match.get("path_prefix", "")), autoescape=True))
    return None


async def goals(db: AsyncSession, q: MetricsQuery) -> List[Dict[str, Any]]:
    goal_rows = (
        await db.execute(
            select(PortalGoal).where(PortalGoal.user_id == q.user_id, PortalGoal.site_id == q.site.id).order_by(PortalGoal.created_at, PortalGoal.id)
        )
    ).scalars().all()
    total_visitors = (await sample_size(db, q))["visitors"]
    out = []
    for goal in goal_rows:
        condition = event_condition(goal.type, goal.match or {})
        if condition is not None:
            stmt = (
                select(func.count(distinct(PortalEvent.visit_id)), func.count(distinct(PortalEvent.visitor_id)))
                .where(PortalEvent.visit_id.in_(q.visit_ids()), condition)
            )
        elif goal.type == "min_active":
            stmt = select(func.count(), func.count(distinct(PortalVisit.visitor_id))).where(
                *q.visit_conditions(), PortalVisit.active_ms >= int((goal.match or {}).get("ms", 0)))
        elif goal.type == "min_pages":
            stmt = select(func.count(), func.count(distinct(PortalVisit.visitor_id))).where(
                *q.visit_conditions(), PortalVisit.pageviews >= int((goal.match or {}).get("pages", 0)))
        else:
            continue
        visits, visitors = (await db.execute(stmt)).one()
        out.append({
            "goal_id": goal.id, "name": goal.name, "type": goal.type, "is_key_event": goal.is_key_event,
            "converted_visits": visits, "converting_visitors": visitors,
            "conversion_rate": _ratio(visitors, total_visitors),
        })
    return out


async def funnel(db: AsyncSession, q: MetricsQuery, definition: PortalFunnel) -> List[Dict[str, Any]]:
    """Visitas que completan cada paso EN ORDEN (cada paso con `seq` mayor que el anterior)."""
    e = PortalEvent
    steps = definition.steps or []
    previous = None
    counts: List[int] = []
    for step in steps:
        condition = event_condition(step.get("type"), step.get("match") or {})
        if condition is None:
            raise ValueError(f"Paso de embudo no válido: {step.get('label')}")
        stmt = select(e.visit_id.label("visit_id"), func.min(e.seq).label("s")).where(e.visit_id.in_(q.visit_ids()), condition)
        if previous is not None:
            stmt = stmt.where(e.visit_id == previous.c.visit_id, e.seq > previous.c.s)
        previous = stmt.group_by(e.visit_id).cte(f"step_{len(counts) + 1}")
        counts.append((await db.execute(select(func.count()).select_from(previous))).scalar_one())
    first = counts[0] if counts else 0
    return [
        {
            "label": step.get("label"),
            "visits": count,
            "from_previous": _ratio(count, counts[i - 1]) if i else None,
            "from_start": _ratio(count, first),
        }
        for i, (step, count) in enumerate(zip(steps, counts))
    ]


async def trend(db: AsyncSession, q: MetricsQuery, granularity: str = "day") -> List[Dict[str, Any]]:
    if granularity not in ("day", "week", "month"):
        raise ValueError("granularity debe ser day, week o month")
    if granularity == "day" and not q.filters and q.exclude_bots and q.exclude_owner:
        return await _daily_trend(db, q)
    tz = q.site.timezone or "America/Mexico_City"
    bucket = func.date_trunc(granularity, func.timezone(tz, PortalVisit.started_at)).label("bucket")
    rows = (
        await db.execute(
            select(bucket, func.count(), func.count(distinct(PortalVisit.visitor_id)), func.coalesce(func.sum(PortalVisit.pageviews), 0),
                   func.count().filter(PortalVisit.is_engaged.is_(True)))
            .where(*q.visit_conditions())
            .group_by(bucket)
            .order_by(bucket)
        )
    ).all()
    found = {r[0].date(): r for r in rows}
    points: List[Dict[str, Any]] = []
    if granularity == "day":
        day = q.since
        while day <= q.until:
            r = found.get(day)
            points.append({"bucket": day, "visits": r[1] if r else 0, "visitors": r[2] if r else 0,
                           "pageviews": int(r[3]) if r else 0, "engaged_visits": r[4] if r else 0})
            day += timedelta(days=1)
    else:
        for key in sorted(found):
            r = found[key]
            points.append({"bucket": key, "visits": r[1], "visitors": r[2], "pageviews": int(r[3]), "engaged_visits": r[4]})
    return points


async def _daily_trend(db: AsyncSession, q: MetricsQuery) -> List[Dict[str, Any]]:
    """Tendencia diaria: días cerrados desde `portal_daily` (recalculada si quedó vieja), hoy desde el crudo."""
    await ensure_daily_fresh(db, q)
    today = datetime.now(q.tz).date()
    rows = (
        await db.execute(
            select(PortalDaily).where(PortalDaily.site_id == q.site.id, PortalDaily.dimension == "total",
                                      PortalDaily.day >= q.since, PortalDaily.day <= q.until)
        )
    ).scalars().all()
    closed = {r.day: r for r in rows}
    live: Dict[date, Dict[str, int]] = {}
    if q.until >= today >= q.since:
        today_row = (
            await db.execute(
                select(func.count(distinct(PortalVisit.visitor_id)), func.count(), func.coalesce(func.sum(PortalVisit.pageviews), 0),
                       func.count().filter(PortalVisit.is_engaged.is_(True)))
                .where(*q.shifted(today, today).visit_conditions())
            )
        ).one()
        live[today] = {"visitors": today_row[0], "visits": today_row[1], "pageviews": int(today_row[2]), "engaged_visits": today_row[3]}
    points: List[Dict[str, Any]] = []
    day = q.since
    while day <= q.until:
        if day in live:
            points.append({"bucket": day, **live[day]})
        elif day in closed:
            r = closed[day]
            points.append({"bucket": day, "visits": r.visits, "visitors": r.visitors, "pageviews": r.pageviews, "engaged_visits": r.engaged_visits})
        else:
            points.append({"bucket": day, "visits": 0, "visitors": 0, "pageviews": 0, "engaged_visits": 0})
        day += timedelta(days=1)
    return points


async def annotations(db: AsyncSession, q: MetricsQuery) -> List[Dict[str, Any]]:
    rows = (
        await db.execute(
            select(PortalAnnotation).where(PortalAnnotation.user_id == q.user_id, PortalAnnotation.site_id == q.site.id,
                                           PortalAnnotation.day >= q.since, PortalAnnotation.day <= q.until).order_by(PortalAnnotation.day)
        )
    ).scalars().all()
    return [{"id": a.id, "day": a.day, "title": a.title, "kind": a.kind, "ref": a.ref} for a in rows]


# ----------------------------------------------------------------------------
# Resumen diario (derivado, recalculable): solo tráfico limpio.
# ----------------------------------------------------------------------------
DAILY_DIMENSIONS = {
    "channel": PortalVisit.channel,
    "source": PortalVisit.source,
    "country": PortalVisit.country,
    "device": PortalVisit.device_type,
    "entry_page": PortalVisit.entry_page,
    "campaign": PortalVisit.utm_campaign,
}


async def rebuild_daily(db: AsyncSession, user_id: str, site: PortalSite, since: date, until: date) -> Dict[str, int]:
    """Recalcula `portal_daily` para [since, until]. Borra y reescribe esos días."""
    q = MetricsQuery(user_id, site, since, until)
    tz = site.timezone or "America/Mexico_City"
    day_col = func.date_trunc("day", func.timezone(tz, PortalVisit.started_at)).label("day")
    v = PortalVisit
    aggregates = (
        func.count(distinct(v.visitor_id)), func.count(), func.coalesce(func.sum(v.pageviews), 0),
        func.count().filter(v.is_engaged.is_(True)), func.count().filter(v.is_bounce.is_(True)),
        func.coalesce(func.sum(v.active_ms), 0), func.count().filter(v.converted.is_(True)),
    )

    await db.execute(
        PortalDaily.__table__.delete().where(PortalDaily.site_id == site.id, PortalDaily.day >= since, PortalDaily.day <= until)
    )
    now = datetime.now(timezone.utc)
    written = 0
    days_with_data = set()

    async def write(dimension: str, key_col) -> None:
        nonlocal written
        cols = [day_col, *aggregates] if key_col is None else [day_col, key_col, *aggregates]
        stmt = select(*cols).where(*q.visit_conditions()).group_by(day_col, *([] if key_col is None else [key_col]))
        for row in (await db.execute(stmt)).all():
            day = row[0].date()
            key = "all" if key_col is None else row[1]
            values = row[1:] if key_col is None else row[2:]
            if key is None:
                key = "(desconocido)"
            visitors, visits, pageviews, engaged, bounces, active, conversions = values
            db.add(PortalDaily(
                user_id=user_id, site_id=site.id, day=day, dimension=dimension, key=str(key)[:255],
                visitors=visitors, visits=visits, pageviews=int(pageviews), engaged_visits=engaged, bounces=bounces,
                active_ms_sum=int(active), conversions=conversions, computed_at=now,
            ))
            days_with_data.add(day)
            written += 1

    await write("total", None)
    for dimension, column in DAILY_DIMENSIONS.items():
        await write(dimension, column)

    # Páginas vistas por página y día (eventos de visitas limpias).
    e = PortalEvent
    page_day = func.date_trunc("day", func.timezone(tz, e.created_at)).label("day")
    page_rows = (
        await db.execute(
            select(page_day, e.page, func.count(distinct(e.visitor_id)), func.count())
            .where(e.visit_id.in_(q.visit_ids()), e.event_type == "pageview")
            .group_by(page_day, e.page)
        )
    ).all()
    for day_ts, page, visitors, views in page_rows:
        day = day_ts.date()
        if since <= day <= until:
            db.add(PortalDaily(user_id=user_id, site_id=site.id, day=day, dimension="page", key=str(page)[:255],
                               visitors=visitors, visits=0, pageviews=views, engaged_visits=0, bounces=0,
                               active_ms_sum=0, conversions=0, computed_at=now))
            written += 1
    await db.flush()
    return {"days_recomputed": (until - since).days + 1, "rows_written": written}


async def ensure_daily_fresh(db: AsyncSession, q: MetricsQuery) -> int:
    """Recalcula los días CERRADOS del rango cuyo resumen falta o quedó viejo respecto de las visitas."""
    tz = q.site.timezone or "America/Mexico_City"
    today = datetime.now(q.tz).date()
    last = min(q.until, today - timedelta(days=1))
    if last < q.since:
        return 0
    day_col = func.date_trunc("day", func.timezone(tz, PortalVisit.started_at))
    activity = dict(
        (await db.execute(
            select(day_col, func.max(PortalVisit.updated_at)).where(
                PortalVisit.user_id == q.user_id, PortalVisit.site_id == q.site.id,
                PortalVisit.started_at >= q.start, PortalVisit.started_at < q.end)
            .group_by(day_col)
        )).all()
    )
    computed = dict(
        (await db.execute(
            select(PortalDaily.day, func.min(PortalDaily.computed_at)).where(
                PortalDaily.site_id == q.site.id, PortalDaily.dimension == "total",
                PortalDaily.day >= q.since, PortalDaily.day <= last).group_by(PortalDaily.day)
        )).all()
    )
    stale = sorted(d.date() for d, updated in activity.items()
                   if d.date() <= last and (computed.get(d.date()) is None or computed[d.date()] < updated))
    if not stale:
        return 0
    # Recalcula en un solo tramo continuo: simple y suficiente a esta escala.
    await rebuild_daily(db, q.user_id, q.site, stale[0], stale[-1])
    await db.commit()  # el resumen es caché derivada: se conserva entre peticiones
    return len(stale)
