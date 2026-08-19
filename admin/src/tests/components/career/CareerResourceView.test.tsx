import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '../../utils'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { CAREER_RESOURCES } from '@/config/careerResources'
import { careerApi } from '@/api/career'

vi.mock('@/api/career')

const mockedCareerApi = vi.mocked(careerApi)

// Real config used to validate this generic component - Competencias is the
// pilot resource for the list/view/edit-in-place redesign (no popup modal).
const config = CAREER_RESOURCES.competencies

const sampleItem = {
  id: 1,
  user_id: 1,
  name: 'Liderazgo Técnico',
  type: 'business',
  category: 'Gestión',
  level: 'Senior',
  years_of_experience: 8,
  proficiency_score: 90,
  is_highlighted: true,
  depth_description: 'Descripción larga de la profundidad de esta competencia, con varias oraciones.',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-02-01T00:00:00Z',
}

describe('CareerResourceView (list / view / edit-in-place)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedCareerApi.list.mockResolvedValue([sampleItem] as never)
  })

  it('renders the table by default', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('never renders a popup dialog - everything happens in place', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Liderazgo Técnico'))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('switches to a read-only view showing the full record when a row is clicked', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Liderazgo Técnico'))

    // The table is gone, replaced by the record view in the same card.
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    // A field that is NOT one of the table's summary columns is shown in full.
    expect(
      screen.getByText('Descripción larga de la profundidad de esta competencia, con varias oraciones.')
    ).toBeInTheDocument()
    // Metadata section.
    expect(screen.getByText('ID')).toBeInTheDocument()
  })

  it('goes back to the table when "Volver" is clicked from the view', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Liderazgo Técnico'))
    fireEvent.click(screen.getByRole('button', { name: /volver/i }))

    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('opens the edit form directly from the row\'s pencil icon, without going through view', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByLabelText('Editar'))

    expect(screen.getByRole('form')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Liderazgo Técnico')).toBeInTheDocument()
  })

  it('opens the edit form from within the view, pre-filled with the record', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Liderazgo Técnico'))
    fireEvent.click(screen.getByRole('button', { name: /editar/i }))

    expect(screen.getByDisplayValue('Liderazgo Técnico')).toBeInTheDocument()
  })

  it('cancelling out of edit (opened from view) returns to the view, not the table', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByText('Liderazgo Técnico'))
    fireEvent.click(screen.getByRole('button', { name: /editar/i }))
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))

    expect(screen.queryByRole('form')).not.toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByText('ID')).toBeInTheDocument() // back in the view
  })

  it('cancelling out of create returns to the table', async () => {
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /nuevo/i }))
    expect(screen.getByRole('form')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('shows the newly created record in the view after a successful create', async () => {
    mockedCareerApi.create.mockResolvedValue({ ...sampleItem, id: 2, name: 'Pensamiento Sistémico' } as never)
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /nuevo/i }))
    const form = screen.getByRole('form')
    fireEvent.change(within(form).getByLabelText(/^nombre/i), { target: { value: 'Pensamiento Sistémico' } })
    fireEvent.change(within(form).getByLabelText(/^tipo/i), { target: { value: 'technical' } })
    fireEvent.click(within(form).getByRole('button', { name: /crear/i }))

    await waitFor(() => expect(screen.getAllByText('Pensamiento Sistémico').length).toBeGreaterThan(0))
    expect(screen.queryByRole('form')).not.toBeInTheDocument()
  })

  it('still asks for confirmation before deleting from the table row', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<CareerResourceView config={config} />)
    await waitFor(() => expect(screen.getByText('Liderazgo Técnico')).toBeInTheDocument())

    fireEvent.click(screen.getByLabelText('Eliminar'))

    expect(confirmSpy).toHaveBeenCalled()
    expect(mockedCareerApi.remove).not.toHaveBeenCalled()
    confirmSpy.mockRestore()
  })
})
