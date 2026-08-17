import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import * as identityApi from '@/api/identity'
import * as projectsApi from '@/api/projects'
import * as trackingApi from '@/api/tracking'
import { HomePage } from '@/pages/HomePage'
import { mockIdentity, mockCompetencies, mockFeaturedProjects } from '../fixtures/mockData'

vi.mock('@/api/identity')
vi.mock('@/api/projects')
vi.mock('@/api/tracking')

describe('HomePage - Entry Point', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders hero section with identity data', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(mockIdentity.name)).toBeInTheDocument()
    })
    expect(screen.getByText(mockIdentity.title)).toBeInTheDocument()
    expect(screen.getByText(mockIdentity.tagline)).toBeInTheDocument()
  })

  it('renders avatar image when available', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      const avatar = screen.getByAltText(mockIdentity.name) as HTMLImageElement
      expect(avatar).toBeInTheDocument()
      expect(avatar.src).toContain(mockIdentity.avatar)
    })
  })

  it('renders quick stats section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/10\+/)).toBeInTheDocument()
      expect(screen.getByText(/50\+/)).toBeInTheDocument()
      expect(screen.getByText(/Years of Experience/i)).toBeInTheDocument()
      expect(screen.getByText(/Projects Completed/i)).toBeInTheDocument()
      expect(screen.getByText(/Technical Skills/i)).toBeInTheDocument()
    })
  })

  it('displays competencies count in stats', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(`${mockCompetencies.length}+`)).toBeInTheDocument()
    })
  })

  it('renders "Why Work With Me" section with differentiators', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Expert Architecture/)).toBeInTheDocument()
      expect(screen.getByText(/Full-Stack Expertise/)).toBeInTheDocument()
      expect(screen.getByText(/Problem Solver/)).toBeInTheDocument()
    })
  })

  it('renders featured projects section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Featured Projects/)).toBeInTheDocument()
      expect(screen.getByText('E-Commerce Platform')).toBeInTheDocument()
      expect(screen.getByText('SaaS Dashboard')).toBeInTheDocument()
    })
  })

  it('displays featured badge on featured projects', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      const badges = screen.getAllByText(/Featured/)
      expect(badges.length).toBeGreaterThan(0)
    })
  })

  it('renders CTA buttons for navigation', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /View Portfolio/i })).toHaveAttribute('href', '/projects')
      expect(screen.getByRole('link', { name: /Get in Touch/i })).toHaveAttribute('href', '/contact')
    })
  })

  it('renders final CTA section', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Ready to work together/i)).toBeInTheDocument()
      expect(screen.getByText(/Start a Conversation/i)).toBeInTheDocument()
    })
  })

  it('tracks clicks on portfolio CTA button', async () => {
    const user = userEvent.setup()
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Featured Projects/)).toBeInTheDocument()
    })

    const portfolioButton = screen.getByRole('link', { name: /View Portfolio/i })
    await user.click(portfolioButton)

    // Tracking should have been called (mocked)
    expect(trackingApi.trackEvent).toHaveBeenCalled()
  })

  it('shows loading spinner initially', () => {
    vi.mocked(identityApi.getIdentity).mockImplementation(
      () => new Promise(() => {})
    )
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows error message when identity fails to load', async () => {
    vi.mocked(identityApi.getIdentity).mockRejectedValue(new Error('Failed'))
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Failed to load profile/i)).toBeInTheDocument()
    })
  })

  it('shows error message when projects fail to load', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockRejectedValue(new Error('Failed'))
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText(/Featured Projects/)).toBeInTheDocument()
      expect(screen.getByText(/Failed to load projects/i)).toBeInTheDocument()
    })
  })

  it('uses default data when identity is missing', async () => {
    const incompleteIdentity = {
      ...mockIdentity,
      avatar: undefined,
      name: undefined,
    }
    vi.mocked(identityApi.getIdentity).mockResolvedValue(incompleteIdentity as any)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      expect(screen.getByText('Carlos Jiménez Hirashi')).toBeInTheDocument()
      expect(screen.getByText('Solutions Architect')).toBeInTheDocument()
    })
  })

  it('renders all featured projects in featured mode', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      mockFeaturedProjects.forEach(project => {
        expect(screen.getByText(project.title)).toBeInTheDocument()
      })
    })
  })

  it('renders view all projects link', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      const viewAllLinks = screen.getAllByRole('link', { name: /View All/i })
      expect(viewAllLinks.length).toBeGreaterThan(0)
    })
  })

  it('renders hero section in gradient background', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    const { container } = render(<HomePage />)

    const heroSection = container.querySelector('.bg-gradient-to-br')
    expect(heroSection).toBeInTheDocument()
  })

  it('navigates to contact page on CTA click', async () => {
    vi.mocked(identityApi.getIdentity).mockResolvedValue(mockIdentity)
    vi.mocked(projectsApi.getFeaturedProjects).mockResolvedValue(mockFeaturedProjects)
    vi.mocked(identityApi.getCompetencies).mockResolvedValue(mockCompetencies)

    render(<HomePage />)

    await waitFor(() => {
      const contactLinks = screen.getAllByRole('link', { name: /Get in Touch|Start a Conversation/i })
      expect(contactLinks.length).toBeGreaterThan(0)
      contactLinks.forEach(link => {
        expect(link).toHaveAttribute('href', '/contact')
      })
    })
  })
})
