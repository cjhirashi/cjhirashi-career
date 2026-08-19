import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import { aboutApi } from '@/api/about'
import { AboutPage } from '@/pages/AboutPage'
import { mockAbout } from '../fixtures/mockData'

vi.mock('@/api/about')

describe('AboutPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the professional tagline in the hero', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.professional_tagline!)).toBeInTheDocument()
    })
  })

  it('renders the photo when available', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      const photo = screen.getByAltText('Carlos A. Jiménez Hirashi') as HTMLImageElement
      expect(photo.src).toContain(mockAbout.photo_url)
    })
  })

  it('renders "Hablemos" and "Ver proyectos" hero CTAs', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getAllByRole('link', { name: 'Hablemos' })[0]).toHaveAttribute('href', '/contact')
      expect(screen.getByRole('link', { name: 'Ver proyectos' })).toHaveAttribute('href', '/projects')
    })
  })

  it('renders bio_summary and unique_value_proposition', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.bio_summary!)).toBeInTheDocument()
      expect(screen.getByText(mockAbout.unique_value_proposition!)).toBeInTheDocument()
    })
  })

  it('renders sections in order: Experiencia, then Habilidades Técnicas, then Certificaciones', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Experiencia')).toBeInTheDocument()
    })

    const headings = Array.from(container.querySelectorAll('h2')).map(h => h.textContent)
    const experienciaIdx = headings.indexOf('Experiencia')
    const habilidadesIdx = headings.indexOf('Habilidades Técnicas')
    const certificacionesIdx = headings.indexOf('Certificaciones')

    expect(experienciaIdx).toBeGreaterThanOrEqual(0)
    expect(experienciaIdx).toBeLessThan(habilidadesIdx)
    expect(habilidadesIdx).toBeLessThan(certificacionesIdx)
  })

  it('renders work_history entries with company and role', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.work_history[0].role_title)).toBeInTheDocument()
      expect(screen.getByText(mockAbout.work_history[0].company)).toBeInTheDocument()
    })
  })

  it('renders skills grouped by category', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      mockAbout.skill_groups.forEach(group => {
        expect(screen.getByText(group.category)).toBeInTheDocument()
        group.skills.forEach(skill => {
          expect(screen.getByText(skill)).toBeInTheDocument()
        })
      })
    })
  })

  it('renders certifications', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.certifications[0].name)).toBeInTheDocument()
    })
  })

  it('renders the footer CTA', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('¿Un sistema que no puede fallar?')).toBeInTheDocument()
    })
  })

  it('shows loading spinner initially', () => {
    vi.mocked(aboutApi.getAbout).mockImplementation(() => new Promise(() => {}))

    render(<AboutPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when the about content fails to load', async () => {
    vi.mocked(aboutApi.getAbout).mockRejectedValue(new Error('Failed'))

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudo cargar el contenido de Sobre Mí/i)).toBeInTheDocument()
    })
  })

  it('gracefully omits sections whose data is empty', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue({
      ...mockAbout,
      certifications: [],
      work_history: [],
      skill_groups: [],
    })

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.professional_tagline!)).toBeInTheDocument()
    })
    expect(screen.queryByText('Certificaciones')).not.toBeInTheDocument()
    expect(screen.queryByText('Experiencia')).not.toBeInTheDocument()
    expect(screen.queryByText('Habilidades Técnicas')).not.toBeInTheDocument()
  })
})
