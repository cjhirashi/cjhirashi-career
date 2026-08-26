import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorMessage } from '@/components/Common/ErrorMessage'

describe('ErrorMessage Component', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="An error occurred" />)
    expect(screen.getByText('An error occurred')).toBeInTheDocument()
  })

  it('renders retry button when provided', () => {
    const retryFn = vi.fn()
    render(<ErrorMessage message="An error occurred" retry={retryFn} />)

    const retryButton = screen.getByRole('button', { name: /try again/i })
    expect(retryButton).toBeInTheDocument()
  })

  it('calls retry function when retry button is clicked', async () => {
    const user = userEvent.setup()
    const retryFn = vi.fn()
    render(<ErrorMessage message="An error occurred" retry={retryFn} />)

    const retryButton = screen.getByRole('button', { name: /try again/i })
    await user.click(retryButton)

    expect(retryFn).toHaveBeenCalledOnce()
  })

  it('does not render retry button when not provided', () => {
    render(<ErrorMessage message="An error occurred" />)
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument()
  })
})
