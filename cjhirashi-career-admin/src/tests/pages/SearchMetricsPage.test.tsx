import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../utils'
import { SearchMetricsPage } from '@/pages/SearchMetricsPage'
import { careerApi } from '@/api/career'
import { SearchOverview } from '@/types/career'

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

const baseOverview: SearchOverview = {
  funnel: [
    { label: 'Vacantes', value: 30 },
    { label: 'Aplicaciones', value: 0 },
    { label: 'Entrevistas', value: 0 },
    { label: 'Ofertas', value: 0 },
  ],
  vacancies_by_evaluation: [{ label: 'pending_review', count: 30 }],
  vacancies_by_track: [
    { label: 'A', count: 13 },
    { label: 'B', count: 11 },
  ],
  fit_percentage_avg: 79.2,
  fit_percentage_min: 65,
  fit_percentage_max: 90,
  market_segments: [],
  networking_by_status: [{ label: 'pending', count: 8 }],
  networking_by_category: [{ label: 'specialized_recruiter', count: 5 }],
  companies_by_tier: [{ label: '1', count: 22 }],
  companies_by_status: [{ label: 'TBD', count: 43 }],
  fit_scoring_factors: [{ factor_name: 'Alignment with Role', weight_percentage: 25 }],
  active_search_plan: null,
}

describe('SearchMetricsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the page title and description', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    render(<SearchMetricsPage />)
    expect(screen.getByText('Métricas de Búsqueda')).toBeInTheDocument()
    await waitFor(() => expect(mockedCareerApi.searchOverview).toHaveBeenCalled())
  })

  it('should render the conversion funnel with real values', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    render(<SearchMetricsPage />)
    await waitFor(() => expect(screen.getByText('Embudo de Conversión')).toBeInTheDocument())
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
    expect(screen.getByText('30')).toBeInTheDocument()
  })

  it('should render fit percentage stats', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    render(<SearchMetricsPage />)
    await waitFor(() => expect(screen.getByText('Fit de Vacantes')).toBeInTheDocument())
    expect(screen.getByText('79.2')).toBeInTheDocument()
    expect(screen.getByText('65')).toBeInTheDocument()
    expect(screen.getByText('90')).toBeInTheDocument()
  })

  it('should show an empty state for market segments when none are active', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    render(<SearchMetricsPage />)
    await waitFor(() =>
      expect(screen.getByText('Aún no hay segmentos de mercado registrados.')).toBeInTheDocument()
    )
  })

  it('should show an empty state when there is no active search plan', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    render(<SearchMetricsPage />)
    await waitFor(() =>
      expect(screen.getByText('No hay ningún plan de búsqueda en progreso.')).toBeInTheDocument()
    )
  })

  it('should render active search plan progress when present', async () => {
    mockedCareerApi.searchOverview.mockResolvedValue({
      ...baseOverview,
      active_search_plan: {
        period_start: '2026-08-01',
        period_end: '2026-08-31',
        plan_status: 'in_progress',
        completion_percentage: 40,
        target_cvs_sent: 20,
        target_interviews: 5,
        target_offers: 1,
      },
    })
    render(<SearchMetricsPage />)
    await waitFor(() => expect(screen.getByText('40%')).toBeInTheDocument())
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('should show an error message when the request fails', async () => {
    mockedCareerApi.searchOverview.mockRejectedValue(new Error('Network error'))
    render(<SearchMetricsPage />)
    await waitFor(() => expect(screen.getByText(/Network error|error/i)).toBeInTheDocument())
  })
})
