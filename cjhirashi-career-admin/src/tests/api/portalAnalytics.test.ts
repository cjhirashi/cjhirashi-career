import { beforeEach, describe, expect, it, vi } from 'vitest'
import { axiosInstance } from '@/api/client'
import { portalAnalyticsApi, toParams } from '@/api/portalAnalytics'
import type { PortalQuery } from '@/types/portalAnalytics'

vi.mock('@/api/client', () => ({ axiosInstance: { get: vi.fn().mockResolvedValue({ data: { ok: true } }) } }))

const base: PortalQuery = { range: { days: 30 }, compare: 'none', excludeBots: true, excludeOwner: true, filters: {} }

describe('toParams (RF-063 parámetros del servidor)', () => {
  it('un preajuste manda days y deja activos bots y dueño excluidos', () => {
    expect(toParams(base)).toEqual({ exclude_bots: true, exclude_owner: true, days: 30 })
  })

  it('un rango exacto manda since y until, no days', () => {
    const p = toParams({ ...base, range: { since: '2026-10-01', until: '2026-10-31' } })
    expect(p).toMatchObject({ since: '2026-10-01', until: '2026-10-31' })
    expect(p).not.toHaveProperty('days')
  })

  it('los filtros combinables van como un solo JSON y los vacíos se omiten', () => {
    const p = toParams({ ...base, filters: { channel: 'Direct', country: '', device_type: 'mobile' } })
    expect(JSON.parse(p.filters as string)).toEqual({ channel: 'Direct', device_type: 'mobile' })
    expect(toParams({ ...base, filters: { channel: '' } })).not.toHaveProperty('filters')
  })

  it('los interruptores apagados se envían apagados', () => {
    expect(toParams({ ...base, excludeBots: false, excludeOwner: false })).toMatchObject({ exclude_bots: false, exclude_owner: false })
  })
})

describe('portalAnalyticsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  const lastCall = () => vi.mocked(axiosInstance.get).mock.calls.at(-1) as [string, { params: Record<string, unknown> }]

  it('kpis y overview llevan la comparación elegida', async () => {
    await portalAnalyticsApi.kpis({ ...base, compare: 'previous' })
    expect(lastCall()[0]).toBe('/career/portal-metrics/kpis')
    expect(lastCall()[1].params.compare).toBe('previous')
    await portalAnalyticsApi.overview({ ...base, compare: 'year' })
    expect(lastCall()[1].params.compare).toBe('year')
  })

  it('la tendencia semanal no manda compare (el servidor solo lo admite por día)', async () => {
    await portalAnalyticsApi.trend({ ...base, compare: 'previous' }, 'week')
    expect(lastCall()[1].params).toMatchObject({ granularity: 'week' })
    expect(lastCall()[1].params).not.toHaveProperty('compare')
    await portalAnalyticsApi.trend({ ...base, compare: 'previous' }, 'day')
    expect(lastCall()[1].params.compare).toBe('previous')
  })

  it.each([
    ['breakdown', () => portalAnalyticsApi.breakdown(base, 'channel'), '/career/portal-metrics/breakdown', { dimension: 'channel' }],
    ['geo', () => portalAnalyticsApi.geo(base, 'city'), '/career/portal-metrics/geo', { level: 'city' }],
    ['devices', () => portalAnalyticsApi.devices(base, 'browser'), '/career/portal-metrics/devices', { by: 'browser' }],
    ['pages', () => portalAnalyticsApi.pages(base), '/career/portal-metrics/pages', {}],
    ['paths', () => portalAnalyticsApi.paths(base), '/career/portal-metrics/paths', {}],
    ['retention', () => portalAnalyticsApi.retention(base), '/career/portal-metrics/retention', { weeks: 4 }],
    ['goals', () => portalAnalyticsApi.goals(base), '/career/portal-metrics/goals', {}],
    ['funnel', () => portalAnalyticsApi.funnel(base, 'pfn-3'), '/career/portal-metrics/funnel/pfn-3', {}],
  ])('%s llama a su ruta con sus parámetros', async (_name, call, path, extra) => {
    await call()
    expect(lastCall()[0]).toBe(path)
    expect(lastCall()[1].params).toMatchObject({ exclude_bots: true, ...extra })
  })

  it('realtime no depende de filtros ni de rango', async () => {
    await portalAnalyticsApi.realtime()
    expect(lastCall()).toEqual(['/career/portal-metrics/realtime', { params: { minutes: 5 } }])
  })
})
