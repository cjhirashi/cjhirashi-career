import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from '@/components/LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders loading spinner with default message', () => {
    render(<LoadingSpinner />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders custom message', () => {
    render(<LoadingSpinner message="Please wait..." />)
    expect(screen.getByText('Please wait...')).toBeInTheDocument()
  })

  it('renders spinner element', () => {
    const { container } = render(<LoadingSpinner />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('renders in fullscreen mode by default', () => {
    const { container } = render(<LoadingSpinner />)
    const fullScreenContainer = container.querySelector('.min-h-screen')
    expect(fullScreenContainer).toBeInTheDocument()
  })

  it('renders inline when fullScreen is false', () => {
    const { container } = render(<LoadingSpinner fullScreen={false} />)
    const inlineContainer = container.querySelector('.py-8')
    expect(inlineContainer).toBeInTheDocument()
  })
})
