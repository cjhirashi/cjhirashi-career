import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '../utils'
import { CareerResourcePage } from '@/pages/CareerResourcePage'
import { careerApi } from '@/api/career'

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/career/:resourceKey/:recordSlug?" element={<CareerResourcePage />} />
      </Routes>
    </MemoryRouter>
  )

describe('CareerResourcePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedCareerApi.list.mockResolvedValue([
      { id: 1, user_id: 1, company: 'Acme Corp', exact_role: 'Data Director', evaluation: 'apply' },
    ] as never)
  })

  it('renders the resource label and table for a known resource key', async () => {
    renderAt('/career/vacancies')
    await waitFor(() =>
      expect(mockedCareerApi.list).toHaveBeenCalledWith('vacancies', {
        skip: 0,
        limit: 20,
        sortBy: undefined,
        sortDir: 'asc',
        search: undefined,
      })
    )
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Acme Corp')).toBeInTheDocument())
    expect(screen.getByRole('tab', { name: 'Lista' })).toHaveAttribute('aria-selected', 'true')
  })

  it('does not show the section description in the view window', async () => {
    renderAt('/career/differentiators')
    await waitFor(() => expect(mockedCareerApi.list).toHaveBeenCalled())
    expect(screen.queryByText(/pilares de ventaja competitiva/i)).not.toBeInTheDocument()
  })

  it('shows a not-found message for an unknown resource key', () => {
    renderAt('/career/does-not-exist')
    expect(screen.getByText('Recurso no encontrado')).toBeInTheDocument()
    expect(mockedCareerApi.list).not.toHaveBeenCalled()
  })

  it('links back to the dashboard from the not-found state', () => {
    renderAt('/career/does-not-exist')
    const link = screen.getByRole('link', { name: /Volver al Dashboard/i })
    expect(link).toHaveAttribute('href', '/dashboard')
  })

  it('renders the singleton form (no table) for the identity resource', async () => {
    mockedCareerApi.list.mockResolvedValue([] as never)
    renderAt('/career/identity')
    await waitFor(() =>
      expect(mockedCareerApi.list).toHaveBeenCalledWith('identity', {
        skip: 0,
        limit: 1,
        sortBy: undefined,
        sortDir: undefined,
        search: undefined,
      })
    )
  })
})
