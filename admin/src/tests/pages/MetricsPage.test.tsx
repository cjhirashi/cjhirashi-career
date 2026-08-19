import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { MetricsPage } from '@/pages/MetricsPage'

describe('MetricsPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<MetricsPage />)
      expect(screen.getByText('Metrics')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<MetricsPage />)
      expect(screen.getByText(/Monitor your portfolio progress and activity/i)).toBeInTheDocument()
    })

    it('should render activity timeline section', () => {
      render(<MetricsPage />)
      expect(screen.getByText('Activity Timeline')).toBeInTheDocument()
    })

    it('should display coming soon message', () => {
      render(<MetricsPage />)
      expect(screen.getByText('Real-time metrics coming soon')).toBeInTheDocument()
    })
  })

  describe('metrics cards', () => {
    it('should render all metric cards', () => {
      render(<MetricsPage />)
      expect(screen.getByText('Profile Completeness')).toBeInTheDocument()
      expect(screen.getByText('Portal Views')).toBeInTheDocument()
      expect(screen.getByText('Interactions')).toBeInTheDocument()
      expect(screen.getByText('Agent Activity')).toBeInTheDocument()
    })

    it('should display metric values as 0', () => {
      render(<MetricsPage />)
      const zeroValues = screen.getAllByText('0')
      expect(zeroValues.length).toBeGreaterThanOrEqual(4)
    })

    it('should display metric percentage for completeness', () => {
      render(<MetricsPage />)
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('should have emoji icons for metrics', () => {
      const { container } = render(<MetricsPage />)
      expect(container.textContent).toContain('📊')
      expect(container.textContent).toContain('👁️')
      expect(container.textContent).toContain('🔗')
      expect(container.textContent).toContain('🤖')
    })
  })

  describe('layout structure', () => {
    it('should use grid layout for metric cards', () => {
      const { container } = render(<MetricsPage />)
      const grid = container.querySelector('.grid')
      expect(grid?.classList.contains('grid-cols-1')).toBe(true)
      expect(grid?.classList.contains('md:grid-cols-2')).toBe(true)
      expect(grid?.classList.contains('lg:grid-cols-4')).toBe(true)
    })

    it('should have proper card styling', () => {
      const { container } = render(<MetricsPage />)
      const cards = container.querySelectorAll('.card')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('should have proper spacing between sections', () => {
      const { container } = render(<MetricsPage />)
      const title = container.querySelector('h1')
      expect(title?.classList.contains('mb-8')).toBe(true)
    })
  })

  describe('styling consistency', () => {
    it('should use slate colors', () => {
      const { container } = render(<MetricsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-slate-900')
    })

    it('should have proper typography', () => {
      const { container } = render(<MetricsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-3xl')
      expect(heading?.className).toContain('font-bold')
    })

    it('should have consistent card padding', () => {
      const { container } = render(<MetricsPage />)
      // Quick-stat tiles use the `.stat-card` variant (a `.card` with glass
      // hover glow baked in via `@apply card p-6` in index.css) instead of
      // the raw `.card.p-6` combo.
      const metricCards = container.querySelectorAll('.stat-card')
      expect(metricCards.length).toBeGreaterThan(0)
    })
  })
})
