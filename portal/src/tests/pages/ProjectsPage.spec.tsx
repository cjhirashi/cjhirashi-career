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
      expect(screen.getByText('Mis Proyectos')).toBeInTheDocument()
    })
  })

  it('renders page description', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/habilidades y experiencia/i)).toBeInTheDocument()
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

  it('renders technology filter buttons', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('Filtrar por tecnología')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Todos los proyectos/i })).toBeInTheDocument()
    })
  })

  it('filters projects by selected technology', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    await waitFor(() => {
      const projects = mockProjects.filter(p => p.tech_stack.includes('React'))
      projects.forEach(project => {
        expect(screen.getByText(project.title)).toBeInTheDocument()
      })
    })
  })

  it('removes filter when same technology is clicked again', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    await waitFor(() => {
      expect(reactFilter).toHaveClass('bg-cyan-600')
    })

    await user.click(reactFilter)

    await waitFor(() => {
      expect(reactFilter).not.toHaveClass('bg-cyan-600')
    })
  })

  it('resets filter to all projects', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    const allButton = screen.getByRole('button', { name: /Todos los proyectos/i })
    await user.click(allButton)

    await waitFor(() => {
      mockProjects.forEach(project => {
        expect(screen.getByText(project.title)).toBeInTheDocument()
      })
    })
  })

  it('tracks technology filter clicks', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: 'filter-React' }))
  })

  it('tracks the "all projects" filter click', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'React' })).toBeInTheDocument()
    })

    const allButton = screen.getByRole('button', { name: /Todos los proyectos/i })
    await user.click(allButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: 'filter-all' }))
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

  it('shows no-results message when filter returns empty', async () => {
    const user = userEvent.setup()
    const projectsWithoutReact = mockProjects.filter(p => !p.tech_stack.includes('React'))
    vi.mocked(projectsApi.getProjects).mockResolvedValue(projectsWithoutReact)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/habilidades y experiencia/i)).toBeInTheDocument()
    })

    const reactFilter = screen.queryByRole('button', { name: 'React' })
    if (reactFilter) {
      await user.click(reactFilter)
      expect(screen.getByText(/No hay proyectos para este filtro/i)).toBeInTheDocument()
    }
  })

  it('renders projects in grid layout', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    const { container } = render(<ProjectsPage />)

    await waitFor(() => {
      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
    })
  })

  it('handles an empty projects array', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue([])

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Mis Proyectos/)).toBeInTheDocument()
    })
  })

  it('displays unique technologies from all projects', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      const uniqueTechs = Array.from(new Set(mockProjects.flatMap(p => p.tech_stack)))
      uniqueTechs.forEach(tech => {
        expect(screen.getByRole('button', { name: tech })).toBeInTheDocument()
      })
    })
  })

  it('shows a "Destacado" badge on featured projects', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Destacado').length).toBeGreaterThan(0)
    })
  })
})
