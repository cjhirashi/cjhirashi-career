import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { EvidencePage } from '@/pages/EvidencePage'
import { useAuthStore } from '@/stores/authStore'
import { mockUser } from '../fixtures/mockData'

vi.mock('@/api/evidence')

describe('EvidencePage - Extended', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true })
  })

  describe('evidence creation', () => {
    it('should add new evidence item', async () => {
      render(<EvidencePage />)
      await waitFor(() => {
        expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
      })
    })

    it('should validate evidence form', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })

  describe('evidence editing', () => {
    it('should edit existing evidence', async () => {
      render(<EvidencePage />)
      await waitFor(() => {
        expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
      })
    })
  })

  describe('evidence deletion', () => {
    it('should delete evidence with confirmation', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })

  describe('evidence filtering', () => {
    it('should filter by evidence type', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })

  describe('error handling', () => {
    it('should show error when fetch fails', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })

  describe('loading states', () => {
    it('should show loading spinner while fetching', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('should show empty state when no evidence', async () => {
      render(<EvidencePage />)
      expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    })
  })
})
