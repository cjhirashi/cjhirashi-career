import type React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render as baseRender, screen, waitFor, fireEvent, within } from '../utils'
import { MetricsPage } from '@/pages/MetricsPage'
import { portalAnalyticsApi } from '@/api/portalAnalytics'
import { careerApi } from '@/api/career'
import type { PortalKpis, PortalKpisResponse, PortalQuery, PortalTrendResponse } from '@/types/portalAnalytics'

vi.mock('@/api/portalAnalytics', async (original) => ({
  ...(await original<typeof import('@/api/portalAnalytics')>()),
  portalAnalyticsApi: {
    overview: vi.fn(), kpis: vi.fn(), trend: vi.fn(), breakdown: vi.fn(), geo: vi.fn(), devices: vi.fn(),
    pages: vi.fn(), paths: vi.fn(), retention: vi.fn(), goals: vi.fn(), funnel: vi.fn(), realtime: vi.fn(),
  },
}))
vi.mock('@/api/career')

const api = vi.mocked(portalAnalyticsApi)
const period = { since: '2026-10-05', until: '2026-11-03' }
const sample = { visits: 54, visitors: 52 }

const kpiValues: PortalKpis = {
  visitors: 52, visits: 54, pageviews: 63, pages_per_visit: 1.17, bounce_rate: 0.9444, engagement_rate: 0.0556,
  median_active_ms: 9778, p90_active_ms: 231176, converted_visits: 0, converting_visitors: 0, conversion_rate: 0,
  new_visitors: 52, returning_visitors: 0,
}
const kpisResponse = (over: Partial<PortalKpisResponse> = {}): PortalKpisResponse => ({
  site_id: 'psi-1', period, sample_size: sample, kpis: kpiValues, compare: null, compare_period: null,
  previous_kpis: null, deltas: null, filters_applied: {}, ...over,
})
const trendResponse: PortalTrendResponse = {
  site_id: 'psi-1', period, granularity: 'day', sample_size: sample, incomplete_from: '2026-11-03',
  points: [
    { bucket: '2026-11-01', visits: 5, visitors: 5, pageviews: 6, engaged_visits: 1, previous_visits: 3 },
    { bucket: '2026-11-02', visits: 7, visitors: 6, pageviews: 8, engaged_visits: 2, previous_visits: 4 },
    { bucket: '2026-11-03', visits: 2, visitors: 2, pageviews: 2, engaged_visits: 0, previous_visits: 5 },
  ],
  annotations: [{ day: '2026-11-02', title: 'Nuevo post del blog', kind: 'blog_post' }],
}
const breakdown = (dimension: string, keys: string[]) => ({
  site_id: 'psi-1', period, dimension, sample_size: sample,
  rows: keys.map((key, i) => ({ key, visitors: 10 - i, visits: 10 - i, pageviews: 12, share: 0.5, bounce_rate: 0.8, median_active_ms: 5000, converted_visits: 0 })),
})
const empty = { site_id: 'psi-1', period, sample_size: sample, rows: [] }

const render = (ui: React.ReactElement) => baseRender(<MemoryRouter>{ui}</MemoryRouter>)

const lastQuery = (fn: unknown): PortalQuery => (fn as ReturnType<typeof vi.fn>).mock.calls.at(-1)![0]

beforeEach(() => {
  vi.clearAllMocks()
  api.kpis.mockImplementation(async (q) => kpisResponse({ sample_size: q.excludeBots ? sample : { visits: 60, visitors: 57 } }))
  api.trend.mockResolvedValue(trendResponse)
  api.overview.mockResolvedValue({ visits_by_location: [{ city: 'Celaya', country: 'Mexico', latitude: 20.5, longitude: -100.8, count: 5 }] } as never)
  api.breakdown.mockImplementation(async (_q, d) => breakdown(d, d === 'channel' ? ['Direct', 'Organic Search'] : d === 'country' ? ['Mexico', 'Spain'] : ['desktop', 'mobile']))
  api.geo.mockResolvedValue(breakdown('country', ['Mexico']))
  api.devices.mockResolvedValue(breakdown('device_type', ['desktop']))
  api.pages.mockResolvedValue({ ...empty, rows: [{ page: '/projects', pageviews: 20, visitors: 15, entries: 4, exits: 6, exit_rate: 0.3, median_active_ms: 12000, avg_max_scroll_pct: 61.5 }] })
  api.paths.mockResolvedValue({ ...empty, rows: [{ from_page: '/', to_page: '/projects', count: 9 }] })
  api.retention.mockResolvedValue({ ...empty, rows: [{ cohort_week: '2026-10-26', size: 10, active_by_week: [10, 3] }] })
  api.goals.mockResolvedValue({ ...empty, rows: [{ goal_id: 'pgl-1', name: 'cv_download', type: 'event', is_key_event: true, converted_visits: 4, converting_visitors: 4, conversion_rate: 0.08 }] })
  api.funnel.mockResolvedValue({ site_id: 'psi-1', funnel_id: 'pfn-1', name: 'CV', period, sample_size: sample, steps: [{ label: 'Inicio', visits: 50, from_previous: null, from_start: 1 }, { label: 'Contacto', visits: 10, from_previous: 0.2, from_start: 0.2 }] })
  api.realtime.mockResolvedValue({ site_id: 'psi-1', window_minutes: 5, visitors_now: 3, top_pages: [], generated_at: '2026-11-04T05:00:00Z' })
  vi.mocked(careerApi.list).mockResolvedValue([{ id: 'pfn-1', name: 'Embudo CV' }] as never)
})

describe('MetricsPage', () => {
  it('enlaza a la configuración de metas, embudos y anotaciones', async () => {
    render(<MetricsPage />)
    expect(await screen.findByRole('link', { name: /Metas, embudos y anotaciones/ })).toHaveAttribute('href', '/metrics/settings')
  })

  it('RF-063 arranca con 30 días, sin comparar y con bots y mis visitas excluidos', async () => {
    render(<MetricsPage />)
    await waitFor(() => expect(api.kpis).toHaveBeenCalled())
    expect(api.kpis.mock.calls[0][0]).toEqual({ range: { days: 30 }, compare: 'none', excludeBots: true, excludeOwner: true, filters: {} })
    expect(screen.getByRole('switch', { name: 'Excluir bots' })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByRole('switch', { name: 'Excluir mis visitas' })).toHaveAttribute('aria-checked', 'true')
  })

  it('RF-060 muestra los KPIs, "visitantes ahora" y la minigráfica de los conteos', async () => {
    render(<MetricsPage />)
    const visitors = await screen.findByTestId('kpi-visitors')
    expect(within(visitors).getByText('52')).toBeInTheDocument()
    expect(within(screen.getByTestId('kpi-bounce_rate')).getByText('94.4 %')).toBeInTheDocument()
    expect(within(screen.getByTestId('kpi-median_active_ms')).getByText('10 s')).toBeInTheDocument()
    expect(within(screen.getByTestId('kpi-pages_per_visit')).getByText('1.17')).toBeInTheDocument()
    await waitFor(() => expect(within(screen.getByTestId('kpi-now')).getByText('3')).toBeInTheDocument())
  })

  it('RF-060 sin comparación no muestra deltas; con comparación sí, con el color según si subir es bueno', async () => {
    api.kpis.mockImplementation(async (q) =>
      kpisResponse(q.compare === 'none' ? {} : {
        compare: 'previous', compare_period: { since: '2026-09-05', until: '2026-10-04' },
        deltas: {
          visits: { current: 54, previous: 27, delta_abs: 27, delta_pct: 1 },
          bounce_rate: { current: 0.94, previous: 0.7, delta_abs: 0.24, delta_pct: 0.34 },
        },
      })
    )
    render(<MetricsPage />)
    await screen.findByTestId('kpi-visits')
    expect(screen.queryByLabelText('Cambio de Visitas')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Comparar con'), { target: { value: 'previous' } })
    const visitsDelta = await screen.findByLabelText('Cambio de Visitas')
    expect(visitsDelta).toHaveTextContent('+100.0 %')
    expect(visitsDelta.className).toContain('text-green')
    expect(screen.getByLabelText('Cambio de Tasa de rebote').className).toContain('text-red')
  })

  it('RF-061 anota la gráfica y avisa que el último tramo está en curso', async () => {
    render(<MetricsPage />)
    expect(await screen.findByText('Visitas en el tiempo')).toBeInTheDocument()
    expect(screen.getByRole('list', { name: 'Anotaciones' })).toHaveTextContent('Post: Nuevo post del blog')
    expect(screen.getByText(/La línea punteada es el periodo aún en curso/)).toBeInTheDocument()
  })

  it('RF-062 cada pestaña pide solo lo suyo al abrirse', async () => {
    render(<MetricsPage />)
    await screen.findByRole('tab', { name: 'Fuentes' })
    expect(api.pages).not.toHaveBeenCalled()
    expect(await within(screen.getByRole('tabpanel', { name: 'Fuentes' })).findByText('Búsqueda orgánica')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Páginas' }))
    expect(await screen.findByText('/projects')).toBeInTheDocument()
    expect(screen.getByText('61.5 %')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Ubicación' }))
    await waitFor(() => expect(api.geo).toHaveBeenCalled())
    expect(await screen.findByTestId('world-bubble-map')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Dispositivos' }))
    await waitFor(() => expect(api.devices).toHaveBeenCalledWith(expect.anything(), 'device_type'))
  })

  it('RF-062 muestra metas, embudo, recorridos y retención', async () => {
    render(<MetricsPage />)
    expect(await screen.findByText('cv_download')).toBeInTheDocument()
    expect(screen.getByText(/evento clave/)).toBeInTheDocument()
    expect(await screen.findByText('2. Contacto')).toBeInTheDocument()
    expect(screen.getByText(/20.0 % del paso anterior/)).toBeInTheDocument()
    expect(await screen.findByTitle('/ → /projects')).toBeInTheDocument()
    expect(await screen.findByTitle('3 de 10')).toHaveTextContent('30 %')
    await waitFor(() => expect(api.funnel).toHaveBeenCalledWith(expect.anything(), 'pfn-1'))
  })

  it('RF-062 calidad de datos: tamaño de muestra, porcentaje de bots y aviso de muestra pequeña', async () => {
    render(<MetricsPage />)
    const quality = (await screen.findByText('Calidad de los datos')).closest('.card') as HTMLElement
    expect(within(quality).getByText(/54 visitas · 52 visitantes/)).toBeInTheDocument()
    await waitFor(() => expect(within(quality).getByText('10.0 %')).toBeInTheDocument()) // (60-54)/60
    expect(within(quality).getByRole('note')).toHaveTextContent('Muestra pequeña (54 visitas)')
  })

  it('RF-063 los interruptores y el rango vuelven a pedir los datos', async () => {
    render(<MetricsPage />)
    await screen.findByTestId('kpi-visits')
    fireEvent.click(screen.getByRole('switch', { name: 'Excluir bots' }))
    await waitFor(() => expect(api.trend.mock.calls.some(([q]) => q.excludeBots === false)).toBe(true))
    fireEvent.change(screen.getByLabelText('Rango de fechas'), { target: { value: '7' } })
    await waitFor(() => expect(lastQuery(api.trend).range).toEqual({ days: 7 }))
  })

  it('RF-063 un rango personalizado manda fechas exactas', async () => {
    render(<MetricsPage />)
    await screen.findByTestId('kpi-visits')
    fireEvent.change(screen.getByLabelText('Rango de fechas'), { target: { value: 'custom' } })
    fireEvent.change(await screen.findByLabelText('Desde'), { target: { value: '2026-10-01' } })
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-10-15' } })
    await waitFor(() => expect(lastQuery(api.trend).range).toEqual({ since: '2026-10-01', until: '2026-10-15' }))
  })

  it('RF-063 los filtros se combinan y se pueden quitar de una vez', async () => {
    render(<MetricsPage />)
    await screen.findByTestId('kpi-visits')
    await screen.findByRole('option', { name: 'Directo' })
    fireEvent.change(screen.getByLabelText('Filtrar por canal'), { target: { value: 'Direct' } })
    fireEvent.change(await screen.findByLabelText('Filtrar por país'), { target: { value: 'Mexico' } })
    await waitFor(() => expect(lastQuery(api.trend).filters).toEqual({ channel: 'Direct', country: 'Mexico' }))

    fireEvent.click(screen.getByRole('button', { name: 'Quitar filtros' }))
    await waitFor(() => expect(lastQuery(api.trend).filters).toEqual({}))
  })

  it('las listas de filtros se piden sin filtros para que elegir uno no vacíe las demás', async () => {
    render(<MetricsPage />)
    await screen.findByRole('option', { name: 'Directo' })
    fireEvent.change(screen.getByLabelText('Filtrar por canal'), { target: { value: 'Direct' } })
    await waitFor(() => expect(lastQuery(api.trend).filters).toEqual({ channel: 'Direct' }))
    const optionCalls = api.breakdown.mock.calls.filter(([, d]) => d === 'country')
    expect(optionCalls.every(([q]) => Object.keys(q.filters).length === 0)).toBe(true)
  })

  it('muestra el error del servidor', async () => {
    api.kpis.mockRejectedValue(new Error('Network error'))
    render(<MetricsPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/Network error|error/i)
  })
})
