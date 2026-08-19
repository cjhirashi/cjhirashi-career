import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { Footer } from '@/components/Layout/Footer'

vi.mock('@/api/tracking')

describe('Footer Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders footer brand information', () => {
    render(<Footer />)

    expect(screen.getByText('Carlos Jiménez Hirashi')).toBeInTheDocument()
    expect(screen.getByText(/Solutions Architect & Portfolio Professional/)).toBeInTheDocument()
  })

  it('renders Navigation section', () => {
    render(<Footer />)

    expect(screen.getByText('Navigation')).toBeInTheDocument()
  })

  it('renders Resources section', () => {
    render(<Footer />)

    expect(screen.getByText('Resources')).toBeInTheDocument()
  })

  it('renders Follow section', () => {
    render(<Footer />)

    expect(screen.getByText('Follow')).toBeInTheDocument()
  })

  it('renders navigation links in footer', () => {
    render(<Footer />)

    const homeLink = screen.getByRole('link', { name: /Home/ })
    const aboutLink = screen.getByRole('link', { name: /About/ })
    const projectsLink = screen.getByRole('link', { name: /Projects/ })

    expect(homeLink).toHaveAttribute('href', '/')
    expect(aboutLink).toHaveAttribute('href', '/about')
    expect(projectsLink).toHaveAttribute('href', '/projects')
  })

  it('renders resources links', () => {
    render(<Footer />)

    expect(screen.getByRole('link', { name: /Blog/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Contact/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Sitemap/ })).toBeInTheDocument()
  })

  it('renders social media links', () => {
    render(<Footer />)

    expect(screen.getByRole('link', { name: /GitHub/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /LinkedIn/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Twitter/i })).toBeInTheDocument()
  })

  it('social links open in new tab', () => {
    render(<Footer />)

    const githubLink = screen.getByRole('link', { name: /GitHub/i })
    expect(githubLink).toHaveAttribute('target', '_blank')
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders copyright information', () => {
    render(<Footer />)

    expect(screen.getByText(/© 2024 Carlos Jiménez Hirashi/)).toBeInTheDocument()
    expect(screen.getByText(/All rights reserved/)).toBeInTheDocument()
  })

  it('renders footer links', () => {
    render(<Footer />)

    expect(screen.getByRole('link', { name: /Privacy/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Terms/i })).toBeInTheDocument()
  })

  it('tracks social media clicks', async () => {
    const user = userEvent.setup()
    render(<Footer />)

    const githubLink = screen.getByRole('link', { name: /GitHub/i })
    await user.click(githubLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'social-github',
      })
    )
  })

  it('tracks all social links individually', async () => {
    const user = userEvent.setup()
    render(<Footer />)

    const linkedinLink = screen.getByRole('link', { name: /LinkedIn/i })
    await user.click(linkedinLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'social-linkedin',
      })
    )

    vi.clearAllMocks()

    const twitterLink = screen.getByRole('link', { name: /Twitter/i })
    await user.click(twitterLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'social-twitter',
      })
    )
  })

  it('displays social icons', () => {
    const { container } = render(<Footer />)

    // Check for text emojis representing social icons
    expect(screen.getByText('📱')).toBeInTheDocument()
    expect(screen.getByText('💼')).toBeInTheDocument()
    expect(screen.getByText('🐦')).toBeInTheDocument()
  })

  it('renders with the Glass Steel section-alt treatment', () => {
    const { container } = render(<Footer />)

    const footer = container.querySelector('footer')
    expect(footer).toHaveClass('section-alt')
    expect(footer).toHaveClass('text-text-secondary')
  })

  it('applies hover effects to navigation links', () => {
    const { container } = render(<Footer />)

    const links = container.querySelectorAll('a.hover\\:text-primary')
    expect(links.length).toBeGreaterThan(0)
  })

  it('displays footer in grid layout', () => {
    const { container } = render(<Footer />)

    const grid = container.querySelector('.grid')
    expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-4')
  })

  it('separates footer sections with divider', () => {
    const { container } = render(<Footer />)

    const divider = container.querySelector('.border-t.border-border')
    expect(divider).toBeInTheDocument()
  })

  it('maintains internal links for navigation', () => {
    render(<Footer />)

    const homeLink = screen.getByRole('link', { name: /Home/ })
    expect(homeLink).toHaveAttribute('href', '/')
    expect(homeLink).not.toHaveAttribute('target')
  })

  it('renders proper spacing and padding', () => {
    const { container } = render(<Footer />)

    const spacer = container.querySelector('.py-12')
    expect(spacer).toBeInTheDocument()
  })
})
