import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../utils'
import { DashboardPage } from '@/pages/DashboardPage'
import { useAuthStore } from '@/stores/authStore'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: useAuthStore.getState().user,
    accessToken: useAuthStore.getState().accessToken,
    isAuthenticated: useAuthStore.getState().isAuthenticated,
  }),
}))

describe('DashboardPage', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: mockUser,
      isAuthenticated: true,
      accessToken: 'token123',
    })
  })

  describe('rendering', () => {
    it('should render dashboard page with title', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })

    it('should display welcome message with user name', () => {
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back, Demo User!/i)).toBeInTheDocument()
    })

    it('should render quick stats section', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Total Skills')).toBeInTheDocument()
      expect(screen.getByText('Projects')).toBeInTheDocument()
      expect(screen.getByText('Positions')).toBeInTheDocument()
      expect(screen.getByText('Contacts')).toBeInTheDocument()
    })

    it('should display initial stat counts as 0', () => {
      render(<DashboardPage />)
      const statNumbers = screen.getAllByText('0')
      expect(statNumbers.length).toBeGreaterThan(0)
    })
  })

  describe('quick stats cards', () => {
    it('should render all four stat cards', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Total Skills')).toBeInTheDocument()
      expect(screen.getByText('Projects')).toBeInTheDocument()
      expect(screen.getByText('Positions')).toBeInTheDocument()
      expect(screen.getByText('Contacts')).toBeInTheDocument()
    })

    it('should display helpful messages for each stat', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Add your competencies')).toBeInTheDocument()
      expect(screen.getByText('Showcase your work')).toBeInTheDocument()
      expect(screen.getByText('Document your experience')).toBeInTheDocument()
      expect(screen.getByText('Build your network')).toBeInTheDocument()
    })

    it('should have a Lucide icon for each quick-stat card', () => {
      const { container } = render(<DashboardPage />)
      const statCards = container.querySelectorAll('.stat-card')
      expect(statCards.length).toBeGreaterThanOrEqual(4)
      statCards.forEach((card) => {
        expect(card.querySelector('svg')).toBeInTheDocument()
      })
    })
  })

  describe('getting started section', () => {
    it('should render getting started guide', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Getting Started')).toBeInTheDocument()
    })

    it('should display three getting started steps', () => {
      render(<DashboardPage />)
      expect(screen.getByText('Set Your Professional Identity')).toBeInTheDocument()
      expect(screen.getByText('Document Your Competencies')).toBeInTheDocument()
      expect(screen.getByText('Showcase Your Evidence')).toBeInTheDocument()
    })

    it('should include step descriptions', () => {
      render(<DashboardPage />)
      expect(screen.getByText(/Define your IKIGAI/i)).toBeInTheDocument()
      expect(screen.getByText(/Add technical, transferable, and business skills/i)).toBeInTheDocument()
      expect(screen.getByText(/Add projects, positions, achievements, and STAR cases/i)).toBeInTheDocument()
    })
  })

  describe('navigation links', () => {
    it('should have link to identity page', () => {
      render(<DashboardPage />)
      const identityLink = screen.getByRole('link', { name: /Go to Identity/i })
      expect(identityLink).toHaveAttribute('href', '/identity')
    })

    it('should have link to competencies page', () => {
      render(<DashboardPage />)
      const competenciesLink = screen.getByRole('link', { name: /Go to Competencies/i })
      expect(competenciesLink).toHaveAttribute('href', '/competencies')
    })

    it('should have link to evidence page', () => {
      render(<DashboardPage />)
      const evidenceLink = screen.getByRole('link', { name: /Go to Evidence/i })
      expect(evidenceLink).toHaveAttribute('href', '/evidence')
    })

    it('should all links have correct navigation arrows', () => {
      render(<DashboardPage />)
      const links = screen.getAllByText(/→/)
      expect(links.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('styling and structure', () => {
    it('should have proper heading hierarchy', () => {
      const { container } = render(<DashboardPage />)
      const headings = container.querySelectorAll('h1, h2, h3')
      expect(headings.length).toBeGreaterThan(0)
    })

    it('should use cyan color for numbered circles', () => {
      const { container } = render(<DashboardPage />)
      const circles = container.querySelectorAll('.bg-cyan-100')
      expect(circles.length).toBeGreaterThanOrEqual(3)
    })

    it('should have proper card styling', () => {
      const { container } = render(<DashboardPage />)
      const cards = container.querySelectorAll('.card')
      expect(cards.length).toBeGreaterThan(0)
    })
  })

  describe('responsive layout', () => {
    it('should render grid layout for stats', () => {
      const { container } = render(<DashboardPage />)
      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4')
    })

    it('should have proper spacing', () => {
      const { container } = render(<DashboardPage />)
      // el bloque de encabezado (título + saludo) lleva `mb-8`
      const header = container.querySelector('h1')?.closest('.mb-8')
      expect(header).not.toBeNull()
    })
  })

  describe('user context', () => {
    it('should display authenticated user information', () => {
      render(<DashboardPage />)
      expect(screen.getByText(/Demo User/i)).toBeInTheDocument()
    })

    it('should handle different user names', () => {
      useAuthStore.setState({
        user: { ...mockUser, full_name: 'John Doe' },
      })
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back, John Doe!/i)).toBeInTheDocument()
    })

    it('should handle null user gracefully', () => {
      useAuthStore.setState({ user: null })
      render(<DashboardPage />)
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument()
    })
  })
})
