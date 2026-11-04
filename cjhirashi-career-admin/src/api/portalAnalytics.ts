import { axiosInstance } from './client'
import type {
  PortalBreakdownResponse,
  PortalFunnelResponse,
  PortalGoalsResponse,
  PortalKpisResponse,
  PortalPagesResponse,
  PortalPathsResponse,
  PortalQuery,
  PortalRealtimeResponse,
  PortalRetentionResponse,
  PortalTrendResponse,
} from '@/types/portalAnalytics'
import type { PortalMetricsOverview } from '@/types/career'

const BASE = '/career/portal-metrics'

/** Parámetros comunes de todo endpoint de métricas (los nombres son los del servidor). */
export const toParams = (q: PortalQuery, extra: Record<string, unknown> = {}): Record<string, unknown> => {
  const params: Record<string, unknown> = {
    exclude_bots: q.excludeBots,
    exclude_owner: q.excludeOwner,
    ...('days' in q.range ? { days: q.range.days } : { since: q.range.since, until: q.range.until }),
    ...extra,
  }
  const filters = Object.fromEntries(Object.entries(q.filters).filter(([, value]) => value))
  if (Object.keys(filters).length > 0) params.filters = JSON.stringify(filters)
  return params
}

const get = async <T>(path: string, params: Record<string, unknown>): Promise<T> =>
  (await axiosInstance.get<T>(`${BASE}${path}`, { params })).data

export const portalAnalyticsApi = {
  overview: (q: PortalQuery) => get<PortalMetricsOverview>('/overview', toParams(q, { compare: q.compare })),
  kpis: (q: PortalQuery) => get<PortalKpisResponse>('/kpis', toParams(q, { compare: q.compare })),
  trend: (q: PortalQuery, granularity: 'day' | 'week' | 'month' = 'day') =>
    get<PortalTrendResponse>('/trend', toParams(q, { granularity, ...(granularity === 'day' ? { compare: q.compare } : {}) })),
  breakdown: (q: PortalQuery, dimension: string, limit = 10) =>
    get<PortalBreakdownResponse>('/breakdown', toParams(q, { dimension, limit })),
  geo: (q: PortalQuery, level: 'country' | 'region' | 'city', limit = 10) =>
    get<PortalBreakdownResponse>('/geo', toParams(q, { level, limit })),
  devices: (q: PortalQuery, by: 'device_type' | 'browser' | 'os' | 'language', limit = 10) =>
    get<PortalBreakdownResponse>('/devices', toParams(q, { by, limit })),
  pages: (q: PortalQuery, limit = 15) => get<PortalPagesResponse>('/pages', toParams(q, { limit })),
  paths: (q: PortalQuery, limit = 10) => get<PortalPathsResponse>('/paths', toParams(q, { limit })),
  retention: (q: PortalQuery, weeks = 4) => get<PortalRetentionResponse>('/retention', toParams(q, { weeks })),
  goals: (q: PortalQuery) => get<PortalGoalsResponse>('/goals', toParams(q)),
  funnel: (q: PortalQuery, funnelId: string) => get<PortalFunnelResponse>(`/funnel/${funnelId}`, toParams(q)),
  realtime: (minutes = 5) => get<PortalRealtimeResponse>('/realtime', { minutes }),
}
