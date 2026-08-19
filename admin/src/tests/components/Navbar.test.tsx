import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render as baseRender, screen, fireEvent, waitFor } from '../utils'
import { Navbar } from '@/components/Navbar'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: useAuthStore.getState().user,
  }),
}))

// Navbar renders a react-router <Link>, so it needs a Router in the tree.
const render = (ui: React.ReactElement) => baseRender(<MemoryRouter>{ui}</MemoryRouter>)

const getUserMenuButton = () => screen.getByRole('button', { name: 'User menu' })

describe('Navbar', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    useAuthStore.setState({ user: mockUser })
    useThemeStore.setState({ theme: 'system', resolvedTheme: 'light' })
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
      expect(screen.getAllByText('demo@example.com').length).toBeGreaterThan(0)
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

  describe('theme toggle', () => {
    it('should always render the theme toggle (not hidden in dropdown)', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByRole('group', { name: 'Tema' })).toBeInTheDocument()
    })

    it('should render the three theme options', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.getByRole('button', { name: 'Tema claro' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Tema del sistema' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Tema oscuro' })).toBeInTheDocument()
    })

    it('should switch theme when a theme option is clicked', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(screen.getByRole('button', { name: 'Tema oscuro' }))
      expect(useThemeStore.getState().theme).toBe('dark')
    })

    it('should also render a theme toggle inside the user dropdown, for mobile', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())
      // One standalone (tablet/desktop) + one inside the dropdown (mobile).
      expect(screen.getAllByRole('group', { name: 'Tema' })).toHaveLength(2)
    })
  })

  describe('mobile menu toggle', () => {
    it('should not render a hamburger button when onMenuToggle is not provided', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.queryByRole('button', { name: /abrir menú/i })).not.toBeInTheDocument()
    })

    it('should render a hamburger button when onMenuToggle is provided', () => {
      const onMenuToggle = vi.fn()
      render(<Navbar onLogout={mockLogout} onMenuToggle={onMenuToggle} />)
      const button = screen.getByRole('button', { name: /abrir menú/i })
      fireEvent.click(button)
      expect(onMenuToggle).toHaveBeenCalled()
    })
  })

  describe('dropdown menu', () => {
    it('should not show dropdown by default', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.queryByText('Change Password')).not.toBeInTheDocument()
    })

    it('should open dropdown when user menu clicked', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())
      expect(screen.getByText('Change Password')).toBeInTheDocument()
    })

    it('should close dropdown when clicked again', async () => {
      render(<Navbar onLogout={mockLogout} />)
      const menuButton = getUserMenuButton()

      fireEvent.click(menuButton)
      expect(screen.getByText('Change Password')).toBeInTheDocument()

      fireEvent.click(menuButton)
      await waitFor(() => {
        expect(screen.queryByText('Change Password')).not.toBeInTheDocument()
      })
    })

    it('should display dropdown menu items', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      expect(screen.getByText('Change Password')).toBeInTheDocument()
      expect(screen.getByText('Logout')).toBeInTheDocument()
    })

    it('should show user info in dropdown header', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      // The dropdown should have user info duplicated
      const userEmails = screen.getAllByText('demo@example.com')
      expect(userEmails.length).toBeGreaterThan(1)
    })

    it('should use the near-opaque popover background, not the translucent card one', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const dropdown = container.querySelector('.absolute.right-0')
      expect(dropdown).toHaveStyle({ backgroundColor: 'var(--bg-popover)' })
    })
  })

  describe('dropdown links', () => {
    it('should have change password link', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const passwordLink = screen.getByRole('link', { name: /Change Password/i })
      expect(passwordLink).toHaveAttribute('href', '/change-password')
    })
  })

  describe('logout functionality', () => {
    it('should call logout callback when logout button clicked', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const logoutButton = screen.getByRole('button', { name: /Logout/i })
      fireEvent.click(logoutButton)

      expect(mockLogout).toHaveBeenCalled()
    })

    it('should close dropdown after logout', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      expect(screen.getByText('Change Password')).toBeInTheDocument()

      const logoutButton = screen.getByRole('button', { name: /Logout/i })
      fireEvent.click(logoutButton)

      // The dropdown menu items should be hidden
      expect(screen.queryByText('Change Password')).not.toBeInTheDocument()
    })
  })

  describe('right panel toggle', () => {
    it('should only be visible on mobile - md and up use the lateral edge tab instead', () => {
      render(<Navbar onLogout={mockLogout} onRightPanelToggle={vi.fn()} rightPanelOpen />)
      const toggle = screen.getByRole('button', { name: /panel de asistencia/i })
      expect(toggle.className).toContain('md:hidden')
    })

    it('should not render when onRightPanelToggle is not provided', () => {
      render(<Navbar onLogout={mockLogout} />)
      expect(screen.queryByRole('button', { name: /panel de asistencia/i })).not.toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('should have header with border', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const header = container.querySelector('header')
      expect(header?.className).toContain('border-b')
      expect(header?.className).toContain('border-border')
    })

    it('should render as a glass (blurred, translucent) panel', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const header = container.querySelector('header')
      expect(header?.className).toContain('glass-panel')
      expect(header?.className).toMatch(/backdrop-blur/)
    })

    it('should use the semantic text token for the title', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const title = container.querySelector('h1')
      expect(title?.className).toContain('text-text')
    })

    it('should have flex layout for navbar content', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      const navContent = container.querySelector('.flex.items-center.justify-between')
      expect(navContent).toBeInTheDocument()
    })

    it('should have hover effects on dropdown items', () => {
      render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const passwordLink = screen.getByRole('link', { name: /Change Password/i })
      expect(passwordLink?.className).toContain('hover:bg-glass')
    })
  })

  describe('responsive behavior', () => {
    it('should display dropdown on right side', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const dropdown = container.querySelector('.absolute.right-0')
      expect(dropdown).toBeInTheDocument()
    })

    it('should have z-index for dropdown visibility', () => {
      const { container } = render(<Navbar onLogout={mockLogout} />)
      fireEvent.click(getUserMenuButton())

      const dropdown = container.querySelector('.z-50')
      expect(dropdown).toBeInTheDocument()
    })
  })
})
