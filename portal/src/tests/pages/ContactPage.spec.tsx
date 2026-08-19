import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { contactApi } from '@/api/contact'
import { ContactPage } from '@/pages/ContactPage'
import { mockContact, mockContactMessage } from '../fixtures/mockData'

vi.mock('@/api/tracking')
vi.mock('@/api/contact')

const renderReady = async () => {
  vi.mocked(contactApi.getContact).mockResolvedValue(mockContact)
  render(<ContactPage />)
  await waitFor(() => {
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument()
  })
}

const fillAndSubmit = async (user: ReturnType<typeof userEvent.setup>) => {
  const nameInput = screen.getByLabelText(/Nombre/i)
  const emailInput = screen.getByLabelText(/Email/i)
  const messageInput = screen.getByLabelText(/Mensaje/i)
  const submitButton = screen.getByRole('button', { name: /Enviar mensaje/i })

  await user.type(nameInput, mockContactMessage.name)
  await user.type(emailInput, mockContactMessage.email)
  await user.type(messageInput, mockContactMessage.message)
  await user.click(submitButton)
}

describe('ContactPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading', async () => {
    await renderReady()

    expect(screen.getByText('Hablemos de tu proyecto')).toBeInTheDocument()
  })

  it('renders the contact form with all fields', async () => {
    await renderReady()

    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Mensaje/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Asunto/i)).not.toBeInTheDocument()
  })

  it('renders WhatsApp and location info cards', async () => {
    await renderReady()

    expect(screen.getByText(mockContact.whatsapp!)).toBeInTheDocument()
    expect(screen.getByText(mockContact.location!)).toBeInTheDocument()
  })

  it('renders the submit button', async () => {
    await renderReady()

    expect(screen.getByRole('button', { name: /Enviar mensaje/i })).toBeInTheDocument()
  })

  it('updates form fields on input change', async () => {
    const user = userEvent.setup()
    await renderReady()

    const nameInput = screen.getByLabelText(/Nombre/i) as HTMLInputElement
    const emailInput = screen.getByLabelText(/Email/i) as HTMLInputElement

    await user.type(nameInput, 'John Doe')
    await user.type(emailInput, 'john@example.com')

    expect(nameInput.value).toBe('John Doe')
    expect(emailInput.value).toBe('john@example.com')
  })

  it('displays a success message after form submission', async () => {
    const user = userEvent.setup()
    await renderReady()
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(screen.getByText(/¡Mensaje enviado!/i)).toBeInTheDocument()
    })
  })

  it('tracks the form submission', async () => {
    const user = userEvent.setup()
    await renderReady()
    await fillAndSubmit(user)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'form_submit', target: 'contact-form' })
    )
  })

  it('tracks the submit button click', async () => {
    const user = userEvent.setup()
    await renderReady()
    await fillAndSubmit(user)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(expect.objectContaining({ target: 'contact-submit' }))
  })

  it('displays the contact email from real data', async () => {
    await renderReady()

    const emailLink = screen.getByRole('link', { name: mockContact.contact_email! })
    expect(emailLink).toHaveAttribute('href', `mailto:${mockContact.contact_email}`)
  })

  it('renders social links from real data', async () => {
    await renderReady()

    expect(screen.getByRole('link', { name: 'GitHub' })).toHaveAttribute('href', mockContact.github_url!)
    expect(screen.getByRole('link', { name: 'LinkedIn' })).toHaveAttribute('href', mockContact.linkedin_url!)
  })

  it('has required attributes on name, email, and message fields', async () => {
    await renderReady()

    expect(screen.getByLabelText(/Nombre/i)).toHaveAttribute('required')
    const emailInput = screen.getByLabelText(/Email/i)
    expect(emailInput).toHaveAttribute('required')
    expect(emailInput).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText(/Mensaje/i)).toHaveAttribute('required')
  })

  it('hides the form and shows success after submission', async () => {
    const user = userEvent.setup()
    await renderReady()

    const form = screen.getByLabelText(/Nombre/i).closest('form')
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(screen.getByText(/¡Mensaje enviado!/i)).toBeInTheDocument()
    })
    expect(form).not.toBeInTheDocument()
  })

  it('shows a green success box', async () => {
    const user = userEvent.setup()
    await renderReady()
    await fillAndSubmit(user)

    await waitFor(() => {
      const successBox = screen.getByText(/¡Mensaje enviado!/i).closest('div')
      expect(successBox).toHaveClass('bg-green-50')
    })
  })

  it('reverts to the form after the success message times out', async () => {
    const user = userEvent.setup()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await renderReady()
    await fillAndSubmit(user)

    await waitFor(() => {
      expect(screen.getByText(/¡Mensaje enviado!/i)).toBeInTheDocument()
    })

    vi.advanceTimersByTime(5000)

    await waitFor(() => {
      expect(screen.queryByText(/¡Mensaje enviado!/i)).not.toBeInTheDocument()
      expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument()
    })

    vi.useRealTimers()
  })

  it('shows a loading spinner while contact info loads', () => {
    vi.mocked(contactApi.getContact).mockImplementation(() => new Promise(() => {}))

    render(<ContactPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('shows an error message when contact info fails to load', async () => {
    vi.mocked(contactApi.getContact).mockRejectedValue(new Error('Failed'))

    render(<ContactPage />)

    await waitFor(() => {
      expect(screen.getByText(/No se pudo cargar la información de contacto/i)).toBeInTheDocument()
    })
  })
})
