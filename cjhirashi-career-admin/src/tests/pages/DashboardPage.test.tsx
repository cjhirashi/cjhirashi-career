import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../utils'
import { DashboardPage } from '@/pages/DashboardPage'
import { useAuthStore } from '@/stores/authStore'
import { careerApi } from '@/api/career'
import { SearchOverview } from '@/types/career'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: useAuthStore.getState().user,
    accessToken: useAuthStore.getState().accessToken,
    isAuthenticated: useAuthStore.getState().isAuthenticated,
  }),
}))

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

const baseOverview: SearchOverview = {
  funnel: [
    { label: 'Vacantes', value: 30 },
    { label: 'Aplicaciones', value: 12 },
    { label: 'Entrevistas', value: 4 },
    { label: 'Ofertas', value: 1 },
  ],
  vacancies_by_evaluation: [{ label: 'pending_review', count: 30 }],
  vacancies_by_track: [{ label: 'A', count: 13 }],
  fit_percentage_avg: 79.2,
  fit_percentage_min: 65,
  fit_percentage_max: 90,
  market_segments: [],
  networking_by_status: [{ label: 'pending', count: 8 }],
  networking_by_category: [{ label: 'specialized_recruiter', count: 5 }],
  companies_by_tier: [{ label: '1', count: 22 }],
  companies_by_status: [{ label: 'TBD', count: 43 }],
  fit_scoring_factors: [{ factor_name: 'Alignment with Role', weight_percentage: 25 }],
  active_search_plan: {
    period_start: '2026-08-01',
    period_end: '2026-08-31',
    plan_status: 'in_progress',
    completion_percentage: 40,
    target_cvs_sent: 20,
    target_interviews: 5,
    target_offers: 1,
  },
  applications_by_status: [{ label: 'applied', count: 12 }],
  interviews_by_result: [{ label: 'pending', count: 4 }],
  networking_activities_by_category: [{ label: 'give_value_70', count: 6 }],
  application_interactions_response_rate: { total: 10, positive: 3, rate_percentage: 30 },
  contact_interactions_response_rate: { total: 16, positive: 2, rate_percentage: 12.5 },
  contact_interactions_opportunity_rate: { total: 16, positive: 0, rate_percentage: 0 },
  funnel_conversion_rates: [
    { label: 'Vacantes → Aplicaciones', value_percentage: 40, detail: '12 de 30' },
    { label: 'Aplicaciones → Entrevistas', value_percentage: 33.3, detail: '4 de 12' },
    { label: 'Entrevistas → Ofertas', value_percentage: 25, detail: '1 de 4' },
    { label: 'Tasa de Éxito Total', value_percentage: 3.3, detail: '1 ofertas de 30 vacantes' },
  ],
  vacancy_kpis: [
    { label: 'Tasa de Fit', value_percentage: 85, detail: '17 de 20 evaluadas' },
    { label: 'Tasa de Aplicación sobre Fit', value_percentage: 70.6, detail: '12 de 17 con fit' },
  ],
  networking_kpis: [
    { label: 'Tasa de Conversión de Contactos', value_percentage: 12.5, detail: '1 de 8' },
    { label: 'Tasa de Respuesta', value_percentage: 12.5, detail: '2 de 16' },
    { label: 'Tasa de Oportunidad Generada', value_percentage: 0, detail: '0 de 16' },
  ],
  vacancies_by_platform: [
    { platform: 'LinkedIn', vacancies: 20, applications: 8, interviews: 3, offers: 1, application_rate_percentage: 40 },
    { platform: 'Referido', vacancies: 10, applications: 4, interviews: 1, offers: 0, application_rate_percentage: 40 },
  ],
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.setState({
      user: mockUser,
      isAuthenticated: true,
      accessToken: 'token123',
    })
    mockedCareerApi.weeklyMetrics.mockResolvedValue([])
    mockedCareerApi.searchOverview.mockResolvedValue(baseOverview)
    mockedCareerApi.count.mockResolvedValue(0)
  })

  describe('rendering', () => {
    it('should render dashboard page with title', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('should display welcome message with user name', () => {
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back, Demo User!/i)).toBeInTheDocument()
    })

    it('should render quick stats section with real resource labels', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Vacantes')).toBeInTheDocument()
      expect(screen.getByText('Aplicaciones')).toBeInTheDocument()
      expect(screen.getByText('Entrevistas')).toBeInTheDocument()
      expect(screen.getByText('Contactos')).toBeInTheDocument()
    })

    it('should not render the Getting Started guide anymore', () => {
      render(<DashboardPage />)
      expect(screen.queryByText('Getting Started')).not.toBeInTheDocument()
      expect(screen.queryByText('Set Your Professional Identity')).not.toBeInTheDocument()
    })
  })

  describe('quick stats cards', () => {
    it('should render all four stat cards with counts from the API', async () => {
      mockedCareerApi.count.mockImplementation(async (resource) => {
        const counts: Record<string, number> = {
          vacancies: 30,
          applications: 12,
          interviews: 4,
          'networking-contacts': 8,
        }
        return counts[resource] ?? 0
      })
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getAllByText('30').length).toBeGreaterThan(0))
      expect(screen.getAllByText('12').length).toBeGreaterThan(0)
      expect(screen.getAllByText('4').length).toBeGreaterThan(0)
      expect(screen.getAllByText('8').length).toBeGreaterThan(0)
    })

    it('should have a Lucide icon for each quick-stat card', () => {
      const { container } = render(<DashboardPage />)
      const statCards = container.querySelectorAll('.stat-card')
      expect(statCards.length).toBeGreaterThanOrEqual(4)
      statCards.forEach((card) => {
        expect(card.querySelector('svg')).toBeInTheDocument()
      })
    })
  })

  describe('embudo de conversión', () => {
    it('should render the funnel stage values and conversion-rate KPIs', async () => {
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getByText('Embudo de Conversión')).toBeInTheDocument())
      expect(screen.getByText('Vacantes → Aplicaciones')).toBeInTheDocument()
      expect(screen.getByText('40%')).toBeInTheDocument()
      expect(screen.getByText('12 de 30')).toBeInTheDocument()
      expect(screen.getByText('Tasa de Éxito Total')).toBeInTheDocument()
    })
  })

  describe('objetivos del plan de búsqueda', () => {
    it('should render target-vs-actual progress for the active plan', async () => {
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getByText('Objetivos del Plan de Búsqueda')).toBeInTheDocument())
      expect(screen.getByText('CVs enviados')).toBeInTheDocument()
      expect(screen.getByText('12 / 20')).toBeInTheDocument()
      expect(screen.getAllByText('Entrevistas').length).toBeGreaterThan(0)
      expect(screen.getByText('4 / 5')).toBeInTheDocument()
    })

    it('should show an empty state when there is no active plan', async () => {
      mockedCareerApi.searchOverview.mockResolvedValue({ ...baseOverview, active_search_plan: null })
      render(<DashboardPage />)
      await waitFor(() =>
        expect(screen.getByText('No hay un plan de búsqueda activo con metas definidas.')).toBeInTheDocument()
      )
    })
  })

  describe('vacantes y networking', () => {
    it('should render Vacantes KPIs and breakdowns', async () => {
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getByText('Tasa de Fit')).toBeInTheDocument())
      expect(screen.getByText('85%')).toBeInTheDocument()
      expect(screen.getByText('Tasa de Aplicación sobre Fit')).toBeInTheDocument()
    })

    it('should render Networking KPIs', async () => {
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getByText('Tasa de Conversión de Contactos')).toBeInTheDocument())
      expect(screen.getByText('Tasa de Oportunidad Generada')).toBeInTheDocument()
    })

    it('should render results by platform', async () => {
      render(<DashboardPage />)
      await waitFor(() => expect(screen.getByText('Vacantes por Plataforma')).toBeInTheDocument())
    })

    it('should show an empty state when no vacancy has a known platform/source', async () => {
      mockedCareerApi.searchOverview.mockResolvedValue({ ...baseOverview, vacancies_by_platform: [] })
      render(<DashboardPage />)
      await waitFor(() =>
        expect(screen.getByText('Aún no hay vacantes con plataforma u origen registrado.')).toBeInTheDocument()
      )
    })
  })

  describe('styling and structure', () => {
    it('should have proper heading hierarchy', () => {
      const { container } = render(<DashboardPage />)
      const headings = container.querySelectorAll('h1, h2, h3')
      expect(headings.length).toBeGreaterThan(0)
    })

    it('should have proper card styling', () => {
      const { container } = render(<DashboardPage />)
      const cards = container.querySelectorAll('.card')
      expect(cards.length).toBeGreaterThan(0)
    })
  })

  describe('responsive layout', () => {
    it('should render grid layout for stats', () => {
      const { container } = render(<DashboardPage />)
      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4')
    })

    it('should have proper spacing', () => {
      const { container } = render(<DashboardPage />)
      // el bloque de encabezado (título + saludo) lleva `mb-8`
      const header = container.querySelector('h1')?.closest('.mb-8')
      expect(header).not.toBeNull()
    })
  })

  describe('user context', () => {
    it('should display authenticated user information', () => {
      render(<DashboardPage />)
      expect(screen.getByText(/Demo User/i)).toBeInTheDocument()
    })

    it('should handle different user names', () => {
      useAuthStore.setState({
        user: { ...mockUser, full_name: 'John Doe' },
      })
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back, John Doe!/i)).toBeInTheDocument()
    })

    it('should handle null user gracefully', () => {
      useAuthStore.setState({ user: null })
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument()
    })
  })
})
