import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { render as renderWithProviders, screen, waitFor, within, fireEvent } from '../../utils'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { CAREER_RESOURCES } from '@/config/careerResources'
import { careerApi } from '@/api/career'

function render(ui: ReactElement) {
  return renderWithProviders(<MemoryRouter initialEntries={['/']}>{ui}</MemoryRouter>)
}

vi.mock('@/api/career')
const mockedCareerApi = vi.mocked(careerApi)

const vacancy = (over: Record<string, unknown> = {}) => ({
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
  ...over,
})

const COLUMN_STORAGE_KEY = 'cjhirashi.career.table-columns.vacancies'

describe('Vacantes: badges de Estado y Etapa en la tabla', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockedCareerApi.list.mockResolvedValue([vacancy()] as never)
    mockedCareerApi.count.mockResolvedValue(1)
  })

  it('RF-010 RF-014: la fila muestra dos badges con la etiqueta en español, no el código', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    const row = (await screen.findByText('ACME')).closest('tr') as HTMLElement
    expect(within(row).getByText('Entrevista RH')).toBeInTheDocument()
    expect(within(row).getByText('En proceso')).toBeInTheDocument()
    expect(within(row).queryByText('hr_interview')).not.toBeInTheDocument()
    expect(within(row).queryByText('in_process')).not.toBeInTheDocument()
  })

  it('RF-019: valor fuera de catálogo o vacío muestra "Sin definir" sin romper la fila', async () => {
    mockedCareerApi.list.mockResolvedValue([
      vacancy({ id: 'vac-2', company: 'Rara', process_stage: 'zzz', vacancy_status: 'zzz' }),
      vacancy({ id: 'vac-3', company: 'Vacía', process_stage: '', vacancy_status: null }),
    ] as never)
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    for (const company of ['Rara', 'Vacía']) {
      const row = (await screen.findByText(company)).closest('tr') as HTMLElement
      expect(within(row).getAllByText('Sin definir')).toHaveLength(2)
    }
  })

  it('RF-017: los encabezados Estado y Etapa tienen botón de filtro', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    await screen.findByText('ACME')
    const headers = screen.getAllByRole('columnheader')
    const header = (name: string) => headers.find((h) => h.textContent?.includes(name)) as HTMLElement
    expect(within(header('Estado')).getByRole('combobox', { name: 'Filtrar Estado' })).toBeInTheDocument()
    expect(within(header('Etapa')).getByRole('combobox', { name: 'Filtrar Etapa del proceso' })).toBeInTheDocument()
  })

  it('RF-025: "En etapa desde" se muestra sólo con fecha, sin hora', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    const row = (await screen.findByText('ACME')).closest('tr') as HTMLElement
    expect(row.textContent).toMatch(/13/)
    expect(row.textContent).not.toMatch(/\d{1,2}:\d{2}/)
  })

  it('RF-020: el formulario no tiene control para vacancy_status ni para la fecha de etapa', async () => {
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    await screen.findByText('ACME')
    fireEvent.click(screen.getByRole('button', { name: 'Nuevo' }))
    await screen.findByText('Etapa del proceso')
    expect(screen.queryByLabelText('Estado')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('En etapa desde')).not.toBeInTheDocument()
    expect(screen.queryByText('Estado de la aplicación')).not.toBeInTheDocument()
  })

  it('no regresión: cv-versions.status sigue mostrando el código crudo en su badge/cápsula', async () => {
    mockedCareerApi.list.mockResolvedValue([
      { id: 'cvv-1', user_id: 'usr-1', title: 'CV Base', status: 'approved', length_pages: 2 },
    ] as never)
    render(<CareerResourceView config={CAREER_RESOURCES['cv-versions']} />)
    const row = (await screen.findByText('CV Base')).closest('tr') as HTMLElement
    expect(row.textContent).toContain('approved')
    expect(row.textContent).not.toContain('Sin definir')
  })

  it('R-5: una preferencia de columnas guardada con application_status no rompe la tabla', async () => {
    localStorage.setItem(
      COLUMN_STORAGE_KEY,
      JSON.stringify(['id', 'company', 'application_status', 'exact_role'])
    )
    render(<CareerResourceView config={CAREER_RESOURCES.vacancies} />)
    const row = (await screen.findByText('ACME')).closest('tr') as HTMLElement
    expect(within(row).getByText('Dev Senior')).toBeInTheDocument()
    await waitFor(() => expect(screen.getAllByRole('columnheader').length).toBeGreaterThan(0))
    expect(screen.queryByText('Estado de la aplicación')).not.toBeInTheDocument()
  })
})
