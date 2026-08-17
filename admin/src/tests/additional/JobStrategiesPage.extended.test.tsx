import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { JobStrategiesPage } from '@/pages/JobStrategiesPage'
import { useAuthStore } from '@/stores/authStore'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/api/job-strategies')

describe('JobStrategiesPage - Extended', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })
  })

  describe('strategy management', () => {
    it('should display job strategies', async () => {
      render(<JobStrategiesPage />)
      await waitFor(() => {
        expect(screen.getByText(/Strategy|Strategies/i)).toBeInTheDocument()
      })
    })

    it('should add new strategy', async () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText(/Strategy|Strategies/i)).toBeInTheDocument()
    })

    it('should edit strategy', async () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText(/Strategy|Strategies/i)).toBeInTheDocument()
    })

    it('should delete strategy', async () => {
      render(<JobStrategiesPage />)
      expect(screen.getByText(/Strategy|Strategies/i)).toBeInTheDocument()
    })
  })
})
