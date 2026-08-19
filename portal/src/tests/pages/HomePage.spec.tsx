import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { homeApi } from '@/api/home'
import { trackingApi } from '@/api/tracking'
import { HomePage } from '@/pages/HomePage'
import { mockHome } from '../fixtures/mockData'

vi.mock('@/api/home')
vi.mock('@/api/tracking')

describe('HomePage - Entry Point', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders hero copy from home content', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
    })
    expect(screen.getByText(mockHome.hero_subtitle!)).toBeInTheDocument()
    expect(screen.getByText(mockHome.hero_intro!)).toBeInTheDocument()
  })

  it('renders featured projects section', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Proyectos Destacados/)).toBeInTheDocument()
      expect(screen.getByText('E-Commerce Platform')).toBeInTheDocument()
      expect(screen.getByText('SaaS Dashboard')).toBeInTheDocument()
    })
  })

  it('links featured projects to their detail page', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      const projectLink = screen.getByText('E-Commerce Platform').closest('a')
      expect(projectLink).toHaveAttribute('href', '/projects/1')
    })
  })

  it('renders featured publications section', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Del Blog/)).toBeInTheDocument()
      expect(screen.getByText('Understanding System Design')).toBeInTheDocument()
    })
  })

  it('renders CTA buttons for navigation', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Ver Proyectos/i })).toHaveAttribute('href', '/projects')
      expect(screen.getByRole('link', { name: /Contactar/i })).toHaveAttribute('href', '/contact')
    })
  })

  it('renders final CTA section', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Trabajamos juntos/i)).toBeInTheDocument()
      expect(screen.getByText(/Iniciar una conversación/i)).toBeInTheDocument()
    })
  })

  it('tracks clicks on the portfolio CTA button', async () => {
    const user = userEvent.setup()
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Proyectos Destacados/)).toBeInTheDocument()
    })

    const portfolioButton = screen.getByRole('link', { name: /Ver Proyectos/i })
    await user.click(portfolioButton)

    expect(trackingApi.trackEvent).toHaveBeenCalled()
  })

  it('shows loading spinner initially', () => {
    vi.mocked(homeApi.getHome).mockImplementation(() => new Promise(() => {}))

    render(<HomePage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when home content fails to load', async () => {
    vi.mocked(homeApi.getHome).mockRejectedValue(new Error('Failed'))

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudo cargar el contenido de la Home/i)).toBeInTheDocument()
    })
  })

  it('falls back to the default title when hero_title is missing', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({ ...mockHome, hero_title: null })

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Carlos Jiménez Hirashi')).toBeInTheDocument()
    })
  })

  it('omits the featured sections when there is no featured content', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({
      ...mockHome,
      featured_projects: [],
      featured_publications: [],
    })

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
    })
    expect(screen.queryByText(/Proyectos Destacados/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Del Blog/)).not.toBeInTheDocument()
  })

  it('renders hero section in gradient background', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    const { container } = render(<HomePage />)

    await waitFor(() => {
      expect(container.querySelector('.bg-gradient-to-br')).toBeInTheDocument()
    })
  })

  it('renders "Ver todos" / "Ver todo" links pointing at their list pages', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Ver todos →' })).toHaveAttribute('href', '/projects')
      expect(screen.getByRole('link', { name: 'Ver todo →' })).toHaveAttribute('href', '/blog')
    })
  })
})
