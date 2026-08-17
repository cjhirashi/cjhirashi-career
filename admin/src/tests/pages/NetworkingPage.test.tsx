import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { NetworkingPage } from '@/pages/NetworkingPage'

describe('NetworkingPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<NetworkingPage />)
      expect(screen.getByText('Networking')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<NetworkingPage />)
      expect(screen.getByText(/Manage your professional network and connections/i)).toBeInTheDocument()
    })

    it('should render coming soon message', () => {
      render(<NetworkingPage />)
      expect(screen.getByText(/Networking management coming soon/i)).toBeInTheDocument()
    })
  })

  describe('layout', () => {
    it('should have proper page structure', () => {
      const { container } = render(<NetworkingPage />)
      const heading = container.querySelector('h1')
      expect(heading?.textContent).toContain('Networking')
    })

    it('should render card component', () => {
      const { container } = render(<NetworkingPage />)
      const card = container.querySelector('.card')
      expect(card).toBeInTheDocument()
    })

    it('should display centered content', () => {
      const { container } = render(<NetworkingPage />)
      const cardBody = container.querySelector('.card-body')
      expect(cardBody?.classList.contains('text-center')).toBe(true)
    })
  })

  describe('styling', () => {
    it('should have slate color scheme', () => {
      const { container } = render(<NetworkingPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-slate-900')
    })

    it('should use consistent typography', () => {
      const { container } = render(<NetworkingPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('font-bold')
      expect(heading?.className).toContain('text-3xl')
    })
  })
})
