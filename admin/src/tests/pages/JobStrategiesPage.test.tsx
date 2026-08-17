import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { JobStrategiesPage } from '@/pages/JobStrategiesPage'

describe('JobStrategiesPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText('Job Search Strategies')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText(/Manage your job search strategy and track opportunities/i)).toBeInTheDocument()
    })

    it('should render coming soon message', () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText(/Job strategies management coming soon/i)).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('should have heading element', () => {
      const { container } = render(<JobStrategiesPage />)
      const h1 = container.querySelector('h1')
      expect(h1).toBeInTheDocument()
    })

    it('should have card component', () => {
      const { container } = render(<JobStrategiesPage />)
      const card = container.querySelector('.card')
      expect(card).toBeInTheDocument()
    })
  })

  describe('styling', () => {
    it('should apply slate colors', () => {
      const { container } = render(<JobStrategiesPage />)
      const title = container.querySelector('h1')
      expect(title?.className).toContain('text-slate')
    })

    it('should have proper heading size', () => {
      const { container } = render(<JobStrategiesPage />)
      const title = container.querySelector('h1')
      expect(title?.className).toContain('text-3xl')
    })
  })
})
