import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../testUtils'
import userEvent from '@testing-library/user-event'
import { trackingApi } from '@/api/tracking'
import { ContactPage } from '@/pages/ContactPage'
import { mockContactMessage } from '../fixtures/mockData'

vi.mock('@/api/tracking')

describe('ContactPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Get in Touch heading', () => {
    render(<ContactPage />)

    expect(screen.getByText('Get in Touch')).toBeInTheDocument()
  })

  it('renders contact page description', () => {
    render(<ContactPage />)

    expect(screen.getByText(/Have a question or want to work together/i)).toBeInTheDocument()
  })

  it('renders contact form with all fields', () => {
    render(<ContactPage />)

    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Subject/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Message/i)).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<ContactPage />)

    expect(screen.getByRole('button', { name: /Send Message/i })).toBeInTheDocument()
  })

  it('updates form fields on input change', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i) as HTMLInputElement
    const emailInput = screen.getByLabelText(/Email/i) as HTMLInputElement

    await user.type(nameInput, 'John Doe')
    await user.type(emailInput, 'john@example.com')

    expect(nameInput.value).toBe('John Doe')
    expect(emailInput.value).toBe('john@example.com')
  })

  it('displays success message after form submission', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Message Sent/i)).toBeInTheDocument()
      expect(screen.getByText(/Thank you for reaching out/i)).toBeInTheDocument()
    })
  })

  it('resets form fields after submission', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i) as HTMLInputElement
    const emailInput = screen.getByLabelText(/Email/i) as HTMLInputElement
    const messageInput = screen.getByLabelText(/Message/i) as HTMLTextAreaElement
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Message Sent/i)).toBeInTheDocument()
    })

    expect(nameInput.value).toBe('')
    expect(emailInput.value).toBe('')
    expect(messageInput.value).toBe('')
  })

  it('tracks form submission', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'form_submit',
        target: 'contact-form',
      })
    )
  })

  it('tracks submit button click', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, 'Test')
    await user.type(emailInput, 'test@example.com')
    await user.type(messageInput, 'Test message')
    await user.click(submitButton)

    expect(trackingApi.trackEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        target: 'contact-submit',
      })
    )
  })

  it('renders contact info section', () => {
    render(<ContactPage />)

    expect(screen.getByText(/Email/)).toBeInTheDocument()
    expect(screen.getByText(/Follow/)).toBeInTheDocument()
  })

  it('displays email address', () => {
    render(<ContactPage />)

    const emailLink = screen.getByRole('link', { name: 'cjhirashi@gmail.com' })
    expect(emailLink).toHaveAttribute('href', 'mailto:cjhirashi@gmail.com')
  })

  it('renders social media links', () => {
    render(<ContactPage />)

    expect(screen.getByRole('link', { name: /GitHub/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /LinkedIn/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Twitter/i })).toBeInTheDocument()
  })

  it('displays response time information', () => {
    render(<ContactPage />)

    expect(screen.getByText(/Response Time/i)).toBeInTheDocument()
    expect(screen.getByText(/Usually within 24 hours/i)).toBeInTheDocument()
  })

  it('has required attributes on name field', () => {
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i) as HTMLInputElement
    expect(nameInput).toHaveAttribute('required')
  })

  it('has required attributes on email field', () => {
    render(<ContactPage />)

    const emailInput = screen.getByLabelText(/Email/i) as HTMLInputElement
    expect(emailInput).toHaveAttribute('required')
    expect(emailInput).toHaveAttribute('type', 'email')
  })

  it('has required attributes on message field', () => {
    render(<ContactPage />)

    const messageInput = screen.getByLabelText(/Message/i) as HTMLTextAreaElement
    expect(messageInput).toHaveAttribute('required')
  })

  it('has subject field not required', () => {
    render(<ContactPage />)

    const subjectInput = screen.getByLabelText(/Subject/i) as HTMLInputElement
    expect(subjectInput).not.toHaveAttribute('required')
  })

  it('hides form and shows success after submission', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const form = screen.getByLabelText(/Name/i).closest('form')

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Message Sent/i)).toBeInTheDocument()
    })

    expect(form).not.toBeInTheDocument()
  })

  it('shows success message with checkmark icon', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    await waitFor(() => {
      const successBox = screen.getByText(/Message Sent/i).closest('div')
      expect(successBox).toHaveClass('bg-green-50')
    })
  })

  it('reverts to form after success message timeout', async () => {
    const user = userEvent.setup()
    vi.useFakeTimers()

    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Message Sent/i)).toBeInTheDocument()
    })

    vi.advanceTimersByTime(5000)

    await waitFor(() => {
      expect(screen.queryByText(/Message Sent/i)).not.toBeInTheDocument()
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument()
    })

    vi.useRealTimers()
  })

  it('disables submit button while loading', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i }) as HTMLButtonElement

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    expect(submitButton).toHaveAttribute('disabled')
  })

  it('shows Sending text while loading', async () => {
    const user = userEvent.setup()
    render(<ContactPage />)

    const nameInput = screen.getByLabelText(/Name/i)
    const emailInput = screen.getByLabelText(/Email/i)
    const messageInput = screen.getByLabelText(/Message/i)
    const submitButton = screen.getByRole('button', { name: /Send Message/i })

    await user.type(nameInput, mockContactMessage.name)
    await user.type(emailInput, mockContactMessage.email)
    await user.type(messageInput, mockContactMessage.message)
    await user.click(submitButton)

    expect(screen.getByText(/Sending/i)).toBeInTheDocument()
  })
})
