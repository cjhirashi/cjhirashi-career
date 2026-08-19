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

  it('renders the page heading', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Sobre Mí')).toBeInTheDocument()
    })
  })

  it('renders the professional tagline', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockAbout.professional_tagline!)).toBeInTheDocument()
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

  it('renders the photo when available', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      const photo = screen.getByAltText('Carlos Jiménez Hirashi') as HTMLImageElement
      expect(photo.src).toContain(mockAbout.photo_url)
    })
  })

  it('renders all four IKIGAI dimensions with translated labels', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Mi IKIGAI')).toBeInTheDocument()
      expect(screen.getByText('Pasión')).toBeInTheDocument()
      expect(screen.getByText('Profesión')).toBeInTheDocument()
      expect(screen.getByText('Vocación')).toBeInTheDocument()
      expect(screen.getByText('Misión')).toBeInTheDocument()
    })
  })

  it('renders values as a list', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      mockAbout.values.forEach(value => {
        expect(screen.getByText(value)).toBeInTheDocument()
      })
    })
  })

  it('renders interests/hobbies as badges', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      mockAbout.interests_hobbies.forEach(item => {
        expect(screen.getByText(item)).toBeInTheDocument()
      })
    })
  })

  it('renders the Technical Skills section with all competencies', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Habilidades Técnicas')).toBeInTheDocument()
      mockAbout.competencies.forEach(skill => {
        expect(screen.getByText(skill.name)).toBeInTheDocument()
      })
    })
  })

  it('renders certifications', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Certificaciones')).toBeInTheDocument()
      expect(screen.getByText(mockAbout.certifications[0].name)).toBeInTheDocument()
    })
  })

  it('renders the experience timeline from work_history', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Experiencia')).toBeInTheDocument()
      expect(screen.getByText(mockAbout.work_history[0].role_title)).toBeInTheDocument()
      expect(screen.getByText(mockAbout.work_history[0].company)).toBeInTheDocument()
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

  it('renders the photo in a sticky container', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      expect(container.querySelector('.sticky')).toBeInTheDocument()
    })
  })

  it('renders timeline dots for experience', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue(mockAbout)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      const dots = container.querySelectorAll('.rounded-full.bg-cyan-600')
      expect(dots.length).toBeGreaterThan(0)
    })
  })

  it('gracefully omits sections whose data is empty', async () => {
    vi.mocked(aboutApi.getAbout).mockResolvedValue({
      ...mockAbout,
      values: [],
      interests_hobbies: [],
      certifications: [],
      work_history: [],
    })

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Sobre Mí')).toBeInTheDocument()
    })
    expect(screen.queryByText('Certificaciones')).not.toBeInTheDocument()
    expect(screen.queryByText('Experiencia')).not.toBeInTheDocument()
  })
})
