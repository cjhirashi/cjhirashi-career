import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { projectsApi } from '@/api/projects'
import { trackingApi } from '@/api/tracking'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { mockProjects } from '../fixtures/mockData'

vi.mock('@/api/projects')
vi.mock('@/api/tracking')

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders page heading', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('Proyectos')).toBeInTheDocument()
    })
  })

  it('renders page description', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/diseñados para operar solos/i)).toBeInTheDocument()
    })
  })

  it('renders all projects', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      mockProjects.forEach(project => {
        expect(screen.getByText(project.title)).toBeInTheDocument()
      })
    })
  })

  it('links each project card to its detail page', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      const link = screen.getByText(mockProjects[0].title).closest('a')
      expect(link).toHaveAttribute('href', `/projects/${mockProjects[0].id}`)
    })
  })

  it('renders category/industry filter buttons', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Todos' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: mockProjects[0].category! })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: mockProjects[0].industry! })).toBeInTheDocument()
    })
  })

  it('filters projects by selected category', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    const filterButton = await screen.findByRole('button', { name: mockProjects[0].category! })
    await user.click(filterButton)

    await waitFor(() => {
      expect(screen.getByText(mockProjects[0].title)).toBeInTheDocument()
      expect(screen.queryByText(mockProjects[2].title)).not.toBeInTheDocument()
    })
  })

  it('removes the filter when the same chip is clicked again', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    const filterButton = await screen.findByRole('button', { name: mockProjects[0].category! })
    await user.click(filterButton)
    await waitFor(() => expect(filterButton).toHaveClass('filter-chip-active'))

    await user.click(filterButton)
    await waitFor(() => expect(filterButton).not.toHaveClass('filter-chip-active'))
  })

  it('resets to all projects via the "Todos" button', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    const filterButton = await screen.findByRole('button', { name: mockProjects[0].category! })
    await user.click(filterButton)

    const allButton = screen.getByRole('button', { name: 'Todos' })
    await user.click(allButton)

    await waitFor(() => {
      mockProjects.forEach(project => {
        expect(screen.getByText(project.title)).toBeInTheDocument()
      })
    })
  })

  it('tracks filter clicks', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    const filterButton = await screen.findByRole('button', { name: mockProjects[0].category! })
    await user.click(filterButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({ target: `filter-${mockProjects[0].category}` })
    )
  })

  it('shows loading spinner initially', () => {
    vi.mocked(projectsApi.getProjects).mockImplementation(() => new Promise(() => {}))

    render(<ProjectsPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when projects fail to load', async () => {
    vi.mocked(projectsApi.getProjects).mockRejectedValue(new Error('Failed'))

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudieron cargar los proyectos/i)).toBeInTheDocument()
    })
  })

  it('renders projects in a grid layout', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    const { container } = render(<ProjectsPage />)

    await waitFor(() => {
      const grid = container.querySelector('.grid')
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
    })
  })

  it('handles an empty projects array', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue([])

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('Proyectos')).toBeInTheDocument()
    })
  })
})
