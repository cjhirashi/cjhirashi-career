import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { homeApi } from '@/api/home'
import { aboutApi } from '@/api/about'
import { trackingApi } from '@/api/tracking'
import { HomePage } from '@/pages/HomePage'
import { mockHome, mockAbout } from '../fixtures/mockData'

vi.mock('@/api/home')
vi.mock('@/api/about')
vi.mock('@/api/tracking')

const renderReady = async () => {
  vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)
  vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)
  render(<HomePage />)
  await waitFor(() => {
    expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
  })
}

describe('HomePage - Entry Point', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders hero copy from home content', async () => {
    await renderReady()

    expect(screen.getByText(mockHome.hero_subtitle!)).toBeInTheDocument()
    expect(screen.getByText(mockHome.hero_intro!)).toBeInTheDocument()
  })

  it('renders the hero photo from about content', async () => {
    await renderReady()

    const photo = screen.getByAltText('Carlos A. Jiménez Hirashi') as HTMLImageElement
    expect(photo.src).toContain(mockAbout.photo_url)
  })

  it('renders the 4 stats', async () => {
    await renderReady()

    mockHome.stats.forEach(stat => {
      expect(screen.getByText(stat.value)).toBeInTheDocument()
      expect(screen.getByText(stat.label)).toBeInTheDocument()
    })
  })

  it('renders the anchor project as a flagship case study', async () => {
    await renderReady()

    expect(screen.getByText('Ver caso completo →')).toBeInTheDocument()
    expect(screen.getAllByText(mockHome.anchor_project!.title).length).toBeGreaterThan(0)
  })

  it('renders a "Ver Caso" CTA linking to the anchor project', async () => {
    await renderReady()

    const anchorLink = screen.getByRole('link', { name: `Ver Caso ${mockHome.anchor_project!.title}` })
    expect(anchorLink).toHaveAttribute('href', `/projects/${mockHome.anchor_project!.id}`)
  })

  it('renders featured projects section', async () => {
    await renderReady()

    expect(screen.getByText('Proyectos')).toBeInTheDocument()
    mockHome.featured_projects.forEach(p => {
      expect(screen.getAllByText(p.title).length).toBeGreaterThan(0)
    })
  })

  it('renders featured publications section', async () => {
    await renderReady()

    expect(screen.getByText('Del blog')).toBeInTheDocument()
    expect(screen.getByText(mockHome.featured_publications[0].title)).toBeInTheDocument()
  })

  it('renders the "Ver proyectos" CTA', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: 'Ver proyectos' })).toHaveAttribute('href', '/projects')
  })

  it('tracks clicks on the "Ver proyectos" CTA', async () => {
    const user = userEvent.setup()
    await renderReady()

    await user.click(screen.getByRole('link', { name: 'Ver proyectos' }))

    expect(trackingApi.trackEvent).toHaveBeenCalled()
  })

  it('renders "Ver todos" links pointing at /projects and /blog', async () => {
    await renderReady()

    const links = screen.getAllByRole('link', { name: /Ver todos/i })
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/projects')
    expect(hrefs).toContain('/blog')
  })

  it('shows loading spinner initially', () => {
    vi.mocked(homeApi.getHome).mockImplementation(() => new Promise(() => {}))
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<HomePage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when home content fails to load', async () => {
    vi.mocked(homeApi.getHome).mockRejectedValue(new Error('Failed'))
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudo cargar el contenido de la Home/i)).toBeInTheDocument()
    })
  })

  it('falls back to the default title when hero_title is missing', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({ ...mockHome, hero_title: null })
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Carlos Jiménez Hirashi')).toBeInTheDocument()
    })
  })

  it('omits the anchor case study and featured sections when there is none', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({
      ...mockHome,
      anchor_project: null,
      featured_projects: [],
      featured_publications: [],
    })
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
    })
    expect(screen.queryByText('Ver caso completo →')).not.toBeInTheDocument()
    expect(screen.queryByText('Del blog')).not.toBeInTheDocument()
  })

  it('renders hero section in gradient background', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)
    const { container } = render(<HomePage />)

    await waitFor(() => {
      expect(container.querySelector('.bg-gradient-to-br')).toBeInTheDocument()
    })
  })
})
