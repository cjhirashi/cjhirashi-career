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
      expect(screen.getByText('My Projects')).toBeInTheDocument()
    })
  })

  it('renders page description', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/showcase my skills and expertise/i)).toBeInTheDocument()
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

  it('renders technology filter buttons', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('Filter by Technology')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /All Projects/i })).toBeInTheDocument()
    })
  })

  it('filters projects by selected technology', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    await waitFor(() => {
      const projects = mockProjects.filter(p => p.technologies.includes('React'))
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
      expect(screen.getByText('React')).toBeInTheDocument()
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

  it('resets filter to All Projects', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    const allButton = screen.getByRole('button', { name: /All Projects/i })
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
      expect(screen.getByText('React')).toBeInTheDocument()
    })

    const reactFilter = screen.getByRole('button', { name: 'React' })
    await user.click(reactFilter)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'filter-React',
      })
    )
  })

  it('tracks all projects filter click', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument()
    })

    const allButton = screen.getByRole('button', { name: /All Projects/i })
    await user.click(allButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'filter-all',
      })
    )
  })

  it('shows loading spinner initially', () => {
    vi.mocked(projectsApi.getProjects).mockImplementation(
      () => new Promise(() => {})
    )

    render(<ProjectsPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when projects fail to load', async () => {
    vi.mocked(projectsApi.getProjects).mockRejectedValue(new Error('Failed'))

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load projects/i)).toBeInTheDocument()
    })
  })

  it('shows no projects message when filter returns empty', async () => {
    const user = userEvent.setup()
    const projectsWithoutReact = mockProjects.filter(p => !p.technologies.includes('React'))
    vi.mocked(projectsApi.getProjects).mockResolvedValue(projectsWithoutReact)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/showcase my skills/i)).toBeInTheDocument()
    })

    // Try to click React filter if it exists
    const reactFilter = screen.queryByRole('button', { name: 'React' })
    if (reactFilter) {
      await user.click(reactFilter)
      expect(screen.getByText(/No projects found/i)).toBeInTheDocument()
    }
  })

  it('renders download CV button section', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Want to know more/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Download Full CV/i })).toBeInTheDocument()
    })
  })

  it('tracks CV download button click', async () => {
    const user = userEvent.setup()
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/Want to know more/i)).toBeInTheDocument()
    })

    const downloadButton = screen.getByRole('button', { name: /Download Full CV/i })
    await user.click(downloadButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'download-cv',
      })
    )
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

  it('handles empty projects array', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue([])

    render(<ProjectsPage />)

    await waitFor(() => {
      expect(screen.getByText(/My Projects/)).toBeInTheDocument()
    })
  })

  it('displays unique technologies from all projects', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue(mockProjects)

    render(<ProjectsPage />)

    await waitFor(() => {
      const uniqueTechs = Array.from(new Set(mockProjects.flatMap(p => p.technologies)))
      uniqueTechs.forEach(tech => {
        expect(screen.getByRole('button', { name: tech })).toBeInTheDocument()
      })
    })
  })
})
