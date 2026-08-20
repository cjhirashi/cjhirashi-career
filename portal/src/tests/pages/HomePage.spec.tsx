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

  it('renders the hero photo from home content', async () => {
    await renderReady()

    const photo = screen.getByAltText('Carlos A. Jiménez Hirashi') as HTMLImageElement
    expect(photo.src).toContain(mockHome.hero_photo_url)
  })

  it('renders the 4 stats', async () => {
    await renderReady()

    mockHome.stats.forEach(stat => {
      expect(screen.getByText(stat.value)).toBeInTheDocument()
      expect(screen.getByText(stat.label)).toBeInTheDocument()
    })
  })

  it('renders the anchor project as a flagship case study with problem/architecture/result', async () => {
    await renderReady()

    expect(screen.getAllByText(mockHome.anchor_project!.title, { exact: false }).length).toBeGreaterThan(0)
    expect(screen.getByText('Problema')).toBeInTheDocument()
    expect(screen.getAllByText('Arquitectura').length).toBeGreaterThan(0)
    expect(screen.getByText('Resultado')).toBeInTheDocument()
    expect(screen.getByText(mockHome.anchor_project!.problem!)).toBeInTheDocument()
  })

  it('renders hero CTA buttons from hero_ctas, first as primary and rest as secondary', async () => {
    await renderReady()

    const primary = screen.getByRole('link', { name: mockHome.hero_ctas[0].label })
    expect(primary).toHaveAttribute('href', mockHome.hero_ctas[0].url)
    expect(primary.className).toContain('btn ')

    const secondary = screen.getByRole('link', { name: mockHome.hero_ctas[1].label })
    expect(secondary).toHaveAttribute('href', mockHome.hero_ctas[1].url)
    expect(secondary.className).toContain('btn-secondary')
  })

  it('omits the CTA row entirely when hero_ctas is empty', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({ ...mockHome, hero_ctas: [] })
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
    })
    expect(screen.queryByRole('link', { name: 'Ver proyectos' })).not.toBeInTheDocument()
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

  it('renders no H1 at all when hero_title is empty - no silent fallback to other content', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue({ ...mockHome, hero_title: null })
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    const { container } = render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_subtitle!)).toBeInTheDocument()
    })
    expect(container.querySelector('h1')).not.toBeInTheDocument()
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

  it('renders the skill group categories as a "Stack técnico" teaser, excluding "Otros"', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue({
      ...mockAbout,
      skill_groups: [
        { category: 'Frontend', skills: ['React'] },
        { category: 'Otros', skills: ['Misc'] },
      ],
    })
    await renderReady()

    expect(await screen.findByText('Stack técnico')).toBeInTheDocument()
    expect(screen.getByText('Frontend')).toBeInTheDocument()
    expect(screen.queryByText('Otros')).not.toBeInTheDocument()
  })

  it('omits the "Stack técnico" section when there are no skill groups', async () => {
    vi.mocked(homeApi.getHome).mockResolvedValue(mockHome)
    vi.mocked(aboutApi.getAbout).mockResolvedValue({ ...mockAbout, skill_groups: [] })

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockHome.hero_title!)).toBeInTheDocument()
    })
    expect(screen.queryByText('Stack técnico')).not.toBeInTheDocument()
  })

  it('renders the footer CTA linking to /contact', async () => {
    await renderReady()

    expect(screen.getByText('¿Hablamos de tu próximo sistema?')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Hablemos' })).toHaveAttribute('href', '/contact')
  })
})
