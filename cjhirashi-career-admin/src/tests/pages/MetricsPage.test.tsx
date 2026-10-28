import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../utils'
import { MetricsPage } from '@/pages/MetricsPage'
import { careerApi } from '@/api/career'
import { PortalMetricsOverview } from '@/types/career'

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

const baseOverview: PortalMetricsOverview = {
  total_pageviews: 142,
  pageviews_in_window: 58,
  total_visits: 97,
  visits_in_window: 41,
  window_days: 30,
  visits_by_day: [
    { day: '2026-10-22', count: 20 },
    { day: '2026-10-23', count: 38 },
  ],
  visits_by_country: [
    { label: 'Mexico', count: 90 },
    { label: 'United States', count: 52 },
  ],
  visits_by_location: [
    { city: 'Mexico City', country: 'Mexico', latitude: 19.4326, longitude: -99.1332, count: 90 },
    { city: 'Austin', country: 'United States', latitude: 30.2672, longitude: -97.7431, count: 52 },
  ],
  top_pages: [
    { label: '/', count: 60 },
    { label: '/projects', count: 40 },
  ],
  duration_ms_min: 1200,
  duration_ms_avg: 45000,
  duration_ms_max: 180000,
  duration_sample_size: 58,
}

describe('MetricsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the page title and description', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue(baseOverview)
    render(<MetricsPage />)
    expect(screen.getByText('Métricas del Portafolio')).toBeInTheDocument()
    await waitFor(() => expect(mockedCareerApi.portalMetricsOverview).toHaveBeenCalled())
  })

  it('should render the total and windowed unique-visit counts, distinct from raw pageviews', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue(baseOverview)
    render(<MetricsPage />)
    await waitFor(() => expect(screen.getByText('97')).toBeInTheDocument())
    expect(screen.getByText('41')).toBeInTheDocument()
    expect(screen.getByText(/142 páginas vistas en total/)).toBeInTheDocument()
    expect(screen.getByText(/58 páginas vistas en la ventana/)).toBeInTheDocument()
  })

  it('should render the top country and top page stat cards', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue(baseOverview)
    render(<MetricsPage />)
    await waitFor(() => expect(screen.getByText('Mexico')).toBeInTheDocument())
    expect(screen.getByText('/')).toBeInTheDocument()
  })

  it('should render one map bubble per visit location', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue(baseOverview)
    render(<MetricsPage />)
    const map = await screen.findByTestId('world-bubble-map')
    expect(map.querySelectorAll('circle').length).toBe(2)
  })

  it('should show an empty state when there are no visits in the window', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue({
      ...baseOverview,
      visits_by_day: [],
      visits_by_country: [],
      visits_by_location: [],
      top_pages: [],
    })
    render(<MetricsPage />)
    await waitFor(() =>
      expect(screen.getAllByText('Aún no hay visitas registradas en esta ventana.').length).toBeGreaterThan(0)
    )
  })

  it('should re-fetch with a new window when the range selector changes', async () => {
    mockedCareerApi.portalMetricsOverview.mockResolvedValue(baseOverview)
    render(<MetricsPage />)
    await waitFor(() => expect(mockedCareerApi.portalMetricsOverview).toHaveBeenCalledWith(30))

    fireEvent.change(screen.getByLabelText('Ventana de tiempo'), { target: { value: '7' } })

    await waitFor(() => expect(mockedCareerApi.portalMetricsOverview).toHaveBeenCalledWith(7))
  })

  it('should show an error message when the request fails', async () => {
    mockedCareerApi.portalMetricsOverview.mockRejectedValue(new Error('Network error'))
    render(<MetricsPage />)
    await waitFor(() => expect(screen.getByText(/Network error|error/i)).toBeInTheDocument())
  })
})
