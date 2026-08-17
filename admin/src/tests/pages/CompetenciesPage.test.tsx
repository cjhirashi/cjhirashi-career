import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { CompetenciesPage } from '@/pages/CompetenciesPage'

describe('CompetenciesPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<CompetenciesPage />)
      expect(screen.getByText('Competencies')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<CompetenciesPage />)
      expect(screen.getByText(/Manage your technical, transferable, and business skills/i)).toBeInTheDocument()
    })

    it('should render coming soon message', () => {
      render(<CompetenciesPage />)
      expect(screen.getByText(/Competencies management coming soon/i)).toBeInTheDocument()
    })

    it('should display help text about skill categories', () => {
      render(<CompetenciesPage />)
      expect(screen.getByText(/Add technical, transferable, and business skills/i)).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('should have proper heading hierarchy', () => {
      const { container } = render(<CompetenciesPage />)
      const h1 = container.querySelector('h1')
      expect(h1).toBeInTheDocument()
      expect(h1?.textContent).toContain('Competencies')
    })

    it('should have card component', () => {
      const { container } = render(<CompetenciesPage />)
      const card = container.querySelector('.card')
      expect(card).toBeInTheDocument()
    })

    it('should have centered text content', () => {
      const { container } = render(<CompetenciesPage />)
      const cardBody = container.querySelector('.card-body')
      expect(cardBody?.classList.contains('text-center')).toBe(true)
    })

    it('should have proper spacing', () => {
      const { container } = render(<CompetenciesPage />)
      const heading = container.querySelector('h1')
      expect(heading?.classList.contains('mb-8')).toBe(true)
    })
  })

  describe('styling', () => {
    it('should use slate colors for text', () => {
      const { container } = render(<CompetenciesPage />)
      const description = container.querySelector('p')
      expect(description?.className).toContain('text-slate')
    })

    it('should have proper font sizing for heading', () => {
      const { container } = render(<CompetenciesPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-3xl')
      expect(heading?.className).toContain('font-bold')
    })

    it('should render card with proper padding', () => {
      const { container } = render(<CompetenciesPage />)
      const cardBody = container.querySelector('.card-body')
      expect(cardBody?.className).toContain('py-12')
    })
  })

  describe('content accuracy', () => {
    it('should only render expected text elements', () => {
      render(<CompetenciesPage />)
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
      expect(screen.queryByRole('form')).not.toBeInTheDocument()
    })

    it('should not render list items', () => {
      const { container } = render(<CompetenciesPage />)
      expect(container.querySelectorAll('li')).toHaveLength(0)
    })

    it('should render as minimal placeholder page', () => {
      const { container } = render(<CompetenciesPage />)
      expect(container.querySelectorAll('input')).toHaveLength(0)
      expect(container.querySelectorAll('textarea')).toHaveLength(0)
    })
  })
})
