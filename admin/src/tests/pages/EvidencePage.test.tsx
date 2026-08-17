import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { EvidencePage } from '@/pages/EvidencePage'

describe('EvidencePage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<EvidencePage />)
      expect(screen.getByText('Evidence')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Document your projects, positions, achievements, and cases/i)).toBeInTheDocument()
    })

    it('should render coming soon message', () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence management coming soon/i)).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('should have proper heading hierarchy', () => {
      const { container } = render(<EvidencePage />)
      const h1 = container.querySelector('h1')
      expect(h1?.textContent).toContain('Evidence')
    })

    it('should have card component', () => {
      const { container } = render(<EvidencePage />)
      const card = container.querySelector('.card')
      expect(card).toBeInTheDocument()
    })

    it('should have centered layout', () => {
      const { container } = render(<EvidencePage />)
      const cardBody = container.querySelector('.card-body')
      expect(cardBody?.classList.contains('text-center')).toBe(true)
    })
  })

  describe('styling consistency', () => {
    it('should use consistent spacing', () => {
      const { container } = render(<EvidencePage />)
      const heading = container.querySelector('h1')
      expect(heading?.classList.contains('mb-8')).toBe(true)
    })

    it('should use slate typography', () => {
      const { container } = render(<EvidencePage />)
      const title = container.querySelector('h1')
      expect(title?.className).toContain('text-slate-900')
    })
  })
})
