import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { Navbar } from '@/components/Navbar'
import { useAuthStore } from '@/stores/authStore'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: useAuthStore.getState().user,
  }),
}))

describe('Navbar', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    useAuthStore.setState({ user: mockUser })
    mockLogout.mockClear()
  })

  describe('rendering', () => {
    it('should render navbar header', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('Welcome to Admin Panel')).toBeInTheDocument()
    })

    it('should render user welcome message', () => {
      render(<Navbar onLogout={mockLogout} />)
      const title = screen.getByText('Welcome to Admin Panel')
      expect(title).toBeInTheDocument()
    })

    it('should render user avatar with initial', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('D')).toBeInTheDocument() // First letter of 'demo'
    })

    it('should display user full name', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('Demo User')).toBeInTheDocument()
    })

    it('should display user email', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('demo@example.com')).toBeInTheDocument()
    })
  })

  describe('user avatar', () => {
    it('should show first letter of username in avatar', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('D')).toBeInTheDocument()
    })

    it('should use cyan background for avatar', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const avatar = container.querySelector('.bg-cyan-600')
      expect(avatar).toBeInTheDocument()
    })

    it('should fallback to U when no username', () => {
      useAuthStore.setState({ user: { ...mockUser, username: '' } })
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByText('U')).toBeInTheDocument()
    })
  })

  describe('dropdown menu', () => {
    it('should not show dropdown by default', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.queryByText('Profile Settings')).not.toBeInTheDocument()
    })

    it('should open dropdown when user menu clicked', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)
      expect(screen.getByText('Profile Settings')).toBeInTheDocument()
    })

    it('should close dropdown when clicked again', async () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')

      fireEvent.click(menuButton)
      expect(screen.getByText('Profile Settings')).toBeInTheDocument()

      fireEvent.click(menuButton)
      await waitFor(() => {
        expect(screen.queryByText('Profile Settings')).not.toBeInTheDocument()
      })
    })

    it('should display dropdown menu items', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      expect(screen.getByText('Profile Settings')).toBeInTheDocument()
      expect(screen.getByText('Change Password')).toBeInTheDocument()
      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    it('should show user info in dropdown header', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      // The dropdown should have user info duplicated
      const userEmails = screen.getAllByText('demo@example.com')
      expect(userEmails.length).toBeGreaterThan(1)
    })
  })

  describe('dropdown links', () => {
    it('should have profile settings link', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const profileLink = screen.getByRole('link', { name: /Profile Settings/i })
      expect(profileLink).toHaveAttribute('href', '/profile')
    })

    it('should have change password link', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const passwordLink = screen.getByRole('link', { name: /Change Password/i })
      expect(passwordLink).toHaveAttribute('href', '/change-password')
    })
  })

  describe('logout functionality', () => {
    it('should call logout callback when logout button clicked', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const logoutButton = screen.getByRole('button', { name: /Logout/i })
      fireEvent.click(logoutButton)

      expect(mockLogout).toHaveBeenCalled()
    })

    it('should close dropdown after logout', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      expect(screen.getByText('Profile Settings')).toBeInTheDocument()

      const logoutButton = screen.getByRole('button', { name: /Logout/i })
      fireEvent.click(logoutButton)

      // The dropdown menu items should be hidden
      expect(screen.queryByText('Profile Settings')).not.toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('should have header with border', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const header = container.querySelector('header')
      expect(header?.className).toContain('border-b')
      expect(header?.className).toContain('border-slate-200')
    })

    it('should use slate colors for text', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const title = container.querySelector('h1')
      expect(title?.className).toContain('text-slate-900')
    })

    it('should have flex layout for navbar content', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const navContent = container.querySelector('.flex.items-center.justify-between')
      expect(navContent).toBeInTheDocument()
    })

    it('should have hover effects on dropdown items', () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const profileLink = screen.getByRole('link', { name: /Profile Settings/i })
      expect(profileLink?.className).toContain('hover:bg-slate-100')
    })
  })

  describe('responsive behavior', () => {
    it('should display dropdown on right side', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const dropdown = container.querySelector('.absolute.right-0')
      expect(dropdown).toBeInTheDocument()
    })

    it('should have z-index for dropdown visibility', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const menuButton = screen.getByRole('button')
      fireEvent.click(menuButton)

      const dropdown = container.querySelector('.z-50')
      expect(dropdown).toBeInTheDocument()
    })
  })
})
