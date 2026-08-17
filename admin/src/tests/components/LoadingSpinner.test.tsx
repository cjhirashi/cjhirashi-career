import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from '@/components/LoadingSpinner'

describe('LoadingSpinner', () => {
  describe('rendering', () => {
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

    it('renders without message when empty string provided', () => {
      const { container } = render(<LoadingSpinner message="" />)
      expect(container.querySelector('p')).not.toBeInTheDocument()
    })

    it('renders border circles for spinner animation', () => {
      const { container } = render(<LoadingSpinner />)
      const circles = container.querySelectorAll('.border-4')
      expect(circles.length).toBeGreaterThan(0)
    })
  })

  describe('fullScreen mode', () => {
    it('renders in fullscreen mode by default', () => {
      const { container } = render(<LoadingSpinner />)
      const fullScreenContainer = container.querySelector('.min-h-screen')
      expect(fullScreenContainer).toBeInTheDocument()
    })

    it('renders with background color when fullscreen', () => {
      const { container } = render(<LoadingSpinner />)
      const bgContainer = container.querySelector('.bg-slate-50')
      expect(bgContainer).toBeInTheDocument()
    })

    it('renders with flex centering in fullscreen mode', () => {
      const { container } = render(<LoadingSpinner />)
      const centerContainer = container.querySelector('.flex.items-center.justify-center.min-h-screen')
      expect(centerContainer).toBeInTheDocument()
    })
  })

  describe('inline mode', () => {
    it('renders inline when fullScreen is false', () => {
      const { container } = render(<LoadingSpinner fullScreen={false} />)
      const inlineContainer = container.querySelector('.py-8')
      expect(inlineContainer).toBeInTheDocument()
    })

    it('does not render background color in inline mode', () => {
      const { container } = render(<LoadingSpinner fullScreen={false} />)
      const bgContainer = container.querySelector('.bg-slate-50')
      expect(bgContainer).not.toBeInTheDocument()
    })

    it('does not have min-h-screen in inline mode', () => {
      const { container } = render(<LoadingSpinner fullScreen={false} />)
      const fullScreenContainer = container.querySelector('.min-h-screen')
      expect(fullScreenContainer).not.toBeInTheDocument()
    })
  })

  describe('styling and colors', () => {
    it('uses cyan color for spinner animation', () => {
      const { container } = render(<LoadingSpinner />)
      const animatedBorder = container.querySelector('.border-t-cyan-600')
      expect(animatedBorder).toBeInTheDocument()
    })

    it('uses slate colors for text', () => {
      const { container } = render(<LoadingSpinner />)
      const textElement = container.querySelector('.text-slate-600')
      expect(textElement).toBeInTheDocument()
    })

    it('uses slate colors for spinner border', () => {
      const { container } = render(<LoadingSpinner />)
      const spinnerBorder = container.querySelector('.border-slate-200')
      expect(spinnerBorder).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('arranges content vertically with spacing', () => {
      const { container } = render(<LoadingSpinner />)
      const flexCol = container.querySelector('.flex-col')
      expect(flexCol).toBeInTheDocument()
    })

    it('centers spinner and message', () => {
      const { container } = render(<LoadingSpinner />)
      const centered = container.querySelector('.items-center.justify-center')
      expect(centered).toBeInTheDocument()
    })

    it('has proper spacing between spinner and message', () => {
      const { container } = render(<LoadingSpinner />)
      const spacedContainer = container.querySelector('.space-y-4')
      expect(spacedContainer).toBeInTheDocument()
    })
  })

  describe('props combinations', () => {
    it('handles both fullScreen true and custom message', () => {
      render(<LoadingSpinner fullScreen={true} message="Custom message" />)
      expect(screen.getByText('Custom message')).toBeInTheDocument()
    })

    it('handles both fullScreen false and custom message', () => {
      render(<LoadingSpinner fullScreen={false} message="Loading data..." />)
      expect(screen.getByText('Loading data...')).toBeInTheDocument()
    })

    it('handles fullScreen true with empty message', () => {
      const { container } = render(<LoadingSpinner fullScreen={true} message="" />)
      expect(container.querySelector('.min-h-screen')).toBeInTheDocument()
      expect(container.querySelector('p')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('displays message for screen readers', () => {
      render(<LoadingSpinner message="Loading content..." />)
      const message = screen.getByText('Loading content...')
      expect(message).toBeVisible()
    })

    it('has semantic structure', () => {
      const { container } = render(<LoadingSpinner />)
      const divs = container.querySelectorAll('div')
      expect(divs.length).toBeGreaterThan(0)
    })
  })
})
