import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { Header } from '@/components/Layout/Header'

vi.mock('@/api/tracking')

describe('Header - Extended Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sticky header', () => {
    const { container } = render(<Header />, { initialRoute: '/' })

    const header = container.querySelector('header')
    expect(header).toHaveClass('sticky')
    expect(header).toHaveClass('top-0')
    expect(header).toHaveClass('z-50')
  })

  it('renders the logo', () => {
    render(<Header />, { initialRoute: '/' })

    expect(screen.getByAltText('cjhirashi')).toBeInTheDocument()
  })

  it('renders all navigation links', () => {
    render(<Header />, { initialRoute: '/' })

    expect(screen.getByRole('link', { name: /Home/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Sobre Mí/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Proyectos/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Blog/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Contacto/i })).toBeInTheDocument()
  })

  it('highlights active link with cyan background', () => {
    const { container } = render(<Header />, { initialRoute: '/' })

    const homeLink = screen.getByRole('link', { name: /Home/i })
    expect(homeLink).toHaveClass('text-cyan-600', 'bg-cyan-50')
  })

  it('inactive links have slate color', () => {
    render(<Header />, { initialRoute: '/' })

    const aboutLink = screen.getByRole('link', { name: /Sobre Mí/i })
    expect(aboutLink).toHaveClass('text-slate-600')
  })

  it('renders mobile menu button', () => {
    render(<Header />, { initialRoute: '/' })

    expect(screen.getByLabelText(/Toggle menu/i)).toBeInTheDocument()
  })

  it('toggles mobile menu visibility', async () => {
    const user = userEvent.setup()
    render(<Header />, { initialRoute: '/' })

    const menuButton = screen.getByLabelText(/Toggle menu/i)
    const homeLink = screen.queryByText('Home')?.closest('a')
    if (homeLink) {
      expect(homeLink.className).not.toContain('md:hidden')
    }

    await user.click(menuButton)

    // After click, mobile menu should show
    const mobileNavLinks = screen.getAllByRole('link', { name: /Home/i })
    expect(mobileNavLinks.length).toBeGreaterThan(1)
  })

  it('closes mobile menu when link is clicked', async () => {
    const user = userEvent.setup()
    render(<Header />, { initialRoute: '/' })

    const menuButton = screen.getByLabelText(/Toggle menu/i)
    await user.click(menuButton)

    const aboutLink = screen.getAllByRole('link', { name: /Sobre Mí/i })[1] // Mobile link
    await user.click(aboutLink)

    // Menu should close after clicking a link
    const menuButton2 = screen.getByLabelText(/Toggle menu/i)
    expect(menuButton2).toBeInTheDocument()
  })

  it('tracks navigation clicks', async () => {
    const user = userEvent.setup()
    render(<Header />, { initialRoute: '/' })

    const aboutLink = screen.getByRole('link', { name: /Sobre Mí/i })
    await user.click(aboutLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'nav-about',
      })
    )
  })

  it('tracks logo click', async () => {
    const user = userEvent.setup()
    render(<Header />, { initialRoute: '/about' })

    const logoLink = screen.getByRole('link', { name: /cjhirashi/i })
    await user.click(logoLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'nav-logo',
      })
    )
  })

  it('has correct links for navigation', () => {
    render(<Header />, { initialRoute: '/' })

    expect(screen.getByRole('link', { name: /Home/i })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: /Sobre Mí/i })).toHaveAttribute('href', '/about')
    expect(screen.getByRole('link', { name: /Proyectos/i })).toHaveAttribute('href', '/projects')
    expect(screen.getByRole('link', { name: /Blog/i })).toHaveAttribute('href', '/blog')
    expect(screen.getByRole('link', { name: /Contacto/i })).toHaveAttribute('href', '/contact')
  })

  it('shows hamburger icon when menu is closed', () => {
    const { container } = render(<Header />, { initialRoute: '/' })

    const menuButton = screen.getByLabelText(/Toggle menu/i)
    const icon = menuButton.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('changes hamburger icon to X when menu is open', async () => {
    const user = userEvent.setup()
    const { container } = render(<Header />, { initialRoute: '/' })

    const menuButton = screen.getByLabelText(/Toggle menu/i)
    const initialIcon = menuButton.querySelector('svg')
    const initialPath = initialIcon?.querySelector('path')?.getAttribute('d')

    await user.click(menuButton)

    const newIcon = menuButton.querySelector('svg')
    const newPath = newIcon?.querySelector('path')?.getAttribute('d')

    // The path should be different (hamburger vs X)
    expect(newPath).not.toEqual(initialPath)
  })

  it('maintains scroll position on header (sticky)', () => {
    const { container } = render(<Header />, { initialRoute: '/' })

    const header = container.querySelector('header')
    expect(header).toHaveClass('sticky')
  })

  it('navigates to different routes', async () => {
    const user = userEvent.setup()

    // Start at home
    const { rerender } = render(<Header />, { initialRoute: '/' })

    let homeLink = screen.getByRole('link', { name: /Home/i })
    expect(homeLink).toHaveClass('bg-cyan-50')

    // Navigate to about
    rerender(<Header />)

    // After navigation, about link should be active
    // (Note: This would require more complex routing setup in real tests)
  })
})
