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
    expect(screen.getByText('GitHub')).toBeInTheDocument()
  })
}

describe('Footer Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders copyright information with the current year', async () => {
    await renderReady()

    const year = new Date().getFullYear()
    expect(screen.getByText(new RegExp(`© ${year} Carlos A. Jiménez Hirashi`))).toBeInTheDocument()
  })

  it('renders social links from real contact data', async () => {
    await renderReady()

    expect(screen.getByText('GitHub').closest('a')).toHaveAttribute('href', mockContact.github_url!)
    expect(screen.getByText('LinkedIn').closest('a')).toHaveAttribute('href', mockContact.linkedin_url!)
    expect(screen.getByText('Email').closest('a')).toHaveAttribute('href', `mailto:${mockContact.contact_email}`)
    expect(screen.getByText('WhatsApp').closest('a')).toHaveAttribute(
      'href',
      expect.stringContaining('wa.me')
    )
  })

  it('social links open in a new tab', async () => {
    await renderReady()

    const githubLink = screen.getByText('GitHub').closest('a')!
    expect(githubLink).toHaveAttribute('target', '_blank')
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('tracks social media clicks', async () => {
    const user = userEvent.setup()
    await renderReady()

    await user.click(screen.getByText('GitHub'))

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: 'social-github' }))
  })

  it('does not render Navegación/Recursos columns', async () => {
    await renderReady()

    expect(screen.queryByText('Navegación')).not.toBeInTheDocument()
    expect(screen.queryByText('Recursos')).not.toBeInTheDocument()
  })

  it('renders no social links when contact data has none', async () => {
    vi.mocked(contactApi.getContact).mockResolvedValue({
      contact_email: null,
      whatsapp: null,
      location: null,
      availability_status: null,
      preferred_contact_method: null,
      footer_links: [],
      linkedin_url: null,
      github_url: null,
    })
    render(<Footer />)

    await waitFor(() => {
      expect(screen.getByText(new RegExp(`© ${new Date().getFullYear()}`))).toBeInTheDocument()
    })
    expect(screen.queryByText('GitHub')).not.toBeInTheDocument()
  })

  it('renders as a footer element with a top border', () => {
    const { container } = render(<Footer />)

    const footer = container.querySelector('footer')
    expect(footer).toHaveClass('border-t', 'border-border')
  })
})
