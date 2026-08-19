import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { contactApi } from '@/api/contact'
import { Footer } from '@/components/Layout/Footer'
import { mockContact } from '../fixtures/mockData'

vi.mock('@/api/tracking')
vi.mock('@/api/contact')

const renderReady = async () => {
  vi.mocked(contactApi.getContact).mockResolvedValue(mockContact)
  render(<Footer />)
  await waitFor(() => {
    expect(screen.getByRole('link', { name: 'GitHub' })).toBeInTheDocument()
  })
}

describe('Footer Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders footer brand information', async () => {
    await renderReady()

    expect(screen.getByText('Carlos Jiménez Hirashi')).toBeInTheDocument()
    expect(screen.getByText(/AI Solutions Architect/)).toBeInTheDocument()
  })

  it('renders the Navegación section', async () => {
    await renderReady()

    expect(screen.getByText('Navegación')).toBeInTheDocument()
  })

  it('renders the Recursos section', async () => {
    await renderReady()

    expect(screen.getByText('Recursos')).toBeInTheDocument()
  })

  it('renders the Sígueme section when social links exist', async () => {
    await renderReady()

    expect(screen.getByText('Sígueme')).toBeInTheDocument()
  })

  it('renders navigation links in the footer', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: /^Home$/ })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Sobre Mí' })).toHaveAttribute('href', '/about')
    expect(screen.getByRole('link', { name: 'Proyectos' })).toHaveAttribute('href', '/projects')
  })

  it('renders resources links', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: 'Blog' })).toHaveAttribute('href', '/blog')
    expect(screen.getByRole('link', { name: 'Contacto' })).toHaveAttribute('href', '/contact')
  })

  it('renders the contact email as a mailto link', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: mockContact.contact_email! })).toHaveAttribute(
      'href',
      `mailto:${mockContact.contact_email}`
    )
  })

  it('renders social links from real contact data', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: 'GitHub' })).toHaveAttribute('href', mockContact.github_url!)
    expect(screen.getByRole('link', { name: 'LinkedIn' })).toHaveAttribute('href', mockContact.linkedin_url!)
    expect(screen.getByRole('link', { name: mockContact.footer_links[0].label })).toHaveAttribute(
      'href',
      mockContact.footer_links[0].url
    )
  })

  it('social links open in a new tab', async () => {
    await renderReady()

    const githubLink = screen.getByRole('link', { name: 'GitHub' })
    expect(githubLink).toHaveAttribute('target', '_blank')
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders copyright information with the current year', async () => {
    await renderReady()

    const year = new Date().getFullYear()
    expect(screen.getByText(new RegExp(`© ${year} Carlos Jiménez Hirashi`))).toBeInTheDocument()
  })

  it('does not render dead placeholder links', async () => {
    await renderReady()

    expect(screen.queryByRole('link', { name: /Sitemap/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Privacy/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Terms/i })).not.toBeInTheDocument()
  })

  it('tracks social media clicks', async () => {
    const user = userEvent.setup()
    await renderReady()

    const githubLink = screen.getByRole('link', { name: 'GitHub' })
    await user.click(githubLink)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: 'social-github' }))
  })

  it('omits the Sígueme section when there are no social links', async () => {
    vi.mocked(contactApi.getContact).mockResolvedValue({
      ...mockContact,
      github_url: null,
      linkedin_url: null,
      footer_links: [],
    })
    render(<Footer />)

    await waitFor(() => {
      expect(screen.getByText('Navegación')).toBeInTheDocument()
    })
    expect(screen.queryByText('Sígueme')).not.toBeInTheDocument()
  })

  it('renders with the Glass Steel section-alt treatment', () => {
    const { container } = render(<Footer />)

    const footer = container.querySelector('footer')
    expect(footer).toHaveClass('section-alt')
    expect(footer).toHaveClass('text-text-secondary')
  })

  it('displays the footer in a grid layout', () => {
    const { container } = render(<Footer />)

    const grid = container.querySelector('.grid')
    expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-4')
  })

  it('separates footer sections with a divider', () => {
    const { container } = render(<Footer />)

    const divider = container.querySelector('.border-t.border-border')
    expect(divider).toBeInTheDocument()
  })
})
