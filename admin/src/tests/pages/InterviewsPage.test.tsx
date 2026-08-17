import { describe, it, expect } from 'vitest'
import { render, screen } from '../utils'
import { InterviewsPage } from '@/pages/InterviewsPage'

describe('InterviewsPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<InterviewsPage />)
      expect(screen.getByText('Interview Preparation')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<InterviewsPage />)
      expect(screen.getByText(/Prepare for interviews with curated questions and answers/i)).toBeInTheDocument()
    })

    it('should render coming soon message', () => {
      render(<InterviewsPage />)
      expect(screen.getByText(/Interview preparation content coming soon/i)).toBeInTheDocument()
    })
  })

  describe('page structure', () => {
    it('should have proper heading', () => {
      const { container } = render(<InterviewsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.textContent).toContain('Interview')
    })

    it('should have card component for content', () => {
      const { container } = render(<InterviewsPage />)
      const card = container.querySelector('.card')
      expect(card).toBeInTheDocument()
    })

    it('should have centered message', () => {
      const { container } = render(<InterviewsPage />)
      const cardBody = container.querySelector('.card-body')
      expect(cardBody?.classList.contains('text-center')).toBe(true)
    })
  })

  describe('styling', () => {
    it('should use slate color palette', () => {
      const { container } = render(<InterviewsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-slate-900')
    })

    it('should have proper typography size', () => {
      const { container } = render(<InterviewsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.className).toContain('text-3xl')
      expect(heading?.className).toContain('font-bold')
    })

    it('should have proper spacing', () => {
      const { container } = render(<InterviewsPage />)
      const heading = container.querySelector('h1')
      expect(heading?.classList.contains('mb-8')).toBe(true)
    })
  })
})
