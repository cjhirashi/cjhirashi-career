import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { portalAnalyticsApi } from '@/api/portalAnalytics'
import { careerQueryKey } from './useCareerResource'
import type { PortalQuery } from '@/types/portalAnalytics'

const key = (name: string, q: PortalQuery | null, extra?: unknown) => careerQueryKey(`portal-analytics-${name}`, { q, extra })

/** Un hook por endpoint. El tablero se refresca solo cada minuto; "ahora" cada 20 s. */
const options = { refetchInterval: 60_000, placeholderData: keepPreviousData }

export const usePortalOverview = (q: PortalQuery) =>
  useQuery({ queryKey: key('overview', q), queryFn: () => portalAnalyticsApi.overview(q), ...options })

export const usePortalKpis = (q: PortalQuery) =>
  useQuery({ queryKey: key('kpis', q), queryFn: () => portalAnalyticsApi.kpis(q), ...options })

export const usePortalTrend = (q: PortalQuery, granularity: 'day' | 'week' | 'month' = 'day') =>
  useQuery({ queryKey: key('trend', q, granularity), queryFn: () => portalAnalyticsApi.trend(q, granularity), ...options })

export const usePortalBreakdown = (q: PortalQuery, dimension: string, enabled = true) =>
  useQuery({ queryKey: key('breakdown', q, dimension), queryFn: () => portalAnalyticsApi.breakdown(q, dimension), enabled, ...options })

export const usePortalGeo = (q: PortalQuery, level: 'country' | 'region' | 'city', enabled = true) =>
  useQuery({ queryKey: key('geo', q, level), queryFn: () => portalAnalyticsApi.geo(q, level), enabled, ...options })

export const usePortalDevices = (q: PortalQuery, by: 'device_type' | 'browser' | 'os' | 'language', enabled = true) =>
  useQuery({ queryKey: key('devices', q, by), queryFn: () => portalAnalyticsApi.devices(q, by), enabled, ...options })

export const usePortalPages = (q: PortalQuery, enabled = true) =>
  useQuery({ queryKey: key('pages', q), queryFn: () => portalAnalyticsApi.pages(q), enabled, ...options })

export const usePortalPaths = (q: PortalQuery) =>
  useQuery({ queryKey: key('paths', q), queryFn: () => portalAnalyticsApi.paths(q), ...options })

export const usePortalRetention = (q: PortalQuery) =>
  useQuery({ queryKey: key('retention', q), queryFn: () => portalAnalyticsApi.retention(q), ...options })

export const usePortalGoals = (q: PortalQuery) =>
  useQuery({ queryKey: key('goals', q), queryFn: () => portalAnalyticsApi.goals(q), ...options })

export const usePortalFunnel = (q: PortalQuery, funnelId: string | null) =>
  useQuery({
    queryKey: key('funnel', q, funnelId),
    queryFn: () => portalAnalyticsApi.funnel(q, funnelId as string),
    enabled: !!funnelId,
    ...options,
  })

export const usePortalRealtime = () =>
  useQuery({ queryKey: key('realtime', null), queryFn: () => portalAnalyticsApi.realtime(), refetchInterval: 20_000 })
