import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { render as renderWithProviders, screen, waitFor, fireEvent } from '../../utils'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { CAREER_RESOURCES } from '@/config/careerResources'
import { careerApi } from '@/api/career'

function render(ui: ReactElement) {
  return renderWithProviders(<MemoryRouter initialEntries={['/']}>{ui}</MemoryRouter>)
}

vi.mock('@/api/career')
const mockedCareerApi = vi.mocked(careerApi)

const LABELS = ['Quiénes son', 'Qué buscan', 'Qué ofrecen', 'Cultura laboral']

const vacancy = {
  id: 'vac-1',
  user_id: 'usr-1',
  company: 'ACME',
  exact_role: 'Dev Senior',
  process_stage: 'hr_interview',
  vacancy_status: 'in_process',
  process_stage_updated_at: '2026-10-13T15:45:00Z',
  evaluation: 'apply',
  is_active: true,
  created_at: '2026-10-01T00:00:00Z',
  updated_at: '2026-10-01T00:00:00Z',
  company_overview: 'Primer párrafo de empresa.\n\nSegundo párrafo de empresa.',
  candidate_profile: 'Buscan **perfil senior**',
  offer_summary: 'Oferta competitiva',
  work_culture: 'Cultura abierta',
}

describe('RF-008 RF-009 RF-010: textos descriptivos de la vacante en el Admin', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockedCareerApi.list.mockResolvedValue([vacancy] as never)
    mockedCareerApi.count.mockResolvedValue(1)
  })

  it('RF-008: el formulario muestra cuatro textareas contiguas y en orden', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    await screen.findByText('ACME')
    fireEvent.click(screen.getByRole('button', { name: 'Nuevo' }))
    await screen.findByText('Etapa del proceso')
    const areas = LABELS.map((l) => screen.getByLabelText(l, { exact: true }))
    for (const area of areas) expect(area.tagName).toBe('TEXTAREA')
    const all = Array.from(document.querySelectorAll('textarea'))
    const positions = areas.map((a) => all.indexOf(a as HTMLTextAreaElement))
    positions.forEach((p, n) => {
      if (n > 0) expect(p).toBe(positions[n - 1] + 1)
    })
  })

  it('RF-009: la ficha muestra los cuatro en orden canónico con Markdown vigente', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    fireEvent.click(await screen.findByText('ACME'))
    await waitFor(() => expect(screen.getByText('Quiénes son')).toBeInTheDocument())
    const text = document.body.textContent ?? ''
    const order = LABELS.map((l) => text.indexOf(l))
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
    // D-06: párrafos separados por línea en blanco -> párrafos distintos.
    expect(screen.getByText('Primer párrafo de empresa.').tagName).toBe('P')
    expect(screen.getByText('Segundo párrafo de empresa.').tagName).toBe('P')
    expect(screen.getByText('perfil senior').tagName).toBe('STRONG')
  })

  it('RF-010: la tabla no tiene columnas de estos campos', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    await screen.findByText('ACME')
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent ?? '')
    for (const l of LABELS) expect(headers.some((h) => h.includes(l))).toBe(false)
  })
})
