import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import * as identityApi from '@/api/identity'
import { AboutPage } from '@/pages/AboutPage'
import { mockIdentity, mockCompetencies } from '../fixtures/mockData'

vi.mock('@/api/identity')

describe('AboutPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders About Me heading', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('About Me')).toBeInTheDocument()
    })
  })

  it('renders bio from identity', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockIdentity.bio)).toBeInTheDocument()
    })
  })

  it('renders avatar image', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      const avatar = screen.getByAltText(mockIdentity.name) as HTMLImageElement
      expect(avatar).toBeInTheDocument()
      expect(avatar.src).toContain(mockIdentity.avatar)
    })
  })

  it('renders name and title in info box', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockIdentity.name)).toBeInTheDocument()
      expect(screen.getByText(mockIdentity.title)).toBeInTheDocument()
    })
  })

  it('renders location in info box', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(mockIdentity.location)).toBeInTheDocument()
    })
  })

  it('renders IKIGAI section with all four pillars', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('My IKIGAI')).toBeInTheDocument()
      if (mockIdentity.ikigai) {
        expect(screen.getByText(mockIdentity.ikigai.passion)).toBeInTheDocument()
        expect(screen.getByText(mockIdentity.ikigai.profession)).toBeInTheDocument()
        expect(screen.getByText(mockIdentity.ikigai.vocation)).toBeInTheDocument()
        expect(screen.getByText(mockIdentity.ikigai.mission)).toBeInTheDocument()
      }
    })
  })

  it('renders IKIGAI labels correctly formatted', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(/passion/i)).toBeInTheDocument()
      expect(screen.getByText(/profession/i)).toBeInTheDocument()
      expect(screen.getByText(/vocation/i)).toBeInTheDocument()
      expect(screen.getByText(/mission/i)).toBeInTheDocument()
    })
  })

  it('renders Core Values section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Core Values')).toBeInTheDocument()
      expect(screen.getByText(/Excellence in technical delivery/)).toBeInTheDocument()
      expect(screen.getByText(/Continuous learning and growth/)).toBeInTheDocument()
      expect(screen.getByText(/Collaboration and communication/)).toBeInTheDocument()
      expect(screen.getByText(/Ethical and sustainable solutions/)).toBeInTheDocument()
    })
  })

  it('renders checkmark icons for core values', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      const svgs = container.querySelectorAll('svg')
      // Should have checkmark SVGs for values
      expect(svgs.length).toBeGreaterThan(0)
    })
  })

  it('renders Technical Skills section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Technical Skills')).toBeInTheDocument()
    })
  })

  it('displays all competencies as skill tags', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      mockCompetencies.forEach(skill => {
        expect(screen.getByText(skill)).toBeInTheDocument()
      })
    })
  })

  it('renders Experience section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('Experience')).toBeInTheDocument()
    })
  })

  it('displays experience timeline items', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(/2020-Present/)).toBeInTheDocument()
      expect(screen.getByText(/Senior Solutions Architect/)).toBeInTheDocument()
      expect(screen.getByText(/Tech Company/)).toBeInTheDocument()
    })
  })

  it('shows loading spinner initially', () => {
    vi.mocked(identityApi.getIdentity).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when identity fails to load', async () => {
    vi.mocked(identityApi.getIdentity).mockRejectedValue(new Error('Failed'))
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load profile/i)).toBeInTheDocument()
    })
  })

  it('renders avatar in sticky position', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      const stickyDiv = container.querySelector('.sticky')
      expect(stickyDiv).toBeInTheDocument()
    })
  })

  it('displays timeline dots for experience', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      const dots = container.querySelectorAll('.rounded-full.bg-cyan-600')
      expect(dots.length).toBeGreaterThan(0)
    })
  })

  it('displays year labels for experience items', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<AboutPage />)

    await waitFor(() => {
      expect(screen.getByText('2020-Present')).toBeInTheDocument()
      expect(screen.getByText('2018-2020')).toBeInTheDocument()
      expect(screen.getByText('2015-2018')).toBeInTheDocument()
    })
  })

  it('renders grid layout for about content', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    const { container } = render(<AboutPage />)

    await waitFor(() => {
      const grids = container.querySelectorAll('.grid')
      expect(grids.length).toBeGreaterThan(0)
    })
  })
})
