/** Respuestas de `/career/portal-metrics/*` (SPEC-0010). Espejo de `schemas/portal_analytics_metrics.py`. */
import type { ISODate } from './career'

export type CompareMode = 'none' | 'previous' | 'year' | 'weekday'

export interface PortalPeriod {
  since: ISODate
  until: ISODate
}

export interface PortalSampleSize {
  visits: number
  visitors: number
}

export interface PortalKpis {
  visitors: number
  visits: number
  pageviews: number
  pages_per_visit: number | null
  bounce_rate: number | null
  engagement_rate: number | null
  median_active_ms: number | null
  p90_active_ms: number | null
  converted_visits: number
  converting_visitors: number
  conversion_rate: number | null
  new_visitors: number
  returning_visitors: number
}

export interface PortalKpiDelta {
  current: number | null
  previous: number | null
  delta_abs: number | null
  delta_pct: number | null
}

export interface PortalKpisResponse {
  site_id: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  kpis: PortalKpis
  compare: CompareMode | null
  compare_period: PortalPeriod | null
  previous_kpis: PortalKpis | null
  deltas: Record<string, PortalKpiDelta> | null
  filters_applied: Record<string, unknown>
}

export interface PortalTrendPoint {
  bucket: ISODate
  visits: number
  visitors: number
  pageviews: number
  engaged_visits: number
  previous_visits?: number | null
}

export interface PortalAnnotation {
  day: ISODate
  title: string
  kind: 'blog_post' | 'application' | 'deploy' | 'other'
  ref?: string | null
}

export interface PortalTrendResponse {
  site_id: string
  period: PortalPeriod
  granularity: 'day' | 'week' | 'month'
  sample_size: PortalSampleSize
  points: PortalTrendPoint[]
  annotations: PortalAnnotation[]
  /** Primer bucket aún en curso: el tablero lo dibuja punteado. */
  incomplete_from: ISODate | null
}

export interface PortalBreakdownRow {
  key: string | null
  visitors: number
  visits: number
  pageviews: number
  share: number
  bounce_rate: number | null
  median_active_ms: number | null
  converted_visits: number
}

export interface PortalBreakdownResponse {
  site_id: string
  period: PortalPeriod
  dimension: string
  sample_size: PortalSampleSize
  rows: PortalBreakdownRow[]
}

export interface PortalPageRow {
  page: string
  pageviews: number
  visitors: number
  entries: number
  exits: number
  exit_rate: number | null
  median_active_ms: number | null
  avg_max_scroll_pct: number | null
}

export interface PortalPagesResponse {
  site_id: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  rows: PortalPageRow[]
}

export interface PortalPathRow {
  from_page: string
  to_page: string
  count: number
}

export interface PortalPathsResponse {
  site_id: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  rows: PortalPathRow[]
}

export interface PortalRetentionRow {
  cohort_week: ISODate
  size: number
  active_by_week: number[]
}

export interface PortalRetentionResponse {
  site_id: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  rows: PortalRetentionRow[]
}

export interface PortalRealtimeResponse {
  site_id: string
  window_minutes: number
  visitors_now: number
  top_pages: { page: string; visitors: number }[]
  generated_at: string
}

export interface PortalGoalRow {
  goal_id: string
  name: string
  type: string
  is_key_event: boolean
  converted_visits: number
  converting_visitors: number
  conversion_rate: number | null
}

export interface PortalGoalsResponse {
  site_id: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  rows: PortalGoalRow[]
}

export interface PortalFunnelStepRow {
  label: string
  visits: number
  from_previous: number | null
  from_start: number | null
}

export interface PortalFunnelResponse {
  site_id: string
  funnel_id: string
  name: string
  period: PortalPeriod
  sample_size: PortalSampleSize
  steps: PortalFunnelStepRow[]
}

export interface PortalFunnelDefinition {
  id: string
  name: string
}

/** Cortes combinables; las claves son las de `FILTERABLE` en el servidor. */
export type PortalFilters = Partial<Record<'channel' | 'country' | 'device_type', string>>

/** Rango: un preajuste en días, o fechas exactas (zona horaria del sitio). */
export type PortalRange = { days: number } | { since: ISODate; until: ISODate }

export interface PortalQuery {
  range: PortalRange
  compare: CompareMode
  excludeBots: boolean
  excludeOwner: boolean
  filters: PortalFilters
}
