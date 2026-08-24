import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../utils'
import { JobDiscoveryPage } from '@/pages/JobDiscoveryPage'
import { careerApi } from '@/api/career'

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

describe('JobDiscoveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedCareerApi.listJobProviders.mockResolvedValue([
      { id: 'getonboard', label: 'Get on Board', enabled: true, listing_kind: 'job' },
      { id: 'indeed', label: 'Indeed', enabled: false, reason: 'Faltan keys', listing_kind: 'job' },
      { id: 'linkedin', label: 'LinkedIn', enabled: true, listing_kind: 'search_url' },
    ])
    mockedCareerApi.list.mockResolvedValue([])
  })

  it('renders title and provider checkboxes', async () => {
    render(<JobDiscoveryPage />)
    expect(screen.getByText('Descubrir vacantes')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Get on Board')).toBeInTheDocument())
    expect(screen.getByRole('checkbox', { name: /Indeed/ })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'LinkedIn' })).toBeInTheDocument()
  })

  it('runs a search and shows LinkedIn as an open-search link', async () => {
    mockedCareerApi.runJobDiscovery.mockResolvedValue({
      query: 'SRE',
      location: 'Mexico',
      listings: [
        {
          company: 'LinkedIn',
          exact_role: 'Búsqueda actual: SRE',
          vacancy_url: 'https://www.linkedin.com/jobs/search/?keywords=SRE',
          source: 'linkedin',
          listing_kind: 'search_url',
          already_saved: false,
        },
      ],
      errors: [],
    })
    render(<JobDiscoveryPage />)
    await waitFor(() => expect(screen.getByText('Get on Board')).toBeInTheDocument())
    fireEvent.change(screen.getByPlaceholderText('Backend engineer'), { target: { value: 'SRE' } })
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }))
    await waitFor(() => expect(mockedCareerApi.runJobDiscovery).toHaveBeenCalled())
    expect(screen.getByRole('link', { name: /Abrir búsqueda en LinkedIn/i })).toHaveAttribute(
      'href',
      'https://www.linkedin.com/jobs/search/?keywords=SRE'
    )
  })

  it('saves a selected job listing', async () => {
    mockedCareerApi.runJobDiscovery.mockResolvedValue({
      query: 'Python',
      listings: [
        {
          company: 'Acme',
          exact_role: 'Python Dev',
          vacancy_url: 'https://www.getonbrd.com/jobs/1',
          source: 'getonboard',
          listing_kind: 'job',
          already_saved: false,
        },
      ],
      errors: [],
    })
    mockedCareerApi.saveJobListings.mockResolvedValue({
      created: [{ id: 'vac-1', vacancy_url: 'https://www.getonbrd.com/jobs/1', company: 'Acme', exact_role: 'Python Dev' }],
      skipped: [],
    })
    render(<JobDiscoveryPage />)
    await waitFor(() => expect(screen.getByText('Get on Board')).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }))
    await waitFor(() => expect(screen.getByText('Python Dev')).toBeInTheDocument())
    const boxes = screen.getAllByRole('checkbox')
    fireEvent.click(boxes[boxes.length - 1])
    fireEvent.click(screen.getByRole('button', { name: 'Guardar seleccionadas' }))
    await waitFor(() => expect(mockedCareerApi.saveJobListings).toHaveBeenCalled())
    expect(screen.getByText(/Guardadas: 1/)).toBeInTheDocument()
  })
})
